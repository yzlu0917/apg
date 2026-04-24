#!/usr/bin/env python3

import json
from pathlib import Path

from reasoning_gym.factory import create_dataset


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "object_gate.json"
WRAPPER_TEMPLATE = """You are solving a verifiable reasoning task.

Instructions:
- Think through the task inside <reasoning> tags.
- In <reasoning>, write one short step per line.
- Keep the reasoning concise and causal; avoid filler.
- Do not copy the full final answer into <reasoning>.
- Use <reasoning> for plan, decomposition, or key intermediate checks only.
- Put only the final answer inside <final> tags.
- The content inside <final> must follow the original task formatting instructions exactly.
- Do not repeat the problem statement.

Problem:
{raw_question}

Return exactly:
<reasoning>
...
</reasoning>
<final>
...
</final>
"""


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def allocate_counts(total: int, families: list[str]) -> dict[str, int]:
    base = total // len(families)
    remainder = total % len(families)
    counts = {family: base for family in families}
    for family in families[:remainder]:
        counts[family] += 1
    return counts


def build_entries(config: dict, split: str, stratum: str, families: list[str]) -> list[dict]:
    split_cfg = config["slices"][split]
    total_key = "high_dependency_prompts" if stratum == "high_dependency" else "shallow_prompts"
    counts = allocate_counts(split_cfg[total_key], families)
    seed = split_cfg["seed"]
    entries: list[dict] = []

    for family in families:
        dataset = create_dataset(family, size=counts[family], seed=seed)
        for idx in range(counts[family]):
            item = dataset[idx]
            prompt_id = f"{split}-{stratum}-{family}-{idx:03d}"
            entry = {
                "prompt_id": prompt_id,
                "split": split,
                "difficulty_stratum": stratum,
                "family": family,
                "dataset_seed": seed,
                "source_index": idx,
                "raw_question": item["question"],
                "oracle_answer": item["answer"],
                "metadata": item["metadata"],
                "prompt_template_version": config["prompt_protocol"]["version"],
                "model_prompt": WRAPPER_TEMPLATE.format(raw_question=item["question"]),
                "output_contract": {
                    "reasoning_tag": config["prompt_protocol"]["reasoning_format"]["tag"],
                    "final_tag": config["prompt_protocol"]["final_format"]["tag"],
                    "extract_final_for_scoring": True,
                    "assistant_prefill": "<reasoning>\n"
                },
                "semantic_generation_policy": config["prompt_protocol"]["semantic_generation"],
            }
            entries.append(entry)

    return entries


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def main() -> None:
    config = load_config()
    sample_dir = ROOT / config["artifacts"]["samples_dir"]
    families_cfg = config["task_source"]["families"]

    dev_rows = build_entries(config, "dev", "high_dependency", families_cfg["high_dependency"])
    dev_rows += build_entries(config, "dev", "shallow", families_cfg["shallow"])
    final_rows = build_entries(config, "final", "high_dependency", families_cfg["high_dependency"])
    final_rows += build_entries(config, "final", "shallow", families_cfg["shallow"])

    dev_path = sample_dir / "dev_manifest.jsonl"
    final_path = sample_dir / "final_manifest.jsonl"
    write_jsonl(dev_path, dev_rows)
    write_jsonl(final_path, final_rows)

    summary = {
        "dev_manifest": str(dev_path.relative_to(ROOT)),
        "dev_count": len(dev_rows),
        "final_manifest": str(final_path.relative_to(ROOT)),
        "final_count": len(final_rows),
        "families": families_cfg,
        "prompt_template_version": config["prompt_protocol"]["version"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
