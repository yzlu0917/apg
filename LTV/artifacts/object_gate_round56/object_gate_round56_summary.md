## Round56 Summary

### Goal

Run a direct head-to-head on the same Putnam hard oracle slice:

- frozen-hidden pairwise separability from round55
- versus an external API-based pairwise after-state judge

### Input Panel

Same panel as round55:

- oracle: [state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)
- generated: [state_first_putnam_candidates_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl)
- replayed: [state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)

Panel size:
- `7` states
- `40` unordered gap pairs
- `31` ordered pairs with direction labels

### External Judge Protocol

For each unordered pair inside a shared `before state`, the judge sees:
- theorem header
- shared `before_goals`
- candidate A tactic + `after_goals`
- candidate B tactic + `after_goals`

Output:
- `choice ∈ {A, B, equivalent}`
- normalized probabilities for `A / B / equivalent`

Implementation:
- [judge_state_first_pairwise_with_api.py](/cephfs/luyanzhen/apg/LTV/scripts/judge_state_first_pairwise_with_api.py)

Outputs:
- [putnam_v1_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl)
- [putnam_v1_judge_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_summary.json)

### Judge Results

Gap task (`ordered` vs `equivalent`):
- AUROC = `0.7903`
- accuracy = `0.7750`
- positive mean prob = `0.9274`
- negative mean prob = `0.8389`
- mean gap = `+0.0885`

Direction task (`better` vs `worse`, on ordered pairs only):
- AUROC = `0.9708`
- accuracy = `0.9355`
- positive mean prob = `0.8460`
- negative mean prob = `0.2254`
- mean gap = `+0.6206`

### Comparison Against Round55 Frozen Hidden

Round55 frozen-hidden on the same Putnam slice:

DeepSeek:
- gap linear AUROC = `0.3405`
- direction linear AUROC = `0.3502`

Goedel:
- gap linear AUROC = `0.3728`
- direction linear AUROC = `0.3007`

So the head-to-head read is:

- external pairwise judge remains strongly aligned with the Putnam oracle
- frozen hidden no longer provides robust cross-state separability on this harder domain

### Interpretation

This sharpens the current project boundary:

1. On easier oracle panels, hidden-based progress signal is real and low-complexity readable.
2. On genuinely hard Putnam states, that latent signal stops generalizing across states.
3. External after-state judging remains much more robust on the same harder slice.

So the right current conclusion is not:
- “latent progress supervision is useless”

but rather:
- “latent progress supervision appears competence-bound, while external after-state judging still works beyond that boundary.”

### Practical Value

This makes the next decision much cleaner:

- if the goal is the strongest immediate supervision signal on hard states, external judge is currently better
- if the goal is a cheap, internal latent reward, that branch now has a clearly exposed difficulty boundary

### Next Step

Do not keep doing hidden recipe sweep on this Putnam branch.

Most useful next moves are:
- freeze this Putnam slice as a hard external-judge comparison panel
- then decide whether to:
  - train a latent scorer to imitate the external judge on this hard slice, or
  - explicitly scope latent supervision claims to the model-competence regime where object gate remains positive
