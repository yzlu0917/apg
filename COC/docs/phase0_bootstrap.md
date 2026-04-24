# Phase 0 Bootstrap

## 1. Bootstrap Objective

本阶段不直接做大规模 benchmark 或多模型 sweep，而是先把项目从 proposal 收束为可执行研究主线：

1. 冻结 claim hierarchy，避免 object / method / deployment 混写。
2. 明确主线失败时仍可交付的 fallback paper framing。
3. 定义四个 gate 的 go/no-go，避免后续跳关讲故事。
4. 建立最小项目骨架、进展记录和结果账本。
5. 在无关键阻塞时，启动 Object gate 的最小闭环。

## 2. Claim Hierarchy

### 2.1 Headline Object Claim

**O1. 在 objective / semi-objective 任务上，judge failure 不是零散噪声，而是可被 failure family 结构化描述的共同盲点；相较 mean accuracy，family-wise coverage 与 miss correlation 更接近“监督可靠性”这个研究对象。**

当前默认只把这一层作为 headline，因为它决定项目是否有独立对象和独立测量问题。

### 2.2 Conditional Method Claim

**M1. 如果 O1 成立，则 coverage-aware judge selection / routing 应能在 matched cost 下优于 strongest-single 或 uncertainty-only baseline，尤其在 hard cases 与 worst-family risk 上。**

这一层只有在 Object gate 和 Audit gate 都通过后，才允许升级为主结论。

### 2.3 Conditional Deployment Claim

**D1. 如果 O1 和 M1 都成立，则高 COC 的监督器应比高 accuracy 但低 coverage 的监督器，更能外推到 reranking / reward labeling / small-scale preference filtering 等下游流程。**

这一层默认最弱，只能在 Conversion gate 通过后进入主文，否则保留为 smoke test 或 appendix。

### 2.4 What Is Supported vs Conditional

| Claim layer | 当前状态 | 允许的 paper headline |
| --- | --- | --- |
| Object / measurement | 可作为主线 | 可以写成新对象定义、measurement principle、risk-sensitive evaluation |
| Method / selection / routing | 条件性 | 只有 matched-cost gain 成立后才能升级 |
| Deployment / downstream robustness | 条件性且更弱 | 默认不作为首轮 headline |

## 3. Fallback Paper Framing

## 3.1 Mainline Framing

如果 O1、M1、D1 依次成立，主论文 framing 是：

**evaluation principle + failure-family benchmark instrument + coverage-aware selection/routing method**

一句话版本：

> The problem with AI oversight is not merely weak judges, but judges that fail on the same families; optimize coverage, not only average accuracy.

## 3.2 Fallback A: Evaluation-Principle Paper

如果 object signal 清楚，但 selection / routing 收益有限，则把论文收束为：

**accuracy-centric judge evaluation is insufficient; COC is a necessary high-risk supplement**

最小可交付：

- 一个干净的 failure-family controlled benchmark slice
- object-level ranking inversion 或 worst-family discrepancy
- 审计后仍成立的 coverage-centric measurement case

## 3.3 Fallback B: Object-Identification / Audit Paper

如果 COC 还不足以构成更强原则，但 family-level blind spot 能稳定复现，则收束为：

**LLM oversight failures cluster into identifiable families, and current judge evaluation under-measures them**

最小可交付：

- failure family taxonomy
- clean audit protocol
- judge family-wise risk map
- 对现有 accuracy 指标盲区的系统性诊断

## 3.4 Fallback C: Clean Negative / Partial Result

如果 O1 也不强，或 COC 与 accuracy 高度重合，则不硬讲新目标函数，改写为：

**coverage helps only on known high-risk slices; average accuracy remains dominant outside those slices**

这仍可形成有价值的负结果或 boundary-setting paper，前提是：

- object slice 干净
- negative result 有清晰失败边界
- 为什么没成功讲得诚实且可复查

## 4. Gate Definitions and Go/No-Go

