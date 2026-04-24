# CIVIC-PRM: Auditing Answer-Sensitive Shortcuts in Process Verifiers

## Abstract

Process verifiers are often evaluated with ordinary discrimination metrics, but these scores do not reveal whether the verifier is actually using local process validity or instead relying on answer-consistency shortcuts. We study answer-visible process verification as an audit problem and introduce an evaluation protocol centered on answer-matched counterfactual discrimination (`AMCD`) and answer-swap sensitivity (`ASS`). We build executable matched-quartet benchmarks over algebra, graph path, and blocksworld-style planning domains, and we distinguish two evaluation regimes: a deployment-oriented naturalized generated slice and a cleaner benchmark-v3 mid-scale audit slice accepted under a proposal-aligned artifact criterion. Across prompt judges, external judges, frozen-backbone heads, minimal repair objectives, and stronger rerankers, we find four main results. First, judge-style evaluators are strongly answer-sensitive and weak on answer-matched local discrimination. Second, `AMCD` tracks downstream utility much better than ordinary AUROC, and local answer sensitivity harms utility primarily through lower local `AMCD`. Third, stronger model scale does not make answer-visible verification safe by default: on the deployment-oriented naturalized generated slice, the best current model is a masked `Qwen3-Reranker-8B`, which outperforms visible reranking and frozen-head baselines on `AMCD`, selection gain, exploitability, robustness, and seed-averaged reproduction. Fourth, on the cleaner benchmark-v3 audit slice, masked reranking still improves `AMCD` and sharply lowers `ASS`, but no longer gains extra selection utility over visible reranking; this suggests the new benchmark is a cleaner process-faithfulness test rather than a direct exploitability surrogate. Minimal conditional-invariance repairs improve faithfulness on some slices but do not uniformly dominate a strong answer-masked baseline, yielding a faithfulness-utility frontier rather than a universal repair win. These results support answer-invariant auditing as a necessary prerequisite for deploying process verifiers in reranking and compute-control pipelines.

## 1. Introduction

Process verifiers are widely used as if a high verification score implied genuine sensitivity to reasoning quality. In practice, however, an answer-visible verifier can mix at least two different signals: whether the local reasoning process is valid, and whether the full trace looks consistent with a correct final answer. This distinction matters because downstream systems such as reranking, search, and compute control depend on the verifier as if it were process-grounded. If the verifier is instead leaning on answer-sensitive shortcuts, then good average scores may mask brittle behavior under counterfactual perturbations.

This paper studies answer-visible process verification as an audit problem rather than as a pure model-improvement problem. The goal is not to build an arbitrarily complex process reward model, but to turn verifier behavior into something falsifiable: a system whose dependence on answer information can be isolated, measured, stress-tested, and, when possible, partially reduced. Our proposal therefore centers on three ingredients: a counterfactual benchmark built from executable domains, an audit protocol based on answer-matched local discrimination (`AMCD`) and answer-swap sensitivity (`ASS`), and a small family of minimal repair objectives that try to improve process grounding without simply suppressing all answer-related information.

The main empirical finding is not that a simple repair term fully solves leakage. Instead, the strongest and most stable conclusion is methodological and deployment-oriented. `AMCD` tracks downstream utility better than ordinary AUROC; judge-style evaluators are strongly answer-sensitive; and the strongest current deployment model is not an answer-visible verifier at all, but a stronger reranker used in the masked condition. At the same time, a cleaner benchmark-v3 audit slice shows that removing answer access continues to help even when utility no longer separates. In other words, scaling helps, but it helps most when direct answer access is removed, and different benchmark regimes expose different parts of that story.

### 1.1 Contributions

Our contributions are fourfold.

- We introduce an audit protocol for answer-visible process verification built around `AMCD`, `ASS`, and strong same-backbone masked baselines rather than ordinary discrimination alone.
- We show that the strongest current deployment configuration is a masked reranker, while judge-style evaluators and visible rerankers remain substantially answer-sensitive.
- We provide mechanism evidence that local answer sensitivity harms utility primarily through lower local process discrimination, rather than merely co-occurring with it.
- We develop a benchmark package that now has two complementary regimes: a deployment-oriented naturalized generated slice and a cleaner benchmark-v3 audit slice accepted under a proposal-aligned artifact criterion.

