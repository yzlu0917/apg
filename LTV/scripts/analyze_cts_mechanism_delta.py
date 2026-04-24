#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def safe_mean(values: List[float]):
    if not values:
        return None
    return float(mean(values))


def pair_metric(pair: Dict, baseline: str) -> float:
    return float(pair["source_scores"][baseline] - pair["variant_scores"][baseline])


def same_gap(pair: Dict, baseline: str) -> float:
    return abs(pair_metric(pair, baseline))


def compare_pairs(
    before_pairs: List[Dict],
    after_pairs: List[Dict],
    annotated_rows: List[Dict],
    before_baseline: str,
    after_baseline: str,
) -> Dict:
    before_map = {row["pair_id"]: row for row in before_pairs}
    after_map = {row["pair_id"]: row for row in after_pairs}
    annotated_map = {row["pair_id"]: row for row in annotated_rows}

    joined = []
    for pair_id in sorted(before_map):
        before = before_map[pair_id]
        after = after_map[pair_id]
        meta = annotated_map[pair_id]

        if before["type"] == "same_semantics":
            before_value = same_gap(before, before_baseline)
            after_value = same_gap(after, after_baseline)
            improvement = before_value - after_value
        else:
            before_value = pair_metric(before, before_baseline)
            after_value = pair_metric(after, after_baseline)
            improvement = after_value - before_value

        joined.append(
            {
                "pair_id": pair_id,
                "type": before["type"],
                "source_theorem_id": before["source_theorem_id"],
                "source_step_index": before["source_step_index"],
                "same_family": meta["same_family"],
                "flip_family": meta["flip_family"],
                "provenance_clean": meta["provenance_clean"],
                "before_value": before_value,
                "after_value": after_value,
                "improvement": improvement,
            }
        )

    same_pairs = [row for row in joined if row["type"] == "same_semantics"]
    flip_pairs = [row for row in joined if row["type"] == "semantic_flip"]

    def summarize(rows: List[Dict], family_key: str) -> Dict[str, Dict]:
        groups = defaultdict(list)
        for row in rows:
            groups[row[family_key]].append(row)
        out = {}
        for key, xs in groups.items():
            out[key] = {
                "num_pairs": len(xs),
                "before_mean": safe_mean([x["before_value"] for x in xs]),
                "after_mean": safe_mean([x["after_value"] for x in xs]),
                "mean_improvement": safe_mean([x["improvement"] for x in xs]),
                "num_improved": sum(1 for x in xs if x["improvement"] > 0),
                "num_worsened": sum(1 for x in xs if x["improvement"] < 0),
            }
        return out

    def top_rows(rows: List[Dict], n: int, reverse: bool) -> List[Dict]:
        xs = sorted(rows, key=lambda x: x["improvement"], reverse=reverse)[:n]
        return [
            {
                "pair_id": x["pair_id"],
                "source_theorem_id": x["source_theorem_id"],
                "source_step_index": x["source_step_index"],
                "same_family": x["same_family"],
                "flip_family": x["flip_family"],
                "provenance_clean": x["provenance_clean"],
                "before_value": x["before_value"],
                "after_value": x["after_value"],
                "improvement": x["improvement"],
            }
            for x in xs
        ]

    report = {
        "before_baseline": before_baseline,
        "after_baseline": after_baseline,
        "same_pairs_overall": {
            "num_pairs": len(same_pairs),
            "before_mean_gap": safe_mean([x["before_value"] for x in same_pairs]),
            "after_mean_gap": safe_mean([x["after_value"] for x in same_pairs]),
            "mean_gap_improvement": safe_mean([x["improvement"] for x in same_pairs]),
            "num_improved": sum(1 for x in same_pairs if x["improvement"] > 0),
            "num_worsened": sum(1 for x in same_pairs if x["improvement"] < 0),
        },
        "flip_pairs_overall": {
            "num_pairs": len(flip_pairs),
            "before_mean_margin": safe_mean([x["before_value"] for x in flip_pairs]),
            "after_mean_margin": safe_mean([x["after_value"] for x in flip_pairs]),
            "mean_margin_improvement": safe_mean([x["improvement"] for x in flip_pairs]),
            "num_improved": sum(1 for x in flip_pairs if x["improvement"] > 0),
            "num_worsened": sum(1 for x in flip_pairs if x["improvement"] < 0),
        },
        "same_family_delta": summarize(same_pairs, "same_family"),
        "flip_family_delta": summarize(flip_pairs, "flip_family"),
        "provenance_delta": summarize(joined, "provenance_clean"),
        "top_same_improved": top_rows(same_pairs, 10, True),
        "top_same_worsened": top_rows(same_pairs, 10, False),
        "top_flip_improved": top_rows(flip_pairs, 10, True),
        "top_flip_worsened": top_rows(flip_pairs, 10, False),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare CTS pair-level deltas between two eval outputs.")
    parser.add_argument("--before-eval", required=True)
    parser.add_argument("--after-eval", required=True)
    parser.add_argument("--annotated-panel", required=True)
    parser.add_argument("--before-baseline", required=True)
    parser.add_argument("--after-baseline", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    before_eval = json.load(open(args.before_eval))
    after_eval = json.load(open(args.after_eval))
    annotated_rows = load_jsonl(Path(args.annotated_panel))

    report = compare_pairs(
        before_pairs=before_eval["pairs"],
        after_pairs=after_eval["pairs"],
        annotated_rows=annotated_rows,
        before_baseline=args.before_baseline,
        after_baseline=args.after_baseline,
    )
    report.update(
        {
            "before_eval": args.before_eval,
            "after_eval": args.after_eval,
            "annotated_panel": args.annotated_panel,
        }
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
