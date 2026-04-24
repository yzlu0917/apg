# Phase 0 Bootstrap

## Scope

This document converts `proposal.md` into a phase-0 execution frame for `/cephfs/luyanzhen/apg/VSI`.
The immediate goal is not to prove the whole thesis, but to freeze the object claim, define go/no-go gates, and start a minimal Object-gate closure that can fail cleanly.

## Claim Hierarchy

### 1. Object / measurement claim

Headline claim for phase 0:

> Verification structure is a measurable object that is not reducible to raw task difficulty, and can be decomposed into certificate horizon, local ambiguity, and exploitability.

Phase-0 support target:

- show that `H/A/E` can be operationalized on controlled tasks
- show that these axes can vary while coarse difficulty proxies stay matched
- show that the object is useful enough to justify a real benchmark, even before any method win

What is **not** claimed yet:

- not yet claiming that a single scalar `VSI` is the uniquely correct summary
- not yet claiming method gains from routing or RL
- not yet claiming transfer to real domains

### 2. Method claim

Conditional claim, not headline yet:

> Once verification structure is measured, training or routing policies that adapt verifier strength to that structure should outperform fixed verifier recipes under equal budget.

Required evidence before promotion:

- Object gate pass
- Audit gate pass
- at least one clean equal-budget conversion result

### 3. Deployment / generalization claim

Strictly conditional claim:

> The same verification-structure lens should explain why verifier-based training works better in formal or executable domains than in open, delayed, or weakly checkable domains.

Required evidence before promotion:

- synthetic law holds across multiple families
- transfer trend appears on at least two real anchors
- result is robust to verifier swap and family holdout

## Fallback Paper Framing

### Preferred framing if main line works

`verification structure` is the hidden axis of trainable reasoning; `VSI` and `CertBench` expose it; `SAVR` is one operational instantiation.

### Fallback A: predictive-law paper

If routing/method gains are weak but the object is real:

> Verification structure predicts when verifier-based reasoning training helps, hurts, or becomes misleading.

Deliverable:

- measurement object
- controlled benchmark
- predictive law / phase diagram

### Fallback B: benchmark + diagnosis paper

If a single scalar `VSI` is unstable but the axes are individually meaningful:

> Difficulty alone is an insufficient coordinate; certificate horizon, ambiguity, and exploitability expose distinct failure modes in reasoning supervision.

Deliverable:

- benchmark
- axis-specific audits
- negative or mixed results on process reward / weak verifiers

### Fallback C: clean negative-result paper

If transfer is weak and method gains fail, but the controlled study is clean:

> Controlled reasoning tasks show where verifier-based progress breaks: delayed certification, process ambiguity, and weak-verifier exploitability.

Deliverable:

- negative result
- taxonomy of failure modes
- design guidance for future benchmarks and verifiers

## Gate Definitions

### Gate 1: Object

Question:

> Does the proposed object exist as something more informative than coarse difficulty?

Required evidence:

- at least one controlled slice where coarse difficulty proxies are matched
- `H/A/E` move in intended directions across families
- metric behavior is stable enough to justify further audit

Go:

- family ordering matches design intent on the bootstrap slice
- object axes are separable without relying on method wins
- acceptance thresholds are frozen before larger sweeps

No-go:

- axes collapse back to difficulty
- operationalization is too ad hoc to reproduce
- object cannot be measured without method-specific assumptions

### Gate 2: Audit

Question:

> Are the observed object measurements genuine rather than artifacts of leakage, canonicalization bias, or a single weak verifier?

Required evidence:

- rewrite robustness
- verifier-swap robustness
- leakage / shortcut checks on the controlled families

Go:

- ordering survives at least one alternative verifier implementation
- ambiguity findings survive non-canonical rewrites
- exploitability is not explained by trivial leakage

No-go:

- object disappears after swap / rewrite controls
- canonical labeling fully explains the signal
- weak verifier artifacts dominate the story

### Gate 3: Conversion

Question:

> Does object signal convert into minimal observable utility for training or decision-making?

Required evidence:

- equal-budget comparison against fixed strategies
- at least one utility metric among `delta accuracy`, `accuracy/cost`, or `reduced weak-strong gap`

Go:

- adaptive routing beats at least one strong fixed baseline on a frozen dev slice
- gain tracks the intended axis, not just more expensive verification

No-go:

- routing adds no information beyond always-strong or random routing
- object is measurable but not actionable

### Gate 4: Scale

Question:

> Should this project absorb real training budget and larger real-task evaluation?

Required evidence:

- Conversion gate pass
- stable estimates on larger synthetic families
- pre-frozen dev/final split and acceptance rules

Go:

- allocate 3B / larger compute and real-anchor budget
- open recipe sweeps and transfer runs

No-go:

- stay in object / benchmark / diagnosis framing
- do not expand model size or sweep space

## Frozen Phase-0 Acceptance Rule

The current bootstrap accepts the Object gate only in the narrow sense below:

- matched difficulty proxy across the microbench families
- `early_cert` vs `delayed_cert` horizon gap `>= 0.50`
- `rewrite_ambiguity` ambiguity gap over low-ambiguity baselines `>= 0.50`
- `partial_test_exploit` exploitability gap over low-exploitability baselines `>= 0.50`

This is a bootstrap acceptance rule for the object, not a paper-level acceptance rule.

## Frozen Slices

The first phase-0 frozen split is recorded in `configs/frozen_slices_phase0.json`.

Current policy:

- use the `dev` slice for prompt shape, verifier choice, and generator debugging
- use the `final` slice only for confirming that the signal does not collapse after those choices
- do not reassign tasks across `dev` and `final` without reopening ALIGN

## Minimal Object-Gate Closure

### Objective

Start with a tiny, fully reproducible microbench that demonstrates:

- the proposed object can be instantiated without training
- the three axes can be separated from a matched coarse-difficulty proxy
- the project can now move to controlled benchmark construction instead of staying at proposal level

### Bootstrap slice

- `early_cert`: prefix-executable arithmetic traces
- `delayed_cert`: same coarse trajectory length and branching proxy, but certification only at the end
- `rewrite_ambiguity`: multiple semantically correct but non-canonical process traces
- `partial_test_exploit`: weak verifier admits exploitable solutions that fail the strong oracle

### Output

- reproducible JSON artifact under `artifacts/object_gate/`
- one command to regenerate
- result summary logged in `results.md`

### Non-goals

- no model training
- no API calls
- no real-anchor claims
- no method comparison

## Next 5-7 Days

### Day 1

- freeze phase-0 framing, claims, gates, and bootstrap acceptance
- implement the microbench and write first result artifact

### Day 2

- replace toy constants with instance generators for the four core families
- formalize `H/A/E` estimators and log per-instance outputs

### Day 3

- add Audit-gate probes: rewrite robustness and verifier swap
- stress-test whether ambiguity and exploitability are artifacts of one implementation

### Day 4

- create a difficulty-matching pipeline for controlled paired instances
- freeze the first dev slice and final slice definitions

### Day 5

- run the smallest `Object -> Audit` study on 1-2 synthetic families
- decide whether the object is strong enough to justify conversion experiments

### Day 6

- if Object and Audit are both alive, prepare the first equal-budget conversion protocol
- otherwise rewrite toward Fallback A/B and tighten the benchmark paper framing

### Day 7

- package the synthetic benchmark spec, estimators, and first figures/tables for an internal checkpoint
