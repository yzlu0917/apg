# 1. Title

**主标题**
**Only Causal Steps Should Be Rewarded: Matched-Counterfactual Process Supervision for Faithful Reasoning**

**备选标题**

1. **Reward What Matters: Causal Credit Assignment for Reasoning Traces**
2. **From Plausible to Causal: Process Supervision for Faithful and Efficient Reasoning**
3. **Counterfactual Process Credit for Language Model Reasoning**

---

# 2. One-Paragraph Thesis Summary

近两年的 reasoning post-training 处在一个尚未被正面解决的张力里：一方面，step-level / process supervision、process verifier 和 dense reward 的确能提升推理性能；另一方面，越来越多工作表明显式 CoT / thinking draft 往往并不 faithful，而 equal-budget 的 NoThinking 与大 (k) 分析又提示，许多所谓“reasoning gain”可能主要来自更好的采样分布，而不是模型真正学会了新的推理过程。这个 proposal 的核心主张是：**问题不在于我们是否应该奖励中间过程，而在于我们一直在奖励错误的过程对象。** 我们提出 **CaPS**：把“好推理步骤”定义为在固定预算、固定 rollout policy 下，**相对于匹配的反事实替代步骤**，能够提升未来 verifier success 的步骤。方法上，我们将构造 delete / paraphrase / distractor 三类 matched interventions，训练一个 **Causal Process Verifier** 预测步骤的反事实边际贡献，再用 **Causal-DPO** 在可验证推理任务上做离线 post-training，并在 equal-cost 协议下与 outcome-only、PAV/PRIME、faithfulness-only 和 NoThinking 基线对比。若该主张成立，它将把社区对 reasoning 的训练原则从“奖励看起来合理的过程”改写为“奖励对正确性有因果贡献的过程”，并同时重塑 reasoning 的评测逻辑。 ([OpenReview][1])

---

# 3. Abstract

近期大语言模型的推理训练越来越依赖 step-level verifier、process reward 与长链显式思考；但与此同时，faithfulness 研究表明，中间 reasoning trace 往往只是在文本上“像推理”，并不一定真正驱动最终答案，而 equal-budget 的对照结果进一步说明，显式 thinking 的收益可能部分来自更优的搜索与采样，而非更好的过程本身。基于这一张力，本 proposal 提出一个更根本的问题：**究竟什么样的中间过程值得被奖励？** 我们的核心假设是，当前方法过度奖励了“局部合理”或“看似进展”的步骤，而真正应被优化的对象应是步骤对未来成功概率的**匹配反事实边际贡献**。为此，我们提出 CaPS：在固定 rollout policy 与预算约束下，通过 delete、paraphrase 和 distractor 三类匹配干预估计步骤的 counterfactual credit，训练一个 Causal Process Verifier，并结合 Causal-DPO 对 7B–8B 级开源模型进行中等规模 post-training。实验上，我们将以 Reasoning Gym 为主训练与主评测底座，以 CRUXEval 和固定快照的 LiveCodeBench 作为外部泛化评测，重点检验四类证据：equal-cost 性能、faithfulness 指标、sample efficiency，以及高信用步骤的机制性影响。若假设成立，该工作将把 process supervision 从“奖励 plausible reasoning”推进到“奖励 causally useful reasoning”，并为 reasoning post-training 提供一个更可解释、可证伪、可复现的新原则。 ([OpenReview][1])

---

# 4. Motivation and Problem Statement

## 4.1 当前领域中最关键的现象或张力是什么

当前 reasoning 研究同时出现了三条互相拉扯的证据链。
第一条证据链来自 process supervision：从 Let’s Verify 到 PAV，再到 PRIME，社区已经看到 step-level / dense process feedback 能帮助推理训练和测试时搜索。第二条证据链来自 faithfulness：thinking draft 和 CoT 的反事实研究表明，很多中间步骤并不稳定地支撑后续推理和最终答案；FRIT、CST 这类方法进一步说明，faithfulness 需要被主动训练，而不能默认存在。第三条证据链来自反例与批判：NoThinking、large-(k) pass@(!k) 分析，以及 process-vs-outcome 的理论工作都提示，显式 reasoning 与 RLVR 的收益，常常可能是**更好的分布重加权或搜索效率**，而非本体性的 reasoning 改善。 ([OpenReview][1])

## 4.2 主流研究范式哪里不够

主流方法默认了一个过强的前提：只要一个步骤在局部上看起来正确，或能让一个 verifier 给出更高分，它就值得被奖励。这个前提现在已经不可靠。它混淆了至少三种不同的东西：

* **表面合理性**：这句话看起来像正确推理。
* **局部进展代理**：这一步让某个 progress proxy 升高。
* **反事实因果贡献**：如果把这一步替换、删去或换成一个表面相似但无用的步骤，最终成功率会下降。

前两者可以帮助优化；但只有第三者真正回答了“模型到底是不是靠这一步想对了”。

## 4.3 我们真正想问的研究问题是什么

本 proposal 要问的不是“如何再做一个更强的 PRM”，而是：

**在 reasoning post-training 中，应该如何定义并学习“值得被奖励的过程”？**

更具体地说，我们研究的是：

1. 能否把步骤质量定义为其在固定预算下对未来成功概率的**匹配反事实边际贡献**？
2. 用这种定义训练出来的模型，是否会同时提高

   * equal-cost reasoning performance，
   * process faithfulness，
   * sample efficiency，
   * 以及对高信用步骤的真实依赖？
3. 这种收益是否只在真正需要多步依赖的任务上成立，而不会在浅层任务上虚假泛化？

## 4.4 这项工作如果成功，会改变什么

