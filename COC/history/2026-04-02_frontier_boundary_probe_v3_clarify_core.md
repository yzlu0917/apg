# 2026-04-02 Frontier Boundary Probe v3 Clarify Core

## What Changed

- 将 `clarify_required` 的工作集收窄到 `v3 core-only`，不再混入当前已接近 control 的广义 clarify 子族。
- 在 family note 中新增 `v3` 的主工作集说明，并显式拆成 `source_unit_missing / timezone_reference_missing / date_convention_missing / measurement_convention_missing / clock_convention_missing`。
- 新建 `frontier_boundary_probe_v3_clarify_core`，并继续用 strongest API `critic` 跑 paired original/swapped 评测。

## Main Outcome

- `clarify_required` 在 `v3 core-only` 上仍然没有被 strongest judge 吃满：balanced `pair-strict=0.6`。
- 但 hardest core 进一步集中，不再平均分布在所有 clarify 子族上：
  - `source_unit_missing = 0.0`
  - `date_convention_missing = 0.333`
  - `timezone_reference_missing = 1.0`
  - `measurement_convention_missing = 1.0`
  - `clock_convention_missing = 1.0`
- 这说明 strongest API judge 当前最稳定的 frontier boundary，不是泛化的“clarify before reasoning”，而是更窄的：
  - 在存在常见默认约定时，是否仍会先暴露缺失 frame，而不是直接按默认约定作答。
