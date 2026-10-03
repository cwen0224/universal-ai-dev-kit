#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q-Index Information Gain Router & Navigation Engine (Akinator-style)
解決「當 AI 不知道要找什麼時，如何以最大資訊增益逐步二分收斂候選空間」。

核心設計：
1. 候選能力具備 tags, positive, negative, inputs, outputs, actions, module
2. 每次以決定性演算法（二分法 / 熵增益）計算出最能平均切分候選集合的問題
3. 支援狀態維度過濾（artifact_state, problem_state）
4. 記錄檢索遙測與反饋（telemetry），供自我進化

用法：
  # 互動式或非互動式診斷導航
  python tools/indexer/q_index.py route --intent "字幕"
  python tools/indexer/q_index.py route --state "rendered_video" --problem "timing_misalignment"
  python tools/indexer/q_index.py next-question --candidates "0_Scriptor,3_Caption,4_Music"
  python tools/indexer/q_index.py feedback --query "字幕時間不對" --selected "3_Caption" --success true
"""

import sys
import json
import math
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / ".cache"
CAPABILITY_GRAPH_FILE = ROOT_DIR / ".agents" / "capability_graph.json"
TELEMETRY_FILE = CACHE_DIR / "retrieval_telemetry.jsonl"

# 預設通用能力圖定義（可由 offline Index Curator 擴充）
DEFAULT_CAPABILITIES = [
    {
        "id": "script_writing",
        "module": "0_Scriptor",
        "name": "劇本與講稿生成",
        "tags": ["script", "text", "story", "copywriting", "prompter"],
        "positive": ["writing", "narrative", "script", "structuring"],
        "negative": ["audio", "video", "render", "music", "animation"],
        "inputs": ["topic", "raw_notes"],
        "outputs": ["script_json", "prompter_html"],
        "actions": ["write", "refactor", "segment"]
    },
    {
        "id": "host_performance",
        "module": "1_Aroll",
        "name": "Live2D 主播演繹與運鏡",
        "tags": ["live2d", "character", "expression", "motion", "camera", "avatar"],
        "positive": ["live2d", "motion", "expression", "camera", "avatar"],
        "negative": ["bgm", "soundtrack", "subtitle_text", "script_draft"],
        "inputs": ["script_json", "audio_voice"],
        "outputs": ["aroll_frames", "rendered_aroll_video"],
        "actions": ["animate", "track", "render_host"]
    },
    {
        "id": "broll_footage",
        "module": "2_Broll",
        "name": "視覺空鏡與動態素材",
        "tags": ["stock", "video", "ken_burns", "hud", "overlay", "broll"],
        "positive": ["broll", "footage", "stock", "visual_transition"],
        "negative": ["voice_synthesis", "music_composition", "subtitle_timing"],
        "inputs": ["keywords", "script_context"],
        "outputs": ["broll_video", "hud_overlay"],
        "actions": ["fetch_stock", "pan_zoom", "render_broll"]
    },
    {
        "id": "caption_titlecards",
        "module": "3_Caption",
        "name": "動態大字報與字幕時間軸",
        "tags": ["subtitle", "caption", "title_card", "timing", "srt", "text_overlay"],
        "positive": ["subtitle", "srt", "caption", "title_card", "timing_alignment"],
        "negative": ["bgm", "sfx", "character_motion", "script_creation"],
        "inputs": ["transcript", "timestamps"],
        "outputs": ["subtitle_track", "rendered_titlecards"],
        "actions": ["generate_srt", "render_cards", "sync_timing"]
    },
    {
        "id": "music_sound_direction",
        "module": "4_Music",
        "name": "聲音敘事與配樂導演",
        "tags": ["music", "bgm", "sfx", "silence", "audio", "narrative_audio"],
        "positive": ["bgm", "sfx", "audio_mood", "silence", "volume_envelope"],
        "negative": ["subtitle_rendering", "live2d", "video_compositing"],
        "inputs": ["narrative_state", "duration"],
        "outputs": ["audio_timeline", "master_audio"],
        "actions": ["compose_timeline", "mix", "ducking"]
    },
    {
        "id": "timeline_editor",
        "module": "6_Editor",
        "name": "主時間軸多軌合成與剪輯",
        "tags": ["editor", "timeline", "mux", "composite", "export_video"],
        "positive": ["timeline_assembly", "multi_track_mix", "export", "cut"],
        "negative": ["scriptwriting", "illustration_drawing"],
        "inputs": ["aroll_video", "broll_video", "audio_timeline", "subtitle_track"],
        "outputs": ["final_video_mp4"],
        "actions": ["assemble", "cut", "encode"]
    }
]

def load_capabilities():
    if CAPABILITY_GRAPH_FILE.is_file():
        try:
            with open(CAPABILITY_GRAPH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CAPABILITIES

def calculate_information_gain_questions(candidates):
    """
    確定性資訊增益選題：
    找出在當前候選群中，回答「是/否」能最接近 50/50 分割候選集合的特徵（Feature/Tag/Input/Output）
    """
    total = len(candidates)
    if total <= 1:
        return []

    # 統計所有出現過的 tags, inputs, outputs, actions
    features = {}
    for c in candidates:
        all_tags = set(c.get("tags", []) + c.get("positive", []) + c.get("inputs", []) + c.get("outputs", []))
        for t in all_tags:
            features[t] = features.get(t, 0) + 1

    # 評估每個特徵的分割均衡度 (目標是 count 越接近 total / 2 越好)
    half = total / 2.0
    scored_features = []
    for feat, count in features.items():
        if count == 0 or count == total:
            continue # 無法切分任何項目
        # 分割分數：越接近 half 分數越高 (差距越小)
        split_diff = abs(count - half)
        scored_features.append({
            "feature": feat,
            "match_count": count,
            "split_ratio": f"{count}/{total - count}",
            "distance_to_perfect": split_diff,
            "question": f"您的任務是否直接關聯或產出 [{feat}]？"
        })

    scored_features.sort(key=lambda x: x["distance_to_perfect"])
    return scored_features[:5]

def route_intent(intent=None, artifact_state=None, problem_state=None):
    capabilities = load_capabilities()
    candidates = list(capabilities)

    # 1. 意圖粗篩 (含負向排除)
    if intent:
        q = intent.lower()
        survivors = []
        for c in candidates:
            # 負向明確排除
            if any(neg in q for neg in c.get("negative", [])):
                continue
            # 正向或標籤匹配
            matched = any(pos in q for pos in c.get("positive", [])) or \
                      any(t in q for t in c.get("tags", [])) or \
                      (q in c["name"].lower()) or (q in c["module"].lower())
            if matched:
                survivors.append(c)
        if survivors:
            candidates = survivors

    # 2. 產物狀態過濾
    if artifact_state:
        art = artifact_state.lower()
        candidates = [c for c in candidates if any(art in inp or art in out for inp in c.get("inputs", []) for out in c.get("outputs", []))] or candidates

    # 3. 推薦最佳切分問題
    next_questions = calculate_information_gain_questions(candidates)

    return {
        "candidate_count": len(candidates),
        "candidates": [{"id": c["id"], "module": c["module"], "name": c["name"]} for c in candidates],
        "top_split_questions": next_questions
    }

def record_telemetry(query, route_path, selected, success, correct_target=None):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "query": query,
        "route": route_path,
        "selected": selected,
        "success": bool(success),
        "correct_target": correct_target
    }
    with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[OK] Telemetry recorded for query: '{query}'")

def main():
    parser = argparse.ArgumentParser(description="Q-Index Information Gain Router & Navigation Engine")
    subparsers = parser.add_subparsers(dest="command")

    # route command
    p_route = subparsers.add_parser("route", help="Route user intent to candidate capabilities")
    p_route.add_argument("-i", "--intent", help="Task intent description")
    p_route.add_argument("-s", "--state", help="Current artifact state (e.g. transcript, rendered_video)")
    p_route.add_argument("-p", "--problem", help="Problem state (e.g. timing_misalignment)")

    # feedback command
    p_fb = subparsers.add_parser("feedback", help="Record retrieval telemetry feedback")
    p_fb.add_argument("--query", required=True, help="Original query")
    p_fb.add_argument("--route", nargs="*", default=[], help="Route path")
    p_fb.add_argument("--selected", required=True, help="Selected module or file")
    p_fb.add_argument("--success", type=lambda x: x.lower() == 'true', required=True, help="true/false")
    p_fb.add_argument("--correct-target", help="If failed, specify the correct target")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "route":
        res = route_intent(args.intent, args.state, args.problem)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "feedback":
        record_telemetry(args.query, args.route, args.selected, args.success, args.correct_target)

if __name__ == "__main__":
    main()
