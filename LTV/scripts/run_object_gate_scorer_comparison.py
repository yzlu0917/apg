#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch

from evaluate_cts_scoring_audit import (
    centroid_cosine_scores,
    fit_linear_probe_with_details,
    fit_mlp_probe,
    normalize_train_test,
)
from run_object_gate_baselines import (
    auroc_score,
    brier_score,
    earliest_fail_localization,
    concat_fields,
    load_features,
    read_jsonl,
    tensor_from_entries,
)


def score_feature_set(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
) -> Dict[str, torch.Tensor]:
    linear = fit_linear_probe_with_details(x_train, y_train, x_test)
    mlp = fit_mlp_probe(x_train, y_train, x_test)
    centroid = centroid_cosine_scores(x_train, y_train, x_test)
    return {
        "linear_prob": linear["probs"],
        "mlp_prob": mlp,
        "centroid_cosine": centroid,
    }


def grouped_cv_scores(
    features: torch.Tensor,
    labels: torch.Tensor,
    groups: List[str],
) -> Dict[str, torch.Tensor]:
    group_to_indices: Dict[str, List[int]] = {}
    for idx, group in enumerate(groups):
        group_to_indices.setdefault(group, []).append(idx)

    predictions = {
        "linear_prob": torch.zeros(len(labels), dtype=torch.float32),
        "mlp_prob": torch.zeros(len(labels), dtype=torch.float32),
        "centroid_cosine": torch.zeros(len(labels), dtype=torch.float32),
    }

    for group, test_indices in group_to_indices.items():
        train_indices = [i for i, g in enumerate(groups) if g != group]
        x_train = features[train_indices]
        y_train = labels[train_indices]
        x_test = features[test_indices]
        torch.manual_seed(0)
        fold_scores = score_feature_set(x_train, y_train, x_test)
        for name, values in fold_scores.items():
            predictions[name][test_indices] = values

    return predictions


def elementwise_interaction(entries: List[Dict], left_field: str, right_field: str) -> torch.Tensor:
    rows = []
    for entry in entries:
        left_items = sorted(entry[left_field].items(), key=lambda kv: int(kv[0]))
        right_items = sorted(entry[right_field].items(), key=lambda kv: int(kv[0]))
        assert [k for k, _ in left_items] == [k for k, _ in right_items]
        rows.append(
            torch.cat(
                [
                    (left.to(torch.float32) * right.to(torch.float32))
                    for (_, left), (_, right) in zip(left_items, right_items)
                ],
                dim=0,
            )
        )
    return torch.stack(rows, dim=0)


def fit_low_rank_bilinear_probe(
    x_ctx_train: torch.Tensor,
    x_delta_train: torch.Tensor,
    y_train: torch.Tensor,
    x_ctx_test: torch.Tensor,
    x_delta_test: torch.Tensor,
    rank: int = 32,
    epochs: int = 300,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
) -> torch.Tensor:
    x_ctx_train, x_ctx_test = normalize_train_test(x_ctx_train, x_ctx_test)
    x_delta_train, x_delta_test = normalize_train_test(x_delta_train, x_delta_test)

    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_ctx_test),), float(prior.item()), dtype=torch.float32)

    effective_rank = min(rank, x_ctx_train.shape[0], x_ctx_train.shape[1], x_delta_train.shape[1])

    class LowRankBilinearProbe(torch.nn.Module):
        def __init__(self, d_ctx: int, d_delta: int, r: int) -> None:
            super().__init__()
            self.ctx_proj = torch.nn.Linear(d_ctx, r, bias=False)
            self.delta_proj = torch.nn.Linear(d_delta, r, bias=False)
            self.ctx_linear = torch.nn.Linear(d_ctx, 1)
            self.delta_linear = torch.nn.Linear(d_delta, 1)
            self.bias = torch.nn.Parameter(torch.zeros(1))

        def forward(self, x_ctx: torch.Tensor, x_delta: torch.Tensor) -> torch.Tensor:
            bilinear = (self.ctx_proj(x_ctx) * self.delta_proj(x_delta)).sum(dim=1, keepdim=True)
            return self.ctx_linear(x_ctx) + self.delta_linear(x_delta) + bilinear + self.bias

    model = LowRankBilinearProbe(x_ctx_train.shape[1], x_delta_train.shape[1], effective_rank)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x_ctx_train, x_delta_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        return torch.sigmoid(model(x_ctx_test, x_delta_test).squeeze(-1)).cpu()


