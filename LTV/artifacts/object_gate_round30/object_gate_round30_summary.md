# Round30 Neighborhood Delta Audit

## Scope

This round does not add new data generation beyond the already-built round28/29 micro-panels, and it does not change the scorer.

It compares:

- the bad singleton rows from round26
- the clean theorem-local micro-panels from round28 and round29

under the same geometry readout, to answer one question:

- why does the frozen round7 panel fail where the micro-panels succeed?

## Inputs

- round26 singleton geometry:
  - `artifacts/object_gate_round26/deepseek_composition_geometry.json`
  - `artifacts/object_gate_round26/goedel_composition_geometry.json`
- round28 micro-panel geometry:
  - `artifacts/object_gate_round30/deepseek_round28_flip_geometry.json`
  - `artifacts/object_gate_round30/goedel_round28_flip_geometry.json`
- round29 micro-panel geometry:
  - `artifacts/object_gate_round30/deepseek_round29_flip_geometry.json`
  - `artifacts/object_gate_round30/goedel_round29_flip_geometry.json`
- compact comparison:
  - `artifacts/object_gate_round30/neighborhood_delta_summary.json`

## Main Result

The round26 failures are not explained by a different local geometry class.

At the neighborhood level, the bad singleton rows and the good micro-panel rows are much closer than their learned score gaps suggest.

So the strongest current reading is:

- the residual failures are not local template failures
- they are scorer/context failures induced by how the singleton sits inside the frozen round7 panel neighborhood

## Three Concrete Differences

### 1. Score gap collapses, but geometry barely moves

`eq_trans`:

- round26 DeepSeek singleton:
  - `delta score gap = 0.0019`
- round28 DeepSeek micro-panel mean:
  - `delta score gap = 0.4546`

But the geometry shift is tiny:

- singleton `delta source_variant_cosine = 0.8746`
- micro mean `delta source_variant_cosine = 0.8520`

`eq_comm` shows the same pattern:

- round26 Goedel singleton `transition gap = 0.0118`
- round29 Goedel micro-panel mean `transition gap = 0.4549`
- while `delta source_variant_cosine` only changes from `0.7198` to `0.7345`

Interpretation:

- the learned scorer is amplifying panel-context differences much more than the raw local geometry changes

### 2. Negative-neighbor identity stays largely stable

`eq_trans`:

- singleton and micro-panel both map `delta` variants to `lean_eq_trans_bad_comp`
- DeepSeek `h_plus` also keeps mapping to `lean_imp_trans_bad_comp`
- Goedel `h_plus` stays in the same coarse nuisance neighborhood (`lean_or_left_wrong_branch` / `lean_add_zero_wrong_ref`)

`eq_comm`:

- singleton and micro-panel both map `delta` variants mostly to `lean_and_comm_bad_order`
- `h_plus` negatives remain in the same coarse nuisance pool (`lean_add_zero_wrong_ref`, `lean_eq_trans_bad_comp`, `lean_imp_trans_bad_comp`)

Interpretation:

- the singleton failures are not caused by a totally different nearest-negative class
- the bad rows live in broadly the same local neighborhood family as the successful micro-panel rows

### 3. Margin-drop sign flips between singleton and micro-panel

For both unresolved families, the biggest systematic change is not nearest-neighbor identity but `margin_drop` direction.

`eq_trans`:

- round26 DeepSeek singleton `h_plus margin_drop = -0.0081`
- round28 DeepSeek micro mean `h_plus margin_drop = +0.0042`

`eq_comm`:

- round26 Goedel singleton `delta margin_drop = -0.0587`
- round29 Goedel micro mean `delta margin_drop = +0.0276`

Interpretation:

- the micro-panels place the variant on the “more negative than source” side of the local margin
- the bad singleton rows do not consistently achieve that sign
- this is a neighborhood calibration problem, not a template-level impossibility

## Interpretation

This is the cleanest current read of the branch:

1. round27 showed `imp_trans` is a singleton template trap
2. round28 showed `transitivity_order_swap` is not an intrinsic template blind spot
3. round29 showed `eq_comm_api_1` is not a theorem-local model split
4. round30 now shows why those apparent failures survived in the large panel:
   - not because local geometry is fundamentally different
   - but because the frozen scorer converts small neighborhood differences into very different margins depending on panel context

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: substantially stronger
- `Conversion gate`: untouched

## Decision

This branch is now ready to be frozen as a context-sensitive audit result.

Further local rescue on these templates is unlikely to teach us much unless the goal is explicitly to study neighborhood calibration.
