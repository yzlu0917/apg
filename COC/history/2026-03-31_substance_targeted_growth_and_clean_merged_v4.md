# 2026-03-31 Substance Targeted Growth And Clean-Merged-v4

## What Changed

- 新增 `math_010/011`、`code_008/009` 四条 compact objective seeds。
- 用 `Qwen3-8B + substance_flip_targeted_v1` 在 fresh seeds 上继续扩 substance 池。
- 将 merged slice 从 `v3` 扩到 `v4`，并复测 `4B` high-cap readout。

## Main Outcome

- fresh seeds 上新增 `3` 条 verifier-clean targeted substance rows。
- `clean_merged_slice_v4` 扩到 `15` 条后，`4B base pair-strict=0.867`，`4B critic=0.933`。
- 说明 `targeted_v1` 已经不是局部 repair，而是可扩展的 substance growth path。
