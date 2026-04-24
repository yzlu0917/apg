from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from civic_prm.domains import DOMAIN_REGISTRY
from civic_prm.schema import TraceExample


def _compose_trace(step_texts: list[str], final_answer_line: str) -> str:
    return "\n".join(step_texts + [final_answer_line])


def build_week1_dataset(seed: int, per_domain: int, difficulty: str = "standard") -> list[TraceExample]:
    rng = random.Random(seed)
    records: list[TraceExample] = []
    for domain_name, sampler in DOMAIN_REGISTRY.items():
        for problem_index in range(per_domain):
            instance = sampler(rng, problem_index, difficulty=difficulty)
            quartet_id = instance["problem_id"]
            for verbalizer in instance["verbalizers"]:
                valid_steps = [
                    verbalizer["render_step"](step, i)
                    for i, step in enumerate(instance["valid_steps"])
                ]
                invalid_steps = [
                    verbalizer["render_step"](step, i)
                    for i, step in enumerate(instance["invalid_steps"])
                ]
                variants = [
                    ("valid_correct", valid_steps, verbalizer["answer_correct"], verbalizer["answer_swapped"], True, True),
                    ("invalid_correct", invalid_steps, verbalizer["answer_correct"], verbalizer["answer_swapped"], False, True),
                    ("valid_swapped", valid_steps, verbalizer["answer_swapped"], verbalizer["answer_correct"], True, False),
                    ("invalid_swapped", invalid_steps, verbalizer["answer_swapped"], verbalizer["answer_correct"], False, False),
                ]
                for role, steps, answer_line, masked_source, is_valid_process, answer_is_correct in variants:
                    masked_answer_line = answer_line.replace(
                        instance["correct_answer"] if answer_is_correct else instance["distractor_answer"],
                        "[ANSWER_MASK]",
                    )
                    trace_text = _compose_trace(steps, answer_line)
                    masked_trace_text = _compose_trace(steps, masked_answer_line)
                    records.append(
                        TraceExample(
                            trace_id=f"{quartet_id}-{verbalizer['id']}-{role}",
                            quartet_id=quartet_id,
                            problem_id=instance["problem_id"],
                            domain=domain_name,
                            verbalizer_id=verbalizer["id"],
                            audited_locus=instance["audited_locus"],
                            counterfactual_role=role,
                            process_variant="valid" if is_valid_process else "invalid",
                            answer_variant="correct" if answer_is_correct else "swapped",
                            is_valid_process=is_valid_process,
                            answer_is_correct=answer_is_correct,
                            problem_text=verbalizer["problem_text"],
                            step_texts=steps,
                            final_answer_line=answer_line,
                            masked_answer_line=masked_answer_line,
                            trace_text=trace_text,
                            masked_trace_text=masked_trace_text,
                            metadata=instance["metadata"],
                        )
                    )
    return records


