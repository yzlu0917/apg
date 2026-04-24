from __future__ import annotations

import copy
import math
from collections import Counter, defaultdict

import torch
import torch.nn.functional as F

from civic_prm.metrics import binary_accuracy, binary_auroc


def _standardize(
    train_features: torch.Tensor,
    *other_features: torch.Tensor,
) -> tuple[torch.Tensor, ...]:
    mean = train_features.mean(dim=0, keepdim=True)
    std = train_features.std(dim=0, keepdim=True).clamp(min=1e-6)
    normalized = [(train_features - mean) / std]
    normalized.extend((features - mean) / std for features in other_features)
    return tuple(normalized)


def _build_pair_indices(records: list[dict]) -> list[tuple[int, int]]:
    grouped: dict[tuple[str, str], dict[str, list[int]]] = defaultdict(lambda: {"valid": [], "invalid": []})
    for index, record in enumerate(records):
        key = (record["quartet_id"], record["verbalizer_id"])
        grouped[key][record["process_variant"]].append(index)
    pairs = []
    for group in grouped.values():
        for valid_index in group["valid"]:
            for invalid_index in group["invalid"]:
                pairs.append((valid_index, invalid_index))
    return pairs


def _build_local_pair_indices(records: list[dict]) -> list[tuple[int, int]]:
    grouped: dict[tuple[str, str, str], dict[str, list[int]]] = defaultdict(
        lambda: {"valid": [], "invalid": []}
    )
    for index, record in enumerate(records):
        key = (record["quartet_id"], record["verbalizer_id"], record["answer_variant"])
        grouped[key][record["process_variant"]].append(index)
    pairs = []
    for group in grouped.values():
        for valid_index in group["valid"]:
            for invalid_index in group["invalid"]:
                pairs.append((valid_index, invalid_index))
    return pairs


def _build_swap_invariance_indices(records: list[dict]) -> list[tuple[int, int]]:
    grouped: dict[tuple[str, str, str], dict[str, list[int]]] = defaultdict(
        lambda: {"correct": [], "swapped": []}
    )
    for index, record in enumerate(records):
        key = (record["quartet_id"], record["verbalizer_id"], record["process_variant"])
        grouped[key][record["answer_variant"]].append(index)
    pairs = []
    for group in grouped.values():
        for correct_index in group["correct"]:
            for swapped_index in group["swapped"]:
                pairs.append((correct_index, swapped_index))
    return pairs


def _collect_scores(
    model: torch.nn.Module,
    features: torch.Tensor,
    records: list[dict],
) -> list[dict]:
    with torch.inference_mode():
        logits = model(features).squeeze(-1).cpu()
        probs = torch.sigmoid(logits).tolist()
    rows = []
    for record, logit, prob in zip(records, logits.tolist(), probs, strict=True):
        rows.append(
            {
                "trace_id": record["trace_id"],
                "quartet_id": record["quartet_id"],
                "domain": record["domain"],
                "verbalizer_id": record["verbalizer_id"],
                "process_variant": record["process_variant"],
                "answer_variant": record["answer_variant"],
                "gold_valid": int(record["is_valid_process"]),
                "logit": float(logit),
                "score": float(prob),
            }
        )
    return rows


def _selection_metric(metrics: dict) -> float:
    amcd = 0.0 if math.isnan(metrics["amcd"]) else metrics["amcd"]
    ass_total = 0.0 if math.isnan(metrics["ass_total"]) else metrics["ass_total"]
    ordinary_auroc = 0.5 if math.isnan(metrics["ordinary_auroc"]) else metrics["ordinary_auroc"]
    return amcd - ass_total + 0.05 * ordinary_auroc


