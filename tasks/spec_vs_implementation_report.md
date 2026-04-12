# 仕様書 vs 実装コード 差分分析レポート

**作成日**: 2026-04-12  
**対象仕様書**: `specification_v10.md` (v10), `script_ai_app_specification_v2.md` (v2)  
**対象実装**: `backend/` 以下の全ソースコード  
**参照**: `PROJECT.md` (Stage 1〜32の実装履歴)

---

## 目次

1. [カテゴリA: 仕様から意図的に変更された箇所](#カテゴリa-仕様から意図的に変更された箇所)
2. [カテゴリB: 仕様に存在しない追加機能](#カテゴリb-仕様に存在しない追加機能)
3. [カテゴリC: 仕様に存在するが未実装の機能](#カテゴリc-仕様に存在するが未実装の機能)
4. [カテゴリD: 仕様と実装の数値・定数の相違](#カテゴリd-仕様と実装の数値定数の相違)
5. [仕様書加筆計画](#仕様書加筆計画)

---

## カテゴリA: 仕様から意図的に変更された箇所

### A-1. 感情強度による理性ブランチのバイパス（v10違反・要仕様書明記）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v10 §4.6: 「Strong emotion ≠ skip reflective. Strong emotion = **lower reflective weight** (still runs, less influential). Keep structure continuous (no if-branch)」 |
| **実装の動作** | `daily_loop/orchestrator.py:651-680, 1716-1720`: `_evaluate_emotion_intensity()` で感情強度を判定。`intensity == "high"` の場合、Reflective Agentを**完全にスキップ**し、空の `ReflectiveOutput()` を生成。Integration Agentに「理性ブランチの報告はありません」と通知。 |
| **影響範囲** | Daily Loop内の全イベント処理。高感情強度時にReflective出力がゼロになり、Integration Agentが衝動ブランチのみで行動決定を行う。 |
| **修正が必要なファイル** | `backend/agents/daily_loop/orchestrator.py` |
| **仕様書への反映方針** | v10の「weight reduction, not skip」原則を維持するか、実装側の「バイパス」を正式採用するか判断が必要。**どちらを採用するにしても、仕様書と実装を一致させる必要がある。** |

### A-2. Perceiver + Impulsive Agentの統合（v10構造変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v10 §4.3: Perceiver Agent は独立エージェント。3要素（現象学的記述、反射的情動、自動的注意）を出力。§4.6 Step 1: Impulsive Agent は別エージェント。 |
| **実装の動作** | Stage 9で統合。Perceiver機能をImpulsive Agentに組み込み、冗長なPerceiver呼び出しを削除。`daily_loop/orchestrator.py` 内で `_impulsive()` メソッドがPerceiver的出力も含めて一括生成。 |
| **影響範囲** | エージェント分離原則の変更。v10のエージェント一覧表（§4.3, §4.6 Step 1）と不一致。 |
| **仕様書への反映方針** | 統合は合理的（コスト削減・冗長性除去）。v10 §4.3のPerceiver独立セクションを「Impulsive Agentに統合」と明記。出力要素（3要素）は維持されていることを確認。 |

### A-3. VoiceFingerprint → LinguisticExpression リファクタ（v10/v2構造変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v10 §A-1: `voice_fingerprint` はMacroProfile内のフィールド。v2 §6.3: `VoiceWorker` がPhase A-1 Step 2で動作。 |
| **実装の動作** | Stage 13で大幅リファクタ。`VoiceFingerprint` → 2層構造に分離: (1) `SpeechCharacteristics`（具体的特徴 + 抽象的雰囲気 + 会話スタイル + 感情表現傾向）、(2) `DiaryWritingAtmosphere`（トーン + 構造 + 内省深度 + 書かれるもの/省かれるもの + 生の雰囲気記述）。`LinguisticExpression` として独立モデル化し、Phase A-1のStep 5（最後）で生成。日記生成時のみ注入。 |
| **影響範囲** | Phase A-1のWorker構成変更（VoiceWorker → LinguisticExpressionWorker、依存グラフ末端に移動）。MacroProfileからvoice_fingerprintを分離。日記生成・検証パイプライン全体に影響。 |
| **修正が必要なファイル** | `backend/models/character.py`, `backend/agents/phase_a1/orchestrator.py` |
| **仕様書への反映方針** | v10 §A-1のvoice_fingerprint定義を `LinguisticExpression` に置換。Phase A-1のWorker一覧と依存グラフを更新。日記生成§4.8のプロンプト構造にLinguisticExpression注入を明記。 |

### A-4. Phase A-2 Worker分割の変更（v2構成変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v2 §6.4: 14 Worker（10パラメータWorker + 4規範層Worker）。各Workerの担当パラメータ群はv2 §6.4.2で明記。 |
| **実装の動作** | Stage 4-9で15分割に変更: 10パラメータWorker + 4規範層Worker + 1認知導出Worker（Python計算）。Worker名称は同一だが、一部の分割境界が微調整されている（例: SocialCognitionWorkerが独立）。 |
| **影響範囲** | Phase A-2の実行フロー。Worker間の依存関係。 |
| **仕様書への反映方針** | v2 §6.4のWorker一覧表を実装に合わせて更新（15 Worker）。CognitiveDerivation Workerの計算式はv10と一致しているため問題なし。 |

### A-5. Phase A-3のエージェンティック化（v2構成変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v2 §6.5: カテゴリ別Writer 8個（RedemptionWriter, ContaminationWriter等）+ EpisodePlanner + BiasAuditor。各カテゴリに専用Writerを配置。 |
| **実装の動作** | Stage 14でエージェンティック化。カテゴリ別Writerを廃止し、単一のエージェンティックループ（draft → request_critique → self_reflect → submit）で全エピソードを一括生成。フォールバック: エージェントループ失敗時は2ステップ簡略版。 |
| **影響範囲** | Phase A-3の実行フロー全体。カテゴリ制約（redemption ≤ 2, contamination ≥ 1等）はプロンプト内で維持。 |
| **仕様書への反映方針** | v2 §6.5のWriter一覧を「単一エージェンティックループ」に置換。カテゴリ制約はプロンプト制約として記述。BiasAuditorはEvaluatorパイプラインに残留。 |

### A-6. 日次ループの実行順序変更（v10フロー変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v10 §4.7-§4.9: 内省(§4.7) → 日記生成(§4.8) → 日記検証(§4.9.1) → ムード更新(§4.9.2) → key memory抽出(§4.9.3.1) → メモリ圧縮(§4.9.3.2) → 翌日予定(§4.9.4) → DB更新(§4.9.5) |
| **実装の動作** | Stage 19で変更: 内省 → **翌日予定（§4.9.4を前倒し）** → 日記生成 → 日記Self-Critic → ムード更新 → key memory抽出 → デイリーログ保存&要約 → DB更新 |
| **変更理由** | 翌日予定を日記の前に移動することで、日記が「明日はこうしよう」という意図を自然に含めるようになる。 |
| **仕様書への反映方針** | v10 §4.9.4の実行位置を§4.7と§4.8の間に移動。理由を設計決定として明記。 |

### A-7. Gemma 4完全廃止 → Gemini統一（v2技術スタック変更）

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v2 §12: Worker層のモデルとして「Gemma 4 26B MoE」「Gemma 4 31B Dense」を指定。Phase A-1/A-2/A-3のWorkerは全てGemma 4。 |
| **実装の動作** | Stage 11でGemma 4を完全廃止。3層モデルティアに統一: (1) opus = Claude Opus 4.6、(2) sonnet = Claude Sonnet 4.6、(3) gemini = Gemini 2.5 Pro（フォールバック: Gemini 2.0 Flash）。Worker層は全て `tier="gemini"` で動作。 |
| **影響範囲** | 全Worker呼び出し。コスト構造。フォールバックチェーン。 |
| **仕様書への反映方針** | v2 §12の技術スタック表を全面改訂。モデル選定理由（Gemma 4のパフォーマンス不足？可用性問題？）を明記。コスト見積もり（v2 §14）を更新。 |

### A-8. エージェント間データ受渡しのJSON → 自然言語変更

| 項目 | 内容 |
|------|------|
| **仕様書の記述** | v2 §7.2: Worker出力は「Structured JSON output (Gemma native JSON output mode)」。v2 §9: 全データ構造がJSON形式。 |
| **実装の動作** | Stage 6-9で段階的に変更。Phase A-3/D のWorker間受渡しをJSON→自然言語Markdownに切替。Phase Dの WorldContext/SupportingCharacters/NarrativeArc/ConflictIntensity はテキスト出力。最終的なPydanticモデルへのパースはオーケストレータが担当。 |
| **変更理由** | エージェント間の中間段階ではJSONパースの失敗リスクを排除し、LLMの自然な表現力を活かす。JSONはシステムパース用のみ。 |
| **仕様書への反映方針** | v2 §7の出力形式を「中間: 自然言語テキスト、最終: JSON/Pydantic」に更新。Phase D各Workerの出力形式を明記。 |

---

## カテゴリB: 仕様に存在しない追加機能

### B-1. CharacterCapabilities（所持品・能力・可能行動）

| 項目 | 内容 |
|------|------|
| **仕様書** | v10/v2のどちらにも記述なし |
| **実装** | Stage 27-28, 31で追加。4モデル: `PossessedItem`, `CharacterAbility`, `AvailableAction`, `CharacterCapabilities`。Phase Dで `CharacterCapabilitiesAgent`（エージェンティック・Web検索2回以上→draft→critique→self_reflect→submit）。Creative Directorにも `capabilities_hints` を追加。Integration Agent・日記生成に `wrap_context` で注入。 |
| **該当ファイル** | `backend/agents/phase_d/capabilities_agent.py`, `backend/models/character.py` |
| **仕様書への反映方針** | v10 Phase Dに§を新設。v2 §6.6のWorker一覧に追加。CharacterPackageのスキーマ定義に追加。 |

### B-2. 3段階日記ゲート（Diary Critic + LinguisticValidator + ThirdPartyReviewer）

| 項目 | 内容 |
|------|------|
| **仕様書** | v10 §4.9.1: 日記検証は単一の「Diary Check AI」。v2には日記検証の詳細記述なし（Day 0フェーズのみ）。 |
| **実装** | Stage 16-18, 22で段階的に構築。3段階ゲート: (1) `DiarySelfCritic`（ルール検証 + AI臭チェック）、(2) `LinguisticExpressionValidator`（10項目の言語的表現検証）、(3) `ThirdPartyReviewer`（5点評価: 理解可能性・娯楽性・一貫性・自然さ・イベント整合性）。 |
| **該当ファイル** | `backend/agents/daily_loop/diary_critic.py`, `backend/agents/daily_loop/linguistic_validator.py`, `backend/agents/daily_loop/third_party_reviewer.py` |
| **仕様書への反映方針** | v10 §4.9.1を拡張し、3段階ゲートの詳細（各段階の検証項目・通過条件・失敗時のリトライロジック）を明記。 |

### B-3. 4並列チェッカー（Profile/Temperament/Personality/Values）

| 項目 | 内容 |
|------|------|
| **仕様書** | v10 §4.6b: 出力検証はPerceiver + Impulsive出力のみ対象。Integration出力の4軸チェックは記述なし。 |
| **実装** | Stage 8で追加。`ProfileChecker`, `TemperamentChecker`, `PersonalityChecker`, `ValuesChecker` の4つを並列実行。Integration Agent出力をプロフィール・気質・性格・価値観の4軸で検証。 |
| **該当ファイル** | `backend/agents/daily_loop/checkers.py` |
| **仕様書への反映方針** | v10 §4.6bを拡張するか、新たに§4.6eを新設して4並列チェッカーの仕様を追加。 |

### B-4. wrap_context()ユーティリティ（コンテキスト説明注入）

| 項目 | 内容 |
|------|------|
| **仕様書** | v10/v2のどちらにも記述なし |
| **実装** | Stage 18で追加。`context_descriptions.py` に30+のコンテキスト型について what/why/how の説明を定義。全エージェントのプロンプトでコンテキストブロックに説明を自動付与。 |
| **該当ファイル** | `backend/agents/context_descriptions.py` |
| **仕様書への反映方針** | v2の設計原則セクション（§2）に「コンテキスト説明注入パターン」として追記。各エージェントのプロンプト構造に反映。 |

### B-5. アーティファクトレベル再生成（Regeneration Module）

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §5.4: Co-Editモードでの編集リクエストワークフローは記述あるが、アーティファクト単位の再生成モジュールは未定義。 |
| **実装** | Stage 15で追加。`regeneration.py`: アーティファクト→フェーズマッピング、依存グラフ、再生成コア。Master Orchestratorをバイパスして直接Phase Orchestratorを呼び出し。`regeneration_context`（元アーティファクト + ユーザー指示）をプロンプトに注入。UI側にも再生成/編集モーダルを実装。 |
| **該当ファイル** | `backend/regeneration.py` |
| **仕様書への反映方針** | v2 §5にRegenerationモジュールのセクションを新設。アーティファクト依存グラフ・再生成フロー・UIインタラクションを明記。 |

### B-6. デイリーログストア（DailyLogStore + LLM圧縮）

| 項目 | 内容 |
|------|------|
| **仕様書** | v10 §4.9.3.2: ステージ圧縮の概念は存在するが、日別フォルダ管理・バージョニング（001_full, 002_summary, 003_summary）の詳細は未定義。LLM圧縮（文字列切り詰めではなくセマンティック重要度保持）も未記述。 |
| **実装** | Stage 19で実装。`DailyLogStore` クラス: 日別フォルダ構造、バージョン管理、LLMによる段階的圧縮。日記とは独立したDBとして分離（参照用途指定）。 |
| **該当ファイル** | `backend/agents/daily_loop/orchestrator.py:223-299` |
| **仕様書への反映方針** | v10 §4.9.3.2の圧縮テーブルを拡張し、DailyLogStoreのフォルダ構造・バージョニング・LLM圧縮の手順を明記。 |

### B-7. デュアルチェックポイント保存 + レジューム

| 項目 | 内容 |
|------|------|
| **仕様書** | v10/v2にチェックポイント・レジュームの記述なし |
| **実装** | Stage 20で追加。SIDフォルダ（常時）+ キャラクター名フォルダ（名前判明後）の双方向保存。DailyLoop完了ごとにpackage.jsonのprotagonist_planイベントを更新。日記生成完了時に最終package.json状態を書き込み。 |
| **該当ファイル** | `backend/storage/md_storage.py`, `backend/agents/master_orchestrator/orchestrator.py` |
| **仕様書への反映方針** | v2に「チェックポイント・レジューム設計」セクションを新設。 |

### B-8. 動的APIキーシステム

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §12: `.env` でAPI鍵管理。動的切替の記述なし。 |
| **実装** | Stage 25で追加。フロントエンドlocalStorage → WebSocket → バックエンド全層（Master/Daily/Worker/call_llm）に `api_keys` パラメータを伝播。提供されたキーが環境変数より優先。UIにモーダル設定画面。 |
| **該当ファイル** | `backend/tools/llm_api.py`, `backend/main.py`, フロントエンド |
| **仕様書への反映方針** | v2 §12にAPIキー管理の動的切替セクションを追加。 |

### B-9. トークンコスト記録（Per-Step）

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §14: 全体コスト見積もりはあるが、ステップ毎の記録機能は未定義。 |
| **実装** | Stage 23で追加。`TokenTracker.snapshot()`, `cost_since()`。`DayProcessingState.cost_records` にステップ毎のコストエントリ。Daily_logs/Day_N.md にコスト表を出力。 |
| **該当ファイル** | `backend/tools/llm_api.py` |
| **仕様書への反映方針** | v2 §14にPer-Stepコスト記録の仕組みを追記。 |

### B-10. Gemini多段フォールバック

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §12: Opus/Sonnet/Gemma 4 の3層。フォールバック未定義。 |
| **実装** | Stage 21, 24で構築。階層: Opus失敗 → Gemini 3.1 Pro、Sonnet失敗 → Gemini 2.5 Pro、Gemini 2.5 Proクォータ超過 → Gemini 2.0 Flash。クォータエラー(429/ResourceExhausted)のみ条件分岐。 |
| **該当ファイル** | `backend/tools/llm_api.py` |
| **仕様書への反映方針** | v2 §12にフォールバックカスケード図を追加。各層の条件・対象エラーを明記。 |

### B-11. Creative Directorの自己内省（self_reflect）ツール追加

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §4.6: ツールは `web_search`, `file_read`, `master_orchestrator_dispatch`, `request_regeneration`, `self_critique` の5つ。`self_reflect` は未記述。 |
| **実装** | Stage 3, 14で追加。Creative DirectorにWeb検索最低回数保証（プロフィールに応じて5/3/2/1回）と `self_reflect`（内的確信チェックポイント）を追加。2層自己批評: 外部批評 + 内部内省の両方通過が必要。 |
| **該当ファイル** | `backend/agents/creative_director/director.py` |
| **仕様書への反映方針** | v2 §4.6のツール一覧に `self_reflect` を追加。Web検索最低回数保証ルールを追記。 |

---

## カテゴリC: 仕様に存在するが未実装の機能

### C-1. Phase B: エコーチャンバー構築

| 項目 | 内容 |
|------|------|
| **仕様書** | v10 §Phase B: はてなブックマーク/note/はてなブログからの好奇心駆動クローリング。Pathak 2017に基づくCuriosity-Driven Crawling。5イテレーション。出力: Emotional Knowledge DB。 |
| **実装** | 未実装。コード内に対応するモジュール・クラスなし。 |
| **優先度** | v10で「Lightweight」と記述されている。現在の実装ではDaily Loop内でEmotional Knowledge DBを参照するコードもないため、影響は限定的。 |

### C-2. Phase C: 擬似経験構築

| 項目 | 内容 |
|------|------|
| **仕様書** | v10: 「RESERVED (not implemented in v10, conceptual only)」 |
| **実装** | 未実装（仕様通り）。 |
| **優先度** | 低。仕様でも概念のみ。 |

### C-3. Co-Editモード（v2 §3.4, §10.2）

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §3.4: ユーザーとMaster Orchestratorの対話。セクション単位の再生成。自然言語編集リクエスト→影響スコープ判定→部分再生成→差分表示→承認。 |
| **実装** | 未実装。PROJECT.mdで「Stage 4 (UX: Collaborative Mode): Not yet implemented」と記録。ただし、アーティファクト再生成（B-5）により部分的な機能は実現。 |
| **優先度** | 中。再生成モジュールで基本機能はカバーされているが、対話型ワークフローは未対応。 |

### C-4. ディスク保存構造の一部（v2 §9.2）

| 項目 | 内容 |
|------|------|
| **仕様書** | v2 §9.2: `concept.md`, `macro_profile.md`, `parameters.csv`, `episodes/ep_001.md`〜, `weekly_events_store.md`, `narrative_arc.md`, `audit_report.md` の個別ファイル生成。 |
| **実装** | `package.json`, `checkpoint.json`, `agent_logs.json/md`, key_memories/short_term_memory/mood_states/diariesは実装済み。しかし `parameters.csv`, `episodes/` フォルダ分割, `narrative_arc.md` 個別出力は未実装。 |
| **優先度** | 低。主要データはpackage.jsonに包含されている。 |

### C-5. Emotional Knowledge DB参照

| 項目 | 内容 |
|------|------|
| **仕様書** | v10 §5（データベース構造）: Emotional Knowledge DBを5ファイルシステムの一つとして定義。Phase B由来、内省で増分追加。 |
| **実装** | Phase B未実装のため、Emotional Knowledge DB自体が存在しない。Daily Loopのプロンプトにも参照コードなし。 |
| **優先度** | Phase B実装まで保留。 |

---

## カテゴリD: 仕様と実装の数値・定数の相違

### D-1. イベント数/日

| 項目 | v10仕様 | v2仕様 | 実装 |
|------|---------|--------|------|
| **1日あたりイベント数** | 4-6件 | 4-6件 | **2-4件**（Stage 12で変更） |
| **7日間合計** | 28-42件 | 28-42件 | **14-28件** |
| **変更理由** | — | — | トークンコスト最適化、品質安定化 |

### D-2. 周囲キャラクター数

| 項目 | v2仕様 | 実装 |
|------|--------|------|
| **SupportingCharactersWorker** | 5-7人 | **3-6人** |

### D-3. 日記の長さ

| 項目 | v10仕様 | 実装 |
|------|---------|------|
| **日記の文字数** | 明示的な規定なし（300-500chars typical for narrative） | **〜400語に標準化**（Stage 12） |

### D-4. Phase A-1 Worker構成

| 項目 | v2仕様 | 実装 |
|------|--------|------|
| **Worker数** | 8個 | **9個**（LinguisticExpressionWorker追加） |
| **依存グラフ** | BasicInfo → (Family/Lifestyle/Dream/Voice/ValuesCore) → Secret → RelationshipNetwork | BasicInfo → (Family/Lifestyle/Dream/ValuesCore) → Secret → RelationshipNetwork → **LinguisticExpression** |

### D-5. Phase D Worker構成

| 項目 | v2仕様 | 実装 |
|------|--------|------|
| **Worker数** | 8個（WorldContext, SupportingChars, NarrativeArc, ConflictIntensity, WeeklyEventWriter, EventMetadataAuditor, DistributionValidator, NarrativeConnectionAuditor） | **6 Worker + Evaluator分離**（WorldContext, SupportingChars, **CharacterCapabilitiesAgent**, NarrativeArc, ConflictIntensity, WeeklyEventWriter）。Evaluatorはパイプライン側に統合。 |

### D-6. Quality Profile定義

| 項目 | v2仕様 | 実装 |
|------|--------|------|
| **Director Tier (high_quality)** | Opus | **Opus** ✓ |
| **Worker Tier (high_quality)** | Gemma 4 26B | **Sonnet** |
| **Worker Tier (fast/draft)** | Gemma 4 26B | **Gemini** |
| **Director Iterations** | 4/3/2/1 | **10/8/2/1** |
| **Worker Regeneration** | 記述なし | **4/3/2/2** |

---

## 仕様書加筆計画

以下に、各仕様書（v10, v2）への具体的な加筆・修正計画を示す。

### Phase 1: v10仕様書への加筆（優先度: 高）

| No | 対象セクション | 加筆内容 | 根拠 | 推定作業量 |
|----|--------------|---------|------|-----------|
| 1 | §4.3 Perceiver Agent | 「Impulsive Agent（§4.6 Step 1）に統合済み。出力3要素（現象学的記述・反射的情動・自動的注意）はImpulsive Agent内で維持。独立エージェントとしては呼び出さない。」を追記 | A-2 | 小 |
| 2 | §4.6 Step 1-2 間 | 感情強度判定メカニズムを新設。現在の実装（バイパス方式）を採用する場合: 「intensity == high の場合、Reflective Agentの出力は空として扱い、Integration Agentは衝動ブランチのみで行動決定を行う」。v10原則（重み低下方式）を維持する場合: 実装の修正が必要。**設計判断が必要。** | A-1 | 中 |
| 3 | §Phase A-1 | voice_fingerprint → LinguisticExpression への構造変更を反映。SpeechCharacteristics + DiaryWritingAtmosphere の2層モデル。Phase A-1のWorker一覧・依存グラフを更新。 | A-3 | 中 |
| 4 | §4.8 日記生成 | LinguisticExpression注入の明記。日記生成プロンプトにLinguisticExpressionブロックを追加。Phase A-2/A-3/Dには注入しないことを明記。 | A-3 | 小 |
| 5 | §4.9.1 日記検証 | 3段階ゲート（DiarySelfCritic → LinguisticExpressionValidator → ThirdPartyReviewer）の詳細仕様を追記 | B-2 | 中 |
| 6 | §4.6 後 | 4並列チェッカー（Profile/Temperament/Personality/Values）の仕様を§4.6eとして新設 | B-3 | 中 |
| 7 | §4.7-§4.8 間 | 実行順序変更の反映: 翌日予定(§4.9.4)を内省(§4.7)と日記生成(§4.8)の間に移動。理由: 「日記が翌日の意図を自然に含むため」 | A-6 | 小 |
| 8 | §Phase D | CharacterCapabilities（所持品・能力・可能行動）のセクションを新設。CharacterCapabilitiesAgentのエージェンティックフロー（Web検索2回以上→draft→critique→self_reflect→submit）を明記。 | B-1 | 中 |
| 9 | §4.9.3.2 | DailyLogStoreのフォルダ構造（日別フォルダ、バージョニング）とLLM圧縮の詳細を追記 | B-6 | 小 |
| 10 | §Phase D イベント数 | 1日あたり2-4件（合計14-28件）に修正。変更理由（コスト・品質最適化）を注記。 | D-1 | 小 |
| 11 | §5 データベース構造 | Emotional Knowledge DBの状態を「Phase B未実装のため保留」に更新 | C-1, C-5 | 小 |
| 12 | 確認済設計決定セクション | 新規決定事項を追加: Perceiver統合、エージェンティック化方針、感情強度判定の採用方式 | A-2, A-5 | 小 |

### Phase 2: v2仕様書への加筆（優先度: 中）

| No | 対象セクション | 加筆内容 | 根拠 | 推定作業量 |
|----|--------------|---------|------|-----------|
| 1 | §12 技術スタック | Gemma 4 → Geminiへの全面改訂。3層ティア（opus/sonnet/gemini）。Gemini 2.5 Pro + 2.0 Flashフォールバック。 | A-7 | 中 |
| 2 | §12 APIキー管理 | 動的APIキーシステム（フロントエンドlocalStorage → WebSocket → バックエンド全層伝播）を追加 | B-8 | 小 |
| 3 | §6.3 Phase A-1 | Worker一覧を9個に更新。LinguisticExpressionWorkerをStep 5として追加。依存グラフ更新。 | A-3, D-4 | 小 |
| 4 | §6.4 Phase A-2 | Worker一覧を15分割に更新。CognitiveDerivation Workerを明記。 | A-4 | 小 |
| 5 | §6.5 Phase A-3 | カテゴリ別Writer方式 → 単一エージェンティックループ方式に全面改訂 | A-5 | 中 |
| 6 | §6.6 Phase D | CharacterCapabilitiesAgentを追加。Worker一覧更新。イベント数を2-4件/日に修正。SupportingCharacters数を3-6人に修正。 | B-1, D-1, D-2 | 中 |
| 7 | §7 Worker出力形式 | JSON → 自然言語テキスト（中間段階）の方針変更を反映 | A-8 | 小 |
| 8 | §5 Master Orchestrator | Regenerationモジュール（アーティファクト→フェーズマッピング、依存グラフ、再生成コア）を追加 | B-5 | 中 |
| 9 | §2 設計原則 | wrap_context()パターン（コンテキスト説明注入）を追加 | B-4 | 小 |
| 10 | §4.6 Creative Director | self_reflectツール追加。Web検索最低回数保証。capabilities_hints出力追加。 | B-11, B-1 | 小 |
| 11 | §8.5 Evaluator Profile | Director Iterations: 10/8/2/1に更新。Worker Tier: sonnet/sonnet/gemini/geminiに更新。Worker Regen: 4/3/2/2に更新。 | D-6 | 小 |
| 12 | §14 コスト見積もり | Gemini課金体系に基づく再計算。Per-Stepコスト記録機能の説明追加。 | A-7, B-9 | 中 |
| 13 | §新設: チェックポイント | デュアルチェックポイント保存・レジューム機能の仕様 | B-7 | 中 |
| 14 | §新設: フォールバック | Gemini多段フォールバックカスケードの仕様 | B-10 | 小 |
| 15 | §3.4 Co-Editモード | 現状: 未実装。Regenerationモジュールによる部分代替の記述。残タスクとして明記。 | C-3 | 小 |

### Phase 3: 設計判断が必要な項目（ユーザー確認）

| No | 項目 | 選択肢 | 影響 |
|----|------|--------|------|
| 1 | 感情強度による理性ブランチ処理 | **(a)** 実装通り「バイパス」を正式採用 → v10の設計原則を修正 | v10 §4.6の「構造継続、分岐なし」原則の撤回 |
| | | **(b)** v10原則「重み低下」を維持 → 実装を修正 | `_evaluate_emotion_intensity` のバイパスロジックをweight reduction方式に変更 |
| 2 | イベント数 2-4件/日 | 正式採用するか、将来的に4-6件に戻すか | コスト・品質・ナラティブ密度のバランス |
| 3 | Phase B実装計画 | 実装するか、仕様から削除するか | Emotional Knowledge DBの参照コードが不要になる |

---

## 修正優先度サマリー

### 最優先（仕様と実装の矛盾解消）
1. **A-1**: 感情強度バイパス → 設計判断 + 仕様/実装の整合
2. **A-3**: LinguisticExpression → v10/v2両方の構造更新
3. **A-7**: Gemma 4廃止 → v2技術スタック全面改訂

### 高優先（仕様に存在しない重要機能の追記）
4. **B-1**: CharacterCapabilities → v10 Phase D + v2 §6.6
5. **B-2**: 3段階日記ゲート → v10 §4.9.1
6. **B-5**: Regenerationモジュール → v2 §5

### 中優先（構成変更の反映）
7. **A-2**: Perceiver統合 → v10 §4.3
8. **A-5**: Phase A-3エージェンティック化 → v2 §6.5
9. **A-6**: 実行順序変更 → v10 §4.7-§4.9
10. **D-1**: イベント数修正 → v10 Phase D + v2 §6.6

### 低優先（補足・改善）
11. **B-3〜B-11**: 追加機能の仕様書反映
12. **C-1〜C-5**: 未実装機能のステータス更新
13. **D-2〜D-6**: 数値・定数の修正
