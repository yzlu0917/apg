from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from civic_prm.acceptance import ACCEPTANCE_MODES
from civic_prm.api_judge import APIJudgeClient, load_api_config
from civic_prm.benchmark_v3 import (
    ROLE_ORDER,
    append_jsonl,
    candidate_from_record,
    build_candidates_for_record,
    build_pair_conditioned_candidates,
    prune_pair_candidates_with_reviewer,
    prune_candidates_with_reviewer,
    select_best_family,
    select_quartets_balanced,
    select_verbalizers,
)
from civic_prm.generator import load_dataset, save_dataset
from civic_prm.reviewer_backends import build_reviewer_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a strict benchmark-v3 candidate pool and select reviewer-filtered families.")
    parser.add_argument("--source-dataset", type=Path, default=Path("data/generated/craft_core_hard_blindfix_v4.jsonl"))
    parser.add_argument("--candidate-input", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("data/generated/craft_core_benchmark_v3_smoke.jsonl"))
    parser.add_argument("--summary-output", type=Path, default=Path("artifacts/benchmark_v3/benchmark_v3_smoke_summary.json"))
    parser.add_argument("--candidate-output", type=Path, default=Path("artifacts/benchmark_v3/benchmark_v3_smoke_candidates.jsonl"))
    parser.add_argument("--review-output", type=Path, default=Path("artifacts/benchmark_v3/benchmark_v3_smoke_reviews.jsonl"))
    parser.add_argument("--candidate-output-mode", choices=["raw", "pruned"], default="raw")
    parser.add_argument("--quartets-per-domain", type=int, default=1)
    parser.add_argument("--verbalizers-per-quartet", type=int, default=1)
    parser.add_argument("--candidates-per-role", type=int, default=2)
    parser.add_argument("--base-temperature", type=float, default=0.8)
    parser.add_argument("--pair-conditioned-generation", action="store_true")
    parser.add_argument("--pair-contrast-generation", action="store_true")
    parser.add_argument("--regenerate-from-candidate-input", action="store_true")
    parser.add_argument("--pair-regeneration-rounds", type=int, default=0)
    parser.add_argument("--pair-regeneration-top-k", type=int, default=1)
    parser.add_argument("--pair-regeneration-threshold", type=float, default=None)
    parser.add_argument("--max-pairs-per-answer-variant-after-prune", type=int, default=None)
    parser.add_argument("--pair-prune-max-detectability", type=float, default=None)
    parser.add_argument("--candidate-max-detectability", type=float, default=None)
    parser.add_argument("--max-candidates-per-role-after-prune", type=int, default=None)
    parser.add_argument("--max-pair-detectability", type=float, default=0.8)
    parser.add_argument("--acceptance-mode", choices=ACCEPTANCE_MODES, default="strict")
    parser.add_argument("--allow-fallback-selection", action="store_true")
    parser.add_argument(
        "--reviewer-backend",
        choices=["api", "local_qwen", "api_local_max", "api_local_advmax"],
        default="api",
    )
    parser.add_argument("--reviewer-model-root", type=Path, default=Path("/cephfs/shared/hf_cache/hub/Qwen3-8B"))
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for path in [args.output, args.summary_output, args.candidate_output, args.review_output]:
        if path.exists():
            path.unlink()
    records = load_dataset(args.source_dataset)
    selected_quartets = select_quartets_balanced(records, quartets_per_domain=args.quartets_per_domain, seed=args.seed)
    selected_verbalizers = select_verbalizers(
        records,
        selected_quartets=selected_quartets,
        verbalizers_per_quartet=args.verbalizers_per_quartet,
        seed=args.seed,
    )

    config = None
    generation_client = None
    api_reviewer_client = None
    if (
        args.candidate_input is None
        or args.regenerate_from_candidate_input
        or args.reviewer_backend in {"api", "api_local_max", "api_local_advmax"}
    ):
        config = load_api_config()
    if args.candidate_input is None or args.regenerate_from_candidate_input:
        assert config is not None
        generation_client = APIJudgeClient(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            max_retries=3,
        )
    if args.reviewer_backend in {"api", "api_local_max", "api_local_advmax"}:
        assert config is not None
        api_reviewer_client = APIJudgeClient(
            base_url=config["base_url"],
            model=config["model"],
            api_key=config["api_key"],
            max_retries=3,
        )
    reviewer_client = build_reviewer_client(
        backend=args.reviewer_backend,
        api_client=api_reviewer_client,
        reviewer_model_root=args.reviewer_model_root,
    )

    selected_records = []
    candidate_rows: list[dict] = []
    candidate_output_rows: list[dict] = []
    review_rows: list[dict] = []
    selected_families: list[dict] = []
    usage_totals = Counter()
    skipped_groups: list[dict] = []

    candidate_input_rows: list[dict] = []
    candidate_input_map: dict[tuple[str, str], dict[str, list]] = {}
    if args.candidate_input is not None:
        candidate_input_rows = [
            json.loads(line)
            for line in args.candidate_input.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for row in candidate_input_rows:
            candidate = candidate_from_record(row)
            key = (candidate.quartet_id, candidate.verbalizer_id)
            role_map = candidate_input_map.setdefault(key, {role: [] for role in ROLE_ORDER})
            role_map[candidate.counterfactual_role].append(candidate)

    for quartet_id in selected_quartets:
        for verbalizer_id in selected_verbalizers[quartet_id]:
            group = [
                record
                for record in records
                if record.quartet_id == quartet_id and record.verbalizer_id == verbalizer_id
            ]
            role_map = {record.counterfactual_role: record for record in group}
            if set(role_map) != set(ROLE_ORDER):
                skipped_groups.append(
                    {
                        "quartet_id": quartet_id,
                        "verbalizer_id": verbalizer_id,
                        "reason": "missing source roles",
                    }
                )
                continue

            candidate_map = {}
            raw_candidate_map = {}
            if args.candidate_input is not None:
                candidate_map = candidate_input_map.get((quartet_id, f"{verbalizer_id}_b3"), {})
                if set(candidate_map) != set(ROLE_ORDER) or any(not candidate_map.get(role) for role in ROLE_ORDER):
                    skipped_groups.append(
                        {
                            "quartet_id": quartet_id,
                            "verbalizer_id": verbalizer_id,
                            "reason": "candidate_input_missing_roles",
                        }
                    )
                    continue
                raw_candidate_map = {role: list(candidates) for role, candidates in candidate_map.items()}
                if args.regenerate_from_candidate_input:
                    if not args.pair_conditioned_generation:
                        skipped_groups.append(
                            {
                                "quartet_id": quartet_id,
                                "verbalizer_id": verbalizer_id,
                                "reason": "regenerate_from_candidate_input_requires_pair_generation",
                            }
                        )
                        continue
                    regenerated_map = {}
                    pair_specs = [
                        ("valid_correct", "invalid_correct"),
                        ("valid_swapped", "invalid_swapped"),
                    ]
                    for role_a, role_b in pair_specs:
                        source_a = sorted(candidate_map[role_a], key=lambda item: item.candidate_id)[0]
                        source_b = sorted(candidate_map[role_b], key=lambda item: item.candidate_id)[0]
                        try:
                            assert generation_client is not None
                            candidates_a, candidates_b, usage = build_pair_conditioned_candidates(
                                generation_client,
                                source_a,
                                source_b,
                                num_candidates=args.candidates_per_role,
                                base_temperature=args.base_temperature,
                                contrast_aware=args.pair_contrast_generation,
                                reviewer_client=reviewer_client,
                                regeneration_rounds=args.pair_regeneration_rounds,
                                regeneration_top_k=args.pair_regeneration_top_k,
                                regeneration_threshold=args.pair_regeneration_threshold,
                            )
                        except Exception as error:
                            skipped_groups.append(
                                {
                                    "quartet_id": quartet_id,
                                    "verbalizer_id": verbalizer_id,
                                    "reason": f"candidate_input_pair_regeneration_failed:{role_a}:{role_b}",
                                    "error": str(error),
                                }
                            )
                            regenerated_map = {}
                            break
                        usage_totals.update(usage)
                        regenerated_map[role_a] = candidates_a
                        regenerated_map[role_b] = candidates_b
                        candidate_rows.extend(candidate.to_record() for candidate in candidates_a)
                        candidate_rows.extend(candidate.to_record() for candidate in candidates_b)
                    if set(regenerated_map) != set(ROLE_ORDER):
                        continue
                    candidate_map = regenerated_map
                    raw_candidate_map = {role: list(candidates) for role, candidates in candidate_map.items()}
            elif args.pair_conditioned_generation:
                pair_specs = [
                    ("valid_correct", "invalid_correct"),
                    ("valid_swapped", "invalid_swapped"),
                ]
                for role_a, role_b in pair_specs:
                    try:
                        assert generation_client is not None
                        candidates_a, candidates_b, usage = build_pair_conditioned_candidates(
                            generation_client,
                            role_map[role_a],
                            role_map[role_b],
                            num_candidates=args.candidates_per_role,
                            base_temperature=args.base_temperature,
                            contrast_aware=args.pair_contrast_generation,
                            reviewer_client=reviewer_client,
                            regeneration_rounds=args.pair_regeneration_rounds,
                            regeneration_top_k=args.pair_regeneration_top_k,
                            regeneration_threshold=args.pair_regeneration_threshold,
                        )
                    except Exception as error:
                        skipped_groups.append(
                            {
                                "quartet_id": quartet_id,
                                "verbalizer_id": verbalizer_id,
                                "reason": f"pair_candidate_generation_failed:{role_a}:{role_b}",
                                "error": str(error),
                            }
                        )
                        candidate_map = {}
                        break
                    usage_totals.update(usage)
                    candidate_map[role_a] = candidates_a
                    candidate_map[role_b] = candidates_b
                    candidate_rows.extend(candidate.to_record() for candidate in candidates_a)
                    candidate_rows.extend(candidate.to_record() for candidate in candidates_b)
                raw_candidate_map = {role: list(candidates) for role, candidates in candidate_map.items()}
            else:
                for role in ROLE_ORDER:
                    try:
                        assert generation_client is not None
                        candidates, usage = build_candidates_for_record(
                            generation_client,
                            role_map[role],
                            num_candidates=args.candidates_per_role,
                            base_temperature=args.base_temperature,
                        )
                    except Exception as error:
                        skipped_groups.append(
                            {
                                "quartet_id": quartet_id,
                                "verbalizer_id": verbalizer_id,
                                "reason": f"candidate_generation_failed:{role}",
                                "error": str(error),
                            }
                        )
                        candidate_map = {}
                        break
                    usage_totals.update(usage)
                    candidate_map[role] = candidates
                    candidate_rows.extend(candidate.to_record() for candidate in candidates)
                raw_candidate_map = {role: list(candidates) for role, candidates in candidate_map.items()}
            if set(candidate_map) != set(ROLE_ORDER):
                continue

            prune_summary = None
            pair_review_cache = None
            if args.pair_conditioned_generation and (
                args.max_pairs_per_answer_variant_after_prune is not None or args.pair_prune_max_detectability is not None
            ):
                pruned_candidate_map, prune_reviews, prune_summary, prune_usage, pair_review_cache = prune_pair_candidates_with_reviewer(
                    reviewer_client,
                    quartet_id=quartet_id,
                    domain=group[0].domain,
                    verbalizer_id=verbalizer_id,
                    candidate_map=candidate_map,
                    acceptance_mode=args.acceptance_mode,
                    max_pairs_per_answer_variant_after_prune=args.max_pairs_per_answer_variant_after_prune,
                    pair_prune_max_detectability=args.pair_prune_max_detectability,
                )
                usage_totals.update(prune_usage)
                review_rows.extend(prune_reviews)
                candidate_map = pruned_candidate_map
                if not prune_summary["all_roles_survive"]:
                    skipped_groups.append(
                        {
                            "quartet_id": quartet_id,
                            "verbalizer_id": verbalizer_id,
                            "reason": "pair_candidate_prune_failed",
                            "details": prune_summary,
                        }
                    )
                    continue
            elif args.candidate_max_detectability is not None or args.max_candidates_per_role_after_prune is not None:
                pruned_candidate_map, prune_reviews, prune_summary, prune_usage = prune_candidates_with_reviewer(
                    reviewer_client,
                    quartet_id=quartet_id,
                    domain=group[0].domain,
                    verbalizer_id=verbalizer_id,
                    candidate_map=candidate_map,
                    candidate_max_detectability=args.candidate_max_detectability,
                    max_candidates_per_role_after_prune=args.max_candidates_per_role_after_prune,
                )
                usage_totals.update(prune_usage)
                review_rows.extend(prune_reviews)
                candidate_map = pruned_candidate_map
                if not prune_summary["all_roles_survive"]:
                    skipped_groups.append(
                        {
                            "quartet_id": quartet_id,
                            "verbalizer_id": verbalizer_id,
                            "reason": "candidate_prune_failed",
                            "details": prune_summary,
                        }
                    )
                    continue

            export_map = candidate_map if args.candidate_output_mode == "pruned" else raw_candidate_map
            for role in ROLE_ORDER:
                candidate_output_rows.extend(candidate.to_record() for candidate in export_map.get(role, []))

            best_family, best_summary, best_reviews, review_usage = select_best_family(
                reviewer_client,
                quartet_id=quartet_id,
                domain=group[0].domain,
                verbalizer_id=verbalizer_id,
                candidate_map=candidate_map,
                acceptance_mode=args.acceptance_mode,
                max_pair_detectability=args.max_pair_detectability,
                allow_fallback_selection=args.allow_fallback_selection,
                pair_review_cache=pair_review_cache,
            )
            usage_totals.update(review_usage)
            review_rows.extend(best_reviews)
            if best_family is None:
                skipped_groups.append(
                    {
                        "quartet_id": quartet_id,
                        "verbalizer_id": verbalizer_id,
                        "reason": "review_selection_failed",
                        "details": {
                            "candidate_prune": prune_summary,
                            "family_selection": best_summary,
                        },
                    }
                )
                continue
            if prune_summary is not None:
                best_summary["candidate_prune"] = prune_summary
            selected_families.append(best_summary)
            for role in ROLE_ORDER:
                selected_records.append(best_family[role].to_trace_example())

    save_dataset(selected_records, args.output)
    if args.candidate_output_mode == "raw":
        append_jsonl(args.candidate_output, candidate_input_rows or candidate_rows)
    else:
        append_jsonl(args.candidate_output, candidate_output_rows)
    append_jsonl(args.review_output, review_rows)

    summary = {
        "source_dataset": str(args.source_dataset),
        "candidate_input": str(args.candidate_input) if args.candidate_input is not None else None,
        "output_dataset": str(args.output),
        "candidate_output_mode": args.candidate_output_mode,
        "selected_quartets": selected_quartets,
        "selected_verbalizers": selected_verbalizers,
        "quartets_per_domain": args.quartets_per_domain,
        "verbalizers_per_quartet": args.verbalizers_per_quartet,
        "candidates_per_role": args.candidates_per_role,
        "pair_conditioned_generation": args.pair_conditioned_generation,
        "pair_contrast_generation": args.pair_contrast_generation,
        "regenerate_from_candidate_input": args.regenerate_from_candidate_input,
        "pair_regeneration_rounds": args.pair_regeneration_rounds,
        "pair_regeneration_top_k": args.pair_regeneration_top_k,
        "pair_regeneration_threshold": args.pair_regeneration_threshold,
        "max_pairs_per_answer_variant_after_prune": args.max_pairs_per_answer_variant_after_prune,
        "pair_prune_max_detectability": args.pair_prune_max_detectability,
        "candidate_max_detectability": args.candidate_max_detectability,
        "max_candidates_per_role_after_prune": args.max_candidates_per_role_after_prune,
        "max_pair_detectability": args.max_pair_detectability,
        "acceptance_mode": args.acceptance_mode,
        "allow_fallback_selection": args.allow_fallback_selection,
        "reviewer_backend": args.reviewer_backend,
        "reviewer_model_root": str(args.reviewer_model_root),
        "num_selected_records": len(selected_records),
        "num_selected_families": len(selected_families),
        "domains": dict(Counter(record.domain for record in selected_records)),
        "usage": dict(usage_totals),
        "selected_family_summaries": selected_families,
        "skipped_groups": skipped_groups,
        "seed": args.seed,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
