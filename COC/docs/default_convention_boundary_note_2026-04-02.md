# Default-Convention Boundary Note 2026-04-02

## Working Object

当前 strongest-judge 边界的最窄工作表述，不再是宽泛的 `clarify_required`，而是：

> 当 prompt 缺少一个会改变具体输出的约定时，judge 是否会错误奖励一个依赖常见默认约定的直接答案。

这类默认约定通常是文化性或任务习惯性的，而不是 prompt 明示的：

- source unit
- short-date convention
- locale-dependent formatting rule
- other socially common but unstated defaults

## Gold Rule

只有在下面条件同时满足时，才计入当前对象：

1. 缺失的是 **约定/convention**，而不是普通背景信息；
2. 这个约定会改变 **具体输出值或字符串**；
3. 直接答案的优势主要来自一个常见默认约定，而不是 prompt 明示条件；
4. 更好的答案应先暴露缺失约定，或至少显式条件化回答；
5. 问题仍然是可审计的，gold label 可以通过窄规则稳定判定。

## Current Hard Recipes

1. `source_unit_missing`
   - 典型形式：`Convert X degrees to Fahrenheit.`
   - 难点：直接答案容易默认 Celsius。
2. `date_convention_missing`
   - 典型形式：`What date is 06/07/08 in ISO format?`
   - 难点：直接答案容易默认某个 locale/date ordering。

## What This Is Not

以下情况暂不算当前对象：

- 只是一般性的“最好更谨慎一点”；
- 缺信息但不会改变具体输出；
- 已有强全局标准，默认回答并不构成未经授权的假设；
- 单纯因为更礼貌而多问一句。

## Current Read

截至 2026-04-02，当前 strongest API judge 的 hard boundary 已可暂时概括为：

- umbrella family: `clarify_required`
- narrower working object: `default-convention boundary`
- best current hard recipes:
  - `source_unit_missing`
  - `date_convention_missing` with compact ambiguous short-date strings
