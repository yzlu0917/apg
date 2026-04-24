# 1. Title

**主标题**
**Beyond Judge Accuracy: Counterfactual Oversight Coverage for Reliable AI Oversight**

**备选标题**

1. **Oversight Coverage, not Judge Strength: Reliable LLM-as-a-Judge under Correlated Failures**
2. **Counterfactual Oversight Coverage for LLM Judges and Reward Models**
3. **Rethinking AI Oversight via Failure-Family Coverage**

---

# 2. One-Paragraph Thesis Summary

本 proposal 要解决的问题是：**当 LLM 被用来评估、筛选、训练和监督其他模型时，什么才是真正决定监督可靠性的核心属性？** 现有范式大多用 judge 的平均准确率、人类一致率或单一 benchmark 分数来衡量质量，但近期工作已经反复暴露出系统性偏差：judge 会偏好自己的输出或相关家族模型的输出，会被风格而非内容牵引，也可能被表面“推理味”或 prompt cue 误导；与此同时，奖励模型研究也表明，平均 accuracy 并不能充分预测下游优化效果。基于这一张力，本 proposal 的核心主张是：**可靠 AI oversight 的关键不是单个 judge 更强，而是监督系统对关键失败模式的覆盖率更高、且不同 judge 的漏判不高度相关。** 我们将把这一主张形式化为 **Counterfactual Oversight Coverage (COC)**，构建一个 failure-family controlled 的评测基准，提出 coverage-aware 的 judge 选择与路由方法，并用理论分析、机制分析和下游实验验证这一新原则。若该主张成立，它将把社区对 LLM judge / reward model 的评价目标，从“平均更准”改写为“对高风险失败模式覆盖更好”，从而影响未来的评测、对齐和自动监督实践。 ([OpenReview][1])

---

# 3. Abstract

大语言模型作为 judge、reward model 和自动监督器，已经从“辅助工具”变成了评测与后训练流程的基础设施。然而，现有研究对 judge 的评价仍主要依赖平均准确率、与人类的一致率或单一 benchmark 的综合分数。这个范式越来越显得不足：一方面，近期工作持续发现 judge 存在自偏好、相关家族偏好、风格偏置、以及可被简单 cue 误导的脆弱性；另一方面，奖励模型研究开始表明，平均 accuracy 并不是下游优化效果的充分统计量。本文提出一个新的研究问题：**在固定成本下，什么性质使一个自动监督系统真正可靠？**

我们提出的核心假设是：监督系统的关键瓶颈不在于单个 judge 的平均能力，而在于其对**反事实失败模式**（failure families）的覆盖率，以及多个 judge 在这些模式上的**漏判相关性**。基于此，我们提出 **Counterfactual Oversight Coverage (COC)** 这一新目标函数，将 judge 评估从 accuracy-centric 转向 coverage-centric。具体而言，我们将构建一个 failure-family controlled 的 pairwise judgment benchmark：从具有客观可验证标签的任务中出发，系统生成内容微扰、风格改写、伪推理包装、相关家族干扰、顺序扰动等反事实配对样本，以测量 judge 在不同失败家族上的 family-wise coverage 与 conditional miss correlation。随后，我们提出两类方法：其一是 **coverage-aware judge selection / routing**，在预算约束下优先调用能提供最大边际覆盖收益的 judge；其二是可选的 **family-aware judge adaptation**，通过 worst-family 风险重加权微调本地开源 judge，以降低高风险家族上的漏判率。

实验将围绕三个问题展开：第一，平均 accuracy 与 COC 是否会发生系统性排序翻转；第二，judge 相似性是否会显著降低新增 judge 的边际监督价值；第三，coverage-aware 的 judge 系统是否能在相同成本下提高 hardest cases 上的可靠性，并改善 reranking / reward modeling 等下游流程的稳健性。若这些预测成立，这项工作将提出一个新的监督原则：**可靠自动监督不是寻找最强裁判，而是构造不在同一处失明的裁判系统。** ([OpenReview][2])

---

# 4. Motivation and Problem Statement

## 4.1 现象：LLM judges 已经变成基础设施，但其失效方式仍被低估

自动 judge 不再只是一个便宜的替代评审器。JudgeLM、PandaLM 和 JudgeBench 代表了一个清晰趋势：LLM judges 被系统化地用于 open-ended evaluation、judge fine-tuning 与客观 judge benchmark；同时，RM-Bench 等工作把 reward model 拉进同一条“自动监督”链条中。换句话说，**评测、reranking、偏好建模、RLHF/RLVR，越来越共享同一种自动监督基础设施。** ([OpenReview][1])

但过去一年半的证据同样清楚：这套基础设施并不只是“有噪声”，而是存在**系统性、可结构化的失效模式**。已有研究表明 judge 会识别并偏好自己的生成结果，表现出自偏好和相关家族偏好；也会把文风、格式、冗长解释等表面信号误认为质量；甚至可以被单个 token 或“master key”式 cue 系统性欺骗。更重要的是，这些错误并非随机散落，而更像是**成簇出现的共同盲点**。 ([OpenReview][2])

## 4.2 张力：主流范式在优化 judge，但可能没有优化对的目标

当前主流补救路径主要有三类。
第一类是“训练更好的 judge”，例如 JudgeLM 一类的 SFT judge，或 JudgeLRM 一类强调 evaluative reasoning 的 judge。
第二类是“在必要时调用更强 judge”，例如不确定时把样本转发给昂贵但更强的 judge。
第三类是“构造更客观的 benchmark”，例如 JudgeBench、LiveBench、LiveCodeBench 和 RM-Bench。 ([OpenReview][1])

这些工作都重要，但它们大多默认：**更高的平均判断准确率，或更高的一致率，就是更好的监督器。** 这正是本 proposal 要挑战的地方。奖励模型方向的最新结果已经表明，仅凭 accuracy 无法充分预测一个 reward model 是否真能当“好老师”；两个准确率相近的 reward model，可能引导出非常不同的下游优化结果。由此得到的自然推论是：对于 judge 而言，**“平均分更高”也可能不是决定监督价值的正确目标函数。** ([OpenReview][3])

