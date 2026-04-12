"""
LLM API 統合ラッパー
Anthropic (Opus/Sonnet) と Google AI Studio (Gemini 3.1 Pro/2.5 Pro/2.0 Flash) を統一インターフェースで呼び出す。
Prompt Caching対応、トークン消費追跡付き。
フォールバック：Opus (Gemini 3.1 Pro), Sonnet (Gemini 2.5 Pro), Gemini (Gemini 2.5 Pro)
"""

import asyncio
import json
import logging
import re
from typing import Any, Optional, Callable

import anthropic
import google.generativeai as genai
from dataclasses import dataclass

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
        else:
            self.gemini_input += input_tokens
            self.gemini_output += output_tokens
    
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
            "estimated_cost_usd": round(self.estimated_cost_usd(), 4),
        }

    def snapshot(self) -> dict:
        """現在の累計値のコピーを返す（スナップショット用）"""
        return {
            "opus_input": self.opus_input,
            "opus_output": self.opus_output,
            "opus_cache_write": self.opus_cache_write,
            "opus_cache_read": self.opus_cache_read,
            "sonnet_input": self.sonnet_input,
            "sonnet_output": self.sonnet_output,
            "sonnet_cache_write": self.sonnet_cache_write,
            "sonnet_cache_read": self.sonnet_cache_read,
            "gemini_input": self.gemini_input,
            "gemini_output": self.gemini_output,
            "total_calls": self.total_calls,
        }

    def cost_since(self, snap: dict, label: str) -> dict:
        """スナップショット以降の差分コストを計算して返す"""
        di = self.opus_input - snap.get("opus_input", 0)
        do = self.opus_output - snap.get("opus_output", 0)
        si = self.sonnet_input - snap.get("sonnet_input", 0)
        so = self.sonnet_output - snap.get("sonnet_output", 0)
        gi = self.gemini_input - snap.get("gemini_input", 0)
        go = self.gemini_output - snap.get("gemini_output", 0)

        opus_cost = (di * 15 + do * 75) / 1_000_000
        sonnet_cost = (si * 3 + so * 15) / 1_000_000
        gemini_cost = (gi * 1.25 + go * 3.75) / 1_000_000
        total_cost = opus_cost + sonnet_cost + gemini_cost

        return {
            "label": label,
            "input_tokens": di + si + gi,
            "output_tokens": do + so + go,
            "cost_usd": round(total_cost, 6),
            "detail": {
                "opus": {"input": di, "output": do},
                "sonnet": {"input": si, "output": so},
                "gemini": {"input": gi, "output": go},
            },
        }


# グローバルトラッカー
token_tracker = TokenTracker()


def _extract_json(text: str) -> Optional[Any]:
    """堅牢なJSON抽出"""
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

    # Strategy 3: 正規表現で検出
    for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Strategy 4: 切り詰めJSON修復
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

def get_anthropic_client(api_key: Optional[str] = None) -> anthropic.Anthropic:
    """ Anthropicクライアントを取得する。 """
    key = api_key or APIKeys.ANTHROPIC
    return anthropic.Anthropic(api_key=key)


async def call_anthropic(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    cache_system: bool = True,
    cache_context: Optional[str] = None,
    json_mode: bool = False,
    api_key: Optional[str] = None,
) -> dict:
    """ Anthropic API呼び出し（Prompt Caching対応） """
    client = get_anthropic_client(api_key=api_key)
    
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


# ─── Google AI Studio (Gemini 3.1 Pro / 2.5 Pro) ────────────────────────

def configure_google_ai(api_key: Optional[str] = None):
    """Google AI SDKを構成。"""
    key = api_key or APIKeys.GOOGLE_AI
    if key:
        genai.configure(api_key=key)


