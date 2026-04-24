# Brief Proposal Update

## Status

Current accepted status:

- Week 1: completed and positive
- Week 2: completed and positive
- Week 3: completed as a clean negative / partial-result branch
- Week 4–6: not yet completed

The project is still aligned with the proposal. What has succeeded is the object-level program. What has not succeeded yet is the current offline training program.

## What Is Established

The following claims are now supported:

1. A trajectory-conditional necessity object can be identified on synthetic data.
2. The same object survives larger-pool audited math Stage A.
3. The current larger-pool GSM8K Week 2 exit is strong enough to support an object-level claim:
   - [audit08 summary](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_summary.json)
   - `230 / 298` candidate-step pairs survive the final joint audit.
4. The present Stage B families do not yet produce a stable CNT-over-control rollout gain.

## What Is Not Established

The following claims are not supported by current evidence:

1. CNT offline training already beats matched SFT-only control in a robust way.
2. The proposal's Week 3 utility goal has already been achieved.
3. Week 4 ablations preserve a positive training advantage.
4. Equal-token frontier or second-domain claims are ready.
5. RL refinement is currently justified.

## Accepted Reading

The stable reading should now be:

> Week 1–2 succeeded. Week 3 is currently a clean negative / partial result.

More explicitly:

- the object stands
- the auditing protocol stands
- the current offline training family does not yet convert that object signal into a stable rollout utility gain

The current Week 3 negative branch is documented in:

- [week3_negative_branch.md](/cephfs/luyanzhen/apg/cnt/history/week3_negative_branch.md)

The strongest recent dev-side evidence is:

- [signal10](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold_compare_summary.json): exact tie
- [signal11](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold_compare_summary.json): sparse frontier
- [signal12](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold_compare_summary.json): exact tie
- [signal13](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold_compare_summary.json): exact tie
- [signal14](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold_compare_summary.json): new-family partial-negative

## Recommended Next Step

The default next step should be writing, not routine continuation of Week 3 sweeps.

Recommended order:

1. Use Week 1–2 as the positive core claim.
2. Treat Week 3 as a clean negative / partial-result branch.
3. Update the proposal / paper narrative accordingly:
   - object identified
   - benchmark and audit protocol established
   - offline utility conversion unresolved
4. Reopen Week 3 only if a genuinely more radical Stage B family is justified.

## Reopen Rule

Week 3 should only be reopened if:

1. the new family is structurally different from `signal10-14`
2. it first wins on the hygienic dev pool
3. it then survives revalidation on the frozen final-test gate:
   - [strict gate manifest](/cephfs/luyanzhen/apg/cnt/outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/strict_gate_manifest.json)
