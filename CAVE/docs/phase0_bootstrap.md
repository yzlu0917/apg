# Phase 0 Bootstrap

Date: 2026-03-31

## Scope

This document converts the current proposal into a disciplined phase-0 research
program. It keeps the project claim-bearing, but narrows the active headline so
that the team can make progress without prematurely depending on large-scale
method wins.

## 1. Claim hierarchy

### 1.1 Headline object claim

The primary research object is not verifier accuracy and not raw self-correction
uplift. The primary object is:

`verifier-content causal control over keep / revise / abstain decisions`.

Operationally, this means CAVE should be able to produce examples where:

- a local intervention changes the correct revision action,
- that action is automatically checkable,
- old proxies such as verifier accuracy or second-try accuracy are insufficient
  to explain the change.

This is the only claim that should be treated as a headline claim before the
Object gate passes.

### 1.2 Conditional method claim

If the object is real and measurable, then `ICVT` may improve:

- verifier-mediated utility,
- intervention response rate,
- localized repair precision,
- selective revision utility under matched token budget.

This is a conditional claim. It is not yet a paper headline. It becomes central
only after the Object and Audit gates pass.

### 1.3 Conditional deployment claim

If the object and method claims survive audit, then exact-checkable training may
transfer first to:

- code self-repair,
- constraint reasoning,
- planning,

and only weakly or inconsistently to open-ended proof writing or free-form QA.

This is the most fragile claim. It should remain explicitly conditional until
the Conversion gate is passed on in-domain tasks and the Scale gate is passed on
external tasks.

### 1.4 Claim discipline

Supported now:

- It is coherent to define a causal-verification object distinct from verifier
  accuracy and end-to-end uplift.
- A seed benchmark protocol can be constructed around paired interventions.

Conditional, not supported yet:

- ICVT is better than strong verifier-guided baselines.
- Localized repair is the dominant mechanism of gains.
- Exact-checkable training transfers robustly to deployment settings.

Not allowed as a current headline:

- "We solve self-correction."
- "CAVE training generalizes broadly."
- "Verifier-guided reasoning is causally faithful in the wild."

## 2. Fallback paper framing

If the full method story does not hold, the project must still terminate in a
clean paper. The default fallback framing is:

`CAVE as a benchmark and protocol for measuring verifier-mediated revision,
plus a diagnostic study of where verifier usage collapses.`

This framing stays publishable even if ICVT underperforms or only works in a
narrow subset.

### 2.1 Primary fallback

Benchmark / protocol paper:

- define the object,
- construct paired interventions,
- separate procedure effect from verifier-content effect,
- report strong baseline profiling,
- show where standard self-correction pipelines fail to causally use feedback.

### 2.2 Secondary fallback

Negative or partial-result empirical paper:

- localized repair helps only on single-error or local-error regimes,
- verifier-content effect is smaller than expected,
- abstain or gain calibration is harder than revise-vs-keep.

### 2.3 Acceptable paper endings if method fails

- object-identification result,
- audit or diagnosis of shallow verifier usage,
- protocol and benchmark release,
- clear negative result on the dominant method hypothesis.

### 2.4 Framing to avoid

Do not force the project into:

- a "new stronger verifier" paper,
- a generic "self-correction works better" paper,
- a deployment-generalization story without object-level evidence.

## 3. Gate definitions

### 3.1 Object gate

Question:
Can we define a stable, checkable research object where verifier-mediated action
choices are distinct from old proxies?

Minimum evidence:

- paired interventions where the gold action flips under local edits,
- a stable schema for `question / initial_trace / fail_span / gold_action /
  repair_suffix / checker / utility`,
- at least one baseline analysis plan showing why verifier accuracy alone does
  not answer the object question,
- manual review protocol for labelability and locality.

Go:

- examples are internally consistent,
- gold action is checkable,
- paired design isolates local changes,
- at least two domains look viable.

No-go:

- labels are ambiguous without human judgment,
- fail spans are too diffuse to localize,
- the object collapses back to ordinary correctness classification.

