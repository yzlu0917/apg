# Substance Seed Refresh Summary 2026-03-31

## Existing-Pool Check

Remaining old seeds:

- `math_triangle_area_001`
- `math_rectangle_perimeter_001`
- `math_division_001`
- `code_reverse_string_001`
- `code_unique_preserve_order_001`
- `code_count_uppercase_001`
- `code_first_nonzero_001`

Outcome:

- generated rows: `7`
- reviewer pass: `1`
- verifier-clean kept: `0`

Failure pattern:

- several rows degenerated into identical or still-correct pairs
- `code_first_nonzero_001` produced a plausible Python bug (`is not 0`) that passed reviewer but not the current verifier tests

Interpretation:

- the original 12-seed pool is close to exhausted for low-cost `substance_flip` growth
- continuing to mine only the old pool is low-yield

## New-Seed Refresh

Added four new seeds:

- `math_008`: `math_percentage_002`
- `math_009`: `math_linear_z_001`
- `code_006`: `code_count_negatives_001`
- `code_007`: `code_last_even_001`

Outcome:

- generated rows: `4`
- reviewer pass: `3`
- verifier-clean kept: `3`

Kept pairs:

- `math_009__substance_flip`
- `code_006__substance_flip`
- `code_007__substance_flip`

## Main Takeaway

- the bottleneck was mainly seed-pool exhaustion, not complete generator collapse
- a small seed refresh immediately restored `substance_flip` yield
- future substance work should favor adding compact objective seeds over repeatedly resampling the same old pool
