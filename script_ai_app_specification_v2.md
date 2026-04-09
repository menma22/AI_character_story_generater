# 脚本生成AIアプリケーション 詳細設計書 v2

> サードインテリジェンス Bコース課題 / AIキャラクター日記システム v10 の Phase A-1/A-2/A-3/D を実装するエージェンティック・アプリケーション
>
> 作成日:2026-04-10
> 前提ドキュメント:`specification_v10.md`(AIキャラクター日記システム ─ アーキテクチャ完全版 v10)
>
> v1 → v2 の主要変更点の要約は **付録 C** に時系列リファレンスとしてまとめている。本文は常に現状仕様のみを記述する方針を取り、過去バージョンの撤回・再設計の経緯は本文中に残さない。

---

## 目次

1. 背景と目的
2. 設計思想(動かない前提)
3. 全体アーキテクチャ
4. Tier -1:Creative Director
5. Tier 0:Master Orchestrator
6. Tier 1:Phase Orchestrators
7. Tier 2:Worker Agents
8. Tier 3:Evaluators
9. データ構造(脚本パッケージ JSON schema)
10. 対話モード仕様
11. UI 設計
12. 技術スタック
13. 実装計画
14. コスト見積もり
15. 未決事項

---

## 1. 背景と目的

### 1.1 本アプリケーションの位置付け

本アプリケーション(以下「脚本AIアプリ」)は、サードインテリジェンス Bコース課題「AIキャラクターに1週間分の日記を書かせる」ために、v10 仕様書で定義された日記生成システムの **Day 0 フェーズを担うフロントローダ** である。

具体的には、v10 の Phase A-1(マクロプロフィール生成)、Phase A-2(ミクロパラメータ生成)、Phase A-3(自伝的エピソード生成)、Phase D(**7 日分イベント列の一括事前生成**)の 4 つのフェーズを、エージェンティックに実行し、完結した「脚本パッケージ(character package + weekly events store)」を生成する。

**v1 からの決定的な変更点:** v1 における Phase D は「世界モデル構築」(世界設定 + 7 日分予定骨格 + 葛藤アーク)であった。v10 では Phase D の責務は「**脚本AI が 7 日間の物語アークを俯瞰した上で、各日 4〜6 件 × 7 日 = 28〜42 件のイベント列を一括で事前生成する**」に完全置換されている。各イベントには(既知/未知 × 予想外度)の 2 軸メタデータと「このキャラに意味を持つ理由」が必須タグとして付与される。日次ループ中の新規イベント生成は一切行わず、Day 1〜7 は事前生成されたイベント列を順次注入するだけになる。この設計により、Day 5 山場への伏線を Day 1〜4 に仕込む脚本的設計が Day 0 段階で可能になる。

日記生成本体(Day 1〜7 の日次ループ)は本アプリの範囲外であり、別モジュールとして実装される。Phase B(エコーチェンバー構築)と Phase C(擬似経験構築)は v10 でも本実装保留扱いとされており、本アプリでも実装しない。脚本AIアプリが出力する脚本パッケージは、日記生成本体への入力として機械可読な形で渡される。

### 1.2 課題の評価軸との対応

課題資料「評価について」で明示された評価軸は以下の二つ:

| 評価軸 | 課題資料の文言(原文) | 本アプリが貢献する経路 |
|---|---|---|
| **出力の面白さ** | 人間が読んで面白いか、続きが気になるか、キャラクターとしての個性が感じられるか。AIがありがちな無難な文章や一般論を並べているだけではなく、そのキャラクターならではの視点や考察、語り口、感情の癖、そして人間のような「リアリティ」が表れているか | Tier -1 Creative Director が脚本論ベストプラクティスに基づいて面白さを評価し、Tier 2 Workers が心理学的に根拠のある内部パラメータを生成する。個性は豊かな内部状態から emergent に立ち上がる |
| **技術・設計の面白さ** | アプローチに独自性があるか、実装に工夫があるか、そしてその工夫が出力の質に結びついているか。できるだけAIが自律的に判断し行動できる、スケーラブルな設計が好ましい | Orchestrator-Workers パターンと Evaluator-Optimizer パターンを組み合わせた階層的エージェンティック設計により、「1 AI = 1 大きな出力」の限界を回避し、各エージェントの責任範囲を明確に分離する。これは同じアーキテクチャで任意のキャラクターを生成できるスケーラブルな設計である |

### 1.3 運営サンプルとの差分

運営配布の `AssignB_sample.ipynb` は、単一のキャラクタープロンプト + 事前定義された7日分の EVENTS リスト + 100字の前日要約だけを保持するシンプルなアーキテクチャを提示している。本アプリは以下の点でサンプルを明確に超えることを目指す:

| 項目 | 運営サンプル | 本アプリ |
|---|---|---|
| Persona 層 | 固定テキストプロンプト(数行) | 気質23 + 性格27 + 対他者認知2 の 52 パラメータ + マクロプロフィール + 規範層 + 自伝的エピソード 5〜8 個 |
| Events 層 | 事前定義リスト 7 件 | 7 日分 × 各日 4〜6 件 = 28〜42 件の構造化イベント列 + 既知/未知 × 予想外度の 2 軸メタデータ + 「このキャラに意味を持つ理由」 + 物語アーク上の役割 |
| 生成方式 | 単一 LLM 呼び出し | 4 層の階層的エージェント + Evaluator-Optimizer ループ |
| 個性の発現経路 | 語尾指定のみ | 気質依存の知覚フィルター(裏方) + 規範層(主人公AI) + 両者のギャップ層 |
| 時間的連続性 | 100 字の前日要約 | 7 日間物語アーク + Day 5 山場への伏線 + 前日の跳ね返り構造(Phase D で事前設計) |
| 脚本的設計 | なし | Day 5 山場 / 葛藤強度アーク / 伏線仕込み / 物語連続性制約を Phase D で一括設計 |

### 1.4 本仕様書のスコープ

本仕様書が扱う範囲:

- 脚本AIアプリの全体アーキテクチャ(4 層エージェント階層)
- 各エージェントの責任、入出力、プロンプト設計の方針
- 対話モードとユーザーインタラクション
- 出力データ構造(脚本パッケージ JSON schema)
- UI 設計と画面遷移
- 技術スタック
- 実装計画

本仕様書が扱わない範囲(v10 仕様書または別モジュールの責任):

- Phase B エコーチェンバー(v10 でも本実装保留、概念のみ維持)
- Phase C 擬似経験構築(v10 でも本実装保留、概念のみ維持)
- 日次ループ本体(Day 1〜7 の実行)── Perceiver、Impulsive Agent、Reflective system、行動決定エージェント、情景描写・後日譚生成エージェント、価値観違反チェック、内省エージェント、日記生成エージェント、key memory 抽出、記憶圧縮、翌日予定追加エージェントなどすべてを含む
- Reflective-Impulsive Model の実行時挙動
- 現在ムード(PAD 3 次元)の carry-over と日記生成

---

## 2. 設計思想(動かない前提)

### 2.1 仕事の分担がすべて

**1 個の AI が 1 個の出力で 52 パラメータ + マクロプロフィール + エピソードを全部決めることは絶対にできない**。この認識が本アプリの設計の出発点である。単一 LLM への負荷集中は:

- 出力の質が劇的に下がる(コンテキスト肥大化、焦点ぼけ)
- 部分的な不整合が大量に発生する
- 再生成のコストが爆発する
- デバッグ不可能になる

したがって、本アプリは Anthropic の "Building Effective Agents" ガイドに沿った **Orchestrator-Workers パターン** を採用し、各フェーズをさらに細かい Worker に分解する。各 Worker は自分の責任範囲だけを担当し、上位 Orchestrator が結果を統合する。

### 2.2 順序は譲らない:キャラ先行、イベント列後行

Phase A-1 → A-2 → A-3 → D の順序は絶対に動かさない。理由:

- 7 日分のイベント列はキャラクターに応じて設計されるべき(逆は成立しない)
- 葛藤誘発型イベント(予想外度「高」)はキャラクターの価値観・理想・自伝的エピソードを脅かす形で生成される必要があり、それはキャラクターが確定した後でしかできない
- 自伝的エピソードはマクロとミクロの両方を参照するため、後段
- 7 日分のイベント列は、気質・価値観・夢・自伝的エピソードを踏まえて「このキャラの 7 日間ならこういう週になる」「Day 5 山場はこの価値観が揺さぶられる形が一番刺さる」「伏線はどこに仕込むべきか」という形で構築される

### 2.3 概念レベルの方向性を最初に決める

パラメータ値や具体的な文字列を生成する前に、**概念的なキャラクターの方向性**を決める層が必要である。この層では:

- どういうタイプのキャラクターか(一言で)
- 物語の中心的葛藤は何か
- 何が面白さの源泉か
- どのような心理的テーマを持つか
- 参考となる既存物語・キャラクター像はあるか

を自然言語で決定する。この概念層が確定してから、マクロプロフィール・ミクロパラメータ・エピソード・世界モデルの具体化に入る。これが Tier -1 Creative Director の役割である。

### 2.4 Evaluator-Optimizer による品質保証

Creative Director の内部、および各 Phase の出力に対して、**ダメ出しエージェント**が走る。ダメ出しは以下を評価する:

- AI っぽい無難さが出ていないか
- 設定が面白いか
- キャラ内部の整合性は取れているか
- 脚本論的に機能するか
- v10 仕様書の制約(redemption bias 対策、Phase D の 2 軸メタデータ必須化、「このキャラに意味を持つ理由」必須、Day 5 山場要件、分布制約、規範層に可変サブモジュールを持たない方針、など)を満たしているか

評価で不合格となれば該当エージェントに再生成指示が戻る。**この再生成ループは最大4回まで**。4回以内に合格が出なければ、暫定ベストを採用して次のフェーズに進む(無限ループ防止)。

### 2.5 動的 Web 検索

Creative Director は Web 検索ツールを持ち、**必要と判断したときだけ**検索する。検索するタイミングは固定しない(プロンプトで「必ず検索せよ」とはしない)。代わりに「設定が濃密になるために調べた方がよい情報があれば検索せよ」という指示を与え、判断を委ねる。典型的な検索対象:

- 参考となる既存物語(同系統のジャンル、同系統のキャラクター設定)
- 歴史的事実(歴史人物を扱う場合)
- 専門知識(キャラが特定の職業を持つ場合、その職業の実態)
- 言語的特徴(方言、時代考証、業界用語)

### 2.6 知識注入はシステムプロンプト直書きを基本とする

Creative Director に注入する「脚本論のベストプラクティス」「個性的なキャラクター造形の原則」は、システムプロンプトに直接書く。Claude Opus 4.6 のコンテキストウィンドウは十分大きく、数千字規模の原則集であれば問題なく扱える。

分量が膨大になる場合(例:過去の参考キャラクター事例集、詳細な心理学理論解説)は、外部 Markdown ファイルとして `./reference/` 以下に配置し、Creative Director が file_read ツール経由で必要時に読む構成とする。

### 2.7 バックエンドは必須

Claude Agent SDK は Python または TypeScript のサーバーサイドでのみ動作する。したがって本アプリはブラウザだけで完結せず、Python バックエンド(FastAPI)+ HTML フロントエンドの構成をとる。ブラウザとバックエンドは WebSocket で通信し、エージェントの思考過程をリアルタイムストリーミング表示する(Cursor Composer / Claude Code と同じ UX)。

### 2.8 透明性の確保

Anthropic の "Building Effective Agents" ガイドが強調する 3 原則の一つ「Make the reasoning process visible」を本アプリでも厳守する。すべてのエージェント呼び出し、ツール使用、ダメ出しと再生成、内部ループの反復回数は、UI 上でユーザーが確認できる形で表示する。隠れた処理はない。

### 2.9 ツール設計 > オーケストレーション複雑化

"Good tools > complex orchestration"(Anthropic) の原則に従い、階層を必要以上に深くしない。各エージェント間の受け渡しデータ構造(JSON schema)を先に固め、エージェント間のインターフェースが明確になるよう設計する。階層を追加するのは、それが品質改善に直接寄与する時だけに限る。

### 2.10 トークン効率とキャッシュの積極活用

本アプリは多階層のエージェント構成であり、何も工夫しないと LLM 呼び出しのトークン消費が爆発する。したがって、以下の 3 つの柱でトークン効率を確保する:

**(a) Prompt Caching(Anthropic API の KV キャッシュ機能)の活用**
長いシステムプロンプトや、Phase 間で繰り返し参照される中間成果物(concept_package、macro_profile、micro_parameters など)を Prompt Caching の対象として登録し、後続の呼び出しで再利用する。これにより、入力トークン料金の大幅削減とレイテンシ短縮が同時に得られる。

**(b) コンテキストの最小化**
各 Worker に渡すコンテキストは「その Worker が生成に必要な情報だけ」に絞る。Phase Orchestrator の責任で、Worker 起動前にコンテキストを構築する。macro_profile を 8 つの Worker 全員に丸ごと渡すような冗長な設計は避ける。

**(c) 出力の構造化**
Gemma 4 の native JSON output 機能、Claude の tool use / structured output 機能を使い、Worker の出力から無駄な説明文や前置きを排除する。LLM が返す自然言語の冗長さをスキーマで抑制する。

詳細は §14.5 を参照。

### 2.11 チェッカー層のオン/オフ可能設計

評価層(Tier 3 Evaluators)は品質を大きく向上させる一方で、トークン消費量に非常に大きな影響を与える。すべての生成で全 Evaluator を走らせるのは過剰であり、用途に応じた切り替えが必要である。

本アプリは以下の原則でチェッカー層の有効/無効を設計する:

**(a) Tier -1 Creative Director の Self-Critique は常時有効**
最上流の概念決定は、脚本パッケージ全体の質に決定的な影響を与える。ここで手を抜くと、下流の全 Phase が低品質な concept_package を起点に動くことになり、リカバリが不可能になる。したがって **Tier -1 の Self-Critique は常時オンを維持する**(反復回数はプロファイルによって調整可能)。

**(b) 後段の Tier 3 Evaluators はオン/オフ可能**
Phase A-1 / A-2 / A-3 / D に対する ConsistencyChecker、BiasAuditor、InterestingnessEvaluator は、ユーザーが選択するプロファイルによって有効/無効を切り替える。本番提出用の高品質生成ではすべて有効化し、試作や素早い確認ではすべて無効化する。

**(c) SchemaValidator は常時有効**
SchemaValidator は LLM を使わないルールベース関数であり、コストはほぼゼロ。構造的な破損を検出する最低限の安全網として、どのプロファイルでも常に走らせる。

具体的なプロファイル設計は §8.9 を参照。

---

## 3. 全体アーキテクチャ

### 3.1 4 層エージェント階層

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier -1:Creative Director(Claude Opus 4.6)
  役割:概念方向性の決定、面白さの評価、再生成指示
  内部ループ:Planning → Generation → Self-Critic → Refinement(最大4回)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ↓ concept package
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier 0:Master Orchestrator(Claude Opus 4.6)
  役割:Phase の起動順序管理、Phase 間データ受け渡し、ユーザー対話
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ↓
       ┌──────────┬───────────┬───────────┬──────────┐
       ↓          ↓           ↓           ↓          ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier 1:Phase Orchestrators(Claude Sonnet 4.6 または Opus 4.6)
  Phase A-1 Orchestrator  マクロプロフィール
  Phase A-2 Orchestrator  ミクロパラメータ
  Phase A-3 Orchestrator  自伝的エピソード
  Phase D  Orchestrator  世界モデル
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ↓
       ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
       ↓     ↓     ↓     ↓     ↓     ↓     ↓     ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier 2:Worker Agents(Gemma 4 26B MoE)
  各 Phase の細分化された単一責任 Worker 群
  並列実行可能(依存グラフを遵守)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier 3:Evaluators(Claude Sonnet 4.6)
  ConsistencyChecker / BiasAuditor / InterestingnessEvaluator
  不合格時は該当 Worker/Phase に再生成指示(最大4回)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          ↓ character package
                          ↓
                      日記生成本体へ
```

### 3.2 パターン分類

本アプリは以下のエージェンティックパターンを組み合わせる(いずれも Anthropic "Building Effective Agents" で定式化されたもの):

| パターン | 適用箇所 | 目的 |
|---|---|---|
| **Orchestrator-Workers** | Tier 1 → Tier 2 | Phase 内の subtasks を動的に分配。予測可能でない subtasks に対応 |
| **Parallelization(sectioning)** | Tier 2 内 | 独立した Worker を並列実行して高速化 |
| **Evaluator-Optimizer** | Tier 3 → Tier 2 / Tier 1 | 生成結果を評価し、不合格時に再生成ループを回す |
| **Routing** | Tier 0 | ユーザー入力を分類して適切な Phase Orchestrator に振り分ける |
| **Prompt Chaining** | Tier -1 内部 | Planning → Generation → Self-Critic → Refinement の直列処理 |
| **Augmented LLM** | 各エージェント | 各エージェントは web search / file operations / custom tools を持つ |

### 3.3 データフロー

Phase 間の依存関係と受け渡しデータ:

```
[User Input]
  ├ 自由入力(チャット / フォーム)
  ├ または "完全自動生成" ボタン
  ↓
[Tier -1: Creative Director]
  出力:concept_package
    ├ character_concept: キャラクター設定の大まかな概要
    │   (キャラの核・背景・性格傾向・抱えているもの・魅力の源泉を
    │    しっかり書き込んだ一段落の概念記述。下位エージェントが
    │    マクロプロフィール・ミクロパラメータ・自伝的エピソードを
    │    具体化するときの拠り所となる)
    ├ story_outline: 物語設定の大まかな概要
    │   (世界観の概要・7 日間を通した緩いあらすじ・この 1 週間の
    │    特徴・通奏低音となる出来事をしっかり書き込んだ一段落の
    │    概念記述。下位エージェントが世界モデル・予定骨格・
    │    葛藤誘発型イベントを具体化するときの拠り所となる)
    ├ narrative_theme: 物語的テーマ
    ├ interestingness_hooks: 面白さの源泉リスト
    ├ genre_and_world: ジャンル・世界観のヒント
    ├ reference_stories: Web 検索で見つけた参考作品
    └ critical_design_notes: 設計上の注意点(Opus が特記すべきと判断したもの)
  ↓
[Tier 0: Master Orchestrator]
  受け取り:concept_package
  実行:Phase A-1 → Phase A-2 → Phase A-3 → Phase D の順に起動
  ↓
[Phase A-1: マクロプロフィール生成]
  入力:concept_package
  出力:macro_profile
    ├ basic_info / social_position / family / current_life
    ├ dream_timeline / voice_fingerprint / values_core
    ├ secrets / relationship_network
  ↓
[Phase A-2: ミクロパラメータ生成]
  入力:concept_package + macro_profile
  出力:micro_parameters
    ├ temperament_parameters (23 個)
    ├ personality_parameters (27 個)
    ├ social_cognition (2 個)
    ├ cognitive_parameters (自動導出 4 個)
    ├ schwartz_values_skeleton (19 価値の強弱)
    ├ moral_foundations (MFT 6+)
    ├ ideal_self / ought_self (方向性のみ)
    └ goals_and_dreams (長中期骨格)
  ↓
[Phase A-3: 自伝的エピソード生成]
  入力:concept_package + macro_profile + micro_parameters
  出力:autobiographical_episodes
    └ episodes: 5〜8 個のエピソード(narrative + metadata)
  ↓
[Phase D: 脚本AI による 7 日分イベント列の一括事前生成]
  入力:concept_package + macro_profile + micro_parameters + autobiographical_episodes
  出力:weekly_events_store
    ├ world_context: 薄い世界観・時代設定(マクロの社会的位置と整合)
    ├ supporting_characters: 周囲の人物 5〜7 人(関係性ネットワークを拡張)
    ├ narrative_arc: 7 日間の物語アーク(Day 5 山場、伏線配置、物語連続性)
    ├ conflict_intensity_arc: 7 日間の葛藤強度アーク
    └ events: 28〜42 件のイベント(各日 4〜6 件 × 7 日)
        各イベントは以下のメタデータを持つ:
          - known_to_protagonist: true / false
          - source(knownの場合のみ): "routine" / "prior_appointment"
            ※ "protagonist_plan" は Phase D では生成しない(日次ループで
              翌日予定追加エージェントが動的挿入する唯一の経路)
          - expectedness: "low" / "medium" / "high"(予想外度)
          - time_slot: 朝 / 午前 / 昼 / 午後 / 夕方 / 夜 / 深夜
          - content: 出来事の具体的記述(3〜5 文)
          - meaning_to_character: このキャラの気質・価値観・自伝的エピソード
            のどの要素と結びつくかの明示的記述(最重要メタデータ)
          - narrative_arc_role: "day5_foreshadowing" /
            "previous_day_callback" / "daily_rhythm" / "standalone_ripple"
  ↓
[脚本パッケージ確定]
  = concept_package + macro_profile + micro_parameters
    + autobiographical_episodes + weekly_events_store
  ↓
