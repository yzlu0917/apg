# Audit Final v0 API Summary

Date: 2026-03-31

Run id:

- `audit_final_v0_api`

Slice:

- `artifacts/audit/audit_final_v0.jsonl`

Controls:

- `artifacts/audit/audit_final_v0_matched_shuffle.jsonl`

Sample filter:

- `revise_only`

## Main numbers

- total rows: `24`
- total tokens: `9695`

Per condition:

- `direct`
  - count: `6`
  - action match rate: `0.833`
  - checker pass rate: `0.500`
- `procedure_retry`
  - count: `6`
  - action match rate: `0.833`
  - checker pass rate: `0.667`
- `gold_signal`
  - count: `6`
  - action match rate: `1.000`
  - checker pass rate: `0.667`
- `matched_shuffle`
  - count: `6`
  - action match rate: `1.000`
  - checker pass rate: `0.500`

## Key interpretation

- The final slice is harder than `audit_dev_v2`.
- The API baseline still shows a checker-level gap between `gold_signal` and
  `matched_shuffle`, but the gap is now modest (`0.667` versus `0.500`).
- The main blocker is not only procedure effect. Two held-out `plan` examples
  fail even under `gold_signal`.

## Important failure mode

The two `plan` failures are not obvious reasoning failures. The model outputs
semantically correct repaired schedules, but they do not match the frozen
canonical answer string closely enough for the current `constraint_check`
implementation.

Affected pairs:

- `plan_0_harder_1101`
  - model output under `gold_signal`: `A:0-2, B:2-3, C:3-6`
  - frozen expected answer: `Schedule: A [0,2], B [2,3], C [3,6]. Total time: 6.`
- `plan_1102_harder_1`
  - model output under `gold_signal`: `Install A, Install B, Install C, Install D; total time = 8 minutes`
  - frozen expected answer: `Sequence: A, B, C, D. Total time: 8 minutes.`

## Current conclusion

`Audit gate is still not closed on the frozen final slice.`

Reason:

- the final slice is now frozen and reproducible,
- but the final result is confounded by brittle plan canonicalization,
- so the current evidence supports a clean diagnostic claim, not a full Audit
  gate `GO`.
