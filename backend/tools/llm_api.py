"""
LLM API 統合ラッパー
Anthropic (Opus/Sonnet) と Google AI Studio (Gemma 4) を統一インターフェースで呼び出す。
Prompt Caching対応、トークン消費追跡付き。
"""

import asyncio
import json
import logging
import re
from typing import Any, Optional

import anthropic
import google.generativeai as genai
from dataclasses import dataclass
from typing import Any, Optional, Callable

from backend.config import APIKeys, LLMModels

logger = logging.getLogger(__name__)


# ─── トークン消費追跡 ─────────────────────────────────────────

class TokenTracker:
    """セッション全体のトークン消費を追跡"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.opus_input = 0
        self.opus_output = 0
        self.opus_cache_write = 0
        self.opus_cache_read = 0
        self.sonnet_input = 0
        self.sonnet_output = 0
        self.sonnet_cache_write = 0
        self.sonnet_cache_read = 0
        self.gemma_input = 0
        self.gemma_output = 0
        self.gemini_input = 0
        self.gemini_output = 0
        self.total_calls = 0
    
    def record(self, model: str, usage: dict):
        self.total_calls += 1
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        
        if "opus" in model.lower():
            self.opus_input += input_tokens
            self.opus_output += output_tokens
            self.opus_cache_write += cache_write
            self.opus_cache_read += cache_read
        elif "sonnet" in model.lower():
            self.sonnet_input += input_tokens
            self.sonnet_output += output_tokens
            self.sonnet_cache_write += cache_write
            self.sonnet_cache_read += cache_read
        elif "gemini" in model.lower():
            self.gemini_input += input_tokens
            self.gemini_output += output_tokens
        else:
            self.gemma_input += input_tokens
            self.gemma_output += output_tokens
    
    def estimated_cost_usd(self) -> float:
        """推定コスト（USD）"""
        opus_cost = (self.opus_input * 15 + self.opus_output * 75) / 1_000_000
        sonnet_cost = (self.sonnet_input * 3 + self.sonnet_output * 15) / 1_000_000
        gemini_cost = (self.gemini_input * 1.25 + self.gemini_output * 3.75) / 1_000_000
        return opus_cost + sonnet_cost + gemini_cost
    
    def summary(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "opus": {"input": self.opus_input, "output": self.opus_output,
                     "cache_write": self.opus_cache_write, "cache_read": self.opus_cache_read},
            "sonnet": {"input": self.sonnet_input, "output": self.sonnet_output,
                       "cache_write": self.sonnet_cache_write, "cache_read": self.sonnet_cache_read},
            "gemini": {"input": self.gemini_input, "output": self.gemini_output},
            "gemma": {"input": self.gemma_input, "output": self.gemma_output},
            "estimated_cost_usd": round(self.estimated_cost_usd(), 4),
        }


# グローバルトラッカー
token_tracker = TokenTracker()


def _extract_json(text: str) -> Optional[Any]:
    """
    堅牢なJSON抽出（4段階フォールバック）
    1. 直接パース
    2. Markdownコードフェンス除去
    3. 正規表現で{...}/[...]ブロック検出
    4. 切り詰めJSON修復（未閉じ括弧を閉じる）
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # Strategy 1: 直接パース
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Markdownコードフェンス除去
    if text.startswith("```"):
        lines = text.split("\n")
        end = -1 if lines[-1].strip().startswith("```") else len(lines)
        stripped = "\n".join(lines[1:end])
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Strategy 3: 正規表現で最外殻の{...}または[...]を検出
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Strategy 4: MAX_TOKENSによる切り詰めJSON修復
    json_start = None
    for i, ch in enumerate(text):
        if ch in ('{', '['):
            json_start = i
            break

    if json_start is not None:
        fragment = text[json_start:]
        opens_brace = 0
        opens_bracket = 0
        in_string = False
        escape_next = False
        for ch in fragment:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                opens_brace += 1
            elif ch == '}':
                opens_brace -= 1
            elif ch == '[':
                opens_bracket += 1
            elif ch == ']':
                opens_bracket -= 1

        suffix = '"]' * 0  # 文字列中断の場合は閉じない（複雑すぎる）
        suffix = ']' * max(0, opens_bracket) + '}' * max(0, opens_brace)
        if suffix:
            try:
                repaired = fragment + suffix
                result = json.loads(repaired)
                logger.info(f"JSON truncation repair succeeded (appended {repr(suffix)})")
                return result
            except json.JSONDecodeError:
                pass

    return None


