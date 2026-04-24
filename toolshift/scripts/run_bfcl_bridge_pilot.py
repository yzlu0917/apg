#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import DescriptionGroundedAgent, LexicalShortcutAgent, OracleAgent, evaluate_agent, load_seed_suite
from toolshift.eval import dump_json
from toolshift.qwen_agent import QwenPromptAgent


def _fmt_metric(value) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TOOLSHIFT agents on the BFCL bridge benchmark.")
    parser.add_argument("--benchmark", default="data/bfcl_bridge_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/bfcl_bridge_pilot")
    parser.add_argument("--qwen-model-path", default=None)
    parser.add_argument("--device-map", default="cuda:0")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--disable-thinking", action="store_true")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agents = [OracleAgent(), LexicalShortcutAgent(), DescriptionGroundedAgent()]
    if args.qwen_model_path:
        agents.append(
            QwenPromptAgent(
                model_path=args.qwen_model_path,
                device_map=args.device_map,
                max_new_tokens=args.max_new_tokens,
                enable_thinking=not args.disable_thinking,
                name=Path(args.qwen_model_path).name.lower().replace(".", "_"),
            )
        )

    all_records = {}
    summaries = {}
    for agent in agents:
        records, summary = evaluate_agent(agent, suite)
        all_records[agent.name] = [record.to_dict(suite.tool_lookup) for record in records]
        summaries[agent.name] = summary

    dump_json(str(output_dir / "summary.json"), summaries)
    dump_json(str(output_dir / "records.json"), all_records)

    print("agent\tCAA\tcoverage\tselective_risk\tcontract_validity")
    for agent in agents:
        metrics = summaries[agent.name]["metrics"]
        print(
            f"{agent.name}\t"
            f"{_fmt_metric(metrics['CAA_overall'])}\t"
            f"{_fmt_metric(metrics['coverage'])}\t"
            f"{_fmt_metric(metrics['selective_risk'])}\t"
            f"{_fmt_metric(metrics['contract_validity'])}"
        )


if __name__ == "__main__":
    main()
