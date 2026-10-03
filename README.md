# 跨專案通用 AI 研發與索引工具套件 (Universal AI Development & Tooling Kit)

本資料夾彙整了可直接複製到**任何新專案**中使用的通用指南文件與索引定位工具鏈，協助 AI 代理人（Claude Code, Cursor, Antigravity, AutoGen 等）達成**超低 Token 消耗、精準定位、防禦性開發與對抗式治理**。

---

## 📦 套件內容結構

```
export_package/
├── UNIVERSAL_AI_DEVELOPMENT_GUIDELINES.md   # 核心開發與工程準則 (可更名為 AGENTS.md / RULES.md)
├── docs/
│   ├── README.md                            # 同上規範文件副本，方便放在文檔庫
│   └── schemas/gen2_navigation_schemas.json # 第二代自適應認知導航標準契約 Schema
└── tools/                                   # 核心索引與漸進式代碼定位工具鏈 (純標準庫，無外部依賴)
    ├── clis/
    │   ├── clis_engine.py                   # AST 語法樹符號提取、骨架檢視與精準切片讀取器
    │   ├── call_graph.py                    # AST 雙向呼叫鏈與因果切片追蹤器 (Callers / Callees)
    │   └── merkle_tree.py                   # Merkle Tree SHA-256 秒級增量變更感知器
    └── indexer/
        ├── q_index.py                       # Gen-2 自適應認知導航引擎 (共形預測閘門 + 診斷探針)
        ├── capability_compiler.py           # 離線能力契約編譯器 (自動萃取 AST 錨點與合約圖譜)
        ├── find_code.py                     # 高效代碼快速搜尋 CLI (支援 FILE_INDEX 快取免遍歷)
        ├── find_skill.py                    # 技能/指南多層漸進式檢索 CLI (Catalog/Describe)
        ├── index_engine.py                  # 全系統索引與 CODEBASE_MAP 自動生成引擎
        └── user_pref.py                     # 使用者偏好日誌與記憶管理 CLI (全域與專案雙層作用域)
```

---

## 🛠️ 工具鏈使用指引 (How to Use Tools)

所有工具均基於 Python 標準庫（AST, Hashlib, Pathlib, Argparse），在任何新專案中**不需要安裝額外的 pip 套件**即可直接運行。

### 1. `tools/clis/clis_engine.py` (漸進式代碼定位器)
避免 AI 整檔傾倒或讀入千行實作，大幅節省 80%~95% Token：
- **符號粗篩**（僅返回函式/類別簽名與行號，15~30 tokens/項）：
  ```bash
  python tools/clis/clis_engine.py search <函式或類別名>
  ```
- **骨架檢驗**（提取檔案 Outline 與簽名，剔除實作內容，約 200~400 tokens）：
  ```bash
  python tools/clis/clis_engine.py struct <檔案路徑>
  ```
- **精準切片擷取**（僅讀取目標符號實作區塊）：
  ```bash
  python tools/clis/clis_engine.py read <檔案路徑> -s <函式名>
  ```

### 2. `tools/clis/merkle_tree.py` (秒級變更感知)
- 快速建立目錄樹的 SHA-256 雜湊，秒級比對出被修改的檔案清單：
  ```bash
  python tools/clis/merkle_tree.py --diff
  ```

### 3. `tools/indexer/find_code.py` (檔案快速定位)
- 支援檔名、特定模組或副檔名快速過濾：
  ```bash
  python tools/indexer/find_code.py <關鍵字> -e py
  ```

### 4. `tools/indexer/find_skill.py` (技能與指南漸進披露)
- **目錄層極簡摘要**（Catalog，15~30 tokens/項）：
  ```bash
  python tools/indexer/find_skill.py --catalog
  ```
- **描述層含負向防誤觸條件**（Describe，50~120 tokens/項）：
  ```bash
  python tools/indexer/find_skill.py <關鍵字> --describe
  ```

### 5. `tools/indexer/user_pref.py` (使用者偏好日誌與記憶管理)
管理全域（`~/.config/ai_toolkit/`）與專案（`./.agents/`）雙層偏好，實現確定性優先級覆蓋：
- **查詢有效偏好或特定節點**：
  ```bash
  python tools/indexer/user_pref.py get
  python tools/indexer/user_pref.py get coding_standards.indent_spaces
  ```
- **寫入專案偏好記憶**（預設 scope 為 project）：
  ```bash
  python tools/indexer/user_pref.py set coding_standards.indent_spaces 2
  python tools/indexer/user_pref.py set domain_glossary.A-Roll "主講人虛擬主播片段"
  ```
- **寫入全域偏好**：
  ```bash
  python tools/indexer/user_pref.py set --scope global general.language "zh-TW"
  ```

### 6. `tools/clis/call_graph.py` (AST 雙向呼叫鏈與因果切片)
為 CLIS 系統提供雙向追蹤，秒級鎖定呼叫來源（Callers）與下游依賴（Callees），避免重啟全域搜尋：
- **反向切片（誰呼叫了這個函式？）**：
  ```bash
  python tools/clis/call_graph.py callers <函式名>
  ```
- **前向切片（這個函式呼叫了誰？）**：
  ```bash
  python tools/clis/call_graph.py callees <檔案路徑> <函式名>
  ```
- **重建呼叫圖索引快取**：
  ```bash
  python tools/clis/call_graph.py reindex
  ```

### 7. `tools/indexer/capability_compiler.py` (離線能力契約編譯器)
自動掃描專案程式庫、docstrings 與符號，編譯出符合 Gen-2 契約規範的能力圖譜（`capability_graph.json`）：
- **全自動編譯能力圖**：
  ```bash
  python tools/indexer/capability_compiler.py compile
  ```
- **合規性靜態檢查**：
  ```bash
  python tools/indexer/capability_compiler.py check
  ```

### 8. `tools/indexer/q_index.py` (Gen-2 自適應認知導航與診斷探針引擎)
整合資訊論熵減、共形預測置信區間與預編譯探針庫，全面杜絕線上純動態問答的推論延遲與語意漂移：
- **快慢雙軌導航 (Conformal Gating)**：
  - 候選數 $\le 2$ 時觸發 `FAST_TRACK` 直接穿透至 CLIS 代碼鏡頭。
  - 候選數過多或熵值過高時觸發 `SLOW_TRACK`，指派靜態/動態/離散診斷探針：
  ```bash
  python tools/indexer/q_index.py route --intent "字幕"
  python tools/indexer/q_index.py route --intent "讓影片節奏更有科技感"
  ```
- **記錄 Gen-2 導航遙測事件**（離線演化能力圖與探針權重）：
  ```bash
  python tools/indexer/q_index.py feedback --query "字幕時間不對" --selected "caption_titlecards" --success true
  ```





---

## 🚀 導入新專案步驟

1. 將 `tools/` 資料夾直接複製到新專案根目錄。
2. 將 `UNIVERSAL_AI_DEVELOPMENT_GUIDELINES.md` 複製至新專案根目錄，可直接命名為 `AGENTS.md`、`RULES.md` 或 `CLAUDE.md` 作為 Agent 的最高行動原則。
3. （可選）在新專案的根目錄加入 `CODEBASE_MAP.md`，並設定 `tools/indexer/index_engine.py` 的模組對應表以啟用自動索引地圖。
