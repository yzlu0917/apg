# Frontier Boundary Probe v8 Date Convention Compact API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v8_date_convention_compact.jsonl`
- family umbrella: `clarify_required`
- working object: `default-convention boundary`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: fresh compact date-only replication using direct ISO conversion

## Balanced Readout

- total pairs: `4`
- balanced directional accuracy: `0.125`
- pair-strict accuracy: `0.0`
- subfamily pair-strict:
  - `date_convention_missing = 0.0`

## Interpretation

This is a clean replication of the `v6` date-side result on a fresh set of compact short-date strings.

The strongest current API judge is still heavily attracted to direct ISO conversions that silently adopt a default date convention. Under the paired readout, the compact date recipe remains maximally hard in this round.

## Decision

- treat compact short-date ISO conversion as a replicated hard recipe
- keep `date_convention_missing` as a core validated subtype of the current `default-convention boundary`
