# Style-Flip Controlled-Code-v1.1 Summary 2026-03-31

## Setup

- family: `style_flip`
- domain: `code`
- recipe: `controlled_code_v1_1`
- target:
  - keep same-structure code pairs
  - tighten length gap
  - reject large loop-vs-comprehension rewrites that were unstable in `controlled_code_v1`

## Generation Outcome

- generated rows: `5`
- reviewer pass: `2`
- reviewer fail: `3`
- generated avg char gap: `32.4`
- verifier-clean kept: `2`

Kept pairs:

- `code_003`: neutral variable naming contrast, gap=`9`
- `code_005`: neutral variable naming + light layout contrast, gap=`6`

Comparison against `controlled_code_v1`:

- `controlled_code_v1`: reviewer pass=`4/5`, verifier-clean kept=`4`, generated avg gap=`34.4`
- `controlled_code_v1_1`: reviewer pass=`2/5`, verifier-clean kept=`2`, generated avg gap=`32.4`

So `v1.1` is not a higher-yield recipe. It is a stricter clean-subset recipe.

## Judge Readout

### Qwen3-4B base

- balanced directional accuracy: `1.0`
- pair-strict accuracy: `1.0`

### Qwen3-4B critic

- balanced directional accuracy: `1.0`
- pair-strict accuracy: `1.0`

Length audit:

- tie rate: `1.0`
- non-tie decisions: `0`
- kept-pair avg char gap: `7.5`

## Main Takeaway

- `controlled_code_v1_1` successfully removes the unstable high-gap loop-vs-comprehension pairs seen in `controlled_code_v1`.
- The remaining subset is small, but both `4B base` and `4B critic` are fully swap-stable on it.
- This makes `controlled_code_v1_1` the current best clean code-side style subset, not the default high-yield generator recipe.

## Decision

- keep `controlled_code_v1` as the current best-yield code recipe
- keep `controlled_code_v1_1` as the current best clean-subset code recipe
- next merged slice should prefer:
  - `controlled_v2.1` for math-side style pairs
  - `controlled_code_v1_1` when audit cleanliness matters
  - `controlled_code_v1` only when expanding code-side candidate yield
