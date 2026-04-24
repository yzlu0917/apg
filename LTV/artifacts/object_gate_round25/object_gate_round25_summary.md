# Round25 Wrong-Composition Subfamily Audit

## Scope

This round does not train a new model.

It refines the composition diagnosis by splitting `wrong_composition` into smaller subfamilies and re-reading existing results from:

- round20 DeepSeek hard-negative contrastive
- round24 Goedel hard-negative contrastive

## Subfamily Scheme

The updated annotation splits `wrong_composition` into:

- `application_argument_swap`
- `transitivity_fabrication`
- `transitivity_order_swap`

Counts on the round7 CTS panel:

- `application_argument_swap = 4`
- `transitivity_fabrication = 3`
- `transitivity_order_swap = 1`

## Inputs

- updated panel:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- round20 subfamily audit:
  - `artifacts/object_gate_round25/round20_subfamily_audit.json`
- round24 subfamily audit:
  - `artifacts/object_gate_round25/round24_subfamily_audit.json`

## Main Result

`wrong_composition` is not one mechanism.

The previous family-level ambiguity was hiding three very different behaviors:

1. `transitivity_fabrication` is mostly transition-friendly
2. `application_argument_swap` is mixed, with one persistent hard case
3. `transitivity_order_swap` is not a transition win on either model

So the next mechanism step should target the specific bad subfamilies, not the whole `wrong_composition` bucket.

## Round20 Read

DeepSeek round20:

- `application_argument_swap`
  - `post = 0.5481`
  - `transition = 0.3800`
- `transitivity_fabrication`
  - `post = 0.4811`
  - `transition = 0.7277`
- `transitivity_order_swap`
  - `post = 0.0088`
  - `transition = 0.0019`

Interpretation:

- `transitivity_fabrication` was already a clear transition-positive slice
- the family-level weakness of `wrong_composition` in round20 mainly came from the other two subfamilies

## Round24 Read

Goedel round24:

- `application_argument_swap`
  - `post = 0.5510`
  - `transition = 0.5288`
- `transitivity_fabrication`
  - `post = 0.4366`
  - `transition = 0.4901`
- `transitivity_order_swap`
  - `post = 0.6872`
  - `transition = 0.0215`

Interpretation:

- `transitivity_fabrication` remains slightly transition-positive on Goedel
- `application_argument_swap` becomes much closer across models, but still does not become a clean transition win
- `transitivity_order_swap` becomes a strong post-state win on Goedel

## Pair-Level Read

Inside `application_argument_swap`, the behavior is not uniform.

Stable easy cases for both models:

- `cts_round6_flip_and_imp_elim_1`
- `cts_round6_flip_false_of_imp_false_1`

Model-sensitive case:

- `cts_round5_flip_double_neg_1`
  - round20 transition: `0.0359`
  - round24 transition: `0.6370`

Persistent hard case:

- `cts_round5_flip_imp_trans_1`
  - round20 transition: `0.0164`
  - round24 transition: `0.0127`

Inside `transitivity_fabrication`, one pair is unstable across models:

- `cts_flip_eq_comm_api_1`
  - round20 transition: `0.7022`
  - round24 transition: `0.0118`

while the other two fabrication pairs stay strong for transition on both models.

## Interpretation

The strongest current reading is:

1. the old `wrong_composition` bucket was too coarse to support clean intervention
2. the real unresolved slices are now narrower:
   - `transitivity_order_swap`
   - the `imp_trans` style argument-swap case
   - one unstable `eq_comm -> trans` fabrication case
3. therefore round23 failed for the right reason: it pushed on a mixed bucket instead of a coherent mechanism

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because the main unresolved family is now decomposed into concrete sub-mechanisms
- `Conversion gate`: untouched

## Next Step

The highest-value next move is a geometry audit focused only on:

1. `transitivity_order_swap`
2. `cts_round5_flip_imp_trans_1`
3. `cts_flip_eq_comm_api_1`

rather than another bucket-level family intervention.
