# Contrastive Locality Structured Code Object

Date: 2026-04-01

## Purpose

Create a code-side counterpart to the structured-plan object, so
`contrastive_locality` does not rely on free-form code generation alone.

## Object definition

Each code pair uses:

- a short Python function with one local conditional expression as the failure
  site
- a structured checker JSON string in `checker.reference`
- an explicit set of nearby repair candidates

The checker schema is:

```json
{
  "schema": "code_local_repair_v1",
  "entrypoint": "function_name",
  "tests": ["assert function_name(...) == ..."],
  "repair_candidates": [
    "gold_condition",
    "nearby_wrong_condition_1",
    "nearby_wrong_condition_2"
  ]
}
```

## Acceptance geometry

For a candidate pair to count as a valid structured-code object:

- `keep` code passes all structured tests
- `revise` code fails the structured tests
- replacing the fail span with the gold condition passes all tests
- every nearby non-gold repair candidate still fails at least one test

This makes the local repair object explicit and testable without relying on
free-form model judgment about what counts as a nearby repair.

## Why this is better than ad hoc code pairs

- nearby repair candidates are explicit rather than heuristic
- uniqueness of the gold repair is checked by execution
- the object is reusable and can be expanded by search or construction

## Current status

As of 2026-04-01:

- the object design exists
- the judge now supports `code_local_repair_v1`
- `judge_v4` can deterministically `auto_accept` exact structured-code pairs
  without an API call when execution fully proves the local-repair geometry
- the search-based builder is implemented
- `batch22` and `batch23` both reviewed cleanly
- a frozen reviewed subpanel now exists at
  `artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl`
