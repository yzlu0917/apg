# 1. Title

**主标题**
**From Accurate Verifiers to Causal Verifiers: Measuring and Training Self-Correction that Actually Uses Verification**

**备选标题 1**
**Do Verifiers Cause Better Reasoning? A Causal Framework for Self-Correction in Language Models**

**备选标题 2**
**Intervention-Calibrated Self-Correction for Language Models**

**备选标题 3**
**Reasoning Needs Causal Verification, Not Just Better Critics**

---

# 2. One-Paragraph Thesis Summary

本 proposal 要解决的问题不是“模型能不能在第二次尝试时答得更准”，而是一个更本质的问题：**当模型收到 verifier / critique 发出的错误信号后，它是否真正把该信号作为决策依据来决定继续保留、局部修复，还是放弃回答**。最近的工作一方面表明 self-correction 可以被训练出来，另一方面又显示 self-critique 往往塌陷，而中间解释或结构化 reasoning 也经常并不因果性地决定最终答案；这说明社区缺少的不是又一个更强 verifier，而是一个新的研究对象：**verification signal 对 revision 行为的因果控制力**。本 proposal 围绕这一点提出新的问题定义、因果评测协议 CAVE、训练原则 ICVT，以及一组可证伪的预测与机制分析，目标是在 exact-checkable reasoning、code self-repair 和 planning 上分离“多一次生成机会的收益”和“真正来自 verifier 内容的收益”，并把后者直接作为训练目标。若该主张成立，它将改变社区对 self-correction、PRM/verifier 和 reasoning faithfulness 的评价标准。 ([OpenReview][1])

---

# 3. Abstract

近一年的研究在 self-correction 与 verifier-guided reasoning 上形成了明显张力：一类工作表明，语言模型的自我修正可以通过在线强化学习或专门微调显著增强；另一类工作则发现，同一个模型生成的 critique 经常并不能稳定提升结果，甚至强 external verifier 的收益中也有相当一部分可能来自“多一次生成机会”而非 critique 内容本身。与此同时，faithfulness 研究开始显示，模型生成的解释、检查表或中间结构常常只是与最终输出相关，却不一定因果性地决定最终输出。基于这一张力，本 proposal 提出一个新的研究问题：**自我修正系统的关键，不是 verifier 是否准确，而是模型是否对 verifier 信号形成可测、可训练、可证伪的因果依赖**。为此，我们计划构建 CAVE（Causal Assessment of Verifier Efficacy）基准：在数学、代码和规划任务中，通过局部反事实干预构造 paired examples，使“如果 verifier 真被用了，模型应如何改变动作”变得可自动判定。方法上，我们提出 ICVT（Intervention-Calibrated Verifier Training）：先定位 fail span，再预测修复收益，最后只对受影响后缀进行局部修复，并通过 matched shuffle controls 将“procedure effect”和“verifier-content effect”分离。实验上，我们将比较 prompt self-correction、external-verifier reprompting、PRM-guided search 与本方法，并在 LiveCodeBench 和 MathArena 等污染控制较强的外部基准上验证迁移性。预期贡献包括：一个新的问题定义、一套新的因果评测指标、一个资源可行的训练原则，以及关于何种 verifier 信号真正改变模型行为的机制证据。 ([OpenReview][1])

---

# 4. Motivation and Problem Statement

## 4.1 当前最关键的现象与领域张力

当前 reasoning 研究有三条并行主线，但它们还没有在一个统一的问题定义下会合：

* **主线 A：训练 self-correction。**
  SCoRe 直接用多轮在线 RL 训练 self-correction；CoSC 与 intrinsic self-correction 工作则表明，自我修正行为可以通过专门的 prompting 或微调被激发。 ([OpenReview][1])

* **主线 B：训练或使用更强 verifier / PRM。**
  ThinkPRM 一类工作说明，生成式 PRM 能用极少 process labels 支撑 best-of-N 与 reward-guided search。 ([arXiv][2])

* **主线 C：质疑 explanation / intermediate structure 的因果性。**
  Walk the Talk 通过 counterfactual concept edits 测 explanation faithfulness；Breaking the Chain 更直接显示，中间结构被干预后，模型常常仍不更新最终决定。 ([arXiv][3])

这三条线合在一起暴露了一个更深的断层：**我们知道如何提高 verifier 的分数，也知道如何让模型多尝试一次，但我们并不知道模型是否真正“因为 verifier 的内容而改了答案”**。这使得很多 reported gains 都难以解释：它们到底来自真实的 error-localization 与 correction，还是来自再采样、prompt 变长、第二次 decode 的偶然修正？([OpenReview][4])

## 4.2 主流研究范式哪里不够

主流范式的不足不在于它们“效果不够好”，而在于它们**测错了对象**：

* verifier 论文主要汇报 verifier accuracy、AUC、best-of-N uplift；
* self-correction 论文主要汇报修正后 accuracy；
* faithfulness 论文主要汇报 explanation 是否与模型行为一致。

但这些指标都无法单独回答同一个问题：**verifier 信号是否因果性地控制了 revision policy**。如果没有这个层面的测量，社区就难以区分：

* “verifier 真的被用了”
* “只是多跑了一次”
* “只是 prompt artifact”
* “只是更长 CoT 带来的重采样收益”

