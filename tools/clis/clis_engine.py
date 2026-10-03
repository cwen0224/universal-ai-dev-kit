#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT AST & Code Location Indexing System (CLIS)
符合論文規範之「漸進式揭露協定 (Progressive Disclosure)」核心實作：
1. search_symbols: 跨專案搜尋函式、類別、方法簽名，返回緊湊 JSON（每項 15~30 tokens）
2. get_symbol_structure: 抽取檔案結構骨架，剔除實作（限制 200~400 tokens）
3. read_symbol_source: 限制性擷取特定符號實作主體或行號區間（防整檔傾倒）
"""

import os
import sys
import ast
import json
import re
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
SYMBOL_INDEX_FILE = CACHE_DIR / "symbol_index.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache",
    ".venv", "venv", "site-packages", "Lib", "Scripts", "Include"
}

# ---------------------------------------------------------
# Python AST 解析器
# ---------------------------------------------------------
def parse_python_symbols(file_path: Path, rel_path: str):
    """解析 Python 原始碼中的 class, function, async function 與 docstring"""
    symbols = []
    try:
        content = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 取得參數簽名
            args = [a.arg for a in node.args.args]
            sig = f"{node.name}({', '.join(args)})"
            doc = ast.get_docstring(node) or ""
            doc_summary = doc.strip().splitlines()[0] if doc.strip() else ""
            
            symbols.append({
                "name": node.name,
                "kind": "function",
                "signature": sig,
                "file": rel_path,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "doc": doc_summary[:100]
            })
        elif isinstance(node, ast.ClassDef):
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            sig = f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
            doc = ast.get_docstring(node) or ""
            doc_summary = doc.strip().splitlines()[0] if doc.strip() else ""
            
            symbols.append({
                "name": node.name,
                "kind": "class",
                "signature": sig,
                "file": rel_path,
                "start_line": node.lineno,
                "end_line": getattr(node, "end_lineno", node.lineno),
                "doc": doc_summary[:100]
            })

    return symbols

# ---------------------------------------------------------
# JavaScript / TypeScript 語法骨架解析器 (Regex AST 模擬)
# ---------------------------------------------------------
def parse_js_symbols(file_path: Path, rel_path: str):
    """解析 JS / TS 檔案中的 function, class, export"""
    symbols = []
    try:
        lines = file_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    except Exception:
        return symbols

    # 正則規則
    func_pattern = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\((.*?)\)")
    class_pattern = re.compile(r"^(?:export\s+)?class\s+([a-zA-Z0-9_$]+)")
    arrow_pattern = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>")

    for idx, line in enumerate(lines, start=1):
        s_line = line.strip()
        
        # 匹配 function
        m_func = func_pattern.search(s_line)
        if m_func:
            fn_name = m_func.group(1)
            params = m_func.group(2)
            symbols.append({
                "name": fn_name,
                "kind": "function",
                "signature": f"{fn_name}({params.strip()})",
                "file": rel_path,
                "start_line": idx,
                "end_line": idx,
                "doc": ""
            })
            continue

        # 匹配 class
        m_class = class_pattern.search(s_line)
        if m_class:
            cls_name = m_class.group(1)
            symbols.append({
                "name": cls_name,
                "kind": "class",
                "signature": f"class {cls_name}",
                "file": rel_path,
                "start_line": idx,
                "end_line": idx,
                "doc": ""
            })
            continue

        # 匹配 arrow function
        m_arrow = arrow_pattern.search(s_line)
        if m_arrow:
            fn_name = m_arrow.group(1)
            params = m_arrow.group(2)
            symbols.append({
                "name": fn_name,
                "kind": "function",
                "signature": f"{fn_name}({params.strip()})",
                "file": rel_path,
                "start_line": idx,
                "end_line": idx,
                "doc": ""
            })

    return symbols

# ---------------------------------------------------------
# 全專案符號索引構建
# ---------------------------------------------------------
def build_symbol_index():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    all_symbols = []

    for p in ROOT_DIR.rglob("*"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if not p.is_file():
            continue

        rel = p.relative_to(ROOT_DIR).as_posix()
        ext = p.suffix.lower()

        if ext == ".py":
            all_symbols.extend(parse_python_symbols(p, rel))
        elif ext in [".js", ".mjs", ".ts"]:
            all_symbols.extend(parse_js_symbols(p, rel))

    with open(SYMBOL_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(all_symbols, f, ensure_ascii=False, indent=2)

    return all_symbols

def get_symbols():
    if not SYMBOL_INDEX_FILE.exists():
        return build_symbol_index()
    try:
        with open(SYMBOL_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return build_symbol_index()

# ---------------------------------------------------------
# Agent 微協定工具 1: search_symbols
# ---------------------------------------------------------
def search_symbols(query: str, kind: str = None, module_prefix: str = None, max_results: int = 15):
    """查詢跨專案符號，回傳緊湊宣告資訊 (15~30 tokens/項)"""
    symbols = get_symbols()
    q = query.lower()
    results = []

    for s in symbols:
        if kind and s["kind"] != kind:
            continue
        if module_prefix and not s["file"].startswith(module_prefix):
            continue

        # 計算匹配權重
        name_lower = s["name"].lower()
        if q == name_lower:
            score = 100
        elif name_lower.startswith(q):
            score = 50
        elif q in name_lower:
            score = 20
        elif q in s.get("signature", "").lower() or q in s.get("doc", "").lower():
            score = 10
        else:
            continue

        results.append((score, {
            "name": s["name"],
            "kind": s["kind"],
            "signature": s["signature"],
            "file": s["file"],
            "lines": f"{s['start_line']}-{s['end_line']}",
            "doc": s.get("doc", "")
        }))

    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:max_results]]

# ---------------------------------------------------------
# Agent 微協定工具 2: get_symbol_structure
# ---------------------------------------------------------
def get_symbol_structure(target_path: str):
    """獲取特定檔案的宣告骨架，剔除實作主體，壓縮至 200~400 tokens"""
    file_p = ROOT_DIR / target_path
    if not file_p.exists():
        return {"error": f"檔案不存在: {target_path}"}

    rel = file_p.relative_to(ROOT_DIR).as_posix()
    ext = file_p.suffix.lower()

    if ext == ".py":
        syms = parse_python_symbols(file_p, rel)
    elif ext in [".js", ".mjs", ".ts"]:
        syms = parse_js_symbols(file_p, rel)
    else:
        return {"file": rel, "note": "非 AST 支援之語言檔案"}

    # 組織成結構骨架
    classes = [s for s in syms if s["kind"] == "class"]
    functions = [s for s in syms if s["kind"] == "function"]

    return {
        "file": rel,
        "total_symbols": len(syms),
        "classes": [{"name": c["name"], "signature": c["signature"], "lines": f"{c['start_line']}-{c['end_line']}"} for c in classes],
        "functions": [{"name": f["name"], "signature": f["signature"], "lines": f"{f['start_line']}-{f['end_line']}"} for f in functions]
    }

# ---------------------------------------------------------
# Agent 微協定工具 3: read_symbol_source
# ---------------------------------------------------------
def read_symbol_source(file_path: str, symbol_name: str = None, start_line: int = None, end_line: int = None):
    """精確擷取目標符號實作或限定行號區間，嚴防整檔傾倒"""
    file_p = ROOT_DIR / file_path
    if not file_p.exists():
        return f"[-] 錯誤：找不到檔案 {file_path}"

    lines = file_p.read_text(encoding="utf-8-sig", errors="ignore").splitlines()

    # 若指定了符號名稱，先透過 AST 鎖定精確行號
    if symbol_name and not start_line:
        syms = get_symbols()
        target = next((s for s in syms if s["file"] == file_path and s["name"] == symbol_name), None)
        if target:
            start_line = target["start_line"]
            end_line = target["end_line"]
        else:
            # 嘗試正則快速尋找
            for idx, l in enumerate(lines, 1):
                if re.search(rf"\b(def|class|function)\s+{symbol_name}\b", l):
                    start_line = idx
                    end_line = min(idx + 50, len(lines))
                    break

    if not start_line:
        return f"[-] 未指定符號或找不到符號 '{symbol_name}'"

    s_idx = max(1, start_line)
    e_idx = min(len(lines), end_line or (s_idx + 40))

    snippet = lines[s_idx - 1:e_idx]
    numbered = [f"{i:4d} | {line}" for i, line in enumerate(snippet, start=s_idx)]

    return "\n".join([
        f"--- 📍 符號實作區塊: {file_path} (Lines {s_idx} ~ {e_idx}) ---",
        *numbered,
        "--- [區塊擷取結束，Token 節制保證] ---"
    ])

# ---------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------
def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="ROBOT 漸進式程式碼定位引擎 (CLIS)")
    subparsers = parser.add_subparsers(dest="command")

    # 1. 搜尋符號
    p_search = subparsers.add_parser("search", help="跨專案搜尋符號 (search_symbols)")
    p_search.add_argument("query", help="符號名稱或關鍵字")
    p_search.add_argument("-k", "--kind", choices=["class", "function"], help="過濾符號類型")
    p_search.add_argument("-m", "--module", help="過濾模組路徑前綴 (例如: 10_Visual)")
    p_search.add_argument("-n", "--limit", type=int, default=10, help="最多返回數量")

    # 2. 結構骨架
    p_struct = subparsers.add_parser("struct", help="取得檔案宣告骨架 (get_symbol_structure)")
    p_struct.add_argument("file", help="目標檔案路徑")

    # 3. 讀取實作
    p_read = subparsers.add_parser("read", help="讀取目標符號實作主體 (read_symbol_source)")
    p_read.add_argument("file", help="目標檔案路徑")
    p_read.add_argument("-s", "--symbol", help="目標符號名稱")
    p_read.add_argument("--start", type=int, help="起始行號")
    p_read.add_argument("--end", type=int, help="結束行號")

    # 4. 重建索引
    p_index = subparsers.add_parser("reindex", help="全專案 AST 符號索引重建")

    args = parser.parse_args()

    if args.command == "search":
        res = search_symbols(args.query, args.kind, args.module, args.limit)
        print(f"\n🔍 符號搜尋結果 (共 {len(res)} 項)：\n" + "=" * 60)
        for r in res:
            print(f"[{r['kind'].upper():<8}] {r['name']:<25} ➔ {r['file']}:{r['lines']}")
            print(f"           簽名: {r['signature']}")
            if r['doc']:
                print(f"           說明: {r['doc']}")
            print("-" * 60)

    elif args.command == "struct":
        res = get_symbol_structure(args.file)
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.command == "read":
        res = read_symbol_source(args.file, args.symbol, args.start, args.end)
        print(res)

    elif args.command == "reindex":
        syms = build_symbol_index()
        print(f"[+] AST 符號索引建立完成！全專案收錄 {len(syms)} 個符號。")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
