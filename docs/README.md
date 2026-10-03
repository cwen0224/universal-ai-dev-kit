# 跨專案通用 AI 協同開發與工程架構準則 (Universal AI Development & Engineering Blueprint)

本文件提煉並匯整了本專案所有的**軟體工程實踐、AI 代理人協同架構、防禦性程式設計、Token 經濟學、多代理 (Multi-Agent) 治理與跨平台檔案規範**。  
此指引**已徹底抽離 Live2D、影音製作等領域特定邏輯**，可直接作為任何軟體專案、AI Agent 系統（如 Claude Code, Cursor, Antigravity, AutoGen, CrewAI）的專案規範（`AGENTS.md` / `RULES.md` / `CLAUDE.md`）。

---

## 總覽架構圖 (Architecture Overview)

```
┌────────────────────────────────────────────────────────────────────────┐
│               語意索引維護層 (Offline / Index Curator)                 │
│  - 語意地圖編寫、能力標籤 (Tags)、負向排除條件 (Negatives) 定義            │
│  - 產出 CAPABILITY_GRAPH.json 與 Q-INDEX 決策樹                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (確定性索引與能力圖資料)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  智能導航與定位層 (Online Navigation)                  │
│  - Q-Index 導航協定 (資訊增益二分選題、狀態感知、排除無關候選)             │
│  - 檔案快取索引 (FILE_INDEX.json) 杜絕即時全域 rglob 掃描               │
│  - CLIS 漸進式代碼定位 (符號粗篩 -> 骨架檢驗 -> 精準區塊切片)              │
│  - 呼叫鏈與依賴圖 (Call Graph / Data Flow) 秒級溯源                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (精準目標位置與最小上下文)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        AI 決策層 (Brain / Semantic)                     │
│  - 語意分析與意圖識別                                                    │
│  - 輸出宣告式規格 (Declarative JSON/YAML)                                │
│  - Actor-Critic 對抗審查 (雙子審核，上限 3 次止損)                       │
│  - 檢索品質記憶 (Retrieval Telemetry) 記錄錯誤路由回饋進化               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (宣告式合約：只有資料，沒有計算)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      傳統程式組裝層 (Muscle / Deterministic)             │
│  - 唯一真理來源 (Single Source of Truth: 物理時間/座標/AST)                │
│  - 確定性演算法 (迴圈/查表/浮點運算)                                      │
│  - 單一進入點執行 (Single Entry CLI，不直打破碎指令)                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      底層防禦與監督層 (Guardrails & Watchdog)            │
│  - 獨立進程監控 (防假冒成功、防僵死掛起、防殘留鎖定)                         │
│  - 防禦性異常處理 (API 指數退避、503 凍結、完整 Error Body 捕獲)            │
│  - 雙軌結構化日誌 (Console 人類可讀 + 檔案 JSON 機器可讀 + 輪轉清理)       │
│  - 暫存生命週期管理 (測試幀/臨時檔即時清理、輸出絕對目錄隔離)                 │
└────────────────────────────────────────────────────────────────────────┘
```


---

## 目錄 (Table of Contents)