## 4.3 我们真正的问题

**研究问题：在固定监督预算下，什么性质使一个 judge 系统真正可靠？**

更具体地说，我们不问“哪个 judge 平均更准”，而问：

* 一个 judge 是否覆盖了关键失败模式，还是只在容易样本上表现好？
* 多个 judge 的新增价值来自哪里：更强能力，还是更低的共同盲点？
* 在相同成本下，弱但互补的 judge 组合，是否能优于强但同质的单 judge？
* 这种“覆盖率”视角，能否预测下游 reranking / reward modeling / alignment 的稳健性？

## 4.4 如果成功，会改变什么

如果本 proposal 成功，它将改变的不只是一个新 benchmark，而是社区对自动监督的**评价方式和设计原则**：

* 从 **accuracy-centric** 转向 **coverage-centric**；
* 从“找最强 judge”转向“找能覆盖不同失败模式的 judge system”；
* 从“平均更准”转向“高风险家族上更不盲”；
* 从把 benchmark 当终点，转向把 benchmark 当作识别监督机制的**实验仪器**。

这里需要明确一点：**如果这项工作只停留在“做了一个更全面的 judge benchmark”，novelty 不够强，最多是一篇扎实的 benchmark / empirical study。** 本 proposal 的核心不是 benchmark，而是一个新的监督目标函数与相应的机制主张；benchmark 只是检验这一主张的手段。

---

# 5. Core Hypothesis and Research Claims

## 主假设

### **H1. Reliable oversight depends more on failure-family coverage and miss correlation than on mean judge accuracy.**

* **Claim**
  在固定预算下，一个监督系统的可靠性主要由其对关键失败家族的覆盖率，以及不同 judge 在这些家族上的漏判相关性决定；平均 accuracy 只是一个不充分、常被 easy cases 主导的代理指标。
* **Intuition**
  如果 judge 的错误高度相关，那么即使每个 judge 单独都很强，组合后的新增监督价值仍然很小。
* **Testability**
  比较 judge 的 overall accuracy、COC、worst-family risk 与 downstream robustness；检验 ranking inversion 是否存在。

## 子假设 / 研究命题

### **H2. Judge similarity predicts diminishing marginal oversight gain.**

* **Claim**
  控制成本与平均准确率后，与当前 judge set 更相似的 judge，其加入后的 marginal COC gain 更低。
* **Intuition**
  相似模型更可能共享同样的 shortcut 与 blind spot。
* **Testability**
  用 error overlap / CAPA-style similarity / miss-correlation 预测新增 judge 的覆盖收益。

### **H3. Coverage-aware selection/routing outperforms strongest-single-judge and uncertainty-only routing on hard cases at matched cost.**

* **Claim**
  在相同推理成本下，coverage-aware 选择/路由比“最强单 judge”或“仅基于不确定性升级到强 judge”的策略在 hardest subsets 上更可靠。
* **Intuition**
  预算最该花在补洞，而不是在已有擅长区域继续加冗余。
* **Testability**
  以 Hard-Error Recall、worst-family miss rate、cost-normalized COC 进行 matched-cost 对比。

### **H4. Family-aware judge adaptation reduces worst-family failure without requiring large-scale retraining.**

* **Claim**
  在中等规模 LoRA / QLoRA 微调下，对高风险 family 做显式重加权或 group-DRO，可显著降低 worst-family 风险，而不必依赖大规模 pretraining。
* **Intuition**
  若失败是结构化的，定向训练应优先改善“共同盲点”，而非平均再抬一点分。
* **Testability**
  对比 average-risk training 与 family-aware training 的 family-wise risk 曲线。

### **H5. Oversight quality should predict downstream robustness better than accuracy.**

* **Claim**
  用高 COC 的 judge 系统做 reranking / reward labeling / preference filtering，应比用高 accuracy 但低 coverage 的 judge 更能提升下游模型的鲁棒性。
* **Intuition**
  如果监督器本身偏向 style、self-family 或伪推理，它会把这些偏差写进下游模型。
* **Testability**
  用不同监督器驱动相同的 reranking / DPO / RM pipeline，比较下游模型在 failure-family stress test 上的差异。

---

# 6. Why This Proposal is Novel

## 6.1 Closest prior work

### 类别 A：训练 judge、让 judge 可扩展

代表工作包括 PandaLM、JudgeLM、JudgeBench。它们建立了 LLM-as-a-judge 的早期范式：训练 judge、构造 judge benchmark、测人与 judge 的一致性或客观 correctness。 ([OpenReview][4])

### 类别 B：诊断 judge 的系统性偏差

代表工作包括 *LLM Evaluators Recognize and Favor Their Own Generations*、*Self-Preference Bias in LLM-as-a-Judge*、*Preference Leakage*、*Style Outweighs Substance*、*One Token to Fool LLM-as-a-Judge*。它们已经明确说明 judge 并不只是 noisy，而是会在某些结构化 shortcut 上系统犯错。 ([OpenReview][2])

### 类别 C：让 judge 更强，或重新思考 accuracy

代表工作包括 JudgeLRM、uncertainty-based routing，以及奖励模型方向的 *What Makes a Reward Model a Good Teacher?*、*Rethinking Reward Model Evaluation*、RM-Bench。它们分别提出：更强 reasoning judge 可能更好；不确定时调用强 judge 可能更省成本；accuracy 不是评价 reward quality 的充分标准。 ([OpenReview][5])

## 6.2 What they achieved

这些工作已经完成了三件重要事情：

* 证明了 LLM judge 可以系统化训练和部署。 ([OpenReview][1])
* 证明了 judge failure 不是个别案例，而是多种可复现偏差。 ([OpenReview][2])
* 证明了“只看 accuracy”在 reward model 甚至 judge 选择上可能不够。 ([OpenReview][3])