| Gate | Core question | Go signal | No-go signal | Default action if no-go |
| --- | --- | --- | --- | --- |
| Object | 我们定义的对象是否真实存在，且不只是 accuracy 的别名？ | family 构造保真；至少出现一组近似同 accuracy 但显著不同 COC / worst-family risk 的 judge；miss overlap 有结构性 | family 不干净；COC 与 accuracy 几乎重合；judge 差异主要来自噪声 | 缩 family、缩 domain，收束为 risk-sensitive evaluation supplement |
| Audit | 观察到的对象是否被 leakage / style / order / source-family artifact 冒充？ | 去掉显著 shortcut 后，object signal 仍存在；人工审查支持 family 标签 | 信号主要由答案长度、位置、来源标签等浅层 artifact 驱动 | 把主张降为 audit/diagnosis，不推进 method claim |
| Conversion | object signal 能否转成最小可观测 utility gain？ | matched cost 下，coverage-aware 优于 strongest-single 或 uncertainty-only 至少一个 hard metric | 没有 matched-cost gain，或 gain 只在不可复现实验设置里出现 | 保留 object/eval paper；method 降级为 appendix 或 future work |
| Scale | 收益能否外推到更大 slice、held-out family/domain 或小型下游流程？ | 方向在 held-out 或 downstream smoke test 上复现，且不靠重写指标 | 扩展后收益消失，或必须修改主指标 / acceptance rule 才能成立 | 主文停在 conversion；scale 只写限制与后续工作 |

### 4.1 Default Go/No-Go Thresholds

这些阈值用于 phase 0 之后的最小决策，不是最终论文统计标准：

- **Object gate**
  - family fidelity: 每个保留 family 的人工审查通过率至少 `>= 0.80`
  - inversion signal: 至少存在一对 judge 满足 `|overall_accuracy_delta| <= 2pt` 且 `|COC_delta| >= 5pt`，或 `|worst_family_miss_delta| >= 10pt`
  - structure signal: 至少一个 family 上观察到非平凡 miss overlap / miss correlation
- **Audit gate**
  - 去掉长度、位置、来源等 shortcut 控制后，object signal 方向仍保持
  - 不允许只靠单一 artifact family 支撑主张
- **Conversion gate**
  - matched cost 下，coverage-aware 在 `Hard-Error Recall` 或 `worst-family miss` 上优于 strongest-single
  - overall accuracy 不应出现明显恶化，默认容忍线为 `<= 1pt` 下降
- **Scale gate**
  - held-out family/domain 或小型 downstream smoke test 至少复现主效应方向
  - 不允许通过更换 main metric 或放宽 acceptance rule 救故事

## 5. Frozen Bootstrap Boundary

### 5.1 Phase 0 Default Scope

- 域：`math` + `code`
- active family：`F1 Substance Flip`、`F2 Style Flip`
- deferred family：`F3 Reasoning-Fluff`
- 标签来源：objective / semi-objective；family 构造与审查默认由模型完成，verifier 只做 correctness guardrail
- judge 形态：先以本地小模型和 prompt variants 组成最小 judge pool，再决定是否引入 API judge

### 5.2 What Is Explicitly Deferred

以下内容默认不在 phase 0 解决：

- same-family / relatedness bias 的大规模正式实验
- 复杂 routing 训练
- family-aware adaptation
- downstream DPO 或大规模 preference training
- 开放域纯主观任务推广

## 6. Minimal 5-7 Day Plan

### Day 1

- 冻结 `object_gate_v0` 配置
- 确认 math / code 的源任务候选与 verifier guardrail
- 建立 data manifest 模板、模型生成协议和人工审查模板

### Day 2

- 为当前激活 family 设计模型驱动的反事实构造模板
- 用 generator/reviewer models 产出每个 domain 的少量 seed examples
- 做第一轮 family fidelity 自检

### Day 3

- 补齐 `object-dev-v0` 的最小样本池
- 运行 4 个最便宜 judge variants
- 打通 accuracy / COC / worst-family miss 的最小计算链路

### Day 4

- 做 object signal 初筛：看是否存在 ranking inversion 或明显 worst-family 分化
- 若信号弱，优先检查 family fidelity 和 judge heterogeneity，而不是盲目扩规模

### Day 5

- 做 shortcut audit：长度、位置、来源提示、reasoning-fluff artifact
- 决定保留哪些 family 进入正式 object slice

### Day 6

- 在冻结的 object slice 上重跑最小评测
- 记录 Object gate 的 go/no-go 决策与原因

### Day 7

- 若 Object gate 通过，准备 Audit gate 的正式控制设计
- 若未通过，收束到 fallback A/B/C 中最合适的一支，不做无界 sweep

## 7. Immediate Next Step

当前默认直接进入 `docs/object_gate.md` 里的最小闭环，不等待额外问题澄清。

## 8. Current Bootstrap Decision

基于当前 verifier-backed 结果，bootstrap 主线默认先用 `style_flip + substance_flip` 推进 Object gate；`reasoning_fluff` 只有在出现明显不同的新生成 recipe 时才重开。
