from __future__ import annotations

import math

import torch

from civic_prm.baselines import score_baseline


def expand_step_scan_records(records: list[dict]) -> list[dict]:
    scan_records = []
    for record in records:
        for locus in range(len(record["step_texts"])):
            cloned = dict(record)
            cloned["trace_id"] = f"{record['trace_id']}::scan::{locus}"
            cloned["audited_locus"] = locus
            scan_records.append(cloned)
    return scan_records


def _parse_scan_trace_id(trace_id: str) -> tuple[str, int]:
    source_trace_id, locus_text = trace_id.rsplit("::scan::", 1)
    return source_trace_id, int(locus_text)


def aggregate_scanned_rows(
    model: torch.nn.Module,
    train_features: torch.Tensor,
    scan_features: torch.Tensor,
    scan_records: list[dict],
    original_records: list[dict],
    aggregation: str = "softmin",
    softmin_beta: float = 5.0,
) -> list[dict]:
    scored_scan_rows = score_baseline(
        model=model,
        train_features=train_features,
        eval_features=scan_features,
        eval_records=scan_records,
    )
    grouped: dict[str, list[tuple[int, dict]]] = {}
    for row in scored_scan_rows:
        source_trace_id, locus = _parse_scan_trace_id(row["trace_id"])
        grouped.setdefault(source_trace_id, []).append((locus, row))

    original_map = {record["trace_id"]: record for record in original_records}
    aggregated_rows = []
    for record in original_records:
        step_rows = sorted(grouped[record["trace_id"]], key=lambda item: item[0])
        logits = torch.tensor([row["logit"] for _, row in step_rows], dtype=torch.float32)
        if aggregation == "softmin":
            aggregated_logit = float(-(torch.logsumexp(-softmin_beta * logits, dim=0) / softmin_beta).item())
        elif aggregation == "mean":
            aggregated_logit = float(logits.mean().item())
        elif aggregation == "min":
            aggregated_logit = float(logits.min().item())
        else:
            raise ValueError(f"unsupported aggregation: {aggregation}")
        aggregated_score = float(torch.sigmoid(torch.tensor(aggregated_logit)).item())
        min_locus, min_row = min(step_rows, key=lambda item: item[1]["logit"])
        aggregated_rows.append(
            {
                "trace_id": record["trace_id"],
                "quartet_id": record["quartet_id"],
                "domain": record["domain"],
                "verbalizer_id": record["verbalizer_id"],
                "process_variant": record["process_variant"],
                "answer_variant": record["answer_variant"],
                "gold_valid": int(record["is_valid_process"]),
                "logit": round(aggregated_logit, 6),
                "score": round(aggregated_score, 6),
                "scan_num_steps": len(step_rows),
                "scan_min_locus": min_locus,
                "scan_min_step_score": round(min_row["score"], 6),
            }
        )
    return aggregated_rows

