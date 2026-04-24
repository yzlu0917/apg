from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from civic_prm.acceptance import ACCEPTANCE_MODES, classify_feedback_reason, summarize_pair_calls


def _load_reviews(review_path: Path) -> dict[tuple[str, str, str, str, int], list[dict[str, Any]]]:
    by_pair: dict[tuple[str, str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    with review_path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if "answer_variant_group" not in row or "candidate_index" not in row:
                continue
            key = (
                row["quartet_id"],
                row["domain"],
                row["verbalizer_id"],
                row["answer_variant_group"],
                row["candidate_index"],
            )
            row["bucket"] = classify_feedback_reason(row.get("reason", ""))
            by_pair[key].append(row)
    return by_pair


def _summarize_run(label: str, summary_path: Path, review_path: Path) -> dict[str, Any]:
    summary = json.loads(summary_path.read_text())
    by_pair = _load_reviews(review_path)
    bucket_counts = Counter()
    bucket_counts_by_domain: dict[str, Counter] = defaultdict(Counter)
    for calls in by_pair.values():
        for call in calls:
            bucket = call["bucket"]
            bucket_counts[bucket] += 1
            bucket_counts_by_domain[call["domain"]][bucket] += 1

    modes = {}
    for mode in ACCEPTANCE_MODES:
        quartet_groups: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
        for (quartet_id, domain, verbalizer_id, answer_variant, candidate_index), calls in by_pair.items():
            pair_summary = summarize_pair_calls(calls, mode=mode)
            quartet_groups[(quartet_id, domain, verbalizer_id)][answer_variant].append(
                {
                    "candidate_index": candidate_index,
                    "avg_detectability_penalty": pair_summary["avg_detectability_penalty"],
                    "invalid_pick_rate": pair_summary["invalid_pick_rate"],
                    "review_buckets": pair_summary["review_buckets"],
                }
            )

        quartet_results = []
        num_selected = 0
        for (quartet_id, domain, verbalizer_id), answer_groups in sorted(quartet_groups.items()):
            correct_best = min(
                answer_groups["correct"],
                key=lambda item: (
                    item["avg_detectability_penalty"],
                    item["invalid_pick_rate"],
                    item["candidate_index"],
                ),
            )
            swapped_best = min(
                answer_groups["swapped"],
                key=lambda item: (
                    item["avg_detectability_penalty"],
                    item["invalid_pick_rate"],
                    item["candidate_index"],
                ),
            )
            accepted = (
                correct_best["avg_detectability_penalty"] <= 0.8
                and swapped_best["avg_detectability_penalty"] <= 0.8
            )
            num_selected += int(accepted)
            quartet_results.append(
                {
                    "quartet_id": quartet_id,
                    "domain": domain,
                    "verbalizer_id": verbalizer_id,
                    "correct_best": correct_best,
                    "swapped_best": swapped_best,
                    "accepted_under_mode": accepted,
                }
            )

        modes[mode] = {
            "selected_quartets": num_selected,
            "quartet_results": quartet_results,
        }

    return {
        "label": label,
        "summary_path": str(summary_path),
        "review_path": str(review_path),
        "strict_usage": summary.get("usage", {}),
        "bucket_counts": dict(bucket_counts),
        "bucket_counts_by_domain": {
            domain: dict(counter) for domain, counter in sorted(bucket_counts_by_domain.items())
        },
        "modes": modes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Run triple in the form label:summary_json:reviews_jsonl",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    runs = []
    for item in args.run:
        label, summary_path, review_path = item.split(":", 2)
        runs.append(
            _summarize_run(
                label=label,
                summary_path=Path(summary_path),
                review_path=Path(review_path),
            )
        )

    output = {
        "runs": runs,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
