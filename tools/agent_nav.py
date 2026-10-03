#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Unified Navigation Portal (agent_nav)
為 AI 代理人與開發者提供「單一進入點 (Single Entrypoint)」命令列工具，
聚合 Q-Index 導航、CLIS 符號定位、AST 呼叫鏈分析、能力圖編譯與全域索引更新。

常用指令：
  # 1. 意圖導航 (Q-Index Gen-2: 共形置信度評估與診斷探針)
  python tools/agent_nav.py route "字幕時間對不上"

  # 2. 符號檢索與結構切片 (CLIS)
  python tools/agent_nav.py symbol <函式/類別名>
  python tools/agent_nav.py struct <檔案路徑>
  python tools/agent_nav.py read <檔案路徑> -s <函式名>

  # 3. 雙向呼叫鏈分析 (Call Graph)
  python tools/agent_nav.py callers <函式名>
  python tools/agent_nav.py callees <檔案路徑> <函式名>
  python tools/agent_nav.py trace <函式名>

  # 4. 技能員工 ↔ 辦公工具雙向查詢 (Skill & Tool Link)
  python tools/agent_nav.py skill <技能名稱>       # 查看員工使用的工具代碼
  python tools/agent_nav.py tool <程式檔案路徑>    # 查看該代碼受哪些技能規範管轄

  # 5. 快取檔案查詢 (File Index)
  python tools/agent_nav.py file <檔名或模組關鍵字>

  # 6. 偏好設定與記憶管理 (User Preferences)
  python tools/agent_nav.py pref get
  python tools/agent_nav.py pref set <key> <value>

  # 7. 一鍵全系統增量索引構建 (Reindex All)
  python tools/agent_nav.py reindex
