# Contrastive Locality Family Bootstrap

Date: 2026-03-31

## Why this family exists

The current family fails to show a stable final-slice gap between
`gold_signal` and `matched_shuffle` after checker repair. The main suspicion is
that many examples remain too easy for generic retry or from-scratch
recomputation.

This family is a versioned attempt to change the object family itself rather
than tuning the old checker.

## Core idea

`contrastive_locality` keeps the same high-level object:

- verifier-mediated choice between `keep` and `revise`

But it changes the task geometry:

- the revise case should expose at least two nearby plausible local fixes
- only one local fix is actually correct under the checker
- the gold repair suffix should disambiguate among those nearby fixes
- generic retry should be more likely to choose a plausible but wrong repair or
  to rewrite too broadly

## Intended benefit

This family should make `matched_shuffle` more damaging because a shuffled
signal is more likely to point toward the wrong local repair among several
plausible ones.

## Preferred domains

- `code`
  - operator choice
  - boundary-condition branch
  - off-by-one versus wrong-aggregation ambiguity
- `plan`
  - local reorderings where several short permutations look plausible
  - deadline or precedence tasks where only one local fix satisfies all
    constraints

## Not the same as the old family

This is not just “harder”.

The intended difference is:

- old family: one obvious local wrong step, often recoverable by recomputation
- new family: one local wrong region with multiple plausible repairs, where the
  verifier content should help choose the right one

## Minimal bootstrap rule

The first bootstrap batch only needs to answer:

- can we generate reviewed pairs that satisfy this family definition?

It does not need to prove Audit conversion yet.

## Current status

As of 2026-03-31, this branch has produced a few individually acceptable pairs
but not a stable reviewed panel. The bottleneck has shifted from schema validity
to semantic reliability:

- equivalent or underdetermined code repairs
- checker/spec disagreement in code
- trivial plan instances that collapse to one obvious order
- revise traces that do not actually violate the written constraints

Current status is therefore:

- `concept viable`
- `generator not yet stable`
- `not Object-bootstrap ready`

## Spin-out note

As of 2026-04-01, the exact structured sub-objects have become strong enough to
justify a separate `structured_locality` branch.

That spin-out should be read as:

- a clean object-level branch built from exact structured plan/code subpanels
- not a retroactive success for the full `contrastive_locality` family
