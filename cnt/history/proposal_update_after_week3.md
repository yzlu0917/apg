# Proposal Update After Week 3

## Executive Summary

The current project state is:

- Week 1: completed and positive
- Week 2: completed and positive
- Week 3: completed as a clean negative / partial-result branch
- Week 4–6: not yet completed

This is still aligned with the proposal. The object-level program has succeeded so far: trajectory-conditional necessity is identifiable on synthetic data and survives larger-pool audited math Stage A. What has not succeeded yet is the current offline Stage B training family: across multiple structurally different recipes, CNT does not yet deliver a stable rollout win over matched SFT-only control.

So the accepted reading should be:

> object success, training non-win

not:

> almost-there training win

## Status Against The Proposal

### Week 1

Proposal target:

- synthetic ground-truth benchmark
- edit / continue / verify pipeline
- deletion-paraphrase asymmetry
- decoy / filler / redundancy suite

Current status:

- completed
- positive

Accepted reading:

- the synthetic object-validity gate works
- necessity recovery clearly beats observational / entropy-style baselines
- the object is not reducible to detectability or generic continuation quality

### Week 2

Proposal target:

- `CounterTrace-mini(math)`
- cross-editor audit
- held-out continuator audit
- small-model real-domain pilot

Current status:

- completed
- positive

Current main evidence:

- larger-pool conservative exit:
  - [audit08 summary](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_summary.json)
- key fact:
  - `230 / 298` candidate-step pairs survive the final joint audit

Accepted reading:

- the object survives real-domain auditing at larger scale
- the current uncertainty is no longer whether `N_t` exists
- the main remaining Week 2 failure family is held-out swap repair, not paraphrase drift

### Week 3

Proposal target:

- main offline training comparison
- matched control
- equal-label-budget style comparison

Current status:

- completed in the sense that the current family has been tested and written up
- not a positive win

Current accepted branch:

- [week3_negative_branch.md](/cephfs/luyanzhen/apg/cnt/history/week3_negative_branch.md)

Accepted reading:

- several structurally different offline training families move offline margins
- none yet deliver a stable CNT-over-control rollout gain
- therefore Week 3 currently belongs on a clean negative / partial-result branch

Strongest recent dev-pool evidence:

- [signal10](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold_compare_summary.json): exact tie
- [signal11](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold_compare_summary.json): sparse frontier
- [signal12](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold_compare_summary.json): exact tie
- [signal13](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold_compare_summary.json): exact tie
- [signal14](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold_compare_summary.json): one-fold frontier, not broad win

The current Week 3 evaluation discipline is:

- keep the strict frozen final-test gate fixed:
  - [strict gate manifest](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/strict_gate_manifest.json)
- use the complementary dev pool for recipe selection
- do not silently widen the final-test gate just to cross `30+`

### Week 4

Proposal target:

- systematic ablations
- `N / S` split and optional `H`
- length matching
- same vs external continuator
- rollout-`K` sweep

Current status:

- not completed

Why not:

- the proposal-quality prerequisite for Week 4 is a meaningful Week 3 signal that can then be stress-tested
- right now the project does not have a stable positive Stage B recipe to carry into these ablations
- some partial ablation-like evidence exists, but it does not satisfy the Week 4 success condition

### Week 5

Proposal target:

- equal-token frontier
- equal-token rerank baseline
- recoverable vs irrecoverable
- second domain

Current status:

- not completed

Why not:

- these are downstream claims that depend on a stronger Week 3 training story
- the current project state does not justify promoting utility/frontier claims yet

### Week 6

Proposal target:

- optional lightweight RL refinement only if earlier signals are strong
- failure boundaries and significance
- lock paper narrative

Current status:

- partially touched, not completed

What is already true:

- the project has now locked an honest narrative for Week 3
- the repo already contains a reusable negative/partial write-up branch

What is not yet done:

- no RL refinement
- no full significance package
- no complete final paper assembly

## Supported Claims

The current evidence supports the following claims:

1. A trajectory-conditional necessity object can be identified on synthetic data.
2. The same object survives larger-pool real-domain math auditing.
3. The project now has a conservative, reproducible Week 2 exit for GSM8K math.
4. The current offline Stage B families do not yet stably convert that object signal into rollout utility gains over matched SFT-only control.

## Unsupported Claims

The current evidence does **not** support the following claims:

1. CNT offline training already beats matched SFT-only control in a robust way.
2. Week 3 has produced a stable equal-budget utility gain.
3. Week 4 ablations preserve a positive training advantage.
4. Equal-token frontier gains are established.
5. Second-domain transfer is established.
6. RL refinement is warranted.

## Recommended Next Step

The default next step should be writing, not more routine experimentation.

Recommended order:

1. Treat Week 1–2 as the positive core of the project.
2. Treat Week 3 as a clean negative / partial-result branch.
3. Update the proposal / paper narrative accordingly:
   - object identified
   - benchmark and audit protocol established
   - offline utility conversion still unresolved
4. Only reopen Week 3 if a genuinely more radical Stage B family is justified.

## Reopen Criteria

Week 3 should only be reopened if both conditions hold:

1. The new family is structurally different from `signal10-14`, not another nearby knob.
2. It first shows a real gain on the hygienic dev pool, then survives revalidation on the frozen strict final-test gate.

Until then, the stable project reading should remain:

> Week 1–2 succeeded; Week 3 is currently a clean negative / partial result; Week 4–6 remain open rather than completed.
