# ToolShift: Schema-Robust and Risk-Aware Tool-Using Agents

## 0. 合并说明

这份 proposal 以 `idea/6.md` 为主干，保留其最有价值的核心: **tool schema evolution robustness**。在此基础上做两处定向吸收:

- 吸收 `idea/5.md` 的 counterfactual invariance / action sensitivity 视角，但明确收窄到 **tool schema 与 tool observation**，不再扩成一个过大的“agent 安全总纲”。
- 吸收 `idea/7.md` 的 risk event / conformal gating 视角，但只把它用作 **部署层的可选安全壳与评测补充**，不把主方法改成理论导向的 risk-control paper。

因此，整合后的主线非常清楚:

> **ToolShift 的主问题是“agent 是否把 schema 外观错当语义”，主方法是 schema-contrastive consistency，主评测是 schema evolution robustness；风险控制只是部署加层，不是主叙事。**

---

## 1. 一句话主张

> 对同一个语义任务，在不同 schema 变换下 agent 应输出等价调用；通过可控 schema 演化谱系、对比一致性训练和合约验证，我们可以显著提升 tool-using agent 在接口演化与真实噪声下的成功率，并用机制分析证明模型从“命名捷径”转向“语义对齐”。

---

## 2. Proposal 摘要

当前 tool-use agent 的一个常见隐含假设是:

> 工具名、参数名、字段顺序、文档写法，基本就是工具语义本身。

这在真实部署中并不成立。实际系统经常发生:

- rename
- reorder
- paraphrase
- deprecate / alias
- partial docs
- distractor tools

很多 agent 失败，不是因为不会用工具，而是因为把 **schema 外观** 学成了 **语义**。ToolShift 要把这个 failure mode 从“零散经验”升级成一条完整主线:

1. 一个新的 benchmark 轴: `Schema Evolution Spectrum (SES)`
2. 一个新的训练原则: `Schema-Contrastive Consistency (SCC)`
3. 一个新的部署组件: `contract verification`
4. 一个新的风险补层: `optional action gate`

---

## 3. 这条主线为什么独立成立

ToolShift 和其他三条主线的边界很明确:

- 它不是 reasoning training
- 不是 verifier benchmark
- 不是 compute controller

它研究的是:

> **agent 与工具接口之间的语义对齐问题**

而且这条线有非常实用的 benchmark moat。哪怕方法结果一般，只要 ToolShift suite 做扎实，也足以成为有价值资产。

---

## 4. 研究问题与可证伪预测

### 4.1 Research Questions

1. `RQ1` 当前强 tool-use agent 对 rename / reorder / partial docs / distractors 到底有多脆?
2. `RQ2` 单纯做 augmentation 是否够，还是需要显式的一致性目标?
3. `RQ3` agent 的错误主要来自 tool-name shortcut，还是 argument extraction / contract violation?
4. `RQ4` 在引入轻量 risk gate 后，是否能在不明显伤 success 的前提下降低高风险调用?

### 4.2 Falsifiable Predictions

- `P1` 在轻度 rename 下，部分 schema adaptation 方法可能占优；但在复合扰动下，SCC 应明显更稳。
- `P2` 如果 SCC 真学到了语义不变性，那么遮蔽工具名后，其性能下降应显著小于基线。
- `P3` contract verification 主要提升 syntactic / type validity，而 SCC 主要提升 semantic robustness；两者作用应互补。
- `P4` 对高风险样本加 action gate 后，风险事件率应下降，但 clean success 不应大幅崩塌；否则说明 gate 过于保守。

---

## 5. 方法设计

### 5.1 SES: Schema Evolution Spectrum

定义一组可组合 schema 变换:

- `Rename`
- `Reorder`
- `Paraphrase`
- `Drop / Mask`
- `Distractor injection`
- `Deprecate / alias`

这些变换共同定义 benchmark 的主轴。ToolShift 不只报告一个 clean score，而是报告模型在 **SES 强度** 变化下的退化曲线。

### 5.2 SCC: Schema-Contrastive Consistency

对同一个任务样本 `(x, S, y)`，采样多个 schema 变换 `g_k(S)`，要求模型在不同变换下都输出等价调用 `g_k(y)`。

训练损失由三部分组成:

1. `L_CE`
   保证基本的结构化调用能力
2. `L_cons`
   保证 tool choice / key decision representation 在不同 schema 视图下保持一致
3. `L_con`
   对 contract violation 加惩罚

这里最重要的不是“多看几种 schema”，而是强制模型在这些视图下学习一个 **nuisance-invariant state**。

### 5.3 Contract Verification

contract verification 负责两件事:

- 检查 JSON / type / range / dependency 是否合法
- 在推理端对 invalid call 做轻量 repair，而不是整轮重做

这让 ToolShift 不只是“更会选工具”，也更像一个能部署的系统组件。

### 5.4 从 5 吸收的 counterfactual 视角

来自 `idea/5.md` 的精华被有意收窄成一个指标与一个训练原则:

