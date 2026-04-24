# 2026-03-31 Substance Targeted Growth v2 And Clean-Merged-v5

## What Changed

- 新增 `math_012/013`、`code_010/011` 四条 compact objective seeds，并补 verifier 支持。
- 用 `Qwen3-8B + substance_flip_targeted_v1` 在第二批 fresh seeds 上继续扩 substance 池。
- 将 merged slice 从 `v4` 扩到 `v5`，并复测 `4B` high-cap readout。

## Main Outcome

- 第二批 fresh seeds 再次新增 `3` 条 verifier-clean targeted substance rows。
- `clean_merged_slice_v5` 扩到 `18` 条后，`4B base pair-strict=0.833`，`4B critic=0.944`。
- 说明 `targeted_v1` 已经不只是“还能扩”，而是开始呈现可重复的 fresh-seed growth pattern；当前更合理的重点从继续小步 sweep 转向整理 comparison table 和 matched-panel 决策。

