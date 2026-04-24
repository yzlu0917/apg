# 2026-03-31 Order-Balanced Audit

## What Changed

- 新增 `scripts/compute_balanced_judge_metrics.py`，把 `original + swapped` judge 输出聚合成 order-balanced 指标。
- 在 `v3` active slice 上补算 balanced directional 与 pair-strict 结果。
- 将 future evaluation 协议冻结为 order-balanced paired readout，而不是继续依赖单边 accuracy。

## Why

- 第一轮 `order-swap audit` 已经确认当前 judge 存在明显顺序敏感性。
- 如果继续只看单边 `overall accuracy / COC`，会把 protocol artifact 和 object signal 混在一起。

## Main Outcome

- `Qwen3-0.6B` 在 pair-strict 下为 `0.0`，说明其 object 读数基本不可用。
- `Qwen3-4B` 在 pair-strict 下为 `0.417`，说明 object signal 经 order control 后仍存在，但明显比 unbalanced 读法更窄。
- `4B base` 与 `4B critic` 的差距在 balanced 读法下被压缩，prompt-style effect 暂时不能升格为强结论。
