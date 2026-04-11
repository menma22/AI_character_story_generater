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

## 2026-04-11 修正: Gemini 2.5 Proフォールバック時の2つのバグ

### バグ1: 思考トークンによるmax_output_tokens枯渇
- Gemini 2.5 Proは内部で「思考トークン」を使用し、`max_output_tokens`の予算を消費する
- 例: `max_tokens=3000`の場合、思考だけで3000トークン全て消費 → 実出力が0トークン → `finish_reason=MAX_TOKENS(2)` + 空レスポンス
- **修正**: `call_gemma`でGemini 2.5 Pro検出時に`max_output_tokens`を4倍(最低16384)に自動拡張

### バグ2: system_promptの不適切な渡し方
- フォールバック時に`system_prompt`が`user_message`に文字列結合されていた
- Geminiの`system_instruction`パラメータとして渡されず、指示の分離が機能していなかった
- **修正**: `call_llm`の全tier(opus/sonnet/gemini/gemma)で`system_prompt`を`call_gemma`の`system_prompt`引数に正しく渡すよう変更

## 2026-04-11 修正: JSON解析失敗によるエピソード・イベント全滅問題

### 根本原因
1. Anthropic APIクレジット枯渇 → 全Claude呼び出しがGeminiフォールバック
2. draftプロファイルの`worker_tier="gemma"`（Gemma 4 31B）が複雑JSON出力に致命的に不安定（113回のJSONパース失敗）
3. llm_api.pyのJSONパース失敗がサイレント（生テキストを返すだけ、エラーなし）
4. Phase D Step1-4で機械的処理が不要なのにJSON出力を強制 → パース失敗 → 空データが伝播

### 修正内容
- **config.py**: draft.worker_tierを`gemma`→`gemini`に変更（Gemini 2.5 Proは無料かつJSON安定）
- **llm_api.py**: 4段階フォールバック付き`_extract_json()`ヘルパー追加、`call_llm()`にjson_mode失敗時の自動リトライ（最大3回）
- **phase_d**: Step1-4のjson_mode強制を完全撤廃。中間データは自然言語テキストで受け渡し
- **phase_a3**: Plannerを自然言語テキスト出力に変更、Writerを全エピソード一括生成に統合

### 設計原則
プロンプトコンテキストとしてのみ使用されるデータはJSON出力不要。機械的にPydanticモデルへ格納する最終出力のみjson_mode=Trueを使用。

## 設定（config.py）
- `director_tier` のデフォルト値: `"opus"`（Claude優先）
- `worker_tier` のデフォルト値: `"sonnet"`（Claude優先）
- draftプロファイル: `worker_tier="gemini"`（Gemma 4は不安定のため変更）
- Geminiモデル名: `models/gemini-2.5-pro`（**変更禁止**: ユーザー指定）