## 6.3 What is still missing

缺失的不是更多 bias case study，而是一个**统一原则**：

* 现有工作告诉我们 judge 有哪些 failure，但没有把这些 failure 统一成一个**可优化的监督目标函数**。
* 现有工作提升了单个 judge 的 reasoning 或做了 cost-aware routing，但没有回答：**为什么更强 judge 仍然可能在关键区域共同失明。**
* 现有 benchmark 更像“难题汇总”或“偏差目录”，还不是针对**failure-family coverage**设计的实验仪器。
* 现有 reward-model 研究已经指出 accuracy 不够，但还没把这个洞见系统迁移到 **LLM-as-a-judge / AI oversight** 的整体设计上。 ([OpenReview][6])

## 6.4 What is irreducibly new here

本 proposal 的不可替代贡献不是“更系统一些”，而是以下四者的组合：

1. **新问题定义**
   把 judge 评价从“谁平均更准”改写为“谁对关键失败模式覆盖更好”。

2. **新评测视角**
   引入 **failure-family controlled counterfactual evaluation**，把 judge failure 从散点案例提升为结构化分布。

3. **新机制主张 / 轻理论**
   提出并检验：**监督价值由 family-wise coverage 与 miss correlation 决定，而非只由 mean accuracy 决定。**

4. **新方法**
   提出 **coverage-aware judge selection / routing**，并进一步探索 **family-aware judge adaptation**。

一句话说：
**这不是再做一个 judge benchmark，而是重新定义“什么叫一个好的自动监督器”。**

---

# 7. Conceptual Framework

## 7.1 研究对象

我们研究的对象不是单个 judge，而是一个**监督系统**：

[
\mathcal{O} = (\mathcal{J}, \pi, A, B)
]

其中：

* (\mathcal{J})：候选 judge 集合
* (\pi)：路由策略，决定给定样本时调用哪些 judge
* (A)：聚合器，将多个 judge 的判断整合为最终 verdict
* (B)：预算约束（API cost、延迟、调用次数）

## 7.2 样本定义

每个 judgment instance 记为：

[
z_i = (x_i, y_i^{(1)}, y_i^{(2)}, g_i, f_i)
]

* (x_i)：任务输入 / prompt
* (y_i^{(1)}, y_i^{(2)})：两个候选回答
* (g_i)：金标准偏好标签
* (f_i \in \mathcal{F})：该样本所属的 failure family

这里的 (f_i) 不是任务类别，而是我们关心的**反事实失败家族**，例如：

* content-subtlety failure
* style-vs-substance failure
* reasoning-fluff / master-key failure
* self-/same-family relatedness failure
* position/order bias
* abstain/clarify-required failure

## 7.3 观测量、机制变量、干预变量、结果变量

### 研究对象

* 单个 judge (j)
* judge set (S \subseteq \mathcal{J})
* oversight system (\mathcal{O})

### 观测量

* judge 对样本 (i) 的判断 (d_{ij})
* per-family correctness
* judge disagreement
* judge cost / latency
* scout judge 输出与简单元特征

### 机制变量

* **Family-wise competence**
  [
  C_j(f)=\Pr(d_{ij}=g_i \mid f_i=f)
  ]
* **Conditional miss correlation**
  [
  \rho_{jk}(f)=\mathrm{Corr}(\mathbf{1}[d_{ij}\neq g_i],\mathbf{1}[d_{ik}\neq g_i]\mid f_i=f)
  ]
* **Marginal oversight gain**
  [
  \Delta(j\mid S)=\mathrm{COC}(S\cup{j})-\mathrm{COC}(S)
  ]

### 干预变量

* judge selection：选择哪些 judge 进入 (S)
* routing：对哪些样本调用哪些 judge
* family reweighting：训练时对高风险 family 加权
* aggregation：majority / calibrated vote / stacking

### 结果变量

* **Counterfactual Oversight Coverage (COC)**
* worst-family risk
* hard-error recall
* downstream reranking / RM robustness

## 7.4 核心定义：Counterfactual Oversight Coverage

对 judge 系统 (S) 定义：

[
\mathrm{COC}(S)=\sum_{f\in\mathcal{F}} w_f \cdot \left(1-\mathrm{Err}_A(S,f)\right)
]

其中：

* (w_f)：failure family 权重，可均匀，也可风险加权
* (\mathrm{Err}_A(S,f))：聚合器 (A) 在 family (f) 上的错误率

直观上，COC 衡量的是：**在重要失败家族上，这个监督系统覆盖得有多好。**

## 7.5 关键机制图

可以把本 proposal 理解为以下因果链：

**failure family (f)**
(\rightarrow) 影响候选回答中的表面 cue 与真实质量差异
(\rightarrow) 触发 judge 的 shortcut / blind spot
(\rightarrow) 通过 judge similarity 放大共同漏判
(\rightarrow) 决定单 judge 与 judge set 的真实监督价值

我们的干预是：

* 改变 judge 选择与组合方式；
* 改变训练目标对 family 的权重；
* 观察 COC、worst-family risk 和 downstream robustness 是否改善。

---

# 8. Research Plan

## 8.1 Data / task / benchmark

## 8.1.1 数据来源

本项目不从纯主观开放域偏好数据起步，而优先使用**客观或半客观可验证任务**，以避免把“监督失败”与“金标噪声”混在一起。第一阶段使用四类来源：

1. **LiveBench**
   用其 reasoning / coding / instruction-following 中可客观验证的子集。LiveBench 的优势是污染受限、题目更新、并且强调 objective scoring。 ([OpenReview][7])

2. **LiveCodeBench**
   用其代码题与 execution-based verification 子集。代码任务非常适合构造“风格不变但语义错一行”的细微反事实对。 ([OpenReview][8])

3. **JudgeBench**
   用其客观判别更困难的 response pairs 作为硬样本来源，尤其适合评估 reasoning / math / code judge。 ([OpenReview][6])

