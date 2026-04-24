# Frontier Boundary Search 2026-04-01

## Pivot

项目主线从“小模型分界”切到“当前强 judge 的边界搜索”。

这意味着：

- `v5` 继续保留为 dev/object slice。
- 小模型只作为开发期仪器，不再承担 headline。
- 新主线问题变成：
  - 在什么 **可审计** 场景下，当前 strongest judge 仍会失效、犹豫或不稳定？

## What Counts as Frontier-Hard

一个 family 只有在满足下面至少两条时，才值得进入强 judge 边界搜索：

1. **不是简单 correctness**
   - 不是“一眼看出算错了/条件写反了”的题。
2. **仍然可审计**
   - 可以用单元测试、明确 rubric 或窄解释规则判断 gold label。
3. **边界窄**
   - 两个答案都看起来大体合理，但只有一个真正满足 prompt 的关键约束。
4. **强 judge 可能需要认真比较**
   - 不能靠表面 pattern 或最后一个 token 直接秒解。

## Candidate Hard Families

第一轮默认优先试三类：

1. `constraint_edge_case`
   - 代码或格式任务里存在狭窄但关键的边界条件。
2. `clarify_required`
   - prompt 本身欠定，真正好的答案应先澄清而不是武断作答。
3. `omission_critical`
   - 两个答案都“基本对”，但一个漏掉决定性的约束或 edge case。

## Acceptance Rule for a Frontier Probe

单轮 frontier probe 的成功信号不是“小模型和大模型分化”，而是强 judge 本身出现以下至少一种：

- balanced `pair-strict < 1.0`
- 某个 hard family 上出现非零 miss
- original / swapped 行为不一致
- base / critic policy 对同一批 hard pairs 有可解释分歧

如果 strongest judge 在一轮 probe 上直接 `1.0`，这不代表 family 没价值，但至少说明：

- 当前这版 probe 还不够难
- 不能把它当 final frontier slice

## Current First Pass

第一轮先做一版手工 `frontier_boundary_probe_v0`，重点不是规模，而是验证这三类 family 是否有潜力卡住 API judge。

