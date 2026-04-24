# Benchmark-V3 Rethink Note

Date: 2026-03-10

## Why This Exists

The current project is conditionally closed on the modeling side, but not on the benchmark side.

What failed in the `benchmark-v2` branch is now clearer:

- `q2f`: best blind-audit-facing packet, but incomplete coverage
- `q2h`: better coverage, still not better blind review
- `q2i`: more natural source invalidity, but rewrite coverage collapses
- `q2j`: perfect coverage, but human reviewers spot the invalid traces even more easily

The bottleneck is therefore no longer "can we generate the data?" but:

- can we get enough coverage,
- preserve enough semantic faithfulness,
- and still avoid making invalid traces too easy for human/LLM reviewers to detect?

## Recommended Next-Phase Direction

If benchmark work continues, it should be treated as a new `benchmark-v3` project rather than another `q2*` patch round.

Recommended direction:

1. stronger model for benchmark generation
2. multi-candidate generation per latent trace
3. reviewer-in-the-loop rejection
4. adversarial filtering against a blind reviewer model or human proxy
5. a small amount of manually curated invalid traces if needed

## Recommended Pipeline

### 1. Latent executable backbone stays programmatic

Keep:

- executable domains
- audited loci
- quartet semantics
- deterministic validity checks

Do **not** switch to pure free-form LLM self-labeling.

### 2. Stronger generation model

Use a stronger model than the current local rewrite path for surface realization and invalid-trace realization.

Reason:

- the current model can either preserve the wrong local step or make the result sound natural, but not both reliably

### 3. Multi-candidate generation

For each latent trace:

- generate `k` candidate rewrites for valid
- generate `k` candidate rewrites for invalid

Then filter by:

- deterministic semantic checks
- quartet completeness
- surface diversity

This is likely better than trying to get one-shot perfect rewrites.

### 4. Reviewer-in-the-loop rejection

Blind-detectability should become a first-class filter.

Candidate protocol:

- sample a small blind-review packet from the candidate pool
- have a human or strong reviewer model mark "obvious synthetic / patched" traces
- reject candidate families that are consistently easy to spot

This is different from ordinary artifact audit. The target is not only shallow style leakage; it is reviewer detectability.

### 5. Adversarial filtering

Add a reviewer model or blind-judge proxy whose job is:

- given two traces with hidden labels, predict which one is more artificial

Then keep only quartets where:

- the reviewer confidence is low
- or the reviewer is unstable across paraphrases / reorderings

This would make benchmark creation closer to adversarial data collection than to static templating.

### 6. Small manual curated set

If algebra-like domains remain brittle, use a small manually curated invalid set rather than forcing everything through the same automatic rewrite stack.

This is acceptable if:

- it is clearly labeled as curated
- it is small
- it is used as a benchmark slice, not hidden as if it were automatic generation

## What Not To Do

- do not keep optimizing only shallow style AUROC
- do not treat perfect rewrite coverage as sufficient
- do not treat exact semantic faithfulness as automatically good for blind audit
- do not keep extending the current `q2*` line indefinitely

## Success Criterion For Benchmark-V3

A stronger replacement benchmark should only be considered successful if it clears all three:

1. executable / deterministic validity closure
2. adequate coverage across all target domains
3. substantially improved blind-audit behavior

Without the third condition, benchmark-v3 should still be treated as unresolved.

## Initial Strict Smoke Status

The project has now completed a first strict smoke under:

- `2` candidates per role
- masked reviewer filtering
- full Cartesian family selection
- `1` quartet per domain

Artifacts:

- `data/generated/craft_core_benchmark_v3_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_smoke_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_internal_review.md`

What the smoke establishes:

- the `benchmark-v3` construction path is technically live
- reviewer-aware family selection is feasible
- answer-visible reviewer filtering was a real bug and had to be removed

What it does **not** establish:

- that the current selector is strict enough
- that the selected families are already blind-clean
- that the project should scale this pipeline up unchanged

Current read:

- the next step is selector redesign, not immediate scale-up
- the main likely changes are:
  - hard detectability thresholds
  - reviewer cascades / pruning
  - stronger adversarial reviewer pressure before promotion

