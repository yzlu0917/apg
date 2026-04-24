# Round50 Summary

## Goal

Add a harder manual-oracle slice from the round49 expansion pool, merge it into the existing oracle panel, and re-run frozen-hidden separability on the larger panel.

## New Hard Oracle Slice

- Hard oracle batch: [state_first_progress_oracle_batch_v2_hard.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_batch_v2_hard.jsonl)
- Combined oracle panel: [state_first_progress_oracle_panel_v2_expanded.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl)
- Combined generated panel: [state_first_candidates_panel_v2_generated.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl)
- Combined replay panel: [state_first_candidates_panel_v2_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl)
- DeepSeek separability: [deepseek_state_first_panel_v2_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/deepseek_state_first_panel_v2_sep.json)
- Goedel separability: [goedel_state_first_panel_v2_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/goedel_state_first_panel_v2_sep.json)

## Hard Slice Stats

- `num_states = 6`
- `num_candidates = 37`
- tier counts:
  - `solved = 13`
  - `strong_partial = 17`
  - `neutral = 7`
- pair counts:
  - `ordered = 69`
  - `equivalent = 30`

This slice is clearly more informative than the earlier all-solved arithmetic rows.

## Expanded Panel Stats

- `num_states = 17`
- `num_candidates = 104`
- tier counts:
  - `solved = 38`
  - `strong_partial = 46`
  - `weak_partial = 11`
  - `neutral = 9`
- pair counts:
  - `ordered = 162`
  - `equivalent = 117`

## Separability Results

DeepSeek:

- gap task:
  - `linear AUROC = 0.9301`
  - `centroid AUROC = 0.8275`
  - `1NN = 0.8925`
- direction task:
  - `linear AUROC = 0.9373`
  - `centroid AUROC = 0.9510`
  - `1NN = 0.9630`

Goedel:

- gap task:
  - `linear AUROC = 0.8754`
  - `centroid AUROC = 0.8020`
  - `1NN = 0.8746`
- direction task:
  - `linear AUROC = 0.9427`
  - `centroid AUROC = 0.9486`
  - `1NN = 0.9444`

## Readout

The harder slice did not wash out the object signal. After expanding from the previous `11`-state panel to a `17`-state panel with more residual-goal structure, frozen hidden states remain strongly separable under weak readouts in both prover families.

The most accurate current object-level claim is:

> pairwise progress-difference information is present in frozen hidden states, low-complexity readable, and robust to a moderate expansion in panel size and difficulty.
