from __future__ import annotations

from collections import defaultdict

from civic_prm.metrics import binary_accuracy, binary_auroc


def _normalized_score(row: dict) -> float:
    score = float(row["score"])
    return score / 100.0 if score > 1.0 else score


def compute_processbench_metrics(rows: list[dict]) -> dict:
    scores = [_normalized_score(row) for row in rows]
    gold = [int(row["gold_valid"]) for row in rows]
    preds = [int(score >= 0.5) for score in scores]

    by_domain = {}
    for domain in sorted({row["domain"] for row in rows}):
        domain_rows = [row for row in rows if row["domain"] == domain]
        by_domain[domain] = {
            "ordinary_accuracy": round(
                binary_accuracy(
                    [row["gold_valid"] for row in domain_rows],
                    [int(_normalized_score(row) >= 0.5) for row in domain_rows],
                ),
                4,
            ),
            "ordinary_auroc": round(
                binary_auroc(
                    [row["gold_valid"] for row in domain_rows],
                    [_normalized_score(row) for row in domain_rows],
                ),
                4,
            ),
        }

    by_answer_variant = defaultdict(list)
    by_process_variant = defaultdict(list)
    for row in rows:
        by_answer_variant[row["answer_variant"]].append(_normalized_score(row))
        by_process_variant[row["process_variant"]].append(_normalized_score(row))

    invalid_answer_gap = None
    invalid_correct = [_normalized_score(row) for row in rows if row["process_variant"] == "invalid" and row["answer_variant"] == "correct"]
    invalid_wrong = [_normalized_score(row) for row in rows if row["process_variant"] == "invalid" and row["answer_variant"] == "wrong"]
    if invalid_correct and invalid_wrong:
        invalid_answer_gap = round(sum(invalid_correct) / len(invalid_correct) - sum(invalid_wrong) / len(invalid_wrong), 4)

    return {
        "num_scored_traces": len(rows),
        "ordinary_accuracy": round(binary_accuracy(gold, preds), 4),
        "ordinary_auroc": round(binary_auroc(gold, scores), 4),
        "mean_score_by_answer_variant": {
            key: round(sum(values) / len(values), 4)
            for key, values in sorted(by_answer_variant.items())
        },
        "mean_score_by_process_variant": {
            key: round(sum(values) / len(values), 4)
            for key, values in sorted(by_process_variant.items())
        },
        "invalid_answer_gap": invalid_answer_gap,
        "by_domain": by_domain,
    }


def compute_processbench_prefix_metrics(rows: list[dict]) -> dict:
    metrics = compute_processbench_metrics(rows)

    by_source = defaultdict(dict)
    for row in rows:
        source_trace_id = row.get("source_trace_id")
        prefix_length = row.get("source_prefix_length")
        if source_trace_id is None or prefix_length is None:
            continue
        by_source[source_trace_id][prefix_length] = row

    boundary_drops = []
    boundary_drops_by_domain = defaultdict(list)
    for prefixes in by_source.values():
        example_row = next(iter(prefixes.values()))
        first_incorrect_step = example_row.get("first_incorrect_step")
        if not isinstance(first_incorrect_step, int) or first_incorrect_step <= 0:
            continue
        before_row = prefixes.get(first_incorrect_step)
        at_row = prefixes.get(first_incorrect_step + 1)
        if before_row is None or at_row is None:
            continue
        drop = _normalized_score(before_row) - _normalized_score(at_row)
        boundary_drops.append(drop)
        boundary_drops_by_domain[example_row["domain"]].append(drop)

    metrics["boundary_drop_mean"] = round(sum(boundary_drops) / len(boundary_drops), 4) if boundary_drops else None
    metrics["boundary_drop_by_domain"] = {
        domain: round(sum(values) / len(values), 4)
        for domain, values in sorted(boundary_drops_by_domain.items())
    }
    metrics["num_boundary_pairs"] = len(boundary_drops)
    return metrics
