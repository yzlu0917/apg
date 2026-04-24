# Frontier Boundary Probe v6 Date Convention API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v6_date_convention.jsonl`
- family umbrella: `clarify_required`
- working object: `default-convention boundary`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: fresh date-only slice using compact ambiguous short-date strings

## Balanced Readout

- total pairs: `4`
- balanced directional accuracy: `0.125`
- pair-strict accuracy: `0.0`
- subfamily pair-strict:
  - `date_convention_missing = 0.0`

## Interpretation

The date-convention subtype remains genuinely frontier-hard when the recipe is tightened around compact short-date strings with direct ISO conversion.

This resolves the ambiguity from `v5`:

- `date_convention_missing` was not disappearing
- the weaker `v5` readout was recipe-sensitive
- the narrower compact-date recipe restores a very strong failure signal

## Decision

- keep `date_convention_missing` as a core hard subtype
- treat compact short-date ISO conversion as the current best date-side recipe
- keep `source_unit_missing + compact date_convention_missing` as the current best working object
