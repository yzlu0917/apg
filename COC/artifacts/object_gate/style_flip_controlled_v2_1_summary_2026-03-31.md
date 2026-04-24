# Style-Flip Controlled-v2.1 Summary 2026-03-31

## Setup

- family: `style_flip`
- domain: `math`
- recipe: `controlled_v2.1`
- target:
  - keep both answers brief and prompt-symmetric
  - allow clearer surface style markers than `controlled_v2`

## Generation Outcome

- generated rows: `7`
- reviewer pass: `2`
- reviewer fail: `5`
- generated avg char gap: `28.9`

Comparison:

- `controlled_v2`: avg gap `34.7`, pass `0/7`
- `controlled_v2.1`: avg gap `28.9`, pass `2/7`

Passed pairs:

- `math_003__style_flip`, gap `10`
- `math_006__style_flip`, gap `1`

Representative kept pattern:

- `Three quarters of 20 is 15. Answer: 15.`
- `Three quarters of 20 equals 15. Final answer: 15.`

## Judge Readout On Kept Pairs

Verifier-clean active slice: `2`

### Qwen3-4B base

- original accuracy: `2/2`
- swapped accuracy: `2/2`
- balanced directional accuracy: `1.0`
- pair-strict accuracy: `1.0`
- length audit:
  - tie rate: `1.0`
  - avg kept gap: `5.5`

### Qwen3-4B critic

- original accuracy: `1/2`
- swapped accuracy: `2/2`
- balanced directional accuracy: `0.75`
- pair-strict accuracy: `0.5`
- length audit:
  - tie rate: `0.75`
  - the single non-tie decision chose the slightly longer answer

## Main Takeaway

- `controlled_v2.1` is the first controlled math recipe that is both:
  - reviewer-acceptable at nonzero rate
  - genuinely tie-stable for `4B base` on the kept pairs
- sample size is tiny, so this is a direction signal, not a claim-ready result

## Decision

- keep `controlled_v2.1` as the current best math-side style recipe
- next extend it carefully to:
  - more math seeds
  - then code seeds
- do not yet replace the full mainline `style_flip` slice
