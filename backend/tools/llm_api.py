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
            self.gemma_input += input_tokens
            self.gemma_output += output_tokens
    
    def estimated_cost_usd(self) -> float:
        """推定コスト（USD）"""
        opus_cost = (self.opus_input * 15 + self.opus_output * 75) / 1_000_000
        sonnet_cost = (self.sonnet_input * 3 + self.sonnet_output * 15) / 1_000_000
        return opus_cost + sonnet_cost
    
    def summary(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "opus": {"input": self.opus_input, "output": self.opus_output,
                     "cache_write": self.opus_cache_write, "cache_read": self.opus_cache_read},
            "sonnet": {"input": self.sonnet_input, "output": self.sonnet_output,
                       "cache_write": self.sonnet_cache_write, "cache_read": self.sonnet_cache_read},
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
                return {"content": parsed, "raw": content, "usage": usage}
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed, returning raw text")
                return {"content": content, "raw": content, "usage": usage}
        
        return {"content": content, "usage": usage}
        
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
                return {"content": parsed, "raw": content, "usage": usage}
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed from Gemma, returning raw text")
                return {"content": content, "raw": content, "usage": usage}
        
        return {"content": content, "usage": usage}
        
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
    if tier == "opus":
        return await call_anthropic(
            model=LLMModels.OPUS,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            cache_system=cache_system,
            cache_context=cache_context,
            json_mode=json_mode,
        )
    elif tier == "sonnet":
        return await call_anthropic(
            model=LLMModels.SONNET,
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=temperature,
            cache_system=cache_system,
            cache_context=cache_context,
            json_mode=json_mode,
        )
    elif tier == "gemma":
        return await call_gemma(
            user_message=f"{system_prompt}\n\n---\n\n{user_message}" if system_prompt else user_message,
            model=LLMModels.GEMMA_4_MOE,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    else:
        raise ValueError(f"Unknown tier: {tier}")
