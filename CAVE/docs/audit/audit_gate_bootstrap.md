# Audit Gate Bootstrap

Date: 2026-03-31

## Objective

The Audit gate asks whether the object-level signal can survive basic controls
against artifact, leakage, and shallow shortcut explanations.

At this stage, the project is not testing method superiority. It is freezing
the audit protocol that later baselines must respect.

## Audit gate acceptance rule

Audit gate entry is allowed only if:

- the Object gate has a frozen reviewed panel,
- a dev slice is explicitly frozen,
- at least one matched shuffle control asset exists,
- at least one artifact probe report exists,
- the team has a logging contract for future baseline runs.

Audit gate `GO` will later require:

- matched shuffle controls that meaningfully damage content-sensitive behavior,
- no dominant formatting or metadata shortcut,
- no moving evaluation boundary after method runs start.

## Bootstrap assets

- Frozen dev slice:
  `artifacts/audit/audit_dev_v2.jsonl`
- Matched shuffle controls:
  `artifacts/audit/audit_dev_v2_matched_shuffle.jsonl`
- Control summary:
  `artifacts/audit/audit_dev_v2_matched_shuffle_summary.json`
- Artifact report:
  `artifacts/audit/audit_dev_v2_artifact_report.md`
- Logging contract:
  `docs/audit/audit_logging_contract.md`
- Final-slice contract:
  `docs/audit/audit_final_slice_contract.md`
- API baseline summary:
  `artifacts/audit/audit_baseline_v2_api_summary.md`
- Local backend replication summary:
  `artifacts/audit/audit_baseline_v2_local_qwen3_8b_summary.md`
- Final-slice API summary:
  `artifacts/audit/audit_final_v0_api_summary.md`
- Final-slice v1 API summary:
  `artifacts/audit/audit_final_v1_api_summary.md`

## Current interpretation

This step only proves that the audit protocol is defined and reproducible. It
does not yet prove that any baseline or method is robust under the controls.

## Current status

- `Audit gate protocol: baseline-ready`
- `Audit gate empirical signal: strengthened on dev slice`
- `Audit gate dev-slice replication: observed across API and local backend`
- `Audit final slice: frozen and first-run completed`
- `Audit final slice v1: checker confound reduced, no clear shuffle gap`

Reason:

- the dev slice is frozen,
- control and artifact assets exist,
- logging contract is defined,
- all active domains now support same-domain matched shuffles.
- on `audit_dev_v2`, `gold_signal` reaches `1.000` checker pass while
  `matched_shuffle` drops to `0.727`.
- on the same slice, local `Qwen3-8B` also keeps `gold_signal=1.000` checker
  pass while `matched_shuffle` drops further to `0.545`.
- on `audit_final_v0`, API `gold_signal` drops to `0.667` checker pass and
  `matched_shuffle` drops to `0.500`.
- on `audit_final_v1`, API `gold_signal` and `matched_shuffle` both land at
  `0.833`, while `procedure_retry` reaches `1.000`.

Remaining gap:

- after reducing the plan-checker confound, final-slice content effect is still
  weak,
- `procedure_retry` dominates on the repaired final slice,
- this is now evidence against an easy Audit-gate `GO`, not just evidence of a
  bad checker.

Immediate next action:

- decide whether to stop Audit as a clean negative/partial-result branch,
- or open a genuinely different object family rather than continuing local
  checker tuning.