def grouped_cv_bilinear_scores(
    context_features: torch.Tensor,
    delta_features: torch.Tensor,
    labels: torch.Tensor,
    groups: List[str],
) -> torch.Tensor:
    group_to_indices: Dict[str, List[int]] = {}
    for idx, group in enumerate(groups):
        group_to_indices.setdefault(group, []).append(idx)

    predictions = torch.zeros(len(labels), dtype=torch.float32)
    for group, test_indices in group_to_indices.items():
        train_indices = [i for i, g in enumerate(groups) if g != group]
        torch.manual_seed(0)
        predictions[test_indices] = fit_low_rank_bilinear_probe(
            context_features[train_indices],
            delta_features[train_indices],
            labels[train_indices],
            context_features[test_indices],
            delta_features[test_indices],
        )
    return predictions


def kmeans_prototypes(
    x: torch.Tensor,
    num_clusters: int = 4,
    num_iters: int = 15,
) -> torch.Tensor:
    if len(x) == 0:
        return torch.zeros((0, x.shape[1]), dtype=torch.float32)
    k = min(num_clusters, len(x))
    centroids = x[:k].clone()
    for _ in range(num_iters):
        distances = torch.cdist(x, centroids)
        assignment = distances.argmin(dim=1)
        new_centroids = []
        for idx in range(k):
            members = x[assignment == idx]
            if len(members) == 0:
                new_centroids.append(centroids[idx])
            else:
                new_centroids.append(members.mean(dim=0))
        centroids = torch.stack(new_centroids, dim=0)
    return centroids


def clue_style_scores(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    num_clusters: int = 4,
) -> torch.Tensor:
    x_train, x_test = normalize_train_test(x_train, x_test)
    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        return torch.zeros(len(x_test), dtype=torch.float32)

    pos_proto = kmeans_prototypes(pos, num_clusters=num_clusters)
    neg_proto = kmeans_prototypes(neg, num_clusters=num_clusters)

    pos_dist = torch.cdist(x_test, pos_proto).min(dim=1).values
    neg_dist = torch.cdist(x_test, neg_proto).min(dim=1).values
    return (neg_dist - pos_dist).cpu()


def grouped_cv_clue_scores(
    features: torch.Tensor,
    labels: torch.Tensor,
    groups: List[str],
    num_clusters: int = 4,
) -> torch.Tensor:
    group_to_indices: Dict[str, List[int]] = {}
    for idx, group in enumerate(groups):
        group_to_indices.setdefault(group, []).append(idx)

    predictions = torch.zeros(len(labels), dtype=torch.float32)
    for group, test_indices in group_to_indices.items():
        train_indices = [i for i, g in enumerate(groups) if g != group]
        predictions[test_indices] = clue_style_scores(
            features[train_indices],
            labels[train_indices],
            features[test_indices],
            num_clusters=num_clusters,
        )
    return predictions


