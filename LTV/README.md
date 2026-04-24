# LTV Project Workspace

本目录现在按一个独立项目维护。当前阶段是 `phase 0 bootstrap`，目标不是直接开大实验，而是先冻结 claim、gate、fallback 和最小执行路径。

## 入口文件

- `proposal.md`：完整研究 proposal
- `phase0_bootstrap.md`：phase 0 产物，包含 claim hierarchy、fallback framing、四个 gate、Object gate 最小闭环、5-7 天计划
- `history/progress.md`：当前主线进展、里程碑、resume point
- `history/results.md`：可复查结果账本；当前已记录环境可用性与 Object gate 启动决策
- `configs/object_gate/*.yaml`：phase 0 冻结的 v0 spec
- `data/lean/lean_mini_v0_smoke.jsonl`：首个 Lean smoke slice
- `data/lean/lean_mini_v0_firstpass.jsonl`：first-pass Lean slice
- `data/cts/cts_mini_v0_panel.jsonl`：扩展后的 CTS panel
- `data/cts/cts_mini_v0_auto_panel.jsonl`：更大但更噪的 CTS auto panel
- `data/cts/cts_mini_v0_panel_annotated.jsonl`：带 provenance/family 标签的 curated panel
- `data/cts/cts_mini_v0_auto_panel_annotated.jsonl`：带 provenance/family 标签的 auto panel
- `scripts/extract_boundary_states_smoke.py`：首条 boundary extraction 管线
- `scripts/generate_cts_with_api.py`：API 扩展 CTS 候选的脚本
- `scripts/evaluate_cts_mini.py`：CTS paired evaluation 脚本
- `scripts/build_cts_auto_panel.py`：从 manual panel + API rounds 构建 auto panel
- `scripts/annotate_cts_panel.py`：清理 provenance 并补 same/flip family 标签
- `scripts/audit_cts_families.py`：按 same/flip family 与 provenance 做 CTS slice audit
- `scripts/extract_cts_novel_rows.py`：从新一轮 API 输出中抽取相对旧 panel 的纯增量 rows
- `artifacts/object_gate_firstpass/baseline_results_v2.json`：补齐 latent ablation 后的 baseline 结果
- `artifacts/object_gate_firstpass/cts_mini_panel_eval_v2.json`：CTS panel v2 结果
- `artifacts/object_gate_firstpass/cts_auto_panel_eval.json`：CTS auto panel 结果
- `artifacts/object_gate_firstpass/cts_family_audit_curated.json`：curated panel 的 family audit
- `artifacts/object_gate_firstpass/cts_family_audit_auto.json`：auto panel 的 family audit
- `artifacts/object_gate_firstpass/cts_family_audit_summary.md`：当前 family audit 的人类可读摘要
- `artifacts/object_gate_firstpass/cts_round4_summary.md`：round4 定向扩数后的摘要
- `artifacts/object_gate_round5/cts_round5_summary.md`：round5 composition 扩展后的摘要
- `artifacts/object_gate_round6/cts_round6_summary.md`：round6 manual stability check 摘要
- `artifacts/object_gate_round7/cts_round7_summary.md`：round7 hard same rewrite audit 摘要
- `artifacts/object_gate_round8/cts_round8_summary.md`：round8 reflexivity dedicated control 摘要
- `artifacts/object_gate_round9/cts_round9_summary.md`：round9 scoring audit 摘要
- `artifacts/object_gate_round10/cts_round10_summary.md`：round10 broader-panel scoring audit 摘要
- `artifacts/object_gate_round11/object_gate_round11_summary.md`：round11 Lean object-gate scorer comparison 摘要
- `artifacts/object_gate_round12/object_gate_round12_summary.md`：round12 Goedel cross-model object-gate 摘要
- `artifacts/object_gate_round13/object_gate_round13_summary.md`：round13 minimal conditional-transition 测试摘要
- `artifacts/object_gate_round14/object_gate_round14_summary.md`：round14 structured interaction conditional 测试摘要
- `artifacts/object_gate_round15/object_gate_round15_summary.md`：round15 low-rank bilinear conditional scorer 摘要
- `artifacts/object_gate_round16/object_gate_round16_summary.md`：round16 CLUE-style geometric baseline 摘要
- `artifacts/object_gate_round17/object_gate_round17_summary.md`：round17 CTS pairwise margin baseline 摘要

## 当前默认路线

