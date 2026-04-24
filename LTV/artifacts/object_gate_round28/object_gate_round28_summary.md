# Round28 `transitivity_order_swap` Micro-Panel Audit

## Scope

This round does not change the recipe.

It asks whether `transitivity_order_swap` is intrinsically a transition blind spot, or whether the round26 singleton was a panel-context artifact.

To test that, this round builds a tiny controlled `eq_trans` micro-panel with:

- same-semantics explicit transitivity rewrites
- semantic-flip order-swap rewrites
- both `exact` and `simpa using` surface forms

## Inputs

- micro-panel:
  - `data/cts/cts_transitivity_order_micro_round28.jsonl`
- DeepSeek eval:
  - `artifacts/object_gate_round28/deepseek_transitivity_order_micro_eval.json`
- Goedel eval:
  - `artifacts/object_gate_round28/goedel_transitivity_order_micro_eval.json`

## Main Result

`transitivity_order_swap` is **not** an intrinsic blind spot of the frozen hard-negative recipe.

On the controlled `eq_trans` micro-panel, both models and both readouts separate order-swapped flips almost perfectly while keeping same rewrites nearly invariant.

So the round26 singleton should now be read as a broader panel-context failure, not as proof that the `eq_trans` order-swap template itself is fundamentally unreadable to `transition`.

## Key Read

DeepSeek:

- `round28deepseek_post_contrastive`
  - `IG = 0.00089`
  - `SS = 0.75821`
- `round28deepseek_transition_contrastive`
  - `IG = 0.00080`
  - `SS = 0.75828`

Goedel:

- `round28goedel_post_contrastive`
  - `IG = 0.00022`
  - `SS = 0.75671`
- `round28goedel_transition_contrastive`
  - `IG = 0.00030`
  - `SS = 0.75671`

And this is not limited to one surface form:

- `exact hbc.trans hab`
- `exact Eq.trans hbc hab`
- `simpa using Eq.trans hbc hab`

all flip cleanly on both models.

## Interpretation

This changes the mechanism read from round26.

Before round28, the strongest read was:

- `transitivity_order_swap` might be a true transition blind spot

After round28, the better read is:

- the original `cts_round5_flip_eq_trans_1` failure is not driven by the local `eq_trans` template alone
- the failure likely depends on broader panel-level training context or contrastive neighborhood construction
- therefore `transitivity_order_swap` should not be frozen as a clean diagnosis branch yet

## Gate Read

- `Object gate`: unchanged
- `Audit gate`: stronger, because one apparent blind spot has been downgraded from “intrinsic template failure” to “context-sensitive failure”
- `Conversion gate`: untouched

## Next Step

The highest-value next move is now:

1. compare the singleton `cts_round5_flip_eq_trans_1` against this micro-panel under shared geometry
2. inspect what negative neighborhoods differ between the frozen round7 panel and the micro-panel
3. or switch back to the remaining unresolved slice `eq_comm_api_1`
