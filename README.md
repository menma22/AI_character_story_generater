# AI Character Story Generator

**心理学的人格モデル × マルチエージェントAI × 脚本理論で、"本当に存在しそうな人間"の7日間の日記を自動生成するシステム**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com/)

---

## Table of Contents

- [概要](#概要)
- [設計思想](#設計思想)
- [システムアーキテクチャ](#システムアーキテクチャ)
  - [4層エージェント階層](#4層エージェント階層)
  - [Day 0: 人格形成期 (Seed Phase)](#day-0-人格形成期-seed-phase)
  - [Day 1-7: 日次ループ](#day-1-7-日次ループ)
- [心理学的基盤](#心理学的基盤)
  - [52パラメータ体系](#52パラメータ体系)
  - [隠蔽原則 (Implicit/Explicit Asymmetry)](#隠蔽原則-implicitexplicit-asymmetry)
  - [Redemption Bias対策](#redemption-bias対策)
- [エージェント詳細設計](#エージェント詳細設計)
  - [Creative Director (Tier -1)](#creative-director-tier--1)
  - [Master Orchestrator (Tier 0)](#master-orchestrator-tier-0)
  - [Phase Orchestrators](#phase-orchestrators)
  - [Daily Loop エージェント群](#daily-loop-エージェント群)
  - [検証・評価システム](#検証評価システム)
- [データモデル](#データモデル)
- [記憶システム](#記憶システム)
- [LLMティアシステム](#llmティアシステム)
- [品質プロファイル](#品質プロファイル)
- [技術スタック](#技術スタック)
- [プロジェクト構造](#プロジェクト構造)
- [Quick Start](#quick-start)
- [API・WebSocket仕様](#apiwebsocket仕様)
- [License](#license)

---

## 概要

本システムは、**1体のAIキャラクターに心理学的人格モデル（気質23項目・性格27項目・価値観・道徳基盤・理想自己）を教え込み、7日分の日記を自動生成する**マルチエージェントシステムである。

単なるテキスト生成ではなく、**計算論的性格心理学**のアプローチでキャラクターの内面を構造化し、日次ループでは**二重過程理論（Reflective-Impulsive Model）**に基づく認知シミュレーションを経て日記を出力する。

### 生成される最終成果物

| 成果物 | 内容 |
|--------|------|
| **Concept Package** | 物語テーマ・Want/Need/Ghost/Lie（McKee脚本理論） |
| **Macro Profile** | 9セクションの人物像（基本情報・家族・夢・話し方・秘密等） |
| **Linguistic Expression** | 言語的指紋（口癖・回避語彙・日記文体の空気感） |
| **Micro Parameters** | 52項目の気質・性格パラメータ + Schwartz価値観 + MFT道徳基盤 |
| **Autobiographical Episodes** | 5-8個の自伝的エピソード（McAdams理論準拠） |
| **Weekly Events Store** | 7日分×各日2-4件の脚本化イベント列（葛藤強度アーク付き） |
| **Character Capabilities** | 所持品・能力・可能行動パターン |
| **7日分の日記** | キャラクター視点の1人称日記（内省・省略を含む） |

---

## 設計思想

### 1. 「1つのAIには52パラメータ+マクロプロフィール+エピソードは作れない」

本システムの全アーキテクチャは、この制約への回答である。**Orchestrator-Workers パターン**で各エージェントに狭いスコープの単一出力を割り当て、品質評価ループで統合する。

### 2. 出力形式の決定原則

> **「コードがこのデータを機械的にパースするか？」**
> - **Yes → JSON**（`json_mode=True`）: パラメータID、エピソード/イベントWriter、Tool Calling
> - **No → 自然言語 / raw text パススルー**: 衝動ブランチ出力、理性ブランチ出力、内省メモ
> - **最終出力 → 自然散文**: 日記、ナラティブ

エージェント間のコンテキスト受け渡しにJSONを使わない。自然言語のまま全文パススルーすることで、LLMの表現力を損なわない。

### 3. 脚本優先のイベント設計

**日次ループはイベントを生成しない**。Day 0で脚本AIが7日分全28-42件のイベントを一括設計し、Day 5クライマックスへの伏線をDay 1-4に事前配置する。これは Generative Agents (Park et al. 2023) にはない、**脚本理論の計算的実装**である。

### 4. Evaluator-Optimizer ループ

各Phase完了後に即時評価し、失敗時はそのPhaseのみを再生成（最大4回）。パイプライン全体のやり直しを排除し、トークンコストを最小化する。

### 5. 高品質タスク = エージェント

設計密度が要求されるタスク（CharacterCapabilities、Episode生成、Event生成）は、ワンショット生成ではなく **Web検索 + 多層品質ゲート付きのエージェンティックループ** に昇格させる。

### 6. コンテキスト記述原則

全エージェントに渡すコンテキストは `wrap_context(section_name, data, agent_role)` で**what/why/howの3点注釈**を付与。同じデータでもエージェントのロールに応じて説明を変える。

---

## システムアーキテクチャ

### 4層エージェント階層

```
┌─────────────────────────────────────────────────────────────────┐
│  Tier -1: Creative Director (総監督)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  自律的Tool Callingによる自己洗練ループ                     │  │
│  │  search_web → file_read → request_critique → submit       │  │
│  │  5フェーズ: 企画→調査→草案→外部批評→自己省察→提出         │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Tier 0: Master Orchestrator (統括指揮)                         │
│  Phase A-1 → A-2 → A-3 → D の逐次制御                         │
│  + Evaluator-Optimizer ループ (各Phase即時評価・再生成)         │
├──────────┬──────────┬──────────┬────────────────────────────────┤
│ Phase    │ Phase    │ Phase    │ Phase D                        │
│ A-1      │ A-2      │ A-3      │ 週間イベント                   │
│ マクロ    │ ミクロ    │ エピソード│ + Capabilities                 │
│ プロフィール│ 52パラメータ│ 5-8個    │ 28-42件                        │
│ 9Workers │ 15Workers│ Agentic  │ Agentic                        │
├──────────┴──────────┴──────────┴────────────────────────────────┤
│  Evaluator Pipeline (横断的品質評価)                             │
│  Schema │ Consistency │ Bias │ Interestingness │ Distribution   │
│  Validator│ Checker   │Auditor│ Evaluator      │ Validator      │
│         │           │       │ EventMetadata  │ NarrativeConn  │
└─────────────────────────────────────────────────────────────────┘

                          ↓ Day 0 完了

┌─────────────────────────────────────────────────────────────────┐
│  Daily Loop (Day 1-7)                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  外層: 1日の全処理を制御するオーケストレーター           │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │  内層: 1イベントあたりの認知シミュレーション     │    │    │
│  │  │  活性化→知覚→衝動→理性→統合→情景→価値観チェック │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │  内省 → 翌日予定 → 日記生成 → ムード更新 → 記憶圧縮    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Day 0: 人格形成期 (Seed Phase)

Day 0は4つのPhaseを逐次実行し、キャラクターの全人格データを構築する。

#### Phase A-1: マクロプロフィール生成（9 Workers）

`BasicInfoWorker`（逐次）→ 6 Workers 並列（`FamilyWorker`, `LifestyleWorker`, `DreamWorker`, `VoiceWorker`, `ValuesCoreWorker`, `SecretWorker`）→ `RelationshipNetworkWorker`（逐次、家族情報依存）→ `LinguisticExpressionWorker`

出力: 基本情報 / 社会的位置 / 家族・親密圏 / 現在の生活の輪郭 / 夢と目標(時系列) / 話し方・文体の指紋 / 価値観の中核 / 秘密 / 関係性ネットワーク + 言語的表現スタイル

#### Phase A-2: ミクロパラメータ生成（15 Workers + 認知導出）

**Step 1** — 10 Parameter Workers 並列:

| Worker | 担当領域 | パラメータ番号 |
|--------|----------|---------------|
| `TemperamentWorker_A1` | 情動反応系 | #1-9 |
| `TemperamentWorker_A2` | 活性・エネルギー系 | #10-14 |
| `TemperamentWorker_A3` | 社会的志向系 | #15-18 |
| `TemperamentWorker_A4` | 認知スタイル系 | #19-23 |
| `PersonalityWorker_B1` | 自己調整・目標追求 | #24-30 |
| `PersonalityWorker_B2` | 対人・社会的態度 | #31-38 |
| `PersonalityWorker_B3` | 経験への開放性 | #39-43 |
| `PersonalityWorker_B4` | 自己概念・実存 | #44-48 |
| `PersonalityWorker_B5` | ライフスタイル・表出 | #49-50 |
| `SocialCognitionWorker` | 対他者認知 | #51-52 |

**Step 2** — 4 Normative Layer Workers 並列:
`ValuesWorker`（Schwartz 19価値）/ `MFTWorker`（道徳基盤理論6基盤）/ `IdealOughtSelfWorker`（理想自己・義務自己）/ `GoalsDreamsWorker`（長期・中期目標）

**Step 3** — `CognitiveDerivation`: ルールベース自動導出（LLM不使用）
- 学習率α ← 新奇性追求 + (1 - 損害回避)
- 情動慣性 ← 固執 + 損害回避
- RPE感受性 ← 新奇性追求
- 減衰係数λ ← 固執 / 新奇性追求 の比

#### Phase A-3: 自伝的エピソード生成（Agentic Loop）

`EpisodePlanner` → カテゴリ別 Writer 並列 → `BiasAuditor` → 不合格なら再生成（最大4ラウンド）

#### Phase D: 7日分イベント列一括生成（Agentic Loop）

1. `WorldContextWorker` + `SupportingCharactersWorker`（並列）
2. `NarrativeArcDesigner` — 7日間の物語アーク設計（Vonnegutアーク型、Day 5クライマックス設計、伏線配置計画）
3. `ConflictIntensityDesigner` — 葛藤強度アーク設計
4. `WeeklyEventWriter` — 全28-42件を一括生成
5. `CharacterCapabilitiesAgent` — 所持品・能力・可能行動を5ツールエージェンティックループで生成

**葛藤強度アーク（固定）:**
```
Day1=弱 → Day2=弱〜中 → Day3=中 → Day4=中〜強 → Day5=強(山場) → Day6=余韻 → Day7=収束
```

**分布制約:**
- 予想外度「低」≥ 各日のイベント総数の50%
- 予想外度「高」≤ 1件/日（Day 5除く）
- Day 5は「高」を必ず1件以上含む

### Day 1-7: 日次ループ

各日の各イベント（2-4件/日）に対して、以下の認知シミュレーションパイプラインを実行する:

```
イベント注入 (既知/未知 × 予想外度タグ)
    │
    ▼
動的活性化 (5-10パラメータ選出)
    │
    ├──── 裏方系 ────────────────────────┐
    │                                    │
    ▼                                    ▼
Perceiver (知覚フィルター)         理性ブランチ
    │                              (規範層のみ参照)
    ▼                                    │
Impulsive Agent (衝動ブランチ)           │
    │                                    │
    ▼                                    ▼
裏方出力検証 (§4.6b)              裏方出力検証 (§4.6b)
    │                                    │
    └──────────┬─────────────────────────┘
               ▼
    ┌─── 感情強度判定 ───┐
    │  high: 理性bypass  │
    │  otherwise: 統合   │
    └────────┬───────────┘
             ▼
    統合エージェント
    (Higgins自己不一致評価 + 2ルート予測 + 最終行動決定 + PAD更新)
             │
             ▼
    情景描写・後日譚生成エージェント
             │
             ▼
    価値観違反チェックエージェント
             │
             ▼
    ── イベント処理完了 → 行動履歴バッファへ保存 ──

全イベント処理後:
    内省エージェント (Self-Perception → 過去記録統合 → 薄れた記憶の再解釈)
        │
        ▼
    翌日予定追加エージェント (Stage 1: 主人公の能動性 → Stage 2: 整合性調整)
        │
        ▼
    日記生成エージェント (3段階ゲート: check_diary_rules → validate_linguistic → third_party_review → submit)
        │
        ▼
    4並列チェッカーAI (Profile / Temperament / Personality / Values)
        │
        ▼
    ムード更新 (Peak-End Rule) → key memory抽出 → 記憶の段階圧縮
        │
        ▼
    ムードcarry-over (減衰係数λ適用 → 閾値以下リセット → 翌日へ)
```

---

## 心理学的基盤

### 52パラメータ体系

Cloningerの神経生物学（ドーパミン/セロトニン/ノルエピネフリン/グルタメート系）に基盤を置く気質23項目と、Big Five拡張の性格27項目、社会的認知2項目の合計52パラメータ。

```
気質層 (23項目)                          性格層 (27項目)
├─ A1 情動反応系 (#1-9)                  ├─ B1 自己調整・目標追求 (#24-30)
│  新奇性追求/損害回避/報酬依存/固執/     │  勤勉性/自己鍛錬/秩序性/良心性/
│  脅威反応性/行動抑制/感情強度/          │  達成志向/慎重さ/コンピテンス感
│  気分基調ポジ性/気分基調ネガ性          │
├─ A2 活性・エネルギー系 (#10-14)        ├─ B2 対人・社会的態度 (#31-38)
│  活動水準/疲労耐性/覚醒水準/           │  他者への信頼/実直さ/利他性/従順・協調/
│  衝動性/感覚閾値                       │  謙虚さ/共感性/誠実性H因子/貪欲回避
├─ A3 社会的志向系 (#15-18)              ├─ B3 経験への開放性 (#39-43)
│  社交性/対人温かさ志向/遊戯性/         │  審美性/感情への開放/行動の開放/
│  支配性志向                            │  アイデア志向/価値観の柔軟性
├─ A4 認知スタイル系 (#19-23)            ├─ B4 自己概念・実存 (#44-48)
│  注意持続/注意切替柔軟性/              │  自己志向性/自己受容/自己超越性/
│  知的好奇心ベースライン/               │  アイデンティティ一貫性/内省傾向
│  想像力・内的生活/規則性志向           ├─ B5 ライフスタイル・表出 (#49-50)
                                        │  感情表出性/ユーモア志向
対他者認知層 (#51-52)                    
├─ 社会的比較傾向 SCO (強さ×質)
└─ 嫉妬気質 (感受性×質 良性/悪性)

認知パラメータ (ルールベース自動導出、LLM不使用)
├─ 学習率α          ← NS + (1-HA)
├─ 情動慣性          ← Persistence + HA
├─ RPE感受性         ← NS
└─ 減衰係数λ         ← Persistence / NS

規範層 (LLM生成)
├─ Schwartz 19価値スケルトン (強/中/弱)
├─ MFT道徳基盤 (6基盤+)
├─ 理想自己 / 義務自己
└─ 長期・中期目標
```

### 隠蔽原則 (Implicit/Explicit Asymmetry)

**Nisbett & Wilson (1977) / McClelland (1989) / Bem (1972) の計算的実装**として、キャラクターの「実際の性格」と「自覚している性格」を構造的に分離する。

| エージェント | 気質・性格層 | 規範層 | 設計意図 |
|-------------|------------|--------|---------|
| **Perceiver** (裏方) | 読取可能 | — | 知覚フィルターとして気質を反映 |
| **Impulsive Agent** (裏方) | 読取可能 | 不可 | 衝動は規範を知らない |
| **Reflective Agent** (主人公AI) | **隠蔽** | 読取可能 | 理性は気質を直接参照できない |
| **日記生成AI** (主人公AI) | **隠蔽** | 活性化済みのみ | 行動から推測するしかない |

この非対称性が、「自分はこういう人間なのかもしれない」という内省的な日記表現を構造的に生み出す。

### Redemption Bias対策

Nature Humanities (2026) の研究に基づき、LLMが「困難→救済→成長」パターンに偏る傾向を構造的に抑制する。

**単一LLMによる一括生成を排除**し、カテゴリ別Episode Writerが独立して生成する:

| 制約 | 内容 |
|------|------|
| Contamination sequence | 最低1個必須（良いことが損なわれるパターン） |
| 未解決のloss | 最低1個必須 |
| Ambivalent episode | 最低1個必須 |
| Redemption sequence | **最大2個まで** |
| BiasAuditor | ラベル偽装の暗黙的redemptionも検出 |

---

## エージェント詳細設計

### Creative Director (Tier -1)

自律的なTool Callingループにより、キャラクターコンセプトを自己洗練する。

**4つのツール:**
| ツール | 機能 |
|--------|------|
| `search_web` | DuckDuckGo検索（品質別最低回数: high=5, standard=3, fast=2, draft=1） |
| `file_read` | ファイル読み込み |
| `request_critique` | 外部LLMインスタンスによる客観評価（pass/refine判定） |
| `submit_final_concept` | 最終提出（critique通過必須） |

**2層自己批評メカニズム:**
1. `request_critique` — 外部LLM評価（合格/修正判定）
2. `self_reflect` — 自己問い（「本当に納得しているか？」convinced: true/false）
3. 両方パスで初めて `submit_` が解放。`convinced=false` なら `critique_passed` もリセットされ、全サイクルやり直し

**出力 `ConceptPackage`:**
- `character_concept` (500-1,000字): キャラクターの濃密な概念記述
- `story_outline` (500-1,000字): 週間の物語アーク概要
- `psychological_hints`: Want/Need/Ghost/Lie（McKee脚本理論）
- `capabilities_hints`: 所持品・能力・署名的行動パターンのヒント
- `interestingness_hooks`: 3-5個の興味フック
- `critical_design_notes`: 下流エージェントへの設計指示

### Master Orchestrator (Tier 0)

Phase A-1 → A-2 → A-3 → D の逐次制御と、各Phase完了後の即時評価。失敗時はそのPhaseのみ再生成（最大4回リトライ）。チェックポイント保存によるレジューム対応。

### Phase Orchestrators

各PhaseはWorkerを並列/逐次で起動し、Evaluator Pipelineで品質評価する。

### Daily Loop エージェント群

#### 主人公AI系（気質・性格層が隠蔽される）

| エージェント | 主務 | 入力 |
|-------------|------|------|
| **理性ブランチ** | 濃密な内面分析 + 示唆 + 予測 | 規範層 + Perceiver/Impulsive出力 + 記憶全体 |
| **統合エージェント** | Higgins自己不一致評価 + 2ルート予測 + 最終行動一発出し + PAD更新 | 衝動/理性両レポート + 全コンテキスト |
| **内省エージェント** | Self-Perception → 過去統合 → 薄れた記憶の再解釈 | 行動履歴全体 + 記憶 + #48内省傾向 |
| **日記生成エージェント** | 1人称日記（省略の指示付き） | 内省結論 + 全イベントパッケージ + 記憶 + ムード |
| **翌日予定 Stage 1** | 「明日やりたいこと」0-3個（強制なし） | 行動履歴 + 記憶 |

#### 裏方エージェント系（気質・性格層にアクセス可）

| エージェント | 主務 | 隠蔽対象 |
|-------------|------|---------|
| **Perceiver** | 現象的記述 + 反射的感情 + 自動的注意配分 | 価値判断・原因帰属を禁止 |
| **Impulsive Agent** | 感情の表層 + 行動傾向(approach/avoidance/freeze) | 規範層 |
| **翌日予定 Stage 2** | 物理的/論理的衝突チェック + 採択判定 | 主人公AIから隠蔽 |
| **出力検証エージェント** | パラメータ名漏出チェック + 3ツール修正ループ | — |

#### 統合エージェント内部のサブステップ

1. **Higgins自己不一致評価**: Ideal不一致=落胆系 / Ought不一致=不安系を明示的分離
2. **予想外度タグからの予測誤差感情生成**: 高→強い驚き、中→軽い驚き、低→ほぼゼロ
3. **2ルート予測の内部組み立て（β方式）**: 理性ルートと衝動ルートそれぞれの良いこと/悪いことを並列表示
4. **最終行動の決定（一発出し方式）**: 衝動性#13・慎重さ#29・Arousal・Loewenstein経路等の重みを加味
5. **PAD更新**: 3次元ムード（Valence/Arousal/Dominance）の更新
6. **気持ちの変化短文記述**

### 検証・評価システム

#### Evaluator Pipeline（Day 0）

| Evaluator | タイプ | 常時ON | 内容 |
|-----------|--------|--------|------|
| `SchemaValidator` | ルールベース | Yes | Pydantic構造整合性 |
| `DistributionValidator` | ルールベース | Yes | パラメータ分布・イベント分布制約 |
| `ConsistencyChecker` | LLM | No | 設定間の矛盾検出 |
| `BiasAuditor` | LLM | No | Redemption Bias + ステレオタイプ検出 |
| `InterestingnessEvaluator` | LLM | No | 物語の面白さ評価 |
| `EventMetadataAuditor` | LLM | No | イベントメタデータの妥当性 |
| `NarrativeConnectionAuditor` | LLM | No | 物語的つながりの評価 |

#### 裏方出力検証（Daily Loop §4.6b）

- **パイプライン形式**: mdファイルベース
- **3ツール**: `str_replace` / `rewrite_sentence` / `request_full_regenerate`
- **最大3周ループ** → 3周失敗時にOpusエスカレーション
- **検出対象**: パラメータ名/番号/英字名の混入、自己特性帰属、原因分析、価値判断

#### 日記3段階ゲート

1. `check_diary_rules` — 言語的指紋・内省含有率・パラメータ漏出チェック
2. `validate_linguistic_expression` — 13フィールドの言語的表現整合性
3. `third_party_review` — 5点満点の読者品質チェック
4. `submit_final_diary` — **コードレベルの決定論的ゲート**（`check_passed == False` or テキスト変更時は強制再チェック）

---

## データモデル

### コアPydantic v2モデル

```python
# Day 0 生成物
ConceptPackage          # Tier-1出力: テーマ・Want/Need/Ghost/Lie・capabilities_hints
MacroProfile            # A-1出力: 9セクション人物像
LinguisticExpression    # A-1出力: 言語的指紋（独立フィールド）
  ├── SpeechCharacteristics    # 具体的特徴・抽象的印象・会話スタイル・感情表出傾向
  └── DiaryWritingAtmosphere   # トーン・構造・内省スタイル・書くこと/省略すること・空気感
MicroParameters         # A-2出力: 52パラメータ + 規範層
AutobiographicalEpisodes # A-3出力: 5-8エピソード（McAdams 5カテゴリ）
WeeklyEventsStore       # D出力: 7日×2-4件イベント（メタデータ7項目付き）
CharacterCapabilities   # D出力: PossessedItem×5-10, CharacterAbility×3-5, AvailableAction×3-5

# Daily Loop 状態
MoodState               # PAD 3次元 (-5〜+5)
ShortTermMemoryDB       # 段階圧縮記憶（通常領域）
KeyMemoryStore          # key memory（保護領域、7日間フル保持）
EventPackage            # 1イベント処理結果（全エージェント出力を格納）
IntrospectionMemo       # 内省3工程の出力
EmotionIntensityResult  # 感情強度判定（low/medium/high）
CheckResult             # 4チェッカーAI結果
```

### ストレージ構造（1キャラクター = 1ディレクトリ）

```
backend/storage/character_packages/{character_name}/
├── package.json                     # 最終キャラクターパッケージ（毎日更新）
├── checkpoint.json                  # レジュームチェックポイント（SID名+キャラ名の二重保存）
├── 00_profile.md                    # 人間可読プロフィール
├── agent_logs.json/.md              # エージェント思考ログ
├── key_memories/
│   └── day_NN.json                  # key memory（日別、7日間フル保持、圧縮対象外）
├── short_term_memory/
│   └── day_NN.json                  # 短期記憶DBスナップショット（段階圧縮済み）
├── mood_states/
│   └── day_NN.json                  # ムード状態スナップショット
├── daily_logs/
│   ├── Day_N.md                     # 包括的MDアーカイブ（コスト記録付き）
│   └── day_NN/
│       ├── 001_full.json            # フルアクションログ
│       ├── 002_summary.json         # ~50%要約
│       └── 003_summary.json         # さらに圧縮（段階的忘却）
└── diaries/
    └── day_NN.md                    # 日記（独立DB、記憶ソースではなく参照扱い）
```

---

## 記憶システム

3層構造 + 行動履歴バッファ + ムード状態で構成される。**Retrieval機構は一切使用しない**（7日間という短期スパンは全文ベタ貼りで対応）。

### 3層記憶構造

| 層 | 生成時期 | 圧縮 | 保持期間 | 用途 |
|----|---------|------|---------|------|
| **自伝的エピソードDB** | Day 0 (A-3) | なし | 7日間不変 | 全エージェントに全文ベタ貼り |
| **短期記憶（通常領域）** | 日次更新 | 4段階LLM圧縮 | 段階的忘却 | 当日400字→1日前200字→2日前80字→3日前以上20字 |
| **key memory（保護領域）** | 日次抽出 | なし | 7日間フル保持 | 1日1個・300字以内・書換不可 |

**日記本文ストア**: 7日分全文保持（圧縮なし）。記憶ソースではなく「参照」として渡す。

### PADムードモデル

- **3次元**: Valence / Arousal / Dominance（各 -5 〜 +5）
- **イベント単位更新**: 統合エージェントが各イベント後にPADを更新
- **日次集約**: Peak-End Rule（ピーク時 × α + 終端時 × β、気質で変調）
- **Carry-over**: 減衰係数λ（気質から自動導出）を適用し翌日へ持ち越し。|値| < 閾値で0リセット

---

## LLMティアシステム

3ティア構成で、各ティアにフォールバックチェーンを持つ。

```
opus ティア:
  Claude Opus 4.6 → (失敗時) → Gemini 3.1 Pro → (429時) → Gemini 2.0 Flash

sonnet ティア:
  Claude Sonnet 4.6 → (失敗時) → Gemini 2.5 Pro → (429時) → Gemini 2.0 Flash

gemini ティア:
  Gemini 2.5 Pro → (429/ResourceExhausted時のみ) → Gemini 2.0 Flash
```

**Gemini 2.5 Pro Thinking Token修正**: `max_output_tokens` を自動4倍拡張（最低16384）。Thinking tokenが出力予算を全消費しゼロ出力になる問題を回避。

**動的APIキーシステム**: フロントエンドのlocalStorageからWebSocket経由で全バックエンドチェーンに伝播。環境変数より動的キーを優先。

---

## 品質プロファイル

| Profile | Director | Worker | Evaluators | リトライ上限 | 想定用途 |
|---------|----------|--------|------------|-------------|---------|
| `high_quality` | opus | sonnet | 全7種ON | 4 | 本番提出 |
| `standard` | sonnet | sonnet | 5種ON | 3 | 推奨バランス |
| `fast` | sonnet | gemini | 3種ON | 2 | 高速検証 |
| `draft` | sonnet | gemini | 2種ON (SchemaValidator + DistributionValidator) | 2 | 開発・テスト |

---

## 技術スタック

| レイヤー | 技術 | 選定理由 |
|---------|------|---------|
| **Backend API** | FastAPI (Python) | 非同期処理 + WebSocket ネイティブサポート |
| **リアルタイム通信** | WebSocket | エージェント思考過程のライブストリーミング |
| **LLM (高ティア)** | Claude Opus 4.6 | Creative Director・統合エージェント等の高密度タスク |
| **LLM (中ティア)** | Claude Sonnet 4.6 | Worker群・検証エージェント |
| **LLM (低ティア/フォールバック)** | Gemini 2.5 Pro / 2.0 Flash | コスト最適化・クォータ超過時の自動切替 |
| **データバリデーション** | Pydantic v2 | 52パラメータ + 全エージェント出力の型安全性保証 |
| **永続化** | ファイルシステム (JSON + Markdown) | 1キャラクター=1ディレクトリ、人間可読 |
| **Web検索** | DuckDuckGo Search API | Creative Directorのリサーチ用 |
| **Frontend** | Vanilla HTML/CSS/JS (SPA) | 依存ゼロ、エージェント思考ストリーミングUI |
| **APIクライアント** | Anthropic Python SDK / Google Generative AI | 直接API呼び出し（SDK経由） |

---

## プロジェクト構造

```
.
├── backend/
│   ├── main.py                          # FastAPI エントリポイント + WebSocket + REST API
│   ├── config.py                        # LLMモデル定義・品質プロファイル・APIキー管理
│   ├── regeneration.py                  # アーティファクト再生成（依存グラフ + カスケード）
│   ├── agents/
│   │   ├── context_descriptions.py      # wrap_context() — what/why/how 3点注釈
│   │   ├── creative_director/
│   │   │   └── director.py              # Tier-1: 自律Tool Callingループ
│   │   ├── master_orchestrator/
│   │   │   └── orchestrator.py          # Tier 0: Phase逐次制御 + チェックポイント
│   │   ├── phase_a1/
│   │   │   ├── orchestrator.py          # マクロプロフィール + 言語的表現
│   │   │   └── workers/                 # 8+1 Workers
│   │   ├── phase_a2/
│   │   │   ├── orchestrator.py          # 15 Workers + 認知導出
│   │   │   └── workers/                 # 10パラメータ + 4規範層 Workers
│   │   ├── phase_a3/
│   │   │   ├── orchestrator.py          # エピソード Planner + BiasAuditor
│   │   │   └── writers/                 # カテゴリ別 Episode Writers
│   │   ├── phase_d/
│   │   │   ├── orchestrator.py          # 脚本AI + アーク設計
│   │   │   ├── capabilities_agent.py    # 5ツールエージェンティック能力生成
│   │   │   └── workers/                 # World/Characters/Arc/Events Workers
│   │   ├── daily_loop/
│   │   │   ├── orchestrator.py          # Day 1-7 外層/内層ループ制御
│   │   │   ├── activation.py            # 動的パラメータ活性化
│   │   │   ├── verification.py          # 裏方出力検証 (§4.6b)
│   │   │   ├── diary_critic.py          # 日記Self-Critic
│   │   │   ├── third_party_reviewer.py  # 第三者レビュアー
│   │   │   ├── linguistic_validator.py  # 言語的表現バリデーション
│   │   │   ├── next_day_planning.py     # 翌日予定追加エージェント
│   │   │   └── checkers.py             # 4並列チェッカーAI
│   │   └── evaluators/
│   │       └── pipeline.py              # 7種Evaluator統合パイプライン
│   ├── models/
│   │   ├── character.py                 # 全Day 0 Pydantic v2モデル
│   │   └── memory.py                    # Daily Loop状態モデル
│   ├── schemas/                         # JSON Schema定義
│   ├── storage/
│   │   ├── md_storage.py               # Markdown/JSON永続化 + チェックポイント
│   │   └── character_packages/          # 生成済みキャラクターデータ
│   ├── tools/
│   │   ├── llm_api.py                   # 統合LLM呼び出し + TokenTracker + フォールバック
│   │   └── agent_utils.py              # エージェントユーティリティ
│   └── websocket/
│       └── handler.py                   # WebSocketManager + 思考ストリーミング
├── frontend/
│   ├── index.html                       # SPA エントリポイント
│   ├── css/style.css                    # スタイルシート
│   └── js/
│       ├── app.js                       # アプリケーションロジック
│       ├── websocket.js                 # WebSocket通信
│       └── renderer.js                  # UI レンダリング
├── docs/                                # ドキュメント・アーキテクチャ図
├── specification_v10.md                 # システム仕様書 v10（完全版）
├── script_ai_app_specification_v2.md    # Day 0仕様書 v2
├── PROJECT.md                           # 開発記録（35ステージ）
├── requirements.txt                     # Python依存パッケージ
├── LICENSE                              # MIT License
└── README.md
```

---

## Quick Start

### 前提条件

- Python 3.11+
- Anthropic API Key（必須）
- Google AI API Key（Gemini使用時）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/menma22/AI_character_story_generater.git
cd AI_character_story_generater

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を編集して API キーを入力
```

### 起動

```bash
# サーバー起動
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001

# ブラウザで http://localhost:8001 を開く
```

### 使い方

1. ブラウザで `http://localhost:8001` にアクセス
2. 画面右上の設定ボタンからAPIキーを入力（フロントエンドからも設定可能）
3. 品質プロファイルを選択（`draft` で高速テスト、`high_quality` で最高品質）
4. 生成を開始 → エージェントの思考過程がリアルタイムでストリーミング表示される
5. Day 0完了後、6タブダッシュボード（コンセプト/プロフィール/パラメータ/エピソード/イベント/日記）で結果を閲覧
6. 各アーティファクトの再生成ボタン/編集ボタンで調整可能（自然言語指示 + カスケード再生成対応）
7. 「日記生成」で Day 1-7 の日次ループを実行

---

## API・WebSocket仕様

### REST API

| エンドポイント | メソッド | 内容 |
|--------------|--------|------|
| `/` | GET | フロントエンド配信 |
| `/api/profiles` | GET | 品質プロファイル一覧 |
| `/api/cost` | GET | トークンコスト情報 |
| `/api/packages` | GET | 生成済みキャラクター一覧 |
| `/api/packages/{name}` | GET | 個別キャラクターデータ |
| `/api/debug/thoughts` | GET | エージェント思考履歴 |

### WebSocket (`/ws`)

**クライアント → サーバー:**

| アクション | 内容 |
|-----------|------|
| `generate_character` | キャラクター生成開始（テーマ・プロファイル・APIキー） |
| `resume_generation` | チェックポイントからレジューム |
| `regenerate_artifact` | アーティファクト再生成（自然言語指示 + カスケード警告） |
| `save_artifact_edit` | 手動JSON編集の保存（Pydanticバリデーション付き） |
| `run_diary_generation` | Day 1-7 日次ループ実行 |
| `get_status` | 現在の生成状態取得 |

**サーバー → クライアント:**

| イベント | 内容 |
|---------|------|
| エージェント思考ストリーミング | リアルタイムの思考過程表示 |
| Phase Tracker更新 | Creative Director → A-1 → A-2 → A-3 → D の進捗 |
| コスト更新 | 各Day完了後の `send_cost_update(token_tracker.summary())` |
| 詳細ハートビート | 生成進捗の詳細情報 |

### トークンコスト追跡

`TokenTracker` が全LLM呼び出しのinput/output/cacheトークンとUSDコストをモデル別に記録。各Dayの `Day_N.md` に6ステップ分のコスト表を自動付与。

---

## 先行研究・理論的背景

本システムの設計は以下の理論・研究に基づく:

| 領域 | 理論・研究 | システムでの適用箇所 |
|------|-----------|-------------------|
| 性格心理学 | Cloninger's Temperament and Character Inventory | 52パラメータの気質・性格分類体系 |
| 二重過程理論 | Reflective-Impulsive Model (Strack & Deutsch) | Impulsive Agent / Reflective Agent の二系統構造 |
| 自伝的記憶 | McAdams' Life Story Theory | Phase A-3の5カテゴリエピソード生成 |
| 価値観理論 | Schwartz Theory of Basic Values (19値) | 規範層のSchwartz価値スケルトン |
| 道徳心理学 | Moral Foundations Theory (Haidt) | MFT 6基盤 |
| 自己不一致理論 | Higgins' Self-Discrepancy Theory | 統合エージェントのIdeal/Ought不一致評価 |
| 自己知覚理論 | Bem's Self-Perception Theory (1972) | 内省エージェントのSelf-Perception工程 |
| 暗黙的性格 | Nisbett & Wilson (1977) / McClelland (1989) | 隠蔽原則（Implicit/Explicit Asymmetry） |
| 脚本理論 | McKee's Story Structure | Want/Need/Ghost/Lie scaffolding |
| 物語アーク | Vonnegut's Story Shapes | Phase DのNarrativeArcDesigner |
| LLMバイアス | Nature Humanities (2026) — Redemption Bias | BiasAuditor + エピソード分布制約 |
| エージェントシミュレーション | Generative Agents (Park et al. 2023) | 翌日予定追加エージェント（差別化要素） |
| 感情モデル | PAD Emotional State Model | 3次元ムード状態 + Peak-End Rule |
| 気分理論 | Panksepp 7 Basic Emotions / OCC Model | 感情カテゴリ参考知識としてプロンプト同梱 |

---

## License

MIT

## Contributing

Issue・Pull Request を歓迎します。バグ報告や機能提案は [Issues](https://github.com/menma22/AI_character_story_generater/issues) からどうぞ。
