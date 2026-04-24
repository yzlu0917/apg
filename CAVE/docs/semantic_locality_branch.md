# Semantic Locality Branch

Date: 2026-04-07

## Why this branch exists

`structured_locality` is now clean enough to act as an exact anchor, but it is
still intentionally narrow and checker-heavy.

If the project also wants to say something about more natural verifier use, it
needs a second branch whose purpose is not maximal exactness, but reduced
program dependence.

`semantic_locality` is that second branch.

## Role in the project

This branch is not meant to replace `structured_locality`.

Instead:

- `structured_locality` asks:
  - can we define and audit a clean local-repair object at all?
- `semantic_locality` asks:
  - can any of that survive when the object is less programmatically pinned
    down and more semantically natural?

## Intended object

The target object is still local verifier-mediated repair, but under weaker
structure:

- the error should still be local
- multiple repairs may still look plausible
- the checker should be stronger than free-form preference, but weaker than a
  fully enumerated exact structured object
- the sample should feel closer to realistic code/planning feedback

## Non-goals

This branch is not trying to:

- immediately beat the old final-slice negative result
- inherit `structured_locality`'s Object `GO`
- skip straight to Audit or method claims

## Current status

As of 2026-04-07:

- branch defined
- no frozen panel yet
- no Object `GO`
- next step is object design, not benchmark sweep

## Candidate directions

- `code`
  - local bug families where the checker is executable but not fully
    enumerative, for example boundary-condition variants with broader hidden
    tests
- `plan`
  - local revision tasks where constraints are structured but not reduced to a
    single adjacent-swap geometry
- mixed verifier format
  - short natural-language feedback plus partial structured hints, instead of a
    fully explicit repair candidate list

## Success condition

This branch is only interesting if it can preserve two things at once:

- enough semantic naturalness to feel less toy-like than `structured_locality`
- enough clarity that Audit still has a chance to separate verifier-content
  effect from pure retry
