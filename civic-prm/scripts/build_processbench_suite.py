from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a package-level summary for the ProcessBench benchmark suite."
    )
    parser.add_argument(
        "--trace-dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument(
        "--prefix-dataset",
        type=Path,
        default=Path("data/external/processbench_prefix_eval_all.jsonl"),
    )
    parser.add_argument(
        "--frozen-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_frozen_baselines.json"),
    )
    parser.add_argument(
        "--reranker-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_reranker_8b.json"),
    )
    parser.add_argument(
        "--trace-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_eval_all_summary.json"),
    )
    parser.add_argument(
        "--prefix-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_prefix_eval_all_summary.json"),
    )
    parser.add_argument(
        "--main-table",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_main_table.json"),
    )
    parser.add_argument(
        "--answer-swap-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_answer_swap_api_summary.json"),
    )
    parser.add_argument(
        "--repair-pilot-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_pd2_v3_partial_pilot_summary.json"),
    )
    parser.add_argument(
        "--repair-judge-summary",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_pd2_v3_api_summary.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_suite.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_suite.md"),
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_manifest.json"),
    )
    parser.add_argument(
        "--output-split-manifest",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_split_manifest.json"),
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _group_id(record: dict) -> str:
    metadata = record.get("metadata", {})
    return str(
        metadata.get("source_trace_id")
        or metadata.get("source_example_id")
        or record["trace_id"]
    )


def _attach_group_splits(records: list[dict], seed: int) -> list[dict]:
    groups_by_domain: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    for record in records:
        group_id = _group_id(record)
        if group_id in seen:
            continue
        seen.add(group_id)
        groups_by_domain[record["domain"]].append(group_id)

    rng = random.Random(seed)
    group_to_split: dict[str, str] = {}
    for domain, group_ids in groups_by_domain.items():
        group_ids = sorted(group_ids)
        rng.shuffle(group_ids)
        total = len(group_ids)
        train_cut = max(1, int(round(total * 0.7)))
        val_cut = max(train_cut + 1, int(round(total * 0.85)))
        for index, group_id in enumerate(group_ids):
            if index < train_cut:
                split = "train"
            elif index < val_cut:
                split = "val"
            else:
                split = "test"
            group_to_split[group_id] = split

    enriched = []
    for record in records:
        cloned = dict(record)
        cloned["_group_id"] = _group_id(record)
        cloned["split"] = group_to_split[cloned["_group_id"]]
        enriched.append(cloned)
    return enriched


def _limit_prefix_records(records: list[dict], per_domain: int | None, seed: int) -> list[dict]:
    if per_domain is None:
        return records
    rng = random.Random(seed)
    groups_by_domain: dict[str, list[str]] = defaultdict(list)
    group_to_records: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        group_id = _group_id(record)
        if group_id not in group_to_records:
            groups_by_domain[record["domain"]].append(group_id)
        group_to_records[group_id].append(record)
    selected_records: list[dict] = []
    for domain in sorted(groups_by_domain):
        group_ids = sorted(groups_by_domain[domain])
        rng.shuffle(group_ids)
        for group_id in group_ids[:per_domain]:
            selected_records.extend(group_to_records[group_id])
    return selected_records


def _build_group_split_manifest(
    records: list[dict],
    seed: int,
    source_limit_per_domain: int | None = None,
) -> dict:
    if source_limit_per_domain is not None:
        records = _limit_prefix_records(records, per_domain=source_limit_per_domain, seed=seed)
    records = _attach_group_splits(records, seed=seed)
    split_group_ids: dict[str, list[str]] = {"train": [], "val": [], "test": []}
    group_split_counts: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    record_split_counts: dict[str, int] = {"train": 0, "val": 0, "test": 0}
    groups_by_domain_split: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})
    records_by_domain_split: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})
    seen: set[str] = set()
    for record in records:
        split = record["split"]
        record_split_counts[split] += 1
        records_by_domain_split[record["domain"]][split] += 1
    for record in records:
        group_id = record["_group_id"]
        if group_id in seen:
            continue
        seen.add(group_id)
        split = record["split"]
        split_group_ids[split].append(group_id)
        group_split_counts[split] += 1
        groups_by_domain_split[record["domain"]][split] += 1
    for split in split_group_ids:
        split_group_ids[split].sort()
    return {
        "seed": seed,
        "source_limit_per_domain": source_limit_per_domain,
        "num_records": len(records),
        "num_groups": sum(group_split_counts.values()),
        "record_split_counts": record_split_counts,
        "group_split_counts": group_split_counts,
        "groups_by_domain_split": {
            domain: groups_by_domain_split[domain]
            for domain in sorted(groups_by_domain_split)
        },
        "records_by_domain_split": {
            domain: records_by_domain_split[domain]
            for domain in sorted(records_by_domain_split)
        },
        "split_group_ids": split_group_ids,
    }


