# Audit Baseline v3 Local Qwen3-8B Summary

Date: 2026-04-01

Run id:

- `audit_baseline_v3_local_qwen3_8b`

Slice:

- `artifacts/audit/audit_dev_v3.jsonl`

Sample filter:

- `revise_only`

Model:

- local `Qwen3-8B`

## Main numbers

- total rows: 64
- total tokens: 0

Per condition:

- `direct`
  - count: 16
  - action match rate: 1.000
  - checker pass rate: 0.875
- `procedure_retry`
  - count: 16
  - action match rate: 1.000
  - checker pass rate: 0.812
- `gold_signal`
  - count: 16
  - action match rate: 1.000
  - checker pass rate: 1.000
- `matched_shuffle`
  - count: 16
  - action match rate: 1.000
  - checker pass rate: 0.750

## Key failures

`direct` failures:

- `plan_structured_search_2203`
  - model revised to `A -> B -> C -> D`, but that is not the target keep order
- `plan_structured_search_2205`
  - model revised to `A -> B -> D -> C`, which still fails the target checker

`procedure_retry` adds one more plan failure:

- `plan_structured_search_2102`

`gold_signal` failures:

- none

`matched_shuffle` failures:

- `plan_structured_search_2202`
- `plan_structured_search_2203`
- `plan_structured_search_2204`
- `plan_structured_search_2205`

These four failures all collapse toward the shuffled repair target
`A -> B -> C -> D`.

## Interpretation

- this dev slice shows a real content effect: `gold_signal` is perfect while
  `matched_shuffle` drops by `0.250`
- the gap is not just retry versus verifier, because `procedure_retry` lands at
  `0.812`, above `matched_shuffle` but below `gold_signal`
- however, the current signal is mostly plan-driven; code remains robust under
  shuffled verifier content on this slice

## Current conclusion

`structured_locality` is now empirically inside the Audit gate on dev slice,
but not yet through it.

The next correct move is to tighten the matched-shuffle construction for the
structured-plan half before opening any final slice.
