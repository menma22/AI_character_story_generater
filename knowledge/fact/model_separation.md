# ClaudeとGeminiのロジック分離に関する実装事実

## 概要
システム刷新により、Claude (Anthropic) と Gemini (Google) の実行プログラムが完全に分離された。これにより、モデル間の不干渉と、個別の最適化（Tool Calling等の仕様差異への対応）が可能になった。

## 実装詳細
1. **llm_api.pyの分離**
   - `call_llm_agentic`: Claude (Opus/Sonnet) 用。Anthropic SDKを使用し、同社独自のTool Calling形式に最適化されている。自動フォールバック機能は削除済み。
   - `call_llm_agentic_gemini`: Gemini 2.5 Pro用。Google AI SDK (Native Tool Calling) を直接使用する。

2. **EvaluationProfile (config.py) による制御**
   - `director_tier`: Tier -1 (Creative Director) が使用するモデルを指定 ("opus", "sonnet", "gemini")。
   - `worker_tier`: Tier 1-2 (各PhaseのWorker) および Daily Loop が使用するモデルを指定。

3. **オーケストレーターの分岐ロジック**
   - `CreativeDirector.run` および `DailyLoopOrchestrator._generate_diary_agentic` は、設定されたTierに応じて `call_llm_agentic` または `call_llm_agentic_gemini` を呼び分ける。

4. **環境の安定性**
   - ポート8000の競合を避けるため、既存プロセスのクリーンアップ手順が導入されている。
