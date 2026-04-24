# 2026-03-31 Style-Flip Controlled-Code-v1

## What Changed

- 新增 code-specific `style_flip` recipe：`controlled_code_v1`。
- 在 5 个 code seeds 上跑完 reviewer、verifier 和 swap-balanced judge 检查。

## Main Outcome

- `controlled_code_v1` 保留了 `4/5` verifier-clean pairs，明显优于之前 code 侧 recipe。
- 但 balanced pair-strict 只有 `0.5`，说明它是当前 best recipe，不是已审计完成的 recipe。
