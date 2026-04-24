#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def api_file_mode(path: Path) -> str:
    name = path.stem
    if "round2" in name or "diverse" in name:
        return "diverse_same"
    if "round3" in name or "plausible" in name:
        return "plausible_flip"
    if "round4" in name or "targeted" in name:
        return "targeted_family"
    return "default"


def build_api_lookup(paths: List[Path]) -> Dict[Tuple[str, int, str, str], Dict]:
    lookup = {}
    for path in paths:
        mode = api_file_mode(path)
        for row in load_jsonl(path):
            for pair_type, variant_key in [
                ("same_semantics", "same_semantics"),
                ("semantic_flip", "semantic_flip"),
            ]:
                key = (
                    row["source_theorem_id"],
                    int(row["source_step_index"]),
                    pair_type,
                    row[variant_key],
                )
                lookup[key] = {
                    "prompt_mode": row.get("api_provenance", {}).get("prompt_mode", mode),
                    "prompt_version": row.get("api_provenance", {}).get("prompt_version", f"cts_api_v1_{mode}"),
                    "model": row.get("api_provenance", {}).get("model", ""),
                    "source_file": str(path),
                }
    return lookup


def annotate_provenance(row: Dict, api_lookup: Dict[Tuple[str, int, str, str], Dict]) -> Dict:
    out = dict(row)
    existing = row.get("provenance", "")
    key = (
        row["source_theorem_id"],
        int(row["source_step_index"]),
        row["type"],
        row["variant_step"],
    )
    if existing.startswith("manual"):
        out["provenance_clean"] = existing
        out["prompt_mode"] = None
        out["prompt_version"] = None
        out["provenance_source_file"] = None
        return out
    if existing.startswith("api_") and existing != "api_unknown":
        out["provenance_clean"] = existing
        derived_mode = existing.removeprefix("api_")
        if existing == "api_round1_curated":
            out["prompt_mode"] = "default"
            out["prompt_version"] = "cts_api_v1_default"
        elif existing == "api_round2_diverse":
            out["prompt_mode"] = "diverse_same"
            out["prompt_version"] = "cts_api_v1_diverse_same"
        elif existing == "api_plausible_flip":
            out["prompt_mode"] = "plausible_flip"
            out["prompt_version"] = "cts_api_v1_plausible_flip"
        else:
            out["prompt_mode"] = derived_mode
            out["prompt_version"] = f"cts_api_v1_{derived_mode}"
        out["provenance_source_file"] = None
        return out

    api_info = api_lookup.get(key)
    if api_info is not None:
        out["provenance_clean"] = f"api_{api_info['prompt_mode']}"
        out["prompt_mode"] = api_info["prompt_mode"]
        out["prompt_version"] = api_info["prompt_version"]
        out["provenance_source_file"] = api_info["source_file"]
    else:
        out["provenance_clean"] = row.get("provenance", "unresolved")
        out["prompt_mode"] = None
        out["prompt_version"] = None
        out["provenance_source_file"] = None
    return out


def attach_clean_pair_id(row: Dict) -> Dict:
    out = dict(row)
    pair_id = row["pair_id"]
    prompt_mode = row.get("prompt_mode")
    if "__unknown__" in pair_id and prompt_mode:
        out["pair_id_clean"] = pair_id.replace("__unknown__", f"__{prompt_mode}__")
    else:
        out["pair_id_clean"] = pair_id
    return out


def classify_same_family(row: Dict) -> str:
    source = row["source_step"].strip()
    variant = row["variant_step"].strip()
    notes = row.get("notes", "").lower()

    if source == variant:
        return "identity_duplicate"
    if "⟨" in variant or "constructor" in notes:
        return "constructor_notation"
    if source.startswith("exact Or.") and variant.startswith("refine Or."):
        return "tactic_keyword_rewrite"
    if source.startswith("rfl") or "eq.refl" in variant.lower():
        return "reflexivity_style"
    if ".left" in source or ".right" in source or "And.left" in variant or "And.right" in variant:
        return "projection_style"
    if "False.elim" in source or ".elim" in variant or "exfalso" in variant:
        return "eliminator_style"
    if "simpa using" in source and variant.startswith("exact "):
        return "theorem_application_style"
    if ".symm" in source or "Eq.symm" in variant:
        return "symmetry_style"
    return "other_same_rewrite"