4. **RM-Bench**
   用其“subtle content differences + style interference”的思路作为 family construction 的重要参考。 ([OpenReview][9])

## 8.1.2 新 benchmark：COC-Bench（工作名）

本 proposal 会新构建一个 **Counterfactual Oversight Coverage Benchmark (COC-Bench)**，但需要明确：

* **它不是核心贡献本身；**
* 它是检验“coverage 而非 accuracy 才是监督关键量”这一理论主张的实验工具。

### COC-Bench 的构建步骤

1. 选取带客观 verifier 的源任务。
2. 生成多样候选回答：来自异质模型、不同 decoding、以及程序化 perturbation。
3. 对每个回答对进行反事实编辑，构造成 failure-family controlled pairs。
4. 用 objective verifier + 小规模人工审查确认标签。
5. 按 family、domain、difficulty 平衡划分 dev / test。

### 初版 failure families

* **F1: Substance Flip**
  内容细微错误，风格基本保持不变。
* **F2: Style Flip**
  内容等价，风格改为更冗长、更 polished、更像“高级答案”。
* **F3: Reasoning-Fluff / Master-Key**
  在错误答案前加入具有“推理感”的包装。
* **F4: Relatedness Bias**
  控制候选答案来源于 judge 同家族/相关家族模型。
* **F5: Position / Order Bias**
  同一 pair 交换 A/B 次序。
* **F6: Abstain / Clarify Required**
  正确动作是拒答、tie 或请求澄清，而不是硬判优劣。

### 数据规模

* dev：8k–12k pairs
* test：4k–6k pairs
* human audit：500–1,000 pairs

### 为什么这样设计

* objective tasks 让我们更有能力把“judge 的错”与“标签本身的争议”区分开；
* failure-family 构造使我们能研究**同一类机制性错误**，而不是散乱的单例；
* 这为后续 selection / routing / adaptation 提供稳定监督信号。

## 8.2 Method

本 proposal 的方法由三部分组成：

### Part A：测量

对每个 judge (j) 估计：

* family-wise coverage (C_j(f))
* miss correlation (\rho_{jk}(f))
* overall accuracy
* cost / latency

### Part B：coverage-aware judge selection

目标是在预算 (B) 下选择 judge set (S)，最大化：

[
\max_{S \subseteq \mathcal{J}, \ \mathrm{cost}(S)\le B} \mathrm{COC}(S)
]

在 per-example coverage 近似下，这个问题可视为**带权预算覆盖问题**。因此我们使用 greedy selection：

1. 在 dev 上跑完所有 judge；
2. 记录每个 judge 在不同 family / sample 上是否纠正已有系统的错误；
3. 每一步加入单位成本带来最大 marginal coverage gain 的 judge。

### Part C：coverage-aware routing

selection 决定“系统里有哪些 judge”；routing 决定“一个样本来了该问谁”。

我们训练一个轻量 router (r_\phi(z))，预测：

* 当前样本属于哪些 failure families 的概率；
* 或者每个 judge 在该样本上的 expected gain / cost。

输入特征 (z) 包括：

* 任务类型 / 来源 benchmark
* 回答长度比
* lexical overlap
* 是否存在语义等价迹象
* scout judge 的 margin / disagreement
* 是否含 reasoning preamble 等 cue

最终对每个样本按 expected marginal gain/cost 排序，依次调用 top-k judges，直到收益低于阈值或预算耗尽。

### Part D（可选强化）：family-aware judge adaptation

对本地开源 judge 做小规模 LoRA/QLoRA，优化 worst-family 风险而非平均 risk：

[
L(\theta)=\sum_{f\in\mathcal{F}} \lambda_f \cdot \mathbb{E}*{i\in D_f}[\ell*\text{pair}(i;\theta)] + \beta \mathrm{KL}(\theta,\theta_0)
]

其中：

* (\lambda_f) 可为 group-DRO 风格的动态权重；
* (\ell_\text{pair}) 为 pairwise preference loss；
* (\beta) 控制偏离原 judge 的程度。

### 伪代码级流程

```text
Input:
  Judge pool J
  Dev set D={(x, y1, y2, g, f)}
  Budget B

Offline:
  1. Evaluate all judges on D
  2. Estimate C_j(f), rho_jk(f), cost_j
  3. Greedily select judge subset S maximizing marginal COC gain / cost
  4. Train router r_phi using cheap meta-features + scout outputs
  5. (Optional) Fine-tune local judges with family-aware objective

Inference:
  1. Query scout judge(s)
  2. Build routing feature z
  3. Score each candidate judge by expected gain / cost
  4. Query top-k judges under budget
  5. Aggregate verdicts with calibrated vote / stacking
  6. Output final verdict + uncertainty
```

### 复杂度与成本

* 离线评估：(O(N|J|))
* greedy selection：(O(BN|J|))
* online routing：额外开销很小，主要成本在所调用 judge 数量
* 训练成本主要集中在可选的本地 judge LoRA

## 8.3 Theoretical / mechanistic analysis

本 proposal 的理论目标不是做重型 theorem paper，而是给出**足够强、可检验、服务主张的轻理论**。

### 命题 1：accuracy 不是 COC 的充分统计量

应存在两个 judge (j_1,j_2)，使得：

[
\mathrm{Acc}(j_1)\approx \mathrm{Acc}(j_2)
\quad \text{但} \quad
\mathrm{COC}(j_1)\ll \mathrm{COC}(j_2)
]

原因是：错误可能集中在不同 family 上。

### 命题 2：高 miss correlation 会压缩新增 judge 的边际收益

若 judge (j) 与当前系统 (S) 在关键 family 上有高 (\rho_{j,S}(f))，则：

[
\Delta(j\mid S)
]

应显著变小，即使 (j) 本身平均 accuracy 很高。

### 命题 3：风险敏感的选择目标优于平均风险目标

