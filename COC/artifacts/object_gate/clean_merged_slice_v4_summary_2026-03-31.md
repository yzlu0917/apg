# Clean Merged Slice v4 Summary 2026-03-31

## Setup

- slice: `object_dev_v0_clean_merged_slice_v4`
- total rows: `15`
- family mix:
  - `substance_flip = 11`
  - `style_flip = 4`
- change from `v3`:
  - added `math_011`, `code_008`, `code_009` as new targeted `substance_flip` rows

## Balanced 4B Readout

### Qwen3-4B base

- balanced directional accuracy: `0.933`
- pair-strict accuracy: `0.867`
- family pair-strict:
  - `substance_flip = 0.818`
  - `style_flip = 1.0`
- balanced COC pair-strict: `0.909`

### Qwen3-4B critic

- balanced directional accuracy: `0.967`
- pair-strict accuracy: `0.933`
- family pair-strict:
  - `substance_flip = 1.0`
  - `style_flip = 0.75`
- balanced COC pair-strict: `0.875`

## Comparison

- vs `v3`:
  - `4B base` pair-strict: `0.833 -> 0.867`
  - `4B critic` pair-strict: `0.917 -> 0.933`
  - `4B base` substance pair-strict: `0.75 -> 0.818`
  - `4B critic` substance pair-strict: `1.0 -> 1.0`

## Main Takeaway

- the targeted substance path scales at least one step further without collapsing
- expanding from `12` to `15` rows does not erase the gains from `v3`
- current high-capacity bottleneck is now very narrow:
  - `4B base`: `math_006` and `code_006`
  - `4B critic`: only the remaining `math_006__style_flip` miss

## Scope Note

- this `v4` summary is currently high-capacity only
- a matched `0.6B` rerun can be added later if this slice becomes a paper-facing candidate
