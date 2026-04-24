# Audit Bootstrap Summary

Date: 2026-03-31

Frozen dev slice:

- `artifacts/audit/audit_dev_v2.jsonl`

Generated assets:

- `artifacts/audit/audit_dev_v2_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v2_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v2_artifact_report.md`
- `artifacts/audit/audit_dev_v2_artifact_report.json`
- `artifacts/audit/audit_baseline_v2_api_summary.md`
- `artifacts/audit/audit_baseline_v2_local_qwen3_8b_summary.md`
- `artifacts/audit/audit_final_v0_api_summary.md`
- `artifacts/audit/audit_final_v1_api_summary.md`

Status:

- Audit gate protocol: `baseline-ready`
- Audit gate empirical signal: `stronger on dev slice`
- Audit gate backend replication: `observed on dev slice`
- Audit final slice: `frozen and first-run executed`
- Audit final slice v1: `checker confound reduced, no clear final shuffle gap`

Implication:

- The audit protocol is reproducible and frozen enough to guide the next step.
- Panel coverage and held-out freezing are no longer the main blocker.
- The main blocker is no longer final-slice coverage or checker brittleness.
- The repaired final slice still does not show a strong `gold_signal` versus
  `matched_shuffle` separation.
- The next step should be a branch decision, not more silent metric repair.
