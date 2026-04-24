# Substance Targeted Growth v2 Summary 2026-03-31

## New Seeds

Added four additional compact objective seeds:

- `math_012`: `math_percentage_004`
- `math_013`: `math_linear_t_001`
- `code_010`: `code_count_odds_001`
- `code_011`: `code_last_positive_001`

## Targeted-v1 Outcome

Generator:

- `Qwen3-8B`

Audit path:

- API reviewer
- local verifier

Outcome:

- generated rows: `4`
- reviewer pass: `3`
- verifier-clean kept: `3`

Kept items:

- `math_013__substance_flip`
- `code_010__substance_flip`
- `code_011__substance_flip`

Rejected item:

- `math_012__substance_flip`
  - failed because the wrong answer still copied the correct reasoning and only changed the final token `15 -> 16`

## Main Takeaway

- `substance_flip_targeted_v1` reproduces the same `3/4` net growth on a second fresh-seed batch
- the protocol now looks stable enough to treat as the default substance expansion path
- remaining failures are localized to cases where the generator slips back to final-token corruption instead of intermediate-step corruption

