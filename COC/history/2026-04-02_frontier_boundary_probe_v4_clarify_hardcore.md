# 2026-04-02 Frontier Boundary Probe v4 Clarify Hardcore

## What Changed

- 在 `v3 core-only` 的基础上，进一步只保留 strongest judge 当前最硬的两类子族：`source_unit_missing` 与 `date_convention_missing`。
- 新建 `frontier_boundary_probe_v4_clarify_hardcore`，用 strongest API `critic` 继续跑 paired original/swapped 评测。
- 本轮不再测试已经接近 control 的 clarify 子族，目标是确认 hardest slice 是否真的能进一步压低 strongest judge 的稳定性。

## Main Outcome

- `v4 hardcore-only` 的 balanced `pair-strict` 下降到 `0.25`，显著低于 `v3 core-only` 的 `0.6`。
- 两个保留下来的 hardest 子族在 paired 读法下都同样硬：
  - `source_unit_missing = 0.25`
  - `date_convention_missing = 0.25`
- 这说明 strongest API judge 当前最真实的 frontier boundary 已经不只是宽泛的 `clarify_required`，而是更窄的：
  - 在存在常见默认约定时，是否仍能优先暴露缺失 frame，而不是直接按默认约定给出具体答案。