# ─── Anthropic API ────────────────────────────────────────────

_anthropic_client: Optional[anthropic.Anthropic] = None

def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(api_key=APIKeys.ANTHROPIC)
    return _anthropic_client


async def call_anthropic(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    cache_system: bool = True,
    cache_context: Optional[str] = None,
    json_mode: bool = False,
) -> dict:
    """
    Anthropic API呼び出し（Prompt Caching対応）
    
    Args:
        model: モデル名（LLMModels.OPUS or LLMModels.SONNET）
        system_prompt: システムプロンプト
        user_message: ユーザーメッセージ
        max_tokens: 最大出力トークン数
        temperature: 温度パラメータ
        cache_system: システムプロンプトをキャッシュするか
        cache_context: キャッシュする追加コンテキスト（静的部分）
        json_mode: JSON出力を期待するか
    
    Returns:
        {"content": str, "usage": dict}
    """
    client = get_anthropic_client()
    
    # システムプロンプト構築
    system = []
    if system_prompt:
        sp = {"type": "text", "text": system_prompt}
        if cache_system:
            sp["cache_control"] = {"type": "ephemeral"}
        system.append(sp)
    
    # メッセージ構築
    messages_content = []
    if cache_context:
        messages_content.append({
            "type": "text",
            "text": cache_context,
            "cache_control": {"type": "ephemeral"}
        })
    messages_content.append({"type": "text", "text": user_message})
    
    messages = [{"role": "user", "content": messages_content}]
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system if system else anthropic.NOT_GIVEN,
            messages=messages,
        )
        
        content = response.content[0].text if response.content else ""
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
        }
        
        token_tracker.record(model, usage)
        logger.info(f"[Anthropic] {model} | in={usage['input_tokens']} out={usage['output_tokens']} cache_r={usage.get('cache_read_input_tokens',0)}")
        
        # JSONモードの場合、堅牢な抽出を試みる
        if json_mode:
            parsed = _extract_json(content)
            if parsed is not None:
                return {"content": parsed, "raw": content, "usage": usage, "model": model}
            else:
                logger.warning(f"[Anthropic] JSON extraction failed (len={len(content)}). Preview: {content[:200]}")
                return {"content": content, "raw": content, "usage": usage, "model": model, "_json_failed": True}

        return {"content": content, "usage": usage, "model": model}
        
    except Exception as e:
        logger.error(f"[Anthropic] Error calling {model}: {e}")
        raise


# ─── Google AI Studio (Gemma 4) ───────────────────────────────

_gemma_configured = False

def configure_gemma():
    global _gemma_configured
    if not _gemma_configured and APIKeys.GOOGLE_AI:
        genai.configure(api_key=APIKeys.GOOGLE_AI)
        _gemma_configured = True


async def call_gemma(
    user_message: str,
    system_prompt: Optional[str] = None,
    model: str = LLMModels.GEMMA_4_MOE,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    json_mode: bool = False,
) -> dict:
    """
    Google AI Studio (Gemma 4) 呼び出し
    
    Args:
        user_message: ユーザーメッセージ
        system_prompt: システムプロンプト（省略可）
        model: モデル名
        max_tokens: 最大出力トークン数
        temperature: 温度パラメータ
        json_mode: JSON出力を期待するか
    
    Returns:
        {"content": str, "usage": dict}
    """
    configure_gemma()

    generation_config = genai.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=temperature,
    )
    
    if json_mode:
        generation_config.response_mime_type = "application/json"
    
    gmodel = genai.GenerativeModel(
        model_name=model,
        system_instruction=system_prompt if system_prompt else None,
        generation_config=generation_config,
    )
    
    try:
        response = await asyncio.to_thread(gmodel.generate_content, user_message)
        
        # finish_reason=MAX_TOKENS の場合、response.text が例外を投げる → 安全に取得
        try:
            content = response.text if response.text else ""
        except ValueError:
            # finish_reason が STOP 以外 (MAX_TOKENS=2, SAFETY=3 等) の場合
            # parts から可能な限りテキストを抽出
            content = ""
            if response.candidates and response.candidates[0].content.parts:
                content = "".join(
                    p.text for p in response.candidates[0].content.parts
                    if hasattr(p, "text") and p.text
                )
            if not content:
                finish = getattr(response.candidates[0], "finish_reason", "UNKNOWN") if response.candidates else "NO_CANDIDATES"
                logger.warning(f"[Gemma] Empty response, finish_reason={finish}. Returning empty.")
        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
        }
        
        token_tracker.record(model, usage)
        logger.info(f"[Gemma] {model} | in={usage['input_tokens']} out={usage['output_tokens']}")
        
        if json_mode:
            parsed = _extract_json(content)
            if parsed is not None:
                return {"content": parsed, "raw": content, "usage": usage, "model": model}
            else:
                logger.warning(f"[Gemini/Gemma] JSON extraction failed (model={model}, len={len(content)}). Preview: {content[:200]}")
                return {"content": content, "raw": content, "usage": usage, "model": model, "_json_failed": True}
        
        return {"content": content, "usage": usage, "model": model}
        
    except Exception as e:
        logger.error(f"[Gemma] Error calling {model}: {e}")
        raise