## 4.3 我们真正想问的研究问题

> **Research Question**
> 对于一个生成初始答案、接收 verifier 信号、再决定 keep / revise / abstain 的语言模型系统，怎样定义、测量并训练“对 verifier 的因果依赖”，使其成为比 verifier accuracy 或 end-to-end uplift 更科学的研究对象？

## 4.4 如果这项工作成功，会改变什么

如果成功，这项工作会改变三个层面：

* **改变问题定义**：
  从 “self-correction 是否有效” 改成 “模型是否对 verification 形成因果依赖”。

* **改变评价方式**：
  verifier 论文不能只报 AUC / reward accuracy；还应报 verifier-mediated utility。

* **改变方法原则**：
  reasoning 系统不该默认通过更多采样、更长 CoT、更复杂 orchestration 提升，而应优先提升 **error localization、action gating 与 localized repair**。
  这也与 honesty work 的核心精神一致：可靠性不仅是“给出答案”，也是“知道什么时候应该修、什么时候该停”。 ([arXiv][5])

---

# 5. Core Hypothesis and Research Claims

## **H1 — 主假设**

**Claim**
在 self-correction 系统中，真正决定长期价值的不是 verifier 的静态准确率，而是模型对 verifier 内容的**因果依赖强度**；只有当 verifier 信号能稳定改变 keep / revise / abstain 决策时，verification 才构成真实能力而非表面相关。

**Intuition**
一个“准但没被用上”的 verifier，不会改变系统的决策结构；一个“被真正用上”的 verifier，哪怕不是最强 judge，也能稳定改变 revision 行为。

**Testability**
通过 matched-shuffle controls、局部反事实干预和 action-level metrics，估计 verifier-mediated utility 与普通二次生成收益的差异。

---

## **H2 — 子假设 1**

**Claim**
现有 prompt-based self-correction 和一部分 verifier-guided pipelines 的主要收益，来自 **procedure effect**（多一次生成/重试）而非 **verifier-content effect**（verifier 内容本身）。

**Intuition**
很多系统在加入 critique 后变好，但 critique 被打乱或弱化时仍维持大部分收益，说明提升并不依赖 critique 内容。

**Testability**
将 verifier 输出在匹配难度的样本间打乱，比较性能下降幅度。

---

## **H3 — 子假设 2**

**Claim**
在单点或局部错误主导的任务上，**localized suffix repair** 比 full regenerate 更能体现 verifier 的因果作用，也更具 token efficiency。

**Intuition**
若 verifier 真定位了错误，最合理的修正应是局部而非整体重写；full regenerate 更容易混入 resampling gain。

**Testability**
比较 localized repair 与 full regenerate 在 LRP、SRU、token cost 上的差异。

---

## **H4 — 子假设 3**

**Claim**
如果 verifier 还输出“修复收益”而不只是 binary correctness，则 action gating 会更稳定，能显著减少 over-revision。

**Intuition**
不是每个错误都值得修；有些答案已经正确，有些修复成本过高，有些任务信息不足。修不修本身是一个 utility decision。

**Testability**
比较有无 gain calibration 时的 revise rate、abstain rate、SRU 与准确率。

---

## **H5 — 子假设 4**

**Claim**
因果依赖最容易在 **exact-checkable** 任务中被训练出来，并首先迁移到 code self-repair、constraint reasoning、planning 这类外部验证强的场景；对开放式 proof-writing 或自由文本 QA 的迁移会更弱。

**Intuition**
verification 的科学实验台应首先来自低歧义环境；这不是缺点，而是识别机制的必要条件。

**Testability**
在 CAVE 上训练后，外测到 LiveCodeBench 与 MathArena 的不同子集，比较迁移强弱。

---

# 6. Why This Proposal is Novel

## 6.1 Closest prior work

### 类别 A：Self-correction 训练与 prompting

* **SCoRe**：用多轮在线 RL 训练 self-correction。 ([OpenReview][1])
* **CoSC**：把 self-correction 嵌入多阶段数学求解流程。 ([OpenReview][6])
* **Intrinsic Self-Correction**：强调 fair prompt 与 zero temperature 可激发内生自我修正。 ([OpenReview][7])

### 类别 B：Verifier / PRM-guided reasoning

* **ThinkPRM**：用生成式 PRM 支撑 best-of-N 与 reward-guided search，强调 verifier 的数据效率与 test-time scaling 价值。 ([arXiv][2])

### 类别 C：Faithfulness / causal evaluation

* **Walk the Talk**：用 counterfactual concept edits 测 explanation faithfulness。 ([arXiv][3])
* **Breaking the Chain**：直接检验中间结构是否因果性地决定最终输出。 ([arXiv][8])

## 6.2 What they achieved

这些工作已经分别解决了重要但局部的问题：

* Self-correction 线证明了“修正行为”可以被 prompt 或训练诱导。 ([OpenReview][1])
* PRM 线证明了 verifier 可以在搜索与 reranking 中带来真实收益。 ([arXiv][2])
* Faithfulness 线证明了“解释/结构看起来合理”不等于“它真的控制了输出”。 ([arXiv][3])

## 6.3 What is still missing

缺的不是更多组件，而是一个尚未被明确提出的研究对象：

