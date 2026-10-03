# AGENTS.md (Universal AI Agent Guidance Template)

本檔案為 AI 代理人（Claude Code, Cursor, Antigravity, AutoGen, CrewAI 等）在本專案作業的**最高行動守則與導航介面規範**。

---

## ⚡ 核心原則 (Core Directives)
1. **決策與計算分離**：AI 僅負責語意決策與宣告式合約（JSON/YAML），嚴禁手寫未經驗證的免洗腳本繞道運算。
2. **禁止整檔全量讀取與盲目搜尋**：嚴禁呼叫 `grep -r` 或無邊界遍歷代碼庫，必須全程使用 `agent_nav` 漸進式工具鏈。
3. **兩次失敗止損**：同一問題修復連續失敗 2 次，立刻停止猜測，輸出結構化止損報告並尋求新證據。

---

## 🧭 代理人導航工具指令手冊 (Agent Navigation CLI)

專案已內建專屬導航入口 `python tools/agent_nav.py`，請在各階段依序調用：

### 1. 任務摸索與模組定位 (不知道在哪裡時)
```bash
# 透過 Gen-2 Q-Index 意圖導航（共形閘門評估，自動穿透快速路徑）
python tools/agent_nav.py route "<任務描述或意圖關鍵字>"
```

### 2. 精準代碼符號定位與切片 (知道函式名時，超省 Token)
```bash
# 符號粗篩 (僅返回簽名與行號，每項 15~30 tokens)
python tools/agent_nav.py symbol <函式或類別名>

# 檔案骨架檢驗 (剔除實作內容，約 200~400 tokens)
python tools/agent_nav.py struct <檔案相對路徑>

# 精準符號區塊讀取 (僅讀取目標實作 50~100 行，嚴禁全檔 dump)
python tools/agent_nav.py read <檔案相對路徑> -s <函式名>
```

### 3. 因果分析與依賴追蹤 (修改程式前必跑)
```bash
# 反向切片：查詢誰呼叫了這個函式 (防止改動破壞呼叫端)
python tools/agent_nav.py callers <函式名>

# 前向切片：查詢這個函式內部依賴了哪些下游對象
python tools/agent_nav.py callees <檔案相對路徑> <函式名>
```

### 4. 檔案快速查詢與偏好記憶
```bash
# 快取檔案定位 (不掃描磁碟，毫秒級返回)
python tools/agent_nav.py file <檔名關鍵字>

# 查詢專案或全域慣例記憶
python tools/agent_nav.py pref get
```

### 5. 提交前檢查
- 提交前必須執行 `git status` 確保工作目錄乾淨，無免洗測試檔案殘留。
- 專案已配置 Pre-commit Hook，提交時會自動同步能力圖譜與代碼索引。