1. [🐴 半人馬合作準則 (Centaur Collaboration Principle)](#1-半人馬合作準則-centaur-collaboration-principle)
2. [🤖 多代理對抗式治理架構 (Twin GAN / Actor-Critic Governance)](#2-多代理對抗式治理架構-twin-gan--actor-critic-governance)
3. [🛡️ 防禦性工程實踐與系統守則 (Defensive Engineering Principles)](#3-防禦性工程踐與系統守則-defensive-engineering-principles)
4. [⚡ 精實 Vibe Coding 與 Token 經濟學 (Lean Vibe Coding)](#4-精實-vibe-coding-與-token-經濟學-lean-vibe-coding)
5. [🧭 自適應認知導航與階層式能力檢索準則 (Generation-2 Cognitive Navigation)](#5-自適應認知導航與階層式能力檢索準則-generation-2-cognitive-navigation)
6. [🎨 耗時任務與視覺高效率迭代規範 (Fast Iteration & Single-Snapshot Protocol)](#6-耗時任務與視覺高效率迭代規範-fast-iteration--single-snapshot-protocol)
7. [🌐 跨平台環境相容與字元編碼鐵律 (Cross-Platform & Encoding Rules)](#7-跨平台環境相容與字元編碼鐵律-cross-platform--encoding-rules)
8. [🔒 系統狀態持久化、安全審批與 CI/CD 規範 (Persistence, Security & CI/CD)](#8-系統狀態持久化安全審批與-cicd-規範-persistence-security--cicd)
9. [🧠 使用者偏好日誌與記憶治理規範 (User Preference & Memory System)](#9-使用者偏好日誌與記憶治理規範-user-preference--memory-system)
10. [📋 跨專案落地檢查清單 (Universal Adoption Checklist)](#10-跨專案落地檢查清單-universal-adoption-checklist)


---

## 1. 半人馬合作準則 (Centaur Collaboration Principle)

> **核心精神：決策與計算分離 (Decouple Semantics from Math)**  
> **「讓 AI 負責語意決策，讓程式負責算數學與組合。」**

大型語言模型擁有極佳的創造力與文本理解力，但在浮點數運算、邊界防護與時間軸連續性上存在天然的不穩定性。切忌用 Prompt 懇求 AI 不要算錯數字，而應在架構上**徹底剝奪 AI 算數學的責任**。

### 1.1 標籤化輸出 (Tagging over Generating)
- AI 不應從零憑空建構帶有嚴格物理/時序約束的最終結構檔。
- **標準實踐**：AI 僅負責輸出「標籤 (Tags)」或「詮釋資料 (Metadata)」。例如在既有資料陣列中為某些項目附加狀態或意圖標籤。

### 1.2 唯一真理來源 (Single Source of Truth)
- 所有的物理時間、長度、座標（X/Y）、雜湊值，必須來自精準的測量工具或系統底層（如語音時間軸、AST 解析器、資料庫實體）。
- **標準實踐**：AI 做決策時只參照物件 ID 或陣列索引（Index），嚴禁憑空捏造絕對數值。

### 1.3 確定性組裝 (Deterministic Assembly)
- 最終交付物必須由腳本進行「確定性 (Deterministic)」組合。
- **標準實踐**：腳本讀取 AI 產出的標籤，查表取得真理數據，利用傳統條件分支與迴圈，精確算至小數點後三位並組裝成 100% 合規格式。

### 1.4 宣告式架構與編碼權限限制 (Declarative Guardrail)
- 在日常任務、內容生成或一般除錯中，AI 的唯一職責是**宣告資料結構 (JSON/YAML)** 與觸發標準管線。
- **最高編碼權限限制**：只有使用者明確下達「擴充底層 Worker、修改核心架構」時，AI 才被允許撰寫或修改邏輯程式碼。嚴禁在日常任務中擅自手刻臨時免洗腳本繞道執行。

#### 💡 宣告式合約範例 (Declarative vs. Procedural Contract)
- ❌ **Bad (AI 越權計算物理數值與排版樣式)**:
  ```json
  {
    "action": "render_card",
    "box_x": 128.45,
    "box_y": 320.12,
    "duration_frames": 45,
    "css_style": "position: absolute; top: 120px; color: red;"
  }
  ```
- ✅ **Good (AI 僅標籤化語意與意圖，座標與渲染由確定性程式組裝)**:
  ```yaml
  target_id: "user_profile_card"
  intent: "highlight_warning"
  semantic_tags:
    - "badge:overdue"
    - "urgency:high"
  # 具體 X/Y 像素、持續影格數、字型佈局全由底層 Worker 查表與動態計算
  ```

### 1.5 嚴禁前端樣式幻覺 (Forbidden Frontend Mockups)
- UI / 前端介面為「純粹的觀測與呈現容器」，嚴禁 AI 在前端用 CSS 或假 DOM 去「山寨」後端尚未完成的功能。
- 若缺少視覺效果或功能，必須遵循宣告式 Specification 驅動後端核心實作，絕不在前端手刻視覺遮掩。


---

## 2. 多代理對抗式治理架構 (Twin GAN / Actor-Critic Governance)

> **核心精神：不相信單向輸出，將審查邏輯獨立為對抗式節點。**

在複雜的 AI 代理人工作流中，單一 Agent 既當球員又當裁判必然會產生「自我幻覺」與「偷懶退化」。

### 2.1 雙子對抗路由 (Actor-Critic Pairing Protocol)
- **禁止單向直通**：生成型代理（Actor / Generator）產出的規劃或規格，嚴禁直接交付給執行引擎。
- **強制審查放行**：必須指派對應的審查代理（Critic / Discriminator）進行獨立稽核：
  - **通過 (Pass)**：驗證規則全部通過，進入下一步。
  - **退回重構 (Reject)**：Critic 具體指出不合格原因，Actor 吸收回饋重寫，直到通過為止。
- **上限 3 次止損原則 (3-Strike Escalation)**：Actor 與 Critic 針對同一任務之退回重構不得超過 3 輪。若第 3 輪仍無法達成一致，必須主動中止循環、拋出例外並呈報人類介入決策，嚴禁無窮對抗消耗 Token 預算。


### 2.2 審查分層架構
1. **靜態邏輯審查 (Semantic & Logic Phase)**：
   - 審查 Actor 產出的 JSON/YAML 企劃。
   - 檢驗指標：字數限制、多樣性門檻、參數極端值防呆、邏輯矛盾。
2. **實體產物審查 (Artifact & Pixel Phase)**：
   - 審查編譯或渲染產出的實際檔案。
   - 檢驗指標：格式編碼合規、檔案大小非零、斷點無黑畫面/空白、無崩潰堆疊。

### 2.3 獨立系統監督官 (Watchdog Supervisor)
- **獨立監控權**：獨立於主流程之外，監控進程狀態，不受業務 Agent 指揮。
- **防造假驗證**：若流程回報「任務完成」，監督節點必須實體調用系統工具（如 `ls`、檔案大小、Header 資訊）驗證產物，防範假報成功。
- **僵死偵測 (Deadlock Detection)**：監控進程超時（如無響應超過門檻），強制中止卡死進程並觸發報警。

---

## 3. 防禦性工程實踐與系統守則 (Defensive Engineering Principles)

> **核心精神：把不可控的外部環境視為隨時會崩潰，構建高容錯的軟體壁壘。**

### 3.1 外部 API 異常與 503 服務保護 (503 Guardrail)
當調用第三方 AI 服務（Gemini、OpenAI、Claude）時遭遇 `503 Service Unavailable`、`High Demand` 或伺服器過載錯誤：
1. **嚴禁擅改代碼**：絕對禁止私自替換模型名稱、修改驗證邏輯或手寫 bypass 繞道。
2. **立即中止程序 (Immediate Halt)**：立刻停止後續重試，避免造成無效計費或請求風暴。
3. **主動請示決策**：回報服務高負載，請使用者決定等待、換金鑰或切換備用方案。

### 3.2 指數退避重試 (Exponential Backoff for Rate Limits)
- 批次處理 API 請求時，**預設必須實作指數退避重試邏輯**（攔截 HTTP 429）。
- 不可等遇到 Rate Limit 才事後補修。

### 3.3 深度異常捕獲 (Deep Exception Logging)
- 捕捉 HTTP 異常時，**嚴禁在 generic `except Exception:` 中吞掉錯誤或只印出狀態碼**。
- **必須完整提取並輸出伺服器回傳的原始 Body**（如 `response.text`），因後端的 JSON 錯誤細節（如參數架構錯誤、配額不足）才是排查關鍵。

### 3.4 殭屍進程主動清理與檔案鎖 (Zombie Process Cleansing)
- 重啟本機後台服務（如 Local Server、Dev Server、資料庫容器）前，**嚴禁假設前一個進程會優雅關閉**。
- 必須在綁定通訊埠或覆寫二進位檔之前，主動偵測並強制終止殘留進程，防止連接埠衝突與檔案鎖死。

### 3.5 暫存檔案即刻清理 (Transient Media Cleanup)
- 測試、預覽或抽幀過程中產生的臨時檔案（如 `test_*.png`、`tmp_chunk.dat`），在驗證完畢後必須立刻清理。
- 嚴禁讓免洗垃圾污染程式庫或交付目錄。

### 3.6 產物絕對路徑隔離 (Artifact Isolation)
- 程式產生的輸出檔、報表、快照，必須強制寫入專屬輸出目錄（如 `_outputs/` 或 `dist/`）。
- 底層路徑處理強制使用路徑拼接（如 `path.join(OUTPUT_DIR, path.basename(filename))`），杜絕路徑穿越（Path Traversal）或污染根目錄。

### 3.7 雙軌結構化日誌與排查規範 (Structured Logging & Diagnostics)
- **雙軌日誌機制 (Human vs. Agent Dual-Track)**：
  - **Console 介面**：輸出簡潔、可讀性高的關鍵節點與進度（可含狀態標籤/Emoji），供人類開發者即時觀測，杜絕 raw dump 刷屏。
  - **檔案日誌 (`.cache/logs/`)**：強制輸出結構化 JSON 格式（JSON Lines），包含 `timestamp`, `level`, `module`, `event`, `context` 與完整 `traceback`，專供 Agent 發生 Failure 時進行精準的程式化解析與「證據驅動除錯」。
- **日誌分級鐵律 (Strict Log Levels)**：
  - `DEBUG`：微觀變數、運算細節與內部狀態。**嚴禁濫用 `print()` 直噴 Console**，預設僅寫入專屬日誌檔。
  - `INFO`：重大階段里程碑（如：`[INFO] 宣告合約解析通過，進入渲染階段`）。
  - `WARN`：非致命異常、降級事件或觸發指數退避重試（如 HTTP 429）。
  - `ERROR`：任務中斷或核心失敗，**必須附帶完整 Exception Stack Trace 與伺服器原始錯誤 Body (Raw Error Response)**。
- **日誌生命週期與滾動 (Rotation & Cleanup)**：
  - 日誌檔統一存放在 `.cache/logs/` 或 `_outputs/logs/` 隔離目錄，嚴禁散落於專案根目錄。
  - 實作單檔大小限制（如 10MB）與自動滾動機制（Rotating File Handler），避免磁碟空間耗盡與檢索困難。

---


## 4. 精實 Vibe Coding 與 Token 經濟學 (Lean Vibe Coding)

> **核心精神：以完成任務的總成本為目標，杜絕無效讀取、重複輸出與猜測式返工。**

### 4.1 任務收斂與界線
- 快速收斂「目標、完成條件、限制」。資訊充足立即動手，只問無法從代碼庫驗證且實質影響實作的問題。
- 小型修改直接執行；跨模組修改拆解為 3–5 個可獨立驗證的階段。

### 4.2 漸進取得上下文 (Progressive Context Acquisition)
- **避免全文傾倒**：預設先檢視 3–5 個核心檔案、每檔約 80–160 行，沿呼叫鏈與介面逐步擴展。
- **搜尋過濾**：自動避開 `node_modules`、編譯產物、lockfile、大型二進位檔。
- **重用既有脈絡**：沿用同一對話已確認且未變動的資訊，僅重讀有改動或上下文不明的區段。
- **版本查證**：遇 API 或依賴問題，先核對專案實際宣告版本，再查詢官方文件。

### 4.3 最小完整修改 (Minimal Patching)
- 重用既有元件與抽象，僅修改達成完成條件所必需的檔案。
- **不順手重構**：嚴禁順便改名、順便格式化全專案、無端升級依賴或引入新套件。
- **精準 Patch**：在工具呼叫中只傳遞要置換的區塊，不在對話輸出中整檔重貼。
- 修改後主動檢查 `git diff` 是否混入不相關變更。

### 4.4 證據驅動除錯 (Evidence-Driven Debugging)
- **先重現後假設**：取得明確的錯誤訊息、日誌或重現步驟後，才提出修復假說。
- **兩次失敗止損原則**：同一問題連續兩次修改未果，**立刻停止猜測式修改**。記錄「已試方法 / 結果 / 已排除原因」，收集一項新證據後再行動。
- **結構化止損報告格式**：當觸發止損時，AI 應輸出以下結構化報告供人類接手或作為下一步分析依據：
  ```markdown
  > 🛑 **兩次嘗試止損報告 (2-Strike Debugging Halt)**
  > - **[現象與重現]**：錯誤代碼、觸發函式與最小重現條件。
  > - **[嘗試 1]**：修改假設、改動點、執行結果與失敗觀察。
  > - **[嘗試 2]**：替代假說、改動點、執行結果與失敗觀察。
  > - **[已排除原因]**：確定無關的變數、模組或環境因素。
  > - **[缺乏之關鍵證據]**：需要人類確認或需額外日誌探針（Probe Log）之盲區。
  ```
- **乾淨回退**：若修改無效，僅精確撤回自己的無效變更，嚴禁隨意使用 `git reset --hard` 覆蓋使用者的工作進度。

### 4.5 依風險分級驗證
- 先跑最小單元測試／局部語法檢查，再依影響範圍擴大到整合測試。
- 文案/樣式修改：驗證畫面與文字差異。
- 邏輯/狀態機修改：驗證邊界值與反向案例。
- 完成所有條件與必要檢查後即停止延伸。

### 4.6 模型能力與情境視窗降級策略 (Context & Model Degradation)
- **Context 壓縮機制**：當單次工作流或對話長度趨近上限時，強制觸發「上下文摘要壓縮」：清空中間工具的冗長輸出（如大型 raw log、大量目錄樹掃描），僅保留「最終決策 JSON、目前狀態快照與最新錯誤堆疊」。
- **模型分級降級 (Model Fallback)**：
  - 輕量篩選/讀檔/語法分析：優先指派輕量快速模型（如 Flash / Haiku）。
  - 架構決策/深層除錯：方升級至旗艦推理模型。
  - 若遇模型額度超額或服務降級，優先切換備用模型，並主動通報使用者。


---

## 5. 自適應認知導航與階層式能力檢索準則 (Generation-2 Cognitive Navigation)

> **核心精神：以「資訊論熵減剪枝 + 契約化能力圖譜 + 程式碼屬性圖切片」建立封閉迴路；全面抑制純機率性幻覺，以符號約束達成高確定性、最小 Token 的導航收斂。**

大型語言模型在複雜 Monorepo 中極易面臨「全域上下文過載、注意力渙散與工具錯選」。本準則將傳統單向搜尋升級為「第二代（Gen-2）自適應認知導航閉環體系」，分為六個解耦層級：

### 5.1 六階自適應導航架構 (Gen-2 Six-Layer Navigation Pipeline)

```
[模糊任務輸入] ──> (1. 歧義評估與共形閘門) ──[快速路徑]──> (4. CLIS 符號與程式切片)
                          │
                      [慢速路徑]
                          ▼
            (2. 貝氏資訊追逐與診斷探針)  ──> 靜態斷言 / 動態測試 / 離散選擇
                          │
                          ▼
            (3. 契約約束能力圖譜與慣性快取) ──> 正負約束過濾 / 馬可夫路徑跳轉
                          │
                          ▼
            (4. 神經符號代碼鏡頭 AST-CPG) ──> 雙向切片 (前向衝擊/反向依賴)
                          │
                          ▼
            (5. 宣告式合約與沙盒執行端)   ──> 確定性編譯器 / 測試驗證
                          │
                          ▼
            (6. 非同步遙測與圖記憶校準)   ──> 記錄熵減路徑，離線演化更新
```

1. **第一層：歧義評估與共形預測閘門 (Ambiguity & Conformal Gating)**
   - **快慢雙軌路由**：計算任務特徵並估算候選能力集合 $C_\alpha$。
   - **快速穿透 (Fast-Track)**：若 $\vert C_\alpha \vert \le 2$ 且置信度高，直接跳過問答，穿透至第 4 層符號切片。
   - **深度消歧 (Slow-Track)**：若夏農熵 $H(C_\alpha)$ 過高或歧義嚴重，才啟動第 2 層診斷探針。
   - **主動棄權機制 (Abstention)**：若 $C_\alpha = \emptyset$（無任何模組吻合），系統必須主動宣告無效任務並中斷，嚴禁盲目通靈猜測。

2. **第二層：貝氏資訊追逐與預編譯診斷探針 (Bayesian Diagnostic Probes)**
   - **杜絕純動態自然語言提問**：每一輪在線上用 LLM 即時生成問卷會產生不可接受的延遲、Token 開銷與語意漂移風險。
   - **三級預編譯診斷探針**：
     1. **`STATIC_ASSERTION` (靜態斷言探針，成本近 0)**：檢查設定檔標記、環境變數、產物檔案副檔名或特定目錄存在性。
     2. **`DYNAMIC_TEST` (動態測試探針，成本低/資訊量極高)**：執行最小單元測試或語法檢查，利用測試覆蓋率矩陣與頻譜故障定位（SBFL / Stack Trace），在數毫秒內排除 99% 的無關代碼。
     3. **`DISCRETE_CLARIFICATION` (離散選擇探針，保底手段)**：僅當靜態與動態探針皆無法區分時，才向開發者丟出具備最大資訊增益（$\arg\max I(\text{Candidate}; \text{Probe})$）的 2 選 1 或 3 選 1 離散選擇題。

3. **第三層：契約約束能力圖譜與慣性快取 (Capability Graph & Inertia Cache)**
   - **正負約束過濾 (Positive/Negative Constraints)**：超越關鍵字匹配。每個能力節點嚴格維護「前置條件（Preconditions）」、「能做什麼（Positive Invariants）」與「絕對不能做什麼（Negative Constraints）」。命中負向條件者一票否決。
   - **工具使用慣性快取 (Markov Tool Inertia)**：借鑑 AutoTool 原則，高達 60% 的工程任務具有高度固定的依賴路徑（例如：修改 Caption 模組後通常接續 Editor）。記錄轉移機率矩陣，高置信度時直接進行微秒級確定性圖跳轉，繞過 LLM 推論。

4. **第四層：神經符號代碼鏡頭與雙向切片 (AST & Bi-directional Program Slicing)**
   - **四階漸進式代碼定位 (CLIS)**：
     - `search`：符號粗篩，僅返回簽名與行號（15~30 tokens/項）。
     - `struct`：骨架檢驗，剔除實作提取類別與方法簽名（200~400 tokens）。
     - `read -s`：精準切片，僅讀取目標函式區塊（50~100 行）。
   - **雙向程式切片 (Program Slicing)**：
     - **反向切片 (Backward Slicing)**：追溯函式輸入參數的全域依賴來源與呼叫鏈。
     - **前向切片 (Forward Slicing)**：評估修改目標函式後對下游回傳值的連鎖影響。
     - 組合為具備完整因果因子的「最小語意閉包 (Minimal Context)」，杜絕無關代碼干擾。

5. **第五層：宣告式合成與確定性沙盒執行 (Declarative Sandbox Execution)**
   - AI 的唯一職責是輸出宣告式合約（JSON/YAML），嚴禁直接以破碎 Shell 指令操作系統。
   - 由隔離沙盒內的確定性工具（編譯器、Linter、測試執行器）執行。執行失敗時將堆疊資訊（Stack Trace）回灌為診斷訊號，啟動局部重修。

6. **第六層：非同步遙測與平攤圖記憶校準 (Asynchronous Telemetry & Consolidation)**
   - 每次導航均非同步寫入結構化遙測事件（`NavigationTelemetryEvent`），記錄初始候選集大小、每步熵減路徑、目標符號與最終成功/失敗狀態。
   - 由離線 Index Curator 定期挖掘歷史失敗軌跡，動態修補能力契約的正負約束、校準慣性圖權重，讓系統自我演化。

### 5.2 檔案快取索引與增量維護 (File Index & Incremental Update)
- **快取索引免遍歷**：`find_code.py` 嚴禁呼叫即時 `rglob("*")`，必須優先查閱 `.cache/file_index.json`（維護檔案路徑、大小、修改時間與 hash）。
- **Merkle Tree 增量維護**：透過 SHA-256 樹秒級比對變動檔案，僅對變更檔案進行 AST 重新解析與圖節點重整，達到 $O(\text{changed files})$ 的高效能。

### 5.3 搜尋與導航排除規範
- 全域搜尋與索引時強制排除：依賴目錄（`node_modules/`, `site-packages/`, `.venv/`）、快取與建置輸出（`dist/`, `build/`, `.cache/`）、暫存檔案與大型媒體資料。



---

## 6. 耗時任務與視覺高效率迭代規範 (Fast Iteration & Single-Snapshot Protocol)

> **核心精神：嚴禁在微調階段執行端到端完整產出，強制採用最小單元快照除錯。**

本原則適用於所有包含「視覺繪圖、影片合成、前端動畫、大型報表生成、批次轉換」等耗時任務。

### 6.1 禁止調校階段執行完整管線
- 每次微調樣式、過渡曲線或排版時，跑一次全流程（數十秒至數分鐘）會嚴重拖垮開發節奏。

### 6.2 單幀 / 單頁快照機制 (Snapshot Debugging)
- 工具鏈必須支援「單幀直出」或「局部快照」旗標（例如 `--preview-sec 1.5`、`--page 1`）。
- **標準工作流**：
  1. 修改排版、色彩或數學公式。
  2. 生成單一時間點或單頁快照（< 1 秒）。
  3. 檢視快照成果驗證視覺效果。
  4. 僅在最後所有視覺細節確認無誤後，才執行一次全量產出。

### 6.3 宣告式排版與安全區域規範
- 避免硬編碼絕對像素座標。
- 定義全局安全邊界（頂部防遮擋、底部防重疊）與統一間距變數。
- 排版由演算法或動態佈局引擎依宣告內容自動計算。

---

## 7. 跨平台環境相容與字元編碼鐵律 (Cross-Platform & Encoding Rules)

> **核心精神：消除環境差異引發的暗坑，確保在 Windows / macOS / Linux 表現一致。**

### 7.1 字元編碼鐵律 (UTF-8 Protocol)
- **禁止原始碼硬編碼非英文字串**：多國語系字串應抽離為獨立的 JSON/YAML 資源檔。
- **檔案讀寫顯式指定編碼**：所有腳本（Python/Node.js）讀寫文字檔時，**必須顯式宣告 `encoding="utf-8"`**，避免 Windows 預設使用 CP950/GBK 導致解碼崩潰。

### 7.2 禁止靜默執行 Windows 安裝程式
- 在 Windows 環境安裝軟體（`.exe` / `.msi`）時，**嚴禁使用 `/SILENT` 或阻擋式靜默安裝**。這會因觸發 UAC（使用者帳戶控制）視窗而導致進程無限期卡死。
- 正確做法：下載檔案後，主動提示使用者並呼叫檔案總管開啟目錄，由人類操作授權。

### 7.3 版本控制與 Git 操作邊界 (Git Hygiene & Version Control Boundary)
- **語意化提交 (Conventional Commits)**：
  - 嚴格遵循 `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:` 等規範前綴。
  - Commit Message 必須包含「變動動機 (Why)」與「影響範圍 (What)」，**嚴禁使用 `update`, `fix bug`, `changes` 等無意義模糊說明**。
- **原子化提交與環境衛生 (Atomic Commits & Working Tree Hygiene)**：
  - **單一職責變更**：每次 Commit 僅能包含單一邏輯任務，嚴禁將「程式重構 + 業務新功能 + 全專案代碼排版 + 測試修正」一次打包提交。
  - **防範髒污 Working Tree**：執行任何修改前，必須先檢查 `git status` 確保工作區狀態乾淨。測試結束後，所有免洗腳本、測試快照與暫存資料必須徹底清理，嚴禁將未追蹤檔案（Untracked Files）意外打包進暫存區（Staging Area）。
- **破壞性 Git 操作禁令 (Non-Destructive Git Rules)**：
  - **嚴禁自動執行破壞性抹除**：AI 絕對禁止私自執行 `git reset --hard`、`git clean -fd` 或強行覆寫未 Commit 的工作進度，除非人類明確下達指示並授權。
  - **精準復原原則**：若修復驗證無效，僅能使用 `git checkout -- <file>` 或 `git restore <file>` 精準回退本次改動的檔案；已提交之變更則採用 `git revert`。
- **分支隔離策略 (Branching & Staging Policy)**：
  - 跨模組或高風險的架構重構，AI 應主動提醒人類或於專屬實驗分支（如 `feat/ai-experiment`）上作業，避免直接破壞 `main` / `master` 主幹穩定性。
- **秘鑰與敏感檔案絕對隔離**：敏感檔案（`.env`, `API_KEY*`, 憑證檔、帳密資料）必須在 `.gitignore` 中嚴格排除，每次 `git add` 前執行二次安全過濾。

---

## 8. 系統狀態持久化、安全審批與 CI/CD 規範 (Persistence, Security & CI/CD)

> **核心精神：保障任務容災與斷點續傳，建立嚴格的人機安全邊界與自動化地圖同步。**

### 8.1 狀態持久化與斷點續傳 (State Persistence & Resume Protocol)
- **checkpoint 狀態快照**：長流程、跨模組或批次任務，必須在每步驟完成後將狀態寫入輕量持久化檔（如 `.cache/execution_state.json` 或 `checkpoint.yaml`）。
- **冪等性設計 (Idempotency)**：重新執行任務時，腳本與 Agent 必須優先檢查快照狀態，自動跳過已成功產出的階段，避免重複調用 API 或重算。

### 8.2 安全性與隱私防護鐵律 (Security & Privacy Guardrails)
- **提示詞注入防禦 (Prompt Injection Defense)**：外部傳入文字、爬蟲擷取內容、用戶上傳文件或第三方 API 回傳資料，必須視為「不可信輸入（Untrusted Input）」，統一作為純資料區塊傳入語意層，嚴禁直接拼接進系統 Prompt。
- **敏感資訊與日誌遮蔽 (Secret Masking)**：終端機輸出、除錯 Log 及快照檔案，必須自動對 API Key、Token、私鑰與個人識別資訊（PII）實施脫敏遮蔽（如 `sk-proj-****`）。

### 8.3 Agent 權限與破壞性指令審批 (Human-in-the-Loop Approval)
- **高風險指令攔截**：涉及以下破壞性或不可逆操作時，Agent 嚴禁擅自執行，必須主動暫停並列出受影響路徑，等待人類明確授權：
  1. 遞迴刪除檔案或目錄（`rm -rf`、`Remove-Item -Recurse`）。
  2. 資料庫結構變更、Drop Table 或清除集合資料。
  3. 強制覆寫未保存之版本控制進度（`git reset --hard`、`git clean -fd`）。
  4. 修改作業系統底層設定或安裝未經許可之全域套件。

### 8.4 自動化測試與 CI/CD 整合指引 (Automated Tooling & Git Hooks)
- **架構地圖自動同步**：在 `pre-commit` 鉤子或 CI/CD Pipeline 中，強制集成專案結構索引腳本（例如 Merkle Tree 與架構索引工具），確保每次變更提交時 `CODEBASE_MAP.md` 永不失真。
- **宣告式合約靜態檢查**：在 CI 中加入 JSON Schema / Pydantic 驗證，防止不合規的宣告式企劃直接進入發布或執行流程。

---

## 9. 使用者偏好日誌與記憶治理規範 (User Preference & Memory System)

> **核心精神：將用戶習慣與專案慣例結構化持久化，減少重複 Prompt 說明並確保跨任務行為一致性。**

### 9.1 偏好作用域與儲存結構 (Scoped Preference Storage)
- **全域偏好 (Global Scope)**：
  - **位置**：`~/.config/ai_toolkit/user_preferences.json`
  - **範疇**：跨專案之個人習慣（如：預設語系 `zh-TW`、開發者暱稱、預設 Git 提交風格、慣用編輯器）。
- **專案偏好 (Project Scope)**：
  - **位置**：專案根目錄 `./.agents/user_preferences.json`
  - **範疇**：特定專案之領域知識（如：專屬術語表、禁用的函式庫、專案架構規範、特定 CLI 預設參數）。

### 9.2 覆蓋優先順序 (Override Hierarchy)
CLI 工具與 Agent 於解析參數時，必須嚴格遵守下列確定性優先順序：
> **`CLI 顯式傳參 (Flags)` > `專案偏好 (Project)` > `全域偏好 (Global)` > `系統內建預設值 (Defaults)`**

### 9.3 偏好資料結構標準 (JSON Schema)
偏好日誌必須維持極簡結構化 JSON，嚴禁寫入非結構化之漫長對話歷史：
```json
{
  "version": "1.0",
  "general": {
    "language": "zh-TW",
    "output_style": "concise"
  },
  "coding_standards": {
    "indent_spaces": 2,
    "forbidden_packages": ["lodash", "moment"],
    "test_framework": "pytest"
  },
  "git_preferences": {
    "commit_prefix_emoji": false,
    "auto_stage_untracked": false
  },
  "domain_glossary": {
    "A-Roll": "主講人虛擬主播片段",
    "B-Roll": "補充空鏡與畫面素材"
  }
}
```

### 9.4 偏好擷取與記憶更新機制 (Memory Read/Write Protocol)
- **動態切片注入 (Scoped Context Injection)**：
  - CLI 工具於提供選單或工具說明時，僅注入與該任務相符之偏好節點（如跑程式碼搜尋只提取 `coding_standards`），嚴禁全量載入全檔以節省 Token。
- **主動持久化觸發 (Implicit Memory Learning)**：
  - 當使用者下達帶有長期約束力的修正指令（如：「以後這個專案的縮排一律用 2 個空格」）時，Agent **必須主動調用偏好管理 CLI**（`tools/indexer/user_pref.py set coding_standards.indent_spaces 2`）將其寫入 `./.agents/user_preferences.json`，並向使用者確認已記錄記憶。
- **敏感隱私邊界**：偏好日誌嚴禁記錄密碼、API Key、Token 或敏感個人隱私資訊；專案偏好檔若含個人路徑，應避免版控污染。

---

## 10. 跨專案落地檢查清單 (Universal Adoption Checklist)

在新專案導入 AI 代理人或編寫 Agent Rules 時，請依下列檢查項配置：

- [ ] **分工邊界**：AI 是否僅負責語意決策與宣告（JSON/YAML），而所有數學與組裝由確定性腳本負責？
- [ ] **審查對抗**：關鍵產出是否建立 Actor-Critic 配對？是否有獨立 Watchdog 稽核產物真實性？是否有設定上限 3 次重構止損？
- [ ] **API 防護**：是否包含指數退避重試？503 錯誤時是否有明令禁止 AI 擅改程式碼？
- [ ] **除錯紀律**：是否落實「連續兩次修改失敗即暫停猜測」、輸出結構化止損報告與依賴新證據驅動？
- [ ] **雙軌日誌**：Console 是否精簡可讀？檔案 Log 是否輸出結構化 JSON，並實作滾動清理與錯誤 Raw Body 完整記錄？
- [ ] **快照預覽**：耗時任務是否有提供最小單元快照旗標？
- [ ] **編碼安全**：跨平台讀寫是否有顯式指定 UTF-8 編碼？
- [ ] **進程清理**：重新啟動服務時，是否有主動清除殘留殭屍進程？
- [ ] **Git 衛生與操作邊界**：是否杜絕 `git reset --hard`？Commit 是否維持原子化、乾淨的工作區與 Conventional 規範？
- [ ] **狀態持久化**：多步驟長任務是否實作快照持久化與冪等跳過機制？
- [ ] **安全審批**：破壞性指令（如遞迴刪除、硬重置）是否配置 Human-in-the-Loop 審批門檻？
- [ ] **提示詞與日誌安全**：非信任外部輸入是否隔離為資料？日誌是否遮蔽金鑰與隱私資料？
- [ ] **Gen-2 自適應導航**：是否支援共形置信閘門（快慢雙軌）、預編譯三級診斷探針（靜態/動態/離散），杜絕線上純動態提問？
- [ ] **能力契約與慣性快取**：是否維護正負約束（Positive/Negative Constraints）與馬可夫高頻轉移路徑？
- [ ] **雙向程式切片**：CLIS 是否支援前向衝擊與反向依賴切片，僅提取最小因果閉包？
- [ ] **快取索引與增量維護**：`find_code` 是否使用 `FILE_INDEX.json` 避免重覆全域掃描？是否由 Merkle Tree 進行 O(changed files) 增量更新？
- [ ] **偏好日誌與記憶**：是否配置全域/專案雙層偏好，並於強修正時主動提煉持久化至 `.agents/`？
- [ ] **CI/CD 地圖同步**：是否透過 Git Hook 或 CI 自動維護專案索引地圖？