* self-correction 论文通常不测 **verifier 是否真正驱动 revision**；
* verifier 论文通常不测 **policy 是否真正使用 verifier**；
* faithfulness 论文通常不把因果性变成 **训练目标**。

也就是说，当前文献还没有把 **“从 verifier 准确，到 verifier 被模型因果性使用”** 作为一个闭环问题来研究。

## 6.4 What is irreducibly new here

本 proposal 的不可替代贡献是一个**组合式创新**：

* **新问题定义**：
  把研究对象从 self-correction 成功率，提升为 **verifier 对 revision policy 的因果控制力**。

* **新评测视角**：
  用局部反事实干预、matched shuffle controls 和 action-level utility，把 “procedure effect” 与 “verifier-content effect” 分离。

* **新训练原则**：
  不再只优化 verifier 分数或最终答案，而是直接训练 **localize → estimate gain → repair suffix / abstain** 的 action pipeline。

* **新机制主张**：
  若 verifier 真在起作用，改动应该局部化、可干预、可被 shuffle 破坏、并在机制分析中显现为对 fail span 的更强依赖。

**重要判断**
如果这项工作只做成一个“新 benchmark”或“更强 pipeline”，novelty 不够强，最多是扎实的 benchmark / empirical study。它之所以有顶会主叙事潜力，是因为 benchmark、metric、training principle 和 mechanism claim 是同一问题定义下的一体化设计，而不是模块拼装。

---

# 7. Conceptual Framework

## 7.1 核心概念

* **Initial reasoning trace**：(r_0)
  模型首次生成的推理轨迹或代码解答。

* **Verifier signal**：(v = (s, g, a))

  * (s)：fail span / suspect span
  * (g)：预计修复收益（gain estimate）
  * (a)：动作先验，(a \in {\text{keep}, \text{revise}, \text{abstain}})

* **Revision policy**：(\pi_\theta(y, a \mid x, r_0, v))
  给定问题 (x)、初始轨迹 (r_0) 与 verifier 信号 (v)，输出动作与最终答案。

* **Utility**：(U(y))
  任务效用，可由 exact correctness、token cost、错误修复收益、过度修正惩罚等构成。

## 7.2 变量角色划分

### 研究对象

* 修正策略 (\pi_\theta)

### 观测量

* 输入问题 (x)
* 初始轨迹 (r_0)
* verifier 输出 (v)
* 最终答案 (y)
* token cost (c)
* exact checker outcome (z)

### 机制变量

* fail span (s)
* gain estimate (g)
* action prior (a)

### 干预变量

