# Round24 Goedel Cross-Model Hard-Negative Check

## Scope

This round transfers the round20 hard-negative contrastive recipe to a second prover:

- source model in round20:
  - `DeepSeek-Prover-V2-7B`
- second prover in round24:
  - `Goedel-Prover-V2-8B`

The goal is not to claim a new best method. It is to check whether the main mechanism split from round20 is model-specific or reproducible across prover families.

## Protocol

Evaluator:

- `scripts/evaluate_cts_hardneg_contrastive.py`

Data:

- `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- annotated panel:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`

Model:

- `/cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a`

Outputs:

- `artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json`
- `artifacts/object_gate_round24/cts_hardneg_contrastive_audit.json`
- `artifacts/object_gate_round24/transition_cross_model_delta.json`
- `artifacts/object_gate_round24/post_cross_model_delta.json`

## Important Note

To keep runtime tractable, this round uses:

- `epochs = 200`

instead of the original round20 default of `400`.

So this is best read as a **near-protocol-matched cross-model diagnostic**, not a strict apples-to-apples leaderboard replacement for round20.

## Main Result

The round20 mechanism split **partially replicates** on Goedel.

The core pattern still holds:

- `transition` is the cleaner same-side representation
- `post-state` remains stronger on some key flip families, especially `wrong_composition`

But the exact family balance shifts across models.

## Overall Metrics

Goedel round24:

- `goedelhardneg_post_contrastive`
  - `IG = 0.0474`
  - `SS = 0.6311`
- `goedelhardneg_transition_contrastive`
  - `IG = 0.0103`
  - `SS = 0.6101`

Compared with DeepSeek round20:

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

So on this near-matched run:

- both Goedel readouts have stronger overall `SS`
- `transition` still keeps much lower `IG` than `post-state`

## Same-Side Read

Goedel still supports the same main qualitative reading:

- `transition` is cleaner on most same families

Examples:

- `other_same_rewrite`
  - `post = 0.1144`
  - `transition = 0.0045`
- `eliminator_style`
  - `post = 0.3188`
  - `transition = 0.1268`
- `projection_style`
  - `post = 0.0036`
  - `transition = 0.0019`
- `reflexivity_style`
  - `post = 0.0019`
  - `transition = 0.0010`

The only notable same-family exception is:

- `theorem_application_style`
  - `post = 0.0015`
  - `transition = 0.0020`

This is still much narrower than the post/transition gap on DeepSeek.

## Flip-Side Read

The flip split also persists, but with a shifted balance.

On Goedel:

- `post-state` is stronger on:
  - `wrong_theorem_reference`
  - `wrong_composition`
  - `wrong_target_term`
  - `goal_mismatch_direct_use`
- `transition` is stronger on:
  - `wrong_projection`
  - `wrong_branch`
  - `ill_typed_or_malformed`

The most important carry-over from DeepSeek is:

- `wrong_composition` is still **not** a `transition` win
  - `post = 0.5252`
  - `transition = 0.4509`

So the hardest unresolved family remains unresolved across both prover families.

## Cross-Model Delta

Relative to DeepSeek round20:

- `transition`:
  - same gap improves slightly:
    - `0.0147 -> 0.0103`
  - flip margin improves strongly:
    - `0.4829 -> 0.6101`
- `post-state`:
  - same gap improves:
    - `0.0748 -> 0.0474`
  - flip margin also improves:
    - `0.5500 -> 0.6311`

But pair-level deltas show that this is not a uniform improvement.

For `transition`, the gains are concentrated in:

- `wrong_theorem_reference`
- `wrong_projection`
- `wrong_target_term`
- `ill_typed_or_malformed`

while the regressions still include:

- `wrong_composition`
- `wrong_branch`
- `goal_mismatch_direct_use`

So the main unresolved split is not removed by changing models.

## Interpretation

The strongest current reading is:

1. round20's core mechanism split is not purely a DeepSeek artifact
2. `transition` remains the more invariant same-side readout across models
3. `wrong_composition` remains a stubborn non-win for `transition` across models
4. model choice changes the strength of several flip families, but does not erase the main mechanism boundary

## Gate Read

- `Object gate`: still partially supported
- `Audit gate`: stronger, because the mechanism split now shows cross-model persistence
- `Conversion gate`: untouched

This is a positive result for the project as a **measurement + mechanism** line.

## Next Step

The highest-value next steps are now:

1. split `wrong_composition` into finer subfamilies
2. inspect composition failures geometrically across DeepSeek and Goedel
3. only then decide whether another family-specific intervention is justified
