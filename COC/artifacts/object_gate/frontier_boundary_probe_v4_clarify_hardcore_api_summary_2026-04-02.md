# Frontier Boundary Probe v4 Clarify Hardcore API Summary 2026-04-02

## Setup

- probe file: `data/raw/frontier_boundary_probe_v4_clarify_hardcore.jsonl`
- family: `clarify_required`
- judge backend: project API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`
- design intent: keep only the two hardest currently identified subtypes

## Balanced Readout

- total pairs: `8`
- balanced directional accuracy: `0.5625`
- pair-strict accuracy: `0.25`
- family pair-strict:
  - `clarify_required = 0.25`
- subfamily pair-strict:
  - `source_unit_missing = 0.25`
  - `date_convention_missing = 0.25`

## Interpretation

This is the strongest frontier-boundary result so far after the project pivot away from weak-model slices.

Compared with `v3 core-only`, the narrower `v4 hardcore-only` slice becomes substantially harder for the strongest current API judge:

- `v3 core-only`: pair-strict `0.6`
- `v4 hardcore-only`: pair-strict `0.25`

The main consequence is that the project no longer needs to describe the boundary as a broad `clarify_required` family. The current hard slice is much narrower:

- prompts with a culturally common default convention
- where that default changes the concrete output
- and where a stronger answer should surface the missing frame before committing

## Main Failure Pattern

The strongest current API judge still over-rewards direct answers when they align with a common default convention, especially for:

- source-unit defaults in temperature conversion
- locale defaults in short-date interpretation

This is not just a one-subtype effect. In `v4`, both hardest subtypes remain equally difficult under the paired readout.

## Decision

- treat `source_unit_missing + date_convention_missing` as the current best frontier-hard slice
- keep the broader `clarify_required` label only as an umbrella family
- start treating the working hard core as a narrower default-convention boundary inside `clarify_required`
