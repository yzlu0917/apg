# Structured Locality Audit Bootstrap Summary

Date: 2026-04-01

Frozen dev slice:

- `artifacts/audit/audit_dev_v3.jsonl`

Generated assets:

- `artifacts/audit/audit_dev_v3_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v3_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v3_artifact_report.md`
- `artifacts/audit/audit_dev_v3_artifact_report.json`
- `artifacts/audit/audit_baseline_v3_local_qwen3_8b_summary.md`

Status:

- Audit gate protocol: `baseline-ready`
- Audit empirical signal on dev slice: `observed`
- Audit branch status: `entry GO, not full pass`

Implication:

- the clean `structured_locality` branch is strong enough to support an Audit
  dev slice
- the first local baseline shows `gold_signal > matched_shuffle`
- but the current shuffle penalty is concentrated in structured-plan, so the
  control builder still needs tightening before any final-slice claim