def mine_hard_negative_indices(
    model: torch.nn.Module,
    train_features: torch.Tensor,
    train_records: list[dict],
    top_fraction: float = 0.25,
    min_count: int = 8,
    strategy: str = "global",
    focus_domain: str | None = None,
    focus_fraction: float = 0.5,
) -> tuple[list[int], dict]:
    scored_rows = score_baseline(
        model=model,
        train_features=train_features,
        eval_features=train_features,
        eval_records=train_records,
    )
    candidates = []
    for index, (record, row) in enumerate(zip(train_records, scored_rows, strict=True)):
        if not record["is_valid_process"]:
            candidates.append(
                {
                    "index": index,
                    "trace_id": record["trace_id"],
                    "domain": record["domain"],
                    "score": row["score"],
                }
            )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    target_count = int(round(len(candidates) * top_fraction))
    target_count = max(min_count, target_count)
    target_count = min(len(candidates), target_count)
    if strategy == "global":
        selected = candidates[:target_count]
    else:
        by_domain: dict[str, list[dict]] = defaultdict(list)
        for item in candidates:
            by_domain[item["domain"]].append(item)
        for domain_candidates in by_domain.values():
            domain_candidates.sort(key=lambda item: item["score"], reverse=True)

        selected = []
        remaining_by_domain = {domain: items[:] for domain, items in by_domain.items()}
        domains = sorted(remaining_by_domain)
        if strategy == "domain_balanced":
            base_quota = target_count // len(domains)
            remainder = target_count % len(domains)
            for domain_index, domain in enumerate(domains):
                quota = base_quota + int(domain_index < remainder)
                take = remaining_by_domain[domain][:quota]
                selected.extend(take)
                remaining_by_domain[domain] = remaining_by_domain[domain][quota:]
        elif strategy == "focus_domain":
            if focus_domain is None:
                raise ValueError("focus_domain strategy requires focus_domain")
            if focus_domain not in remaining_by_domain:
                raise ValueError(f"focus_domain {focus_domain} missing from candidates")
            focus_quota = max(1, int(round(target_count * focus_fraction)))
            focus_quota = min(focus_quota, len(remaining_by_domain[focus_domain]))
            selected.extend(remaining_by_domain[focus_domain][:focus_quota])
            remaining_by_domain[focus_domain] = remaining_by_domain[focus_domain][focus_quota:]
            other_domains = [domain for domain in domains if domain != focus_domain]
            remaining_target = target_count - len(selected)
            if other_domains and remaining_target > 0:
                base_quota = remaining_target // len(other_domains)
                remainder = remaining_target % len(other_domains)
                for domain_index, domain in enumerate(other_domains):
                    quota = base_quota + int(domain_index < remainder)
                    take = remaining_by_domain[domain][:quota]
                    selected.extend(take)
                    remaining_by_domain[domain] = remaining_by_domain[domain][quota:]
        else:
            raise ValueError(f"unsupported hard-neg strategy: {strategy}")

        if len(selected) < target_count:
            leftovers = []
            for domain in domains:
                leftovers.extend(remaining_by_domain[domain])
            leftovers.sort(key=lambda item: item["score"], reverse=True)
            selected.extend(leftovers[: target_count - len(selected)])

    score_values = [item["score"] for item in selected]
    summary = {
        "top_fraction": top_fraction,
        "min_count": min_count,
        "strategy": strategy,
        "focus_domain": focus_domain,
        "focus_fraction": focus_fraction if strategy == "focus_domain" else None,
        "num_invalid_candidates": len(candidates),
        "num_selected_hard_negs": len(selected),
        "selected_domains": dict(Counter(item["domain"] for item in selected)),
        "selected_trace_ids": [item["trace_id"] for item in selected],
        "score_range": {
            "max": round(max(score_values), 4) if score_values else math.nan,
            "min": round(min(score_values), 4) if score_values else math.nan,
        },
    }
    return [item["index"] for item in selected], summary


def compute_verifier_metrics(rows: list[dict]) -> dict:
    scores = [row["score"] for row in rows]
    gold = [row["gold_valid"] for row in rows]
    preds = [int(score >= 0.5) for score in scores]

    by_amcd = {}
    for row in rows:
        key = (row["quartet_id"], row["verbalizer_id"], row["answer_variant"])
        by_amcd.setdefault(key, {})[row["process_variant"]] = row["score"]

    amcd_hits = []
    for pair in by_amcd.values():
        if "valid" in pair and "invalid" in pair:
            amcd_hits.append(int(pair["valid"] > pair["invalid"]))

    by_swap = {}
    for row in rows:
        key = (row["quartet_id"], row["verbalizer_id"], row["process_variant"])
        by_swap.setdefault(key, {})[row["answer_variant"]] = row["score"]

    swap_deltas = []
    for pair in by_swap.values():
        if "correct" in pair and "swapped" in pair:
            swap_deltas.append(abs(pair["correct"] - pair["swapped"]))

    by_domain = {}
    for domain in sorted({row["domain"] for row in rows}):
        domain_rows = [row for row in rows if row["domain"] == domain]
        by_domain[domain] = {
            "ordinary_accuracy": round(
                binary_accuracy(
                    [row["gold_valid"] for row in domain_rows],
                    [int(row["score"] >= 0.5) for row in domain_rows],
                ),
                4,
            ),
            "ordinary_auroc": round(
                binary_auroc(
                    [row["gold_valid"] for row in domain_rows],
                    [row["score"] for row in domain_rows],
                ),
                4,
            ),
        }

    return {
        "num_scored_traces": len(rows),
        "ordinary_accuracy": round(binary_accuracy(gold, preds), 4),
        "ordinary_auroc": round(binary_auroc(gold, scores), 4),
        "amcd": round(sum(amcd_hits) / len(amcd_hits), 4) if amcd_hits else math.nan,
        "ass_total": round(sum(swap_deltas) / len(swap_deltas), 4) if swap_deltas else math.nan,
        "by_domain": by_domain,
    }