- 指标: `Counterfactual Tool Sensitivity (CTS)`
  - 等价变换下 action 应不变
  - 关键语义翻转下 action 应改变
- 原则:
  - 不优化“识别某种攻击模式”
  - 而优化“对不该影响行动的观测保持不变”

这样可以让 ToolShift 在 schema evolution 之外，顺带覆盖一部分 observation noise / benign injection 情况，但不会把主线拖成泛安全论文。

### 5.5 从 7 吸收的 risk-aware 部署层

来自 `idea/7.md` 的内容不作为主方法，而作为 deploy-time optional layer:

- 用小 scorer 或 verifier 给 tool action 打风险分
- 对高风险动作启用 gate 或 abstain / clarification
- 只在高风险子集上报告 `risk-success frontier`

这个设计的好处是:

- 保留了 deployability
- 不牺牲主叙事的清晰度
- 如果主方法够强，risk gate 只是锦上添花

---

## 6. 数据与实验设计

### 6.1 基准与任务

优先基准:

1. `BFCL`
2. `StableToolBench`
3. `tau-bench`

补充 stress sets:

- `FAIL-TALMS`
- `AgentNoiseBench`
- 一小部分 prompt injection / tool hijacking 子集

### 6.2 Baselines

至少比较以下五类:

1. Vanilla SFT
2. SFT + SES augmentation only
3. Hammer / robust function-calling
4. PA-Tool / schema adaptation
5. Template-based function calling / strong prompt baseline

如果做 risk gate 子实验，再加:

6. Fixed-threshold verifier gating
7. Self-certainty gating

### 6.3 核心指标

- `Success@clean`
- `Success@SES-k`
- `Contract violation rate`
- `CTS`
- `Risk-success frontier`
- `First-pass valid call rate`
- `Name sensitivity slope`

### 6.4 Minimum Viable Experiments

1. `ToolShift-lite benchmark`
   在 BFCL/StableToolBench 上先做 rename / reorder / distractor 三种扰动。
2. `SFT vs Augmentation vs SCC`
   检验一致性损失是不是核心增量。
3. `PA-Tool / Hammer boundary`
   看什么 regime 下是“适配 schema”更优，什么 regime 下是“训模型”更优。
4. `Contract verification ablation`
   比较无约束解码、仅推理约束、训练时惩罚、两者都加。
5. `Mechanistic validation`
   看 name token 遮蔽敏感性是否下降，description/constraint 依赖是否上升。
6. `Cross-benchmark transfer`
   训练在一类 schema 扰动上，测试到另一类扰动或新基准。
7. `Risk gate subset`
   只在高风险动作子集上加 gate，看风险事件率与成功率权衡。

---

## 7. 预期贡献

这条线整合完成后，目标是形成一个“bench + method + mechanism + deployment”的完整 proposal:

1. 一个新的 benchmark 主轴: `Schema Evolution Spectrum`
2. 一个新的训练原则: `Schema-Contrastive Consistency`
3. 一个新的系统组件: `contract verification`
4. 一个新的可选部署层: `risk-aware action gate`
5. 一条清晰机制结论:
   **agent 失败往往不是不会用工具，而是把 schema 外观学成了语义**

---

## 8. 风险与备选路线

### 风险 1

SES 变换不够真实，被质疑成“人造鲁棒 benchmark”。

应对:

- 参考真实工具版本演化日志
- 收集一小部分真实 API 变更样本
- 明确区分 synthetic SES 与 real evolution split

### 风险 2

提升主要来自“更多增强数据”，而不是一致性原则。

应对:

- 严格做 augmentation-only 对照
- 做 representation-level 机制验证

### 风险 3

加入 risk gate 后 success 掉太多。

应对:

- 把 risk gate 从主结果降级为 deploy appendix
- 只把它作为高风险场景的 optional layer

---

## 9. 执行计划

### Phase 1: 两周 Go / No-Go

- 搭 `ToolShift-lite`
- 跑 clean + rename + distractor 三组脆弱性曲线
- 做 `SFT vs augmentation vs SCC` 的第一轮结果

### Phase 2: 四到六周主结果

- 扩展到完整 SES
- 补 Hammer / PA-Tool / strong prompt baselines
- 固化 contract verification 与机制分析

### Phase 3: 加分项

- 做真实 API evolution split
- 补 risk gate 子实验
- 扩展到更复杂多轮工具环境

---

## 10. 最终收敛后的 proposal 形态

整合后的 ToolShift，相比原始 `5/6/7` 的分散状态，边界清楚很多:

- 主线只保留 `6` 的 schema evolution robustness
- 用 `5` 补 counterfactual invariance 的机制和评测
- 用 `7` 补 deploy-time risk layer，而不把它变成主方法

最后的工作形态非常清楚:

> **先解决 agent 是否真正学会了工具语义，再决定是否需要更强的风险控制壳。**

这让 ToolShift 成为四条主线里最像“可落地系统论文 + 强 benchmark”的那一条。
