# 2026-04-01 Clean-Merged-v5 Fullpanel

## What Changed

- 在 `clean_merged_slice_v5` 上补跑了 `Qwen3-0.6B base/critic` 的 original + swapped eval。
- 将 `0.6B` 与既有 `4B` 结果合并成同一份 balanced fullpanel。
- 用 matched cross-cap 读法重新判断 `v5` 是否足以替代 `v3` 成为当前主 slice。

## Main Outcome

- 两条 `0.6B` 在 `v5` 上仍然都是 balanced `pair-strict=0.0`。
- `4B base` 保持 `0.833`，`4B critic` 升到 `0.944`。
- 说明 `v5` 的扩大没有把 slice 做“普遍更容易”，而是在更大样本上保留了清晰的 capacity split；当前 best fully matched slice 应从 `v3` 升到 `v5`。

