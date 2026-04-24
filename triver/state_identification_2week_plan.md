# Two-Week State-Identification Plan

## 0. Goal

This document defines the next algorithmic phase after the current paper freeze.
The objective is not to rescue the original strongest TriVer claim at any cost.
The objective is to test one specific hypothesis:

> The main recoverable gap is the exact-state to predicted-state deployment gap, and the most promising way to reduce it is to improve state identification rather than to continue local value-head search.

The plan is therefore scoped to state identification, teacher targets, and noisy deployment.
Value-head family sweeps and router-family sweeps are out of scope unless they directly serve that goal.

---

## 1. Working Hypothesis

Current evidence already supports three statements:

1. Exact-state structured control is informative.
2. Predicted-state deployment degrades sharply.
3. `predicted_state_exact_value` consistently beats `predicted_state`.

The simplest reading is:

- the main bottleneck is not missing value-head capacity alone;
- the main bottleneck is noisy state identification under deployment.

This plan is designed to falsify or support that interpretation.

---

## 2. Success Criteria

We should continue the line only if at least one of the following happens on the selected evaluation slice:

1. The predicted-state controller recovers a substantial fraction of the exact-state gap.
2. The predicted-state controller improves both regret and revision harm on at least one exact-checker domain.
3. The predicted-state controller materially improves compute-value calibration without increasing regret.

Suggested operational thresholds:

- gap recovery:
  - recover at least `30%` of the `exact-state -> predicted-state` regret gap on one domain
- decision quality:
  - improve mean action regret by at least `0.02`
  - without increasing revision harm
- calibration:
  - improve Spearman calibration by at least `0.15`
  - or reduce utility-scale RMSE by at least `15%`

If none of these happen after the full two-week plan, stop algorithmic rescue work and keep the paper fixed as benchmark + mechanism + deployment diagnosis.

---

## 3. Evaluation Slice

Do not evaluate on a moving target.
Freeze the following evaluation slice before starting:

1. domains:
   - arithmetic
   - linear equations
2. controller comparison anchor:
   - ordered scalar
   - learned-1D
   - direct policy
   - factorized exact-state
   - one selected predicted-state controller per domain
3. quality metrics:
   - overall action regret
   - oracle action accuracy
   - revision harm
   - compute-value calibration
4. deployment diagnostics:
   - exact-state
   - predicted-state
   - predicted-state-exact-value

The goal is gap recovery, not a new leaderboard.

---

## 4. Week 1: Clean Targets and Teacher Signals

## 4.1 Task A: High-Determinacy Training Slice

Build a high-determinacy-only training variant:

- keep the current ambiguity filter
- add a stricter slice using non-ambiguous prefixes only
- optionally report a second stricter slice by top-gap percentile

Question answered:

- is predicted-state weak because the labels are noisy?

Go/No-Go:

- if high-determinacy training materially improves predicted-state deployment, target noise remains a live issue
- if not, move emphasis even more strongly to representation/state estimation

## 4.2 Task B: Soft Targets / Pairwise Teacher Labels

Train against softer teacher signals instead of only hard oracle actions:

- pairwise preference targets between actions
- soft action probabilities derived from oracle utility margins
- exact-state teacher value ranking when available

Question answered:

- is the bottleneck partly caused by hard-label collapse on near-tie prefixes?

Go/No-Go:

- keep this line only if it improves deployment metrics, not just train-set fit

## 4.3 Task C: Exact-State Teacher Distillation

Use exact-state structured control as a teacher.
Predicted-state should imitate one or more of:

- exact-state action values
- exact-state action ranking
- exact-state regime partition
  - continue-dominant
  - revise-dominant
  - abstain-dominant

Question answered:

- can predicted-state recover exact-state behavior more effectively by imitating the structured teacher rather than by fitting oracle actions directly?

Priority:

- highest

---

## 5. Week 2: State Identification Proper

## 5.1 Task D: Predict State, Not Just Action

Train predicted-state models to recover the exact-state sufficient statistics as directly as possible.
Recommended target families:

1. local invalidity risk `q_t`
2. continuation outcome statistics
3. exact-state value margin or regime features derived from those statistics

The main comparison should ask:

- does better state prediction reduce deployment regret?

Not:

- does a more complex head reduce training loss?

## 5.2 Task E: Teacher-Student Deployment Controller

Build one deployment controller whose only change is the teacher-student state-ID objective.
Keep the downstream controller as fixed as possible.

This is important because otherwise the result will be confounded with another value-head search.

Recommended policy:

- freeze the valuation head or keep one fixed valuation family
- vary only the state-identification objective

## 5.3 Task F: Error Decomposition

For the final comparison, report four numbers per domain:

1. exact-state regret
2. predicted-state-exact-value regret
3. baseline predicted-state regret
4. teacher-distilled predicted-state regret

The quantity that matters is:

- how much of the gap between (2) and (3) disappears

That is the cleanest state-identification progress metric.

---

## 6. Minimal Experimental Matrix

Keep the matrix small.

Required:

1. baseline predicted-state controller
2. high-determinacy training variant
3. soft/pairwise target variant
4. exact-state teacher-distilled variant

Optional only if one of the above is clearly positive:

5. one stronger representation variant

Do not add:

- new heteroscedastic heads
- new calibration wrappers
- new router families
- new broad model sweeps

unless the previous stage clearly shows state-ID progress and the new addition is necessary to isolate it.

---

## 7. Reporting Template

Every run in this phase should answer the same checklist:

1. Did overall regret improve?
2. Did revision harm improve or worsen?
3. Did compute-value calibration improve?
4. How much exact-state gap was recovered?
5. Was the gain domain-specific or cross-domain?
6. Did the change come from better state estimation, or only from another valuation effect?

If a run cannot answer these questions, it does not belong in this phase.

---

## 8. Stop Rules

Stop the rescue line early if any of the following becomes true:

1. Three consecutive state-ID variants fail to improve gap recovery.
2. Improvements appear only in train-proxy metrics, not in regret/harm/calibration.
3. Gains come only from another value-head change rather than from state prediction.
4. Predicted-state remains unable to recover a meaningful fraction of the exact-state gap in either domain.

At that point, freeze the algorithmic story and keep the publication centered on:

- prefix-level oracle benchmark
- scalar-insufficiency diagnostics
- deployment-gap diagnosis

---

## 9. Deliverables

By the end of the two-week plan, we should have:

1. one concise result table for state-identification recovery
2. one gap-recovery figure
3. one clear go/no-go memo

The go/no-go memo should answer only one question:

> Is deployable predicted-state factorization recoverable enough to justify a follow-up algorithm paper?

If yes, continue.
If no, stop and keep the current paper as the benchmark/mechanism paper it already supports.
