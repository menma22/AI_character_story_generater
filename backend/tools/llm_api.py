"""
LLM API 統合ラッパー
Anthropic (Opus/Sonnet) と Google AI Studio (Gemma 4) を統一インターフェースで呼び出す。
Prompt Caching対応、トークン消費追跡付き。
"""

import json
import logging
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
        
        # JSONモードの場合、パースを試みる
        if json_mode:
            try:
                # ```json ... ``` ブロックの除去
                text = content.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
                parsed = json.loads(text)
                return {"content": parsed, "raw": content, "usage": usage, "model": model}
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed, returning raw text")
                return {"content": content, "raw": content, "usage": usage, "model": model}
        
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
        response = gmodel.generate_content(user_message)
        
        content = response.text if response.text else ""
        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
        }
        
        token_tracker.record(model, usage)
        logger.info(f"[Gemma] {model} | in={usage['input_tokens']} out={usage['output_tokens']}")
        
        if json_mode:
            try:
                text = content.strip()
                if text.startswith("```"):
                    lines = text.split("\n")
                    text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
                parsed = json.loads(text)
                return {"content": parsed, "raw": content, "usage": usage, "model": model}
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed from Gemma, returning raw text")
                return {"content": content, "raw": content, "usage": usage, "model": model}
        
        return {"content": content, "usage": usage, "model": model}
        
    except Exception as e:
        logger.error(f"[Gemma] Error calling {model}: {e}")
        raise


# ─── ユーティリティ ────────────────────────────────────────────

async def call_llm(
    tier: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    json_mode: bool = False,
    cache_system: bool = True,
    cache_context: Optional[str] = None,
) -> dict:
    """
    統一LLM呼び出しインターフェース
    
    Args:
        tier: "opus" | "sonnet" | "gemma"
        その他: 各API固有の引数
    
    Returns:
        {"content": str or dict, "usage": dict}
    """
    if tier in ("opus", "sonnet"):
        model_name = LLMModels.OPUS if tier == "opus" else LLMModels.SONNET
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
            
    if tier == "gemini":
        return await call_gemma(
            user_message=f"{system_prompt}\n\n---\n\n{user_message}" if system_prompt else user_message,
            model=LLMModels.GEMINI_2_5_PRO,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
            
    if tier == "gemma":
        return await call_gemma(
            user_message=f"{system_prompt}\n\n---\n\n{user_message}" if system_prompt else user_message,
            model=LLMModels.GEMMA_4_MOE,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    else:
        raise ValueError(f"Unknown tier: {tier}")


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
    
    # Tool定義の変換
    gemini_tools = [
        genai.types.FunctionDeclaration(
            name=t.name,
            description=t.description,
            parameters=t.input_schema,
        )
        for t in tools
    ]
    tool_map = {t.name: t.handler for t in tools}
    
    gmodel = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        tools=gemini_tools,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
    )
    
    chat = gmodel.start_chat(history=[])
    current_message = user_message
    
    for i in range(max_iterations):
        logger.info(f"[call_llm_agentic_gemini] Iteration {i+1}/{max_iterations}")
        
        response = chat.send_message(current_message)
        
        # トークン記録
        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
        }
        token_tracker.record(model_name, usage)
        
        # モデルの回答確認
        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            call = part.function_call
            logger.info(f"[call_llm_agentic_gemini] Tool called: {call.name}")
            
            if call.name in tool_map:
                try:
                    handler = tool_map[call.name]
                    import inspect
                    # 引数のマッピング (GenerativeModelの引数は辞書形式)
                    args = {k: v for k, v in call.args.items()}
                    
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
            
            # ツール結果を返信してループ継続
            current_message = genai.types.Part.from_function_response(
                name=call.name,
                response=result_data
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
            current_message = "指示: 用意されたツールのいずれかを呼び出してください。プロファイルを提出する場合は submit_concept を使用してください。"

    logger.warning("[call_llm_agentic_gemini] Hit max iterations.")
    return chat.history[-1].parts[0].text
