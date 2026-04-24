# 2026-03-31 Seed Expansion And Controlled-v2

## What Changed

- 新增 3 条可直接 verifier 的 math seeds。
- 用这批新 seeds 跑了一轮 `substance_flip` 扩张。
- 在 math 上试跑了更强约束的 `style_flip controlled_v2`。

## Main Outcome

- `substance_flip` 新增 `2` 条 reviewer+verifier 都通过的 math pair，方向稳定。
- `style_flip controlled_v2` 把长度差降下来了，但 reviewer `0/7` 全拒，说明 recipe 过约束。

## Implication

- 后续应该把资源继续放在 `substance_flip` 扩张上。
- `style_flip` 需要一个介于 `controlled_v1` 和 `controlled_v2` 之间的带宽，而不是继续盲目加严。
