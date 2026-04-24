#!/usr/bin/env python3
import argparse
import json
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import build_prefix, encode_last_token_states, load_jsonl, resolve_layers


TIER_TO_ORDINAL = {
    "neutral": 0,
    "weak_partial": 1,
    "strong_partial": 2,
    "solved": 3,
}


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


def extract_candidate_states(
    model,
    tokenizer,
    replay_row: Dict,
    resolved_layers: List[int],
    device: str,
) -> Dict[str, torch.Tensor]:
    before_text = build_prefix(replay_row["header"], replay_row["prefix_steps"], len(replay_row["prefix_steps"]))
    candidate_vectors = {}
    for idx, candidate in enumerate(replay_row["generated_candidates"]):
        if candidate["replay_status"] != "ok":
            continue
        step_text = candidate["tactic"]
        after_text = before_text + "\n" + step_text if before_text else step_text
        after = encode_last_token_states(model, tokenizer, after_text, resolved_layers, device)
        candidate_vectors[str(idx)] = flatten_states(after["states"])
    return candidate_vectors


def build_candidate_dataset(oracle_rows: List[Dict], replay_index: Dict[str, Dict], candidate_vectors: Dict[str, Dict[str, torch.Tensor]]):
    candidates = []
    for row in oracle_rows:
        state_id = row["state_id"]
        for cand in row["candidates"]:
            idx = str(cand["candidate_index"])
            if idx not in candidate_vectors[state_id]:
                continue
            candidates.append(
                {
                    "state_id": state_id,
                    "candidate_index": cand["candidate_index"],
                    "tier": cand["progress_tier"],
                    "ordinal": TIER_TO_ORDINAL[cand["progress_tier"]],
                    "feature": candidate_vectors[state_id][idx],
                    "tactic": cand["tactic"],
                }
            )
    return candidates


def build_pair_constraints(candidates: List[Dict]):
    by_state = defaultdict(list)
    for cand in candidates:
        by_state[cand["state_id"]].append(cand)
    ordered_pairs = []
    equivalent_pairs = []
    for state_id, rows in by_state.items():
        for a, b in combinations(rows, 2):
            if a["ordinal"] == b["ordinal"]:
                equivalent_pairs.append((a, b))
            elif a["ordinal"] > b["ordinal"]:
                ordered_pairs.append((a, b))
            else:
                ordered_pairs.append((b, a))
    return ordered_pairs, equivalent_pairs, by_state


class LinearScorer(torch.nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.linear = torch.nn.Linear(dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x).squeeze(-1)


class MLPScorer(torch.nn.Module):
    def __init__(self, dim: int, hidden_dim: int = 512):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(dim, hidden_dim),
            torch.nn.GELU(),
            torch.nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def standardize(x_train: torch.Tensor, x_test: torch.Tensor):
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return (x_train - mean) / std, (x_test - mean) / std


def fit_scorer(
    train_candidates: List[Dict],
    model_type: str,
    *,
    epochs: int = 400,
    lr: float = 5e-3,
    weight_decay: float = 1e-4,
    pairwise_weight: float = 1.0,
    pointwise_weight: float = 0.3,
    equiv_weight: float = 0.2,
):
    x = torch.stack([c["feature"] for c in train_candidates], dim=0)
    x_std, _ = standardize(x, x.clone())
    ordinals = torch.tensor([c["ordinal"] for c in train_candidates], dtype=torch.float32)
    targets = ordinals / 3.0

    for i, cand in enumerate(train_candidates):
        cand["_train_idx"] = i

    ordered_pairs, equivalent_pairs, _ = build_pair_constraints(train_candidates)
    if model_type == "linear":
        model = LinearScorer(x_std.shape[1])
    elif model_type == "mlp":
        model = MLPScorer(x_std.shape[1])
    else:
        raise ValueError(model_type)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    for _ in range(epochs):
        optimizer.zero_grad()
        scores = model(x_std)
        loss = torch.tensor(0.0, dtype=torch.float32)

        if ordered_pairs:
            diffs = []
            for better, worse in ordered_pairs:
                diffs.append(scores[better["_train_idx"]] - scores[worse["_train_idx"]])
            diffs = torch.stack(diffs)
            loss = loss + pairwise_weight * torch.nn.functional.softplus(-diffs).mean()

        if equivalent_pairs:
            eq_diffs = []
            for a, b in equivalent_pairs:
                eq_diffs.append(scores[a["_train_idx"]] - scores[b["_train_idx"]])
            eq_diffs = torch.stack(eq_diffs)
            loss = loss + equiv_weight * (eq_diffs ** 2).mean()

        point_probs = torch.sigmoid(scores)
        loss = loss + pointwise_weight * ((point_probs - targets) ** 2).mean()
        loss.backward()
        optimizer.step()

    return model, x.mean(dim=0, keepdim=True), x.std(dim=0, keepdim=True)


def apply_scorer(model, mean, std, test_candidates: List[Dict]) -> torch.Tensor:
    x = torch.stack([c["feature"] for c in test_candidates], dim=0)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    x = (x - mean) / std
    with torch.no_grad():
        return model(x).cpu()


def auc_from_scores(pos_scores: List[float], neg_scores: List[float]) -> float:
    if not pos_scores or not neg_scores:
        return float("nan")
    wins = 0.0
    for p in pos_scores:
        for n in neg_scores:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(pos_scores) * len(neg_scores))