def train_bce_head(
    train_features: torch.Tensor,
    train_labels: torch.Tensor,
    val_features: torch.Tensor,
    val_labels: torch.Tensor,
    epochs: int = 250,
    learning_rate: float = 1e-2,
    patience: int = 30,
) -> torch.nn.Module:
    train_features, val_features = _standardize(train_features, val_features)
    model = torch.nn.Linear(train_features.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-3)
    best_state = copy.deepcopy(model.state_dict())
    best_metric = -float("inf")
    stale_epochs = 0

    for _ in range(epochs):
        model.train()
        logits = model(train_features).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, train_labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.inference_mode():
            val_probs = torch.sigmoid(model(val_features).squeeze(-1)).tolist()
        metric = binary_auroc(val_labels.tolist(), val_probs)
        if metric > best_metric:
            best_metric = metric
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= patience:
            break

    best_model = torch.nn.Linear(train_features.shape[1], 1)
    best_model.load_state_dict(best_state)
    return best_model


def train_pairwise_head(
    train_features: torch.Tensor,
    train_records: list[dict],
    val_features: torch.Tensor,
    val_records: list[dict],
    epochs: int = 250,
    learning_rate: float = 1e-2,
    patience: int = 30,
) -> torch.nn.Module:
    train_features, val_features = _standardize(train_features, val_features)
    train_pairs = _build_pair_indices(train_records)
    val_pairs = _build_pair_indices(val_records)
    model = torch.nn.Linear(train_features.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-3)
    best_state = copy.deepcopy(model.state_dict())
    best_metric = -float("inf")
    stale_epochs = 0

    for _ in range(epochs):
        model.train()
        train_logits = model(train_features).squeeze(-1)
        pos = torch.stack([train_logits[left] for left, _ in train_pairs])
        neg = torch.stack([train_logits[right] for _, right in train_pairs])
        loss = F.softplus(-(pos - neg)).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.inference_mode():
            val_logits = model(val_features).squeeze(-1)
        pair_hits = []
        for left, right in val_pairs:
            pair_hits.append(int(val_logits[left] > val_logits[right]))
        metric = sum(pair_hits) / len(pair_hits) if pair_hits else 0.0
        if metric > best_metric:
            best_metric = metric
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= patience:
            break

    best_model = torch.nn.Linear(train_features.shape[1], 1)
    best_model.load_state_dict(best_state)
    return best_model


def train_repair_head(
    train_features: torch.Tensor,
    train_records: list[dict],
    train_labels: torch.Tensor,
    val_features: torch.Tensor,
    val_records: list[dict],
    val_labels: torch.Tensor,
    lambda_local_pair: float = 1.0,
    lambda_cond_swap: float = 1.0,
    lambda_hard_neg: float = 0.0,
    hard_neg_indices: list[int] | None = None,
    epochs: int = 250,
    learning_rate: float = 1e-2,
    patience: int = 30,
) -> torch.nn.Module:
    train_features, val_features = _standardize(train_features, val_features)
    local_pairs = _build_local_pair_indices(train_records)
    swap_pairs = _build_swap_invariance_indices(train_records)
    model = torch.nn.Linear(train_features.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-3)
    best_state = copy.deepcopy(model.state_dict())
    best_metric = -float("inf")
    stale_epochs = 0

    for _ in range(epochs):
        model.train()
        train_logits = model(train_features).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(train_logits, train_labels)
        if lambda_local_pair > 0 and local_pairs:
            pos = torch.stack([train_logits[left] for left, _ in local_pairs])
            neg = torch.stack([train_logits[right] for _, right in local_pairs])
            loss = loss + lambda_local_pair * F.softplus(-(pos - neg)).mean()
        if lambda_cond_swap > 0 and swap_pairs:
            correct_logits = torch.stack([train_logits[left] for left, _ in swap_pairs])
            swapped_logits = torch.stack([train_logits[right] for _, right in swap_pairs])
            loss = loss + lambda_cond_swap * (correct_logits - swapped_logits).pow(2).mean()
        if lambda_hard_neg > 0 and hard_neg_indices:
            hard_neg_logits = torch.stack([train_logits[index] for index in hard_neg_indices])
            loss = loss + lambda_hard_neg * F.softplus(hard_neg_logits).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        model.eval()
        val_rows = _collect_scores(model, val_features, val_records)
        metrics = compute_verifier_metrics(val_rows)
        metric = _selection_metric(metrics)
        if metric > best_metric:
            best_metric = metric
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= patience:
            break

    best_model = torch.nn.Linear(train_features.shape[1], 1)
    best_model.load_state_dict(best_state)
    return best_model


def score_baseline(
    model: torch.nn.Module,
    train_features: torch.Tensor,
    eval_features: torch.Tensor,
    eval_records: list[dict],
) -> list[dict]:
    mean = train_features.mean(dim=0, keepdim=True)
    std = train_features.std(dim=0, keepdim=True).clamp(min=1e-6)
    normalized_eval = (eval_features - mean) / std
    model.eval()
    return _collect_scores(model, normalized_eval, eval_records)
