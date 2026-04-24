# Frontier Boundary Probe v1 Clarify API Summary 2026-04-01

## Setup

- probe file: `data/raw/frontier_boundary_probe_v1_clarify.jsonl`
- family: `clarify_required`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`

## Balanced Readout

- total pairs: `8`
- balanced directional accuracy: `0.438`
- pair-strict accuracy: `0.25`
- family pair-strict:
  - `clarify_required = 0.25`
- worst-family pair-strict miss:
  - `clarify_required = 0.75`

## Main Failure Pattern

The API judge repeatedly prefers direct default answers over clarify-first answers in underspecified prompts.

Examples:

- `fbc_001`: `What is the probability of drawing a king?`
  - judge often prefers `1/13`
- `fbc_003`: `Convert 100 degrees to Fahrenheit.`
  - judge often prefers `212 F`
- `fbc_005`: `If I start counting from 0, what is the 5th index?`
  - judge often prefers `4`
- `fbc_008`: `What is the pass rate?`
  - judge often prefers a generic formula answer over asking for the actual counts

It also shows a weaker but notable pattern:

- on some items it shifts under swap without becoming pair-stable
- on `fbc_006`, it abstains into `tie` rather than clearly rewarding the clarify-first answer

## Interpretation

- `clarify_required` is no longer just a two-item curiosity; it now looks like a real frontier-hard family
- the current strongest judge is not merely “bad at ambiguity” in a vague sense
- more specifically, it tends to reward:
  - literal directness
  - default assumptions
  - answer completion
  over
  - epistemic caution
  - explicit identification of missing context

## Decision

- promote `clarify_required` to the current main strong-judge boundary family
- treat `v1` as the first real frontier-boundary slice, even though it is still small
- next step should be to tighten the gold rule further and expand this family before searching for additional frontier-hard families

