#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Preferences & Memory CLI
用於管理 AI 代理人與使用者偏好日誌（全域與專案雙層作用域），支援階層式讀取、覆蓋與寫入。

用法範例：
  # 查詢合併後的有效偏好（支援點記法 key 查詢或模組過濾）
  python tools/indexer/user_pref.py get
  python tools/indexer/user_pref.py get general.language
  python tools/indexer/user_pref.py get coding_standards

  # 寫入專案偏好（預設為 project 作用域）
  python tools/indexer/user_pref.py set coding_standards.indent_spaces 2
  python tools/indexer/user_pref.py set domain_glossary.A-Roll "主講人虛擬主播片段"

  # 寫入全域偏好
  python tools/indexer/user_pref.py set --scope global general.language "zh-TW"

  # 列出儲存路徑與狀態
  python tools/indexer/user_pref.py info
"""

import sys
import json
import argparse
from pathlib import Path

# 專案根目錄與偏好檔案路徑
ROOT_DIR = Path(__file__).resolve().parents[2]
PROJECT_PREF_PATH = ROOT_DIR / ".agents" / "user_preferences.json"
GLOBAL_PREF_PATH = Path.home() / ".config" / "ai_toolkit" / "user_preferences.json"

DEFAULT_PREFERENCES = {
    "version": "1.0",
    "general": {
        "language": "zh-TW",
        "output_style": "concise"
    },
    "coding_standards": {
        "indent_spaces": 2,
        "forbidden_packages": [],
        "test_framework": "pytest"
    },
    "git_preferences": {
        "commit_prefix_emoji": False,
        "auto_stage_untracked": False
    },
    "domain_glossary": {}
}

def deep_merge(base: dict, override: dict) -> dict:
    """遞迴合併字典，override 權重高於 base"""
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged

def load_json_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to load preferences from {path}: {e}\n")
        return {}

def save_json_file(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_nested_key(data: dict, key_path: str):
    tokens = key_path.split(".")
    curr = data
    for token in tokens:
        if isinstance(curr, dict) and token in curr:
            curr = curr[token]
        else:
            return None
    return curr

def set_nested_key(data: dict, key_path: str, value):
    tokens = key_path.split(".")
    curr = data
    for token in tokens[:-1]:
        if token not in curr or not isinstance(curr[token], dict):
            curr[token] = {}
        curr = curr[token]
    curr[tokens[-1]] = value

def parse_value(raw_val: str):
    """嘗試轉換布林值、數值或維持字串"""
    lower = raw_val.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null":
        return None
    try:
        if "." in raw_val:
            return float(raw_val)
        return int(raw_val)
    except ValueError:
        pass
    # 嘗試解析 JSON 陣列或物件
    if (raw_val.startswith("[") and raw_val.endswith("]")) or (raw_val.startswith("{") and raw_val.endswith("}")):
        try:
            return json.loads(raw_val)
        except json.JSONDecodeError:
            pass
    return raw_val

def get_effective_preferences() -> dict:
    """計算最終偏好：預設值 -> 全域偏好 -> 專案偏好"""
    res = dict(DEFAULT_PREFERENCES)
    global_pref = load_json_file(GLOBAL_PREF_PATH)
    if global_pref:
        res = deep_merge(res, global_pref)
    project_pref = load_json_file(PROJECT_PREF_PATH)
    if project_pref:
        res = deep_merge(res, project_pref)
    return res

def cmd_get(args):
    effective = get_effective_preferences()
    if args.key:
        val = get_nested_key(effective, args.key)
        if val is None:
            sys.stderr.write(f"[INFO] Key '{args.key}' not found in preferences.\n")
            sys.exit(1)
        if isinstance(val, (dict, list)):
            print(json.dumps(val, ensure_ascii=False, indent=2))
        else:
            print(val)
    else:
        print(json.dumps(effective, ensure_ascii=False, indent=2))

def cmd_set(args):
    target_path = GLOBAL_PREF_PATH if args.scope == "global" else PROJECT_PREF_PATH
    data = load_json_file(target_path)
    if not data:
        data = {"version": "1.0"}
    
    parsed_val = parse_value(args.value)
    set_nested_key(data, args.key, parsed_val)
    save_json_file(target_path, data)
    print(f"[OK] Successfully updated ({args.scope}): {args.key} = {json.dumps(parsed_val, ensure_ascii=False)}")

def cmd_info(args):
    print("=== User Preferences & Memory System Info ===")
    print(f"Project Scope Path : {PROJECT_PREF_PATH}")
    print(f"  Exists           : {PROJECT_PREF_PATH.is_file()}")
    print(f"Global Scope Path  : {GLOBAL_PREF_PATH}")
    print(f"  Exists           : {GLOBAL_PREF_PATH.is_file()}")
    print("\nResolution Priority:")
    print("  CLI Flags > Project Preference > Global Preference > System Defaults")

def main():
    parser = argparse.ArgumentParser(description="User Preferences & Memory CLI for AI Agents & Humans")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # get command
    p_get = subparsers.add_parser("get", help="Get effective preferences or specific key")
    p_get.add_argument("key", nargs="?", default=None, help="Key path in dot notation (e.g. general.language, coding_standards)")

    # set command
    p_set = subparsers.add_parser("set", help="Set preference key in project or global scope")
    p_set.add_argument("key", help="Key path in dot notation (e.g. coding_standards.indent_spaces)")
    p_set.add_argument("value", help="Value to set (supports bool, int, float, json, string)")
    p_set.add_argument("--scope", choices=["project", "global"], default="project", help="Target scope (default: project)")

    # info command
    subparsers.add_parser("info", help="Display paths and hierarchy info")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "get":
        cmd_get(args)
    elif args.command == "set":
        cmd_set(args)
    elif args.command == "info":
        cmd_info(args)

if __name__ == "__main__":
    main()
