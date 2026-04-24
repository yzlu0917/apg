# Clean Merged Slice v5 Summary 2026-03-31

## Setup

- slice: `object_dev_v0_clean_merged_slice_v5`
- total rows: `18`
- family mix:
  - `substance_flip = 14`
  - `style_flip = 4`
- change from `v4`:
  - added `math_013`, `code_010`, `code_011` as new targeted `substance_flip` rows

## Balanced 4B Readout

### Qwen3-4B base

- balanced directional accuracy: `0.917`
- pair-strict accuracy: `0.833`
- family pair-strict:
  - `substance_flip = 0.786`
  - `style_flip = 1.0`
- balanced COC pair-strict: `0.893`

### Qwen3-4B critic

- balanced directional accuracy: `0.972`
- pair-strict accuracy: `0.944`
- family pair-strict:
  - `substance_flip = 1.0`
  - `style_flip = 0.75`
- balanced COC pair-strict: `0.875`

## Comparison

- vs `v4`:
  - `4B base` pair-strict: `0.867 -> 0.833`
  - `4B critic` pair-strict: `0.933 -> 0.944`
  - `4B base` substance pair-strict: `0.818 -> 0.786`
  - `4B critic` substance pair-strict: `1.0 -> 1.0`

## Main Takeaway

- `substance_flip_targeted_v1` still scales one step further on fresh rows without collapsing the merged slice
- `4B critic` remains perfect on the larger substance subset
- `4B base` is robust but not monotonic, so the honest readout is stability-with-some-residual-hard-pairs rather than smooth saturation

## Remaining High-Cap Failures

- `4B base`:
  - `math_006__substance_flip`
  - `code_006__substance_flip`
  - `code_011__substance_flip`
- `4B critic`:
  - `math_006__style_flip`

## Scope Note

- this `v5` summary is currently high-capacity only
- the next decision is whether `v5` deserves a matched `0.6B` rerun or whether the project should move directly to table-making with `v2/v3/v4/v5`