async def call_google_ai(
    user_message: str,
    system_prompt: Optional[str] = None,
    model: str = LLMModels.GEMINI_2_5_PRO,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    json_mode: bool = False,
    api_key: Optional[str] = None,
) -> dict:
    """ Google AI Studio (Gemini 3.1 Pro / 2.5 Pro / 2.0 Flash) 呼び出し """
    configure_google_ai(api_key=api_key)

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
        
        try:
            content = response.text if response.text else ""
        except ValueError:
            content = ""
            if response.candidates and response.candidates[0].content.parts:
                content = "".join(
                    p.text for p in response.candidates[0].content.parts
                    if hasattr(p, "text") and p.text
                )
            if not content:
                finish = getattr(response.candidates[0], "finish_reason", "UNKNOWN") if response.candidates else "NO_CANDIDATES"
                logger.warning(f"[Google AI] Empty response, finish_reason={finish}. Returning empty.")

        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
        }
        
        token_tracker.record(model, usage)
        logger.info(f"[Google AI] {model} | in={usage['input_tokens']} out={usage['output_tokens']}")
        
        if json_mode:
            parsed = _extract_json(content)
            if parsed is not None:
                return {"content": parsed, "raw": content, "usage": usage, "model": model}
            else:
                logger.warning(f"[Google AI] JSON extraction failed (model={model}, len={len(content)}). Preview: {content[:200]}")
                return {"content": content, "raw": content, "usage": usage, "model": model, "_json_failed": True}
        
        return {"content": content, "usage": usage, "model": model}
        
    except Exception as e:
        logger.error(f"[Google AI] Error calling {model}: {e}")
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
    api_keys: Optional[dict] = None,
) -> dict:
    """単一LLM呼び出し（フォールバック付き）"""
    def _is_quota_error(e: Exception) -> bool:
        return (
            "ResourceExhausted" in type(e).__name__
            or "429" in str(e)
            or "quota" in str(e).lower()
        )

    async def _call_gemini_with_flash_fallback(
        system_prompt: str,
        user_message: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
    ) -> dict:
        if gemini_model is None:
            gemini_model = LLMModels.GEMINI_2_5_PRO
        try:
            return await call_google_ai(
                system_prompt=system_prompt,
                user_message=user_message,
                model=gemini_model,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=json_mode,
                api_key=api_key,
            )
        except Exception as e:
            if _is_quota_error(e):
                logger.warning(f"[call_llm] {gemini_model} quota exceeded. Falling back to Gemini 2.0 Flash.")
                return await call_google_ai(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    model=LLMModels.GEMINI_2_0_FLASH,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    json_mode=json_mode,
                    api_key=api_key,
                )
            raise

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
                api_key=api_keys.get("anthropic") if api_keys else None,
            )
        except Exception as e:
            logger.warning(f"[call_llm] Claude ({tier}) failed: {e}. Falling back to Gemini.")
            gemini_model = LLMModels.GEMINI_3_1_PRO if tier == "opus" else None
            return await _call_gemini_with_flash_fallback(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=max_tokens,
                temperature=temperature,
                json_mode=json_mode,
                api_key=api_keys.get("google_ai") if api_keys else None,
                gemini_model=gemini_model,
            )

    if tier == "gemini":
        return await _call_gemini_with_flash_fallback(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
            api_key=api_keys.get("google_ai") if api_keys else None,
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
    api_keys: Optional[dict] = None,
) -> dict:
    """ 統一LLM呼び出しインターフェース """
    max_attempts = 3 if json_mode else 1
    result = None
    temp = temperature

    for attempt in range(1, max_attempts + 1):
        result = await _call_llm_once(
            tier=tier, system_prompt=system_prompt, user_message=user_message,
            max_tokens=max_tokens, temperature=temp,
            json_mode=json_mode, cache_system=cache_system, cache_context=cache_context,
            api_keys=api_keys,
        )

        if not json_mode or not result.get("_json_failed"):
            return result

        if attempt < max_attempts:
            logger.warning(f"[call_llm] JSON parse failed (attempt {attempt}/{max_attempts}), tier={tier}. Retrying with temp={temp + 0.1:.1f}...")
            temp = min(temp + 0.1, 1.5)
        else:
            logger.error(f"[call_llm] JSON parse failed after {max_attempts} attempts.")

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
    api_keys: Optional[dict] = None,
) -> Any:
    """ Tool Callingによる自立ループを実行する """
    if tier not in ("opus", "sonnet"):
        raise ValueError("Agentic loop requires Anthropic tier ('opus' or 'sonnet').")
    
    client = get_anthropic_client(api_key=api_keys.get("anthropic") if api_keys else None)
    model_name = LLMModels.OPUS if tier == "opus" else LLMModels.SONNET
    
    anthropic_tools = [
        { "name": t.name, "description": t.description, "input_schema": t.input_schema }
        for t in tools
    ]
    tool_map = {t.name: t.handler for t in tools}
    
    system = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
    messages = [{"role": "user", "content": [{"type": "text", "text": user_message}]}]
    
    for i in range(max_iterations):
        logger.info(f"[call_llm_agentic] Iteration {i+1}/{max_iterations}")
        
        response = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
            tools=anthropic_tools,
            tool_choice={"type": "any"}
        )
        
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
        }
        token_tracker.record(model_name, usage)
        
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
            
            messages.append({"role": "user", "content": tool_results})
            
            if any(block.name.startswith("submit_") and not res["is_error"] for block, res in zip(tool_use_blocks, tool_results)):
                logger.info(f"[call_llm_agentic] Final submit tool called successfully. Exiting loop.")
                return "Success"
        else:
            final_text = next((getattr(block, "text", "") for block in response.content if getattr(block, "type", "") == "text"), "")
            logger.warning("[call_llm_agentic] Returned without tool_use.")
            messages.append({"role": "user", "content": [{"type": "text", "text": "指示: 用意されたツールのいずれかを呼び出してください。"}]})
    
    return next((getattr(block, "text", "") for block in messages[-1]["content"] if getattr(block, "type", "") == "text"), "")


