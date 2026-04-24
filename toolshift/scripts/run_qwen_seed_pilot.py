#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import evaluate_agent, load_seed_suite
from toolshift.eval import dump_json
from toolshift.qwen_agent import QwenPromptAgent


def _fmt_metric(value) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Qwen prompt-only evaluation on a ToolShift benchmark.")
    parser.add_argument("--benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--model-path", default="/cephfs/shared/hf_cache/hub/Qwen3-0.6B")
    parser.add_argument("--output-dir", default="artifacts/qwen_seed_pilot")
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--agent-name", default=None)
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = QwenPromptAgent(
        model_path=args.model_path,
        device_map=args.device_map,
        max_new_tokens=args.max_new_tokens,
        enable_thinking=not args.disable_thinking,
        name=args.agent_name or Path(args.model_path).name.lower().replace(".", "_"),
    )
    records, summary = evaluate_agent(agent, suite)

    dump_json(str(output_dir / "summary.json"), summary)
    dump_json(str(output_dir / "records.json"), [record.to_dict(suite.tool_lookup) for record in records])

    metrics = summary["metrics"]
    print("agent\tCAA\tCAA_clean\tCAA+\tNOS\tPOC\tcoverage")
    print(
        f"{agent.name}\t"
        f"{_fmt_metric(metrics['CAA_overall'])}\t"
        f"{_fmt_metric(metrics['CAA_clean'])}\t"
        f"{_fmt_metric(metrics['CAA_positive'])}\t"
        f"{_fmt_metric(metrics['NOS'])}\t"
        f"{_fmt_metric(metrics['POC'])}\t"
        f"{_fmt_metric(metrics['coverage'])}"
    )


if __name__ == "__main__":
    main()
