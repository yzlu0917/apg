#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dump_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold current CTS rows into pairwise-progress-label-v0 schema.")
    parser.add_argument("--cts-seed", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    cts_rows = load_jsonl(Path(args.cts_seed))
    out_rows = []
    for row in cts_rows:
        out_rows.append(
            {
                "pair_id": row["pair_id"],
                "theorem_id": row["source_theorem_id"],
                "step_index": row["source_step_index"],
                "shared_pre_state_guarantee": True,
                "source_candidate": {
                    "candidate_id": "source",
                    "step_text": row["source_step"],
                    "local_sound": 1,
                    "parser_status": None,
                    "before_goal_count": None,
                    "after_goal_count": None,
                    "main_goal_solved": None,
                    "spawned_goal_count": None,
                    "before_main_goal_pp": None,
                    "after_main_goal_pp": None,
                    "before_total_goal_tokens": None,
                    "after_total_goal_tokens": None,
                    "progress_class": "equivalent_or_better_proxy",
                    "progress_evidence": "current CTS source treated as canonical positive proxy",
                },
                "variant_candidate": {
                    "candidate_id": "variant",
                    "step_text": row["variant_step"],
                    "local_sound": 1 if row["type"] == "same_semantics" else 0,
                    "parser_status": None,
                    "before_goal_count": None,
                    "after_goal_count": None,
                    "main_goal_solved": None,
                    "spawned_goal_count": None,
                    "before_main_goal_pp": None,
                    "after_main_goal_pp": None,
                    "before_total_goal_tokens": None,
                    "after_total_goal_tokens": None,
                    "progress_class": "equivalent_proxy" if row["type"] == "same_semantics" else "unsound_proxy",
                    "progress_evidence": "derived from existing CTS same/flip label only",
                },
                "pair_label": "no_progress_difference" if row["type"] == "same_semantics" else "source_better_strong",
                "pair_label_strength": "proxy",
                "label_source": "cts_v0_type_mapping",
                "label_status": "proxy_only",
                "notes": row.get("notes"),
                "provenance": row.get("provenance"),
            }
        )

    dump_jsonl(Path(args.output), out_rows)
    summary = {
        "num_pairs": len(out_rows),
        "proxy_only_pairs": len(out_rows),
        "needs_proof_state_extraction_pairs": len(out_rows),
        "same_pairs": sum(r["pair_label"] == "no_progress_difference" for r in out_rows),
        "source_better_strong_pairs": sum(r["pair_label"] == "source_better_strong" for r in out_rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
