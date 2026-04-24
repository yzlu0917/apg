# 2026-04-02 Frontier Boundary Probe v5/v6 Default Convention

## What Changed

- 新建 fresh mixed slice `frontier_boundary_probe_v5_default_convention`，用全新题面同时测试 `source_unit_missing + date_convention_missing`。
- 新建 fresh `date-only` slice `frontier_boundary_probe_v6_date_convention`，用 compact ambiguous short-date strings 单独复测日期约定子族。
- 将对象表述从宽泛的 `clarify_required` 进一步压成当前更准确的工作名：`default-convention boundary`。

## Main Outcome

- `v5 default-convention` 仍然卡住 strongest API judge：balanced `pair-strict=0.375`。
  - `source_unit_missing = 0.0`
  - `date_convention_missing = 0.75`
- `v6 date-only` 说明日期约定并没有消失，而是 recipe 敏感：在 compact short-date ISO recipe 下，balanced `pair-strict=0.0`。
- 因此当前 best strong-judge object 不应写成宽泛的 `clarify_required`，而应写成更窄的：
  - 在缺失默认约定时，judge 是否会错误奖励依赖常见默认约定的直接答案。