## 2. Problem Setup

We study process verification in audited executable domains. Each example has a problem statement, a reasoning trace, and a marked audited locus indicating the local step whose validity is scientifically relevant. The core distinction is between two input settings:

- `answer-visible`: the verifier sees the full trace including the final answer line
- `answer-masked`: the verifier sees the same trace with the answer line masked

The central question is whether verifier scores reflect local process validity or whether they are materially distorted by answer-sensitive behavior.

### 2.1 Step Validity And Matched Counterfactuals

Each benchmark item is derived from an executable latent trajectory. We construct matched quartets with two orthogonal axes:

- process validity: `valid` vs `invalid`
- answer surface: `correct` vs `swapped`

This yields the minimal quartet:

- `valid_correct`
- `invalid_correct`
- `valid_swapped`
- `invalid_swapped`

The point of this construction is that the verifier can be tested under answer-matched local comparisons. A model that simply prefers traces with a correct-looking answer will fail this test.

### 2.2 Metrics

We use the following metrics throughout the paper:

- `ordinary_auroc`: ordinary valid-vs-invalid discrimination over all traces
- `AMCD`: answer-matched counterfactual discrimination, which asks whether a verifier prefers `valid` over `invalid` when the answer surface is held fixed
- `ASS_total`: average score change under answer-swap interventions
- `selection_gain_at4`: improvement over random top-of-quartet selection
- `exploitability_rate`: how often the top-ranked trace is an invalid-but-lucky one

These metrics serve different purposes. `ordinary_auroc` captures global separability, `AMCD` captures local process grounding, and `ASS_total` measures direct sensitivity to answer swapping. The downstream metrics test whether these audit signals matter operationally.

## 3. Benchmark And Audit Protocol

### 3.1 CRAFT-Core

The benchmark begins with three executable domains:

- algebra
- graph path
- blocksworld-like planning

We verbalize each problem into natural-language reasoning traces and construct matched counterfactual families around the audited locus. The benchmark focuses on executable, auditable settings because the goal is to isolate verifier failure modes cleanly before making stronger natural-language generalization claims.

### 3.2 Counterfactual Families

The core families are:

- `local-invalid`: the process is changed locally near the audited locus
- `answer-swap`: the process is kept fixed while the final answer surface changes
- `lucky-answer`: an invalid process is paired with a correct-looking final answer
- `paraphrase`: the language surface changes while semantics are preserved

`Delayed-repair` is treated as a stress slice rather than part of the core benchmark, because it mixes local invalidity with later trajectory recovery.

### 3.3 Artifact Audit

Each benchmark stage is filtered through artifact checks. The first hard slice passes shallow-feature audit without obvious style leakage, for example with `validity_style_accuracy = 0.4385` and `length_only_validity_accuracy = 0.4769`, both close to chance. Later, benchmark-v3 is accepted under a narrower, proposal-aligned criterion: artifact-clean audited counterfactuals rather than universal human-indistinguishable pairs. Under that criterion, the mid-scale benchmark-v3 export reaches `52 / 54` accepted families and `208` records after deterministic acceptance correction.

The human blind audit packet exists, but the external human review is still pending. We therefore treat the benchmark package as strongly audited by automated checks and internal protocol checks, while keeping external human validation as an explicit open gate. The hidden-key scoring pipeline is already in place, so the remaining blocker is reviewer return rather than local execution infrastructure.

### 3.4 Two Benchmark Regimes

The project now reports two benchmark regimes on purpose rather than by accident.

- The naturalized full-hybrid generated slice is the main deployment benchmark. It is the right regime for asking whether a verifier or reranker will improve selection quality and reduce exploitability under realistic distribution shift.
- Benchmark-v3 mid-scale is the cleaner audit benchmark. It is accepted under a proposal-aligned artifact criterion and is more useful for isolating process-faithfulness gaps than for maximizing utility separation.

These regimes should not be merged into a single headline score. They answer different questions, and that difference is now part of the paper's claim rather than a nuisance variable.

## 4. Experimental Stages

### 4.1 Judge-Style Evaluators

