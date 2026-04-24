## Round55 Summary

### Goal

Expand the tiny Putnam harder-domain pilot into a larger human-oracle slice and check whether frozen-hidden pairwise progress signal still survives under the same `state-first -> Lean legality -> human oracle` protocol.

### Inputs

- Seed panel: [state_first_putnam_seed_panel_v1_expanded.jsonl](/cephfs/luyanzhen/apg/LTV/data/lean/state_first_putnam_seed_panel_v1_expanded.jsonl)
- Generated candidates: [state_first_putnam_candidates_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl)
- Replayed candidates: [state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)
- Human oracle: [state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)

### Data

- `7` Putnam harder states with oracle labels
- `27` replay-ok candidates
- `40` gap pairs:
  - `31 ordered`
  - `9 equivalent`
- `62` direction examples

State coverage:
- `coeff_X_sub_C_pow__sorry0`
- `finite_diff_identity__sorry1`
- `putnam_1976_b5__sorry2`
- `putnam_1976_b5__sorry3`
- `putnam_1993_a4__sorry0`
- `putnam_2013_b4__sorry2`
- `putnam_2013_b4__sorry3`

### Frozen-Hidden Audit

DeepSeek:
- gap:
  - linear AUROC = `0.3405`
  - centroid AUROC = `0.1989`
  - linear mean gap = `-0.3082`
- direction:
  - linear AUROC = `0.3502`
  - centroid AUROC = `0.4984`
  - linear mean gap = `-0.2344`

Goedel:
- gap:
  - linear AUROC = `0.3728`
  - centroid AUROC = `0.2330`
  - linear mean gap = `-0.3403`
- direction:
  - linear AUROC = `0.3007`
  - centroid AUROC = `0.5463`
  - linear mean gap = `-0.3548`

Result files:
- [deepseek_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/deepseek_putnam_v1_sep.json)
- [goedel_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/goedel_putnam_v1_sep.json)

### Interpretation

This is materially different from round54's tiny pilot.

- In round54, Putnam still preserved a coarse `ordered vs equivalent` gap while fine `better vs worse` direction collapsed.
- In round55, after expanding to `7` harder states, both coarse gap and fine direction fail to generalize across states.

The most plausible current reading is:

1. The earlier Putnam pilot was too small to define a stable hard-domain boundary.
2. On genuinely harder Putnam states, frozen hidden no longer provides a robust cross-state pairwise progress geometry under the current protocol.
3. The latent signal is therefore not just difficulty-dependent in a mild sense; it appears to break once we move outside the prover's comfortable competence regime.

This does **not** imply there is zero useful signal on every Putnam state.
Some individual states still show locally sensible orderings, but the leave-one-state-out separability that supported the easier domains no longer survives.

### Claim Update

Current object claim boundary:

- Supported:
  - On easy-to-medium Lean states, and on our earlier consensus oracle panel, frozen hidden contains low-complexity pairwise progress information.
- Not currently supported:
  - The same cross-state pairwise progress separability transfers to genuinely hard Putnam states.

### Immediate Next Step

Do not jump into method sweep here.

Most useful next moves are:
- add a second annotator or disagreement audit on this Putnam slice, or
- compare frozen hidden against an external LLM after-state judge on the same Putnam panel.

At this point, the important result is the **boundary**, not another recipe tweak.
