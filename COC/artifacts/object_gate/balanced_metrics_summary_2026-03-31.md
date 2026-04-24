# Balanced Metrics Summary 2026-03-31

## Setup

- original slice: `data/interim/object_dev_v0_active_slice_v3.jsonl`
- swapped slice: `data/interim/object_dev_v0_active_slice_v3_swapped.jsonl`
- paired size: `12`
- families:
  - `style_flip = 9`
  - `substance_flip = 3`

## Protocol

- `balanced_directional_accuracy`: 原顺序与交换顺序两个方向的平均正确率
- `pair_strict_accuracy`: 同一 pair 的两个顺序都判对才算通过
- `balanced_coc_pair_strict`: 用 family-level `pair_strict_accuracy` 计算的均匀 family COC

这个读法比单边 `overall accuracy` 更保守，适合当前 order-sensitive 的 judge。

## Metrics

### Qwen3-0.6B base

- balanced directional accuracy: `0.125`
- pair strict accuracy: `0.0`
- balanced COC pair strict: `0.0`
- worst-family pair strict miss: `1.0`

Interpretation:

- 在 order-balanced 协议下完全塌陷
- `substance_flip` 也没有任何 pair 能双边都判对

### Qwen3-0.6B critic

- balanced directional accuracy: `0.125`
- pair strict accuracy: `0.0`
- balanced COC pair strict: `0.0`
- worst-family pair strict miss: `1.0`

Interpretation:

- 与 `0.6B base` 基本相同
- 当前低容量 judge 不应再作为 audit-controlled 主比较对象

### Qwen3-4B base

- balanced directional accuracy: `0.667`
- pair strict accuracy: `0.417`
- balanced COC pair strict: `0.5`
- worst-family pair strict miss: `0.667`
- family pair strict:
  - `substance_flip = 0.667`
  - `style_flip = 0.333`

Interpretation:

- order-balanced 后仍保留明显 object signal
- 但 `style_flip` 严格通过率只有 `1/3`

### Qwen3-4B critic

- balanced directional accuracy: `0.583`
- pair strict accuracy: `0.417`
- balanced COC pair strict: `0.5`
- worst-family pair strict miss: `0.667`
- family pair strict:
  - `substance_flip = 0.667`
  - `style_flip = 0.333`

Interpretation:

- 相比 unbalanced 读法，`critic` 与 `base` 的差距显著缩小
- prompt-style effect 目前不够稳，不能当强 object 证据

## Main Finding

- order-balanced 之后，`4B` 与 `0.6B` 的能力级差仍然存在，所以 object 不是纯顺序幻觉
- 但原先一部分看起来像“judge ranking / prompt-style separation”的现象，被 balanced 协议明显压缩了
- 当前最稳的结论是：
  - `style_flip` 确实有对象信号
  - 但这个信号还没有通过严格 audit
  - `substance_flip` 可用，但样本太少，暂时不足以单独支撑 headline

## Consequence

从这轮开始：

- future judge evaluation 默认采用 order-balanced paired protocol
- `pair_strict_accuracy / balanced_coc_pair_strict` 作为 audit-controlled 主读数
- 单边 `overall accuracy / COC` 只保留为 exploratory support，不再单独承载 gate 结论
