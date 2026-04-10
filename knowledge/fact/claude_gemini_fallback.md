# Claude→Geminiフォールバック機構の実装事実

## 概要
Claude APIを優先し、APIが利用不可の場合にのみGemini 2.5 Proへ自動フォールバックする仕組みを実装した。

## フォールバックの動作箇所

### 1. call_llm（単発LLM呼び出し）
- `tier="opus"` または `"sonnet"` が指定された場合、まず `call_anthropic` を試行する。
- `call_anthropic` が例外をスローした場合のみ、`call_gemma(model=GEMINI_2_5_PRO)` にフォールバックする。
- `call_anthropic` の内部ロジックには一切手を加えていない。

### 2. エージェンティックループ（CreativeDirector, DailyLoop）
- `call_llm_agentic`（Claude専用）を試行し、例外時に `call_llm_agentic_gemini` にフォールバックする。
- `call_llm_agentic` および `call_llm_agentic_gemini` のコード自体は独立しており、フォールバック処理はオーケストレーター側で行われる。

## 動作確認結果
- Claude API利用不可の状態でテストし、正しくGemini 2.5 Proにフォールバックされることをログで確認した。
- Gemini 2.5 Pro側のクォータ制限（429エラー）が発生しているが、これはプログラムのバグではなくAPIプランの制限。

## 設定（config.py）
- `director_tier` のデフォルト値: `"opus"`（Claude優先）
- `worker_tier` のデフォルト値: `"sonnet"`（Claude優先）
- Geminiモデル名: `models/gemini-2.5-pro`（**変更禁止**: ユーザー指定）
