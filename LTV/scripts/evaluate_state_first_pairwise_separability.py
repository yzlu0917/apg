#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import build_prefix, encode_last_token_states, load_jsonl, resolve_layers
from run_object_gate_baselines import auroc_score, brier_score
from evaluate_cts_scoring_audit import normalize_train_test


TIER_TO_ORDINAL = {
    "solved": 3,
    "strong_partial": 2,
    "weak_partial": 1,
    "neutral": 0,
    "uncertain": None,
}


def flatten_states(entry: Dict[str, torch.Tensor]) -> torch.Tensor:
    layer_items = sorted(entry.items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def fit_linear_probe(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    *,
    epochs: int = 400,
    lr: float = 0.05,
    weight_decay: float = 1e-3,
) -> torch.Tensor:
    if len(x_train) == 0:
        return torch.full((len(x_test),), 0.5, dtype=torch.float32)
    positives = int(y_train.sum().item())
    if positives == 0 or positives == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)

    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std

    model = torch.nn.Linear(x_train.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        return torch.sigmoid(model(x_test).squeeze(-1)).cpu()


def fit_centroid_probe(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
) -> torch.Tensor:
    if len(x_train) == 0:
        return torch.full((len(x_test),), 0.5, dtype=torch.float32)
    positives = int(y_train.sum().item())
    if positives == 0 or positives == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)

    x_train, x_test = normalize_train_test(x_train, x_test)
    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
    pos_centroid = pos.mean(dim=0, keepdim=True)
    neg_centroid = neg.mean(dim=0, keepdim=True)
    pos_dist = torch.norm(x_test - pos_centroid, dim=1)
    neg_dist = torch.norm(x_test - neg_centroid, dim=1)
    return torch.sigmoid(neg_dist - pos_dist).cpu()


def binary_metrics(y_true: torch.Tensor, y_prob: torch.Tensor) -> Dict[str, float]:
    preds = (y_prob >= 0.5).long()
    return {
        "auroc": auroc_score(y_true, y_prob),
        "accuracy": float((preds == y_true).float().mean().item()),
        "brier": brier_score(y_true, y_prob),
        "num_examples": int(len(y_true)),
        "positive_mean_prob": float(y_prob[y_true == 1].mean().item()) if int((y_true == 1).sum().item()) > 0 else None,
        "negative_mean_prob": float(y_prob[y_true == 0].mean().item()) if int((y_true == 0).sum().item()) > 0 else None,
        "mean_gap": float(y_prob[y_true == 1].mean().item() - y_prob[y_true == 0].mean().item()) if int((y_true == 1).sum().item()) > 0 and int((y_true == 0).sum().item()) > 0 else None,
    }