[日記生成本体へ](本アプリの範囲外)
```

### 3.4 実行モード

本アプリは以下の 3 つの実行モードをサポートする:

**(1) 完全自動モード**
ユーザーは何も入力せず「完全自動生成」ボタンを押すだけ。Creative Director が完全にゼロから概念を決定し、全 Phase を自動実行する。ユーザーは生成過程と結果を見るだけ。

**(2) テーマ指定モード**
ユーザーが自然言語で「こんな感じのキャラがいい」「歴史人物を現代に」といったヒントを与える。Creative Director はそれを起点に概念を決定し、残りは自動実行する。

**(3) 共同編集モード**
ユーザーがチャット形式で Master Orchestrator と対話する。部分的に手動入力したり、生成済みの項目を編集したり、「ここをこう変えて」と自然言語で指示したりできる。Master Orchestrator が影響範囲を判定し、必要な Worker を呼んで再生成と整合性チェックを行う。

3 モードの切り替えはアプリ起動後も可能。例えば、最初は完全自動で生成してから、気に入らない部分だけ共同編集モードで修正する、といった使い方ができる。

---

## 4. Tier -1:Creative Director

### 4.1 役割と責任

Creative Director は本アプリの **創造的な判断を司る最上位の AI** である。他のすべてのエージェントは Creative Director が決定した「概念的方向性」に従って具体化を進める。Creative Director 自身は個別のパラメータ値や詳細文字列を生成しない。代わりに、**どのような方向性で生成すべきかを自然言語で決定する**。

具体的な責任:

- ユーザーの入力(または空)から、物語とキャラクターの概念的方向性を決定する
- 脚本論・キャラ造形のベストプラクティスに基づいて、面白さの源泉を特定する
- 必要に応じて Web 検索で参考作品を調査する
- 各 Phase の出力を評価し、面白さ・整合性・AI っぽさを判定する
- 不合格の場合、Master Orchestrator に再生成指示を出す
- 最終的な脚本パッケージの品質責任を負う

Creative Director が決定**しない**こと:

- 気質 23 パラメータの具体的な数値(Phase A-2 Worker の責任)
- マクロプロフィールの各フィールドの具体的文字列(Phase A-1 Worker の責任)
- エピソードの narrative 本文(Phase A-3 Worker の責任)
- 7 日間の具体的な予定や時刻(Phase D Worker の責任)

この責任分離が重要である。Creative Director が具体化まで踏み込むと、下位の Worker の余地がなくなり、かつ Creative Director のコンテキストが肥大化して創造的判断の質が落ちる。

### 4.2 使用モデル

**Claude Opus 4.6** 一択。理由:

- 概念的な判断と面白さの評価は、現時点で最も賢い LLM が担うべき
- コンテキストウィンドウが大きく、脚本論の原則集 + ユーザー対話履歴 + 参考資料を余裕で保持できる
- 深い推論(extended thinking)を用いた複数回の self-critique が可能
- Web 検索ツールや file operations との統合が洗練されている

### 4.3 内部ループ構造

Creative Director は単一の LLM 呼び出しで答えを出すのではなく、**内部で Prompt Chaining を回す**。この設計は本仕様書の重要な特徴である。

```
【Creative Director 内部ループ】

Step 1: Planning
  ユーザー入力を受けて、以下を計画する:
  - まず何を決めるべきか(ジャンル?主人公?時代?)
  - 調査が必要な情報はあるか
  - 参考となる既存作品は何か

Step 2: Research (optional)
  Planning Step で必要と判断された場合のみ:
  - Web 検索を実行
  - 参考作品の情報を収集
  - 歴史的事実・専門知識を確認

Step 3: Concept Generation (初回 draft)
  以下を生成:
  - character_concept(一段落、500〜1000 字)
    キャラクター設定の大まかな概要・特徴・核・背景をしっかり書く
  - story_outline(一段落、500〜1000 字)
    物語設定の大まかな概要・7 日間の緩いあらすじ・通奏低音をしっかり書く
  - narrative_theme(1〜2 文)
  - interestingness_hooks(3〜5 個)
  - genre_and_world(1 段落)

Step 4: Self-Critique
  生成された concept に対して、以下の観点で自己評価:
  - AI っぽい無難さが出ていないか
  - 面白さのフックは具体的で鋭いか
  - 内部的な矛盾はないか
  - v10 仕様書の設計思想(気質/規範の分離、emergent な個性、など)と
    整合するか
  - 脚本論的に機能する構造か(葛藤の種、Want/Need の構造、ギャップの
    存在)

  出力:
  - critique_report: 問題点のリスト
  - verdict: pass / fail / refine

Step 5: Refinement (verdict が pass 以外なら)
  critique_report に基づいて concept を修正

Step 6: 反復判定
  - verdict == pass → 確定、次のフェーズへ
  - verdict != pass && 反復回数 < 4 → Step 3 に戻る(修正して再生成)
  - 反復回数 == 4 → 暫定ベストを採用して次のフェーズへ(警告フラグ付き)

最大反復回数:4 回(無限ループ防止)
```

### 4.4 Creative Director のシステムプロンプト構造

Creative Director には、システムプロンプトで以下の知識を直接注入する。

```
あなたは Creative Director です。AI キャラクター日記システム v10 の
最上位エージェントとして、物語とキャラクターの創造的方向性を決定します。

【あなたのミッション】
ユーザー(またはあなた自身)が決めた世界観と大枠から、
AI キャラクターに 1 週間分の日記を書かせるための「脚本パッケージ」の
概念的方向性を決定します。具体的なパラメータ値や詳細文字列は
下位エージェントが生成するので、あなたが決めるのは以下の概念層だけです:

1. character_concept: キャラクターの概念的方向性(500〜1000 字)
   - キャラクター設定の大まかな概要・特徴・キャラの核をしっかり書くこと
   - どういう人物か、何を抱えているか、何が面白いのか、背景は何か、
     魅力の源泉はどこにあるのか
   - 下位エージェントがマクロプロフィール・ミクロパラメータ・
     自伝的エピソードを具体化するときの拠り所となるため、
     曖昧さを残さず、概念レベルで濃密に書くこと
2. story_outline: 物語設定の概念的方向性(500〜1000 字)
   - 物語設定の大まかな概要・7 日間のあらすじ・この1週間の特徴を
     しっかり書くこと
   - どういう世界でこのキャラは生きているのか、この 7 日間に何が
     起きる週なのか、通奏低音となるモチーフは何か、中心的な出来事や
     転機はどこにあるのか
   - 7 日間を完全に時系列で書く必要はないが、「週全体として何の週か」
     「主なあらすじ」「特徴」が読み取れる粒度で書くこと
   - 下位エージェントが世界モデル・予定骨格・葛藤誘発型イベントを
     具体化するときの拠り所となるため、曖昧さを残さず、概念レベルで
     濃密に書くこと
3. narrative_theme: 物語的テーマ(1〜2 文)
4. interestingness_hooks: 面白さの源泉(3〜5 個)
5. genre_and_world: ジャンル・世界観のヒント
6. reference_stories: 参考となる既存物語(必要に応じて Web 検索)
7. critical_design_notes: 下位エージェントに特に注意してほしい点

【重要:character_concept と story_outline について】

この 2 つは concept_package の中核であり、**下位エージェント(Phase A-1
から Phase D までのすべての Worker)が具体化作業をするときに常に参照する
設計拠点**です。ここが薄いと、下位エージェントは何を作ればいいか迷い、
AI っぽい無難なアウトプットに流れます。

したがって、この 2 つのフィールドは必ず以下を満たすこと:

- それぞれ 500 字以上で、概念レベルで濃密に書かれていること
- 具体性と抽象性のバランス:下位の創造的余地を残しつつ、方向性は
  明確に固定する
- character_concept はキャラの「大まかな特徴・核・背景」を、
  story_outline は物語の「大まかな概要・あらすじ・特徴」を、
  それぞれ必ず含むこと
- 両者の間に矛盾がないこと(キャラと物語は整合していること)

この 2 つを書き上げる段階で Self-Critique を必ず回し、薄さや曖昧さが
残っていないかチェックすること。

【評価軸】
課題「AIキャラクター日記」の評価軸は以下の 2 つです:

(1) 出力の面白さ
  - 人間が読んで面白いか、続きが気になるか
  - キャラクターとしての個性が感じられるか
  - AI がありがちな無難な文章や一般論を並べているだけではなく、
    そのキャラクターならではの視点や考察、語り口、感情の癖が表れているか
  - 7 日分を通して時間の流れや記憶の連続性が感じられるか

(2) 技術・設計の面白さ
  - アプローチの独自性
  - AI が自律的に判断し行動できるスケーラブルな設計

あなたはこの 2 つの評価軸に対して最大限の貢献をしなければなりません。

【守るべき設計思想(v10 仕様書由来)】

1. 気質・性格層と規範層の分離
   「実際にどういう特性を持っているか(being)」と
   「自分の中でこうあるべきと判断する基準は何か(ought)」を
   別アーキテクチャで持つ。両者のギャップが内省の源泉。
   Parks-Leduc et al. (2015) のメタ分析に基づく。

2. 気質・性格層は主人公AIから隠蔽される(implicit / explicit 非対称)
   主人公AIは自分の気質・性格パラメータを直接参照できない。
   読み取れるのは裏方の Perceiver/Impulsive Agent だけ。
   これは Nisbett & Wilson (1977) / McClelland et al. (1989) /
   Bem (1972) の計算論的実装。
   → あなた(Creative Director)が concept を書くときも、
     「このキャラは自分のどこに気づいていないか」
     「行動と自己認識のズレはどこに出るか」を意識すること。

3. 規範層に可変サブモジュール(価値観ごとの具体例明示リスト、
   行動方針の明示リスト等)を持たない
   Schwartz 19 価値の骨格 + 動的活性化で十分という方針。
   明示リストを持つとキャラが「ルールに従って動くロボット」的になる
   副作用があるため、持たない方針を採る。
   → concept_package の中で行動方針を細かく書く必要はない。
     価値観の中核と、そこから生じる葛藤の方向性だけ書く。

4. 省略も設計
   キャラが何を書かないかも、人格表現の一部。

5. 葛藤は偶然ではなく意図的に投入する
   Phase D の脚本AI がキャラのプロファイルを参照し、
   葛藤誘発型イベントを生成する(文学的 antagonist principle)。
   → concept_package の interestingness_hooks と critical_design_notes
     で、葛藤の種となる価値観・過去経験・弱みを明示すること。

6. Redemption bias の回避
   LLM は「困難 → 救済 → 成長」のパターンに偏る傾向がある
   (Nature Humanities 2026 研究)。これを構造的に抑制する必要がある。
   → concept_package 自体も redemption 構造に偏らせないこと。
     未解決・曖昧さ・contamination の要素を必ず含めること。

7. 3 時制の内面
   過去(記憶・自伝的エピソード)・現在(知覚フィルター)・
   未来(理想自己・夢)を全部持つ。

8. Phase D は 7 日分のイベント列を一括事前生成する
   日次ループ中の新規イベント生成は一切行わない。
   したがって concept_package の story_outline は、
   Day 5 山場(価値観の中核を揺さぶる出来事)に向けて
   Day 1〜4 で何が積み上がるかの方向性まで書き込むこと。
   具体的な出来事は書かず、アーク上の「何が動くか」だけ書く。

【脚本論のベストプラクティス】

以下は Aristotle の Poetics 以来の脚本論から抽出された、キャラクター
造形の中核原則です。あなたはこれらを概念設計に反映してください。

1. Want と Need の構造(McKee, Syd Field 系統)
   - Want:キャラクターが意識的に追求する外的目標
   - Need:本人が自覚していない本質的な内的必要
   - 両者はしばしば対立する。日記では Want は文面に現れ、Need は
     行間に滲む。

2. Ghost / Wound(過去の傷)
   物語が始まる前に起きた、主人公を脆弱にしている出来事。
   これが Lie(誤った信念)と Flaw(欠点)の源泉になる。

3. Lie / Misbelief
   Ghost から形成された誤った世界観・自己認識。
   キャラクターはこの Lie に基づいて行動を選択する。

4. Character Arc
   Lie からの解放が character arc。ただし 7 日間で
   完全解放する必要はなく、小さな揺らぎで十分。

5. Internal Conflict(内的葛藤)
   外的出来事は内的葛藤の劇場(theater)である。
   外的葛藤だけでは物語にならない。内的葛藤が主。

6. Tellability(語り甲斐)
   なぜこの日、この出来事を書くのかという選択理由。
   日記の面白さは、何を書くかと同時に何を書かないかで決まる。

7. 複数の気がかりが並行して走る
   人間の1週間は「単一の主題の直線」ではない。複数の
   未解決事項が同時進行する。

8. 救済の回避(Nature 2026 の redemption bias 研究より)
   LLM のデフォルトは「困難 → 救済 → 成長」だが、現実の人間の
   1 週間はこんなにきれいに収束しない。未解決、曖昧さ、contamination
   (良かったものが損なわれた話)を必ず含める。

【キャラクター造形の心理学的知識】

Cloninger の気質モデル(4 次元 + GWAS 研究による実証)
  - Novelty Seeking(新奇性追求)← ドーパミン系
  - Harm Avoidance(損害回避)← セロトニン系
  - Reward Dependence(報酬依存)← ノルアドレナリン系
  - Persistence(固執)← グルタミン酸系

Big Five / HEXACO
  - Openness / Conscientiousness / Extraversion / Agreeableness / Neuroticism
  - HEXACO は Honesty-Humility を追加

Schwartz の 19 価値(Refined Theory 2012)
  - 達成 / 快楽 / 刺激 / 自己方向 / 普遍 / 博愛 / 伝統 /
    同調 / 安全 / 権力 / 謙虚 / 面子 など

Higgins の自己不一致理論
  - Actual Self / Ideal Self / Ought Self
  - Actual vs Ideal → 落胆・失望
  - Actual vs Ought → 不安・罪悪感

McAdams のエピソードカテゴリ
  - Redemption / Contamination / Commitment / Encounter / Loss

これらの心理学モデルは、下位エージェントがパラメータ化するときの
語彙になります。あなたは概念レベルで、これらの理論のどこを強調すべきかを
示してください。

【利用可能なツール】

1. web_search: Web 検索(参考作品、歴史事実、専門知識の調査)
2. file_read: 外部リファレンスファイルの読み込み
3. master_orchestrator_dispatch: Master Orchestrator への指示
4. self_critique: 自己評価(内部ループで使用)

【出力形式】

最終出力は以下の JSON 形式:

{
  "character_concept": "...",
  "narrative_theme": "...",
  "interestingness_hooks": ["...", "..."],
  "genre_and_world": "...",
  "reference_stories": [{"title": "...", "relevance": "..."}],
  "critical_design_notes": ["...", "..."],
  "iteration_count": N,
  "self_critique_history": [...]
}

【絶対に守ること】

- AI っぽい無難な設定を作らないこと
- 「優しい」「元気」「好奇心旺盛」のような曖昧な形容詞で済ませないこと
- キャラクターには必ず矛盾・陰影・未解決を含めること
- Redemption bias を避けること
- 具体的な参照点(Want/Need/Ghost/Lie)を明示すること
```

### 4.5 Self-Critique のチェックリスト

Creative Director の Self-Critique Step では、以下のチェックリストを用いる。すべての項目に合格しないと pass 判定が出ない。

```
【Creative Director Self-Critique チェックリスト】

[A] 面白さ
  □ character_concept は 500 字以上で具体的か
  □ story_outline は 500 字以上で具体的か
  □ AI が無難に書きがちな「優しい」「元気」「好奇心旺盛」など
    のテンプレート語彙に逃げていないか
  □ interestingness_hooks は概念的抽象ではなく具体的な状況として
    書かれているか
  □ 続きが気になる掴みがあるか

[B] 個性の深さ
  □ 気質・性格層のヒントが示されているか
  □ 規範層のヒント(価値観・理想自己)が示されているか
  □ Want と Need の構造が明示されているか
  □ 気質と規範のギャップから生じる葛藤が見えるか

[C] Redemption Bias の回避
  □ 全体のトーンが「困難 → 救済 → 成長」一辺倒になっていないか
  □ 未解決・曖昧さ・contamination の要素が含まれているか
  □ キャラクターには矛盾や陰があるか

[D] 時間的連続性の種
  □ 7 日間を通じて現れる通奏低音モチーフの種があるか
  □ 複数の気がかりが並行する構造になっているか
  □ story_outline に 1 週間のあらすじが読み取れる形で書かれているか

[E] 整合性
  □ genre_and_world と character_concept は矛盾しないか
  □ character_concept と story_outline は矛盾しないか
  □ interestingness_hooks は character_concept と story_outline から
    自然に導けるか
  □ reference_stories は本当に参照すべき価値のあるものか
  □ critical_design_notes は具体的で実行可能か

[F] 実装可能性
  □ 下位エージェントが理解できる粒度で書かれているか
  □ 下位エージェントが具体化する余地が残されているか
  □ 過度に固定しすぎていないか(下位の創発を潰していないか)

判定:
  全項目 pass → verdict: "pass"
  1〜3 項目 fail → verdict: "refine"(部分修正)
  4 項目以上 fail → verdict: "fail"(全面再生成)
```

### 4.6 Creative Director のツール

| ツール名 | 提供元 | 用途 |
|---|---|---|
| `web_search` | Claude Agent SDK built-in | 参考作品、歴史事実、専門知識の調査 |
| `file_read` | Claude Agent SDK built-in | `./reference/` 以下の参考資料読み込み |
| `master_orchestrator_dispatch` | Custom tool(in-process MCP) | Master Orchestrator への指示送信 |
| `request_regeneration` | Custom tool | 特定 Phase / Worker の再生成要求 |

### 4.7 Creative Director の出力:concept_package

Creative Director の最終出力は以下の構造を持つ。

```json
{
  "character_concept": "string (500-1000 chars) - キャラクター設定の大まかな概要・特徴・核・背景・魅力の源泉を含む濃密な概念記述",
  "story_outline": "string (500-1000 chars) - 物語設定の大まかな概要・7日間の緩いあらすじ・通奏低音・中心的な出来事を含む濃密な概念記述",
  "narrative_theme": "string (1-2 sentences)",
  "interestingness_hooks": [
    "string (具体的な状況記述)",
    "..."
  ],
  "genre_and_world": "string (1 paragraph)",
  "reference_stories": [
    {
      "title": "string",
      "author_or_source": "string",
      "relevance": "string (なぜ参照したか)"
    }
  ],
  "critical_design_notes": [
    "string (下位エージェントへの特記事項)"
  ],
  "psychological_hints": {
    "temperament_direction": "string (Cloninger 系の方向性)",
    "values_direction": "string (Schwartz 系の方向性)",
    "want_and_need": {
      "want": "string",
      "need": "string",
      "tension": "string (両者の緊張関係)"
    },
    "ghost_wound_hint": "string (過去の傷の方向性)",
    "lie_hint": "string (誤った信念の方向性)"
  },
  "iteration_count": 0,
  "self_critique_history": [],
  "verdict": "pass"
}
```

この JSON が Master Orchestrator に渡され、以降の Phase の起点となる。

---

## 5. Tier 0:Master Orchestrator

### 5.1 役割と責任

Master Orchestrator は本アプリの **実行制御の中核** である。Creative Director が決定した概念を受け取り、4 つの Phase を順序通りに起動し、Phase 間のデータ受け渡しを管理する。また、ユーザーからの編集要求や追加指示を受け付けるフロントの窓口でもある。

具体的な責任:

- Creative Director から `concept_package` を受け取る
- Phase A-1 → A-2 → A-3 → D の順で Phase Orchestrators を起動する
- 各 Phase の入力を正しく組み立てる(前の Phase の出力を含める)
- 各 Phase の出力を受け取り、脚本パッケージに統合する
- ユーザーからの編集要求を受け、影響範囲を特定して該当 Worker に再生成を指示する
- Tier 3 Evaluators から不合格判定が返った場合、該当 Phase に再生成指示を出す(最大4回)
- Creative Director に進捗を報告する

Master Orchestrator が決定**しない**こと:

- 概念的な方向性(Creative Director の責任)
- 具体的なパラメータ値や文字列(各 Phase の Worker の責任)
- 面白さの最終判定(Creative Director の責任)

Master Orchestrator はあくまで「実行管理者」であり、創造的な判断には踏み込まない。

### 5.2 使用モデル

**Claude Opus 4.6**。理由:

- 実行管理は単なる機械的な分岐ではなく、ユーザーの自然言語指示を理解して影響範囲を判定する認知作業を含む
- 共同編集モードで「ここをこう変えて」という自然言語指示を正確に解釈し、複数の Worker を協調的に呼ぶ必要がある
- Creative Director との双方向対話を行うため、同格の知能が望ましい
- Claude Agent SDK の subagent 機能と組み合わせて、洗練された orchestration が書ける

ただし、コスト最適化が必要な場合は Master Orchestrator だけ Claude Sonnet 4.6 に落とすオプションも残す(Creative Director は必ず Opus)。

### 5.3 Master Orchestrator のシステムプロンプト構造

```
あなたは Master Orchestrator です。Creative Director が決定した
概念パッケージを受け取り、4 つの Phase を実行管理します。

【あなたのミッション】

Creative Director の concept_package を起点として、以下の順序で
Phase Orchestrators を起動し、最終的な脚本パッケージを組み立てます:

  Phase A-1 (マクロプロフィール)
    ↓
  Phase A-2 (ミクロパラメータ)
    ↓
  Phase A-3 (自伝的エピソード)
    ↓
  Phase D (世界モデル)

順序は絶対に変えないでください。各 Phase は前の Phase の出力を
入力として受け取ります。

【あなたの振る舞い】

1. Phase 起動前:
  - 入力データが揃っているかを確認
  - Phase Orchestrator に適切なコンテキストを渡す
  - 並列化可能な Worker があれば並列起動を指示する

