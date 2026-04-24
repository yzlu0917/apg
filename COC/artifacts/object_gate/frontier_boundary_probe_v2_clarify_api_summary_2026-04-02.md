# Frontier Boundary Probe v2 Clarify API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v2_clarify.jsonl`
- family: `clarify_required`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`

## Balanced Readout

- total pairs: `8`
- balanced directional accuracy: `0.625`
- pair-strict accuracy: `0.5`
- family pair-strict:
  - `clarify_required = 0.5`
- subfamily pair-strict:
  - `sample_space_missing = 1.0`
  - `reference_frame_missing = 0.333`
  - `convention_missing = 0.333`

## Interpretation

- tightening the gold rule did not erase the frontier boundary
- but it made the boundary more specific
- the strongest current API judge is no longer failing broadly on every kind of underspecification
- instead, the persistent misses are concentrated in:
  - `reference_frame_missing`
  - `convention_missing`

This is a useful refinement:

- `sample_space_missing` may be too easy or too culturally standardized to remain a frontier-hard subtype
- the stronger remaining signal is on prompts where a hidden frame or convention changes the concrete output

## Main Failure Pattern

The current API judge still tends to reward direct default answers in prompts such as:

- unit conversion without a specified source unit
- ambiguous date-format convention
- ambiguous indexing convention

Compared with `v1`, the new read is narrower and cleaner:

- `v1` showed a broad `clarify_required` signal
- `v2` shows that the real hard core is not all clarify-first cases, but specifically underdetermined prompts with concrete-output ambiguity

## Decision

- keep `clarify_required` as the main frontier-hard family
- narrow the working core further toward:
  - `reference_frame_missing`
  - `convention_missing`
- demote `sample_space_missing` from core hard subtype to secondary/control subtype unless later expansions revive it
