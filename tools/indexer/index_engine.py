#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBOT Indexer Engine
- 解析全專案核心結構與技能清單
- 產出精簡版主 CODEBASE_MAP.md (200~300行) 與各模組子地圖 MODULE_MAP.md
- 產出結構化去重之 SKILLS_MAP.md 與 .agents/skills_registry.json
"""

import os
import sys
import re
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

MODULE_DEFINITIONS = [
    {
        "id": "0_Scriptor",
        "name": "劇本與講稿生成模組 (Scriptwriting & Prompter)",
        "desc": "長篇解說影片講稿撰寫、語意重構、逐字稿分段、台詞節奏審核與 HTML 提詞機排版。",
        "key_entries": [
            ("0_Scriptor/skills", "講稿編劇與審查專用技能群 (script-writer, actor, critic 等)")
        ]
    },
    {
        "id": "1_Aroll",
        "name": "Live2D 虛擬主播演繹與運鏡模組 (Host Performance & A-Roll)",
        "desc": "依據逐字稿情感軌跡排定 Live2D 表情、手勢意圖、PixiJS 渲染管線與反應式相機運鏡。",
        "key_entries": [
            ("1_Aroll/run_aroll_pipeline.js", "A-Roll 主執行流水線"),
            ("1_Aroll/generate_lipsync.js", "唇形同步音訊特徵提取"),
            ("1_Aroll/skills", "Live2D 表情/動作/運鏡導演與批評官規範")
        ]
    },
    {
        "id": "2_Broll",
        "name": "視覺空鏡與動態影片模組 (B-Roll Video & Stock Clips)",
        "desc": "靜態 AI 生成圖 Ken Burns 動態運鏡轉影片、Pexels/Pixabay 圖庫搜尋採購與微距螢幕 HUD 特效。",
        "key_entries": [
            ("2_Broll/skills", "B-Roll 運鏡指南、圖庫採購規範、微距螢幕與引用特效")
        ]
    },
    {
        "id": "3_Caption",
        "name": "動態大字報與字幕渲染模組 (Title Cards & Subtitles)",
        "desc": "自動解析講稿拍點關鍵字，排定動態大字報時間軸並無頭渲染透明 PNG/MOV 字幕軌。",
        "key_entries": [
            ("3_Caption/generate_title_cards_ai.js", "AI 大字報關鍵字產生器"),
            ("3_Caption/render_title_cards.js", "Puppeteer 大字報渲染引擎"),
            ("3_Caption/subtitle_pipeline.js", "字幕時間軸組裝工作流")
        ]
    },
    {
        "id": "4_Music",
        "name": "聲音敘事與配樂導演模組 (Narrative Music & Sound Direction)",
        "desc": "建立「敘事狀態 -> 配樂功能 -> 時間軸」架構，以 Silence 為一級公民，排定 BGM/SFX 軌道。",
        "key_entries": [
            ("4_Music/skills", "聲音導演系統規範、音樂演員與批評官技能")
        ]
    },
    {
        "id": "5_Chat",
        "name": "社群對話框與動態 UI 模組 (Dynamic UI & Social Chats)",
        "desc": "模擬社群動態介面（YouTube 留言區、IG 私訊、推特留言）並無頭錄製為獨立透明影片素材。",
        "key_entries": [
            ("5_Chat/templates/yt_comment.html", "YouTube 留言動畫模板"),
            ("5_Chat/skills", "動態 UI 生成指南")
        ]
    },
    {
        "id": "6_Editor",
        "name": "剪輯工程與時間軸裝配模組 (Video Assembly & NLE Export)",
        "desc": "WhisperX 時間戳精確剪輯、動態規劃 (DP) 語意匹配、多軌視訊與音訊同步與 Premiere 插件支援。",
        "key_entries": [
            ("assemble.js", "根目錄總影片軌道組裝腳本"),
            ("6_Editor/skills", "Whisper 自動剪輯引擎、拆片專家與 Premiere 插件規範")
        ]
    },
    {
        "id": "7_Designer",
        "name": "視覺設計與動態圖表模組 (Motion Design & Infographics)",
        "desc": "高解析參數化 SVG 動態圖表、語意圖表切換狀態精確同步、AI 去背向量化與貼紙邊緣生成。",
        "key_entries": [
            ("7_Designer/skills", "設計師快速單幀迭代、動態 SVG 圖表與語意同步指引")
        ]
    },
    {
        "id": "8_Explainer",
        "name": "棋盤解說與概念圖解模組 (Board Explainer & Dynamic Diagrams)",
        "desc": "長篇大論拆解為分鏡關鍵影格藍圖，微秒級棋子位移、光束導向、對話框與物理碰撞稽查。",
        "key_entries": [
            ("8_Explainer/renderer/board_engine.js", "棋盤動畫核心執行引擎"),
            ("8_Explainer/skills", "棋盤母導演、分鏡執行官與批評官")
        ]
    },
    {
        "id": "9_Nexus",
        "name": "全自動管線指揮總署與審核總監 (Governance & Single Source of Truth)",
        "desc": "半人馬合作準則守護、跨模組 Pipeline 調度執行 (nexus_runner)、母子代理人合規流通與品質把關。",
        "key_entries": [
            ("9_Nexus/nexus_runner.py", "Nexus 核心調度配發器"),
            ("9_Nexus/clean_project_artifacts.py", "專案暫存與產出物清理工具"),
            ("9_Nexus/skills", "全自動管線總指南、半人馬準則、技術/演算法總監規約")
        ]
    },
    {
        "id": "10_Visual",
        "name": "視覺分鏡導演與預覽工作室 (Visual Directing & Preview Studio)",
        "desc": "全片視覺 Scene Graph 時間軸編排、多軌即時預覽 Native Studio、即時音訊播放與效果測試。",
        "key_entries": [
            ("10_Visual/python_preview_studio.py", "Python 原生視覺預覽工作室"),
            ("10_Visual/build_full_visual_project.py", "視覺分鏡全案構建器"),
            ("10_Visual/audio_timeline_engine.py", "多軌音訊預覽引擎")
        ]
    },
    {
        "id": "12_Voice",
        "name": "語音合成與旁白管理模組 (TTS & Voice Studio)",
        "desc": "TTS 旁白生成（Gemini Native / Edge-TTS / ElevenLabs）、情緒 Prompt 調校與字幕音訊毫秒對齊。",
        "key_entries": [
            ("12_Voice/VoiceStudio", "本地語音合成工作室介面與服務"),
            ("12_Voice/skills", "TTS 語音生成指引與字幕音訊工程師")
        ]
    },
    {
        "id": "14_Buyer",
        "name": "視覺素材採購與生成調度官 (Visual Asset Procurement)",
        "desc": "嚴格 4 階層採購降級梯隊 (免費圖庫 API -> 網路搜尋+轉繪重構 -> Gemini 生圖 -> 人工審批清單)。",
        "key_entries": [
            ("14_Buyer/skills", "視覺素材採購總監與 B-Roll 候選清單搜尋")
        ]
    },
    {
        "id": "_pipeline_scripts",
        "name": "流水線全域共用腳本庫 (Global Pipeline Scripts)",
        "desc": "多模組共用之 GAN 表情編排、Whisper 重構、API 呼叫與系統相容性測試工具。",
        "key_entries": [
            ("_pipeline_scripts/gan_expression_director.js", "GAN 表情自動編排器"),
            ("_pipeline_scripts/validate_plan.js", "執行計畫有效性檢驗"),
            ("_pipeline_scripts/gas-cli.js", "Google Apps Script 雲端同步工具")
        ]
    }
]

IGNORE_DIRS = {
    "node_modules", ".git", ".idea", ".vscode", "__pycache__", 
    ".system_generated", "dist", "build", "coverage", "_outputs", "tmp"
}

def parse_skill_file(skill_path: Path):
    """解析 SKILL.md 中的 YAML Frontmatter 或直接 key: value 描述"""
    try:
        content = skill_path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return None

    name = skill_path.parent.name
    desc = ""
    
    # 模式 1: 標準 --- YAML ---
    fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        for line in fm_text.splitlines():
            line = line.strip()
            if line.startswith("name:"):
                n = line.split("name:", 1)[1].strip().strip('"').strip("'")
                if n:
                    name = n
            elif line.startswith("description:"):
                d = line.split("description:", 1)[1].strip().strip('"').strip("'")
                if d and d != ">-":
                    desc = d

    # 模式 2: 開頭直接是 name: / description:
    if not desc:
        lines = content.splitlines()
        for i in range(min(15, len(lines))):
            line = lines[i].strip()
            if line.startswith("name:") and name == skill_path.parent.name:
                n = line.split("name:", 1)[1].strip().strip('"').strip("'")
                if n:
                    name = n
            elif line.startswith("description:"):
                d = line.split("description:", 1)[1].strip().strip('"').strip("'")
                if d and d != ">-":
                    desc = d

    # 模式 3: 若無 description，嘗試抓取 H1/H2 之後的首段說明文字
    if not desc:
        clean_content = content
        if fm_match:
            clean_content = content[fm_match.end():]
        for line in clean_content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---") and not line.startswith(">") and not line.startswith("name:"):
                desc = line[:200]
                break
                
    if not desc:
        desc = "專案內建專業指導原則與執行規範。"

    # 提取目錄層極簡摘要 (15-30字以內)
    summary = desc.split("。")[0].split("，")[0].strip()
    if len(summary) > 30:
        summary = summary[:28] + "..."

    # 提取防誤觸/限制條件 (negative patterns / constraints)
    negatives = []
    for line in content.splitlines():
        line = line.strip()
        if any(kw in line for kw in ["禁止", "嚴禁", "絕對不可", "杜絕", "切勿", "不支援"]):
            clean_rule = re.sub(r"^[-*0-9.\s#]+", "", line).strip()
            if 5 < len(clean_rule) < 80:
                negatives.append(clean_rule)
                if len(negatives) >= 3:
                    break

    return {
        "id": f"urn:skill:{skill_path.parent.name}",
        "name": name,
        "summary": summary,
        "description": desc,
        "path": skill_path.relative_to(ROOT_DIR).as_posix(),
        "dir_name": skill_path.parent.name,
        "triggers": {
            "intent_keywords": [name.replace("-", " "), skill_path.parent.name],
            "negative_patterns": negatives
        }
    }

def collect_all_skills():
    """收集全專案所有 SKILL.md 並進行去重與正規化分類"""
    all_skills = {}
    
    # 優先掃描 .agents/skills (全域標準註冊點)
    global_skills_dir = ROOT_DIR / ".agents" / "skills"
    if global_skills_dir.exists():
        for sp in global_skills_dir.glob("*/SKILL.md"):
            data = parse_skill_file(sp)
            if data:
                all_skills[data["dir_name"]] = data
                all_skills[data["dir_name"]]["is_global"] = True
                
    # 次要掃描各模組內的 skills (子模組複本或獨立 skill)
    for mod in ROOT_DIR.iterdir():
        if mod.is_dir() and mod.name not in IGNORE_DIRS:
            for sp in mod.glob("**/SKILL.md"):
                # 排除 .agents
                if ".agents" in sp.parts:
                    continue
                data = parse_skill_file(sp)
                if not data:
                    continue
                dir_n = data["dir_name"]
                if dir_n not in all_skills:
                    data["is_global"] = False
                    all_skills[dir_n] = data
                else:
                    # 記錄模組在地路徑
                    if "local_paths" not in all_skills[dir_n]:
                        all_skills[dir_n]["local_paths"] = []
                    all_skills[dir_n]["local_paths"].append(data["path"])

    # 賦予各 Skill 推薦的工作流模組分類
    categorized = {m["id"]: [] for m in MODULE_DEFINITIONS}
    categorized["_Global"] = []

    for name, s in all_skills.items():
        matched_mod = None
        # 依據路徑判斷
        path_str = s["path"]
        for m in MODULE_DEFINITIONS:
            if m["id"] in path_str:
                matched_mod = m["id"]
                break
            # 檢查 local_paths
            for lp in s.get("local_paths", []):
                if m["id"] in lp:
                    matched_mod = m["id"]
                    break
            if matched_mod:
                break
                
        # 依據關鍵字推測
        if not matched_mod:
            n = s["name"].lower()
            if any(k in n for k in ["script", "writer", "teleprompter"]):
                matched_mod = "0_Scriptor"
            elif any(k in n for k in ["live2d", "aroll", "camera", "gesture", "expression"]):
                matched_mod = "1_Aroll"
            elif any(k in n for k in ["broll", "macro", "green-screen", "cinematographer"]):
                matched_mod = "2_Broll"
            elif any(k in n for k in ["caption", "subtitle", "title"]):
                matched_mod = "3_Caption"
            elif any(k in n for k in ["music", "sound", "audio"]):
                matched_mod = "4_Music"
            elif any(k in n for k in ["chat", "dynamic-ui"]):
                matched_mod = "5_Chat"
            elif any(k in n for k in ["editor", "whisper", "premiere", "shot-breakdown"]):
                matched_mod = "6_Editor"
            elif any(k in n for k in ["designer", "svg", "chart", "matting"]):
                matched_mod = "7_Designer"
            elif any(k in n for k in ["explainer", "board"]):
                matched_mod = "8_Explainer"
            elif any(k in n for k in ["nexus", "orchestrator", "centaur", "pipeline", "team-leader"]):
                matched_mod = "9_Nexus"
            elif any(k in n for k in ["visual", "scene-director"]):
                matched_mod = "10_Visual"
            elif any(k in n for k in ["voice", "tts"]):
                matched_mod = "12_Voice"
            elif any(k in n for k in ["buyer"]):
                matched_mod = "14_Buyer"
            else:
                matched_mod = "_Global"
                
        s["category"] = matched_mod
        if matched_mod in categorized:
            categorized[matched_mod].append(s)
        else:
            categorized["_Global"].append(s)

    return all_skills, categorized

def generate_skills_map(all_skills, categorized):
    """產生去除冗餘、易查閱的 SKILLS_MAP.md 與 JSON Registry"""
    json_path = ROOT_DIR / ".agents" / "skills_registry.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_skills, f, ensure_ascii=False, indent=2)

    lines = [
        "# 🧭 ROBOT 專業技能總導航地圖 (Skills Map)",
        "",
        "> **Token 節省與調用規範**：",
        "> 1. 本檔案由 `tools/indexer/index_engine.py` 自動維護與去重，記錄專案所有正式註冊之技能規格。",
        "> 2. 查閱技能時**嚴禁發動全專案搜尋**，請依據下方模組分類或使用指令 `python tools/indexer/find_skill.py <關鍵字>` 精準調用。",
        f"> 3. 目前全專案收錄 **{len(all_skills)} 個精煉專業技能**。",
        "",
        "---",
        "",
        "## 📑 模組目錄快速跳轉",
        ""
    ]

    for m in MODULE_DEFINITIONS:
        count = len(categorized.get(m["id"], []))
        lines.append(f"- [{m['id']}：{m['name']}](#{m['id'].lower()}) — `{count} 個技能`")
    lines.append(f"- [全域共用技能與基礎設施 (_Global)](#_global) — `{len(categorized.get('_Global', []))} 個技能`")
    lines.append("\n---\n")

    for m in MODULE_DEFINITIONS:
        sks = categorized.get(m["id"], [])
        if not sks:
            continue
        lines.append(f"### <a id=\"{m['id'].lower()}\"></a>🎯 {m['id']}：{m['name']}")
        lines.append(f"*{m['desc']}*\n")
        lines.append("| 技能名稱 | 核心職責與使用時機 | 註冊路徑 (Skill Path) |")
        lines.append("|---|---|---|")
        for s in sorted(sks, key=lambda x: x["name"]):
            p = s["path"]
            lines.append(f"| **{s['name']}** | {s['description']} | [`{p}`](file:///{ROOT_DIR.as_posix()}/{p}) |")
        lines.append("")

    global_sks = categorized.get("_Global", [])
    if global_sks:
        lines.append("### <a id=\"_global\"></a>🌐 全域共用技能與基礎設施 (_Global)")
        lines.append("| 技能名稱 | 核心職責與使用時機 | 註冊路徑 (Skill Path) |")
        lines.append("|---|---|---|")
        for s in sorted(global_sks, key=lambda x: x["name"]):
            p = s["path"]
            lines.append(f"| **{s['name']}** | {s['description']} | [`{p}`](file:///{ROOT_DIR.as_posix()}/{p}) |")
        lines.append("")

    skills_map_path = ROOT_DIR / "SKILLS_MAP.md"
    skills_map_path.write_text("\n".join(lines), encoding="utf-8")
    return skills_map_path, json_path

def generate_codebase_maps(all_skills):
    """
    產生雙層程式架構索引：
    1. 根目錄主地圖 CODEBASE_MAP.md (精簡 200~300 行)
    2. 各核心模組詳細清單 <Module>/MODULE_MAP.md
    """
    main_lines = [
        "# 🗺️ ROBOT 全系統架構導航地圖 (Master Codebase Map)",
        "",
        "> **Token 節約核心準則 (Lean Vibe Coding)**：",
        "> 本專案由多個功能獨立的自動化管道模組構成。進行跨模組開發時，**僅需閱讀本總圖定位目標**；",
        "> 若需深入特定模組細節，直接前往該模組專屬之 `MODULE_MAP.md` 或入口檔案，**嚴禁發動全專案遞迴搜尋**。",
        "",
        "---",
        "",
        "## 🏗️ 核心管線資料流向 (Pipeline Dataflow)",
        "```mermaid",
        "graph LR",
        "  0[0_Scriptor 講稿] --> 12[12_Voice TTS 旁白]",
        "  12 --> 1[1_Aroll 主播表演]",
        "  12 --> 2[2_Broll 空鏡動態]",
        "  12 --> 3[3_Caption 大字報字幕]",
        "  12 --> 4[4_Music 敘事配樂]",
        "  12 --> 7[7_Designer 圖表設計]",
        "  12 --> 8[8_Explainer 棋盤動畫]",
        "  1 & 2 & 3 & 4 & 7 & 8 --> 10[10_Visual 分鏡預覽]",
        "  10 --> 6[6_Editor 剪輯組裝]",
        "  9[9_Nexus 調度守護] -.-> 0 & 1 & 2 & 3 & 4 & 6 & 7 & 8 & 10",
        "  14[14_Buyer 素材採購] -.-> 2 & 7",
        "```",
        "",
        "---",
        "",
        "## 🧭 核心模組職責與關鍵入口 (Modules Overview)",
        "",
        "| 模組代號 | 模組名稱與職責摘要 | 核心入口腳本與技能 | 詳細模組地圖 |",
        "|---|---|---|:---:|",
    ]

    for m in MODULE_DEFINITIONS:
        mod_id = m["id"]
        mod_name = m["name"].split("(")[0].strip()
        mod_dir = ROOT_DIR / mod_id
        
        # 整理關鍵入口
        entries_str = "<br>".join([f"• [`{e[0]}`](file:///{ROOT_DIR.as_posix()}/{e[0]})" for e in m["key_entries"]])
        map_link = f"[`{mod_id}/MODULE_MAP.md`](file:///{ROOT_DIR.as_posix()}/{mod_id}/MODULE_MAP.md)" if mod_dir.exists() and mod_dir.is_dir() else "—"
        
        main_lines.append(f"| **{mod_id}** | **{mod_name}**<br>{m['desc']} | {entries_str} | {map_link} |")

    main_lines.extend([
        "",
        "---",
        "",
        "## ⚡ 常用快捷指令與工具",
        "- **更新全專案索引**：`python tools/indexer/index_engine.py`",
        "- **查詢特定技能**：`python tools/indexer/find_skill.py <關鍵字>`",
        "- **定位程式檔案**：`python tools/indexer/find_code.py <檔名或模組>`",
        "- **查閱完整技能庫**：參閱 [`SKILLS_MAP.md`](file:///{ROOT_DIR.as_posix()}/SKILLS_MAP.md)",
        ""
    ])

    root_map_path = ROOT_DIR / "CODEBASE_MAP.md"
    root_map_path.write_text("\n".join(main_lines), encoding="utf-8")

    # 為各模組產生 MODULE_MAP.md
    for m in MODULE_DEFINITIONS:
        mod_id = m["id"]
        mod_dir = ROOT_DIR / mod_id
        if not mod_dir.exists() or not mod_dir.is_dir():
            continue

        # 收集該模組下的主要檔案 (深入 2 層)
        files_list = []
        for p in mod_dir.rglob("*"):
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            if p.is_file():
                rel = p.relative_to(mod_dir)
                if len(rel.parts) <= 3:  # 深度不超過 3
                    files_list.append(rel)

        sub_lines = [
            f"# 🗺️ {mod_id} 模組詳細地圖 (Module Detail Map)",
            "",
            f"> **模組名稱**：{m['name']}  ",
            f"> **模組職責**：{m['desc']}  ",
            f"> **返回全系統總地圖**：[`CODEBASE_MAP.md`](file:///{ROOT_DIR.as_posix()}/CODEBASE_MAP.md)",
            "",
            "---",
            "",
            "## 📁 核心檔案與腳本清單",
            "",
            "| 檔案路徑 | 類型 | 實體連結 |",
            "|---|---|---|",
        ]

        for rf in sorted(files_list):
            ext = rf.suffix.lower() if rf.suffix else "file"
            sub_lines.append(f"| `{rf.as_posix()}` | `{ext}` | [`開啟`](file:///{mod_dir.as_posix()}/{rf.as_posix()}) |")

        sub_lines.append("")
        sub_map_path = mod_dir / "MODULE_MAP.md"
        sub_map_path.write_text("\n".join(sub_lines), encoding="utf-8")

    return root_map_path

def run_all():
    print(f"[*] ROBOT Index Engine 啟動，目標根目錄: {ROOT_DIR}")
    skills, categorized = collect_all_skills()
    print(f"[+] 成功掃描與整理 {len(skills)} 個技能")
    
    s_map, s_json = generate_skills_map(skills, categorized)
    print(f"[+] 產出技能索引地圖: {s_map}")
    print(f"[+] 產出結構化 Registry: {s_json}")
    
    c_map = generate_codebase_maps(skills)
    print("[+] 產出精簡版主程式地圖: " + str(c_map))
    print("[OK] 雙層架構與索引庫同步完畢！")

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    run_all()
