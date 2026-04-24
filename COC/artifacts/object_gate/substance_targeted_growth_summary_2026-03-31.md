# Substance Targeted Growth Summary 2026-03-31

## New Seeds

Added four compact objective seeds:

- `math_010`: `math_percentage_003`
- `math_011`: `math_linear_x_002`
- `code_008`: `code_count_positives_001`
- `code_009`: `code_first_even_001`

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

- `math_011__substance_flip`
- `code_008__substance_flip`
- `code_009__substance_flip`

## Main Takeaway

- `substance_flip_targeted_v1` is not just a repair trick for old failures
- it also produces net-new verifier-clean substance rows on fresh seeds
- this is now the default growth path for expanding the substance pool
