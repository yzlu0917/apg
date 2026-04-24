from __future__ import annotations

from pathlib import Path

# Current authoritative base benchmark after the proposal-aligned acceptance correction.
DEFAULT_BASE_BENCHMARK_DATASET = Path(
    "data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl"
)

# Legacy benchmarks retained for reproduction and comparison.
LEGACY_BASE_BENCHMARK_DATASET = Path("data/generated/craft_core_hard.jsonl")
LEGACY_WEEK1_BENCHMARK_DATASET = Path("data/generated/craft_core_week1.jsonl")
