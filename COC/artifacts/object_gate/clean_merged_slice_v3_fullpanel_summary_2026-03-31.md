# Clean Merged Slice v3 Full-Panel Summary 2026-03-31

## Setup

- slice: `object_dev_v0_clean_merged_slice_v3`
- total rows: `12`
- family mix:
  - `substance_flip = 8`
  - `style_flip = 4`
- panel:
  - `Qwen3-0.6B base`
  - `Qwen3-0.6B critic`
  - `Qwen3-4B base`
  - `Qwen3-4B critic`

This is the first fully matched cross-capacity readout for `v3`.

## Balanced Panel Readout

### Qwen3-0.6B base

- balanced directional accuracy: `0.333`
- pair-strict accuracy: `0.0`
- balanced COC pair-strict: `0.0`

### Qwen3-0.6B critic

- balanced directional accuracy: `0.333`
- pair-strict accuracy: `0.0`
- balanced COC pair-strict: `0.0`

### Qwen3-4B base

- balanced directional accuracy: `0.917`
- pair-strict accuracy: `0.833`
- balanced COC pair-strict: `0.875`

### Qwen3-4B critic

- balanced directional accuracy: `0.958`
- pair-strict accuracy: `0.917`
- balanced COC pair-strict: `0.875`

## Main Comparison

- targeted repair materially improved the high-capacity judges
- the low-capacity judges did not improve at all

In other words:

- `0.6B` remains dominated by answer-order behavior
- `4B` substantially benefits from the repaired substance error locus

## Interpretation

- this strongly supports the claim that the `v3` gain is not just because the slice became easier
- if the slice had simply become easier in a generic way, `0.6B` should also have improved
- instead, the improvement is capacity-sensitive:
  - higher-capacity judges can use the repaired intermediate-step errors
  - low-capacity judges still collapse under swap-balanced evaluation

## Decision

- treat `clean_merged_slice_v3` as the current best fully matched audit-controlled slice
- keep `substance_flip_targeted_v1` as the default repair path for future stubborn substance items
