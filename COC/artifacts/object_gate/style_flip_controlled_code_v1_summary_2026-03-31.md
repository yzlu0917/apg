# Style-Flip Controlled-Code-v1 Summary 2026-03-31

## Setup

- family: `style_flip`
- domain: `code`
- recipe: `controlled_code_v1`
- target:
  - code-only answers
  - meaningful but harmless code-style contrast
  - avoid comment-vs-no-comment degeneration

## Generation Outcome

- generated rows: `5`
- reviewer pass: `4`
- reviewer fail: `1`
- generated avg char gap: `34.4`
- verifier-clean kept: `4`

Kept pairs:

- `code_001`: generator expression vs explicit loop
- `code_003`: neutral variable naming contrast
- `code_004`: comprehension-like sum vs explicit counter loop
- `code_005`: `n` vs `num`

This is materially better than `controlled_v2.1` on code, which only kept `1/5`.

## Judge Readout

### Qwen3-4B base

- original accuracy: `4/4`
- swapped accuracy: `2/4`
- balanced directional accuracy: `0.75`
- pair-strict accuracy: `0.5`

### Qwen3-4B critic

- original accuracy: `4/4`
- swapped accuracy: `2/4`
- balanced directional accuracy: `0.75`
- pair-strict accuracy: `0.5`

Length audit:

- tie rate: `0.75`
- non-tie decisions all choose the shorter answer
- the unstable pairs are:
  - `code_001`
  - `code_004`

## Main Takeaway

- `controlled_code_v1` is the first code-side style recipe that is clearly reviewer-acceptable and verifier-clean at useful scale.
- But it still does not fully pass audit:
  - two loop-vs-comprehension style pairs flip under order swap
  - swapped non-tie choices favor the shorter answer

## Decision

- adopt `controlled_code_v1` as the current best code-side style recipe
- do not yet treat it as fully audited
- next refinement should target the unstable subset:
  - reduce length gap for loop-vs-comprehension pairs
  - keep structural contrast while making both sides equally terse
