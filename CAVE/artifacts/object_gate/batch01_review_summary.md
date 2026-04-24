# Batch 01 Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch01_candidates.jsonl`

## Accepted

- `sym_0_31`
  - Clear local arithmetic error in the revise example.
  - Repair suffix updates the incorrect step and final answer coherently.
- `code_pair_1_seed_32`
  - Expression-level logic bug is local and checker-backed.
  - Repair is a concrete operator correction, not just an abstract note.
- `plan_pair_0`
  - Local order violation is well specified and the correction is plausible.
  - Pair still tests local revision rather than complete regeneration.
- `plan_pair_1_seed_32`
  - Constraint violation is local and recoverable by a small swap.
  - Repair suffix is concrete enough for suffix-style correction.

## Rejected

- `sym_1_32`
  - Rejected because the repair suffix is underspecified (`should be 44.`) and
    does not cleanly represent a localized correction.
- `code_pair_0`
  - Rejected because the fail span is only the token `b` and the repair suffix
    `**2` is too fragmentary for robust localization.

## Outcome

- Reviewed pairs: 6
- Accepted pairs: 4
- Rejected pairs: 2
- Acceptance rate: 66.7 percent

Interpretation:

The hybrid generation pipeline is viable, but the prompt still allows
under-specified repair fields. Another small batch should be generated after
tightening repair and fail-span instructions.
