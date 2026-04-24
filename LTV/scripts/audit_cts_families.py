#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def mean(values: List[float]):
    if not values:
        return None
    return sum(values) / len(values)


def compute_slice_metrics(pairs: List[Dict], baselines: List[str]) -> Dict[str, Dict]:
    result = {}
    for baseline in baselines:
        same_gaps = [
            abs(pair["source_scores"][baseline] - pair["variant_scores"][baseline])
            for pair in pairs
            if pair["type"] == "same_semantics"
        ]
        flip_diffs = [
            pair["source_scores"][baseline] - pair["variant_scores"][baseline]
            for pair in pairs
            if pair["type"] == "semantic_flip"
        ]
        result[baseline] = {
            "num_same": len(same_gaps),
            "num_flip": len(flip_diffs),
            "invariance_gap": mean(same_gaps),
            "semantic_sensitivity": mean(flip_diffs),
        }
    return result


def best_baseline_for_same(metrics: Dict[str, Dict]):
    candidates = [
        (name, stats["invariance_gap"])
        for name, stats in metrics.items()
        if stats["invariance_gap"] is not None
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda x: x[1])[0]


def best_baseline_for_flip(metrics: Dict[str, Dict]):
    candidates = [
        (name, stats["semantic_sensitivity"])
        for name, stats in metrics.items()
        if stats["semantic_sensitivity"] is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[1])[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Family-sliced CTS audit.")
    parser.add_argument("--eval-json", required=True)
    parser.add_argument("--annotated-panel", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    eval_data = json.load(open(args.eval_json))
    annotated_rows = load_jsonl(Path(args.annotated_panel))

    annotated_map = {row["pair_id"]: row for row in annotated_rows}
    joined = []
    for pair in eval_data["pairs"]:
        meta = annotated_map[pair["pair_id"]]
        joined.append({**pair, **{
            "provenance_clean": meta["provenance_clean"],
            "same_family": meta["same_family"],
            "same_subfamily": meta.get("same_subfamily"),
            "flip_family": meta["flip_family"],
            "flip_subfamily": meta.get("flip_subfamily"),
            "pair_id_clean": meta["pair_id_clean"],
        }})

    baselines = sorted(joined[0]["source_scores"].keys())

    overall = compute_slice_metrics(joined, baselines)

    same_family_groups = defaultdict(list)
    same_subfamily_groups = defaultdict(list)
    flip_family_groups = defaultdict(list)
    flip_subfamily_groups = defaultdict(list)
    provenance_groups = defaultdict(list)
    for pair in joined:
        provenance_groups[pair["provenance_clean"]].append(pair)
        if pair["type"] == "same_semantics":
            same_family_groups[pair["same_family"]].append(pair)
            if pair["same_subfamily"] is not None:
                same_subfamily_groups[pair["same_subfamily"]].append(pair)
        else:
            flip_family_groups[pair["flip_family"]].append(pair)
            if pair["flip_subfamily"] is not None:
                flip_subfamily_groups[pair["flip_subfamily"]].append(pair)

    def summarize_groups(groups: Dict[str, List[Dict]], group_type: str):
        out = {}
        for name, pairs in groups.items():
            metrics = compute_slice_metrics(pairs, baselines)
            out[name] = {
                "group_type": group_type,
                "num_pairs": len(pairs),
                "metrics": metrics,
                "best_same_baseline": best_baseline_for_same(metrics),
                "best_flip_baseline": best_baseline_for_flip(metrics),
            }
        return out

    report = {
        "eval_json": args.eval_json,
        "annotated_panel": args.annotated_panel,
        "num_pairs": len(joined),
        "baselines": baselines,
        "overall": overall,
        "same_family": summarize_groups(same_family_groups, "same_family"),
        "same_subfamily": summarize_groups(same_subfamily_groups, "same_subfamily"),
        "flip_family": summarize_groups(flip_family_groups, "flip_family"),
        "flip_subfamily": summarize_groups(flip_subfamily_groups, "flip_subfamily"),
        "provenance": summarize_groups(provenance_groups, "provenance"),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