We first test local prompt judges and an external API judge. These are useful because they resemble how process evaluation is often deployed in practice, but they are weak scientific instruments for local process grounding. Across easy, hard, and naturalized slices, they show the same qualitative pattern: high answer sensitivity and weak `AMCD`.

This matters because it establishes an early distinction that persists throughout the project: judge-style leakage is real, but it should not be conflated with the behavior of trained verifiers.

### 4.2 Same-Backbone Frozen-Head Baselines

The next stage uses a frozen `Qwen3-1.7B` backbone with small learned heads:

- `visible_bce`
- `masked_bce`
- `pairwise_visible`
- `step_only`

These baselines are the first place where the proposal’s Risk 3 becomes active. On early synthetic slices, the answer-masked baseline is already very strong. This is a critical result because it prevents us from overstating the necessity of more complex repair objectives.

### 4.3 Minimal Repairs

We then test minimal repair variants:

- `local-pair`
- `cond-swap`
- `hard-neg`
- minimal and step-scan dual-head variants

The best story here is limited but real. `visible_cond_swap` can improve faithfulness and sometimes `AMCD`, especially on structured hard OOD slices. However, no simple repair variant uniformly dominates the masked baseline across naturalized OOD. The resulting picture is a faithfulness-utility frontier rather than a universal repair win.

### 4.4 Stronger Rerankers

Week 4 moves beyond frozen linear heads to stronger local rerankers:

- `Qwen3-Reranker-8B`
- `Qwen3-Reranker-4B`

These models change the deployment picture materially. The strongest current model is `Qwen3-Reranker-8B` in the masked setting, not a visible reranker and not a frozen-head repair.

## 5. Main Results

### 5.1 Main Table

Our recommended main slice is the naturalized full-hybrid generated benchmark:

- tri-domain
- model-generated origin
- auditable counterfactual structure
- naturalized surface shift
- deployment-relevant reranking setting

On this slice, the seed-averaged main comparison set is:

| model | ordinary_auroc | amcd | ass_total | selection_gain_at4 | exploitability_rate |
|---|---:|---:|---:|---:|---:|
| reranker8_masked | 0.6795 | 0.8529 | 0.0184 | 0.3824 | 0.0588 |
| masked_bce | 0.5969 | 0.7647 | 0.1041 | 0.2647 | 0.1765 |
| pairwise_visible | 0.5753 | 0.7353 | 0.0848 | 0.2059 | 0.2941 |
| visible_bce | 0.5926 | 0.7059 | 0.0941 | 0.2647 | 0.2353 |
| visible_cond_swap | 0.5640 | 0.7059 | 0.0377 | 0.2059 | 0.2353 |
| reranker8_visible | 0.5398 | 0.5294 | 0.2128 | 0.3235 | 0.1765 |

This table supports three immediate conclusions.

First, the best current deployment model is `reranker8_masked`.

Second, stronger scale does not remove the answer-leakage problem in the visible setting. The visible reranker is worse than the masked reranker on both `AMCD` and `ASS_total`.

Third, the best frozen-head repair, `visible_cond_swap`, improves answer invariance relative to other visible frozen-head baselines but still trails the masked reranker on the main table.

### 5.2 Bootstrap Comparisons

The cleanest comparison is `reranker8_masked` vs `reranker8_visible`:

- `ordinary_auroc` difference: `+0.1397`, CI `[0.0644, 0.2608]`
- `amcd` difference: `+0.3235`, CI `[0.1818, 0.4583]`
- `ass_total` difference: `-0.1944`, CI `[-0.2485, -0.1355]`

The masked reranker also beats the strongest repair baseline:

`reranker8_masked` vs `visible_cond_swap`

- `ordinary_auroc` difference: `+0.1155`, CI `[0.0419, 0.2102]`
- `amcd` difference: `+0.1470`, CI `[0.0454, 0.2500]`
- `ass_total` difference: `-0.0193`, CI `[-0.0278, -0.0108]`

These intervals make the current deployment conclusion substantially harder to dismiss as a one-run artifact.

### 5.3 Secondary Benchmark: Benchmark-V3 Mid-Scale

