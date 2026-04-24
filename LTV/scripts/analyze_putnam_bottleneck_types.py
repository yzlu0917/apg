#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_state_first_pairwise_separability import (
    TIER_TO_ORDINAL,
    extract_candidate_states,
    flatten_states,
    load_state_index,
)
from extract_boundary_states_smoke import load_jsonl, resolve_layers


def safe_mean(values: List[float]) -> Optional[float]:
    return float(sum(values) / len(values)) if values else None


def binary_auc(scores: List[float], labels: List[int]) -> Optional[float]:
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    wins = 0.0
    total = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / total if total else None


def correct_direction_prob(row: Dict) -> float:
    score = float(row["judge_direction_score"])
    return score if int(row["direction_label"]) == 1 else 1.0 - score


def load_typing(path: Path) -> Dict[str, Dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {row["state_id"]: row for row in rows}


def ordered_pair_rows(oracle_rows: List[Dict]) -> Dict[str, List[Dict]]:
    out = defaultdict(list)
    for row in oracle_rows:
        sid = row["state_id"]
        for a, b in combinations(row["candidates"], 2):
            oa = TIER_TO_ORDINAL[a["progress_tier"]]
            ob = TIER_TO_ORDINAL[b["progress_tier"]]
            if oa is None or ob is None or oa == ob:
                continue
            better, worse = (a, b) if oa > ob else (b, a)
            out[sid].append(
                {
                    "better_candidate_index": int(better["candidate_index"]),
                    "worse_candidate_index": int(worse["candidate_index"]),
                    "better_tier": better["progress_tier"],
                    "worse_tier": worse["progress_tier"],
                    "tier_gap": int(TIER_TO_ORDINAL[better["progress_tier"]] - TIER_TO_ORDINAL[worse["progress_tier"]]),
                }
            )
    return out


def normalized_mean(vectors: List[torch.Tensor]) -> torch.Tensor:
    proto = torch.stack(vectors, dim=0).mean(dim=0)
    return torch.nn.functional.normalize(proto, dim=0)


def compute_state_geometry(
    oracle_rows: List[Dict],
    state_vectors: Dict[str, Dict[str, Dict[str, torch.Tensor]]],
) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]]]:
    ordered = ordered_pair_rows(oracle_rows)
    prototypes = {}
    diff_vectors = {}
    for sid, rows in ordered.items():
        diffs = []
        vecs = state_vectors[sid]
        for row in rows:
            better = flatten_states(vecs[str(row["better_candidate_index"])]["h_plus"])
            worse = flatten_states(vecs[str(row["worse_candidate_index"])]["h_plus"])
            diffs.append(better - worse)
        if diffs:
            diff_vectors[sid] = diffs
            prototypes[sid] = normalized_mean(diffs)
    return prototypes, diff_vectors


def evaluate_reference(
    diffs: List[torch.Tensor],
    ref: torch.Tensor,
) -> Tuple[Optional[float], Optional[float]]:
    scores = []
    labels = []
    cosines = []
    for diff in diffs:
        pos = float(torch.dot(torch.nn.functional.normalize(diff, dim=0), ref).item())
        neg = float(torch.dot(torch.nn.functional.normalize(-diff, dim=0), ref).item())
        scores.extend([pos, neg])
        labels.extend([1, 0])
        cosines.append(pos)
    return binary_auc(scores, labels), safe_mean(cosines)