# ─── ユーティリティ ────────────────────────────────────────────

async def _call_llm_once(
    tier: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
    json_mode: bool,
    cache_system: bool,
    cache_context: Optional[str],
) -> dict:
    """単一LLM呼び出し（フォールバック付き）"""
    if tier in ("opus", "sonnet"):
        model_name = LLMModels.OPUS if tier == "opus" else LLMModels.SONNET
        try:
            return await call_anthropic(
                model=model_name,
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=max_tokens,
                temperature=temperature,
                cache_system=cache_system,
                cache_context=cache_context,
                json_mode=json_mode,
            )
        except Exception as e:
            logger.warning(f"[call_llm] Claude ({tier}) failed: {e}. Falling back to Gemini 2.5 Pro.")
            return await call_gemma(
                system_prompt=system_prompt,
                user_message=user_message,
                model=LLMModels.GEMINI_2_5_PRO,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=json_mode,
            )

    if tier == "gemini":
        return await call_gemma(
            system_prompt=system_prompt,
            user_message=user_message,
            model=LLMModels.GEMINI_2_5_PRO,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
        )

    if tier == "gemma":
        return await call_gemma(
            system_prompt=system_prompt,
            user_message=user_message,
            model=LLMModels.GEMMA_4_MOE,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
        )

    raise ValueError(f"Unknown tier: {tier}")


async def call_llm(
    tier: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 16384,
    temperature: float = 1.0,
    json_mode: bool = False,
    cache_system: bool = True,
    cache_context: Optional[str] = None,
) -> dict:
    """
    統一LLM呼び出しインターフェース（json_mode時は自動リトライ付き）

    Claude優先フォールバック方式:
    - tier="opus"/"sonnet" → まずClaudeを試行。失敗時にGemini 2.5 Proへ自動フォールバック。
    - tier="gemini" → Gemini 2.5 Pro直接指定。
    - tier="gemma" → Gemma 4直接指定。

    Returns:
        {"content": str or dict, "usage": dict}
    """
    max_attempts = 3 if json_mode else 1
    result = None
    temp = temperature

    for attempt in range(1, max_attempts + 1):
        result = await _call_llm_once(
            tier=tier, system_prompt=system_prompt, user_message=user_message,
            max_tokens=max_tokens, temperature=temp,
            json_mode=json_mode, cache_system=cache_system, cache_context=cache_context,
        )

        if not json_mode or not result.get("_json_failed"):
            return result

        if attempt < max_attempts:
            logger.warning(f"[call_llm] JSON parse failed (attempt {attempt}/{max_attempts}), tier={tier}. Retrying with temp={temp + 0.1:.1f}...")
            temp = min(temp + 0.1, 1.5)
        else:
            logger.error(f"[call_llm] JSON parse failed after {max_attempts} attempts. tier={tier}, raw_len={len(str(result.get('raw', '')))}")

    return result



# ─── 真の自律型エージェントループ (Agentic Execution Loop) ────────

@dataclass
class AgentTool:
    name: str
    description: str
    input_schema: dict
    handler: Callable  # (kwargs) -> str | dict


