#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT Code Finder CLI
快速搜尋專案中的程式碼、腳本與模組入口。
用法：
  python tools/indexer/find_code.py <檔名或關鍵字>
  python tools/indexer/find_code.py --module 10_Visual
  python tools/indexer/find_code.py --ext js
"""

import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp"
}

def search_code(query=None, module_filter=None, ext_filter=None):
    results = []
    q = query.lower() if query else None
    mod = module_filter.lower() if module_filter else None
    ext = ("." + ext_filter.lower().lstrip(".")) if ext_filter else None

    for p in ROOT_DIR.rglob("*"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue

        rel_path = p.relative_to(ROOT_DIR).as_posix()
        
        # 模組過濾
        if mod and not rel_path.lower().startswith(mod):
            continue
            
        # 副檔名過濾
        if ext and p.suffix.lower() != ext:
            continue

        # 關鍵字比對
        if q:
            if q in p.name.lower() or q in rel_path.lower():
                results.append(p)
        else:
            results.append(p)

    return sorted(results, key=lambda x: x.name)

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="ROBOT 程式檔案快速定位工具 (Code Finder)")
    parser.add_argument("query", nargs="?", default="", help="欲搜尋的檔名或關鍵字")
    parser.add_argument("-m", "--module", help="過濾特定模組（例如：10_Visual, 1_Aroll）")
    parser.add_argument("-e", "--ext", help="過濾副檔名（例如：py, js, html）")

    args = parser.parse_args()

    if not args.query and not args.module and not args.ext:
        parser.print_help()
        print("\n範例：")
        print("  python tools/indexer/find_code.py timeline")
        print("  python tools/indexer/find_code.py -m 10_Visual -e py")
        print("  python tools/indexer/find_code.py -m 1_Aroll")
        return

    matched = search_code(args.query, args.module, args.ext)

    print(f"\n🔎 搜尋結果（共找到 {len(matched)} 個相符檔案）：\n" + "=" * 60)
    for p in matched[:50]:  # 限制最多輸出 50 筆
        rel = p.relative_to(ROOT_DIR).as_posix()
        size_kb = p.stat().st_size / 1024
        print(f"📄 {rel:<60} ({size_kb:.1f} KB)")

    if len(matched) > 50:
        print(f"... 還有 {len(matched) - 50} 筆結果未展開，請縮小關鍵字範圍。")
    print("=" * 60)

if __name__ == "__main__":
    main()
