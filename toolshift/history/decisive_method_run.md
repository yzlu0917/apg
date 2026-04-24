# ToolShift Decisive Method Run

## One-Line Decision

如果要再给 original SCC method thesis 一次机会，当前只允许再做 **一次** faithful-to-thesis 的方法复核：

`teacher-distilled canonical-bottleneck SCC`

这次复核的目标不是继续“找一个能赢的变体”，而是回答一个更窄也更关键的问题：

> 在固定 `matched transformed-data budget`、固定 base model、固定 verifier、固定 compute 的条件下，围绕 `canonical bottleneck` 的 SCC 是否能稳定优于 `AugOnly`，并且不是靠牺牲 `POC` 换取 `NOS`。

如果这次仍然不能成立，方法主张正式收口，后续 paper 只保留：

`benchmark / protocol + diagnosis + strong scaffold baseline`

## Why This Run Exists

当前 learned route 的失败，已经不是单个实现问题：

- frozen pair head / pair-text / MLP pair head
- cross-encoder threshold / supervised / ranked / pairwise / listwise localizer
- capability-only / multitask fine-tune
- hard-negative / class-balanced weighting
- asymmetric calibration / objective
- dual-threshold / abstain-band rule

这些路线都没有稳定追平 `semantic_embedding_capability_gate`。

但 proposal 里真正决定性的版本，其实还没有被完整、干净地做过：

- action-state / decision bottleneck 是显式对象
- `L_inv` 只作用在 positive orbit 的 canonical bottleneck
- `L_ctr / L_ctl` 直接建模 negative capability shift
- 用 matched-budget `AugOnly` 做主对照

因此，当前只保留一次更 faithful-to-thesis 的复核，而不是继续沿 pair/localizer family 做同级别 sweep。

## Non-Goals

这次复核 **不做** 以下事情：

1. 不再开新的 pair-model / localizer family。
2. 不再做 loss / threshold / calibration sweep。
3. 不在 frozen blind panel 上做任何方法选择。
4. 不把 strongest scaffold baseline 偷偷塞回 inference 当 rule fallback。
5. 不为赢 dev panel 而继续扩 benchmark / 改 blind asset。

## Fixed Experimental Governance

### Panels

- `dev panel`:
  - `data/real_evolution_benchmark.json`
  - 只用于方法开发、回归、诊断和锁定最终 checkpoint

- `blind panel`:
  - `data/real_evolution_blind_benchmark.json`
  - 已冻结，只允许在 dev 锁定后做一次最终复核

### Fixed Controls

以下条件必须固定，不允许因为方法表现不佳而中途变更：

1. base model / encoder family
2. transformed-data budget
3. compute budget
4. verifier / evaluator / canonicalizer
5. control tags 与 admissible-set policy
6. blind panel 内容

### Seeds

- 目标正式运行：`3` 个 seeds
- `2` 个 seeds 只允许用于 smoke，不允许作为最终结论

## Compared Methods

本轮只允许比较以下三组主方法：

1. `SeedOnly`
   - 与当前 method architecture 相同，但不使用 transformed views
   - 若 full-sequence SFT 不在现有基础设施内，则用 “same architecture, no transformed augmentation” 作为最小公平 control

2. `AugOnly`
   - proposal 的 matched-budget 主对照
   - 使用与 SCC 完全相同的 transformed-data budget，但不加 SCC bottleneck / consistency / control losses

3. `TeacherDistilledBottleneckSCC`
   - 当前唯一允许的新方法
   - 训练期可使用 strongest scaffold baseline 产生的 supervision
   - 推理期不允许调用 teacher 的 cue extractor / rule gate

`semantic_embedding_capability_gate` 仍保留，但只作为：

- teacher source
- strongest scaffold reference line
- blind final framing reference

而不是本轮主 claim 的公平对照对象。

## Method Shape

### Core Representation

新的 SCC 只允许围绕显式 canonical bottleneck 建模：

- `z_tool`
- `z_slot`
- `z_ctl`

必要时可拆成：

- `z_exec`
- `z_abstain`
- `z_ask`

但必须仍然属于 `decision bottleneck`，而不是全序列 hidden-state 对齐。

### Teacher Distillation

teacher 来自当前 strongest scaffold baseline `semantic_embedding_capability_gate`。

teacher 可提供的训练期 supervision：

1. candidate canonical tool target
2. canonical slot / argument target
3. execute vs non-execute / ask_clarification decision
4. localized contract / description cue attribution

这些 supervision 只能用于训练；推理时学生模型必须自给。

### Loss Design

允许的 loss family：

1. `L_tool`
   - canonical tool prediction
