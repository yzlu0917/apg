from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import torch

from civic_prm.downstream import compute_selection_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze answer-swap intervention and utility trade-offs from saved repair/baseline result files."
    )
    parser.add_argument(
        "--result",
        type=Path,
        nargs="+",
        default=[
            Path("artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json"),
            Path("artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json"),
        ],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/generated/mechanism_analysis_full_hybrid.json"),
    )
    return parser.parse_args()


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return math.nan
    x = torch.tensor(xs, dtype=torch.float32)
    y = torch.tensor(ys, dtype=torch.float32)
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denom = torch.sqrt((x_centered.pow(2).sum()) * (y_centered.pow(2).sum())).item()
    if denom == 0:
        return math.nan
    return float((x_centered * y_centered).sum().item() / denom)


def _ols_coefficients(y_values: list[float], columns: list[list[float]]) -> list[float]:
    y = torch.tensor(y_values, dtype=torch.float32).unsqueeze(-1)
    x_columns = [torch.ones(len(y_values), dtype=torch.float32)]
    x_columns.extend(torch.tensor(column, dtype=torch.float32) for column in columns)
    x = torch.stack(x_columns, dim=1)
    solution = torch.linalg.lstsq(x, y).solution.squeeze(-1)
    return [float(value) for value in solution.tolist()]


def _mediation(x_values: list[float], mediator_values: list[float], y_values: list[float]) -> dict:
    if len(x_values) < 3:
        return {
            "n": len(x_values),
            "total_effect": math.nan,
            "path_a": math.nan,
            "path_b": math.nan,
            "direct_effect": math.nan,
            "indirect_effect": math.nan,
        }
    total_coeffs = _ols_coefficients(y_values, [x_values])
    mediator_coeffs = _ols_coefficients(mediator_values, [x_values])
    direct_coeffs = _ols_coefficients(y_values, [x_values, mediator_values])
    return {
        "n": len(x_values),
        "total_effect": round(total_coeffs[1], 4),
        "path_a": round(mediator_coeffs[1], 4),
        "path_b": round(direct_coeffs[2], 4),
        "direct_effect": round(direct_coeffs[1], 4),
        "indirect_effect": round(mediator_coeffs[1] * direct_coeffs[2], 4),
    }


def _summarize_head(head_payload: dict) -> dict:
    rows = head_payload["test_rows"]
    utility = compute_selection_metrics(rows)
    quartet_rows = utility["quartet_rows"]
    local_ass = [row["local_ass_total"] for row in quartet_rows]
    local_amcd = [row["local_amcd"] for row in quartet_rows]
    selected_valid = [row["selected_valid"] for row in quartet_rows]
    selection_gain = [row["selection_gain_at4"] for row in quartet_rows]
    exploitability = [row["exploitability_rate"] for row in quartet_rows]
    wrong_answer_invalid = [row["wrong_answer_invalid_rate"] for row in quartet_rows]

    return {
        "metrics": head_payload["metrics"],
        "utility": {
            "selection_accuracy_at4": utility["selection_accuracy_at4"],
            "selection_gain_at4": utility["selection_gain_at4"],
            "exploitability_rate": utility["exploitability_rate"],
            "wrong_answer_invalid_rate": utility["wrong_answer_invalid_rate"],
        },
        "answer_swap_intervention": {
            "ass_valid_pair": utility["ass_valid_pair"],
            "ass_invalid_pair": utility["ass_invalid_pair"],
        },
        "local_relations": {
            "pearson_ass_vs_local_amcd": round(_pearson(local_ass, local_amcd), 4),
            "pearson_ass_vs_selection_gain": round(_pearson(local_ass, selection_gain), 4),
            "pearson_ass_vs_exploitability": round(_pearson(local_ass, exploitability), 4),
            "pearson_local_amcd_vs_selection_gain": round(_pearson(local_amcd, selection_gain), 4),
            "pearson_local_amcd_vs_exploitability": round(_pearson(local_amcd, exploitability), 4),
        },
        "quartet_rows": quartet_rows,
    }


def _iter_heads(result_payload: dict):
    for section_name in ["baselines", "repair_variants"]:
        for head_name, payload in result_payload.get(section_name, {}).items():
            yield section_name, head_name, payload


