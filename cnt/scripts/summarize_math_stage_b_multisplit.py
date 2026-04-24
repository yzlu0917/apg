from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


ROLLOUT_KEYS = (
    "mean_original_solve",
    "mean_drop_solve",
    "mean_paraphrase_solve",
    "mean_swap_solve",
    "mean_n_t",
    "mean_n_t_weighted",
    "mean_paraphrase_gap",
    "positive_n_fraction",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate robust Stage B split-compare summaries.")
    parser.add_argument(
        "--split-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_split_compare",
    )
    parser.add_argument(
        "--split-seeds",
        type=int,
        nargs="+",
        default=(5, 23, 41, 77),
    )
    parser.add_argument(
        "--seed17-dataset-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_dataset03_cleanchosen" / "stage_b_dataset_summary.json",
    )
    parser.add_argument(
        "--seed17-base-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_rollout_eval_base_lc120_v2_robust" / "stage_b_rollout_summary.json",
    )
    parser.add_argument(
        "--seed17-control-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_rollout_eval_control01_sftonly_lc120_robust" / "stage_b_rollout_summary.json",
    )
    parser.add_argument(
        "--seed17-cnt-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120_robust" / "stage_b_rollout_summary.json",
    )
    parser.add_argument(
        "--seed23-lc160-control-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_split_compare" / "seed23" / "control_rollout_lc160_robust" / "stage_b_rollout_summary.json",
    )
    parser.add_argument(
        "--seed23-lc160-cnt-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_split_compare" / "seed23" / "cnt_rollout_lc160_robust" / "stage_b_rollout_summary.json",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_split_compare" / "multisplit_summary_robust.json",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rollout_view(summary: dict) -> dict:
    return {key: summary[key] for key in ROLLOUT_KEYS}


def _delta(cnt_rollout: dict, control_rollout: dict) -> dict:
    return {key: cnt_rollout[key] - control_rollout[key] for key in ROLLOUT_KEYS}


def _split_entry(split_root: Path, seed: int) -> dict:
    seed_dir = split_root / f"seed{seed:02d}"
    dataset_summary = _load_json(seed_dir / "dataset" / "stage_b_dataset_summary.json")
    base_rollout = _rollout_view(_load_json(seed_dir / "base_rollout_robust" / "stage_b_rollout_summary.json"))
    control_rollout = _rollout_view(_load_json(seed_dir / "control_rollout_robust" / "stage_b_rollout_summary.json"))
    cnt_rollout = _rollout_view(_load_json(seed_dir / "cnt_rollout_robust" / "stage_b_rollout_summary.json"))
    return {
        "split_seed": seed,
        "eval_example_ids": dataset_summary["eval_example_ids"],
        "base_rollout": base_rollout,
        "control_rollout": control_rollout,
        "cnt_rollout": cnt_rollout,
        "delta_cnt_minus_control_rollout": _delta(cnt_rollout, control_rollout),
    }


def main() -> None:
    args = parse_args()
    rows = [_split_entry(args.split_root, seed) for seed in sorted(args.split_seeds)]

    seed17_dataset = _load_json(args.seed17_dataset_summary)
    seed17_base = _rollout_view(_load_json(args.seed17_base_summary))
    seed17_control = _rollout_view(_load_json(args.seed17_control_summary))
    seed17_cnt = _rollout_view(_load_json(args.seed17_cnt_summary))
    rows.append(
        {
            "split_seed": 17,
            "eval_example_ids": seed17_dataset["eval_example_ids"],
            "base_rollout": seed17_base,
            "control_rollout": seed17_control,
            "cnt_rollout": seed17_cnt,
            "delta_cnt_minus_control_rollout": _delta(seed17_cnt, seed17_control),
        }
    )
    rows = sorted(rows, key=lambda row: row["split_seed"])

    aggregate = {
        "num_splits_lc120": len(rows),
        "nonzero_delta_seeds_lc120": [
            row["split_seed"] for row in rows if abs(row["delta_cnt_minus_control_rollout"]["mean_n_t_weighted"]) > 1e-12
        ],
        "mean_delta_n_t_weighted_lc120": mean(row["delta_cnt_minus_control_rollout"]["mean_n_t_weighted"] for row in rows),
        "mean_delta_n_t_lc120": mean(row["delta_cnt_minus_control_rollout"]["mean_n_t"] for row in rows),
        "mean_delta_drop_solve_lc120": mean(row["delta_cnt_minus_control_rollout"]["mean_drop_solve"] for row in rows),
    }

    seed23_lc160_control = _rollout_view(_load_json(args.seed23_lc160_control_summary))
    seed23_lc160_cnt = _rollout_view(_load_json(args.seed23_lc160_cnt_summary))
    seed23_lc160 = {
        "control_rollout": seed23_lc160_control,
        "cnt_rollout": seed23_lc160_cnt,
        "delta_cnt_minus_control_rollout": _delta(seed23_lc160_cnt, seed23_lc160_control),
        "interpretation": "the only apparent positive split at lc120 vanishes when continuation budget increases from 120 to 160",
    }

    summary = {
        "splits_lc120": rows,
        "aggregate_lc120": aggregate,
        "seed23_lc160_recheck": seed23_lc160,
        "verdict_mode": "strict_final_answer_or_blank_final_recovery",
    }

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.output_path}")


if __name__ == "__main__":
    main()
