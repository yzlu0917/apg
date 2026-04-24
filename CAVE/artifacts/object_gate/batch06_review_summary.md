# Batch 06 Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch06_code_plan_candidates.jsonl`

## Accepted

- `code_pair_0_501`
  - Clean loop-based code task with checker-backed local expression bug.
  - Sufficiently local for same-domain shuffle support.
- `code_pair_1`
  - Simple list-processing task with a local wrong-expression bug.
  - Repair remains compact but still usable and checker-backed.
- `plan_pair_1`
  - Explicit constraint violation with a plausible local repair suffix.
  - Suitable as the second accepted `plan` pair for same-domain shuffles.

## Rejected

- `plan_pair_0`
  - Rejected because the stated checker constraints do not actually require
    `mix dry` before `mix wet`, so the revise example is not a guaranteed
    violation under the written checker.

## Outcome

- Reviewed pairs: 4
- Accepted pairs: 3
- Rejected pairs: 1
- Acceptance rate: 75.0 percent

Interpretation:

This batch was not for a fresh gate decision. Its role was to add domain
coverage to the frozen panel. It succeeded in making same-domain shuffles
possible for all active domains.
