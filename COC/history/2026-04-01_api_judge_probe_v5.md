# 2026-04-01 API Judge Probe on v5

## What Changed

- 给 `eval_judges.py` 补了最小 API backend。
- 在 `clean_merged_slice_v5` 上跑了一个单模型 API `critic` probe，并补了 swapped 对照。
- 用同样的 balanced protocol 检查 API judge 是否会把 object signal 打没。

## Main Outcome

- API `critic` 在 `v5` 上达到 balanced `pair-strict=1.0`。
- 这不是“API 一上就挂”，而是“更强 judge 直接吃满当前 slice”。
- 因此当前 object 的确是 model-sensitive，但方向是能力越强越稳，而不是 API 会让 object 消失。

