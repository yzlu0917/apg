# 2026-04-01 Frontier Boundary Probe v1 Clarify

## What Changed

- 为 `clarify_required` 单独写了 family note，收紧 gold rule。
- 新增了 8 条更系统的 clarify-first probes。
- 用 strongest API `critic` 跑了 paired original/swapped 评测。

## Main Outcome

- `clarify_required` 在更系统的一轮 probe 上仍然稳定卡住 strongest judge：
  - balanced `pair-strict=0.25`
  - family miss `=0.75`
- 这说明第一轮 `v0` 信号不是偶然，而是项目当前最像样的 frontier-hard 边界。
- 当前 strongest judge 的核心问题可以更准确地描述为：
  - **default-answer bias under underspecification**
  - 而不是简单的 reasoning weakness。

