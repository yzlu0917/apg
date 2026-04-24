# Frozen Reviewed Panel v0.3

Date: 2026-03-31

Panel file:

- `artifacts/object_gate/frozen_reviewed_panel_v0.3.jsonl`

Included pairs:

- `sym_0`
- `sym_pair_0`
- `code_pair_0`
- `code_pair_0_501`
- `code_pair_1`
- `plan_pair_0_301`
- `plan_pair_1`

Purpose:

- extend the bootstrap frozen panel so each active domain supports same-domain
  matched shuffle controls.

Status:

- validator: passed
- pairs: 7
- domains: `sym`, `code`, `plan`

Residual risk:

- `code_pair_0_501` has a compact repair suffix and remains a mild artifact risk
  to monitor, but not enough to block Audit-gate preparation.