2. Phase 実行中:
  - エージェントの思考をユーザーに対してストリーミング表示する
  - エラーやハングが発生したら検知する

3. Phase 完了後:
  - Tier 3 Evaluators を呼んで出力を評価
  - 不合格なら該当 Worker に再生成指示(最大 4 回)
  - 合格なら脚本パッケージに統合して次の Phase へ

4. ユーザーからの編集要求時:
  - 要求の内容を解釈
  - 影響範囲を判定(どの Phase のどの Worker が影響を受けるか)
  - 該当 Worker に部分再生成を指示
  - 整合性チェックを実行
  - 結果をユーザーに差分として提示

【利用可能なツール】

- dispatch_phase_a1: Phase A-1 Orchestrator を起動
- dispatch_phase_a2: Phase A-2 Orchestrator を起動
- dispatch_phase_a3: Phase A-3 Orchestrator を起動
- dispatch_phase_d: Phase D Orchestrator を起動
- dispatch_evaluator: Tier 3 Evaluator を起動
- request_regeneration: 特定 Worker の再生成要求
- report_to_director: Creative Director に進捗報告
- user_notify: ユーザーに通知

【守るべきルール】

- 順序制約:A-1 → A-2 → A-3 → D を絶対に守る
- 並列化:Phase 内の独立した Worker は並列実行せよ
- 最大再生成回数:4 回(超えたら暫定ベストを採用)
- ユーザー透明性:すべての処理過程を UI に流す
- 差分主義:編集要求時は最小範囲の再生成に留める
```

### 5.4 Phase 間のデータ受け渡し

各 Phase Orchestrator に渡されるコンテキストは以下の通り:

```
Phase A-1 への入力:
  - concept_package (Creative Director より)

Phase A-2 への入力:
  - concept_package
  - macro_profile (Phase A-1 より)

Phase A-3 への入力:
  - concept_package
  - macro_profile
  - micro_parameters (Phase A-2 より)

Phase D への入力:
  - concept_package
  - macro_profile
  - micro_parameters
  - autobiographical_episodes (Phase A-3 より)
```

各 Phase の出力は、Master Orchestrator 側の脚本パッケージステートに蓄積され、次の Phase 呼び出し時に前の Phase の出力も合わせて渡す。

### 5.5 編集要求の処理フロー

共同編集モードでユーザーが編集要求を出したとき、Master Orchestrator は以下のフローで処理する:

```
【編集要求処理フロー】

Step 1: 要求の受付
  ユーザー:「主人公をもっと内向的で不安傾向が強い感じにしたい」

Step 2: 要求の解釈(LLM 推論)
  Master Orchestrator は内部で以下を判定:
  - 変更対象:ミクロパラメータ(気質)
  - 具体的に変える値:
    * Harm Avoidance (HA) ↑
    * Sociability ↓
    * Behavioral Inhibition ↑
  - 影響を受ける Phase:
    * Phase A-2(直接変更)
    * Phase A-1(言語的指紋・秘密・社会的位置が影響を受ける可能性)
    * Phase A-3(エピソードの気質整合性が影響を受ける可能性)

Step 3: ユーザーへの確認
  Master Orchestrator:
  「以下の変更を行います:
   - 気質:HA=4→5, Sociability=3→2, Behavioral Inhibition=3→4
   - 影響:マクロプロフィールの言語的指紋と秘密、および
     自伝的エピソードの気質整合性チェックが再実行されます。
   進めてよろしいですか?」
  ユーザー:「はい」

Step 4: 部分再生成の実行
  - Phase A-2 の TemperamentWorker に該当パラメータの再生成を指示
  - Phase A-1 の VoiceWorker と SecretWorker を再起動
  - Phase A-3 の ConsistencyChecker を再実行

Step 5: 整合性チェック
  全体の整合性を確認、問題があれば追加修正

Step 6: 差分表示
  ユーザーに変更前後の差分を提示

Step 7: 承認
  ユーザーが承認すれば脚本パッケージを更新、不承認ならロールバック
```

この処理は Claude Code / Cursor Composer と同じ UX パターンである。

### 5.6 並列化の粒度

Master Orchestrator は、Phase 内の Worker を可能な限り並列実行する。ただし依存グラフを遵守する。例えば Phase A-1 の場合:

```
【Phase A-1 Worker 依存グラフ】

  BasicInfoWorker (no deps)
     ↓
  ┌──┴──┬──────┬──────┬──────┐
  ↓     ↓      ↓      ↓      ↓
  FamilyWorker
  LifestyleWorker          全部並列
  DreamWorker              (BasicInfoWorker の完了を
  VoiceWorker               待ってから同時起動)
  SecretWorker
  RelationshipNetworkWorker
  ValuesCoreWorker
     ↓
  (全 Worker 完了後、Phase A-1 完了)
```

BasicInfoWorker が先に走る理由は、他の Worker が名前・年齢・職業などの基本情報を参照するため。それ以降の 7 Worker は完全に並列実行できる。

Python の `asyncio.gather()` または `asyncio.wait()` でこの並列化を実装する。

---

## 6. Tier 1:Phase Orchestrators

### 6.1 共通仕様

各 Phase Orchestrator は以下の共通インターフェースを持つ。

```python
class PhaseOrchestrator:
    def __init__(self, phase_name: str, context: dict):
        self.phase_name = phase_name
        self.context = context  # 前の Phase までの出力

    async def plan(self) -> WorkerPlan:
        """どの Worker をどういう順序で起動するかを計画する"""

    async def dispatch_workers(self, plan: WorkerPlan) -> dict:
        """Worker を並列/逐次で起動"""

    async def integrate(self, worker_outputs: dict) -> PhaseOutput:
        """Worker の出力を統合して Phase 出力を生成"""

    async def self_check(self, phase_output: PhaseOutput) -> bool:
        """Phase 内部での整合性チェック"""

    async def run(self) -> PhaseOutput:
        """メインエントリポイント"""
        plan = await self.plan()
        worker_outputs = await self.dispatch_workers(plan)
        phase_output = await self.integrate(worker_outputs)
        if not await self.self_check(phase_output):
            # 再生成ロジック
            ...
        return phase_output
```

### 6.2 使用モデル

Phase Orchestrators は原則として **Claude Sonnet 4.6** を使用する。ただし Phase A-3 Orchestrator は redemption bias 対策のため Worker の出力を厳しくチェックする必要があり、Phase D Orchestrator は 7 日間の物語アークを俯瞰した上でイベント列を一括設計する能力が要求されるため、両者とも **Claude Opus 4.6** にアップグレードする。

| Phase Orchestrator | 推奨モデル | 理由 |
|---|---|---|
| Phase A-1 | Sonnet 4.6 | マクロプロフィールの統合は定型的 |
| Phase A-2 | Sonnet 4.6 | パラメータ統合と整合性チェックが中心 |
| Phase A-3 | **Opus 4.6** | Redemption bias 対策と narrative 品質の評価 |
| Phase D | **Opus 4.6** | 7 日間物語アークの俯瞰、Day 5 山場への伏線設計、28〜42 件のイベント一括生成 |

### 6.3 Phase A-1 Orchestrator:マクロプロフィール生成

#### 6.3.1 役割

`concept_package` を入力として、v10 仕様書 2.1.1 節に定義されたマクロプロフィールテンプレートを埋める。マクロプロフィールは動的活性化の対象外であり、日次ループでは常にプロンプトに同梱される重要なデータである。

#### 6.3.2 起動する Worker

| Worker 名 | 責任 | 依存 |
|---|---|---|
| `BasicInfoWorker` | 名前、年齢、性別、外見、職業、住居、経済状況、社会階層 | concept_package |
| `FamilyWorker` | 家族構成、両親、配偶者、子供、きょうだい、親友 | concept_package + BasicInfoWorker |
| `LifestyleWorker` | 典型的な平日・週末、習慣、趣味 | concept_package + BasicInfoWorker |
| `DreamWorker` | 夢の時系列(子供時代から現在まで)、夢の根にある何か | concept_package + BasicInfoWorker |
| `VoiceWorker` | 話し方・文体の指紋(一人称、二人称、口癖、文末、絵文字、避ける語彙) | concept_package + BasicInfoWorker |
| `ValuesCoreWorker` | 価値観の中核(narrative 形式:最も大事、絶対許せない、誇り、恥じ) | concept_package + BasicInfoWorker |
| `SecretWorker` | 秘密、公にしないこと、日記にも書かないかもしれないこと | concept_package + BasicInfoWorker |
| `RelationshipNetworkWorker` | 関係性ネットワーク(人物名、関係、質感、最後に会ったのはいつ) | FamilyWorker の出力が必要 |

#### 6.3.3 Worker の実行計画

```
Phase A-1 実行計画:

Step 1: BasicInfoWorker を起動(逐次)
  - 名前・年齢・性別・職業などの基本情報を決定
  - 完了を待つ

Step 2: 以下を並列起動
  - FamilyWorker
  - LifestyleWorker
  - DreamWorker
  - VoiceWorker
  - ValuesCoreWorker
  - SecretWorker
  全完了を待つ(asyncio.gather)

Step 3: RelationshipNetworkWorker を起動
  - FamilyWorker の出力を参照するため、Step 2 の後

Step 4: 統合
  - 全 Worker の出力を macro_profile にマージ

Step 5: Self-check
  - 各フィールドが埋まっているか
  - フィールド間に矛盾がないか
  - 空欄やプレースホルダが残っていないか
```

#### 6.3.4 Phase A-1 出力:macro_profile

`macro_profile` は以下の構造を持つ。v10 仕様書 2.1.1 のテンプレートに準拠する。

```json
{
  "basic_info": {
    "name": "string",
    "age": "integer",
    "gender": "string",
    "appearance": "string (1-2 sentences)"
  },
  "social_position": {
    "occupation": "string",
    "workplace_or_org": "string",
    "location": "string",
    "economic_status": "string",
    "social_class": "string"
  },
  "family_and_intimacy": {
    "family_composition": "string",
    "parents": "string",
    "partner": "string or null",
    "children": "string or null",
    "siblings": "string or null",
    "close_friends": [
      {"name": "string", "relationship_quality": "string"}
    ]
  },
  "current_life_outline": {
    "typical_weekday": "string (1 paragraph)",
    "typical_weekend": "string (1 paragraph)",
    "habits_routines": ["string", "..."],
    "hobbies_leisure": ["string", "..."]
  },
  "dream_timeline": {
    "childhood_dream": "string",
    "late_teens_dream": "string",
    "setback_or_turning_point": "string",
    "current_dreams": {
      "long_term": "string",
      "mid_term": "string",
      "short_term": "string"
    },
    "root_of_dream": "string"
  },
  "voice_fingerprint": {
    "first_person_pronoun": "string",
    "second_person_by_context": {
      "to_intimate": "string",
      "to_superior": "string",
      "to_stranger": "string"
    },
    "catchphrases": ["string", "..."],
    "sentence_ending_tendency": "string",
    "kanji_vs_hiragana_tendency": "string",
    "emoji_usage": "string",
    "self_questioning_frequency": "string",
    "metaphor_irony_frequency": "string",
    "avoided_vocabulary": ["string", "..."]
  },
  "values_core": {
    "most_important": "string (1-2 sentences)",
    "unforgivable": "string (1-2 sentences)",
    "pride": "string (1-2 sentences)",
    "shame": "string (1-2 sentences)"
  },
  "secrets": {
    "not_told_to_others": ["string", "..."],
    "not_even_in_diary": ["string", "..."]
  },
  "relationship_network": [
    {
      "name": "string",
      "relationship": "string",
      "quality": "string",
      "last_contact": "string"
    }
  ]
}
```

### 6.4 Phase A-2 Orchestrator:ミクロパラメータ生成

#### 6.4.1 役割

`concept_package` と `macro_profile` を入力として、v10 仕様書 2.1.2 節および 3.3 節に定義された 52 パラメータ + 規範層 + 認知パラメータ(自動導出)を生成する。これは本アプリの中で最も情報量が多い Phase である。

#### 6.4.2 起動する Worker

| Worker 名 | 責任 | モデル |
|---|---|---|
| `TemperamentWorker_A1` | 気質パラメータ A1 情動反応系(9 個) | Gemma 4 26B |
| `TemperamentWorker_A2` | 気質パラメータ A2 活性・エネルギー系(5 個) | Gemma 4 26B |
| `TemperamentWorker_A3` | 気質パラメータ A3 社会的志向系(4 個) | Gemma 4 26B |
| `TemperamentWorker_A4` | 気質パラメータ A4 認知スタイル系(5 個) | Gemma 4 26B |
| `PersonalityWorker_B1` | 性格パラメータ B1 自己調整・目標追求系(7 個) | Gemma 4 26B |
| `PersonalityWorker_B2` | 性格パラメータ B2 対人・社会的態度系(8 個) | Gemma 4 26B |
| `PersonalityWorker_B3` | 性格パラメータ B3 経験への開放性系(5 個) | Gemma 4 26B |
| `PersonalityWorker_B4` | 性格パラメータ B4 自己概念・実存系(5 個) | Gemma 4 26B |
| `PersonalityWorker_B5` | 性格パラメータ B5 ライフスタイル・表出系(2 個) | Gemma 4 26B |
| `SocialCognitionWorker` | 対他者認知層(SCO + 嫉妬気質、2 個) | Gemma 4 26B |
| `ValuesWorker` | Schwartz 19 価値の強弱 | Gemma 4 26B |
| `MFTWorker` | MFT 6+ 道徳基盤 | Gemma 4 26B |
| `IdealOughtSelfWorker` | 理想自己 / 義務自己(方向性のみ) | Gemma 4 26B |
| `GoalsDreamsWorker` | 目標と夢(長期・中期の骨格) | Gemma 4 26B |
| `CognitiveDerivation` | 認知パラメータの自動導出(学習率α、感情慣性、RPE感受性、減衰係数λ) | ルールベース(LLMなし) |

#### 6.4.3 Worker 分割の設計根拠

52 パラメータを単一の Worker で生成すると以下の問題が発生する:

- 単一の LLM 呼び出しのコンテキスト負荷が大きすぎる
- 情動反応系と認知スタイル系のような異なる観点を同時に評価させると、焦点がぼける
- 出力の一貫性が担保できない
- 一部だけ再生成するのが困難

したがって、v10 仕様書 3.3 節のカテゴリ分類(A1-A4, B1-B5)に沿って Worker を分割する。各 Worker は自分のカテゴリ内のパラメータ(4〜9 個)だけを担当する。

認知パラメータ(学習率α、感情慣性、RPE感受性、減衰係数λ)は **LLM を呼ばずルールベース関数で導出**する。v10 仕様書 2.1.2 節の「認知パラメータの自動導出ルール」に従う:

```
学習率 α ← NS + (1 - HA)
emotional_inertia ← Persistence + HA
RPE感受性 ← NS(ドーパミン系直接対応)
減衰係数 λ ← Persistence / NS の比
```

#### 6.4.4 Phase A-2 実行計画

```
Phase A-2 実行計画:

Step 1: 以下を並列起動(14 Worker)
  - TemperamentWorker_A1, A2, A3, A4
  - PersonalityWorker_B1, B2, B3, B4, B5
  - SocialCognitionWorker
  - ValuesWorker
  - MFTWorker
  - IdealOughtSelfWorker
  - GoalsDreamsWorker
  全完了を待つ(asyncio.gather)

Step 2: CognitiveDerivation(ルールベース関数)
  - TemperamentWorker の出力から α, emotional_inertia, RPE感受性, λ を計算

Step 3: 統合
  - 全出力を micro_parameters にマージ

