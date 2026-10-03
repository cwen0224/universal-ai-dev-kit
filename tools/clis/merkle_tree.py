#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT Merkle Tree & Incremental Change Detector
- 為專案檔案計算 SHA-256 雜湊樹
- 支援迅速比對與秒級變更感知，提供增量索引基礎
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
MERKLE_CACHE_FILE = CACHE_DIR / "merkle_tree.json"

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp", ".cache"
}

def hash_file(file_path: Path) -> str:
    """計算單一檔案的 SHA-256 雜湊"""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def build_tree(current_dir: Path) -> dict:
    """遞迴建立目錄樹的 Merkle 結構"""
    node = {
        "name": current_dir.name or "/",
        "type": "dir",
        "hash": "",
        "children": {}
    }
    
    child_hashes = []
    
    try:
        entries = sorted(list(current_dir.iterdir()), key=lambda x: x.name)
    except PermissionError:
        return node

    for entry in entries:
        if entry.name in IGNORE_DIRS or entry.name.startswith("."):
            continue
            
        if entry.is_dir():
            child_node = build_tree(entry)
            node["children"][entry.name] = child_node
            child_hashes.append(child_node["hash"])
        elif entry.is_file():
            f_hash = hash_file(entry)
            node["children"][entry.name] = {
                "name": entry.name,
                "type": "file",
                "hash": f_hash,
                "size": entry.stat().st_size,
                "mtime": entry.stat().st_mtime
            }
            child_hashes.append(f_hash)

    # 目錄節點雜湊由其所有子節點的雜湊串接後計算
    h = hashlib.sha256()
    for ch in sorted(child_hashes):
        h.update(ch.encode("utf-8"))
    node["hash"] = h.hexdigest()
    
    return node

def get_changed_files(old_node: dict, new_node: dict, current_path="") -> list:
    """比對兩個 Merkle Tree 節點，精準找出更動、新增或刪除的檔案路徑"""
    changes = []
    
    if old_node.get("hash") == new_node.get("hash"):
        return changes  # 雜湊相同表示內容完全無異動，秒級剪枝！

    old_children = old_node.get("children", {})
    new_children = new_node.get("children", {})
    
    all_keys = set(old_children.keys()) | set(new_children.keys())
    
    for k in sorted(all_keys):
        sub_path = f"{current_path}/{k}" if current_path else k
        if k not in old_children:
            changes.append({"status": "added", "path": sub_path})
        elif k not in new_children:
            changes.append({"status": "deleted", "path": sub_path})
        else:
            old_c = old_children[k]
            new_c = new_children[k]
            if old_c.get("hash") != new_c.get("hash"):
                if old_c.get("type") == "file" or new_c.get("type") == "file":
                    changes.append({"status": "modified", "path": sub_path})
                else:
                    changes.extend(get_changed_files(old_c, new_c, sub_path))
                    
    return changes

def sync_merkle():
    """執行 Merkle Tree 同步並回傳變更列表"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    old_tree = {}
    if MERKLE_CACHE_FILE.exists():
        try:
            with open(MERKLE_CACHE_FILE, "r", encoding="utf-8") as f:
                old_tree = json.load(f)
        except Exception:
            old_tree = {}
            
    new_tree = build_tree(ROOT_DIR)
    
    if old_tree:
        diff = get_changed_files(old_tree, new_tree)
    else:
        diff = [{"status": "initial", "path": "全專案首次建立快取"}]
        
    with open(MERKLE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_tree, f, ensure_ascii=False, indent=2)
        
    return new_tree["hash"], diff

def main():
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
    root_hash, diff = sync_merkle()
    print(f"🌳 Merkle Tree 根雜湊: {root_hash[:16]}...")
    if not diff:
        print("✨ 程式碼庫與上次快取完全一致，無任何檔案異動 (0 files changed)")
    else:
        print(f"🔄 偵測到 {len(diff)} 項異動：")
        for d in diff[:20]:
            print(f"  [{d['status'].upper():<8}] {d['path']}")
        if len(diff) > 20:
            print(f"  ... 以及其他 {len(diff) - 20} 項檔案")

if __name__ == "__main__":
    main()
