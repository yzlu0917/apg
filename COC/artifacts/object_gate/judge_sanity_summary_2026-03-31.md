# Judge Sanity Summary 2026-03-31

## Active Slice

- source: `data/interim/object_dev_v0_active_slice.jsonl`
- size: `5`
- families:
  - `substance_flip`: `2`
  - `style_flip`: `3`

## Judge Results

- `Qwen3-0.6B base`: `2/5`
- `Qwen3-0.6B critic`: `2/5`
- `Qwen3-4B base`: `4/5`
- `Qwen3-4B critic`: `3/5`

## Family Breakdown

- `Qwen3-0.6B base`
  - substance_flip: `2/2`
  - style_flip: `0/3`
- `Qwen3-0.6B critic`
  - substance_flip: `2/2`
  - style_flip: `0/3`
- `Qwen3-4B base`
  - substance_flip: `2/2`
  - style_flip: `2/3`
- `Qwen3-4B critic`
  - substance_flip: `2/2`
  - style_flip: `1/3`

## Takeaway

- 当前 active slice 上，judge 差异主要来自 `style_flip`，不是 `substance_flip`。
- `Qwen3-4B base` 当前优于 `Qwen3-4B critic`，说明 prompt style 也会显著改变 family-wise behavior。
- 这足以支持下一步扩 active slice，并开始真正计算 early `COC` / family-wise miss，而不是只看 overall accuracy。