def _build_summary(
    frozen_summary: dict,
    reranker_summary: dict,
    trace_summary: dict,
    prefix_summary: dict,
    main_table: dict,
    answer_swap_summary: dict,
    repair_pilot_summary: dict,
    repair_judge_summary: dict,
    args: argparse.Namespace,
) -> dict:
    best_trace = main_table["takeaways"]["best_trace_by_auroc"]
    best_prefix = main_table["takeaways"]["best_prefix_by_auroc"]
    best_reranker = main_table["takeaways"]["best_reranker_by_auroc"]
    local_amcd = repair_judge_summary["local_amcd"]
    coverage = repair_pilot_summary["selection"]
    answer_swap = answer_swap_summary["ass"]

    return {
        "spec_version": "processbench-suite-v1",
        "artifact_paths": {
            "trace_dataset": str(args.trace_dataset),
            "prefix_dataset": str(args.prefix_dataset),
            "frozen_summary": str(args.frozen_summary),
            "reranker_summary": str(args.reranker_summary),
            "trace_summary": str(args.trace_summary),
            "prefix_summary": str(args.prefix_summary),
            "main_table": str(args.main_table),
            "answer_swap_summary": str(args.answer_swap_summary),
            "repair_pilot_summary": str(args.repair_pilot_summary),
            "repair_judge_summary": str(args.repair_judge_summary),
            "manifest": str(args.output_manifest),
            "split_manifest": str(args.output_split_manifest),
        },
        "task_status": {
            "pb_trace": "production",
            "pb_prefix": "production",
            "answer_swap": "production",
            "local_repair": "pilot",
        },
        "tasks": {
            "pb_trace": {
                "dataset_summary": trace_summary,
                "best_model_by_auroc": best_trace,
                "split_summary": frozen_summary["trace_split_summary"],
            },
            "pb_prefix": {
                "dataset_summary": prefix_summary,
                "best_model_by_auroc": best_prefix,
                "split_summary": frozen_summary["prefix_split_summary"],
            },
            "answer_swap": {
                "successful_pairs": answer_swap["visible"]["num_pairs"],
                "visible_mean_abs_delta": answer_swap["visible"]["mean_abs_delta"],
                "masked_mean_abs_delta": answer_swap["masked"]["mean_abs_delta"],
                "gap_visible_minus_masked": answer_swap["ass_gap_visible_minus_masked"],
            },
            "local_repair": {
                "selected_sources": coverage["num_selected_sources"],
                "successful_pairs": coverage["num_successful_pairs"],
                "failed_sources": coverage["num_failed_sources"],
                "visible_local_amcd": local_amcd["visible"]["local_amcd"],
                "masked_local_amcd": local_amcd["masked"]["local_amcd"],
                "gap_visible_minus_masked": local_amcd["local_amcd_gap_visible_minus_masked"],
            },
        },
        "takeaways": {
            "best_trace_model": best_trace["model"],
            "best_prefix_model": best_prefix["model"],
            "best_reranker_model": best_reranker["model"],
            "trace_reranker_default_threshold_accuracy": reranker_summary["views"]["visible"]["metrics"]["ordinary_accuracy"],
            "trace_reranker_val_tuned_accuracy": reranker_summary["views"]["visible"]["threshold_analysis"]["test_accuracy_at_selected_threshold"],
            "answer_sensitivity_transfers": answer_swap["ass_gap_visible_minus_masked"] > 0,
            "local_repair_construction_closed": coverage["num_failed_sources"] == 0,
            "visible_local_repair_advantage": local_amcd["local_amcd_gap_visible_minus_masked"] > 0,
            "role": "external-source corroboration benchmark package, not a matched-quartet replacement",
        },
    }


def _build_manifest(summary: dict, args: argparse.Namespace) -> dict:
    return {
        "spec_version": "processbench-manifest-v1",
        "benchmark_name": "ProcessBench",
        "role": "external-source corroboration benchmark package",
        "canonical_docs": {
            "spec": "docs/processbench_benchmark.md",
        },
        "canonical_datasets": {
            "raw_import": "data/external/processbench_all.jsonl",
            "pb_trace": str(args.trace_dataset),
            "pb_prefix": str(args.prefix_dataset),
            "answer_swap_pilot": "data/external/processbench_answer_swap_pilot.jsonl",
            "local_repair_pilot": "data/external/processbench_repair_pd2_v3_partial_pilot.jsonl",
        },
        "canonical_artifacts": summary["artifact_paths"],
        "task_status": summary["task_status"],
        "claim_boundary": {
            "supports": [
                "external whole-trace corroboration",
                "external prefix-level corroboration",
                "external answer-sensitivity stress via answer-only swap",
                "small fully constructed local-repair pilot",
            ],
            "does_not_support": [
                "matched-quartet replacement for CRAFT",
                "full external-source AMCD benchmark identical to CRAFT",
                "deployment-benchmark replacement for CRAFT-Deploy",
            ],
        },
    }


