# 2026-04-02 Frontier Boundary Probe v8 Date Convention Compact

## What Changed

- 新建 fresh compact `date-only` replication，只保留短日期串直接转 ISO 的最强 recipe。
- 用 strongest API `critic` 跑 paired original/swapped 评测。
- 同步更新 `default-convention boundary` 的 object memo 与短版主文 wording。

## Main Outcome

- `v8 compact-date` 的 balanced `pair-strict=0.0`，与 `v6` 一致，说明 compact `date_convention_missing` 已经是一个重复验证过的 hard recipe。
- 结合 `v7 source-unit-only`，当前 strongest-judge object 已经可以更稳地写成：judge 会奖励依赖常见 source-unit 或 date-format 默认约定的直接答案。
