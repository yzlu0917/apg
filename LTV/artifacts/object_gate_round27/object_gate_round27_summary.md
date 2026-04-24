# Round27 Template-Controlled Audit for `application_argument_swap`

## Scope

This round does not add a new scorer or recipe.

It asks a narrower mechanism question after round26:

- is `lean_imp_trans_bad_comp` a generic negative anchor for the whole `application_argument_swap` slice,
- or only for the persistent hard case `cts_round5_flip_imp_trans_1`?

## Inputs

- DeepSeek geometry dump:
  - `artifacts/object_gate_round27/deepseek_application_argument_swap_geometry.json`
- Goedel geometry dump:
  - `artifacts/object_gate_round27/goedel_application_argument_swap_geometry.json`
- frozen panel:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- geometry extractor:
  - `scripts/analyze_cts_slice_geometry.py`

## Main Result

`lean_imp_trans_bad_comp` is not a generic anchor for the whole `application_argument_swap` subfamily.

It is a stable local trap for exactly one pair:

- `cts_round5_flip_imp_trans_1`

The other three pairs do not show the same symmetric anchoring pattern.

So the correct reading is:

- `application_argument_swap` is not one unresolved mechanism
- the persistent hard case is a singleton-style template trap
- the rest of the subfamily is already largely explained by theorem-local bad templates

## Pair-Level Read

### Persistent hard case: `cts_round5_flip_imp_trans_1`

This is the only pair where both models, both fields, and both sides line up on the same bad template.

DeepSeek:

- `h_plus source_variant_cosine = 0.9655`
- `delta source_variant_cosine = 0.9663`
- source nearest negative:
  - `lean_imp_trans_bad_comp:3`
  - `post 0.9612`, `delta 0.9609`
- variant nearest negative:
  - `lean_imp_trans_bad_comp:3`
  - `post 0.9950`, `delta 0.9933`
- learned gap:
  - `post = 0.0059`
  - `transition = 0.0164`

Goedel:

- `h_plus source_variant_cosine = 0.9642`
- `delta source_variant_cosine = 0.9633`
- source nearest negative:
  - `lean_imp_trans_bad_comp:3`
  - `post 0.9560`, `delta 0.9553`
- variant nearest negative:
  - `lean_imp_trans_bad_comp:3`
  - `post 0.9967`, `delta 0.9962`
- learned gap:
  - `post = 0.0067`
  - `transition = 0.0127`

Interpretation:

- both source and variant live inside the same bad-template basin
- the variant is almost an exact copy of the negative exemplar
- this explains why the pair remains hard across models and readouts

### Non-persistent pair: `cts_round5_flip_double_neg_1`

This pair does not behave like `imp_trans`.

- DeepSeek still points nearest negative to `lean_imp_trans_bad_comp`, but only weakly:
  - `post ≈ 0.81`
  - `delta ≈ 0.56-0.60`
- Goedel already breaks the symmetry:
  - `h_plus` nearest negative becomes `lean_or_left_wrong_branch`
  - `delta` variant nearest negative becomes `lean_false_of_imp_false_bad_comp`
- learned gap is already large:
  - DeepSeek `post = 0.7197`
  - Goedel `transition = 0.6370`

Interpretation:

- this is not the same failure mode
- `lean_imp_trans_bad_comp` is at most a weak neighborhood attractor here, not the decisive template trap

### Non-persistent pair: `cts_round6_flip_and_imp_elim_1`

This pair resolves cleanly onto its theorem-local negative template.

DeepSeek:
- variant nearest negative: `lean_and_imp_elim_bad_comp:1`
  - `post 0.9968`, `delta 0.9946`

Goedel:
- variant nearest negative: `lean_and_imp_elim_bad_comp:1`
  - `post 0.9979`, `delta 0.9977`

Learned gap stays large on both models:
- `post ≈ 0.72`
- `transition ≈ 0.73`

Interpretation:

- this is the healthy case for the subfamily
- the bad branch gets mapped to the correct local negative template, not to the `imp_trans` basin

### Non-persistent pair: `cts_round6_flip_false_of_imp_false_1`

This pair also resolves mostly through its own local bad template.

DeepSeek:
- `h_plus` source nearest negative is still `lean_imp_trans_bad_comp`
- but variant nearest negative is `lean_false_of_imp_false_bad_comp:2` with `0.9963`

Goedel:
- same overall pattern
- variant nearest negative is `lean_false_of_imp_false_bad_comp:2` with `0.9989` (`post`) and `0.9965` (`delta`)

Learned gap stays large on both models:
- DeepSeek `transition = 0.7410`
- Goedel `transition = 0.7386`

Interpretation:

- `imp_trans` is not the main explanation here
- once the variant snaps to the theorem-local bad exemplar, the pair becomes easy

## Mechanism Read

The strongest current mechanism reading is:

1. `application_argument_swap` is mostly solved.
2. `cts_round5_flip_imp_trans_1` is the only stable unresolved member.
3. its failure is a symmetric template-anchoring trap around `lean_imp_trans_bad_comp:3`.
4. therefore this is not a subfamily-level deficit in transition reasoning; it is a very local template basin.

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because one previously broad unresolved slice is now reduced to a singleton-style mechanism
- `Conversion gate`: untouched

## Next Step

The highest-value next move is not more `application_argument_swap` coverage.

It is one of:

1. a micro-panel around `lean_imp_trans_bad_comp` with minimal lexical variation
2. an intervention that perturbs only the nested application order in the `imp_trans` template
3. or switching back to the remaining unresolved branches:
   - `transitivity_order_swap`
   - `eq_comm_api_1`