如果 rare-but-high-impact family 存在，则最大化平均 accuracy 的系统可在部署上明显劣于最大化 COC 或 worst-family coverage 的系统。

### 机制分析

* error overlap heatmap
* family-wise confusion matrix
* judge similarity vs marginal gain 散点图
* router 选择了哪些 judge、为什么选择

这些分析不是装饰，而是用于判断：**收益到底来自更强能力，还是来自更低的共同盲点。**

## 8.4 Expected empirical signatures

如果核心 hypothesis 成立，实验上应看到以下 signature：

* judge 的 overall accuracy 与 COC 只有中等相关，而不是几乎一致；
* judge similarity 与 marginal gain 显著负相关；
* coverage-aware 组合在 hardest subsets 上有更大收益，而平均 accuracy 提升未必最大；
* family-aware adaptation 主要改善 worst-family risk；
* 用高 COC 监督器驱动的 reranking / RM pipeline，在 style/leakage/master-key stress test 上更稳健。

---

# 9. Experimental Design

## 9.1 Models

## 主实验模型

* **Judge pool（异质）**

  * 4–6 个本地开源 judge / assistant / reward-style models（7B–32B）
  * 2–4 个 API judges
  * 至少包含：

    * 一个 **JudgeLM-style** 可扩展 judge
    * 一个 **JudgeLRM-style** reasoning judge
    * 一个小型 reward-model judge
    * 一个普通通用 assistant 作为非专门 judge 对照
      这样能保证 judge family 的异质性，而不是只比较同质强模型。JudgeLM / PandaLM / JudgeLRM 对应的 judge 范式已被前人证明具有代表性。 ([OpenReview][1])

## 辅助模型

* 用于生成 counterfactual pairs 的 heterogeneous generator models
* 用于语义等价检测 / style rewrite 的 API 模型
* 可选 7B policy model，用于 downstream reranking / DPO smoke test

## Judge / evaluator 选择理由

* 我们需要的不是单一最强模型，而是**跨家族、跨训练风格、跨 judge 范式**的监督池；
* judge pool 同时包含 prompted judges、trained judges、reasoning judges 与 RM-style evaluators，才能真正测量 coverage 与 miss correlation。

## 9.2 Baselines

### B1. Best single judge by overall accuracy

* **为什么强**：这是当前最自然、最主流的选择策略。
* **哪个最难打败**：它通常会在 overall accuracy 上最强，是最必须击败的 baseline。
* **为什么必须比较**：如果连它都打不过，coverage 主张就站不住。

### B2. Uniform majority vote / weighted vote at matched cost

* **为什么强**：检验收益是否只是“多问几个 judge”带来的 ensemble 效应。
* **为什么必须比较**：用来排除“coverage-aware 其实只是普通投票”的解释。

### B3. Similarity-only diversity selection

* **为什么强**：它直接使用 model similarity / error diversity，但不显式考虑 failure-family coverage。
* **为什么必须比较**：用来验证“coverage-aware 比单纯 diversity-aware 更强”。

### B4. Uncertainty-based escalation

* **为什么强**：这是近期很自然的成本优化方案：不确定时再叫强 judge。 ([OpenReview][10])
* **为什么必须比较**：若 coverage-aware 只等价于“不确定时升级”，理论价值就会变弱。

### B5. Strong reasoning judge / JudgeLRM-style judge

* **为什么强**：代表“更会 reasoning 的 judge 就更可靠”这一主流改进路径。 ([OpenReview][5])
* **为什么必须比较**：用来检验“更强单 judge”是否真优于“互补 judge system”。

### B6. Objective verifier oracle（上界，不作主基线）

* 仅用于 objective subsets 上估计 ceiling，不用于主要比较。

## 9.3 Main experiments

## E1. COC-Bench 构造有效性验证

* **目的**：验证 failure-family 标签与反事实构造是否可信。
* **设置**：对 500–1,000 个样本做人审；检查 style rewrite 是否保持语义、substance flip 是否只改内容、reasoning-fluff 是否未改变真实 correctness。
* **变量**：family 类型、构造来源、自动 verifier 与人工判断。
* **指标**：family fidelity、人审一致率、标签冲突率。
* **预期现象**：大多数 family 的构造应具有高保真。
* **如果结果相反**：benchmark 的有效性受损，需缩减 family 集合并加强人工校验。

## E2. Accuracy vs COC ranking inversion

* **目的**：验证平均 accuracy 不是足够指标。
* **设置**：对 judge pool 中所有 judge 测量 overall accuracy、COC、worst-family risk。
* **变量**：judge identity、family 权重设置。
* **指标**：rank correlation、ranking inversion count。
* **预期现象**：多个 judge 在 overall accuracy 上相近，但在 COC 上差异显著。
* **如果结果相反**：说明本 proposal 的核心张力较弱，需转向高风险子集的 risk-sensitive framing。

## E3. Similarity / miss-correlation vs marginal gain

* **目的**：验证共同盲点机制。
* **设置**：从当前 judge set 中逐个加入新 judge，测其 marginal COC gain。
* **变量**：judge similarity、average accuracy、cost。
* **指标**：partial correlation / regression coefficient。
* **预期现象**：相似性越高，新增 gain 越低。
* **如果结果相反**：说明“相似性导致冗余”并非主因，可能需要改用更细粒度 family-specific similarity。

## E4. Coverage-aware selection vs baselines at matched cost

* **目的**：验证新目标函数的实际价值。
* **设置**：在相同 API/generation 成本下比较 B1–B5。
* **变量**：预算、judge pool 规模、aggregation 方式。
* **指标**：COC@Budget、Hard-Error Recall、worst-family miss、latency。
* **预期现象**：coverage-aware 在 hard cases 上显著更好。
* **如果结果相反**：说明 selection 目标函数需修正，或 judge pool 异质性不足。

## E5. Coverage-aware routing