The naturalized full-hybrid slice remains our main deployment benchmark, but it is not the only regime we report. On the benchmark-v3 mid-scale audit slice, the comparison shifts in an informative way.

For `Qwen3-Reranker-8B`:

- visible: `ordinary_auroc = 0.5524`, `amcd = 0.6058`, `ass_total = 0.1344`, `selection_gain_at4 = 0.3889`, `exploitability_rate = 0.1111`
- masked: `ordinary_auroc = 0.5589`, `amcd = 0.6731`, `ass_total = 0.0438`, `selection_gain_at4 = 0.3889`, `exploitability_rate = 0.1111`

The masked reranker still wins on process-facing metrics, but the utility edge disappears. This is useful rather than contradictory. It shows that benchmark-v3 behaves as a cleaner process-faithfulness benchmark, whereas the naturalized full-hybrid slice is more deployment-like and more sensitive to exploitability consequences.

A benchmark-v3-specific reproduction pass reaches the same conclusion. Across `3` seeds, the quartet-protocol frozen-head baselines remain strong but do not overturn the masked-vs-visible reranker readout: mean quartet `amcd` is `0.9028` for `visible_bce`, `0.9213` for `masked_bce`, and `0.9028` for `pairwise_visible`, while paired bootstrap on the same reranker rows gives `amcd` diff `+0.0673` for masked over visible with CI `[0.0, 0.1406]` and `ass_total` diff `-0.0906` with CI `[-0.1177, -0.0641]`. Utility still does not separate (`selection_gain_at4` diff `0.0`, `exploitability_rate` diff `0.0`), which again confirms that benchmark-v3 is a cleaner process-faithfulness regime rather than a deployment exploit surrogate.

The same benchmark-v3 run also changes the frozen-head picture. `step_only_bce`, `visible_bce`, `masked_bce`, and `pairwise_visible` are all much stronger than they were on the older hard synthetic benchmark, and the main weak slice shifts toward graph path rather than blocksworld. This confirms that benchmark replacement is not only a dataset-path change; it creates a genuinely different evaluation regime.

The benchmark-v3 robustness summary reinforces the same interpretation rather than changing it. Under the mixed visible-attacker ensemble, `reranker8_masked` is still slightly more stable than `reranker8_visible` (`pairwise_attack_win_rate = 0.1324` vs `0.1618`), but the attacked-quartet utility is identical (`selection_gain_at4 = 0.4091`, `exploitability_rate = 0.0909`) for both views. The main weak slices also shift: for `reranker8_masked`, algebra and graph path are now the weaker domains (`amcd = 0.5556` and `0.625`), while blocksworld is no longer the dominant failure slice on the cleaner benchmark. This is consistent with benchmark-v3 being a faithfulness benchmark first, not a deployment exploit benchmark in disguise.

## 6. Mechanism Evidence

The strongest support for the proposal is not “repair wins everywhere,” but the mechanism chain linking answer sensitivity, local process discrimination, and downstream utility.

Across pooled head-level points:

- `corr(AMCD, selection_gain_at4) = 0.8778`
- `corr(AMCD, exploitability_rate) = -0.7724`
- `corr(ordinary_auroc, selection_gain_at4) = 0.4659`
- `corr(ordinary_auroc, exploitability_rate) = -0.0104`

This is already enough to show that `AMCD` is much closer to downstream utility than ordinary AUROC.

The local analysis is stronger still:

- `corr(local_ASS, local_AMCD) = -0.2851`
- `corr(local_ASS, selection_gain_at4) = -0.2758`
- `corr(local_ASS, exploitability_rate) = 0.2726`
- `corr(local_AMCD, selection_gain_at4) = 0.8475`
- `corr(local_AMCD, exploitability_rate) = -0.6662`

The local mediation estimates are directionally aligned with the proposal:

- for `selection_gain_at4`, indirect effect through local `AMCD` is `-0.8559`
- for `exploitability_rate`, indirect effect through local `AMCD` is `0.5770`

The cleanest reading is that answer sensitivity is harmful not merely because it exists, but because it damages local process discrimination, and this damage is what propagates to utility.

## 7. Robustness

### 7.1 Transfer