async def call_llm_agentic(
    tier: str,
    system_prompt: str,
    user_message: str,
    tools: list[AgentTool],
    max_iterations: int = 10,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Any:
    """
    Tool Callingによる自立ループを実行する
    ※ この機能は高度な推論を必要とするため Anthropic API 専用とし、Geminiへの自動フォールバックは使用しません。
    
    Args:
        tier: "opus" or "sonnet"
        system_prompt: システムプロンプト
        user_message: 最初の指示
        tools: 利用可能なツールのリスト
        max_iterations: 最大ループ回数
        
    Returns:
        最終アクションの戻り値、または最後に確定した状態など
    """
    if tier not in ("opus", "sonnet"):
        raise ValueError("Agentic loop requires Anthropic tier ('opus' or 'sonnet').")
    
    client = get_anthropic_client()
    model_name = LLMModels.OPUS if tier == "opus" else LLMModels.SONNET
    
    anthropic_tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
        }
        for t in tools
    ]
    tool_map = {t.name: t.handler for t in tools}
    
    system = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
    messages = [{"role": "user", "content": [{"type": "text", "text": user_message}]}]
    
    for i in range(max_iterations):
        logger.info(f"[call_llm_agentic] Iteration {i+1}/{max_iterations}")
        
        # DEBUG LOGGING FOR MESSAGES
        try:
            import copy
            dbg_msgs = []
            for m in messages:
                if isinstance(m.get("content"), list):
                    content_str = []
                    for c in m["content"]:
                        if hasattr(c, "model_dump"):
                            content_str.append(c.model_dump())
                        else:
                            content_str.append(c)
                    dbg_msgs.append({"role": m["role"], "content": content_str})
                else:
                    dbg_msgs.append(m)
            logger.info(f"[call_llm_agentic] SENDING MESSAGES: {json.dumps(dbg_msgs, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"Debug print failed: {e}")
            
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
            tools=anthropic_tools,
            tool_choice={"type": "any"} # ツール使用を強制
        )
        
        # トークン記録
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
        }
        token_tracker.record(model_name, usage)
        
        # Response内容を履歴に追加
        messages.append({"role": "assistant", "content": response.content})
        
        tool_use_blocks = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        
        if tool_use_blocks or response.stop_reason == "tool_use":
            tool_results = []
            for block in tool_use_blocks:
                tool_name = block.name
                tool_args = block.input
                logger.info(f"[call_llm_agentic] Tool called: {tool_name}")
                
                if tool_name in tool_map:
                    try:
                        # ツール実行 (async/sync両対応)
                        handler = tool_map[tool_name]
                        import inspect
                        if inspect.iscoroutinefunction(handler):
                            result_data = await handler(**tool_args)
                        else:
                            result_data = handler(**tool_args)
                            
                        result_str = json.dumps(result_data, ensure_ascii=False) if isinstance(result_data, (dict, list)) else str(result_data)
                        is_error = False
                    except Exception as e:
                        logger.error(f"[call_llm_agentic] Tool '{tool_name}' failed: {e}")
                        result_str = f"Error executing tool: {e}"
                        is_error = True
                else:
                    result_str = f"Error: Tool '{tool_name}' not found."
                    is_error = True
                    
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                    "is_error": is_error,
                })
            
            # ツール結果をユーザーメッセージとして追加し、ループ継続
            messages.append({"role": "user", "content": tool_results})
            
            # もし `submit_` で始まるツール（最終提出ツール）が呼ばれており、エラーでないなら、ループを正常終了させる
            if any(block.name.startswith("submit_") and not res["is_error"] for block, res in zip(tool_use_blocks, tool_results)):
                logger.info(f"[call_llm_agentic] Final submit tool called successfully. Exiting loop.")
                return final_text if 'final_text' in locals() else "Success"
        
        else:
            # any強制しているのにテキストで返ってきた場合の安全網
            final_text = next((getattr(block, "text", "") for block in response.content if getattr(block, "type", "") == "text"), "")
            logger.warning(f"[call_llm_agentic] Returned without tool_use (stop_reason={response.stop_reason}). Forcing instruction.")
            messages.append({"role": "user", "content": [{"type": "text", "text": "指示: あなたは必ず用意されたツールのいずれかを呼び出す必要があります。自然言語のみの回答は受け付けられません。最終的な回答を提出したい場合は提供された `submit_` ツールを使用してください。"}]})
    
    logger.warning("[call_llm_agentic] Hit max iterations without final resolution.")
    return next((getattr(block, "text", "") for block in messages[-1]["content"] if getattr(block, "type", "") == "text"), "")


