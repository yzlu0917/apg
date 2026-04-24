# Audit Logging Contract

Date: 2026-03-31

Any baseline or method run that touches the Audit gate must log the following
for every evaluated sample:

- `run_id`
- `slice_id`
- `pair_id`
- `domain`
- `condition`
  - one of `direct`, `procedure_retry`, `matched_shuffle`, `gold_signal`
- `model_or_system`
- `input_question`
- `initial_trace`
- `verifier_signal_used`
  - fail span, repair suffix, or equivalent verifier content
- `action_taken`
  - `keep`, `revise`, `abstain`
- `final_output`
- `checker_outcome`
- `token_cost`
- `notes`

## Frozen slices

- old mixed-family dev slice:
  `artifacts/audit/audit_dev_v2.jsonl`
- structured-locality dev slice:
  `artifacts/audit/audit_dev_v3.jsonl`
- current final slice for the old mixed-family branch:
  `artifacts/audit/audit_final_v1.jsonl`

## Rule

No method comparison should start until all evaluated systems can emit this log
shape. If a system cannot produce the required fields, it is not Audit-ready.
