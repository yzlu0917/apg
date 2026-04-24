#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import load_jsonl, resolve_layers
from evaluate_state_first_pairwise_separability import (
    binary_metrics,
    derive_pair_rows,
    extract_candidate_states,
    fit_centroid_probe,
    fit_linear_probe,
    flatten_states,
    geometry_metrics,
    load_state_index,
    score_leave_one_state_out,
)


def score_within_state_loo(
    rows: List[Dict],
    x: torch.Tensor,
    state_ids: List[str],
    *,
    group_keys: Optional[List[str]] = None,
) -> Dict[str, torch.Tensor]:
    scores = {
        "linear": torch.zeros(len(rows), dtype=torch.float32),
        "centroid": torch.zeros(len(rows), dtype=torch.float32),
    }
    grouped = defaultdict(list)
    for idx, state_id in enumerate(state_ids):
        grouped[state_id].append(idx)

    for state_id, indices in grouped.items():
        if len(indices) <= 1:
            scores["linear"][indices] = 0.5
            scores["centroid"][indices] = 0.5
            continue
        state_groups = {}
        if group_keys is None:
            for idx in indices:
                state_groups[idx] = [idx]
        else:
            by_group = defaultdict(list)
            for idx in indices:
                by_group[group_keys[idx]].append(idx)
            for members in by_group.values():
                for idx in members:
                    state_groups[idx] = members
        for test_idx in indices:
            holdout = set(state_groups[test_idx])
            train_indices = [i for i in indices if i not in holdout]
            x_train = x[train_indices]
            x_test = x[[test_idx]]
            y_train = torch.tensor([rows[i]["label"] for i in train_indices], dtype=torch.long)
            torch.manual_seed(0)
            scores["linear"][test_idx] = fit_linear_probe(x_train, y_train, x_test)[0]
            scores["centroid"][test_idx] = fit_centroid_probe(x_train, y_train, x_test)[0]
    return scores


def summarize_by_state(rows: List[Dict], score_dict: Dict[str, torch.Tensor]) -> List[Dict]:
    grouped = defaultdict(list)
    for idx, row in enumerate(rows):
        grouped[row["state_id"]].append((idx, row))

    summary = []
    for state_id, items in grouped.items():
        labels = torch.tensor([row["label"] for _, row in items], dtype=torch.long)
        record = {"state_id": state_id, "num_rows": len(items)}
        for name, scores in score_dict.items():
            probs = torch.tensor([float(scores[idx].item()) for idx, _ in items], dtype=torch.float32)
            record[name] = binary_metrics(labels, probs)
        summary.append(record)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze within-state vs cross-state locality on state-first pairwise data.")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--replayed", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    oracle_rows = load_jsonl(Path(args.oracle))
    replay_index = load_state_index(Path(args.generated), Path(args.replayed))

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
        replay_row = replay_index[row["state_id"]]
        vecs, _ = extract_candidate_states(model, tokenizer, replay_row, resolved_layers, args.device)
        state_vectors[row["state_id"]] = vecs

    gap_rows, direction_rows = derive_pair_rows(oracle_rows, replay_index)

    gap_features = []
    for row in gap_rows:
        vecs = state_vectors[row["state_id"]]
        a = flatten_states(vecs[str(row["candidate_a_index"])]["h_plus"])
        b = flatten_states(vecs[str(row["candidate_b_index"])]["h_plus"])
        gap_features.append(torch.abs(a - b))
    direction_features = []
    for row in direction_rows:
        vecs = state_vectors[row["state_id"]]
        first = flatten_states(vecs[str(row["first_candidate_index"])]["h_plus"])
        second = flatten_states(vecs[str(row["second_candidate_index"])]["h_plus"])
        direction_features.append(first - second)

    gap_x = torch.stack(gap_features, dim=0)
    direction_x = torch.stack(direction_features, dim=0)
    gap_state_ids = [row["state_id"] for row in gap_rows]
    direction_state_ids = [row["state_id"] for row in direction_rows]
    gap_y = torch.tensor([row["label"] for row in gap_rows], dtype=torch.long)
    direction_y = torch.tensor([row["label"] for row in direction_rows], dtype=torch.long)

    cross_gap = score_leave_one_state_out(gap_rows, gap_x, state_ids=gap_state_ids)
    cross_direction = score_leave_one_state_out(direction_rows, direction_x, state_ids=direction_state_ids)
    within_gap = score_within_state_loo(gap_rows, gap_x, gap_state_ids)
    direction_group_keys = [
        f"{row['state_id']}::{min(int(row['first_candidate_index']), int(row['second_candidate_index']))}::{max(int(row['first_candidate_index']), int(row['second_candidate_index']))}"
        for row in direction_rows
    ]
    within_direction = score_within_state_loo(
        direction_rows,
        direction_x,
        direction_state_ids,
        group_keys=direction_group_keys,
    )

    output = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "batch_stats": {
            "num_states": len(oracle_rows),
            "num_gap_pairs": len(gap_rows),
            "num_direction_examples": len(direction_rows),
        },
        "gap_task": {
            "cross_state_metrics": {name: binary_metrics(gap_y, probs) for name, probs in cross_gap.items()},
            "within_state_metrics": {name: binary_metrics(gap_y, probs) for name, probs in within_gap.items()},
            "geometry": geometry_metrics(gap_x, gap_y),
            "state_rows_cross": summarize_by_state(gap_rows, cross_gap),
            "state_rows_within": summarize_by_state(gap_rows, within_gap),
        },
        "direction_task": {
            "cross_state_metrics": {name: binary_metrics(direction_y, probs) for name, probs in cross_direction.items()},
            "within_state_metrics": {name: binary_metrics(direction_y, probs) for name, probs in within_direction.items()},
            "geometry": geometry_metrics(direction_x, direction_y),
            "state_rows_cross": summarize_by_state(direction_rows, cross_direction),
            "state_rows_within": summarize_by_state(direction_rows, within_direction),
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(out),
        "gap_cross": output["gap_task"]["cross_state_metrics"],
        "gap_within": output["gap_task"]["within_state_metrics"],
        "direction_cross": output["direction_task"]["cross_state_metrics"],
        "direction_within": output["direction_task"]["within_state_metrics"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
