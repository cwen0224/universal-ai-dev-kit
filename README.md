# 跨專案通用 AI 研發與索引工具套件 (Universal AI Development & Tooling Kit)

本資料夾彙整了可直接複製到**任何新專案**中使用的通用指南文件與索引定位工具鏈，協助 AI 代理人（Claude Code, Cursor, Antigravity, AutoGen 等）達成**超低 Token 消耗、精準定位、防禦性開發與對抗式治理**。

---

## 📦 套件內容結構

```
export_package/
├── UNIVERSAL_AI_DEVELOPMENT_GUIDELINES.md   # 核心開發與工程準則 (可更名為 AGENTS.md / RULES.md)
├── docs/
│   ├── README.md                            # 同上規範文件副本，方便放在文檔庫
│   ├── schemas/gen2_navigation_schemas.json # 第二代自適應認知導航標準契約 Schema
│   └── templates/AGENTS.template.md         # 專為外掛 AI 代理人設計之極簡行動規範樣板
└── tools/                                   # 核心索引與漸進式代碼定位工具鏈 (純標準庫，無外部依賴)
    ├── agent_nav.py                         # 🌟 代理人統一導航入口 (Unified Single Entrypoint CLI)
    ├── clis/
    │   ├── clis_engine.py                   # AST 語法樹符號提取、骨架檢視與精準切片讀取器
    │   ├── call_graph.py                    # AST 雙向呼叫鏈與因果切片追蹤器 (Callers / Callees)
    │   └── merkle_tree.py                   # Merkle Tree SHA-256 秒級增量變更感知器
    ├── hooks/
    │   └── install_hooks.py                 # Git Pre-commit Hook 一鍵安裝腳本 (防止中繼資料腐化)
    └── indexer/
        ├── q_index.py                       # Gen-2 自適應認知導航引擎 (共形預測閘門 + 診斷探針)
        ├── capability_compiler.py           # 離線能力契約編譯器 (自動萃取 AST 錨點與合約圖譜)
        ├── skill_code_linker.py             # 🔗 技能員工 (SKILL) ↔ 辦公工具 (CODE) 雙向智慧映射器
        ├── find_code.py                     # 高效代碼快速搜尋 CLI (支援 FILE_INDEX 快取免遍歷)
        ├── find_skill.py                    # 技能/指南多層漸進式檢索 CLI (Catalog/Describe)
        ├── index_engine.py                  # 全系統索引與 CODEBASE_MAP 自動生成引擎
        └── user_pref.py                     # 使用者偏好日誌與記憶管理 CLI (全域與專案雙層作用域)
```

---

## 🌟 統一導航入口：`tools/agent_nav.py`

為了避免 AI 或人類記誦多個工具腳本，專案提供單一聚合入口 `agent_nav.py`：

```bash
# 1. 意圖導航 (模糊任務收斂)
python tools/agent_nav.py route "字幕時間對不上"

# 2. 符號與切片定位
python tools/agent_nav.py symbol <函式名>
python tools/agent_nav.py struct <檔案路徑>
python tools/agent_nav.py read <檔案路徑> -s <函式名>

# 3. 雙向呼叫鏈與因果分析
python tools/agent_nav.py callers <函式名>
python tools/agent_nav.py callees <檔案路徑> <函式名>

# 4. 技能員工 ↔ 辦公工具雙向查詢 (Skill-Code Link)
python tools/agent_nav.py skill <技能名稱>       # 查看該員工負責管轄的辦公工具與實作代碼
python tools/agent_nav.py tool <程式檔案路徑>    # 查看修改該程式碼時，必須遵守與參考的職人規範

# 5. 檔案定位與偏好設定
python tools/agent_nav.py file <檔名關鍵字>
python tools/agent_nav.py pref get

# 6. 一鍵全系統增量重建索引
python tools/agent_nav.py reindex
```

---

## 🛠️ 各工具鏈獨立使用指引 (Independent Tools)

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

### 2. `tools/clis/call_graph.py` (AST 雙向呼叫鏈與因果切片)
為 CLIS 系統提供雙向追蹤，秒級鎖定呼叫來源（Callers）與下游依賴（Callees），避免重啟全域搜尋：
- **反向切片（誰呼叫了這個函式？）**：
  ```bash
  python tools/clis/call_graph.py callers <函式名>
  ```
- **前向切片（這個函式呼叫了誰？）**：
  ```bash
  python tools/clis/call_graph.py callees <檔案路徑> <函式名>
  ```

### 3. `tools/clis/merkle_tree.py` (秒級變更感知)
- 快速建立目錄樹的 SHA-256 雜湊，秒級比對出被修改的檔案清單：
  ```bash
  python tools/clis/merkle_tree.py --diff
  ```

### 4. `tools/indexer/capability_compiler.py` (離線能力契約編譯器)
自動掃描專案程式庫、docstrings 與符號，編譯出符合 Gen-2 契約規範的能力圖譜（`capability_graph.json`）：
```bash
python tools/indexer/capability_compiler.py compile
```

### 5. `tools/indexer/skill_code_linker.py` (技能員工 ↔ 辦公工具雙向智慧映射器)
將專案技能 (SKILL) 視為負責專項工作的員工，代碼 (CODE) 視為其操作的辦公工具，實現雙向追蹤：
- **職人叫工具（Skill ➔ Code）**：
  ```bash
  python tools/indexer/skill_code_linker.py <技能名> -t
  # 或透過統一入口：python tools/agent_nav.py skill <技能名>
  ```
- **工具找職人（Code ➔ Skill）**：
  ```bash
  python tools/indexer/skill_code_linker.py <檔案路徑> -s
  # 或透過統一入口：python tools/agent_nav.py tool <檔案路徑>
  ```

### 6. `tools/indexer/q_index.py` (Gen-2 自適應認知導航引擎)
整合資訊論熵減、共形預測置信區間與預編譯探針庫：
```bash
python tools/indexer/q_index.py route --intent "字幕"
```

### 7. `tools/hooks/install_hooks.py` (Git Pre-commit Hook 安裝器)
一鍵安裝自動化 Pre-commit 鉤子，提交時自動執行 `agent_nav reindex`，杜絕中繼資料腐化：
```bash
python tools/hooks/install_hooks.py
```

---

## 🚀 導入新專案步驟

1. 將 `tools/` 資料夾直接複製到新專案根目錄。
2. 將 `docs/templates/AGENTS.template.md` 複製至新專案根目錄並命名為 `AGENTS.md`（或 `CLAUDE.md`）。
3. 執行 `python tools/agent_nav.py reindex` 構建專案初次索引。
4. （推薦）執行 `python tools/hooks/install_hooks.py` 啟用 Commit 自動同步防護。

