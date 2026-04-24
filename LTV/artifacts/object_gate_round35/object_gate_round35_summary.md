# Round35: pairwise separability audit

## Goal

Return to the narrower object question:

- not whether we can train a stronger verifier,
- but whether frozen hidden states contain low-complexity information about whether a pair has a real progress difference.

The round35 task is therefore:

- same theorem,
- same pre-state,
- compare `source` vs `variant`,
- predict whether this pair is `same_semantics` or `semantic_flip`.

## Method

Implemented [evaluate_cts_pairwise_separability.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_cts_pairwise_separability.py).

For each CTS pair, define the pair representation:

- `d = φ(source) - φ(variant)`

Then evaluate two low-complexity readouts:

- `linear_diff_probe`: linear classifier on `d`
- `centroid_diff_scorer`: nearest-centroid distance score on `d`

This is intentionally weaker than round20/32/34. The goal is separability, not a full verifier.

## Important algebraic note

In this pairwise setup, `source` and `variant` share the same pre-state `h^-`.
So:

- `Δh(source) = h^+_source - h^-`
- `Δh(variant) = h^+_variant - h^-`

Therefore:

- `Δh(source) - Δh(variant) = h^+_source - h^+_variant`

So the pair-difference task collapses `post-state` and `transition` into the same comparison object.
That is why round35 reports identical pairwise results for `post` and `transition`.
This is not a bug; it is the correct algebra of the fixed-pre-state comparison task.

## Main result

Round35 gives a clear positive object-level answer:

- yes, frozen hidden states do contain low-complexity separable information about whether a pair has a real progress difference.

Overall:

- `post_linear_sep`
  - `AUROC = 0.8964`
  - `accuracy = 0.8793`
  - `same_mean_prob = 0.0667`
  - `flip_mean_prob = 0.8214`
  - `same_flip_gap = 0.7548`
- `post_centroid_sep`
  - `AUROC = 0.9226`
  - `accuracy = 0.8103`
  - `same_mean_prob = 0.0655`
  - `flip_mean_prob = 0.6621`
  - `same_flip_gap = 0.5966`

Because of the algebraic collapse above, the `transition_*` results are identical.

The geometry metrics also support nontrivial separability:

- `centroid_gap = 0.4023`
- `fisher_ratio = 0.0940`
- `leave-one-out 1NN accuracy = 0.8448`

So the right reading is:

- the signal is not only present,
- it is accessible to weak readouts,
- and it does not require the heavier judge-style heads to be detectable.

## Family reading

The best simple picture is from `linear_diff_probe`:

- same families are mostly very low-probability:
  - `reflexivity_style = 0.0`
  - `projection_style = 0.0`
  - `theorem_application_style = 0.0`
- concentrated weak same families remain:
  - `eliminator_style = 0.5`
  - `other_same_rewrite = 0.1667`

flip families are mostly high-probability:

- `goal_mismatch_direct_use = 1.0`
- `wrong_branch = 1.0`
- `wrong_projection = 1.0`
- `wrong_target_term = 1.0`
- `wrong_composition = 0.875`

but a few remain weak even under this simplified pairwise readout:

- `ill_typed_or_malformed = 0.5`
- `wrong_theorem_reference = 0.5`

## Interpretation

Round35 answers the narrower question more directly than round34:

- if the question is whether hidden states contain progress-difference information, the answer is yes;
- and the answer is strong enough under low-complexity pairwise readouts that the object claim is now much cleaner than the earlier big-judge formulations.

But round35 does **not** yet say:

- that we have a deployable verifier,
- or that a full general method has been solved.

It only says something narrower and more important for object-gate work:

- frozen hidden states already support weak-readout separability of pairwise progress differences.