如果该项目成功，它改变的不会只是一个训练 recipe，而是四个层面的默认设定：

* **训练原则**：从奖励“看起来合理的过程”转向奖励“对成功有因果贡献的过程”。
* **研究问题定义**：从“如何生成更长、更漂亮的 reasoning trace”转向“哪些 trace steps 在反事实上真正有用”。
* **评测逻辑**：从只看 final accuracy 转向同时看 **budgeted performance + process credibility**。
* **机制理解**：把 reasoning、faithfulness、credit assignment 放到同一个框架里讨论，而不是分成三个互不沟通的小方向。

---

# 5. Core Hypothesis and Research Claims

## 主假设

**H1（主假设）**
**Claim**：在固定 rollout policy 与固定预算下，步骤的“匹配反事实边际贡献”比“step correctness”或“raw progress proxy”更接近真正值得被奖励的过程对象；以此训练的模型会在不依赖额外 test-time compute 的情况下，提升 equal-cost 性能与 faithfulness。
**Intuition**：真正有用的步骤，应该在反事实替换下表现出可测的未来成功率差异。
**Testability**：比较 CaPS 估计的 step credit、step correctness、PAV-style raw progress 与真实 step deletion effect 的相关性，并比较下游训练效果。

## 子假设 / 研究命题

**H2**
**Claim**：CaPS 的收益会在**高依赖深度**任务上显著高于浅层任务。
**Intuition**：只有当任务真的需要中间状态时，过程信用才有信息量。
**Testability**：按 task family complexity / dependency depth 分层，比较 BAUC 与 faithfulness 提升曲线。

**H3**
**Claim**：matched-counterfactual credit 必须同时依赖 **delete + paraphrase + distractor**；仅做 delete-only 或 raw before/after progress 不足以排除表面形式混淆。
**Intuition**：如果不做 paraphrase invariance 与 spurious-step rejection，模型仍可能奖励“像 reasoning 的句子”。
**Testability**：做 credit estimator ablation，比较三类干预组合对 faithfulness 和下游性能的影响。

**H4**
**Claim**：CaPS 的性能提升若成立，应伴随更强的 process-credibility signature，而不只是更长或更短的 trace。
**Intuition**：如果训练真的学到了“有用步骤”，top-credit steps 被删去时应更显著地损害最终成功。
**Testability**：测 Top-Step Causal Drop、Paraphrase Stability、Distractor Vulnerability，并和长度、token 数控制后的结果对照。

**H5**
**Claim**：高信用步骤在训练后应对最终答案的内部表示产生更强影响。
**Intuition**：如果过程信用是真正的机制变量，而非输出层的表面正则，那么高信用步骤对应的 hidden states 应更强地决定后续答案。
**Testability**：做 hidden-state patching、step-level ablation、answer-logit influence 分析；参考已有 probing 工作的 correctness probe 作为辅助诊断。 ([arXiv][2])

---

# 6. Why This Proposal is Novel

## 6.1 Closest prior work

### A. Process supervision / process reward

* **Let’s Verify Step by Step**：用 step-level human feedback 训练 verifier，并显示 process supervision 可优于 outcome supervision。 ([OpenReview][1])
* **Rewarding Progress / PAV**：把过程奖励定义为步骤前后未来正确性变化，强调 distinct prover 的重要性。 ([arXiv][3])
* **PRIME**：用 outcome labels 学 dense implicit process rewards，降低在线 PRM 的标注成本。 ([arXiv][4])

### B. Faithfulness measurement / training

* **Measuring the Faithfulness of Thinking Drafts**：提出对 thinking draft 的系统化 counterfactual evaluation。 ([arXiv][5])
* **FRIT**：基于 step intervention 生成 faithful/unfaithful 对，并用 DPO 提升 CoT faithfulness。 ([arXiv][6])
* **CST**：奖励那些能帮助 simulator 预测 counterfactual outputs 的 CoT。 ([arXiv][7])

### C. Skeptical counterpoints / alternative explanations

* **NoThinking**：指出显式 thinking 在 equal-budget 下并非总是必要，尤其在低预算时常被简单并行采样击败。 ([arXiv][8])
* **Does RL Really Incentivize Reasoning Beyond the Base Model?**：指出许多 RLVR 收益更像 sampling efficiency improvement，而非新 reasoning pattern。 ([OpenReview][9])
* **Do We Need to Verify Step by Step?**：理论上质疑 process supervision 相对 outcome supervision 的天然统计优势。 ([arXiv][10])

## 6.2 What they achieved

这些工作已经分别做到三件重要的事：

* 证明了 **过程监督是有效的训练信号**。
* 证明了 **faithfulness 不是默认成立的性质**。
* 证明了 **显式 reasoning gain 需要更严格的 equal-budget 解释**。

## 6.3 What is still missing

缺的不是“更多 process reward”或“更多 faithfulness benchmark”，而是一个能把这三件事统一起来的对象：

* 现有 PRM / PAV / PRIME 主要回答“怎样给过程打分更有用”，但没有充分区分**文本步骤的表面形式**与**步骤内容本身的因果作用**。
* 现有 faithfulness 工作主要回答“如何测 / 如何提升 faithful CoT”，但没有把 faithfulness 直接变成 reasoning post-training 的**核心信用分配对象**。
* 现有批判工作指出“许多 gain 可能是搜索和采样造成的”，但没有提出一个新的训练原则来回应这个批评。

## 6.4 What is irreducibly new here

这份 proposal 的不可替代贡献，不是“把几个已有模块拼起来”，而是四件事的组合：

### (i) 新问题定义

我们把“好步骤”重定义为：
**在固定预算下，相对于匹配的反事实替代步骤，能提升未来 verifier success 的步骤。**

