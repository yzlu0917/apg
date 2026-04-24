#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from analyze_state_first_locality import score_within_state_loo
from evaluate_state_first_pairwise_separability import (
    binary_metrics,
    derive_pair_rows,
    flatten_states,
    geometry_metrics,
    load_state_index,
    score_leave_one_state_out,
)
from extract_boundary_states_smoke import load_jsonl, resolve_layers


def encode_mean_pooled_states(
    model,
    tokenizer,
    text: str,
    resolved_layers: List[int],
    device: str,
) -> Dict[str, torch.Tensor]:
    if text == "":
        text = "[GOAL_SOLVED]"
    encoded = tokenizer(text, return_tensors="pt", add_special_tokens=False)
    if encoded["input_ids"].numel() == 0:
        raise ValueError("Encountered empty token sequence during goal feature extraction.")
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    hidden_states = outputs.hidden_states
    states = {}
    for layer in resolved_layers:
        layer_tensor = hidden_states[layer + 1][0].mean(dim=0).detach().to(torch.float32).cpu()
        states[str(layer)] = layer_tensor
    return states


def extract_goal_candidate_vectors(
    replay_row: Dict,
    model,
    tokenizer,
    resolved_layers: List[int],
    device: str,
) -> Dict[str, Dict[str, torch.Tensor]]:
    before_text = "\n".join(replay_row["before_goals"])
    before_states = encode_mean_pooled_states(model, tokenizer, before_text, resolved_layers, device)

    vectors = {}
    for idx, candidate in enumerate(replay_row["generated_candidates"]):
        if candidate["replay_status"] != "ok":
            continue
        after_text = "\n".join(candidate["after_goals"])
        after_states = encode_mean_pooled_states(model, tokenizer, after_text, resolved_layers, device)
        delta_states = {layer: (after_states[layer] - before_states[layer]) for layer in after_states}
        concat_states = {
            layer: torch.cat([before_states[layer], after_states[layer], delta_states[layer]], dim=0)
            for layer in after_states
        }
        vectors[str(idx)] = {
            "goal_after_mean": after_states,
            "goal_delta_mean": delta_states,
            "goal_concat_rel": concat_states,
        }
    return vectors


def build_features(rows: List[Dict], state_vectors: Dict[str, Dict], feature_key: str, task: str) -> torch.Tensor:
    features = []
    for row in rows:
        vecs = state_vectors[row["state_id"]]
        if task == "gap":
            a = flatten_states(vecs[str(row["candidate_a_index"])][feature_key])
            b = flatten_states(vecs[str(row["candidate_b_index"])][feature_key])
            features.append(torch.abs(a - b))
        elif task == "direction":
            first = flatten_states(vecs[str(row["first_candidate_index"])][feature_key])
            second = flatten_states(vecs[str(row["second_candidate_index"])][feature_key])
            features.append(first - second)
        else:
            raise ValueError(f"Unknown task: {task}")
    return torch.stack(features, dim=0)


def summarize_feature(
    feature_key: str,
    rows: List[Dict],
    x: torch.Tensor,
    state_ids: List[str],
    *,
    group_keys: List[str] = None,
) -> Dict:
    y = torch.tensor([row["label"] for row in rows], dtype=torch.long)
    cross = score_leave_one_state_out(rows, x, state_ids=state_ids)
    within = score_within_state_loo(rows, x, state_ids, group_keys=group_keys)
    return {
        "cross_state_metrics": {name: binary_metrics(y, probs) for name, probs in cross.items()},
        "within_state_metrics": {name: binary_metrics(y, probs) for name, probs in within.items()},
        "geometry": geometry_metrics(x, y),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate goal-aligned relational features on Putnam state-first panel.")
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
        state_id = row["state_id"]
        state_vectors[state_id] = extract_goal_candidate_vectors(
            replay_index[state_id], model, tokenizer, resolved_layers, args.device
        )

    gap_rows, direction_rows = derive_pair_rows(oracle_rows, replay_index)
    gap_state_ids = [row["state_id"] for row in gap_rows]
    direction_state_ids = [row["state_id"] for row in direction_rows]
    direction_group_keys = [
        f"{row['state_id']}::{min(int(row['first_candidate_index']), int(row['second_candidate_index']))}::{max(int(row['first_candidate_index']), int(row['second_candidate_index']))}"
        for row in direction_rows
    ]

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
        "feature_variants": {},
    }

    for feature_key in ["goal_after_mean", "goal_delta_mean", "goal_concat_rel"]:
        gap_x = build_features(gap_rows, state_vectors, feature_key, "gap")
        direction_x = build_features(direction_rows, state_vectors, feature_key, "direction")
        output["feature_variants"][feature_key] = {
            "gap_task": summarize_feature(feature_key, gap_rows, gap_x, gap_state_ids),
            "direction_task": summarize_feature(
                feature_key,
                direction_rows,
                direction_x,
                direction_state_ids,
                group_keys=direction_group_keys,
            ),
        }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preview = {
        k: {
            "gap_cross_linear_auroc": v["gap_task"]["cross_state_metrics"]["linear"]["auroc"],
            "direction_cross_linear_auroc": v["direction_task"]["cross_state_metrics"]["linear"]["auroc"],
            "gap_within_linear_auroc": v["gap_task"]["within_state_metrics"]["linear"]["auroc"],
            "direction_within_linear_auroc": v["direction_task"]["within_state_metrics"]["linear"]["auroc"],
        }
        for k, v in output["feature_variants"].items()
    }
    print(json.dumps({"output": str(out), "variants": preview}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