* **目的**：验证路由层而非只靠离线 selection 的收益。
* **设置**：用 scout judge + meta-features 预测 per-example routing。
* **变量**：router 输入特征、调用阈值、top-k。
* **指标**：cost-normalized COC、AUC of useful escalation。
* **预期现象**：比 uncertainty-only routing 更能覆盖 rare families。
* **如果结果相反**：说明 per-example family 识别不充分，可退回只做 offline selection。

## E6. Family-aware judge adaptation

* **目的**：验证不需大训练也能针对共同盲点改进本地 judge。
* **设置**：对 7B/8B judge 做 LoRA，比较 average-risk 与 family-aware training。
* **变量**：重加权方式、(\lambda_f)、训练数据组成。
* **指标**：worst-family risk、COC、overall accuracy。
* **预期现象**：worst-family risk 明显下降，overall accuracy 不显著恶化。
* **如果结果相反**：说明 family-aware training 存在 tradeoff，可能只保留为附加实验。

## E7. Downstream reranking / reward-labeling robustness

* **目的**：证明这不是“只在 judge benchmark 上有效”的现象。
* **设置**：用不同监督器给同一批候选答案 rerank 或做小规模 preference labeling，再训练/选择同一个 7B policy。
* **变量**：监督器类型、采样温度、训练步数。
* **指标**：下游模型在 family stress test 上的鲁棒性、风格偏差率、same-family artifact 依赖度。
* **预期现象**：高 COC 监督器对应更稳健的下游结果。
* **如果结果相反**：说明 benchmark 与 training bottleneck 脱钩，论文需更偏 evaluation-principle。

## E8. Held-out family / held-out domain transfer

* **目的**：检验是不是只记住了某些 family。
* **设置**：在部分 family 上开发，在未见 family 或未见 domain 上测试。
* **变量**：held-out family、held-out benchmark。
* **指标**：generalization gap。
* **预期现象**：coverage-aware 至少部分迁移。
* **如果结果相反**：需要把主张缩窄为“risk-sensitive evaluation on known failure families”。

## 9.4 Ablations

关键 ablation 维度：

* 去掉某一 family 后的性能变化
* family 权重：uniform vs risk-weighted
* router 特征：仅元特征 vs 加 scout judge vs 加 family metadata
* 聚合器：majority / weighted vote / calibrated stacking
* judge pool 同质性：高同质 vs 高异质
* training objective：ERM vs family-reweighted vs group-DRO
* only-objective data vs 加入小量 subjective data

## 9.5 Robustness / stress test

至少三类：

1. **Prompt paraphrase / surface perturbation**

   * 检验 coverage 不是 prompt-specific trick。

2. **Pool homogeneity stress test**

   * 故意只选同家族 judge，测 marginal gain 是否塌缩。

3. **Adversarial cue injection**

   * 注入 reasoning fluff、provenance cue、order swap 等，测 system 是否稳健。

4. **Domain shift**

   * 从 math/code 转到 instruction / semi-objective tasks。

## 9.6 Statistical validity

* trainable components：**3 seeds**
* judge ranking / routing结果：**paired bootstrap 95% CI**
* baseline 比较：**paired permutation test**
* 明确 dev / test 分离；所有 model selection 仅在 dev 完成
* 预先固定主要指标：COC、worst-family miss、HER、cost-normalized COC
* 所有 judge 原始 verdict 全部保存，避免 cherry-picking

---

# 10. Falsifiable Predictions

## Prediction 1

* **Prediction**
  存在多个 judge 对，其 overall accuracy 接近，但 COC 与 worst-family risk 显著不同。
* **How to test**
  在统一 test set 上同时计算 judge 的 overall accuracy、COC、worst-family miss。
* **What failure would imply**
  若排序几乎一致，则“accuracy 不充分”这一主张在当前 setting 下不强。
* **How the theory would be revised**
  将理论缩窄为：coverage 主要在高风险子集上有额外价值，而非全局替代 accuracy。

## Prediction 2

* **Prediction**
  judge 与当前系统越相似，其 marginal coverage gain 越低，即使平均 accuracy 更高。
* **How to test**
  对每个候选 judge 回归 marginal COC gain，对 similarity、accuracy、cost 做联合控制。
* **What failure would imply**
  若无显著负相关，说明“共同盲点”可能不是主要机制。
* **How the theory would be revised**
  改为更细粒度地度量 family-specific correlation，而不是全局 similarity。

## Prediction 3

* **Prediction**
  在 matched cost 下，coverage-aware selection 会优于 strongest-single-judge，尤其在 HER 与 worst-family coverage 上。
* **How to test**
  对不同预算进行 matched-cost 实验，对比 B1–B5。
* **What failure would imply**
  若 strongest-single-judge 总体和 hardest cases 都更好，则“互补性胜过单体强度”不成立。
* **How the theory would be revised**
  将主张改为：coverage-aware 仅在特定 failure families 或特定 pool heterogeneity 下成立。

## Prediction 4

* **Prediction**
  uncertainty-only routing 会遗漏某些低不确定但高偏置的 failure family；coverage-aware routing 会更稳。
* **How to test**
  比较 uncertainty-routing 与 coverage-routing 在各 family 上的 recall。
* **What failure would imply**
  若两者几乎等价，说明 family-aware 特征没有带来额外信息。
* **How the theory would be revised**
  将 coverage-aware routing 降级为更简单的 uncertainty-augmented routing。

## Prediction 5

* **Prediction**
  family-aware adaptation 可以在小规模 LoRA 下显著降低 worst-family risk，而无需大规模预训练。
* **How to test**
  比较 ERM 与 family-aware 微调在 worst-family risk 与 overall accuracy 上的 tradeoff。
* **What failure would imply**
  若 worst-family 改善必须以明显牺牲 overall accuracy 为代价，说明 failure 可能并非可局部修正。
* **How the theory would be revised**
  将 adaptation 从主贡献降为附加实验，主线保留在 selection / evaluation principle。

## Prediction 6

