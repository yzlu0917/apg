# Round46: first separability audit on state-first human progress oracle

## Goal

Run the first frozen-hidden separability audit on the new state-first human progress oracle batch.

## Inputs

- oracle: `data/annotations/state_first_progress_oracle_batch_v0.jsonl`
- generated batch: `artifacts/object_gate_round44/state_first_candidates_batch_v0.jsonl`
- replayed batch: `artifacts/object_gate_round44/state_first_candidates_batch_v0_replayed.jsonl`

## Protocol

- derive state-local pairwise relations from oracle tiers
- keep two tasks separate:
  - `gap task`: distinguish `ordered` pairs from `equivalent` pairs
  - `direction task`: for ordered pairs only, distinguish `better-minus-worse` from `worse-minus-better`
- use frozen prover hidden states with weak readouts only:
  - linear probe
  - centroid scorer

## Batch Size

- `num_states = 5`
- `num_gap_pairs = 89`
  - `ordered = 32`
  - `equivalent = 57`
- `num_direction_examples = 64`

## Main Result

This batch is genuinely separable.

### DeepSeek-Prover-V2-7B

- gap task:
  - `linear AUROC = 0.8591`
  - `centroid AUROC = 0.7341`
- direction task:
  - `linear AUROC = 0.7090`
  - `centroid AUROC = 0.7637`

### Goedel-Prover-V2-8B

- gap task:
  - `linear AUROC = 0.7881`
  - `centroid AUROC = 0.8114`
- direction task:
  - `linear AUROC = 0.7109`
  - `centroid AUROC = 0.8228`

## Geometry

### DeepSeek

- gap task:
  - `centroid_gap = 0.2250`
  - `fisher_ratio = 0.0799`
  - `loo_1nn_acc = 0.8652`
- direction task:
  - `centroid_gap = 0.7515`
  - `fisher_ratio = 0.3298`
  - `loo_1nn_acc = 0.8125`

### Goedel

- gap task:
  - `centroid_gap = 0.2241`
  - `fisher_ratio = 0.0810`
  - `loo_1nn_acc = 0.8315`
- direction task:
  - `centroid_gap = 0.7795`
  - `fisher_ratio = 0.3597`
  - `loo_1nn_acc = 0.7813`

## Interpretation

- The new human-oracle batch is not just subjectively tiered; it induces a real low-complexity hidden-space separation.
- This is stronger than the old CTS proxy story because:
  - legality is handled upstream by Lean
  - preference is defined on replay-ok candidates under a shared before-state
  - the signal survives across two prover families
- Within a fixed before-state pairwise comparison, post-state differences and transition differences collapse to the same object, so this audit uses pairwise `h_plus` features.

## Limits

- only `5` states
- single annotator
- current batch still includes two fully solved arithmetic states, so this is not yet a final panel

## Next

- freeze a small final state-first oracle panel
- add medium-difficulty states with richer partial-order structure
- rerun the same separability protocol on the expanded panel
