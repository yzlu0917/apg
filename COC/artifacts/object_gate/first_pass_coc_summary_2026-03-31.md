# First-Pass COC Summary 2026-03-31

## Expanded Active Slice

- file: `data/interim/object_dev_v0_active_slice_v2.jsonl`
- size: `7`
- family counts:
  - `substance_flip`: `2`
  - `style_flip`: `5`

## Judge Metrics

### Qwen3-0.6B base

- overall accuracy: `2/7 = 0.286`
- family accuracy:
  - substance_flip: `1.0`
  - style_flip: `0.0`
- family miss:
  - substance_flip: `0.0`
  - style_flip: `1.0`
- first-pass uniform COC: `0.5`

### Qwen3-0.6B critic

- overall accuracy: `2/7 = 0.286`
- family accuracy:
  - substance_flip: `1.0`
  - style_flip: `0.0`
- family miss:
  - substance_flip: `0.0`
  - style_flip: `1.0`
- first-pass uniform COC: `0.5`

### Qwen3-4B base

- overall accuracy: `6/7 = 0.857`
- family accuracy:
  - substance_flip: `1.0`
  - style_flip: `0.8`
- family miss:
  - substance_flip: `0.0`
  - style_flip: `0.2`
- first-pass uniform COC: `0.9`

### Qwen3-4B critic

- overall accuracy: `5/7 = 0.714`
- family accuracy:
  - substance_flip: `1.0`
  - style_flip: `0.6`
- family miss:
  - substance_flip: `0.0`
  - style_flip: `0.4`
- first-pass uniform COC: `0.8`

## Main Pattern

- 当前所有 judge 在 `substance_flip` 上都没有错。
- 区分度几乎全部来自 `style_flip`。
- `Qwen3-0.6B` 的两个 judge 版本对所有 `style_flip` 都偏向 `A`，说明它几乎不会给 `tie`。
- `Qwen3-4B base` 明显优于 `Qwen3-4B critic`，说明 prompt style 本身会改变 family-wise miss。

## Interpretation

- 这已经足以说明当前 active families 不是空对象。
- 当前最早期的 object signal 是：**judge 之间的差异集中体现在 style-equivalent cases，而不是 obvious correctness flips。**
- 下一步值得做的不是继续堆更多 judge 类型，而是先扩 `style_flip + substance_flip` 的样本量，确认这个 family-wise pattern 是否稳定。
