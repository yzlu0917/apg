# Style Length Audit Summary 2026-03-31

## Setup

- slice: `data/interim/object_dev_v0_active_slice_v3.jsonl`
- swapped slice: `data/interim/object_dev_v0_active_slice_v3_swapped.jsonl`
- audited family: `style_flip`
- total pairs: `9`
- average absolute char gap per directional view: `72.3`

## Metrics

### Qwen3-0.6B base

- tie rate: `0.0`
- choose longer rate among non-tie: `0.444`
- choose shorter rate among non-tie: `0.556`
- pair breakdown:
  - `shorter+longer = 8`
  - `shorter+shorter = 1`

Interpretation:

- 主要不是长度偏好，而是位置偏好
- 原顺序几乎总选 `A`，交换后也仍常选 `A`

### Qwen3-0.6B critic

- tie rate: `0.0`
- choose longer rate among non-tie: `0.444`
- choose shorter rate among non-tie: `0.556`
- pair breakdown:
  - `shorter+longer = 8`
  - `shorter+shorter = 1`

Interpretation:

- 与 `0.6B base` 基本一致
- 低容量 judge 的 style 行为应主要归因于 position bias，而不是 verbosity bias

### Qwen3-4B base

- tie rate: `0.611`
- choose longer rate among non-tie: `0.143`
- choose shorter rate among non-tie: `0.857`
- pair breakdown:
  - `tie+tie = 3`
  - `tie+shorter = 4`
  - `longer+tie = 1`
  - `shorter+shorter = 1`

Interpretation:

- 大部分时候会给 `tie`
- 一旦不判 `tie`，更常偏向更短答案，而不是更长答案

### Qwen3-4B critic

- tie rate: `0.5`
- choose longer rate among non-tie: `0.222`
- choose shorter rate among non-tie: `0.778`
- pair breakdown:
  - `tie+tie = 3`
  - `tie+shorter = 2`
  - `shorter+shorter = 2`
  - `longer+tie = 1`
  - `longer+shorter = 1`

Interpretation:

- 与 `4B base` 同方向，但更噪
- surviving non-tie preference 仍主要偏向 shorter / briefer answer

## Main Finding

- 当前 `style_flip` 的主要 artifact 不是“偏爱更长答案”
- 对 `4B` judge 来说，更像：
  - 一部分 case 会判 `tie`
  - 另一部分 case 会偏向更短、更贴近 `brief explanation` 的答案
- 对 `0.6B` judge 来说，主导问题仍是 answer position bias

## Consequence

- `style_flip` 后续 audit 不应只盯 verbosity 增长
- 更准确的控制方向应是：
  - `brief vs verbose` 的 instruction-fit 审计
  - 长短差受控的 style pair
  - 继续保留 order-balanced paired protocol
