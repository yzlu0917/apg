# 2026-04-01 Object Gate Synthesis

## What Changed

- 将 `v2/v3/v4/v5` 的 object-gate 主结果整理成 paper-facing comparison table。
- 基于 `v5` fullpanel 结果重写了 object-gate memo。
- 明确 `v5` 取代 `v3` 成为当前 best fully matched reference slice。

## Main Outcome

- 现在可以用一张简洁表格解释 `v2 -> v5` 的演化路径，而不再依赖分散的 run summaries。
- 当前 headline slice 选择规则已经明确：
  - 优先 audited
  - 优先 fully matched
  - 优先保留 capacity split 的更大 slice
- 因此 `v5` 是当前 paper-facing object claim 的最佳承载体，`v3` 退居 first-breakthrough supporting role。

