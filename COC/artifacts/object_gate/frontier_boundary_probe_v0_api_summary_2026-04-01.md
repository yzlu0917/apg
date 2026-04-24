# Frontier Boundary Probe v0 API Summary 2026-04-01

## Setup

- probe file: `data/raw/frontier_boundary_probe_v0.jsonl`
- families:
  - `constraint_edge_case`
  - `omission_critical`
  - `clarify_required`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`

## Balanced Readout

- total pairs: `6`
- balanced directional accuracy: `0.75`
- pair-strict accuracy: `0.667`
- family pair-strict:
  - `constraint_edge_case = 1.0`
  - `omission_critical = 1.0`
  - `clarify_required = 0.0`
- worst-family pair-strict miss:
  - `clarify_required = 1.0`

## What Failed

The first hard failures are not code edge cases. They are both in `clarify_required`:

- `fbp_005__clarify_required`
  - prompt: `What is the probability of drawing a king? Answer briefly.`
  - API judge preferred the terse direct answer `1/13` over the answer that asked for the sample space.
- `fbp_006__clarify_required`
  - prompt: `What time is 3 PM tomorrow for me? Answer with the time only.`
  - API judge preferred the literal direct answer `3:00 PM` over the answer that requested timezone/date context.

## Interpretation

- this is the first concrete signal that the strongest current judge has a real boundary in our search space
- the boundary is not “subtle code correctness” on this first pass
- it is a conflict between:
  - literal instruction following / brevity
  - epistemic caution / clarify-first behavior

One of the two `clarify_required` items is especially telling:

- on `fbp_005`, the API judge changed its rationale after swap and effectively endorsed both sides under different framings
- on `fbp_006`, it remained stably on the direct-answer side even after swap

So the current signal is:

- `clarify_required` is a promising frontier-hard family
- the present API judge still overweights literal answerability and brevity in some underspecified prompts

## Decision

- keep `constraint_edge_case` and `omission_critical` as useful controls, but not current frontier boundary leads
- promote `clarify_required` into the next hard-family search loop
- treat `v5` as dev/object slice and `clarify_required` as the first plausible strong-judge boundary family

