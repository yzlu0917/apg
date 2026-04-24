# Contrastive Locality Acceptance

Date: 2026-03-31

## Purpose

Freeze the acceptance rule for the `contrastive_locality` family so the branch
does not keep moving its own boundary while bootstrapping.

## Family objective

This family is meant to test a narrower object than the original CAVE panel:

- local `keep` versus `revise` decisions
- multiple nearby plausible local repairs in the revise case
- only one checker-correct local repair
- verifier content should matter more than generic retry

## Pipeline

Every candidate pair must pass four stages:

1. generation
2. deterministic validation
3. model-judge pre-screen
4. human review freeze

## Deterministic validation requirements

Before any semantic review:

- pair contains exactly one `keep` and one `revise`
- keep and revise share the same question and domain
- revise has non-empty fail span and non-empty repair suffix
- keep has empty fail span and empty repair suffix
- keep/revise both remain exact-checkable

If a pair fails here, it is invalid, not rejected on family grounds.

## Model-judge pre-screen

The judge must score each pair on:

- `same_task_local_error`
- `checker_disambiguates_repairs`
- `gold_repair_informative`
- `retry_vulnerable`

Judge verdicts:

- `accept`
- `borderline`
- `reject`

Pre-screen rule:

- only `accept` pairs should normally move to human review
- `borderline` may be spot-checked when the batch is otherwise sparse
- `reject` should not enter the frozen panel
- the model-judge is a pre-screen only, not a final acceptance oracle

## Human review rule

A reviewed pair counts as accepted only if all are true:

- the revise trace still solves the same task as the keep trace
- the revise error is genuinely local
- at least one nearby wrong repair is plausible
- the checker would reject those nearby wrong repairs
- the gold repair gives useful local guidance rather than restating the answer
- the case is not trivially recoverable by generic retry or from-scratch
  recomputation

## Bootstrap Object gate target

`contrastive_locality` only gets a fresh Object bootstrap `GO` if:

- there is a frozen reviewed panel with at least `6` accepted pairs
- both `code` and `plan` are represented
- reviewed acceptance rate is at least `80 percent`
- model-judge pre-screen acceptance among valid candidates is at least `70 percent`
- no dominant failure mode shows checker/spec inconsistency or false revise
  violations

## Current status

This acceptance rule is frozen before any new bootstrap claim.

As of now:

- the branch is still `Object bootstrap in progress`
- existing reviewed acceptance is too low
- current bottleneck is semantic generation reliability, not schema validity
- the first blind judge pass (`judge_v2`) is useful for filtering obviously bad
  pairs, but still disagrees with human review on several borderline cases
- the current execution-backed pass (`judge_v3.1`) is best viewed as a
  high-precision veto tool, not a final acceptance oracle
- `judge_v3.2` added schedule-style plan semantics and materially improved the
  plan-side pre-screen
- the current `judge_v4` is the best pre-screen so far: it adds
  execution-backed code semantics with synthesized-reference probe checks and
  now matches the current human review ledger on the 10 reviewed pairs
- a structured plan object now exists for this family, using a one-adjacent-swap
  local repair checker schema instead of prose constraints
- that structured object is easier to audit; direct API generation still fails
  on it, but a search-constructed path can now produce clean accepted pairs
- the structured-plan search path now has a frozen reviewed subpanel, but this
  should be read as sub-object viability rather than whole-family Object `GO`
- a matching structured-code object now also exists; under `code_local_repair_v1`
  the current `judge_v4` can `auto_accept` exact cases when execution proves
  that only the gold local repair passes
- the structured-code search path now has a frozen reviewed subpanel alongside
  structured-plan, again as sub-object viability rather than whole-family
  Object `GO`
- these two exact structured sub-objects are now strong enough to justify a
  separate `structured_locality` spin-out branch with fresh Object criteria
- even under `judge_v4`, accepted pairs still require human review and no
  model-judge version is a standalone freeze oracle
