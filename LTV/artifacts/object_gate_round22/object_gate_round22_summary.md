# Round22 Mechanism Audit Summary

## Scope

This round does **not** introduce a new recipe. It audits the mechanism of the round20 gain by comparing:

- round18 contrastive baseline
- round20 hard-negative contrastive

for both:

- `post-state`
- `transition`

The goal is to answer: **what did hard negatives actually change?**

## Inputs

- before eval:
  - `artifacts/object_gate_round18/cts_contrastive_eval.json`
- after eval:
  - `artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json`
- annotated CTS panel:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`

Derived audit artifacts:

- `artifacts/object_gate_round22/transition_mechanism_delta.json`
- `artifacts/object_gate_round22/post_mechanism_delta.json`

## Main Result

Hard negatives are **not** acting as a generic score booster.

They produce two different mechanisms:

- for `transition`, the gain is driven mainly by **same-side cleanup** plus selective flip gains
- for `post-state`, the gain is driven mainly by **broad flip-margin amplification** with a mild same-side cost

So round20 should be read as a **mechanism split**, not just a better hyperparameter setting.

## Transition Mechanism

Overall:

- same gap: `0.0648 -> 0.0147`
- mean same improvement: `+0.0501`
- improved same pairs: `27 / 30`
- flip margin: `0.4199 -> 0.4829`
- mean flip improvement: `+0.0630`
- improved flip pairs: `19 / 28`

Same-family cleanup is the dominant effect:

- `eliminator_style`: `0.2887 -> 0.0506`
- `other_same_rewrite`: `0.1650 -> 0.0327`
- `theorem_application_style`: `0.0961 -> 0.0423`
- `reflexivity_style`: `0.0079 -> 0.0006`
- `projection_style`: `0.0035 -> 0.0008`

Flip-side gains are real but selective:

- `wrong_branch`: `0.6113 -> 0.7498`
- `goal_mismatch_direct_use`: `0.6126 -> 0.7465`
- `wrong_target_term`: `0.3789 -> 0.5017`
- `wrong_projection`: `0.4550 -> 0.5276`
- `wrong_theorem_reference`: `0.3175 -> 0.3676`

The weakest flip mechanism remains `wrong_composition`:

- `0.4582 -> 0.4631`

This is a net positive change, but only barely, and pair-level outcomes are mixed.

## Post-State Mechanism

Overall:

- same gap: `0.0657 -> 0.0748`
- mean same improvement: `-0.0090`
- improved same pairs: `21 / 30`
- flip margin: `0.4480 -> 0.5500`
- mean flip improvement: `+0.1020`
- improved flip pairs: `21 / 28`

This is a different mechanism from `transition`.

The dominant effect is broad flip amplification:

- `wrong_target_term`: `0.4391 -> 0.5931`
- `wrong_projection`: `0.5843 -> 0.7160`
- `goal_mismatch_direct_use`: `0.6062 -> 0.7351`
- `wrong_theorem_reference`: `0.2936 -> 0.4054`
- `ill_typed_or_malformed`: `0.5858 -> 0.6917`
- `wrong_branch`: `0.6534 -> 0.7488`

But this comes with same-side regressions in a few important slices:

- `theorem_application_style`: `0.0815 -> 0.1907`
- `eliminator_style`: `0.2948 -> 0.3267`
- `symmetry_style`: `0.0191 -> 0.0397`

So round20 makes `post-state` more aggressive on flip separation, but not cleaner overall.

## Pair-Level Readout

Representative `transition` same-pair improvements:

- `cts_same_false_elim_api_2`: `0.5773 -> 0.0975`
- `cts_round6_same_false_of_imp_false_1`: `0.5886 -> 0.1461`
- `cts_same_zero_add_left_api_1`: `0.2653 -> 0.1256`

Representative `transition` flip improvements:

- `lean_mul_zero_right_pos__...2798d541`: `0.4791 -> 0.7487`
- `lean_eq_refl_pos__...79e2da93`: `0.4943 -> 0.7460`
- `cts_flip_eq_comm_api_1`: `0.4831 -> 0.7022`

Representative `transition` flip failures that remain:

- `cts_round5_flip_double_neg_1`: `0.4587 -> 0.0359`
- `cts_flip_add_zero_1`: `0.4296 -> 0.0279`
- `cts_round5_flip_imp_trans_1`: `0.3475 -> 0.0164`

These failures are consistent with the family-level reading that `wrong_composition` is still unstable.

## Interpretation

The strongest current interpretation is:

1. round20 works because hard negatives reshape the representation geometry, not because of a generic optimization tweak
2. `transition` and `post-state` benefit through different mechanisms
3. the main unresolved mechanism question is no longer "does hard-negative training help?"
4. it is now "which flip families are actually being separated, and why does `wrong_composition` remain unstable for `transition`?"

## Gate Read

- `Object gate`: still partially supported
- `Audit gate`: stronger than before, because round20 now has a mechanism-level explanation
- `Conversion gate`: still untouched

This round strengthens the project as a **measurement + mechanism** line even without claiming a final best verifier.

## Next Step

If continuing the mechanism line, the highest-value next moves are:

1. family-targeted hard negatives for `wrong_composition`
2. transfer the round20 recipe to a second prover and check whether the same mechanism split appears
3. inspect representation geometry directly instead of only scalar `IG / SS`
