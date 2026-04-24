# Two-Branch Strategy

Date: 2026-04-07

## Purpose

Make the project's next phase explicit:

- keep one branch optimized for clarity
- open one branch optimized for naturalness

This avoids forcing a single branch to satisfy both goals at once.

## Branch A: `structured_locality`

Purpose:

- clean anchor branch
- exact object definition
- benchmark / audit / diagnostic value

Current status:

- Object gate: `GO`
- Audit: `empirical dev-slice entry, not full pass`

What it is good for:

- measuring whether verifier content can matter in a tightly controlled local
  repair object
- producing a clean benchmark or diagnosis paper even if broader method claims
  fail

Main weakness:

- narrow and checker-heavy

## Branch B: `semantic_locality`

Purpose:

- reduced-program-dependence branch
- closer-to-natural verifier object
- bridge from exact object work toward more realistic settings

Current status:

- design only
- Object gate: `not started`

What it is good for:

- testing whether the core idea survives weaker structure
- probing the external validity of `structured_locality`

Main weakness:

- much higher risk of drifting back into ambiguous objects and weak Audit

## Governance rule

The two branches should not be silently merged in evaluation or reporting.

Rules:

- `structured_locality` keeps its own panel, audit slice, and gate status
- `semantic_locality` starts from a new Object gate, not from inherited credit
- negative or partial results on one branch do not automatically transfer to
  the other

## Recommended next move

Short term:

- continue tightening `structured_locality` Audit controls
- define the first minimal object proposal for `semantic_locality`

Do not:

- open a large `semantic_locality` batch before its object rule is written
- treat `structured_locality` as the final deployment story
