## Round61: Mixed-panel hybrid reranking shows first positive conversion result

### Goal

Turn the current object/mechanism findings into a minimal utility test on one mixed panel:

- easy/medium consensus oracle states
- Putnam hard oracle states

Compare four ranking strategies on the same candidate sets:

1. weak baseline
2. latent-only reranking
3. judge-only reranking
4. trust-gated hybrid reranking

The key question is no longer whether hidden contains signal, but whether that signal can be converted into useful ranking decisions once paired with the `before hidden` trust gate discovered in round57.

### Inputs

Easy/medium side:
- oracle: [state_first_progress_oracle_panel_v2_consensus.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl)
- generated: [state_first_candidates_panel_v2_generated.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl)
- replayed: [state_first_candidates_panel_v2_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl)
- external judge rows: [panel_v2_consensus_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl)

Putnam hard side:
- oracle: [state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)
- generated: [state_first_putnam_candidates_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl)
- replayed: [state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)
- external judge rows: [putnam_v1_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl)

Trust inputs:
- [deepseek_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/deepseek_trust_gating.json)
- [goedel_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/goedel_trust_gating.json)

Implementation:
- [generate_state_first_candidates_with_api.py](/cephfs/luyanzhen/apg/LTV/scripts/generate_state_first_candidates_with_api.py)
- [judge_state_first_pairwise_with_api.py](/cephfs/luyanzhen/apg/LTV/scripts/judge_state_first_pairwise_with_api.py)
- [evaluate_hybrid_reranking.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_hybrid_reranking.py)

Outputs:
- [deepseek_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/deepseek_hybrid_reranking.json)
- [goedel_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/goedel_hybrid_reranking.json)
- [panel_v2_consensus_judge_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/panel_v2_consensus_judge_summary.json)

### Mixed Panel

- `24` states total
- `131` replay-ok candidates total
  - `17` easy/medium consensus states
  - `7` Putnam hard states

The easy/medium external judge itself is strong:
- gap AUROC = `0.9429`
- direction AUROC = `1.0000`

### Ranking Methods

All methods rank the same replay-ok candidates inside each state.

#### Baseline

- `baseline_index_order`
- deterministic candidate-index fallback

#### Latent-only

- train a leave-one-state-out state-local latent scorer on frozen hidden states over the mixed panel

#### Judge-only

- aggregate pairwise external-judge probabilities into candidate-level scores

#### Hybrid

- predict state-level trust from `before hidden`
- if trust is low, use judge ranking
- if trust is high, use latent ranking

Two trust variants are evaluated:
- `linear`
- `centroid`

Both hard-gate and soft-mixture variants are included.

### Results

Metrics:
- `top1_max_tier_hit_rate`
- `top2_max_tier_hit_rate`
- `mean_ndcg`
- `mean_top1_ordinal`

#### DeepSeek

Baseline:
- top1 hit = `0.2917`
- top2 hit = `0.5000`
- mean NDCG = `0.8366`

Latent-only:
- top1 hit = `0.7500`
- top2 hit = `0.8333`
- mean NDCG = `0.9256`
- mean top1 ordinal = `2.4167`

Judge-only:
- top1 hit = `0.9583`
- top2 hit = `1.0000`
- mean NDCG = `0.9914`
- mean top1 ordinal = `2.6250`

Hybrid, linear trust:
- top1 hit = `0.9167`
- top2 hit = `0.9583`
- mean NDCG = `0.9779`
- mean top1 ordinal = `2.5833`

Hybrid, centroid trust:
- top1 hit = `0.9583`
- top2 hit = `1.0000`
- mean NDCG = `0.9901`
- mean top1 ordinal = `2.6250`

#### Goedel

Baseline:
- top1 hit = `0.2917`
- top2 hit = `0.5000`
- mean NDCG = `0.8366`

Latent-only:
- top1 hit = `0.8333`
- top2 hit = `0.9167`
- mean NDCG = `0.9509`
- mean top1 ordinal = `2.5000`

Judge-only:
- top1 hit = `0.9583`
- top2 hit = `1.0000`
- mean NDCG = `0.9914`
- mean top1 ordinal = `2.6250`

Hybrid, linear trust:
- top1 hit = `0.9583`
- top2 hit = `0.9583`
- mean NDCG = `0.9805`
- mean top1 ordinal = `2.6250`

Hybrid, centroid trust:
- top1 hit = `0.9583`
- top2 hit = `1.0000`
- mean NDCG = `0.9852`
- mean top1 ordinal = `2.6250`

### Interpretation

This is the first clear positive `conversion gate` result.

#### 1. Latent-only already has genuine decision value

On the mixed easy+hard panel, latent-only is far above the weak baseline for both models:

- DeepSeek top1 hit: `0.2917 -> 0.7500`
- Goedel top1 hit: `0.2917 -> 0.8333`

So the object/method findings are not merely diagnostic. The learned latent signal already converts into meaningful candidate-ranking gain.

#### 2. Judge-only remains the strongest overall ranking signal

Judge-only stays best on the mixed panel for both models:

- top1 hit = `0.9583`
- top2 hit = `1.0000`
- mean NDCG = `0.9914`

This is consistent with the harder-domain story from rounds 55–60:
- judge behaves like a more canonical cross-state scalar
- latent is still partially competence-bound

#### 3. Trust-gated hybrid captures most of the judge advantage

The central result is that the round57 trust signal is now useful at the ranking level, not just as a mechanism diagnostic.

DeepSeek:
- latent-only top1 hit = `0.7500`
- centroid-hybrid top1 hit = `0.9583`
- latent-only mean NDCG = `0.9256`
- centroid-hybrid mean NDCG = `0.9901`

Goedel:
- latent-only top1 hit = `0.8333`
- centroid-hybrid top1 hit = `0.9583`
- latent-only mean NDCG = `0.9509`
- centroid-hybrid mean NDCG = `0.9852`

So a simple trust gate closes most of the utility gap between latent-only and judge-only, especially with the centroid trust predictor.

#### 4. This gives the current findings a concrete system role

The best current reading is now:

- `after hidden` = cheap local reranking signal
- `before hidden` = competence / trust gate
- external judge = fallback / canonical scorer beyond the latent regime

That is stronger than the earlier claim that trust was merely a boundary detector. It is now a useful routing primitive in a real mixed-panel decision task.

### Claim Update

Now supported:
- latent progress signals convert into useful reranking gain on a mixed panel
- trust gating substantially improves over latent-only
- the best hybrid nearly matches judge-only utility on this mixed panel

Still not supported:
- latent alone can replace judge on hardest states
- a single global latent ranking geometry exists on hard Putnam states

### Conclusion

Round61 is the first round where the latent progress story clearly crosses from:

- object evidence
- mechanism explanation

into:

- actionable utility

The resulting role is not “latent replaces judge everywhere”.
It is:

**latent local scorer + before-state trust gate + judge fallback**

And on the current mixed panel, that hybrid is already close to the strongest available ranking signal.