def classify_same_subfamily(row: Dict) -> Optional[str]:
    if row["type"] != "same_semantics":
        return None

    family = classify_same_family(row)
    if family != "reflexivity_style":
        return family

    variant = row["variant_step"].strip().lower()
    notes = row.get("notes", "").lower()

    if "pure_format" in notes or variant == "exact rfl":
        return "reflexivity_pure_format"
    if "target_term" in notes or "explicit target term" in notes:
        return "reflexivity_target_term"
    if "proof_keyword" in notes or "simpa using" in variant or "show" in variant:
        return "reflexivity_proof_keyword"
    if "eq.refl" in variant:
        return "reflexivity_target_term"
    return "reflexivity_other"


def classify_flip_family(row: Dict) -> str:
    source = row["source_step"].strip()
    variant = row["variant_step"].strip()
    notes = row.get("notes", "").lower()

    if "ill-typed" in notes or "malformed" in notes or "False.intro" in variant:
        return "ill_typed_or_malformed"
    if (
        ".trans" in variant
        or "transitivity" in notes
        or "composition" in notes
        or "nesting" in notes
        or "wrong direction" in notes
    ):
        return "wrong_composition"
    if (
        ("Nat.add_zero" in source and "Nat.zero_add" in variant)
        or ("Nat.zero_add" in source and "Nat.add_zero" in variant)
        or ("Nat.mul_zero" in source and "Nat.zero_mul" in variant)
        or ("Nat.zero_mul" in source and "Nat.mul_zero" in variant)
    ):
        return "wrong_theorem_reference"
    if "Or.inl" in source and "Or.inr" in variant or "Or.inr" in source and "Or.inl" in variant:
        return "wrong_branch"
    if (".left" in source and ".right" in variant) or (".right" in source and ".left" in variant):
        return "wrong_projection"
    if ("And.left" in source and "And.right" in variant) or ("And.right" in source and "And.left" in variant):
        return "wrong_projection"
    if "And.intro" in source and "And.intro" in variant:
        return "wrong_argument_order"
    if "Eq.refl" in variant or "succ_eq_succ" in variant or "succ_ne_self" in variant:
        return "wrong_target_term"
    if variant == "exact h":
        return "goal_mismatch_direct_use"
    return "other_flip"


def classify_flip_subfamily(row: Dict, family: str) -> Optional[str]:
    if family != "wrong_composition":
        return family

    source = row["source_step"].strip()
    variant = row["variant_step"].strip()

    if ".trans" in variant and ".trans" not in source:
        return "transitivity_fabrication"
    if ".trans" in source and ".trans" in variant:
        return "transitivity_order_swap"
    return "application_argument_swap"


def annotate_family(row: Dict) -> Dict:
    out = dict(row)
    if row["type"] == "same_semantics":
        out["same_family"] = classify_same_family(row)
        out["same_subfamily"] = classify_same_subfamily(row)
        out["flip_family"] = None
        out["flip_subfamily"] = None
    else:
        out["same_family"] = None
        out["same_subfamily"] = None
        out["flip_family"] = classify_flip_family(row)
        out["flip_subfamily"] = classify_flip_subfamily(row, out["flip_family"])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize CTS panel provenance and family labels.")
    parser.add_argument("--panel", required=True)
    parser.add_argument("--api-jsonl", nargs="*", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    api_lookup = build_api_lookup([Path(p) for p in args.api_jsonl])
    rows = load_jsonl(Path(args.panel))

    annotated = []
    for row in rows:
        row = annotate_provenance(row, api_lookup)
        row = attach_clean_pair_id(row)
        row = annotate_family(row)
        annotated.append(row)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in annotated:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    provenance_counts: Dict[str, int] = {}
    same_counts: Dict[str, int] = {}
    flip_counts: Dict[str, int] = {}
    for row in annotated:
        provenance_counts[row["provenance_clean"]] = provenance_counts.get(row["provenance_clean"], 0) + 1
        if row["same_family"] is not None:
            same_counts[row["same_family"]] = same_counts.get(row["same_family"], 0) + 1
        if row["flip_family"] is not None:
            flip_counts[row["flip_family"]] = flip_counts.get(row["flip_family"], 0) + 1

    summary = {
        "rows": len(annotated),
        "provenance_clean": provenance_counts,
        "same_family": same_counts,
        "flip_family": flip_counts,
        "output": str(output_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
