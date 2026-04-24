# Contrastive Locality Judge V4 Assessment

Date: 2026-03-31

## Headline

`judge_v4` is the first version that aligns cleanly with the current human
review ledger on the 10 reviewed `contrastive_locality` pairs.

Compared with `v3.2`:

- accepted set now matches human review exactly
- `code_1501_0` is no longer a false positive
- code-side checker undercoverage is now screened with execution-backed probe
  disagreement against a synthesized reference oracle

## Current result shape

- judged pairs: `10`
- accepts: `2`
- rejects: `8`
- auto rejects: `5`
- model with program findings: `5`

Accepted pairs:

- `code_contrastive_locality_0`
- `plan_contrastive_locality_0`

## What improved

- code pairs now get a synthesized reference implementation from the task text
  alone
- probe inputs are generated from written test literals by structured mutation
- keep, revise, and heuristic nearby repairs are compared against the
  synthesized reference on those probes
- this lets the judge reject checker-undercovered code pairs even when the
  written unit tests are too weak

## Key catch

The most important new correction is `code_1501_0`.

- prior human review rejected it because the written tests missed mixed-sign odd
  inputs
- `judge_v3.2` still accepted it
- `judge_v4` rejects it because the keep trace disagrees with the synthesized
  reference on probe `[[-1, -3, -5, -7]]`

This is the clearest sign that execution-backed code semantics closed a real
gap rather than just making the judge stricter.

## Remaining limitations

- `judge_v4` still only validates the current narrow code and plan patterns
- the synthesized reference oracle is model-produced, so it is best used as a
  veto aid rather than a standalone freeze criterion
- accepted pairs still require human review before they can enter any frozen
  panel

## Operational conclusion

`judge_v4` is now the best default pre-screen for `contrastive_locality`.

Recommended usage:

- use `judge_v4` as the default veto pre-screen for new batches
- continue to require human review for every accepted pair
- if this family continues, the next leverage point is better generation
  quality, not more judge-side prompt patching