## First Hard-Gated Result

The first rerun with a real hard gate is now complete:

- `max_pair_detectability = 0.8`
- `allow_fallback_selection = false`
- `k = 2` candidates per role
- `1` quartet per domain

Result:

- promoted families: `0`
- all `3/3` smoke quartets rejected

Interpretation:

- the strict selector is now behaving honestly
- but the current candidate pool is not strong enough to survive that gate

Immediate implication:

- the next move should not be threshold relaxation
- it should be one of:
  - stronger candidate generation
  - more candidate diversity with cheaper pruning
  - a reviewer cascade that can screen many candidates before the expensive full pairwise stage

## Pairwise Cascade Follow-Up

The reviewer cascade has now been tried in two forms.

Unary candidate screen:

- too blunt
- marked almost every candidate as artificial
- collapsed coverage before family selection

Within-role pairwise prune:

- much better as a pruning primitive
- preserves one candidate per role across all three smoke quartets
- cuts total usage to `70` calls on the same smoke scale

But:

- even after pairwise prune, the final valid/invalid family comparison still fails the strict pair-detectability gate in all `3/3` quartets

Updated read:

- the benchmark-v3 bottleneck is no longer “find a better selector” in the abstract
- it is more specifically:
  - generate candidate pairs whose contrast is less visibly patched
  - or filter at the pair level with a stronger adversarial objective

## Pair-Conditioned Generation Follow-Up

Pair-conditioned generation has now been tested directly.

What improved:

- lower end-to-end cost (`48` calls on the smoke)
- cleaner within-role candidate ranking
- full role survival after pairwise prune

What did not improve:

- final strict pair acceptance remains `0/3`

Updated read:

- joint rewriting is useful, but not sufficient
- the benchmark-v3 bottleneck is now clearly:
  - pair-level adversarial filtering
  - or a generation objective that directly targets low-detectability contrast, not only good individual rewrites

## Pair-Level Adversarial Prune Follow-Up

Pair-level adversarial prune has now been tested directly.

What improved:

- pruning is now aligned with the joint candidate pair rather than separate role top-1 choices
- the best algebra and graph/path pair scores move slightly closer to the strict threshold

What did not improve:

- accepted families remain `0/3`
- blocksworld remains clearly above the strict gate

Updated read:

- the selector structure is now close to the right one
- the remaining leverage is likely:
  - stronger pair-contrast generation
  - or a stronger reviewer adversary

## Contrast-Aware Prompt Follow-Up

Contrast-aware pair prompting has now also been tested.

Result:

- accepted families remain `0/3`
- final pair detectability does not materially improve relative to the simpler pair-conditioned setup

Updated read:

- prompt-side generation changes look close to saturated on the current setup
- the remaining leverage is now more likely:
  - a stronger generator
  - or a stronger reviewer adversary

## Stronger Reviewer Follow-Up

A stronger reviewer adversary has now been tested on the same `pairadv` candidate pool:

- reviewer backend: `api + local Qwen3-8B`
- generation held fixed by reusing `benchmark_v3_pairadv_smoke_candidates.jsonl`
- result: `3/3` families pass the current strict scalar gate

But:

- shallow artifact audit on the selected set looks clean
- blind-facing internal review still rejects the packet

Updated read:

- the benchmark-v3 problem is no longer only generator quality or selector structure
- reviewer aggregation itself is now a bottleneck
- simple label-space union is too permissive because repeated `both` judgments can understate practical detectability

Next strict move:

- replace reviewer aggregation with an adversarial max-penalty rule
- or use a different reviewer family rather than permissive ensemble collapse

## Adversarial Aggregation Follow-Up

The adversarial max-penalty aggregation has now also been tested on the same `pairadv` candidate pool.

Result:

- accepted families return to `0/3`
- all quartets fail already at pair-candidate prune

Updated read:

- the earlier `api_local_max` acceptance was not a real benchmark-v3 breakthrough
- it was a reviewer-aggregation artifact
- the stricter reading is now back to:
  - current candidate quality still does not clear a blind-clean gate
  - and prompt/selector changes remain downstream of generation/reviewer strength

