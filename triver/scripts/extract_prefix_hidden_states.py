from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from triver.envs.arithmetic import ArithmeticEnv
from triver.envs.linear_equations import LinearEquationEnv
from triver.models.qwen_runner import QwenRunner


ENVS = {
    "arithmetic": ArithmeticEnv(),
    "linear_equations": LinearEquationEnv(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract prefix hidden states for TriVer baselines.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output-npz", required=True)
    parser.add_argument(
        "--pooling",
        default="last_generation_prompt",
        choices=[
            "last_generation_prompt",
            "last_content",
            "mean_content",
            "last_and_mean_content",
        ],
        help="Embedding strategy for the prefix prompt.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runner = QwenRunner(model_path=args.model_path)

    embeddings: list[np.ndarray] = []
    row_ids: list[int] = []
    with open(args.input_csv, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_id, row in enumerate(reader):
            env = ENVS[row["env"]]
            sample = env.sample_from_record(str(row["problem"]), str(row["target"]))
            prefix_lines = [part.strip() for part in str(row["prefix_trace"]).split(" | ")]
            prompt, _ = env.build_solver_messages(sample, prefix_lines, "continue")
            embedding = runner.prompt_embedding(prompt, strategy=args.pooling)
            embeddings.append(embedding)
            row_ids.append(row_id)

    output_path = Path(args.output_npz)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        embeddings=np.stack(embeddings),
        row_ids=np.array(row_ids, dtype=np.int64),
        pooling=np.array(args.pooling),
    )
    print(f"saved {len(row_ids)} embeddings with {args.pooling} to {output_path}")


if __name__ == "__main__":
    main()
