# Audit Final v1 API Summary

Date: 2026-03-31

Run id:

- `audit_final_v1_api`

Slice:

- `artifacts/audit/audit_final_v1.jsonl`

Controls:

- `artifacts/audit/audit_final_v1_matched_shuffle.jsonl`

## Main numbers

- total rows: `24`
- total tokens: `9677`

Per condition:

- `direct`
  - count: `6`
  - action match rate: `0.833`
  - checker pass rate: `0.833`
- `procedure_retry`
  - count: `6`
  - action match rate: `0.833`
  - checker pass rate: `1.000`
- `gold_signal`
  - count: `6`
  - action match rate: `1.000`
  - checker pass rate: `0.833`
- `matched_shuffle`
  - count: `6`
  - action match rate: `1.000`
  - checker pass rate: `0.833`

## Comparison to v0

- v0 `gold_signal` checker pass: `0.667`
- v1 `gold_signal` checker pass: `0.833`
- v0 `matched_shuffle` checker pass: `0.500`
- v1 `matched_shuffle` checker pass: `0.833`

Interpretation:

- the plan canonicalization repair removed most of the artificial final-slice
  failure seen in `v0`
- after removing that confound, the final slice no longer shows a meaningful
  checker-level gap between `gold_signal` and `matched_shuffle`
- `procedure_retry` reaches `1.000`, so procedure effect remains dominant

## Remaining failures

- `sym_harder_1101_0`
  - `direct` keeps the wrong `3.0`
  - `matched_shuffle` revises to `15`
- `plan_1102_harder_1`
  - `gold_signal` output omits the total-time field, so it still fails the
    structured checker

## Current conclusion

`Audit gate is still not closed after v1.`

Reason:

- `v1` fixes the main checker brittleness from `v0`
- but the repaired final slice does not preserve a meaningful
  `gold_signal > matched_shuffle` separation
- this is now closer to a clean negative/partial-result signal than to a
  checker artifact
