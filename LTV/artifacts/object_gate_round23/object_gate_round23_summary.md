# Round23 Wrong-Composition Targeted Hard-Negative Summary

## Scope

This round tests a minimal family-targeted mechanism change on top of round20:

- keep the round20 hard-negative contrastive recipe
- add extra loss pressure only for `wrong_composition` flip pairs

The purpose is not generic tuning. It is to check whether the remaining `wrong_composition` bottleneck can be opened by a targeted hard-negative construction.

## Recipe

Evaluator:

- `scripts/evaluate_cts_family_hardneg_contrastive.py`

Setting:

- model: `DeepSeek-Prover-V2-7B`
- data: `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- annotated family labels:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- target family:
  - `wrong_composition`
- target weight:
  - `2.0`

Outputs:

- `artifacts/object_gate_round23/cts_family_hardneg_eval.json`
- `artifacts/object_gate_round23/cts_family_hardneg_audit.json`
- `artifacts/object_gate_round23/transition_mechanism_delta.json`
- `artifacts/object_gate_round23/post_mechanism_delta.json`

## Main Result

This round is a **negative mechanism result**.

The targeted family weighting does **not** rescue `wrong_composition` for `transition`.

Instead it creates a mixed tradeoff:

- `transition`: slightly higher overall flip sensitivity, but much worse same-side stability
- `post-state`: slightly better same-side stability, but slightly worse overall flip sensitivity

So this is not a clean mechanism improvement over round20.

## Overall Metrics

Reference from round20:

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

Round23 targeted result:

- `comphardneg_post_contrastive`
  - `IG = 0.0712`
  - `SS = 0.5389`
- `comphardneg_transition_contrastive`
  - `IG = 0.0537`
  - `SS = 0.5018`

Interpretation:

- `post-state` gets a tiny same-side improvement but loses flip strength
- `transition` gets a tiny flip gain but gives back most of the round20 same-side cleanup

## Target Family Read

What we actually wanted:

- improve `wrong_composition`, especially for `transition`

What happened:

- `transition wrong_composition`
  - `0.4631 -> 0.4613`
  - net change: slightly worse
  - `3 / 8` improved, `5 / 8` worsened
- `post-state wrong_composition`
  - `0.4556 -> 0.4594`
  - net change: slightly better
  - `7 / 8` improved, `1 / 8` worsened

So the targeted mechanism did **not** solve the intended bottleneck on the representation we most care about.

## Transition Mechanism Delta

Compared with round20:

- same gap:
  - `0.0147 -> 0.0537`
  - mean delta: `-0.0390`
- flip margin:
  - `0.4829 -> 0.5018`
  - mean delta: `+0.0189`

This is a bad trade for the current mechanism story.

The main regressions are on same families:

- `eliminator_style`: `0.0506 -> 0.3230`
- `other_same_rewrite`: `0.0327 -> 0.1027`
- `theorem_application_style`: `0.0423 -> 0.1099`

The flip-side changes are mostly elsewhere:

- improved:
  - `wrong_theorem_reference`: `0.3676 -> 0.4542`
  - `wrong_target_term`: `0.5017 -> 0.5063`
- worsened:
  - `wrong_projection`: `0.5276 -> 0.5072`
  - `wrong_composition`: `0.4631 -> 0.4613`

So the targeted pressure is not selectively sharpening the intended family. It is disturbing the broader transition geometry.

## Post-State Mechanism Delta

Compared with round20:

- same gap:
  - `0.0748 -> 0.0712`
- flip margin:
  - `0.5500 -> 0.5389`

This is milder than the transition case.

Notable changes:

- same-side gain:
  - `theorem_application_style`: `0.1907 -> 0.0126`
- flip-side target-family gain:
  - `wrong_composition`: `0.4556 -> 0.4594`

But these gains are too small to offset the overall drop in `SS`.

## Interpretation

The strongest reading is:

1. round20 worked because of a broader hard-negative geometry effect
2. a naive family-targeted weight is too blunt to isolate `wrong_composition`
3. on `transition`, the targeted pressure mostly breaks previously cleaned same-side structure
4. therefore the unresolved issue is not "do we need more pressure on `wrong_composition`?"
5. it is "what kind of hard negative is composition-specific enough not to damage same-side geometry?"

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because a plausible targeted mechanism was tested and failed cleanly
- `Conversion gate`: untouched

This round is useful as a **negative mechanism branch**, not as a new best method.

## Next Step

If continuing this line, the best next moves are:

1. split `wrong_composition` into finer subfamilies instead of weighting it as one bucket
2. move to geometry inspection for composition failures
3. or transfer round20 to a second prover before doing more family-specific intervention
