#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Pre-Commit Hook Installer
一鍵安裝自動化 Git Hook，在每次 `git commit` 前自動執行：
1. `file_index.json` 更新 (防止新加入的檔案未被索引)
2. `capability_graph.json` 重新編譯 (防止能力契約中繼資料腐化 Metadata Drift)
3. `call_graph.json` 重新編譯 (保持呼叫鏈最新狀態)

用法：
  python tools/hooks/install_hooks.py
"""

import sys
import os
import stat
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
GIT_HOOKS_DIR = ROOT_DIR / ".git" / "hooks"
PRE_COMMIT_FILE = GIT_HOOKS_DIR / "pre-commit"

HOOK_SCRIPT_CONTENT = """#!/bin/sh
# Universal AI Dev Kit - Automatic Metadata & Index Sync Hook
echo "[Git Hook] 正在自動同步專案能力契約圖譜與代碼索引..."

# 使用 python 執行增量重新索引
python tools/agent_nav.py reindex

# 若索引產物被更新，自動加回 staging 區
git add .agents/capability_graph.json .cache/file_index.json .cache/call_graph.json 2>/dev/null || true

echo "[Git Hook] 索引與能力合約同步完成，繼續提交。"
exit 0
"""

def install_hook():
    if not (ROOT_DIR / ".git").is_dir():
        print("[-] 錯誤：當前專案根目錄下找不到 .git 資料夾，請確認已執行 git init。")
        sys.exit(1)

    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PRE_COMMIT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(HOOK_SCRIPT_CONTENT)

    # 在 Unix/Linux/macOS 或 Windows Git Bash 給予執行權限
    st = os.stat(PRE_COMMIT_FILE)
    os.chmod(PRE_COMMIT_FILE, st.st_mode | stat.S_IEXEC)

    print(f"[OK] 成功安裝 Pre-Commit Hook 至：{PRE_COMMIT_FILE}")
    print("     今後每次執行 git commit 前，將自動執行 agent_nav reindex 並同步圖譜，徹底防範中繼資料腐化！")

if __name__ == "__main__":
    install_hook()