def save_dataset(records: list[TraceExample], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


def load_dataset(input_path: str | Path) -> list[TraceExample]:
    records: list[TraceExample] = []
    with Path(input_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            records.append(TraceExample(**payload))
    return records


def summarize_dataset(records: list[TraceExample]) -> dict:
    domain_counts = Counter(record.domain for record in records)
    verbalizer_counts = Counter(record.verbalizer_id for record in records)
    return {
        "num_traces": len(records),
        "num_quartets": len({record.quartet_id for record in records}),
        "difficulty": records[0].metadata.get("difficulty", "standard") if records else "unknown",
        "domains": dict(domain_counts),
        "verbalizers": dict(verbalizer_counts),
    }


def _select_domain_balanced_quartets(
    grouped: dict[str, list[TraceExample]],
    sample_quartets: int,
    seed: int,
) -> list[str]:
    rng = random.Random(seed)
    quartets_by_domain: dict[str, list[str]] = {}
    for quartet_id, members in grouped.items():
        quartets_by_domain.setdefault(members[0].domain, []).append(quartet_id)
    for quartet_ids in quartets_by_domain.values():
        quartet_ids.sort()
        rng.shuffle(quartet_ids)

    selected: list[str] = []
    while len(selected) < sample_quartets:
        advanced = False
        for domain in sorted(quartets_by_domain):
            quartet_ids = quartets_by_domain[domain]
            if not quartet_ids:
                continue
            selected.append(quartet_ids.pop())
            advanced = True
            if len(selected) >= sample_quartets:
                break
        if not advanced:
            break
    return selected


def export_blind_audit_sample(
    records: list[TraceExample],
    output_path: str | Path,
    sample_quartets: int = 6,
    seed: int = 17,
    answer_key_output_path: str | Path | None = None,
    response_form_output_path: str | Path | None = None,
) -> dict:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[TraceExample]] = {}
    for record in records:
        grouped.setdefault(record.quartet_id, []).append(record)
    eligible_grouped = {}
    eligible_verbalizers_by_quartet: dict[str, list[str]] = {}
    for quartet_id, members in grouped.items():
        by_verbalizer: dict[str, list[TraceExample]] = {}
        for record in members:
            by_verbalizer.setdefault(record.verbalizer_id, []).append(record)
        eligible_verbalizer_ids = [
            verbalizer_id
            for verbalizer_id, rows in sorted(by_verbalizer.items())
            if {"valid_correct", "invalid_correct"}.issubset({row.counterfactual_role for row in rows})
        ]
        if eligible_verbalizer_ids:
            eligible_grouped[quartet_id] = members
            eligible_verbalizers_by_quartet[quartet_id] = eligible_verbalizer_ids
    selected = _select_domain_balanced_quartets(eligible_grouped, sample_quartets=sample_quartets, seed=seed)
    rng = random.Random(seed)
    lines = [
        "# Blind Audit Packet",
        "",
        "The labels are intentionally hidden.",
        "",
        "Review prompt:",
        "- Do not judge which trace is correct.",
        "- Only judge whether either trace looks artificially templated, hand-edited, or obviously synthetic.",
        "- For each item, mark one option: `Trace 1`, `Trace 2`, `Both`, or `Neither`.",
        "- Add a short note only if something looked suspicious.",
        "",
    ]
    answer_key: list[dict] = []
    for quartet_id in selected:
        by_verbalizer: dict[str, list[TraceExample]] = {}
        for record in eligible_grouped[quartet_id]:
            by_verbalizer.setdefault(record.verbalizer_id, []).append(record)
        verbalizer_id = rng.choice(eligible_verbalizers_by_quartet[quartet_id])
        pair_records = by_verbalizer[verbalizer_id]
        pair_map = {
            record.counterfactual_role: record
            for record in pair_records
        }
        pair = [
            pair_map["valid_correct"],
            pair_map["invalid_correct"],
        ]
        rng.shuffle(pair)
        item_id = f"item-{len(answer_key) + 1:02d}"
        lines.append(f"## {item_id} | {quartet_id}")
        lines.append(f"Domain: {pair[0].domain}")
        lines.append(f"Problem: {pair[0].problem_text}")
        lines.append("")
        for idx, record in enumerate(pair[:2], start=1):
            lines.append(f"### Trace {idx}")
            lines.append(record.trace_text)
            lines.append("")
        lines.append("Reviewer response:")
        lines.append("- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`")
        lines.append("- Confidence: `1` / `2` / `3` / `4` / `5`")
        lines.append("- Notes:")
        lines.append("")
        answer_key.append(
            {
                "item_id": item_id,
                "quartet_id": quartet_id,
                "domain": pair[0].domain,
                "problem_id": pair[0].problem_id,
                "verbalizer_id": verbalizer_id,
                "trace_1_id": pair[0].trace_id,
                "trace_1_role": pair[0].counterfactual_role,
                "trace_2_id": pair[1].trace_id,
                "trace_2_role": pair[1].counterfactual_role,
            }
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    if answer_key_output_path is not None:
        key_path = Path(answer_key_output_path)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(json.dumps(answer_key, indent=2), encoding="utf-8")
    if response_form_output_path is not None:
        form_path = Path(response_form_output_path)
        form_path.parent.mkdir(parents=True, exist_ok=True)
        header = "item_id,quartet_id,domain,more_artificial,confidence,notes\n"
        rows = [
            f"{entry['item_id']},{entry['quartet_id']},{entry['domain']},,,"
            for entry in answer_key
        ]
        form_path.write_text(header + "\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    return {
        "num_items": len(answer_key),
        "selected_quartets": selected,
        "domains": dict(Counter(eligible_grouped[quartet_id][0].domain for quartet_id in selected)),
        "verbalizers": dict(Counter(entry["verbalizer_id"] for entry in answer_key)),
        "num_eligible_quartets": len(eligible_grouped),
        "num_incomplete_quartets_skipped": len(grouped) - len(eligible_grouped),
        "seed": seed,
        "packet_path": str(path),
        "answer_key_path": str(answer_key_output_path) if answer_key_output_path is not None else None,
        "response_form_path": str(response_form_output_path) if response_form_output_path is not None else None,
    }