### (ii) 新机制

我们不是只看 before/after progress，而是用 **matched counterfactual alternatives** 来识别步骤内容本身的作用：

* paraphrase：语义等价，不应改变信用；
* distractor：表面相似但语义无用，不应获得正信用；
* delete：若步骤必要，删除应降低未来成功率。

### (iii) 新评测视角

我们把主评测从单点 accuracy 改成：

* **equal-cost performance**，
* **process credibility**，
* **depth-conditioned gains**。

### (iv) 轻理论闭环

我们给出 step credit 近似误差如何影响 trace 排序和 policy 学习的分析，而不是只给经验图表。

**关键判断**：
如果把这项工作写成“训练一个更好的 step verifier”，novelty 不够强，只能算一篇扎实的 empirical paper。
它只有在“**matched-counterfactual causal credit 重写了 process supervision 的训练对象**”这一叙事下，才有顶会主线强度。

---

# 7. Conceptual Framework

## 7.1 核心概念

设输入问题为 (x)，模型生成 reasoning trace
[
\tau = (s_1, s_2, \dots, s_T),
]
其中 (s_t) 是第 (t) 个**语义步骤**。最终答案为 (y)，客观 verifier 为
[
v(x,\tau,y)\in{0,1}\ \text{或}\ [0,1].
]

定义第 (t) 步之前的 prefix 为
[
p_{t-1}=(x,s_{<t}).
]

在 rollout policy (\rho) 和剩余预算 (B_t) 下，给定候选步骤 (s) 的未来成功效用定义为
[
U^\rho_B(p_{t-1}, s)
====================

\mathbb{E}*{z\sim \rho(\cdot \mid p*{t-1}\oplus s; B_t)}
\left[
v(x, p_{t-1}\oplus s \oplus z)
\right].
]

## 7.2 区分四类步骤集合

对真实步骤 (s_t)，我们定义两个集合：

* **正集合 (\mathcal{E}(s_t))**：语义等价的 paraphrase / reformulation。
* **负集合 (\mathcal{N}(s_t))**：删除、无用但风格相近的 distractor、或局部看似合理但不会推进求解的替代步骤。

然后定义 **matched-counterfactual causal credit**：

