# Round26 Composition Geometry Audit

## Scope

This round does not introduce a new recipe.

It explains the three unresolved `wrong_composition` slices from round25 by re-reading them in raw latent geometry for:

- DeepSeek round20 hard-negative contrastive
- Goedel round24 hard-negative contrastive

## Inputs

- DeepSeek features:
  - `artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- Goedel features:
  - `artifacts/object_gate_round12/goedel_prover_v2_8b/boundary_states.pt`
- frozen annotated panel:
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- learned-score references:
  - `artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json`
  - `artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json`
- geometry dumps:
  - `artifacts/object_gate_round26/deepseek_composition_geometry.json`
  - `artifacts/object_gate_round26/goedel_composition_geometry.json`

## Main Result

The three unresolved composition slices fail for three different reasons.

1. `transitivity_order_swap` is a near-identity transition case.
2. `cts_round5_flip_imp_trans_1` is a bad-template anchoring case.
3. `cts_flip_eq_comm_api_1` is a model-specific alignment split, not a persistent geometric impossibility.

So the current mechanism bottleneck is not `wrong_composition` as a whole. It is a much narrower mix of:

- one order-sensitive transitivity slice
- one persistent argument-swap template
- one unstable fabrication slice

## Pair-Level Read

### 1. `cts_round5_flip_eq_trans_1`

This is the `transitivity_order_swap` singleton.

DeepSeek:

- `h_plus source_variant_cosine = 0.8894`
- `delta source_variant_cosine = 0.8746`
- learned gap:
  - `post = 0.0088`
  - `transition = 0.0019`

Goedel:

- `h_plus source_variant_cosine = 0.8790`
- `delta source_variant_cosine = 0.8654`
- learned gap:
  - `post = 0.6872`
  - `transition = 0.0215`

Interpretation:

- raw `post` and raw `delta` geometry both see source and variant as extremely close
- `transition` stays near-collapse on both models
- only Goedel's learned post-state scorer opens a large gap

This is the clearest evidence that `transitivity_order_swap` is not just “another composition error”. It is an order-sensitive slice where the separable cue currently lives much more in learned post-state readout than in raw transition geometry.

### 2. `cts_round5_flip_imp_trans_1`

This is the persistent `application_argument_swap` hard case.

DeepSeek:

- `h_plus source_variant_cosine = 0.9655`
- `delta source_variant_cosine = 0.9663`
- variant nearest negative is exactly `lean_imp_trans_bad_comp:3`
  - `h_plus cosine = 0.9950`
  - `delta cosine = 0.9933`
- learned gap:
  - `post = 0.0059`
  - `transition = 0.0164`

Goedel:

- `h_plus source_variant_cosine = 0.9642`
- `delta source_variant_cosine = 0.9633`
- variant nearest negative is again `lean_imp_trans_bad_comp:3`
  - `h_plus cosine = 0.9967`
  - `delta cosine = 0.9962`
- learned gap:
  - `post = 0.0067`
  - `transition = 0.0127`

Interpretation:

- this slice is not a family-wide abstraction failure
- it is a template-local ambiguity
- both source and variant sit extremely close to the same bad-composition exemplar, and the variant is almost identical to that negative anchor

This explains why the failure persists across both models: the bad branch is not merely semantically similar, it is geometrically almost the same template.

### 3. `cts_flip_eq_comm_api_1`

This is the unstable `transitivity_fabrication` case.

DeepSeek:

- `h_plus source_variant_cosine = 0.7265`
- `delta source_variant_cosine = 0.7067`
- learned gap:
  - `post = 0.0172`
  - `transition = 0.7022`

Goedel:

- `h_plus source_variant_cosine = 0.7629`
- `delta source_variant_cosine = 0.7198`
- learned gap:
  - `post = -0.0408`
  - `transition = 0.0118`

Interpretation:

- unlike the other two unresolved slices, this one is not near-collapse in raw geometry
- source and variant are materially less similar here
- DeepSeek's learned transition scorer converts that separation into a large flip gap
- Goedel's learned scorer does not

So this pair should not be read as a raw latent impossibility. It is a scorer/model-alignment split.

## Mechanism Read

The strongest current mechanism reading is:

1. `transitivity_order_swap` is the most likely true transition-blind slice.
2. `imp_trans` is a negative-template anchoring problem.
3. `eq_comm_api_1` is mainly model/scorer alignment noise.

This sharpens the round25 conclusion:

- `wrong_composition` is not one failure family
- even the remaining unresolved part is not one mechanism
- only one of the three slices currently looks like a genuine transition-side blind spot

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because the residual composition failure is now narrowed to concrete mechanisms rather than one vague family
- `Conversion gate`: untouched

## Next Step

The highest-value next move is not more family weighting.

It is one of:

1. a dedicated `transitivity_order_swap` micro-panel
2. a template-controlled audit around `lean_imp_trans_bad_comp`
3. a scorer-alignment comparison for the `eq_comm_api_1` slice
