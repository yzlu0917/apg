# Week 3 Clean Negative / Partial-Result Branch

## Status

Current reading:

- Week 1 and Week 2 are positive.
- Week 3 is not a win.
- The right narrative is now `object success, training non-win`, not `almost-there training win`.

This branch is the accepted write-up for the current Stage B state unless a later recipe clearly beats matched SFT-only control on the dev pool and then revalidates on the frozen strict `29`-example gate.

The current default project decision is to keep this branch accepted and move into writing closure rather than routine Stage B continuation.

## What Holds

The object-level story is positive.

- Synthetic CounterTrace works as an object-validity gate.
- Real-domain math Stage A scales to the larger GSM8K pool.
- The current larger-pool conservative Week 2 exit is:
  - [audit08 summary](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_summary.json)
- Key Week 2 fact:
  - `230 / 298` candidates survive the final joint audit.

So the object is not surviving only because of tiny-sample luck. The current uncertainty is not “does `N_t` exist,” but “can the current offline training setup convert that object signal into non-harmful utility gain.”

## What Does Not Hold

The current Stage B family has not produced a robust CNT-over-control win.

The accepted dev-pool evidence is:

- [signal10](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold_compare_summary.json): exact tie
- [signal11](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold_compare_summary.json): sparse frontier
- [signal12](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold_compare_summary.json): exact tie
- [signal13](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold_compare_summary.json): exact tie
- [signal14](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold_compare_summary.json): one-fold frontier, not broad win

The most recent and strongest negative/partial result is `signal14`, because it changes objective family rather than only moving knobs inside the old one.

Its aggregate dev-pool readout is:

- `mean_delta_drop_solve = -0.0060`
- `mean_delta_n_t = -0.0040`
- `mean_delta_n_t_weighted = +0.0057`
- `nonzero_delta_folds = [2]`

Interpretation:

- three folds are exact rollout ties
- one fold recreates the familiar `utility - / weighted N_t +` frontier
- offline margins move, but rollout still does not yield a broad CNT-over-control gain

That is a clean partial-negative result, not a noisy almost-win.

## Current Decision Rule

Stage B should now be read with a two-stage verdict:

1. Utility / no-harm first
   - `mean_original_solve(cnt) >= mean_original_solve(control)`
   - `mean_drop_solve(cnt) >= mean_drop_solve(control)`
2. Object-preservation second
   - inspect `mean_n_t_weighted`
   - inspect paraphrase / equiv stability

Under that rule, the current Stage B family does not pass.

## Accepted Interpretation

The current proposal-compatible interpretation is:

- `Week 1–2`: success
- `Week 3`: clean negative / partial-result branch

More explicitly:

- trajectory-conditional necessity is identifiable and survives larger-pool math auditing
- but the present offline pair-training families do not yet stably outperform matched SFT-only control on rollout utility
- therefore the current paper-quality claim should be:
  - `object identified`
  - `faithful supervision protocol established`
  - `offline utility conversion remains unresolved`

## What Reopens Week 3

Week 3 should only be reopened for a new family if both conditions are met:

1. It is structurally different from `signal10-14`, not another nearby pairwise knob.
2. It first passes the hygienic `81`-example dev pool, then revalidates on the frozen strict gate:
   - [strict gate manifest](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/strict_gate_manifest.json)

Until then, the stable project reading should stay on this negative/partial branch.

## Reuse

For longer-form writing, the concise one-sentence project status is:

> Week 1–2 succeeded: the object stands on synthetic and larger-pool math Stage A. Week 3 is currently a clean negative/partial result: several structurally different offline training families move offline margins, but none yet deliver a stable CNT-over-control rollout gain.