def main() -> None:
    args = parse_args()
    outputs = {
        "config": {
            "result_files": [str(path) for path in args.result],
        },
        "runs": {},
        "pooled_correlations": {},
        "pooled_local_relations": {},
        "mediation": {},
    }

    pooled_points = []
    pooled_local_points = []
    for result_path in args.result:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        run_label = result_path.stem
        run_summary = {
            "source_file": str(result_path),
            "heads": {},
        }
        for _, head_name, head_payload in _iter_heads(payload):
            head_summary = _summarize_head(head_payload)
            run_summary["heads"][head_name] = head_summary
            pooled_points.append(
                {
                    "run_label": run_label,
                    "head_name": head_name,
                    "ass_total": head_summary["metrics"]["ass_total"],
                    "amcd": head_summary["metrics"]["amcd"],
                    "ordinary_auroc": head_summary["metrics"]["ordinary_auroc"],
                    "selection_gain_at4": head_summary["utility"]["selection_gain_at4"],
                    "selection_accuracy_at4": head_summary["utility"]["selection_accuracy_at4"],
                    "exploitability_rate": head_summary["utility"]["exploitability_rate"],
                    "wrong_answer_invalid_rate": head_summary["utility"]["wrong_answer_invalid_rate"],
                }
            )
            for quartet_row in head_summary["quartet_rows"]:
                pooled_local_points.append(
                    {
                        "run_label": run_label,
                        "head_name": head_name,
                        "quartet_id": quartet_row["quartet_id"],
                        "domain": quartet_row["domain"],
                        "local_ass_total": quartet_row["local_ass_total"],
                        "local_amcd": quartet_row["local_amcd"],
                        "selection_gain_at4": quartet_row["selection_gain_at4"],
                        "exploitability_rate": quartet_row["exploitability_rate"],
                    }
                )
        outputs["runs"][run_label] = run_summary

    ass_total = [point["ass_total"] for point in pooled_points]
    amcd = [point["amcd"] for point in pooled_points]
    ordinary_auroc = [point["ordinary_auroc"] for point in pooled_points]
    selection_gain_at4 = [point["selection_gain_at4"] for point in pooled_points]
    selection_accuracy_at4 = [point["selection_accuracy_at4"] for point in pooled_points]
    exploitability_rate = [point["exploitability_rate"] for point in pooled_points]

    outputs["pooled_correlations"] = {
        "pearson_ass_vs_amcd": round(_pearson(ass_total, amcd), 4),
        "pearson_ass_vs_selection_gain": round(_pearson(ass_total, selection_gain_at4), 4),
        "pearson_ass_vs_exploitability": round(_pearson(ass_total, exploitability_rate), 4),
        "pearson_amcd_vs_selection_gain": round(_pearson(amcd, selection_gain_at4), 4),
        "pearson_amcd_vs_exploitability": round(_pearson(amcd, exploitability_rate), 4),
        "pearson_ordinary_auroc_vs_selection_gain": round(_pearson(ordinary_auroc, selection_gain_at4), 4),
        "pearson_ordinary_auroc_vs_exploitability": round(_pearson(ordinary_auroc, exploitability_rate), 4),
    }
    outputs["mediation"] = {
        "selection_gain_at4": _mediation(ass_total, amcd, selection_gain_at4),
        "selection_accuracy_at4": _mediation(ass_total, amcd, selection_accuracy_at4),
        "exploitability_rate": _mediation(ass_total, amcd, exploitability_rate),
    }
    outputs["pooled_points"] = pooled_points
    local_ass_total = [point["local_ass_total"] for point in pooled_local_points]
    local_amcd = [point["local_amcd"] for point in pooled_local_points]
    local_selection_gain = [point["selection_gain_at4"] for point in pooled_local_points]
    local_exploitability = [point["exploitability_rate"] for point in pooled_local_points]
    outputs["pooled_local_relations"] = {
        "pearson_ass_vs_local_amcd": round(_pearson(local_ass_total, local_amcd), 4),
        "pearson_ass_vs_selection_gain": round(_pearson(local_ass_total, local_selection_gain), 4),
        "pearson_ass_vs_exploitability": round(_pearson(local_ass_total, local_exploitability), 4),
        "pearson_local_amcd_vs_selection_gain": round(_pearson(local_amcd, local_selection_gain), 4),
        "pearson_local_amcd_vs_exploitability": round(_pearson(local_amcd, local_exploitability), 4),
        "mediation_selection_gain": _mediation(local_ass_total, local_amcd, local_selection_gain),
        "mediation_exploitability": _mediation(local_ass_total, local_amcd, local_exploitability),
    }
    outputs["pooled_local_points"] = pooled_local_points

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pooled_correlations": outputs["pooled_correlations"],
                "pooled_local_relations": outputs["pooled_local_relations"],
                "mediation": outputs["mediation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
