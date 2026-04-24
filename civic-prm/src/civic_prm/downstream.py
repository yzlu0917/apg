from __future__ import annotations


def group_rows_by_quartet(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["quartet_id"], []).append(row)
    return grouped


def summarize_quartet(rows: list[dict]) -> dict:
    by_process: dict[str, dict[str, float]] = {}
    by_answer: dict[str, dict[str, float]] = {}
    for row in rows:
        by_process.setdefault(row["process_variant"], {})[row["answer_variant"]] = row["score"]
        by_answer.setdefault(row["answer_variant"], {})[row["process_variant"]] = row["score"]

    valid_swap = abs(by_process["valid"]["correct"] - by_process["valid"]["swapped"])
    invalid_swap = abs(by_process["invalid"]["correct"] - by_process["invalid"]["swapped"])
    local_ass = (valid_swap + invalid_swap) / 2.0

    amcd_hits = []
    for answer_variant in ["correct", "swapped"]:
        amcd_hits.append(int(by_answer[answer_variant]["valid"] > by_answer[answer_variant]["invalid"]))
    local_amcd = sum(amcd_hits) / len(amcd_hits)

    top_row = max(rows, key=lambda row: row["score"])
    selected_valid = int(top_row["gold_valid"])
    exploit_lucky_answer = int(
        top_row["process_variant"] == "invalid" and top_row["answer_variant"] == "correct"
    )
    exploit_wrong_answer = int(
        top_row["process_variant"] == "invalid" and top_row["answer_variant"] == "swapped"
    )
    return {
        "quartet_id": rows[0]["quartet_id"],
        "domain": rows[0]["domain"],
        "local_ass_total": round(local_ass, 4),
        "ass_valid_pair": round(valid_swap, 4),
        "ass_invalid_pair": round(invalid_swap, 4),
        "local_amcd": round(local_amcd, 4),
        "selected_valid": selected_valid,
        "selection_gain_at4": round(selected_valid - 0.5, 4),
        "exploitability_rate": exploit_lucky_answer,
        "wrong_answer_invalid_rate": exploit_wrong_answer,
        "top_trace_id": top_row["trace_id"],
        "top_process_variant": top_row["process_variant"],
        "top_answer_variant": top_row["answer_variant"],
        "top_score": round(top_row["score"], 4),
    }


def compute_selection_metrics(rows: list[dict]) -> dict:
    quartet_rows = [summarize_quartet(group) for group in group_rows_by_quartet(rows).values()]
    if not quartet_rows:
        return {
            "selection_accuracy_at4": 0.0,
            "selection_gain_at4": 0.0,
            "exploitability_rate": 0.0,
            "wrong_answer_invalid_rate": 0.0,
            "ass_valid_pair": 0.0,
            "ass_invalid_pair": 0.0,
            "quartet_rows": [],
        }
    return {
        "selection_accuracy_at4": round(
            sum(row["selected_valid"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "selection_gain_at4": round(
            sum(row["selection_gain_at4"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "exploitability_rate": round(
            sum(row["exploitability_rate"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "wrong_answer_invalid_rate": round(
            sum(row["wrong_answer_invalid_rate"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "ass_valid_pair": round(
            sum(row["ass_valid_pair"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "ass_invalid_pair": round(
            sum(row["ass_invalid_pair"] for row in quartet_rows) / len(quartet_rows),
            4,
        ),
        "quartet_rows": quartet_rows,
    }
