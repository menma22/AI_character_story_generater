# AIキャラクターストーリー生成システム

> specification_v10.md と script_ai_app_specification_v2.md に基づく、心理学的人格モデルを搭載したキャラクターAI日記生成システム

---

## パート1: アプリシステム概要

### ディレクトリ・ファイル構成

```
AI_character_story_generater/
├── backend/
│   ├── main.py                                # FastAPI エントリポイント (WebSocket + REST API)
│   ├── config.py                              # 設定管理 (APIキー, プロファイル, モデル定義)
│   ├── agents/
│   │   ├── creative_director/
│   │   │   └── director.py                    # Tier -1: Creative Director (Opus, Self-Critique)
│   │   ├── master_orchestrator/
│   │   │   └── orchestrator.py                # Tier 0: Phase A-1→A-2→A-3→D 順次制御
│   │   ├── phase_a1/
│   │   │   └── orchestrator.py                # Phase A-1: マクロプロフィール (8 Workers)
│   │   ├── phase_a2/
│   │   │   └── orchestrator.py                # Phase A-2: ミクロパラメータ 52個 + 規範層
│   │   ├── phase_a3/
│   │   │   └── orchestrator.py                # Phase A-3: 自伝的エピソード (McAdams)
│   │   ├── phase_d/
│   │   │   └── orchestrator.py                # Phase D: 7日間イベント列 (28-42件)
│   │   ├── daily_loop/
│   │   │   └── orchestrator.py                # Day 1-7 日次ループ (RIM + 内省 + 日記)
│   │   └── evaluators/                        # Evaluator群 (品質評価・再生成管理)
│   ├── models/
│   │   ├── character.py                       # Pydantic v2 データモデル (脚本パッケージ)
│   │   └── memory.py                          # 記憶・ムード・イベント処理モデル
│   ├── tools/
│   │   └── llm_api.py                         # LLM API統合ラッパー (Anthropic + Gemma)
│   ├── websocket/
│   │   └── handler.py                         # WebSocket接続管理 + 思考ストリーミング
│   ├── schemas/                               # JSON Schema (今後定義)
│   ├── reference/                             # 心理学理論参考資料 (今後追加)
│   └── storage/character_packages/            # 生成済みパッケージ保存先
├── frontend/
│   ├── index.html                             # メインUI (4画面構成)
│   ├── css/style.css                          # プレミアムダークテーマ
│   └── js/
│       ├── websocket.js                       # WebSocket接続管理 (自動再接続)
│       ├── renderer.js                        # データ → HTML レンダリング
│       └── app.js                             # アプリケーションロジック
├── .env.example                               # 環境変数テンプレート
├── .gitignore
├── requirements.txt                           # Python依存関係
├── specification_v10.md                       # コア仕様書 (v10)
└── script_ai_app_specification_v2.md          # 脚本AI仕様書 (v2)
```

### モジュール依存関係

```mermaid
graph TB
    subgraph "フロントエンド"
        HTML["index.html"] --> CSS["style.css"]
        HTML --> WSClient["websocket.js"]
        HTML --> Renderer["renderer.js"]
        HTML --> App["app.js"]
        App --> WSClient
        App --> Renderer
    end
    
    subgraph "バックエンド"
        Main["main.py<br>(FastAPI)"] --> Config["config.py"]
        Main --> WSHandler["websocket/handler.py"]
        Main --> MO["master_orchestrator.py"]
        Main --> DLO["daily_loop/orchestrator.py"]
        
        MO --> CD["creative_director.py"]
        MO --> PA1["phase_a1/orchestrator.py"]
        MO --> PA2["phase_a2/orchestrator.py"]
        MO --> PA3["phase_a3/orchestrator.py"]
        MO --> PD["phase_d/orchestrator.py"]
        
        CD --> LLM["tools/llm_api.py"]
        PA1 --> LLM
        PA2 --> LLM
        PA3 --> LLM
        PD --> LLM
        DLO --> LLM
        
        CD --> Models["models/character.py"]
        PA1 --> Models
        PA2 --> Models
        PA3 --> Models
        PD --> Models
        DLO --> Memory["models/memory.py"]
    end

    WSClient <-.->|"WebSocket"| WSHandler
    
    style CD fill:#a855f7,color:#fff
    style MO fill:#a855f7,color:#fff
    style PA1 fill:#6366f1,color:#fff
    style PA2 fill:#6366f1,color:#fff
    style PA3 fill:#6366f1,color:#fff
    style PD fill:#6366f1,color:#fff
    style DLO fill:#22c55e,color:#fff
    style LLM fill:#f59e0b,color:#000
    style Main fill:#ef4444,color:#fff
```

