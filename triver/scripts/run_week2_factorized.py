from __future__ import annotations

import argparse
import json
from pathlib import Path

from triver.baselines.week2 import attach_embeddings, load_oracle_frame
from triver.factorized.week2 import infer_embedding_columns, run_factorized_cv, summarize_factorized_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TriVer Week-2 factorized controller experiment.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--embedding-npz", default="")
    parser.add_argument("--q-embedding-npz", default="")
    parser.add_argument("--s-embedding-npz", default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--include-ambiguous", action="store_true")
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--state-mode", choices=["legacy", "s_proxy"], default="legacy")
    parser.add_argument("--state-head-model", choices=["linear", "pca_ridge", "pca_enet", "rf"], default="linear")
    parser.add_argument(
        "--value-head-model",
        choices=[
            "ridge",
            "interaction_ridge",
            "heteroscedastic_interaction",
            "shared_covariance_heteroscedastic_interaction",
            "lowrank_heteroscedastic_interaction",
            "rank2_lowrank_heteroscedastic_interaction",
            "conditional_lowrank_heteroscedastic_interaction",
            "huber",
            "noise_weighted_ridge",
            "pairwise_logit",
            "pairwise_interaction_logit",
            "pairwise_heteroscedastic_interaction",
            "uncertainty_ridge",
            "uncertainty_heteroscedastic_interaction",
            "uncertainty_shared_covariance_heteroscedastic_interaction",
            "uncertainty_lowrank_heteroscedastic_interaction",
            "uncertainty_rank2_lowrank_heteroscedastic_interaction",
            "uncertainty_conditional_lowrank_heteroscedastic_interaction",
            "uncertainty_interaction_ridge",
            "uncertainty_noise_weighted_ridge",
            "uncertainty_pairwise_logit",
            "uncertainty_pairwise_interaction_logit",
            "uncertainty_pairwise_heteroscedastic_interaction",
            "joint_pairwise_gate",
            "pairwise_error_calibrated",
            "conditional_lowrank_pairwise_error_calibrated",
            "conditional_lowrank_selective_pairwise_error_calibrated",
            "conditional_lowrank_capped_pairwise_error_calibrated",
            "conditional_lowrank_banded_pairwise_error_calibrated",
            "conditional_lowrank_clustered_pairwise_error_calibrated",
            "pairwise_meta_calibrated",
            "pairwise_selective_calibrated",
        ],
        default="ridge",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not any([args.embedding_npz, args.q_embedding_npz, args.s_embedding_npz]):
        raise ValueError("Provide --embedding-npz or at least one of --q-embedding-npz / --s-embedding-npz")

    frame = load_oracle_frame(args.input_csv, exclude_ambiguous=not args.include_ambiguous)
    q_embedding_path = args.q_embedding_npz or args.embedding_npz or args.s_embedding_npz
    s_embedding_path = args.s_embedding_npz or args.embedding_npz or args.q_embedding_npz

    frame, q_embedding_columns = attach_embeddings(frame, q_embedding_path, column_prefix="qemb")
    frame, s_embedding_columns = attach_embeddings(frame, s_embedding_path, column_prefix="semb")
    q_embedding_columns = infer_embedding_columns(frame, prefix="qemb_")
    s_embedding_columns = infer_embedding_columns(frame, prefix="semb_")
    results = run_factorized_cv(
        frame=frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        state_mode=args.state_mode,
        state_head_model=args.state_head_model,
        value_head_model=args.value_head_model,
    )
    summary = summarize_factorized_results(results)

    results.to_csv(output_dir / "cv_results.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary.to_dict(orient="records"), handle, ensure_ascii=False, indent=2)

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
