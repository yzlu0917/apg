from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .benchmark import load_seed_suite
from .schema import SplitTag


@dataclass(frozen=True)
class BlindPanelSummary:
    benchmark_path: str
    audit_path: str | None
    audit_markdown_path: str | None
    panel_role: str | None
    panel_version: str | None
    panel_state: str | None
    method_selection_allowed: bool
    case_count: int
    view_count: int
    source_count: int
    family_tags: tuple[str, ...]
    vendor_tags: tuple[str, ...]
    split_tags: tuple[str, ...]
    dev_family_overlap: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_blind_panel(
    benchmark_path: str | Path,
    *,
    dev_benchmark_path: str | Path | None = "data/real_evolution_benchmark.json",
) -> BlindPanelSummary:
    benchmark = Path(benchmark_path)
    payload = json.loads(benchmark.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {})
    suite = load_seed_suite(benchmark)
    family_tags = tuple(sorted({case.family_tag for case in suite.cases if case.family_tag}))
    vendor_tags = tuple(sorted(metadata.get("vendor_tags", ())))
    split_tags = tuple(sorted({example.split_tag.value for example in suite.examples}))
    dev_overlap: tuple[str, ...] = ()
    if dev_benchmark_path is not None:
        dev_path = Path(dev_benchmark_path)
        if dev_path.exists():
            dev_suite = load_seed_suite(dev_path)
            dev_families = {case.family_tag for case in dev_suite.cases if case.family_tag}
            dev_overlap = tuple(sorted(set(family_tags) & dev_families))
    return BlindPanelSummary(
        benchmark_path=str(benchmark),
        audit_path=metadata.get("audit_path"),
        audit_markdown_path=metadata.get("audit_markdown_path"),
        panel_role=metadata.get("panel_role"),
        panel_version=metadata.get("panel_version"),
        panel_state=metadata.get("panel_state"),
        method_selection_allowed=bool(metadata.get("method_selection_allowed", False)),
        case_count=len(payload.get("cases", ())),
        view_count=len(payload.get("views", ())),
        source_count=len(payload.get("sources", {})),
        family_tags=family_tags,
        vendor_tags=vendor_tags,
        split_tags=split_tags,
        dev_family_overlap=dev_overlap,
    )


def validate_blind_panel(
    benchmark_path: str | Path,
    *,
    dev_benchmark_path: str | Path | None = "data/real_evolution_benchmark.json",
    require_frozen: bool = True,
) -> BlindPanelSummary:
    benchmark = Path(benchmark_path)
    payload = json.loads(benchmark.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {})
    summary = summarize_blind_panel(benchmark, dev_benchmark_path=dev_benchmark_path)

    errors: list[str] = []
    if metadata.get("panel_role") != "blind_test":
        errors.append("metadata.panel_role must equal blind_test")
    if require_frozen and metadata.get("panel_state") != "frozen":
        errors.append("metadata.panel_state must equal frozen")
    if metadata.get("method_selection_allowed", True):
        errors.append("metadata.method_selection_allowed must be false")

    counts = metadata.get("counts", {})
    if counts.get("cases") != summary.case_count:
        errors.append("metadata.counts.cases does not match benchmark case count")
    if counts.get("views") != summary.view_count:
        errors.append("metadata.counts.views does not match benchmark view count")
    if counts.get("sources") != summary.source_count:
        errors.append("metadata.counts.sources does not match benchmark source count")

    expected_families = tuple(sorted(metadata.get("family_tags", ())))
    if expected_families != summary.family_tags:
        errors.append("metadata.family_tags does not match benchmark families")
    expected_vendors = tuple(sorted(metadata.get("vendor_tags", ())))
    if expected_vendors != summary.vendor_tags:
        errors.append("metadata.vendor_tags does not match benchmark vendors")
    if summary.split_tags != (SplitTag.UNAMBIGUOUS_CORE.value,):
        errors.append("blind panel examples must all stay in unambiguous_core")
    if summary.dev_family_overlap:
        errors.append(f"blind families overlap with dev panel: {', '.join(summary.dev_family_overlap)}")

    audit_path = metadata.get("audit_path")
    if not audit_path or not Path(audit_path).exists():
        errors.append("metadata.audit_path must exist")
    audit_markdown_path = metadata.get("audit_markdown_path")
    if not audit_markdown_path or not Path(audit_markdown_path).exists():
        errors.append("metadata.audit_markdown_path must exist")

    if errors:
        raise ValueError("; ".join(errors))
    return summary