"""

import sys
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT_DIR / "tools"

def run_script(script_rel_path, args):
    script_path = ROOT_DIR / script_rel_path
    cmd = [sys.executable, str(script_path)] + args
    return subprocess.run(cmd).returncode

def cmd_reindex():
    print("🔄 [agent_nav] 開始執行全專案認知導航與索引增量更新...\n")
    
    # 1. 更新檔案快取索引
    print("1️⃣ [1/5] 構建檔案快取索引 (File Index)...")
    run_script("tools/indexer/find_code.py", ["--reindex"])
    
    # 2. 更新 AST 雙向呼叫圖
    print("\n2️⃣ [2/5] 解析 AST 雙向呼叫圖 (Call Graph)...")
    run_script("tools/clis/call_graph.py", ["reindex"])
    
    # 3. 更新技能與程式碼雙向映射
    print("\n3️⃣ [3/5] 構建技能員工與辦公工具雙向地圖 (Skill-Code Linker)...")
    run_script("tools/indexer/skill_code_linker.py", ["--reindex"])
    
    # 4. 自動編譯能力圖譜與符號錨點
    print("\n4️⃣ [4/5] 編譯 Gen-2 能力契約圖譜 (Capability Graph)...")
    run_script("tools/indexer/capability_compiler.py", ["compile"])
    
    # 5. 檢查 Merkle Tree 增量狀態
    print("\n5️⃣ [5/5] 檢查 Merkle Tree 增量狀態...")
    run_script("tools/clis/merkle_tree.py", ["--diff"])
    
    print("\n✅ [agent_nav] 全系統索引與導航能力庫已全面更新完成！")

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="Agent Unified Navigation Portal (agent_nav)")
    subparsers = parser.add_subparsers(dest="command")

    # 1. route
    p_route = subparsers.add_parser("route", help="Route task intent via Gen-2 Q-Index")
    p_route.add_argument("intent", help="Task description or intent")
    p_route.add_argument("-s", "--state", help="Artifact state")

    # 2. symbol
    p_symbol = subparsers.add_parser("symbol", help="Search symbol signature via CLIS")
    p_symbol.add_argument("name", help="Function or class name")

    # 3. struct
    p_struct = subparsers.add_parser("struct", help="Inspect file outline skeleton via CLIS")
    p_struct.add_argument("file_path", help="Relative file path")

    # 4. read
    p_read = subparsers.add_parser("read", help="Scoped read of symbol implementation via CLIS")
    p_read.add_argument("file_path", help="Relative file path")
    p_read.add_argument("-s", "--symbol", help="Specific function/class name")
    p_read.add_argument("-l", "--lines", help="Line range e.g. 50-100")

    # 5. callers
    p_callers = subparsers.add_parser("callers", help="Find who calls this function (Backward slice)")
    p_callers.add_argument("func_name", help="Function name")

    # 6. callees
    p_callees = subparsers.add_parser("callees", help="Find what this function calls (Forward slice)")
    p_callees.add_argument("file_path", help="File path")
    p_callees.add_argument("func_name", help="Function name")

    # 7. trace
    p_trace = subparsers.add_parser("trace", help="Comprehensive call graph trace for symbol")
    p_trace.add_argument("func_name", help="Function name")

    # 8. file
    p_file = subparsers.add_parser("file", help="Fast file lookup via FILE_INDEX cache")
    p_file.add_argument("query", nargs="?", default="", help="Filename or keyword")
    p_file.add_argument("-e", "--ext", help="File extension filter")

    # 9. skill (Skill -> Tools)
    p_skill = subparsers.add_parser("skill", help="Find tools & code used by a skill/worker")
    p_skill.add_argument("name", help="Skill name or keyword")

    # 10. tool (Tool -> Skills)
    p_tool = subparsers.add_parser("tool", help="Find skills/rules governing a code file")
    p_tool.add_argument("path", help="Code file path")

    # 11. pref
    p_pref = subparsers.add_parser("pref", help="Manage user preferences and memory")
    p_pref.add_argument("action", choices=["get", "set", "info"], help="pref action")
    p_pref.add_argument("args", nargs="*", help="Additional arguments for pref")

    # 12. reindex
    subparsers.add_parser("reindex", help="Rebuild all indexes, call graphs and capability contracts")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "route":
        fwd_args = ["route", "-i", args.intent]
        if args.state:
            fwd_args += ["-s", args.state]
        sys.exit(run_script("tools/indexer/q_index.py", fwd_args))

    elif args.command == "symbol":
        sys.exit(run_script("tools/clis/clis_engine.py", ["search", args.name]))

    elif args.command == "struct":
        sys.exit(run_script("tools/clis/clis_engine.py", ["struct", args.file_path]))

    elif args.command == "read":
        fwd_args = ["read", args.file_path]
        if args.symbol:
            fwd_args += ["-s", args.symbol]
        if args.lines:
            fwd_args += ["-l", args.lines]
        sys.exit(run_script("tools/clis/clis_engine.py", fwd_args))

    elif args.command == "callers":
        sys.exit(run_script("tools/clis/call_graph.py", ["callers", args.func_name]))

    elif args.command == "callees":
        sys.exit(run_script("tools/clis/call_graph.py", ["callees", args.file_path, args.func_name]))

    elif args.command == "trace":
        sys.exit(run_script("tools/clis/call_graph.py", ["trace", args.func_name]))

    elif args.command == "file":
        fwd_args = []
        if args.query:
            fwd_args.append(args.query)
        if args.ext:
            fwd_args += ["-e", args.ext]
        sys.exit(run_script("tools/indexer/find_code.py", fwd_args))

    elif args.command == "skill":
        sys.exit(run_script("tools/indexer/skill_code_linker.py", ["-t", args.name]))

    elif args.command == "tool":
        sys.exit(run_script("tools/indexer/skill_code_linker.py", ["-s", args.path]))

    elif args.command == "pref":
        sys.exit(run_script("tools/indexer/user_pref.py", [args.action] + args.args))

    elif args.command == "reindex":
        cmd_reindex()

if __name__ == "__main__":
    main()