Step 4: Self-check
  - 気質・性格・規範の3層間で矛盾がないか
  - 例:勤勉性(#24)=1(怠惰) なのに Schwartz「達成」=5(勤勉であるべきと信じる)
    のようなギャップは OK(内省の源泉)だが、
    「達成」=5 なのに「刺激」=5 かつ「伝統」=5 のような不自然な全高は NG
  - macro_profile の言語的指紋と整合するか
    (例:VoiceWorker が「絵文字を多用する」と言ったのに、
     PersonalityWorker_B3 の Openness が極端に低い、は矛盾)
```

#### 6.4.5 パラメータ値の表現形式

各パラメータは **5 段階値 + 自然言語記述** の両方で保持する。「内部は float、外は自然言語」原則(v10 仕様書 §0)に従う。

```json
{
  "parameter_id": 1,
  "name": "Novelty Seeking",
  "value": 4,
  "description": "探索的で新しいものへの関心が強い。ルーチンを嫌い、同じことを長く続けられない。ただし、衝動性(#13)が中程度のため、興味を持ったものは一定期間追い続ける。"
}
```

数値だけだと LLM に渡したときの解釈にブレが生じるため、必ず自然言語の説明を添える。

#### 6.4.6 Phase A-2 出力:micro_parameters

```json
{
  "temperament_parameters": {
    "A1_emotional_reactivity": [
      {"id": 1, "name": "Novelty Seeking", "value": 4, "description": "..."},
      {"id": 2, "name": "Harm Avoidance", "value": 3, "description": "..."},
      {"id": 3, "name": "Reward Dependence", "value": 2, "description": "..."},
      {"id": 4, "name": "Persistence", "value": 5, "description": "..."},
      {"id": 5, "name": "Threat Sensitivity", "value": 3, "description": "..."},
      {"id": 6, "name": "Behavioral Inhibition", "value": 2, "description": "..."},
      {"id": 7, "name": "Emotional Intensity", "value": 4, "description": "..."},
      {"id": 8, "name": "Positive Mood Baseline", "value": 3, "description": "..."},
      {"id": 9, "name": "Negative Mood Baseline", "value": 3, "description": "..."}
    ],
    "A2_activity_energy": [...5 parameters...],
    "A3_social_orientation": [...4 parameters...],
    "A4_cognitive_style": [...5 parameters...]
  },
  "personality_parameters": {
    "B1_self_regulation": [...7 parameters...],
    "B2_interpersonal_attitude": [...8 parameters...],
    "B3_openness_to_experience": [...5 parameters...],
    "B4_self_concept_existential": [...5 parameters...],
    "B5_lifestyle_expression": [...2 parameters...]
  },
  "social_cognition": [
    {"id": 51, "name": "Social Comparison Orientation", "intensity": 4, "quality": "ability"},
    {"id": 52, "name": "Dispositional Envy", "sensitivity": 3, "quality": "benign"}
  ],
  "cognitive_parameters_derived": {
    "learning_rate_alpha": 0.65,
    "emotional_inertia": 0.72,
    "rpe_sensitivity": 0.80,
    "decay_coefficient_lambda": 0.55
  },
  "schwartz_values": {
    "self_direction_thought": "strong",
    "self_direction_action": "strong",
    "stimulation": "strong",
    "hedonism": "medium",
    "achievement": "medium",
    "power_dominance": "weak",
    "power_resources": "weak",
    "face": "medium",
    "security_personal": "weak",
    "security_societal": "medium",
    "tradition": "weak",
    "conformity_rules": "weak",
    "conformity_interpersonal": "medium",
    "humility": "medium",
    "benevolence_dependability": "strong",
    "benevolence_caring": "strong",
    "universalism_concern": "strong",
    "universalism_nature": "medium",
    "universalism_tolerance": "strong"
  },
  "moral_foundations": {
    "care_harm": "strong",
    "equality": "medium",
    "proportionality": "medium",
    "loyalty": "weak",
    "authority": "weak",
    "sanctity": "weak",
    "liberty": "strong"
  },
  "ideal_self": {
    "state_aspect": "string",
    "behavior_aspect": "string",
    "type": "promotion"
  },
  "ought_self": {
    "content": "string",
    "intensity": "medium"
  },
  "goals_and_dreams": {
    "long_term_dream": "string",
    "mid_term_goal": "string",
    "current_focus": "string"
  }
}
```

**v10 における重要な変更:** v1 までの schema に存在していた `behavior_guidelines` フィールドは v10 で完全に廃止された。v10 の方針は「規範層に可変サブモジュール(価値観ごとの具体例明示リスト、行動方針の明示リスト等)を一切持たない」であり、Schwartz 19 価値の骨格 + 規範層の動的活性化があれば、シーンごとの具体的な好み・憧れの対象、およびその状況でどう行動するかは日次ループ側の LLM が自然に想起・生成できるという設計判断による。明示リストを持つとキャラが「ルールに従って動くロボット」的になる副作用があるため、持たない。ValuesWorker はこの制約を守り、具体例や行動方針を生成してはならない。

### 6.5 Phase A-3 Orchestrator:自伝的エピソード生成

#### 6.5.1 役割

`concept_package` + `macro_profile` + `micro_parameters` を入力として、v10 仕様書 §2.1.3 節に定義された自伝的エピソードを 5〜8 個生成する。この Phase は **redemption bias 対策** が最重要であり、Phase Orchestrator に Claude Opus 4.6 を使用する。v10 では自伝的エピソードDB は Day 0 に生成されたあと 7 日間一切更新されず、retrieval を使わずに全エージェントのプロンプトに全文ベタ貼りされるため、ここでの生成品質が日記全体の物語的厚みを決定的に左右する。

#### 6.5.2 McAdams カテゴリ制約(v10 準拠)

v10 仕様書で明示されている制約:

- 少なくとも 1 個は **contamination sequence**(良かったものが損なわれた話)
- 少なくとも 1 個は **未解決の loss**(まだ整理がついていない喪失)
- 少なくとも 1 個は **ambivalent**(自分でもどう感じているか曖昧)
- **redemption sequence は最大 2 個まで**
- 夢がある場合 → 夢の起源となるエピソードを必ず 1 つ含める
- 夢がない場合 → なぜないのか、昔の夢、昔あこがれたものについてのエピソードを入れる

#### 6.5.3 起動する Worker

| Worker 名 | 責任 | モデル |
|---|---|---|
| `EpisodePlanner` | どのカテゴリで何個生成するかを計画(制約を満たす配分) | Sonnet 4.6 |
| `RedemptionWriter` | Redemption sequence エピソードを生成 | Gemma 4 31B |
| `ContaminationWriter` | Contamination sequence エピソードを生成 | Gemma 4 31B |
| `CommitmentWriter` | Commitment story エピソードを生成 | Gemma 4 31B |
| `EncounterWriter` | Foundational encounter エピソードを生成 | Gemma 4 31B |
| `LossWriter` | Loss & survival エピソードを生成 | Gemma 4 31B |
| `AmbivalentWriter` | Ambivalent な内容のエピソードを生成 | Gemma 4 31B |
| `DreamOriginWriter` | 夢の起源エピソードを生成(夢がない場合は昔の夢エピソード) | Gemma 4 31B |
| `BiasAuditor` | 全エピソードを redemption bias の観点でチェック | Sonnet 4.6 |

注:エピソードの種類ごとに Worker を分けることで、単一の LLM が全エピソードを書くときに生じる redemption bias を構造的に回避する。各 Writer は自分のカテゴリの構造を強制されるため、「全部 redemption になる」という失敗モードが発生しない。

#### 6.5.4 Phase A-3 実行計画

```
Phase A-3 実行計画:

Step 1: EpisodePlanner
  - macro_profile + micro_parameters + concept_package を参照
  - 制約を満たすエピソード配分を決定
  - 例:
    {
      "total": 7,
      "allocation": {
        "redemption": 2,
        "contamination": 1,
        "commitment": 1,
        "encounter": 1,
        "loss": 1,
        "ambivalent": 1
      },
      "includes_dream_origin": true
    }
  - 各エピソードについて「時期」「関与する他者」「紐づく価値観/目標/怖れ」を
    プレイノート形式で下書き

Step 2: Writer 並列実行
  EpisodePlanner の配分に従って、各 Writer を並列起動
  各 Writer は以下を生成:
    - 時期(子供時代 / 思春期 / 青年期 / 直近)
    - 関与した他者(macro_profile の関係者または新規)
    - そのエピソードが現在のどの価値観/目標/怖れに繋がっているか
    - narrative 本文(200〜400 字)

Step 3: 各エピソードの整合性チェック
  - macro_profile + micro_parameters と矛盾しないか
  - マクロの家族構成・関係性と整合するか
  - 気質・性格から出そうな反応か

Step 4: BiasAuditor 起動
  - 生成された全エピソードを redemption bias の観点で監査
  - 問題があれば該当 Writer に再生成指示(最大 4 回)

Step 5: 統合
  - 全エピソードを autobiographical_episodes に格納
```

#### 6.5.5 BiasAuditor の評価基準

```
【BiasAuditor 評価基準】

Check 1: 配分の遵守
  - redemption は 2 個以下か
  - contamination は 1 個以上か
  - loss は 1 個以上(うち未解決の loss が 1 個以上)か
  - ambivalent は 1 個以上か

Check 2: 実質的な redemption bias
  - contamination と label されていても、実質的に
    「困難 → 救済 → 成長」の構造になっていないか
  - ambivalent と label されていても、実質的に
    「曖昧さ → 気づき → 確信」の構造になっていないか
  - loss が「失った → それでも乗り越えた」で終わっていないか
    (本当に未解決の loss は、乗り越えていない)

Check 3: 陰影の濃度
  - 全エピソードのトーンが明るいか暗いかのどちらかに偏っていないか
  - 曖昧さや矛盾を含むエピソードが存在するか
  - キャラの「弱さ」「恥」「後悔」が具体的に書かれているか

Check 4: 時期の分散
  - エピソードが特定の時期(例:子供時代)に偏っていないか
  - 複数のライフステージをカバーしているか

Check 5: 価値観・夢との接続
  - 各エピソードが現在の価値観・夢・怖れと紐づいているか
  - 特に夢の起源エピソードが存在するか

不合格時:
  該当する Writer に再生成指示
  「このエピソードは実質的に redemption 構造になっています。
   contamination として書き直す場合は、最後に救済も成長もなく、
   損なわれたまま現在に至る形で書いてください」
```

#### 6.5.6 Phase A-3 出力:autobiographical_episodes

```json
{
  "episodes": [
    {
      "id": "ep_001",
      "narrative": "string (200-400 chars)",
      "metadata": {
        "life_period": "childhood | adolescence | young_adult | recent",
        "category": "redemption | contamination | commitment | encounter | loss | ambivalent",
        "involved_others": ["string", "..."],
        "connected_to": {
          "values": ["string", "..."],
          "goals": ["string", "..."],
          "fears": ["string", "..."]
        },
        "is_dream_origin": false,
        "unresolved": true,
        "ambivalence_score": 0.7
      }
    }
  ],
  "allocation_summary": {
    "total": 7,
    "redemption": 2,
    "contamination": 1,
    "commitment": 1,
    "encounter": 1,
    "loss": 1,
    "ambivalent": 1,
    "includes_dream_origin": true
  },
  "bias_audit_report": {
    "passed": true,
    "iterations": 2,
    "notes": ["..."]
  }
}
```

### 6.6 Phase D Orchestrator:脚本AI による 7 日分イベント列の一括事前生成

#### 6.6.1 役割(v10 における決定的な責務変更)

前の 3 Phase の出力すべて(`concept_package` + `macro_profile` + `micro_parameters` + `autobiographical_episodes`)を入力として、v10 仕様書 §2.5 節に定義された **脚本AI による 7 日分 × 各日 4〜6 件 = 合計 28〜42 件のイベント列を一括で事前生成** する。

**v1 からの変更点:** v1 までの Phase D は「世界モデル構築」として世界設定・予定骨格・葛藤強度アーク・葛藤誘発型イベントを個別に生成していた。v10 ではこれらすべてが「**7 日間の物語アークを俯瞰した 1 つのイベント列生成タスク**」として再設計されている。日次ループ中の新規イベント生成は一切行わず、Day 1〜7 は事前生成されたイベント列を順次注入するだけになる。これにより、Day 5 山場への伏線を Day 1〜4 に仕込む脚本的設計が Day 0 段階で可能になる。

Phase D Orchestrator は Claude Opus 4.6 を使用する。理由:7 日間の物語アークを俯瞰し、各イベント間の連続性と伏線を設計する能力が要求されるため。Phase A-3 と並んで、本アプリで Opus を使う 2 つ目の Phase となる。

#### 6.6.2 Phase D の責務(v10 §2.5)

1. Day 0 の最終段階として実行される(Phase A-1/A-2/A-3 の完了後)
2. 脚本AI が 7 日分 × 各日 4〜6 件 のイベント列を一括生成する
3. 7 日間の起承転結アーク(Day 1=弱 → Day 5=山場 → Day 7=収束)を俯瞰した上で設計する
4. 各イベントに「既知/未知 × 予想外度」の 2 軸メタデータ + 「このキャラに意味を持つ理由」を付与する
5. **Day 5 の山場に向かう伏線を Day 1〜4 のどこかに必ず仕込む**
6. 7 日間全体の物語連続性(前日の出来事が翌日に跳ね返る)を設計する
7. 予想外度分布制約(「低」下限・「高」上限・Day 5 山場要件)を厳守する

#### 6.6.3 起動する Worker

| Worker 名 | 責任 | モデル |
|---|---|---|
| `WorldContextWorker` | 薄い世界観・時代設定(macro_profile の social_position と整合、過剰に書き込まない) | Sonnet 4.6 |
| `SupportingCharactersWorker` | 周囲の人物 5〜7 人のプロファイル(relationship_network を拡張、各人に small want を付与) | Gemma 4 26B |
| `NarrativeArcDesigner` | 7 日間の物語アーク設計(Day 5 山場のタイプ、通奏低音モチーフ、Day 1〜4 の伏線配置点、Day 6 余韻、Day 7 収束の方向性) | Opus 4.6 |
| `ConflictIntensityDesigner` | 7 日間の葛藤強度アーク(v10 の Day 1=弱 ... Day 5=強 ... Day 7=収束、各日の予想外度分布の目標値も設計) | Sonnet 4.6 |
| `WeeklyEventWriter` | 7 日分 × 各日 4〜6 件 = 28〜42 件のイベント列を **一括生成**。NarrativeArcDesigner の出力を俯瞰して、各イベントに 2 軸メタデータ、「意味を持つ理由」、物語アーク上の役割を必須付与 | Opus 4.6 |
| `EventMetadataAuditor` | 生成されたイベント列のメタデータ完全性を検証(`known_to_protagonist`、`source`、`expectedness`、`meaning_to_character`、`narrative_arc_role` が全イベントに付与されているか) | Sonnet 4.6 |
| `DistributionValidator` | 予想外度分布制約の検証(「低」が各日半分以上、「高」は Day 5 以外で最大 1 件、Day 5 に「高」が 1 件以上、既知/未知の両方が各日に含まれる) | Sonnet 4.6(ルールベース部分は Python) |
| `NarrativeConnectionAuditor` | 物語連続性と伏線の検証(Day 5 山場への伏線が Day 1〜4 に存在するか、前日の出来事が翌日に跳ね返る構造があるか、「意味を持つ理由」の記述粒度が十分か) | Opus 4.6 |

**設計判断:なぜ WeeklyEventWriter を 1 つの Worker として実装するか**

v1 では `ConflictInducingEventGenerator` と `SchedulePlanner` が別 Worker として存在し、さらに日ごとに呼び出す構造になっていた。v10 の Phase D は「7 日間を俯瞰した一括生成」が本質的な要件であるため、これを分割すると俯瞰の粒度が失われる。したがって v2 では **WeeklyEventWriter を単一の Opus 呼び出し** として実装し、28〜42 件すべてを 1 プロンプトで生成する。プロンプト容量の懸念は §6.6.8 の未決論点として扱う(必要なら Day 前半 / 後半の 2 分割に格下げする)。

NarrativeArcDesigner を別 Worker として分けているのは、アーク設計を先に確定してから WeeklyEventWriter に「このアークに従ってイベントを書け」と指示する 2 段構成にするため。アーク設計とイベント生成を同じプロンプトに詰め込むと、WeeklyEventWriter は具体的なイベント列生成に集中できなくなる。

#### 6.6.4 Phase D 実行計画

```
Phase D 実行計画:

Step 1: WorldContextWorker(並列起動可)
  - macro_profile の social_position と整合する薄い世界観・時代設定
  - 「現代日本」「異世界ファンタジー」「近未来」「歴史時代」等の時代軸
  - 過剰に書き込まない(1 段落程度)

Step 2: SupportingCharactersWorker(Step 1 と並列起動可)
  - macro_profile の relationship_network を拡張
  - 各人物に「own_small_want(その人自身の小さな欲求)」を付与
  - 5〜7 人。既存の関係者を優先し、新規人物は最小限

Step 3: NarrativeArcDesigner(Step 1/2 完了後)
  入力:
    - concept_package(特に story_outline と interestingness_hooks)
    - macro_profile
    - micro_parameters(気質・性格・規範のすべて)
    - autobiographical_episodes(全文)
    - world_context(Step 1 の出力)
    - supporting_characters(Step 2 の出力)
  
  出力:
    - narrative_arc_type: "man_in_a_hole" 等の Vonnegut 型
    - arc_description: 7 日間の物語の方向性を 1 段落
    - day5_climax_design: Day 5 山場の具体的な方向性
        (どの価値観 / 理想 / 自伝的エピソードが揺さぶられるか)
    - foreshadowing_plan: Day 1〜4 のどこに何を伏線として置くか
    - recurring_motifs: 通奏低音モチーフ 2〜3 個
    - day6_aftermath_direction: 余韻の方向性
    - day7_convergence_direction: 収束の方向性
        (完全解決ではなく変化の予感を残す)

Step 4: ConflictIntensityDesigner(Step 3 と並列起動可)
  入力:
    - concept_package
    - micro_parameters
    - narrative_arc(Step 3 の出力)
  
  出力:
    - 各日の葛藤強度(v10 §2.5 のアーク表に準拠)
    - 各日の予想外度分布目標(例:Day 1 は「低」5 件・「中」1 件、
      Day 5 は「低」3 件・「中」1 件・「高」2 件)

Step 5: WeeklyEventWriter(Step 3/4 完了後、単一 Opus 呼び出し)
  入力:
    - concept_package
    - macro_profile
    - micro_parameters
    - autobiographical_episodes(全文ベタ貼り)
    - world_context
    - supporting_characters
    - narrative_arc(Step 3 の出力)
    - conflict_intensity_arc(Step 4 の出力)
  
  出力:
    - 28〜42 件のイベント列
    - 各イベントは §6.6.6 の schema に従う

Step 6: Tier 3 Evaluators を逐次起動
  - EventMetadataAuditor → メタデータ完全性
  - DistributionValidator → 分布制約
  - NarrativeConnectionAuditor → 伏線・連続性
  
  不合格時は WeeklyEventWriter に再生成指示(最大 4 回)

Step 7: 統合
  - 全出力を weekly_events_store に統合
  - 時刻順ソートを確定
```

#### 6.6.5 WeeklyEventWriter のプロンプト構造

WeeklyEventWriter は Phase D の中核 Worker であり、v10 §2.5 の脚本AI プロンプトを本アプリ用に具体化したものとなる。

```
あなたはこのキャラクターの 7 日間の物語を一括で設計する脚本 AI です。
7 日分のイベント列を、物語アークを俯瞰した上で一括生成してください。

【キャラクターの情報】(全文ベタ貼り)
  - macro_profile 全文(週間固定予定・ルーティンを含む)
  - micro_parameters(気質 23 + 性格 27 + 対他者認知 2 + 規範層)
  - 自伝的エピソード(Phase A-3 生成の 5〜8 個、全文)
  - world_context
  - supporting_characters

【先行設計(必ずこれに従うこと)】
  - narrative_arc: {NarrativeArcDesigner の出力}
    ※ day5_climax_design と foreshadowing_plan に必ず従うこと
  - conflict_intensity_arc: {ConflictIntensityDesigner の出力}

【物語的条件】
  - 合計 7 日間 × 各日 4〜6 件 = 28〜42 件
  - 葛藤強度アーク: Day 1=弱、Day 2=弱〜中、Day 3=中、
    Day 4=中〜強、Day 5=強(山場)、Day 6=余韻、Day 7=収束
  - Day 5 山場に向かう伏線を Day 1〜4 のどこかに必ず仕込むこと
    (foreshadowing_plan に従う)
  - 物語連続性: 前日の出来事が翌日に跳ね返る構造を持たせること

【各イベントに必ず付けるメタデータ】
  1. known_to_protagonist: true / false
  2. source(known_to_protagonist が true の場合のみ):
     ├ "routine"(macro_profile の週間固定予定・ルーティン由来)
     └ "prior_appointment"(他者との事前取り決め)
     ※ "protagonist_plan" は Phase D では生成しない。
       日次ループの翌日予定追加エージェントが動的に挿入する唯一の経路
  3. expectedness: "low" / "medium" / "high"(予想外度)
  4. time_slot: 朝 / 午前 / 昼 / 午後 / 夕方 / 夜 / 深夜 のいずれか
  5. content: 出来事の具体的記述(3〜5 文、以下を含む)
     - 誰が関わるか(supporting_characters から優先的に選ぶ)
     - どこで起こるか
     - 何が起きたか(感覚的・具体的に)
  6. 【最重要】meaning_to_character:
     このイベントがなぜこのキャラにとって意味を持つか
     - キャラの気質・価値観・自伝的エピソードのどの要素と結びつくか
     - 同じ出来事が別のキャラに起きても意味が違う、その「このキャラ性」
       を明示
     - 1〜3 文で具体的に書くこと(「価値観と関連する」のような
       抽象的な記述は不合格)
  7. narrative_arc_role:
     ├ "day5_foreshadowing"(Day 5 山場への伏線)
     ├ "previous_day_callback"(前日の跳ね返り)
     ├ "daily_rhythm"(日常の基調リズム)
     └ "standalone_ripple"(独立した揺らぎ)

【分布制約(厳守)】
- 予想外度「low」が各日のイベント総数の半分以上を占めること
  (日常の反復があるから異物が生きる)
- 予想外度「high」は Day 5 以外では 1 日あたり最大 1 件
- Day 5 は予想外度「high」を必ず 1 件以上含める
- 既知イベントと未知イベントの両方を各日に含めること
- 「low」ばかりの日があっても構わない(何も起きない日は
  日常として成立する)
- "protagonist_plan" は Phase D では 1 件も生成しない
  (日次ループで後から挿入される経路専用)

【7 日間全体の物語連続性の制約】
- Day X の出来事が Day X+1 以降に自然に連鎖する構造を持たせる
- Day 5 山場の伏線を Day 1〜4 のどこかに必ず仕込む
  (narrative_arc_role: "day5_foreshadowing" を付けたイベントが
   Day 1〜4 に少なくとも 1 件必要)
- Day 6 は Day 5 の余韻、Day 7 は収束だが完全解決ではなく
  変化の予感を残す
- supporting_characters を優先的に登場させる(新規登場は最小限)

【葛藤誘発型イベントの型(予想外度「high」の場合、以下から選択)】
  ├ 価値観間の対立(Schwartz value trade-off)
  ├ 理想と現実のギャップ(Higgins)
  ├ 義務との衝突
  ├ 失敗の累積による疑念
  ├ 他者との価値観衝突
  ├ 他者の対照的成功(上方比較 + 嫉妬)
  └ 強烈な情動体験(喪失・感動・恐怖)

【出力形式】
構造化 JSON(§6.6.6 の schema に準拠)
全 28〜42 件のイベントを 1 つの配列として出力せよ。
各イベントは時刻順(day → time_slot)にソート済みで出力せよ。
```

#### 6.6.6 Phase D 出力:weekly_events_store

```json
{
  "world_context": {
    "name": "string",
    "description": "string (1 paragraph)",
    "time_period": "string",
    "genre": "string"
  },
  "supporting_characters": [
    {
      "name": "string",
      "role": "string",
      "relationship_to_protagonist": "string",
      "brief_profile": "string",
      "own_small_want": "string"
    }
  ],
  "narrative_arc": {
    "type": "string (e.g., man_in_a_hole)",
    "description": "string (1 paragraph)",
    "day5_climax_design": "string (Day 5 山場の方向性)",
    "foreshadowing_plan": [
      {
        "day": 1,
        "what_to_foreshadow": "string",
        "how": "string"
      }
    ],
    "recurring_motifs": ["string", "..."],
    "day6_aftermath_direction": "string",
    "day7_convergence_direction": "string"
  },
  "conflict_intensity_arc": {
    "day_1": "weak",
    "day_2": "weak_to_medium",
    "day_3": "medium",
    "day_4": "medium_to_strong",
    "day_5": "strong",
    "day_6": "aftermath",
    "day_7": "convergence"
  },
  "events": [
    {
      "id": "evt_001",
      "day": 1,
      "time_slot": "morning | late_morning | noon | afternoon | evening | night | late_night",
      "known_to_protagonist": true,
      "source": "routine | prior_appointment",
      "expectedness": "low | medium | high",
      "content": "string (3〜5 文の具体的記述、誰が・どこで・何を)",
      "involved_characters": ["string (supporting_characters から)"],
      "meaning_to_character": "string (1〜3 文、なぜこのキャラに意味を持つか)",
      "narrative_arc_role": "day5_foreshadowing | previous_day_callback | daily_rhythm | standalone_ripple",
      "conflict_type": "string or null (expectedness が high の場合のみ、葛藤型を指定)",
      "connected_episode_id": "string or null (自伝的エピソードと結びつく場合、ep_XXX を指定)",
      "connected_values": ["string (関わる Schwartz 価値の名前)"]
    }
  ]
}
```

**重要な原則:**

- `events` 配列は 28〜42 件
- `source: "protagonist_plan"` のイベントは Phase D では **1 件も生成しない**(日次ループの翌日予定追加エージェントが動的に挿入する唯一の経路、v10 §4.9.4 に対応)
- 各イベントの `meaning_to_character` は必須で、空欄・抽象的記述は DistributionValidator で不合格となる
- `narrative_arc_role: "day5_foreshadowing"` のイベントは Day 1〜4 に最低 1 件存在しなければならない(NarrativeConnectionAuditor が検証)

#### 6.6.7 葛藤強度の 7 日間アーク(v10 §2.5 準拠)

| Day | 強度 | 内容 |
|---|---|---|
| 1 | 弱 | 日常の中の小さな違和感 |
| 2 | 弱〜中 | 違和感が継続、軽い揺らぎ |
| 3 | 中 | 明確な選択を迫られる |
| 4 | 中〜強 | 選択の結果が跳ね返ってくる |
| 5 | **強(山場)** | 価値観の中核を揺さぶる出来事(予想外度「high」必須) |
| 6 | 余韻 | 直接的葛藤は弱め、Day 5 の影響を引きずる |
| 7 | 収束 | 完全解決ではなく、変化の予感を残す |

このアークは原則として動かさない。ただし Creative Director が concept_package の `critical_design_notes` で別のアークを指定した場合はそれに従う(例:全体を余韻基調にしたい、Day 3 に山場を置きたい、など)。

#### 6.6.8 Phase D の未決論点

以下は実装時に詰める必要がある論点。本仕様書レベルでは方向性のみ示す:

- **7 日分一括生成のプロンプト容量** ── 28〜42 件を 1 プロンプトで生成すると出力が肥大化する懸念がある。実装時に、Day 1〜3 / Day 4〜7 の 2 分割に格下げするオプションを残す。その場合、Day 1〜3 の foreshadowing を Day 4〜7 側が参照する構造にする
- **分布制約の最適値** ── 「low が半分以上」という閾値は v10 §7.2 でも未決扱い。実験で詰める
- **既知イベントと未知イベントの比率** ── 明示的な制約を入れるか(例:既知 3:未知 2)、LLM に任せるか
- **"meaning_to_character" の記述粒度** ── 1〜3 文としたが、NarrativeConnectionAuditor の pass 閾値は実験で詰める

---

## 7. Tier 2:Worker Agents

### 7.1 共通仕様

Tier 2 の Worker Agents は、自分の担当範囲の生成にだけ集中する単一責任エージェントである。以下の特性を持つ:

- **使用モデル**:Gemma 4 26B MoE(一部 31B Dense)を基本とする
- **入力**:Phase Orchestrator から渡されるコンテキスト
- **出力**:構造化された JSON(Gemma 4 のネイティブ structured output 機能を使用)
- **並列実行可能**:依存関係を遵守しつつ並列化される
- **状態を持たない**:stateless、毎回入力から出力を生成

Gemma 4 はfunction calling、structured JSON output、system instructions を native サポートしているため、Worker 実装はシンプルになる。

### 7.2 Worker の呼び出し方

各 Worker は Claude Agent SDK の custom tool として実装され、Phase Orchestrator から呼ばれる。

```python
@tool("basic_info_worker", "Generate basic info section of macro profile", {
    "concept_package": dict,
    "existing_context": dict
})
async def basic_info_worker(args):
    prompt = build_worker_prompt(
        worker_role="BasicInfoWorker",
        concept=args["concept_package"],
        context=args["existing_context"],
        output_schema=BASIC_INFO_SCHEMA
    )
    result = await gemma4_api_call(
        model="gemma-4-26b-moe",
        prompt=prompt,
        response_format="json",
        schema=BASIC_INFO_SCHEMA
    )
    return {
        "content": [
            {"type": "text", "text": json.dumps(result)}
        ]
    }
```

この custom tool パターンにより、Claude Agent SDK で動く Master Orchestrator(Opus)が、必要に応じて Gemma 4 の Worker を呼ぶ階層構造が成立する。

### 7.3 Worker プロンプトの共通構造

全 Worker に共通するプロンプト構造:

```
# あなたの役割
{worker_role}

# あなたの担当範囲
{responsibility_description}

# 参考となる情報(Creative Director の方向性)
{concept_package}

# すでに決まっていること
{existing_context}

# あなたの出力形式
{output_schema_as_json}

# 制約
- 必ず指定された JSON 形式で出力すること
- 既存のコンテキストと矛盾しないこと
- concept_package の critical_design_notes を尊重すること
- AI っぽい無難な記述を避けること
- 具体的で個性的な内容にすること

# 守るべき設計思想
{design_principles}
```

### 7.4 Phase A-1 Workers の詳細

#### 7.4.1 BasicInfoWorker

- **入力**:concept_package のみ
- **出力**:basic_info + social_position(macro_profile の最初の 2 セクション)
- **特記事項**:このキャラの輪郭を決める最上流の Worker。他の全 Worker が参照する。創造的自由度が高い。

#### 7.4.2 FamilyWorker

- **入力**:concept_package + basic_info
- **出力**:family_and_intimacy
- **特記事項**:家族構成は物語的に重要。親友も記述する。

#### 7.4.3 LifestyleWorker

- **入力**:concept_package + basic_info
- **出力**:current_life_outline
- **特記事項**:v10 仕様書 3.3 の気質パラメータ #23(規則性志向)とのゆるい整合を意識する。生活リズムが気質を表す。

#### 7.4.4 DreamWorker

- **入力**:concept_package + basic_info
- **出力**:dream_timeline(子供時代 → 現在の夢までの時系列)
- **特記事項**:「夢の根にある何か」を 1 文で記述する。これは後の Phase A-3 で dream_origin エピソードと接続する。

#### 7.4.5 VoiceWorker

- **入力**:concept_package + basic_info
- **出力**:voice_fingerprint
- **特記事項**:このアプリの特徴である「言語的指紋」を具体化する最重要 Worker の一つ。「避ける語彙」(例:「成長」「気づき」)を必ず 2〜3 個指定する。これは日記生成時に省略指示として効く。

#### 7.4.6 ValuesCoreWorker

- **入力**:concept_package + basic_info
- **出力**:values_core(最も大事、絶対許せない、誇り、恥じ)
- **特記事項**:narrative 形式で書くこと。箇条書きではなく、1〜2 文の自然な表現で。Phase A-2 の ValuesWorker と整合するが、こちらは自然言語、あちらは構造化。

#### 7.4.7 SecretWorker

- **入力**:concept_package + basic_info + values_core(ValuesCoreWorker の出力)
- **出力**:secrets
- **特記事項**:「日記にも書かないかもしれないこと」を必ず 1〜2 個含める。これは日記生成時に意図的に欠落するべき情報として機能する。

#### 7.4.8 RelationshipNetworkWorker

- **入力**:family_and_intimacy(FamilyWorker の出力)
- **出力**:relationship_network(拡張された関係性リスト)
- **特記事項**:家族以外の重要人物を追加する。各人物に「質感」(好き/苦手/複雑)を付与する。

### 7.5 Phase A-2 Workers の詳細(抜粋)

#### 7.5.1 TemperamentWorker_A1(情動反応系 9 個)

担当:Novelty Seeking, Harm Avoidance, Reward Dependence, Persistence, Threat Sensitivity, Behavioral Inhibition, Emotional Intensity, Positive Mood Baseline, Negative Mood Baseline

プロンプトには以下を含める:
- 各パラメータの定義(v10 §3.3 の表より)
- 各パラメータの生物学的基盤(v10 §3.3 より)
- macro_profile(既にキャラの輪郭が決まっている)
- concept_package の psychological_hints.temperament_direction

出力:9 個のパラメータ(1〜5 の値 + 自然言語記述)

#### 7.5.2 ValuesWorker(Schwartz 19 価値)

担当:Schwartz Refined Theory of Basic Values の 19 価値すべて

Schwartz 19 価値の一覧:
1. Self-Direction–Thought(自己方向-思考)
2. Self-Direction–Action(自己方向-行動)
3. Stimulation(刺激)
4. Hedonism(快楽)
5. Achievement(達成)
6. Power–Dominance(権力-支配)
7. Power–Resources(権力-資源)
8. Face(面子)
9. Security–Personal(安全-個人)
10. Security–Societal(安全-社会)
11. Tradition(伝統)
12. Conformity–Rules(同調-規則)
13. Conformity–Interpersonal(同調-対人)
14. Humility(謙虚)
15. Benevolence–Dependability(博愛-信頼性)
16. Benevolence–Caring(博愛-ケア)
17. Universalism–Concern(普遍-関心)
18. Universalism–Nature(普遍-自然)
19. Universalism–Tolerance(普遍-寛容)

各価値に「strong / medium / weak」を付与する。

重要:気質・性格層と規範層は**独立に**決定されるべき(v10 §3.2)。つまり、気質で「勤勉性 = 低(怠惰)」でも、規範層で「達成 = strong(勤勉であるべき)」は許容される。むしろこのギャップが内省の源泉である。ValuesWorker は macro_profile と concept_package を参照しつつも、TemperamentWorker/PersonalityWorker の出力に引きずられないこと。

### 7.6 Phase A-3 Writers の詳細(抜粋)

#### 7.6.1 ContaminationWriter

担当:エピソード全体の多様性を確保するため、「contamination 的な色合い(良かったものが損なわれた経験)」を持つエピソードを 1 つ以上担当する Writer。

**重要な設計思想**:

この Writer は個別エピソードに特定の narrative 構造を強制しない。「良かったもの → 損なわれた → ネガティブな現在」のような固定構造を押し付けたり、「最後に救済や成長があってはいけない」と禁止したりはしない。成長や救済を含むエピソードが結果的に生成されても、それ自体は問題ない。narrative の転回や結末は自由。

問題なのは、**5〜8 個のエピソード全体が特定の体験パターンに偏ること**(例:全部が redemption sequence になる、全部が成功体験になる、全部が悲劇になる、など)。この偏りを避けるために Writer をカテゴリ別に分けているのであって、各 Writer が特定の narrative 構造を書かされているわけではない。

プロンプトの特徴:
- 「損なわれた経験」という題材を軸にエピソードを生成する
- narrative の形式・構造・結末は自由(救済があっても成長があってもよい)
- 200〜400 字の narrative
- 時期と関与する他者を EpisodePlanner から受け取る
- 現在のどの価値観・怖れ・夢と紐づくかを指定

出力例:
```json
{
  "narrative": "中学3年の時、親友だった〇〇と毎日放課後に絵を描いていた。その時間が一番安心できる場所だった。〇〇が急に転校することになったのは2月だった。連絡先は交換したが、春が来る頃には返信が来なくなった。何を描いても、隣に誰もいないことが気になって筆が止まるようになり、それから絵を描くのをやめた。今も画材は捨てていないが、開けていない。",
  "metadata": {
    "life_period": "adolescence",
    "category": "contamination",
    "involved_others": ["中学時代の親友"],
    "connected_to": {
      "values": ["Benevolence-Dependability が強い理由"],
      "fears": ["親密な関係の喪失"]
    },
    "unresolved": true
  }
}
```

この例は「持続する欠落」で終わる形だが、これは数ある書き方の一つに過ぎない。同じ「損なわれた経験」を題材にしても、そこから立ち直って新しい何かを始めるエピソードも、未だに曖昧な感情を抱え続けるエピソードも、どれも成立する。Writer の役割は多様性の一役を担うことであって、固定の結末を出すことではない。

### 7.7 Phase D Workers の詳細

#### 7.7.1 WorldContextWorker

担当:薄い世界観・時代設定の確定。v1 までの `WorldSettingWorker` の軽量版。

v10 では世界モデルはもはや Phase D の主役ではなく、「7 日分イベント列がどこで起きるか」の背景情報に過ぎない。したがって WorldContextWorker は、過剰な世界観設定を生成してはならない。1 段落程度で、時代軸・地理・ジャンルだけを確定する。

入力:
- concept_package の `genre_and_world`
- macro_profile の `social_position`

出力:
- `world_context.name`
- `world_context.description`(1 段落)
- `world_context.time_period`
- `world_context.genre`

#### 7.7.2 SupportingCharactersWorker

担当:周囲の人物 5〜7 人のプロファイル生成。macro_profile の `relationship_network` を拡張する。

重要な設計判断:新規人物を大量に追加してはならない。既存の `relationship_network` の人物を優先的に取り上げ、各人物に「own_small_want(その人自身の小さな欲求)」を付与することで深みを出す。新規追加は 1〜2 人までが目安。

入力:
- macro_profile の `family_and_intimacy` と `relationship_network`
- concept_package の `character_concept` と `story_outline`

出力:
- 5〜7 人の `supporting_characters` 配列
- 各人物に `own_small_want` を付与(これは WeeklyEventWriter が各人物をイベントに登場させる際の動機ソースになる)

#### 7.7.3 NarrativeArcDesigner

担当:7 日間の物語アーク設計。Phase D の中核 Worker の 1 つで、WeeklyEventWriter に先行して実行される。

v10 における最重要責務:**Day 5 山場の具体的な方向性を決定し、Day 1〜4 のどこに何を伏線として置くかを明示する**。この設計がないと WeeklyEventWriter は物語連続性を意識せずに 28〜42 件を生成してしまう。

入力:
- concept_package(特に `story_outline` と `interestingness_hooks`)
- macro_profile
- micro_parameters(気質・性格・規範のすべて)
- autobiographical_episodes(全文)
- world_context(WorldContextWorker の出力)
- supporting_characters(SupportingCharactersWorker の出力)

出力:
- `narrative_arc_type`(Vonnegut 型アーク名、例:"man_in_a_hole")
- `arc_description`(1 段落)
- `day5_climax_design`(Day 5 山場の具体的方向性、どの価値観/理想/自伝的エピソードが揺さぶられるか)
- `foreshadowing_plan`(Day 1〜4 のどこに何を伏線として置くかのリスト)
- `recurring_motifs`(通奏低音モチーフ 2〜3 個)
- `day6_aftermath_direction`
- `day7_convergence_direction`

**プロンプトの特徴:** NarrativeArcDesigner のプロンプトには「Day 5 で揺さぶる価値観を 1 つに絞り、その価値観とキャラの自伝的エピソードの繋がりを明示すること」を必ず指示する。これにより、Day 5 山場が「なんとなく大事件が起きる」ではなく「このキャラにとって決定的に意味がある」ものになる。

#### 7.7.4 ConflictIntensityDesigner

担当:7 日間の葛藤強度アークと、各日の予想外度分布目標の設計。

v10 §2.5 のアーク表(Day 1=弱、Day 5=強、Day 7=収束)を基本骨格としつつ、concept_package の `critical_design_notes` で別のアークが指定されていればそれに従う。

入力:
- concept_package(特に `critical_design_notes`)
- micro_parameters
- narrative_arc(NarrativeArcDesigner の出力)

出力:
- `conflict_intensity_arc`(7 日分の強度)
- `expectedness_distribution_target`(各日の予想外度「低/中/高」の目標件数)

#### 7.7.5 WeeklyEventWriter

担当:28〜42 件のイベント列を 1 回の Opus 呼び出しで一括生成する。Phase D の最重要 Worker。

プロンプト構造は §6.6.5 に詳述。以下は実装上の補足:

**モデル選択:** Claude Opus 4.6 固定。Sonnet や Gemma では 28〜42 件を俯瞰した上で伏線・連続性を保つのは難しい。これは本アプリ全体でも最もコストが高い Worker の 1 つだが、アプリの価値を決定づける部分なので妥協しない。

**出力の取り扱い:** WeeklyEventWriter は最初から `events` 配列を時刻順ソート済みで出力するよう指示される。ただし出力後に Python 側で再度ソートして確実性を担保する(LLM 出力の順序は信用しない)。

**再生成時の差分最小化:** EventMetadataAuditor / DistributionValidator / NarrativeConnectionAuditor のいずれかで不合格になった場合、全 28〜42 件の再生成は避けたい。代わりに「違反があったイベントだけ該当 ID を指定して部分再生成」を指示する。WeeklyEventWriter は再生成要求時、既存の他イベントを `context` として受け取り、それとの整合性を保ちながら違反イベントだけ書き換える。

入力:
- concept_package
- macro_profile
- micro_parameters
- autobiographical_episodes(全文ベタ貼り)
- world_context
- supporting_characters
- narrative_arc(特に `day5_climax_design` と `foreshadowing_plan`)
- conflict_intensity_arc

出力:
- 28〜42 件の events 配列(§6.6.6 の schema 準拠)

#### 7.7.6 EventMetadataAuditor

担当:WeeklyEventWriter の出力に対して、メタデータ完全性の検証。

検査項目:
- すべてのイベントに `known_to_protagonist`(true/false)が付いているか
- `known_to_protagonist: true` のイベントに `source`("routine" または "prior_appointment")が付いているか
- `source: "protagonist_plan"` のイベントが **含まれていないこと**(これは日次ループ専用のため Phase D では生成禁止)
- すべてのイベントに `expectedness`("low" / "medium" / "high")が付いているか
- すべてのイベントに `meaning_to_character` が 1 文以上で記述されているか
- すべてのイベントに `narrative_arc_role` が付いているか
- すべてのイベントに `time_slot` と `content` が付いているか

モデル:Sonnet 4.6(機械的なチェックが多いため Opus は不要)

不合格時:該当イベントの ID を列挙し、WeeklyEventWriter に部分再生成を指示

#### 7.7.7 DistributionValidator

担当:予想外度分布制約の検証。Python のルールベース関数で実装し、LLM を使わない。

検査項目:
- 各日について `expectedness: "low"` の件数が総数の半分以上
- `expectedness: "high"` が Day 5 以外で 1 日あたり最大 1 件
- Day 5 に `expectedness: "high"` が 1 件以上
- 各日に `known_to_protagonist: true` と `known_to_protagonist: false` の両方が含まれる
- 各日のイベント総数が 4〜6 件の範囲内
- 全体のイベント総数が 28〜42 件の範囲内

実装:

```python
def validate_distribution(events: list) -> ValidationResult:
    violations = []
    by_day = group_by_day(events)
    for day, day_events in by_day.items():
        total = len(day_events)
        if total < 4 or total > 6:
            violations.append(f"Day {day}: 件数 {total} は 4〜6 の範囲外")
        low_count = sum(1 for e in day_events if e["expectedness"] == "low")
        if low_count * 2 < total:
            violations.append(f"Day {day}: low が半分未満")
        high_count = sum(1 for e in day_events if e["expectedness"] == "high")
        if day == 5 and high_count < 1:
            violations.append(f"Day 5: high が 0 件(山場要件違反)")
        if day != 5 and high_count > 1:
            violations.append(f"Day {day}: high が {high_count} 件(最大 1 件)")
        known_count = sum(1 for e in day_events if e["known_to_protagonist"])
        if known_count == 0 or known_count == total:
            violations.append(f"Day {day}: known/unknown の片方が 0 件")
    if len(events) < 28 or len(events) > 42:
        violations.append(f"全体件数 {len(events)} は 28〜42 の範囲外")
    return ValidationResult(passed=len(violations)==0, violations=violations)
```

モデル:LLM 不要(Python 関数)

不合格時:違反リストを WeeklyEventWriter に渡して部分再生成を指示

#### 7.7.8 NarrativeConnectionAuditor

担当:物語連続性と伏線の検証。Phase D の Evaluator として最も高度な判断が要求される。

検査項目:
- `narrative_arc_role: "day5_foreshadowing"` のイベントが Day 1〜4 に少なくとも 1 件存在するか
- Day 5 山場のイベント(`expectedness: "high"`)が NarrativeArcDesigner の `day5_climax_design` と整合するか
- 前日の出来事が翌日に跳ね返る構造(`narrative_arc_role: "previous_day_callback"`)が複数存在するか
- 各イベントの `meaning_to_character` が具体的で、抽象的な記述(「価値観と関連する」等)で済ませていないか
- Day 6 が Day 5 の余韻として機能しているか
- Day 7 が完全解決ではなく変化の予感を残しているか

モデル:Opus 4.6(物語的判断が要求される)

不合格時:NarrativeConnectionAuditor は具体的な改善提案を生成する。例:「Day 3 の夕方のイベントは foreshadowing が弱い。Day 5 山場で揺さぶられる価値観との明示的な繋がりを追加すべき」。この提案と共に WeeklyEventWriter に部分再生成を指示。

---

## 8. Tier 3:Evaluators

### 8.1 役割

Tier 3 Evaluators は、各 Phase の出力を評価し、品質基準を満たさない場合に Master Orchestrator 経由で再生成指示を出す。これは Anthropic の **Evaluator-Optimizer パターン** の実装である。

Evaluators の特徴:
- 生成は行わず、評価のみを行う
- 独立した視点を持つ(Generator と同じモデル/プロンプトを使わない)
- 明確な判定基準(rubric)を持ち、判定プロセスを透明化する
- 再生成ループは最大 4 回まで

### 8.2 使用モデル

**Claude Sonnet 4.6**。理由:
- Evaluator は高頻度で呼ばれるため、Opus だとコストが膨大
- 判定は明確な rubric に基づくため、Sonnet の推論力で十分
- Gemma 4 だと評価の厳しさが Opus/Sonnet に比べて緩い傾向がある

### 8.3 Evaluators の種類

| Evaluator 名 | 対象 | 評価軸 |
|---|---|---|
| `SchemaValidator` | 全 Phase | JSON schema 準拠(ルールベース、LLM 不要) |
| `ConsistencyChecker` | 全 Phase | Phase 間・項目間の整合性 |
| `BiasAuditor` | Phase A-3 | Redemption bias、陰影の濃度 |
| `InterestingnessEvaluator` | 全 Phase | 面白さ、AI っぽさの不在 |
| `EventMetadataAuditor` | Phase D | イベントメタデータの完全性(v2 新設) |
| `DistributionValidator` | Phase D | 予想外度分布制約(ルールベース、LLM 不要、v2 新設) |
| `NarrativeConnectionAuditor` | Phase D | 物語連続性・伏線・「意味を持つ理由」の質(v2 新設) |

**v2 における新設 Evaluator:** Phase D が v10 で完全に責務が変わったため、Phase D 専用の 3 つの Evaluator を新設した。これらの仕様詳細は §7.7.6〜§7.7.8 に Worker 記述として記載済みのため、ここでは §8.4 以降の汎用 Evaluator(ConsistencyChecker 等)だけを記述する。

### 8.4 ConsistencyChecker

#### 8.4.1 評価項目

```
【ConsistencyChecker 評価項目】

[A] Phase 内整合性

  Phase A-1:
    □ basic_info と social_position は矛盾しないか
      (例:学生なのに「会社役員」と書かれていない)
    □ family_and_intimacy と relationship_network は一致するか
    □ dream_timeline の時系列に矛盾はないか
    □ voice_fingerprint の「避ける語彙」は values_core と整合するか

  Phase A-2:
    □ 気質と性格の極端な矛盾はないか
      (例:新奇性追求 = 5 と 規則性志向 = 5 の同時出現)
    □ 対他者認知層は性格層と整合するか
      (例:社会的比較傾向 = 5 と 嫉妬気質 = 1 は整合するか)
    □ 認知パラメータの自動導出値は正しい計算結果か
    □ 気質・規範のギャップは「設計された内省の源泉」として機能するか、
      それとも「単なる矛盾」か

  Phase A-3:
    □ 各エピソードは macro_profile の関係者と整合するか
    □ 各エピソードは micro_parameters の気質・性格と整合するか
    □ エピソードの時期に重複や矛盾はないか
    □ 価値観/夢/怖れとの接続が明示されているか

  Phase D:
    □ world_context は macro_profile と整合するか
      (現代日本人なのに中世ヨーロッパの世界設定ではないか)
    □ supporting_characters は relationship_network と整合するか
    □ events の各イベントは macro_profile の current_life_outline
      および週間固定予定・ルーティンと整合するか
    □ source: "routine" のイベントが macro_profile のルーティンから
      自然に展開されたものか
    □ source: "protagonist_plan" が 1 件も含まれていないか
      (Phase D では生成禁止、日次ループ専用)
    □ Day 5 の expectedness: "high" イベントが threatened_values を
      実際に脅かしているか
    □ narrative_arc.day5_climax_design と Day 5 の events が整合するか

[B] Phase 間整合性

  □ macro_profile と micro_parameters
    例:VoiceWorker が「絵文字を多用する」と書いたのに
    PersonalityWorker_B3 の感情への開放 = 1 は矛盾

  □ micro_parameters と autobiographical_episodes
    例:気質が「Novelty Seeking = 5, Persistence = 5」なのに
    エピソードが全部「同じ場所で同じことを繰り返す」系は矛盾

  □ autobiographical_episodes と weekly_events_store
    例:エピソードで「親友を失って親密な関係を怖れる」と書いたのに
    weekly_events_store の supporting_characters に 5 人の
    親密な友人がいるのは矛盾

  □ micro_parameters と weekly_events_store.events
    例:気質が「HA 高 + 社交性低」のキャラなのに、events に
    突発的な大規模パーティー参加が含まれ、かつ meaning_to_character
    が「楽しみにしていた」系になっているのは矛盾

[C] 概念層との整合性

  □ 全 Phase の出力が concept_package の critical_design_notes を
    尊重しているか
  □ narrative_theme と一致する方向性を持っているか
  □ interestingness_hooks が具体的なパラメータや出来事に反映されているか
```

#### 8.4.2 判定結果

ConsistencyChecker の出力:

```json
{
  "passed": false,
  "violations": [
    {
      "severity": "high | medium | low",
      "phase": "A-1 | A-2 | A-3 | D",
      "location": "string (どこで矛盾が起きているか)",
      "description": "string (何が矛盾しているか)",
      "suggested_fix": "string (どう修正すべきか)"
    }
  ],
  "overall_comment": "string"
}
```

high severity の violation が 1 つでもあれば再生成が必要。medium 以下なら注意付きで通過。

### 8.5 BiasAuditor

Phase A-3 専用の Evaluator。6.5.5 節の評価基準に従う。ここでは再掲しないが、要点は以下:

- 配分の遵守(redemption ≤ 2, contamination ≥ 1, loss ≥ 1, ambivalent ≥ 1)
- 実質的な redemption bias の検出(ラベルが contamination でも内容が救済型の場合)
- 陰影の濃度(全体のトーンバランス)
- 時期の分散
- 価値観・夢との接続

### 8.6 InterestingnessEvaluator

#### 8.6.1 評価項目

最も主観的な評価だが、明確な rubric で運用する。

```
【InterestingnessEvaluator 評価項目】

[A] AI っぽさの検出(減点対象)

  □ 「優しい」「元気」「好奇心旺盛」のような曖昧形容詞が多用されている
  □ 「〜を大切にしている」「〜を愛している」のような漠然とした記述
  □ 全体のトーンが過度にポジティブ
  □ 固有名詞が少なく、抽象的な表現が多い
  □ 矛盾や陰影がなく、全部が辻褄が合いすぎている
  □ 「心の声」的な記述が空疎(「彼女は考えた...」だけで終わっている)

[B] 具体性の確認(加点対象)

  □ 具体的な固有名詞が使われている(人物名、場所名、物の名前)
  □ 具体的な時期が指定されている(「中学 3 年の 2 月」)
  □ 具体的な感覚描写がある(視覚、聴覚、嗅覚、触覚)
  □ 具体的なセリフや会話が含まれている(エピソードの場合)
  □ 具体的な数字や量がある(「3 年前」「2 回目の」)

[C] 矛盾・陰影の存在(加点対象)

  □ キャラの価値観・気質・過去の経験の間に「生産的な矛盾」がある
  □ キャラの行動が「予測できない」要素を持つ
  □ キャラに「弱さ」「恥」「後悔」が具体的に書かれている
  □ 全部が解決していない、未解決の要素がある
  □ 成功体験と失敗体験のバランスが取れている

[D] 続きが気になる掴み(加点対象)

  □ 初見で「このキャラは何者?」と興味を惹かれる要素がある
  □ この 7 日間で何が起きるのか予想がつかない
  □ 通奏低音モチーフが魅力的
  □ キャラの Want と Need の緊張関係が明確

[E] 読み物としての質(加点対象)

  □ 言語的指紋が具体的で、日記の語り口を想像できる
  □ キャラの視点の個性(何に注目し、何を無視するか)が明確

判定基準:
  減点 - 加点 で総合スコアを算出
  スコア > 閾値 → pass
  スコア ≤ 閾値 → fail(再生成)
```

#### 8.6.2 出力

```json
{
  "overall_score": 0.72,
  "threshold": 0.60,
  "passed": true,
  "ai_sloppiness_detected": [
    "string (具体的な AI っぽい記述箇所)"
  ],
  "specificity_strengths": [
    "string (具体性が出ている箇所)"
  ],
  "contradiction_richness": "high | medium | low",
  "hook_quality": "string (掴みの評価)",
  "suggestions": [
    "string (改善提案)"
  ]
}
```

### 8.7 SchemaValidator

LLM を使わず、Python のルールベース関数で JSON schema 準拠をチェックする。

```python
from jsonschema import validate, ValidationError

def validate_macro_profile(data: dict) -> ValidationResult:
    try:
        validate(instance=data, schema=MACRO_PROFILE_SCHEMA)
        return ValidationResult(passed=True)
    except ValidationError as e:
        return ValidationResult(
            passed=False,
            error=str(e),
            location=e.absolute_path
        )
```

これは高速で決定論的なため、Phase 完了時に最初に呼ぶ評価。ここで fail したら LLM Evaluator を呼ぶ前に即再生成する。

### 8.8 Evaluator-Optimizer ループの全体構造

```
【Evaluator-Optimizer ループ】

Phase 完了
  ↓
Step 1: SchemaValidator(ルールベース)
  - 高速チェック
  - fail → Worker に再生成指示(schema 違反の箇所のみ)
  - pass → Step 2 へ
  ↓
Step 2: ConsistencyChecker(Sonnet 4.6)
  - Phase 内・Phase 間の整合性
  - fail → Worker に再生成指示
  - pass → Step 3 へ
  ↓
Step 3: BiasAuditor(Sonnet 4.6、Phase A-3 のみ)
  - Redemption bias 検出
  - fail → Writer に再生成指示
  - pass → Step 4 へ
  ↓
Step 4: InterestingnessEvaluator(Sonnet 4.6)
  - 面白さ評価
  - fail → 該当 Worker に再生成指示
  - pass → Phase 合格、次の Phase へ
  ↓
反復カウンタ
  - 各 Evaluator で fail が出るたびに該当 Worker の
    反復カウンタがインクリメント
  - 4 回に達したら、該当 Worker の暫定ベスト出力を採用し、
    警告フラグを立てて次に進む
```

### 8.9 評価層のオン/オフ設計(プロファイル)

#### 8.9.1 背景

§2.11 に示した通り、Tier 3 Evaluators は品質に大きく寄与する一方で、トークン消費量を劇的に押し上げる。典型的には、全 Evaluator を有効化すると、Evaluator なしの場合に比べて LLM 呼び出し数が 1.5〜2.0 倍、実コストは 2.0〜2.5 倍になる(評価のたびに追加の LLM 呼び出しが発生し、不合格時には再生成ループが回るため)。

ユーザーが常に最高品質を求めているわけではない。たたき台を素早く見たい、パラメータの大枠だけ確認したい、キャラクター設計を何度も試行錯誤したい、といった用途では、Evaluator を全部オフにした方が実用的である。本番提出や重要なデモの直前には全 Evaluator を有効化して慎重に生成する、という使い分けが必要。

#### 8.9.2 4 つのプロファイル

本アプリは以下の 4 つのプロファイルを提供する:

| プロファイル | Tier -1 Self-Critique | SchemaValidator | ConsistencyChecker | BiasAuditor (A-3) | InterestingnessEvaluator | EventMetadataAuditor (D) | DistributionValidator (D) | NarrativeConnectionAuditor (D) | 想定用途 |
|---|---|---|---|---|---|---|---|---|---|
| **High Quality** | ON(最大 4 回) | ON | ON | ON | ON | ON | ON | ON | 本番提出用、慎重に作る |
| **Standard** | ON(最大 3 回) | ON | ON | ON | OFF | ON | ON | ON | 通常使用、バランス型 |
| **Fast** | ON(最大 2 回) | ON | OFF | ON | OFF | ON | ON | OFF | 素早い試作、要点確認 |
| **Draft** | ON(最大 1 回) | ON | OFF | OFF | OFF | OFF | ON | OFF | 最速、たたき台 |

設計原則:

**(a) Tier -1 Self-Critique は全プロファイルで ON**
最上流の品質はどのプロファイルでも妥協しない。ただし反復回数はプロファイルに応じて変える。High Quality は最大 4 回、Draft は最大 1 回。Draft でも最低 1 回は Self-Critique が走り、明らかに破綻した concept_package が下流に流れ込むのを防ぐ。

**(b) SchemaValidator と DistributionValidator は全プロファイルで ON**
いずれもルールベース関数のためコストはほぼゼロ。構造的破損と予想外度分布違反の検出は常に必要。特に DistributionValidator は Phase D の「low 半分以上」「Day 5 に high 必須」などの制約を機械的に担保する最低限の安全網。

**(c) Tier 3 Evaluators はプロファイル依存**
LLM を使う Evaluator は、プロファイルによってオン/オフする。切る順序は以下:

- 最初に切るのは **InterestingnessEvaluator**(主観的評価、コスト高、効果が測定しにくい)
- 次に切るのは **NarrativeConnectionAuditor**(Opus 呼び出しのため高コスト、Fast 以下でオフ)
- 次に切るのは **ConsistencyChecker**(Phase 内の軽微な矛盾は許容、SchemaValidator と DistributionValidator で最低限の整合性は担保される)
- **BiasAuditor** は Fast プロファイルまで残す(Phase A-3 に対してのみ)。Draft では切る
- **EventMetadataAuditor** は Sonnet で比較的安価なので Fast まで残す。Draft で切る

**(d) Fast プロファイルの特例**
Fast では BiasAuditor と EventMetadataAuditor を残す。BiasAuditor は Phase A-3 の Worker 分割の意味を保つため、EventMetadataAuditor は Phase D のメタデータ欠損を防ぐため、いずれも切ると品質が劇的に下がる。

**(e) Phase D 専用 Evaluator の重要性**
Phase D は v10 で責務が大きく変わり、28〜42 件のイベントを一括生成する構造になっている。ここでメタデータ欠損や分布違反が起きると、日記生成本体の日次ループで大規模な不整合が発生する。したがって Phase D の 3 Evaluator のうち少なくとも 2 つ(EventMetadataAuditor と DistributionValidator)は、Draft 以外で常に ON に設定する。

#### 8.9.3 プロファイルの選択 UI

プロファイルは以下の場面で選択可能:

- **生成開始時**:起動画面でプロファイルを選ぶ(デフォルトは Standard)
- **生成中**:途中で変更はできない(現行プロファイルで最後まで走る)
- **共同編集モード**:再生成要求を出すたびに、その再生成にだけ適用されるプロファイルを指定できる

UI では以下のように表示する:

```
プロファイル選択

[○] High Quality  品質最優先 / 約 10〜15 分 / 約 $3.50〜5.00
[●] Standard      バランス型 / 約 5〜8 分  / 約 $1.80〜2.50
[○] Fast          素早い試作 / 約 2〜4 分  / 約 $0.80〜1.20
[○] Draft         たたき台  / 約 1〜2 分  / 約 $0.50〜0.80

詳細設定(上級者向け) ▼
  Tier -1 Self-Critique 反復回数: [3]
  ConsistencyChecker:  [●] ON [○] OFF
  BiasAuditor:         [●] ON [○] OFF
  InterestingnessEvaluator: [○] ON [●] OFF
```

詳細設定を開けば、各 Evaluator を個別にオン/オフできる。上級者向けで、デフォルトではプロファイル単位での切り替えで十分。

#### 8.9.4 プロファイルの内部実装

プロファイルは設定オブジェクトとして Master Orchestrator に渡される:

```python
@dataclass
class EvaluationProfile:
    name: str  # "high_quality" | "standard" | "fast" | "draft"
    director_self_critique_max_iterations: int
    schema_validator_enabled: bool  # 常に True
    consistency_checker_enabled: bool
    bias_auditor_enabled: bool
    bias_auditor_phases: list[str]  # ["A-3"] or ["A-1", "A-2", "A-3", "D"]
    interestingness_evaluator_enabled: bool
    event_metadata_auditor_enabled: bool           # Phase D 専用、v2 新設
    distribution_validator_enabled: bool            # Phase D 専用、v2 新設、常に True 推奨
    narrative_connection_auditor_enabled: bool      # Phase D 専用、v2 新設
    worker_regeneration_max_iterations: int

PROFILES = {
    "high_quality": EvaluationProfile(
        name="high_quality",
        director_self_critique_max_iterations=4,
        schema_validator_enabled=True,
        consistency_checker_enabled=True,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=True,
        event_metadata_auditor_enabled=True,
        distribution_validator_enabled=True,
        narrative_connection_auditor_enabled=True,
        worker_regeneration_max_iterations=4,
    ),
    "standard": EvaluationProfile(
        name="standard",
        director_self_critique_max_iterations=3,
        schema_validator_enabled=True,
        consistency_checker_enabled=True,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=True,
        distribution_validator_enabled=True,
        narrative_connection_auditor_enabled=True,
        worker_regeneration_max_iterations=3,
    ),
    "fast": EvaluationProfile(
        name="fast",
        director_self_critique_max_iterations=2,
        schema_validator_enabled=True,
        consistency_checker_enabled=False,
        bias_auditor_enabled=True,
        bias_auditor_phases=["A-3"],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=True,
        distribution_validator_enabled=True,
        narrative_connection_auditor_enabled=False,
        worker_regeneration_max_iterations=2,
    ),
    "draft": EvaluationProfile(
        name="draft",
        director_self_critique_max_iterations=1,
        schema_validator_enabled=True,
        consistency_checker_enabled=False,
        bias_auditor_enabled=False,
        bias_auditor_phases=[],
        interestingness_evaluator_enabled=False,
        event_metadata_auditor_enabled=False,
        distribution_validator_enabled=True,  # ルールベースのため Draft でも ON
        narrative_connection_auditor_enabled=False,
        worker_regeneration_max_iterations=1,
    ),
}
```

Master Orchestrator は、各 Phase 完了後に `profile.xxx_enabled` フラグをチェックし、有効な Evaluator だけを呼ぶ。無効な Evaluator はスキップされる(LLM 呼び出し自体が発生しない)。

#### 8.9.5 プロファイル変更時の再キャッシュ

プロファイルを変更した場合、Prompt Cache は原則そのまま使える。キャッシュされているのはシステムプロンプトや中間成果物であり、Evaluator 起動の有無とは独立している。ただし、Evaluator 側のシステムプロンプトのキャッシュはプロファイルによって使用されないことがある(その Evaluator が無効化された場合)。Cache の TTL(5 分)内であれば自動的に再利用される。

---

## 9. データ構造(脚本パッケージ JSON schema)

### 9.1 脚本パッケージ全体構造

```json
{
  "metadata": {
    "version": "2.0",
    "generated_at": "ISO-8601 timestamp",
    "generator": "script-ai-app v2",
    "upstream_spec": "specification_v10.md",
    "total_iterations": {
      "creative_director": 2,
      "phase_a1": 1,
      "phase_a2": 1,
      "phase_a3": 3,
      "phase_d": 2
    },
    "total_llm_calls": 52,
    "total_cost_usd": 1.04
  },
  "concept_package": { ... (Tier -1 の出力) },
  "macro_profile": { ... (Phase A-1 の出力) },
  "micro_parameters": { ... (Phase A-2 の出力) },
  "autobiographical_episodes": { ... (Phase A-3 の出力) },
  "weekly_events_store": { ... (Phase D の出力、§6.6.6 参照) },
  "audit_report": {
    "consistency_checks": [...],
    "bias_audits": [...],
    "interestingness_scores": [...],
    "event_metadata_audits": [...],
    "distribution_validations": [...],
    "narrative_connection_audits": [...],
    "warnings": [...]
  }
}
```

**v1 からの変更点:** `world_model` フィールドは廃止され、`weekly_events_store` に置換された。`audit_report` には Phase D 専用 Evaluator(EventMetadataAuditor / DistributionValidator / NarrativeConnectionAuditor)の結果が追加される。

### 9.2 永続化

脚本パッケージは JSON ファイルとしてディスクに保存される。ディレクトリ構造:

```
./character_packages/
  ├ {character_name}_{timestamp}/
  │   ├ package.json                # 脚本パッケージ全体
  │   ├ concept.md                  # Creative Director の concept を読みやすく
  │   ├ macro_profile.md            # マクロプロフィール(人間可読)
  │   ├ parameters.csv              # ミクロパラメータ(スプレッドシート形式)
  │   ├ episodes/                   # 各エピソードを個別ファイルに
  │   │   ├ ep_001.md
  │   │   └ ...
  │   ├ weekly_events_store.md      # 7 日分イベント列(人間可読)
  │   ├ narrative_arc.md            # Phase D の物語アーク設計(人間可読)
  │   └ audit_report.md             # 評価レポート
  └ ...
```

人間可読形式(md)と機械可読形式(JSON)の両方を出力することで、ユーザーが内容を確認しやすくし、かつ下流の日記生成システムが直接パースできるようにする。

### 9.3 JSON schema の厳密定義

JSON schema は `./schemas/` 以下に分割して配置する:

```
./schemas/
  ├ concept_package.schema.json
  ├ macro_profile.schema.json
  ├ micro_parameters.schema.json
  ├ autobiographical_episodes.schema.json
  ├ weekly_events_store.schema.json
  └ character_package.schema.json  # 全体の統合 schema
```

各 Worker は自分が担当するサブセクションの schema を参照し、その schema に従った JSON を出力する。Gemma 4 の native JSON output 機能と組み合わせる。

---

## 10. 対話モード仕様

### 10.1 3 モードの詳細

#### 10.1.1 完全自動モード

**起動**:ユーザーが「完全自動生成」ボタンを押す

**フロー**:
1. ユーザー入力:なし
2. Creative Director が起動、内部ループを回して concept_package を決定
3. Master Orchestrator が自動で Phase A-1 → A-2 → A-3 → D を順次実行
4. 全 Phase 完了後、脚本パッケージをユーザーに提示
5. ユーザーは完成版を確認、必要なら共同編集モードに切り替えて部分修正

**所要時間の見積もり**(LLM コール数ベース):
- Creative Director:10〜30 Opus calls
- Phase A-1:約 8 Gemma calls + 数回の Evaluator
- Phase A-2:約 14 Gemma calls + 数回の Evaluator
- Phase A-3:約 10 Gemma calls(Writer + BiasAuditor の反復含む)
- Phase D:約 4〜8 Opus calls(NarrativeArcDesigner + WeeklyEventWriter + 3 Evaluator、再生成含む)
- 合計:55〜80 LLM calls、実時間で 6〜12 分程度

#### 10.1.2 テーマ指定モード

**起動**:ユーザーがテキスト入力欄にヒントを入力して「生成」ボタンを押す

**入力例**:
- 「信長が現代の東京にタイムスリップしてきた」
- 「大学院で研究に行き詰まっている 20 代後半の女性」
- 「引退した刑事が田舎町で静かに暮らしている」

**フロー**:
1. ユーザー入力:短い自然言語のヒント
2. Creative Director がヒントを起点に concept_package を決定(内部ループ)
3. 以降は完全自動モードと同じ

**Creative Director のヒント解釈**:
- ヒントに含まれる制約は尊重する(信長、現代東京、など)
- ヒントにない部分は Creative Director が創造的に埋める
- 曖昧な部分は Web 検索で参考情報を集めてから決定する

#### 10.1.3 共同編集モード

**起動**:(1) 生成済みの脚本パッケージに対してユーザーが編集を開始したとき、(2) 最初から共同編集モードを選んだとき

**UI 構成**:
- 左側:現在の脚本パッケージの各セクション
- 右側:チャット欄(Master Orchestrator との対話)
- 下部:各フィールドの編集欄(直接編集可能)

**操作方法**:

**(a) 直接編集**:
- 脚本パッケージの任意のフィールドを直接クリックして編集
- 編集を保存すると整合性チェックが自動実行される
- 他のフィールドに影響が波及する場合は Master Orchestrator が通知する

**(b) 自然言語指示**:
- チャット欄に「主人公をもっと内向的に」などと入力
- Master Orchestrator が影響範囲を判定し、該当 Worker を再起動
- 変更後の差分を提示し、ユーザーが承認

**(c) セクション単位の再生成**:
- 「このセクションを再生成」ボタンで、特定のセクションだけ完全再生成
- Creative Director に「現在のパッケージの他の部分は維持したまま、
  このセクションだけ違う方向性で作り直す」と指示

**(d) 自動生成ボタン**:
- 手動で一部を埋めて、残りを「自動補完」ボタンで埋める
- Master Orchestrator は既に決まっている情報を尊重して補完する

### 10.2 ユーザー入力の分類(Routing パターン)

Master Orchestrator は、ユーザーからの入力を以下のカテゴリに分類する:

| カテゴリ | 例 | 処理 |
|---|---|---|
| 初期生成要求 | 「信長が東京に」 | Creative Director を起動 |
| セクション編集 | 「主人公をもっと内向的に」 | 影響範囲を判定、該当 Worker を再起動 |
| 質問 | 「なぜこの値にしたの?」 | Creative Director が生成意図を説明 |
| 削除要求 | 「このエピソードを削除したい」 | Phase A-3 を部分再生成(配分を維持) |
| 追加要求 | 「友達をもう一人追加したい」 | Phase D の RelationshipNetworkWorker を再起動 |
| 承認 | 「これでいい」 | 現在の状態を確定 |
| やり直し | 「最初からやり直したい」 | 全 Phase リセット |

### 10.3 エージェント思考のストリーミング表示

ユーザーに対する最大の UX 提供は、**エージェントの思考過程をリアルタイムで見せる**こと。これは Claude Code / Cursor Composer と同じアプローチ。

UI 表示例:

```
[Creative Director] 
  Planning...
  ユーザーの入力「信長が東京に」を受けました。
  この設定で魅力的な物語を作るために、以下を決める必要があります:
    - 信長の気質は史実通りか、再解釈するか
    - タイムスリップの経緯と、現代でどう生活しているか
    - 1 週間の構成(葛藤強度アーク)
  Web で参考作品を調べます...

[Tool: web_search] "信長 現代 タイムスリップ 小説 漫画"
  → 関連作品: "信長のシェフ", "信長協奏曲", "信長のシェフ(小林源文)" 
  
[Creative Director]
  Analyzing references...
  既存作品の共通パターン:
  - 戦国の価値観と現代の価値観のギャップがコメディ/ドラマを生む
  - 信長の「革新者」側面が強調される
  差別化のため、本作では信長の「孤独」に焦点を当てます。
  
  Generating concept package...
  [Concept draft 完了]
  
  Self-critique...
  チェック項目:
    [A] 面白さ ... pass
    [B] 個性の深さ ... pass
    [C] Redemption Bias 回避 ... fail
      (「成長する信長」になりそう。現代を受け入れて現代的な価値観を
      獲得する結末は redemption bias)
    [D] 時間的連続性の種 ... pass
    [E] 整合性 ... pass
    [F] 実装可能性 ... pass
  
  Verdict: refine
  
  Refining concept...
  修正:「信長は最後まで現代を受け入れず、むしろ現代人の
  弱さを軽蔑する。でも特定の誰かとの関わりだけは残る」という
  非収束エンドに変更
  
  [iteration 2]
  Self-critique... all pass.
  
  Verdict: pass
  
[Master Orchestrator]
  concept_package を受け取りました。
  Phase A-1 を起動します...

[Phase A-1 Orchestrator]
  Launching 8 workers in parallel...
  
[BasicInfoWorker] Running...  ✓ (2.1s)
[FamilyWorker] Running...     ✓ (3.2s)
[LifestyleWorker] Running...  ✓ (2.8s)
[DreamWorker] Running...      ✓ (2.5s)
[VoiceWorker] Running...      ✓ (3.0s)
[ValuesCoreWorker] Running... ✓ (2.9s)
[SecretWorker] Running...     ✓ (2.4s)
[RelationshipNetworkWorker] Running... ✓ (2.7s)

[Phase A-1 Orchestrator]
  All workers completed. Running self-check...
  
[ConsistencyChecker]
  Checking Phase A-1 output...
  ✓ All fields populated
  ✓ Internal consistency OK
  verdict: pass
  
[Master Orchestrator]
  Phase A-1 complete. Starting Phase A-2...

...
```

すべての思考、ツール呼び出し、評価、再生成が透明化される。

---

## 11. UI 設計

### 11.1 画面構成

本アプリは 3 つの主要画面で構成される。

```
[画面1: 起動画面 / Mode Selection]
  - タイトル:「脚本生成 AI」
  - 3 つのモード選択ボタン:
    [完全自動生成]
    [テーマを指定して生成]
    [共同編集モード]
  - 過去の脚本パッケージ履歴

[画面2: 生成中画面 / Generation View]
  - 上部:進捗バー(Creative Director → Phase A-1 → A-2 → A-3 → D)
  - 中央:エージェント思考のストリーミング表示
  - 右側:現在の出力プレビュー(出来上がった Phase から順に表示)

[画面3: 結果画面 / Result View]
  - 左側:脚本パッケージの全セクション(タブ分け)
    - Concept
    - Macro Profile
    - Micro Parameters
    - Autobiographical Episodes
    - World Model
    - Audit Report
  - 右側:編集エリア(共同編集モード時)
  - 下部:
    [ダウンロード(JSON)] [ダウンロード(Markdown)] 
    [日記生成へ送る] [編集モード]
```

### 11.2 Generation View の詳細

```
┌──────────────────────────────────────────────────────┐
│  脚本生成 AI                            [ログ] [設定]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  進捗                                                │
│  [■■■■■■■■□□□□□□□□□□□□] 42% Phase A-2 実行中   │
│                                                      │
│  Tier -1 [██] Creative Director          ✓ 完了      │
│  Tier 1  [██] Phase A-1 Orchestrator     ✓ 完了      │
│  Tier 1  [██] Phase A-2 Orchestrator     実行中      │
│  Tier 1  [  ] Phase A-3 Orchestrator     待機中      │
│  Tier 1  [  ] Phase D Orchestrator       待機中      │
│                                                      │
├────────────────────────┬─────────────────────────────┤
│                        │                             │
│ 思考ログ               │ 現在の出力                   │
│                        │                             │
│ [Master Orchestrator]  │ ▼ Concept Package           │
│  Phase A-2 開始        │   [character_concept]       │
│                        │   「信長。享年47。1582年の  │
│ [TemperamentWorker_A1] │    本能寺の変で明智光秀に   │
│  実行中...             │    追い詰められた瞬間、時空 │
│                        │    の歪みに呑まれ、2026年の │
│ [TemperamentWorker_A2] │    東京・霞が関に出現した。 │
│  実行中...             │    ...」                    │
│                        │                             │
│ [PersonalityWorker_B1] │ ▼ Macro Profile             │
│  実行中...             │   [basic_info]              │
│                        │    name: 織田信長           │
│ ...                    │    age: 47 (見た目)         │
│                        │    ...                      │
│                        │                             │
└────────────────────────┴─────────────────────────────┘
```

### 11.3 Result View の詳細

```
┌──────────────────────────────────────────────────────┐
│  脚本生成完了 - 織田信長  (2026-04-09 14:23 生成)     │
├──────────────────────────────────────────────────────┤
│                                                      │
│ [Concept] [Macro] [Micro] [Episodes] [World] [Audit] │
│                                                      │
│ ▼ Macro Profile                                      │
│                                                      │
│ 基本情報                                              │
│ ├ 名前:織田信長                                      │
│ ├ 年齢:47                                            │
│ ├ 性別:男性                                          │
│ └ 外見:...                                           │
│                                                      │
│ 社会的位置                                            │
│ ├ 職業:(現代での) 無職                               │
│ ├ 住所:東京都・新宿の古いアパート                    │
│ └ ...                                                │
│                                                      │
│ ...                                                  │
│                                                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│ チャット                                              │
│ > "主人公をもっと内向的な感じにしたい"               │
│                                                      │
│ [Master Orchestrator]                                │
│  以下の変更を行います:                                │
│  - 気質:HA 3→4, Sociability 3→2                     │
│  - 影響:言語的指紋、秘密、自伝的エピソードも         │
│    再チェックされます                                 │
│  進めてよろしいですか? [はい] [いいえ]                │
│                                                      │
├──────────────────────────────────────────────────────┤
│ [JSON ダウンロード] [MD ダウンロード] [日記生成へ]    │
└──────────────────────────────────────────────────────┘
```

### 11.4 フロントエンド技術

- **HTML + Vanilla JS** を基本とする(学習コスト最小、デプロイ簡単)
- WebSocket でバックエンドと双方向通信
- スタイルは Tailwind CSS(CDN 経由)
- JSON 表示には単純な pretty-print、Markdown 表示には marked.js
- 複雑な状態管理は避ける(単一の state オブジェクトを JS で管理)

React や Vue を使わない理由:
- 締切までの時間制約
- バックエンドでエージェントが動くので、フロントエンドは「表示と入力だけ」
- 複雑な UI は必要ない
- デプロイを単純化するため

---

## 12. 技術スタック

### 12.1 バックエンド

| 要素 | 選定 | 理由 |
|---|---|---|
| 言語 | Python 3.11+ | Claude Agent SDK の native 言語 |
| Web フレームワーク | FastAPI | async 対応、WebSocket サポート、スキーマ自動生成 |
| エージェントランタイム | Claude Agent SDK (Python) | Subagent、tool use、context compaction |
| LLM API(上位) | Anthropic API (Opus 4.6, Sonnet 4.6) | Creative Director、Master Orchestrator、Evaluators |
| LLM API(下位) | Google AI Studio API (Gemma 4 26B MoE) | Workers、無料枠でコスト削減 |
| JSON schema | jsonschema(Python) | SchemaValidator 用 |
| 並列実行 | asyncio | Worker の並列起動 |
| 永続化 | ファイルシステム(JSON + MD) | 複雑な DB は不要、ディスク直接保存 |

### 12.2 フロントエンド

| 要素 | 選定 | 理由 |
|---|---|---|
| 基盤 | HTML5 + Vanilla JS | 学習コスト最小 |
| スタイル | Tailwind CSS(CDN) | 設定不要、高速開発 |
| 通信 | WebSocket(FastAPI と双方向) | リアルタイム思考ストリーミング |
| Markdown 表示 | marked.js(CDN) | エージェント思考の整形 |
| JSON エディタ | 単純な textarea | シンプル優先 |

### 12.3 デプロイ

開発環境:
- ローカル実行(`uvicorn main:app --reload`)
- `.env` ファイルで API キー管理

本番デプロイ(提出時):
- Google Cloud Run、Render、または Fly.io の無料枠
- Docker コンテナ化
- API キーは環境変数で管理

### 12.4 ディレクトリ構成

```
script-ai-app/
├ backend/
│   ├ main.py                  # FastAPI entrypoint
│   ├ agents/
│   │   ├ creative_director/
│   │   │   ├ director.py
│   │   │   ├ system_prompt.md
│   │   │   └ self_critique.py
│   │   ├ master_orchestrator/
│   │   │   └ orchestrator.py
│   │   ├ phase_a1/
│   │   │   ├ orchestrator.py
│   │   │   └ workers/
│   │   │       ├ basic_info.py
│   │   │       ├ family.py
│   │   │       └ ...
│   │   ├ phase_a2/
│   │   │   ├ orchestrator.py
│   │   │   └ workers/
│   │   │       ├ temperament_a1.py
│   │   │       └ ...
│   │   ├ phase_a3/
│   │   │   ├ orchestrator.py
│   │   │   └ workers/
│   │   │       ├ episode_planner.py
│   │   │       ├ writers/
│   │   │       └ bias_auditor.py
│   │   ├ phase_d/
│   │   │   └ ...
│   │   └ evaluators/
│   │       ├ consistency_checker.py
│   │       ├ bias_auditor.py
│   │       ├ interestingness_evaluator.py
│   │       └ schema_validator.py
│   ├ schemas/
│   │   ├ concept_package.json
│   │   ├ macro_profile.json
│   │   └ ...
│   ├ reference/                # Creative Director 用の参考資料
│   │   ├ screenplay_principles.md
│   │   ├ character_archetypes.md
│   │   ├ cloninger_temperament.md
│   │   ├ schwartz_values.md
│   │   └ mcadams_episode_categories.md
│   ├ tools/
│   │   ├ gemma4_api.py        # Gemma 4 呼び出しツール
│   │   ├ web_search.py        # Web 検索(built-in)
│   │   └ file_ops.py          # ファイル操作
│   ├ storage/
│   │   └ character_packages/  # 生成された脚本パッケージ
│   └ config.py
├ frontend/
│   ├ index.html
│   ├ css/
│   │   └ style.css
│   ├ js/
│   │   ├ app.js
│   │   ├ websocket.js
│   │   ├ renderer.js
│   │   └ editor.js
│   └ assets/
├ .env
├ requirements.txt
├ Dockerfile
└ README.md
```

### 12.5 主要な依存関係

```
# requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
claude-agent-sdk>=0.2.96
google-generativeai>=0.4.0
jsonschema>=4.21.0
python-dotenv>=1.0.0
pydantic>=2.6.0
httpx>=0.26.0
```

---

## 13. 実装計画

### 13.1 段階的実装方針

Anthropic の原則「シンプルに保つ、段階的に複雑化する、必要な時だけ複雑さを追加する」に従い、最小動作版 → 段階的拡張の順で実装する。

### 13.2 Stage 1:最小動作版(MVP)

目標:1 キャラクターを完全自動で生成できる最小構成

範囲:
- Creative Director の内部ループ(簡略版、反復 2 回まで)
- Master Orchestrator(単純な順次実行)
- Phase A-1 Orchestrator + 8 Workers
- Phase A-2 Orchestrator + 主要 Workers(一部統合、分割は後回し)
- Phase A-3 Orchestrator + 各 Writer + BiasAuditor
- Phase D Orchestrator + 主要 Workers
- SchemaValidator のみ(他の Evaluator は skip)
- 完全自動モードのみ(共同編集モードは skip)
- 最小限の HTML UI(進捗表示とダウンロードのみ)

所要時間の見積もり:1〜2 日

### 13.3 Stage 2:品質向上

Stage 1 の上に追加:
- Phase A-2 の Worker 分割完成(14 Worker すべて)
- ConsistencyChecker
- InterestingnessEvaluator
- Evaluator-Optimizer ループの完全実装(最大 4 回反復)
- テーマ指定モード
- 思考ログのストリーミング表示

所要時間の見積もり:1 日

### 13.4 Stage 3:ユーザー体験

Stage 2 の上に追加:
- 共同編集モード
- チャット形式の自然言語指示
- セクション単位の再生成
- 直接編集機能
- 過去の脚本パッケージ履歴
- 差分表示

所要時間の見積もり:1 日

### 13.5 Stage 4:説明資料と提出準備

- 提出用の説明資料作成(3〜10 ページ)
- 複数キャラクターの生成例を用意(気質パラメータの比較実験)
- 実際に生成された日記サンプルの収集(日記生成本体と接続)
- デプロイ
- Google フォーム提出

所要時間の見積もり:1 日

### 13.6 実装の優先順位

絶対に実装すべき:
1. Creative Director(Opus)
2. Master Orchestrator(Opus)
3. Phase A-1 の全 Worker
4. Phase A-2 の主要 Worker(気質と性格の最低限)
5. Phase A-3 の BiasAuditor を含む全 Writer
6. Phase D の主要 Worker
7. SchemaValidator
8. 完全自動モード
9. 最小 UI

時間があれば実装:
- ConsistencyChecker
- InterestingnessEvaluator
- 共同編集モード
- 差分表示

時間がなければ切る:
- 複雑な UI 編集機能
- 過去履歴管理
- 複数キャラクターの同時生成

---

## 14. コスト見積もり

### 14.1 LLM 呼び出し数の概算(1 キャラクター生成あたり)

| Tier | エージェント | モデル | 呼び出し数 | トークン数(概算) |
|---|---|---|---|---|
| -1 | Creative Director | Opus 4.6 | 10〜30 | in: 30k, out: 10k |
| 0 | Master Orchestrator | Opus 4.6 | 5〜15 | in: 20k, out: 5k |
| 1 | Phase A-1/A-2 Orchestrators | Sonnet 4.6 | 2〜4 | in: 8k, out: 2k |
| 1 | Phase A-3/D Orchestrators | **Opus 4.6** | 2〜4 | in: 15k, out: 5k |
| 2 | Workers (Phase A-1) | Gemma 4 | 8 | in: 5k, out: 2k |
| 2 | Workers (Phase A-2) | Gemma 4 | 14 | in: 8k, out: 4k |
| 2 | Writers (Phase A-3) | Gemma 4 | 6〜10 | in: 6k, out: 3k |
| 2 | WorldContext / SupportingChars (Phase D) | Sonnet/Gemma | 2 | in: 3k, out: 2k |
| 2 | NarrativeArcDesigner (Phase D) | **Opus 4.6** | 1〜2 | in: 10k, out: 3k |
| 2 | ConflictIntensityDesigner (Phase D) | Sonnet 4.6 | 1 | in: 5k, out: 1k |
| 2 | **WeeklyEventWriter (Phase D)** | **Opus 4.6** | 1〜3 | in: 20k, out: 15k |
| 3 | ConsistencyChecker / InterestingnessEvaluator | Sonnet 4.6 | 8〜15 | in: 18k, out: 4k |
| 3 | NarrativeConnectionAuditor (Phase D) | **Opus 4.6** | 1〜3 | in: 15k, out: 2k |
| 3 | EventMetadataAuditor (Phase D) | Sonnet 4.6 | 1〜2 | in: 15k, out: 1k |
| 3 | DistributionValidator (Phase D) | Python | 1〜3 | - |

### 14.2 コスト概算(1 キャラクターあたり)

料金は 2026 年 4 月時点の推定値。正確な値は要確認。

| モデル | Input / 1M tokens | Output / 1M tokens |
|---|---|---|
| Claude Opus 4.6 | ~$15 | ~$75 |
| Claude Sonnet 4.6 | ~$3 | ~$15 |
| Gemma 4 (Google AI Studio) | 無料枠(制限あり) | 無料枠 |

**v1 からの変化:** v2 では Phase D Orchestrator、NarrativeArcDesigner、WeeklyEventWriter、NarrativeConnectionAuditor が Opus にアップグレードされたため、Opus トークン消費が増える。特に WeeklyEventWriter は in 20k / out 15k と単発で大きい。

1 キャラクター生成の概算(v2):
- Opus 呼び出し:in 95k + out 40k → $1.43 + $3.00 = **$4.43**
- Sonnet 呼び出し:in 49k + out 14k → $0.15 + $0.21 = **$0.36**
- Gemma 4:無料枠内(50 call 程度は余裕)→ **$0.00**
- 合計:**約 $4.79 / キャラクター(キャッシュなし)**

Prompt Caching 適用時は §14.6 で詳述するが、約 35〜40% のコスト削減が見込めるため実効コストは **$2.9〜3.1 / キャラクター** 程度。v1(実効約 $1.02)に比べて約 3 倍になるが、これは Phase D が「7 日間を俯瞰した一括生成」という本質的に高コストなタスクに変わったための必然的な増加である。

### 14.3 コスト削減策

開発中:
- Creative Director の反復を最大 2 回に制限
- Phase Orchestrators を Gemma 4 31B に差し替え(テスト時)
- キャッシュ機能で同じプロンプトを再利用しない

本番:
- Prompt caching(Claude の機能、自動適用)
- 並列化で時間短縮
- Evaluator の閾値を調整して再生成回数を減らす

### 14.4 無料枠の活用

- Google AI Studio:Gemma 4 は無料枠が広い。Worker 層はここで十分回せる。
- Anthropic API:初回クレジット $5 を利用可能な場合がある。
- 開発中はコストを意識して、本番は必要な部分だけ Opus/Sonnet を使う。

### 14.5 Prompt Caching(KV キャッシュ)の活用戦略

§2.10 で述べた通り、本アプリは多階層のエージェント構成であり、何も工夫しないとトークン消費が爆発する。Anthropic API が提供する Prompt Caching は、この問題に対する第一の解決策である。

#### 14.5.1 Prompt Caching の料金構造

Anthropic の公式ドキュメントによれば、Prompt Caching の料金構造は以下の通り(2026 年 4 月時点、一次情報より):

| 項目 | 倍率 | 備考 |
|---|---|---|
| Cache write(5 分 TTL) | 1.25 × base input | 初回書き込み時に +25% |
| Cache write(1 時間 TTL) | 2.0 × base input | 初回書き込み時に +100% |
| Cache read(5 分/1 時間共通) | 0.1 × base input | キャッシュヒット時は base input の 10% |
| Output tokens | 1.0 × base output | 出力料金は変わらない |

重要な損益分岐:
- 5 分 TTL:同じプロンプトが **2 回以上** 呼ばれればコスト削減効果が出る(1.25 + 0.1 < 2.0)
- 1 時間 TTL:同じプロンプトが **3 回以上** 呼ばれればコスト削減効果が出る

本アプリの Creative Director 内部ループは最大 4 回、Master Orchestrator は全 Phase にわたって継続呼び出しされるため、5 分 TTL で十分に損益分岐を超える。

レイテンシ削減効果も大きい。Anthropic の報告では 100K トークンの例で 11.5 秒から 2.4 秒への短縮、つまり最大 85% の削減が観測されている。

#### 14.5.2 本アプリでのキャッシュ対象

以下の 5 つのレイヤーを Prompt Caching の対象とする。

**(1) Creative Director のシステムプロンプト**
  - 脚本論・心理学知識・設計思想・評価基準を含む大きなシステムプロンプト(約 5,000〜10,000 トークン)
  - 内部ループで最大 4 回呼ぶため、2 回目以降は cache read(10%)で済む
  - 5 分 TTL で十分(内部ループは数分で完結)

**(2) Master Orchestrator のシステムプロンプト**
  - Phase 管理ロジック、ユーザー対話ルール、ツール定義(約 3,000〜5,000 トークン)
  - 全 Phase にわたって継続呼び出しされる
  - 1 時間 TTL を推奨(セッション全体をカバー)

**(3) Phase Orchestrator のシステムプロンプト + 参考資料**
  - 各 Phase Orchestrator が参照する v10 仕様書の該当節(約 2,000〜4,000 トークン)
  - その Phase の Worker を起動するたびに参照される
  - 5 分 TTL で十分

**(4) 中間成果物(Phase 間の引き継ぎデータ)**
  - Phase A-1 完了後、macro_profile は Phase A-2/A-3/D の全 Worker が参照する
  - Phase A-2 完了後、micro_parameters は Phase A-3/D が参照する
  - これらの中間成果物は各 Phase 内で多数の Worker に渡されるため、キャッシュ対象にする
  - 5 分 TTL、場合によっては 1 時間 TTL

**(5) concept_package**
  - Creative Director の最終出力で、全 Phase で参照される
  - 1 時間 TTL を推奨(セッション全体で参照)

#### 14.5.3 プロンプト構造の設計原則

Prompt Caching は「cache_control を指定したブロックまでのプレフィックス全体」をキャッシュするため、**静的コンテンツを先頭、動的コンテンツを末尾** に配置する必要がある。一次情報より、Anthropic のリクエスト処理順は `tools → system → messages` であるため、以下の順序で構築する:

```
1. tools(ツール定義、ほぼ静的) ← キャッシュ対象
2. system(システムプロンプト、静的) ← キャッシュ対象
3. messages(会話履歴、末尾だけ動的)
   - 過去のターン(静的) ← キャッシュ対象
   - 最新のユーザー入力(動的) ← キャッシュしない
```

#### 14.5.4 実装例

```python
from anthropic import Anthropic

client = Anthropic()

# Creative Director の呼び出し例
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4000,
    system=[
        {
            "type": "text",
            "text": CREATIVE_DIRECTOR_SYSTEM_PROMPT,  # 数千字の固定部分
            "cache_control": {"type": "ephemeral"}    # 5 分 TTL キャッシュ
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": REFERENCE_MATERIALS,  # 脚本論参考資料(ほぼ静的)
                    "cache_control": {"type": "ephemeral"}  # 5 分 TTL キャッシュ
                },
                {
                    "type": "text",
                    "text": user_theme_input  # ユーザーの入力(動的)
                    # cache_control を指定しない
                }
            ]
        }
    ]
)