def summarize_baseline(
    entries: List[Dict],
    labels: torch.Tensor,
    scores: torch.Tensor,
    baseline_name: str,
    feature_dim: int,
) -> Dict[str, float]:
    metrics = {"feature_dim": feature_dim}
    if baseline_name.endswith("centroid_cosine") or baseline_name.endswith("clue_proto"):
        threshold = 0.0
        preds = (scores >= threshold).long()
        metrics.update(
            {
                "auroc": auroc_score(labels, scores),
                "accuracy_at_zero": float((preds == labels).float().mean().item()),
                "earliest_fail_localization": earliest_fail_localization(entries, scores),
                "mean_score_positive": float(scores[labels == 1].mean().item()) if int((labels == 1).sum().item()) else float("nan"),
                "mean_score_negative": float(scores[labels == 0].mean().item()) if int((labels == 0).sum().item()) else float("nan"),
                "score_threshold_note": "geometry-style score; no calibrated probability metrics",
            }
        )
        return metrics

    preds = (scores >= 0.5).long()
    metrics.update(
        {
            "auroc": auroc_score(labels, scores),
            "accuracy": float((preds == labels).float().mean().item()),
            "brier": brier_score(labels, scores),
            "earliest_fail_localization": earliest_fail_localization(entries, scores),
        }
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run scorer-conditioned Lean object-gate comparisons.")
    parser.add_argument("--features", required=True, help="Path to boundary_states.pt")
    parser.add_argument("--raw-jsonl", required=True, help="Path to corresponding raw jsonl slice")
    parser.add_argument("--output", required=True, help="Path to output result json")
    args = parser.parse_args()

    feature_entries = load_features(Path(args.features))
    raw_rows = read_jsonl(Path(args.raw_jsonl))
    theorem_ids = {row["theorem_id"] for row in raw_rows}

    labels = torch.tensor([entry["local_sound"] for entry in feature_entries], dtype=torch.long)
    groups = [entry["theorem_id"] for entry in feature_entries]

    feature_sets = {
        "post": tensor_from_entries(feature_entries, "h_plus"),
        "transition": tensor_from_entries(feature_entries, "delta_h"),
        "conditional_transition": concat_fields(feature_entries, ["h_minus", "delta_h"]),
        "interaction_transition": torch.cat(
            [
                tensor_from_entries(feature_entries, "delta_h"),
                elementwise_interaction(feature_entries, "h_minus", "delta_h"),
            ],
            dim=1,
        ),
    }

    results = {
        "features": args.features,
        "raw_jsonl": args.raw_jsonl,
        "num_examples": len(feature_entries),
        "num_theorems": len(theorem_ids),
        "positive_steps": int(labels.sum().item()),
        "negative_steps": int((labels == 0).sum().item()),
        "baselines": {},
    }

    for representation_name, feats in feature_sets.items():
        score_map = grouped_cv_scores(feats, labels, groups)
        for scorer_name, scores in score_map.items():
            baseline_name = f"{representation_name}_{scorer_name}"
            results["baselines"][baseline_name] = summarize_baseline(
                feature_entries,
                labels,
                scores,
                baseline_name,
                int(feats.shape[1]),
            )

    context_features = tensor_from_entries(feature_entries, "h_minus")
    delta_features = tensor_from_entries(feature_entries, "delta_h")
    bilinear_scores = grouped_cv_bilinear_scores(context_features, delta_features, labels, groups)
    results["baselines"]["conditional_bilinear_prob"] = summarize_baseline(
        feature_entries,
        labels,
        bilinear_scores,
        "conditional_bilinear_prob",
        int(context_features.shape[1] + delta_features.shape[1]),
    )
    results["baselines"]["conditional_bilinear_prob"]["structure"] = "linear(h_minus)+linear(delta_h)+low_rank_bilinear(h_minus, delta_h)"
    results["baselines"]["conditional_bilinear_prob"]["rank"] = 32

    clue_scores = grouped_cv_clue_scores(delta_features, labels, groups, num_clusters=4)
    results["baselines"]["transition_clue_proto"] = summarize_baseline(
        feature_entries,
        labels,
        clue_scores,
        "transition_clue_proto",
        int(delta_features.shape[1]),
    )
    results["baselines"]["transition_clue_proto"]["structure"] = "normalized delta_h + per-class kmeans prototypes + nearest-prototype distance gap"
    results["baselines"]["transition_clue_proto"]["num_clusters_per_class"] = 4

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