[
g_t
===

\mathbb{E}*{\tilde s\sim \mathcal{E}(s_t)}
U^\rho_B(p*{t-1}, \tilde s)
;-;
\mathbb{E}*{s' \sim \mathcal{N}(s_t)}
U^\rho_B(p*{t-1}, s').
]

这个定义有两个关键点：

1. **语义等价应保信用不变**。
2. **表面相似但语义无用的步骤不应获得信用**。

所以它不只是“step 后成功率变高没有”，而是“**这一步的内容本身**有没有带来提升”。

## 7.3 研究对象、观测量、机制变量、干预变量、结果变量

* **研究对象**：步骤级 causal process credit (g_t)。
* **观测量**：prompt、trace、步骤文本、verifier 输出、continuation 成功率、token 成本。
* **机制变量**：高信用步骤对后续隐藏状态与最终答案分布的影响强度。
* **干预变量**：delete / paraphrase / distractor、rollout policy (\rho)、剩余预算 (B_t)。
* **结果变量**：budgeted accuracy、faithfulness 指标、sample efficiency、hidden-state influence。

## 7.4 简化因果图

可以把每一步看成一个因果节点：

[
s_t \rightarrow h_t \rightarrow \text{future search distribution} \rightarrow y
]

但这里存在两个混淆因素：

* **任务难度**：难题更可能需要长推理；
* **表面风格**：某些句式可能让 verifier 或 policy 误以为步骤更“高级”。

matched counterfactual 的作用，就是尽量把“步骤内容的真实作用”从“难度”和“表面风格”里分离出来。

---

# 8. Research Plan

## 8.1 Data / task / benchmark

### 主训练与主评测底座：Reasoning Gym

Reasoning Gym 提供了 **100+ 个带 verifiable reward 的推理环境**，支持几乎无限数据生成和可调复杂度，非常适合做：

* 训练分布可控；
* family-level held-out generalization；
* depth-conditioned analysis；
* objective evaluation。 ([NeurIPS][11])

### 外部泛化 1：CRUXEval

CRUXEval 含 800 个短 Python 函数，核心是 input/output prediction，强调**可执行代码推理**而非代码生成流畅度。它适合检验：CaPS 是否能从通用 procedural reasoning 迁移到 executable reasoning。 ([arXiv][12])

### 外部泛化 2：固定快照 LiveCodeBench（建议附加实验）

LiveCodeBench 是 contamination-free、持续更新的代码 benchmark，并覆盖 test output prediction、自修复、执行等多种能力。它对“真实世界新题”很有价值，但因为动态更新会增加复现复杂度，所以本 proposal 将其设为**固定快照的附加实验或 appendix**，不作为主证据。 ([OpenReview][13])

### 不建议第一版纳入主文的评测

* 开放域 free-form QA
* 依赖 LLM judge 的主指标
* 动态更新但难以快照锁定的评测

原因：这些设置会削弱“可证伪、可复现、objective verifier”这条主线。

### 新数据构建：CaPS-Intervention Set

我们将从 Reasoning Gym + CRUXEval 生成一个步骤级反事实数据集：

1. 采样 prompt；
2. 生成 (K) 条 trace；
3. 切分 semantic steps；
4. 为每个候选步骤生成

   * delete 版本，
   * paraphrase 版本，
   * distractor 版本；
5. 在固定剩余预算下 rollout (M) 次 continuation，估计 (\hat g_t)。

输出 artifact：

* 原始 prompt
* 原始 trace
* step segmentation
* 每步的 (\mathcal{E}(s_t))、(\mathcal{N}(s_t))
* Monte Carlo utility 估计
* 最终 step credit label

## 8.2 Method

### 核心方法：CaPS

#### Stage A: Trace collection

* 对每个 prompt (x)，用 base policy 采样 (K) 条 reasoning traces。
* 默认 (K=4)。
* 采样参数：temperature 0.7，top-p 0.95。
* 保持统一最大 token budget。

#### Stage B: Semantic step segmentation

* math / logic / procedural：按自然 reasoning units 切分。
* code：按 block / statement group / execution state 切分。
* 首版采用启发式 + 少量人工审查；必要时再加 teacher-aided segmentation。

#### Stage C: Matched counterfactual generation

对每个步骤 (s_t)：

* **delete**：直接移除该步骤；
* **paraphrase**：用高质量 API 模型生成 2–3 个语义等价版本；
* **distractor**：生成风格匹配但语义无推进作用的替代步骤。

我们只把 API 用于**候选生成与人工审查辅助**，不把闭源 judge 放进主评测闭环。

#### Stage D: Utility estimation

对每个干预版本，在相同剩余 token budget 下 rollout (M) 次 continuation，计算成功率均值作为 (\hat U^\rho_B)。
默认：

* pilot：(M=3)
* 主实验：(M=5)

得到估计标签：
[
\hat g_t
========

## \frac{1}{|\mathcal{E}|}\sum_{\tilde s\in \mathcal{E}(s_t)} \hat U(p_{t-1}, \tilde s)

\frac{1}{|\mathcal{N}|}\sum_{s'\in \mathcal{N}(s_t)} \hat U(p_{t-1}, s').
]

#### Stage E: 训练 Causal Process Verifier（CPV）

训练一个标量头 (q_\phi(p_{t-1}, s_t)\approx \hat g_t)，损失为：

[
L_{\text{CPV}}
==============

L_{\text{regress}}
+
\lambda_{\text{para}} L_{\text{para-inv}}
+
\lambda_{\text{rank}} L_{\text{neg-rank}}.
]

其中：

* (L_{\text{regress}})：拟合 (\hat g_t)；
* (L_{\text{para-inv}})：约束 paraphrase 等价版本分数接近；
* (L_{\text{neg-rank}})：要求真实步骤优于 matched distractor。

#### Stage F: Causal-DPO policy training

给每条 trace 赋分：

[
R(\tau)
=======

w_{\text{ans}}, v(x,\tau,y)
+
w_{\text{proc}} \cdot \frac{1}{T}\sum_{t=1}^T q_\phi(p_{t-1},s_t)
-----------------------------------------------------------------

w_{\text{len}} \cdot \text{len}(\tau).
]

在同一 prompt 内按 (R(\tau)) 排序，构造 preference pairs，使用 DPO 做离线 post-training。选 DPO 而不是把在线 RL 作为核心，是因为 DPO更稳定、更轻量；在线 RL 可作为后续增强，但不是本 proposal 的成立前提。另一方面，直接对 proxy reward 做强优化存在 reward over-optimization 风险，这也是我们先采用保守离线方案的原因。 ([arXiv][14])

### 伪代码级流程

```text
for each prompt x:
    sample K traces τ1...τK from base policy
    segment each trace into semantic steps
    for selected steps st:
        generate E(st): paraphrases
        generate N(st): delete + distractors
        for each intervention version:
            rollout M continuations under fixed remaining budget
            estimate utility U_hat
        compute step credit g_hat_t

train CPV q_phi on step-credit regression + invariance + ranking

for each prompt x:
    score traces using answer reward + mean CPV score - length penalty
    build within-prompt preference pairs
train policy with Causal-DPO
(optional) small online refinement, appendix only
```

### 复杂度与成本

核心成本在反事实 rollout，近似为：
[
O(N \cdot K \cdot L \cdot M),
]
其中：

* (N)：prompt 数
* (K)：每题采样 trace 数
* (L)：每条 trace 被干预的步骤数
* (M)：每个干预的 continuation 数

这比大规模预训练便宜一个数量级以上，且与 16×80GB A800 资源相匹配。

## 8.3 Theoretical / mechanistic analysis

### 理论命题 A：trace 排序稳定性

若 CPV 对 step credit 的估计满足
[
|q_\phi - g_t| \le \epsilon
]
且 trace 长度上界为 (T)，则总过程分数误差至多为 (T\epsilon)。因此，只要两条 trace 的理想信用差距大于 (2T\epsilon)，其排序不会被估计误差翻转。
**作用**：这给“为什么 step-level credit 估计精度重要”一个直接解释。

### 理论命题 B：表面形式不变性

若 paraphrase invariance 成立，则语义等价的步骤不应因表面词形不同而获得系统性不同信用。
**作用**：这把 faithfulness 约束从外部评测变成训练目标的一部分。

### 理论命题 C：spurious-step rejection

若 matched distractor 与真实步骤的局部风格相似，但真实步骤 consistently 具有更高 future utility，则 CPV 必须学到“推进求解的内容”，而非“像推理的句式”。
**作用**：这是“不是工程堆砌”的关键机制点。

### 机制分析

我们将使用两类机制证据：

1. **step-level hidden-state patching / ablation**：看高信用步骤被移除后，对最终答案 logits 的影响是否更大；
2. **correctness probe 辅助分析**：已有 probing 工作表明，reasoning 模型的 hidden states 含有中间答案正确性信息。我们将把这一发现用作辅助诊断，而不是核心前提。 ([arXiv][2])

## 8.4 Expected empirical signatures

如果主假设成立，实验上应看到以下模式：

* CaPS 在 **equal-cost** 条件下优于 outcome-only 与 raw-progress baselines。
* 收益主要出现在 **高依赖深度** 任务，而非浅层任务。
* faithfulness 指标显著提升，且不是单纯由 trace 变长带来。
* 高信用步骤删除导致的性能下降，大于低信用步骤删除。
* CPV 的信用估计与真实 intervention effect 的相关性，高于 step correctness 与 PAV-style score。

---

# 9. Experimental Design

## 9.1 Models

### 主实验模型

* **Pilot policy**：1.5B–3B 级开源模型
* **Main policy**：7B–8B 级开源模型
* **CPV backbone**：与 main policy 同家族的 3B 或 7B 版本，外接 scalar head
* **训练方式**：LoRA / QLoRA 优先；只在必要时做 7B 全参微调
* **理由**：

  * 能在当前算力内完成多轮对照；
  * 足以观察 process credit 是否形成稳定信号；
  * 避免“大模型才看得见效果”的叙事依赖。

### Judge / evaluator

* **主评测**：objective verifiers
* **API judge**：只用于 paraphrase 候选生成、小规模人工核查辅助，不进入主指标闭环
* **理由**：减少 judge bias，保持可复现

## 9.2 Baselines

1. **Outcome-only DPO / ORM-style post-training**

   * 强，因为它是最直接的 answer-only 基线。
   * 必须比，因为它回答“过程信用是否真的必要”。

2. **PAV / Rewarding Progress-style verifier**

   * 强，因为它是最接近的 process credit 基线。
   * 必须比，因为若打不过它，本 proposal 的“matched counterfactual”增益不成立。 ([arXiv][3])

3. **PRIME-style implicit process reward**

   * 强，因为它代表“只用 outcome labels 学 dense reward”的可扩展路线。
   * 必须比，因为它是当前最现实的 scalable dense-reward baseline。 ([arXiv][4])

4. **FRIT 或 CST-style faithfulness training**

   * 强，因为它们直接针对 faithfulness。
   * 必须比，因为若 CaPS 只提升 faithful CoT，而无法比过已有 faithfulness training，就不足以成为新原则。 ([arXiv][6])

5. **NoThinking + verifier / best-of-N**

   * **最难打败的 baseline**。
   * 必须比，因为它直接检验你的收益是不是仅仅来自更会花 token 或更会采样。 ([arXiv][8])

## 9.3 Main experiments

### Experiment 1: Credit recovery sanity check

* **目的**：验证 step credit estimator 是否真的恢复“因果有用性”
* **设置**：在带显式中间状态的可执行小任务上，构造 ground-truth necessary / unnecessary steps
* **变量**：CaPS credit、step correctness、PAV-style score
* **指标**：与真实 deletion effect 的 Spearman / Kendall 相关
* **预期现象**：CaPS 显著高于 step correctness 与 raw progress
* **若结果相反**：说明 matched counterfactual 估计不足以识别真实因果步骤；需缩窄到更干净的 executable 域或修改干预构造

### Experiment 2: In-domain performance on Reasoning Gym

* **目的**：验证主任务性能
* **设置**：选 12 个 train families、4 个 validation families、4 个 held-out families
* **变量**：训练方法
* **指标**：Acc@B、BAUC、macro average over families
* **预期现象**：CaPS 在 equal-cost 条件下优于 outcome-only / PAV / PRIME
* **若结果相反**：说明 causal credit 未转化成更好的 policy 学习

### Experiment 3: Depth-conditioned phase diagram

* **目的**：检验收益是否与任务依赖深度相关
* **设置**：按 RG complexity bins / CRUXEval control-flow depth 分层
* **变量**：dependency depth、budget
* **指标**：各 depth bin 上的 BAUC
* **预期现象**：浅任务上 NoThinking 接近或更强；深任务上 CaPS 反超
* **若结果相反**：说明“中间状态必要性”不是收益主因，需修正理论为一般性 reward shaping

### Experiment 4: Faithfulness stress test

* **目的**：验证不是单纯性能增益
* **设置**：对 reasoning trace 做 top-credit deletion、low-credit deletion、paraphrase、distractor 插入
* **指标**：Top-Step Causal Drop、Paraphrase Stability、Distractor Vulnerability
* **预期现象**：CaPS 显著提升这些指标
* **若结果相反**：说明模型仍在利用表面 proxy，而非真实过程信用

### Experiment 5: Sample efficiency

* **目的**：检验是否更高效
* **设置**：固定数据预算，比较达到同一验证集水平所需训练步数
* **指标**：learning curve、steps-to-threshold、AUC of training curve
* **预期现象**：CaPS 更快达到同等性能
* **若结果相反**：说明 credit 信号太噪，可能只适合作评测而非训练目标

### Experiment 6: Mechanistic dependence

* **目的**：验证高信用步骤是否真的更“被模型用到”
* **设置**：对 top-credit vs low-credit steps 做 hidden-state patching / ablation
* **指标**：answer-logit shift、final correctness drop
* **预期现象**：高信用步骤对最终答案分布的影响更大
* **若结果相反**：说明性能改善可能来自输出层偏置，而非内部因果依赖

### Experiment 7: External transfer

* **目的**：检验是否跨域迁移
* **设置**：在 CRUXEval 上零样本或少量适配评测；LiveCodeBench 固定快照放附加实验
* **指标**：input/output prediction accuracy、budgeted transfer
* **预期现象**：在 executable reasoning 上保留部分增益
* **若结果相反**：说明当前原则更适合 structured/procedural reasoning，应收缩 claim

## 9.4 Ablations

关键 ablation 维度：

* raw progress vs matched-counterfactual credit
* delete-only vs delete+paraphrase vs full delete+paraphrase+distractor
* same-policy rollout vs distinct prover rollout
* 3B CPV vs 7B CPV
* LoRA-only vs LoRA + online RL refinement
* 不同 (w_{\text{proc}})、(w_{\text{len}})、(M)、(K)
* 不同步骤粒度（粗步 vs 细步）

## 9.5 Robustness / stress test

至少三类：

1. **Counterfactual robustness**

   * paraphrase
   * reorder non-essential steps
   * insert style-matched distractors

2. **Budget robustness**

   * fixed token budget
   * fixed wall-clock proxy
   * pass@1 与小规模 pass@k 对照

3. **Generalization robustness**

   * held-out families
   * cross-domain transfer to CRUXEval
   * fixed-snapshot LiveCodeBench appendix

## 9.6 Statistical validity

* **Seeds**：

  * pilot：5 seeds
  * 7B 主实验：3 seeds
* **置信区间**：95% bootstrap CI
* **显著性检验**：

  * paired bootstrap / paired permutation
  * McNemar 用于 paired correctness
* **避免 cherry-picking**：

  * 预先锁定 benchmark families
  * 预先锁定预算档位
  * 所有 family 全量报告，不只汇报最强子集
  * HPO 预算固定，先在 3B 上搜，再迁移到 7B

---

# 10. Falsifiable Predictions

## Prediction 1

* **Prediction**：CaPS 估计的 step credit 与真实 deletion effect 的相关性，高于 step correctness 与 PAV-style raw progress。
* **How to test**：在可执行任务上，对每一步做真实删除干预，比较各信用指标与性能下降的相关性。
* **What failure would imply**：matched counterfactual 并没有比现有 proxy 更接近“因果有用性”。
* **How the theory would be revised**：把主张缩减为“CaPS 是训练上有效的 proxy”，不再声称它更接近真实 process credit。

## Prediction 2

* **Prediction**：CaPS 的 equal-cost 收益主要出现在高 dependency depth 任务上。
* **How to test**：按 complexity/depth 分层做 BAUC 曲线。
* **What failure would imply**：我们的“中间状态必要性”解释过强。
* **How the theory would be revised**：改为“CaPS 是一般性的 reward shaping / regularization”，而非专门针对多步依赖。

## Prediction 3

* **Prediction**：只做 delete-only 不足以复现 full CaPS；必须加入 paraphrase invariance 和 distractor rejection。
* **How to test**：做干预类型 ablation。
* **What failure would imply**：表面形式混淆不是主要问题。
* **How the theory would be revised**：将 matched counterfactual 简化为 delete-based causal credit，弱化“surface-form confounding”论点。

## Prediction 4

* **Prediction**：CaPS 对 Top-Step Causal Drop、Paraphrase Stability、Distractor Vulnerability 的改善，会超过 outcome-only、PAV/PRIME 和 FRIT/CST-style baselines。
* **How to test**：统一预算下比较这些指标。
* **What failure would imply**：CaPS 可能只是提升 accuracy，而没有更 faithful。
* **How the theory would be revised**：把贡献收缩为“更好的过程训练信号”，不再主张 faithfulness 是关键机制。

## Prediction 5

* **Prediction**：高信用步骤的 hidden-state ablation 对最终答案的损害，在 CaPS 模型中大于在基线模型中。
* **How to test**：做 step-level patching / ablation。
* **What failure would imply**：性能收益可能来自输出层校准或长度偏置，而非内部过程依赖。
* **How the theory would be revised**：将机制主张改写为“output-level policy shaping”，而非“internal causal reliance”。

## Prediction 6

* **Prediction**：在弱 verifier 或开放域 free-form QA 上，CaPS 的收益会显著下降。
* **How to test**：在低可信 verifier 任务上复现实验。
* **What failure would imply**：该原则的适用范围比预期更广。
* **How the theory would be revised**：扩展 claim，从“verifiable reasoning principle”改成更一般的 process-credit principle。

---

# 11. Risks, Failure Modes, and Plan B/C

## 11.1 理论风险

### 风险

“因果信用”在这里其实是**policy-conditioned counterfactual utility**，不是哲学意义上的真实因果效应。若 rollout policy 或 intervention 构造不合理，信用估计会失真。

### 应对

* 明确在文中限定定义：**under fixed policy and fixed budget**
* 对 distinct prover / same-policy prover 都做 ablation
* 不过度宣称“识别真实 causality”，而是识别“训练上有用的反事实信用”

## 11.2 实验风险

### 风险

step segmentation 不稳，导致干预不匹配。

### 应对

* 先在 executable/procedural task 上做
* 首版只干预 4 个关键步骤，而不是整条 trace 所有步骤
* 加人工抽查 200–300 个 step intervention 样本

## 11.3 Benchmark 风险

### 风险

Reasoning Gym 太“干净”，迁移到开放环境可能弱。

### 应对

* 主文把 claim 限定为 **verifiable reasoning**
* 外部泛化用 CRUXEval
* LiveCodeBench 作为 appendix，不把结论建立在动态 benchmark 上

## 11.4 识别 / 解释风险

### 风险

accuracy 提升了，但 faithfulness 没有提升；或者 faithfulness 提升了，但 accuracy 没有提升。

### 应对

* 若前者发生：说明仍在走 proxy optimization，需增强 paraphrase/distractor loss
* 若后者发生：说明 credit 信号有价值但太保守，需降低 (w_{\text{proc}}) 或做 curriculum

## 11.5 工程风险

### 风险

反事实 rollout 成本过高，拖慢项目节奏。

### 应对

* 先做 pilot：小模型、少任务、(M=3)
* 主实验只扩最有效的设置
* data generation 与 training 两机并行

## Plan B

若主假设在通用 RG family 上不成立，收缩到：
**“CaPS 在 executable / verifiable multi-step domains 中提升 process credibility 与 equal-cost performance”**。
这仍然是一篇强的 structured reasoning 论文。

## Plan C

若训练增益弱，但 step credit 评测很强，则转向：
**“Matched-counterfactual process credibility 作为新评测协议”**。
论文主贡献变为：

* 新问题定义
* 新数据构建
* 新评测指标
* 对现有 PRM / faithfulness 方法的系统诊断

这会从方法论文转为 field-shaping evaluation paper。

---

# 12. Feasibility Under Compute Constraints

## 12.1 模型规模

* Pilot：1.5B–3B
* Main：7B–8B
* CPV：3B 或 7B + scalar head
* 训练方式：LoRA/QLoRA 优先

这完全落在 16×80GB A800 可承受范围内。

## 12.2 预估数据规模

### Pilot

* 5k prompts
* 每题 4 条 trace
* 每条 trace 干预 4 个步骤
* 每个干预 3 次 continuation

总 continuation 数约：
[
5{,}000 \times 4 \times 4 \times 3 = 240{,}000
]

### Main

* 20k prompts
* 其余配置不变

总 continuation 数约：
[
20{,}000 \times 4 \times 4 \times 3 = 960{,}000
]

这是大规模 inference，但远低于预训练级开销。

## 12.3 GPU-days 估算

* **Counterfactual data generation**：10–18 GPU-days
* **CPV 训练**：3–5 GPU-days
* **7B LoRA Causal-DPO**：12–20 GPU-days
* **强基线与 ablation**：18–30 GPU-days
* **机制实验与外测**：8–12 GPU-days

**总计**：约 **51–85 GPU-days**

在两台机器并行下，这个量级是可做的。

## 12.4 API 使用位置

API 预算充足，但只用于：

* paraphrase 候选生成
* distractor 候选生成
* 小规模 semantic equivalence 审查
* 附加人工分析辅助

**不用于主指标计算**，避免不可复现。

## 12.5 并行策略

* **机器 A**：vLLM / rollout / intervention generation
* **机器 B**：CPV 训练、policy LoRA、评测
* 生成与训练并行进行，减少 idle time

## 12.6 为什么在给定资源下可做

关键原因有三个：

1. **不用大规模预训练**，只做中等规模 post-training
2. **主方法先离线后在线**，避免在线 RL 成为成败前提
3. **主 benchmark 使用 objective verifiers**，评测与诊断成本低

DPO 本身也比 RLHF / PPO 类方案更轻量、更稳定，适合作为核心训练器。 ([arXiv][14])

---

# 13. Reproducibility and Engineering Plan

## 13.1 配置管理

* Hydra / OmegaConf 分层配置
* 明确区分：

  * `dataset_config`
  * `rollout_config`
  * `cpv_config`
  * `policy_train_config`
  * `eval_budget_config`

## 13.2 实验记录

* W&B 记录训练曲线
* JSONL 保存每个 prompt 的 trace、干预、credit 估计
* 每个主实验 run 固定记录 git commit hash

## 13.3 数据版本

至少保存以下版本化 artifacts：

* prompt manifest
* raw traces
* step segmentation
* paraphrase / distractor candidates
* utility rollouts
* final step credit labels
* prompt-wise preference pairs
* benchmark snapshot ids

## 13.4 随机种子

* 统一固定 seeds 列表
* rollout、训练、评测分别记录 seed
* 所有表格默认报告 seed mean ± CI

## 13.5 Checkpoint 策略

* CPV：每 500–1000 steps 保存
* Policy：每 epoch / 每固定步数保存
* 保留：

  * best validation BAUC
  * best faithfulness metric
  * last checkpoint

## 13.6 评测脚本

* 所有主指标使用 deterministic scripts
* objective verifier 优先
* equal-budget 评测脚本与训练脚本分离
* 对动态 benchmark 必须固定快照并发布 snapshot manifest

## 13.7 Artifact 发布建议

建议公开发布：

* CaPS-Intervention Set
* CPV 训练脚本与权重
* Causal-DPO 数据构建脚本
* 主结果评测脚本
* 关键 figure 复现 notebook

---

# 14. Timeline and Milestones

## Week 1–2：最小闭环

目标：

* 跑通 RG + step segmentation + intervention pipeline
* 完成 5k prompts pilot 数据生成
* 在 1.5B/3B 模型上训练初版 CPV

**最小闭环成功信号**：

* CaPS credit 与 deletion effect 的相关性高于 step correctness / raw progress
* 至少 2 个深任务 family 上出现初步 BAUC 提升

## Week 3：第一轮 3B policy 实验

目标：

* 完成 3B Causal-DPO
* 跑 outcome-only、delete-only、NoThinking 对照
* 确定 (w_{\text{proc}})、(w_{\text{len}})、(M) 的稳定区间

## Week 4：中期 Go / No-Go

**Go 条件**：

* credit estimator 明显优于 proxy baselines
* 3B 上 faithfulness 指标有清晰改善
* equal-cost 至少不输 outcome-only

**No-Go / Pivot 条件**：

* credit 估计不优于 proxy
* faithfulness 与 accuracy 同时无增益
* 则转 Plan B 或 Plan C

## Week 5–6：7B 主实验

目标：

* 训练 7B CPV 与主 policy
* 完成 PAV / PRIME / faithfulness-only / NoThinking 主对照
* 完成 held-out family 评测

## Week 7：机制与鲁棒性

目标：

* hidden-state patching / ablation
* paraphrase / distractor / reorder stress tests
* depth-phase diagram

## Week 8：外部泛化与附加实验

目标：

* CRUXEval
* 固定快照 LiveCodeBench appendix
* 清理所有表格与统计显著性结果

## Week 9–10：写作阶段

目标：

* 主文 8 页叙事
* appendix 补全实现细节、额外曲线、额外模型
* 统一图表风格与 claim scope

---

# 15. Paper Framing

## 15.1 Best-paper style one-sentence pitch

**The field currently rewards reasoning traces that look plausible; we argue and test that it should reward only those steps whose semantic content causally improves the chance of being correct.**

## 15.2 Contribution bullets

* 提出 **matched-counterfactual causal process credit**，把 reasoning post-training 的训练对象从“局部合理步骤”重写为“对未来成功有反事实贡献的步骤”。
* 提出 **CaPS**：用 delete / paraphrase / distractor 三类 matched interventions 训练 Causal Process Verifier，并结合 Causal-DPO 做离线 post-training。
* 提出一组新的 **process credibility** 指标与 equal-cost 评测协议，避免把更高 token 消耗误判为更好 reasoning。
* 给出 step credit 估计误差与 trace 排序稳定性的轻理论分析。
* 在 verifiable reasoning 环境中系统验证：CaPS 何时有效、为何有效、何时不该有效。
* 通过机制实验区分“真的学到高信用步骤”与“只是学到新的输出偏置”。

## 15.3 Figure plan

### Figure 1：领域张力图

三角结构：

* process supervision 有效
* faithfulness 不可靠
* NoThinking / RL critique 质疑 gain 来源
  要表达：当前文献缺一个统一对象。

### Figure 2：CaPS 方法图

prompt → trace → semantic steps → matched interventions → utility rollouts → CPV → Causal-DPO
要表达：方法不是 pipeline 堆砌，而是围绕“credit object”展开。

### Figure 3：核心概念图 / 公式图

真实步骤、paraphrase、distractor 的未来成功概率对比
要表达：什么叫 matched-counterfactual credit。

### Figure 4：Equal-cost phase diagram

横轴 budget，纵轴 dependency depth，颜色表示哪种方法更优
要表达：CaPS 不是 everywhere better，而是在“需要中间状态”的区域更优。

### Figure 5：Faithfulness vs performance 散点图

不同方法在 BAUC 与 Top-Step Causal Drop 上的 Pareto
要表达：CaPS 不是只提升一个维度。

### Table 1：主结果表

RG macro average、held-out family、CRUXEval
要表达：主效果稳定。

### Table 2：关键 ablation

delete-only / raw progress / full CaPS / same-policy vs distinct prover
要表达：matched counterfactual 是必要的。

## 15.4 Related work organization

related work 不应按“论文清单”写，而应按四个争论轴组织：

1. **What should process reward represent?**
   Let’s Verify, PAV, PRIME, PRM/ORM 路线

2. **Can reasoning traces be trusted?**
   thinking draft faithfulness、FaithCoT、FRIT、CST

3. **Are reasoning gains real or just better search?**
   NoThinking、RLVR critique、process-vs-outcome theory

4. **Why verifiable environments matter**
   Reasoning Gym、CRUXEval、LiveCodeBench / contamination-free evaluation

---

这份 proposal 里最值得你守住的一句话是：

**不要把它写成“一个更好的 PRM”。要把它写成“我们重新定义了 reasoning post-training 里什么样的过程值得被奖励”。**

[1]: https://openreview.net/forum?id=v8L0pN6EOi&utm_source=chatgpt.com "Let's Verify Step by Step"
[2]: https://arxiv.org/abs/2504.05419?utm_source=chatgpt.com "Reasoning Models Know When They're Right: Probing Hidden States for Self-Verification"
[3]: https://arxiv.org/abs/2410.08146?utm_source=chatgpt.com "Rewarding Progress: Scaling Automated Process Verifiers for LLM Reasoning"
[4]: https://arxiv.org/abs/2502.01456?utm_source=chatgpt.com "Process Reinforcement through Implicit Rewards"
[5]: https://arxiv.org/abs/2505.13774?utm_source=chatgpt.com "Measuring the Faithfulness of Thinking Drafts in Large Reasoning Models"
[6]: https://arxiv.org/abs/2509.13334?utm_source=chatgpt.com "FRIT: Using Causal Importance to Improve Chain-of-Thought Faithfulness"
[7]: https://www.arxiv.org/abs/2602.20710?utm_source=chatgpt.com "Counterfactual Simulation Training for Chain-of-Thought ..."
[8]: https://arxiv.org/abs/2504.09858?utm_source=chatgpt.com "Reasoning Models Can Be Effective Without Thinking"
[9]: https://openreview.net/forum?id=4OsgYD7em5&utm_source=chatgpt.com "Does Reinforcement Learning Really Incentivize ..."
[10]: https://arxiv.org/abs/2502.10581?utm_source=chatgpt.com "Do We Need to Verify Step by Step? Rethinking Process Supervision from a Theoretical Perspective"
[11]: https://neurips.cc/virtual/2025/poster/121745?utm_source=chatgpt.com "Reasoning Environments for Reinforcement Learning with ..."
[12]: https://arxiv.org/abs/2401.03065?utm_source=chatgpt.com "CRUXEval: A Benchmark for Code Reasoning, Understanding and Execution"
[13]: https://openreview.net/forum?id=chfJJYC3iL&utm_source=chatgpt.com "LiveCodeBench: Holistic and Contamination Free ..."
[14]: https://arxiv.org/abs/2305.18290?utm_source=chatgpt.com "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
