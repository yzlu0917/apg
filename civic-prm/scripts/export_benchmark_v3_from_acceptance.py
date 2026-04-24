from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROLE_BY_ANSWER_VARIANT = {
    "correct": ("valid_correct", "invalid_correct"),
    "swapped": ("valid_swapped", "invalid_swapped"),
}


def _benchmark_verbalizer_id(verbalizer_id: str) -> str:
    return verbalizer_id if verbalizer_id.endswith("_b3") else f"{verbalizer_id}_b3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export benchmark-v3 records from an acceptance analysis JSON.")
    parser.add_argument("--candidate-input", type=Path, required=True)
    parser.add_argument("--acceptance-analysis", type=Path, required=True)
    parser.add_argument("--run-label", type=str, required=True)
    parser.add_argument("--mode", choices=["strict", "ignore_semantic_only", "surface_or_mixed_only"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    return parser.parse_args()


def _load_candidates(path: Path) -> dict[tuple[str, str, str, int], dict]:
    by_key: dict[tuple[str, str, str, int], dict] = {}
    with path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (
                row["quartet_id"],
                row["verbalizer_id"],
                row["counterfactual_role"],
                int(row["metadata"]["benchmark_v3_candidate_index"]),
            )
            by_key[key] = row
    return by_key


def main() -> None:
    args = parse_args()
    candidates = _load_candidates(args.candidate_input)
    analysis = json.loads(args.acceptance_analysis.read_text(encoding="utf-8"))
    run = next(item for item in analysis["runs"] if item["label"] == args.run_label)
    mode_payload = run["modes"][args.mode]

    exported_records: list[dict] = []
    selected_family_summaries: list[dict] = []
    missing_records: list[dict] = []

    for quartet_result in mode_payload["quartet_results"]:
        if not quartet_result["accepted_under_mode"]:
            continue
        quartet_id = quartet_result["quartet_id"]
        verbalizer_id = _benchmark_verbalizer_id(quartet_result["verbalizer_id"])
        selected_family_summaries.append(quartet_result)

        for answer_variant, role_pair in ROLE_BY_ANSWER_VARIANT.items():
            candidate_index = int(quartet_result[f"{answer_variant}_best"]["candidate_index"])
            for role in role_pair:
                key = (quartet_id, verbalizer_id, role, candidate_index)
                row = candidates.get(key)
                if row is None:
                    missing_records.append(
                        {
                            "quartet_id": quartet_id,
                            "verbalizer_id": verbalizer_id,
                            "counterfactual_role": role,
                            "candidate_index": candidate_index,
                        }
                    )
                    continue
                exported_records.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in exported_records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    selected_quartets = sorted({row["quartet_id"] for row in exported_records})
    selected_verbalizers: dict[str, list[str]] = defaultdict(list)
    for row in exported_records:
        verbalizer_id = row["verbalizer_id"]
        quartet_id = row["quartet_id"]
        if verbalizer_id not in selected_verbalizers[quartet_id]:
            selected_verbalizers[quartet_id].append(verbalizer_id)

    summary = {
        "candidate_input": str(args.candidate_input),
        "acceptance_analysis": str(args.acceptance_analysis),
        "run_label": args.run_label,
        "mode": args.mode,
        "output_dataset": str(args.output),
        "num_selected_families": len(selected_family_summaries),
        "num_selected_records": len(exported_records),
        "domains": dict(Counter(row["domain"] for row in exported_records)),
        "selected_quartets": selected_quartets,
        "selected_verbalizers": dict(selected_verbalizers),
        "missing_records": missing_records,
        "bucket_counts": run["bucket_counts"],
        "mode_selected_quartets": mode_payload["selected_quartets"],
        "selected_family_summaries": selected_family_summaries,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
