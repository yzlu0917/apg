# Round29 `eq_comm` Micro-Panel Audit

## Scope

This round does not change the scorer or recipe.

It revisits the remaining round26 slice `cts_flip_eq_comm_api_1` with a theorem-local micro-panel around `lean_eq_comm_pos`.

Because the original theorem family contains only one theorem id, this round uses a protocol-preserving two-theorem clone setup:

- `lean_eq_comm_pos`
- `lean_eq_comm_pos_clone`

This keeps leave-one-theorem-out training non-empty without changing the local proof template.

## Inputs

- base micro-panel:
  - `data/cts/cts_eq_comm_micro_round29.jsonl`
- two-theorem protocol copy:
  - `data/cts/cts_eq_comm_micro_round29_2theorem.jsonl`
- cloned raw theorem file:
  - `data/lean/lean_eq_comm_micro_round29_raw.jsonl`
- DeepSeek eval:
  - `artifacts/object_gate_round29/deepseek_eq_comm_micro_eval.json`
- Goedel eval:
  - `artifacts/object_gate_round29/goedel_eq_comm_micro_eval.json`

## Main Result

`eq_comm_api_1` does **not** reproduce as a stable theorem-local model split.

On the controlled `eq_comm` micro-panel, both models and both readouts:

- keep symmetry rewrites nearly invariant
- cleanly separate all fabrication-style transitivity flips

So the round26 `eq_comm_api_1` behavior should now be read as a broader panel / neighborhood artifact, not as an intrinsic `eq_comm` template failure.

## Key Read

DeepSeek:

- `round29deepseek_post_contrastive`
  - `IG = 0.00023`
  - `SS = 0.75944`
- `round29deepseek_transition_contrastive`
  - `IG = 0.00022`
  - `SS = 0.75945`

Goedel:

- `round29goedel_post_contrastive`
  - `IG = 0.00016`
  - `SS = 0.75816`
- `round29goedel_transition_contrastive`
  - `IG = 0.00015`
  - `SS = 0.75816`

This holds across multiple local surface forms:

Same rewrites:
- `exact Eq.symm h`
- `simpa using Eq.symm h`
- `exact (show b = a from h.symm)`

Fabrication flips:
- `exact h.trans rfl`
- `exact h.trans (Eq.refl b)`
- `exact Eq.trans h rfl`
- `simpa using Eq.trans h (Eq.refl b)`
- `exact (show a = b from Eq.trans h (Eq.refl b))`

## Interpretation

This changes the read of round26's remaining unstable fabrication slice.

Before round29, a plausible read was:

- `eq_comm_api_1` may reveal a stable scorer/model alignment split

After round29, the better read is:

- the local `eq_comm` fabrication template is not hard for either model
- the round26 divergence is therefore not theorem-local
- it more likely came from broader training neighborhood effects inside the frozen round7 panel

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because another apparent residual failure has been downgraded from template-level issue to context-sensitive artifact
- `Conversion gate`: untouched

## Next Step

The highest-value next move is now:

1. compare round26 singleton rows against round28/29 micro-panels under shared neighborhood statistics
2. or stop local rescue entirely and freeze the current branch as a context-sensitive audit result
