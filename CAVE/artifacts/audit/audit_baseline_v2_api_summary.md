# Audit Baseline v2 API Summary

Date: 2026-03-31

Run id:

- `audit_baseline_v2_api`

Slice:

- `artifacts/audit/audit_dev_v2.jsonl`

Sample filter:

- `revise_only`

## Main numbers

- total rows: 44
- total tokens: 17331

Per condition:

- `direct`
  - count: 11
  - action match rate: 0.909
  - checker pass rate: 0.909
- `procedure_retry`
  - count: 11
  - action match rate: 0.909
  - checker pass rate: 0.909
- `gold_signal`
  - count: 11
  - action match rate: 1.000
  - checker pass rate: 1.000
- `matched_shuffle`
  - count: 11
  - action match rate: 0.818
  - checker pass rate: 0.727

## Comparison to v1

- v1 `matched_shuffle` checker pass: `0.857`
- v2 `matched_shuffle` checker pass: `0.727`

The larger and harder slice increases the observed shuffle penalty.

## Key failures under matched shuffle

- `sym_0`
  - shuffled signal pushed the model to output `7` instead of `15`
- `plan_pair_0_301`
  - shuffled signal led to `keep` on an actually bad trace
- `plan_pair_1_harder_602`
  - shuffled signal did not recover the correct `infinite` answer

## Interpretation

- `gold_signal` now cleanly dominates `matched_shuffle` on this dev slice.
- The gap is materially larger than in v1.
- But `direct` and `procedure_retry` remain strong, so procedure effect is still
  substantial.

## Current conclusion

The empirical audit story is now stronger and points in the proposal's intended
direction, but it is still dev-slice evidence rather than a final gate close.