def ndcg_at_all(ordinals: List[int], scores: List[float]) -> float:
    def dcg(items):
        total = 0.0
        for rank, gain in enumerate(items, start=1):
            total += (2 ** gain - 1) / math.log2(rank + 1)
        return total

    pred_order = [o for _, o in sorted(zip(scores, ordinals), key=lambda x: x[0], reverse=True)]
    ideal_order = sorted(ordinals, reverse=True)
    ideal = dcg(ideal_order)
    return 1.0 if ideal == 0 else dcg(pred_order) / ideal


def evaluate_by_state(test_candidates: List[Dict], scores: torch.Tensor):
    by_state = defaultdict(list)
    for cand, score in zip(test_candidates, scores.tolist()):
        by_state[cand["state_id"]].append((cand, score))

    ordered_correct = 0
    ordered_total = 0
    equivalent_abs_gaps = []
    top1_hits = 0
    ndcgs = []
    state_rows = []
    pos_diffs = []
    neg_diffs = []

    for state_id, rows in by_state.items():
        ordinals = [cand["ordinal"] for cand, _ in rows]
        score_vals = [score for _, score in rows]
        max_ordinal = max(ordinals)
        top_idx = max(range(len(rows)), key=lambda i: rows[i][1])
        top1_hits += int(rows[top_idx][0]["ordinal"] == max_ordinal)
        ndcgs.append(ndcg_at_all(ordinals, score_vals))

        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                ca, sa = rows[i]
                cb, sb = rows[j]
                if ca["ordinal"] == cb["ordinal"]:
                    equivalent_abs_gaps.append(abs(sa - sb))
                else:
                    if ca["ordinal"] > cb["ordinal"]:
                        diff = sa - sb
                    else:
                        diff = sb - sa
                    ordered_correct += int(diff > 0)
                    ordered_total += 1
                    pos_diffs.append(diff)
                    neg_diffs.append(-diff)

        state_rows.append(
            {
                "state_id": state_id,
                "num_candidates": len(rows),
                "top1_candidate_index": rows[top_idx][0]["candidate_index"],
                "top1_tier": rows[top_idx][0]["tier"],
                "top1_is_max_tier": rows[top_idx][0]["ordinal"] == max_ordinal,
                "ndcg": ndcgs[-1],
                "candidates": [
                    {
                        "candidate_index": cand["candidate_index"],
                        "tier": cand["tier"],
                        "ordinal": cand["ordinal"],
                        "score": score,
                        "tactic": cand["tactic"],
                    }
                    for cand, score in sorted(rows, key=lambda x: x[1], reverse=True)
                ],
            }
        )

    return {
        "ordered_pair_accuracy": ordered_correct / ordered_total if ordered_total else None,
        "ordered_pair_count": ordered_total,
        "equivalent_abs_gap_mean": sum(equivalent_abs_gaps) / len(equivalent_abs_gaps) if equivalent_abs_gaps else None,
        "equivalent_pair_count": len(equivalent_abs_gaps),
        "top1_max_tier_hit_rate": top1_hits / len(by_state) if by_state else None,
        "mean_ndcg": sum(ndcgs) / len(ndcgs) if ndcgs else None,
        "pairwise_direction_auroc": auc_from_scores(pos_diffs, neg_diffs),
        "state_rows": state_rows,
    }


def leave_one_state_out(candidates: List[Dict], scorer_type: str):
    state_ids = sorted(set(c["state_id"] for c in candidates))
    all_state_rows = []
    metrics = []
    for holdout in state_ids:
        train = [c for c in candidates if c["state_id"] != holdout]
        test = [c for c in candidates if c["state_id"] == holdout]
        model, mean, std = fit_scorer(train, scorer_type)
        scores = apply_scorer(model, mean, std, test)
        state_eval = evaluate_by_state(test, scores)
        metrics.append({k: v for k, v in state_eval.items() if k != "state_rows"})
        all_state_rows.extend(state_eval["state_rows"])

    def mean_of(key):
        vals = [m[key] for m in metrics if m[key] is not None]
        return sum(vals) / len(vals) if vals else None

    return {
        "ordered_pair_accuracy": mean_of("ordered_pair_accuracy"),
        "ordered_pair_count": int(sum(m["ordered_pair_count"] for m in metrics)),
        "equivalent_abs_gap_mean": mean_of("equivalent_abs_gap_mean"),
        "equivalent_pair_count": int(sum(m["equivalent_pair_count"] for m in metrics)),
        "top1_max_tier_hit_rate": mean_of("top1_max_tier_hit_rate"),
        "mean_ndcg": mean_of("mean_ndcg"),
        "pairwise_direction_auroc": mean_of("pairwise_direction_auroc"),
        "state_rows": all_state_rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate state-first pairwise progress scorer.")
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
        dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    candidate_vectors = {}
    for row in oracle_rows:
        candidate_vectors[row["state_id"]] = extract_candidate_states(
            model,
            tokenizer,
            replay_index[row["state_id"]],
            resolved_layers,
            args.device,
        )

    candidates = build_candidate_dataset(oracle_rows, replay_index, candidate_vectors)

    results = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "num_states": len({c["state_id"] for c in candidates}),
        "num_candidates": len(candidates),
        "tier_counts": {tier: sum(1 for c in candidates if c["tier"] == tier) for tier in TIER_TO_ORDINAL},
        "scorers": {
            "linear": leave_one_state_out(candidates, "linear"),
            "mlp": leave_one_state_out(candidates, "mlp"),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "linear": {k: v for k, v in results["scorers"]["linear"].items() if k != "state_rows"},
        "mlp": {k: v for k, v in results["scorers"]["mlp"].items() if k != "state_rows"},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
