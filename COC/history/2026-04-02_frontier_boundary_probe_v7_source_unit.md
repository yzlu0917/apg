# 2026-04-02 Frontier Boundary Probe v7 Source Unit

## What Changed

- 新建 fresh `source-unit-only` probe，完全换新数值，专门复测 strongest judge 是否稳定默认 Celsius。
- 用 strongest API `critic` 跑 paired original/swapped 评测。
- 同步把 `default-convention boundary` 的当前 object claim 压成 paper-facing memo。

## Main Outcome

- `v7 source-unit-only` 的 balanced `pair-strict=0.25`，与 `v4/v5` 一致表明 `source_unit_missing` 是当前最稳定的 hard subtype。
- 原顺序与 swapped 都只有 `1/4` 正确，且有 `3` 条双边都错，说明这不是单纯位置效应。
- 结合 `v6 date-only`，当前 strongest-judge object 已可更稳地表述为 `default-convention boundary`，而不是宽泛的 `clarify_required`。
