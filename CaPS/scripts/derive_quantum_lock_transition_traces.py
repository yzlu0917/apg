#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUTTON_RE = re.compile(r"[A-C]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive structured quantum_lock transition traces from answer-only sequences.")
    parser.add_argument("--input", required=True, help="Input answer-only rollout JSONL.")
    parser.add_argument("--output", required=True, help="Output structured rollout JSONL.")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Minimum score required to emit a structured transition trace.",
    )
    return parser.parse_args()


def parse_sequence(text: str | None) -> list[str]:
    if not text:
        return []
    return BUTTON_RE.findall(text.upper())


def simulate(metadata: dict, sequence: list[str]) -> list[str]:
    value = metadata["initial_value"]
    color = metadata["initial_state"]
    buttons = {button["name"]: button for button in metadata["buttons"]}
    lines: list[str] = []

    for action in sequence:
        button = buttons.get(action)
        if not button:
            break
        if button["active_state"] not in [color, "any"]:
            break

        next_value = value
        if button["type"] == "add":
            next_value += button["value"]
        elif button["type"] == "subtract":
            next_value -= button["value"]
        elif button["type"] == "multiply":
            next_value *= button["value"]

        next_color = "green" if color == "red" else "red"
        lines.append(f"State {value}/{color} -> {action} -> {next_value}/{next_color}")
        value = next_value
        color = next_color

    return lines


def main() -> None:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    rows = [json.loads(line) for line in input_path.open("r", encoding="utf-8")]

    kept = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if row["score"] < args.min_score or not row["final_present"]:
                continue

            sequence = parse_sequence(row["final"])
            reasoning_lines = simulate(row["metadata"], sequence)
            if not reasoning_lines:
                continue

            updated = dict(row)
            updated["protocol_branch"] = "quantum_lock_state_search_v0"
            updated["reasoning"] = "\n".join(reasoning_lines)
            updated["reasoning_present"] = True
            updated["format_ok"] = True
            updated["transition_line_count"] = len(reasoning_lines)
            updated["derived_from_final_sequence"] = True
            handle.write(json.dumps(updated, ensure_ascii=True) + "\n")
            kept += 1

    print(
        json.dumps(
            {
                "output": str(output_path.relative_to(ROOT)),
                "input_count": len(rows),
                "kept_count": kept,
                "min_score": args.min_score,
            },
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