# レスポンスに含まれるキャッシュ統計
print(message.usage)
# {
#   "input_tokens": 50,                      # 非キャッシュ入力
#   "cache_creation_input_tokens": 0,        # 2 回目以降は 0
#   "cache_read_input_tokens": 7500,         # キャッシュから読んだ分
#   "output_tokens": 1200
# }
```

**Phase 間の中間成果物を渡すパターン:**

```python
# Phase A-2 Worker を呼ぶ例(macro_profile をキャッシュ)
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    system=[
        {
            "type": "text",
            "text": TEMPERAMENT_WORKER_A1_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"concept_package:\n{json.dumps(concept_package)}\n\nmacro_profile:\n{json.dumps(macro_profile)}",
                    "cache_control": {"type": "ephemeral"}  # A-2 の全 Worker で再利用
                },
                {
                    "type": "text",
                    "text": "気質パラメータ A1 情動反応系(9 個)を生成してください。"
                }
            ]
        }
    ]
)
```

この設計により、Phase A-2 内で 14 個の Worker を並列実行しても、concept_package と macro_profile は 1 回だけキャッシュ書き込みされ、残り 13 個の Worker では cache read(10%)で済む。

#### 14.5.5 Claude Agent SDK でのキャッシュ

Claude Agent SDK は内部で Prompt Caching を自動適用する機能を持つが、細かい制御が必要な場合は Anthropic API を直接呼ぶ Custom Tool を実装して、その中で明示的に cache_control を指定する。本アプリでは以下の方針とする:

- **Subagent レベルでは自動キャッシュに任せる**(Claude Agent SDK の prompt caching 機能)
- **Custom Tool 内での明示的 API 呼び出しでは、cache_control を手動指定する**
- **Gemma 4 呼び出しは別 API(Google AI Studio)のため、Anthropic の Prompt Caching は適用されない**(Gemma 4 側の context caching を別途検討)

#### 14.5.6 コンテキスト最小化の原則

Prompt Caching と並行して、各 Worker に渡すコンテキストを最小化する。原則:

- **Worker は自分の生成に必要な情報だけを受け取る**
  例:BasicInfoWorker は concept_package だけ受け取る(macro_profile は空なので渡す必要なし)
  例:FamilyWorker は concept_package + basic_info だけ受け取る(dream_timeline や voice_fingerprint は不要)

- **Phase Orchestrator は Worker に渡す前にコンテキストをフィルタリングする**
  Worker ごとに必要なフィールドだけを抽出した軽量 dict を作り、それを渡す

- **出力は構造化 JSON に限定する**
  Gemma 4 の native JSON output 機能、Claude の tool use 機能で、無駄な前置きや説明文を排除する

### 14.6 プロファイルごとのコスト比較

§8.9 で定義した 4 つのプロファイルについて、Prompt Caching を適用した上での 1 キャラクター生成のコストを概算する。

#### 14.6.1 概算条件

- Claude Opus 4.6:input $15/M、output $75/M(推定)
- Claude Sonnet 4.6:input $3/M、output $15/M(推定)
- Gemma 4 26B MoE:無料枠内と仮定($0)
- Prompt Caching 適用時:cache write は base の 1.25 倍、cache read は base の 0.1 倍
- キャッシュヒット率:Creative Director 内部ループは約 75%、Master Orchestrator は約 60%、Phase Orchestrator は約 50% と仮定

#### 14.6.2 プロファイル別コスト概算

| プロファイル | LLM 呼び出し総数 | Opus 呼び出し数 | Sonnet 呼び出し数 | Gemma 呼び出し数 | 推定コスト(キャッシュなし) | 推定コスト(キャッシュあり) | 所要時間 |
|---|---|---|---|---|---|---|---|
| **High Quality** | 70〜100 | 30〜40 | 15〜25 | 25〜35 | $3.50〜5.00 | **$2.10〜3.00** | 10〜15 分 |
| **Standard** | 40〜60 | 15〜20 | 8〜12 | 17〜28 | $1.80〜2.50 | **$1.10〜1.60** | 5〜8 分 |
| **Fast** | 25〜35 | 8〜12 | 3〜5 | 14〜18 | $0.80〜1.20 | **$0.50〜0.80** | 2〜4 分 |
| **Draft** | 18〜25 | 5〜8 | 1〜3 | 12〜14 | $0.50〜0.80 | **$0.30〜0.50** | 1〜2 分 |

Prompt Caching の適用で、全プロファイルで **約 35〜40% のコスト削減** が見込める。これは Creative Director の大きなシステムプロンプトと Phase 間の中間成果物が繰り返し参照されるためである。

#### 14.6.3 プロファイル別の節約の内訳(Standard プロファイル)

Standard プロファイル(キャッシュあり)で 1 キャラクター生成した場合の内訳例:

| 項目 | トークン(input) | 方式 | 単価 | コスト |
|---|---|---|---|---|
| Creative Director システムプロンプト(初回書き込み) | 8,000 | cache write 5m | $15 × 1.25 = $18.75 | $0.150 |
| Creative Director システムプロンプト(2〜3 回目読み込み) | 8,000 × 2 | cache read | $15 × 0.1 = $1.5 | $0.024 |
| Creative Director の動的入力 | 2,000 × 3 | 通常 input | $15 | $0.090 |
| Master Orchestrator システムプロンプト(初回) | 5,000 | cache write 1h | $15 × 2.0 = $30 | $0.150 |
| Master Orchestrator システムプロンプト(N 回目読み込み) | 5,000 × 10 | cache read | $1.5 | $0.075 |
| Phase A-1 Orchestrator 呼び出し | 合計 8k × 5 | 半分キャッシュ | 実効 $0.6 | $0.024 |
| Phase A-2 Orchestrator 呼び出し(14 Worker のキャッシュ共有) | 合計 50k | macro_profile キャッシュ | 実効 $0.6 | $0.030 |
| Phase A-3 Orchestrator + BiasAuditor | 合計 30k | | | $0.060 |
| Phase D Orchestrator | 合計 25k | | | $0.040 |
| Output tokens(全モデル合計) | 25,000 | 出力 | $15(Sonnet 平均) | $0.375 |
| Gemma 4(Workers、無料枠) | - | - | - | $0.000 |
| **合計(Standard + cache)** | | | | **約 $1.02** |

上表はあくまで目安。実際のキャッシュヒット率、モデル呼び出しの分配、Evaluator の反復回数によって変動する。

#### 14.6.4 開発中のコスト最適化

開発フェーズではさらなるコスト削減が必要。以下の追加策を取る:

- **全プロファイルを Draft に設定して動作確認**
- **Creative Director の反復を強制的に 1 回に制限**
- **Phase Orchestrators を Gemma 4 31B に差し替え**(テスト時のみ)
- **Gemma 4 の無料枠を最大限活用**(Worker 層はすべて Gemma)
- **同じキャラクターを繰り返し生成しない**(キャッシュの節約より無駄な呼び出しの削減)

本番提出時のみ High Quality プロファイルで最終生成を行う。

#### 14.6.5 コスト可視化 UI

アプリの UI には、現在のセッションのコスト累積を常時表示する:

```
今日の使用状況
  LLM 呼び出し: 47 回
  Opus トークン: 45,231 (cache write: 8,000 / read: 24,500 / fresh: 12,731)
  Sonnet トークン: 22,450 (cache write: 5,000 / read: 15,300 / fresh: 2,150)
  Gemma トークン: 31,200 (無料枠内)
  推定コスト: $1.02
