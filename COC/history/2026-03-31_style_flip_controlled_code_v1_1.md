# 2026-03-31 Style-Flip Controlled-Code-v1.1

## What Changed

- 在 `controlled_code_v1` 基础上收紧 code-side `style_flip` recipe，得到 `controlled_code_v1_1`。
- 明确拒绝高长度差、强结构改写的 loop-vs-comprehension pairs。

## Main Outcome

- `controlled_code_v1_1` 只保留了 `2/5` verifier-clean pairs，但这两条在 `Qwen3-4B base/critic` 下都是 swap-balanced `pair-strict=1.0`。
- 因此 `controlled_code_v1_1` 应被视为当前 best clean subset，而不是取代 `controlled_code_v1` 的高产主 recipe。
