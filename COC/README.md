# Counterfactual Oversight Coverage

本目录现在按独立项目推进，目标是验证：自动监督系统的可靠性，是否更多取决于对关键失败家族的覆盖率和漏判相关性，而不是 judge 的平均准确率。

## Current Phase

- 当前阶段：`phase 0 bootstrap`
- 当前 headline：先做 object-level validation；method 和 deployment claim 暂时保持 conditional
- 核心入口：
  - `proposal.md`
  - `docs/phase0_bootstrap.md`
  - `docs/object_gate.md`
  - `progress.md`
  - `results.md`

## Environment Notes

- 可用本地模型：`/cephfs/shared/hf_cache/hub/Qwen3*`
- 开始实验默认优先：`Qwen3 1.7B` 或 `Qwen3 4B`
- 数据默认放在 `data/`
- 默认 conda 环境：`infer`
- 若需要额外包、工具或 API 预算，先与用户确认

可用 API（按需，不在 phase 0 默认使用）：

```yaml
deepseek-v3.2:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  endpoint: ep-20251213141929-gk2jb
  api_key: 8da5e4ba-59ad-47af-8f87-005fd1d1641b
```

## Project Layout

- `proposal.md`: 原始研究 proposal
- `docs/`: phase 0 bootstrap、gate 和后续方法文档
- `configs/`: 冻结的最小配置与切片范围
- `scripts/`: 后续轻量脚本入口
- `data/`: 数据与 manifest
- `artifacts/`: 图表、中间产物、导出结果
- `history/`: 阶段性变更记录
- `progress.md`: 当前主线进展
- `results.md`: 可复现结果账本
