# 2026-03-31 Style-Flip Controlled-v2.1

## What Changed

- 在 `bootstrap_object_data.py` 中新增 `style_flip controlled_v2.1`。
- 对 math seeds 跑了一轮 `controlled_v2.1` pilot，并对 verifier-clean 子集做了 swap-balanced judge 检查。

## Why

- `controlled_v2` 已经证明“更短、更对称”是对的，但也证明单纯继续加严会把通过率压到零。
- 需要一个介于 `v1` 和 `v2` 之间、能保留可审 style marker 的带宽。

## Main Outcome

- `controlled_v2.1` 在 math 上恢复到 `2/7` reviewer pass。
- 这两条 kept pairs 的平均 gap 只有 `5.5`。
- `4B base` 在这两条上 swap-balanced `pair-strict=1.0`，说明 recipe 方向可行。
