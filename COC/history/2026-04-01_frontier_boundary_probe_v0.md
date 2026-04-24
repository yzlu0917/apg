# 2026-04-01 Frontier Boundary Probe v0

## What Changed

- 正式把主线从“小模型分界”切到“强 judge 边界搜索”。
- 新增 `frontier_boundary_search_2026-04-01.md` 和一版手工 `frontier_boundary_probe_v0`。
- 用 API `critic` 按 paired original/swapped 协议跑了第一轮 hard-family probe。

## Main Outcome

- 第一轮 probe 已经找到非平凡强 judge 边界信号：
  - API `critic` 在整批 probe 上只有 balanced `pair-strict=0.667`
  - `clarify_required` family 是 `0.0`
- 当前 strongest judge 的首个可复现边界不是代码 edge-case，而是“literal answering vs clarify-first”冲突。
- 这说明项目可以开始从 dev/object slice 过渡到真正的 frontier-boundary search。

