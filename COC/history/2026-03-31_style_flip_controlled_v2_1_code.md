# 2026-03-31 Style-Flip Controlled-v2.1 Code

## What Changed

- 将 `style_flip controlled_v2.1` 从 math 迁到 code 做了一轮 pilot。
- 对唯一 verifier-clean kept pair 做了 swap-balanced judge 检查。

## Main Outcome

- code 侧 reviewer 只保留了 `1/5`。
- 失败样本大多退化成“同样代码 + 一两行注释”，被 reviewer 判成 `weak_contrast`。
- 因此 `controlled_v2.1` 目前只适合 math，不适合原样迁到 code。
