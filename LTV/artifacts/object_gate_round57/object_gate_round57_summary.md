## Round57 Summary

### Goal

Test whether the harder-domain failure of latent ranking can itself be predicted from `before hidden`, and whether that trust signal is useful enough to gate between:

- latent-only ranking
- external judge ranking
- a trust-gated hybrid

### Minimal Trust Definition

For each state, define a model-specific trust label from that model's frozen-hidden separability result:

- `trust = 1` iff:
  - direction mean gap > 0
  - and gap mean gap > 0 when the state has both ordered/equivalent gap rows
- else `trust = 0`

This is a deliberately minimal state-level proxy for:

> "On this state, can we trust latent ranking to align with the oracle?"

### Inputs

Easy/medium side:
- oracle: [state_first_progress_oracle_panel_v2_consensus.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl)
- generated: [state_first_candidates_panel_v2_generated.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl)
- replayed: [state_first_candidates_panel_v2_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl)
- latent sep:
  - [deepseek_state_first_panel_v2_consensus_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/deepseek_state_first_panel_v2_consensus_sep.json)
  - [goedel_state_first_panel_v2_consensus_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/goedel_state_first_panel_v2_consensus_sep.json)

Putnam hard side:
- oracle: [state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)
- generated: [state_first_putnam_candidates_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl)
- replayed: [state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)
- latent sep:
  - [deepseek_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/deepseek_putnam_v1_sep.json)
  - [goedel_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/goedel_putnam_v1_sep.json)
- external judge rows:
  - [putnam_v1_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl)

### Method

1. Combine easy/medium consensus states and Putnam hard states into one state-level trust dataset.
2. Extract `before hidden` for each state.
3. Train leave-one-state-out trust predictors from `before hidden`.
4. On Putnam only, compare:
   - latent-only
   - judge-only
   - hard-gated hybrid (`trust >= 0.5 ? latent : judge`)
   - soft mixture (`trust * latent + (1-trust) * judge`)

Implementation:
- [evaluate_state_first_trust_gating.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_state_first_trust_gating.py)

Outputs:
- [deepseek_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/deepseek_trust_gating.json)
- [goedel_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/goedel_trust_gating.json)

### Trust Prediction

#### DeepSeek

- `24` total states
- trusted = `15`
- untrusted = `9`

From `before hidden`:
- linear trust AUROC = `0.7037`
- centroid trust AUROC = `0.8222`

#### Goedel

- `24` total states
- trusted = `15`
- untrusted = `9`

From `before hidden`:
- linear trust AUROC = `0.8481`
- centroid trust AUROC = `0.8444`

### Putnam Hybrid Comparison

#### DeepSeek

Gap task:
- latent-only AUROC = `0.3405`
- judge-only AUROC = `0.7903`
- hybrid AUROC = `0.6362`

Direction task:
- latent-only AUROC = `0.3502`
- judge-only AUROC = `0.9750`
- hybrid AUROC = `0.7492`

#### Goedel

Gap task:
- latent-only AUROC = `0.3728`
- judge-only AUROC = `0.7903`
- hybrid AUROC = `0.7652`

Direction task:
- latent-only AUROC = `0.3007`
- judge-only AUROC = `0.9750`
- hybrid AUROC = `0.7529`

### Interpretation

This round supports a stronger version of the competence-bound story:

1. `before hidden` does contain a nontrivial state-level trust / competence signal.
2. That trust signal is useful enough to improve over latent-only routing on Putnam.
3. But it does **not** recover judge-only quality.

So the current best reading is:

- latent failure on hard states is not just random noise
- it is at least partially predictable from state-level latent structure
- but the resulting gate is still a fallback mechanism, not a replacement for external judging

### Claim Update

What is now supported:
- easy/medium: latent progress ranking works
- hard Putnam: latent ranking fails, but `before hidden` partially predicts that failure
- trust-gated hybrid beats latent-only on hard states

What is not yet supported:
- trust gating is strong enough to replace judge-only ranking on hard states

### Practical Meaning

This makes the higher-level system picture sharper:

- latent signal = internal progress signal inside the competence regime
- before-hidden trust = boundary detector for that regime
- external judge = stronger supervision beyond that boundary

### Next Step

Do not keep tuning latent ranking on Putnam directly.

Most useful next moves are:
- distill the external judge into a latent scorer on the hard slice, or
- formalize a scoped claim that latent progress supervision is reliable only inside the model's competence regime