> **凡例**: 🟣紫 = Tier -1/0 エージェント、🔵青 = Phase Orchestrators、🟢緑 = 日次ループ、🟡黄 = LLM API、🔴赤 = FastAPI

### プロジェクト要件

| 項目 | 内容 |
|---|---|
| **目的** | サード・インテリジェンス社 Bコースインターン選考課題 |
| **課題** | キャラクターAIに密教学（心理学的人格モデル）を教え、7日間の日記を生成する |
| **理想的最終形** | 1キャラクターの完全な脚本パッケージ（52パラメータ + マクロプロフィール + 自伝的エピソード + 7日間イベント列）を生成し、日次ループで7日間の日記を自動生成 |
| **対象ユーザー** | インターン選考の審査員 |
| **実装対象外** | クローリング（Phase B）、擬似体験（Phase C）、エコーチェンバー |

### 現在のシステム仕様・状態

#### コアロジック・ルール

**4層エージェント階層（Day 0）:**
1. **Tier -1 Creative Director** (Opus): Tool-Callingによる自律推敲ループ (Agentic Loop) でconcept_packageを生成・自己批評・修正。
2. **Tier 0 Master Orchestrator** (Opus): Phase A-1→A-2→A-3→D順次制御
3. **Phase Orchestrators**: 各Phase内のWorker群を管理
4. **Workers** (Gemma 4 / Sonnet): 個別生成タスク

**日次ループ（Day 1-7）:**
```
各日のイベント(4-6個) → Perceiver → [Impulsive | Reflective](並列)
→ 統合(Higgins): Agentic行動決定(事前シミュレーションツール使用) → 情景描写
→ 内省(Self-Perception + 過去統合 + 再解釈)
→ 日記生成: Agentic日記執筆(言語的指紋・AI臭さツール検証込み)
→ key memory抽出 + 記憶圧縮 + 翌日予定追加
```

**隠蔽原則（implicit/explicit非対称）:**
- Impulsive Agent: 気質・性格層にアクセス可 / 規範層にアクセス不可
- Reflective Agent: 気質・性格層に隠蔽 / 規範層にアクセス可
- 日記生成AI: 気質・性格パラメータを知らない（行動からの推測のみ）

#### データモデル

| モデル | 用途 | Phase |
|---|---|---|
| `ConceptPackage` | キャラクター概念設計 | Tier -1 |
| `MacroProfile` | マクロプロフィール（8セクション） | A-1 |
| `MicroParameters` | 52パラメータ + 規範層 | A-2 |
| `AutobiographicalEpisodes` | 自伝的エピソード（5-8個） | A-3 |
| `WeeklyEventsStore` | 7日間イベント列（28-42件） | D |
| `MoodState` | PAD 3次元ムード | 日次ループ |
| `ShortTermMemoryDB` | 記憶（key memory + 段階圧縮） | 日次ループ |
| `EventPackage` | 1イベント処理結果 | 日次ループ |

#### UI/UX

