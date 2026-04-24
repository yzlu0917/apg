# 2026-03-31 Substance Targeted Repair And Clean-Merged-v3

## What Changed

- 为 `substance_flip` 新增 `targeted_v1`，要求错误进入中间语义步骤，而不是只改最后输出。
- 先验证本地 `Qwen3-4B` 无法稳定服从该约束，再改用 `Qwen3-8B` 做 targeted math 修复。
- 用修复后的 `math_003`、`math_007`、`math_009` 替换 `v2` 中的弱 substance pairs，构造 `clean_merged_slice_v3`。

## Main Outcome

- `Qwen3-8B` 成功产出 `3` 条 verifier-clean 的 targeted math repairs。
- `4B base` 在 `v3` 上的 balanced pair-strict 从 `0.583` 升到 `0.833`。
- `4B critic` 在 `v3` 上的 balanced pair-strict 从 `0.667` 升到 `0.917`，且 `substance_flip` 达到 `1.0` pair-strict。
