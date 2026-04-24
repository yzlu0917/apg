# Seed Audit Policy

## Goal
把 seed benchmark 中当前无法稳定定义 canonical action 的样本移出主表，并把 control policy 写成可审计规则。

## Audit Rules

1. `unambiguous core`
   - 用户请求与 schema 足以稳定定义 canonical action
   - 或 near-orbit 控制策略可由显式规则唯一决定

2. `ambiguous split`
   - 请求本身缺少执行所需信息，导致 execute / ask_clarification 边界不稳
   - 或 canonical argument 依赖未提供的外部参考量，例如当前日期

3. `negative_deprecate`
   - 若 schema 明示 relevant tool 已 deprecated，且当前 seed suite 无可替代工具
   - audited admissible control 设为 `abstain`

4. `negative_contract`
   - 默认 policy 为 `ask_clarification`
   - 但若底层请求在 contract mutation 之前就不稳定，则该 view 进入 `ambiguous split`

## Current Seed Decisions

- `reminder_tax_form::{clean, positive_*, negative_contract}` 进入 `ambiguous split`
  原因：`tomorrow 9am` 依赖未提供的 reference date

- `calendar_toolshift_sync::{clean, positive_*, negative_contract}` 进入 `ambiguous split`
  原因：请求缺少 calendar date，execute / clarification 边界不稳

- 所有 `negative_deprecate` view 统一审计为 `abstain`

- `reminder_tax_form_absolute::*` 与 `calendar_toolshift_sync_absolute::*`
  保留在 `unambiguous core`
  原因：请求内已给出绝对时间，执行与 control policy 都可稳定判定