async def call_llm_agentic_gemini(
    system_prompt: str,
    user_message: str,
    tools: list[AgentTool],
    max_iterations: int = 10,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    api_keys: Optional[dict] = None,
) -> Any:
    """ Google Geminiを用いた自立ループの実装 """
    configure_google_ai(api_key=api_keys.get("google_ai") if api_keys else None)
    model_name = LLMModels.GEMINI_2_5_PRO
    
    def _jsonschema_to_gemini_schema(schema: dict) -> dict:
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
        
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(chat.send_message, current_message),
                timeout=300.0
            )
        except Exception as e:
            if "MALFORMED_FUNCTION_CALL" in str(e) or "finish_reason" in str(e):
                fallback_text = "前回の指示でツール呼び出し形式エラーが発生しました。正しいJSON形式で再度ツールを呼び出してください。"
                try: chat.history.pop()
                except: pass
                response = await asyncio.to_thread(chat.send_message, fallback_text)
            else:
                raise e
        
        usage = {
            "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
            "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
        }
        token_tracker.record(model_name, usage)
        
        if not response.candidates or not response.candidates[0].content.parts:
            raise ValueError("Geminiから有効な回答を得られませんでした。")

        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            call = part.function_call
            if call.name in tool_map:
                try:
                    handler = tool_map[call.name]
                    import inspect
                    def _to_plain(obj):
                        if hasattr(obj, 'items'): return {k: _to_plain(v) for k, v in obj.items()}
                        elif isinstance(obj, (list, tuple)): return [_to_plain(i) for i in obj]
                        return obj
                    args = _to_plain(call.args)
                    result_data = await handler(**args) if inspect.iscoroutinefunction(handler) else handler(**args)
                    is_error = False
                except Exception as e:
                    result_data = {"error": str(e)}; is_error = True
            else:
                result_data = {"error": "Not Found"}; is_error = True
            
            plain_result = json.loads(json.dumps(result_data, default=str))
            current_message = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(name=call.name, response=plain_result)
            )
            
            if call.name.startswith("submit_") and not is_error:
                return "Success"
        else:
            current_message = "指示: 用意されたツールのいずれかを呼び出してください。"

    return chat.history[-1].parts[0].text