- **フェーズ構成の区分化**: Day 0 ダッシュボード（キャラクター設定結果確認画面）と Day 1-7（日記生成）のシミュレーションループを明確にUI分割。
- **4画面構成**: 起動 → 生成中（思考とフェーズトラッカー） → Day 0結果（6タブ・ダッシュボード） → 履歴
- **生成進行UI（Phase Tracker）**: 生成中画面にて、現在のパイプライン実行状態（Creative Director → A-1 → A-2 → A-3 → D）をステップ形式で可視化するUIを導入。
- **インライン日記生成とキャンセル機能**: 「日記」ダッシュボード内で、他画面に遷移せずインラインで思考ログと生成中の日記をリアルタイム表示。また、バックエンドでのタスク強制終了（asyncio.Task.cancel）を伴う「🛑 停止してリセット」機能を実装。
- **エラー耐性と生成再開（Resume）**: Pydantic v2 の `field_validator` によるデータ型の自己修復機能、および各フェーズ完了ごとの「チェックポイント保存」を実装。エラー発生時に「中断した箇所から再開」ボタンを表示し、既存の進行状況を飛ばして再開することが可能。
- **構成設定UI**: 生成画面にて、7種のEvaluator（Stage 2 品質評価層）のON/OFFをそれぞれ独立して切り替え可能、かつワンボタンで一括変更するトグルUIを実装。
- **Day 0 の再生成**: ダッシュボードにて気に入らない設定をその場で「破棄して再生成」できる機能を追加。
- **WebSocket**: エージェント思考のリアルタイム表示
- **詳細進捗ハートビート**: 長時間かかるAI推論中、`[Step X/N]` 形式で進捗を逐次表示。
- **デザイン**: プレミアムライトモード（以前のダークテーマから刷新）
- **ログ品質向上**: 通信重複排除（Deduplication）の実装、および各思考ログへの使用モデル（Opus/Sonnet/Gemini）表示バッジを実装。
- **安定性強化**: サーバーサイドの非同期処理最適化による「ハングアップ」の完全解消。ポート競合対策として 8001 番を使用。
- **コスト表示**: リアルタイムトークン消費・推定コスト表示。Gemini 2.5 Pro のコスト集計にも対応。

#### データフロー・永続化仕様

- **インメモリ共有**: 処理途中の全オブジェクト構成はPydanticスキーマによってメモリ上に保たれる
- **MDファイル永続化DB**: キャラクター作成と日次ループ終了後、以下の構造でディスクへ自律保存される。
  - `backend/storage/character_packages/{character_name}/00_profile.md` （事前生成のキャラクタープロファイル一式）
  - `backend/storage/character_packages/{character_name}/agent_logs.json/.md` （エージェントの思考過程・エンジニアリングログ）
  - `backend/storage/character_packages/{character_name}/daily_logs/Day_{N}.md` （日次イベント、行動、感情変化、内省、日記、記憶ログ）

#### エッジケース・制約

- `source: "protagonist_plan"` は Phase D では1件も生成禁止（日次ループの翌日予定追加が唯一の経路）
- redemption bias対策: contamination/loss/ambivalent型が安易な救済で終わることを構造的に防止
- 予想外度分布制約: `low`（予定通り・日常）が各日の半分以上、`high`（強い驚き）は Day 5 以外で各日最大1件

---

## パート2: ベストプラクティス・設計進化

### 1. エージェント階層の設計と評価ループ

**(a) 当初設計**: 仕様書v2の4層階層を採用。評価(EvaluatorPipeline)はすべての生成が終わった最後にまとめて呼び出して成否をテストする想定。
**(b) 変更・根拠**: 全工程終了後のテストでは、例えばPhase A-1（マクロ）で不合格が出た場合、既に無駄に消費したPhase Dまでのトークン生成が全て破棄されるというコスト破壊の問題が存在した。
**(c) 採用プラクティス**: `MasterOrchestrator` の `run()` 内に「Evaluator-Optimizer ループ」を完全統合。各Phase（例えばPhase A-3完了直後）ごとに即座に評価を挟み、FailならそのPhaseだけを指定回数（最大4回）再生成（リトライ）させる堅牢な自律修正システムへ進化した。また、APIの404エラー障害に対してフォールバックルーティング（Anthropic → Gemini 2.5 Pro）を実装して安定化を図った。

### 2. LLM API設計

**(a) 当初設計**: Claude Agent SDK使用を前提。また、Opus 4.6やGemma 4などの指定について代替えの現行モデルを使用して検証していた。
**(b) 変更・根拠**: SDK未確認のため、直接Anthropic APIおよびGoogle Generative AIに切替。さらに最新のAPIエコシステム（2026年現在）にて、 `claude-opus-4-6`, `claude-sonnet-4-6`, `models/gemma-4-31b-it` が実在・稼働していることが確認されたため。
**(c) 採用プラクティス**: `call_llm()` 統一インターフェースで、実在する最新モデルID（`claude-opus-4-6`等）を直接指定。エラー時にはフォールバックルーティング（Anthropic → Gemini 2.5 Pro）が作動して安定化を図る設計とした。