* **Prediction**
  用高 COC 监督器生成的标签或 reranking 决策，会带来更稳健的下游模型。
* **How to test**
  用不同监督器驱动同一 reranking / DPO smoke test，比对下游 stress test 结果。
* **What failure would imply**
  若下游差异很小，说明静态 judge metric 与动态训练效果存在脱钩。
* **How the theory would be revised**
  将论文定位收缩为“evaluation and oversight principle”，而不强推对齐收益。

---

# 11. Risks, Failure Modes, and Plan B/C

## 11.1 理论风险

### 风险

COC 可能与 accuracy 高度重合，无法形成真正的新目标函数。

### Plan B

把主张收缩为：**coverage 是 high-risk evaluation 的必要补充**，而不是全局替代 accuracy。

### Plan C

把论文重心转向“accuracy 为何失真”的理论与实证分析。

## 11.2 实验风险

### 风险

failure family 构造不够干净，style 与 content disentanglement 不充分。

### Plan B

保留最干净的 3–4 个 family，删去噪声高的 subjective families。

### Plan C

把高噪声 family 放入 appendix，主论文只做 objective / semi-objective setting。

## 11.3 Benchmark 风险

### 风险

若 benchmark 过度依赖 objective tasks，reviewer 可能质疑其外部有效性。

### Plan B

增加小规模 semi-objective 子集，做外推验证。

### Plan C

明确论文定位：先建立原则，再讨论开放域推广，不强做“通吃一切”的表述。

## 11.4 识别 / 解释风险

### 风险

judge similarity 与 marginal gain 的关系可能被隐藏变量混淆，例如模型规模、训练数据谱系、任务专长。

### Plan B

使用 matched-accuracy、matched-cost 的 controlled comparisons。

### Plan C

把机制结论写成条件性：在给定 family distribution 与 judge pool 条件下成立。

## 11.5 工程风险

### 风险

API judge 成本高、延迟大、缓存复杂。

### Plan B

先用离线 judge 输出做 selection 研究，再加 routing。

### Plan C

若 API 不稳定，将 coverage-aware routing 降为模拟实验，本地 judge adaptation 前置。

## 11.6 诚实判断：哪些部分应降级

* **最核心**：新问题定义 + COC + selection/routing + falsifiable analysis
* **次核心**：family-aware judge adaptation
* **可降级到 appendix**：主观开放域扩展、复杂下游 DPO 全量实验、太多 family 的泛化分析

如果 adaptation 与下游实验收益不稳定，主论文仍可以是一篇强的 **evaluation-principle + mechanism + method** 论文；但若只剩 benchmark，而没有 selection / theory / downstream link，这篇工作会更像 benchmark track 或 strong empirical study，而不是最强的 main-track narrative。

---

# 12. Feasibility Under Compute Constraints

## 12.1 资源假设

* 2 台机器
* 每台 2×8×80GB A800
* 总计 16×80GB A800
* API 预算充足

## 12.2 模型规模与训练策略

* judge pool 主体：7B–32B
* 本地训练只做 **LoRA / QLoRA**
* 不做大规模 pretraining
* 下游 policy 仅做 7B 级 smoke test 或 reranking

## 12.3 主要成本来源

### A. 数据构造与 judge 批量评测

* 主要消耗 API 与离线 batched inference
* GPU 压力不大
* 估计：10–15 个 judge × 12k–18k pairs，可通过缓存与并行分批完成

### B. 本地 judge adaptation

* 7B/8B LoRA：单次 8 GPU × 12–24 小时
* 3 seeds + 数个配置：约 25–40 GPU-days

### C. Downstream smoke test

* 7B reranking / DPO 小规模实验：约 15–25 GPU-days

### D. 全量分析与 ablation

* 额外 20–40 GPU-days

## 12.4 总体估计

* **总 GPU-days：约 70–110**
* 这是中等规模项目，显著低于需要数千卡周的大训练路线
* 主要依赖：

  * API judge 调用
  * 中等规模本地微调
  * 大量离线分析与缓存

## 12.5 并行策略

* **机器 A**：本地 judge 训练、离线 open judge 批量推理
* **机器 B**：router 训练、数据构造、downstream smoke tests
* API 调用走异步队列，所有 judge verdict 强缓存

**结论**：在给定算力约束下，这个 proposal 是明确可执行的；其主要难点不在算力，而在实验设计与评价逻辑是否干净。

---

# 13. Reproducibility and Engineering Plan

## 13.1 配置管理

* 使用统一配置系统（如 Hydra/YAML）
* 每个实验保存：

  * judge pool
  * prompt template
  * family set
  * weights (w_f)
  * budget
  * router config
  * seed
  * git hash

## 13.2 实验记录

* 对所有 judge verdict 做缓存
* 保存每个样本：

  * 来源任务
  * family 标签
  * 构造脚本版本
  * 自动 verifier 输出
  * 人工审计状态

## 13.3 数据版本

* `raw/`：源 benchmark 样本
* `transformed/`：反事实构造结果
* `audited/`：人工确认后的 gold subset
* 每个版本有 manifest 和 checksum

## 13.4 随机种子

* 所有 trainable modules 固定 3 seeds
* 数据划分、抽样、LoRA 初始化单独记录

## 13.5 checkpoint 策略

* judge adaptation 每个 epoch 存 checkpoint
* 根据 dev COC / worst-family risk 早停
* 不以 overall accuracy 单独做 early stopping

## 13.6 评测脚本

* 独立脚本计算：

  * COC
  * family-wise coverage
  * worst-family risk
  * HER
  * cost-normalized metrics
* 脚本与原始 judge 输出分离，避免后处理作弊

## 13.7 artifact 发布建议

建议最终公开：

* COC-Bench 构造脚本
* family 定义与标签标准
* judge verdict cache（若许可证允许）
* selection / routing / analysis 代码
* 微调配置与评测脚本
* human audit subset

---

# 14. Timeline and Milestones

