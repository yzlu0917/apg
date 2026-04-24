# Round49 Summary

## Goal

Expand the `state-first` oracle pipeline beyond the current `11`-state panel and identify additional replayable states that are likely to yield harder progress distinctions.

## Expansion Replay

- Seed panel: [state_first_expansion_seed_panel_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/lean/state_first_expansion_seed_panel_v1.jsonl)
- Generated candidates: [state_first_candidates_expansion_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round49/state_first_candidates_expansion_v1.jsonl)
- Replayed candidates: [state_first_candidates_expansion_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round49/state_first_candidates_expansion_v1_replayed.jsonl)
- Replay summary: [state_first_candidates_expansion_v1_replayed_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round49/state_first_candidates_expansion_v1_replayed_summary.json)

## Key Stats

- `num_states = 15`
- `num_generated_candidates = 121`
- `num_replay_ok = 100`
- `num_replay_error = 21`

Per-state replay / coarse structure:

- `lean_or_right_pos__step1`: `5 ok / 3 err`, `2 solved_ok / 3 residual_ok`
- `lean_and_left_pos__step1`: `6 ok / 2 err`, `1 solved_ok / 5 residual_ok`
- `lean_and_right_pos__step1`: `8 ok / 0 err`, `5 solved_ok / 3 residual_ok`
- `lean_false_elim_pos__step1`: `7 ok / 1 err`, `5 solved_ok / 2 residual_ok`
- `lean_eq_refl_pos__step0`: `6 ok / 2 err`, `6 solved_ok / 0 residual_ok`
- `lean_mul_zero_right_pos__step0`: `6 ok / 2 err`, `5 solved_ok / 1 residual_ok`
- `lean_double_neg_intro_pos__step2`: `8 ok / 0 err`, `4 solved_ok / 4 residual_ok`
- `lean_eq_succ_refl_pos__step0`: `7 ok / 1 err`, `7 solved_ok / 0 residual_ok`
- `lean_eq_add_self_refl_pos__step0`: `7 ok / 1 err`, `6 solved_ok / 1 residual_ok`
- `lean_eq_succ_add_refl_pos__step0`: `7 ok / 1 err`, `7 solved_ok / 0 residual_ok`
- `lean_eq_proj_left_refl_pos__step0`: `7 ok / 1 err`, `7 solved_ok / 0 residual_ok`
- `lean_eq_proj_right_refl_pos__step0`: `8 ok / 0 err`, `7 solved_ok / 1 residual_ok`
- `lean_and_left_proj_simpa_pos__step1`: `6 ok / 2 err`, `1 solved_ok / 5 residual_ok`
- `lean_and_right_proj_simpa_pos__step1`: `7 ok / 1 err`, `3 solved_ok / 4 residual_ok`
- `lean_eq_trans_show_pos__step2`: `5 ok / 4 err`, `2 solved_ok / 3 residual_ok`

## Readout

The expansion replay succeeded and produced a useful harder candidate pool. The most informative states are not the reflexivity / ex-falso rows; they are the ones with many replay-ok candidates and nontrivial residual-goal structure:

- `lean_and_left_pos__step1`
- `lean_double_neg_intro_pos__step2`
- `lean_and_left_proj_simpa_pos__step1`
- `lean_and_right_proj_simpa_pos__step1`
- `lean_eq_trans_show_pos__step2`

These became the natural source for the next hard-oracle batch.