def judge_by_type(judge_rows: List[Dict], typing: Dict[str, Dict]) -> Dict[str, Dict]:
    by_type = defaultdict(list)
    for row in judge_rows:
        if row["relation"] != "ordered":
            continue
        t = typing[row["state_id"]]["bottleneck_type"]
        by_type[t].append(correct_direction_prob(row))
    return {
        t: {
            "num_ordered_rows": len(vals),
            "mean_judge_direction_correct_prob": safe_mean(vals),
        }
        for t, vals in sorted(by_type.items())
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze bottleneck-conditioned alignment on Putnam hard states.")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--replayed", required=True)
    parser.add_argument("--judge-rows", required=True)
    parser.add_argument("--typing-json", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    oracle_rows = load_jsonl(Path(args.oracle))
    replay_index = load_state_index(Path(args.generated), Path(args.replayed))
    judge_rows = load_jsonl(Path(args.judge_rows))
    typing = load_typing(Path(args.typing_json))

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    state_vectors = {}
    for row in oracle_rows:
        sid = row["state_id"]
        candidate_vectors, _ = extract_candidate_states(
            model,
            tokenizer,
            replay_index[sid],
            resolved_layers,
            args.device,
        )
        state_vectors[sid] = candidate_vectors

    prototypes, diff_vectors = compute_state_geometry(oracle_rows, state_vectors)
    state_ids = sorted(prototypes.keys())

    type_to_states = defaultdict(list)
    for sid in state_ids:
        type_to_states[typing[sid]["bottleneck_type"]].append(sid)

    offdiag_within = []
    offdiag_cross = []
    for a, b in combinations(state_ids, 2):
        cos = float(torch.dot(prototypes[a], prototypes[b]).item())
        if typing[a]["bottleneck_type"] == typing[b]["bottleneck_type"]:
            offdiag_within.append(cos)
        else:
            offdiag_cross.append(cos)

    state_rows = []
    for sid in state_ids:
        my_type = typing[sid]["bottleneck_type"]
        same_type_peers = [x for x in type_to_states[my_type] if x != sid]
        global_peers = [x for x in state_ids if x != sid]
        other_type_peers = [x for x in state_ids if x != sid and typing[x]["bottleneck_type"] != my_type]

        same_type_ref = normalized_mean([prototypes[x] for x in same_type_peers]) if same_type_peers else None
        global_ref = normalized_mean([prototypes[x] for x in global_peers]) if global_peers else None
        other_type_ref = normalized_mean([prototypes[x] for x in other_type_peers]) if other_type_peers else None

        same_auc, same_cos = evaluate_reference(diff_vectors[sid], same_type_ref) if same_type_ref is not None else (None, None)
        global_auc, global_cos = evaluate_reference(diff_vectors[sid], global_ref) if global_ref is not None else (None, None)
        other_auc, other_cos = evaluate_reference(diff_vectors[sid], other_type_ref) if other_type_ref is not None else (None, None)

        state_rows.append(
            {
                "state_id": sid,
                "theorem_id": replay_index[sid]["theorem_id"],
                "bottleneck_type": my_type,
                "typing_reason": typing[sid]["reason"],
                "same_type_peer_count": len(same_type_peers),
                "prototype_norm": float(torch.norm(prototypes[sid]).item()),
                "same_type_direction_auc": same_auc,
                "global_direction_auc": global_auc,
                "other_type_direction_auc": other_auc,
                "same_type_mean_cos": same_cos,
                "global_mean_cos": global_cos,
                "other_type_mean_cos": other_cos,
                "same_vs_global_auc_gain": None if same_auc is None or global_auc is None else float(same_auc - global_auc),
                "same_vs_global_cos_gain": None if same_cos is None or global_cos is None else float(same_cos - global_cos),
            }
        )

    type_rows = []
    for t, sids in sorted(type_to_states.items()):
        typed = [r for r in state_rows if r["bottleneck_type"] == t]
        type_rows.append(
            {
                "bottleneck_type": t,
                "num_states": len(sids),
                "states": sids,
                "mean_same_type_direction_auc": safe_mean([r["same_type_direction_auc"] for r in typed if r["same_type_direction_auc"] is not None]),
                "mean_global_direction_auc": safe_mean([r["global_direction_auc"] for r in typed if r["global_direction_auc"] is not None]),
                "mean_same_vs_global_auc_gain": safe_mean([r["same_vs_global_auc_gain"] for r in typed if r["same_vs_global_auc_gain"] is not None]),
                "mean_same_type_cos": safe_mean([r["same_type_mean_cos"] for r in typed if r["same_type_mean_cos"] is not None]),
                "mean_global_cos": safe_mean([r["global_mean_cos"] for r in typed if r["global_mean_cos"] is not None]),
                "mean_same_vs_global_cos_gain": safe_mean([r["same_vs_global_cos_gain"] for r in typed if r["same_vs_global_cos_gain"] is not None]),
            }
        )

    output = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "judge_rows": args.judge_rows,
        "typing_json": args.typing_json,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "state_rows": state_rows,
        "type_rows": type_rows,
        "prototype_alignment": {
            "within_type_offdiag_mean_cos": safe_mean(offdiag_within),
            "cross_type_offdiag_mean_cos": safe_mean(offdiag_cross),
            "within_type_pairs": len(offdiag_within),
            "cross_type_pairs": len(offdiag_cross),
        },
        "judge_by_type": judge_by_type(judge_rows, typing),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "type_rows": type_rows, "prototype_alignment": output["prototype_alignment"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
