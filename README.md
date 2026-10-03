# 跨專案通用 AI 研發與索引工具套件 (Universal AI Development & Tooling Kit)

本資料夾彙整了可直接複製到**任何新專案**中使用的通用指南文件與索引定位工具鏈，協助 AI 代理人（Claude Code, Cursor, Antigravity, AutoGen 等）達成**超低 Token 消耗、精準定位、防禦性開發與對抗式治理**。

---

## 📦 套件內容結構

```
export_package/
├── UNIVERSAL_AI_DEVELOPMENT_GUIDELINES.md   # 核心開發與工程準則 (可更名為 AGENTS.md / RULES.md)
├── docs/
│   └── README.md                            # 同上規範文件副本，方便放在文檔庫
└── tools/                                   # 核心索引與漸進式代碼定位工具鏈 (純標準庫，無外部依賴)
    ├── clis/
    │   ├── clis_engine.py                   # AST 語法樹符號提取、骨架檢視與精準切片讀取器
    │   └── merkle_tree.py                   # Merkle Tree SHA-256 秒級增量變更感知器
    └── indexer/
        ├── q_index.py                       # Akinator 式資訊增益選題與模糊意圖導航引擎
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

### 6. `tools/indexer/q_index.py` (Q-Index 智能意圖導航引擎)
Akinator 式資訊增益二分導航：當 AI 不確定任務歸屬時，以最高資訊量問題迅速二分收斂候選空間：
- **意圖與狀態導航**：
  ```bash
  python tools/indexer/q_index.py route --intent "字幕"
  python tools/indexer/q_index.py route --state "rendered_video" --problem "timing_misalignment"
  ```
- **記錄檢索遙測與回饋**（自我進化）：
  ```bash
  python tools/indexer/q_index.py feedback --query "字幕時間不對" --selected "3_Caption" --success true
  ```



---

## 🚀 導入新專案步驟

1. 將 `tools/` 資料夾直接複製到新專案根目錄。
2. 將 `UNIVERSAL_AI_DEVELOPMENT_GUIDELINES.md` 複製至新專案根目錄，可直接命名為 `AGENTS.md`、`RULES.md` 或 `CLAUDE.md` 作為 Agent 的最高行動原則。
3. （可選）在新專案的根目錄加入 `CODEBASE_MAP.md`，並設定 `tools/indexer/index_engine.py` 的模組對應表以啟用自動索引地圖。
