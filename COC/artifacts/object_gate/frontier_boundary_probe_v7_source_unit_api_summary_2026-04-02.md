# Frontier Boundary Probe v7 Source Unit API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v7_source_unit.jsonl`
- family umbrella: `clarify_required`
- working object: `default-convention boundary`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: fresh source-unit-only replication probe

## Balanced Readout

- total pairs: `4`
- balanced directional accuracy: `0.25`
- pair-strict accuracy: `0.25`
- subfamily pair-strict:
  - `source_unit_missing = 0.25`

## Interpretation

This confirms that `source_unit_missing` is not a one-off effect tied to earlier numbers. On a fresh source-unit-only slice, the strongest current API judge still fails heavily under the paired readout.

The failure is also not primarily a position artifact:

- original accuracy: `1/4`
- swapped accuracy: `1/4`
- three items are wrong in both orders

## Decision

- treat `source_unit_missing` as the most stable current hard subtype
- use it as the anchor recipe for the current `default-convention boundary`