### 3. 隠蔽原則の実装

**(a) 当初設計**: 各エージェントに渡すコンテキストを関数引数レベルで制御
**(b) 採用プラクティス**: 
- Impulsive Agent: `micro_parameters.temperament` を直接渡す
- Reflective Agent: `schwartz_values`, `ideal_self`, `ought_self` のみ渡す（気質パラメータは渡さない）
- 日記生成AI: `voice_fingerprint` のみ渡す（パラメータ値は一切渡さない）

### 4. コアAPI層の自律エージェント化 (Agentic Loops v10)

**(a) 当初設計**: 各タスク（Creative Directorによるドラフト生成や、日記の評価）はPython側の固定化された順次・反復ループ構造（プロンプトチェイン）を用いて、外部からLLMをコントロールする「制御型フロー」だった。
**(b) 変更・根拠**: V10仕様書に基づく「真のエージェンティックな振る舞い」を実現するため。LLMに対し、外部から判定を押し付けるのではなく、複数のツール（機能）を提供し、自ら考えて行動・検証させる方が高度な成果が得られる。
**(c) 採用プラクティス**: Anthropic Tool Calling機能を統合した `call_llm_agentic` インフラを構築し、CreativeDirector、Integration Agent(行動決定)、DiaryGenerationAgentの3コアを、すべてツールの呼び出し可否を自律判断して自己完結する「Tool-using Autonomous Agent」へと置き換えた。

### 5. WebサーチおよびMDファイル保存ルーティング

**(a) 当初設計**: キャラクター作成はAI内テキスト生成のみに依存し、データ出力はJSONオブジェクトやインメモリ保持に留まっていた。
**(b) 変更・根拠**: V10仕様上、世界観に深みを持たせるための既存物語の「リサーチ能力」と、生成ログやプロセスを読み物として美しく永続化するための「MDデータベース」が必要不可欠であった。
**(c) 採用プラクティス**: 
- クリエイティブディレクターにのみ特権的に `search_web`（duckduckgo-searchベース）を渡し、ドラフト前に自律検索を行うように `llm_api.py` のイテレーション枠を拡張。
- `md_storage.py` を実装し、Master Orchestrator と Daily Loop の各完了フェーズにて、`00_profile.md` と `Day_x.md` を `backend/storage/character_packages/` フォルダへ自動保存させる堅牢な出力ルーティング（getattrベースの安全処理込み）を確立。

---

## パート3: プロジェクト管理

### 現在のフェーズ

| ステージ | 状態 | 備考 |
|---|---|---|
| Stage 1: MVP | ✅ 実装完了 | 4層エージェント構造、日次ループ統合済 |
| Stage 2: 品質向上 | ✅ 実装完了 | Evaluator群7種、再生成ループ統合完了 |
| Stage 3: エージェント自律化 | ✅ 実装完了 | コア3種(Director, Action, Diary)のTool-Using化 |
| Stage 4: UX改善 | ⬜ 未着手 | 共同編集・ストリーミング強化 |
| Stage 5: インフラ・完成 | ✅ 実装完了 | Webサーチ・MD永続化・E2Eテスト済 |

### 次のアクション（現行ステータス: Stage 5 完了 -> 本稼働テスト）

1. **提出用キャラクター生成** → High Qualityプロファイルで全EvaluatorをONにし、MDデータベース出力まで通して実行する。
2. **フロントエンド連携強化** → WebSocketでの思考ストリーミング確認とアプリ統合。（Stage 4への移行）

### ブロッカー

> [!WARNING]
> 一部のLLM API（特にAnthropic無料枠の残高不足エラーや、Gemini APIのクォータ制限）による生成中断ログが確認されています。本システムは現在、Claudeが利用不可の場合に自動でGemini 2.5 Proへフォールバックする機能が安定稼働しています。本稼働させる場合は有償Tierキーへ切り替えるか、リセット枠の回復をお待ちください。
