# 2026-03-31 Clean-Merged-v3 Full Panel

## What Changed

- 在 `clean_merged_slice_v3` 上补跑了 `Qwen3-0.6B base/critic` 的 original 和 swapped judge eval。
- 将 `v3` 从 high-cap-only slice 升成 fully matched cross-capacity panel。

## Main Outcome

- `0.6B base/critic` 在 `v3` 上仍是 balanced `pair-strict=0.0`。
- `4B base=0.833`、`4B critic=0.917` 保持不变。
- 因此 `v3` 的提升应解释为 capacity-sensitive repair，而不是 slice 普遍变简单。
