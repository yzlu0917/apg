# Contrastive Locality Judge V3.1 Assessment

Date: 2026-03-31

## Headline

`judge_v3.1` is better treated as a high-precision veto tool than as a
standalone acceptor.

It now combines:

- execution-backed code checks
- structured plan checks for simple order-style cases
- model judgment only after attaching program findings

## What improved

- obvious code checker failures are now auto-rejected:
  - `code_contrastive_locality_1202_harder_1`
  - `code_contrastive_locality_1301_harder`
  - `code_1601_0`
- obvious plan boundary failures are now auto-rejected:
  - `plan_1501_0`
- the earlier false structural auto-reject on batch12 plan disappeared after
  tightening order-style detection
- `code_1501_0` is preserved as the only current `accept`, which is more
  consistent with the execution evidence than `judge_v2`

## Current result shape

- judged pairs: `10`
- accepts: `1`
- rejects: `9`
- auto rejects: `4`
- model-with-program-findings: `6`

## Interpretation

This is not yet a good ranking model for finding new positives.

It is useful for:

- vetoing obviously inconsistent code pairs
- vetoing plan pairs whose revise trace is actually valid
- vetoing simple order cases with multiple checker-valid total orders

It is still weak at:

- distinguishing genuinely good code pairs from merely narrow ones
- handling schedule-style plan cases where constraints are partly implicit
- deciding whether the family should require multiple checker-valid nearby
  repairs or merely nearby plausible wrong repairs

## Operational recommendation

Use `judge_v3.1` like this:

- `reject`: drop before human review
- `accept`: still send to human review

Do not use `judge_v3.1` acceptance rate itself as the Object-gate metric.
