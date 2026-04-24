# Audit Final v1 Change Note

Date: 2026-03-31

Base:

- `artifacts/audit/audit_final_v0.jsonl`

New version:

- `artifacts/audit/audit_final_v1.jsonl`

## What changed

Only the two `plan` pairs were updated, and only in `checker` metadata.

- `plan_0_harder_1101`
  - moved from string-equality-like `constraint_check` to structured
    `scheduled_ranges`
- `plan_1102_harder_1`
  - moved from string-equality-like `constraint_check` to structured
    `ordered_sequence_total`

No `sym` or `code` pair changed.
No question, trace, fail span, repair suffix, or expected answer text changed.

## Why v0 and v1 are not directly comparable

- `audit_final_v0` is a frozen diagnostic result that exposed brittle plan
  canonicalization.
- `audit_final_v1` changes the plan checker semantics to better capture valid
  repaired outputs.
- Therefore `v0` and `v1` are comparable as a diagnosis-to-repair sequence, not
  as one unchanged metric series.

## Intended interpretation

- `v0` answers: did frozen final-slice string canonicalization create a false
  blocker?
- `v1` answers: once that blocker is reduced, does the final slice still show a
  meaningful `gold_signal` versus `matched_shuffle` gap?
