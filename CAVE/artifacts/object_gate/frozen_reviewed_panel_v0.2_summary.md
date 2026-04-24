# Frozen Reviewed Panel v0.2

Date: 2026-03-31

Panel file:

- `artifacts/object_gate/frozen_reviewed_panel_v0.2.jsonl`

Included pairs:

- `sym_0`
- `code_pair_0`
- `plan_pair_0_301`
- `sym_pair_0`

Source batches:

- `artifacts/object_gate/batch02_candidates.jsonl`
- `artifacts/object_gate/batch04_plan_candidates.jsonl`
- `artifacts/object_gate/batch05_sym_candidates.jsonl`

Why frozen:

- These pairs were generated after prompt tightening.
- They pass deterministic validation.
- They survive first-pass review for label clarity, locality, and repair
  plausibility.
- The frozen review set reaches the 80 percent acceptance threshold.

Scope warning:

- This is a bootstrap dev panel, not a final benchmark split.
- It is sufficient to start Audit-gate preparation.
