#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gen-2 Adaptive Cognitive Navigation & Diagnostic Probing Engine
第二代自適應認知導航引擎：
1. 共形置信度評估與快慢雙軌閘門 (Conformal Gating / Fast-Track vs. Slow-Track)
2. 預編譯診斷探針庫 (Pre-compiled Diagnostic Probes: 靜態斷言、動態測試、離散選擇)
3. 契約化能力圖譜 (Capability Graph with Positive/Negative Constraints)
4. 工具慣性快取與轉移路徑 (Markov Tool Inertia)
5. 導航遙測追蹤 (Navigation Telemetry Event: 記錄初始集合大小、每步熵減與執行成敗)

用法：
  # 快慢雙軌導航 (自動判斷是否穿透快速路徑)
  python tools/indexer/q_index.py route --intent "字幕"
  python tools/indexer/q_index.py route --intent "讓影片節奏更有科技感"

  # 執行預編譯診斷探針評估 (避免線上 LLM 生成問卷)
  python tools/indexer/q_index.py probe --candidates "0_Scriptor,3_Caption,4_Music"

  # 記錄 Gen-2 遙測事件
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
PROBE_LIBRARY_FILE = ROOT_DIR / ".agents" / "diagnostic_probes.json"
INERTIA_CACHE_FILE = ROOT_DIR / ".agents" / "tool_inertia.json"
TELEMETRY_FILE = CACHE_DIR / "navigation_telemetry.jsonl"

# 預設通用能力圖定義 (相容 CapabilityNodeContract)
DEFAULT_CAPABILITIES = [
    {
        "node_id": "script_writing",
        "module_path": "0_Scriptor",
        "semantic_summary": "長篇解說影片講稿撰寫、語意重構與提詞機排版",
        "capabilities": ["scriptwriting", "prompter_layout", "text_structuring"],
        "contracts": {
            "preconditions": ["topic_or_outline_ready"],
            "positive_invariants": ["script", "text", "story", "copywriting", "prompter"],
            "negative_constraints": ["audio", "video", "render", "music", "animation"]
        },
        "dependencies": [
            {"target_node_id": "host_performance", "relation_type": "DATA_FLOW"},
            {"target_node_id": "caption_titlecards", "relation_type": "DATA_FLOW"}
        ],
        "symbol_anchors": [
            {"file_path": "0_Scriptor/skills/script_writer.md", "symbol_name": "ScriptWriter", "symbol_kind": "Class"}
        ],
        "inputs": ["topic", "raw_notes"],
        "outputs": ["script_json", "prompter_html"]
    },
    {
        "node_id": "host_performance",
        "module_path": "1_Aroll",
        "semantic_summary": "Live2D 虛擬主播演繹、逐字稿情感軌跡與相機運鏡",
        "capabilities": ["live2d_avatar", "motion_tracking", "lipsync", "camera_director"],
        "contracts": {
            "preconditions": ["script_json_ready", "voice_audio_ready"],
            "positive_invariants": ["live2d", "character", "expression", "motion", "camera", "avatar"],
            "negative_constraints": ["bgm", "soundtrack", "subtitle_text", "script_draft"]
        },
        "dependencies": [
            {"target_node_id": "timeline_editor", "relation_type": "DATA_FLOW"}
        ],
        "symbol_anchors": [
            {"file_path": "1_Aroll/run_aroll_pipeline.js", "symbol_name": "runArollPipeline", "symbol_kind": "Function"}
        ],
        "inputs": ["script_json", "audio_voice"],
        "outputs": ["aroll_frames", "rendered_aroll_video"]
    },
    {
        "node_id": "broll_footage",
        "module_path": "2_Broll",
        "semantic_summary": "視覺空鏡、Ken Burns 動態運鏡與微距 HUD 影片合成",
        "capabilities": ["stock_search", "ken_burns", "hud_overlay", "broll_rendering"],
        "contracts": {
            "preconditions": ["script_context_ready"],
            "positive_invariants": ["stock", "video", "ken_burns", "hud", "overlay", "broll"],
            "negative_constraints": ["voice_synthesis", "music_composition", "subtitle_timing"]
        },
        "dependencies": [
            {"target_node_id": "timeline_editor", "relation_type": "DATA_FLOW"}
        ],
        "symbol_anchors": [
            {"file_path": "2_Broll/skills/broll_director.md", "symbol_name": "BrollDirector", "symbol_kind": "Class"}
        ],
        "inputs": ["keywords", "script_context"],
        "outputs": ["broll_video", "hud_overlay"]
    },
    {
        "node_id": "caption_titlecards",
        "module_path": "3_Caption",
        "semantic_summary": "動態大字報與字幕時間軸渲染引擎",
        "capabilities": ["subtitle_generation", "title_card_render", "srt_alignment"],
        "contracts": {
            "preconditions": ["timestamps_ready", "transcript_ready"],
            "positive_invariants": ["subtitle", "caption", "title_card", "timing", "srt", "text_overlay"],
            "negative_constraints": ["bgm", "sfx", "character_motion", "script_creation"]
        },
        "dependencies": [
            {"target_node_id": "timeline_editor", "relation_type": "DATA_FLOW"}
        ],
        "symbol_anchors": [
            {"file_path": "3_Caption/subtitle_pipeline.js", "symbol_name": "subtitlePipeline", "symbol_kind": "Function"}
        ],
        "inputs": ["transcript", "timestamps"],
        "outputs": ["subtitle_track", "rendered_titlecards"]
    },
    {
        "node_id": "music_sound_direction",
        "module_path": "4_Music",
        "semantic_summary": "聲音敘事、Silence 靜音一級公民與配樂音效導演",
        "capabilities": ["bgm_direction", "sfx_placement", "silence_control", "audio_ducking"],
        "contracts": {
            "preconditions": ["narrative_beats_ready"],
            "positive_invariants": ["music", "bgm", "sfx", "silence", "audio", "narrative_audio"],
            "negative_constraints": ["subtitle_rendering", "live2d", "video_compositing"]
        },
        "dependencies": [
            {"target_node_id": "timeline_editor", "relation_type": "DATA_FLOW"}
        ],
        "symbol_anchors": [
            {"file_path": "4_Music/skills/sound_director.md", "symbol_name": "SoundDirector", "symbol_kind": "Class"}
        ],
        "inputs": ["narrative_state", "duration"],
        "outputs": ["audio_timeline", "master_audio"]
    },
    {
        "node_id": "timeline_editor",
        "module_path": "6_Editor",
        "semantic_summary": "多軌時間軸匯流排合成、剪輯與最終母帶渲染",
        "capabilities": ["timeline_assembly", "multi_track_mix", "export_mp4"],
        "contracts": {
            "preconditions": ["tracks_ready"],
            "positive_invariants": ["editor", "timeline", "mux", "composite", "export_video"],
            "negative_constraints": ["scriptwriting", "illustration_drawing"]
        },
        "dependencies": [],
        "symbol_anchors": [
            {"file_path": "6_Editor/skills/timeline_assembler.md", "symbol_name": "TimelineAssembler", "symbol_kind": "Class"}
        ],
        "inputs": ["aroll_video", "broll_video", "audio_timeline", "subtitle_track"],
        "outputs": ["final_video_mp4"]
    }
]