Current status:
`ACTIVE`. Bootstrap seed exists, but the gate is not yet passed.

### 3.2 Audit gate

Question:
Are apparent gains or correlations actually caused by leakage, artifact, or
shallow shortcuts?

Minimum evidence:

- matched shuffle control,
- verdict-preserving paraphrase control,
- at least one artifact checklist per domain,
- frozen dev slice and frozen final slice before method comparison.

Go:

- controls significantly damage verifier-content effect while leaving procedure
  effect interpretable,
- no obvious label leakage or formatting shortcut dominates.

No-go:

- gains survive shuffling nearly unchanged,
- labels are recoverable from artifact fields,
- evaluation boundary is still moving after seeing results.

### 3.3 Conversion gate

Question:
Does the object signal convert into measurable utility or decision gain?

Minimum evidence:

- action-level metrics improve against matched baselines,
- keep / revise decisions become better calibrated,
- localized repair or abstain reduces over-revision cost.

Go:

- positive signal on VMG-like and SRU-like metrics under matched budget,
- utility gain is not only due to longer generation or retries.

No-go:

- the object is measurable but does not translate into better decisions,
- improvements disappear under token-budget matching.

### 3.4 Scale gate

Question:
After conversion is real, does the recipe survive more data, stronger baselines,
and external benchmarks?

Minimum evidence:

- confirmatory runs on larger backbones or broader slices,
- transfer to at least one external exact-checkable benchmark,
- stable trend under moderate scaling, not just a one-off win.

Go:

- results survive stronger baselines and scale-up,
- the headline can expand from object to method, with cautious deployment claims.

No-go:

- gains vanish on stronger settings,
- the method only works on the handcrafted bootstrap slice.

## 4. Frozen framing for the next stage

Until the Object gate is passed, the project should be framed as:

`Can verifier-mediated revision be isolated as a measurable causal object?`

Not as:

- "Can ICVT beat all baselines?"
- "Can we generalize to every reasoning domain?"

This framing protects the project from premature overclaiming and preserves a
clean fallback path.

## 5. Minimal project skeleton

The workspace now uses:

- `README.md` for project orientation
- `docs/phase0_bootstrap.md` for the main phase-0 contract
- `docs/object_gate_min_loop.md` for the first executable loop
- `progress.md` for current milestone tracking
- `results.md` for reproducible commands and outcomes
- `data/object_gate_seed/` for hand-built paired interventions
- `scripts/validate_object_gate_seed.py` for schema validation
- `artifacts/object_gate/` for generated reports
- `history/` reserved for archived branches and superseded decisions

## 6. 5-7 day minimum execution plan

Day 1:

- freeze the bootstrap schema and seed review checklist,
- expand paired examples from the current seed into a small dev panel,
- add explicit artifact checks for each domain.

Day 2:

- implement a small baseline runner interface contract,
- define how direct-answer, generic retry, and shuffled-verifier controls will
  be logged,
- freeze dev-slice acceptance rules for Object and Audit gates.

Day 3:

- collect the first reviewed dev panel,
- measure labelability failures, diffuse-span failures, and pair consistency,
- decide whether `abstain` stays in scope for stage 1 or moves to stage 2.

Day 4:

- run baseline causal-gap profiling on the smallest exact-checkable subset,
- compute the first non-training descriptive metrics,
- log failure modes rather than chasing wins.

Day 5:

- decide Object gate go / no-go,
- if go, freeze the Audit gate controls and baseline roster,
- if no-go, collapse to benchmark/protocol framing and stop method expansion.

Days 6-7 if the Object gate is healthy:

- prepare the first audit slice,
- implement matched-shuffle and paraphrase controls,
- only then start the smallest possible modeling or prompting comparison.

## 7. Immediate next action

The current immediate action is the Object gate minimum loop:

- validate the seed schema,
- confirm pairwise keep / revise flips,
- record the result in `results.md`,
- keep the project headline at the object level.