## 第 1–2 周：最小闭环

目标：判断这个方向是否值得全推。

* 选 2 个 domain：math + code
* 只做 3 个 family：Substance / Style / Reasoning-Fluff
* 跑 6–8 个 judge
* 完成：

  * COC 指标实现
  * judge accuracy vs COC 散点图
  * strongest-single vs simple coverage-aware selection pilot

### 2–3 周 go/no-go 信号

继续推进需要满足至少两条：

1. 出现明显 ranking inversion（accuracy vs COC）
2. 相同成本下，coverage-aware 在 HER 上优于 strongest-single
3. judge similarity 与 marginal gain 有清晰负相关

## 第 3–5 周：扩充 benchmark 与 selection

* 补充 same-family / order bias families
* 做 500+ 样本人工审查
* 完成正式 selection 基线比较
* 固定主指标与主图表草稿

## 第 6–7 周：routing

* 训练轻量 router
* 完成 uncertainty-routing vs coverage-routing 对比
* 做 budget sweep

## 第 8–9 周：family-aware adaptation

* 对 7B/8B 本地 judge 做 LoRA
* 完成 ERM vs family-aware 对比
* 若收益不稳定，降级为附加实验

## 第 10 周：downstream smoke test

* 做 reranking 或小规模 DPO
* 检查监督器质量是否外推到下游

## 第 11–12 周：稳健性 + 写作

* held-out family/domain
* bootstrap / significance
* failure cases 与 rebuttal-ready analysis
* 成稿

---

# 15. Paper Framing

## 15.1 Best-paper style one-sentence pitch

**The problem with AI oversight is not that judges are weak, but that strong judges often miss the same things; this paper shows that oversight should be optimized for failure-family coverage, not average judge accuracy.**

## 15.2 Contribution bullets

* 提出 **Counterfactual Oversight Coverage (COC)**，把自动监督从 accuracy-centric 重定义为 coverage-centric。
* 构造 **failure-family controlled** 的 counterfactual judge benchmark，用于测量 system blind spots，而非只测平均能力。
* 给出一个机制主张：**监督价值由 family-wise coverage 与 miss correlation 决定**，并用理论与实验双重支持。
* 提出 **coverage-aware judge selection / routing**，在相同成本下提升 hardest cases 上的监督可靠性。
* 证明监督器的 coverage 质量比平均 accuracy 更能预测下游 reranking / reward-labeling 的稳健性。
* 给出一个对社区有方法论意义的结论：**自动监督应优先优化“不要在同一处一起犯错”。**

## 15.3 Figure plan

### Figure 1

**同样 accuracy，不同 coverage 的两个 judge**

* 目的：一图讲清 thesis
* 展示：两个 judge 的 overall accuracy 相近，但 family-wise risk 完全不同

### Figure 2

**COC-Bench 的 failure-family 构造示意**

* 展示各 family 的反事实构造方式
* 目的是说明 benchmark 不是杂乱样本堆砌

### Figure 3

**overall accuracy vs COC / HER 散点图**

* 证明 accuracy 不是充分指标

### Figure 4

**judge similarity vs marginal coverage gain**

* 支撑共同盲点机制

### Figure 5

**matched-cost baseline comparison**

* strongest-single / majority / uncertainty-routing / coverage-routing
* 展示成本—可靠性 tradeoff

### Figure 6

**downstream robustness transfer**

* 不同监督器驱动的 reranking / DPO 在 family stress test 上的差异

## 15.4 Related work organization

建议 related work 按问题链组织，而不是按年份列举：

1. **LLM-as-a-Judge as scalable oversight infrastructure**
   PandaLM、JudgeLM、JudgeBench、LiveBench、LiveCodeBench

2. **Systematic judge failures and shortcut biases**
   self-recognition、自偏好、preference leakage、style bias、master-key attacks

3. **Improving judges: stronger reasoning, routing, and RM evaluation**
   JudgeLRM、uncertainty-based routing、RM-Bench、Good Teacher、Rethinking RM Evaluation

4. **Risk-sensitive and group-robust evaluation**
   作为本文 coverage-aware 视角的概念桥梁

---

这份 proposal 的最强版本，不是“我们做了一个新 benchmark”，而是：**我们提出并验证了一个新的自动监督原则。**
benchmark、router、adaptation，都是围绕这个原则服务的。

[1]: https://openreview.net/forum?id=87YOFayjcG "https://openreview.net/forum?id=87YOFayjcG"
[2]: https://openreview.net/forum?id=4NJBV6Wp0h "https://openreview.net/forum?id=4NJBV6Wp0h"
[3]: https://openreview.net/forum?id=7pufO0SJAC "https://openreview.net/forum?id=7pufO0SJAC"
[4]: https://openreview.net/forum?id=5Nn2BLV7SB "https://openreview.net/forum?id=5Nn2BLV7SB"
[5]: https://openreview.net/forum?id=7JbWlwNltD "https://openreview.net/forum?id=7JbWlwNltD"
[6]: https://openreview.net/forum?id=G0dksFayVq "https://openreview.net/forum?id=G0dksFayVq"
[7]: https://openreview.net/forum?id=sKYHBTAxVa "https://openreview.net/forum?id=sKYHBTAxVa"
[8]: https://openreview.net/forum?id=chfJJYC3iL "https://openreview.net/forum?id=chfJJYC3iL"
[9]: https://openreview.net/forum?id=QEHrmQPBdd "https://openreview.net/forum?id=QEHrmQPBdd"
[10]: https://openreview.net/forum?id=SkdhLeuq8P&referrer=%5Bthe+profile+of+Qingru+Zhang%5D%28%2Fprofile%3Fid%3D~Qingru_Zhang2%29 "https://openreview.net/forum?id=SkdhLeuq8P&referrer=%5Bthe+profile+of+Qingru+Zhang%5D%28%2Fprofile%3Fid%3D~Qingru_Zhang2%29"
