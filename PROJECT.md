# AI繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧ｹ繝医・繝ｪ繝ｼ逕滓・繧ｷ繧ｹ繝・Β

> specification_v10.md 縺ｨ script_ai_app_specification_v2.md 縺ｫ蝓ｺ縺･縺上∝ｿ・炊蟄ｦ逧・ｺｺ譬ｼ繝｢繝・Ν繧呈政霈峨＠縺溘く繝｣繝ｩ繧ｯ繧ｿ繝ｼAI譌･險倡函謌舌す繧ｹ繝・Β

---

## 繝代・繝・: 繧｢繝励Μ繧ｷ繧ｹ繝・Β讎りｦ・

![繧ｷ繧ｹ繝・Β繧｢繝ｼ繧ｭ繝・け繝√Ε蝗ｳ - 逕滓・騾ｲ謐礼ｮ｡逅・ｼ育ｮ｡逅・・繝・け繧ｹ・峨→螟壼ｱ､繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝域ｧ矩](file:///C:/Users/mahim/.gemini/antigravity/brain/f368796d-9d68-4be2-8d61-ffe79fea65d0/app_architecture_diagram_1776697107291.png)

### 繝・ぅ繝ｬ繧ｯ繝医Μ繝ｻ繝輔ぃ繧､繝ｫ讒区・

```
AI_character_story_generater/
笏懌楳笏 backend/
笏・  笏懌楳笏 main.py                                # FastAPI 繧ｨ繝ｳ繝医Μ繝昴う繝ｳ繝・(WebSocket + REST API) 窶ｻ2026-04-22 02:26 蜀崎ｵｷ蜍募ｮ御ｺ・(PID: 27072)
笏・  笏懌楳笏 regeneration.py                        # 繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝亥句挨蜀咲函謌舌Δ繧ｸ繝･繝ｼ繝ｫ (萓晏ｭ倥・繝・・ + 蜀咲函謌舌さ繧｢)
笏・  笏懌楳笏 config.py                              # 險ｭ螳夂ｮ｡逅・(API繧ｭ繝ｼ, 4谿ｵ髫弱・繝ｭ繝輔ぃ繧､繝ｫ, 繝｢繝・Ν螳夂ｾｩ)
笏・  笏懌楳笏 agents/
笏・  笏・  笏懌楳笏 creative_director/
笏・  笏・  笏・  笏披楳笏 director.py                    # Tier -1: Creative Director (5繝輔ぉ繝ｼ繧ｺ, 2螻､閾ｪ蟾ｱ謇ｹ蛻､, Web讀懃ｴ｢蠢・・ file_read, 讒区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹ豕ｨ蜈･+[G]謨ｴ蜷域ｧ繝√ぉ繝・け)
笏・  笏・  笏懌楳笏 master_orchestrator/
笏・  笏・  笏・  笏披楳笏 orchestrator.py                # Tier 0: Phase A-1竊但-2竊但-3竊奪 鬆・ｬ｡蛻ｶ蠕｡ + Evaluator邨ｱ蜷・+ concept_review荳譎ょ●豁｢ + cancel()荳ｭ譁ｭ讖溯・
笏・  笏・  笏懌楳笏 phase_a1/
笏・  笏・  笏・  笏披楳笏 orchestrator.py                # Phase A-1: 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ (8 Workers, 荳ｦ蛻怜喧)
笏・  笏・  笏懌楳笏 phase_a2/
笏・  笏・  笏・  笏披楳笏 orchestrator.py                # Phase A-2: 繝溘け繝ｭ繝代Λ繝｡繝ｼ繧ｿ 52蛟・+ 隕冗ｯ・ｱ､ (15 Workers, v2 ﾂｧ6.4.2貅匁侠)
笏・  笏・  笏懌楳笏 phase_a3/
笏・  笏・  笏・  笏披楳笏 orchestrator.py                # Phase A-3: 閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝・(繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け, 2螻､閾ｪ蟾ｱ謇ｹ蛻､)
笏・  笏・  笏懌楳笏 phase_d/
笏・  笏・  笏・  笏懌楳笏 orchestrator.py                # Phase D: 7譌･髢薙う繝吶Φ繝亥・ (Step5繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け, 2螻､閾ｪ蟾ｱ謇ｹ蛻､)
笏・  笏・  笏・  笏披楳笏 capabilities_agent.py          # CharacterCapabilitiesAgent (Web讀懃ｴ｢2蝗樔ｻ･荳・謇ｹ隧・蜀・怐, 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け蛹・
笏・  笏・  笏懌楳笏 daily_loop/
笏・  笏・  笏・  笏懌楳笏 orchestrator.py                # Day 1-7 譌･谺｡繝ｫ繝ｼ繝・(RIM + 諢滓ュ蠑ｷ蠎ｦ蛻､螳・+ 蜀・怐 + 譌･險・ 窶ｻcancel()荳ｭ譁ｭ讖溯・繝ｻ謖・､ｺ蜿肴丐蟇ｾ蠢懈ｸ・
笏・  笏・  笏・  笏懌楳笏 activation.py                  # 繝代Λ繝｡繝ｼ繧ｿ蜍慕噪豢ｻ諤ｧ蛹・(5-10蛟矩∈謚・ v10 ﾂｧ3.5)
笏・  笏・  笏・  笏懌楳笏 verification.py                # 陬乗婿蜃ｺ蜉帶､懆ｨｼ (#1-#52貍乗ｴｩ繝√ぉ繝・け, v10 ﾂｧ4.6b)
笏・  笏・  笏・  笏懌楳笏 checkers.py                    # 4縺､縺ｮ蛟句挨繝√ぉ繝・けAI (Profile/Temperament/Personality/Values)
笏・  笏・  笏・  笏懌楳笏 diary_critic.py                # 譌･險牢elf-Critic (LLM繝吶・繧ｹ縺ｮ繧ｷ繝ｳ繝励Ν縺ｪ蜩∬ｳｪ繝√ぉ繝・け)
笏・  笏・  笏・  笏懌楳笏 linguistic_validator.py        # 險隱櫁｡ｨ迴ｾ繝舌Μ繝・・繧ｿ繝ｼ (LinguisticExpression蜈ｨ繝輔ぅ繝ｼ繝ｫ繝画､懆ｨｼ, Stage 22)
笏・  笏・  笏・  笏懌楳笏 third_party_reviewer.py        # 隨ｬ荳芽・ｦ也せ縺ｮ譌･險俶､懆ｨｼAI (隱ｭ閠・ｽ馴ｨ灘刀雉ｪ繝√ぉ繝・け)
笏・  笏・  笏・  笏披楳笏 next_day_planning.py           # 鄙梧律莠亥ｮ夊ｿｽ蜉 (Stage1+2, protagonist_plan)
笏・  笏・  笏懌楳笏 context_descriptions.py            # 繧ｳ繝ｳ繝・く繧ｹ繝郁ｪｬ譏惹ｻ倅ｸ弱・繝ｫ繝代・ (wrap_context, 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・騾・
笏・  笏・  笏披楳笏 evaluators/
笏・  笏・      笏披楳笏 pipeline.py                    # Evaluator鄒､7遞ｮ (SchemaValidator蟶ｸ譎０N, LLM5遞ｮ)
笏・  笏懌楳笏 models/
笏・  笏・  笏懌楳笏 character.py                       # Pydantic v2 繝・・繧ｿ繝｢繝・Ν (v2 ﾂｧ6.3.4貅匁侠繧ｹ繧ｭ繝ｼ繝・+ StoryCompositionPreferences)
笏・  笏・  笏披楳笏 memory.py                          # 險俶・繝ｻ繝繝ｼ繝峨・繧､繝吶Φ繝亥・逅・Δ繝・Ν
笏・  笏懌楳笏 tools/
笏・  笏・  笏懌楳笏 llm_api.py                         # LLM API邨ｱ蜷医Λ繝・ヱ繝ｼ (Anthropic + Google AI Studio + 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ)
笏・  笏・  笏披楳笏 agent_utils.py                     # Worker讀懆ｨｼ + Markdown繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繝代・繧ｵ繝ｼ
笏・  笏懌楳笏 websocket/
笏・  笏・  笏披楳笏 handler.py                         # WebSocket謗･邯夂ｮ｡逅・+ 諤晁・せ繝医Μ繝ｼ繝溘Φ繧ｰ
笏・  笏懌楳笏 reference/                             # 蠢・炊蟄ｦ逅・ｫ門盾閠・ｳ・侭 (Creative Director縺ｮfile_read繝・・繝ｫ蟇ｾ雎｡)
笏・  笏披楳笏 storage/character_packages/            # 逕滓・貂医∩繝代ャ繧ｱ繝ｼ繧ｸ菫晏ｭ伜・・・繧ｭ繝｣繝ｩ=1繝・ぅ繝ｬ繧ｯ繝医Μ・・
笏・      笏披楳笏 {繧ｭ繝｣繝ｩ蜷閤/
笏・          笏懌楳笏 package.json                   # 譛邨ゅく繝｣繝ｩ繧ｯ繧ｿ繝ｼ繝代ャ繧ｱ繝ｼ繧ｸ
笏・          笏懌楳笏 checkpoint.json                # 荳ｭ譁ｭ蜀埼幕逕ｨ繝√ぉ繝・け繝昴う繝ｳ繝・
笏・          笏懌楳笏 00_profile.md                  # 莠ｺ髢灘庄隱ｭ繝励Ο繝輔ぃ繧､繝ｫ
笏・          笏懌楳笏 agent_logs.json/.md            # 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝域晁・Ο繧ｰ
笏・          笏懌楳笏 key_memories/day_NN.json       # key memory・・譌･髢薙ヵ繝ｫ菫晄戟・・
笏・          笏懌楳笏 short_term_memory/day_NN.json  # 遏ｭ譛溯ｨ俶・DB譌･蜊倅ｽ阪せ繝翫ャ繝励す繝ｧ繝・ヨ
笏・          笏懌楳笏 mood_states/day_NN.json        # 繝繝ｼ繝臥憾諷区律蜊倅ｽ阪せ繝翫ャ繝励す繝ｧ繝・ヨ
笏・          笏懌楳笏 daily_logs/
笏・          笏・  笏懌楳笏 Day_N.md                   # 蛹・峡逧МD繧｢繝ｼ繧ｫ繧､繝厄ｼ井ｺｺ髢鍋畑・・
笏・          笏・  笏披楳笏 day_NN/                    # 陦悟虚繝ｭ繧ｰ譌･蛻･繝輔か繝ｫ繝
笏・          笏懌楳笏 diaries/day_NN.md              # 譌･險俶悽譁・
笏・          笏披楳笏 sessions/                      # 蜀咲函謌舌・繝舌・繧ｸ繝ｧ繝ｳ邂｡逅・畑
笏・              笏披楳笏 {session_id}/              # 繧ｻ繝・す繝ｧ繝ｳ蛻･縺ｮ繝ｭ繧ｰ/譌･險倅ｸ蠑・
笏懌楳笏 frontend/
笏・  笏懌楳笏 index.html                             # 繝｡繧､繝ｳUI (API繧ｭ繝ｼ險ｭ螳夂判髱｢, 4逕ｻ髱｢讒区・, 讒区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹUI, 繧ｳ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ逕ｻ髱｢)
笏・  笏懌楳笏 css/style.css                          # 繝励Ξ繝溘い繝繝繝ｼ繧ｯ繝・・繝・(險ｭ螳壹Δ繝ｼ繝繝ｫ蟇ｾ蠢・
笏・  笏披楳笏 js/
笏・      笏懌楳笏 websocket.js                       # WebSocket謗･邯夂ｮ｡逅・(閾ｪ蜍募・謗･邯・
笏・      笏懌楳笏 renderer.js                        # 繝・・繧ｿ 竊・HTML 繝ｬ繝ｳ繝繝ｪ繝ｳ繧ｰ
笏・      笏懌楳笏 settings.js                        # API繧ｭ繝ｼ邂｡逅・(localStorage 騾｣謳ｺ)
笏・      笏披楳笏 app.js                             # 繧｢繝励Μ繧ｱ繝ｼ繧ｷ繝ｧ繝ｳ繝ｭ繧ｸ繝・け (繝壹う繝ｭ繝ｼ繝峨∈縺ｮ繧ｭ繝ｼ莉伜刈)
笏懌楳笏 .env.example                               # 迺ｰ蠅・､画焚繝・Φ繝励Ξ繝ｼ繝・
笏懌楳笏 requirements.txt                           # Python萓晏ｭ倬未菫・
笏懌楳笏 specification_v10.md                       # 繧ｳ繧｢莉墓ｧ俶嶌 (v10)
笏披楳笏 script_ai_app_specification_v2.md          # 閼壽悽AI莉墓ｧ俶嶌 (v2)
```

### 繝｢繧ｸ繝･繝ｼ繝ｫ萓晏ｭ倬未菫・

```mermaid
graph TB
    subgraph "繝輔Ο繝ｳ繝医お繝ｳ繝・
        HTML["index.html"] --> CSS["style.css"]
        HTML --> WSClient["websocket.js"]
        HTML --> Renderer["renderer.js"]
        HTML --> App["app.js"]
        App --> WSClient
        App --> Renderer
    end
    
    subgraph "繝舌ャ繧ｯ繧ｨ繝ｳ繝・
        Main["main.py<br>(FastAPI)"] --> Config["config.py"]
        Main --> WSHandler["websocket/handler.py"]
        Main --> MO["master_orchestrator.py"]
        Main --> REGEN["regeneration.py"]
        Main --> DLO["daily_loop/orchestrator.py"]
        
        REGEN --> CD
        REGEN --> PA1
        REGEN --> PA2
        REGEN --> PA3
        REGEN --> PD
        
        MO --> CD["creative_director.py"]
        MO --> PA1["phase_a1/orchestrator.py"]
        MO --> PA2["phase_a2/orchestrator.py<br>(15 Workers)"]
        MO --> PA3["phase_a3/orchestrator.py"]
        MO --> PD["phase_d/orchestrator.py"]
        MO --> EVAL["evaluators/pipeline.py"]
        
        CD --> LLM["tools/llm_api.py"]
        PA1 --> LLM
        PA2 --> LLM
        PA3 --> LLM
        PD --> LLM
        DLO --> LLM
        
        DLO --> ACT["activation.py"]
        DLO --> VER["verification.py"]
        DLO --> CRITIC["diary_critic.py"]
        DLO --> VALIDATOR["linguistic_validator.py"]
        DLO --> NEXT["next_day_planning.py"]
        
        CD --> Models["models/character.py"]
        PA1 --> Models
        PA2 --> Models
        PA3 --> Models
        PD --> Models
        DLO --> Memory["models/memory.py"]
        
        DLO --> Utils["tools/agent_utils.py"]
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

> **蜃｡萓・*: 泪邏ｫ = Tier -1/0 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医Å沐ｵ髱・= Phase Orchestrators縲Å沺｢邱・= 譌･谺｡繝ｫ繝ｼ繝励Å沺｡鮟・= LLM API縲Å沐ｴ襍､ = FastAPI

### 繝励Ο繧ｸ繧ｧ繧ｯ繝郁ｦ∽ｻｶ

| 鬆・岼 | 蜀・ｮｹ |
|---|---|
| **逶ｮ逧・* | 繧ｵ繝ｼ繝峨・繧､繝ｳ繝・Μ繧ｸ繧ｧ繝ｳ繧ｹ遉ｾ B繧ｳ繝ｼ繧ｹ繧､繝ｳ繧ｿ繝ｼ繝ｳ驕ｸ閠・ｪｲ鬘・|
| **隱ｲ鬘・* | 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼAI縺ｫ蟇・蕗蟄ｦ・亥ｿ・炊蟄ｦ逧・ｺｺ譬ｼ繝｢繝・Ν・峨ｒ謨吶∴縲・譌･髢薙・譌･險倥ｒ逕滓・縺吶ｋ |
| **逅・Φ逧・怙邨ょｽ｢** | 1繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ螳悟・縺ｪ閼壽悽繝代ャ繧ｱ繝ｼ繧ｸ・・2繝代Λ繝｡繝ｼ繧ｿ + 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ + 閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝・+ 7譌･髢薙う繝吶Φ繝亥・・峨ｒ逕滓・縺励∵律谺｡繝ｫ繝ｼ繝励〒7譌･髢薙・譌･險倥ｒ閾ｪ蜍慕函謌・|
| **蟇ｾ雎｡繝ｦ繝ｼ繧ｶ繝ｼ** | 繧､繝ｳ繧ｿ繝ｼ繝ｳ驕ｸ閠・・蟇ｩ譟ｻ蜩｡ |
| **螳溯｣・ｯｾ雎｡螟・* | 繧ｯ繝ｭ繝ｼ繝ｪ繝ｳ繧ｰ・・hase B・峨∵闘莨ｼ菴馴ｨ難ｼ・hase C・峨√お繧ｳ繝ｼ繝√ぉ繝ｳ繝舌・ |

### 迴ｾ蝨ｨ縺ｮ繧ｷ繧ｹ繝・Β莉墓ｧ倥・迥ｶ諷・

#### 繧ｳ繧｢繝ｭ繧ｸ繝・け繝ｻ繝ｫ繝ｼ繝ｫ

**4螻､繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝磯嚴螻､・・ay 0・・**
1. **Tier -1 Creative Director** (Opus): Tool-Calling縺ｫ繧医ｋ閾ｪ蠕区耳謨ｲ繝ｫ繝ｼ繝励Ｔearch_web + file_read + request_critique + submit_final_concept 縺ｮ4繝・・繝ｫ縲４elf-Critique繝√ぉ繝・け繝ｪ繧ｹ繝・[A]-[G] 縺ｮ7繧ｫ繝・ざ繝ｪ・・G]=繝ｦ繝ｼ繧ｶ繝ｼ讒区・譁ｹ驥昴→縺ｮ謨ｴ蜷域ｧ・峨ゅΘ繝ｼ繧ｶ繝ｼ謖・ｮ壹・ `StoryCompositionPreferences` 繧樽arkdown蠖｢蠑上〒繝励Ο繝ｳ繝励ヨ縺ｫ豕ｨ蜈･縲・
2. **Tier 0 Master Orchestrator** (Opus): Phase A-1竊但-2竊但-3竊奪鬆・ｬ｡蛻ｶ蠕｡縲ょ推Phase螳御ｺ・ｾ後↓Evaluator-Optimizer繝ｫ繝ｼ繝励〒蜊ｳ譎りｩ穂ｾ｡繝ｻ蜀咲函謌舌・*Creative Director螳御ｺ・ｾ後↓concept_review荳譎ょ●豁｢**・・syncio.Event・峨〒繝ｦ繝ｼ繧ｶ繝ｼ繝ｬ繝薙Η繝ｼ繧貞ｾ・ｩ溘Ｂpprove/revise/edit 縺ｮ3繧｢繧ｯ繧ｷ繝ｧ繝ｳ蟇ｾ蠢懊・*`cancel()`繝｡繧ｽ繝・ラ縺ｫ繧医ｋ荳ｭ譁ｭ讖溯・**・・ebSocket `cancel_character_generation` 繧｢繧ｯ繧ｷ繝ｧ繝ｳ蟇ｾ蠢懶ｼ峨１hase D縺ｫ縺ｯ`set_master_orch()`縺ｧ蜿ら・繧呈ｸ｡縺励√く繝｣繝ｳ繧ｻ繝ｫ莨晄眺縲・
3. **Phase Orchestrators**: 蜷Пhase蜀・・Worker鄒､繧堤ｮ｡逅・・-1=8 Workers+LinguisticExpressionWorker・・Worker蜷郁ｨ医￣haseA1Result霑泌唆・峨、-2=15 Workers・・2 ﾂｧ6.4.2貅匁侠・峨、-3=Planner(閾ｪ辟ｶ險隱・+Writer(JSON荳諡ｬ)縲．=4 Workers(閾ｪ辟ｶ險隱・+EventWriter(JSON)縲・
4. **Workers**: 繝励Ο繝輔ぃ繧､繝ｫ蛻･繝｢繝・Ν・・igh_quality=sonnet, draft=gemini・峨よ怙菴弱ユ繧｣繧｢=Gemini 2.5 Pro縲・

**Phase A-2 Worker 15蛻・牡讒区・・・2 ﾂｧ6.4.2貅匁侠・・**
```
Step 1: 繝代Λ繝｡繝ｼ繧ｿ Worker 10蝓ｺ繧剃ｸｦ蛻怜ｮ溯｡・
  TemperamentWorker_A1 (諠・虚蜿榊ｿ懃ｳｻ #1-9)
  TemperamentWorker_A2 (豢ｻ諤ｧ繝ｻ繧ｨ繝阪Ν繧ｮ繝ｼ邉ｻ #10-14)
  TemperamentWorker_A3 (遉ｾ莨夂噪蠢怜髄邉ｻ #15-18)
  TemperamentWorker_A4 (隱咲衍繧ｹ繧ｿ繧､繝ｫ邉ｻ #19-23)
  PersonalityWorker_B1 (閾ｪ蟾ｱ隱ｿ謨ｴ繝ｻ逶ｮ讓呵ｿｽ豎らｳｻ #24-30)
  PersonalityWorker_B2 (蟇ｾ莠ｺ繝ｻ遉ｾ莨夂噪諷句ｺｦ邉ｻ #31-38)
  PersonalityWorker_B3 (邨碁ｨ薙∈縺ｮ髢区叛諤ｧ邉ｻ #39-43)
  PersonalityWorker_B4 (閾ｪ蟾ｱ讎ょｿｵ繝ｻ螳溷ｭ倡ｳｻ #44-48)
  PersonalityWorker_B5 (繝ｩ繧､繝輔せ繧ｿ繧､繝ｫ繝ｻ陦ｨ蜃ｺ邉ｻ #49-50)
  SocialCognitionWorker (蟇ｾ莉冶・ｪ咲衍 #51-52)
Step 2: 隕冗ｯ・ｱ､ Worker 4蝓ｺ繧剃ｸｦ蛻怜ｮ溯｡・
  ValuesWorker (Schwartz 19萓｡蛟､)
  MFTWorker (驕灘ｾｳ蝓ｺ逶､逅・ｫ・6蝓ｺ逶､)
  IdealOughtSelfWorker (逅・Φ閾ｪ蟾ｱ/鄒ｩ蜍呵・蟾ｱ)
  GoalsDreamsWorker (髟ｷ譛溘・荳ｭ譛溽岼讓・
Step 3: CognitiveDerivation (繝ｫ繝ｼ繝ｫ繝吶・繧ｹ閾ｪ蜍募ｰ主・, LLM荳堺ｽｿ逕ｨ)
```

**Human in the Loop・育函謌仙燕 + 逕滓・蠕鯉ｼ・**
```
縲千函謌仙燕縲代Θ繝ｼ繧ｶ繝ｼ縺・繧ｫ繝・ざ繝ｪ縺ｮ迚ｩ隱樊ｧ区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹ繧剃ｻｻ諢城∈謚・
  竊・StoryCompositionPreferences 縺ｨ縺励※ WebSocket 繝壹う繝ｭ繝ｼ繝峨↓蜷梧｢ｱ
  竊・Creative Director 縺ｮ繝励Ο繝ｳ繝励ヨ縺ｫMarkdown蠖｢蠑上〒豕ｨ蜈･
  竊・Self-Critique [G] 縺ｧ繝ｦ繝ｼ繧ｶ繝ｼ讒区・譁ｹ驥昴→縺ｮ謨ｴ蜷域ｧ繧定・蜍輔メ繧ｧ繝・け

縲千函謌仙ｾ後舛reative Director 竊・[concept_review 荳譎ょ●豁｢] 竊・繝ｦ繝ｼ繧ｶ繝ｼ繝ｬ繝薙Η繝ｼ
  竊・縲梧価隱阪＠縺ｦ邯夊｡後・ approve_concept 竊・Phase A-1 縺ｸ
  竊・縲後ヵ繧｣繝ｼ繝峨ヰ繝・け縺励※蜀咲函謌舌・ revise_concept 竊・Creative Director 蜀榊ｮ溯｡・
  竊・縲檎峩謗･邱ｨ髮・・ edit_concept_direct 竊・邱ｨ髮・ｸ医∩JSON縺ｧ邯夊｡・
```

**迚ｩ隱樊ｧ区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹ `StoryCompositionPreferences`・・繧ｫ繝・ざ繝ｪ + 閾ｪ逕ｱ險倩ｿｰ・・**
| 繧ｫ繝・ざ繝ｪ | 驕ｸ謚櫁い謨ｰ | 逅・ｫ也噪譬ｹ諡 |
|---|---|---|
| 迚ｩ隱樊ｧ矩 (narrative_structure) | 12遞ｮ | Aristotle, Freytag, Campbell, Harmon, Snyder, 襍ｷ謇ｿ霆｢邨・|
| 諢滓ュ繝医・繝ｳ (emotional_tone) | 12遞ｮ | Ekman, Plutchik, McKee |
| 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧｢繝ｼ繧ｯ (character_arc) | 8遞ｮ | Weiland, Vogler, Campbell |
| 繝・・繝槭・驥阪＆ (theme_weight) | 8遞ｮ | Booker, McKee |
| 繧ｯ繝ｩ繧､繝槭ャ繧ｯ繧ｹ讒矩 (climax_structure) | 8遞ｮ | Freytag, McKee, Field |
| 繧ｸ繝｣繝ｳ繝ｫ (genre) | 12遞ｮ | 譁・ｭｦ繧ｸ繝｣繝ｳ繝ｫ逅・ｫ・|
| 繝壹・繧ｷ繝ｳ繧ｰ (pacing) | 8遞ｮ | McKee, Field, Snyder |
| 隱槭ｊ蜿｣ (narrative_voice) | 10遞ｮ | Genette, Booth, Bakhtin |
| 閾ｪ逕ｱ險倩ｿｰ (free_notes) | - | 繝ｦ繝ｼ繧ｶ繝ｼ閾ｪ逕ｱ蜈･蜉・|

**譌･谺｡繝ｫ繝ｼ繝暦ｼ・ay 1-7・・**
```
蜷・律縺ｮ繧､繝吶Φ繝・2-4蛟・ 竊・蜍慕噪豢ｻ諤ｧ蛹・5-10繝代Λ繝｡繝ｼ繧ｿ驕ｸ謚・ 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ+邨碁ｨ泥B蜈･蜉・
竊・陦晏虚邉ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・Perceiver+Impulsive邨ｱ蜷・ raw text蜃ｺ蜉・
竊・縲先─諠・ｼｷ蠎ｦ蛻､螳壹訴ntensity=high 竊・Reflective繝舌う繝代せ / 縺昴ｌ莉･螟・竊・Reflective螳溯｡・raw text蜃ｺ蜉・
竊・蜃ｺ蜉帶､懆ｨｼ(#1-#52貍乗ｴｩ繝√ぉ繝・け, raw text繝吶・繧ｹ)
竊・蜃ｺ譚･莠句捉霎ｺ諠・ｱ邨ｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝・Agentic: 陦悟虚豎ｺ螳・諠・勹謠丞・+繧ｹ繝医・繝ｪ繝ｼ邨ｱ蜷・
竊・縲・縺､縺ｮ蛟句挨繝√ぉ繝・けAI縲善rofile/Temperament/Personality/Values荳ｦ蛻励メ繧ｧ繝・け
竊・萓｡蛟､隕ｳ驕募渚繝√ぉ繝・け
竊・蜀・怐(Self-Perception + 驕主悉邨ｱ蜷・+ 蜀崎ｧ｣驥・ raw text蜃ｺ蜉・
竊・鄙梧律莠亥ｮ夊ｿｽ蜉(蠢・医う繝吶Φ繝亥喧) 竊・Stage 19螟画峩: 譌･險倡函謌舌・蜑阪↓螳溯｡・
竊・譌･險倡函謌・ Agentic譌･險伜濤遲・險隱樒噪陦ｨ迴ｾ譁ｹ豕票LinguisticExpression]蜈ｨ諠・ｱ豕ｨ蜈･繝ｻcheck_diary_rules蠢・医ご繝ｼ繝井ｻ倥″繝ｻsubmit譎ょｼｷ蛻ｶ繝√ぉ繝・け)
竊・縲・縺､縺ｮ蛟句挨繝√ぉ繝・けAI縲第律險伜・蜉帙メ繧ｧ繝・け
竊・繝繝ｼ繝画峩譁ｰ(Peak-End Rule) 竊・key memory謚ｽ蜃ｺ(蛟句挨繝輔ぃ繧､繝ｫ菫晏ｭ・ + 險俶・蝨ｧ邵ｮ
竊・繝繝ｼ繝営arry-over(貂幄｡ｰ+髢ｾ蛟､繝ｪ繧ｻ繝・ヨ)

窶ｻ 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繝ｻ荳也阜險ｭ螳壹・蜻ｨ蝗ｲ莠ｺ迚ｩ繝ｻ邨碁ｨ泥B繝ｻkey memory繧貞酔譴ｱ
窶ｻ 邨ｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医・譌･險倥お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓縺ｯ謇謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚・・haracterCapabilities・峨ｂ蜷梧｢ｱ・・apabilities 縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷医・縺ｿ・・
窶ｻ 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙・markdown繝代・繧ｹ縺帙★raw text縺ｧ谺｡縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺昴・縺ｾ縺ｾ貂｡縺・
```

**蜃ｺ蜉帛ｽ｢蠑上・險ｭ險亥次蜑・**
| 蜃ｺ蜉帙・逕ｨ騾・| 蠖｢蠑・| 萓・|
|-----------|------|-----|
| 繧ｳ繝ｼ繝峨′讖滓｢ｰ逧・↓繝代・繧ｹ縺励※Pydantic繝｢繝・Ν縺ｫ譬ｼ邏阪☆繧句､ | JSON (`json_mode=True`) | 繝代Λ繝｡繝ｼ繧ｿID縲・pisode Writer蜈ｨ蜃ｺ蜉帙仝eeklyEventWriter蜈ｨ蜃ｺ蜉帙ゝool Calling |
| 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝磯俣縺ｧ繝励Ο繝ｳ繝励ヨ繧ｳ繝ｳ繝・く繧ｹ繝医→縺励※貂｡縺吶ｂ縺ｮ | raw text・亥・譁㎝ass-through・・| 陦晏虚邉ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙ヽeflective蜃ｺ蜉帙∝・逵√Γ繝｢ |
| 譛邨ょ・蜉・| 閾ｪ辟ｶ縺ｪ譁・ｫ | 譌･險倥√リ繝ｩ繝・ぅ繝・|

**髫阡ｽ蜴溷援・・mplicit/explicit髱槫ｯｾ遘ｰ・・**
- 陦晏虚邉ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ・erceiver+Impulsive邨ｱ蜷茨ｼ・ 豌苓ｳｪ繝ｻ諤ｧ譬ｼ螻､縺ｫ繧｢繧ｯ繧ｻ繧ｹ蜿ｯ / 隕冗ｯ・ｱ､縺ｫ繧｢繧ｯ繧ｻ繧ｹ荳榊庄
- Reflective Agent: 豌苓ｳｪ繝ｻ諤ｧ譬ｼ螻､縺ｫ髫阡ｽ / 隕冗ｯ・ｱ､縺ｫ繧｢繧ｯ繧ｻ繧ｹ蜿ｯ / 陦晏虚邉ｻ蜃ｺ蜉帙ｒraw text縺ｧ蜿励￠蜿悶ｋ
- 譌･險倡函謌植I: 豌苓ｳｪ繝ｻ諤ｧ譬ｼ繝代Λ繝｡繝ｼ繧ｿ繧堤衍繧峨↑縺・ｼ郁｡悟虚縺九ｉ縺ｮ謗ｨ貂ｬ縺ｮ縺ｿ・・

**蜩∬ｳｪ繝励Ο繝輔ぃ繧､繝ｫ蛻･繝｢繝・Ν險ｭ螳・**
| Profile | director_tier | worker_tier | Evaluator | retry蝗樊焚 | 蛯呵・|
|---------|--------------|-------------|-----------|-----------|------|
| high_quality | opus | sonnet | 蜈ｨ7遞ｮON | 4 | 譛ｬ逡ｪ謠仙・逕ｨ |
| standard | sonnet | sonnet | 5遞ｮON | 3 | 謗ｨ螂ｨ繝舌Λ繝ｳ繧ｹ |
| fast | sonnet | gemini | 3遞ｮON | 2 | 邏譌ｩ縺・｢ｺ隱・|
| draft | sonnet | gemini | 2遞ｮON | 2 | 譛蟆上さ繧ｹ繝茨ｼ域怙菴弱ユ繧｣繧｢=Gemini 2.5 Pro 竊・2.0 Flash閾ｪ蜍輔ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ・・|

**Gemini 2谿ｵ髫弱ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ・・tier="gemini"`・・**
- 隨ｬ1隧ｦ陦・ Gemini 2.5 Pro・磯ｫ伜刀雉ｪ縲・000繝ｪ繧ｯ繧ｨ繧ｹ繝・譌･縺ｮ辟｡譁呎棧・・
- 隨ｬ2隧ｦ陦・ 繧ｯ繧ｩ繝ｼ繧ｿ雜・℃・・29 / ResourceExhausted・画凾 竊・Gemini 2.0 Flash・・500繝ｪ繧ｯ繧ｨ繧ｹ繝・譌･縺ｮ辟｡譁呎棧・・
- Claude・・pus/sonnet・峨°繧烏emini縺ｸ縺ｮ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ譎ゅｂ蜷梧ｧ倥・2谿ｵ髫弱ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ繧帝←逕ｨ

#### 繝・・繧ｿ繝｢繝・Ν・・2 ﾂｧ6.3.4貅匁侠諡｡蠑ｵ貂茨ｼ・

| 繝｢繝・Ν | 逕ｨ騾・| Phase | 諡｡蠑ｵ繝輔ぅ繝ｼ繝ｫ繝・|
|---|---|---|---|
| `ConceptPackage` | 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ讎ょｿｵ險ｭ險・| Tier -1 | psychological_hints(want_and_need, ghost_wound, lie) |
| `GenerationStatus` | 逕滓・繝励Ο繧ｻ繧ｹ縺ｮ騾ｲ謐礼ｮ｡逅・ｼ育ｮ｡逅・・繝・け繧ｹ・・| 蜈ｨ菴・| 蜷・ヵ繧ｧ繝ｼ繧ｺ繝ｻ繧ｹ繝・ャ繝励・螳御ｺ・ヵ繝ｩ繧ｰ縲￣hase D縺ｮ譌･谺｡騾ｲ謐・|
| `CharacterPackage` | 閼壽悽繝代ャ繧ｱ繝ｼ繧ｸ蜈ｨ菴・| 蜈ｨ菴・| `status: GenerationStatus` 繧貞・蛹・|
| `MacroProfile` | 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ・・繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ・・| A-1 | VoiceFingerprint諡｡蠑ｵ(莠御ｺｺ遘ｰ, 邨ｵ譁・ｭ・ 閾ｪ蝠城ｻ蠎ｦ, 豈泌湊鬆ｻ蠎ｦ)縲Ｗoice_fingerprint縺ｯ蠕梧婿莠呈鋤縺ｮ縺溘ａ谿句ｭ・|
| `LinguisticExpression` | 險隱樒噪陦ｨ迴ｾ譁ｹ豕包ｼ育峡遶狗函謌舌い繧､繝・Β・・| A-1 | SpeechCharacteristics(concrete_features+abstract_feel+conversation_style+emotional_expression_tendency) + DiaryWritingAtmosphere(tone+structure+introspection+written/omitted+atmosphere)縲よ律險倡函謌舌・繝ｭ繝ｳ繝励ヨ縺ｫ縺ｮ縺ｿ豕ｨ蜈･ |
| `MicroParameters` | 52繝代Λ繝｡繝ｼ繧ｿ + 隕冗ｯ・ｱ､ | A-2 | 15 Worker蟇ｾ蠢懊し繝悶Δ繝・Ν(SchwartzValuesOutput遲・ |
| `AutobiographicalEpisodes` | 閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝会ｼ・-8蛟具ｼ・| A-3 | McAdams 5繧ｫ繝・ざ繝ｪ + redemption bias蟇ｾ遲・|
| `WeeklyEventsStore` | 7譌･髢薙う繝吶Φ繝亥・・・4-28莉ｶ・・| D | 2霆ｸ繝｡繧ｿ繝・・繧ｿ(known/unknown x expectedness) |
| `CharacterCapabilities` | 謇謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚・・hase D 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け逕滓・・・| D | PossessedItem(name/description/always_carried/emotional_significance) ﾃ・5-10蛟九，haracterAbility(name/description/proficiency/origin) ﾃ・3-5蛟九、vailableAction(action/context/prerequisites) ﾃ・3-5蛟・|
| `CapabilitiesHints` | 謇謖∝刀繝ｻ閭ｽ蜉帙・譁ｹ蜷第ｧ繝偵Φ繝茨ｼ・reative Director險ｭ險茨ｼ・| Tier -1 | key_possessions_hint / core_abilities_hint / signature_actions_hint 縺ｮ3繝輔ぅ繝ｼ繝ｫ繝峨・onceptPackage縺ｫ蜀・桁縲１hase D capabilities逕滓・縺ｮ襍ｷ轤ｹ縺ｨ縺励※蜿ら・ |
| `MoodState` | PAD 3谺｡蜈・Β繝ｼ繝・| 譌･谺｡繝ｫ繝ｼ繝・| Peak-End Rule + carry-over |
| `ShortTermMemoryDB` | 險俶・・磯壼ｸｸ鬆伜沺縺ｮ縺ｿ縲∵ｮｵ髫主悸邵ｮ・・| 譌･谺｡繝ｫ繝ｼ繝・| LLM谿ｵ髫主悸邵ｮ(400竊・00竊・0竊・0蟄・ |
| `KeyMemoryStore` | key memory・亥句挨繝輔ぃ繧､繝ｫ邂｡逅・・譌･髢薙ヵ繝ｫ菫晄戟・・| 譌･谺｡繝ｫ繝ｼ繝・| `key_memories/day_01.json`蠖｢蠑上〒菫晏ｭ・|
| `ShortTermMemoryStore` | 遏ｭ譛溯ｨ俶・DB譌･蜊倅ｽ阪せ繝翫ャ繝励す繝ｧ繝・ヨ豌ｸ邯壼喧 | 譌･谺｡繝ｫ繝ｼ繝・| `short_term_memory/day_01.json`蠖｢蠑上∝悸邵ｮ蠕後・蜈ｨ迥ｶ諷九ｒ菫晄戟 |
| `MoodStateStore` | 繝繝ｼ繝臥憾諷区律蜊倅ｽ阪せ繝翫ャ繝励す繝ｧ繝・ヨ豌ｸ邯壼喧 | 譌･谺｡繝ｫ繝ｼ繝・| `mood_states/day_01.json`蠖｢蠑上‥aily_mood+carry_over_mood繧剃ｿ晄戟 |
| `EmotionIntensityResult` | 諢滓ュ蠑ｷ蠎ｦ蛻､螳夲ｼ・ow/medium/high・・| 譌･谺｡繝ｫ繝ｼ繝・| Impulsive蠕後↓JSON蛻､螳・|
| `CheckResult` | 4蛟句挨繝√ぉ繝・けAI縺ｮ邨先棡 | 譌･谺｡繝ｫ繝ｼ繝・| passed/issues/severity |
| `EventPackage` | 1繧､繝吶Φ繝亥・逅・ｵ先棡 | 譌･谺｡繝ｫ繝ｼ繝・| 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙ｒ蛹・性 |

#### UI/UX

- **繝輔ぉ繝ｼ繧ｺ讒区・縺ｮ蛹ｺ蛻・喧**: Day 0 繝繝・す繝･繝懊・繝会ｼ医く繝｣繝ｩ繧ｯ繧ｿ繝ｼ險ｭ螳夂ｵ先棡遒ｺ隱咲判髱｢・峨→ Day 1-7・域律險倡函謌撰ｼ峨・繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繝ｫ繝ｼ繝励ｒ譏守｢ｺ縺ｫUI蛻・牡縲・
- **逕滓・騾ｲ謐礼ｮ｡逅・ｼ育ｮ｡逅・・繝・け繧ｹ・・*: `GenerationStatus` 繝｢繝・Ν縺ｫ繧医ｋ蜴ｳ蟇・↑迥ｶ諷狗ｮ｡逅・ょ推繝輔ぉ繝ｼ繧ｺ・・1-3, D・峨♀繧医・ Phase D 蜀・Κ縺ｮ蜷・せ繝・ャ繝励・螳御ｺ・ｒ繝輔Λ繧ｰ縺ｧ邂｡逅・＠縲・㍾隍・函謌舌ｒ讒矩逧・↓髦ｲ豁｢縲・
- **4逕ｻ髱｢讒区・**: 襍ｷ蜍・竊・逕滓・荳ｭ・域晁・→繝輔ぉ繝ｼ繧ｺ繝医Λ繝・き繝ｼ・・竊・Day 0邨先棡・・繧ｿ繝悶・繝繝・す繝･繝懊・繝会ｼ・竊・螻･豁ｴ
- **逕滓・騾ｲ陦袈I・・hase Tracker・・*: 逕滓・荳ｭ逕ｻ髱｢縺ｫ縺ｦ縲∫樟蝨ｨ縺ｮ繝代う繝励Λ繧､繝ｳ螳溯｡檎憾諷具ｼ・reative Director 竊・A-1 竊・A-2 竊・A-3 竊・D・峨ｒ繧ｹ繝・ャ繝怜ｽ｢蠑上〒蜿ｯ隕門喧縲・
- **譌･險倡函謌舌Ρ繝ｼ繧ｯ繝輔Ο繝ｼ縺ｮ邨ｱ蜷医→ UI 蛻ｷ譁ｰ**: 譌･險倥ち繝門・縺ｫ縲檎ｵｱ蜷医さ繝ｳ繝医Ο繝ｼ繝ｫ繝代ロ繝ｫ縲阪ｒ螳溯｣・ら函謌仙燕縺ｮ繧､繝ｳ繝ｩ繧､繝ｳ謖・､ｺ蜈･蜉幢ｼ医さ繝｡繝ｳ繝域ｩ溯・・峨∫憾諷九↓蠢懊§縺ｦ縲檎函謌・蜀咲函謌・荳ｭ譁ｭ縲阪→蠖ｹ蜑ｲ縺悟・繧頑崛繧上ｋ繝繧､繝翫Α繝・け縺ｪ繧｢繧ｯ繧ｷ繝ｧ繝ｳ繝懊ち繝ｳ縲√Μ繧｢繝ｫ繧ｿ繧､繝縺ｪ騾ｲ謐苓｡ｨ遉ｺ繝ｻ諤晁・Ο繧ｰ繧貞腰荳逕ｻ髱｢縺ｫ邨ｱ蜷医＠縲∬ｩｦ陦碁険隱､縺ｮ繝ｫ繝ｼ繝励ｒ鬮倬溷喧縲・
- **謖・､ｺ蜈･蜉・(regeneration_context)**: 譌･險倥・蛻晏屓逕滓・縺翫ｈ縺ｳ蜀咲函謌先凾縺ｫ繝ｦ繝ｼ繧ｶ繝ｼ縺九ｉ縺ｮ繧ｳ繝｡繝ｳ繝茨ｼ医後ｂ縺｣縺ｨ隧ｩ逧・↓縲阪↑縺ｩ・峨ｒ繝舌ャ繧ｯ繧ｨ繝ｳ繝峨・繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繝ｼ縺ｫ貂｡縺励√・繝ｭ繝ｳ繝医↓蜿肴丐縺輔○繧倶ｻ慕ｵ・∩繧貞ｰ主・縲・
- **荳ｭ譁ｭ讖溯・ (Cancellation)**: WebSocket 邨檎罰縺ｮ `cancel_diary` 繧｢繧ｯ繧ｷ繝ｧ繝ｳ縺ｫ繧医ｊ縲∝ｮ溯｡御ｸｭ縺ｮ譌･險倡函謌舌・繝ｭ繧ｻ繧ｹ繧貞ｮ牙・縺ｫ蛛懈ｭ｢縺励ゞI繧貞叉蠎ｧ縺ｫ繝ｪ繧ｻ繝・ヨ蜿ｯ閭ｽ縲・
- **繧ｨ繝ｩ繝ｼ閠先ｧ縺ｨ逕滓・蜀埼幕・・esume・・*: Pydantic v2 縺ｮ `field_validator` 縺ｫ繧医ｋ閾ｪ蟾ｱ菫ｮ蠕ｩ + 蜷Пhase螳御ｺ・＃縺ｨ縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝井ｿ晏ｭ倥・
- **繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝亥句挨蜀咲函謌舌・邱ｨ髮・*: 蜷・ち繝厄ｼ医さ繝ｳ繧ｻ繝励ヨ/繝励Ο繝輔ぅ繝ｼ繝ｫ/繝代Λ繝｡繝ｼ繧ｿ/繧ｨ繝斐た繝ｼ繝・繧､繝吶Φ繝茨ｼ峨↓縲悟・逕滓・縲阪檎ｷｨ髮・阪・繧ｿ繝ｳ繧帝・鄂ｮ縲ょ刈縺医※縲∝・譛溽判髱｢縺ｮ縲檎ｴ譽・＠縺ｦ蜀咲函謌舌阪・繧ｿ繝ｳ・亥・繝・・繧ｿ蝟ｪ螟ｱ繝ｪ繧ｹ繧ｯ・峨ｒ謦､蟒・＠縲√後そ繧ｯ繧ｷ繝ｧ繝ｳ縺斐→縺ｫ蜀咲函謌舌阪Δ繝ｼ繝繝ｫ縺ｸ遘ｻ陦後ょ・逕滓・繝｢繝ｼ繝繝ｫ縺ｧ閾ｪ辟ｶ險隱樊欠遉ｺ繧貞・蜉帛庄閭ｽ縲らｷｨ髮・Δ繝ｼ繝繝ｫ縺ｧJSON逶ｴ謗･邱ｨ髮・・菫晏ｭ倥ゆｸ区ｵ√き繧ｹ繧ｱ繝ｼ繝牙・逕滓・縺ｯ繧ｪ繝励ヨ繧､繝ｳ縲・
- **荳榊・蜷医→菫ｮ豁｣迥ｶ豕・(2026-04-22)**: 螻･豁ｴ荳隕ｧ縺九ｉ譌｢蟄倥ヱ繝・こ繝ｼ繧ｸ繧帝∈謚槭＠縺滄圀縺ｫ縲∝炎髯､貂医∩縺ｮDOM隕∫ｴ・・diary-start-panel`縺ｪ縺ｩ・峨ｒ蜿ら・縺励※繧ｹ繧ｯ繝ｪ繝励ヨ縺後け繝ｩ繝・す繝･縺吶ｋ荳榊・蜷医ｒ遒ｺ隱阪ら樟蝨ｨ菫ｮ豁｣繝励Λ繝ｳ繧剃ｽ懈・荳ｭ縲・
- **讒区・險ｭ螳啅I**: 7遞ｮ縺ｮEvaluator縺ｮON/OFF繧堤峡遶句・繧頑崛縺亥庄閭ｽ縲・
- **WebSocket**: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝域晁・・繝ｪ繧｢繝ｫ繧ｿ繧､繝陦ｨ遉ｺ縲りｩｳ邏ｰ騾ｲ謐励ワ繝ｼ繝医ン繝ｼ繝医・
- **繧ｳ繧ｹ繝郁｡ｨ遉ｺ**: 繝ｪ繧｢繝ｫ繧ｿ繧､繝繝医・繧ｯ繝ｳ豸郁ｲｻ繝ｻ謗ｨ螳壹さ繧ｹ繝郁｡ｨ遉ｺ縲・

#### 繝・・繧ｿ繝輔Ο繝ｼ繝ｻ豌ｸ邯壼喧莉墓ｧ・

- **1繧ｭ繝｣繝ｩ=1繝・ぅ繝ｬ繧ｯ繝医Μ蜴溷援**: 逕滓・荳ｭ繝ｻ螳御ｺ・ｾ後ｒ蝠上ｏ縺壹∝・繝・・繧ｿ縺ｯ `character_packages/{safe_name(繧ｭ繝｣繝ｩ蜷・}/` 驟堺ｸ九↓邨ｱ荳菫晏ｭ・
- **繧､繝ｳ繝｡繝｢繝ｪ蜈ｱ譛・*: 蜃ｦ逅・比ｸｭ縺ｮ蜈ｨ繧ｪ繝悶ず繧ｧ繧ｯ繝域ｧ区・縺ｯPydantic繧ｹ繧ｭ繝ｼ繝槭↓繧医▲縺ｦ繝｡繝｢繝ｪ荳翫↓菫昴◆繧後ｋ
- **繝輔ぃ繧､繝ｫ豌ｸ邯壼喧・域律蜊倅ｽ阪ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・ｼ・*: 譌･谺｡繝ｫ繝ｼ繝励・蜷・律邨ゆｺ・凾縺ｫ莉･荳九ｒ閾ｪ蜍穂ｿ晏ｭ・
  - `short_term_memory/day_NN.json` 窶・ShortTermMemoryDB繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ・・ormal_area + diary_store・・
  - `mood_states/day_NN.json` 窶・MoodState・・aily_mood + carry_over_mood・・
  - `key_memories/day_NN.json` 窶・key memory・・00蟄嶺ｻ･蜀・∝悸邵ｮ蟇ｾ雎｡螟厄ｼ・
  - `daily_logs/Day_{N}.md` 窶・譌･谺｡繝ｭ繧ｰ・育ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙・繝繝ｼ繝牙､蛾・繝ｻ蜀・怐繝ｻ譌･險倥・鄙梧律莠亥ｮ壹り｡晏虚/逅・ｧ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙・髯､螟厄ｼ・
  - `daily_logs/Day_{N}_rim_outputs.md` 窶・陦晏虚/逅・ｧ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ・mpulsive/Reflective・峨・逕溷・蜉幢ｼ医ョ繝舌ャ繧ｰ繝ｻ蛻・梵逕ｨ・・
- **蠕ｩ蜈・・蜀埼幕**: DailyLoopOrchestrator蛻晄悄蛹匁凾縺ｫ譛譁ｰ繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ繧定・蜍輔Ο繝ｼ繝峨＠縲∽ｿ晏ｭ俶ｸ医∩譌･縺ｮ鄙梧律縺九ｉ蜀埼幕
- **繧ｷ繧ｹ繝・Β繝ｻ繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝医・豌ｸ邯壼喧**: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝郁・霄ｫ縺檎函謌舌☆繧九Γ繧ｿ繝・・繧ｿ・亥ｮ溯｣・ｨ育判縲√え繧ｩ繝ｼ繧ｯ繧ｹ繝ｫ繝ｼ縲√ち繧ｹ繧ｯ繝ｪ繧ｹ繝育ｭ会ｼ峨・縲√・繝ｭ繧ｸ繧ｧ繧ｯ繝亥､悶・繧ｷ繧ｹ繝・Β鬆伜沺縺ｫ莨夊ｩｱID縺斐→縺ｫ菫晏ｭ倥＆繧後ｋ
  - 菫晏ｭ伜・: `C:\Users\mahim\.gemini\antigravity\brain\<conversation-id>\`
  - 蟇ｾ雎｡: `implementation_plan.md`, `walkthrough.md`, `task.md` 縺翫ｈ縺ｳ縺昴・螻･豁ｴ縲・
- **縺昴・莉匁ｰｸ邯壼喧繝輔ぃ繧､繝ｫ**:
  - `package.json` 窶・譛邨ゅく繝｣繝ｩ繧ｯ繧ｿ繝ｼ繝代ャ繧ｱ繝ｼ繧ｸ・育函謌仙ｮ御ｺ・凾・・
  - `checkpoint.json` 窶・Phase A-C荳ｭ譁ｭ蜀埼幕逕ｨ
  - `00_profile.md` 窶・莠ｺ髢灘庄隱ｭ繝励Ο繝輔ぃ繧､繝ｫ
  - `agent_logs.json/.md` 窶・繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝域晁・Ο繧ｰ

#### 繧ｨ繝・ず繧ｱ繝ｼ繧ｹ繝ｻ蛻ｶ邏・

- `source: "protagonist_plan"` 縺ｯ Phase D 縺ｧ縺ｯ1莉ｶ繧ら函謌千ｦ∵ｭ｢・域律谺｡繝ｫ繝ｼ繝励・鄙梧律莠亥ｮ夊ｿｽ蜉縺悟髪荳縺ｮ邨瑚ｷｯ・・
- redemption bias蟇ｾ遲・ contamination/loss/ambivalent蝙九′螳画・縺ｪ謨第ｸ医〒邨ゅｏ繧九％縺ｨ繧呈ｧ矩逧・↓髦ｲ豁｢
- 莠域Φ螟門ｺｦ蛻・ｸ・宛邏・ `low`・井ｺ亥ｮ夐壹ｊ繝ｻ譌･蟶ｸ・峨′蜷・律縺ｮ蜊雁・莉･荳翫～high`・亥ｼｷ縺・ｩ壹″・峨・ Day 5 莉･螟悶〒蜷・律譛螟ｧ1莉ｶ

---

## 繝代・繝・: 繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ繝ｻ險ｭ險磯ｲ蛹・

### 1. 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝磯嚴螻､縺ｮ險ｭ險医→隧穂ｾ｡繝ｫ繝ｼ繝・

**(a) 蠖灘・險ｭ險・*: 莉墓ｧ俶嶌v2縺ｮ4螻､髫主ｱ､繧呈治逕ｨ縲りｩ穂ｾ｡(EvaluatorPipeline)縺ｯ縺吶∋縺ｦ縺ｮ逕滓・縺檎ｵゅｏ縺｣縺滓怙蠕後↓縺ｾ縺ｨ繧√※蜻ｼ縺ｳ蜃ｺ縺励※謌仙凄繧偵ユ繧ｹ繝医☆繧区Φ螳壹・
**(b) 螟画峩繝ｻ譬ｹ諡**: 蜈ｨ蟾･遞狗ｵゆｺ・ｾ後・繝・せ繝医〒縺ｯ縲∽ｾ九∴縺ｰPhase A-1・医・繧ｯ繝ｭ・峨〒荳榊粋譬ｼ縺悟・縺溷ｴ蜷医∵里縺ｫ辟｡鬧・↓豸郁ｲｻ縺励◆Phase D縺ｾ縺ｧ縺ｮ繝医・繧ｯ繝ｳ逕滓・縺悟・縺ｦ遐ｴ譽・＆繧後ｋ縺ｨ縺・≧繧ｳ繧ｹ繝育ｴ螢翫・蝠城｡後′蟄伜惠縺励◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: `MasterOrchestrator` 縺ｮ `run()` 蜀・↓縲窪valuator-Optimizer 繝ｫ繝ｼ繝励阪ｒ螳悟・邨ｱ蜷医ょ推Phase螳御ｺ・峩蠕後↓蜊ｳ蠎ｧ縺ｫ隧穂ｾ｡繧呈検縺ｿ縲：ail縺ｪ繧峨◎縺ｮPhase縺縺代ｒ謖・ｮ壼屓謨ｰ・域怙螟ｧ4蝗橸ｼ牙・逕滓・縺輔○繧句・欧縺ｪ閾ｪ蠕倶ｿｮ豁｣繧ｷ繧ｹ繝・Β縺ｸ騾ｲ蛹悶・

### 2. LLM API險ｭ險・

**(a) 蠖灘・險ｭ險・*: Claude Agent SDK菴ｿ逕ｨ繧貞燕謠舌・
**(b) 螟画峩繝ｻ譬ｹ諡**: SDK譛ｪ遒ｺ隱阪・縺溘ａ縲∫峩謗･Anthropic API縺翫ｈ縺ｳGoogle Generative AI縺ｫ蛻・崛縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: `call_llm()` 邨ｱ荳繧､繝ｳ繧ｿ繝ｼ繝輔ぉ繝ｼ繧ｹ縺ｧ縲∝ｮ溷惠縺吶ｋ譛譁ｰ繝｢繝・ΝID・・claude-opus-4-6`遲会ｼ峨ｒ逶ｴ謗･謖・ｮ壹ゅお繝ｩ繝ｼ譎ゅ↓縺ｯ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ繝ｫ繝ｼ繝・ぅ繝ｳ繧ｰ・・nthropic 竊・Gemini 2.5 Pro・峨′菴懷虚縲ゅΔ繝・Ν繝・ぅ繧｢縺ｯ3谿ｵ髫・ opus / sonnet / gemini・・emini 2.5 Pro・峨・

### 2b. Gemini 2.5 Pro繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｮ諤晁・ヨ繝ｼ繧ｯ繝ｳ蟇ｾ遲・

**(a) 蠖灘・險ｭ險・*: Claude縺ｨ蜷後§`max_tokens`蛟､繧偵◎縺ｮ縺ｾ縺ｾGemini縺ｸ貂｡縺励※縺・◆縲Ａsystem_prompt`縺ｯ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ譎ゅ↓`user_message`縺ｫ譁・ｭ怜・邨仙粋縺励※貂｡縺励※縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: Gemini 2.5 Pro縺ｯ蜀・Κ縺ｧ縲梧晁・ヨ繝ｼ繧ｯ繝ｳ縲阪ｒ菴ｿ逕ｨ縺励～max_output_tokens`縺ｮ莠育ｮ励ｒ豸郁ｲｻ縺吶ｋ縲ゆｾ九∴縺ｰ`max_tokens=3000`縺ｮ蝣ｴ蜷医∵晁・□縺代〒3000繝医・繧ｯ繝ｳ蜈ｨ縺ｦ繧剃ｽｿ縺・・繧翫∝ｮ滄圀縺ｮ蜃ｺ蜉帙′0繝医・繧ｯ繝ｳ・・finish_reason=MAX_TOKENS`・峨↓縺ｪ繧句撫鬘後′逋ｺ隕壹ゅ∪縺歔system_prompt`繧蛋user_message`縺ｫ邨仙粋縺吶ｋ譁ｹ蠑上〒縺ｯGemini縺ｮ`system_instruction`讖溯・縺御ｽｿ繧上ｌ縺壹∵欠遉ｺ縺ｮ蛻・屬縺梧ｩ溯・縺励↑縺九▲縺溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: `call_google_ai()`縺ｧGemini 2.5 Pro讀懷・譎ゅ↓`max_output_tokens`繧定・蜍慕噪縺ｫ4蛟搾ｼ域怙菴・6384・峨↓諡｡蠑ｵ縲ょ・tier(opus/sonnet/gemini)縺ｮ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｧ`system_prompt`繧蛋call_google_ai`縺ｮ`system_prompt`蠑墓焚縺ｨ縺励※豁｣縺励￥貂｡縺吶ｈ縺・ｿｮ豁｣縲・

### 3. 髫阡ｽ蜴溷援縺ｮ螳溯｣・

**(a) 蠖灘・險ｭ險・*: 蜷・お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺吶さ繝ｳ繝・く繧ｹ繝医ｒ髢｢謨ｰ蠑墓焚繝ｬ繝吶Ν縺ｧ蛻ｶ蠕｡
**(b) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 
- Impulsive Agent: 豢ｻ諤ｧ蛹悶＆繧後◆豌苓ｳｪ繝ｻ諤ｧ譬ｼ繝代Λ繝｡繝ｼ繧ｿ繧堤峩謗･貂｡縺・
- Reflective Agent: 豢ｻ諤ｧ蛹悶＆繧後◆隕冗ｯ・ｱ､縺ｮ縺ｿ貂｡縺呻ｼ域ｰ苓ｳｪ繝代Λ繝｡繝ｼ繧ｿ縺ｯ貂｡縺輔↑縺・ｼ・
- 譌･險倡函謌植I: `linguistic_expression`・郁ｨ隱樒噪陦ｨ迴ｾ譁ｹ豕包ｼ牙・諠・ｱ繧呈ｸ｡縺呻ｼ医ヱ繝ｩ繝｡繝ｼ繧ｿ蛟､縺ｯ荳蛻・ｸ｡縺輔↑縺・ｼ・
- 讀懆ｨｼ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ 繝代Λ繝｡繝ｼ繧ｿ蜷阪・ID (#1-#52) 縺ｮ貍乗ｴｩ繧偵く繝ｼ繝ｯ繝ｼ繝会ｼ記LM縺ｧ閾ｪ蜍穂ｿｮ豁｣

### 4. 繧ｳ繧｢API螻､縺ｮ閾ｪ蠕九お繝ｼ繧ｸ繧ｧ繝ｳ繝亥喧 (Agentic Loops v10)

**(a) 蠖灘・險ｭ險・*: Python蛛ｴ縺ｮ蝗ｺ螳壼喧縺輔ｌ縺滄・ｬ｡繝ｻ蜿榊ｾｩ繝ｫ繝ｼ繝玲ｧ矩縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: V10莉墓ｧ俶嶌縺ｫ蝓ｺ縺･縺上檎悄縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け縺ｪ謖ｯ繧玖・縺・阪ｒ螳溽樟縺吶ｋ縺溘ａ縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: Anthropic Tool Calling讖溯・繧堤ｵｱ蜷医＠縺・`call_llm_agentic` 繧､繝ｳ繝輔Λ繧呈ｧ狗ｯ峨＠縲，reativeDirector縲！ntegration Agent(陦悟虚豎ｺ螳・縲．iaryGenerationAgent縺ｮ3繧ｳ繧｢繧・Tool-using Autonomous Agent 縺ｸ鄂ｮ謠帙ょ・Agentic繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・ `self.profile.worker_tier` 縺ｫ蝓ｺ縺･縺・Claude竊竪emini閾ｪ蜍輔ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ・・ry/except + `call_llm_agentic_gemini`・峨ｒ螳溯｣・ょ・驛ｨ繝・・繝ｫ・・simulate_action_consequences`遲会ｼ峨・tier繧ゅ・繝ｭ繝輔ぃ繧､繝ｫ騾｣蜍輔・

### 5. 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帛ｽ｢蠑・ JSON 竊・閾ｪ辟ｶ險隱・竊・raw text pass-through

**(a) 蠖灘・險ｭ險・*: 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙ｒ `json_mode=True` 縺ｧ JSON 蠖｢蠑上↓邨ｱ荳縺励￣ydantic 繝｢繝・Ν縺ｧ逶ｴ謗･繝代・繧ｹ縺励※縺・◆縲・
**(b) 隨ｬ1谺｡螟画峩**: JSON竊樽arkdown讒矩蛹悶Ａparse_markdown_sections()`縺ｧ`## 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ蜷港蜊倅ｽ阪↓繝代・繧ｹ縺励￣ydantic繝｢繝・Ν縺ｮ繝輔ぅ繝ｼ繝ｫ繝峨↓蛻・・縲・
**(c) 隨ｬ2谺｡螟画峩繝ｻ譬ｹ諡**: Markdown繝代・繧ｹ譁ｹ蠑上〒縺ｯ縲´LM縺檎函謌舌＠縺溘そ繧ｯ繧ｷ繝ｧ繝ｳ・井ｾ・縲檎函縺倥◆陦晏虚縲搾ｼ峨′Pydantic繝｢繝・Ν縺ｫ蟇ｾ蠢懊ヵ繧｣繝ｼ繝ｫ繝峨′縺ｪ縺・ｴ蜷医↓謐ｨ縺ｦ繧峨ｌ縺ｦ縺・◆縲ゅ∪縺溘√ヱ繝ｼ繧ｹ竊貞・讒区・縺ｮ蠕蠕ｩ縺悟・髟ｷ縺ｧ縺ゅｊ縲∵ｬ｡縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺咎圀縺ｫ繧上＊繧上＊蛻・ｧ｣縺励※蜀咲ｵ仙粋縺吶ｋ諢丞袖縺後↑縺九▲縺溘・
**(d) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 
- **JSON邯ｭ謖・*: DynamicActivation(繝代Λ繝｡繝ｼ繧ｿID)縲〃aluesViolation(bool蛻､螳・縲・motionIntensity(蛻､螳・縲ゝool Calling(decision_package)
- **raw text pass-through**: 陦晏虚邉ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・Reflective繝ｻ蜀・怐縺ｮ蜃ｺ蜉帙・LLM蜃ｺ蜉帙・蜈ｨ譁・ｒ`raw_text`繝輔ぅ繝ｼ繝ｫ繝峨↓譬ｼ邏阪＠縲∵ｬ｡縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓縺昴・縺ｾ縺ｾ貂｡縺・
- `ImpulsiveOutput`, `ReflectiveOutput`, `IntrospectionMemo`縺ｯ蜈ｨ縺ｦ`raw_text: str`縺ｮ蜊倅ｸ繝輔ぅ繝ｼ繝ｫ繝峨↓邁｡邏蛹・
- `parse_markdown_sections()`縺ｯorchestrator.py縺九ｉ縺ｯ荳崎ｦ√→縺ｪ繧翫（mport蜑企勁貂医∩

### 6. Phase A-3/D: 荳崎ｦ√↑JSON萓晏ｭ倥・謗帝勁

**(a) 蠖灘・險ｭ險・*: Phase D 縺ｮ蜈ｨ5繧ｹ繝・ャ繝暦ｼ・orldContext, SupportingCharacters, NarrativeArc, ConflictIntensity, WeeklyEventWriter・峨♀繧医・ Phase A-3 縺ｮ蜈ｨ繧ｹ繝・ャ繝暦ｼ・pisodePlanner, 蛟句挨EpisodeWriterﾃ湧・峨ｒ `json_mode=True` 縺ｧJSON蜃ｺ蜉帙＆縺帙∝・邨先棡繧谷SON繝代・繧ｹ縺励※縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: Phase D Step1-4縺翫ｈ縺ｳA-3 Planner縺ｮ蜃ｺ蜉帙・谺｡縺ｮLLM縺ｸ縺ｮ繝励Ο繝ｳ繝励ヨ繧ｳ繝ｳ繝・く繧ｹ繝医→縺励※縺励°菴ｿ繧上ｌ縺壹∵ｩ滓｢ｰ逧・↑繝代・繧ｹ縺ｯ荳崎ｦ√□縺｣縺溘・nthropic API繧ｯ繝ｬ繧ｸ繝・ヨ譫ｯ貂・・Gemini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ迺ｰ蠅・ｸ九〒縲；emma 4 (31B)縺ｮJSON蜃ｺ蜉帙′閾ｴ蜻ｽ逧・↓荳榊ｮ牙ｮ壹〒113蝗槭・JSON繝代・繧ｹ螟ｱ謨励′逋ｺ逕溘＠縲√お繝斐た繝ｼ繝峨・繧､繝吶Φ繝医′蜈ｨ縺冗函謌舌＆繧後↑縺九▲縺溘よｹ譛ｬ蜴溷屏縺ｯ縲後・繝ｭ繝ｳ繝励ヨ縺ｨ縺励※貂｡縺吶□縺代・繝・・繧ｿ縺ｫJSON蜃ｺ蜉帙ｒ蠑ｷ蛻ｶ縺励※縺・◆縲阪％縺ｨ縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- Phase D Step1-4: `json_mode` 繧貞ｮ悟・謦､蟒・り・辟ｶ險隱槭ユ繧ｭ繧ｹ繝医〒蜃ｺ蜉帙＠縲√◎縺ｮ縺ｾ縺ｾ谺｡繧ｹ繝・ャ繝励・繧ｳ繝ｳ繝・く繧ｹ繝医↓貂｡縺・
- Phase D Step5 (WeeklyEventWriter): JSON邯ｭ謖・ｼ・4-28莉ｶ縺ｮEvent繝｢繝・Ν縺ｸ讖滓｢ｰ逧・ｼ邏阪′蠢・ｦ・ｼ・
- Phase A-3 Planner: 閾ｪ辟ｶ險隱槭ユ繧ｭ繧ｹ繝亥・蜉帙↓螟画峩
- Phase A-3 Writer: 蛟句挨荳ｦ蛻礼函謌舌°繧牙・繧ｨ繝斐た繝ｼ繝我ｸ諡ｬJSON逕滓・縺ｫ邨ｱ蜷茨ｼ・LM蜻ｼ縺ｳ蜃ｺ縺怜屓謨ｰ蜑頑ｸ・ 1+N 竊・2蝗橸ｼ・
- `llm_api.py`: 4谿ｵ髫弱ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ莉倥″`_extract_json()`繝倥Ν繝代・霑ｽ蜉縲Ａcall_llm()`縺ｫjson_mode螟ｱ謨玲凾縺ｮ閾ｪ蜍輔Μ繝医Λ繧､・域怙螟ｧ3蝗橸ｼ峨ｒ螳溯｣・
- draft繝励Ο繝輔ぃ繧､繝ｫ: `worker_tier`繧蛋gemini`縺ｫ邨ｱ荳・・emma 4縺ｯ螳悟・蟒・ｭ｢貂医∩・・
- **蛻､譁ｭ蝓ｺ貅・*: 縲後◎縺ｮ繝・・繧ｿ繧偵さ繝ｼ繝峨′讖滓｢ｰ逧・↓繝代・繧ｹ縺吶ｋ縺具ｼ溘杭es 竊・JSON縲¨o 竊・閾ｪ辟ｶ險隱・

### 7. Phase A-2 Worker 邏ｰ蛻・喧

**(a) 蠖灘・險ｭ險・*: MVP谿ｵ髫弱〒縺ｯ4縺､縺ｮ邨ｱ蜷・orker・域ｰ苓ｳｪ蜈ｨ驛ｨ縲∵ｧ譬ｼ蜈ｨ驛ｨ縲∝ｯｾ莉冶・ｪ咲衍縲∬ｦ冗ｯ・ｱ､・峨〒螳溯｡後・
**(b) 螟画峩繝ｻ譬ｹ諡**: v2 ﾂｧ6.4.2 縺ｧ15 Worker縺ｸ縺ｮ蛻・牡縺梧・遒ｺ縺ｫ隕丞ｮ壹ょ腰荳LLM縺・2繝代Λ繝｡繝ｼ繧ｿ繧剃ｸ蠎ｦ縺ｫ逕滓・縺吶ｋ縺ｨ繧ｳ繝ｳ繝・く繧ｹ繝郁ｲ闕ｷ縺ｧ蜩∬ｳｪ縺御ｽ惹ｸ九＠縲∽ｸ驛ｨ蜀咲函謌舌ｂ蝗ｰ髮｣縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: v10 ﾂｧ3.3縺ｮ繧ｫ繝・ざ繝ｪ蛻・｡橸ｼ・1-A4, B1-B5・峨↓豐ｿ縺｣縺ｦ10繝代Λ繝｡繝ｼ繧ｿWorker + 4隕冗ｯ・ｱ､Worker + 1繝ｫ繝ｼ繝ｫ繝吶・繧ｹ蟆主・縺ｮ險・5 Worker縺ｫ蛻・牡縲４tep 1(10荳ｦ蛻・ 竊・Step 2(4荳ｦ蛻・ 竊・Step 3(騾先ｬ｡) 縺ｮ3谿ｵ髫弱〒螳溯｡後・

### 8. 繝輔Ο繝ｳ繝医お繝ｳ繝臥憾諷狗ｮ｡逅・ package_name縺ｮ荳雋ｫ諤ｧ

**(a) 蠖灘・險ｭ險・*: `currentPackage._package_name` 縺ｯ螻･豁ｴ隱ｭ縺ｿ霎ｼ縺ｿ譎ゑｼ・loadPackage()`・峨・縺ｿ縺ｧ險ｭ螳壹＆繧後※縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 譁ｰ隕上く繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・螳御ｺ・凾・・onGenerationComplete()`・峨〒縺ｯ `_package_name` 縺後そ繝・ヨ縺輔ｌ縺壹∫峩蠕後・譌･險倥す繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ髢句ｧ区凾縺ｫ `'unknown'` 縺後ヰ繝・け繧ｨ繝ｳ繝峨↓騾∽ｿ｡縺輔ｌ縲後ヱ繝・こ繝ｼ繧ｸ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ縲阪お繝ｩ繝ｼ縺檎匱逕溘＠縺ｦ縺・◆縲ょｱ･豁ｴ邨檎罰縺ｧ縺ｮ縺ｿ譌･險倡函謌舌′蜍穂ｽ懊☆繧狗憾諷九□縺｣縺溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: `onGenerationComplete()` 蜀・〒 `currentPackage._package_name = result.package_name` 繧定ｨｭ螳壹＠縲∫函謌舌ヵ繝ｭ繝ｼ繝ｻ螻･豁ｴ繝輔Ο繝ｼ荳｡譁ｹ縺ｧ荳雋ｫ縺励※ `_package_name` 縺御ｿ晄戟縺輔ｌ繧九ｈ縺・ｿｮ豁｣縲・

### 9. 陦悟虚豎ｺ螳壹お繝ｼ繧ｸ繧ｧ繝ｳ繝・竊・蜃ｺ譚･莠句捉霎ｺ諠・ｱ邨ｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ騾ｲ蛹・

**(a) 蠖灘・險ｭ險・*: 陦悟虚豎ｺ螳壹お繝ｼ繧ｸ繧ｧ繝ｳ繝・`_integration`)縺ｨ諠・勹謠丞・繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・`_scene_narration`)繧貞・髮｢縲らｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医・陦悟虚豎ｺ螳壹・縺ｿ繧呈球蠖薙＠縲∝挨騾斐・諠・勹謠丞・繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′蝣ｴ髱｢繧呈緒蜀吶＠縺ｦ縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 陦悟虚豎ｺ螳壹→諠・勹謠丞・縺ｯ蟇・磁縺ｫ髢｢騾｣縺励※縺翫ｊ縲∝・髮｢縺吶ｋ縺ｨ陦悟虚縺ｮ譁・ц縺ｨ蝣ｴ髱｢謠丞・縺ｮ髢薙↓荵夜屬縺檎函縺倥※縺・◆縲ゅ∪縺溘∝・譚･莠九・蜻ｨ霎ｺ諠・ｱ・亥ｴ謇繝ｻ譎る俣繝ｻ髮ｰ蝗ｲ豌暦ｼ峨ｄ陦悟虚蠕後・邨先棡繧剃ｸ雋ｫ縺励◆繧ｹ繝医・繝ｪ繝ｼ縺ｨ縺励※邨ｱ蜷医☆繧句ｱ､縺御ｸ榊惠縺縺｣縺溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 縲悟・譚･莠句捉霎ｺ諠・ｱ邨ｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医阪→縺励※邨ｱ蜷医・蝗槭・Agentic繝ｫ繝ｼ繝励〒陦悟虚豎ｺ螳・+ 蜻ｨ霎ｺ諠・ｱ + 諠・勹謠丞・ + 蠕梧律隴・+ 荳ｻ莠ｺ蜈ｬ縺ｮ蜍輔″ + 繧ｹ繝医・繝ｪ繝ｼ繧ｻ繧ｰ繝｡繝ｳ繝医ｒ荳諡ｬ逕滓・縲ＡIntegrationOutput`繝｢繝・Ν繧・繝輔ぅ繝ｼ繝ｫ繝画僑蠑ｵ・・surrounding_context`, `action_consequences`, `scene_description`, `aftermath`, `protagonist_movement`, `story_segment`・峨・

### 10. 諢滓ュ蠑ｷ蠎ｦ縺ｫ繧医ｋ逅・ｧ繝舌う繝代せ繝｡繧ｫ繝九ぜ繝

**(a) 蠖灘・險ｭ險・*: Impulsive Agent縺ｨReflective Agent繧貞ｸｸ縺ｫ荳ｦ蛻怜ｮ溯｡後＠縲∫ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医′荳｡譁ｹ縺ｮ蜃ｺ蜉帙ｒ邨ｱ蜷医＠縺ｦ縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 迴ｾ螳溘・莠ｺ髢灘ｿ・炊縺ｧ縺ｯ縲∵─諠・′讌ｵ遶ｯ縺ｫ鬮倥∪縺｣縺溽憾諷具ｼ医ヱ繝九ャ繧ｯ縲∵ｿ諤偵∵ｭ灘万縺ｮ邨ｶ鬆らｭ会ｼ峨〒縺ｯ逅・ｧ逧・愛譁ｭ縺御ｻ句・縺ｧ縺阪↑縺・ゆｸｦ蛻怜ｮ溯｡後・險育ｮ怜柑邇・・濶ｯ縺・′縲∝ｿ・炊蟄ｦ逧・Μ繧｢繝ｪ繝・ぅ縺ｫ谺縺代※縺・◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: Impulsive Agent螳溯｡悟ｾ後↓霆ｽ驥上↑諢滓ュ蠑ｷ蠎ｦ蛻､螳壹せ繝・ャ繝暦ｼ・_evaluate_emotion_intensity`, tier=gemini, JSON蜃ｺ蜉幢ｼ峨ｒ霑ｽ蜉縲Ａintensity=high`縺ｮ蝣ｴ蜷医ヽeflective Agent繧貞ｮ悟・繧ｹ繧ｭ繝・・縺励∫ｩｺ縺ｮReflectiveOutput繧堤ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺吶らｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝亥・縺ｯ逅・ｧ蜿ら・縺ｪ縺励・譌ｨ繧偵す繧ｹ繝・Β繝励Ο繝ｳ繝励ヨ縺ｫ譏手ｨ倥・

### 11. 4縺､縺ｮ蛟句挨繝√ぉ繝・けAI・域紛蜷域ｧ讀懆ｨｼ繝ｬ繧､繝､繝ｼ・・

**(a) 蠖灘・險ｭ險・*: 蜃ｺ蜉帶､懆ｨｼ縺ｯ`OutputVerificationAgent`・医ヱ繝ｩ繝｡繝ｼ繧ｿ蜷肴ｼ乗ｴｩ繝√ぉ繝・け・峨・縺ｿ縲り｡悟虚繝ｻ譌･險倥′繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ險ｭ螳壹↓蠢螳溘°縺ｮ讀懆ｨｼ縺ｯ證鈴ｻ咏噪・・LM縺ｮ繝励Ο繝ｳ繝励ヨ萓晏ｭ假ｼ峨・
**(b) 螟画峩繝ｻ譬ｹ諡**: LLM縺ｯ繝励Ο繝ｳ繝励ヨ縺縺代〒縺ｯ險ｭ螳壼ｿ螳溷ｺｦ繧剃ｿ晁ｨｼ縺ｧ縺阪↑縺・ら音縺ｫ髟ｷ縺Бgentic繝ｫ繝ｼ繝怜・縺ｧ縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ豌苓ｳｪ繧・ｧ譬ｼ縺九ｉ騾ｸ閼ｱ縺励◆陦悟虚縺檎函謌舌＆繧後ｋ繧ｱ繝ｼ繧ｹ縺悟ｭ伜惠縺励◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 4縺､縺ｮ迢ｬ遶九メ繧ｧ繝・き繝ｼ繧蛋checkers.py`縺ｫ螳溯｣・＠縲∫ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙→譌･險伜・蜉帙・2邂・園縺ｧ荳ｦ蛻怜ｮ溯｡・
  - `ProfileChecker`: 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ・亥錐蜑阪・閨ｷ讌ｭ繝ｻ逕滓ｴｻ讒伜ｼ上・莠ｺ髢馴未菫ゑｼ峨→縺ｮ謨ｴ蜷域ｧ
  - `TemperamentChecker`: 豢ｻ諤ｧ蛹匁ｸ医∩豌苓ｳｪ繝代Λ繝｡繝ｼ繧ｿ・・loninger繝｢繝・Ν・峨→縺ｮ謨ｴ蜷域ｧ
  - `PersonalityChecker`: 豢ｻ諤ｧ蛹匁ｸ医∩諤ｧ譬ｼ繝代Λ繝｡繝ｼ繧ｿ・・ig Five/HEXACO・峨→縺ｮ謨ｴ蜷域ｧ
  - `ValuesChecker`: 萓｡蛟､隕ｳ・・chwartz繝ｻMFT繝ｻ逅・Φ閾ｪ蟾ｱ繝ｻ鄒ｩ蜍呵・蟾ｱ・峨→縺ｮ謨ｴ蜷域ｧ
  蜈ｨ繝√ぉ繝・き繝ｼ縺ｯ陬乗婿繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ磯國阡ｽ蜴溷援蟇ｾ雎｡螟厄ｼ峨》ier=gemini・井ｽ弱さ繧ｹ繝茨ｼ峨《everity=major縺ｮ縺ｿ繝ｭ繧ｰ隴ｦ蜻翫・

### 12. key memory縺ｮ遏ｭ譛溯ｨ俶・縺九ｉ縺ｮ蛻・屬

**(a) 蠖灘・險ｭ險・*: `ShortTermMemoryDB.key_memories: list[KeyMemory]`縺ｨ縺励※繧､繝ｳ繝｡繝｢繝ｪ縺ｮ遏ｭ譛溯ｨ俶・DB縺ｮ荳驛ｨ縺ｨ縺励※邂｡逅・・
**(b) 螟画峩繝ｻ譬ｹ諡**: key memory縺ｯ谿ｵ髫主悸邵ｮ縺ｮ蟇ｾ雎｡螟厄ｼ・譌･髢薙ヵ繝ｫ菫晄戟・峨〒縺ゅｊ縲∫洒譛溯ｨ俶・縺ｮ騾壼ｸｸ鬆伜沺・域ｮｵ髫主悸邵ｮ譁ｹ蠑擾ｼ峨→縺ｯ繝ｩ繧､繝輔し繧､繧ｯ繝ｫ縺梧ｹ譛ｬ逧・↓逡ｰ縺ｪ繧九ょ酔荳繝・・繧ｿ讒矩縺ｫ豺ｷ蝨ｨ縺輔○繧九→邂｡逅・ｸ翫・隍・尅縺輔′蠅励☆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: `KeyMemoryStore`繧ｯ繝ｩ繧ｹ繧呈眠險ｭ縺励～key_memories/day_01.json`蠖｢蠑上〒蛟句挨繝輔ぃ繧､繝ｫ縺ｨ縺励※豌ｸ邯壼喧縲ＡShortTermMemoryDB`縺九ｉ縺ｯ`key_memories`繝輔ぅ繝ｼ繝ｫ繝峨ｒ蜑企勁縲Ａ_build_memory_context()`縺ｧ縺ｯ`KeyMemoryStore.load_all()`縺ｧ隱ｭ縺ｿ霎ｼ縺ｿ縲∝ｾ捺擂縺ｨ蜷後§繧ｳ繝ｳ繝・く繧ｹ繝亥ｽ｢蠑上ｒ邯ｭ謖√・

### 13. Gemini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｮ螟壼ｱ､髦ｲ蠕｡蛹・

**(a) 蠖灘・險ｭ險・*: `call_llm_agentic`(Claude)螟ｱ謨玲凾縺ｫ`call_llm_agentic_gemini`縺ｸ蜊伜ｱ､繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縲・emini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ閾ｪ菴薙′螟ｱ謨励＠縺溷ｴ蜷医・繝上Φ繝峨Μ繝ｳ繧ｰ縺ｯ譛ｪ螳溯｣・Ａ_introspection()`縺ｯtier="sonnet"繧偵ワ繝ｼ繝峨さ繝ｼ繝峨・
**(b) 螟画峩繝ｻ譬ｹ諡**: Claude繧ｯ繝ｬ繧ｸ繝・ヨ譫ｯ貂・凾縺ｫGemini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺悟ｮ溯｡後＆繧後※繧ゅ；emini蛛ｴ縺ｧ繧・PI髫懷ｮｳ繧・・繝ｭ繝医さ繝ｫ繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺・ｋ縲ゅヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ縺檎┌髦ｲ蛯吶□縺ｨ萓句､悶′譌･險倡函謌仙・菴薙ｒ繧ｯ繝ｩ繝・す繝･縺輔○縺ｦ縺・◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 3螻､縺ｮ髦ｲ蠕｡繧貞ｮ溯｣・
  1. Claude try/except 竊・Gemini fallback try/except 竊・繝・ヵ繧ｩ繝ｫ繝亥､繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ
  2. end-of-day蜃ｦ逅・・蜷・せ繝・ャ繝暦ｼ亥・逵√・譌･險倥・key memory繝ｻ鄙梧律莠亥ｮ夲ｼ峨↓蛟句挨try/except霑ｽ蜉
  3. `_introspection()`縺ｮtier繧蛋self.profile.worker_tier`縺ｫ螟画峩・医・繝ｭ繝輔ぃ繧､繝ｫ騾｣蜍包ｼ・

### 14. Web繧ｵ繝ｼ繝√♀繧医・MD繝輔ぃ繧､繝ｫ菫晏ｭ倥Ν繝ｼ繝・ぅ繝ｳ繧ｰ

**(a) 蠖灘・險ｭ險・*: 繝・・繧ｿ蜃ｺ蜉帙・JSON繧ｪ繝悶ず繧ｧ繧ｯ繝医ｄ繧､繝ｳ繝｡繝｢繝ｪ菫晄戟縺ｫ逡吶∪縺｣縺ｦ縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 荳也阜隕ｳ縺ｫ豺ｱ縺ｿ繧呈戟縺溘○繧九Μ繧ｵ繝ｼ繝∬・蜉帙→縲∽ｺｺ髢灘庄隱ｭ縺ｪMD豌ｸ邯壼喧縺悟ｿ・ｦ√・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**: 
- Creative Director縺ｫ `search_web` + `file_read`・・ackend/reference/蜿ら・・峨・2繝・・繝ｫ繧剃ｻ倅ｸ弱・
- `md_storage.py` 縺ｧ蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥・蜉帙・繝繝ｼ繝牙､蛾・繝ｻ蜀・怐繝ｻ譌･險倥・key memory繧貞性繧螳悟・縺ｪDay_N.md繧定・蜍慕函謌舌・

### 15. Perceiver + Impulsive Agent邨ｱ蜷・+ 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝域僑蜈・

**(a) 蠖灘・險ｭ險・*: Perceiver(ﾂｧ4.3, 遏･隕壹ヵ繧｣繝ｫ繧ｿ繝ｼ)縺ｨImpulsive Agent(ﾂｧ4.6 Step 1, 陦晏虚逧・渚蠢・繧堤峡遶九＠縺・縺､縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医→縺励※鬆・ｬ｡螳溯｡後１erceiver縺ｯ3繝輔ぅ繝ｼ繝ｫ繝牙・蜉幢ｼ育樟雎｡逧・ｨ倩ｿｰ繝ｻ蜿榊ｰ・─諠・・閾ｪ蜍墓ｳｨ諢擾ｼ峨！mpulsive縺ｯ3繝輔ぅ繝ｼ繝ｫ繝牙・蜉幢ｼ郁｡晏虚逧・渚蠢懊・霄ｫ菴捺─隕壹・陦悟虚蛯ｾ蜷托ｼ峨１erceiver縺ｫ縺ｯ繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ(400譁・ｭ怜宛髯・縺ｮ縺ｿ貂｡縺励∫ｵ碁ｨ泥B繝ｻkey memory繝ｻ荳也阜險ｭ螳壹・蜻ｨ蝗ｲ莠ｺ迚ｩ縺ｯ譛ｪ蜷梧｢ｱ縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: Perceiver縺ｮ繝励Ο繝ｳ繝励ヨ繧定｡晏虚邉ｻ蟇・ｊ縺ｫ謾ｹ螟峨＠縺溽ｵ先棡縲！mpulsive Agent縺ｨ蠖ｹ蜑ｲ縺悟ｮ悟・縺ｫ驥崎､・ゅ∪縺溘￣erceiver蜃ｺ蜉帙↓縲檎函縺倥◆陦晏虚縲阪そ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉縺励◆縺訓ydantic繝｢繝・Ν縺ｫ蟇ｾ蠢懊ヵ繧｣繝ｼ繝ｫ繝峨′縺ｪ縺丞・蜉帙′謐ｨ縺ｦ繧峨ｌ縺ｦ縺・◆縲ゅお繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝医′荳崎ｶｳ縺励※縺翫ｊ縲∽ｸ也阜險ｭ螳壹・蜻ｨ蝗ｲ莠ｺ迚ｩ繝ｻ邨碁ｨ泥B繝ｻkey memory縺ｪ縺励〒縺ｯ譁・ц縺ｫ荵上＠縺・・蜉帙↓縺ｪ縺｣縺ｦ縺・◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `_perceiver()`繧貞ｮ悟・蜑企勁縺輿_impulsive()`縺ｫ邨ｱ蜷医ょ・逅・ヵ繝ｭ繝ｼ: `蜍慕噪豢ｻ諤ｧ蛹・竊・陦晏虚邉ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・竊・諢滓ュ蠑ｷ蠎ｦ蛻､螳・竊・Reflective 竊・讀懆ｨｼ 竊・邨ｱ蜷・
  - `PerceiverOutput`繧貞炎髯､縲ＡEventPackage`縺九ｉ`perceiver_output`繝輔ぅ繝ｼ繝ｫ繝峨ｂ蜑企勁
  - 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ郁｡晏虚邉ｻ繝ｻReflective繝ｻ邨ｱ蜷医・蜀・怐繝ｻ譌･險假ｼ峨↓莉･荳九ｒ蜷梧｢ｱ:
    - 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ・亥・譁・・00譁・ｭ怜宛髯先彫蟒・ｼ・
    - 荳也阜險ｭ螳夲ｼ・_build_world_context()` 譁ｰ險ｭ・・
    - 蜻ｨ蝗ｲ莠ｺ迚ｩ・・_build_supporting_characters_context()` 譁ｰ險ｭ・・
    - 邨碁ｨ泥B・郁・莨晉噪繧ｨ繝斐た繝ｼ繝会ｼ・
    - key memory + 騾壼ｸｸ險俶・
  - 讀懆ｨｼ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医ｂPerceiver荳崎ｦ√・raw text繝吶・繧ｹ縺ｫ蛻ｷ譁ｰ

### 16. 繧ｹ繝医Ξ繝ｼ繧ｸ邨ｱ荳縺ｨ迥ｶ諷区ｰｸ邯壼喧・・hortTermMemoryDB繝ｻMoodState・・

**(a) 蠖灘・險ｭ險・*: `_finalize_character_generation()`縺ｯ`{繧ｭ繝｣繝ｩ蜷閤_{timestamp}`蠖｢蠑上〒譁ｰ縺励＞繝・ぅ繝ｬ繧ｯ繝医Μ繧剃ｽ懈・縺励※package.json縺ｮ縺ｿ繧剃ｿ晏ｭ倥ら函謌蝉ｸｭ縺ｮ繝・・繧ｿ・・heckpoint, profile, logs・峨・`{繧ｭ繝｣繝ｩ蜷閤/`縺ｫ菫晏ｭ倥らｵ先棡縺ｨ縺励※1繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ繝・・繧ｿ縺・繝・ぅ繝ｬ繧ｯ繝医Μ縺ｫ蛻・｣ゅＡShortTermMemoryDB`・域ｮｵ髫主悸邵ｮ險俶・・峨→`MoodState`・・AD 3谺｡蜈・Β繝ｼ繝会ｼ峨・繝｡繝｢繝ｪ荳翫・縺ｿ縺ｧ縲√・繝ｭ繧ｻ繧ｹ邨ゆｺ・凾縺ｫ豸亥､ｱ縺励※縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 1繧ｭ繝｣繝ｩ=1繝・ぅ繝ｬ繧ｯ繝医Μ縺ｮ蜴溷援縺檎ｴ繧後※縺・◆縲ゅ∪縺溘∵律谺｡繝ｫ繝ｼ繝励′騾比ｸｭ縺ｧ螟ｱ謨励＠縺溷ｴ蜷医∬ｨ俶・縺ｨ繝繝ｼ繝峨・騾ｲ陦檎憾諷九′蠕ｩ蜈・ｸ榊庄閭ｽ縺ｧ縲．ay 1縺九ｉ縺ｮ蜈ｨ蜀榊ｮ溯｡後′蠢・ｦ√□縺｣縺溘・eyMemoryStore縺ｯ譌｢縺ｫ蛟句挨繝輔ぃ繧､繝ｫ豌ｸ邯壼喧縺輔ｌ縺ｦ縺・◆縺後ヾhortTermMemoryDB縺ｨMoodState縺ｯ豌ｸ邯壼喧螻､縺梧ｬ關ｽ縺励※縺・◆縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `_finalize_character_generation()`繧蛋safe_name(char_name)`繝吶・繧ｹ縺ｮ邨ｱ荳繝代せ縺ｫ螟画峩・医ち繧､繝繧ｹ繧ｿ繝ｳ繝嶺ｻ倥″繝・ぅ繝ｬ繧ｯ繝医Μ蟒・ｭ｢・・
  - `ShortTermMemoryStore`: `short_term_memory/day_NN.json`蠖｢蠑上〒險俶・蝨ｧ邵ｮ螳御ｺ・ｾ後↓繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ菫晏ｭ・
  - `MoodStateStore`: `mood_states/day_NN.json`蠖｢蠑上〒carry-over螳御ｺ・ｾ後↓daily_mood + carry_over_mood繧剃ｿ晏ｭ・
  - DailyLoopOrchestrator蛻晄悄蛹匁凾縺ｫ譛譁ｰ繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ繧定・蜍輔Ο繝ｼ繝峨＠縲∽ｿ晏ｭ俶ｸ医∩譌･縺ｮ鄙梧律縺九ｉ蜀埼幕
  - KeyMemoryStore縺ｨ蜷御ｸ縺ｮ繝輔ぃ繧､繝ｫ邂｡逅・ヱ繧ｿ繝ｼ繝ｳ・域律蜊倅ｽ阪ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・∵怙譁ｰ繝輔ぃ繧､繝ｫ=迴ｾ蝨ｨ迥ｶ諷具ｼ・

### 17. Gemma 4螳悟・蟒・ｭ｢縺ｨGemini 2.5 Pro譛菴弱ユ繧｣繧｢邨ｱ荳

**(a) 蠖灘・險ｭ險・*: 譛菴弱さ繧ｹ繝医ユ繧｣繧｢縺ｨ縺励※Gemma 4 (gemma-4-31b-it)繧蛋tier="gemma"`縺ｧ菴ｿ逕ｨ縲Ａcall_gemma()`髢｢謨ｰ縺隈emma 4縺ｨGemini 2.5 Pro縺ｮ荳｡譁ｹ繧偵Ν繝ｼ繝・ぅ繝ｳ繧ｰ縺励※縺・◆縲５okenTracker縺ｫgemma蟆ら畑繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ繧剃ｿ晄戟縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: Gemma 4縺ｯJSON蜃ｺ蜉帙′閾ｴ蜻ｽ逧・↓荳榊ｮ牙ｮ夲ｼ・13蝗槭・繝代・繧ｹ螟ｱ謨暦ｼ峨〒譌｢縺ｫ螳溯ｳｪ菴ｿ逕ｨ蛛懈ｭ｢迥ｶ諷九□縺｣縺溘ゅさ繝ｼ繝峨・繝ｼ繧ｹ縺ｫGemma 4繝代せ縺梧ｮ句ｭ倥☆繧九％縺ｨ縺ｧ豺ｷ荵ｱ縺ｨ菫晏ｮ郁ｲ諡・′逋ｺ逕溘よ怙菴弱ユ繧｣繧｢縺ｯGemini 2.5 Pro縺ｧ蜊∝・縺ｪ蜩∬ｳｪ繧堤｢ｺ菫昴〒縺阪ｋ縺溘ａ縲；emma 4繧貞ｮ悟・蟒・ｭ｢縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `LLMModels.GEMMA_4_MOE`螳壽焚繧貞炎髯､縲ゅユ繧｣繧｢菴鍋ｳｻ縺ｯ3谿ｵ髫趣ｼ・pus / sonnet / gemini・峨↓邨ｱ荳
  - `call_gemma()` 竊・`call_google_ai()`縺ｫ繝ｪ繝阪・繝縲√ョ繝輔か繝ｫ繝医Δ繝・Ν繧竪emini 2.5 Pro縺ｫ螟画峩
  - `_call_llm_once()`縺九ｉ`tier=="gemma"`繝悶Ο繝・け繧貞ｮ悟・蜑企勁
  - 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・Worker繝ｻ繝√ぉ繝・き繝ｼ縺ｮ`tier="gemma"`繝・ヵ繧ｩ繝ｫ繝医ｒ`tier="gemini"`縺ｫ荳諡ｬ螟画峩
  - TokenTracker縺九ｉgemma蟆ら畑繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ繧貞炎髯､縺励“emini繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ縺ｫ邨ｱ蜷・

### 18. 繝代Λ繝｡繝ｼ繧ｿ蜍慕噪豢ｻ諤ｧ蛹悶お繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繝ｻ邨碁ｨ泥B蜈･蜉幄ｿｽ蜉

**(a) 蠖灘・險ｭ險・*: 豢ｻ諤ｧ蛹悶お繝ｼ繧ｸ繧ｧ繝ｳ繝医・蜈･蜉帙・縲悟・52繝代Λ繝｡繝ｼ繧ｿ繧ｫ繧ｿ繝ｭ繧ｰ・域焚蛟､蜈･繧奇ｼ・ 迴ｾ蝨ｨ繝繝ｼ繝・+ 繧ｷ繝ｼ繝ｳ險倩ｿｰ縲阪・縺ｿ縲ゅ・繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ縺ｨ閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝峨・縲悟虚逧・ｴｻ諤ｧ蛹悶・蟇ｾ雎｡螟悶阪→縺励※迢ｬ遶句盾辣ｧ縺輔ｌ繧玖ｨｭ險医□縺｣縺溘ゅ∪縺溘》ier縺形"gemma"`縺ｫ繝上・繝峨さ繝ｼ繝峨＆繧後√・繝ｭ繝輔ぃ繧､繝ｫ騾｣蜍輔＠縺ｦ縺・↑縺九▲縺溘・
**(b) 螟画峩繝ｻ譬ｹ諡**: 繝代Λ繝｡繝ｼ繧ｿ縺ｮ豢ｻ諤ｧ蛹門愛譁ｭ縺ｫ縺ｯ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ閭梧勹縺御ｸ榊庄谺縲ゆｾ九∴縺ｰ縲瑚・蝣ｴ縺ｮ譏・ｲ繧呈妙繧峨ｌ縺溘阪す繝ｼ繝ｳ縺ｧ縺ｯ縲√く繝｣繝ｩ縺ｮ螟｢縺ｮ繧ｿ繧､繝繝ｩ繧､繝ｳ繝ｻ莠ｺ髢馴未菫ゅ・驕主悉縺ｮ謖ｫ謚倅ｽ馴ｨ薙ｒ遏･繧峨↑縺代ｌ縺ｰ縲√←縺ｮ繝代Λ繝｡繝ｼ繧ｿ・磯＃謌仙ｿ怜髄縲∬・蟆頑─諠・∵偵ｊ遲会ｼ峨′逋ｺ轣ｫ縺吶∋縺阪°豁｣遒ｺ縺ｫ蛻､譁ｭ縺ｧ縺阪↑縺・・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `DynamicActivationAgent.__init__()`縺ｫ`macro_profile`縺ｨ`episodes`繧定ｿｽ蜉
  - `_build_macro_summary()`: 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繧偵さ繝ｳ繝代け繝郁ｦ∫ｴ・ｼ亥錐蜑阪・閨ｷ讌ｭ繝ｻ萓｡蛟､隕ｳ繧ｳ繧｢繝ｻ螟｢繝ｻ莠ｺ髢馴未菫ゑｼ・
  - `_build_episodes_summary()`: 閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝峨ｒ`[譎よ悄/繧ｫ繝・ざ繝ｪ] 隕∫ｴ・00蟄輿蠖｢蠑上〒蝨ｧ邵ｮ
  - `activate()`縺ｮLLM繝励Ο繝ｳ繝励ヨ縺ｫ`縲舌く繝｣繝ｩ繧ｯ繧ｿ繝ｼ閭梧勹縲疏縺ｨ`縲占・莨晉噪繧ｨ繝斐た繝ｼ繝峨疏繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉
  - 繧ｷ繧ｹ繝・Β繝励Ο繝ｳ繝励ヨ縺ｮ謚ｽ蜃ｺ繝ｫ繝ｼ繝ｫ縺ｫ縲後く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ閭梧勹繝ｻ邨梧ｭｴ繝ｻ莠ｺ髢馴未菫ゅｒ閠・・縲阪☆繧区葎繧呈・險・
  - tier 繝舌げ菫ｮ豁｣: 繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ縺九ｉ`tier=self.profile.worker_tier`繧呈ｸ｡縺吶ｈ縺・､画峩

### 19. Day1譌･險倥・荳也阜隕ｳ蟆主・繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繝ｻ譌･險俶枚蟄玲焚邨ｱ荳繝ｻ繧､繝吶Φ繝域焚蜑頑ｸ・

**(a) 蠖灘・險ｭ險・*: 譌･險倡函謌舌・蜈ｨ譌･蜷御ｸ繝励Ο繝ｳ繝励ヨ・・00-600蟄励∽ｸ也阜隕ｳ邏ｹ莉九↑縺暦ｼ峨１hase D縺ｮ繧､繝吶Φ繝域焚縺ｯ蜷・律4-6莉ｶ・亥粋險・8-42莉ｶ・峨らｿ梧律莠亥ｮ壹・stage2謨ｴ蜷域ｧ繝√ぉ繝・け縺君one霑泌唆譎ゅ・繧､繝吶Φ繝域悴謖ｿ蜈･縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: Day1縺ｯ迚ｩ隱槭・蜈･蜿｣縺ｧ縺ゅｊ縲∬ｪｭ閠・′險ｭ螳壹・荳也阜隕ｳ繧堤炊隗｣縺吶ｋ縺溘ａ縺ｮ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ縺御ｸ榊庄谺縺縺｣縺溘よ律險俶枚蟄玲焚縺ｯ邏・00蟄暦ｼ・00蟄嶺ｻ･荳具ｼ峨↓邨ｱ荳縺励∬ｪｭ縺ｿ繧・☆縺輔ｒ蜆ｪ蜈医ゅう繝吶Φ繝域焚縺ｯ2-4莉ｶ縺ｫ蜑頑ｸ帙＠縲∝推繧､繝吶Φ繝医・謠丞・蟇・ｺｦ縺ｨ蜃ｦ逅・柑邇・ｒ蜷台ｸ翫らｿ梧律莠亥ｮ壹′謨ｴ蜷域ｧ繝√ぉ繝・け螟ｱ謨励〒繧､繝吶Φ繝亥喧縺輔ｌ縺ｪ縺・こ繝ｼ繧ｹ繧よ賜髯､縲・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `_generate_diary()`縺ｫDay1譚｡莉ｶ蛻・ｲ舌ｒ霑ｽ蜉: `day == 1`縺ｮ蝣ｴ蜷医《ystem_prompt縺ｫ荳也阜隕ｳ繝ｻ閾ｪ蟾ｱ邏ｹ莉九・迚ｹ蛻･謖・､ｺ繧剃ｻ伜刈・井ｸｻ莠ｺ蜈ｬ縺ｮ螢ｰ縺ｧ閾ｪ辟ｶ縺ｫ郢斐ｊ霎ｼ繧蠖｢蠑擾ｼ・
  - 譌･險俶枚蟄玲焚繧貞・譌･邨ｱ荳: 繝励Ο繝ｳ繝励ヨ縲檎ｴ・00蟄暦ｼ・00蟄嶺ｻ･荳具ｼ峨阪‥iary_critic縺ｮ荳企剞繧・00竊・00縺ｫ菫ｮ豁｣
  - Phase D繝励Ο繝ｳ繝励ヨ繧偵悟推譌･2-4莉ｶ縲∝粋險・4-28莉ｶ縲阪↓螟画峩
  - 鄙梧律莠亥ｮ壹↓繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ螳溯｣・ stage2縺君one譎ゅ↓plans[0]縺九ｉ逶ｴ謗･Event逕滓・・・ource: "protagonist_plan"・・
  - 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯEvent縺ｮ`time_slot`縺ｯpreferred_time縺梧怏蜉ｹ縺ｪ繧ｹ繝ｭ繝・ヨ蜷阪↑繧峨◎縺ｮ縺ｾ縺ｾ謗｡逕ｨ縲∽ｸ肴・縺ｪ繧・afternoon"

### 20. VoiceFingerprint 竊・LinguisticExpression・郁ｨ隱樒噪陦ｨ迴ｾ譁ｹ豕輔・迢ｬ遶句喧・・

**(a) 蠖灘・險ｭ險・*: 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ蝟九ｊ譁ｹ繝ｻ譁・ｽ捺ュ蝣ｱ縺ｯ`MacroProfile.voice_fingerprint`・・oiceFingerprint・峨→縺励※繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ蜀・↓蝓九ａ霎ｼ縺ｿ縲４tep 2縺ｮ6荳ｦ蛻邑orker縺ｮ1縺､・・oiceWorker・峨′`concept_package + basic_info`縺ｮ縺ｿ縺九ｉ逕滓・縺励※縺・◆縲ょ・蜉帙・讒矩蛹悶＆繧後◆謚陦薙ヵ繧｣繝ｼ繝ｫ繝会ｼ井ｸ莠ｺ遘ｰ繝ｻ蜿｣逋悶・譁・忰陦ｨ迴ｾ繝ｻ驕ｿ縺代ｋ隱槫ｽ咏ｭ会ｼ峨・縺ｿ縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: VoiceFingerprint 縺ｯ蜈ｷ菴鍋噪縺ｪ迚ｹ蠕ｴ繝ｪ繧ｹ繝医↓逡吶∪繧翫√後％縺ｮ莠ｺ縺ｯ縺ｩ繧薙↑髮ｰ蝗ｲ豌励〒蝟九ｋ縺九阪→縺・≧謚ｽ雎｡逧・↑繧､繝｡繝ｼ繧ｸ繧・√後％縺ｮ莠ｺ縺ｮ譌･險倥・縺ｩ繧薙↑遨ｺ豌玲─縺後≠繧九°縲阪→縺・≧繝医・繝ｳ繝ｻ讒区・蛯ｾ蜷代′谺關ｽ縺励※縺・◆縲ゅ∪縺溘∫函謌先凾縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝医′荳榊香蛻・ｼ・oncept+basic_info縺ｮ縺ｿ・峨〒縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ遉ｾ莨夂噪遶句ｴ繝ｻ萓｡蛟､隕ｳ繝ｻ遘伜ｯ・・莠ｺ髢馴未菫ゅ′蝟九ｊ譁ｹ縺ｫ蜿肴丐縺輔ｌ縺ｦ縺・↑縺九▲縺溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `LinguisticExpression`繧辰haracterPackage縺ｮ繝医ャ繝励Ξ繝吶Ν迢ｬ遶九ヵ繧｣繝ｼ繝ｫ繝峨→縺励※譁ｰ險ｭ
  - `SpeechCharacteristics`: 譌｢蟄老oiceFingerprint(concrete_features) + abstract_feel(謚ｽ雎｡逧・峅蝗ｲ豌・ + conversation_style + emotional_expression_tendency
  - `DiaryWritingAtmosphere`: tone + structure_tendency + introspection_depth + what_gets_written + what_gets_omitted + raw_atmosphere_description
  - Phase A-1縺ｮ螳溯｡後ヵ繝ｭ繝ｼ: Step 2縺九ｉVoiceWorker繧帝勁蜴ｻ・・竊・荳ｦ蛻暦ｼ峨ヾtep 4(RelationshipNetwork)縺ｮ蠕後↓Step 5縺ｨ縺励※蜈ｨWorker邨先棡繧偵さ繝ｳ繝・く繧ｹ繝医↓謖√▽LinguisticExpressionWorker繧帝・ｬ｡螳溯｡・
  - `PhaseA1Result`繝・・繧ｿ繧ｯ繝ｩ繧ｹ縺ｧ`MacroProfile + LinguisticExpression`繧偵そ繝・ヨ霑泌唆
  - **繝・・繧ｿ繝輔Ο繝ｼ蛻ｶ邏・*: LinguisticExpression縺ｯ譌･險倡函謌舌・繝ｭ繝ｳ繝励ヨ縺ｫ縺ｮ縺ｿ豕ｨ蜈･縲１hase A-2/A-3/D縺ｫ縺ｯ荳蛻・ｸ｡縺輔↑縺・
  - `MacroProfile.voice_fingerprint`縺ｯ蠕梧婿莠呈鋤縺ｮ縺溘ａ谿句ｭ假ｼ・oncrete_features縺九ｉ繧ｳ繝斐・・・
  - Daily Loop: `_build_voice_context()`繧呈僑蠑ｵ縺励∥bstract_feel + diary_writing_atmosphere蜈ｨ繝輔ぅ繝ｼ繝ｫ繝峨ｒ譌･險倡函謌舌・繝ｭ繝ｳ繝励ヨ縺ｫ豕ｨ蜈･

### 21. 繧ｨ繝斐た繝ｼ繝・繧､繝吶Φ繝育函謌舌・繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け蛹悶→2螻､閾ｪ蟾ｱ謇ｹ蛻､繝｡繧ｫ繝九ぜ繝

**(a) 蠖灘・險ｭ險・*: Phase A-3・医お繝斐た繝ｼ繝臥函謌撰ｼ峨・Planner縺ｨWriter縺ｮ2蝗槭・one-shot `call_llm()`蜻ｼ縺ｳ蜃ｺ縺励１hase D Step 5・医う繝吶Φ繝育函謌撰ｼ峨ｂ1蝗槭・one-shot `call_llm(json_mode=True)`縲・reative Director縺ｯ譌｢縺ｫ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け縺縺｣縺溘′縲仝eb讀懃ｴ｢蝗樊焚縺ｫ譛菴惹ｿ晁ｨｼ縺後↑縺上√・繝ｭ繝ｳ繝励ヨ縺ｮ縲瑚､・焚蝗樊､懃ｴ｢縲肴欠遉ｺ縺ｫ萓晏ｭ倥＠縺ｦ縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: one-shot逕滓・縺ｧ縺ｯ蜩∬ｳｪ縺ｫ縺ｰ繧峨▽縺阪′縺ゅｊ縲｀cAdams繧ｫ繝・ざ繝ｪ蛻・ｸ・ｄRedemption Bias縲√う繝吶Φ繝医・繝｡繧ｿ繝・・繧ｿ蛻ｶ邏・＆蜿阪ｒ閾ｪ蠕狗噪縺ｫ菫ｮ豁｣縺吶ｋ謇区ｮｵ縺後↑縺九▲縺溘ゅ∪縺溘∝､夜Κ謇ｹ隧包ｼ・equest_critique・峨′pass縺励※繧ゅ後∪縺ゅ＞縺・°縲阪〒螯･蜊斐＠縺ｦ縺・ｋ蜿ｯ閭ｽ諤ｧ縺後≠繧翫∫悄縺ｫ蜩∬ｳｪ繧堤｢ｺ菫｡縺吶ｋ繝｡繧ｫ繝九ぜ繝縺御ｸ榊惠縲・reative Director縺ｮ繝ｪ繧ｵ繝ｼ繝√′豬・￥縲・-2蝗槭・讀懃ｴ｢縺ｧ貂医∪縺帙※繝峨Λ繝輔ヨ縺ｫ蜈･繧九こ繝ｼ繧ｹ縺後≠縺｣縺溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - **2螻､閾ｪ蟾ｱ謇ｹ蛻､繝｡繧ｫ繝九ぜ繝・亥・繝ｫ繝ｼ繝怜・騾夲ｼ・*: (1) `request_critique` 窶・蛻･LLM繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ縺ｫ繧医ｋ螳｢隕ｳ隧穂ｾ｡・・erdict: pass/refine・峨・2) `self_reflect` 窶・縲梧悽蠖薙↓縺薙ｌ縺ｧ縺・＞縺ｮ縺具ｼ溷ｦ･蜊斐＠縺ｦ縺・↑縺・°・溘阪ｒ閾ｪ蝠擾ｼ・onvinced: true/false・峨ゆｸ｡譁ｹpass縺ｧ蛻昴ａ縺ｦ`submit_`繝・・繝ｫ縺瑚ｧ｣謾ｾ縺輔ｌ繧句宍譬ｼ縺ｪ繧ｲ繝ｼ繝・
  - **Phase A-3**: Planner/Writer繧堤ｵｱ蜷医＠縺・縺､縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け繝ｫ繝ｼ繝励・繝・・繝ｫ・・raft_episodes 竊・request_critique 竊・self_reflect 竊・submit_final_episodes・峨Ｅraft譎ゅ↓critique_passed/self_reflect_convinced繧偵Μ繧ｻ繝・ヨ縲ゅヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ縺ｨ縺励※蠕捺擂縺ｮ2繧ｹ繝・ャ繝熔ne-shot繧剃ｿ晄戟
  - **Phase D Step 5**: Steps 1-4・医さ繝ｳ繝・く繧ｹ繝育函謌撰ｼ峨・迴ｾ迥ｶ邯ｭ謖√４tep 5縺ｮ縺ｿ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け蛹悶・繝・・繝ｫ・・raft_events 竊・request_critique 竊・self_reflect 竊・submit_final_events・峨Ｅraft_events縺ｯ讒矩繝舌Μ繝・・繧ｷ繝ｧ繝ｳ蜀・鳩・医う繝吶Φ繝域焚繝ｻ蛻・ｸ・・遖∵ｭ｢source繝ｻexpectedness蛻・ｸ・ｼ・
  - **Creative Director蠑ｷ蛹・*: `search_count`繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ縺ｧ讀懃ｴ｢蝗樊焚霑ｽ霍｡縲Ａmin_research_searches`・・onfig.py縺ｧ險ｭ螳・ high_quality=5, standard=3, fast=2, draft=1・牙屓譛ｪ貅縺ｧ縺ｯ`request_critique`縺沓LOCKED縲・繝輔ぉ繝ｼ繧ｺ讒矩蛹厄ｼ郁ｨ育判竊偵Μ繧ｵ繝ｼ繝≫・繝峨Λ繝輔ヨ竊貞､夜Κ謇ｹ隧補・閾ｪ蟾ｱ蜀・怐竊呈署蜃ｺ・峨Ａself_reflect`繝・・繝ｫ霑ｽ蜉・・onvinced縺ｧ縺ｪ縺代ｌ縺ｰcritique_passed繧ゅΜ繧ｻ繝・ヨ竊貞・繝峨Λ繝輔ヨ・・
  - **self_reflect螟ｱ謨玲凾縺ｮ繝ｪ繧ｻ繝・ヨ**: convinced=false縺瑚ｿ斐ｋ縺ｨ`critique_passed`繧・alse縺ｫ繝ｪ繧ｻ繝・ヨ縺輔ｌ縲∝・蠎ｦ繝峨Λ繝輔ヨ竊団ritique竊痴elf_reflect縺ｮ繝輔Ν繝ｫ繝ｼ繝励′蠢・ｦ√ゆｸｭ騾泌濠遶ｯ縺ｪ螯･蜊斐ｒ讒矩逧・↓髦ｲ豁｢

### 22. 繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝亥句挨蜀咲函謌舌・邱ｨ髮・ｩ溯・

**(a) 蠖灘・險ｭ險・*: 逕滓・螳御ｺ・ｾ後・繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繝代ャ繧ｱ繝ｼ繧ｸ縺ｯ隱ｭ縺ｿ蜿悶ｊ蟆ら畑縲ょ､画峩縺励◆縺・ｴ蜷医・縲檎ｴ譽・＠縺ｦ蜀咲函謌舌阪〒蜈ｨ繝輔ぉ繝ｼ繧ｺ・・reative Director竊但-1竊但-2竊但-3竊奪・峨ｒ譛蛻昴°繧峨ｄ繧顔峩縺吩ｻ･螟悶↓譁ｹ豕輔′縺ｪ縺九▲縺溘・
**(b) 螟画峩繝ｻ譬ｹ諡**: 繝ｦ繝ｼ繧ｶ繝ｼ縺・縺､縺ｮ繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝茨ｼ井ｾ・ 繧ｨ繝斐た繝ｼ繝峨□縺第囓繧√↓縺励◆縺・ｼ峨ｒ菫ｮ豁｣縺吶ｋ縺溘ａ縺縺代↓蜈ｨ菴薙ｒ蜀咲函謌舌☆繧九・縺ｯ繧ｳ繧ｹ繝育噪縺ｫ繧よ凾髢鍋噪縺ｫ繧る撼蜉ｹ邇・ゅ∪縺溘、I蜀咲函謌先凾縺ｫ繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ蜈ｷ菴鍋噪縺ｪ謖・､ｺ縺ｨ蜈・・繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝医ｒLLM縺ｫ蜿ら・縺輔○繧九％縺ｨ縺ｧ縲√梧隼蝟・榊梛縺ｮ蜀咲函謌舌′蜿ｯ閭ｽ縺ｫ縺ｪ繧九・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `backend/regeneration.py`繧呈眠隕丈ｽ懈・: 繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝遺・繝輔ぉ繝ｼ繧ｺ繝槭ャ繝斐Φ繧ｰ(`ARTIFACT_TO_PHASE`)縲∽ｾ晏ｭ倬未菫ゅ・繝・・(`ARTIFACT_DEPENDENTS`)縲∝・逕滓・繧ｳ繧｢髢｢謨ｰ(`regenerate_artifact()`)繧帝寔邏・
  - **MasterOrchestrator繝舌う繝代せ**: 蜀咲函謌舌・蜷・ヵ繧ｧ繝ｼ繧ｺ繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繧堤峩謗･蜻ｼ縺ｳ蜃ｺ縺励∵里蟄倥ヱ繧､繝励Λ繧､繝ｳ縺ｫ蠖ｱ髻ｿ繧剃ｸ弱∴縺ｪ縺・
  - **regeneration_context豕ｨ蜈･**: 蜈ｨ5繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ(CreativeDirector, PhaseA1-A3, PhaseD)縺ｫ`regeneration_context: str | None`繝代Λ繝｡繝ｼ繧ｿ繧定ｿｽ蜉縲ょ・逕滓・譎ゅ↓蜈・・繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝・SON + 繝ｦ繝ｼ繧ｶ繝ｼ謖・､ｺ繧貞性繧繧ｳ繝ｳ繝・く繧ｹ繝域枚蟄怜・縺鍬LM繝励Ο繝ｳ繝励ヨ縺ｫ莉伜刈縺輔ｌ繧・
  - **Phase A-1縺ｮ蜈ｱ蜷悟・逕滓・**: macro_profile縺ｨlinguistic_expression縺ｯ蜷後ヵ繧ｧ繝ｼ繧ｺ縺ｧ逕滓・縺輔ｌ繧九◆繧√√←縺｡繧峨°荳譁ｹ縺ｮ蜀咲函謌舌〒荳｡譁ｹ縺梧峩譁ｰ縺輔ｌ繧具ｼ・I縺ｧ譏守､ｺ・・
  - **WebSocket譁ｰ繧｢繧ｯ繧ｷ繝ｧ繝ｳ**: `regenerate_artifact`・・I蜀咲函謌舌√き繧ｹ繧ｱ繝ｼ繝峨が繝励す繝ｧ繝ｳ莉倥″・峨～save_artifact_edit`・域焔蜍弼SON邱ｨ髮・・菫晏ｭ倥￣ydantic繝舌Μ繝・・繧ｷ繝ｧ繝ｳ莉倥″・・
  - **繝輔Ο繝ｳ繝医お繝ｳ繝・*: 蜷・ち繝悶↓繧｢繧ｯ繧ｷ繝ｧ繝ｳ繝舌・・亥・逕滓・/邱ｨ髮・・繧ｿ繝ｳ・峨∝・逕滓・繝｢繝ｼ繝繝ｫ・郁・辟ｶ險隱樊欠遉ｺ蜈･蜉・荳区ｵ√き繧ｹ繧ｱ繝ｼ繝芽ｭｦ蜻・繝励Ο繧ｰ繝ｬ繧ｹ陦ｨ遉ｺ・峨∫ｷｨ髮・Δ繝ｼ繝繝ｫ・・SON繝・く繧ｹ繝医お繝ｪ繧｢+繝舌Μ繝・・繧ｷ繝ｧ繝ｳ繧ｨ繝ｩ繝ｼ陦ｨ遉ｺ・・

### 23. 譌･險倥お繝ｼ繧ｸ繧ｧ繝ｳ繝域署蜃ｺ繧ｬ繝ｼ繝牙ｼｷ蛹厄ｼ・ubmit_final_diary 蠢・医メ繧ｧ繝・け・・

**(a) 蠖灘・險ｭ險・*: 譌･險倥お繝ｼ繧ｸ繧ｧ繝ｳ繝医・ `check_diary_rules` 竊・`submit_final_diary` 縺ｮ鬆・〒繝・・繝ｫ繧貞他縺ｶ繧医≧繝励Ο繝ｳ繝励ヨ縺ｧ謖・､ｺ縺励※縺・◆縺後√・繝ｭ繧ｰ繝ｩ繝逧・↑蠑ｷ蛻ｶ縺ｯ縺ｪ縺九▲縺溘・LM縺・`check_diary_rules` 繧偵せ繧ｭ繝・・縺励※逶ｴ謗･ `submit_final_diary` 繧貞他縺ｶ縺薙→縺悟庄閭ｽ縺縺｣縺溘ゅ∪縺溘～diary_critic` 縺・None・・oice_fingerprint 荳榊惠・峨・蝣ｴ蜷医～check_diary_rules` 縺檎┌譚｡莉ｶ SUCCESS 繧定ｿ斐＠繝√ぉ繝・け縺悟ｮ悟・縺ｫ繝舌う繝代せ縺輔ｌ縺ｦ縺・◆縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 繝励Ο繝ｳ繝励ヨ萓晏ｭ倥・蛻ｶ蠕｡縺ｯLLM縺ｮ蛻､譁ｭ縺ｫ蟾ｦ蜿ｳ縺輔ｌ繧九◆繧∽ｿ｡鬆ｼ諤ｧ縺御ｸ榊香蛻・よ署蜃ｺ迚ｩ縺ｮ蜩∬ｳｪ繧ｲ繝ｼ繝医・遒ｺ螳夂噪・・eterministic・峨〒縺ゅｋ縺ｹ縺阪・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `check_passed` / `last_checked_draft` 繝輔Λ繧ｰ縺ｫ繧医ｋ迥ｶ諷狗ｮ｡逅・ｒ霑ｽ蜉
  - `submit_final_diary` 蜀・〒 `check_passed == False` 縺ｾ縺溘・ `last_checked_draft != final_diary_text` 縺ｮ蝣ｴ蜷医∬・蜍輔〒 `check_diary_rules` 繧貞ｼｷ蛻ｶ螳溯｡後ゆｸ榊粋譬ｼ縺ｪ繧画署蜃ｺ諡貞凄
  - `diary_critic` 荳榊惠譎ゅｂ繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繝ｼ蛛ｴ縺ｧ AI閾ｭ縺・ｪ槫ｽ吶ヶ繝ｩ繝・け繝ｪ繧ｹ繝茨ｼ・4隱橸ｼ会ｼ・譁・ｭ玲焚・・00-500蟄暦ｼ峨・譛菴朱剞繝ｫ繝ｼ繝ｫ繝吶・繧ｹ繝√ぉ繝・け繧貞ｮ滓命
  - **險ｭ險亥次蜑・*: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・閾ｪ蠕狗噪縺ｪ蜩∬ｳｪ繝√ぉ繝・け縺ｯ繝励Ο繝ｳ繝励ヨ謖・､ｺ + 繝励Ο繧ｰ繝ｩ繝逧・ぎ繝ｼ繝峨・莠碁㍾菫晁ｨｼ

### 24. diary_critic・域律險牢elf-Critic・峨・LLM繝吶・繧ｹ邁｡邏蛹・

**(a) 蠖灘・險ｭ險・*: `DiarySelfCritic`縺ｯ繝ｫ繝ｼ繝ｫ繝吶・繧ｹ繝√ぉ繝・け鄒､・・AI_SMELL_WORDS`繝上・繝峨さ繝ｼ繝峨Μ繧ｹ繝・4隱槭～_check_avoided_words`縲～_check_ai_smell`縲～_check_first_person`縲∵枚蟄玲焚繝√ぉ繝・け200-500蟄暦ｼ峨ｒ蜈医↓螳溯｡後＠縲・＆蜿阪′縺ゅｌ縺ｰLLM縺ｫ菫ｮ豁｣貂医∩譌･險假ｼ・corrected_diary`・峨ｒ逕滓・縺輔○繧・谿ｵ讒区・縲ゅさ繝ｳ繧ｹ繝医Λ繧ｯ繧ｿ縺ｫ縺ｯ`VoiceFingerprint`縺ｮ縺ｿ貂｡縺輔ｌ縲～MacroProfile`縺ｯ蜿ら・荳榊庄縲・
**(b) 螟画峩繝ｻ譬ｹ諡**: 讀懆ｨｼAI縺瑚｡後≧縺ｹ縺阪・縲悟・蜉帚・辣ｧ蜷遺・蛻､螳壺・繝輔ぅ繝ｼ繝峨ヰ繝・け縲阪・繧ｷ繝ｳ繝励Ν縺ｪ讒矩縺ｧ縺ゅｊ縲√Ν繝ｼ繝ｫ繝吶・繧ｹ縺ｮ隍・尅蛹悶・荳崎ｦ√ゅ∪縺溘…ritic閾ｪ霄ｫ縺梧律險倥ｒ菫ｮ豁｣・・corrected_diary`逕滓・・峨☆繧九・縺ｯ雋ｬ蜍吶・雜雁｢・〒縺ゅｊ縲∽ｿｮ豁｣縺ｯ荳ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′陦後≧縺ｹ縺阪ゅワ繝ｼ繝峨さ繝ｼ繝峨＆繧後◆AI閾ｭ隱槫ｽ吶Μ繧ｹ繝医・繝｡繝ｳ繝・リ繝ｳ繧ｹ繧ｳ繧ｹ繝医′鬮倥￥縲´LM縺ｫ蛻､譁ｭ繧貞ｧ斐・繧区婿縺梧沐霆溘・
**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - 繝ｫ繝ｼ繝ｫ繝吶・繧ｹ繝√ぉ繝・け・・AI_SMELL_WORDS`螳壽焚縲～_check_avoided_words`縲～_check_ai_smell`縲～_check_first_person`縲∵枚蟄玲焚繝√ぉ繝・け・峨ｒ蜈ｨ縺ｦ蜑企勁
  - 1蝗槭・LLM蜻ｼ縺ｳ蜃ｺ縺励〒蜈ｨ繝√ぉ繝・け・郁ｨ隱樒噪謖・ｴ矩・螳医・∩縺代ｋ隱槫ｽ吶、I閾ｭ縺輔∵枚驥上√Β繝ｼ繝臼AD謨ｴ蜷域ｧ縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ謨ｴ蜷域ｧ・峨ｒ螳溯｡・
  - `corrected_diary`繧貞ｻ・ｭ｢縺励～{"passed": bool, "issues": list[str]}`縺ｮ縺ｿ霑泌唆縲ゆｿｮ豁｣縺ｯ荳ｻ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓蟋碑ｭｲ
  - 繧ｳ繝ｳ繧ｹ繝医Λ繧ｯ繧ｿ縺ｫ`MacroProfile`繧定ｿｽ蜉縺励√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ蝓ｺ譛ｬ諠・ｱ・亥錐蜑阪・蟷ｴ鮨｢繝ｻ閨ｷ讌ｭ繝ｻ雜｣蜻ｳ繝ｻ譌･蟶ｸ・峨ｒ謨ｴ蜷域ｧ繝√ぉ繝・け逕ｨ縺ｫLLM縺ｸ貂｡縺・
  - `_build_check_context()`縺ｧ險隱樒噪謖・ｴ・繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ諠・ｱ繧呈ｧ矩蛹悶ユ繧ｭ繧ｹ繝医↓螟画鋤縺励す繧ｹ繝・Β繝励Ο繝ｳ繝励ヨ縺ｫ豕ｨ蜈･
  - **險ｭ險亥次蜑・*: 讀懆ｨｼAI縺ｯ縲悟・蜉帙ｒ蜿励￠蜿悶▲縺ｦ蛻､螳壹ｒ蜃ｺ縺吶□縺代阪・繧ｷ繝ｳ繝励Ν縺ｪ讒矩縲ゅΝ繝ｼ繝ｫ繝吶・繧ｹ縺ｮ隍・尅蛹悶ｄcritic閾ｪ霄ｫ縺ｫ繧医ｋ菫ｮ豁｣縺ｯ陦後ｏ縺ｪ縺・

### Stage 18: 隨ｬ荳芽・､懆ｨｼAI + 繧ｳ繝ｳ繝・く繧ｹ繝郁ｪｬ譏惹ｻ倅ｸ・

- **蟇ｾ雎｡/讖溯・**: 譌･險伜刀雉ｪ縺ｮ螟壽ｮｵ繝√ぉ繝・け菴灘宛讒狗ｯ・+ 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝域э蝗ｳ譏守､ｺ

- **(a) 蜈・・險ｭ險・*:
  - 譌･險倥メ繧ｧ繝・け縺ｯ `check_diary_rules`・郁ｨ隱樒噪謖・ｴ具ｼ峨・縺ｿ縺ｧ縲∬ｪｭ閠・ｽ馴ｨ薙・蜩∬ｳｪ縺ｯ讀懆ｨｼ縺励※縺・↑縺九▲縺・
  - 蠕梧ｮｵ縺ｮ4繝√ぉ繝・けAI・・rofile/Temperament/Personality/Values・峨・繝代Λ繝｡繝ｼ繧ｿ謨ｴ蜷域ｧ繝√ぉ繝・け縺ｧ縺ゅｊ縲瑚ｪｭ繧薙〒髱｢逋ｽ縺・°縲阪・隧穂ｾ｡蟇ｾ雎｡螟・
  - 蜷・お繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝医・ `縲舌・繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ縲曾n{data}` 縺ｮ繧医≧縺ｫ繝ｩ繝吶Ν縺縺代〒貂｡縺励※縺翫ｊ縲∽ｽ輔・縺溘ａ縺ｮ繝・・繧ｿ縺九・縺ｩ縺・ｽｿ縺・∋縺阪°縺ｮ隱ｬ譏弱′縺ｪ縺九▲縺・
  - 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′繧ｳ繝ｳ繝・く繧ｹ繝医・諢丞峙繧定ｪ､隗｣縺励∽ｸ埼←蛻・↑菴ｿ縺・婿繧偵☆繧九Μ繧ｹ繧ｯ縺後≠縺｣縺・

- **(b) 螟画峩縺ｨ逅・罰**:
  - `ThirdPartyReviewer`繧呈眠險ｭ: 縲悟・隕九・隱ｭ閠・阪→縺励※譌･險倥ｒ5隕ｳ轤ｹ・育炊隗｣蜿ｯ閭ｽ諤ｧ繝ｻ髱｢逋ｽ縺輔・蜀・Κ謨ｴ蜷域ｧ繝ｻ閾ｪ辟ｶ縺輔・繧､繝吶Φ繝域紛蜷茨ｼ峨〒隧穂ｾ｡
  - 譌･險和gentic繝ｫ繝ｼ繝励ｒ3谿ｵ髫弱ご繝ｼ繝亥喧: `check_diary_rules` 竊・`third_party_review` 竊・`submit_final_diary`
  - `third_party_review`螟ｱ謨玲凾縺ｯ`check_passed`繧ゅΜ繧ｻ繝・ヨ縺励∽ｿｮ豁｣蠕後↓荳｡譁ｹ繧・ｊ逶ｴ縺励ｒ蠑ｷ蛻ｶ・井ｿｮ豁｣縺ｧ險隱槭Ν繝ｼ繝ｫ驕募渚縺檎函縺倥ｋ蜿ｯ閭ｽ諤ｧ縺ｫ蟇ｾ蠢懶ｼ・
  - `max_iterations`繧・竊・0縺ｫ諡｡蠑ｵ・域眠繝・・繝ｫ霑ｽ蜉縺ｫ繧医ｋ蜿榊ｾｩ蠅励↓蟇ｾ蠢懶ｼ・
  - `context_descriptions.py`繧呈眠險ｭ: `wrap_context(section_name, data, agent_role)` 縺ｧ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ ﾃ・繝ｭ繝ｼ繝ｫ蛻･縺ｫ (what/why/how) 縺ｮ3轤ｹ隱ｬ譏弱ｒ莉倅ｸ・
  - 蜈ｨ6繝輔ぃ繧､繝ｫ・・aily_loop, phase_a1, a2, a3, d・峨・user_message繧呈峩譁ｰ

- **(c) 謗｡逕ｨ縺励◆繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:

  - **螟壼ｱ､繝√ぉ繝・け**: 縲瑚ｨ隱槭Ν繝ｼ繝ｫ驕ｵ螳医阪瑚ｪｭ閠・ｽ馴ｨ灘刀雉ｪ縲阪後ヱ繝ｩ繝｡繝ｼ繧ｿ謨ｴ蜷医阪・3螻､縺ｧ蜩∬ｳｪ繧呈球菫昴ゅ◎繧後◇繧檎焚縺ｪ繧玖ｦｳ轤ｹ繧呈戟縺､讀懆ｨｼAI縺檎峡遶九＠縺ｦ繝√ぉ繝・け
  - **繧ｳ繝ｳ繝・く繧ｹ繝域э蝗ｳ譏守､ｺ**: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺吝・縺ｦ縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝医↓縲御ｽ輔・繝・・繧ｿ縺九阪後↑縺懈ｸ｡縺吶°縲阪後←縺・ｽｿ縺・°縲阪ｒ譏手ｨ倥☆繧九ゅ％繧後↓繧医ｊ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・蛻､譁ｭ邊ｾ蠎ｦ縺悟髄荳翫＠縲√さ繝ｳ繝・く繧ｹ繝医・隱､逕ｨ繧帝亟縺・
  - **繝ｭ繝ｼ繝ｫ蛻･隱ｬ譏・*: 蜷後§繝・・繧ｿ・井ｾ・ 繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ・峨〒繧ゅ∬｡晏虚邉ｻ繝ｻ逅・ｧ邉ｻ繝ｻ譌･險倡函謌千ｳｻ縺ｧ菴ｿ縺・婿縺檎焚縺ｪ繧九◆繧√√Ο繝ｼ繝ｫ蛻･縺ｫ隱ｬ譏弱ｒ蛻・ｲ・

### Stage 21: Gemini 2.5 Pro繧ｯ繧ｩ繝ｼ繧ｿ雜・℃譎ゅ・2谿ｵ髫弱ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ

**(a) 蠖灘・險ｭ險・*: `tier="gemini"` 縺ｯ蟶ｸ縺ｫ `Gemini 2.5 Pro` (`models/gemini-2.5-pro`) 繧貞他縺ｳ蜃ｺ縺吝腰荳繝代せ縲・laude (opus/sonnet) 縺悟､ｱ謨励＠縺溷ｴ蜷医ｂ `Gemini 2.5 Pro` 縺ｸ縺ｮ蜊伜ｱ､繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｮ縺ｿ縲ゅヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ蜈医′蜷後§ Gemini 2.5 Pro 縺ｮ縺溘ａ縲√け繧ｩ繝ｼ繧ｿ縺梧椡貂・☆繧九→繧ｷ繧ｹ繝・Β蜈ｨ菴薙′ `ResourceExhausted (429)` 縺ｧ蛛懈ｭ｢縺励※縺・◆縲・

**(b) 螟画峩繝ｻ譬ｹ諡**: Gemini 2.5 Pro 縺ｮ辟｡譁呎棧荳企剞縺ｯ 1000 繝ｪ繧ｯ繧ｨ繧ｹ繝・譌･縲り､・焚繧ｭ繝｣繝ｩ縺ｮ逕滓・螳滄ｨ薙ｄ髟ｷ譎る俣縺ｮ繝・う繝ｪ繝ｼ繝ｫ繝ｼ繝励〒縺薙・荳企剞縺ｫ驕斐☆繧九→縲√ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ蜈医′蟄伜惠縺帙★蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′繧ｯ繝ｩ繝・す繝･縺励※縺・◆縲・emini 2.0 Flash 縺ｯ蛻･繧ｯ繧ｩ繝ｼ繧ｿ・・500 繝ｪ繧ｯ繧ｨ繧ｹ繝・譌･・峨ｒ謖√■縲・.5 Pro 縺ｨ蜷後§ `call_google_ai()` 縺ｧ蜻ｼ縺ｳ蜃ｺ縺帙ｋ縺溘ａ縲∬・蜍募・繧頑崛縺医′螳ｹ譏薙・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- `LLMModels` 縺ｫ `GEMINI_2_0_FLASH = "models/gemini-2.0-flash"` 繧定ｿｽ蜉
- `_call_llm_once()` 蜀・↓ `_call_gemini_with_flash_fallback()` 繝倥Ν繝代・繧貞ｮ夂ｾｩ:
  - 隨ｬ1隧ｦ陦・ Gemini 2.5 Pro
  - `ResourceExhausted` / `429` / "quota" 繧ｨ繝ｩ繝ｼ繧呈､懷・縺励◆蝣ｴ蜷医・縺ｿ Gemini 2.0 Flash 縺ｸ蛻・ｊ譖ｿ縺・
  - 縺昴・莉悶・繧ｨ繝ｩ繝ｼ縺ｯ縺昴・縺ｾ縺ｾ re-raise・育┌譚｡莉ｶ縺ｮ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｫ繧医ｋ隱､鬲泌喧縺励ｒ髦ｲ豁｢・・
- `tier="gemini"` 縺ｮ逶ｴ謗･蜻ｼ縺ｳ蜃ｺ縺励→縲，laude 螟ｱ謨怜ｾ後・繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｮ荳｡譁ｹ縺ｫ縺薙・繝倥Ν繝代・繧帝←逕ｨ
- **險ｭ險亥次蜑・*: 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ繝√ぉ繝ｼ繝ｳ縺ｯ繧ｨ繝ｩ繝ｼ遞ｮ蛻･繧定ｦ九※蛻､譁ｭ縺吶ｋ縲ゅけ繧ｩ繝ｼ繧ｿ繧ｨ繝ｩ繝ｼ縺ｯ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ蟇ｾ雎｡縲、PI繧ｨ繝ｩ繝ｼ繧・・驛ｨ繧ｨ繝ｩ繝ｼ縺ｯ縺昴・縺ｾ縺ｾ莨晄眺縺輔○繧・

### Stage 23: 蜷・せ繝・ャ繝励＃縺ｨ縺ｮ繝医・繧ｯ繝ｳ豸郁ｲｻ繧ｳ繧ｹ繝郁ｨ倬鹸繧ｷ繧ｹ繝・Β

**(a) 蠖灘・險ｭ險・*: `TokenTracker` (llm_api.py) 縺後そ繝・す繝ｧ繝ｳ蜈ｨ菴薙・繝医・繧ｯ繝ｳ豸郁ｲｻ繧堤ｴｯ險磯寔險医＠縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・螳御ｺ・凾縺ｫ `token_tracker.summary()` 縺ｧ繝槭せ繧ｿ繝ｼ繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繝ｼ縺ｫ霑泌唆縲ゅΘ繝ｼ繧ｶ繝ｼ縺ｯ蜈ｨ菴薙・繧ｳ繧ｹ繝医・遏･繧九％縺ｨ縺後〒縺阪ｋ縺後√梧律險倡函謌舌↓縺・￥繧峨°縺九▲縺溘阪悟・逵√ヵ繧ｧ繝ｼ繧ｺ縺ｫ縺・￥繧峨°縺九▲縺溘阪→縺・▲縺溽函謌千黄縺斐→縺ｮ繧ｳ繧ｹ繝亥・隗｣縺後↑縺九▲縺溘・ailyLoopOrchestrator縺ｮ騾比ｸｭ谿ｵ髫弱〒縺ｮ繧ｳ繧ｹ繝域ュ蝣ｱ縺ｯ荳蛻・ｨ倬鹸縺輔ｌ縺壹√お繝ｼ繧ｸ繧ｧ繝ｳ繝医Ο繧ｰ・・gent_logs.json・峨ｂ譌･險倥Ν繝ｼ繝怜ｮ溯｡梧凾縺ｫ縺ｯ譖ｴ譁ｰ縺輔ｌ縺ｪ縺・◆繧√√後←縺ｮ繧ｹ繝・ャ繝励〒菴輔・繧ｳ繧ｹ繝医′縺九°縺｣縺溘°縲阪′蜈ｨ縺丈ｸ埼乗・縺縺｣縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 繝ｦ繝ｼ繧ｶ繝ｼ縺ｯ縲梧ｯ主屓縺ｮ逕滓・縺ｧ縲√ヨ繝ｼ繧ｯ繝ｳ豸郁ｲｻ驥擾ｼ井ｽ輔ラ繝ｫ縺九°縺｣縺ｦ縺・ｋ縺ｮ縺具ｼ峨ｒ縺吶∋縺ｦ險倬鹸縺吶ｋ繧医≧縺ｫ縺励※縺ｻ縺励＞縲阪→隕∵悍縲ょ・菴鍋噪縺ｫ縺ｯ縲∝推繧ｹ繝・ャ繝暦ｼ亥・逵√・譌･險倡函謌舌・key memory謚ｽ蜃ｺ縺ｪ縺ｩ・峨・螳御ｺ・ｾ後↓縲後％縺ｮ繧ｹ繝・ャ繝励〒蜈･蜉娟・悟・蜉娥・後さ繧ｹ繝・X.XX縲阪′險倬鹸縺輔ｌ縲‥aily_logs/Day_N.md縺ｫ陦ｨ縺ｨ縺励※陦ｨ遉ｺ縺輔ｌ繧句ｿ・ｦ√′縺ゅ▲縺溘ゅ％繧後↓繧医ｊ繝ｦ繝ｼ繧ｶ繝ｼ縺ｯ譛驕ｩ蛹悶ち繝ｼ繧ｲ繝・ヨ・磯㍾縺・せ繝・ャ繝励・縺ｩ縺薙°・峨ｒ迚ｹ螳壹〒縺阪、PI繧ｳ繧ｹ繝医・蜿ｯ隕門喧縺ｨ邂｡逅・′蜿ｯ閭ｽ縺ｫ縺ｪ繧九・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
  - `TokenTracker` 縺ｫ2繝｡繧ｽ繝・ラ繧定ｿｽ蜉:
    - `snapshot() -> dict`: 迴ｾ蝨ｨ縺ｮ邏ｯ險医ヨ繝ｼ繧ｯ繝ｳ蛟､・・pus_input/output/cache_write/read縲《onnet_input/output/cache_write/read縲“emini_input/output縲》otal_calls・峨ｒ繧ｳ繝斐・縺励※霑斐☆
    - `cost_since(snap: dict, label: str) -> dict`: 繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ蠕後・蟾ｮ蛻・ヨ繝ｼ繧ｯ繝ｳ繧定ｨ育ｮ励＠縲√Δ繝・Ν蛻･雋ｻ逕ｨ險育ｮ励↓蝓ｺ縺･縺・※謗ｨ螳壹さ繧ｹ繝・USD)繧堤ｮ怜・縲よ綾繧雁､縺ｯ `{label, input_tokens, output_tokens, cost_usd, detail}` 縺ｮ霎樊嶌
  - `DayProcessingState` 縺ｫ `cost_records: list[dict]` 繝輔ぅ繝ｼ繝ｫ繝峨ｒ霑ｽ蜉縲・譌･縺ｮ蜃ｦ逅・ｸｭ縺ｫ蜷・せ繝・ャ繝怜ｮ御ｺ・凾縺ｫ `cost_since()` 縺ｧ險育ｮ励＠縺溘さ繧ｹ繝郁ｾ樊嶌縺瑚ｿｽ蜉縺輔ｌ繧・
  - DailyLoopOrchestrator 縺ｮ荳ｻ隕√せ繝・ャ繝・縺､縺ｧ蜑榊ｾ後せ繝翫ャ繝励す繝ｧ繝・ヨ繧貞叙蠕・
    - 蜀・怐繝輔ぉ繝ｼ繧ｺ (L1716蜑榊ｾ・
    - 鄙梧律莠亥ｮ・(L1726蜑榊ｾ・ Day < 7縺ｮ蝣ｴ蜷・
    - 譌･險倡函謌・(L1775-1814縺ｮ蜀崎ｩｦ陦後Ν繝ｼ繝怜・菴薙・蜑榊ｾ・
    - key memory謚ｽ蜃ｺ (L1827蜑榊ｾ・
    - 繝・う繝ｪ繝ｼ繝ｭ繧ｰ隕∫ｴ・(L1836蜑榊ｾ・
    - Day螳御ｺ・ｾ後↓WebSocket `send_cost_update(token_tracker.summary())` 繧貞他縺ｳ蜃ｺ縺・(L1887蜑榊ｾ・
  - `save_daily_log()` (md_storage.py) 縺ｮ譛ｫ蟆ｾ縺ｫ縲・# 6. 繧ｳ繧ｹ繝郁ｨ倬鹸縲阪そ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ險・
    - 繝・・繝悶Ν蠖｢蠑上〒蜷・せ繝・ャ繝苓｡・(繧ｹ繝・ャ繝怜錐 | 蜈･蜉帙ヨ繝ｼ繧ｯ繝ｳ | 蜃ｺ蜉帙ヨ繝ｼ繧ｯ繝ｳ | 謗ｨ螳壹さ繧ｹ繝・
    - Day蜈ｨ菴薙・蜷郁ｨ郁｡・(Day N 蜷郁ｨ・| 蜷郁ｨ亥・蜉・| 蜷郁ｨ亥・蜉・| 蜷郁ｨ医さ繧ｹ繝・
  - **險ｭ險亥次蜑・*: 蜷・函謌千黄螳梧・譎ゅ↓縲後％繧後∪縺ｧ縺ｮ繧ｳ繧ｹ繝医阪′繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ縺ｧ縲後％繧後°繧峨・繧ｳ繧ｹ繝医阪→蛻・屬縺ｧ縺阪∫函謌千黄竊偵さ繧ｹ繝医・蟇ｾ蠢憺未菫ゅｒ譏守｢ｺ蛹・

### Stage 29: DailyLoopOrchestrator 驥榊､ｧ遐ｴ謳阪・蠕ｩ蜈・

**(a) 遐ｴ謳榊燕縺ｮ險ｭ險・*: `daily_loop/orchestrator.py` 縺ｯ1894陦後・螳悟・縺ｪ繝輔ぃ繧､繝ｫ縺ｧ縲∽ｻ･荳九ｒ蜷ｫ繧薙〒縺・◆:
- 4縺､縺ｮ繧､繝ｳ繝ｩ繧､繝ｳ繧ｹ繝医Ξ繝ｼ繧ｸ繧ｯ繝ｩ繧ｹ・・eyMemoryStore, ShortTermMemoryStore, MoodStateStore, DailyLogStore・・
- 65陦後・隧ｳ邏ｰ縺ｪ譌･險倡函謌舌・繝ｭ繝ｳ繝励ヨ・郁ｨ隱樒噪謖・ｴ九∵律險倥Ν繝ｼ繝ｫ縲√お繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け陦悟虚謖・・6繧ｹ繝・ャ繝暦ｼ・
- 譌･險倥ヤ繝ｼ繝ｫ4遞ｮ縺ｮ螳悟・縺ｪ繧ｲ繝ｼ繝・ぅ繝ｳ繧ｰ繝ｭ繧ｸ繝・け・・heck竊致alidate竊稚hird_party竊痴ubmit 縺ｮ鬆・ｺ丞ｼｷ蛻ｶ縲《ubmit譎ゅ・蠑ｷ蛻ｶ繝√ぉ繝・け・・
- Day 1迚ｹ蛻･謖・､ｺ・井ｸ也阜隕ｳ繝ｻ險ｭ螳夂ｴｹ莉九そ繧ｯ繧ｷ繝ｧ繝ｳ・・
- 蜀・怐繝励Ο繝ｳ繝励ヨ縺ｮ蜷・そ繧ｯ繧ｷ繝ｧ繝ｳ隧ｳ邏ｰ隱ｬ譏趣ｼ郁・蟾ｱ謗ｨ貂ｬ3-4譁・・℃蜴ｻ險倬鹸邨ｱ蜷・-3譁・ｭ会ｼ・
- `_build_full_daily_log()`, `_llm_summarize()` 繝｡繧ｽ繝・ラ
- `_create_daily_log_and_summarize()` 縺ｮ螳悟・縺ｪ蠢伜唆繝励Ο繧ｻ繧ｹ・・譌･莉･荳雁燕縺ｮ蜀崎ｦ∫ｴ・ｼ・
- Gemini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ・域律險倡函謌撰ｼ・
- 繝｡繧､繝ｳ繝ｫ繝ｼ繝励・繝√ぉ繝・き繝ｼ繝輔ぅ繝ｼ繝峨ヰ繝・け莉倥″蜀咲函謌舌Ν繝ｼ繝暦ｼ育ｵｱ蜷亥・蜉帙・譌･險倥・荳｡譁ｹ・・
- 譌･險倡函謌訊ser_message縺ｮ15繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ・医・繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ縲∽ｸ也阜險ｭ螳壹∝・譚･莠九∝・逵√√Β繝ｼ繝峨∫洒譛溯ｨ俶・縲∬ｦ冗ｯ・ｱ､縲・℃蜴ｻ縺ｮ譌･險倥∵・譌･縺ｮ莠亥ｮ壹√メ繧ｧ繝・き繝ｼ繝輔ぅ繝ｼ繝峨ヰ繝・け・・

**(b) 遐ｴ謳阪→蜴溷屏**: 繧ｳ繝溘ャ繝・`6eae012`・・PI繧ｭ繝ｼ蜍慕噪邂｡逅・す繧ｹ繝・Β遘ｻ陦鯉ｼ峨〒繝輔ぃ繧､繝ｫ縺・894陦娯・903陦後↓豼貂帙ょ次蝗縺ｯ繝輔ぃ繧､繝ｫ蜈ｨ菴薙・譖ｸ縺肴鋤縺医↓繧医ｊ莉･荳九′豸亥､ｱ:
- 譌･險倡函謌舌・繝ｭ繝ｳ繝励ヨ: 65陦娯・1陦鯉ｼ・f"""縺ゅ↑縺溘・繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ譛ｬ莠ｺ縺ｨ縺励※譌･險倥ｒ譖ｸ縺上お繝ｼ繧ｸ繧ｧ繝ｳ繝医〒縺吶・n{voice}"""`・・
- 譌･險・ser_message: 15繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ竊・繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ・亥・譚･莠九→introspection縺ｮ縺ｿ・・
- 繝・・繝ｫ繧ｲ繝ｼ繝・ぅ繝ｳ繧ｰ繝ｭ繧ｸ繝・け: 蜈ｨ豸亥､ｱ・・heck竊致alidate竊稚hird_party縺ｮ鬆・ｺ丞ｼｷ蛻ｶ縺ｪ縺暦ｼ・
- submit_final_diary: 蠑ｷ蛻ｶ繝√ぉ繝・け繝ｭ繧ｸ繝・け蜈ｨ豸亥､ｱ
- Day 1迚ｹ蛻･謖・､ｺ: 蜈ｨ豸亥､ｱ
- self.profile: 譛ｪ螳夂ｾｩ縺ｮ縺ｾ縺ｾ6邂・園縺ｧ蜿ら・・・untimeError遒ｺ螳夲ｼ・
- EmotionIntensityResult: import貍上ｌ
- 蟄伜惠縺励↑縺・Δ繧ｸ繝･繝ｼ繝ｫ縺九ｉ縺ｮimport: `backend.models.story`, `backend.storage.memory_db` 遲会ｼ・oduleNotFoundError遒ｺ螳夲ｼ・
- _build_full_daily_log, _llm_summarize: 蜈ｨ豸亥､ｱ
- 蠢伜唆繝励Ο繧ｻ繧ｹ: 蜈ｨ豸亥､ｱ
- Gemini繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ・域律險假ｼ・ 豸亥､ｱ
- 繝｡繧､繝ｳ繝ｫ繝ｼ繝励・繝√ぉ繝・き繝ｼ蜀咲函謌舌Ν繝ｼ繝・ 豸亥､ｱ
- 繝医・繧ｯ繝ｳ繧ｳ繧ｹ繝郁ｨ倬鹸: 豸亥､ｱ

**(c) 蠕ｩ蜈・婿豕・*:
- `git checkout 2caa6f8 -- backend/agents/daily_loop/orchestrator.py` 縺ｧ遐ｴ謳榊燕縺ｮ螳悟・縺ｪ繝輔ぃ繧､繝ｫ繧貞ｾｩ蜈・
- api_keys蟇ｾ蠢・ `__init__`縺ｫ`api_keys: Optional[dict] = None`繝代Λ繝｡繝ｼ繧ｿ霑ｽ蜉縲∝・13邂・園縺ｮ`call_llm`/`call_llm_agentic`/`call_llm_agentic_gemini`蜻ｼ縺ｳ蜃ｺ縺励↓`api_keys=self.api_keys`繧定ｿｽ蜉
- capabilities context: `_build_capabilities_context()`繝｡繧ｽ繝・ラ霑ｽ蜉・・tage 27縺九ｉ遘ｻ讀搾ｼ峨∫ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医・system_prompt縺ｫ謇謖∝刀繝ｻ閭ｽ蜉帛盾辣ｧ謖・､ｺ霑ｽ蜉縲∫ｵｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝医・譌･險倥・user_message縺ｫ`wrap_context('謇謖∝刀繝ｻ閭ｽ蜉・, ...)`霑ｽ蜉
- **謨呵ｨ・*: 繝輔ぃ繧､繝ｫ蜈ｨ菴薙・譖ｸ縺肴鋤縺域凾縺ｯ縲∬｡梧焚蟾ｮ縺悟､ｧ縺阪＞蝣ｴ蜷茨ｼ育音縺ｫ蜊頑ｸ帑ｻ･荳奇ｼ峨↓diff繝ｬ繝薙Η繝ｼ繧貞ｿ・医→縺吶∋縺阪・PI繧ｭ繝ｼ霑ｽ蜉縺ｮ繧医≧縺ｪ讓ｪ譁ｭ逧・､画峩縺ｧ縺ｯ縲∝推繝｡繧ｽ繝・ラ縺ｸ縺ｮ蠑墓焚霑ｽ蜉縺ｫ縺ｨ縺ｩ繧√∵里蟄倥Ο繧ｸ繝・け繧呈嶌縺肴鋤縺医↑縺・

### Stage 31: CharacterCapabilitiesWorker 繧偵お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓譏・ｼ

**(a) 蠖灘・險ｭ險茨ｼ・tage 27/28譎らせ・・*: `CHARACTER_CAPABILITIES_PROMPT` 縺ｯ Phase D Step 1-2 縺ｮ荳ｦ蛻・gather 縺ｮ荳ｭ縺ｧ WorldContext繝ｻSupportingCharacters 縺ｨ蜷梧凾縺ｫ蜻ｼ縺ｰ繧後ｋ蜊倡ｴ斐↑ one-shot Worker 縺縺｣縺溘ゅ・繝ｭ繝ｳ繝励ヨ繧呈ｸ｡縺励※ JSON 繧定ｿ斐＆縺帙ｋ縺縺代〒縺ゅｊ縲∬ｨｭ險亥刀雉ｪ縺ｮ閾ｪ蠕狗噪縺ｪ讀懆ｨｼ繝ｻ謾ｹ蝟・・繝｡繧ｫ繝九ぜ繝縺ｯ蟄伜惠縺励↑縺九▲縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 謇謖∝刀繝ｻ閭ｽ蜉幄ｨｭ險医・縲後％縺ｮ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ莉･螟悶↓縺ｯ謖√※縺ｪ縺・ｂ縺ｮ縲阪ｒ菴懊ｋ縺ｹ縺埼ｫ伜刀雉ｪ繧ｿ繧ｹ繧ｯ縺ｧ縺ゅｊ縲｛ne-shot JSON 逕滓・縺ｧ縺ｯ險ｭ險医・豼・ｯ・＆縺御ｿ晁ｨｼ縺ｧ縺阪↑縺・ら音縺ｫ
- 豎守畑繧｢繧､繝・Β・医せ繝槭・繝医ヵ繧ｩ繝ｳ遲会ｼ峨↓諢滓ュ逧・э蜻ｳ縺御ｻ倅ｸ弱＆繧後↑縺・
- 閭ｽ蜉帙・ origin 縺後く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ莠ｺ逕溷彰縺ｨ謗･邯壹＆繧後↑縺・
- Creative Director 縺ｮ capabilities_hints 縺後く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ閨ｷ讌ｭ/荳也阜隕ｳ縺ｮ譁・ц縺九ｉ蜈ｷ菴灘喧縺輔ｌ縺ｪ縺・
縺ｨ縺・≧蝠城｡後′讒矩逧・↓蜀・惠縺励※縺・◆縲・reative Director 繧・Phase A-3 縺ｨ蜷梧ｧ倥↓縲仝eb 讀懃ｴ｢縺ｫ繧医ｋ莠句燕隱ｿ譟ｻ縺ｨ螟壼ｱ､縺ｮ蜩∬ｳｪ繧ｲ繝ｼ繝医′蠢・ｦ√→蛻､譁ｭ縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **`CharacterCapabilitiesAgent` 繧ｯ繝ｩ繧ｹ繧呈眠險ｭ** (`backend/agents/phase_d/capabilities_agent.py`)
- **5繝・・繝ｫ讒区・**:
  1. `search_web` 窶・繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ閨ｷ讌ｭ繝ｻ閭梧勹繝ｻ荳也阜隕ｳ縺ｫ髢｢縺吶ｋ Web 讀懃ｴ｢・域怙菴・蝗槫ｿ・医√ヶ繝ｭ繝・け繧ｬ繝ｼ繝我ｻ倥″・・
  2. `draft_capabilities` 窶・謇謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚縺ｮ繝峨Λ繝輔ヨ謠仙・・・earch 2蝗樊悴貅縺ｯ繝悶Ο繝・け縲∵ｧ矩繝舌Μ繝・・繧ｷ繝ｧ繝ｳ蜀・鳩・・
  3. `request_critique` 窶・蛻･ LLM・・onnet・峨↓繧医ｋ蜩∬ｳｪ謇ｹ隧包ｼ・隕ｳ轤ｹ: 謇謖∝刀蟇・ｺｦ/閭ｽ蜉帶紛蜷・陦悟虚譛臥畑諤ｧ/繧ｭ繝｣繝ｩ蝗ｺ譛画ｧ/蜈ｷ菴捺ｧ・・
  4. `self_reflect` 窶・縲梧─諠・噪豺ｱ縺ｿ繝ｻ蝗ｺ譛画ｧ繝ｻ陦悟虚縺ｮ螳溽畑諤ｧ縲阪ｒ閾ｪ蝠上☆繧句・逵・ｼ・ritique pass 蠕後・縺ｿ・・
  5. `submit_final_capabilities` 窶・critique + self_reflect 荳｡譁ｹ pass 蠕後・縺ｿ謠仙・蜿ｯ
- **繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け陦悟虚謖・・**: 繝ｪ繧ｵ繝ｼ繝・search_web ﾃ・蝗樔ｻ･荳・ 竊・繝峨Λ繝輔ヨ 竊・謇ｹ隧・竊・蜀・怐 竊・謠仙・ 縺ｮ5繝輔ぉ繝ｼ繧ｺ蜴ｳ螳・
- **Phase D 邨ｱ蜷・*: Step 1-2 縺ｮ gather 縺九ｉ `caps_task` 繧帝勁蜴ｻ縺励ヾtep 2.5 縺ｨ縺励※ `CharacterCapabilitiesAgent.run()` 繧堤峡遶句ｮ溯｡・
- **繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ**: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け繝ｫ繝ｼ繝怜､ｱ謨玲凾縺ｯ one-shot JSON 逕滓・縺ｫ蛻・ｊ譖ｿ縺茨ｼ亥ｾ梧婿莠呈鋤邯ｭ謖・ｼ・
- **險ｭ險亥次蜑・*: 縲碁ｫ伜刀雉ｪ繧ｿ繧ｹ繧ｯ縺ｯ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥喧縺励仝eb 讀懃ｴ｢縺ｫ繧医ｋ莠句燕隱ｿ譟ｻ縺ｨ螟壼ｱ､蜩∬ｳｪ繧ｲ繝ｼ繝医〒險ｭ險医・蟇・ｺｦ繧剃ｿ晁ｨｼ縺吶ｋ縲阪ヱ繧ｿ繝ｼ繝ｳ繧・CharacterCapabilities 縺ｫ繧る←逕ｨ縲・

### Stage 32: `_generate_diary` NameError菫ｮ豁｣ + linguistic_expression 縺ｮ user_message 譏守､ｺ豕ｨ蜈･

**(a) 蠖灘・縺ｮ險ｭ險・*: `_build_voice_context()` 縺・`linguistic_expression` 縺九ｉ讒狗ｯ峨＠縺溷｣ｰ縺ｮ譁・ц・・oice・峨・ `system_prompt` 縺ｮ `縲占ｨ隱樒噪謖・ｴ具ｼ亥宍螳井ｺ矩・ｼ峨捜voice}` 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ縺ｫ縺ｮ縺ｿ豕ｨ蜈･縺輔ｌ縺ｦ縺・◆縲Ａuser_message` 縺ｫ縺ｯ `linguistic_expression` 縺ｫ髢｢騾｣縺吶ｋ繧ｳ繝ｳ繝・く繧ｹ繝医ヶ繝ｭ繝・け縺悟ｭ伜惠縺励↑縺九▲縺溘ゅ∪縺溘～_generate_diary()` 縺ｮ user_message 讒狗ｯ臥ｮ・園・・ine 1484・峨〒 `normative_context` 縺ｨ `protagonist_plan_note` 縺悟盾辣ｧ縺輔ｌ縺ｦ縺・◆縺後√％繧後ｉ縺ｮ螟画焚縺ｯ蛻･繝｡繧ｽ繝・ラ (`_integration()`, 邏・line 802) 縺ｧ螳夂ｾｩ縺輔ｌ縺ｦ縺翫ｊ縲～_generate_diary()` 縺ｮ繝ｭ繝ｼ繧ｫ繝ｫ繧ｹ繧ｳ繝ｼ繝励↓縺ｯ蟄伜惠縺励↑縺九▲縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 
- **NameError 繝舌げ**: Python 縺ｮ繧ｹ繧ｳ繝ｼ繝励Ν繝ｼ繝ｫ荳翫√け繝ｩ繧ｹ繝｡繧ｽ繝・ラ髢薙〒繝ｭ繝ｼ繧ｫ繝ｫ螟画焚縺ｯ蜈ｱ譛峨＆繧後↑縺・Ａnormative_context` 縺ｨ `protagonist_plan_note` 縺ｯ `_generate_diary()` 蜀・〒譛ｪ螳夂ｾｩ縺ｮ縺溘ａ縲∵律險倡函謌仙ｮ溯｡梧凾縺ｫ蠢・★ `NameError` 縺檎匱逕溘＠縺ｦ縺・◆縲・
- **險隱樒噪陦ｨ迴ｾ繝・・繧ｿ縺ｮ莨晞＃荳崎ｶｳ**: `system_prompt` 縺ｸ縺ｮ豕ｨ蜈･縺縺代〒縺ｯ縲∫音縺ｫ Gemini 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ迺ｰ蠅・ｸ九ｄ髟ｷ縺・system_prompt 縺ｧ繝・・繧ｿ縺悟ｸ瑚埋蛹悶☆繧九Μ繧ｹ繧ｯ縺後≠縺｣縺溘ＡLinguisticExpressionWorker` 縺檎ｲｾ蟇・↓險ｭ險医＠縺滓嶌縺肴婿險ｭ螳夲ｼ井ｸ莠ｺ遘ｰ繝ｻ蜿｣逋悶・譌･險倥ヨ繝ｼ繝ｳ繝ｻ遨ｺ豌玲─遲会ｼ峨ｒ縲∵律險倡函謌・AI 縺檎｢ｺ螳溘↓蜿ら・縺ｧ縺阪ｋ繧医≧ user_message 縺ｫ繧よ・遉ｺ逧・↓貂｡縺吝ｿ・ｦ√′縺ゅ▲縺溘・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **NameError 隗｣豸・*: `_generate_diary()` 縺ｮ蜀帝ｭ・・oice/event_summaries 螳夂ｾｩ逶ｴ蠕鯉ｼ峨↓ `normative_context` 縺ｨ `protagonist_plan_note` 繧呈・遉ｺ逧・↓螳夂ｾｩ縲Ａnormative_context` 縺ｯ `self.package.micro_parameters` 縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷医↓ `ideal_self` 縺ｨ `ought_self` 縺九ｉ讒狗ｯ峨Ａprotagonist_plan_note` 縺ｯ譌･險倥さ繝ｳ繝・く繧ｹ繝医〒縺ｯ荳崎ｦ√↑縺溘ａ遨ｺ譁・ｭ励〒螳夂ｾｩ縲・
- **險隱樒噪陦ｨ迴ｾ縺ｮ user_message 譏守､ｺ豕ｨ蜈･**: `voice_section = wrap_context('險隱樒噪陦ｨ迴ｾ譁ｹ豕包ｼ域怙驥崎ｦ・窶・蠢・★螳医ｋ縺薙→・・, voice, 'diary')` 繧・user_message 縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝医ヶ繝ｭ繝・け縺ｫ霑ｽ蜉・・oice 縺檎ｩｺ縺ｧ縺ｪ縺・ｴ蜷医・縺ｿ・峨ゅ％繧後↓繧医ｊ system_prompt 縺ｨ user_message 縺ｮ荳｡譁ｹ縺ｫ險隱樒噪陦ｨ迴ｾ繝・・繧ｿ縺悟ｭ伜惠縺励∽ｺ碁㍾縺ｮ遒ｺ螳溘↑蜿ら・縺御ｿ晁ｨｼ縺輔ｌ繧九・
- **險ｭ險亥次蜑・*: 縲後く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ險隱樒噪謖・ｴ九・ system_prompt・郁｡悟虚隕冗ｯ・→縺励※・峨→ user_message・亥盾辣ｧ縺吶∋縺阪さ繝ｳ繝・く繧ｹ繝医→縺励※・峨・蜿梧婿縺ｫ豕ｨ蜈･縺励√←縺｡繧峨・邨瑚ｷｯ縺ｧ繧ら｢ｺ螳溘↓蜿ら・蜿ｯ閭ｽ縺ｫ縺吶ｋ縲阪・

### Stage 28: Creative Director 縺ｸ縺ｮ CapabilitiesHints 霑ｽ蜉

**(a) 蠖灘・險ｭ險・*: Stage 27 縺ｧ CharacterCapabilities 繧・Phase D 縺ｧ逕滓・縺吶ｋ髫帙∵婿蜷第ｧ縺ｮ襍ｷ轤ｹ縺ｯ `concept_package` 縺ｮ JSON 蜈ｨ菴薙→繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ縺ｮ縺ｿ縲・reative Director 縺ｯ `psychological_hints`・域ｰ苓ｳｪ繝ｻ萓｡蛟､隕ｳ縺ｮ譁ｹ蜷第ｧ・峨ｒ蜃ｺ蜉帙＠縺ｦ縺・◆縺後√後←繧薙↑謇謖∝刀繝ｻ閭ｽ蜉帙′蠢・ｦ√°縲阪→縺・≧ capabilities 縺ｮ譁ｹ蜷第ｧ繝偵Φ繝医・荳蛻・・蜉帙＠縺ｦ縺・↑縺九▲縺溘１hase D 縺ｮ capabilities 繝ｯ繝ｼ繧ｫ繝ｼ縺ｯ蜈ｨ繧ｳ繝ｳ繝・く繧ｹ繝医°繧画囓鮟咏噪縺ｫ謗ｨ隲悶☆繧九＠縺九↑縺上，reative Director 縺ｮ諢丞峙縺悟香蛻・↓蜿肴丐縺輔ｌ繧九°縺御ｸ咲｢ｺ螳溘□縺｣縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: Creative Director 縺ｯ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ Want/Need/Ghost 讒矩繧呈怙繧よｷｱ縺冗炊隗｣縺励※縺・ｋ遶句ｴ縺ｧ縺ゅｊ縲√後％縺ｮ莠ｺ迚ｩ縺梧戟縺｡豁ｩ縺上∋縺阪ｂ縺ｮ縲阪檎黄隱槭↓驥崎ｦ√↑閭ｽ蜉帙阪悟崋譛峨・陦悟虚繝代ち繝ｼ繝ｳ縲阪↓縺､縺・※縺ｮ譁ｹ蜷第ｧ繧呈・遉ｺ逧・↓險ｭ險医〒縺阪ｋ縲よ囓鮟咏噪縺ｪ謗ｨ隲悶ｈ繧翫ｂ縲，reative Director 縺梧・遉ｺ逧・↓ `capabilities_hints` 繧定ｨｭ險医＠ Phase D 縺後◎繧後ｒ襍ｷ轤ｹ縺ｨ縺吶ｋ譁ｹ縺後∫黄隱樊紛蜷域ｧ縺ｮ鬮倥＞謇謖∝刀繝ｻ閭ｽ蜉帙′逕滓・縺輔ｌ繧九・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **`CapabilitiesHints` 繝｢繝・Ν譁ｰ險ｭ** (`backend/models/character.py`): `key_possessions_hint`・域園謖∝刀縺ｮ譁ｹ蜷第ｧ・峨～core_abilities_hint`・郁・蜉帙・譁ｹ蜷第ｧ・峨～signature_actions_hint`・郁｡悟虚繝代ち繝ｼ繝ｳ縺ｮ譁ｹ蜷第ｧ・峨・3繝輔ぅ繝ｼ繝ｫ繝峨ＡConceptPackage.capabilities_hints` 縺ｨ縺励※蠕梧婿莠呈鋤繝輔ぅ繝ｼ繝ｫ繝峨〒霑ｽ蜉・医ョ繝輔か繝ｫ繝育ｩｺ・峨・
- **Creative Director 蜃ｺ蜉帙せ繧ｭ繝ｼ繝樊峩譁ｰ** (`director.py`): SYSTEM_PROMPT 縺ｮ JSON 蜃ｺ蜉帙↓ `capabilities_hints` 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉縲ょ推繝輔ぅ繝ｼ繝ｫ繝峨↓縲檎黄隱槭ｄ諢滓ュ逧・э蜻ｳ縺ｨ謗･邯壹☆繧九ｂ縺ｮ繧貞性繧√ｋ縲咲ｭ峨・險ｭ險域欠遉ｺ繧剃ｻ倩ｨ倥・
- **謇ｹ隧輔メ繧ｧ繝・け繝ｪ繧ｹ繝域峩譁ｰ**: SELF_CRITIQUE_PROMPT 縺ｮ [F] 螳溯｣・庄閭ｽ諤ｧ繝√ぉ繝・け縺ｫ縲慶apabilities_hints 縺ｮ3繝輔ぅ繝ｼ繝ｫ繝峨′繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ閨ｷ讌ｭ繝ｻ萓｡蛟､隕ｳ繝ｻwant 縺ｨ謨ｴ蜷医＠縺ｦ縺・ｋ縺九阪ｒ霑ｽ蜉縲・
- **Phase D 縺ｸ縺ｮ譏守､ｺ逧・ｳｨ蜈･** (`phase_d/orchestrator.py`): `_full_context()` 蜀・〒 `capabilities_hints` 縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷医↓蟆ら畑繝・く繧ｹ繝医そ繧ｯ繧ｷ繝ｧ繝ｳ・・縲燭reative Director capabilities_hints縲疏・峨→縺励※繧ｳ繝ｳ繝・く繧ｹ繝医↓霑ｽ蜉縲ＡCHARACTER_CAPABILITIES_PROMPT` 縺ｮ蜀帝ｭ縺ｫ hints 繧定ｵｷ轤ｹ縺ｨ縺励※蜿ら・縺吶ｋ譌ｨ縺ｮ謖・､ｺ繧定ｿｽ蜉縲・
- **險ｭ險亥次蜑・*: Creative Director 竊・Phase D 縺ｸ縺ｮ諠・ｱ騾｣骼悶ｒ psychological_hints 縺ｨ蜷梧ｧ倥・繝代ち繝ｼ繝ｳ縺ｧ capabilities 縺ｫ繧よ僑蠑ｵ縲ゆｸ贋ｽ崎ｨｭ險郁・・諢丞峙縺御ｸ倶ｽ阪Ρ繝ｼ繧ｫ繝ｼ縺ｫ譏守､ｺ逧・↓莨晞＃縺輔ｌ繧区ｧ矩繧堤ｶｭ謖√・

### Stage 27: CharacterCapabilities・域園謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚・峨・霑ｽ蜉

**(a) 蠖灘・險ｭ險・*: Phase D 縺ｯ WorldContext繝ｻSupportingCharacters 縺ｮ2繧ｿ繧ｹ繧ｯ繧剃ｸｦ蛻礼函謌舌☆繧九・縺ｿ縺ｧ縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺後悟ｮ滄圀縺ｫ菴輔ｒ謖√▲縺ｦ縺・ｋ縺九阪御ｽ輔′縺ｧ縺阪ｋ縺九阪御ｽ輔ｒ縺ｨ繧後ｋ縺九阪→縺・≧蜈ｷ菴鍋噪縺ｪ諠・ｱ繧剃ｸ蛻・函謌舌・菫晄戟縺励※縺・↑縺九▲縺溘り｡悟虚豎ｺ螳壹お繝ｼ繧ｸ繧ｧ繝ｳ繝医・譌･險倡函謌舌お繝ｼ繧ｸ繧ｧ繝ｳ繝医・縲√・繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繧・・莨晉噪繧ｨ繝斐た繝ｼ繝峨ｒ蜿ら・縺励※陦悟虚繧呈ｱｺ螳壹＠縺ｦ縺・◆縺後∵園謖∝刀繝ｻ驕灘・繝ｻ繧ｹ繧ｭ繝ｫ縺ｸ縺ｮ蜿ら・縺ｯ荳榊庄閭ｽ縺縺｣縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 陦悟虚豎ｺ螳壹・蜈ｷ菴捺ｧ繧帝ｫ倥ａ繧九◆繧√↓縺ｯ縲√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺悟ｮ滄圀縺ｫ謇句・縺ｫ謖√▽驕灘・繝ｻ霄ｫ縺ｫ縺､縺代※縺・ｋ繧ｹ繧ｭ繝ｫ繝ｻ蜿悶ｌ繧玖｡悟虚縺ｮ驕ｸ謚櫁い繧偵お繝ｼ繧ｸ繧ｧ繝ｳ繝医′蜿ら・縺ｧ縺阪ｋ蠢・ｦ√′縺ゅ▲縺溘ゆｾ九∴縺ｰ縲梧焔蟶ｳ繧呈戟縺｡豁ｩ縺剰ｨ倩・く繝｣繝ｩ縲阪′縲後◎縺ｮ蝣ｴ縺ｧ繝｡繝｢繧偵→繧九阪→縺・≧蜈ｷ菴鍋噪縺ｪ陦悟虚繧貞叙繧九↓縺ｯ縲∵園謖∝刀繝ｻ閭ｽ蜉帙・蜿ら・縺御ｸ榊庄谺縲ゅ∪縺溘∵ュ譎ｯ謠丞・縺ｧ繧よ園謖∝刀縺瑚・辟ｶ縺ｫ逋ｻ蝣ｴ縺吶ｋ縺薙→縺ｧ謠丞・縺ｮ蟇・ｺｦ縺悟｢励☆縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **4繝｢繝・Ν霑ｽ蜉** (`backend/models/character.py`): `PossessedItem`・域園謖∝刀・峨～CharacterAbility`・郁・蜉幢ｼ峨～AvailableAction`・亥庄閭ｽ陦悟虚・峨～CharacterCapabilities`・・縺､繧堤ｵｱ蜷医☆繧九さ繝ｳ繝・リ・峨ＡCharacterPackage.character_capabilities: Optional[CharacterCapabilities]` 縺ｨ縺励※蠕梧婿莠呈鋤繝輔ぅ繝ｼ繝ｫ繝峨ｒ霑ｽ蜉縲・
- **Phase D 荳ｦ蛻礼函謌占ｿｽ蜉** (`phase_d/orchestrator.py`): Step 1-2 縺ｮ荳ｦ蛻・gather 縺ｫ `caps_task`・・CHARACTER_CAPABILITIES_PROMPT`縲）son_mode=True・峨ｒ3縺､逶ｮ縺ｨ縺励※霑ｽ蜉縲らｵ先棡繧・`PossessedItem/CharacterAbility/AvailableAction` 縺ｸ繝代・繧ｹ縺・`self.character_capabilities` 縺ｫ譬ｼ邏阪Ａupstream_context`・・eeklyEventWriter 縺ｸ縺ｮ繧ｳ繝ｳ繝・く繧ｹ繝茨ｼ峨↓繧・capabilities 繝・く繧ｹ繝医ｒ霑ｽ蜉縺励√う繝吶Φ繝育函謌先凾縺ｫ謇謖∝刀繝ｻ閭ｽ蜉帙ｒ蜿ら・蜿ｯ閭ｽ縺ｫ縲・
- **Master Orchestrator菫晏ｭ・* (`master_orchestrator/orchestrator.py`): `_execute_phase_with_retry` 蜀・〒 `self._last_orch = orch` 繧定ｨｭ螳壹＠縲￣hase D 螳御ｺ・ｾ後↓ `self.package.character_capabilities = self._last_orch.character_capabilities` 縺ｧ繝代ャ繧ｱ繝ｼ繧ｸ縺ｫ譬ｼ邏阪・
- **Daily Loop 縺ｸ縺ｮ謚募・** (`daily_loop/orchestrator.py`): `_build_capabilities_context()` 繝｡繧ｽ繝・ラ繧呈眠險ｭ・域園謖∝刀繝ｻ閭ｽ蜉帙・陦悟虚繧偵ユ繧ｭ繧ｹ繝亥喧・峨Ａ_integration()` 縺ｮ user_message 縺ｫ `wrap_context('謇謖∝刀繝ｻ閭ｽ蜉・, ..., 'integration')` 繧定ｿｽ蜉縲～_generate_diary()` 縺ｮ user_message 縺ｫ繧・`wrap_context('謇謖∝刀繝ｻ閭ｽ蜉・, ..., 'diary')` 繧定ｿｽ蜉・井ｸ｡譁ｹ縺ｨ繧・capabilities 縺悟ｭ伜惠縺励↑縺・ｴ蜷医・繧ｹ繧ｭ繝・・・峨・
- **MD 蜃ｺ蜉・* (`md_storage.py`): `save_character_profile()` 縺ｫ縲・# 4.5. 謇謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚縲阪そ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉・・pisodes 縺ｨ Events 縺ｮ髢難ｼ峨よ園謖∝刀繝ｻ閭ｽ蜉帙・陦悟虚縺ｮ3繧ｵ繝悶そ繧ｯ繧ｷ繝ｧ繝ｳ繧貞句挨縺ｫ蜃ｺ蜉帙・
- **繧ｳ繝ｳ繝・く繧ｹ繝郁ｪｬ譏手ｿｽ蜉** (`context_descriptions.py`): 縲梧園謖∝刀繝ｻ閭ｽ蜉帙阪く繝ｼ縺ｫ default/integration/diary 縺ｮ3繝ｭ繝ｼ繝ｫ隱ｬ譏趣ｼ・hat/why/how・峨ｒ霑ｽ蜉縲・
- **蠕梧婿莠呈鋤**: `character_capabilities: Optional[CharacterCapabilities] = None` 縺ｮ縺溘ａ縲∵里蟄倥メ繧ｧ繝・け繝昴う繝ｳ繝医ｒ繝ｭ繝ｼ繝峨＠縺ｦ繧・None 縺ｧ豁｣蟶ｸ蜍穂ｽ懊・

### Stage 24: Opus繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ蜈医ｒGemini 3.1 Pro縺ｫ譖ｴ譁ｰ

**(a) 蠖灘・險ｭ險・*: `_call_llm_once()` 縺ｧ `tier="opus"` 縺ｾ縺溘・ `tier="sonnet"` 縺ｮ縺ｩ縺｡繧峨〒繧ょ､ｱ謨玲凾縺ｫ蜷後§ `_call_gemini_with_flash_fallback()` 繝倥Ν繝代・繧貞他縺ｳ蜃ｺ縺吶ゅ％縺ｮ繝倥Ν繝代・縺ｯ **蟶ｸ縺ｫ** `LLMModels.GEMINI_2_5_PRO` 縺ｧGemini繧定ｩｦ陦後＠縺ｦ縺・◆縲ゅ▽縺ｾ繧翫・ｫ伜刀雉ｪ縺ｪ Opus 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′螟ｱ謨励＠縺溷ｴ蜷医ｂ縲∽ｽ弱さ繧ｹ繝医↑ Sonnet 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′螟ｱ謨励＠縺溷ｴ蜷医ｂ縲∝酔縺・Gemini 2.5 Pro 縺ｸ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺励※縺・◆縲・

**(b) 螟画峩繝ｻ譬ｹ諡**: Gemini 2.5 Pro 縺九ｉ Gemini 3.1 Pro 縺後Μ繝ｪ繝ｼ繧ｹ縺輔ｌ縲√ｈ繧企ｫ俶ｧ閭ｽ繝ｻ鬮伜刀雉ｪ縺ｨ縺ｪ縺｣縺溘０pus 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ磯ｫ伜刀雉ｪ繝・ぅ繧｢・峨′ Claude 縺ｧ螟ｱ謨励＠縺溷ｴ蜷医√ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ蜈医ｂ鬮俶ｧ閭ｽ縺ｪ Gemini 3.1 Pro 縺ｫ縺吶ｋ縺薙→縺ｧ縲∝刀雉ｪ謳榊､ｱ繧呈怙蟆丞喧縺ｧ縺阪ｋ縺ｨ蛻､譁ｭ縲ゆｸ譁ｹ縲ヾonnet 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ井ｽ弱さ繧ｹ繝医ユ繧｣繧｢・峨・繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｯ譌｢縺ｫ Gemini 2.5 Pro 縺ｧ蜊∝・縺ｪ諤ｧ閭ｽ繧偵ｂ縺､縺溘ａ縲√さ繧ｹ繝医・繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ縺ｮ繝舌Λ繝ｳ繧ｹ縺九ｉ螟画峩荳崎ｦ√ゅ∪縺・`tier="gemini"` 縺ｮ逶ｴ謗･蜻ｼ縺ｳ蜃ｺ縺暦ｼ域怙菴弱さ繧ｹ繝医ユ繧｣繧｢・峨ｂ Gemini 2.5 Pro 縺ｮ縺ｾ縺ｾ邯ｭ謖√・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- `LLMModels` 縺ｫ譁ｰ螳壽焚 `GEMINI_3_1_PRO = "models/gemini-3.1-pro"` 繧定ｿｽ蜉
- `_call_gemini_with_flash_fallback()` 髢｢謨ｰ繧ｷ繧ｰ繝阪メ繝｣縺ｫ `gemini_model: Optional[str] = None` 繝代Λ繝｡繝ｼ繧ｿ繧定ｿｽ蜉
  - 繝・ヵ繧ｩ繝ｫ繝医・ `LLMModels.GEMINI_2_5_PRO`・・onnet/Gemini tier逕ｨ・・
  - 髢｢謨ｰ蜀・〒 `if gemini_model is None: gemini_model = LLMModels.GEMINI_2_5_PRO`
- Opus 螟ｱ謨玲凾縺ｮ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ蜻ｼ縺ｳ蜃ｺ縺暦ｼ郁｡・431-440・峨〒 `gemini_model=LLMModels.GEMINI_3_1_PRO` 繧呈欠螳・
  - ```python
    gemini_model = LLMModels.GEMINI_3_1_PRO if tier == "opus" else None
    return await _call_gemini_with_flash_fallback(
        ...,
        gemini_model=gemini_model,
    )
    ```
- 繝ｭ繧ｰ繝｡繝・そ繝ｼ繧ｸ繧ょ虚逧・喧・啻f"[call_llm] {gemini_model} quota exceeded. Falling back to Gemini 2.0 Flash."` 縺ｧ螳滄圀縺ｮ繝｢繝・Ν蜷阪ｒ蜃ｺ蜉・
- **險ｭ險亥次蜑・*: 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ蜈医ｒ繝・ぅ繧｢蛻･縺ｫ蟾ｮ蛻･蛹悶＠縲∝推繝・ぅ繧｢縺ｮ蜩∬ｳｪ隕∵ｱゅ↓蠢懊§縺滓怙驕ｩ縺ｪ繝｢繝・Ν繧貞牡繧雁ｽ薙※繧九ゅさ繧ｹ繝医・蜩∬ｳｪ縺ｮ繝舌Λ繝ｳ繧ｹ繧帝嚴螻､蛹悶☆繧・

### Stage 20: 繧ｻ繝ｼ繝悶・繧､繝ｳ繝井ｺ碁㍾菫晏ｭ倥・荳ｭ譁ｭ蜀埼幕縺ｮ遒ｺ螳溷喧

- **蟇ｾ雎｡/讖溯・**: 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・繝√ぉ繝・け繝昴う繝ｳ繝医・繝ｭ繝ｼ繝ｫ繝舌ャ繧ｯ蝠城｡御ｿｮ豁｣縲∵律險倥Ν繝ｼ繝励・package.json豌ｸ邯壼喧

- **(a) 蜈・・險ｭ險・*:
  - `MasterOrchestrator._checkpoint()`縺ｯ菫晏ｭ伜・蜷阪ｒ1縺､縺縺鷹∈謚・ Phase A-1螳御ｺ・燕縺ｯSID蜷搾ｼ井ｾ・ `SID_20260412_023236`・峨、-1螳御ｺ・ｾ後・繧ｭ繝｣繝ｩ蜷搾ｼ井ｾ・ `蜚千ｹｰ 繝昴・`・峨４ID繝輔か繝ｫ繝縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝医・A-1莉･髯阪〒莠悟ｺｦ縺ｨ譖ｴ譁ｰ縺輔ｌ縺ｪ縺九▲縺・
  - 譌･險倥Ν繝ｼ繝暦ｼ・ailyLoopOrchestrator・峨〒縺ｯ蜷Дay螳御ｺ・ｾ後↓ `short_term_memory/`, `mood_states/`, `key_memories/` 縺ｯ菫晏ｭ倥＆繧後※縺・◆縺後～package.json` 縺ｯ譖ｴ譁ｰ縺輔ｌ縺ｪ縺九▲縺・
  - `protagonist_plan`縺ｨ縺励※鄙梧律縺ｫ霑ｽ蜉縺輔ｌ縺溘う繝吶Φ繝茨ｼ・weekly_events_store.events`縺ｸ縺ｮ`append`・峨・繝｡繝｢繝ｪ荳翫□縺代↓蟄伜惠縺励∽ｸｭ譁ｭ蠕後・蜀埼幕譎ゅ↓豸域ｻ・＠縺ｦ縺・◆

- **(b) 螟画峩縺ｨ逅・罰**:
  - **繝ｭ繝ｼ繝ｫ繝舌ャ繧ｯ逋ｺ逕溘Γ繧ｫ繝九ぜ繝**: 繝ｦ繝ｼ繧ｶ繝ｼ縺郡ID蜷搾ｼ医そ繝・す繝ｧ繝ｳ髢句ｧ区凾縺ｫUI縺ｫ陦ｨ遉ｺ縺輔ｌ繧句錐蜑搾ｼ峨〒繝ｬ繧ｸ繝･繝ｼ繝縺吶ｋ縺ｨ縲ヾID繝輔か繝ｫ繝縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝茨ｼ・-1螳御ｺ・燕縺ｮ蛻晄悄迥ｶ諷具ｼ峨′隱ｭ縺ｿ霎ｼ縺ｾ繧後￣hase A-1縺九ｉ蜀咲函謌舌′蟋九∪繧九ゅ後Α繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繧・う繝吶Φ繝医・騾比ｸｭ縺ｾ縺ｧ逕滓・縺ｧ縺阪※縺・◆縺ｨ縺励※繧よ怙蛻昴・繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ逕滓・縺ｾ縺ｧ謌ｻ繧九阪→縺・≧迴ｾ雎｡縺ｮ譬ｹ譛ｬ蜴溷屏
  - **譌･險倥Ν繝ｼ繝励・蜀埼幕荳肴紛蜷・*: `package.json`譛ｪ譖ｴ譁ｰ縺ｫ繧医ｊ縲∝・髢区凾縺ｫ縺ｯ鄙梧律莠亥ｮ壹う繝吶Φ繝医′豸医∴縺溘が繝ｪ繧ｸ繝翫Ν縺ｮ繧､繝吶Φ繝医Μ繧ｹ繝医′隱ｭ縺ｿ霎ｼ縺ｾ繧後∽ｻ･髯阪・Day蜃ｦ逅・〒繧､繝吶Φ繝井ｸ崎ｶｳ縺檎函縺倥ｋ

- **(c) 謗｡逕ｨ縺励◆繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:
  - **`_checkpoint()` 莠碁㍾菫晏ｭ・*: SID蜷阪ヵ繧ｩ繝ｫ繝縺ｫ**蟶ｸ縺ｫ菫晏ｭ・*・医←縺ｮ繝輔ぉ繝ｼ繧ｺ縺ｧ繧ゑｼ峨＠縲√く繝｣繝ｩ蜷阪′蛻､譏弱＠縺ｦ縺・ｋ蝣ｴ蜷医・繧ｭ繝｣繝ｩ蜷阪ヵ繧ｩ繝ｫ繝縺ｫ繧・*霑ｽ蜉菫晏ｭ・*縲４ID繝ｻ繧ｭ繝｣繝ｩ蜷阪←縺｡繧峨〒繝ｬ繧ｸ繝･繝ｼ繝縺励※繧ょｸｸ縺ｫ譛譁ｰ迥ｶ諷九ｒ蜿門ｾ怜庄閭ｽ縺ｫ
  - **DailyLoopOrchestrator 蜷Дay螳御ｺ・ｾ後↓package.json譖ｴ譁ｰ**: `run()`縺ｮ蜷Дay繝ｫ繝ｼ繝玲忰蟆ｾ縺ｧ `package.json` 繧呈嶌縺榊・縺励Ｑrotagonist_plan繧､繝吶Φ繝医ｒ蜷ｫ繧譛譁ｰ迥ｶ諷九ｒ蜊ｳ譎よｰｸ邯壼喧
  - **run_diary_generation 螳御ｺ・ｾ後↓package.json菫晏ｭ・*: 繝ｫ繝ｼ繝怜ｮ御ｺ・ｾ後↓繧よ怙邨ら憾諷九ｒ `package.json` 縺ｫ譖ｸ縺榊・縺励∝ｮ悟・諤ｧ繧剃ｿ晁ｨｼ
  - **險ｭ險亥次蜑・*: 繝√ぉ繝・け繝昴う繝ｳ繝医・縲後←縺ｮ蜷榊燕縺ｧ繧｢繧ｯ繧ｻ繧ｹ縺輔ｌ縺ｦ繧よ怙譁ｰ迥ｶ諷九′蠕励ｉ繧後ｋ縲阪％縺ｨ繧剃ｿ晁ｨｼ縺吶ｋ縲ゆｿ晏ｭ倥さ繧ｹ繝医・2蛟阪□縺後√Ξ繧ｸ繝･繝ｼ繝螟ｱ謨励・繧ｳ繧ｹ繝茨ｼ亥・蜀咲函謌撰ｼ峨→豈碑ｼ・☆繧後・蝨ｧ蛟堤噪縺ｫ譛牙茜

### Stage 19: 繝・う繝ｪ繝ｼ繝ｭ繧ｰ隕∫ｴ・・險俶・繧ｷ繧ｹ繝・Β蜀崎ｨｭ險・

- **蟇ｾ雎｡/讖溯・**: 遏ｭ譛溯ｨ俶・繝・・繧ｿ繝吶・繧ｹ縺ｮ蜀崎ｨｭ險医∫ｿ梧律莠亥ｮ哂I縺ｮ螳溯｡碁・ｺ丞､画峩縲∵律險倥・迢ｬ遶汽B蛹・

- **(a) 蜈・・險ｭ險・*:
  - **螳溯｡碁・ｺ・*: 蜀・怐竊呈律險倡函謌絶・繝繝ｼ繝画峩譁ｰ竊談ey memory竊定ｨ俶・蝨ｧ邵ｮ竊堤ｿ梧律莠亥ｮ壺・繝繝ｼ繝営arry-over縲らｿ梧律莠亥ｮ哂I縺ｯ譌･險倡函謌舌・蠕後↓蜍穂ｽ懊＠縺ｦ縺翫ｊ縲∵律險倥・荳ｭ縺ｧ縲梧・譌･縺ｯ縺薙≧縺励◆縺・阪→縺・≧諢丞髄繧貞渚譏縺ｧ縺阪↑縺九▲縺・
  - **遏ｭ譛溯ｨ俶・繧ｽ繝ｼ繧ｹ**: `normal_area`縺ｮ繧ｽ繝ｼ繧ｹ縺ｯ譌･險倥ユ繧ｭ繧ｹ繝茨ｼ・diary.content`・峨〒縺ゅｊ縲∬｡悟虚繝ｭ繧ｰ縺ｮ隕∫ｴ・〒縺ｯ縺ｪ縺九▲縺・
  - **險俶・蝨ｧ邵ｮ**: `_compress_memories()`縺ｯ `one_day_ago`縺ｧ蝨ｧ邵ｮ縺ｪ縺励～two_days_ago`縺ｧLLM 2/3蝨ｧ邵ｮ・・200蟄励・縺ｿ・峨～three_plus_days_ago`縺ｧ200蟄玲枚蟄怜・蛻・ｊ謐ｨ縺ｦ縲ょｮ溘ョ繝ｼ繧ｿ縺ｧ縺ｯDay7譎らせ縺ｧDay1縺・00蟄玲ｮ句ｭ假ｼ井ｻ墓ｧ倥〒縺ｯ20-30蟄励〒縺ゅｋ縺ｹ縺搾ｼ・
  - **繝・う繝ｪ繝ｼ繝ｭ繧ｰ**: `daily_logs/Day_N.md`縺ｯ22-32KB縺ｮ蛹・峡逧・・繝ｼ繧ｯ繝繧ｦ繝ｳ繧｢繝ｼ繧ｫ繧､繝厄ｼ井ｺｺ髢鍋畑・峨〒縺ゅｊ縲√お繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ遏ｭ譛溯ｨ俶・縺ｨ縺励※縺ｯ菴ｿ逕ｨ縺輔ｌ縺ｦ縺・↑縺九▲縺・
  - **譌･險倥・謇ｱ縺・*: `diary_store`縺ｫ蜈ｨ譌･蛻・・譌･險倥ユ繧ｭ繧ｹ繝医ｒ闢・ｩ阪＠縲～_build_memory_context()`縺ｧ`normal_area`縺ｨ荳邱偵↓貂｡縺励※縺・◆・域律險倥→繝・う繝ｪ繝ｼ繝ｭ繧ｰ縺ｮ蛹ｺ蛻･縺ｪ縺暦ｼ・

- **(b) 螟画峩縺ｨ逅・罰**:
  - **鄙梧律莠亥ｮ壹ｒ譌･險倥・蜑阪↓遘ｻ蜍・*: 蜀・怐竊・*鄙梧律莠亥ｮ・*竊呈律險倡函謌舌・鬆・↓螟画峩縲らｿ梧律莠亥ｮ哂I縺ｮ蜈･蜉帙ｒ`diary`竊蛋events`・・ventPackage繝ｪ繧ｹ繝茨ｼ峨↓螟画峩縲よ律險倥・繝ｭ繝ｳ繝励ヨ縺ｫ縲梧・譌･縺ｮ莠亥ｮ壹阪そ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉縺励√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺梧律險倥・荳ｭ縺ｧ鄙梧律縺ｸ縺ｮ諢丞髄繝ｻ譛溷ｾ・・荳榊ｮ峨ｒ閾ｪ辟ｶ縺ｫ陦ｨ迴ｾ蜿ｯ閭ｽ縺ｫ
  - **DailyLogStore譁ｰ險ｭ**: 陦悟虚繝ｭ繧ｰ繧呈律蛻･繝輔か繝ｫ繝・・daily_logs/day_01/001_full.json`, `002_summary.json`...・峨〒邂｡逅・ゅお繝ｼ繧ｸ繧ｧ繝ｳ繝医↓縺ｯ蜷・律縺ｮ**譛譁ｰID繝輔ぃ繧､繝ｫ繧貞・縺ｦ蛟句挨縺ｫ**貂｡縺・
  - **LLM繝吶・繧ｹ谿ｵ髫守噪隕∫ｴ・*: 譌･險倡函謌舌・蠕後↓`_create_daily_log_and_summarize()`繧貞ｮ溯｡後ょｽ捺律縺ｮ蜈ｨ陦悟虚繝ｭ繧ｰ繧貞濠蛻・↓隕∫ｴ・＠縲・譌･莉･荳雁燕縺ｮ驕主悉譌･縺ｯ縺輔ｉ縺ｫ蜀崎ｦ∫ｴ・ｼ亥ｿ伜唆繝励Ο繧ｻ繧ｹ・・
  - **譌･險倥ｒ迢ｬ遶汽B縺ｨ縺励※蛻・屬**: `diaries/`繝輔か繝ｫ繝縺九ｉ隱ｭ縺ｿ霎ｼ縺ｿ縲√碁℃蜴ｻ縺ｮ譌･險倥〒縺吶ょ盾辣ｧ縺励∬ｨ蜿翫☆縺ｹ縺咲せ縺後≠繧後・閾ｪ辟ｶ縺ｫ隗ｦ繧後※縺上□縺輔＞縲阪→縺・≧謖・､ｺ莉倥″縺ｧ貂｡縺・
  - **`_build_memory_context()`繧貞・讒狗ｯ・*: key memory + 繝・う繝ｪ繝ｼ繝ｭ繧ｰ譛譁ｰ迚医ｒ縲檎洒譛溯ｨ俶・・域怙驥崎ｦ・ｼ峨阪→縺励※貂｡縺励・℃蜴ｻ縺ｮ譌･險倥・`_build_past_diary_context()`縺ｧ縲悟盾辣ｧ逕ｨ縲阪→縺励※蛻・屬

- **(c) 謗｡逕ｨ縺励◆繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:
  - **險俶・髫主ｱ､縺ｮ譏守｢ｺ蛹・*: 縲檎洒譛溯ｨ俶・・域怙驥崎ｦ・ｼ峨・ 繝・う繝ｪ繝ｼ繝ｭ繧ｰ隕∫ｴ・+ key memory縲√碁℃蜴ｻ縺ｮ譌･險假ｼ亥盾辣ｧ逕ｨ・峨・ 迢ｬ遶汽B縲ゅお繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺咎圀縺ｫ驥崎ｦ∝ｺｦ繧呈・遉ｺ
  - **谿ｵ髫守噪蠢伜唆**: 豈取律邏・濠蛻・↓蝨ｧ邵ｮ縺励∝商縺・律縺ｻ縺ｩ縺輔ｉ縺ｫ蜀崎ｦ∫ｴ・☆繧玖・辟ｶ縺ｪ蠢伜唆繝励Ο繧ｻ繧ｹ縲・LM縺梧э蜻ｳ逧・↓驥崎ｦ√↑驛ｨ蛻・ｒ谿九☆縺溘ａ縲∝腰邏斐↑譁・ｭ怜・蛻・ｊ謐ｨ縺ｦ繧医ｊ繧りｳｪ縺碁ｫ倥＞
  - **鄙梧律莠亥ｮ壹・蜈郁｡檎函謌・*: 險育判竊呈律險倥・鬆・↓縺吶ｋ縺薙→縺ｧ縲∵律險倥′縲梧険繧願ｿ斐ｊ + 譏取律縺ｸ縺ｮ螻墓悍縲阪→縺・≧閾ｪ辟ｶ縺ｪ讒矩縺ｫ縺ｪ繧・
  - **繝輔か繝ｫ繝蜀・ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・*: 蜷・律縺ｮ繝輔か繝ｫ繝縺ｫ001, 002, 003...縺ｨ繝舌・繧ｸ繝ｧ繝ｳ繧定塘遨阪＠縲∵怙譁ｰID繝輔ぃ繧､繝ｫ縺悟ｸｸ縺ｫ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓貂｡縺輔ｌ繧狗洒譛溯ｨ俶・縲る℃蜴ｻ縺ｮ繝舌・繧ｸ繝ｧ繝ｳ繧ゆｿ晄戟縺輔ｌ繧九◆繧∬ｿｽ霍｡蜿ｯ閭ｽ

### 22. 險隱櫁｡ｨ迴ｾ縺ｮ螳悟・豢ｻ逕ｨ縺ｨ隧ｳ邏ｰ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ

- **(a) 蠖灘・險ｭ險・*: Phase A-1縺ｮ LinguisticExpressionWorker 縺ｧ縲御ｸ莠ｺ遘ｰ縲阪悟哨逋悶阪梧枚譛ｫ陦ｨ迴ｾ縲阪梧ｼ｢蟄励・繧峨′縺ｪ蛯ｾ蜷代阪碁∩縺代ｋ隱槫ｽ吶阪悟幕繧頑婿縺ｮ髮ｰ蝗ｲ豌励阪御ｼ夊ｩｱ繧ｹ繧ｿ繧､繝ｫ縲阪梧─諠・｡ｨ迴ｾ蛯ｾ蜷代阪梧律險倥・繝医・繝ｳ縲阪梧律險倥・讒区・蛯ｾ蜷代阪悟・逵√・豺ｱ縺輔阪梧嶌縺・逵∫払縺吶ｋ蜀・ｮｹ縲阪梧律險倥・遨ｺ豌玲─縲阪→縺・▲縺・3蛟九・隧ｳ邏ｰ縺ｪ險隱櫁｡ｨ迴ｾ諠・ｱ繧堤函謌舌＠縺ｦ縺・◆縲ゅ◆縺縺励％繧後ｉ縺ｮ蜈ｨ縺ｦ縺梧律險倡函謌先凾縺ｫ豢ｻ逕ｨ縺輔ｌ縺ｦ縺・↑縺九▲縺溘・

- **(b) 螟画峩繝ｻ譬ｹ諡**: LinguisticExpression 縺ｮ讒矩螳夂ｾｩ縺ｫ縺ｯ縲御ｺ御ｺｺ遘ｰ縺ｮ菴ｿ縺・・縺托ｼ郁ｦｪ縺励＞莠ｺ/逶ｮ荳・遏･繧峨↑縺・ｺｺ・峨阪檎ｵｵ譁・ｭ励・險伜捷縺ｮ菴ｿ逕ｨ蛯ｾ蜷代阪瑚・蝠丞ｽ｢蠑上・鬆ｻ蠎ｦ縲阪梧ｯ泌湊繝ｻ蜿崎ｪ槭・鬆ｻ蠎ｦ縲阪→縺・≧4縺､縺ｮ繝輔ぅ繝ｼ繝ｫ繝峨′蟄伜惠縺励◆縺ｫ繧ゅ°縺九ｏ繧峨★縲～_build_voice_context()`繝｡繧ｽ繝・ラ縺ｧ縺ｯ蜑崎・・9鬆・岼縺縺代ｒ讒狗ｯ峨＠縺ｦ縺・◆縲ゅ▽縺ｾ繧顔函謌舌＆繧後◆險隱櫁｡ｨ迴ｾ險ｭ螳壹・70%縺励°譌･險倥・繝ｭ繝ｳ繝励ヨ縺ｫ貂｡縺輔ｌ縺ｦ縺翫ｉ縺壹√く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ險隱樒音諤ｧ縺悟香蛻・↓蜿肴丐縺輔ｌ縺ｦ縺・↑縺九▲縺溘ゅ∪縺溘∵律險倥ラ繝ｩ繝輔ヨ謠仙・譎ゅ↓縲瑚ｨ隱槭Ν繝ｼ繝ｫ・・heck_diary_rules・俄・ 隨ｬ荳芽・ｦ也せ・・hird_party_review・峨阪・2谿ｵ髫弱ご繝ｼ繝医□縺代〒縲´inguisticExpression 縺ｮ邏ｰ縺九＞隕∫ｴ・育ｵｵ譁・ｭ嶺ｽｿ逕ｨ蛯ｾ蜷代∬・蝠城ｻ蠎ｦ縺ｪ縺ｩ・峨∪縺ｧ縺ｯ讀懆ｨｼ縺輔ｌ縺ｦ縺・↑縺九▲縺溘・

- **(c) 謗｡逕ｨ縺励◆繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:
  - **螳悟・縺ｪ險隱櫁｡ｨ迴ｾ莨晄眺**: `_build_voice_context()`繧呈僑蠑ｵ縺励∽ｺ御ｺｺ遘ｰ繝ｻ邨ｵ譁・ｭ励・閾ｪ蝠城ｻ蠎ｦ繝ｻ豈泌湊鬆ｻ蠎ｦ繧貞性繧蜈ｨ13鬆・岼繧偵ユ繧ｭ繧ｹ繝亥ｽ｢蠑上〒讒矩蛹悶＠縺ｦ譌･險倥す繧ｹ繝・Β繝励Ο繝ｳ繝励ヨ縺ｫ豕ｨ蜈･縲ゅ％繧後↓繧医ｊ LinguisticExpression 諠・ｱ縺・00%豢ｻ逕ｨ縺輔ｌ繧・
  - **險隱櫁｡ｨ迴ｾ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ螻､縺ｮ霑ｽ蜉**: `LinguisticExpressionValidator`繧ｯ繝ｩ繧ｹ繧呈眠險ｭ縲よ律險倥ユ繧ｭ繧ｹ繝医′莉･荳九ｒ螳医▲縺ｦ縺・ｋ縺玖ｩｳ邏ｰ縺ｫ讀懆ｨｼ: 荳莠ｺ遘ｰ縺ｮ邨ｱ荳縲・∩縺代ｋ隱槫ｽ吶・譛臥┌縲∝哨逋悶・閾ｪ辟ｶ縺ｪ蜃ｺ迴ｾ縲∵枚譛ｫ陦ｨ迴ｾ縺ｮ繝舌Μ繧ｨ繝ｼ繧ｷ繝ｧ繝ｳ縲∵ｼ｢蟄励・繧峨′縺ｪ蛯ｾ蜷代∫ｵｵ譁・ｭ嶺ｽｿ逕ｨ蛯ｾ蜷代∬・蝠丞ｽ｢蠑上・鬆ｻ蠎ｦ縲∵ｯ泌湊繝ｻ蜿崎ｪ槭・鬆ｻ蠎ｦ縲∵律險倥・繝医・繝ｳ縲∝・逵√・豺ｱ縺・
  - **3谿ｵ髫弱ご繝ｼ繝亥喧**: 譌･險俶署蜃ｺ繝輔Ο繝ｼ 繧偵慶heck_diary_rules・亥渕譛ｬ逧・↑險隱槭Ν繝ｼ繝ｫ・・竊・validate_linguistic_expression・郁ｩｳ邏ｰ縺ｪ險隱櫁｡ｨ迴ｾ・・竊・third_party_review・郁ｪｭ縺ｿ迚ｩ縺ｨ縺励※縺ｮ蜩∬ｳｪ・峨阪・3谿ｵ髫弱↓縲らｬｬ2谿ｵ髫弱〒邏ｰ縺九＞險隱樒音諤ｧ縺ｮ驕ｵ螳医ｒ蜴ｳ蟇・↓讀懆ｨｼ縺励∽ｿｮ豁｣繧｢繝峨ヰ繧､繧ｹ繧定ｿ斐☆

### Stage 33: 螻･豁ｴ繝ｭ繝ｼ繝画凾縺ｮ譌･險倥ョ繝ｼ繧ｿ縺ｮ邨ｱ蜷郁｡ｨ遉ｺ縺ｨUI繝励Ο繧ｰ繝ｬ繧ｹ迥ｶ諷九・菫ｮ豁｣

- **(a) 蠖灘・險ｭ險・*: 
  - 繝｡繝九Η繝ｼ繝代ロ繝ｫ縺九ｉ縲檎函謌先ｸ医∩繝代ャ繧ｱ繝ｼ繧ｸ縲阪ｒ繝ｭ繝ｼ繝峨☆繧矩未謨ｰ・・frontend/api/get_package`, frontend `loadPackage`・峨・縲√ヱ繝・こ繝ｼ繧ｸJSON縺ｨ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繝・・繧ｿ縺励°繝ｭ繝ｼ繝峨＠縺ｦ縺翫ｉ縺壹∵律險倥・蜀・ｮｹ縺ｯ隱ｭ縺ｿ霎ｼ縺ｾ繧後※縺・↑縺九▲縺溘ゅ◎縺ｮ邨先棡縲∵律險倥′譌｢縺ｫ逕滓・縺輔ｌ縺ｦ縺・ｋ縺ｮ縺ｫ縲√梧律險倥阪ち繝悶ｒ髢九￥縺ｨ遨ｺ迥ｶ諷具ｼ医梧律險倥す繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ繧帝幕蟋九☆繧九阪・繧ｿ繝ｳ・峨′蜀榊ｺｦ陦ｨ遉ｺ縺輔ｌ縺ｦ縺励∪縺・∝・逅・′譛ｪ螳御ｺ・↓隕九∴縺ｦ縺・◆縲・
  - 繝輔Ο繝ｳ繝医お繝ｳ繝峨〒縺ｮ騾ｲ陦檎憾諷玖｡ｨ遉ｺ縺ｫ縺翫＞縺ｦ縲∵律險倡函謌舌′螳御ｺ・＠縺滄圀縺ｫ豬√ｌ繧・`diary_complete` 遲牙ｰら畑繝輔ぉ繝ｼ繧ｺ繧､繝吶Φ繝医′豁｣縺励￥陦ｨ遉ｺUI隕∫ｴ縺ｨ騾｣謳ｺ縺励※縺・↑縺九▲縺溘◆繧√√梧律險倥す繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ騾ｲ陦御ｸｭ...縲阪・繝・く繧ｹ繝医′邨ゆｺ・ｾ後ｂ繧ｹ繧ｿ繝・け縺励※谿九▲縺ｦ縺・◆縲・

- **(b) 螟画峩繝ｻ譬ｹ諡**: 
  - 繝ｦ繝ｼ繧ｶ繝ｼ縺九ｉ隕九※縲檎ｵゅｏ縺｣縺溘・縺壹・菴懈･ｭ縺梧悴螳御ｺ・↓縺ｪ縺｣縺ｦ縺・ｋ縲阪→諢溘§縺輔○繧九・縺ｯ縲∽ｽ懈･ｭ繝励Ο繧ｻ繧ｹ繧・ｿ｡鬆ｼ諤ｧ繧貞､ｧ縺阪￥謳阪↑縺・X荳翫・閾ｴ蜻ｽ逧・↑谺髯･縲・
  - 繝舌ャ繧ｯ繧ｨ繝ｳ繝峨→繝輔Ο繝ｳ繝医お繝ｳ繝峨′蜈ｱ騾壹・繝・・繧ｿ繧ｹ繝・・繝医Γ繝ｳ繝医ｒ謖√◆縺壹√し繝悶ョ繧｣繝ｬ繧ｯ繝医Μ・・diaries/`・牙・縺ｮ菫晏ｭ倥ヵ繧｡繧､繝ｫ縺ｫ蟇ｾ縺吶ｋ隱ｭ縺ｿ霎ｼ縺ｿ繝ｫ繝ｼ繝√Φ縺悟ｭ伜惠縺励↑縺九▲縺溘◆繧√∝ｱ･豁ｴ縺九ｉ螳悟・縺ｪ繝・・繧ｿ繧貞ｾｩ蜈・☆繧玖ｦ∽ｻｶ繧呈ｺ縺溘○縺ｦ縺・↑縺九▲縺溘・

- **(c) 謗｡逕ｨ縺励◆繝吶せ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:
  - **繝舌ャ繧ｯ繧ｨ繝ｳ繝陰PI縺ｮ繝ｬ繧ｹ繝昴Φ繧ｹ邨ｱ蜷・*: `main.py`縺ｮ`get_package`・・PI繝ｫ繝ｼ繝茨ｼ峨ｒ諡｡蠑ｵ縺励～package.json`繧貞叙蠕励☆繧矩圀縺ｫ繧ｵ繝悶ョ繧｣繝ｬ繧ｯ繝医Μ`diaries/day_*.md`繧りｵｰ譟ｻ縺励※隱ｭ縺ｿ霎ｼ縺ｿ縲√☆縺ｹ縺ｦ`diaries`驟榊・縺ｨ縺励※繝ｬ繧ｹ繝昴Φ繧ｹ縺ｫ邨ｱ蜷医＠縺ｦ霑斐☆繧医≧縺ｫ螟画峩縲・
  - **繝輔Ο繝ｳ繝医お繝ｳ繝峨・繧ｹ繝・・繝亥ｾｩ蜈・*: `app.js`縺ｮ`loadPackage`蜀・〒縲∝叙蠕励＠縺歔currentPackage.diaries`縺悟ｭ伜惠縺吶ｌ縺ｰ縲∝叉蠎ｧ縺ｫ`Renderer.renderDiary`繧剃ｽｿ縺｣縺ｦ繝ｬ繝ｳ繝繝ｪ繝ｳ繧ｰ縲ょ酔譎ゅ↓縲∝・譛溘・髢句ｧ九ヱ繝阪Ν・・diary-start-panel`・峨♀繧医・繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ騾ｲ謐鈴伜沺・・diary-generation-area`・峨ｒ髱櫁｡ｨ遉ｺ蛹悶☆繧九％縺ｨ縺ｧ縲√Θ繝ｼ繧ｶ繝ｼ縺ｫ螳悟・縺ｫ螳御ｺ・＠縺溽憾諷九ｒ繧ｷ繝ｼ繝繝ｬ繧ｹ縺ｫ謠千､ｺ縺吶ｋ讒矩繧堤｢ｺ遶九・
  - **繝励Ο繧ｰ繝ｬ繧ｹ邂｡逅・・蛻・屬縺ｨ邊ｾ蟇・喧**: `app.js`縺ｮ`updateProgress`縺ｧ縲∵磁鬆ｭ霎槭′`diary_`縺ｧ蟋九∪繧九ヵ繧ｧ繝ｼ繧ｺ・・diary_init`繧Яdiary_complete`遲会ｼ牙髄縺代・DOM謫堺ｽ懊Ο繧ｸ繝・け繧堤峡遶句・髮｢縲ょｮ御ｺ・凾縺ｫ騾ｲ陦御ｸｭ繝・く繧ｹ繝医ｒ遒ｺ螳溘°縺､譏守､ｺ逧・↓縲梧律險倥・逕滓・縺悟ｮ御ｺ・＠縺ｾ縺励◆縲阪↓譖ｸ縺肴鋤縺医ｋ縺薙→縺ｧ繧ｹ繧ｿ繝・け繧帝亟豁｢縲・
  - **繧ｹ繧ｳ繧｢繝ｪ繝ｳ繧ｰ**: 繝舌Μ繝・・繧ｿ繝ｼ 縺ｯ縲・.0・・.0縺ｮ蜩∬ｳｪ繧ｹ繧ｳ繧｢縲阪→縲後←縺ｮ鬆・岼縺悟ｮ医ｉ繧後※縺・◆縺・螳医ｉ繧後※縺・↑縺九▲縺溘°縲阪ｒ譏守､ｺ縺吶ｋ縲ゅ％繧後↓繧医ｊ蜩∬ｳｪ縺ｮ蜿ｯ隕門喧縺ｨ谿ｵ髫守噪謾ｹ蝟・′蜿ｯ閭ｽ

### Stage 45: 譌･險伜・逕滓・讖溯・縺ｮ蛻ｷ譁ｰ・医そ繝・す繝ｧ繝ｳ繝吶・繧ｹ縺ｮ繝舌・繧ｸ繝ｧ繝ｳ邂｡逅・ｰ主・・・

**(a) 蠖灘・險ｭ險・*: 譌･險倥・蜀咲函謌先凾縲∵里蟄倥・騾ｲ陦檎憾諷具ｼ郁ｨ俶・繧・Β繝ｼ繝画耳遘ｻ・峨ｒ荳蠎ｦ迚ｩ逅・噪縺ｫ蜑企勁・・shutil.rmtree`・峨＠縺ｦ縺九ｉ Day 1 縺九ｉ逕滓・縺礼峩縺咏ｴ螢顔噪縺ｪ蜀崎ｵｷ蜍輔Ο繧ｸ繝・け繧呈治逕ｨ縺励※縺・◆縲ゅ∪縺溘∵律險倥ョ繝ｼ繧ｿ繧・`CharacterPackage` 繝｢繝・Ν蜀・↓驥崎､・＠縺ｦ菫晄戟縺輔○繧医≧縺ｨ縺励◆縺溘ａ縲∝腰荳繝輔ぃ繧､繝ｫ・・ackage.json・峨′蟾ｨ螟ｧ蛹悶＠縲√ョ繧｣繝ｬ繧ｯ繝医Μ蜀・・ `.md` 繝輔ぃ繧､繝ｫ縺ｨ縺ｮ蜷梧悄荳肴紛蜷医′逋ｺ逕溘☆繧九Μ繧ｹ繧ｯ縺後≠縺｣縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 繝ｦ繝ｼ繧ｶ繝ｼ縺後梧乖譌･縺ｮ譌･險倥ｒ繧・ｊ逶ｴ縺励◆縺・阪→閠・∴縺溘→縺阪∽ｻ･蜑阪・逕滓・邨先棡繧よｯ碑ｼ・ｯｾ雎｡縺ｨ縺励※谿九＠縺ｦ縺翫￥譁ｹ縺檎黄隱槭・謗｢邏｢縺ｫ縺翫＞縺ｦ螳牙・縺ｧ譛臥寢縺ｧ縺ゅｋ縲ら黄逅・炎髯､縺ｯ蠕ｩ譌ｧ荳榊庄閭ｽ縺ｧ縺ゅｊ縲√お繝ｩ繝ｼ逋ｺ逕滓凾縺ｫ蜈ｨ繝・・繧ｿ縺梧ｶ亥､ｱ縺吶ｋ繝ｪ繧ｹ繧ｯ縺碁ｫ倥＞縲ゅ◎縺ｮ縺溘ａ縲∫函謌舌＃縺ｨ縺ｫ繝ｦ繝九・繧ｯ縺ｪ `session_id` 繧剃ｻ倅ｸ弱＠縲∫峡遶九＠縺溘ヵ繧ｩ繝ｫ繝讒矩縺ｧ邂｡逅・☆繧矩撼遐ｴ螢顔噪縺ｪ縲後そ繝・す繝ｧ繝ｳ邂｡逅・婿蠑上阪↓蛻ｷ譁ｰ縺励◆縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **繧ｻ繝・す繝ｧ繝ｳ繝輔か繝ｫ繝縺ｮ閾ｪ蜍慕函謌・*: `storage/<char>/sessions/<session_id>/` 驟堺ｸ九↓譌･險倥√Ο繧ｰ縲√Β繝ｼ繝峨∬ｨ俶・繧貞ｮ悟・縺ｫ蛻・屬縺励※菫晏ｭ倥Ａsession_id` 縺ｯ繧ｿ繧､繝繧ｹ繧ｿ繝ｳ繝励ｒ蜷ｫ縺ｿ縲∽ｸ諢乗ｧ繧剃ｿ晁ｨｼ縲・
- **繧ｪ繝ｳ繝・・繝ｳ繝峨・繝槭・繧ｸ隱ｭ縺ｿ霎ｼ縺ｿ**: `get_package` API 縺ｫ縺翫＞縺ｦ縲√ヵ繧｡繧､繝ｫ繧ｷ繧ｹ繝・Β荳翫・ `sessions/` 繧定ｵｰ譟ｻ縺励∵怙譁ｰ縺ｮ繧ｻ繝・す繝ｧ繝ｳ繝・・繧ｿ繧貞虚逧・↓繝代ャ繧ｱ繝ｼ繧ｸJSON縺ｫ邨仙粋縺励※霑斐☆縲ゅΔ繝・Ν蛛ｴ縺ｫ蟾ｨ螟ｧ縺ｪ繝・・繧ｿ繧剃ｿ晄戟縺輔○繧句ｿ・ｦ√′縺ｪ縺上↑繧翫∵ュ蝣ｱ縺ｮ魄ｮ蠎ｦ縺ｨ謨ｴ蜷域ｧ繧剃ｸ｡遶九・
- **繧ｹ繝医い繧ｯ繝ｩ繧ｹ縺ｮ繧ｻ繝・す繝ｧ繝ｳ蟇ｾ蠢・*: `KeyMemoryStore`, `DailyLogStore` 遲峨′ `session_id` 繧貞女縺大叙繧翫∝虚逧・↓繝代せ繧貞・繧頑崛縺医ｋ繧医≧謚ｽ雎｡蛹門ｱ､繧呈僑蠑ｵ縲・
- **蜀鈴聞縺ｪ蜷梧悄縺ｮ謗帝勁**: 繝輔ぃ繧､繝ｫ繧ｷ繧ｹ繝・Β繧貞髪荳縺ｮ逵溷ｮ溘・繧ｽ繝ｼ繧ｹ (Single Source of Truth) 縺ｨ縺励√Δ繝・Ν蛛ｴ縺ｸ縺ｮ荳崎ｦ√↑繝・・繧ｿ縺ｮ譖ｸ縺肴綾縺暦ｼ・diaries` 繝輔ぅ繝ｼ繝ｫ繝臥ｭ会ｼ峨ｒ蟒・ｭ｢縲・
- **險ｭ險亥次蜑・*: 縲檎函謌舌・繝ｭ繧ｻ繧ｹ縺ｯ蟶ｸ縺ｫ髱樒ｴ螢顔噪縺ｧ縺ゅｊ縲√☆縺ｹ縺ｦ縺ｮ繝舌・繧ｸ繝ｧ繝ｳ縺ｯ繝・ぅ繝ｬ繧ｯ繝医Μ讒矩縺ｫ繧医▲縺ｦ霑ｽ霍｡繝ｻ蠕ｩ蜈・庄閭ｽ縺ｧ縺ゅｋ縺ｹ縺阪阪→縺・≧繧ｹ繝・・繝医Ξ繧ｹ縺ｪ繧ｹ繝医Ξ繝ｼ繧ｸ邂｡逅・ｒ蠕ｹ蠎輔・
### 28. 譌･險倡函謌仙●豁｢蝠城｡後・菫ｮ豁｣・医う繝ｳ繝昴・繝域ｼ上ｌ縺ｨ繧ｨ繝ｩ繝ｼ繝上Φ繝峨Μ繝ｳ繧ｰ・・

**(a) 蠖灘・險ｭ險・*: `backend/agents/daily_loop/linguistic_validator.py` 縺ｫ縺翫＞縺ｦ縲～Optional` 蝙九ヲ繝ｳ繝医′菴ｿ逕ｨ縺輔ｌ縺ｦ縺・◆縺後～typing.Optional` 縺ｮ繧､繝ｳ繝昴・繝医′貍上ｌ縺ｦ縺・◆縲ゅ∪縺溘～main.py` 縺ｮ髱槫酔譛溽函謌舌ち繧ｹ繧ｯ (`run_diary_generation` 遲・ 縺ｧ縺ｯ蛻晄悄蛹匁凾縺ｮ萓句､匁黒謐峨′荳榊香蛻・□縺｣縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 譌･險倥す繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ縺ｮ髢句ｧ区凾縺ｫ `NameError` 縺檎匱逕溘＠縲√ヰ繝・け繧ｨ繝ｳ繝峨′繧ｵ繧､繝ｬ繝ｳ繝医↓蛛懈ｭ｢・医碁幕蟋区ｺ門ｙ荳ｭ...縲阪〒繝ｭ繧ｰ縺梧ｭ｢縺ｾ繧具ｼ峨＠縺ｦ縺・◆縲る撼蜷梧悄繧ｿ繧ｹ繧ｯ縺ｮ蛻晄悄蛹悶ヵ繧ｧ繝ｼ繧ｺ縺ｧ逋ｺ逕溘＠縺溘お繝ｩ繝ｼ縺梧黒謐峨＆繧後★縲√ヵ繝ｭ繝ｳ繝医お繝ｳ繝峨↓騾夂衍縺輔ｌ縺ｪ縺・◆繧√∝次蝗縺ｮ迚ｹ螳壹′蝗ｰ髮｣縺縺｣縺溘・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **譬ｹ譛ｬ蜴溷屏縺ｮ菫ｮ豁｣**: `linguistic_validator.py` 縺ｫ `from typing import Optional` 繧定ｿｽ蜉縲・
- **蛹・峡逧・お繝ｩ繝ｼ繝上Φ繝峨Μ繝ｳ繧ｰ**: `main.py` 縺ｮ蜷・函謌舌お繝ｳ繝医Μ繝ｼ繝昴う繝ｳ繝医↓縺翫＞縺ｦ縲∝・繧､繝ｳ繝昴・繝医・蛻晄悄蛹門・逅・ｒ `try-except` 繝悶Ο繧ｰ蜀・↓驟咲ｽｮ縲ゆｺ域悄縺帙〓繧ｨ繝ｩ繝ｼ逋ｺ逕滓凾繧ょ叉蠎ｧ縺ｫ `generation_error` 繧､繝吶Φ繝医ｒ騾∽ｿ｡縺励∝次蝗繧偵ヵ繝ｭ繝ｳ繝医お繝ｳ繝峨〒蜿ｯ隕門喧縲・
- **髱咏噪繧､繝ｳ繝昴・繝医メ繧ｧ繝・け**: `backend` 蜀・・荳ｻ隕√ヵ繧｡繧､繝ｫ繧堤ｶｲ鄒・噪縺ｫ繝√ぉ繝・け縺励∽ｻ悶・ `typing` 繧､繝ｳ繝昴・繝域ｼ上ｌ縺後↑縺・％縺ｨ繧堤｢ｺ隱阪・

---
### 23. API繧ｭ繝ｼ縺ｮ蜍慕噪謫堺ｽ懊・莨晄眺繧ｷ繧ｹ繝・Β・医ョ繧ｫ繝・・繝ｪ繝ｳ繧ｰ・・

**(a) 蠖灘・險ｭ險・*: API繧ｭ繝ｼ縺ｯ繝舌ャ繧ｯ繧ｨ繝ｳ繝峨・ `.env` 繝輔ぃ繧､繝ｫ縺ｫ繝上・繝峨さ繝ｼ繝峨＆繧後∫腸蠅・､画焚縺ｨ縺励※縺ｮ縺ｿ邂｡逅・＆繧後※縺・◆縲ゅΘ繝ｼ繧ｶ繝ｼ縺瑚・霄ｫ縺ｮ繧ｭ繝ｼ繧剃ｽｿ逕ｨ縺吶ｋ謇区ｮｵ縺後↑縺上√し繝ｼ繝舌・蛛ｴ縺ｮ繝ｪ繧ｽ繝ｼ繧ｹ縺ｫ萓晏ｭ倥＠縺ｦ縺・◆縲・

**(b) 螟画峩繝ｻ譬ｹ諡**: 繝ｦ繝ｼ繧ｶ繝ｼ縺檎峡閾ｪ縺ｮ API 繧ｭ繝ｼ・・penAI, Anthropic, Google AI・峨ｒ繝輔Ο繝ｳ繝医お繝ｳ繝峨°繧牙・蜉帙・邂｡逅・〒縺阪ｋ繧医≧縺ｫ縺励√し繝ｼ繝舌・蛛ｴ縺ｮ繧ｭ繝ｼ縺ｫ萓晏ｭ倥○縺壽沐霆溘↑驕狗畑繧貞庄閭ｽ縺ｫ縺吶ｋ縺溘ａ縲ゅそ繧ｭ繝･繝ｪ繝・ぅ髱｢縺ｧ繧ゅ√さ繝ｼ繝牙・繧・腸蠅・､画焚縺ｸ縺ｮ蝗ｺ螳壹ｒ驕ｿ縺代√Μ繧ｯ繧ｨ繧ｹ繝亥腰菴阪〒縺ｮ蜍慕噪謠蝉ｾ帙′譛帙∪縺励＞縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **繝輔Ο繝ｳ繝医お繝ｳ繝峨・豌ｸ邯壼喧**: `localStorage` 繧剃ｽｿ逕ｨ縺励※繝悶Λ繧ｦ繧ｶ蛛ｴ縺ｫ證怜捷蛹厄ｼ医∪縺溘・髮｣隱ｭ蛹厄ｼ峨＠縺ｦ菫晏ｭ倥・
- **WebSocket 邨檎罰縺ｮ莨晄眺**: 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・縲∝・逕滓・縲∵律險倡函謌舌・蜷・Μ繧ｯ繧ｨ繧ｹ繝医↓ `api_keys` 繝壹う繝ｭ繝ｼ繝峨ｒ蜷梧｢ｱ縲・
- **繝舌ャ繧ｯ繧ｨ繝ｳ繝峨・邯ｲ鄒・噪莨晄眺**: WebSocket 繝上Φ繝峨Λ縺九ｉ `MasterOrchestrator`縲～DailyLoopOrchestrator`縲～regenerate_artifact` 繧堤ｵ後※縲∝・縺ｦ縺ｮ Worker (Phase A-1, A-2, A-3, Phase D) 縺翫ｈ縺ｳ繧ｵ繝悶お繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ・mpulsive, Reflective 遲会ｼ峨・ `call_llm` 蜻ｼ縺ｳ蜃ｺ縺励∪縺ｧ `api_keys` 蠑墓焚繧帝夊ｲｫ縲・
- **蜍慕噪繧ｭ繝ｼ蜆ｪ蜈医Ο繧ｸ繝・け**: `llm_api.py` 縺ｮ `call_llm` 縺ｫ縺翫＞縺ｦ縲∝ｼ墓焚縺ｨ縺励※貂｡縺輔ｌ縺・`api_keys` 縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷医・迺ｰ蠅・､画焚繧医ｊ繧ょ━蜈医＠縺ｦ菴ｿ逕ｨ縺吶ｋ縲・
- **險ｭ螳・UI**: 繝｢繝繝ｳ縺ｪ繝｢繝ｼ繝繝ｫ UI 繧貞ｮ溯｣・＠縲∝推繝励Ο繝舌う繝縺斐→縺ｮ繧ｭ繝ｼ險ｭ螳壹ｒ螳ｹ譏薙↓縲・

### 24. Human in the Loop: 迚ｩ隱樊ｧ区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹ + Creative Director蠕後Ξ繝薙Η繝ｼ

**(a) 蠖灘・險ｭ險・*: 繝ｦ繝ｼ繧ｶ繝ｼ縺梧欠螳壹〒縺阪ｋ縺ｮ縺ｯ縲後ユ繝ｼ繝槭阪→縲悟刀雉ｪ繝励Ο繝輔ぃ繧､繝ｫ縲阪・縺ｿ縲ら黄隱槭・讒矩繝ｻ諢滓ュ繝医・繝ｳ繝ｻ隱槭ｊ蜿｣遲峨・讒区・隕∫ｴ繧剃ｺ句燕縺ｫ謖・ｮ壹☆繧倶ｻ慕ｵ・∩縺後↑縺九▲縺溘ゅ∪縺溘，reative Director縺ｮ蜃ｺ蜉帛ｾ後↓莠ｺ髢薙′遒ｺ隱阪・菫ｮ豁｣縺励※縺九ｉ荳区ｵ￣hase縺ｫ騾ｲ繧謇区ｮｵ繧ょｭ伜惠縺励↑縺九▲縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 2縺､縺ｮ蝠城｡後ｒ蜷梧凾縺ｫ隗｣豎ｺ縲や蔵**逕滓・蜑・*: 譁・鍵繝吶・繧ｹ・・ristotle, Freytag, Campbell, Harmon, Snyder, McKee, Weiland, Vogler, Genette, Booth, Bakhtin遲・1逅・ｫ門ｮｶ・・7Web諠・ｱ貅撰ｼ峨・邯ｲ鄒・噪縺ｪ驕ｸ謚櫁い縺九ｉ迚ｩ隱樊ｧ区・繧呈欠螳壹〒縺阪ｋUI縲・繧ｫ繝・ざ繝ｪ78+驕ｸ謚櫁い縲や贈**逕滓・蠕・*: Creative Director螳御ｺ・ｾ後↓繝代う繝励Λ繧､繝ｳ繧蛋asyncio.Event`縺ｧ荳譎ょ●豁｢縺励√Θ繝ｼ繧ｶ繝ｼ縺慶oncept_package繧堤｢ｺ隱坂・謇ｿ隱・繝輔ぅ繝ｼ繝峨ヰ繝・け蜀咲函謌・逶ｴ謗･邱ｨ髮・・3繝代せ縺ｧ莉句・蜿ｯ閭ｽ縺ｫ縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **`StoryCompositionPreferences`繝｢繝・Ν**: 8繧ｫ繝・ざ繝ｪ・玖・逕ｱ險倩ｿｰ縺ｮ蜈ｨOptional Pydantic繝｢繝・Ν縲よ悴驕ｸ謚樣・岼縺ｯAI閾ｪ蠕句愛譁ｭ
- **Creative Director縺ｸ縺ｮ豕ｨ蜈･**: 驕ｸ謚槭＆繧後◆鬆・岼繧呈律譛ｬ隱槭Λ繝吶Ν縺ｫ螟画鋤縺輿縲舌Θ繝ｼ繧ｶ繝ｼ謖・ｮ壹・讒区・譁ｹ驥晢ｼ・uman in the Loop・峨疏縺ｨ縺励※Markdown蠖｢蠑上〒繝励Ο繝ｳ繝励ヨ縺ｫ豕ｨ蜈･縲４elf-Critique縺ｫ`[G] 繝ｦ繝ｼ繧ｶ繝ｼ讒区・譁ｹ驥昴→縺ｮ謨ｴ蜷域ｧ`繝√ぉ繝・け鬆・岼・・繝√ぉ繝・け繝懊ャ繧ｯ繧ｹ・峨ｒ霑ｽ蜉
- **繝代う繝励Λ繧､繝ｳ荳譎ょ●豁｢**: MasterOrchestrator縺靴reative Director螳御ｺ・ｾ後↓`concept_review`繧､繝吶Φ繝医ｒ騾∽ｿ｡縲～asyncio.Event`縺ｧ繝ｦ繝ｼ繧ｶ繝ｼ蠢懃ｭ斐ｒ蠕・ｩ溘Ａactive_orchestrator`繧ｰ繝ｭ繝ｼ繝舌Ν螟画焚縺ｧWebSocket繝上Φ繝峨Λ縺九ｉ繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繝ｼ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ縺ｫ繧｢繧ｯ繧ｻ繧ｹ
- **3繧｢繧ｯ繧ｷ繝ｧ繝ｳ**: `approve_concept`・育ｶ夊｡鯉ｼ峨～revise_concept`・医ヵ繧｣繝ｼ繝峨ヰ繝・け莉倥″蜀咲函謌撰ｼ峨～edit_concept_direct`・育ｷｨ髮・ｸ医∩JSON驕ｩ逕ｨ・・
- **繝輔Ο繝ｳ繝医お繝ｳ繝蔚I**: 繧｢繧ｳ繝ｼ繝・ぅ繧ｪ繝ｳ蠖｢蠑上・繧ｫ繝ｼ繝蛾∈謚朸I・亥推繧ｫ繝ｼ繝峨↓蜷榊燕+隱ｬ譏・蜃ｺ蜈ｸ逅・ｫ門ｮｶ・峨√さ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ逕ｻ髱｢・域里蟄倭Renderer.renderConcept()`蜀榊茜逕ｨ・峨√し繝槭Μ繝ｼ繝舌・陦ｨ遉ｺ

### 26. 逕滓・騾ｲ謐礼ｮ｡逅・ｼ育ｮ｡逅・・繝・け繧ｹ・峨↓繧医ｋ蜀咲函謌宣亟豁｢

**Subject / Feature**: 繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・縺ｮ荳ｭ譁ｭ蜀埼幕縺ｫ縺翫￠繧句・欧諤ｧ縺ｨ繝・・繧ｿ菫晁ｭｷ

**(a) Original Design**: 蜷・ヵ繧ｧ繝ｼ繧ｺ縺ｮ螳溯｡悟燕縺ｫ縲檎音螳壹・繝輔ぅ繝ｼ繝ｫ繝会ｼ井ｾ・ `macro_profile`・峨′遨ｺ縺九←縺・°縲阪ｒ蛻､螳壹＠縺ｦ繧ｹ繧ｭ繝・・繧呈ｱｺ螳壹＠縺ｦ縺・◆縲１hase D 縺ｪ縺ｩ縺ｮ螟壽ｮｵ髫弱せ繝・ャ繝励〒繧ょ酔讒倥↓縲∽ｸ驛ｨ繝・・繧ｿ縺ｮ譛臥┌縺縺代〒繝輔ぉ繝ｼ繧ｺ蜈ｨ菴薙・螳溯｡後ｒ蛻､譁ｭ縺励※縺・◆縲・

**(b) The Change & Rationale**: 
- **蜀咲函謌舌・逋ｺ逕・*: 繝輔ぅ繝ｼ繝ｫ繝峨・譛臥┌縺ｫ繧医ｋ蛻､螳壹・縲∽ｸ驛ｨ縺檎函謌舌＆繧後◆迥ｶ諷九〒荳ｭ譁ｭ縺励◆蝣ｴ蜷医ｄ縲∵耳隲也ｵ先棡縺檎ｩｺ縺ｫ霑代＞蝣ｴ蜷医↓縲梧悴逕滓・縲阪→隱､隱阪＆繧後∵里縺ｫ蟄伜惠縺吶ｋ繝・・繧ｿ繧剃ｸ頑嶌縺阪＠縺溘ｊ縲・ｫ倥さ繧ｹ繝医↑逕滓・繧貞・髟ｷ縺ｫ郢ｰ繧願ｿ斐＠縺溘ｊ縺吶ｋ繝ｪ繧ｹ繧ｯ縺後≠縺｣縺溘・
- **繝ｭ繧ｰ縺ｮ莠碁㍾蛹・*: 蜀榊ｮ溯｡後↓繧医ｊ縲梧晁・ｼ・hinking・峨阪Ο繧ｰ縺悟・蠎ｦ蜃ｺ蜉帙＆繧後√Θ繝ｼ繧ｶ繝ｼ縺ｫ縲後∪縺滓怙蛻昴°繧峨ｄ繧顔峩縺励※縺・ｋ縲阪→縺・≧荳榊ｮ峨ｒ荳弱∴繧九・
- **邂｡逅・・荳埼乗・諤ｧ**: 縺ｩ縺ｮ繧ｹ繝・ャ繝励′遒ｺ螳溘↓螳御ｺ・＠縺ｦ縺・ｋ縺九ｒ譏守､ｺ逧・↓遉ｺ縺吶檎ｮ｡逅・・繝・け繧ｹ縲阪′荳榊惠縺縺｣縺溘・

**(c) Adopted Best Practice**:
- **`GenerationStatus` 繝｢繝・Ν縺ｮ蟆主・**: 蜷・ヵ繧ｧ繝ｼ繧ｺ縺翫ｈ縺ｳ Phase D 蜀・Κ縺ｮ蜷・せ繝・ャ繝暦ｼ井ｸ也阜, 莠ｺ迚ｩ, 謇謖∝刀, 繧｢繝ｼ繧ｯ, 蠑ｷ蠎ｦ・峨↓蛟句挨縺ｮ螳御ｺ・ヵ繝ｩ繧ｰ・・oolean・峨ｒ莉倅ｸ弱ゅ％繧後ｒ縲檎ｮ｡逅・・繝・け繧ｹ縲阪→縺励※ `CharacterPackage` 縺ｫ邨ｱ蜷医・
- **繧ｹ繝・・繧ｿ繧ｹ閾ｪ蜍募ｾｩ譌ｧ・・elf-Healing・・*: 譌｢蟄倥・繝√ぉ繝・け繝昴う繝ｳ繝医ｒ繝ｭ繝ｼ繝峨＠縺滄圀縲√ヵ繝ｩ繧ｰ縺梧ｬ關ｽ縺励※縺・※繧ゅョ繝ｼ繧ｿ縺ｮ蟄伜惠繧呈､懃衍縺励※繝輔Λ繧ｰ繧定・蜍墓峩譁ｰ縺吶ｋ繝ｭ繧ｸ繝・け繧貞ｮ溯｣・よ里蟄倥く繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ繝・・繧ｿ縺ｮ荳肴紛蜷医ｒ閾ｪ蜍輔〒菫ｮ蠕ｩ縺吶ｋ縲・
- **繝√ぉ繝・け繝昴う繝ｳ繝医・邯ｲ鄒・ｧ**: 蜷・せ繝・ャ繝怜ｮ御ｺ・＃縺ｨ縺ｫ `GenerationStatus` 繧呈峩譁ｰ縺励∝叉蠎ｧ縺ｫ菫晏ｭ倥ｒ陦後≧縺薙→縺ｧ縲∽ｸｭ譁ｭ蠕後・蜀埼幕蝨ｰ轤ｹ繧堤｢ｺ螳溘↓菫晁ｭｷ縲・
- **繝ｭ繧ｰ縺ｮ謨ｴ逅・*: 繧ｹ繧ｭ繝・・譎ゅ↓縺ｯ縲梧里蟄倥ョ繝ｼ繧ｿ縺ｮ螳悟ｙ (Skip)縲阪→1陦後□縺鷹夂衍縺励∝・髟ｷ縺ｪ諤晁・Ο繧ｰ繧貞・蜉帙＠縺ｪ縺・・

### 27. Phase D繧ｨ繝ｩ繝ｼ菫ｮ豁｣繝ｻ繧ｿ繧ｹ繧ｯ邂｡逅・隼蝟・・荳ｭ譁ｭ讖溯・

**(a) 蠖灘・險ｭ險・*: Phase D縺ｮ`call_llm_agentic_gemini`縺ｧGemini縺形MALFORMED_FUNCTION_CALL`繧定ｿ斐＠縺溷ｴ蜷医・縺､縺ｮ繝代ち繝ｼ繝ｳ縺悟ｭ伜惠縺励◆: (1) 萓句､悶→縺励※ `send_message` 縺九ｉ謚輔￡繧峨ｌ繧九こ繝ｼ繧ｹ縲・2) 繝ｬ繧ｹ繝昴Φ繧ｹ縺ｮ `finish_reason` 繝輔ぅ繝ｼ繝ｫ繝峨↓險ｭ螳壹＆繧後ｋ繧ｱ繝ｼ繧ｹ縲ょｾ瑚・・ `except` 繝悶Ο繝・け縺ｫ蜈･繧峨★ `ValueError("Gemini縺九ｉ譛牙柑縺ｪ蝗樒ｭ斐ｒ蠕励ｉ繧後∪縺帙ｓ縺ｧ縺励◆縲・)` 縺ｨ縺励※荳贋ｽ阪↓莨晄眺縺励∫ｵ先棡縺ｨ縺励※ MasterOrchestrator 縺ｮ `_execute_phase_with_retry` 縺訓hase D蜈ｨ菴薙ｒ譛蛻昴°繧牙・螳溯｡後＠縺ｦ縺・◆縲ゅ％繧後↓繧医ｊ譌｢縺ｫ逕滓・貂医∩縺ｮ荳也阜險ｭ螳壹・蜻ｨ蝗ｲ莠ｺ迚ｩ繝ｻ謇謖∝刀繝ｻ閭ｽ蜉帙′縺吶∋縺ｦ蜀咲函謌舌＆繧後※縺・◆縲ゅ∪縺溘∫函謌舌ｒ荳ｭ譁ｭ縺吶ｋ謇区ｮｵ縺後↑縺上・聞譎る俣縺ｮ逕滓・荳ｭ縺ｫ繝ｦ繝ｼ繧ｶ繝ｼ縺悟ｾ・▽縺励°縺ｪ縺九▲縺溘・

**(b) 螟画峩繝ｻ譬ｹ諡**: 繧ｨ繝ｩ繝ｼ繝ｭ繧ｰ縺ｮ蛻・梵縺ｫ繧医ｊ縲～finish_reason: MALFORMED_FUNCTION_CALL` 縺後Ξ繧ｹ繝昴Φ繧ｹ繧ｪ繝悶ず繧ｧ繧ｯ繝医・繝輔ぅ繝ｼ繝ｫ繝峨→縺励※霑斐ｋ繧ｱ繝ｼ繧ｹ縺御ｸｻ隕√↑蜴溷屏縺縺｣縺溘ＡMALFORMED_FUNCTION_CALL` 縺ｮ enum蛟､縺ｯ `7`・・nt・峨□縺後ヾDK繝舌・繧ｸ繝ｧ繝ｳ縺ｫ繧医ｊ譁・ｭ怜・縺ｧ霑斐ｋ蝣ｴ蜷医ｂ縺ゅｋ縺溘ａ縲∽ｸ｡譁ｹ縺ｫ蟇ｾ蠢懊′蠢・ｦ√ゅ∪縺溘￣hase D縺ｮ蜷・せ繝・ャ繝暦ｼ井ｸ也阜險ｭ螳壺・蜻ｨ蝗ｲ莠ｺ迚ｩ竊呈園謖∝刀閭ｽ蜉帚・迚ｩ隱槭い繝ｼ繧ｯ竊定騒阯､蠑ｷ蠎ｦ竊偵う繝吶Φ繝育函謌撰ｼ峨・迢ｬ遶九＠縺ｦ縺翫ｊ縲・比ｸｭ縺ｧ螟ｱ謨励＠縺ｦ繧ゅ◎繧後∪縺ｧ縺ｮ繧ｹ繝・ャ繝励・繝・・繧ｿ縺ｯ蜀榊茜逕ｨ縺ｧ縺阪ｋ縺ｹ縺阪・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け繝ｫ繝ｼ繝励・2螻､MALFORMED蟇ｾ遲・* (`llm_api.py`):
  - `except` 繝悶Ο繝・け: `send_message` 縺御ｾ句､悶ｒ謚輔￡縺溷ｴ蜷医・繝ｪ繧ｫ繝舌Μ・亥｣翫ｌ縺溷ｱ･豁ｴ蜑企勁+蜀崎ｩｦ陦後Γ繝・そ繝ｼ繧ｸ・・
  - `finish_reason` 繝√ぉ繝・け: 繝ｬ繧ｹ繝昴Φ繧ｹ蜿嶺ｿ｡蠕後↓ `finish_reason` 縺・`MALFORMED` 繧貞性繧縺・`7` 縺ｧ縺ゅｌ縺ｰ縲∝｣翫ｌ縺溷ｱ･豁ｴ繧貞炎髯､縺・`continue` 縺ｧ繝ｫ繝ｼ繝励・谺｡縺ｮ繧､繝・Ξ繝ｼ繧ｷ繝ｧ繝ｳ縺ｸ遘ｻ陦鯉ｼ井ｾ句､悶↓縺帙★繝ｪ繧ｫ繝舌Μ・・
- **Phase D繝√ぉ繝・け繝昴う繝ｳ繝医・繧ｹ繧ｭ繝・・** (`phase_d/orchestrator.py`):
  - 蜷・せ繝・ャ繝暦ｼ井ｸ也阜險ｭ螳壹・蜻ｨ蝗ｲ莠ｺ迚ｩ繝ｻ閭ｽ蜉帙・繧｢繝ｼ繧ｯ繝ｻ闡幄陸・牙ｮ御ｺ・ｾ後↓ `_master_orch._checkpoint()` 縺ｧ蜊ｳ譎ゆｿ晏ｭ・
  - 蜷・せ繝・ャ繝鈴幕蟋区凾縺ｫ譌｢蟄倥ョ繝ｼ繧ｿ縺ｮ譛臥┌繧偵メ繧ｧ繝・け縺励∝ｭ伜惠縺吶ｌ縺ｰ繧ｹ繧ｭ繝・・・井ｾ・ `world_context.description` 縺梧里縺ｫ蟄伜惠縺吶ｋ蝣ｴ蜷医・Step 1繧ｹ繧ｭ繝・・・・
  - `_check_cancelled()` 繧・邂・園縺ｫ謖ｿ蜈･縺励√く繝｣繝ｳ繧ｻ繝ｫ繝輔Λ繧ｰ繧堤｢ｺ隱・
- **繧ｭ繝｣繝ｳ繧ｻ繝ｫ讖溯・繝輔Ν繧ｹ繧ｿ繝・け螳溯｣・*:
  - 繝舌ャ繧ｯ繧ｨ繝ｳ繝・ `MasterOrchestrator.cancel()` + `_cancelled` 繝輔Λ繧ｰ + Phase D縺ｸ縺ｮ `set_master_orch()` 莨晄眺
  - WebSocket: `cancel_character_generation` 繧｢繧ｯ繧ｷ繝ｧ繝ｳ 竊・繝√ぉ繝・け繝昴う繝ｳ繝亥ｼｷ蛻ｶ菫晏ｭ・竊・`generation_cancelled` 繧､繝吶Φ繝磯∽ｿ｡・医ヱ繝・こ繝ｼ繧ｸ蜷堺ｻ倥″・・
  - 繝輔Ο繝ｳ繝医お繝ｳ繝・ 逕滓・荳ｭ逕ｻ髱｢縺ｫ縲交泝・逕滓・繧剃ｸｭ譁ｭ縲阪・繧ｿ繝ｳ霑ｽ蜉縲～cancelCharacterGeneration()` 遒ｺ隱阪ム繧､繧｢繝ｭ繧ｰ莉倥″縲～generation_cancelled` 繝上Φ繝峨Λ縺ｧ繝代・繧ｷ繝｣繝ｫ繝・・繧ｿ繧偵ム繝・す繝･繝懊・繝峨↓陦ｨ遉ｺ
- **繝繝・す繝･繝懊・繝峨・繝代・繧ｷ繝｣繝ｫ繝・・繧ｿ陦ｨ遉ｺ**:
  - `Renderer.renderCapabilities()` 譁ｰ險ｭ: 謇謖∝刀・亥錐蜑阪・隱ｬ譏弱・蟶ｸ縺ｫ謳ｺ蟶ｯ繝ｻ諢滓ュ逧・э蜻ｳ・峨∬・蜉幢ｼ亥錐蜑阪・辭溽ｷｴ蠎ｦ・峨∝庄閭ｽ陦悟虚・亥錐蜑阪・譁・ц・峨ｒ繧ｫ繝ｼ繝牙ｽ｢蠑上〒陦ｨ遉ｺ
  - `renderResults()` 縺ｧ繧､繝吶Φ繝医ち繝悶↓ capabilities + events 繧堤ｵｱ蜷郁｡ｨ遉ｺ
  - 蜷・Ξ繝ｳ繝繝ｩ繝ｼ髢｢謨ｰ縺ｯ蜈磯ｭ縺ｧ `if (!data) return '譛ｪ逕滓・'` 縺ｮnull繝√ぉ繝・け繧定｡後≧縺溘ａ縲√ヱ繝ｼ繧ｷ繝｣繝ｫ繝・・繧ｿ縺ｧ繧ゅけ繝ｩ繝・す繝･縺励↑縺・
- **險ｭ險亥次蜑・*: 縲後お繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け繝ｫ繝ｼ繝励・繧ｨ繝ｩ繝ｼ縺ｯ萓句､悶→繝ｬ繧ｹ繝昴Φ繧ｹ繝輔ぅ繝ｼ繝ｫ繝峨・2縺､縺ｮ邨瑚ｷｯ縺ｧ逋ｺ逕溘＠縺・ｋ縲ゆｸ｡譁ｹ繧呈黒謐峨＠縺ｦ蜷後§繝ｪ繧ｫ繝舌Μ繝代せ縺ｫ蜷域ｵ√＆縺帙ｋ縲阪後メ繧ｧ繝・け繝昴う繝ｳ繝医・蜷・せ繝・ャ繝励・邊貞ｺｦ縺ｧ菫晏ｭ倥＠縲∝・螳溯｡梧凾縺ｯ菫晏ｭ俶ｸ医∩繧ｹ繝・ャ繝励ｒ繧ｹ繧ｭ繝・・縺吶ｋ縲・
- **繧｢繝ｼ繧ｭ繝・け繝√Ε螟画峩・・譌･縺斐→縺ｮ鬆・ｬ｡繧､繝吶Φ繝育函謌撰ｼ・*:
  - **隱ｲ鬘・*: 逡ｶ蛻昴・Step 5縺ｯ7譌･蛻・ｼ・4-28莉ｶ・峨ｒ1蝗槭・Agentic Loop縺ｧ荳諡ｬ逕滓・縺励ｈ縺・→縺励※縺・◆縺溘ａ縲∝ｷｨ螟ｧ縺ｪJSON蜃ｺ蜉帙↓閠舌∴縺阪ｌ縺哭LM蛛ｴ縺ｧ `MALFORMED_FUNCTION_CALL` 繧帝ｻ逋ｺ縺輔○縺ｦ縺・◆縲・
  - **隗｣豎ｺ遲・*: `for day in range(1, 8)` 縺ｮ繝ｫ繝ｼ繝励〒1譌･縺壹▽繧､繝吶Φ繝茨ｼ・-4莉ｶ縺壹▽・峨ｒ鬆・ｬ｡逕滓・縺吶ｋ譁ｹ蠑上↓謚懈悽逧・↓螟画峩縲ょ燕譌･縺ｾ縺ｧ縺ｮ逕滓・蛻・ｒ `縲舌％繧後∪縺ｧ縺ｮ繧､繝吶Φ繝医疏 縺ｨ縺励※繧ｳ繝ｳ繝・く繧ｹ繝医↓邏ｯ遨阪＠縺ｦ貂｡縺吶ゅ％繧後↓繧医ｊ竭蜃ｺ蜉帙ヱ繝ｼ繧ｹ關ｽ縺｡縺ｮ譬ｹ譛ｬ蜴溷屏繧定ｧ｣豸医＠縲≫贈蜷・律螳御ｺ・＃縺ｨ縺ｫ繝√ぉ繝・け繝昴う繝ｳ繝医ｒ菫晏ｭ伜庄閭ｽ縺ｫ縺励≫造蜑肴律縺ｮ繧､繝吶Φ繝育ｵ先棡繧定ｸ上∪縺医◆隲也炊逧・↑騾｣邯壽ｧ縺悟髄荳翫＠縺溘・

### Stage 40: 荳ｭ譁ｭ蜀埼幕(繝ｬ繧ｸ繝･繝ｼ繝)譎ゅ・迥ｶ諷句ｾｩ蜈・→繝輔ぃ繧ｹ繝医ヵ繧ｩ繝ｯ繝ｼ繝峨・遒ｺ螳溷喧

**(a) 蠖灘・險ｭ險・*: WebSocket荳翫・ `resume_generation` 繧｢繧ｯ繧ｷ繝ｧ繝ｳ螳溯｡梧凾縲～main.py`縺ｮ`resume_character_generation` 髢｢謨ｰ縺ｧ縺ｯ `MasterOrchestrator` 縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ繧貞・譛溷喧縺吶ｋ縺ｮ縺ｿ縺ｧ縲√げ繝ｭ繝ｼ繝舌Ν螟画焚 `active_orchestrator` 縺ｸ縺ｮ莉｣蜈･繧定｡後▲縺ｦ縺・↑縺九▲縺溘ゅ∪縺溘～MasterOrchestrator` 縺ｮ繝代う繝励Λ繧､繝ｳ險ｭ險井ｸ翫√靴reative Director 螳御ｺ・ｾ後↓縺ｯ蠢・★繧ｳ繝ｳ繧ｻ繝励ヨ縺ｮ謇ｿ隱搾ｼ・uman in the Loop・峨ｒ荳譌ｦ蠕・ｩ溘☆繧九阪→縺・≧蜷梧悄蜃ｦ逅・ｼ・asyncio.Event`・峨′邨・∩霎ｼ縺ｾ繧後※縺・◆縲・

**(b) 螟画峩繝ｻ譬ｹ諡**: 縺薙・險ｭ險医↓繧医ｊ2縺､縺ｮ驥榊､ｧ縺ｪ繝舌げ縺檎匱逕溘＠縺ｦ縺・◆縲・
1. **繧ｻ繝・す繝ｧ繝ｳ螟画焚縺ｮ谺謳・*: 繧ｰ繝ｭ繝ｼ繝舌Ν螟画焚縺ｫ繧ｻ繝・ヨ縺輔ｌ縺ｦ縺・↑縺・◆繧√√ヵ繝ｭ繝ｳ繝医お繝ｳ繝峨〒縲後さ繝ｳ繧ｻ繝励ヨ謇ｿ隱・(approve_concept)縲阪い繧ｯ繧ｷ繝ｧ繝ｳ繧堤匱轣ｫ縺励※繧ゅ後い繧ｯ繝・ぅ繝悶↑逕滓・繧ｻ繝・す繝ｧ繝ｳ縺後≠繧翫∪縺帙ｓ縲阪→縺・≧繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｦ騾壻ｿ｡縺檎ｴ譽・＆繧後※縺・◆縲・
2. **蜀鈴聞縺ｪ蠕・ｩ溘→騾ｲ陦後ヶ繝ｭ繝・け**: 譌｢縺ｫ荳区ｵ√・縲訓hase A-1・医・繧ｯ繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ・峨・Phase D縲阪′逕滓・縺輔ｌ縺ｦ縺・ｋ繝√ぉ繝・け繝昴う繝ｳ繝医°繧牙・髢九＠縺溷ｴ蜷医〒繧ゅ∝ｼｷ蠑輔↓縲後さ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ繧貞ｾ・ｩ溘咲憾諷九〒荳譎ょ●豁｢縺励※縺励∪縺・√悟・縺ｦ逕滓・貂医∩縺ｮ蝣ｴ蜷医・蜊ｳ蠎ｧ縺ｫ繝繝・す繝･繝懊・繝峨∈驕ｷ遘ｻ縺吶ｋ縲阪→縺・≧繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ譛溷ｾ・☆繧九ヵ繧｡繧ｹ繝医ヵ繧ｩ繝ｯ繝ｼ繝峨・謖吝虚繧堤ｴ螢翫＠縺ｦ縺・◆縲・

**(c) 謗｡逕ｨ繝励Λ繧ｯ繝・ぅ繧ｹ**:
- **繧ｰ繝ｭ繝ｼ繝舌Ν繧ｻ繝・す繝ｧ繝ｳ縺ｸ縺ｮ繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ蜀堺ｻ｣蜈･**: `resume_character_generation` 螳溯｡梧凾縺ｫ `global active_orchestrator` 縺ｨ縺励※繧､繝ｳ繧ｹ繧ｿ繝ｳ繧ｹ繧堤｢ｺ螳溘↓繧ｻ繝・ヨ縺励～finally` 繝悶Ο繝・け縺ｧ螳牙・縺ｫ `None` 蛹悶☆繧九Λ繧､繝輔し繧､繧ｯ繝ｫ邂｡逅・ｒ蠕ｹ蠎輔・
- **荳区ｵ∽ｾ晏ｭ倥ョ繝ｼ繧ｿ縺ｫ蝓ｺ縺･縺上せ繝・・繝亥愛螳・(`has_downstream`)**: `MasterOrchestrator` 縺ｫ縺ｦ繧ｳ繝ｳ繧ｻ繝励ヨ縺ｮ繝ｦ繝ｼ繧ｶ繝ｼ繝ｬ繝薙Η繝ｼ蠕・ｩ溷・逅・↓蜈･繧句燕縺ｫ縲√後☆縺ｧ縺ｫ荳区ｵ√・逕滓・繝・・繧ｿ・・hase A-1縺ｮ `basic_info.name`・峨′蟄伜惠縺励※縺・ｋ縺九阪→縺・≧ `has_downstream` 蛻､螳壹ｒ螳溯｡後ょｭ伜惠縺吶ｋ蝣ｴ蜷医・縲碁℃蜴ｻ縺ｮ螳溯｡後そ繝・す繝ｧ繝ｳ縺ｫ縺翫＞縺ｦ譌｢縺ｫ謇ｿ隱肴ｸ医∩縺ｧ縺ゅｋ縲阪→隕九↑縺励√Ξ繝薙Η繝ｼ蠕・ｩ溘ｒ繧ｹ繧ｭ繝・・・医ヵ繧｡繧ｹ繝医ヵ繧ｩ繝ｯ繝ｼ繝会ｼ峨＠縺ｦ蠕檎ｶ壹・讀懆ｨｼ繝ｻ螳御ｺ・ヵ繧ｧ繝ｼ繧ｺ縺ｸ閾ｪ蜍暮ｲ陦後＆縺帙ｋ繧医≧縺ｫ繧｢繝ｼ繧ｭ繝・け繝√Ε繧剃ｿｮ豁｣縲・

### Stage 45: 譌･險伜・逕滓・讖溯・縺ｫ縺翫￠繧玖・蜍輔ヰ繝・け繧｢繝・・縺ｨ繝励Ο繝ｳ繝励ヨ豕ｨ蜈･

**(a) 蠖灘・縺ｮ險ｭ險・*:
譌･險倥・蜀咲函謌撰ｼ・tage 45・峨↓縺翫＞縺ｦ縲∝ｽ灘・縺ｯ縲轡ay 1 縺九ｉ縺ｮ謨ｴ蜷域ｧ繧堤｢ｺ菫昴☆繧九◆繧√↓縲∵里蟄倥・逕滓・迥ｶ諷具ｼ郁ｨ俶・縲√Β繝ｼ繝峨√Ο繧ｰ・峨ｒ螳悟・縺ｫ蜑企勁縺吶ｋ縲阪→縺・≧遐ｴ螢顔噪縺ｪ繧｢繝励Ο繝ｼ繝√ｒ險育判縺励※縺・◆縲ゅ％繧後・螳溯｣・・邁｡逡･蛹悶→繝・・繧ｿ縺ｮ繧ｯ繝ｪ繝ｼ繝ｳ縺輔ｒ蜆ｪ蜈医＠縺溷愛譁ｭ縺ｧ縺ゅ▲縺溘・

**(b) 螟画峩縺ｨ蜷育炊諤ｧ**:
繝ｦ繝ｼ繧ｶ繝ｼ縺九ｉ縺ｮ縲碁℃蜴ｻ縺ｮ逕滓・邨先棡繧よｮ九＠縺ｦ縺翫″縺溘＞縲阪→縺・≧蠑ｷ縺・ｦ∵悍縺ｫ蝓ｺ縺･縺阪∫ｴ螢顔噪謫堺ｽ懊ｒ螳悟・縺ｫ謗帝勁縺励◆縲・
- **蜑企勁縺九ｉ騾驕ｿ縺ｸ**: `shutil.rmtree()` 縺ｫ繧医ｋ蜑企勁繧偵～shutil.move()` 縺ｫ繧医ｋ `backups/` 繝輔か繝ｫ繝縺ｸ縺ｮ騾驕ｿ・医ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・ｼ峨↓螟画峩縺励◆縲ゅ％繧後↓繧医ｊ縲∝､ｱ謨励ｒ諱舌ｌ縺壹↓菴募ｺｦ縺ｧ繧ょ・逕滓・繧定ｩｦ陦後〒縺阪ｋ迺ｰ蠅・ｒ螳溽樟縺励◆縲・
- **繧ｳ繝ｳ繝・く繧ｹ繝域ｳｨ蜈･**: 蜊倥↓蜀榊ｮ溯｡後☆繧九□縺代〒縺ｪ縺上√Θ繝ｼ繧ｶ繝ｼ縺ｮ縲後ｂ縺｣縺ｨ縲懊＠縺ｦ縺ｻ縺励＞縲阪→縺・≧諢丞峙繧・`regeneration_context` 縺ｨ縺励※ `DailyLoopOrchestrator` 縺ｫ貂｡縺励∵律險倡函謌舌お繝ｼ繧ｸ繧ｧ繝ｳ繝医・繝励Ο繝ｳ繝励ヨ縺ｫ豕ｨ蜈･縺吶ｋ莉慕ｵ・∩繧貞ｰ主・縺励◆縲ゅ％繧後↓繧医ｊ縲∝ｯｾ隧ｱ逧・↑蜩∬ｳｪ謾ｹ蝟・′蜿ｯ閭ｽ縺ｨ縺ｪ縺｣縺溘・

**(c) 謗｡逕ｨ縺輔ｌ縺溘・繧ｹ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ**:
- **髱樒ｴ螢雁次蜑・・蠕ｹ蠎・*: 譌｢蟄倥ョ繝ｼ繧ｿ繧剃ｸ頑嶌縺阪・蜑企勁縺吶ｋ蜑阪↓蠢・★蛻･繝・ぅ繝ｬ繧ｯ繝医Μ縺ｫ騾驕ｿ縺輔○繧九・
- **繧ｻ繝・す繝ｧ繝ｳ繝吶・繧ｹ縺ｮ邂｡逅・*: `session_id`・医ち繧､繝繧ｹ繧ｿ繝ｳ繝嶺ｻ倥″・峨ｒ繧ｭ繝ｼ縺ｨ縺励※繝舌ャ繧ｯ繧｢繝・・繧呈ｧ矩蛹悶＠縲√←縺ｮ蜀咲函謌占ｩｦ陦後′縺ｩ縺ｮ繝・・繧ｿ縺ｫ蟇ｾ蠢懊☆繧九°繧呈・遒ｺ縺ｫ縺吶ｋ縲・

---

## 繝代・繝・: 繝励Ο繧ｸ繧ｧ繧ｯ繝育ｮ｡逅・

### 迴ｾ蝨ｨ縺ｮ繝輔ぉ繝ｼ繧ｺ

| 繧ｹ繝・・繧ｸ | 迥ｶ諷・| 蛯呵・|
|---|---|---|
| Stage 1: MVP | 笨・螳溯｣・ｮ御ｺ・| 4螻､繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝域ｧ矩縲∵律谺｡繝ｫ繝ｼ繝礼ｵｱ蜷域ｸ・|
| Stage 2: 蜩∬ｳｪ蜷台ｸ・| 笨・螳溯｣・ｮ御ｺ・| Evaluator鄒､7遞ｮ縲∝・逕滓・繝ｫ繝ｼ繝礼ｵｱ蜷亥ｮ御ｺ・|
| Stage 3: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝郁・蠕句喧 | 笨・螳溯｣・ｮ御ｺ・| 繧ｳ繧｢3遞ｮ(Director, Action, Diary)縺ｮTool-Using蛹・|
| Stage 4: UX謾ｹ蝟・| 筮・譛ｪ逹謇・| 蜈ｱ蜷檎ｷｨ髮・Δ繝ｼ繝会ｼ・2 ﾂｧ3.4・榎
| Stage 5: 繧､繝ｳ繝輔Λ繝ｻ螳梧・ | 笨・螳溯｣・ｮ御ｺ・| Web繧ｵ繝ｼ繝√・MD豌ｸ邯壼喧繝ｻE2E繝・せ繝域ｸ・|
| Stage 6: 莉墓ｧ俶嶌螳悟・貅匁侠 | 笨・螳溯｣・ｮ御ｺ・| 繝舌げ菫ｮ豁｣縲、-2 15Worker蛹門ｮ御ｺ・|
| Stage 7: 逶｣譟ｻ繝ｻ驕狗畑菫晏ｮ・| 笨・螳溯｣・ｮ御ｺ・| 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・繝ｭ繝ｳ繝励ヨ縺ｮ謚ｽ蜃ｺ繝ｻ讒矩蛹悶Ξ繝昴・繝井ｽ懈・ |
| Stage 8: 譌･谺｡繝ｫ繝ｼ繝鈴ｫ伜ｺｦ蛹・| 笨・螳溯｣・ｮ御ｺ・| 諢滓ュ蠑ｷ蠎ｦ蛻､螳壹・4繝√ぉ繝・けAI繝ｻ邨ｱ蜷医お繝ｼ繧ｸ繧ｧ繝ｳ繝域僑蠑ｵ繝ｻkey memory蛻・屬繝ｻ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ螟壼ｱ､蛹・|
| Stage 9: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝育ｵｱ蜷医・繧ｳ繝ｳ繝・く繧ｹ繝域僑蜈・| 笨・螳溯｣・ｮ御ｺ・| Perceiver+Impulsive邨ｱ蜷医・raw text pass-through繝ｻ蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医∈縺ｮ繝槭け繝ｭ/荳也阜險ｭ螳・邨碁ｨ泥B蜷梧｢ｱ |
| Stage 10: 繧ｹ繝医Ξ繝ｼ繧ｸ邨ｱ荳繝ｻ迥ｶ諷区ｰｸ邯壼喧 | 笨・螳溯｣・ｮ御ｺ・| 1繧ｭ繝｣繝ｩ=1繝・ぅ繝ｬ繧ｯ繝医Μ邨ｱ荳繝ｻShortTermMemoryDB/MoodState譌･蜊倅ｽ肴ｰｸ邯壼喧繝ｻ譌･谺｡繝ｫ繝ｼ繝怜・髢句ｯｾ蠢・|
| Stage 11: Gemma4蟒・ｭ｢繝ｻ豢ｻ諤ｧ蛹悶お繝ｼ繧ｸ繧ｧ繝ｳ繝亥ｼｷ蛹・| 笨・螳溯｣・ｮ御ｺ・| Gemma4螳悟・蟒・ｭ｢竊竪emini 2.5 Pro邨ｱ荳縲∵ｴｻ諤ｧ蛹悶お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓繝槭け繝ｭ繝励Ο繝輔ぅ繝ｼ繝ｫ繝ｻ邨碁ｨ泥B蜈･蜉幄ｿｽ蜉 |
| Stage 12: Day1荳也阜隕ｳ蟆主・繝ｻ繧､繝吶Φ繝域焚隱ｿ謨ｴ繝ｻ鄙梧律莠亥ｮ壼ｿ・亥喧 | 笨・螳溯｣・ｮ御ｺ・| Day1譌･險倥↓荳也阜隕ｳ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ霑ｽ蜉縲∵律險俶枚蟄玲焚邏・00蟄礼ｵｱ荳縲√う繝吶Φ繝域焚2-4莉ｶ/譌･縲∫ｿ梧律莠亥ｮ壹ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ |
| Stage 13: 險隱樒噪陦ｨ迴ｾ譁ｹ豕輔・迢ｬ遶句喧 | 笨・螳溯｣・ｮ御ｺ・| VoiceFingerprint竊鱈inguisticExpression迢ｬ遶句喧縲∵歓雎｡逧・幕繧頑婿髮ｰ蝗ｲ豌・譌･險俶嶌縺肴婿縺ｮ遨ｺ豌玲─霑ｽ蜉縲∵律險倡函謌舌・繝ｭ繝ｳ繝励ヨ縺ｫ縺ｮ縺ｿ豕ｨ蜈･ |
| Stage 14: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け逕滓・蛹・| 笨・螳溯｣・ｮ御ｺ・| Phase A-3/D Step5縺ｮ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け蛹悶，reative Director閾ｪ蟾ｱ謇ｹ蛻､蠑ｷ蛹悶・螻､閾ｪ蟾ｱ謇ｹ蛻､(螟夜Κ謇ｹ隧・蜀・怐)蟆主・ |
| Stage 15: 繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝亥句挨蜀咲函謌舌・邱ｨ髮・| 笨・螳溯｣・ｮ御ｺ・| regeneration.py譁ｰ險ｭ縲∝・5繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ縺ｫregeneration_context豕ｨ蜈･縲仝S 2繧｢繧ｯ繧ｷ繝ｧ繝ｳ霑ｽ蜉縲∝・逕滓・/邱ｨ髮・Δ繝ｼ繝繝ｫUI |
| Stage 16: 譌･險倥お繝ｼ繧ｸ繧ｧ繝ｳ繝域署蜃ｺ繧ｬ繝ｼ繝牙ｼｷ蛹・| 笨・螳溯｣・ｮ御ｺ・| submit_final_diary 縺ｫ check_diary_rules 蠢・医ご繝ｼ繝郁ｿｽ蜉縲…ritic荳榊惠譎ゅｂ譛菴朱剞繝ｫ繝ｼ繝ｫ繝吶・繧ｹ繝√ぉ繝・け螳滓命 |
| Stage 17: diary_critic LLM繝吶・繧ｹ邁｡邏蛹・| 笨・螳溯｣・ｮ御ｺ・| 繝ｫ繝ｼ繝ｫ繝吶・繧ｹ繝√ぉ繝・け蜈ｨ蟒・ｭ｢竊鱈LM荳諡ｬ讀懆ｨｼ縲…orrected_diary蟒・ｭ｢竊段ssues謖・遭縺ｮ縺ｿ縲｀acroProfile豕ｨ蜈･ |
| Stage 18: 隨ｬ荳芽・､懆ｨｼAI + 繧ｳ繝ｳ繝・く繧ｹ繝郁ｪｬ譏惹ｻ倅ｸ・| 笨・螳溯｣・ｮ御ｺ・| ThirdPartyReviewer譁ｰ險ｭ・郁ｪｭ閠・ｦ也せ5隕ｳ轤ｹ繝√ぉ繝・け・峨∵律險和gentic繝ｫ繝ｼ繝励↓third_party_review繝・・繝ｫ霑ｽ蜉・・谿ｵ髫弱ご繝ｼ繝亥喧・峨∝・繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医↓wrap_context縺ｫ繧医ｋ繧ｳ繝ｳ繝・く繧ｹ繝郁ｪｬ譏惹ｻ倅ｸ趣ｼ・hat/why/how 3轤ｹ隱ｬ譏趣ｼ・|
| Stage 19: 繝・う繝ｪ繝ｼ繝ｭ繧ｰ隕∫ｴ・・險俶・繧ｷ繧ｹ繝・Β蜀崎ｨｭ險・| 笨・螳溯｣・ｮ御ｺ・| 鄙梧律莠亥ｮ哂I繧呈律險倡函謌舌・蜑阪↓遘ｻ蜍包ｼ域律險倥↓譏取律縺ｸ縺ｮ諢丞髄繧貞渚譏蜿ｯ閭ｽ縺ｫ・峨．ailyLogStore譁ｰ險ｭ・域律蛻･繝輔か繝ｫ繝邂｡逅・・谿ｵ髫守噪LLM隕∫ｴ・↓繧医ｋ蠢伜唆繝励Ο繧ｻ繧ｹ・峨∵律險倥ｒ迢ｬ遶汽B縺ｨ縺励※蛻・屬・亥盾辣ｧ逕ｨ・峨《hort_term_memory縺ｮ繧ｽ繝ｼ繧ｹ繧壇iary竊定｡悟虚繝ｭ繧ｰ縺ｫ螟画峩縲＼compress_memories繧胆create_daily_log_and_summarize縺ｫ鄂ｮ謠・|
| Stage 20: 繧ｻ繝ｼ繝悶・繧､繝ｳ繝井ｺ碁㍾菫晏ｭ倥・荳ｭ譁ｭ蜀埼幕遒ｺ螳溷喧 | 笨・螳溯｣・ｮ御ｺ・| `_checkpoint()`繧担ID蜷・繧ｭ繝｣繝ｩ蜷阪・莠碁㍾菫晏ｭ倥↓螟画峩縲．ailyLoop縺ｧ縺ｮ蜷Дay螳御ｺ・ｾ継ackage.json譖ｴ譁ｰ縲〉un_diary_generation螳御ｺ・ｾ継ackage.json譛邨ゆｿ晏ｭ・|
| Stage 21: Gemini 2.5 Pro繧ｯ繧ｩ繝ｼ繧ｿ雜・℃譎ゅ・2谿ｵ髫弱ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ | 笨・螳溯｣・ｮ御ｺ・| `LLMModels.GEMINI_2_0_FLASH`霑ｽ蜉縲～_call_gemini_with_flash_fallback()`縺ｧ2.5 Pro竊・.0 Flash閾ｪ蜍募・繧頑崛縺茨ｼ医け繧ｩ繝ｼ繧ｿ雜・℃譎ゅ・縺ｿ・峨，laude螟ｱ謨玲凾繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ縺ｫ繧る←逕ｨ |
| Stage 22: LinguisticExpression蜈ｨ繝輔ぅ繝ｼ繝ｫ繝画ｴｻ逕ｨ繝ｻ隧ｳ邏ｰ繝舌Μ繝・・繧ｷ繝ｧ繝ｳ | 笨・螳溯｣・ｮ御ｺ・| `_build_voice_context()`繧貞ｮ悟・諡｡蠑ｵ・井ｺ御ｺｺ遘ｰ縲∫ｵｵ譁・ｭ励∬・蝠城ｻ蠎ｦ縲∵ｯ泌湊鬆ｻ蠎ｦ繧定ｿｽ蜉・峨～LinguisticExpressionValidator`譁ｰ險ｭ縲∵律險和gentic繝ｫ繝ｼ繝励↓`validate_linguistic_expression`繝・・繝ｫ霑ｽ蜉・・heck_diary_rules竊致alidate_linguistic_expression竊稚hird_party_review 縺ｮ3谿ｵ髫弱ご繝ｼ繝亥喧・・|
| Stage 23: 蜷・せ繝・ャ繝励＃縺ｨ縺ｮ繝医・繧ｯ繝ｳ豸郁ｲｻ繧ｳ繧ｹ繝郁ｨ倬鹸繧ｷ繧ｹ繝・Β | 笨・螳溯｣・ｮ御ｺ・| `TokenTracker.snapshot()`縺ｨ`cost_since()`繝｡繧ｽ繝・ラ霑ｽ蜉縲～DayProcessingState.cost_records`繝輔ぅ繝ｼ繝ｫ繝芽ｿｽ蜉縲．ailyLoopOrchestrator縺ｧ蜷・せ繝・ャ繝怜燕蠕後・繧ｹ繝翫ャ繝励す繝ｧ繝・ヨ蜿門ｾ励‥aily_logs譛ｫ蟆ｾ縺ｫ繧ｳ繧ｹ繝郁ｨ倬鹸繝・・繝悶Ν蜃ｺ蜉・|
| Stage 24: Opus繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医・繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ蜈医ｒGemini 3.1 Pro縺ｫ譖ｴ譁ｰ | 笨・螳溯｣・ｮ御ｺ・| `config.py`縺ｫ`GEMINI_3_1_PRO`螳壽焚霑ｽ蜉縲～_call_gemini_with_flash_fallback()`縺ｫ`gemini_model`繝代Λ繝｡繝ｼ繧ｿ霑ｽ蜉縲＾pus螟ｱ謨玲凾縺ｮ縺ｿ`GEMINI_3_1_PRO`繧呈欠螳壹ヾonnet/Gemini tier縺ｯGemini 2.5 Pro邯ｭ謖・|
| Stage 25: API繧ｭ繝ｼ縺ｮ蜍慕噪謫堺ｽ懊・莨晄眺繧ｷ繧ｹ繝・Β | 笨・螳溯｣・ｮ御ｺ・| 蜈ｨ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥ｱ､・・aster/DailyLoop/Workers/DailyAgents・峨∈縺ｮ蜍慕噪繝励Ο繝代ご繝ｼ繧ｷ繝ｧ繝ｳ縺ｨ繝輔Ο繝ｳ繝医お繝ｳ繝蔚I縺ｮ邨ｱ蜷医ｒ螳御ｺ・・|
| Stage 26: Phase A-2蝙九ヲ繝ｳ繝域ｬ關ｽ繝舌げ菫ｮ豁｣ | 笨・螳溯｣・ｮ御ｺ・| `backend/agents/phase_a2/orchestrator.py`縺ｧ`Optional`蝙九ヲ繝ｳ繝医′菴ｿ逕ｨ縺輔ｌ縺ｦ縺・ｋ縺ｮ縺ｫ`typing.Optional`縺後う繝ｳ繝昴・繝医＆繧後※縺・↑縺九▲縺溷撫鬘後ｒ菫ｮ豁｣縲Ａfrom typing import Optional`霑ｽ蜉縲・|
| Stage 27: CharacterCapabilities・域園謖∝刀繝ｻ閭ｽ蜉帙・蜿ｯ閭ｽ陦悟虚・芽ｿｽ蜉 | 笨・螳溯｣・ｮ御ｺ・| 4繝｢繝・Ν譁ｰ險ｭ・・ossessedItem/CharacterAbility/AvailableAction/CharacterCapabilities・峨￣hase D 縺ｫ caps_task 荳ｦ蛻苓ｿｽ蜉縲｀aster Orchestrator 縺ｧ package 縺ｫ譬ｼ邏阪．aily Loop 縺ｮ邨ｱ蜷医・譌･險倥お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓謚募・縲｀D 縺ｫ 4.5 繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ霑ｽ蜉 |
| Stage 28: Creative Director 縺ｸ縺ｮ CapabilitiesHints 霑ｽ蜉 | 笨・螳溯｣・ｮ御ｺ・| `CapabilitiesHints`繝｢繝・Ν譁ｰ險ｭ繝ｻConceptPackage縺ｫ邨ｱ蜷医，reative Director蜃ｺ蜉帙せ繧ｭ繝ｼ繝・謇ｹ隧輔メ繧ｧ繝・け譖ｴ譁ｰ縲￣hase D縺ｮ`_full_context()`縺ｧhints譏守､ｺ豕ｨ蜈･ |
| Stage 29: DailyLoopOrchestrator驥榊､ｧ遐ｴ謳榊ｾｩ蜈・| 笨・菫ｮ豁｣螳御ｺ・| 繧ｳ繝溘ャ繝・eae012縺ｧ1000陦御ｻ･荳頑ｶ亥､ｱ縺励※縺・◆蝠城｡後ｒ2caa6f8繝吶・繧ｹ縺ｧ蠕ｩ蜈・∥pi_keys+capabilities邨ｱ蜷・|
| Stage 30: 諤ｧ譬ｼ繝ｻ豌苓ｳｪ繝代Λ繝｡繝ｼ繧ｿ髫阡ｽ + 遏ｭ譛溯ｨ俶・蜆ｪ蜈医メ繧ｧ繝・き繝ｼ險ｭ險・| 笨・螳溯｣・ｮ御ｺ・| 繝代Λ繝｡繝ｼ繧ｿ #1-#52 縺ｮ險ｭ險郁ｨ倬鹸 |
| Stage 32: `_generate_diary` NameError菫ｮ豁｣ + linguistic_expression 縺ｮ user_message 譏守､ｺ豕ｨ蜈･ | 笨・菫ｮ豁｣螳御ｺ・| normative_context/protagonist_plan_note 譛ｪ螳夂ｾｩ繝舌げ隗｣豸医∬ｨ隱樒噪陦ｨ迴ｾ繝・・繧ｿ繧・user_message 縺ｫ繧よ・遉ｺ霑ｽ蜉 |
| Stage 31: CharacterCapabilitiesWorker 繧偵お繝ｼ繧ｸ繧ｧ繝ｳ繝医↓譏・ｼ | 笨・螳溯｣・ｮ御ｺ・| `capabilities_agent.py` 譁ｰ險ｭ縲《earch_web 2蝗樔ｻ･荳雁ｿ・・謇ｹ隧・蜀・怐縺ｮ5繝輔ぉ繝ｼ繧ｺ繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝亥喧縲￣hase D Step 2.5 縺ｨ縺励※迢ｬ遶句ｮ溯｡・|
| Stage 33: 莉墓ｧ俶嶌 vs 螳溯｣・さ繝ｼ繝牙ｷｮ蛻・・譫舌・蜉遲・ｨ育判遲門ｮ・| 笨・蛻・梵螳御ｺ・| v10/v2莉墓ｧ俶嶌縺ｨ螳溯｣・さ繝ｼ繝峨・菴鍋ｳｻ逧・ｷｮ蛻・・譫仙ｮ御ｺ・・繧ｫ繝・ざ繝ｪ・・:諢丞峙逧・､画峩8莉ｶ縲。:霑ｽ蜉讖溯・11莉ｶ縲，:譛ｪ螳溯｣・莉ｶ縲．:謨ｰ蛟､逶ｸ驕・莉ｶ・峨↓蛻・｡槭ゆｻ墓ｧ俶嶌蜉遲・ｨ育判・・10: 12鬆・岼縲」2: 15鬆・岼・臥ｭ門ｮ壽ｸ医りｩｳ邏ｰ繝ｬ繝昴・繝・ `tasks/spec_vs_implementation_report.md` |
| Stage 34: 繧ｯ繝ｪ繝・ぅ繧ｫ繝ｫ繝舌げ菫ｮ豁｣・・ameError 3莉ｶ + 繝・・繧ｿ谺謳・+ 繧ｳ繝ｳ繝・く繧ｹ繝域ｬ關ｽ・・| 笨・菫ｮ豁｣螳御ｺ・| 讀懆ｨｼ繝ｬ繝昴・繝育罰譚･縺ｮ閾ｴ蜻ｽ繝ｻ鬮伜━蜈亥ｺｦ繝舌げ7莉ｶ繧貞・菫ｮ豁｣縲や蔵`_values_violation()` normative_context NameError縲≫贈`_introspection()` normative_context/protagonist_plan_note NameError縲≫造`_extract_key_memory()` action_summary NameError・・vents_processed 蠑墓焚霑ｽ蜉繝ｻ蜻ｼ縺ｳ蜃ｺ縺怜・譖ｴ譁ｰ・峨≫促Phase D supporting_chars 譛ｪ繝代・繧ｹ蝠城｡鯉ｼ・LM JSON螟画鋤繧ｹ繝・ャ繝苓ｿｽ蜉・峨≫側`_introspection()` 蜻ｨ蝗ｲ莠ｺ迚ｩ繧ｳ繝ｳ繝・く繧ｹ繝域ｬ關ｽ縲≫則`_generate_diary()` 蜻ｨ蝗ｲ莠ｺ迚ｩ繝ｻ閾ｪ莨晉噪繧ｨ繝斐た繝ｼ繝画ｬ關ｽ縲≫即PROJECT.md蜀帝ｭ繝輔Ο繝ｼ險倩ｿｰ縺ｮ鄙梧律莠亥ｮ壻ｽ咲ｽｮ菫ｮ豁｣ |
| Stage 35: 鄙梧律莠亥ｮ夊ｿｽ蜉繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・NameError/AttributeError菫ｮ豁｣ | 笨・菫ｮ豁｣螳御ｺ・| `next_day_planning.py`縺ｮ`stage1_protagonist_plan()`縺梧ｯ主屓繧ｯ繝ｩ繝・す繝･縺励※縺・◆閾ｴ蜻ｽ繝舌げ繧剃ｿｮ豁｣縲や蔵`wrap_context`譛ｪ繧､繝ｳ繝昴・繝茨ｼ・context_descriptions.py`縺九ｉ霑ｽ蜉・峨≫贈`self._build_memory_context()`縺君extDayPlanningAgent繧ｯ繝ｩ繧ｹ縺ｫ蟄伜惠縺励↑縺・ｼ・memory_context`繝代Λ繝｡繝ｼ繧ｿ縺ｨ縺励※繧ｪ繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ繝ｼ縺九ｉ豕ｨ蜈･縺吶ｋ譁ｹ蠑上↓螟画峩・峨ゅ％縺ｮ菫ｮ豁｣縺ｫ繧医ｊ`protagonist_plan`繧､繝吶Φ繝医′蛻昴ａ縺ｦweekly_events_store縺ｫ謖ｿ蜈･縺輔ｌ繧九ｈ縺・↓縺ｪ繧翫」10 ﾂｧ4.9.4縺ｮ讖溯・縺檎ｨｼ蜒埼幕蟋・|
| Stage 36: README.md莉墓ｧ俶嶌繝ｬ繝吶Ν謚陦薙ラ繧ｭ繝･繝｡繝ｳ繝亥喧 | 笨・螳御ｺ・| 邁｡譏迭EADME縺九ｉspecification_v10.md繝ｻv2繝ｻPROJECT.md縺ｮ蜀・ｮｹ繧堤ｵｱ蜷医＠縺滓ｿ・ｯ・↑謚陦薙ラ繧ｭ繝･繝｡繝ｳ繝医↓蜈ｨ髱｢蛻ｷ譁ｰ縲りｨｭ險域晄Φ6蜴溷援縲・螻､繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝磯嚴螻､隧ｳ邏ｰ蝗ｳ隗｣縲・2繝代Λ繝｡繝ｼ繧ｿ蜈ｨ讒矩縲・國阡ｽ蜴溷援縲ヽedemption Bias蟇ｾ遲悶．aily Loop隱咲衍繧ｷ繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ蜈ｨ繝輔Ο繝ｼ縲・螻､險俶・繧ｷ繧ｹ繝・Β縲´LM繝・ぅ繧｢繧ｷ繧ｹ繝・Β縲∵､懆ｨｼ繝ｻ隧穂ｾ｡7遞ｮ縲√ョ繝ｼ繧ｿ繝｢繝・Ν繝ｻ繧ｹ繝医Ξ繝ｼ繧ｸ讒矩縲、PI/WebSocket莉墓ｧ倥∝・陦檎皮ｩｶ14逅・ｫ門ｯｾ蠢懆｡ｨ繧堤ｶｲ鄒・ｼ・49陦娯・邏・50陦鯉ｼ・|
| Stage 37: Human in the Loop・育黄隱樊ｧ区・繝励Μ繝輔ぃ繝ｬ繝ｳ繧ｹ + 繧ｳ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ・・| 笨・螳溯｣・ｮ御ｺ・| `StoryCompositionPreferences`・・繧ｫ繝・ざ繝ｪ78+驕ｸ謚櫁い縲∵枚迪ｮ繝吶・繧ｹ11逅・ｫ門ｮｶ・峨，reative Director讒区・譁ｹ驥晄ｳｨ蜈･+Self-Critique[G]霑ｽ蜉縲～asyncio.Event`縺ｫ繧医ｋconcept_review荳譎ょ●豁｢縲∥pprove/revise/edit 3繧｢繧ｯ繧ｷ繝ｧ繝ｳ縲√い繧ｳ繝ｼ繝・ぅ繧ｪ繝ｳ蝙九き繝ｼ繝蛾∈謚朸I縲√さ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ逕ｻ髱｢縲ょ､画峩繝輔ぃ繧､繝ｫ: character.py, main.py, orchestrator.py, director.py, index.html, app.js, style.css |
| Stage 38: Phase D繧ｨ繝ｩ繝ｼ菫ｮ豁｣繝ｻ繧ｿ繧ｹ繧ｯ邂｡逅・隼蝟・・荳ｭ譁ｭ讖溯・ | 笨・螳溯｣・ｮ御ｺ・| `MALFORMED_FUNCTION_CALL`繧ｨ繝ｩ繝ｼ縺ｮ蝗槫ｾｩ蜃ｦ逅・ｼｷ蛹厄ｼ・lm_api.py: 螢翫ｌ縺溷ｱ･豁ｴ蜑企勁+蜈ｷ菴鍋噪繝ｪ繧ｫ繝舌Μ繝｡繝・そ繝ｼ繧ｸ+400繧ｨ繝ｩ繝ｼ蟇ｾ蠢懶ｼ峨・asterOrchestrator: `cancel()`繝｡繧ｽ繝・ラ+`_cancelled`繝輔Λ繧ｰ+`set_master_orch()`縺ｫ繧医ｋ荳倶ｽ阪が繝ｼ繧ｱ繧ｹ繝医Ξ繝ｼ繧ｿ縺ｸ縺ｮ繧ｭ繝｣繝ｳ繧ｻ繝ｫ莨晄眺縲１haseDOrchestrator: 蜷・せ繝・ャ繝・WorldContext/SupportingCharacters/Capabilities/NarrativeArc/ConflictIntensity)縺ｫ譌｢蟄倥ョ繝ｼ繧ｿ繝√ぉ繝・け+繧ｹ繧ｭ繝・・讖溯・霑ｽ蜉縲∫函謌千峩蠕後↓繝√ぉ繝・け繝昴う繝ｳ繝井ｿ晏ｭ倥～_check_cancelled()`縺ｫ繧医ｋ荳ｭ譁ｭ繝昴う繝ｳ繝・邂・園螳溯｣・Ｎain.py: `cancel_character_generation` WebSocket繧｢繧ｯ繧ｷ繝ｧ繝ｳ霑ｽ蜉縲√ち繧ｹ繧ｯ繧蜘s_active_tasks縺ｧ邂｡逅・ゅヵ繧ｧ繝ｼ繧ｺ繧ｹ繧ｭ繝・・蛻､螳壹ｒ繝・・繧ｿ蜀・ｮｹ縺ｮ蜈・ｮ溷ｺｦ縺ｧ蛻､螳壹☆繧九ｈ縺・↓蠑ｷ蛹厄ｼ・mpty object縺ｧ縺ｯ騾夐℃縺励↑縺・ｼ峨ょ､画峩繝輔ぃ繧､繝ｫ: llm_api.py, master_orchestrator/orchestrator.py, phase_d/orchestrator.py, main.py |
| Stage 39: repomix MCP 繧ｵ繝ｼ繝舌・逋ｻ骭ｲ繝ｻ繧ｳ繝ｼ繝峨・繝ｼ繧ｹ謚頑升謇矩・・讓呎ｺ門喧 | 笨・螳御ｺ・| Claude Code 縺ｫ repomix MCP 繧ｵ繝ｼ繝舌・・・cmd /c npx -y repomix --mcp`・峨ｒ繝励Ο繧ｸ繧ｧ繧ｯ繝医せ繧ｳ繝ｼ繝励〒逋ｻ骭ｲ縲８indows 縺ｧ `npx` 縺檎峩謗･襍ｷ蜍輔〒縺阪↑縺・◆繧・`cmd /c` 邨檎罰縺ｮ繝ｩ繝・ヱ繝ｼ繧呈治逕ｨ縲・CP 繝倥Ν繧ｹ繝√ぉ繝・け縲娯恣 Connected縲咲｢ｺ隱肴ｸ医ゅ・繝ｭ繧ｸ繧ｧ繧ｯ繝・`CLAUDE.md` 縺ｫ縲御ｽｿ逕ｨ蜿ｯ閭ｽ縺ｪ MCP 繧ｵ繝ｼ繝舌・縲阪そ繧ｯ繧ｷ繝ｧ繝ｳ繧定ｿｽ蜉縺励・*繧ｳ繝ｼ繝峨・蜈ｨ菴灘ワ繧呈滑謠｡縺吶ｋ蠢・ｦ√′縺ゅｋ蝣ｴ蜷医・ repomix MCP・・pack_codebase` / `pack_remote_repository`・峨ｒ蠢・★蜆ｪ蜈井ｽｿ逕ｨ縺吶ｋ**驕狗畑繝ｫ繝ｼ繝ｫ繧呈・譁・喧縲ょ句挨 Glob/Grep/Read 縺ｮ螟壽焚蝗槫他縺ｳ蜃ｺ縺励ｈ繧雁・縺ｫ pack 竊・`grep_repomix_output` 縺ｫ繧医ｋ蠢・ｦ∫ｮ・園謚ｽ蜃ｺ繧定｡後≧謇矩・ｒ讓呎ｺ門喧縲ょ､画峩繝輔ぃ繧､繝ｫ: `CLAUDE.md`, `C:\Users\mahim\.claude.json`・・CP 逋ｻ骭ｲ・・|
| Stage 40: 荳ｭ譁ｭ蜀埼幕繝輔ぉ繝ｼ繧ｺ縺ｮ鬮倬溷喧縺ｨ繧ｻ繝・す繝ｧ繝ｳ螟画焚縺ｮ螳牙ｮ壼喧 | 笨・菫ｮ豁｣螳御ｺ・| `resume_character_generation`螳溯｡梧凾縺ｫ`active_orchestrator`繧ｰ繝ｭ繝ｼ繝舌Ν螟画焚縺瑚ｨｭ螳壹＆繧後※縺翫ｉ縺壹√ヵ繝ｭ繝ｳ繝医お繝ｳ繝峨・繝ｬ繝薙Η繝ｼ繧｢繧ｯ繧ｷ繝ｧ繝ｳ縺後後い繧ｯ繝・ぅ繝悶↑逕滓・繧ｻ繝・す繝ｧ繝ｳ縺後≠繧翫∪縺帙ｓ縲阪〒螟ｱ謨励☆繧九ヰ繧ｰ繧剃ｿｮ豁｣縲ょ酔譎ゅ↓縲∽ｸ区ｵ√・Phase A-1縺悟ｭ伜惠縺吶ｋ蝣ｴ蜷茨ｼ・has_downstream`・峨・驕主悉縺ｫ繧ｳ繝ｳ繧ｻ繝励ヨ繝ｬ繝薙Η繝ｼ縺梧価隱肴ｸ医∩縺ｧ縺ゅｋ縺ｨ蛻､螳壹＠縲∝・髢区凾縺ｮ荳崎ｦ√↑蠕・ｩ溘ｒ繧ｹ繧ｭ繝・・縺吶ｋ繝ｭ繧ｸ繝・け繧貞ｰ主・縲ゅ％繧後↓繧医ｊ蜈ｨ繝√ぉ繝・け繝昴う繝ｳ繝医°繧峨・騾泌・繧後・縺ｪ縺・・髢九・繝輔ぃ繧ｹ繝医ヵ繧ｩ繝ｯ繝ｼ繝峨ｒ螳溽樟縲ょ､画峩繝輔ぃ繧､繝ｫ: main.py, orchestrator.py |
| Stage 41: Phase D 荳ｭ譁ｭ蜀埼幕譎ゅ・ AttributeError 菫ｮ豁｣ | 笨・菫ｮ豁｣螳御ｺ・| Phase D縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝亥・髢区凾縲～ConflictIntensityArc`縺ｫ蟄伜惠縺励↑縺Яdaily_intensities`螻樊ｧ縺ｮ`len()`繧定ｩ穂ｾ｡縺励※繧ｯ繝ｩ繝・す繝･縺吶ｋ繝舌げ繧剃ｿｮ豁｣縲ＡConflictIntensityArc`繝｢繝・Ν縺ｫ`raw_text`繝輔ぅ繝ｼ繝ｫ繝峨ｒ蠕梧婿莠呈鋤諤ｧ繧呈戟縺溘○縺ｦ霑ｽ蜉縺励√せ繧ｭ繝・・蛻､螳壹→繝・く繧ｹ繝亥ｾｩ蜈・ｒ豁｣縺励￥陦後≧繧医≧菫ｮ豁｣縲ょ､画峩繝輔ぃ繧､繝ｫ: character.py, phase_d/orchestrator.py |
| Stage 42: 譌･險倡函謌仙●豁｢蝠城｡後・菫ｮ豁｣・・ameError + 繧ｨ繝ｩ繝ｼ繝上Φ繝峨Μ繝ｳ繧ｰ・・| 笨・菫ｮ豁｣螳御ｺ・| `linguistic_validator.py` 縺ｮ `Optional` 繧､繝ｳ繝昴・繝域ｼ上ｌ菫ｮ豁｣縲√♀繧医・ `main.py` 縺ｮ髱槫酔譛溘ち繧ｹ繧ｯ蛻晄悄蛹悶ヵ繧ｧ繝ｼ繧ｺ縺ｸ縺ｮ蛹・峡逧・try-except 蟆主・縺ｫ繧医ｊ縲√し繧､繝ｬ繝ｳ繝亥●豁｢蝠城｡後ｒ隗｣豎ｺ縲よ､懆ｨｼ E2E 繝・せ繝茨ｼ・ay 1 譛ｬ逡ｪ蜍穂ｽ懶ｼ牙ｮ御ｺ・・|
| Stage 43: 譌･險倡函謌舌そ繝・す繝ｧ繝ｳ邂｡逅・+ Day繝ｭ繧ｰ蛻・屬 | 笨・螳溯｣・ｮ御ｺ・| DailyLoopOrchestrator縺ｫsession_id邂｡逅・ｰ主・・医く繝｣繝ｩ蜷・繧ｿ繧､繝繧ｹ繧ｿ繝ｳ繝暦ｼ峨［ain.py縺ｫ蜷梧凾螳溯｡碁亟豁｢繧ｬ繝ｼ繝会ｼ・_diary_generation_active` Set・芽ｿｽ蜉縲Ｔave_daily_log()縺九ｉ陦晏虚/逅・ｧ蜃ｺ蜉帙ｒ髯､蜴ｻ縺励∵眠髢｢謨ｰsave_rim_outputs()縺ｧ`Day_{N}_rim_outputs.md`縺ｫ蛻・屬菫晏ｭ倥・generate_diary()縺ｮ繧ｷ繧ｹ繝・Β繝励Ο繝ｳ繝励ヨ縺ｫ繧ｭ繝｣繝ｩ蜷阪・繧ｻ繝・す繝ｧ繝ｳID繧呈・遉ｺ豕ｨ蜈･縺励∝・繝ｭ繧ｰ縺ｫsession_id縺ｨexc_info=True繧定ｿｽ蜉 |
| Stage 44: 蜀咲函謌舌・遐ｴ螢顔噪謫堺ｽ懈賜髯､繝ｻ繧ｻ繧ｯ繧ｷ繝ｧ繝ｳ驕ｸ謚槫梛UI遘ｻ陦後→螻･豁ｴ繝舌ャ繧ｯ繧｢繝・・遒ｺ菫・| 笨・螳溯｣・ｮ御ｺ・| `regenerateCharacter()` 縺ｫ縺翫￠繧句・繝代ャ繧ｱ繝ｼ繧ｸ豸亥悉縺ｮ遐ｴ螢顔噪蜃ｦ逅・ｒ螳悟・蟒・ｭ｢縺励√後そ繧ｯ繧ｷ繝ｧ繝ｳ蜊倅ｽ阪・蜀咲函謌撰ｼ・ection-select-modal・峨阪∈縺ｮ隱伜ｰ弱↓螟画峩縲ゅ檎ｴ譽・＠縺ｦ蜀咲函謌舌阪↓繧医ｋ繝・・繧ｿ蝟ｪ螟ｱ繝ｪ繧ｹ繧ｯ繧呈ｧ矩逧・↓謗帝勁縲ゅ＆繧峨↓ `backend/main.py` 縺ｫ縺ｦ縲√い繝ｼ繝・ぅ繝輔ぃ繧ｯ繝医・蜀咲函謌舌ｄ謇句虚邱ｨ髮・′螳溯｡後・菫晏ｭ倥＆繧後ｋ逶ｴ蜑阪↓縲∝ｿ・★蜈・・ `package.json` 繧・`package_backup_YYYYMMDD_HHMMSS_{name}_{action}.json` 縺ｨ縺励※閾ｪ蜍輔ヰ繝・け繧｢繝・・縺吶ｋ讖溯・繧定ｿｽ蜉縲ゆｸ頑嶌縺阪↓繧医ｋ驕主悉縺ｮ逕滓・邨先棡縺ｮ螳悟・蝟ｪ螟ｱ繧帝亟縺蝉ｿ晁ｭｷ讖滓ｧ九ｒ遒ｺ遶九・|
| Stage 45: 譌･險伜・逕滓・讖溯・縺ｮ霑ｽ蜉縺ｨ閾ｪ蜍輔ヰ繝・け繧｢繝・・・医ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・ｼ・| 笨・螳溯｣・ｮ御ｺ・| 譌･險倩｡ｨ遉ｺ繧ｿ繝悶∈縺ｮ繝懊ち繝ｳ邨ｱ蜷医∝・逕滓・蜑阪・譌｢蟄倥ョ繝ｼ繧ｿ・郁ｨ俶・繝ｻ繝繝ｼ繝峨・繝ｭ繧ｰ・峨・ `backups/` 繝輔か繝ｫ繝縺ｸ縺ｮ閾ｪ蜍暮驕ｿ・医ヰ繝ｼ繧ｸ繝ｧ繝ｳ邂｡逅・ｼ峨√Θ繝ｼ繧ｶ繝ｼ謖・､ｺ縺ｮ繝励Ο繝ｳ繝励ヨ豕ｨ蜈･縺ｫ繧医ｋ繧ｫ繧ｹ繧ｿ繝槭う繧ｺ蜿ｯ閭ｽ縺ｪ蜀咲函謌舌ｒ螳溽樟縲・|
### 谺｡縺ｮ繧｢繧ｯ繧ｷ繝ｧ繝ｳ

1. **縲宣㍾隕√台ｻ墓ｧ俶嶌蜉遲・・險ｭ險亥愛譁ｭ** 竊・諢滓ュ蠑ｷ蠎ｦ繝舌う繝代せ譁ｹ蠑上√う繝吶Φ繝域焚縲￣hase B螳溯｣・怏辟｡縺ｮ3轤ｹ繧呈ｱｺ螳・
2. **莉墓ｧ俶嶌v10縺ｸ縺ｮ蜉遲・ｼ・hase 1, 12鬆・岼・・* 竊・Perceiver邨ｱ蜷医´inguisticExpression縲，haracterCapabilities遲・
3. **莉墓ｧ俶嶌v2縺ｸ縺ｮ蜉遲・ｼ・hase 2, 15鬆・岼・・* 竊・謚陦薙せ繧ｿ繝・け蜈ｨ髱｢謾ｹ險ゅ￣hase A-3/D繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝・ぅ繝・け蛹也ｭ・
4. **E2E繝・せ繝亥ｮ溯｡鯉ｼ・ay0竊呈律險倥す繝溘Η繝ｬ繝ｼ繧ｷ繝ｧ繝ｳ騾壹＠・・* 竊・draft繝励Ο繝輔ぃ繧､繝ｫ縺ｧ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・竊呈律險倡函謌舌∪縺ｧ繧帝｣邯壼ｮ溯｡後＠縲∝・繝輔Ο繝ｼ縺ｮ蜍穂ｽ懃｢ｺ隱阪☆繧・
5. **謠仙・逕ｨ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕滓・** 竊・High Quality繝励Ο繝輔ぃ繧､繝ｫ縺ｧ蜈ｨEvaluator繧丹N縺ｫ縺励｀D繝・・繧ｿ繝吶・繧ｹ蜃ｺ蜉帙∪縺ｧ騾壹＠縺ｦ螳溯｡後☆繧・



### 繝悶Ο繝・き繝ｼ

> [!WARNING]
> - Anthropic API縺ｮ繧ｯ繝ｬ繧ｸ繝・ヨ谿矩ｫ倅ｸ崎ｶｳ縺ｫ繧医ｊ蜈ｨClaude蜻ｼ縺ｳ蜃ｺ縺励′Gemini 2.5 Pro縺ｸ繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ荳ｭ縲よ悽遞ｼ蜒肴凾縺ｯ譛牙─Tier繧ｭ繝ｼ縺悟ｿ・ｦ√・
> - Gemini 2.5 Pro縺ｮ1譌･1000繝ｪ繧ｯ繧ｨ繧ｹ繝育┌譁呎棧雜・℃譎ゅ・縲；emini 2.0 Flash・・500繝ｪ繧ｯ繧ｨ繧ｹ繝・譌･・峨∈縺ｮ閾ｪ蜍輔ヵ繧ｩ繝ｼ繝ｫ繝舌ャ繧ｯ繧貞ｮ溯｣・ｸ医∩・・tage 21・峨・
> - Gemini 2.5 Pro縺ｮ諤晁・ヨ繝ｼ繧ｯ繝ｳ蝠城｡後・菫ｮ豁｣貂医∩縲・SON萓晏ｭ俶賜髯､繝ｻ繝ｪ繝医Λ繧､讖滓ｧ玖ｿｽ蜉繧ょｮ御ｺ・・
> - Gemma 4繧貞ｮ悟・蟒・ｭ｢縺励∵怙菴弱ユ繧｣繧｢繧竪emini 2.5 Pro縺ｫ邨ｱ荳貂医∩縲Ａcall_gemma()`竊蛋call_google_ai()`縺ｫ繝ｪ繝阪・繝縲・
> - 蜈ｨAgentic繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝茨ｼ・irector, Integration, Diary・峨〒Claude竊竪emini竊偵ョ繝輔か繝ｫ繝亥､縺ｮ3螻､繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ螳溯｣・ｸ医∩縲・
> - end-of-day蜃ｦ逅・・蜷・せ繝・ャ繝暦ｼ亥・逵√・譌･險倥・key memory繝ｻ鄙梧律莠亥ｮ夲ｼ峨↓蛟句挨繧ｨ繝ｩ繝ｼ繝上Φ繝峨Μ繝ｳ繧ｰ霑ｽ蜉貂医∩縲・


### 26. 繧ｷ繧ｹ繝・Β繝ｻ繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝医・豌ｸ邯壼喧縺ｨ騾乗・諤ｧ

- **Subject / Feature**: 螳溯｣・ｨ育判繧・え繧ｩ繝ｼ繧ｯ繧ｹ繝ｫ繝ｼ險倬鹸縺ｮ菫晏ｭ倡ｮ｡逅・
- **(a) Original Design**: 繧ｨ繝ｼ繧ｸ繧ｧ繝ｳ繝医′逕滓・縺吶ｋ繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝医・縲∝ｯｾ隧ｱ荳ｭ縺ｮUI荳翫〒縺ｮ縺ｿ陦ｨ遉ｺ縺輔ｌ繧倶ｸ譎ら噪縺ｪ繧ゅ・縺ｨ縺・≧隱崎ｭ倥・
- **(b) The Change & Rationale**: 繝ｦ繝ｼ繧ｶ繝ｼ縺九ｉ縲碁℃蜴ｻ縺ｮ繧ｦ繧ｩ繝ｼ繧ｯ繧ｹ繝ｫ繝ｼ縺ｯ縺ｩ縺薙↓菫晏ｭ倥＆繧後※縺・ｋ縺ｮ縺九阪→縺・≧蝠上＞縺ｫ蟇ｾ縺励∵ｰｸ邯夂噪縺ｪ繝医Ξ繝ｼ繧ｵ繝薙Μ繝・ぅ繧剃ｿ晁ｨｼ縺吶ｋ蠢・ｦ√′逕溘§縺溘・
- **(c) Adopted Best Practice**: 莨夊ｩｱID縺ｫ邏舌▼縺・`brain` 繝輔か繝ｫ繝縺ｸ蜈ｨ繧｢繝ｼ繝・ぅ繝輔ぃ繧ｯ繝茨ｼ医♀繧医・縺昴・迚育ｮ｡逅・ョ繝ｼ繧ｿ・峨ｒ閾ｪ蜍穂ｿ晏ｭ倥＠縲√・繝ｭ繧ｸ繧ｧ繧ｯ繝医・螟夜Κ遏･隴假ｼ・nowledge・峨→縺励※繧ゅ％繧後ｉ繧貞盾辣ｧ蜿ｯ閭ｽ縺ｫ縺吶ｋ譁ｹ驥昴ｒ謗｡逕ｨ縲・

---

## 繧｢繝励Μ縺ｮ蜀崎ｵｷ蜍墓婿豕・

繝舌ャ繧ｯ繧ｨ繝ｳ繝峨し繝ｼ繝舌・・・astAPI・峨・蜀崎ｵｷ蜍輔・縲∽ｻ･荳九・謇矩・〒陦後▲縺ｦ縺上□縺輔＞縲りｩｳ邏ｰ縺ｯ [backend-management 繧ｹ繧ｭ繝ｫ](file:///c:/Users/mahim/.gemini/antigravity/scratch/AI_character_story_generater/.agents/skills/backend-management/SKILL.md) 繧貞盾辣ｧ縺励※縺上□縺輔＞縲・

### 1. 譌｢蟄倥・繝ｭ繧ｻ繧ｹ縺ｮ蛛懈ｭ｢・医・繝ｼ繝・8001 蜊譛画凾・・

繝昴・繝・8001 繧剃ｽｿ逕ｨ縺励※縺・ｋ繝励Ο繧ｻ繧ｹ繧堤音螳壹＠縲∝ｼｷ蛻ｶ邨ゆｺ・＠縺ｾ縺吶・

```powershell
# 繝昴・繝・8001 繧剃ｽｿ逕ｨ縺励※縺・ｋ PID 繧堤音螳・
netstat -ano | findstr :8001

# 迚ｹ螳壹＠縺・PID・井ｾ・ 27276・峨ｒ蠑ｷ蛻ｶ邨ゆｺ・
taskkill /F /PID 27276
```

> [!TIP]
> 蜈ｨ縺ｦ縺ｮ Python 繝励Ο繧ｻ繧ｹ繧堤ｵゆｺ・＆縺帙※繧り憶縺・ｴ蜷医・ `taskkill /F /IM python.exe` 縺御ｽｿ逕ｨ蜿ｯ閭ｽ縺ｧ縺吶・

### 2. 繧｢繝励Μ縺ｮ襍ｷ蜍・

繝励Ο繧ｸ繧ｧ繧ｯ繝医・繝ｫ繝ｼ繝医ョ繧｣繝ｬ繧ｯ繝医Μ縺ｧ莉･荳九・繧ｳ繝槭Φ繝峨ｒ螳溯｡後＠縺ｾ縺吶・

```powershell
# 讓呎ｺ也噪縺ｪ襍ｷ蜍・
python -m backend.main

# 繝ｭ繧ｰ繧偵ヵ繧｡繧､繝ｫ縺ｫ蜃ｺ蜉帙＠縺ｪ縺後ｉ襍ｷ蜍包ｼ域耳螂ｨ・・
powershell -Command "python -m backend.main 2>&1 | Out-File -Encoding utf8 server_stdout.log"
```

> [!IMPORTANT]
> 蠢・★繝励Ο繧ｸ繧ｧ繧ｯ繝医Ν繝ｼ繝医〒螳溯｡後＠縺ｦ縺上□縺輔＞縲Ａbackend/main.py` 繧堤峩謗･螳溯｡後☆繧九→繧､繝ｳ繝昴・繝医お繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺吶・

### 3. 迴ｾ蝨ｨ縺ｮ迥ｶ諷・
- **譛譁ｰ襍ｷ蜍・*: 2026-04-22 02:26 (JST)
- **PID**: 19668
- **繝昴・繝・*: 8001
- **迥ｶ諷九Ο繧ｰ**: `knowledge/fact/app_status.md`
=== Part 3: プロジェクト管理 ===

### 7. 現在のフェーズと次なるアクション

**現在のステータス**: ?? デバッグ中（履歴表示機能のクラッシュ）

**発生中のブロック事項**:
- 履歴画面からキャラクターパッケージをロードしようとすると、frontend/js/app.js 内で存在しないDOM ID (diary-start-panel, diary-generation-area) にアクセスしようとして TypeError で停止する。

**次のアクション**:
1. frontend/js/app.js の修正（不適切なDOM参照の削除とUI表示制御の整合性確保） [ ]
2. agent-browser による修正後の遷移確認 [ ]
3. 日記生成機能における最新UI（指示入力、プログレス表示）の動作再確認 [ ]

---
最終更新: 2026-04-22 01:50

