# Frontier Boundary Probe v5 Default Convention API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v5_default_convention.jsonl`
- family umbrella: `clarify_required`
- working object: `default-convention boundary`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: fresh mixed slice with new prompts under `source_unit_missing + date_convention_missing`

## Balanced Readout

- total pairs: `8`
- balanced directional accuracy: `0.625`
- pair-strict accuracy: `0.375`
- subfamily pair-strict:
  - `source_unit_missing = 0.0`
  - `date_convention_missing = 0.75`

## Interpretation

The fresh mixed slice still exposes a non-trivial strong-judge boundary, but the two subtypes do not behave identically in this round.

- `source_unit_missing` replicates very strongly and remains the most stable failure mode.
- `date_convention_missing` looks easier in this mixed slice than it did in `v4`.

This does not yet demote `date_convention_missing`; it only means the recipe matters. The next question is whether a narrower fresh date-only recipe restores the strong signal.

## Decision

- keep `source_unit_missing` as the most stable current hard subtype
- do not yet demote `date_convention_missing`
- immediately test a narrower fresh date-only recipe
