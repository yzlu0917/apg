# Expansion And Controlled-v2 Summary 2026-03-31

## 1. Substance-Flip New-Math Expansion

Seed expansion:

- total seeds: `12`
- math seeds: `7`
- newly added:
  - `math_005` / `math_division_001`
  - `math_006` / `math_percentage_001`
  - `math_007` / `math_linear_y_001`

Pilot result:

- generated rows: `3`
- reviewer pass: `2`
- verifier-clean kept: `2`
- kept items:
  - `math_006__substance_flip`
  - `math_007__substance_flip`

Takeaway:

- 扩 `substance_flip` 的 math seed 是有效路线
- 合并当前已通过的 substance pool 后，verifier-clean `substance_flip` 数量达到 `5`
- 这条线目前没有暴露新的 audit artifact，值得继续扩

## 2. Style-Flip Controlled-v2 Math Pilot

Setup:

- family: `style_flip`
- domain: `math`
- recipe: `controlled_v2`
- target gap: `<= 25` characters

Result:

- generated rows: `7`
- reviewer pass: `0`
- verifier-clean kept: `0`
- average char gap: `34.7`
- comparison to `controlled_v1` on math:
  - `v1` math avg gap: `60.5`
  - `v1` math pass: `2/4`
  - `v2` math avg gap: `34.7`
  - `v2` math pass: `0/7`

Common failure modes:

- `weak_contrast`
- `style_leakage`
- occasional `semantic_drift` / `reasoning_fix`

Interpretation:

- `controlled_v2` 成功压低了长度差
- 但它把 pair 压得过于相似，或者仍然落回“brief direct answer vs slight explanation”这种 reviewer 会拒的形态
- 当前 `controlled_v2` 是 overconstrained，不是最终 recipe

## Main Decision

- 保留新 math seeds，并继续扩 `substance_flip`
- `style_flip` 不继续盲跑 `controlled_v2`
- 下一版应做 `controlled_v2.1`：
  - 保持 brevity symmetry
  - 但允许更明确的表面 style marker
  - 避免把 contrast 压成纯同义改写