## Cross-Family Reviewer Follow-Up

A different local reviewer family has now also been tested:

- `CriticLeanGPT-Qwen3-8B-RL`
- same `pairadv` candidate pool
- same strict thresholds

Result:

- accepted families remain `0/3`
- all quartets fail at pair-candidate prune

Updated read:

- the current negative result is now stable across reviewer families
- the benchmark-v3 bottleneck remains candidate pair quality under a strict reviewer

## Stronger Generator Feasibility

The next stronger local generator candidate was probed:

- `Qwen3.5-35B-A3B`

Current blocker:

- the local `infer` environment cannot load `qwen3_5_moe`
- so the next stronger-generation step is currently blocked by environment support rather than benchmark-v3 code structure

## API Pair Generation V2 Follow-Up

The first stronger-usage API generation loop has now been tested directly.

Protocol:

- same API model
- pair-conditioned generation
- `1` reviewer-guided regeneration round
- strict reviewer unchanged

Result:

- accepted families remain `0/3`
- but regenerated candidate pairs do appear
- and some algebra penalties drop from `0.95/1.0` to `0.9`

Updated read:

- the current API model is not “incapable”
- but one regeneration round is not enough to produce blind-clean pairs under the strict gate
- the next API-native move is deeper protocol, not a different prompt wording

## Two-Round Regeneration Follow-Up

The deeper API-native follow-up has now also been tested:

- `k=2`
- `2` reviewer-guided regeneration rounds
- same strict reviewer

Result:

- accepted families remain `0/3`
- cost rises sharply
- candidate penalties now flatten around `0.9` across all three domains

Updated read:

- the current API-native loop is not failing because it does nothing
- it is failing because extra depth alone saturates before the strict threshold
- the next useful API-native move should widen search or change branching, not just add more rounds

## Wider-Branch Regeneration Follow-Up

The next API-native continuation has now also been tested:

- `k=2`
- `1` reviewer-guided regeneration round
- regenerate the top `2` failing pairs instead of only the top `1`
- same strict reviewer

Result:

- accepted families remain `0/3`
- cost rises to `69618` total tokens, still far below the `2`-round run
- the widened search reaches the same `0.9` plateau as the deeper run

Updated read:

- width is a better lever than extra depth under the current API-native loop
- but width alone still does not create a blind-clean pair under the strict gate
- the next useful API-native move should widen earlier or widen more, not return to deeper top-1 regeneration

## Larger-Initial-Pool Follow-Up

The next API-native breadth continuation has now also been tested:

- increase `candidates_per_role` from `2` to `3`
- keep `1` reviewer-guided regeneration round
- keep `top_k=2`
- same strict reviewer

Result:

- accepted families remain `0/3`
- cost rises to `93053` total tokens
- all three domains still bottom out at `0.9`

Updated read:

- simply enlarging the initial pool is not enough
- the `k=3, top_k=2` run is dominated by the earlier `k=2, top_k=2` breadth run
- if API-native breadth continues, it should add cheaper early screening or change branching structure, not just add one more initial candidate per side

## Pair Cascade Follow-Up

The first true cascade has now also been tested:

- stage 1: API generation + local cheap prune at `0.9`
- stage 2: strict `api_local_advmax` final rerun on the pruned pool

Result:

- stage 1 keeps one candidate pair per answer variant for all `3/3` quartets
- stage 2 still accepts `0/3`
- all final domains still land at `0.9`

Updated read:

- cascade helps efficiency
- cascade does not yet help quality
- the next useful move is not another plain re-score cascade; it is a second-stage regeneration step built on the locally pruned survivors

## Second-Stage Regeneration Follow-Up

That continuation has now also been tested:

- use the locally pruned survivors as candidate-input
- run strict pair-conditioned regeneration on top
- keep the same strict reviewer and thresholds

Result:

- accepted families remain `0/3`
- all domains still stay at `0.9`
- total measured cost rises above both one-shot breadth baselines

Updated read:

- simply regenerating from cleaner survivors is not enough
- the current bottleneck is not just staging order
- the next useful move has to change the feedback target or the optimization objective, not only the pipeline structure

