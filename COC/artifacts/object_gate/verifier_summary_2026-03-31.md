# Verifier Summary 2026-03-31

## Verified Samples

### Math

- `math_001__substance_flip`: verifier prefers `A`, gold consistent
- `math_001__style_flip`: verifier prefers `tie`, gold consistent
- `math_001__reasoning_fluff`: verifier prefers `tie`, gold inconsistent

### Code

- `code_001__substance_flip`: verifier prefers `A`, gold consistent
- `code_001__style_flip`: verifier prefers `tie`, gold consistent
- `code_001__reasoning_fluff`: verifier prefers `tie`, gold inconsistent
- `code_002__substance_flip`: verifier prefers `A`, gold consistent
- `code_002__style_flip`: verifier prefers `tie`, gold consistent
- `code_002__reasoning_fluff`: verifier prefers `tie`, gold inconsistent
- `code_003__reasoning_fluff`: verifier prefers `tie`, gold inconsistent

## Takeaway

- `style_flip` is verifier-clean in the current bootstrap slice.
- `substance_flip` is verifier-clean on current kept samples, though some code cases still need tighter reviewer wording.
- `reasoning_fluff` is not verifier-clean in the current bootstrap slice and is therefore deferred.
