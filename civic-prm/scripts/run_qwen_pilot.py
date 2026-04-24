from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.prompt_verifier import compute_pilot_metrics, load_model, score_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a Qwen Week 1 pilot verifier on generated traces.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument("--max-quartets", type=int, default=6)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/pilot/qwen_pilot_results.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    by_domain: dict[str, set[str]] = {}
    for record in records:
        by_domain.setdefault(record["domain"], set()).add(record["quartet_id"])
    ordered_domains = sorted(by_domain)
    ordered_quartets = {domain: sorted(quartet_ids) for domain, quartet_ids in by_domain.items()}
    quartet_ids = []
    cursor = 0
    while len(quartet_ids) < args.max_quartets:
        added = False
        for domain in ordered_domains:
            domain_quartets = ordered_quartets[domain]
            if cursor < len(domain_quartets):
                quartet_ids.append(domain_quartets[cursor])
                added = True
                if len(quartet_ids) == args.max_quartets:
                    break
        if not added:
            break
        cursor += 1
    selected = [record for record in records if record["quartet_id"] in quartet_ids]
    tokenizer, model = load_model(args.model_root)
    all_scores = []
    for answer_visible in [True, False]:
        for record in selected:
            all_scores.append(score_record(tokenizer, model, record, answer_visible=answer_visible))

    visible_scores = [row for row in all_scores if row["answer_visible"]]
    masked_scores = [row for row in all_scores if not row["answer_visible"]]
    summary = {
        "selected_quartets": quartet_ids,
        "visible": compute_pilot_metrics(visible_scores),
        "masked": compute_pilot_metrics(masked_scores),
        "raw_scores": all_scores,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "raw_scores"}, indent=2))


if __name__ == "__main__":
    main()