- headline 先只站稳 **object claim**，不提前宣称 method/deployment 成立
- Object gate 先走 **Lean clean-room + 小型 counterfactual slice** 的最小闭环
- 若 object 信号不成立或审计不过，优先收束到 measurement/diagnostic framing，而不是强推大规模主线
- 当前已跑通首条 smoke extraction，artifact 位于 `artifacts/object_gate_smoke/deepseek_prover_v2_7b/`
- 当前已得到 first-pass baseline 结果，位于 `artifacts/object_gate_firstpass/baseline_results.json`
- 当前已得到 `CTS-mini-v0` first-pass paired 结果，位于 `artifacts/object_gate_firstpass/cts_mini_eval.json`
- 当前已用 API 扩展 CTS panel，扩展评测结果位于 `artifacts/object_gate_firstpass/cts_mini_panel_eval.json`
- 当前已补齐 latent ablation，并有 v2 结果可读
- 当前已完成 family-sliced audit，结论是 `transition_only` 只在部分 family 上有清晰优势，尚不能写成全局 claim
- 当前已完成 round4 弱 family 定向扩数：`wrong_theorem_reference` 与 `wrong_target_term` 有所改善，但 `wrong_composition` 仍未解
- 当前已完成 round5 composition 扩展：`wrong_composition` 有所改善，但 family-level 结果仍不稳定，`Audit gate` 仍未通过
- 当前已完成 round6 manual stability check：flip-family 读数明显增强，但 same-family invariance 仍然不够干净，`Audit gate` 仍未通过
- 当前已完成 round7 hard same rewrite audit：`projection_style` 与部分 `other_same_rewrite` 有改善，但 `reflexivity_style` 仍是 hardest failure family，`Audit gate` 仍未通过
- 当前已完成 round8 reflexivity dedicated control：`transition_only` 连 `pure_format` 级别的 reflexivity rewrite 都不稳，说明该分支当前更像 hard negative / diagnosis，而不是简单 coverage gap
- 当前已完成 round9 scoring audit：固定 round8 control 后发现 scorer 选择会主导 `reflexivity_style` 结论，`transition` 表示本身不能再被简单判成 hard negative
- 当前已完成 round10 broader-panel scoring audit：round9 的 scorer 修复在更大 panel 上也成立，但它不是 `transition` 独享的，`transition vs post-state` 在更合理 scorer 下重新变成 open question
- 当前已完成 round11 Lean object-gate scorer comparison：scorer 选择也会改变主 object-gate 上的 `post-state vs transition` 读法，当前不存在 scorer-robust 的单边优势结论
- 当前已完成 round12 Goedel cross-model object-gate comparison：`post-state vs transition` 的主读法同时依赖 scorer choice 与 model choice，“模型是否学到该 invariant” 成为活跃解释分支
- 当前已完成 round13 minimal conditional-transition test：最朴素的 `concat(h^-, delta)` 没有改善 object gate，当前应把它视为 negative baseline，而不是更本质对象的实现
- 当前已完成 round14 structured interaction conditional test：`concat(delta, h^- * delta)` 比 raw concat 更好，但仍未超过裸 `transition`，说明下一步应优先转向 bilinear / energy-style conditional scorer
- 当前已完成 round15 low-rank bilinear conditional scorer test：该 scorer 在 single-point object gate 上显著劣于当前竞争性 baseline，当前这条 conditional-scorer 支线应阶段性收束，并转向 pairwise / contrastive objective
- 当前已完成 round16 CLUE-style geometric baseline：`transition_clue_proto` 优于最简单的单质心几何 baseline，但仍弱于 `transition_mlp_prob`，说明借前人 verifier 结构有价值，但最小移植版还不足以成为最优 step-level 判别器
- 当前已完成 round17 CTS pairwise margin baseline：pairwise 目标确实改变了 same/flip tradeoff，但当前 scalar margin objective 仍太 blunt，`transition` 的 `IG` 改善伴随 `SS` 明显塌掉，下一步应转向 embedding-style contrastive objective

## 可用资源

- 本地模型缓存：`/cephfs/shared/hf_cache/hub`
  - 已确认可见 `Qwen3-1.7B`、`Qwen3-4B`、`DeepSeek-Prover-V2-7B`、`ReasonFlux-PRM-7B` 等候选
- conda 环境：`infer`
- 数据：按需下载到未来的 `data/` 目录
- API（仅在需要做改写或审计时申请预算）：

```yaml
deepseek-v3.2:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  endpoint: ep-20251213141929-gk2jb
  api_key: 8da5e4ba-59ad-47af-8f87-005fd1d1641b
```
