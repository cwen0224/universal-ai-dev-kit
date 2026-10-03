#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill-to-Code & Code-to-Skill Linker Tool
為 ROBOT 專案建立「技能員工 (SKILL) ↔ 辦公工具 (CODE)」雙向映射與索引。

能力：
  1. 從 SKILL 找 CODE: 查詢該技能/工作者依據規範調用的核心腳本與工具檔案。
  2. 從 CODE 找 SKILL: 查詢修改某個程式檔案時，必須遵守與參考的技能規範。
  3. 支援一鍵重建雙向快取 (.cache/skill_code_map.json)。
"""

import sys
import json
import re
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
MAP_FILE = CACHE_DIR / "skill_code_map.json"
FILE_INDEX_FILE = CACHE_DIR / "file_index.json"
SKILLS_REGISTRY_FILE = ROOT_DIR / ".agents" / "skills_registry.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache"
}

def build_skill_code_map(force_refresh=False) -> dict:
    if not force_refresh and MAP_FILE.is_file():
        try:
            with open(MAP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # 1. 確保基礎索引存在
    if not FILE_INDEX_FILE.is_file():
        current_dir = Path(__file__).resolve().parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from find_code import build_file_index
        file_index = build_file_index()
    else:
        with open(FILE_INDEX_FILE, "r", encoding="utf-8") as f:
            file_index = json.load(f)

    if not SKILLS_REGISTRY_FILE.is_file():
        current_dir = Path(__file__).resolve().parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        from index_engine import run_all
        run_all()

        
    with open(SKILLS_REGISTRY_FILE, "r", encoding="utf-8") as f:
        skills_registry = json.load(f)

    # 建立檔名 basename 反查表
    basename_to_paths = {}
    for rel_path, meta in file_index.items():
        if meta.get("ext") in ["py", "js", "html", "sh", "bat", "ps1"]:
            bname = Path(rel_path).name.lower()
            basename_to_paths.setdefault(bname, []).append(rel_path)

    skill_to_tools = {}
    tool_to_skills = {}

    for skill_name, skill_meta in skills_registry.items():
        skill_path = ROOT_DIR / skill_meta["path"]
        direct_files = set()
        
        if skill_path.is_file():
            content = skill_path.read_text(encoding="utf-8", errors="ignore")
            # 提取文檔中出現的代碼檔案
            raw_tokens = re.findall(r'[\w\-/\\]+\.(?:py|js|json|html|sh|ps1|bat)', content)
            for tok in raw_tokens:
                clean_name = tok.replace("\\", "/").split("/")[-1].lower()
                if clean_name in basename_to_paths:
                    for p in basename_to_paths[clean_name]:
                        direct_files.add(p)

        cat = skill_meta.get("category", "")
        # 所屬模組的核心程式 (作為同模組 context 候選)
        module_files = [
            p for p, m in file_index.items() 
            if cat and m.get("module") == cat and m.get("ext") in ["py", "js"]
        ]

        skill_to_tools[skill_name] = {
            "name": skill_name,
            "category": cat,
            "description": skill_meta.get("description", ""),
            "path": skill_meta["path"],
            "direct_tools": sorted(list(direct_files)),
            "module_tools_count": len(module_files)
        }

        # 建立反向索引：檔案 -> 技能
        for f in direct_files:
            tool_to_skills.setdefault(f, []).append({
                "skill": skill_name,
                "role": "Direct Reference (直接規範引用)",
                "category": cat
            })

    full_map = {
        "skill_to_tools": skill_to_tools,
        "tool_to_skills": tool_to_skills,
        "summary": {
            "total_skills": len(skill_to_tools),
            "linked_tools_count": len(tool_to_skills)
        }
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(full_map, f, ensure_ascii=False, indent=2)

    return full_map

def find_tools_for_skill(skill_name_query: str):
    data = build_skill_code_map()
    s2t = data["skill_to_tools"]
    
    q = skill_name_query.lower()
    matches = [k for k in s2t.keys() if q in k.lower()]
    
    if not matches:
        print(f"[-] 找不到名稱包含「{skill_name_query}」的技能規範。")
        return

    for k in matches[:5]:
        meta = s2t[k]
        print(f"\n👔 技能員工: {meta['name']} (所屬模組: {meta['category'] or '全域'})")
        print(f"📜 規範指南: {meta['path']}")
        print(f"📝 職責摘要: {meta['description'][:90]}...")
        
        tools = meta["direct_tools"]
        if tools:
            print(f"🛠️ 直接綁定的辦公工具與實作程式 ({len(tools)} 項):")
            for t in tools:
                print(f"   • {t}")
        else:
            print("💡 (該技能未在內文明確標註單一腳本，依賴模組標準管線執行)")

def find_skills_for_code(code_file_query: str):
    data = build_skill_code_map()
    t2s = data["tool_to_skills"]
    s2t = data["skill_to_tools"]
    
    q = code_file_query.lower().replace("\\", "/")
    matched_tools = [p for p in t2s.keys() if q in p.lower()]
    
    if matched_tools:
        print(f"\n🔍 查詢程式檔案「{code_file_query}」關聯的技能規範：")
        for tool in matched_tools[:10]:
            print(f"\n📄 程式檔案: {tool}")
            for item in t2s[tool]:
                print(f"   👔 遵守規範: {item['skill']} [{item['role']}]")
                sk_meta = s2t.get(item['skill'], {})
                if sk_meta.get("path"):
                    print(f"      📖 規範指南: {sk_meta['path']}")
    else:
        # 如果沒有直接文字關聯，依據模組路徑查找該模組的主管技能
        mod_prefix = q.split("/")[0] if "/" in q else q
        mod_skills = [
            (k, v) for k, v in s2t.items() 
            if v.get("category", "").lower() == mod_prefix.lower()
        ]
        if mod_skills:
            print(f"\n📄 程式檔案: {code_file_query}")
            print(f"ℹ️ (該檔案無個別 SKILL 直接指名，但屬於模組「{mod_prefix}」，適用以下模組指導規範):")
            for k, meta in mod_skills[:8]:
                print(f"   👔 {meta['name']}")
                print(f"      📖 規範指南: {meta['path']}")
        else:
            print(f"[-] 找不到程式「{code_file_query}」對應的技能規範。")

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Skill ↔ Code 雙向連結器")
    parser.add_argument("query", nargs="?", default="", help="技能名或程式檔案路徑")
    parser.add_argument("-t", "--to-code", action="store_true", help="查詢該技能使用的程式碼工具 (預設自動偵測)")
    parser.add_argument("-s", "--to-skill", action="store_true", help="查詢該程式碼受哪些技能規範管轄 (預設自動偵測)")
    parser.add_argument("--reindex", action="store_true", help="重新建立雙向對照索引")

    args = parser.parse_args()

    if args.reindex:
        res = build_skill_code_map(force_refresh=True)
        print(f"[OK] 技能與代碼雙向索引已更新：收錄 {res['summary']['total_skills']} 個技能，{res['summary']['linked_tools_count']} 組精準工具對應。")
        return

    # 自動判斷模式：如果 query 包含 / 或副檔名，偏向 code-to-skill；否則為 skill-to-code
    is_code = bool(re.search(r'\.(py|js|html|json|sh|bat)|[/\\]', args.query))
    if args.to_skill or (is_code and not args.to_code):
        find_skills_for_code(args.query)
    else:
        find_tools_for_skill(args.query)

if __name__ == "__main__":
    main()
