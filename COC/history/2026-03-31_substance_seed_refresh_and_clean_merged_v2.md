# 2026-03-31 Substance Seed Refresh And Clean-Merged-v2

## What Changed

- 先验证旧 seed 池剩余任务的 `substance_flip` 扩样空间，确认旧池基本耗尽。
- 新增 `4` 条 objective seeds，并补上 verifier 支持。
- 基于新增 verifier-clean `substance_flip` 行，把 clean merged slice 从 `v1` 升到 `v2`。

## Main Outcome

- 新 seed 立即带来 `3` 条新的 verifier-clean `substance_flip`，说明瓶颈主要是 seed 池，而不是 generator 完全失效。
- `clean_merged_slice_v2` 达到 `12` 条，其中 `8 substance + 4 style`。
- 在 balanced 读法下，`Qwen3-4B critic` 维持 `pair-strict=0.667`，而 `0.6B` 仍为 `0.0`；当前主瓶颈已从 style recipe 转向 stubborn `substance_flip` pairs。
