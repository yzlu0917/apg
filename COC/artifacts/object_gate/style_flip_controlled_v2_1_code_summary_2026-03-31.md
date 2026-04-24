# Style-Flip Controlled-v2.1 Code Summary 2026-03-31

## Setup

- family: `style_flip`
- domain: `code`
- recipe: `controlled_v2.1`
- target:
  - code-only answers
  - light formatting / naming / comment differences
  - no explanation paragraphs

## Generation Outcome

- generated rows: `5`
- reviewer pass: `1`
- reviewer fail: `4`
- generated avg char gap: `48.4`
- verifier-clean kept: `1`

Failure pattern:

- reviewer repeatedly marked:
  - `style_leakage`
  - `weak_contrast`
- typical failure: identical code plus one trivial comment line

Representative failure:

- `code_001`: plain function vs same function with one comment
- `code_003`: same code plus two trivial comments

Reviewer interpretation:

- trivial comments are not a meaningful style contrast
- but they still add visible length gap, so the pair is neither clean nor well controlled

## Kept Pair

- kept item: `code_005__style_flip`
- gap: `66`
- style difference: one explanatory comment line

This kept pair is not strong enough to define the recipe; it is better read as a permissive reviewer edge case than a robust controlled-code pattern.

## Judge Readout On The Kept Pair

### Qwen3-4B base

- original accuracy: `1/1`
- swapped accuracy: `1/1`
- balanced pair-strict: `1.0`
- tie rate: `1.0`

### Qwen3-4B critic

- original accuracy: `1/1`
- swapped accuracy: `0/1`
- balanced pair-strict: `0.0`
- non-tie choice on swapped order: chooses shorter answer

## Main Takeaway

- `controlled_v2.1` does not yet transfer cleanly to code.
- The current code recipe collapses into:
  - comment-vs-no-comment
  - large length gap with weak style contrast
- This is not a good mainline code-side `style_flip`.

## Decision

- keep `controlled_v2.1` as the best math-side style recipe only
- do not migrate the same recipe unchanged to code
- next code-side recipe should use clearer code-style markers, such as:
  - compact one-liner vs expanded multi-line layout
  - neutral variable naming contrast
  - mirrored harmless comments on both sides rather than comment-vs-no-comment
