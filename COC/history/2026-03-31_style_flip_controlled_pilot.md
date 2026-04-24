# 2026-03-31 Style-Flip Controlled Pilot

## What Changed

- 在 `bootstrap_object_data.py` 中新增 `style_flip_controlled_v1` 生成/审查协议。
- 对全量 seed 跑了一轮 `style_flip` controlled pilot。
- 对 pilot 的 verifier-clean 子集跑了 `4B base/critic` 的 balanced judge 检查。

## Why

- 之前的 audit 显示 `style_flip` 的剩余 artifact 更像 `briefness / prompt-fit bias`。
- 需要把 recipe 从“更长/更 polished”改成“长度更受控、指令更对称”。

## Main Outcome

- 总体字符差从 `72.3` 降到 `40.8`，方向正确。
- reviewer 只保留了 `4/9` 条，说明 recipe 还不够稳。
- 在这 4 条上，`4B base` 的 tie-stability 明显改善，但 `4B critic` 仍不稳定。
- 结论是：值得继续做 `controlled_v2`，但还不能替换主线 slice。
