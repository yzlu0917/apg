## Round62: Budgeted k-candidate reranking shows large judge-cost savings for trust-gated hybrid

### Goal

Push the round61 hybrid story into a more search-like setting.

Instead of evaluating ranking over the full candidate pool of each state, evaluate exact `k`-candidate subsets and ask:

- how often does each method pick the best candidate?
- how often does it pick a `solved` candidate?
- how much external-judge cost does it require?

This is the first direct quality-cost tradeoff test for the current:

**latent local reranker + trust gate + judge fallback**

### Inputs

Mixed-panel ranking outputs from round61:
- [deepseek_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/deepseek_hybrid_reranking.json)
- [goedel_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/goedel_hybrid_reranking.json)

Trust predictions from round57:
- [deepseek_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/deepseek_trust_gating.json)
- [goedel_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/goedel_trust_gating.json)

Implementation:
- [evaluate_budgeted_hybrid_reranking.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_budgeted_hybrid_reranking.py)

Outputs:
- [deepseek_budgeted_hybrid.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round62/deepseek_budgeted_hybrid.json)
- [goedel_budgeted_hybrid.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round62/goedel_budgeted_hybrid.json)

### Protocol

For each state, evaluate all exact subsets of size:
- `k = 4`
- `k = 6`

Methods compared:
- `baseline_index_order`
- `latent_only`
- `judge_only`
- `hybrid_hard_gate_centroid`

Judge cost is measured as pairwise judge comparisons:
- judge-only cost per subset = `C(k, 2)`
- hybrid cost per subset = `C(k, 2)` only on states where centroid trust says latent is untrusted

### Important Caveat

This budgeted protocol is useful, but it is **not** a clean hard-domain benchmark.

The subset counts are highly imbalanced:

- for `k = 4`:
  - easy subsets = `422`
  - Putnam subsets = `9`
- for `k = 6`:
  - easy subsets = `111`
  - Putnam subsets = `0`

So:
- `k = 6` is effectively an easy-only evaluation
- `k = 4` is still dominated by easy states

This means the very strong round62 aggregate numbers should be read as:

**evidence for search-like utility inside the current mixed/easy-heavy regime**

not as:

**evidence that latent reranking is now strong on hard Putnam subsets**

### Results

#### DeepSeek

##### `k = 4`

Baseline:
- top1 max-tier hit = `0.3991`
- top1 solved hit = `0.1810`
- mean NDCG = `0.8607`

Latent-only:
- top1 max-tier hit = `0.9675`
- top1 solved hit = `0.7378`
- mean NDCG = `0.9851`
- mean judge pair calls = `0.0`

Judge-only:
- top1 max-tier hit = `0.9977`
- top1 solved hit = `0.7401`
- mean NDCG = `0.9995`
- mean judge pair calls = `6.0`

Hybrid:
- top1 max-tier hit = `0.9838`
- top1 solved hit = `0.7401`
- mean NDCG = `0.9900`
- mean judge pair calls = `0.8213`
- judge-cost ratio vs judge-only = `0.1369`

##### `k = 6`

Baseline:
- top1 max-tier hit = `0.2072`
- top1 solved hit = `0.0811`
- mean NDCG = `0.8069`

Latent-only:
- top1 max-tier hit = `1.0000`
- top1 solved hit = `0.8649`
- mean NDCG = `0.9901`
- mean judge pair calls = `0.0`

Judge-only:
- top1 max-tier hit = `1.0000`
- top1 solved hit = `0.8649`
- mean NDCG = `1.0000`
- mean judge pair calls = `15.0`

Hybrid:
- top1 max-tier hit = `1.0000`
- top1 solved hit = `0.8649`
- mean NDCG = `0.9901`
- mean judge pair calls = `1.0811`
- judge-cost ratio vs judge-only = `0.0721`

#### DeepSeek hard-only sanity check (`k = 4`, Putnam subsets only)

- latent-only:
  - top1 max-tier hit = `0.1111`
  - top1 solved hit = `0.0000`
- judge-only:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`
- hybrid:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`

