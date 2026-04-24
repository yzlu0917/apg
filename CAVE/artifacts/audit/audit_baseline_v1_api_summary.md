# Audit Baseline v1 API Summary

Date: 2026-03-31

Run id:

- `audit_baseline_v1_api`

Slice:

- `artifacts/audit/audit_dev_v1.jsonl`

Conditions:

- `direct`
- `procedure_retry`
- `gold_signal`
- `matched_shuffle`

Sample filter:

- `revise_only`

## Main numbers

- total rows: 28
- total tokens: 10452

Per condition:

- `direct`
  - count: 7
  - action match rate: 0.857
  - checker pass rate: 1.000
- `procedure_retry`
  - count: 7
  - action match rate: 0.857
  - checker pass rate: 1.000
- `gold_signal`
  - count: 7
  - action match rate: 1.000
  - checker pass rate: 1.000
- `matched_shuffle`
  - count: 7
  - action match rate: 0.857
  - checker pass rate: 0.857

## Interpretation

- `gold_signal` outperforms `matched_shuffle`, so there is at least one clear
  content-sensitive failure under shuffle.
- But the gap is small in this first pass.
- `procedure_retry` already matches `direct` on checker success and both are
  very strong, which is consistent with the proposal risk that procedure effect
  is large.

## Critical example

- `plan_pair_0_301`
  - `gold_signal`: revise + pass
  - `matched_shuffle`: keep + fail

This is the cleanest evidence in the current run that shuffled verifier content
can break behavior on at least one sample.

## Current conclusion

The first empirical audit pass is informative but not yet strong enough to say
that verifier-content effect is robustly separated from procedure effect.