2. `L_slot`
   - canonical slot/argument prediction
3. `L_ctl`
   - control-tag prediction
4. `L_inv`
   - 只在 `clean <-> positive near-orbit` 上约束 bottleneck invariance
5. `L_ctr`
   - 只在 `positive <-> negative near-orbit` 或 `clean <-> negative near-orbit` 上约束 capability-sensitive separation
6. `L_distill`
   - teacher 提供的 tool / slot / control / localized cue distillation

不允许的做法：

- 对全序列 hidden states 做粗暴 invariance
- 再造一个新的 generic pair/localizer scorer 作为主路线
- 在 inference 中拼接 teacher cue clause 当显式 fallback

## Required Evaluation Pack

### Main Dev Table

必须在 `dev panel family_holdout_cv` 上报告：

- `CAA`
- `CAA_clean`
- `CAA+`
- `NOS`
- `POC`
- `coverage`
- `coverage-controlled NOS` 或等价 selective-risk 版本

并同时给出：

- exact counts
- family-level breakdown
- seed mean
- seed variance / CI

### Required Diagnostics

必须跑：

1. `scripts/diagnose_saved_records.py`
2. `scripts/compare_fixed_panel_methods.py`
3. `scripts/run_masking_sensitivity.py`
4. `scripts/run_decision_probe.py`

作用分别是：

- 错误桶分解
- dev panel paired comparison
- `name vs description/contract` 机制分析
- action-state / decision-state 机制分析

### Optional But Allowed

以下只能作为 sanity，不得替代主表：

- richer synthetic family benchmark
- same-family split smoke
- execution/replay/docs/api-surface regression

## Go / No-Go Criteria

### Go-to-Blind Criteria

只有同时满足以下条件，才允许进入 frozen blind review：

1. 相对 `AugOnly`，`CAA+` 不下降。
2. 相对 `AugOnly`，`NOS` 不下降。
3. 相对 `AugOnly`，`POC` 不得下降超过 `0.02` 绝对值。
4. `coverage-controlled NOS` 不低于 `AugOnly`。
5. 不出现新的 family-level execute collapse。
6. 至少 `2/3` seeds 上，`CAA+` 与 `NOS` 同时不劣于 `AugOnly`。

### Mechanism Criteria

即使 dev 指标达标，也必须至少满足两条机制条件中的一条：

1. `name_mask` 影响显著小于 `description_mask / contract_mask`
2. `positive-state similarity` 或 `state_separation_gap` 高于 `AugOnly`

如果行为提升与机制证据完全脱节，不进入 blind。

### Final Success Criteria

这次 decisive run 只有在以下条件下才算方法主张成立：

1. blind panel 上 `CAA+` 与 `NOS` 均不低于 `AugOnly`
2. blind panel 上不出现新的 `NOS=0.0` family collapse
3. blind panel 上的增量不是靠明显牺牲 `POC` 换来的
4. 机制证据仍指向 canonical bottleneck / description-contract grounding，而不是 name shortcut

### No-Go Criteria

任一条成立就停止方法主线，不再开第二轮救援：

1. dev 上仍无法同时保住 `CAA+ / NOS / POC`
2. 只能通过明显 tradeoff 拿到更高 `NOS`
3. blind 上再次出现 hard-family collapse
4. 机制证据表明模型仍然没有学到比 `AugOnly` 更稳定的 decision bottleneck

## Deliverables If We Execute This Run

必须同时产出：

1. 新方法代码与训练入口
2. `results.md` 结果账本
3. `progress.md` 当前结论与 resume point
4. `artifacts/...` 下的正式 summary / diagnostics / masking / probe / blind review
5. 一页明确的 go / no-go 结论

建议 artifact 命名：

- `artifacts/real_evolution_teacher_distilled_bottleneck_scc_v1/`
- `artifacts/real_evolution_teacher_distilled_bottleneck_scc_v1_diagnostics/`
- `artifacts/real_evolution_teacher_distilled_bottleneck_scc_v1_masking/`
- `artifacts/real_evolution_teacher_distilled_bottleneck_scc_v1_probe/`
- `artifacts/real_evolution_teacher_distilled_bottleneck_scc_v1_blind/`

## Final Policy

这份计划的核心不是“再给 SCC 无限机会”，而是：

> 只再做一次真正 faithful-to-thesis 的 decisive run。

如果成功，paper 才有资格重新讨论更强的方法主张。  
如果失败，就正式接受当前闭环：

`ToolShift = benchmark / protocol + diagnosis + strong scaffold baseline`

而不是继续在 dev panel 上做无边界的方法搜索。
