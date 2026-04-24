# Structured Locality Audit Bootstrap

Date: 2026-04-01

## Objective

Test whether the clean `structured_locality` object branch survives the first
Audit bootstrap controls on a frozen dev slice.

This stage is still not a method-comparison claim. It is asking whether the
new exact structured object shows content sensitivity beyond a pure retry
effect.

## Bootstrap assets

- Frozen dev slice:
  `artifacts/audit/audit_dev_v3.jsonl`
- Matched shuffle controls:
  `artifacts/audit/audit_dev_v3_matched_shuffle.jsonl`
- Control summary:
  `artifacts/audit/audit_dev_v3_matched_shuffle_summary.json`
- Artifact report:
  `artifacts/audit/audit_dev_v3_artifact_report.md`
- Logging contract:
  `docs/audit/audit_logging_contract.md`
- Dev slice contract:
  `docs/audit/structured_locality_audit_dev_slice_contract.md`
- Local baseline summary:
  `artifacts/audit/audit_baseline_v3_local_qwen3_8b_summary.md`

## Current status

- `Audit gate protocol: baseline-ready`
- `Audit empirical signal on dev slice: observed`
- `Audit branch status: not yet passed`

Reason:

- the new branch has a frozen dev slice, matched shuffle controls, and an
  artifact report
- all 16 matched shuffle controls are same-domain
- the artifact report shows no dominant formatting or tiny-span risk
- on local `Qwen3-8B`, `gold_signal` reaches `1.000` checker pass while
  `matched_shuffle` drops to `0.750`

## Main caveat

The observed shuffle penalty is concentrated in `plan`, not `code`.

On `audit_dev_v3`, the current matched-shuffle builder reuses one plan repair
hint (`A -> B -> C -> D`) across several target plan pairs, which creates a
clean dev-slice content effect but may also overstate the plan-side penalty if
left unrefined.

So the current reading is:

- the branch is strong enough to enter empirical Audit
- there is real dev-slice content sensitivity
- but the controls should be tightened before any final-slice claim