* (do(r_0[s] \leftarrow r_0'[s]))：局部修改推理/代码片段
* (do(v \leftarrow \tilde v))：打乱 verifier 内容
* (do(s \leftarrow \varnothing))：遮蔽定位信息

### 结果变量

* exact accuracy
* selective revision utility
* localized repair precision
* verifier mediation gap

## 7.3 简化因果图

[
X \rightarrow R_0 \rightarrow V \rightarrow A \rightarrow Y
]
同时存在直接路径：
[
X \rightarrow Y,\quad R_0 \rightarrow Y
]

其中：

* (V) 不是研究终点；
* **关键因果链** 是 (V \rightarrow A \rightarrow Y)；
* 若该链很弱，则 verifier 只是“相关上下文”，而非“因果中介”。

## 7.4 核心分解

我们把二次修正系统相对于单次生成的总收益分解为：

[
\Delta_{\text{total}}
=====================

\Delta_{\text{proc}} + \Delta_{\text{ver}}
]

其中：

[
\Delta_{\text{proc}}
====================

\mathbb{E}[U(\pi_\theta(x, r_0, \tilde v)) - U(\pi_0(x))]
]

表示**procedure effect**：多一次生成机会、更多上下文、更多 decode 带来的收益。

[
\Delta_{\text{ver}}
===================

\mathbb{E}[U(\pi_\theta(x, r_0, v)) - U(\pi_\theta(x, r_0, \tilde v))]
]

表示**verifier-content effect**：真实 verifier 内容相对于 matched-shuffled verifier 的额外收益。

本 proposal 的核心不是最大化 (\Delta_{\text{total}})，而是最大化 (\Delta_{\text{ver}})。

## 7.5 关键指标

* **VMG (Verifier Mediation Gap)**
  估计 (\Delta_{\text{ver}})

* **IRR (Intervention Response Rate)**
  在 paired interventions 上，动作是否随 gold intervention 正确变化

* **LRP (Localized Repair Precision)**
  修复是否主要集中在 gold fail span 附近

* **SRU (Selective Revision Utility)**
  修正收益减去 token / over-revision 成本后的净效用

* **CCE (Causal Calibration Error)**
  预测 gain 与真实 gain 的校准误差

---

# 8. Research Plan

## 8.1 Data / task / benchmark

## 8.1.1 核心新基准：CAVE

我们将构建 **CAVE: Causal Assessment of Verifier Efficacy**。

### 组成

* **CAVE-Sym**：算术、方程、逻辑约束、小型组合推理
* **CAVE-Code**：可执行、可单测的代码生成与局部修复
* **CAVE-Plan**：Game of 24、graph coloring、STRIPS-like planning

选择这些任务的原因是：

* 有明确 correctness checker；
* 可构造局部错误与唯一 gold action；
* 与现有 self-verification 争议任务高度对齐。
  其中 Game of 24、graph coloring、STRIPS planning 已被用于研究 self-verification 的局限。 ([OpenReview][4])

### 数据构建方式

每个样本包含：

* 问题 (x)
* 初始轨迹 (r_0)
* gold fail span (s^*)
* gold action (a^*)
* gold repair suffix (t^*)
* exact checker
* utility delta

### paired interventions 生成

1. 从正确解或高质量候选解出发
2. 在单个 step / 单个 code block / 单个 planning constraint 上注入局部错误
3. 保留其余上下文不变
4. 通过 exact checker 自动判定：

   * 是否必须 revise
   * 是否应该 keep
   * 是否应 abstain（通过构造信息缺失或约束矛盾切片）

### 控制切片

* **verdict-preserving paraphrase**：改写表述，不改变 gold verdict
* **matched shuffle**：打乱 verifier 内容但保持难度匹配
* **multi-error / entangled-error**：测试 locality 假设边界

### 规模

* CAVE-Sym：30k train / 3k dev / 3k test
* CAVE-Code：20k train / 2k dev / 2k test
* CAVE-Plan：15k train / 2k dev / 2k test
  总量控制在 LoRA 微调可承受范围内。

## 8.1.2 外部评测基准

* **LiveCodeBench**：
  它显式覆盖 code generation、self-repair、code execution 与 test output prediction，非常适合验证“从 exact-checkable 合成环境学到的 verifier dependence 能否迁移到真实代码场景”。 ([OpenReview][9])

* **MathArena**：
  它通过新发布竞赛题降低污染风险，并额外覆盖 proof-writing；这使其适合作为“更开放、更难、但污染控制更强”的 out-of-domain stress test。 ([arXiv][10])

**注意**
MathArena 的 proof-writing slice 不适合作为主训练数据，因为精确局部因果标签较弱；它更适合作为迁移与边界测试。

---

## 8.2 Method

## 8.2.1 方法概览

提出 **ICVT: Intervention-Calibrated Verifier Training**。

### 核心思路

不是让模型“再想一遍”，而是让它学会三个动作：

1. **Localize**：哪里错了
2. **Estimate**：修这处错值不值得
3. **Act**：keep / revise / abstain
4. **Repair**：若 revise，只修受影响后缀

## 8.2.2 模型组件

* **Policy model** (P_\theta)
  负责初始解答与局部修复

* **Verifier model** (V_\phi)
  输入 (x, r_0)，输出 (v=(s,g,a))

### 输出定义

* (s)：离散 span 或 segment index
* (g \in [0,1])：预计修复收益
* (a \in {\text{keep}, \text{revise}, \text{abstain}})

## 8.2.3 训练流程

### Phase A — Verifier pretraining

目标：学习 fail span、action、gain

损失：
[
L_{\text{ver}} = L_{\text{loc}} + \lambda_1 L_{\text{act}} + \lambda_2 L_{\text{gain}}
]

### Phase B — Repair policy SFT

给定 oracle fail span，学习 gold repair suffix

[
L_{\text{rep}}
==============

\text{NLL}(t^* \mid x, r_0[:s^*])
]

### Phase C — Joint intervention-calibrated finetuning

使用 predicted span 与 predicted action 进行闭环训练

[
L
=

L_{\text{loc}} + \lambda_1 L_{\text{act}} + \lambda_2 L_{\text{gain}} + \lambda_3 L_{\text{rep}} + \lambda_4 L_{\text{inv}}
]

其中 (L_{\text{inv}}) 用于强制 verdict-preserving paraphrase 下策略稳定。

## 8.2.4 推理流程

**Algorithm: Causal self-correction**

1. 生成初始轨迹 (r_0 = P_\theta(x))
2. 计算 verifier 输出 (v=(s,g,a)=V_\phi(x,r_0))
3. 若 (a=\text{keep}) 且 (g < \tau_k)：直接输出
4. 若 (a=\text{abstain})：输出 abstain
5. 若 (a=\text{revise}) 且 (g \ge \tau_r)：
   仅从 (s) 之后进行 suffix repair
6. 最多进行 1 次修复迭代

**设计选择**
核心方法刻意限制为 **单次 verifier + 单次 repair**。
原因：我们要研究 verifier dependence，而不是靠多轮 agent loop 把性能“搅出来”。

## 8.2.5 复杂度与成本

设完整输出长度为 (L)，修复后缀占比为 (\rho)。

* full regenerate：约 (O(L)) 额外 decode
* localized repair：约 (O(\rho L)) 额外 decode，通常 (\rho < 0.5)

因此该方法天然更适合在固定 token budget 下测试“同样预算里，verifier 内容是否真正带来额外收益”。

---

## 8.3 Theoretical / mechanistic analysis

这一节不是装饰，而是直接服务于主张。

### A. 因果分解分析

目标：估计 (\Delta_{\text{proc}}) 与 (\Delta_{\text{ver}})

方法：

* matched shuffle controls
* matched generic retry baseline
* same token-budget comparisons

作用：

* 证明收益来自 verifier 内容，而非简单多试一次

### B. Locality analysis

目标：验证“错误定位—局部修复”是否真实发生

分析：

* edit distance / edit span overlap
* repair token concentration near fail span
* LRP 分布

作用：

* 若改进主要来自局部修复，支持我们的机制假设；
* 若大量成功样本靠整体重写，说明 locality 假设过强。

### C. Internal sensitivity analysis

目标：检查模型是否更依赖 verifier 指向的局部状态

分析：

* fail-span attention mass
* verifier-conditioned hidden-state perturbation
* masked-span ablation

作用：

* 提供机制证据，表明模型并非把 verifier 当作泛化提示词，而是对特定错误位置产生更强依赖。

### D. Calibration analysis

目标：验证“修复收益预测”是否有意义

分析：

* 预测 gain vs realized gain 的 reliability curve
* CCE
* over-revision / under-revision breakdown

作用：

* 支撑“修不修”本身是一个可学习的 utility decision。

---

## 8.4 Expected empirical signatures

如果 hypothesis 成立，实验应出现以下 pattern：

* baseline 往往有明显 **procedure effect**，但 **VMG 较低**
* ICVT 在相近 token budget 下提升 **VMG、IRR、SRU**
* shuffle verifier 会显著伤害 ICVT，但对 generic regenerate baseline 伤害较小
* localized repair 优势集中在单点或局部错误
* 在 multi-error / entangled-error 任务上，localized repair 的优势会减弱
* 向 LiveCodeBench 的迁移应强于向开放式 proof-writing 的迁移

---

# 9. Experimental Design

## 9.1 Models

## 主实验模型

* **Math / planning policy**：Qwen2.5-Math-7B-Instruct 或同级 7B reasoning backbone
* **Code policy**：Qwen2.5-Coder-7B-Instruct
* **Confirmatory scale-up**：Qwen2.5-14B-Instruct / Qwen2.5-Coder-14B-Instruct
* **Auxiliary reasoning backbone**：DeepSeek-R1-Distill-Qwen-7B（用于 backbone 替换实验）

这些选择的理由是：

* Qwen 官方模型卡同时提供 7B/14B 一般模型与 coder 变体；
* Qwen2.5-Math-7B 明确被定位为更适合作为 math fine-tuning 起点；
* DeepSeek-R1-Distill-Qwen-7B 是公开可得的 7B reasoning model。 ([Hugging Face][11])

## Verifier 模型

* 3B–7B 同系列轻量模型
* 先独立训练，再尝试 shared-backbone multi-head 作为 ablation

## Judge / evaluator

* **主评测**：exact checker、unit tests、planning validator
* **辅助评测**：仅在开放式 error taxonomy 上使用 API judge
* 原则：**核心结论不依赖 LLM-as-a-judge**

---

## 9.2 Baselines

### B1. Direct-answer baseline

* 单次生成，无 correction
* 必须有，用于估计总收益

### B2. Prompted intrinsic self-correction

* fair prompt + low/zero temperature 的 intrinsic self-correction
* 强在于它是“最便宜”的自我修正控制组。 ([OpenReview][7])

### B3. Self-critique + full regenerate

* 同模型自评后整体重写
* 强在于它代表最常见、最容易实现的 self-correction pipeline。 ([OpenReview][4])

### B4. Sound external verifier + reprompting

* 用外部 checker / verifier 反馈后再生成
* 这是 reasoning/planning 场景下最难打败的强基线之一。 ([OpenReview][4])

### B5. ThinkPRM-style PRM-guided reranking / search

* best-of-N + verifier scoring
* 强在于它直接代表当前 verifier/PRM 路线。 ([arXiv][2])

### B6. Released self-correction-tuned system（可选）

* 若 SCoRe/CoSC 的可复现 checkpoint 可用，则作为附加对比
* 这类对比有价值，但**不应绑死主线**；若复现成本高，放附录。 ([OpenReview][1])

**最难打败的 baseline**
在 exact-checkable 场景下，最难的是 **B4 + B5**：
一个代表“强 external verification”，一个代表“强 verifier-guided search”。

---

## 9.3 Main experiments

## E1. Baseline causal-gap profiling

* **目的**：确认现有系统中“verifier 准”与“真的用 verifier”是否脱钩
* **设置**：在 CAVE-Sym / Code / Plan 上运行 B2–B5
* **变量**：verifier accuracy、VMG、IRR
* **指标**：AUC, exact acc, VMG
* **预期现象**：会出现高 verifier accuracy 但低 VMG 的方法
* **若结果相反**：说明社区已有方法已具备较强 causal dependence，本 proposal 需收缩为更窄的 efficiency / locality paper

## E2. ICVT vs baselines under equal token budget

* **目的**：验证在相同预算下，ICVT 是否更有效地把预算转化为 verifier-mediated gain
* **设置**：固定 token budget，对比 B3/B4/B5 与 ICVT
* **变量**：方法类型、budget
* **指标**：exact acc, SRU, VMG
* **预期现象**：ICVT 的 VMG/SRU 提升大于 total compute increase
* **若结果相反**：说明当前优势仍主要来自额外计算，而非问题重定义

## E3. Shuffle-verifier null test

* **目的**：检验方法是否真的依赖 verifier 内容
* **设置**：将 verifier 输出在难度匹配样本间打乱
* **变量**：real vs shuffled verifier
* **指标**：VMG, exact acc, revise rate
* **预期现象**：ICVT 明显掉；generic regenerate 掉得少
* **若结果相反**：说明 ICVT 的提升并非来自 causal use

## E4. Localized repair vs full regenerate

* **目的**：验证 locality 假设
* **设置**：只改 fail span 后缀 vs 整体重写
* **变量**：repair scope
* **指标**：LRP, token cost, SRU, exact acc
* **预期现象**：localized repair 在单错误场景更优；entangled errors 下会退化
* **若结果相反**：说明局部修复不是核心机制，需考虑 hierarchical repair

## E5. Gain calibration ablation

* **目的**：验证“修不修”的 gain prediction 是否关键
* **设置**：去掉 gain head / action gating
* **变量**：with vs without (g)
* **指标**：over-revision, abstain error, SRU
* **预期现象**：无 gain calibration 时 revise 过多、SRU 下降
* **若结果相反**：说明单一 gain 标量不足以描述 decision utility

## E6. Out-of-domain transfer

* **目的**：检验该原则是否只对 synthetic benchmark 有效
* **设置**：训练于 CAVE；外测到 LiveCodeBench self-repair 与 MathArena
* **变量**：domain, task type
* **指标**：self-repair success, execution pass@1, proof-writing quality, VMG proxy
* **预期现象**：迁移到 code self-repair 强于开放式 proof-writing
* **若结果相反**：若完全不迁移，则该方法更适合作为 diagnostic/evaluation proposal

## E7. Mechanistic verification

* **目的**：提供“为什么有效”的证据
* **设置**：对成功修复样本做 edit locality 与 hidden-state sensitivity 分析
* **变量**：baseline vs ICVT
* **指标**：fail-span attention mass, edit concentration, masked-span sensitivity
* **预期现象**：ICVT 对 fail span 的依赖更集中
* **若结果相反**：说明模型可能只是学会“收到 verifier 后重写”，而非真正定位并利用错误

---

## 9.4 Ablations

关键 ablation 维度：

* Oracle fail span vs predicted fail span
* with vs without gain calibration
* localized repair vs full regenerate
* single-step repair vs two-step repair
* same-model verifier vs separate verifier
* with vs without paraphrase invariance loss
* single-error vs multi-error training mix
* exact-checkable only vs mixed training

---

## 9.5 Robustness / stress test

至少三类压力测试：

1. **Distribution-preserving shuffle controls**
   排除 prompt-length / retry artifact

2. **Verdict-preserving paraphrase**
   排除 lexical shortcut

3. **Entangled-error stress test**
   检验 locality 边界

4. **Cross-domain transfer**
   检验是否只是 synthetic overfit

5. **Budget sweep**
   检验提升是否依赖额外 token 而非 verifier dependence

---

## 9.6 Statistical validity

* **Seeds**：所有 trainable system 至少 3 seeds
* **Confidence intervals**：paired bootstrap 95% CI
* **Significance test**：

  * McNemar for paired exact accuracy
  * randomization test for shuffle controls
* **避免 cherry-picking**：

  * 预先固定主指标：VMG、SRU、exact acc
  * 预先固定选择规则：仅按 dev 上的 (0.5 \cdot VMG + 0.3 \cdot SRU + 0.2 \cdot acc) 选 checkpoint
  * 所有 budget sweeps 全量报告，不只报最佳点

---

# 10. Falsifiable Predictions

## **Prediction 1**

**Prediction**
现有强 baseline 会出现“verifier accuracy 高，但 VMG 低”的显著脱钩。

**How to test**
在 CAVE 上同时测 verifier accuracy、AUC、VMG、IRR。

**What failure would imply**
如果 accuracy 与 VMG 高度一致，说明社区现有评价标准已经接近正确。

**How the theory would be revised**
将主张从“需要新问题定义”收缩为“需要更高效的 verifier-conditioned repair”。

---

## **Prediction 2**

**Prediction**
ICVT 对 shuffled verifier 会比 prompt-only / generic regenerate baseline 更敏感。

**How to test**
在 matched difficulty bucket 内打乱 verifier 输出，比较性能下降幅度。

**What failure would imply**
如果 ICVT 对 shuffle 不敏感，说明它没有真正利用 verifier 内容。

**How the theory would be revised**
把方法解释从“causal dependence training”下调为“regularized second-pass generation”。

---

## **Prediction 3**

**Prediction**
localized repair 会在单局部错误任务上优于 full regenerate，但在多错误、全局纠缠任务上优势减弱。

**How to test**
将测试集按 error locality 分层，分别比较 LRP、SRU、token cost 与 accuracy。

**What failure would imply**
如果 full regenerate 全面更强，则 locality 不是决定性机制。

**How the theory would be revised**
改为两级策略：先 local repair，失败后 global restart。

---

## **Prediction 4**

**Prediction**
加入 gain calibration 后，over-revision 会显著下降，SRU 上升，即使 exact accuracy 提升有限。

**How to test**
做无 gain head / 无 action gating ablation。

**What failure would imply**
如果 gain head 没用，说明“修复收益”不适合用单标量表示。

**How the theory would be revised**
改为多维 utility state，如 error type、repairability、information sufficiency 的分解预测。

---

## **Prediction 5**

**Prediction**
从 CAVE 训练得到的提升，会更强地迁移到 LiveCodeBench self-repair / execution，而不是开放式 proof-writing。

**How to test**
固定模型与 budget，比较两类外部评测的相对收益。

**What failure would imply**
如果迁移完全不成立，说明 CAVE 的局部因果标签缺乏外推性。

**How the theory would be revised**
将论文重心调整为 evaluation / diagnosis，而非 general training principle。

---

## **Prediction 6**

**Prediction**
成功修复样本中，ICVT 的编辑位置和内部敏感性会更集中于 verifier 标记的 fail span。

**How to test**
比较 baseline 与 ICVT 的 edit locality、masked-span sensitivity、attention mass。

**What failure would imply**
如果成功修复并不局部，说明模型只是把 verifier 当作“重试触发器”。

**How the theory would be revised**
需引入更强的 structural editing module，或接受“causal dependence 主要表现为 action selection 而非 local mechanism”。

---

# 11. Risks, Failure Modes, and Plan B/C

## 11.1 理论风险

### 风险 A：procedure effect 与 verifier-content effect 难以干净分离

* **问题**：matched shuffle 可能仍有残余分布差异
* **后果**：VMG 解释力下降
* **缓解**：

  * difficulty buckets
  * length buckets
  * initial correctness matching
  * generic retry controls

## 11.2 实验风险

### 风险 B：verifier 能定位，但 repair model 改不动

* **问题**：闭环训练可能卡在“会指出错，但不会修”
* **缓解**：

  * 先用 oracle fail span 训练 repair
  * 再切换 predicted fail span
  * 必要时引入 hierarchical fallback

### 风险 C：localized repair 过度约束

* **问题**：某些任务错误会全局传播
* **缓解**：

  * 加 multi-error split
  * 提供 local-to-global fallback ablation

## 11.3 Benchmark 风险

### 风险 D：CAVE 太 synthetic

* **问题**：审稿人可能质疑外推性
* **缓解**：

  * 早期就接 LiveCodeBench / MathArena
  * 对 200–300 个样本做人审
  * 公布 intervention templates 与 checker scripts

## 11.4 识别与解释风险

### 风险 E：即便看到提升，也未必能证明是“因果依赖”

* **问题**：解释性证据不充分
* **缓解**：

  * 强化 shuffle null
  * 做 fail-span masking
  * 报告机制分析而非只报 accuracy

## 11.5 工程风险

### 风险 F：训练成本蔓延成复杂 pipeline

* **问题**：容易失控成另一个 orchestration paper
* **缓解**：

  * 核心方法只允许单 verifier + 单 repair
  * 多轮 search/RL 只进附录
  * 任何新增组件必须证明它提高的是 VMG，而不是纯 compute

---

## Plan B

如果训练方法增益有限，但 CAVE 明确揭示了强 baseline 的 causal gap，则项目转为：

* **主线**：新评测透镜 + 系统性诊断
* **方法**：保留最简 action-gated verifier 作为 proof-of-concept
* **论文定位**：强顶会 evaluation / methodology paper
  这仍有较高价值，但“best-paper 叙事”会弱于完整闭环。

## Plan C

如果 general reasoning 迁移弱，则收缩到 **code self-repair / planning**：

* 这些域有更强 external verification
* 因果识别更干净
* 更容易给出机制与可复现结论

**诚实判断**
纯 benchmark-only 版本像强 benchmark / empirical study；
缩到 code/planning 的 exact-verification 版本，仍可能是很强的顶会方法+evaluation 论文；
完整版本才最接近“问题定义改变”的 best-paper 叙事。

---

# 12. Feasibility Under Compute Constraints

## 模型规模

* Verifier：3B–7B
* Policy：7B 主实验，14B confirmatory
* 不做大规模预训练，只做 LoRA / full-head 微调

## 训练估算

* **Verifier 3B/7B LoRA**：2–4 GPU-days
* **Policy 7B LoRA**：6–10 GPU-days / seed
* **Confirmatory 14B LoRA**：10–14 GPU-days / seed
* **大规模评测与 budget sweeps**：6–8 GPU-days
* **总量**：约 55–75 GPU-days
  在 16×80GB A800 下完全可做，且可并行化。

## 显存与并行

* 7B BF16 + LoRA：2–4 卡足够
* 14B BF16 + LoRA：4–8 卡
* 一台机器跑训练，一台机器跑评测 / 数据构造 / verifier sweep

## 数据生成成本

* CAVE 主体依赖 exact checker、unit tests、planning validator，GPU/API 成本低
* API 主要用于：

  * paraphrase 生成
  * 小规模人工审核辅助
  * qualitative taxonomy
* 核心结论不依赖大量 API judge

## 为什么在给定资源下可做

* 无需数千卡周预训练
* 核心数据可程序化构造
* 核心训练是中等规模 LoRA
* 关键识别依赖对照实验，而非模型规模

---

# 13. Reproducibility and Engineering Plan

## 配置管理

* Hydra / OmegaConf
* 每个实验一个 config hash
* 训练、推理、评测配置分离

## 实验记录

* W&B 或 MLflow
* 强制记录：

  * model hash
  * dataset version
  * seed
  * token budget
  * checkpoint step
  * exact checker result

## 数据版本

* `cave_sym_v1`
* `cave_code_v1`
* `cave_plan_v1`
* `lcb_slice_YYYYMM`
* `matharena_slice_YYYYMM`

## 随机种子

* 固定 3 seeds
* 数据构造脚本与 split seed 分离保存

## Checkpoint 策略

* 固定步长保存
* 不按 test 表现选模型
* 按预注册 dev composite 选唯一主模型

## 评测脚本

必须公开：

* exact checker
* unit-test runner
* shuffle-control generator
* paraphrase-control builder
* metric scripts（VMG / IRR / SRU / LRP / CCE）

## 需要保存的关键 artifacts

* 初始轨迹 (r_0)
* verifier 输出 (v)
* fail span 标注
* final repair
* edit diff
* token cost
* checker outputs
* shuffle mapping
* per-example utility logs

## 发布建议

* 开源 CAVE 数据构造代码
* 发布最小可运行 checkpoint
* 提供全部主要图表复现 notebook
* 发布 error taxonomy sample pack

---

# 14. Timeline and Milestones

## Week 1–2：最小闭环

* 搭建 CAVE-Sym v0 与 CAVE-Plan v0
* 跑 B1–B4 prompt baselines
* 实现 VMG / IRR / SRU
* **目标**：确认 baseline 存在 causal gap

## Week 3：Go / No-Go

* 训练 verifier v0
* 完成 shuffle null
* **Go 条件**：

  * baseline verifier accuracy 与 VMG 脱钩明显
  * shuffle 能显著打掉部分方法收益
* **No-Go 条件**：

  * 若所有方法都已高 VMG，则改写为 narrower efficiency proposal

## Week 4–5：主方法成型

* 训练 repair policy v0
* 跑 oracle span vs predicted span
* 完成 localized repair vs full regenerate

## Week 6：完整 ablation

* gain calibration
* invariance loss
* same-model vs separate verifier
* multi-error stress test

## Week 7：外部迁移

* LiveCodeBench self-repair / execution
* MathArena final-answer / proof-writing slices
* error breakdown

## Week 8：机制分析与写作

* internal sensitivity
* final plots/tables
* appendix baselines
* paper draft v1

---

# 15. Paper Framing

## 15.1 Best-paper style one-sentence pitch

**A verifier is only as useful as the policy’s causal dependence on it; we turn that dependence into a measurable objective, a trainable principle, and a new standard for self-correction research.**

## 15.2 Contribution bullets

* 提出 **causal verifier dependence** 作为 self-correction 的新研究对象
* 提出 **CAVE**：局部反事实、exact-checkable 的 verifier efficacy 基准
* 提出 **VMG / IRR / SRU / LRP / CCE** 一组新指标
* 提出 **ICVT**：localize → estimate gain → repair suffix / abstain 的训练原则
* 系统揭示并量化 **procedure effect 与 verifier-content effect** 的差异
* 提供机制证据，说明改进何时来自真实局部修复，何时只是“多试一次”

## 15.3 Figure plan

### Fig.1 — Problem decomposition

* 展示二次修正总收益如何分解为 procedure effect 与 verifier-content effect

### Fig.2 — CAVE construction

* 一张图说明正确轨迹、局部错误注入、gold action、repair suffix

### Fig.3 — Verifier accuracy vs VMG

* 证明“准”不等于“被真正用上”

### Fig.4 — Shuffle null

* real verifier vs shuffled verifier 的性能差异

### Fig.5 — Localized repair vs full regenerate

* token cost、LRP、SRU 的三维对比

### Fig.6 — Mechanistic evidence

* fail-span attention / edit locality / sensitivity heatmaps

## 15.4 Related work organization

建议按“问题链条”而非“方法堆叠”组织：

1. **Self-correction as behavior**
   intrinsic self-correction、CoSC、SCoRe

2. **Verification as scoring/search**
   PRM、verifier-guided reranking、best-of-N

3. **Faithfulness as causal validity**
   Walk the Talk、Breaking the Chain

4. **Reliability as action selection**
   honesty、abstention、calibration

5. **Why our framing differs**
   不是更强 critic，不是更大 compute，而是把 verifier 是否被因果性使用作为新的中心问题

---

[1]: https://openreview.net/forum?id=CjwERcAU7w "https://openreview.net/forum?id=CjwERcAU7w"
[2]: https://arxiv.org/abs/2504.16828 "https://arxiv.org/abs/2504.16828"
[3]: https://arxiv.org/abs/2504.14150 "https://arxiv.org/abs/2504.14150"
[4]: https://openreview.net/forum?id=4O0v4s3IzY "https://openreview.net/forum?id=4O0v4s3IzY"
[5]: https://arxiv.org/abs/2312.07000 "https://arxiv.org/abs/2312.07000"
[6]: https://openreview.net/forum?id=8Dj6OEMj6W "https://openreview.net/forum?id=8Dj6OEMj6W"
[7]: https://openreview.net/forum?id=pTyEnkuSQ0 "https://openreview.net/forum?id=pTyEnkuSQ0"
[8]: https://arxiv.org/abs/2603.16475 "https://arxiv.org/abs/2603.16475"
[9]: https://openreview.net/forum?id=chfJJYC3iL "https://openreview.net/forum?id=chfJJYC3iL"
[10]: https://arxiv.org/abs/2505.23281 "https://arxiv.org/abs/2505.23281"
[11]: https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct"
