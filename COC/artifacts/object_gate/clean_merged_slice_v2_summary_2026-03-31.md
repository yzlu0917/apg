# Clean Merged Slice v2 Summary 2026-03-31

## Setup

- slice: `object_dev_v0_clean_merged_slice_v2`
- total rows: `12`
- family mix:
  - `substance_flip = 8`
  - `style_flip = 4`
- style sources:
  - math: `controlled_v2.1`
  - code: `controlled_code_v1_1`

Compared with `clean_merged_slice_v1`, `v2` adds three new verifier-clean `substance_flip` rows:

- `math_009__substance_flip`
- `code_006__substance_flip`
- `code_007__substance_flip`

## Balanced Judge Readout

### Qwen3-0.6B base

- balanced directional accuracy: `0.333`
- pair-strict accuracy: `0.0`
- family pair-strict:
  - `substance_flip = 0.0`
  - `style_flip = 0.0`

### Qwen3-0.6B critic

- balanced directional accuracy: `0.333`
- pair-strict accuracy: `0.0`
- family pair-strict:
  - `substance_flip = 0.0`
  - `style_flip = 0.0`

### Qwen3-4B base

- balanced directional accuracy: `0.792`
- pair-strict accuracy: `0.583`
- family pair-strict:
  - `substance_flip = 0.375`
  - `style_flip = 1.0`
- balanced COC pair-strict: `0.688`

### Qwen3-4B critic

- balanced directional accuracy: `0.833`
- pair-strict accuracy: `0.667`
- family pair-strict:
  - `substance_flip = 0.625`
  - `style_flip = 0.75`
- balanced COC pair-strict: `0.688`

## Main Takeaway

- the low-capacity judges remain dominated by answer-order behavior: both `0.6B` variants still collapse to pair-strict `0.0`
- the high-capacity judges still separate clearly from `0.6B`, so the object signal remains real under the cleaner slice
- `style_flip` is no longer the main problem:
  - `4B base` is perfect on the audited style subset
  - `4B critic` drops only one style pair
- the primary bottleneck is now `substance_flip`, especially a small cluster of math items that still fail under swap-balanced reading

## Decision

- keep `clean_merged_slice_v2` as the current best audit-controlled merged slice
- treat `substance_flip` as the main target for the next refinement loop
- do not reopen broad style-recipe sweeping until the stubborn `substance_flip` pairs are understood
