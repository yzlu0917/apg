from __future__ import annotations

import argparse
import json
from pathlib import Path

from toolshift.blind_panel import validate_blind_panel


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the frozen ToolShift blind real-evolution panel.")
    parser.add_argument("--benchmark", default="data/real_evolution_blind_benchmark.json")
    parser.add_argument("--dev-benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-json", default="")
    args = parser.parse_args()

    summary = validate_blind_panel(args.benchmark, dev_benchmark_path=args.dev_benchmark)
    payload = summary.to_dict()
    print(json.dumps(payload, indent=2))

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