async def call_llm_agentic_gemini(
    system_prompt: str,
    user_message: str,
    tools: list[AgentTool],
    max_iterations: int = 10,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Any:
    """
    Google Geminiを用いた自立ループの実装 (Claude版とは完全にロジックを分離)
    """
    configure_gemma()
    model_name = LLMModels.GEMINI_2_5_PRO
    
    # Tool定義の変換: JSONSchema → Gemini SDK の protos.Schema 形式
    def _jsonschema_to_gemini_schema(schema: dict) -> dict:
        """JSONSchemaをGemini SDKが受け付ける形式に変換する。
        Gemini SDKは 'type' を大文字の列挙型、未定義propertiesのobjectを嫌うため正規化する。
        """
        TYPE_MAP = {
            "string": "STRING", "integer": "INTEGER", "number": "NUMBER",
            "boolean": "BOOLEAN", "array": "ARRAY", "object": "OBJECT",
        }
        result = {}
        if "type" in schema:
            result["type_"] = TYPE_MAP.get(schema["type"], schema["type"])
        if "description" in schema:
            result["description"] = schema["description"]
        if "properties" in schema:
            result["properties"] = {
                k: _jsonschema_to_gemini_schema(v)
                for k, v in schema["properties"].items()
            }
        if "required" in schema:
            result["required"] = schema["required"]
        if "items" in schema:
            result["items"] = _jsonschema_to_gemini_schema(schema["items"])
        # Geminiは properties なしの "object" を嫌う → string にフォールバック
        if result.get("type_") == "OBJECT" and "properties" not in result:
            result["type_"] = "STRING"
            result["description"] = result.get("description", "") + " (JSON文字列として渡してください)"
        return result

    gemini_func_decls = []
    for t in tools:
        params_schema = _jsonschema_to_gemini_schema(t.input_schema)
        gemini_func_decls.append(
            genai.protos.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters=genai.protos.Schema(**params_schema) if params_schema else None,
            )
        )
    gemini_tool = genai.protos.Tool(function_declarations=gemini_func_decls)
    tool_map = {t.name: t.handler for t in tools}

    gmodel = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        tools=[gemini_tool],
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        ),
        tool_config=genai.protos.ToolConfig(
            function_calling_config=genai.protos.FunctionCallingConfig(
                mode=genai.protos.FunctionCallingConfig.Mode.ANY
            )
        ),
    )
    
    from backend.websocket.handler import manager
    
    chat = gmodel.start_chat(history=[])
    current_message = user_message
    
    for i in range(max_iterations):
        step_info = f"[Step {i+1}/{max_iterations}] リサーチと推論を行っています..."
        logger.info(f"[call_llm_agentic_gemini] {step_info}")
        if manager:
            await manager.send_agent_thought("Creative Director (Gemini)", step_info, "thinking")
        
        # タイムアウト付きでAPI呼び出し
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(chat.send_message, current_message),
                timeout=300.0
            )
        except asyncio.TimeoutError:
            error_msg = "Gemini APIの応答がタイムアウトしました(5分)。負荷が高いか、複雑すぎる指示の可能性があります。"
            logger.error(f"[call_llm_agentic_gemini] {error_msg}")
            if manager:
                await manager.send_error(error_msg)
            raise TimeoutError(error_msg)
        except Exception as e:
            # MALFORMED_FUNCTION_CALL などのSDKエラーが発生した場合のリトライ
            if "MALFORMED_FUNCTION_CALL" in str(e) or "finish_reason" in str(e):
                warn_msg = "[System] Gemini SDKのプロトコルエラーを検知しました。テキストフォールバックで自動復旧を試みます。"
                logger.warning(f"[call_llm_agentic_gemini] {warn_msg}: {e}")
                if manager:
                    await manager.send_agent_thought("System", warn_msg, "warning")
                
                # フォールバックテキストの組み立て
                if isinstance(current_message, genai.protos.Part) and current_message.function_response:
                    call_name = current_message.function_response.name
                    resp_data = current_message.function_response.response
                    fallback_text = f"【システム通知】前回のツール '{call_name}' の実行結果は以下の通りです。この情報を元に思考を継続してください:\n{json.dumps(resp_data, ensure_ascii=False, default=str)}"
                else:
                    fallback_text = "前回の指示でツール呼び出し形式エラーが発生しました。ツールを正しいJSON引数で呼び出してください。"

                # 履歴を戻してフォールバック送信（フォールバック自体が失敗してもcontinueで回復）
                try:
                    chat.history.pop()
                except (IndexError, Exception):
                    pass
                try:
                    response = await asyncio.to_thread(chat.send_message, fallback_text)
                except Exception as fallback_err:
                    logger.warning(f"[call_llm_agentic_gemini] Fallback also failed: {fallback_err}. Retrying next iteration.")
                    current_message = "ツール呼び出しで問題が発生しています。引数を単純化して再度お試しください。"
                    continue
            else:
                raise e
        
        # トークン記録
        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
        }
        token_tracker.record(model_name, usage)
        
        # finish_reason チェック (MALFORMED_FUNCTION_CALLがレスポンスとして返る場合)
        if response.candidates:
            finish_reason = getattr(response.candidates[0], 'finish_reason', None)
            finish_str = str(finish_reason) if finish_reason else ""
            if "MALFORMED" in finish_str or "MALFORMED_FUNCTION_CALL" in finish_str:
                warn_msg = f"[System] Gemini finish_reason: {finish_str}。ツール呼び出し形式を修正して再試行します。"
                logger.warning(f"[call_llm_agentic_gemini] {warn_msg}")
                if manager:
                    await manager.send_agent_thought("System", warn_msg, "warning")
                try:
                    chat.history.pop()
                except (IndexError, Exception):
                    pass
                current_message = "前回のツール呼び出しでJSON形式エラーが発生しました。引数のJSONを正しい形式で再度ツールを呼び出してください。"
                continue

        # モデルの回答確認 (安全性のチェックを追加)
        if not response.candidates or not response.candidates[0].content.parts:
            warn_msg = "[System] Geminiから有効な回答が得られませんでした（セーフティフィルター等の影響の可能性があります）。再試行します。"
            logger.warning(f"[call_llm_agentic_gemini] {warn_msg}")
            if manager:
                await manager.send_agent_thought("System", warn_msg, "warning")
            
            # 履歴を戻して再試行
            if len(chat.history) > 0:
                chat.history.pop()
            response = await asyncio.to_thread(chat.send_message, "前回の指示を、別の表現で再実行してください。")
            
            if not response.candidates or not response.candidates[0].content.parts:
                raise ValueError("Geminiから有効な回答を得られませんでした。")

        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            call = part.function_call
            tool_msg = f"ツールを実行中: {call.name} (引数: {dict(call.args) if hasattr(call.args, 'items') else call.args})"
            logger.info(f"[call_llm_agentic_gemini] {tool_msg}")
            if manager:
                await manager.send_agent_thought("Creative Director (Gemini)", tool_msg, "thinking")
            
            if call.name in tool_map:
                try:
                    handler = tool_map[call.name]
                    import inspect
                    # 引数のマッピング: MapCompositeを再帰的にプレーンなdictに変換
                    def _to_plain(obj):
                        if hasattr(obj, 'items'):
                            return {k: _to_plain(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)):
                            return [_to_plain(i) for i in obj]
                        return obj
                    args = _to_plain(call.args)
                    
                    if inspect.iscoroutinefunction(handler):
                        result_data = await handler(**args)
                    else:
                        result_data = handler(**args)
                        
                    is_error = False
                except Exception as e:
                    logger.error(f"[call_llm_agentic_gemini] Tool '{call.name}' failed: {e}")
                    result_data = {"error": str(e)}
                    is_error = True
            else:
                result_data = {"error": f"Tool '{call.name}' not found."}
                is_error = True
            
            # ツール結果を返信してループ継続 (Google SDKの内部プロトコルに準拠)
            # result_dataにMapComposite等のproto型が混入していないことを保証
            plain_result = json.loads(json.dumps(result_data, default=str))
            current_message = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=call.name,
                    response=plain_result
                )
            )
            
            # submit_ツールが成功したなら終了
            if call.name.startswith("submit_") and not is_error:
                logger.info("[call_llm_agentic_gemini] Final submit tool called successfully.")
                return "Success"
        else:
            # ツールを使用しなかった場合
            final_text = part.text
            logger.warning("[call_llm_agentic_gemini] Returned without tool_use.")
            # ツール使用を強制するためのメッセージを追加
            current_message = "指示: 用意されたツールのいずれかを呼び出してください。最終的な回答を提出したい場合は提供された `submit_` ツールを使用してください。"

    logger.warning("[call_llm_agentic_gemini] Hit max iterations.")
    return chat.history[-1].parts[0].text
