# Paper Outline Draft

## Candidate Titles

1. `CIVIC-PRM: Auditing Answer-Sensitive Shortcuts in Process Verifiers`
2. `Answer-Invariant Verification for Process Reward Models`
3. `When Process Verifiers Look at the Answer: Auditing with Answer-Matched Counterfactuals`

## One-Paragraph Abstract

Process verifiers are often evaluated with ordinary discrimination metrics, but these scores do not reveal whether the verifier is actually using local process validity or instead relying on answer-consistency shortcuts. We study answer-visible process verification as an audit problem and introduce an evaluation protocol centered on answer-matched counterfactual discrimination (`AMCD`) and answer-swap sensitivity (`ASS`). On audited executable domains spanning algebra, graph path, and blocksworld, we distinguish a deployment-oriented naturalized generated benchmark from a cleaner benchmark-v3 audit slice accepted under a proposal-aligned artifact criterion. Across both regimes, judge-style evaluators are strongly answer-sensitive, while trained verifiers are more process-grounded but still vulnerable under distribution shift. Minimal conditional-invariance repairs improve faithfulness on some slices but do not uniformly dominate a strong answer-masked baseline, yielding a faithfulness-utility frontier. Moving to a stronger reranker changes the deployment picture: the best current model is a masked `Qwen3-Reranker-8B`, which outperforms visible reranking and frozen-head baselines on the deployment benchmark, while benchmark-v3 confirms a cleaner process-faithfulness gap even when utility no longer separates. These results support answer-invariant auditing as a necessary prerequisite for deploying process verifiers in reranking and compute-control pipelines.

## Tight Claim Version

The paper should claim:

- answer-visible process verification should be audited with answer-matched counterfactuals
- `AMCD` is more aligned with downstream utility than ordinary AUROC
- answer-sensitive behavior is severe in judge-style evaluators
- stronger reranking works best when answer access is removed
- benchmark-v3 should be framed as a complementary cleaner audit benchmark, not as a silent replacement for the deployment slice

The paper should not claim:

- that all trained verifiers are dominated by outcome leakage
- that a simple repair term fully solves leakage
- that dual-head disentanglement already succeeds at the current scale

## Section Outline

### 1. Introduction

- Motivation:
  ordinary verifier scores can look good while local process grounding is weak
- Core problem:
  answer-visible verification mixes process validity and answer consistency
- Main idea:
  audit this mixture with answer-matched counterfactuals and minimal invariance
- Main findings:
  - `AMCD` tracks utility better than ordinary AUROC
  - judge-style evaluators are highly answer-sensitive
  - stronger masked reranking is the best current deployment choice

### 2. Problem Setup

- step validity and audited locus
- answer-visible vs answer-masked verification
- `G_proc`, `G_cons`, `G_total`
- claim boundary: audited executable domains first, naturalized/model-generated transfer as supporting evidence

### 3. Benchmark And Audit Protocol

- CRAFT-Core domains
- quartet construction
- artifact audit and proposal-aligned benchmark acceptance
- secondary benchmark-v3 acceptance rule:
  artifact-clean audited benchmark, not universal human-indistinguishable pairs
- primary metrics:
  - `AMCD`
  - `ASS_total`
- downstream metrics:
  - selection gain @ 4
  - exploitability rate
  - calibration appendix metrics

### 4. Baselines And Minimal Repairs

- same-backbone `visible_bce`
- same-backbone `masked_bce`
- same-backbone `pairwise_visible`
- judge-style baselines
- minimal repairs:
  - `local-pair`
  - `cond-swap`
  - `hard-neg`
  - dual-head negative results

### 5. Main Results

- main table on naturalized full-hybrid
- secondary benchmark-v3 table or boxed comparison
- visible vs masked reranker
- frozen-head comparison set
- paired bootstrap intervals

### 6. Mechanism And Robustness

- `ASS -> AMCD -> utility` mechanism analysis
- Week 5 transfer summary
- mixed-attacker transfer
- worst-group slices

### 7. Discussion

- strongest supported claim
- why the result is more about auditing and disentangling than about a universally best repair
- remaining weak slice: naturalized blocksworld
- why benchmark-v3 behaves as a process-faithfulness benchmark rather than an exploitability surrogate
- calibration is secondary

### 8. Limitations

- external human blind audit still pending, including the replacement benchmark
- claim boundary remains audited executable domains
- current dual-head result is negative at this scale
- benchmark-v3 is accepted under a proposal-aligned criterion, while universal strict pair indistinguishability remains a diagnostic only

## Recommended Figure / Table Map

### Main Table

- [main_table.md](/cephfs/luyanzhen/apg/civic-prm/history/main_table.md)

### Secondary Benchmark Table

- benchmark-v3 mid-scale visible vs masked reranker
- benchmark-v3 frozen-head quartet comparison

### Figure 1

- quartet construction and answer-swap / local-invalid families

### Figure 2

- mechanism plot:
  `AMCD` vs selection gain
  `AMCD` vs exploitability

### Table 2

- Week 5 transfer and mixed-attacker robustness

### Appendix Table A

- calibration (`ECE / Brier / AURC`)

### Appendix Table B

- seed table and bootstrap intervals

### Appendix Table C

- verbalizer and worst-group slices

## Writing Status

- `paper_draft.md` exists and already carries the dual-benchmark framing.
- `main_table.md` remains the primary deployment table.
- `final_summary.md` is the authoritative claim hierarchy and benchmark status note.
- The remaining writing task is no longer core restructuring. It is mainly:
  - insert the final external blind-audit result once reviewer CSVs return
  - do venue-specific prose / figure / bibliography polish
