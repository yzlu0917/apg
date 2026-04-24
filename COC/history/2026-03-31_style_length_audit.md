# 2026-03-31 Style Length Audit

## What Changed

- 新增 `scripts/compute_style_length_audit.py`，对 `style_flip` 进行长度/简洁性偏置审计。
- 在 `v3 + swapped-v3` 上对 4 个 judge 全量运行长度审计。

## Why

- balanced metrics 说明 `style_flip` 仍有剩余信号，但还不清楚这部分信号是否只是长度偏置。
- 需要把“顺序偏置”和“风格偏置”拆开看。

## Main Outcome

- `0.6B` 的主问题仍是 position bias，不是稳定的长度偏好。
- `4B` 在 non-tie 情况下更常偏向更短答案，而不是更长答案。
- 因此 `style_flip` 的下一轮 audit 应从“verbosity bias”收束为“briefness / instruction-fit bias”。
