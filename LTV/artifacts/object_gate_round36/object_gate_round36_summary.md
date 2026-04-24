# Round36: cross-model pairwise separability audit (Goedel)

## Goal

Test whether the narrower round35 object claim survives on a second prover family:

- same fixed-pre-state pairwise task,
- same low-complexity readouts,
- different frozen hidden states.

## Method

Reused [evaluate_cts_pairwise_separability.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_cts_pairwise_separability.py) without changing the task definition.

Model:

- [Goedel-Prover-V2-8B](/cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a)

Task remains:

- same theorem / same pre-state
- pair label `1 = semantic_flip`, `0 = same_semantics`
- pair representation `d = φ(source) - φ(variant)`

As in round35, the algebraic collapse still holds:

- `Δh(source) - Δh(variant) = h^+_source - h^+_variant`

So `post_*` and `transition_*` pairwise results are again identical.

## Main result

Round36 strengthens the round35 object claim.

Overall on Goedel:

- `post_linear_sep`
  - `AUROC = 0.9304`
  - `accuracy = 0.9310`
  - `brier = 0.0690`
  - `same_mean_prob = 0.1000`
  - `flip_mean_prob = 0.9643`
  - `same_flip_gap = 0.8643`
- `post_centroid_sep`
  - `AUROC = 0.8976`
  - `accuracy = 0.8103`
  - `brier = 0.1716`
  - `same_mean_prob = 0.1988`
  - `flip_mean_prob = 0.8110`
  - `same_flip_gap = 0.6122`

DeepSeek vs Goedel comparison:

- `linear_diff_probe`
  - DeepSeek: `AUROC = 0.8964`, `accuracy = 0.8793`
  - Goedel: `AUROC = 0.9304`, `accuracy = 0.9310`
- `centroid_diff_scorer`
  - DeepSeek: `AUROC = 0.9226`, `accuracy = 0.8103`
  - Goedel: `AUROC = 0.8976`, `accuracy = 0.8103`

So the clearest cross-model reading is:

- the object-level separability claim survives;
- the linear weak readout is actually stronger on Goedel;
- the centroid geometry baseline is not universally stronger, but still clearly above chance.

## Geometry reading

Goedel geometry:

- `centroid_gap = 0.4834`
- `fisher_ratio = 0.1481`
- `leave-one-out 1NN accuracy = 0.7241`

Compared with DeepSeek:

- stronger global class separation (`centroid_gap`, `fisher_ratio` up)
- weaker local nearest-neighbor consistency (`1NN acc` down)

So Goedel looks more linearly separable at the global level, even though its local neighborhood structure is less clean.

## Family reading

The linear readout again gives the cleanest picture.

Stable cross-model positives:

- same-side still near zero on
  - `reflexivity_style`
  - `projection_style`
  - `theorem_application_style`
- flip-side still near one on
  - `goal_mismatch_direct_use`
  - `wrong_branch`
  - `wrong_projection`
  - `wrong_target_term`

Goedel-specific strengthening:

- `wrong_composition: 0.875 -> 1.0`
- `wrong_theorem_reference: 0.5 -> 1.0`

Remaining weak same families persist:

- `eliminator_style = 0.5`
- `other_same_rewrite = 0.3333`

## Interpretation

Round36 makes the narrower object claim much stronger:

- hidden states do not just contain pairwise progress-difference information on one model family;
- the same low-complexity protocol also works on a second prover;
- and on Goedel the linear weak readout is even cleaner.

So the updated reading is:

- the object-level separability claim is now cross-model supported;
- this is stronger evidence than round34-style big-judge results for the question you actually care about;
- but it still stops short of a deployable verifier or a solved general method.
