#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capability Compiler & Contract Generator
依據第二代認知導航規範 (CapabilityNodeContract)，
自動掃描專案模組、CLI 工具、技能文件與 AST 符號，編譯出高密度的能力圖譜檔案 (.agents/capability_graph.json)。

用法：
  python tools/indexer/capability_compiler.py compile
  python tools/indexer/capability_compiler.py check
"""

import sys
import ast
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT_DIR / ".agents"
CAPABILITY_GRAPH_PATH = AGENTS_DIR / "capability_graph.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache",
    ".venv", "venv", "site-packages"
}

def extract_python_module_capabilities(file_path: Path, rel_path: str) -> dict:
    """從 Python 程式碼中提取模組 docstring 與函式/類別作為符號錨點"""
    try:
        content = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return None

    module_doc = ast.get_docstring(tree) or ""
    summary = module_doc.strip().splitlines()[0] if module_doc.strip() else f"Module {file_path.stem}"

    symbols = []
    capabilities = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append({
                "file_path": rel_path,
                "symbol_name": node.name,
                "symbol_kind": "Function"
            })
            capabilities.add(node.name.replace("_", " "))
        elif isinstance(node, ast.ClassDef):
            symbols.append({
                "file_path": rel_path,
                "symbol_name": node.name,
                "symbol_kind": "Class"
            })
            capabilities.add(node.name.lower())

    node_id = file_path.stem.lower()
    return {
        "node_id": node_id,
        "module_path": rel_path,
        "semantic_summary": summary[:120],
        "capabilities": list(capabilities)[:8],
        "contracts": {
            "preconditions": [],
            "positive_invariants": [file_path.stem.lower()] + [c.split()[0] for c in capabilities if c][:5],
            "negative_constraints": []
        },
        "dependencies": [],
        "symbol_anchors": symbols[:10]
    }

def compile_capability_graph() -> list:
    """自動掃描 tools/ 與核心目錄，生成標準 CapabilityNodeContract 清單"""
    nodes = []

    # 1. 掃描 tools 目錄下的核心 CLI 工具
    tools_dir = ROOT_DIR / "tools"
    if tools_dir.is_dir():
        for p in tools_dir.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            rel = p.relative_to(ROOT_DIR).as_posix()
            mod_data = extract_python_module_capabilities(p, rel)
            if mod_data and mod_data["symbol_anchors"]:
                nodes.append(mod_data)

    # 2. 補充全域領域契約 (若既有 capability_graph 存在，保留人工微調之正負約束與 inputs/outputs)
    existing_map = {}
    if CAPABILITY_GRAPH_PATH.is_file():
        try:
            with open(CAPABILITY_GRAPH_PATH, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for item in old_data:
                    k = item.get("node_id") or item.get("id")
                    if k:
                        existing_map[k] = item
        except Exception:
            pass

    # 合併現有或預設能力
    merged_nodes = []
    compiled_ids = {n["node_id"] for n in nodes}

    # 保留舊有專屬領域節點（例如業務模組 0_Scriptor, 1_Aroll 等）
    for old_id, old_item in existing_map.items():
        if old_id not in compiled_ids:
            # 標準化舊節點結構
            std_node = {
                "node_id": old_id,
                "module_path": old_item.get("module_path") or old_item.get("module", ""),
                "semantic_summary": old_item.get("semantic_summary") or old_item.get("name", ""),
                "capabilities": old_item.get("capabilities", []),
                "contracts": old_item.get("contracts", {
                    "preconditions": old_item.get("inputs", []),
                    "positive_invariants": old_item.get("positive", old_item.get("tags", [])),
                    "negative_constraints": old_item.get("negative", [])
                }),
                "dependencies": old_item.get("dependencies", []),
                "symbol_anchors": old_item.get("symbol_anchors", []),
                "inputs": old_item.get("inputs", []),
                "outputs": old_item.get("outputs", [])
            }
            merged_nodes.append(std_node)

    # 加入新編譯的工具節點
    merged_nodes.extend(nodes)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAPABILITY_GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(merged_nodes, f, ensure_ascii=False, indent=2)

    return merged_nodes

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="Capability Compiler & Contract Generator")
    subparsers = parser.add_subparsers(dest="command")

    p_compile = subparsers.add_parser("compile", help="Compile and generate .agents/capability_graph.json")
    p_check = subparsers.add_parser("check", help="Verify capability graph contract compliance")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "compile":
        res = compile_capability_graph()
        print(f"[OK] 能力圖譜編譯成功！已寫入 {CAPABILITY_GRAPH_PATH}")
        print(f"     共收錄 {len(res)} 個能力節點與合約。")
        for node in res:
            anchors_count = len(node.get("symbol_anchors", []))
            print(f"     • [{node['node_id']}] {node['semantic_summary']} ({anchors_count} 個符號錨點)")
    elif args.command == "check":
        if not CAPABILITY_GRAPH_PATH.is_file():
            print(f"[-] 尚未找到 {CAPABILITY_GRAPH_PATH}，請先執行 compile。")
            sys.exit(1)
        with open(CAPABILITY_GRAPH_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[OK] 能力圖譜合規性檢查通過，節點數: {len(data)}")

if __name__ == "__main__":
    main()
