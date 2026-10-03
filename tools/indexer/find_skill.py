#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT Skill Finder CLI
快速檢索專案技能與指南。
用法：
  python tools/indexer/find_skill.py <關鍵字>
  python tools/indexer/find_skill.py --module 1_Aroll
  python tools/indexer/find_skill.py --list
"""

import sys
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
REGISTRY_FILE = ROOT_DIR / ".agents" / "skills_registry.json"

def search_skills(query=None, module_filter=None, show_all=False):
    if not REGISTRY_FILE.exists():
        print("[-] 尚未找到 skills_registry.json，正在自動為您產生索引...")
        from index_engine import run_all
        run_all()

    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)

    results = []
    q = query.lower() if query else None
    mod = module_filter.lower() if module_filter else None

    for name, data in registry.items():
        if mod and mod not in data.get("category", "").lower():
            continue
        if show_all:
            results.append((0, data))
            continue
        if q:
            match_name = q in data["name"].lower()
            match_desc = q in data.get("description", "").lower()
            match_cat = q in data.get("category", "").lower()
            if match_name or match_desc or match_cat:
                score = 0
                if match_name:
                    score += 10
                if match_cat:
                    score += 5
                if match_desc:
                    score += 2
                results.append((score, data))
        else:
            results.append((0, data))

    if q:
        results.sort(key=lambda x: x[0], reverse=True)
        results = [x[1] for x in results]
    else:
        results = [x[1] for x in results]
        results.sort(key=lambda x: x["name"])

    return results

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="ROBOT 專業技能快速檢索工具 (Skill Finder)")
    parser.add_argument("query", nargs="?", default="", help="欲搜尋的關鍵字或任務描述（例如：表情、運鏡、broll、剪輯）")
    parser.add_argument("-m", "--module", help="過濾特定模組（例如：1_Aroll, 7_Designer）")
    parser.add_argument("-l", "--list", action="store_true", help="列出全專案所有技能清單")
    parser.add_argument("-c", "--catalog", action="store_true", help="【目錄層披露】極簡摘要 (15~30 tokens/項，常駐導航首選)")
    parser.add_argument("-d", "--describe", action="store_true", help="【描述層披露】含負向防誤觸條件與詳細職責 (50~120 tokens/項)")
    parser.add_argument("-j", "--json", action="store_true", help="以 JSON 格式輸出")

    args = parser.parse_args()

    if not args.query and not args.module and not args.list:
        parser.print_help()
        print("\n範例：")
        print("  python tools/indexer/find_skill.py 運鏡")
        print("  python tools/indexer/find_skill.py -m 1_Aroll --catalog")
        print("  python tools/indexer/find_skill.py 配樂 --describe")
        return

    matched = search_skills(args.query, args.module, args.list)

    # 確保字典序排序以支援 Prompt Caching 命中
    matched = sorted(matched, key=lambda x: x["name"])

    if args.json:
        print(json.dumps(matched, ensure_ascii=False, indent=2))
        return

    print(f"\n🔍 技能檢索結果（共找到 {len(matched)} 個相符技能，已依字典序排列）：\n" + "=" * 60)
    for s in matched:
        cat = s.get("category", "_Global")
        if args.catalog:
            # 目錄層 (Catalog Layer): 約 15~30 tokens
            summary = s.get("summary") or s.get("description", "")[:25]
            print(f"[{cat:<10}] {s['name']:<30} ➔ {summary}")
        elif args.describe:
            # 描述層 (Descriptor Layer): 包含負向防誤觸 patterns
            print(f"📦 技能名稱: {s['name']}  [{cat}]")
            print(f"📄 核心職責: {s['description']}")
            negs = s.get("triggers", {}).get("negative_patterns", [])
            if negs:
                print("⚠️  防誤觸/限制條件 (Negative Patterns):")
                for n in negs:
                    print(f"   • {n}")
            print(f"🔗 實體路徑: {s['path']}")
            print("-" * 60)
        else:
            # 預設標準輸出
            print(f"📦 技能名稱: {s['name']}  [{cat}]")
            print(f"📄 核心職責: {s['description']}")
            print(f"🔗 實體路徑: {s['path']}")
            print("-" * 60)

if __name__ == "__main__":
    main()
