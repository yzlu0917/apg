# Clean Merged Slice v5 Full-Panel Summary 2026-04-01

## Setup

- slice: `object_dev_v0_clean_merged_slice_v5`
- total rows: `18`
- family mix:
  - `substance_flip = 14`
  - `style_flip = 4`
- panel:
  - `Qwen3-0.6B base`
  - `Qwen3-0.6B critic`
  - `Qwen3-4B base`
  - `Qwen3-4B critic`

This is the first fully matched cross-capacity readout for `v5`.

## Balanced Panel Readout

### Qwen3-0.6B base

- balanced directional accuracy: `0.389`
- pair-strict accuracy: `0.0`
- balanced COC pair-strict: `0.0`

### Qwen3-0.6B critic

- balanced directional accuracy: `0.389`
- pair-strict accuracy: `0.0`
- balanced COC pair-strict: `0.0`

### Qwen3-4B base

- balanced directional accuracy: `0.917`
- pair-strict accuracy: `0.833`
- balanced COC pair-strict: `0.893`

### Qwen3-4B critic

- balanced directional accuracy: `0.972`
- pair-strict accuracy: `0.944`
- balanced COC pair-strict: `0.875`

## Main Comparison

- `v5` preserves the same strong capacity split already seen on `v3`
- low-capacity judges still collapse under swap-balanced evaluation
- high-capacity judges remain strong on the larger merged slice

Compared with `v3`:

- `0.6B base`: pair-strict `0.0 -> 0.0`
- `0.6B critic`: pair-strict `0.0 -> 0.0`
- `4B base`: pair-strict `0.833 -> 0.833`
- `4B critic`: pair-strict `0.917 -> 0.944`

## Interpretation

- `v5` does not look like generic slice easing, because the extra rows do not rescue `0.6B`
- instead, the enlargement continues to benefit only the higher-capacity judges
- this makes `v5` a stronger matched-slice candidate than `v3`, since it is larger while preserving the same cross-cap separation

## Decision

- treat `clean_merged_slice_v5` as the current best fully matched audit-controlled slice
- move the project focus from additional local sweep to paper-facing comparison and table-making

