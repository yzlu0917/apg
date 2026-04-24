#!/usr/bin/env python3
"""Minimal Object-gate bootstrap for the VSI project.

This script does not run model training. It produces a deterministic microbench
that tests whether the proposed measurement object can be separated from a
matched coarse-difficulty proxy.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class FamilyMeasurement:
    name: str
    description: str
    difficulty: Dict[str, float]
    certificate_horizon: float
    local_ambiguity: float
    exploitability: float
    notes: List[str]


def build_measurements(config: Dict[str, object]) -> List[FamilyMeasurement]:
    length = int(config["trajectory_length"])
    branching = int(config["branching_factor"])
    search_space = float(branching**length)
    shared_difficulty = {
        "trajectory_length": float(length),
        "branching_factor": float(branching),
        "search_space_proxy": search_space,
    }

    early_h = round(1.0 / length, 3)
    delayed_h = 1.0

    return [
        FamilyMeasurement(
            name="early_cert",
            description="Prefix-executable arithmetic traces with immediate local checking.",
            difficulty=shared_difficulty,
            certificate_horizon=early_h,
            local_ambiguity=0.0,
            exploitability=0.0,
            notes=[
                "Every intermediate state is exact-checkable.",
                "Final-answer checking is exact, so weak and strong verifier coincide.",
            ],
        ),
        FamilyMeasurement(
            name="delayed_cert",
            description="Matched-length traces where certification is only available at the final step.",
            difficulty=shared_difficulty,
            certificate_horizon=delayed_h,
            local_ambiguity=0.0,
            exploitability=0.0,
            notes=[
                "Coarse difficulty proxies are matched to early_cert.",
                "Prefix verification is unavailable until the final step.",
            ],
        ),
        FamilyMeasurement(
            name="rewrite_ambiguity",
            description="Semantically correct but non-canonical rewrite traces rejected by a canonical weak verifier.",
            difficulty=shared_difficulty,
            certificate_horizon=early_h,
            local_ambiguity=0.75,
            exploitability=0.0,
            notes=[
                "Strong verifier accepts multiple semantically equivalent traces.",
                "Weak verifier only accepts the canonical surface form.",
            ],
        ),
        FamilyMeasurement(
            name="partial_test_exploit",
            description="Toy program tasks where visible tests are exploitable but the strong oracle is exact.",
            difficulty=shared_difficulty,
            certificate_horizon=1.0,
            local_ambiguity=0.0,
            exploitability=1.0,
            notes=[
                "Weak verifier uses visible partial tests only.",
                "An exploit solution can score perfectly on the weak verifier and fail the strong oracle.",
            ],
        ),
    ]


def compute_gate_summary(
    measurements: List[FamilyMeasurement], thresholds: Dict[str, float]
) -> Dict[str, object]:
    by_name = {measurement.name: measurement for measurement in measurements}

    matched_difficulty = len(
        {
            tuple(sorted(measurement.difficulty.items()))
            for measurement in measurements
        }
    ) == 1

    h_gap = round(
        by_name["delayed_cert"].certificate_horizon
        - by_name["early_cert"].certificate_horizon,
        3,
    )
    a_gap = round(by_name["rewrite_ambiguity"].local_ambiguity, 3)
    e_gap = round(by_name["partial_test_exploit"].exploitability, 3)

    checks = {
        "matched_difficulty": matched_difficulty,
        "h_gap_pass": h_gap >= float(thresholds["required_h_gap"]),
        "a_gap_pass": a_gap >= float(thresholds["required_a_gap"]),
        "e_gap_pass": e_gap >= float(thresholds["required_e_gap"]),
    }

    gate_pass = all(checks.values())
    decision = "GO" if gate_pass else "NO_GO"

    interpretation = (
        "The measurement object is separable from the matched coarse-difficulty proxy "
        "on the toy bootstrap slice."
        if gate_pass
        else "The measurement object is not yet reliably separable on the toy bootstrap slice."
    )

    return {
        "decision": decision,
        "checks": checks,
        "gaps": {
            "h_gap": h_gap,
            "a_gap": a_gap,
            "e_gap": e_gap,
        },
        "interpretation": interpretation,
        "limitations": [
            "This bootstrap uses fixed toy families rather than full generators.",
            "A GO here does not validate any method claim.",
            "Audit, conversion, and transfer remain untested.",
        ],
    }


def render_table(measurements: List[FamilyMeasurement]) -> str:
    header = "family                 H      A      E      difficulty(search_space)"
    rows = [header, "-" * len(header)]
    for measurement in measurements:
        rows.append(
            f"{measurement.name:<22} "
            f"{measurement.certificate_horizon:<6.3f} "
            f"{measurement.local_ambiguity:<6.3f} "
            f"{measurement.exploitability:<6.3f} "
            f"{measurement.difficulty['search_space_proxy']:<.0f}"
        )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text())
    measurements = build_measurements(config)
    gate_summary = compute_gate_summary(measurements, config["thresholds"])

    payload = {
        "config": config,
        "measurements": [asdict(measurement) for measurement in measurements],
        "gate_summary": gate_summary,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")

    print(render_table(measurements))
    print()
    print(f"Object gate bootstrap decision: {gate_summary['decision']}")
    print(json.dumps(gate_summary["gaps"], indent=2))
    print(gate_summary["interpretation"])


if __name__ == "__main__":
    main()