## Proposal Alignment Correction

The benchmark-v3 strict line drifted beyond the original proposal.

Proposal hard requirements:

- preserve audited quartet semantics
- pass shallow / length artifact checks
- avoid obvious templating or patched-edit cues
- survive blind audit against artificial-edit artifacts

Proposal does **not** require:

- universal human-indistinguishability of valid/invalid pairs under one scalar strict gate
- forcing structured algebra errors to become visually as inconspicuous as valid derivations

Updated read:

- benchmark-v3 should be judged by artifact cleanliness, not by maximal pairwise indistinguishability
- the current `0.9` plateau may partly reflect semantic wrongness visibility rather than benchmark corruption

## Acceptance-Aligned Rerun

The first rerun after this correction is now complete:

- rerun the current best one-shot breadth configuration with the corrected prompt objective
- then rescore old vs new review logs under acceptance-aligned modes

Result:

- strict scalar gate remains `0/3`
- but the acceptance analysis no longer supports reading that `0/3` as universal benchmark failure

Artifacts:

- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_acceptance_compare.json`

Acceptance read:

- if `semantic_only` reviewer penalties are ignored:
  - old wider-branch run: `2/3`
  - corrected accept rerun: `2/3`
- if only explicit `surface_only` or `mixed` penalties are counted:
  - old wider-branch run: `3/3`
  - corrected accept rerun: `3/3`

Most important domain shift:

- graph/path moves from mostly `surface_only` reviewer reasons to mostly `semantic_only` reviewer reasons
- blocksworld remains the clearest unresolved surface-artifact domain

Updated read:

- the proposal correction is methodologically real even though the universal strict scalar did not flip
- the next useful benchmark-v3 move is no longer blind breadth/depth scaling
- it is to isolate and reduce blocksworld surface artifacts under the corrected acceptance rule

## Blocksworld-Focused Hardening

That next move has now been tested.

Method:

- keep the corrected proposal-aligned acceptance rule
- tighten only blocksworld
- standardize each step to the exact source move action plus resulting state
- forbid explanatory stack narration and goal narration in blocksworld prompts

Authoritative same-quartet comparison:

- before:
  - `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl`
- after:
  - `artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl`
- acceptance compare:
  - `artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_acceptance_compare.json`

Result:

- strict scalar gate still rejects the quartet
- proposal-aligned acceptance now accepts it
- reviewer reasons shift from surface templating cues to move-sequence directness / extra-step cues

Updated read:

- blocksworld is no longer the clearest remaining surface-artifact bottleneck
- the universal strict gate still over-penalizes semantic/task-structure visibility
- the next benchmark-v3 hardening target should move away from blocksworld

## Algebra-Focused Hardening

That follow-up has now also been tested.

Method:

- keep the corrected proposal-aligned acceptance rule
- tighten only algebra
- standardize each step to a compact operation-driven form with the exact equation fragment
- freeze algebra problem text during rewrite to remove irrelevant validator drift

Authoritative same-quartet comparison:

- before:
  - `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl`
- after:
  - `artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl`
- acceptance compare:
  - `artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_acceptance_compare.json`

Result:

- strict scalar gate still rejects the quartet
- proposal-aligned acceptance improves from `0.0 / 0.45` to `0.0 / 0.0`
- reviewer reasons shift away from `suggesting patching / awkward phrasing` toward plain arithmetic inconsistency

Updated read:

- algebra no longer looks like a strong remaining surface-artifact problem either
- after blocksworld and algebra hardening, the remaining strict failures now look mostly semantic rather than artifact-driven
- the next useful move is an integrated full-smoke rerun under the corrected acceptance standard

## Integrated Full-Smoke Acceptance Result

That integrated rerun is now complete.

Authoritative artifacts:

- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_acceptance_compare.json`

Result:

- universal strict scalar gate still returns `0/3`
- proposal-aligned acceptance now returns:
  - `ignore_semantic_only = 3/3`
  - `surface_or_mixed_only = 3/3`

Updated read:

