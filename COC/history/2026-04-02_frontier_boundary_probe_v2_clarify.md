# 2026-04-02 Frontier Boundary Probe v2 Clarify

## What Changed

- 收紧了 `clarify_required` 的 gold rule，要求缺失信息必须导向多个具体输出。
- 新增了 `v2` clarify probe，并把子族显式拆成 `sample_space_missing / reference_frame_missing / convention_missing`。
- 用 strongest API `critic` 继续跑 paired original/swapped 评测。

## Main Outcome

- `clarify_required` 在更窄规则下仍然成立：balanced `pair-strict=0.5`。
- 但信号发生了重要分化：
  - `sample_space_missing = 1.0`
  - `reference_frame_missing = 0.333`
  - `convention_missing = 0.333`
- 这说明真正的 frontier-hard core 更像“hidden frame / convention changes the concrete output”，而不是泛泛的 clarify-first。
