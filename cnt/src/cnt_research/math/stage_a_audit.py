from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Sequence, Tuple


RecordKey = Tuple[str, int]


def load_stage_a_records(path: Path) -> Dict[RecordKey, Dict[str, Any]]:
    records: Dict[RecordKey, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            key = (payload["example_id"], int(payload["candidate_step_index"]))
            records[key] = payload
    return records


def _swap_mean(record: Dict[str, Any]) -> float:
    scores = record["scores"]
    return (float(scores["swap_quantity"]) + float(scores["swap_operation"])) / 2.0


def score_snapshot(record: Dict[str, Any]) -> Dict[str, float]:
    scores = record["scores"]
    return {
        "original": float(scores["original"]),
        "drop": float(scores["drop"]),
        "paraphrase": float(scores["paraphrase"]),
        "swap_quantity": float(scores["swap_quantity"]),
        "swap_operation": float(scores["swap_operation"]),
        "swap_mean": _swap_mean(record),
        "n_t": float(scores["n_t"]),
        "n_t_weighted": float(scores["n_t_weighted"]),
        "stability": float(scores["stability"]),
        "paraphrase_gap": float(scores["paraphrase_gap"]),
    }


def _validate_record_alignment(
    train_records: Dict[RecordKey, Dict[str, Any]],
    heldout_records: Dict[RecordKey, Dict[str, Any]],
) -> None:
    missing_in_heldout = sorted(key for key in train_records if key not in heldout_records)
    missing_in_train = sorted(key for key in heldout_records if key not in train_records)
    if missing_in_heldout or missing_in_train:
        raise ValueError(
            "Record keys do not align between train and held-out runs: "
            f"missing_in_heldout={missing_in_heldout[:3]} missing_in_train={missing_in_train[:3]}"
        )


def _prefilter_decision(
    train_record: Dict[str, Any],
    train_min_original_solve: float | None,
    train_max_paraphrase_gap: float | None,
    train_min_weighted_n: float | None,
    train_max_swap_solve: float | None,
) -> List[str]:
    reasons: List[str] = []
    scores = score_snapshot(train_record)
    if train_min_original_solve is not None and scores["original"] < train_min_original_solve:
        reasons.append("train_prefilter_original_solve")
    if train_max_paraphrase_gap is not None and scores["paraphrase_gap"] > train_max_paraphrase_gap:
        reasons.append("train_prefilter_paraphrase_gap")
    if train_min_weighted_n is not None and scores["n_t_weighted"] < train_min_weighted_n:
        reasons.append("train_prefilter_weighted_n")
    if train_max_swap_solve is not None and scores["swap_mean"] > train_max_swap_solve:
        reasons.append("train_prefilter_swap_solve")
    return reasons


def filter_stage_a_records(
    train_records_path: Path,
    heldout_records_path: Path,
    output_dir: Path,
    train_min_original_solve: float | None = None,
    train_max_paraphrase_gap: float | None = None,
    train_min_weighted_n: float | None = None,
    train_max_swap_solve: float | None = None,
) -> Dict[str, Any]:
    train_records = load_stage_a_records(train_records_path)
    heldout_records = load_stage_a_records(heldout_records_path)
    _validate_record_alignment(train_records, heldout_records)

    filtered_train_records: List[Dict[str, Any]] = []
    filtered_heldout_records: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []
    reason_counts = Counter()

    for key in sorted(train_records):
        train_record = train_records[key]
        heldout_record = heldout_records[key]
        reasons = _prefilter_decision(
            train_record=train_record,
            train_min_original_solve=train_min_original_solve,
            train_max_paraphrase_gap=train_max_paraphrase_gap,
            train_min_weighted_n=train_min_weighted_n,
            train_max_swap_solve=train_max_swap_solve,
        )
        keep = len(reasons) == 0
        if keep:
            filtered_train_records.append(train_record)
            filtered_heldout_records.append(heldout_record)
        reason_counts.update(reasons)
        manifest_rows.append(
            {
                "example_id": key[0],
                "candidate_step_index": key[1],
                "question": train_record["question"],
                "original_step": train_record["original_step"],
                "keep": keep,
                "drop_reasons": reasons,
                "train_scores": score_snapshot(train_record),
                "heldout_scores": score_snapshot(heldout_record),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    filtered_train_path = output_dir / "filtered_train_records.jsonl"
    filtered_heldout_path = output_dir / "filtered_heldout_records.jsonl"
    manifest_path = output_dir / "filtered_manifest.jsonl"
    for path, rows in (
        (filtered_train_path, filtered_train_records),
        (filtered_heldout_path, filtered_heldout_records),
        (manifest_path, manifest_rows),
    ):
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    kept_rows = [row for row in manifest_rows if row["keep"]]
    dropped_rows = [row for row in manifest_rows if not row["keep"]]
    summary = {
        "train_records_path": str(train_records_path),
        "heldout_records_path": str(heldout_records_path),
        "filtered_train_records_path": str(filtered_train_path),
        "filtered_heldout_records_path": str(filtered_heldout_path),
        "num_pairs_total": len(manifest_rows),
        "num_pairs_kept": len(kept_rows),
        "keep_fraction": len(kept_rows) / len(manifest_rows) if manifest_rows else 0.0,
        "drop_reason_counts": dict(sorted(reason_counts.items())),
        "train_min_original_solve": train_min_original_solve,
        "train_max_paraphrase_gap": train_max_paraphrase_gap,
        "train_min_weighted_n": train_min_weighted_n,
        "train_max_swap_solve": train_max_swap_solve,
        "sample_kept": kept_rows[:3],
        "sample_dropped": dropped_rows[:3],
    }
    (output_dir / "filter_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "summary": summary,
        "filtered_train_records": filtered_train_records,
        "filtered_heldout_records": filtered_heldout_records,
        "manifest_rows": manifest_rows,
    }


def _keep_decision(
    train_record: Dict[str, Any],
    heldout_record: Dict[str, Any],
    min_weighted_n: float,
    min_original_solve: float,
    max_paraphrase_gap: float,
    max_swap_solve: float,
) -> List[str]:
    reasons: List[str] = []
    for label, record in (("train", train_record), ("heldout", heldout_record)):
        scores = score_snapshot(record)
        if scores["n_t_weighted"] <= min_weighted_n:
            reasons.append(f"{label}_weighted_n")
        if scores["original"] < min_original_solve:
            reasons.append(f"{label}_original_solve")
        if scores["paraphrase_gap"] > max_paraphrase_gap:
            reasons.append(f"{label}_paraphrase_gap")
        if scores["swap_mean"] > max_swap_solve:
            reasons.append(f"{label}_swap_solve")
    return reasons


def _paired_record(
    key: RecordKey,
    train_record: Dict[str, Any],
    heldout_record: Dict[str, Any],
    keep_reasons: Sequence[str],
) -> Dict[str, Any]:
    return {
        "example_id": key[0],
        "candidate_step_index": key[1],
        "question": train_record["question"],
        "original_step": train_record["original_step"],
        "keep": len(keep_reasons) == 0,
        "drop_reasons": list(keep_reasons),
        "train_scores": score_snapshot(train_record),
        "heldout_scores": score_snapshot(heldout_record),
    }


def summarize_audit(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "num_pairs": 0,
            "num_kept": 0,
            "keep_fraction": 0.0,
            "drop_reason_counts": {},
            "mean_train_n_t_weighted_all": 0.0,
            "mean_heldout_n_t_weighted_all": 0.0,
            "mean_train_n_t_weighted_kept": 0.0,
            "mean_heldout_n_t_weighted_kept": 0.0,
            "sample_kept": [],
            "sample_dropped": [],
        }
    kept = [record for record in records if record["keep"]]
    reason_counts = Counter()
    for record in records:
        reason_counts.update(record["drop_reasons"])

    def avg(rows: Sequence[Dict[str, Any]], side: str, metric: str) -> float:
        if not rows:
            return 0.0
        return mean(float(row[f"{side}_scores"][metric]) for row in rows)

    return {
        "num_pairs": len(records),
        "num_kept": len(kept),
        "keep_fraction": len(kept) / len(records),
        "drop_reason_counts": dict(sorted(reason_counts.items())),
        "mean_train_n_t_weighted_all": avg(records, "train", "n_t_weighted"),
        "mean_heldout_n_t_weighted_all": avg(records, "heldout", "n_t_weighted"),
        "mean_train_n_t_weighted_kept": avg(kept, "train", "n_t_weighted"),
        "mean_heldout_n_t_weighted_kept": avg(kept, "heldout", "n_t_weighted"),
        "mean_train_paraphrase_gap_kept": avg(kept, "train", "paraphrase_gap"),
        "mean_heldout_paraphrase_gap_kept": avg(kept, "heldout", "paraphrase_gap"),
        "sample_kept": kept[:3],
        "sample_dropped": [record for record in records if not record["keep"]][:3],
    }


def audit_stage_a_runs(
    train_records_path: Path,
    heldout_records_path: Path,
    output_dir: Path,
    min_weighted_n: float = 0.0,
    min_original_solve: float = 2.0 / 3.0,
    max_paraphrase_gap: float = 1.0 / 3.0,
    max_swap_solve: float = 1.0 / 3.0,
) -> Dict[str, Any]:
    train_records = load_stage_a_records(train_records_path)
    heldout_records = load_stage_a_records(heldout_records_path)
    _validate_record_alignment(train_records, heldout_records)

    paired_records: List[Dict[str, Any]] = []
    for key in sorted(train_records):
        train_record = train_records[key]
        heldout_record = heldout_records[key]
        keep_reasons = _keep_decision(
            train_record=train_record,
            heldout_record=heldout_record,
            min_weighted_n=min_weighted_n,
            min_original_solve=min_original_solve,
            max_paraphrase_gap=max_paraphrase_gap,
            max_swap_solve=max_swap_solve,
        )
        paired_records.append(_paired_record(key, train_record, heldout_record, keep_reasons))

    summary = summarize_audit(paired_records)
    summary.update(
        {
            "train_records_path": str(train_records_path),
            "heldout_records_path": str(heldout_records_path),
            "min_weighted_n": min_weighted_n,
            "min_original_solve": min_original_solve,
            "max_paraphrase_gap": max_paraphrase_gap,
            "max_swap_solve": max_swap_solve,
        }
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage_a_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "stage_a_audit_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in paired_records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    with (output_dir / "stage_a_audit_kept.jsonl").open("w", encoding="utf-8") as handle:
        for record in paired_records:
            if record["keep"]:
                handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return {"summary": summary, "records": paired_records}