def fisher_ratio(x: torch.Tensor, y: torch.Tensor) -> float:
    pos = x[y == 1]
    neg = x[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    pos_mean = pos.mean(dim=0)
    neg_mean = neg.mean(dim=0)
    between = torch.sum((pos_mean - neg_mean) ** 2)
    pos_cov = torch.mean(torch.sum((pos - pos_mean) ** 2, dim=1)) if len(pos) > 0 else torch.tensor(0.0)
    neg_cov = torch.mean(torch.sum((neg - neg_mean) ** 2, dim=1)) if len(neg) > 0 else torch.tensor(0.0)
    denom = pos_cov + neg_cov
    if float(denom.item()) < 1e-8:
        return float("inf")
    return float((between / denom).item())


def loo_knn_accuracy(x: torch.Tensor, y: torch.Tensor) -> float:
    if len(x) <= 1:
        return float("nan")
    x = torch.nn.functional.normalize(x, dim=1)
    sims = x @ x.T
    sims.fill_diagonal_(-1e9)
    nn_idx = sims.argmax(dim=1)
    preds = y[nn_idx]
    return float((preds == y).float().mean().item())


def geometry_metrics(x: torch.Tensor, y: torch.Tensor) -> Dict[str, float]:
    x_norm = torch.nn.functional.normalize(x, dim=1)
    pos = x_norm[y == 1]
    neg = x_norm[y == 0]
    pos_mean = pos.mean(dim=0) if len(pos) > 0 else torch.zeros(x.shape[1])
    neg_mean = neg.mean(dim=0) if len(neg) > 0 else torch.zeros(x.shape[1])
    return {
        "positive_centroid_norm": float(torch.norm(pos_mean).item()),
        "negative_centroid_norm": float(torch.norm(neg_mean).item()),
        "centroid_gap": float(torch.norm(pos_mean - neg_mean).item()),
        "fisher_ratio": fisher_ratio(x, y),
        "loo_1nn_acc": loo_knn_accuracy(x, y),
    }


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


def extract_candidate_states(
    model,
    tokenizer,
    replay_row: Dict,
    resolved_layers: List[int],
    device: str,
) -> Tuple[Dict[str, Dict[str, torch.Tensor]], Dict[str, Dict]]:
    before_text = build_prefix(replay_row["header"], replay_row["prefix_steps"], len(replay_row["prefix_steps"]))
    before = encode_last_token_states(model, tokenizer, before_text, resolved_layers, device)

    candidate_vectors = {}
    candidate_meta = {}
    for idx, candidate in enumerate(replay_row["generated_candidates"]):
        if candidate["replay_status"] != "ok":
            continue
        step_text = candidate["tactic"]
        after_text = before_text + "\n" + step_text if before_text else step_text
        after = encode_last_token_states(model, tokenizer, after_text, resolved_layers, device)
        h_plus = after["states"]
        h_minus = before["states"]
        delta_h = {layer: (h_plus[layer] - h_minus[layer]) for layer in h_plus}
        key = str(idx)
        candidate_vectors[key] = {
            "h_plus": h_plus,
            "delta_h": delta_h,
        }
        candidate_meta[key] = {
            "candidate_index": idx,
            "tactic": step_text,
            "after_goals": candidate["after_goals"],
        }
    return candidate_vectors, candidate_meta


def derive_pair_rows(oracle_rows: List[Dict], replay_index: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
    gap_rows = []
    direction_rows = []
    for row in oracle_rows:
        state_id = row["state_id"]
        replay_row = replay_index[state_id]
        candidates = row["candidates"]
        by_idx = {str(c["candidate_index"]): c for c in candidates}
        for a, b in combinations(candidates, 2):
            oa = TIER_TO_ORDINAL[a["progress_tier"]]
            ob = TIER_TO_ORDINAL[b["progress_tier"]]
            if oa is None or ob is None:
                continue
            relation = "equivalent" if oa == ob else "ordered"
            better = None
            worse = None
            if oa != ob:
                better, worse = (a, b) if oa > ob else (b, a)
            gap_rows.append(
                {
                    "state_id": state_id,
                    "theorem_id": replay_row["theorem_id"],
                    "label": 1 if relation == "ordered" else 0,
                    "relation": relation,
                    "candidate_a_index": a["candidate_index"],
                    "candidate_b_index": b["candidate_index"],
                    "candidate_a_tier": a["progress_tier"],
                    "candidate_b_tier": b["progress_tier"],
                    "preferred_candidate_index": None if better is None else better["candidate_index"],
                    "preferred_tier": None if better is None else better["progress_tier"],
                    "nonpreferred_candidate_index": None if worse is None else worse["candidate_index"],
                    "nonpreferred_tier": None if worse is None else worse["progress_tier"],
                }
            )
            if relation == "ordered":
                direction_rows.append(
                    {
                        "state_id": state_id,
                        "theorem_id": replay_row["theorem_id"],
                        "label": 1,
                        "first_candidate_index": better["candidate_index"],
                        "second_candidate_index": worse["candidate_index"],
                        "first_tier": better["progress_tier"],
                        "second_tier": worse["progress_tier"],
                    }
                )
                direction_rows.append(
                    {
                        "state_id": state_id,
                        "theorem_id": replay_row["theorem_id"],
                        "label": 0,
                        "first_candidate_index": worse["candidate_index"],
                        "second_candidate_index": better["candidate_index"],
                        "first_tier": worse["progress_tier"],
                        "second_tier": better["progress_tier"],
                    }
                )
    return gap_rows, direction_rows


def score_leave_one_state_out(
    rows: List[Dict],
    x: torch.Tensor,
    *,
    state_ids: List[str],
) -> Dict[str, torch.Tensor]:
    scores = {
        "linear": torch.zeros(len(rows), dtype=torch.float32),
        "centroid": torch.zeros(len(rows), dtype=torch.float32),
    }
    grouped = defaultdict(list)
    for idx, state_id in enumerate(state_ids):
        grouped[state_id].append(idx)

    for state_id, test_indices in grouped.items():
        train_indices = [i for i in range(len(rows)) if state_ids[i] != state_id]
        if len(test_indices) == 0:
            continue
        x_train = x[train_indices]
        x_test = x[test_indices]
        y_train = torch.tensor([rows[i]["label"] for i in train_indices], dtype=torch.long)
        torch.manual_seed(0)
        scores["linear"][test_indices] = fit_linear_probe(x_train, y_train, x_test)
        scores["centroid"][test_indices] = fit_centroid_probe(x_train, y_train, x_test)
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate pairwise separability on state-first human progress oracle.")
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
    state_candidate_meta = {}
    for row in oracle_rows:
        replay_row = replay_index[row["state_id"]]
        vecs, meta = extract_candidate_states(model, tokenizer, replay_row, resolved_layers, args.device)
        state_vectors[row["state_id"]] = vecs
        state_candidate_meta[row["state_id"]] = meta

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

    gap_scores = score_leave_one_state_out(gap_rows, gap_x, state_ids=gap_state_ids)
    direction_scores = score_leave_one_state_out(direction_rows, direction_x, state_ids=direction_state_ids)

    gap_y = torch.tensor([row["label"] for row in gap_rows], dtype=torch.long)
    direction_y = torch.tensor([row["label"] for row in direction_rows], dtype=torch.long)

    output = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "note": "Within shared before-state, transition pair differences equal post-state pair differences, so this audit uses h_plus pair features.",
        "batch_stats": {
            "num_states": len(oracle_rows),
            "num_gap_pairs": len(gap_rows),
            "num_gap_ordered": int(gap_y.sum().item()),
            "num_gap_equivalent": int((gap_y == 0).sum().item()),
            "num_direction_examples": len(direction_rows),
        },
        "gap_task": {
            "metrics": {name: binary_metrics(gap_y, probs) for name, probs in gap_scores.items()},
            "geometry": geometry_metrics(gap_x, gap_y),
            "rows": [
                {
                    **row,
                    "scores": {name: float(gap_scores[name][idx].item()) for name in gap_scores},
                }
                for idx, row in enumerate(gap_rows)
            ],
        },
        "direction_task": {
            "metrics": {name: binary_metrics(direction_y, probs) for name, probs in direction_scores.items()},
            "geometry": geometry_metrics(direction_x, direction_y),
            "rows": [
                {
                    **row,
                    "scores": {name: float(direction_scores[name][idx].item()) for name in direction_scores},
                }
                for idx, row in enumerate(direction_rows)
            ],
        },
        "state_summary": [
            {
                "state_id": row["state_id"],
                "tier_counts": dict(Counter(c["progress_tier"] for c in row["candidates"])),
                "num_candidates": len(row["candidates"]),
            }
            for row in oracle_rows
        ],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps({
        "output": str(output_path),
        "gap_metrics": output["gap_task"]["metrics"],
        "direction_metrics": output["direction_task"]["metrics"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