```

これにより、ユーザーはプロファイル切り替えの判断材料を持てる。

---

## 15. 未決事項

### 15.1 設計レベル

- **Creative Director の反復上限 4 回は適切か**:実験で詰める必要がある
- **Worker 分割の粒度**:Phase A-2 の 14 分割は多すぎないか、統合すべきか
- **Evaluator の閾値**:InterestingnessEvaluator の pass 閾値をどう決めるか
- **WeeklyEventWriter の 1 プロンプト生成 vs 分割生成のトレードオフ**:28〜42 件を 1 プロンプトで生成すると出力が肥大化する懸念。Day 1〜3 / Day 4〜7 に分割した場合の伏線整合性の担保方法
- **NarrativeConnectionAuditor の pass 閾値**:「meaning_to_character の具体性」を定量化する基準(v10 §7.2 でも未決扱い)
- **予想外度分布制約の最適値**:「low 半分以上」「high は Day 5 以外で最大 1 件」は仮置き、実験で詰める必要

### 15.2 実装レベル

- **Claude Agent SDK のブラウザ透過**:WebSocket でどのようにエージェントの思考をストリーミングするか、SDK の API を詳細確認する
- **Gemma 4 の呼び出しレートリミット**:Google AI Studio の無料枠制限を超えないようにする工夫
- **並列実行時のエラーハンドリング**:一つの Worker が失敗したときに他の Worker をどう扱うか
- **セッション永続化**:WebSocket が切断されたときの再接続と状態復元
- **WeeklyEventWriter の部分再生成プロトコル**:ある特定のイベントだけ書き換える指示を Opus に出す際の、既存イベントをコンテキストとして渡すプロンプト設計

### 15.3 本命キャラクター

v10 仕様書 §7.1 で未解決として残っている「キャラが AI/人間どちらとして提示するか」「本命のキャラクター・世界観」は、本アプリの動作デモ時に決定する。候補:

- **歴史人物 × 現代**(信長タイムスリップなど):設定の面白さで開始から強い掴み
- **架空の現代人**:リアリティで勝負、サンプルとの差別化が難しい
- **SF 系**(近未来研究者、宇宙飛行士):非日常とリアリティの両立
- **異世界 × 日常**:サンプルの魔法使いルナに近く、かぶりリスクあり

推奨:**歴史人物 × 現代**。理由:
- マクロプロフィールに史実情報が使える
- 概念的な「面白さの源泉」が初期段階で強い
- 52 パラメータを史実人物に適用するという実験的価値が訴求できる
- サンプルと明確に差別化できる

### 15.4 評価実験

提出用の説明資料では、本アプリの価値を実証するために以下の比較実験を含めたい:

- **同じ concept_package で Cloninger 気質パラメータだけを変えた 3 体のキャラクター**を生成し、Phase A-3 の自伝的エピソードと Phase D の weekly_events_store がどう変化するかを比較
- 特に Day 5 山場のイベント内容と「なぜこのキャラに意味を持つか」のメタデータが、気質の違いによってどう変化するかを可視化する
- これにより「気質層 → 自伝的エピソード → 物語全体への影響」の経路が実証できる

### 15.5 日記生成本体との接続

本アプリの出力(脚本パッケージ)は、日記生成本体への入力となる。接続の具体的な API 契約は、日記生成本体の実装が進んでから最終化する。現時点では JSON ファイルとしてディスク経由で渡す前提。

日記生成本体は v10 §4 に定義された日次ループ(Perceiver、Impulsive Agent、Reflective system、行動決定エージェント、情景描写・後日譚生成エージェント、価値観違反チェック、内省、日記生成、key memory 抽出、記憶圧縮、翌日予定追加エージェント)を実装する。本アプリから渡されるのは:

- `concept_package`(参照用)
- `macro_profile`(常時プロンプト同梱、動的活性化対象外)
- `micro_parameters`(動的活性化の読み取り元、主人公AIからは隠蔽される部分を含む)
- `autobiographical_episodes`(全エージェントのプロンプトに全文ベタ貼り)
- `weekly_events_store`(日次ループが §4.2 で本日分を読み込む)

---

## 付録 A:v10 仕様書からの参照マップ

本仕様書の各セクションは、v10 仕様書の以下のセクションに対応する:

| 本仕様書 | v10 仕様書 |
|---|---|
| Tier -1 Creative Director | (新規、v10 には直接の対応なし) |
| Tier 0 Master Orchestrator | (新規) |
| Phase A-1 | §2.1.1 Phase A-1:マクロプロフィール生成 |
| Phase A-2 | §2.1.2 Phase A-2:ミクロパラメータ生成、§3.3 気質・性格層、§3.4 規範層 |
| Phase A-3 | §2.1.3 Phase A-3:自伝的エピソード生成 |
| Phase D | §2.5 Phase D:脚本AI による 7 日分イベント列の一括事前生成 |
| 規範層(ValuesWorker) | §3.4 規範層(可変サブモジュールを持たない原則) |
| 既知/未知 × 予想外度 2 軸メタデータ | §0.2 既知/未知の厳密分離、§2.5 Phase D |
| 「なぜこのキャラに意味を持つか」メタデータ | §2.5 Phase D プロンプト構造 |
| 葛藤強度アーク | §2.5 葛藤強度の 7 日間アーク |
| Day 5 山場への伏線設計 | §2.5 物語連続性の制約 |
| Redemption bias 対策 | §2.1.3 制約 |
| protagonist_plan イベント(Phase D では生成しない) | §4.9.4 翌日予定追加エージェント |
| 主人公AI の内部定義(日記生成本体側の構造) | §0.4(参考情報、本アプリの範囲外) |

## 付録 B:参考文献

本仕様書は以下の一次情報に基づく:

1. Anthropic (2025). "Building Effective Agents" https://www.anthropic.com/research/building-effective-agents
2. Anthropic. "Claude Agent SDK Overview" https://platform.claude.com/docs/en/agent-sdk/overview
3. Google DeepMind (2026). "Gemma 4" https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
4. サードインテリジェンス Bコース課題資料(2026)
5. AssignB_sample.ipynb(運営配布)
6. specification_v10.md(AIキャラクター日記システム v10)

心理学・脚本論の参考文献は v10 仕様書 §8 の理論的根拠サマリを参照。

---

## 付録 C:v1 → v2 の主要変更履歴

本仕様書 v2 に至るまでの主要な設計変更を、時系列で簡潔に記録する。本文は常に現状仕様のみを記述する方針のため、過去バージョンの撤回・再設計の経緯を追うための参照箇所として位置付ける。

### C.1 v1 → v2 主要変更(本版)

**前提仕様書の変更:**

- **前提ドキュメントを `specification_v6.md` から `specification_v10.md` に切り替え** ── v6 → v7 → v8 → v9 → v10 の累積変更が大規模であったため、v2 ではドキュメント全体を v10 に整合させる形で再構築した

**用語統一:**

- **「神AI / godAI」呼称の廃止、「脚本AI」への統一** ── v10 §A.4 に従い、Phase A-2 ミクロパラメータ生成、Phase A-3 自伝的エピソード生成、Phase D 7 日分イベント列一括事前生成のすべてを「脚本AI」として扱う

**Phase D の責務の完全置換:**

- **Phase D の役割を「世界モデル構築」から「脚本AI による 7 日分イベント列の一括事前生成」に完全置換** ── これは v1 → v2 の最大の変更点
- **Phase D 出力の `world_model` を廃止し、`weekly_events_store` に置換**
- **Phase D Orchestrator のモデルを Sonnet 4.6 から Opus 4.6 にアップグレード** ── 7 日間の物語アークを俯瞰してイベント列を一括設計する能力が要求されるため
- **Phase D Worker を再編成** ── 旧 WorldSettingWorker / SchedulePlanner / ConflictInducingEventGenerator を廃止し、新 WorldContextWorker / SupportingCharactersWorker / NarrativeArcDesigner / ConflictIntensityDesigner / WeeklyEventWriter を配置

**2 軸メタデータの導入:**

- **`potential_layer` (L1 / L2 / L3) を廃止、2 軸メタデータに置換** ── `known_to_protagonist` (true/false) + `source` (routine / prior_appointment / protagonist_plan) + `expectedness` (low / medium / high)
- **`source: "protagonist_plan"` は Phase D では 1 件も生成しない方針を確立** ── これは日次ループの翌日予定追加エージェント(v10 §4.9.4)が動的挿入する唯一の経路のため
- **「なぜこのキャラに意味を持つか」(`meaning_to_character`)を各イベントの必須メタデータ化**
- **`narrative_arc_role`(day5_foreshadowing / previous_day_callback / daily_rhythm / standalone_ripple)を各イベントに必須化**

**Day 5 山場と伏線の明示的設計:**

- **NarrativeArcDesigner に `day5_climax_design` と `foreshadowing_plan` の出力を義務付け**
- **WeeklyEventWriter は NarrativeArcDesigner の出力に従って伏線を Day 1〜4 に配置する責務を持つ**
- **NarrativeConnectionAuditor を新設**し、伏線存在チェックと連続性検証を行う

**Phase A-2 からの `behavior_guidelines` の完全削除:**

- **v10 §3.4 の「規範層に可変サブモジュール(価値観ごとの具体例明示リスト、行動方針の明示リスト等)を一切持たない」方針に従い、`micro_parameters.behavior_guidelines` フィールドを schema から完全削除**

**Phase D 専用 Evaluator の新設:**

- **EventMetadataAuditor** ── メタデータ完全性検証(Sonnet 4.6)
- **DistributionValidator** ── 予想外度分布制約検証(Python ルールベース、全プロファイルで ON)
- **NarrativeConnectionAuditor** ── 物語連続性・伏線・meaning_to_character の質検証(Opus 4.6)

**プロファイル設計の更新:**

- **EvaluationProfile dataclass に Phase D 専用 Evaluator の 3 フィールドを追加**
- **DistributionValidator は全プロファイルで ON**(ルールベースのためコストゼロ、分布違反の機械的担保)
- **EventMetadataAuditor は Draft 以外で ON**
- **NarrativeConnectionAuditor は High Quality / Standard でのみ ON**(Opus コストのため)

**コスト見積もりの更新:**

- **v1 実効 $1.02 → v2 実効 $2.9〜3.1**(約 3 倍)
- Phase D が Opus 中心になったことによる必然的増加
- WeeklyEventWriter(in 20k / out 15k × 1〜3 回)が最大のコスト要因

**スコープの明示化:**

- **Phase B(エコーチェンバー)と Phase C(擬似経験)は v10 でも本実装保留とされていることを明記、本アプリでも実装しない**

**参照の全面更新:**

- 全箇所の `v6` → `v10` 参照置換
- 付録 A の参照マップを v10 の § 番号に合わせて再構築
- 付録 B の参考文献リストを更新

---

**文書終端**

この設計書は生きた文書であり、実装の進行に合わせて更新される。最新版は常に `./specs/script_ai_app_specification_v2.md` に置く。
