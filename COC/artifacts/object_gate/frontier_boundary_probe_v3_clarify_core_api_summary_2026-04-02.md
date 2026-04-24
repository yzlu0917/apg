# Frontier Boundary Probe v3 Clarify Core API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v3_clarify_core.jsonl`
- family: `clarify_required`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: drop broad clarify cases and keep only the current hard-core subtypes

## Balanced Readout

- total pairs: `10`
- balanced directional accuracy: `0.7`
- pair-strict accuracy: `0.6`
- family pair-strict:
  - `clarify_required = 0.6`
- subfamily pair-strict:
  - `source_unit_missing = 0.0`
  - `date_convention_missing = 0.333`
  - `timezone_reference_missing = 1.0`
  - `measurement_convention_missing = 1.0`
  - `clock_convention_missing = 1.0`

## Interpretation

`v3` does not make the whole family uniformly harder. Instead, it isolates the real hard core more sharply:

- `source_unit_missing` is currently the strongest stable failure mode.
- `date_convention_missing` still contains non-trivial misses.
- `timezone_reference_missing`, `measurement_convention_missing`, and `clock_convention_missing` look more like controls in this round.

This is a useful refinement rather than a setback. The project goal is not to keep a broad family artificially hard, but to identify the narrowest audited subtype that still exposes a frontier boundary.

## Main Failure Pattern

The strongest current API judge still defaults to a concrete answer when the prompt leaves room for multiple legitimate outputs, especially when there is a culturally common default:

- omitted temperature source unit (`100 degrees`, `0 degrees`)
- ambiguous short date strings (`10/11/12`, `01/02/03`)

In these cases the judge often rewards a direct answer justified by a common convention, instead of rewarding the answer that first surfaces the missing frame.

## Decision

- keep `clarify_required` as the main frontier-hard family
- narrow its hard core further toward:
  - `source_unit_missing`
  - `date_convention_missing`
- demote the following from hard-core status for now:
  - `timezone_reference_missing`
  - `measurement_convention_missing`
  - `clock_convention_missing`
