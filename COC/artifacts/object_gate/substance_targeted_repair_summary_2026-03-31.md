# Substance Targeted Repair Summary 2026-03-31

## Problem

In `clean_merged_slice_v2`, several `substance_flip` math pairs were formally clean but still unstable under swap-balanced judge reading.

Representative failure mode:

- the wrong answer copied the correct reasoning almost verbatim
- only the final numeric token changed
- after answer-order swap, `4B` judges often kept choosing the first answer

So the issue was not family invalidity. It was a weak error locus.

## Targeted Repair

Added `substance_flip_targeted_v1` to [bootstrap_object_data.py](/cephfs/luyanzhen/apg/COC/scripts/bootstrap_object_data.py#L1):

- forbid wrong answers that only change the final numeric token or return value
- require the semantic mistake to appear in the intermediate reasoning step, operator, or condition
- for code, prefer prompt-opposite logic over subtle runtime artifacts

## Generator Check

### Qwen3-4B targeted generation

- targeted set: `math_003`, `math_006`, `math_007`, `math_009`, `code_006`
- reviewer pass: `1/5`
- verdict:
  - local `4B` still ignored the targeted math instruction
  - this was not enough to repair the stubborn math pairs

### Qwen3-8B targeted generation

- targeted set: `math_003`, `math_006`, `math_007`, `math_009`
- reviewer pass: `3/4`
- verifier-clean kept: `3/4`
- kept items:
  - `math_003__substance_flip`
  - `math_007__substance_flip`
  - `math_009__substance_flip`

These repaired pairs move the error into the intermediate step itself, for example:

- `math_003`: `(2/4) * 20 = 10`
- `math_007`: divide by `4` instead of `3`
- `math_009`: divide by `3` instead of `4`

## v2 -> v3 Slice Effect

Replacing the three stubborn math rows in the substance pool yields `clean_merged_slice_v3`.

High-capacity judge changes:

- `4B base`:
  - pair-strict: `0.583 -> 0.833`
  - substance pair-strict: `0.375 -> 0.75`
- `4B critic`:
  - pair-strict: `0.667 -> 0.917`
  - substance pair-strict: `0.625 -> 1.0`

## Main Takeaway

- the bottleneck was the location of the error, not just the presence of an error
- when the wrong answer is semantically wrong in the intermediate step, swap-balanced stability improves sharply
- current best interpretation:
  - `style_flip` is already sufficiently audited for this slice
  - `substance_flip` quality rises materially when repaired with targeted error-locus control