- under the proposal target, benchmark-v3 is now good enough at smoke scale
- the remaining strict failures should be read primarily as semantic/task-structure visibility, not unresolved surface-artifact corruption
- further benchmark-v3 work should scale or diversify the acceptance-clean protocol, not continue chasing universal strict pairwise indistinguishability

## Mini-Benchmark Scale-Up

That scale-up is now complete with `2 quartets/domain`.

Authoritative artifacts:

- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_acceptance_compare.json`

Result:

- universal strict scalar gate still returns `0/6`
- proposal-aligned acceptance now returns:
  - `ignore_semantic_only = 6/6`
  - `surface_or_mixed_only = 6/6`

Updated read:

- benchmark-v3 now looks adequate not only at smoke scale but at mini-benchmark scale under the proposal target
- the current constraint has shifted from benchmark validity to benchmark construction cost and diversity
- further work should keep the same acceptance rule and focus on cheaper scaling or broader quartet coverage

## Acceptance-Mode Export

The builder/export mismatch is now fixed.

Authoritative artifact:

- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_summary.json`

Result:

- `acceptance_mode = ignore_semantic_only`
- `num_selected_families = 6`
- `num_selected_records = 24`
- domain balance:
  - algebra `8`
  - blocksworld `8`
  - graph_path `8`

Updated read:

- benchmark-v3 is no longer only “acceptable on paper”; the builder can now export the proposal-aligned accepted families directly
- strict detectability remains available as a diagnostic field in the exported summaries
- future scale-up should prefer candidate-pool reuse plus acceptance-mode promotion before paying for full regeneration

## Mid-Scale Export

The first larger exported benchmark-v3 run is now complete.

Authoritative artifacts:

- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis.json`
- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic.jsonl`

Result:

- `acceptance_mode = ignore_semantic_only`
- `44 / 54` families accepted
- `176` records exported
- domain balance:
  - algebra `72`
  - blocksworld `40`
  - graph_path `64`

Acceptance analysis:

- `strict = 2 / 54`
- `ignore_semantic_only = 44 / 54`
- `surface_or_mixed_only = 48 / 54`

Updated read:

- benchmark-v3 is now a real mid-scale exported benchmark under the proposal target
- algebra is no longer the scaling bottleneck
- blocksworld is now the main domain blocking higher acceptance at scale

## Mid-Scale Acceptance Correction

The first `44 / 54` mid-scale export turned out to be a raw build-pass read, not the final proposal-aligned acceptance result.

Authoritative corrected artifacts:

- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json`
- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

What changed:

- the acceptance taxonomy was corrected so broad planning-domain cues like `forced sequence`, `more direct`, and `table clearing` no longer count as automatic surface-artifact failures
- the exported dataset was then rebuilt deterministically from the existing candidate pool and the corrected acceptance analysis
- this is not a new generation run; it is a corrected read of the same mid-scale candidate/review evidence

Corrected result:

- `52 / 54` families accepted
- `208` records exported
- domain balance:
  - algebra `72`
  - blocksworld `72`
  - graph_path `64`

Corrected acceptance analysis:

- `strict = 2 / 54`
- `ignore_semantic_only = 52 / 54`
- `surface_or_mixed_only = 52 / 54`

Updated read:

- benchmark-v3 mid-scale export is stronger than the first raw summary suggested
- the apparent blocksworld bottleneck was mostly an acceptance-taxonomy problem
- the current remaining gap is only `2` rejected groups, not `10`
- the old `44 / 54` raw export should be kept as a checkpoint, but not as the authoritative mid-scale benchmark-v3 result

## Default Benchmark Replacement

Benchmark-v3 is now strong enough under the proposal-aligned acceptance rule to replace the old default benchmark pointer.

What changed:

- the project now treats
  - `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`
  as the default base benchmark
- older
  - `data/generated/craft_core_week1.jsonl`
  - `data/generated/craft_core_hard.jsonl`
  remain only as legacy reproduction/comparison datasets

Scope:

- this replacement updates default entrypoints for future runs
- it does **not** retroactively relabel historical Week 1-6 artifacts as if they had already been rerun on benchmark-v3
