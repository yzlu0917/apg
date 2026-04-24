#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import build_prefix, encode_last_token_states, load_jsonl, resolve_layers
from run_object_gate_baselines import auroc_score, brier_score


def flatten_states(entry: Dict[str, torch.Tensor]) -> torch.Tensor:
    layer_items = sorted(entry.items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def load_state_index(generated_path: Path, replayed_path: Path) -> Dict[str, Dict]:
    generated_rows = {row["state_id"]: row for row in load_jsonl(generated_path)}
    replayed_rows = {row["state_id"]: row for row in load_jsonl(replayed_path)}
    merged = {}
    for state_id, replayed in replayed_rows.items():
        generated = generated_rows[state_id]
        merged[state_id] = {
            **replayed,
            "header": generated["header"],
            "prefix_steps": generated["prefix_steps"],
        }
    return merged


def standardize(x_train: torch.Tensor, x_test: torch.Tensor):
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return (x_train - mean) / std, (x_test - mean) / std


def fit_linear_classifier(x_train, y_train, x_test, epochs=400, lr=0.05, weight_decay=1e-3):
    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
    x_train, x_test = standardize(x_train, x_test)
    model = torch.nn.Linear(x_train.shape[1], 1)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        opt.zero_grad()
        logits = model(x_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        opt.step()
    with torch.no_grad():
        return torch.sigmoid(model(x_test).squeeze(-1)).cpu()


def fit_centroid_classifier(x_train, y_train, x_test):
    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
    x_train, x_test = standardize(x_train, x_test)
    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    pos_c = torch.nn.functional.normalize(pos.mean(dim=0, keepdim=True), dim=1)
    neg_c = torch.nn.functional.normalize(neg.mean(dim=0, keepdim=True), dim=1)
    x_test = torch.nn.functional.normalize(x_test, dim=1)
    pos_sim = (x_test @ pos_c.T).squeeze(-1)
    neg_sim = (x_test @ neg_c.T).squeeze(-1)
    return torch.sigmoid(5.0 * (pos_sim - neg_sim)).cpu()


def binary_metrics(y_true: torch.Tensor, y_prob: torch.Tensor):
    preds = (y_prob >= 0.5).long()
    pos_mean = y_prob[y_true == 1].mean().item() if int((y_true == 1).sum().item()) > 0 else None
    neg_mean = y_prob[y_true == 0].mean().item() if int((y_true == 0).sum().item()) > 0 else None
    return {
        "auroc": auroc_score(y_true, y_prob),
        "accuracy": float((preds == y_true).float().mean().item()),
        "brier": brier_score(y_true, y_prob),
        "positive_mean_prob": None if pos_mean is None else float(pos_mean),
        "negative_mean_prob": None if neg_mean is None else float(neg_mean),
    }


def state_trust_from_sep(sep_json: Dict) -> Dict[str, Dict]:
    out = {}
    gap_by_state = defaultdict(list)
    dir_by_state = defaultdict(list)
    for row in sep_json["gap_task"]["rows"]:
        gap_by_state[row["state_id"]].append((int(row["label"]), float(row["scores"]["linear"])))
    for row in sep_json["direction_task"]["rows"]:
        dir_by_state[row["state_id"]].append((int(row["label"]), float(row["scores"]["linear"])))

    for state_id in set(gap_by_state) | set(dir_by_state):
        gap_vals = gap_by_state.get(state_id, [])
        dir_vals = dir_by_state.get(state_id, [])
        def mean_gap(vals):
            pos = [s for y, s in vals if y == 1]
            neg = [s for y, s in vals if y == 0]
            if not pos or not neg:
                return None
            return (sum(pos) / len(pos)) - (sum(neg) / len(neg))

        gap_mean_gap = mean_gap(gap_vals)
        dir_mean_gap = mean_gap(dir_vals)
        trust = 1 if (dir_mean_gap is not None and dir_mean_gap > 0 and (gap_mean_gap is None or gap_mean_gap > 0)) else 0
        out[state_id] = {
            "trust_label": trust,
            "gap_mean_gap": gap_mean_gap,
            "direction_mean_gap": dir_mean_gap,
            "num_gap_rows": len(gap_vals),
            "num_direction_rows": len(dir_vals),
        }
    return out


def load_judge_rows(path: Path) -> List[Dict]:
    return load_jsonl(path)


def build_pair_maps(sep_json: Dict, judge_rows: List[Dict]) -> Tuple[Dict[Tuple[str, int, int], float], Dict[Tuple[str, int, int], float], Dict[Tuple[str, int, int], float], Dict[Tuple[str, int, int], float]]:
    latent_gap = {}
    latent_dir = {}
    judge_gap = {}
    judge_dir = {}

    for row in sep_json["gap_task"]["rows"]:
        a = int(row["candidate_a_index"])
        b = int(row["candidate_b_index"])
        key = (row["state_id"], min(a, b), max(a, b))
        latent_gap[key] = float(row["scores"]["linear"])

    for row in sep_json["direction_task"]["rows"]:
        key = (row["state_id"], int(row["first_candidate_index"]), int(row["second_candidate_index"]))
        latent_dir[key] = float(row["scores"]["linear"])

    for row in judge_rows:
        a = int(row["candidate_a_index"])
        b = int(row["candidate_b_index"])
        gap_key = (row["state_id"], min(a, b), max(a, b))
        judge_gap[gap_key] = float(row["judge_gap_score"])
        if row["direction_label"] is not None:
            judge_dir[(row["state_id"], a, b)] = float(row["judge_direction_score"])
            judge_dir[(row["state_id"], b, a)] = 1.0 - float(row["judge_direction_score"])

    return latent_gap, latent_dir, judge_gap, judge_dir


def collect_state_rows(model, tokenizer, state_sources: List[Dict], resolved_layers: List[int], device: str) -> List[Dict]:
    rows = []
    for src in state_sources:
        oracle_rows = load_jsonl(Path(src["oracle"]))
        replay_index = load_state_index(Path(src["generated"]), Path(src["replayed"]))
        trust_index = state_trust_from_sep(json.loads(Path(src["sep"]).read_text(encoding="utf-8")))
        for row in oracle_rows:
            sid = row["state_id"]
            replay_row = replay_index[sid]
            before_text = build_prefix(replay_row["header"], replay_row["prefix_steps"], len(replay_row["prefix_steps"]))
            before = encode_last_token_states(model, tokenizer, before_text, resolved_layers, device)
            rows.append(
                {
                    "state_id": sid,
                    "source_name": src["name"],
                    "x": flatten_states(before["states"]),
                    **trust_index[sid],
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Evaluate trust-gated hybrid using before-hidden trust prediction.")
    parser.add_argument("--easy-oracle", required=True)
    parser.add_argument("--easy-generated", required=True)
    parser.add_argument("--easy-replayed", required=True)
    parser.add_argument("--easy-sep", required=True)
    parser.add_argument("--putnam-oracle", required=True)
    parser.add_argument("--putnam-generated", required=True)
    parser.add_argument("--putnam-replayed", required=True)
    parser.add_argument("--putnam-sep", required=True)
    parser.add_argument("--putnam-judge-rows", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

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

    state_sources = [
        {
            "name": "easy_consensus_v2",
            "oracle": args.easy_oracle,
            "generated": args.easy_generated,
            "replayed": args.easy_replayed,
            "sep": args.easy_sep,
        },
        {
            "name": "putnam_v1",
            "oracle": args.putnam_oracle,
            "generated": args.putnam_generated,
            "replayed": args.putnam_replayed,
            "sep": args.putnam_sep,
        },
    ]

    state_rows = collect_state_rows(model, tokenizer, state_sources, resolved_layers, args.device)
    x = torch.stack([row["x"] for row in state_rows], dim=0)
    y = torch.tensor([row["trust_label"] for row in state_rows], dtype=torch.long)
    state_ids = [row["state_id"] for row in state_rows]

    linear_probs = torch.zeros(len(state_rows), dtype=torch.float32)
    centroid_probs = torch.zeros(len(state_rows), dtype=torch.float32)
    for i in range(len(state_rows)):
        train_idx = [j for j in range(len(state_rows)) if j != i]
        test_idx = [i]
        linear_probs[test_idx] = fit_linear_classifier(x[train_idx], y[train_idx], x[test_idx])
        centroid_probs[test_idx] = fit_centroid_classifier(x[train_idx], y[train_idx], x[test_idx])

    putnam_sep = json.loads(Path(args.putnam_sep).read_text(encoding="utf-8"))
    judge_rows = load_judge_rows(Path(args.putnam_judge_rows))
    latent_gap, latent_dir, judge_gap, judge_dir = build_pair_maps(putnam_sep, judge_rows)

    putnam_state_prob = {row["state_id"]: float(linear_probs[i].item()) for i, row in enumerate(state_rows) if row["source_name"] == "putnam_v1"}

    gap_labels = []
    latent_gap_scores = []
    judge_gap_scores = []
    hybrid_gap_scores = []
    soft_gap_scores = []
    for row in putnam_sep["gap_task"]["rows"]:
        a = int(row["candidate_a_index"])
        b = int(row["candidate_b_index"])
        key = (row["state_id"], min(a, b), max(a, b))
        latent = latent_gap[key]
        judge = judge_gap[key]
        trust_p = putnam_state_prob[row["state_id"]]
        gap_labels.append(int(row["label"]))
        latent_gap_scores.append(latent)
        judge_gap_scores.append(judge)
        hybrid_gap_scores.append(latent if trust_p >= 0.5 else judge)
        soft_gap_scores.append(trust_p * latent + (1.0 - trust_p) * judge)

    dir_labels = []
    latent_dir_scores = []
    judge_dir_scores = []
    hybrid_dir_scores = []
    soft_dir_scores = []
    for row in putnam_sep["direction_task"]["rows"]:
        key = (row["state_id"], int(row["first_candidate_index"]), int(row["second_candidate_index"]))
        latent = latent_dir[key]
        judge = judge_dir[key]
        trust_p = putnam_state_prob[row["state_id"]]
        dir_labels.append(int(row["label"]))
        latent_dir_scores.append(latent)
        judge_dir_scores.append(judge)
        hybrid_dir_scores.append(latent if trust_p >= 0.5 else judge)
        soft_dir_scores.append(trust_p * latent + (1.0 - trust_p) * judge)

    gap_y = torch.tensor(gap_labels, dtype=torch.long)
    dir_y = torch.tensor(dir_labels, dtype=torch.long)

    output = {
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "trust_prediction": {
            "num_states": len(state_rows),
            "num_trusted": int(y.sum().item()),
            "num_untrusted": int((y == 0).sum().item()),
            "linear": binary_metrics(y, linear_probs),
            "centroid": binary_metrics(y, centroid_probs),
            "state_rows": [
                {
                    "state_id": row["state_id"],
                    "source_name": row["source_name"],
                    "trust_label": row["trust_label"],
                    "gap_mean_gap": row["gap_mean_gap"],
                    "direction_mean_gap": row["direction_mean_gap"],
                    "linear_trust_prob": float(linear_probs[i].item()),
                    "centroid_trust_prob": float(centroid_probs[i].item()),
                }
                for i, row in enumerate(state_rows)
            ],
        },
        "putnam_hybrid": {
            "gap_task": {
                "latent_only": binary_metrics(gap_y, torch.tensor(latent_gap_scores, dtype=torch.float32)),
                "judge_only": binary_metrics(gap_y, torch.tensor(judge_gap_scores, dtype=torch.float32)),
                "hybrid_hard": binary_metrics(gap_y, torch.tensor(hybrid_gap_scores, dtype=torch.float32)),
                "hybrid_soft": binary_metrics(gap_y, torch.tensor(soft_gap_scores, dtype=torch.float32)),
            },
            "direction_task": {
                "latent_only": binary_metrics(dir_y, torch.tensor(latent_dir_scores, dtype=torch.float32)),
                "judge_only": binary_metrics(dir_y, torch.tensor(judge_dir_scores, dtype=torch.float32)),
                "hybrid_hard": binary_metrics(dir_y, torch.tensor(hybrid_dir_scores, dtype=torch.float32)),
                "hybrid_soft": binary_metrics(dir_y, torch.tensor(soft_dir_scores, dtype=torch.float32)),
            },
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