def _build_split_manifest(
    trace_records: list[dict],
    prefix_records: list[dict],
    frozen_summary: dict,
    reranker_summary: dict,
    args: argparse.Namespace,
) -> dict:
    frozen_seed = int(frozen_summary["config"]["seed"])
    prefix_limit = frozen_summary["config"]["prefix_source_limit_per_domain"]
    reranker_seed = int(reranker_summary["config"]["seed"])
    return {
        "spec_version": "processbench-split-manifest-v1",
        "trace": {
            "dataset": str(args.trace_dataset),
            "producer": "grouped split by source_trace_id",
            "frozen": _build_group_split_manifest(trace_records, seed=frozen_seed),
            "reranker": _build_group_split_manifest(trace_records, seed=reranker_seed),
        },
        "prefix": {
            "dataset": str(args.prefix_dataset),
            "producer": "grouped split by source_trace_id after per-domain source cap",
            "frozen": _build_group_split_manifest(
                prefix_records,
                seed=frozen_seed,
                source_limit_per_domain=prefix_limit,
            ),
        },
    }


def _render_markdown(summary: dict) -> str:
    pb_trace = summary["tasks"]["pb_trace"]
    pb_prefix = summary["tasks"]["pb_prefix"]
    answer_swap = summary["tasks"]["answer_swap"]
    local_repair = summary["tasks"]["local_repair"]
    takeaways = summary["takeaways"]
    lines = [
        "# ProcessBench Benchmark Suite",
        "",
        "## Role",
        "",
        "- External-source corroboration benchmark package.",
        "- Not a matched-quartet replacement for CRAFT.",
        "- Canonical spec: `docs/processbench_benchmark.md`",
        "",
        "## PB-Trace",
        "",
        f"- Records: `{pb_trace['dataset_summary']['num_records']}`",
        f"- Best model by AUROC: `{pb_trace['best_model_by_auroc']['model']}` (`{pb_trace['best_model_by_auroc']['ordinary_auroc']:.4f}`)",
        f"- Canonical split counts: train `{pb_trace['split_summary']['train']}`, val `{pb_trace['split_summary']['val']}`, test `{pb_trace['split_summary']['test']}`",
        "",
        "## PB-Prefix",
        "",
        f"- Records: `{pb_prefix['dataset_summary']['num_records']}`",
        f"- Best model by AUROC: `{pb_prefix['best_model_by_auroc']['model']}` (`{pb_prefix['best_model_by_auroc']['ordinary_auroc']:.4f}`)",
        f"- Canonical split counts: train `{pb_prefix['split_summary']['train']}`, val `{pb_prefix['split_summary']['val']}`, test `{pb_prefix['split_summary']['test']}`",
        "",
        "## External Counterfactuals",
        "",
        f"- Answer-swap pairs: `{answer_swap['successful_pairs']}`",
        f"- Answer-swap mean abs delta: visible `{answer_swap['visible_mean_abs_delta']:.4f}`, masked `{answer_swap['masked_mean_abs_delta']:.4f}`, gap `{answer_swap['gap_visible_minus_masked']:.4f}`",
        f"- Local-repair pairs: `{local_repair['successful_pairs']} / {local_repair['selected_sources']}`",
        f"- Local repair discrimination: visible `{local_repair['visible_local_amcd']:.4f}`, masked `{local_repair['masked_local_amcd']:.4f}`, gap `{local_repair['gap_visible_minus_masked']:.4f}`",
        "",
        "## Takeaways",
        "",
        f"- Best trace verifier: `{takeaways['best_trace_model']}`",
        f"- Best prefix verifier: `{takeaways['best_prefix_model']}`",
        f"- Best reranker: `{takeaways['best_reranker_model']}`",
        f"- Visible reranker accuracy: default `{takeaways['trace_reranker_default_threshold_accuracy']:.4f}`, val-tuned `{takeaways['trace_reranker_val_tuned_accuracy']:.4f}`",
        f"- Answer sensitivity transfers: `{takeaways['answer_sensitivity_transfers']}`",
        f"- Local repair construction closed on current pilot: `{takeaways['local_repair_construction_closed']}`",
        f"- Visible local-repair advantage observed: `{takeaways['visible_local_repair_advantage']}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    frozen_summary = _load_json(args.frozen_summary)
    reranker_summary = _load_json(args.reranker_summary)
    trace_records = _load_jsonl(args.trace_dataset)
    prefix_records = _load_jsonl(args.prefix_dataset)
    summary = _build_summary(
        frozen_summary=frozen_summary,
        reranker_summary=reranker_summary,
        trace_summary=_load_json(args.trace_summary),
        prefix_summary=_load_json(args.prefix_summary),
        main_table=_load_json(args.main_table),
        answer_swap_summary=_load_json(args.answer_swap_summary),
        repair_pilot_summary=_load_json(args.repair_pilot_summary),
        repair_judge_summary=_load_json(args.repair_judge_summary),
        args=args,
    )
    manifest = _build_manifest(summary, args=args)
    split_manifest = _build_split_manifest(
        trace_records=trace_records,
        prefix_records=prefix_records,
        frozen_summary=frozen_summary,
        reranker_summary=reranker_summary,
        args=args,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    args.output_md.write_text(_render_markdown(summary), encoding="utf-8")
    args.output_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    args.output_split_manifest.write_text(json.dumps(split_manifest, indent=2), encoding="utf-8")
    print(json.dumps(summary["takeaways"], indent=2))


if __name__ == "__main__":
    main()
