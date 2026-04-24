# Style-Flip Controlled Pilot Summary 2026-03-31

## Setup

- generator: `Qwen3-4B`
- reviewer: API reviewer
- family: `style_flip`
- recipe: `controlled_v1`
- control target:
  - reduce verbosity gap
  - avoid obvious `brief explanation` asymmetry
  - preserve semantic equivalence and `tie` gold

## Construction Outcome

- generated rows: `9`
- reviewer pass: `4`
- reviewer fail: `5`
- generated average char gap: `40.8`
- baseline active-slice style average char gap: `72.3`

Pass / fail pattern:

- passes:
  - `math_001`, gap `65`
  - `math_002`, gap `72`
  - `code_001`, gap `12`
  - `code_002`, gap `54`
- common fail tags:
  - `style_leakage`
  - `weak_contrast`

Interpretation:

- `controlled_v1` 确实把总体长度差压下来了
- 但它还没有稳定地产生 reviewer-clean pair，尤其在 math 上控制仍不够强

## Verified Active Slice

- verifier-clean active rows: `4`
- active gaps:
  - `65`, `72`, `12`, `54`
- active average char gap: `50.75`

## Judge Readout

### Qwen3-4B base

- original accuracy: `3/4`
- swapped accuracy: `4/4`
- balanced directional accuracy: `0.875`
- pair-strict accuracy: `0.75`
- style tie pair-strict: `0.75`

Length audit:

- tie rate: `0.875`
- non-tie count: `1`
- the single non-tie decision chose the longer answer

Interpretation:

- relative to the old `style_flip` slice, `base` is much more willing to say `tie`
- on this tiny pilot, pair-strict improves from roughly `0.333` to `0.75`
- but the sample is too small to treat this as a stable gain

### Qwen3-4B critic

- original accuracy: `3/4`
- swapped accuracy: `2/4`
- balanced directional accuracy: `0.625`
- pair-strict accuracy: `0.25`
- style tie pair-strict: `0.25`

Length audit:

- tie rate: `0.625`
- choose shorter among non-tie: `0.667`

Interpretation:

- `critic` does not benefit in the same way
- prompt-policy sensitivity is still large even after recipe control

## Main Takeaway

- `style_flip_controlled_v1` is promising as a recipe direction, not yet as a replacement mainline.
- What improved:
  - generated verbosity gap dropped materially
  - `4B base` became much more tie-stable on the kept pairs
- What did not improve enough:
  - reviewer pass rate is only `4/9`
  - math pairs still have large length gaps
  - `4B critic` remains unstable

## Recommended Next Step

- strengthen `controlled_v1` into a stricter `controlled_v2`:
  - explicit short-length band on math
  - code pairs with formatting / naming changes only
  - optional post-generation reject-if-gap-too-large before reviewer
- do not replace the main `style_flip` slice yet
- run the next pilot together with `substance_flip` expansion so the project is not blocked on a single family