#### Goedel

##### `k = 4`

Baseline:
- top1 max-tier hit = `0.3991`
- top1 solved hit = `0.1810`
- mean NDCG = `0.8607`

Latent-only:
- top1 max-tier hit = `0.9211`
- top1 solved hit = `0.7309`
- mean NDCG = `0.9784`
- mean judge pair calls = `0.0`

Judge-only:
- top1 max-tier hit = `0.9977`
- top1 solved hit = `0.7401`
- mean NDCG = `0.9995`
- mean judge pair calls = `6.0`

Hybrid:
- top1 max-tier hit = `0.9304`
- top1 solved hit = `0.7309`
- mean NDCG = `0.9804`
- mean judge pair calls = `0.8213`
- judge-cost ratio vs judge-only = `0.1369`

##### `k = 6`

Baseline:
- top1 max-tier hit = `0.2072`
- top1 solved hit = `0.0811`
- mean NDCG = `0.8069`

Latent-only:
- top1 max-tier hit = `0.9459`
- top1 solved hit = `0.8649`
- mean NDCG = `0.9775`
- mean judge pair calls = `0.0`

Judge-only:
- top1 max-tier hit = `1.0000`
- top1 solved hit = `0.8649`
- mean NDCG = `1.0000`
- mean judge pair calls = `15.0`

Hybrid:
- top1 max-tier hit = `0.9459`
- top1 solved hit = `0.8649`
- mean NDCG = `0.9775`
- mean judge pair calls = `1.0811`
- judge-cost ratio vs judge-only = `0.0721`

#### Goedel hard-only sanity check (`k = 4`, Putnam subsets only)

- latent-only:
  - top1 max-tier hit = `0.4444`
  - top1 solved hit = `0.1111`
- judge-only:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`
- hybrid:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`

### Interpretation

This result sharpens the practical role of the current system, but only after correcting for panel composition.

#### 1. Latent-only is already very strong in the easy-heavy search-like regime

Even on exact `k`-candidate subsets, latent-only is far above baseline across both models and both budgets.

So the round61 utility result was not an artifact of evaluating the full candidate pool.

But the stronger statement must be weakened:
- it **is** partly an artifact of evaluating a subset family dominated by easy states
- it does **not** show hard-Putnam latent reranking becoming strong

#### 2. Judge-only still gives the strongest ranking quality

Judge-only remains the best method overall, especially on:
- max-tier hit
- NDCG

This is consistent with the harder-domain findings from rounds 55–60.

#### 3. Hybrid gives a strong quality-cost tradeoff in the mixed regime

The key practical result is:

- for `k = 4`, hybrid uses only `13.69%` of judge-only pairwise judge calls
- for `k = 6`, hybrid uses only `7.21%` of judge-only pairwise judge calls

while preserving most of the ranking quality.

DeepSeek is the clearest positive case on the mixed easy-heavy panel:
- at `k = 4`, hybrid exactly matches judge-only on `top1 solved hit`
- at `k = 6`, hybrid matches judge-only on both `top1 max-tier hit` and `top1 solved hit`
- with `86%–93%` fewer judge pair calls

Goedel is weaker:
- hybrid saves the same judge budget
- but adds little over latent-only on these subset metrics

So the mixed-panel hybrid story is real, but:
- model-dependent in strength
- and still mostly driven by easy states in this budgeted protocol

#### 4. The right use is now clearer

The system role is not:
- use judge everywhere
- or hope latent replaces judge on hard states

It is:
- latent for cheap local reranking
- trust gate for deciding when local latent is likely unsafe
- sparse judge use for the remaining difficult states

### Conclusion

Round62 strengthens the conversion result from round61, but with an important scope correction:

- the current hybrid is not only better than latent-only in aggregate full-pool reranking
- it also gives a real quality-cost tradeoff in a more search-like `k`-candidate setting

The strongest current reading is:

**latent + trust + sparse judge** is a plausible system pattern in the current mixed/easy-heavy regime, even though latent alone is still not a universal hard-domain judge.
