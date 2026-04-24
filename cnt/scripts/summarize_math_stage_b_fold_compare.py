from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate disjoint-fold Stage B comparison summaries.")
    parser.add_argument(
        "--fold-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_fold_compare",
    )
    parser.add_argument("--num-folds", type=int, default=4)
    parser.add_argument(
        "--output-path",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_fold_compare" / "fold_compare_summary.json",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    rows = []
    unique_eval_ids: list[str] = []
    for fold_index in range(args.num_folds):
        path = args.fold_root / f"fold{fold_index:02d}" / "comparison_summary.json"
        summary = _load_json(path)
        rows.append(summary)
        unique_eval_ids.extend(summary["eval_example_ids"])

    aggregate = {
        "num_folds": len(rows),
        "unique_eval_example_ids": sorted(set(unique_eval_ids)),
        "num_unique_eval_examples": len(set(unique_eval_ids)),
        "all_eval_ids_disjoint": len(unique_eval_ids) == len(set(unique_eval_ids)),
        "mean_delta_n_t_weighted": mean(row["delta_cnt_minus_control_rollout"]["mean_n_t_weighted"] for row in rows),
        "mean_delta_n_t": mean(row["delta_cnt_minus_control_rollout"]["mean_n_t"] for row in rows),
        "mean_delta_drop_solve": mean(row["delta_cnt_minus_control_rollout"]["mean_drop_solve"] for row in rows),
        "nonzero_delta_folds": [
            int(row["fold_index"])
            for row in rows
            if abs(row["delta_cnt_minus_control_rollout"]["mean_n_t_weighted"]) > 1e-12
        ],
        "mean_base_n_t_weighted": mean(row["base_rollout"]["mean_n_t_weighted"] for row in rows),
        "mean_control_n_t_weighted": mean(row["control_rollout"]["mean_n_t_weighted"] for row in rows),
        "mean_cnt_n_t_weighted": mean(row["cnt_rollout"]["mean_n_t_weighted"] for row in rows),
    }

    summary = {
        "fold_summaries": rows,
        "aggregate": aggregate,
        "verdict_mode": "strict_final_answer_or_blank_final_recovery",
    }
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.output_path}")


if __name__ == "__main__":
    main()
