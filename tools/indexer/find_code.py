#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT Code Finder CLI (with FILE_INDEX Cache)
快速搜尋專案中的程式碼、腳本與模組入口。
優化策略：
  優先讀取 .cache/file_index.json 快取索引，避免每次執行 rglob("*") 遍歷檔案系統。
  若快取不存在或加上 --refresh 旗標時，才執行一次性索引構建。

用法：
  python tools/indexer/find_code.py <檔名或關鍵字>
  python tools/indexer/find_code.py --module 10_Visual
  python tools/indexer/find_code.py --ext js
  python tools/indexer/find_code.py --reindex
"""

import sys
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
FILE_INDEX_PATH = CACHE_DIR / "file_index.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache",
    ".venv", "venv", "site-packages"
}

def build_file_index() -> dict:
    """一次性構建輕量檔案索引字典，節省後續每次呼叫的磁碟 IO"""
    index = {}
    for p in ROOT_DIR.rglob("*"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue

        rel_path = p.relative_to(ROOT_DIR).as_posix()
        module_name = rel_path.split("/")[0] if "/" in rel_path else ""
        ext = p.suffix.lower().lstrip(".")
        stat = p.stat()

        index[rel_path] = {
            "name": p.name,
            "module": module_name,
            "ext": ext,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime)
        }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(FILE_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index

def load_file_index(force_refresh=False) -> dict:
    if force_refresh or not FILE_INDEX_PATH.is_file():
        return build_file_index()
    try:
        with open(FILE_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return build_file_index()

def search_code(query=None, module_filter=None, ext_filter=None, force_refresh=False):
    index = load_file_index(force_refresh)
    results = []

    q = query.lower() if query else None
    mod = module_filter.lower() if module_filter else None
    ext = ext_filter.lower().lstrip(".") if ext_filter else None

    for rel_path, meta in index.items():
        # 模組過濾
        if mod and not meta["module"].lower().startswith(mod):
            continue
        # 副檔名過濾
        if ext and meta["ext"] != ext:
            continue
        # 關鍵字比對
        if q:
            if q in meta["name"].lower() or q in rel_path.lower():
                results.append((rel_path, meta))
        else:
            results.append((rel_path, meta))

    results.sort(key=lambda x: x[0])
    return results

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="ROBOT 程式檔案快速定位工具 (Code Finder with Cache)")
    parser.add_argument("query", nargs="?", default="", help="欲搜尋的檔名或關鍵字")
    parser.add_argument("-m", "--module", help="過濾特定模組（例如：10_Visual, 1_Aroll）")
    parser.add_argument("-e", "--ext", help="過濾副檔名（例如：py, js, html）")
    parser.add_argument("--reindex", action="store_true", help="強制重新掃描檔案系統建立索引快取")

    args = parser.parse_args()

    if args.reindex:
        idx = build_file_index()
        print(f"[OK] 檔案索引已重新構建，共計 {len(idx)} 個有效檔案。")
        return

    results = search_code(args.query, args.module, args.ext)

    if not results:
        print(f"[-] 找不到符合「{args.query}」的程式檔案。")
        sys.exit(0)

    print(f"\n[+] 找到 {len(results)} 個符合條件的程式檔案：\n")
    for rel_path, meta in results:
        print(f"  • {rel_path} ({meta['size']} bytes)")
    print()

if __name__ == "__main__":
    main()