Week 5 shows that the visible-vs-masked reranker gap survives transfer checks.

For `Qwen3-Reranker-8B` visible:

- hard synthetic: `amcd = 0.6667`
- structured generated: `amcd = 0.3235`
- naturalized generated: `amcd = 0.5294`

For `Qwen3-Reranker-8B` masked:

- hard synthetic: `amcd = 0.7546`
- structured generated: `amcd = 0.8235`
- naturalized generated: `amcd = 0.8529`

The visible reranker is more brittle under generated OOD, while the masked reranker stays strong and low-sensitivity.

### 7.2 Multi-Attacker Transfer

We evaluate self attackers, cross-family attackers, and a mixed visible-attacker ensemble. The strongest current target, `reranker8_masked`, remains robust under these attacks.

Against the mixed visible-attacker ensemble:

- `pairwise_attack_win_rate = 0.1944`
- `quartet_top_attack_rate = 0.1111`
- attacked-quartet `selection_gain_at4 = 0.3333`
- attacked-quartet `exploitability_rate = 0.0833`

For comparison, `reranker8_visible` under the same mixed attacker has attacked-quartet `exploitability_rate = 0.25`, and `visible_cond_swap` also remains at `0.25`. This is strong evidence that masked deployment is not only better on average but also more robust under transfer from visible-family failures.

### 7.3 Worst-Group Slices

The main remaining weak slice for the best current model is planning-style naturalized blocksworld:

- `reranker8_masked` on naturalized blocksworld: `ordinary_auroc = 0.6875`, `amcd = 0.5833`, `ass_total = 0.0075`

By contrast, the same model is much stronger on naturalized algebra and graph path:

- algebra: `ordinary_auroc = 0.9167`, `amcd = 1.0`
- graph_path: `ordinary_auroc = 0.82`, `amcd = 1.0`

This makes the remaining weakness concrete. The project does not end in a generic “OOD is hard” statement; it ends with a specific remaining problem: planning-style naturalized traces are still the most difficult deployment slice.

## 8. What The Paper Should Claim

The strongest defensible claim is:

> answer-visible process verification should be audited with answer-matched counterfactuals; `AMCD` is more aligned with downstream utility than ordinary AUROC; and stronger reranking works best when direct answer access is removed.

This claim is strongly supported by the current evidence.

By contrast, the paper should not claim:

- that all trained verifiers are dominated by outcome leakage
- that a simple repair term fully solves leakage
- that the current dual-head formulation successfully disentangles process and consistency at this scale

The dual-head results are informative negative results, not a positive mechanism story.

## 9. Limitations

The first limitation is scope. The strongest results are on audited executable domains and naturalized/model-generated transfer built around those domains. The paper should not overclaim broad open-domain generality.

The second limitation is that the benchmark story remains layered. The benchmark-v3 replacement path is now usable at mid-scale under the proposal-aligned acceptance rule, but the external human blind audit is still pending. We therefore treat benchmark-v3 as a usable audited benchmark package rather than a fully closed replacement benchmark.

The third limitation is calibration. Week 4 and Week 5 include `ECE / Brier / AURC`, but the strongest improvements are on ranking and exploitability rather than probability calibration. Calibration should therefore remain a secondary downstream result.

## 10. Conclusion

This project began as a proposal about outcome leakage in process verifiers. The strongest final result is slightly different from the strongest initial algorithmic hope, but scientifically stronger. We now have an audited counterfactual protocol, a mechanism story linking answer sensitivity to local process discrimination and utility, a robustness package over transfer and attacker families, a deployment-oriented benchmark where masked reranking is clearly best, and a cleaner benchmark-v3 audit slice where masked reranking still wins on process-faithfulness even when utility no longer separates. This is enough to support a clear conclusion: answer-visible process verification should not be trusted on ordinary metrics alone. It should first be audited with answer-matched counterfactuals, and in the current setting, the safest deployment path is to remove direct answer access rather than assume model scale will disentangle the signals automatically.

## Final Insertions Before Submission

- insert the final external blind-audit result once reviewer CSVs return
- compress calibration into an appendix table
- keep dual-head and replay ablations in appendix
- add final figure captions and venue-specific bibliography / formatting
