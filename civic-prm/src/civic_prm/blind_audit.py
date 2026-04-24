from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


CHOICE_ALIASES = {
    "trace 1": "trace_1",
    "trace1": "trace_1",
    "1": "trace_1",
    "t1": "trace_1",
    "trace 2": "trace_2",
    "trace2": "trace_2",
    "2": "trace_2",
    "t2": "trace_2",
    "both": "both",
    "neither": "neither",
}


def load_answer_key(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalize_choice(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    return CHOICE_ALIASES.get(normalized, "missing")


def _parse_confidence(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        parsed = int(stripped)
    except ValueError:
        return None
    if 1 <= parsed <= 5:
        return parsed
    return None


def _choice_outcome(entry: dict[str, Any], choice: str) -> str:
    if choice in {"missing", "neither", "both"}:
        return choice
    role = entry[f"{choice}_role"]
    return "invalid" if role.startswith("invalid") else "valid"


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 4)


def _summarize_scored_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(row["choice"] for row in rows)
    outcome_counts = Counter(row["outcome"] for row in rows)
    answered_rows = [row for row in rows if row["choice"] != "missing"]
    confidence_values = [row["confidence"] for row in answered_rows if row["confidence"] is not None]
    total_items = len(rows)
    answered_items = len(answered_rows)
    return {
        "num_items": total_items,
        "num_answered": answered_items,
        "label_counts": dict(label_counts),
        "outcome_counts": dict(outcome_counts),
        "avg_confidence_answered": round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else None,
        "any_artifact_flag_rate": _rate(sum(1 for row in rows if row["choice"] in {"trace_1", "trace_2", "both"}), total_items),
        "invalid_trace_flag_rate": _rate(outcome_counts.get("invalid", 0), total_items),
        "valid_trace_flag_rate": _rate(outcome_counts.get("valid", 0), total_items),
        "both_flag_rate": _rate(outcome_counts.get("both", 0), total_items),
        "neither_rate": _rate(outcome_counts.get("neither", 0), total_items),
        "missing_rate": _rate(outcome_counts.get("missing", 0), total_items),
        "invalid_minus_valid_flag_rate": round(
            _rate(outcome_counts.get("invalid", 0), total_items)
            - _rate(outcome_counts.get("valid", 0), total_items),
            4,
        ),
    }


def _score_one_response(
    answer_key: list[dict[str, Any]],
    response_path: str | Path,
) -> dict[str, Any]:
    path = Path(response_path)
    rows_by_item: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = row.get("item_id", "").strip()
            if item_id:
                rows_by_item[item_id] = row

    scored_rows: list[dict[str, Any]] = []
    domain_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in answer_key:
        raw_row = rows_by_item.get(entry["item_id"], {})
        choice = _normalize_choice(raw_row.get("more_artificial", ""))
        confidence = _parse_confidence(raw_row.get("confidence", ""))
        scored = {
            "item_id": entry["item_id"],
            "quartet_id": entry["quartet_id"],
            "domain": entry["domain"],
            "choice": choice,
            "confidence": confidence,
            "notes": raw_row.get("notes", "").strip(),
            "outcome": _choice_outcome(entry, choice),
            "trace_1_role": entry["trace_1_role"],
            "trace_2_role": entry["trace_2_role"],
        }
        scored_rows.append(scored)
        domain_rows[entry["domain"]].append(scored)

    return {
        "reviewer_id": path.stem,
        "response_path": str(path),
        "summary": _summarize_scored_rows(scored_rows),
        "by_domain": {
            domain: _summarize_scored_rows(rows)
            for domain, rows in sorted(domain_rows.items())
        },
        "items": scored_rows,
    }


def _pairwise_agreement(scored_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agreements: list[dict[str, Any]] = []
    for left, right in combinations(scored_reviews, 2):
        left_rows = {row["item_id"]: row for row in left["items"]}
        right_rows = {row["item_id"]: row for row in right["items"]}
        overlap = sorted(set(left_rows) & set(right_rows))
        compared = [
            item_id
            for item_id in overlap
            if left_rows[item_id]["choice"] != "missing" and right_rows[item_id]["choice"] != "missing"
        ]
        exact = sum(
            1
            for item_id in compared
            if left_rows[item_id]["choice"] == right_rows[item_id]["choice"]
        )
        agreements.append(
            {
                "reviewer_a": left["reviewer_id"],
                "reviewer_b": right["reviewer_id"],
                "num_overlap_answered": len(compared),
                "exact_label_agreement": _rate(exact, len(compared)),
            }
        )
    return agreements


def score_blind_audit(
    answer_key_path: str | Path,
    response_paths: list[str | Path],
) -> dict[str, Any]:
    answer_key = load_answer_key(answer_key_path)
    scored_reviews = [_score_one_response(answer_key, path) for path in response_paths]
    pooled_rows = [row for review in scored_reviews for row in review["items"]]
    pooled_domains: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pooled_rows:
        pooled_domains[row["domain"]].append(row)
    return {
        "answer_key_path": str(answer_key_path),
        "num_reviewers": len(scored_reviews),
        "num_items": len(answer_key),
        "reviewers": scored_reviews,
        "pooled_summary": _summarize_scored_rows(pooled_rows),
        "pooled_by_domain": {
            domain: _summarize_scored_rows(rows)
            for domain, rows in sorted(pooled_domains.items())
        },
        "pairwise_agreement": _pairwise_agreement(scored_reviews),
    }


def render_blind_audit_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Blind Audit Score Report",
        "",
        f"- Answer key: `{summary['answer_key_path']}`",
        f"- Reviewers: `{summary['num_reviewers']}`",
        f"- Items per reviewer: `{summary['num_items']}`",
        "",
        "## Pooled Summary",
        "",
    ]
    pooled = summary["pooled_summary"]
    lines.extend(
        [
            f"- Answered: `{pooled['num_answered']} / {pooled['num_items']}`",
            f"- Invalid-trace flag rate: `{pooled['invalid_trace_flag_rate']}`",
            f"- Valid-trace flag rate: `{pooled['valid_trace_flag_rate']}`",
            f"- Both rate: `{pooled['both_flag_rate']}`",
            f"- Neither rate: `{pooled['neither_rate']}`",
            f"- Invalid-minus-valid flag rate: `{pooled['invalid_minus_valid_flag_rate']}`",
            "",
            "## Reviewer Breakdown",
            "",
        ]
    )
    for reviewer in summary["reviewers"]:
        reviewer_summary = reviewer["summary"]
        lines.extend(
            [
                f"### {reviewer['reviewer_id']}",
                "",
                f"- Response file: `{reviewer['response_path']}`",
                f"- Answered: `{reviewer_summary['num_answered']} / {reviewer_summary['num_items']}`",
                f"- Invalid-trace flag rate: `{reviewer_summary['invalid_trace_flag_rate']}`",
                f"- Valid-trace flag rate: `{reviewer_summary['valid_trace_flag_rate']}`",
                f"- Both rate: `{reviewer_summary['both_flag_rate']}`",
                f"- Neither rate: `{reviewer_summary['neither_rate']}`",
                "",
            ]
        )
    if summary["pairwise_agreement"]:
        lines.extend(["## Pairwise Agreement", ""])
        for item in summary["pairwise_agreement"]:
            lines.append(
                f"- `{item['reviewer_a']}` vs `{item['reviewer_b']}`: "
                f"`{item['exact_label_agreement']}` over `{item['num_overlap_answered']}` answered overlaps"
            )
        lines.append("")
    return "\n".join(lines)
