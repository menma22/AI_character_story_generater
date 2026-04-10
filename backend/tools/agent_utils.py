import re
import json
import logging
from typing import Type, Optional, Any
from pydantic import BaseModel, ValidationError
from backend.tools.llm_api import call_llm

logger = logging.getLogger(__name__)


def parse_markdown_sections(text: str) -> dict[str, str]:
    """
    Markdownのセクションヘッダー（## セクション名）でテキストを分割し、
    セクション名 → テキスト本体の辞書を返す。

    エージェント出力のパースに使用。JSON形式を使わず、自然言語の構造化出力を
    プログラム的に各フィールドに分配するためのユーティリティ。

    例:
        text = "## 現象的記述\n五感を使った描写...\n\n## 反射的感情反応\n胸がざわつく..."
        → {"現象的記述": "五感を使った描写...", "反射的感情反応": "胸がざわつく..."}
    """
    sections: dict[str, str] = {}
    # ## で始まるヘッダーで分割
    pattern = r"^##\s+(.+?)$"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    # parts[0] はヘッダー前のテキスト（通常空）
    # parts[1], parts[2] = セクション名, セクション本体
    # parts[3], parts[4] = 次のセクション名, 本体 ...
    i = 1
    while i < len(parts) - 1:
        section_name = parts[i].strip()
        section_body = parts[i + 1].strip()
        sections[section_name] = section_body
        i += 2

    return sections

async def run_worker_with_validation(
    worker_name: str,
    system_prompt: str,
    user_message: str,
    schema_model: Type[BaseModel],
    ws_manager=None,
    tier: str = "gemma",
    max_retries: int = 3
) -> Any:
    """
    バリデーション付きWorker呼び出し。
    エラーが発生した場合、エージェントにフィードバックを送り自己修復を促す。
    """
    current_user_message = user_message
    attempts = 0
    history = []

    while attempts < max_retries:
        attempts += 1
        if ws_manager:
            status = "実行中..." if attempts == 1 else f"自己修復中 ({attempts}/{max_retries})..."
            await ws_manager.send_agent_thought(f"Worker:{worker_name}", status, "thinking")

        # LLM呼び出し
        result = await call_llm(
            tier=tier,
            system_prompt=system_prompt,
            user_message=current_user_message,
            max_tokens=3000,
            json_mode=True,
        )
        
        data = result["content"] if isinstance(result["content"], dict) else {}
        # モデル名の取得 (モデル情報は config.py または llm_api.py の LLMModels から推測)
        actual_model = result.get("model", tier) 
        
        try:
            # バリデーション実行
            validated_data = schema_model(**data)
            
            if ws_manager:
                await ws_manager.send_agent_thought(
                    f"Worker:{worker_name}", 
                    f"完了 (試行:{attempts}) ✓", 
                    "complete",
                    model=actual_model
                )
            
            return validated_data
            
        except ValidationError as e:
            logger.warning(f"Validation failed for {worker_name} (attempt {attempts}): {e}")
            
            error_msg = str(e)
            # エージェントへのフィードバック構築
            current_user_message = (
                f"{user_message}\n\n"
                f"### 前回の出力エラー報告 ###\n"
                f"出力されたJSONでバリデーションエラーが発生しました。修正して再出力してください。\n"
                f"エラー内容:\n{error_msg}\n\n"
                f"JSONのみを正しい形式（数値型、必須フィールドの不足なし等）で出力してください。"
            )
            
            if ws_manager:
                await ws_manager.send_agent_thought(
                    f"Worker:{worker_name}", 
                    f"型エラー検知: AIへ修正を依頼中... ({attempts}/{max_retries})", 
                    "warning"
                )

        except Exception as e:
            logger.error(f"Unexpected error in {worker_name}: {e}")
            if attempts >= max_retries:
                raise
    
    # リトライ上限到達時は、最後のデータを無理やりパースするか例外を投げる
    logger.error(f"Worker {worker_name} reached max retries.")
    raise RuntimeError(f"Worker {worker_name} failed to generate valid data after {max_retries} attempts.")
