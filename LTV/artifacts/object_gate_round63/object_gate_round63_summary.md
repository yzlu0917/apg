## Round63: Hard-aware stratified budgeted evaluation confirms that round62 was easy-dominated

### Goal

Re-run the budgeted reranking story with a protocol that does not let easy states dominate the result.

Instead of pooling all exact `k`-candidate subsets together, split by:
- `easy`
- `putnam`

and report **state-balanced macro averages**.

This directly answers the concern that round62's very high latent-only `top1` numbers might be caused by panel composition rather than real hard-domain utility.

### Inputs

Round61 mixed-panel ranking outputs:
- [deepseek_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/deepseek_hybrid_reranking.json)
- [goedel_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/goedel_hybrid_reranking.json)

Round57 trust predictions:
- [deepseek_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/deepseek_trust_gating.json)
- [goedel_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/goedel_trust_gating.json)

Implementation:
- [evaluate_stratified_budgeted_hybrid.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_stratified_budgeted_hybrid.py)

Outputs:
- [deepseek_stratified_budgeted.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round63/deepseek_stratified_budgeted.json)
- [goedel_stratified_budgeted.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round63/goedel_stratified_budgeted.json)

### Protocol

Two corrections over round62:

1. **Split by regime**
- `easy`
- `putnam`

2. **State-balanced reporting**
- for each state, average over all exact `k`-candidate subsets
- then macro-average across states

Valid hard-side budgets are:
- `k = 3`
- `k = 4`

because Putnam candidate counts are:
- `5, 4, 4, 4, 4, 3, 3`

Methods:
- `latent_only`
- `judge_only`
- `hybrid_hard_gate_centroid`

### Results

#### DeepSeek, Putnam-only

`k = 3`:
- latent-only:
  - top1 max-tier = `0.3429`
  - top1 solved = `0.0000`
  - mean NDCG = `0.7984`
  - mean judge calls = `0.0`
- judge-only:
  - top1 max-tier = `0.8929`
  - top1 solved = `0.1071`
  - mean NDCG = `0.9781`
  - mean judge calls = `3.0`
- hybrid:
  - top1 max-tier = `0.8929`
  - top1 solved = `0.1071`
  - mean NDCG = `0.9781`
  - mean judge calls = `3.0`

`k = 4`:
- latent-only:
  - top1 max-tier = `0.0400`
  - top1 solved = `0.0000`
  - mean NDCG = `0.7204`
  - mean judge calls = `0.0`
- judge-only:
  - top1 max-tier = `0.8000`
  - top1 solved = `0.2000`
  - mean NDCG = `0.9587`
  - mean judge calls = `6.0`
- hybrid:
  - top1 max-tier = `0.8000`
  - top1 solved = `0.2000`
  - mean NDCG = `0.9587`
  - mean judge calls = `6.0`

#### Goedel, Putnam-only

`k = 3`:
- latent-only:
  - top1 max-tier = `0.5643`
  - top1 solved = `0.1071`
  - mean NDCG = `0.8859`
  - mean judge calls = `0.0`
- judge-only:
  - top1 max-tier = `0.8929`
  - top1 solved = `0.1071`
  - mean NDCG = `0.9781`
  - mean judge calls = `3.0`
- hybrid:
  - top1 max-tier = `0.8929`
  - top1 solved = `0.1071`
  - mean NDCG = `0.9781`
  - mean judge calls = `3.0`

`k = 4`:
- latent-only:
  - top1 max-tier = `0.4800`
  - top1 solved = `0.2000`
  - mean NDCG = `0.8668`
  - mean judge calls = `0.0`
- judge-only:
  - top1 max-tier = `0.8000`
  - top1 solved = `0.2000`
  - mean NDCG = `0.9587`
  - mean judge calls = `6.0`
- hybrid:
  - top1 max-tier = `0.8000`
  - top1 solved = `0.2000`
  - mean NDCG = `0.9587`
  - mean judge calls = `6.0`

#### Easy-only sanity check

Easy-side results remain strong and consistent with round62:

DeepSeek:
- easy `k = 4` latent-only top1 max-tier = `0.9950`
- easy `k = 4` hybrid top1 max-tier = `0.9950`
- easy `k = 4` hybrid mean judge calls = `0.7059` vs judge-only `6.0`

Goedel:
- easy `k = 4` latent-only top1 max-tier = `0.9723`
- easy `k = 4` hybrid top1 max-tier = `0.9723`
- easy `k = 4` hybrid mean judge calls = `0.7059` vs judge-only `6.0`

### Interpretation

This round fixes the main ambiguity in round62.

#### 1. Round62 was indeed easy-dominated

The concern was correct:
- the huge latent-only `top1` values in round62 were largely driven by easy states and subset combinatorics
- they should not be read as hard-domain budgeted success

#### 2. Hard Putnam still preserves the earlier boundary

On Putnam-only subsets:
- latent-only remains weak
- judge-only remains strong
- hybrid matches judge-only because the trust gate effectively routes the hard states to judge

So round63 does **not** overturn rounds 55–60.

#### 3. The trust gate is still useful, but its role is now sharper

On the current hard slice, hybrid is not “latent plus a little judge”.
It is effectively:

- easy states -> latent
- hard Putnam states -> judge

That is still a valid and useful system behavior, but it is a different claim from:
- “latent remains strong under budget on hard states”

#### 4. The real utility split is now clearer

Current best reading:
- easy/medium:
  - latent reranking is strong
  - hybrid keeps quality while using very little judge
- hard Putnam:
  - latent reranking is still weak
  - hybrid works because trust correctly escalates to judge

### Conclusion

Round63 is a correction round, not a failure round.

It shows that:
- round62's aggregate budgeted result was too optimistic if read as a hard-domain story
- but the deeper hybrid picture still holds

The accurate system conclusion is now:

**latent + trust + sparse judge** is useful because it separates regimes correctly, not because latent has suddenly become a strong hard-domain ranker.
