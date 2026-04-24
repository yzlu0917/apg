#!/usr/bin/env python3
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


TIER_ORDER = {
    "neutral": 0,
    "weak_partial": 1,
    "strong_partial": 2,
    "solved": 3,
}


def load_oracle(path: Path):
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_state = {}
    for row in rows:
        by_state[row["state_id"]] = {
            "before_goals": row["before_goals"],
            "oracle_source": row["oracle_source"],
            "candidates": {int(c["candidate_index"]): c for c in row["candidates"]},
        }
    return by_state


def pair_counts(candidates):
    ordered = 0
    equivalent = 0
    idxs = sorted(candidates)
    for i, a in enumerate(idxs):
        for b in idxs[i + 1 :]:
            ta = TIER_ORDER[candidates[a]["progress_tier"]]
            tb = TIER_ORDER[candidates[b]["progress_tier"]]
            if ta == tb:
                equivalent += 1
            else:
                ordered += 1
    return ordered, equivalent


def main():
    parser = argparse.ArgumentParser(description="Compare two state-first progress oracle panels.")
    parser.add_argument("--oracle-a", required=True)
    parser.add_argument("--oracle-b", required=True)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--disagreements-out", required=True)
    args = parser.parse_args()

    a = load_oracle(Path(args.oracle_a))
    b = load_oracle(Path(args.oracle_b))
    common_states = sorted(set(a) & set(b))

    total = 0
    agree = 0
    abs_gap_counter = Counter()
    confusion = Counter()
    by_state = []
    disagreements = []

    for state_id in common_states:
        ca = a[state_id]["candidates"]
        cb = b[state_id]["candidates"]
        common_candidates = sorted(set(ca) & set(cb))
        state_total = 0
        state_agree = 0
        state_disagreements = []
        for idx in common_candidates:
            ta = ca[idx]["progress_tier"]
            tb = cb[idx]["progress_tier"]
            total += 1
            state_total += 1
            confusion[(ta, tb)] += 1
            gap = abs(TIER_ORDER[ta] - TIER_ORDER[tb])
            abs_gap_counter[gap] += 1
            if ta == tb:
                agree += 1
                state_agree += 1
            else:
                row = {
                    "state_id": state_id,
                    "candidate_index": idx,
                    "tactic": ca[idx]["tactic"],
                    "tier_a": ta,
                    "tier_b": tb,
                    "rationale_a": ca[idx].get("oracle_rationale", ""),
                    "rationale_b": cb[idx].get("oracle_rationale", ""),
                }
                disagreements.append(row)
                state_disagreements.append(row)

        ordered_a, equiv_a = pair_counts(ca)
        ordered_b, equiv_b = pair_counts(cb)
        by_state.append(
            {
                "state_id": state_id,
                "num_candidates": len(common_candidates),
                "candidate_agreement": state_agree / state_total if state_total else None,
                "num_disagreements": len(state_disagreements),
                "ordered_pairs_a": ordered_a,
                "equivalent_pairs_a": equiv_a,
                "ordered_pairs_b": ordered_b,
                "equivalent_pairs_b": equiv_b,
            }
        )

    summary = {
        "oracle_a": args.oracle_a,
        "oracle_b": args.oracle_b,
        "num_states": len(common_states),
        "num_candidates_compared": total,
        "candidate_agreement": agree / total if total else None,
        "agreement_count": agree,
        "disagreement_count": total - agree,
        "absolute_gap_histogram": dict(sorted(abs_gap_counter.items())),
        "confusion": {f"{k[0]}__{k[1]}": v for k, v in sorted(confusion.items())},
        "by_state": sorted(by_state, key=lambda x: (-x["num_disagreements"], x["state_id"])),
    }

    out_summary = Path(args.summary_out)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    out_dis = Path(args.disagreements_out)
    out_dis.parent.mkdir(parents=True, exist_ok=True)
    out_dis.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in disagreements) + ("\n" if disagreements else ""), encoding="utf-8")

    print(json.dumps({
        "summary_out": str(out_summary),
        "disagreements_out": str(out_dis),
        "candidate_agreement": summary["candidate_agreement"],
        "disagreement_count": summary["disagreement_count"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
