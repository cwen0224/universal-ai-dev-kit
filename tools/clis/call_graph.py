#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AST Call Graph & Program Slicing Tool
為 CLIS 系統提供雙向語意呼叫鏈分析與程式切片支援：
1. 查詢特定函式被誰呼叫 (Callers / Inbound / 反向切片)
2. 查詢特定函式呼叫了誰 (Callees / Outbound / 前向切片)
3. 支援跨檔案 import 追蹤與最小依賴閉包輸出

用法：
  # 查詢特定函式在全專案中的呼叫者與被呼叫者
  python tools/clis/call_graph.py callers <function_name>
  python tools/clis/call_graph.py callees <file_path> <function_name>
  python tools/clis/call_graph.py trace <function_name>
  python tools/clis/call_graph.py reindex
"""

import sys
import ast
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
CALL_GRAPH_FILE = CACHE_DIR / "call_graph.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache",
    ".venv", "venv", "site-packages"
}

class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, rel_path):
        self.rel_path = rel_path
        self.current_function = None
        self.definitions = [] # [(name, line)]
        self.calls = []       # [(caller_func, callee_name, line)]

    def visit_FunctionDef(self, node):
        prev_func = self.current_function
        self.current_function = node.name
        self.definitions.append((node.name, node.lineno))
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr

        if callee_name and self.current_function:
            self.calls.append((self.current_function, callee_name, node.lineno))
        elif callee_name:
            self.calls.append(("<global>", callee_name, node.lineno))
            
        self.generic_visit(node)

def build_call_graph(force_refresh=False) -> dict:
    if not force_refresh and CALL_GRAPH_FILE.is_file():
        try:
            with open(CALL_GRAPH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    graph = {
        "definitions": {}, # func_name: [{"file": rel_path, "line": line}]
        "callers": {},     # callee_name: [{"caller_file": rel_path, "caller_func": func, "line": line}]
        "callees": {}      # f"{rel_path}:{func}": [callee_name]
    }

    for p in ROOT_DIR.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        rel_path = p.relative_to(ROOT_DIR).as_posix()
        try:
            content = p.read_text(encoding="utf-8-sig", errors="ignore")
            tree = ast.parse(content, filename=str(p))
        except Exception:
            continue

        visitor = CallGraphVisitor(rel_path)
        visitor.visit(tree)

        for name, line in visitor.definitions:
            if name not in graph["definitions"]:
                graph["definitions"][name] = []
            graph["definitions"][name].append({"file": rel_path, "line": line})

        for caller_func, callee_name, line in visitor.calls:
            if callee_name not in graph["callers"]:
                graph["callers"][callee_name] = []
            graph["callers"][callee_name].append({
                "caller_file": rel_path,
                "caller_func": caller_func,
                "line": line
            })

            caller_key = f"{rel_path}:{caller_func}"
            if caller_key not in graph["callees"]:
                graph["callees"][caller_key] = []
            if callee_name not in graph["callees"][caller_key]:
                graph["callees"][caller_key].append(callee_name)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CALL_GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    return graph

def cmd_callers(graph, func_name):
    """查詢反向呼叫者 (Inbound / Who calls this?)"""
    callers = graph["callers"].get(func_name, [])
    defs = graph["definitions"].get(func_name, [])
    print(f"\n🔍 [反向呼叫分析 / Backward Slice] 查詢符號: '{func_name}'")
    if defs:
        print(f"📍 符號定義位置 ({len(defs)} 處):")
        for d in defs:
            print(f"   • {d['file']}:{d['line']}")
    else:
        print("📍 (未在專案中找到該符號的 Python 定義，可能為內建、第三方或動態方法)")

    print(f"\n👥 呼叫來源 (Callers) [共 {len(callers)} 處呼叫]:")
    if not callers:
        print("   • (無直接靜態呼叫紀錄)")
    else:
        # 去重統計
        seen = set()
        for c in callers:
            loc = f"{c['caller_file']}:{c['line']} (in {c['caller_func']})"
            if loc not in seen:
                seen.add(loc)
                print(f"   • {loc}")
    print()

def cmd_callees(graph, file_path, func_name):
    """查詢前向被呼叫者 (Outbound / What does this call?)"""
    key = f"{file_path}:{func_name}"
    callees = graph["callees"].get(key, [])
    print(f"\n🔍 [前向依賴分析 / Forward Slice] 函式: '{key}'")
    print(f"📦 呼叫之下游對象 (Callees) [共 {len(callees)} 個]:")
    if not callees:
        print("   • (未發起任何函式呼叫)")
    else:
        for callee in sorted(callees):
            print(f"   • {callee}")
    print()

def cmd_trace(graph, func_name):
    """綜合追蹤：定義、呼叫者、以及若是本專案函式，列出其下游呼叫"""
    cmd_callers(graph, func_name)
    defs = graph["definitions"].get(func_name, [])
    for d in defs:
        cmd_callees(graph, d["file"], func_name)

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="AST Call Graph & Program Slicing Tool for CLIS")
    subparsers = parser.add_subparsers(dest="command")

    p_callers = subparsers.add_parser("callers", help="Find who calls a specific function (Backward Slice)")
    p_callers.add_argument("func_name", help="Target function name")

    p_callees = subparsers.add_parser("callees", help="Find what a specific function calls (Forward Slice)")
    p_callees.add_argument("file_path", help="Relative file path")
    p_callees.add_argument("func_name", help="Function name in the file")

    p_trace = subparsers.add_parser("trace", help="Comprehensive trace of definitions, callers and callees")
    p_trace.add_argument("func_name", help="Target function name")

    p_reindex = subparsers.add_parser("reindex", help="Rebuild full AST call graph cache")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "reindex":
        g = build_call_graph(force_refresh=True)
        print(f"[OK] 呼叫圖 (Call Graph) 重建完成，收錄 {len(g['definitions'])} 個函式定義與 {len(g['callers'])} 組調用關聯。")
        return

    graph = build_call_graph(force_refresh=False)
    if args.command == "callers":
        cmd_callers(graph, args.func_name)
    elif args.command == "callees":
        cmd_callees(graph, args.file_path, args.func_name)
    elif args.command == "trace":
        cmd_trace(graph, args.func_name)

if __name__ == "__main__":
    main()
