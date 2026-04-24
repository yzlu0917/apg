# Round47: medium-difficulty state-first expansion batch

## Goal

Expand the new state-first oracle pipeline beyond the initial easy/dev batch by adding a medium-difficulty slice.

## Panel Split

- frozen dev panel:
  - `data/lean/state_first_dev_panel_v0.jsonl`
- new medium seed slice:
  - `data/lean/state_first_medium_seed_panel_v0.jsonl`
- split config:
  - `configs/object_gate/state_first_panel_split_v0.yaml`

## Medium Slice

The new medium slice contains `6` states:

- `lean_imp_trans_pos__step3`
- `lean_eq_trans_pos__step2`
- `lean_and_imp_elim_pos__step1`
- `lean_false_of_imp_false_pos__step2`
- `lean_and_to_imp_apply_pos__step1`
- `lean_imp_chain_four_pos__step4`

These states bias toward:

- implication composition
- equality transitivity
- projection-plus-application
- nested implication chains

## Generation + Replay

- generated candidates: `49`
- replay-ok: `35`
- replay-error: `14`

Per-state replay profile:

- `lean_imp_trans_pos__step3`: `6 ok / 2 err`
- `lean_eq_trans_pos__step2`: `4 ok / 5 err`
- `lean_and_imp_elim_pos__step1`: `7 ok / 1 err`
- `lean_false_of_imp_false_pos__step2`: `6 ok / 2 err`
- `lean_and_to_imp_apply_pos__step1`: `8 ok / 0 err`
- `lean_imp_chain_four_pos__step4`: `4 ok / 4 err`

## Why This Slice Matters

Unlike the initial dev batch, this slice is not dominated by all-solved arithmetic states.
Most states now exhibit a nontrivial mix of:

- direct solve candidates
- clear strong partial progress
- weaker local setup moves
- outright replay failures

That makes this slice a better source for the next human progress oracle panel.

## Next

- annotate the replay-ok candidates with the same tiered human oracle
- merge dev + medium into a larger combined panel
- rerun the same frozen-hidden separability audit