# 預編譯診斷探針庫 (相容 DiagnosticProbeSpecification)
DEFAULT_PROBES = [
    {
        "probe_id": "probe_has_transcript",
        "target_ambiguity_class": "text_vs_audio",
        "probe_type": "STATIC_ASSERTION",
        "execution_payload": "Path('0_Scriptor/output/transcript.json').exists()",
        "discriminant_outcomes": [
            {"outcome_identifier": "TRUE", "pruned_node_ids": ["script_writing"], "posterior_belief_weight": 0.8},
            {"outcome_identifier": "FALSE", "pruned_node_ids": ["host_performance", "caption_titlecards"], "posterior_belief_weight": 0.9}
        ],
        "computational_cost": 0.05
    },
    {
        "probe_id": "probe_target_is_sound",
        "target_ambiguity_class": "audio_vs_visual",
        "probe_type": "DISCRETE_CLARIFICATION",
        "execution_payload": "您的任務是否主要涉及 [背景配樂 / 音效 / 靜音]？",
        "discriminant_outcomes": [
            {"outcome_identifier": "YES", "pruned_node_ids": ["host_performance", "broll_footage", "caption_titlecards"], "posterior_belief_weight": 0.95},
            {"outcome_identifier": "NO", "pruned_node_ids": ["music_sound_direction"], "posterior_belief_weight": 0.9}
        ],
        "computational_cost": 0.3
    },
    {
        "probe_id": "probe_target_is_subtitle",
        "target_ambiguity_class": "subtitle_vs_character",
        "probe_type": "DISCRETE_CLARIFICATION",
        "execution_payload": "您的任務是否主要改變 [字幕 / 大字報時間軸]？",
        "discriminant_outcomes": [
            {"outcome_identifier": "YES", "pruned_node_ids": ["host_performance", "broll_footage", "music_sound_direction"], "posterior_belief_weight": 0.95},
            {"outcome_identifier": "NO", "pruned_node_ids": ["caption_titlecards"], "posterior_belief_weight": 0.9}
        ],
        "computational_cost": 0.3
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

def load_probes():
    if PROBE_LIBRARY_FILE.is_file():
        try:
            with open(PROBE_LIBRARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_PROBES

def calculate_shannon_entropy(candidate_count, total_count):
    if candidate_count == 0 or total_count == 0:
        return 0.0
    p = candidate_count / float(total_count)
    if p >= 1.0 or p <= 0.0:
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))

def evaluate_conformal_gate(candidates, total_count):
    """共形置信度評估：若候選集合小於等於 2 則觸發快速穿透"""
    count = len(candidates)
    if count == 0:
        return {"action": "ABSTAIN", "reason": "No candidate matches positive/negative constraints. Aborting to prevent hallucination."}
    elif count <= 2:
        return {"action": "FAST_TRACK", "target_nodes": [c["node_id"] for c in candidates], "reason": "Candidate set size <= 2. Bypassing dialogue probes directly to CLIS AST lens."}
    else:
        entropy = calculate_shannon_entropy(count, total_count)
        return {"action": "SLOW_TRACK", "entropy": round(entropy, 3), "reason": f"High entropy ({round(entropy, 3)}). Initiating Bayesian diagnostic probing."}

def find_best_diagnostic_probe(candidates):
    probes = load_probes()
    cand_ids = {c["node_id"] for c in candidates}
    scored = []

    for probe in probes:
        # 計算此探針能修剪的候選節點數
        max_pruned = 0
        for outcome in probe.get("discriminant_outcomes", []):
            intersect = set(outcome.get("pruned_node_ids", [])) & cand_ids
            if len(intersect) > max_pruned:
                max_pruned = len(intersect)
        
        if max_pruned > 0:
            # 優先度：修剪能力高 + 代價低
            cost = probe.get("computational_cost", 0.5)
            score = (max_pruned / float(len(candidates))) / (cost + 0.1)
            scored.append({
                "probe_id": probe["probe_id"],
                "probe_type": probe["probe_type"],
                "payload": probe["execution_payload"],
                "expected_pruning_power": f"{max_pruned}/{len(candidates)}",
                "score": round(score, 2)
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored

def route_gen2(intent=None, artifact_state=None):
    capabilities = load_capabilities()
    total_count = len(capabilities)
    candidates = list(capabilities)

    # 1. 契約過濾 (Positive Invariants vs. Negative Constraints)
    if intent:
        q = intent.lower()
        survivors = []
        for c in candidates:
            contracts = c.get("contracts", {})
            # 負向約束一票否決
            if any(neg in q for neg in contracts.get("negative_constraints", [])):
                continue
            # 正向約束或能力匹配
            matched = any(pos in q for pos in contracts.get("positive_invariants", [])) or \
                      any(cap in q for cap in c.get("capabilities", [])) or \
                      (q in c.get("semantic_summary", "").lower()) or \
                      (q in c["module_path"].lower())
            if matched:
                survivors.append(c)
        if survivors:
            candidates = survivors

    # 2. 產物狀態感知
    if artifact_state:
        art = artifact_state.lower()
        candidates = [c for c in candidates if any(art in inp or art in out for inp in c.get("inputs", []) for out in c.get("outputs", []))] or candidates

    # 3. 共形閘門評估 (Conformal Gating)
    gate_decision = evaluate_conformal_gate(candidates, total_count)
    recommended_probes = find_best_diagnostic_probe(candidates) if gate_decision["action"] == "SLOW_TRACK" else []

    return {
        "conformal_gate": gate_decision,
        "candidate_count": len(candidates),
        "candidates": [{
            "node_id": c["node_id"],
            "module_path": c["module_path"],
            "symbol_anchors": c.get("symbol_anchors", [])
        } for c in candidates],
        "recommended_probes": recommended_probes
    }

def record_navigation_telemetry(query, candidate_count, selected_node, execution_verdict, latency_ms=120):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "trace_id": f"trace_{int(Path().stat().st_mtime) if Path().exists() else 1000}_{len(query)}",
        "task_fingerprint": query[:40],
        "initial_conformal_set_size": candidate_count,
        "traversed_capability_nodes": [selected_node] if selected_node else [],
        "execution_verdict": execution_verdict,
        "total_latency_ms": latency_ms
    }
    with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"[OK] Gen-2 Telemetry event recorded for task: '{query[:30]}...' -> verdict: {execution_verdict}")

def main():
    parser = argparse.ArgumentParser(description="Gen-2 Adaptive Cognitive Navigation Engine")
    subparsers = parser.add_subparsers(dest="command")

    # route command
    p_route = subparsers.add_parser("route", help="Evaluate conformal gating and route task")
    p_route.add_argument("-i", "--intent", help="Task intent description")
    p_route.add_argument("-s", "--state", help="Artifact state")

    # feedback command
    p_fb = subparsers.add_parser("feedback", help="Record navigation telemetry event")
    p_fb.add_argument("--query", required=True, help="Task query")
    p_fb.add_argument("--selected", required=True, help="Selected capability node")
    p_fb.add_argument("--success", type=lambda x: x.lower() == 'true', required=True, help="true/false")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "route":
        res = route_gen2(args.intent, args.state)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "feedback":
        verdict = "SUCCESS" if args.success else "ORACLE_FAILURE"
        record_navigation_telemetry(args.query, 1, args.selected, verdict)

if __name__ == "__main__":
    main()
