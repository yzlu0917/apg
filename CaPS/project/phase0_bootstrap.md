# CaPS Phase 0 Bootstrap

Date: 2026-03-31
Status: active
Phase: bootstrap -> Object gate

## 1. Scope

This directory is treated as an independent research project. Phase 0 does not run large-scale training or benchmark sweeps. Its job is to freeze the research object, define failure-safe framing, and start the smallest Object-gate loop that can later produce claim-bearing evidence.

## 2. Claim Hierarchy

| Layer | Current claim | Status now | What would support it | What would falsify it |
| --- | --- | --- | --- | --- |
| Object / measurement claim | Matched-counterfactual step credit is a more faithful process object than step correctness or raw progress under fixed rollout policy and budget. | Headline claim for the project. This is the only claim allowed to be the main story before conversion evidence exists. | Non-trivial signal on objective-verifier tasks; better alignment with deletion effect / continuation utility than old proxies; paraphrase-invariant and distractor-sensitive behavior. | Credit collapses to noise, position/length/style artifacts, or does not beat old proxies on the same slice. |
| Method claim | Training a CPV and using that signal in offline post-training improves equal-cost performance and process faithfulness. | Conditional claim only. Not a headline yet. | Small conversion win on frozen slices versus outcome-only / raw-progress controls without extra test-time compute. | Signal exists but does not convert, or only helps through compute/search inflation. |
| Deployment / generalization claim | The CaPS recipe or protocol transfers across families and external benchmarks, and is useful beyond one curated sandbox. | Conditional and weakest claim. Not for title/abstract until late. | Stable gains on held-out families and at least one external objective-verifier benchmark. | Gains vanish outside the pilot distribution or require benchmark-specific tuning. |

Claim policy:
- Headline only the object claim until Conversion gate passes.
- Method and deployment statements must be written as conditional claims in all planning notes.
- If the project stalls after Object or Audit, the paper must be reframed rather than story-saved.

## 3. Fallback Paper Framing

If the main CaPS training story does not survive, the project still has a viable paper path.

Primary fallback:
- A benchmark/protocol paper on matched-counterfactual process auditing.
- Deliverable: a reproducible intervention protocol, a small but clean step-credit dataset, and a direct comparison showing where step correctness / raw progress / length proxies fail.

Secondary fallback:
- An object-identification paper.
- Deliverable: evidence that causal step credit can be measured on some tasks, but conversion to policy gain is weak or selective.
- Framing: the object is real, but the scalable training bridge is the missing piece.

Negative-result fallback:
- A clean negative result on process reward design under equal-cost evaluation.
- Deliverable: evidence that plausible process proxies do not robustly outperform answer-only or NoThinking-style baselines once budget is frozen.
- Framing: the contribution is diagnostic and methodological, not recipe superiority.

Fallback boundary:
- Even if method training fails, the project must preserve value as protocol, audit, or negative result.
- No fallback may claim broad deployment value without Scale-gate evidence.

## 4. Gate System

| Gate | Question | Required input | Go if | No-go if | Output if passed |
| --- | --- | --- | --- | --- | --- |
| Object | Does the proposed object exist and improve on old proxies? | Small objective-verifier slice, matched delete/paraphrase/distractor interventions, fixed rollout budget | Signal is non-trivial, beats old proxies on at least one primary comparison, and respects paraphrase/distractor behavior | Signal is mostly noise or explained by shallow artifacts | Frozen object definition and a CPV target worth modeling |
| Audit | Is the signal genuine rather than leakage or artifact? | Object-gate data plus negative controls | Main effect survives controls for length, position, style markers, and shallow shortcuts | Signal vanishes after controls or appears equally on shallow tasks | Credible measurement object |
| Conversion | Can the object produce minimal utility gain? | Frozen CPV or reranker on held-out prompts | Equal-cost rerank/filter or tiny offline tuning beats answer-only / raw-progress controls on the main dev slice | No measurable utility gain, or gains require extra compute | Justification for small-scale training |
| Scale | Is the recipe stable enough to justify real resource spend? | Conversion-positive recipe, frozen final slice, external check | Gains hold on frozen final slice and at least one external setting with acceptable variance | Wins are brittle, vanish on freeze, or depend on post-hoc metric changes | Permission to run larger training / broader benchmarking |

## 5. Frozen Evaluation Boundary for Phase 0

These settings are frozen before any recipe sweep.

- Main metric for Object gate: proxy-vs-effect alignment under fixed budget.
- Primary comparison: matched-counterfactual credit versus step correctness and raw progress.
- Dev slice policy: objective-verifier tasks only; split into high-dependency and shallow strata.
- Final slice policy: disjoint prompts, same strata, untouched until Object protocol is stable.
- Acceptance rule: pass/fail is determined at the gate level, not by changing metrics after results arrive.

What is intentionally not frozen yet:
- Exact Reasoning Gym family names, because the package is not installed in the current environment.
- External benchmark activation, which is deferred until Scale planning.

## 6. 5-7 Day Minimal Execution Plan

Day 1:
- Connect `infer` environment to the primary data/task source.
- Freeze exact dev/final family names and write them into `configs/object_gate.json`.
- Generate the first tiny manifest and sample schema.

Day 2:
- Produce 8-12 pilot prompts and 2 traces per prompt.
- Stress-test semantic step segmentation and intervention formatting on a handful of cases.
- Record failure patterns before any broad data generation.

Day 3:
- Run the minimal Object loop on the first batch with delete/paraphrase/distractor variants.
- Compute the first proxy comparison against step correctness and raw progress.
- Decide whether the object signal is promising enough to widen the slice.

Day 4:
- Add artifact checks: position, length, reasoning-marker baselines, and shallow-task controls.
- Write the first Audit pre-read in `results.md`.

Day 5:
- If Object looks real, train or fit the smallest possible scorer/reranker.
- Test equal-cost reranking on held-out prompts as the first Conversion probe.

Day 6:
- Decide whether to continue toward CPV + offline tuning, or to pivot to the fallback benchmark/diagnosis framing.
- Freeze a short experiment list for the next phase only if Conversion is non-zero.

Day 7:
- Consolidate results, retire dead branches, and rewrite the abstract/intro framing to match the highest supported claim.

## 7. Immediate Next Action

Immediate objective:
- Start Object gate without large experiments by freezing the protocol, config, artifact layout, and run-state files.

Phase-0 completion rule:
- Once the project skeleton exists, the gate protocol is frozen, and the Object bootstrap command initializes a run state, phase 0 is complete and day-1 execution can begin.
