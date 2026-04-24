# Audit Baseline v2 Local Qwen3-8B Summary

Date: 2026-03-31

Run id:

- `audit_baseline_v2_local_qwen3_8b`

Slice:

- `artifacts/audit/audit_dev_v2.jsonl`

Controls:

- `artifacts/audit/audit_dev_v2_matched_shuffle.jsonl`

Sample filter:

- `revise_only`

Backend:

- local `Qwen3-8B`

## Main numbers

- total rows: `44`
- total tokens: `0` for local backend logging

Per condition:

- `direct`
  - count: `11`
  - action match rate: `0.727`
  - checker pass rate: `0.545`
- `procedure_retry`
  - count: `11`
  - action match rate: `0.727`
  - checker pass rate: `0.727`
- `gold_signal`
  - count: `11`
  - action match rate: `1.000`
  - checker pass rate: `1.000`
- `matched_shuffle`
  - count: `11`
  - action match rate: `1.000`
  - checker pass rate: `0.545`

## Comparison to API v2

- API v2 `gold_signal` checker pass: `1.000`
- local Qwen3-8B `gold_signal` checker pass: `1.000`
- API v2 `matched_shuffle` checker pass: `0.727`
- local Qwen3-8B `matched_shuffle` checker pass: `0.545`

Interpretation:

- the content-sensitive checker gap survives across backends on the same dev
  slice
- local Qwen3-8B is much weaker in `direct` and only moderately better under
  `procedure_retry`
- unlike the API run, the local model almost always chooses `revise` under
  `matched_shuffle`, so the informative signal is in checker outcome rather than
  action choice

## Key failures under matched shuffle

- `sym_0`
  - revised to `7` instead of `15`
- `plan_pair_0_301`
  - preserved the wrong wet-before-dry order
- `sym_601_harder`
  - revised to `15` instead of `7`
- `sym_harder_602_1`
  - revised to `15` instead of `189`
- `plan_pair_1_harder_602`
  - produced a finite linear schedule instead of `infinite`

## Current conclusion

This is a useful cross-backend replication on the dev slice, not a final Audit
gate close. The final blocker remains the absence of a frozen held-out audit
slice.
