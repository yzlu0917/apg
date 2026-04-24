# 1. Title

**主标题**
**Verify the State, Not the Sentence: Latent Process Supervision for Reasoning Models**

**备选标题 1**
**Supervising the Wrong Object: Latent State-Transition Verification for Reasoning**

**备选标题 2**
**From Chain-of-Thought to State-of-Reasoning: A Proposal for Latent Process Supervision**

**备选标题 3**
**Counterfactually Invariant Process Supervision via Task-Conditioned Latent Verifiers**

---

# 2. One-Paragraph Thesis Summary

本 proposal 要解决的不是“怎样再做一个更强的 verifier”，而是一个更基础的问题：**过程监督到底在监督什么对象**。当前主流做法默认把文本化的 chain-of-thought 步骤当作 process supervision 的基本单位；但近年的证据形成了清晰张力：过程监督在部分数学推理中有效，理论上却未必天然比 outcome supervision 更容易；最新基准又表明 step-level verifier 在高难度、开放式和分布外推理上仍然脆弱；与此同时，hidden-state probing 工作显示模型内部早已编码了 correctness 与 behavior 信号，而且这些信号具有明显的任务依赖性。([arXiv][1]) 基于这一张力，本 proposal 的核心主张是：**过程监督真正应监督的不是表面文本步骤，而是模型在生成步骤前后是否发生了一个通向正确解的潜在状态转移**。我们将围绕这一主张提出 task-conditioned latent transition verifier、构建 counterfactual invariance 评测、在自然语言数学与 Lean 形式化推理上做机制与效用验证，并用一组可证伪预测来检验“监督对象重定义”是否真的比“更强文本 judge”更接近问题本质。若成立，这个工作会把社区对 process supervision 的默认对象、评价方式和方法原则一起推前一步。

---

# 3. Abstract

过程监督已成为推理模型研究的核心范式，但当前范式几乎默认把**文本化推理步骤**当作监督对象。这个设定正在遭遇三重张力：一方面，早期工作表明 step-level process supervision 能显著改善数学推理；另一方面，后续理论分析指出，在标准覆盖假设下，outcome supervision 未必在统计上更难；与此同时，最新的 ProcessBench 与 Hard2Verify 又显示，现有文本 PRM、critic 和生成式 judge 在高难度、开放式与分布外验证中依然脆弱。另一方面，hidden-state probe 研究表明，模型在显式输出前就已编码 correctness 与未来行为信号，但这些信号并不表现为一个可跨任务稳定复用的统一 truth geometry。([arXiv][1])

本 proposal 的核心假设是：**过程监督之所以重要却又脆弱，是因为社区长期在监督错误的对象**。真正应被监督的不是“这句话像不像合理的推理步骤”，而是模型在生成该步骤前后，内部表征是否发生了一个**语义上朝正确解推进的状态转移**。为此，我们提出一个可执行研究计划：训练一个 **task-conditioned latent transition verifier**，输入步骤边界前后的多层 hidden states 及其差分，预测局部步骤正确性；同时构建一个小而严格的 counterfactual benchmark，系统测量 verifier 在“语义保持改写”与“语义翻转扰动”下的稳定性与敏感性。实验将覆盖自然语言数学与 Lean 形式化证明两个域；后者提供可执行的 tactic-level process oracle，可用于区分“监督对象问题”与“标签噪声问题”。([OpenReview][2])

预期贡献不是一个更复杂的 pipeline，而是四点：一个新的问题定义、一个新的监督机制、一个新的评测透镜，以及一组机制上可证伪的经验预测。若该假设成立，process supervision 的主线将从“文本步骤打分”转向“潜在推理状态监督”。

---

# 4. Motivation and Problem Statement

## 4.1 当前领域最关键的现象与张力

当前 reasoning 研究存在一个没有被正面回答的张力。

第一，**经验上**，过程监督被广泛视为提升复杂推理的关键路径；《Let’s Verify Step by Step》给出了这一路线的经典证据。第二，**理论上**，《Do We Need to Verify Step by Step?》指出，在标准覆盖假设下，outcome supervision 未必在统计上比 process supervision 更难。第三，**实践上**，ProcessBench 和 Hard2Verify 显示，现有 step verifier 在难题、开放式证明和 frontier math 上仍然不稳，生成式 judge 如 ThinkPRM、StepWiser 的部分进展还与额外 verification-time reasoning 紧密相关。第四，**机制上**，hidden-state probing 工作表明模型在显式输出前就已经“知道”很多关于最终行为和正确性的东西，但这些 truth-related signals 又呈现明显的 task specificity。([arXiv][1])

这组事实共同指向一个更深的可能性：**当前瓶颈不只是 process 标签还不够多，也不只是 verifier 还不够大，而是我们可能把监督对象选错了。**

## 4.2 主流研究范式哪里不够

主流范式把“一个文本步骤是否合理”当作 process supervision 的原子问题。
但文本步骤并不是推理本身，而只是潜在推理状态的一种表面实现。于是文本 verifier 被迫同时学习两类因素：

* 与 correctness 真正相关的过程语义
* 与 correctness 无关的表面 nuisance：措辞、格式、冗长度、符号风格、模板痕迹

这种混杂会直接带来两个后果：

* verifier 对 same-semantics 的改写不稳定
* verifier 在 harder / OOD 场景中容易退化为“判断推理写得像不像”，而不是“判断推理是否真的在前进”

这也是为什么仅靠 self-correction 或更长 verification CoT 往往不能从根本上解决问题。([arXiv][3])

## 4.3 我们真正想问的研究问题

本 proposal 的中心问题是：

> **在 reasoning 中，“步骤是否正确”究竟更自然地是一个文本属性，还是一个潜在状态转移属性？**

拆开来，是四个更具体的问题：

* 局部正确性是否在步骤前后 hidden-state transition 中比在文本步骤中更稳定可读出？
* 这种信号是否对语义保持改写更不敏感、对语义翻转更敏感？
* 这种信号是否必须是 task-conditioned，而不是一个全局通用的 truth direction？
* 它能否在**相同预算**下改善 reranking、pruning 或 targeted revision，而不是靠更长 verifier CoT 取胜？

## 4.4 这项工作如果成功，会改变什么

如果成功，这项工作会改变三件事：

* **问题定义**：process supervision 的对象从 text step 转为 latent state transition
* **评价方式**：verifier 不再只看 nominal accuracy，而要看 invariance 与 semantic sensitivity
* **方法原则**：后续 PRM、critic、reasoning search、甚至 RLVR 的训练信号设计，都会更偏向“监督潜在过程”而不是“监督表面文本”

---

# 5. Core Hypothesis and Research Claims

## H1. 主假设

**Claim**
局部推理正确性更自然地编码在**步骤前后潜在状态转移**中，而不是文本步骤本身中；因此，一个 task-conditioned latent transition verifier 在稳健性和样本效率上应优于文本 step verifier。

**Intuition**
正确性依赖的是“状态有没有朝正确方向变化”，不是“这句话看起来像不像好推理”。

**Testability**
比较 latent verifier 与强文本 PRM / generative judge 在 nominal、OOD、counterfactual 和 fixed-budget utility 上的表现。

---

## H2. 子假设：不变性优势

**Claim**
在语义保持改写下，latent verifier 的分数波动应显著小于文本 verifier；在语义翻转扰动下，它仍应保持足够的区分 margin。

**Intuition**
如果 verifier 真在读“过程语义”，则 wording / format / notation 的改变不应显著改变分数；反之，语义翻转必须改变分数。

**Testability**
构造 paired counterfactual set，比较 invariance gap 与 semantic sensitivity。

---

## H3. 子假设：转移特征比单状态更关键

**Claim**
显式使用 ((h_t^{-}, h_t^{+}, \Delta h_t)) 的 transition representation 将显著优于只用 (h_t^{+}) 的 post-state probe。

**Intuition**
局部步骤正确性是“从哪里到哪里”的问题，而不是“落点看起来像不像对”。

**Testability**
做 state-only vs transition-feature ablation，并加入一个“text PRM + 相同 counterfactual regularizer”的控制基线。

---

## H4. 子假设：task-conditioning 是必要的

**Claim**
跨自然语言数学与 Lean 形式化推理，一个统一的 universal probe 将劣于 task-conditioned verifier。

**Intuition**
若 truth-related geometry 高度任务相关，则 process signal 更可能是“同原则、不同子空间”，而不是一个统一方向。([OpenReview][4])

**Testability**
比较 global probe 与 task-conditioned verifier 的跨任务泛化、校准和子空间相似性。

---

## H5. 子假设：效用优势主要出现在 hard / OOD / same-budget 场景

**Claim**
latent verifier 的优势不会主要体现在 easy in-domain 上，而会集中出现在 harder verification、OOD robustness 和固定预算的 reranking / pruning 上。

**Intuition**
如果它真的减少了对表面特征的依赖，那么收益应首先在最容易暴露表面过拟合的场景中出现。

**Testability**
分别在 ProcessBench、Hard2Verify、Lean clean-room 与固定预算搜索场景上测相对增益。

---

# 6. Why This Proposal is Novel

## 6.1 Closest prior work

### A. 文本过程监督 / PRM / stepwise judge

代表工作：

* *Let’s Verify Step by Step*
* *ProcessBench*
* *ThinkPRM / Process Reward Models That Think*
* *StepWiser* ([arXiv][1])

### B. Hidden-state correctness / behavior prediction

代表工作：

* *Reasoning Models Know When They’re Right*
* *Language Models Can Predict Their Own Behavior*
* *The Geometries of Truth Are Orthogonal Across Tasks* ([arXiv][5])

### C. Formal reasoning as process-oracle laboratory

代表工作：

* *Lean-STaR*
* *Process-Verified Reinforcement Learning for Theorem Proving*
* *DeepSeek-Prover-V2* ([OpenReview][2])

## 6.2 What they achieved

这些工作已经分别做到三件事：

* 证明了 process supervision 与 step verification 很重要，并给出了强基准与强 judge。([arXiv][1])
* 证明了 hidden states 中确实编码了 correctness / behavior 信号，且这些信号在某些任务上可以被提前读出。([arXiv][5])
* 证明了 Lean 可以提供细粒度、可执行、可验证的过程反馈，是研究 reasoning 机制的 clean-room。([OpenReview][2])

## 6.3 What is still missing

仍缺四个关键点：

* 没有人系统地把**监督对象本身**当作研究问题来处理
* 没有人把 verifier 的**counterfactual invariance**作为一等评测目标
* 没有人把 latent-process 假设在**自然语言推理与 formal clean-room**上同时验证
* 没有人把“hidden-state signal 存在”推进到“step-level latent process supervision 是否比 text supervision 更合理”

## 6.4 What is irreducibly new here

本 proposal 的不可替代贡献是四个层面的组合：

* **新问题定义**：process supervision 的对象应是 latent state transition，而不是 textual step
* **新机制**：task-conditioned latent transition verifier
* **新评测视角**：same-semantics invariance + semantic-flip sensitivity
* **新实验范式**：自然语言数学 + Lean clean-room 的双域机制验证

### 为什么这不是工程堆砌

如果只做以下任何一件事，这个项目都不够强：

* 只做一个 hidden-state probe：更像经验性 probing paper
* 只做一个更强 PRM：更像 engineering improvement
* 只做一个新 benchmark：更像 methodology / benchmark paper

这个 proposal 的核心不是“多加一个 head”，而是**把领域一直默认的监督对象重定义掉**，并围绕这个重定义建立机制、评测和实验闭环。
如果没有“对象重定义 + invariance 评测 + formal clean-room”，这个 idea 的 novelty 会明显降级。

---

# 7. Conceptual Framework

## 7.1 核心概念定义

给定问题 (x)，生成模型产生步骤轨迹 (\tau=(s_1,\dots,s_T))。

对每个步骤 (t)，定义：

* (u_t^{-})：生成第 (t) 步之前的 prefix
* (u_t^{+})：生成第 (t) 步之后的 prefix
* (h_{\ell}(u))：模型在层 (\ell) 对 prefix (u) 的边界 hidden state
* (\Delta h_{t,\ell}=h_{\ell}(u_t^{+})-h_{\ell}(u_t^{-}))

标签定义：

* (y_t^{loc}\in{0,1})：步骤 (t) 是否局部 sound
* (y_t^{path}\in{0,1})：prefix 到 (t) 为止，在有界 continuation budget 下是否仍存在可验证成功路径

  * 该标签只在 Lean 与可执行答案校验的子集上使用；不是主张成立的必要条件

## 7.2 研究对象、观测量、机制变量、干预变量、结果变量

**研究对象**

* 潜在推理状态转移

**观测量**

* 文本步骤 (s_t)
* 边界 hidden states (h_t^{-}, h_t^{+})
* step position、trace length、task id

**机制变量**

* 与 correctness 相关的潜在语义状态 (r_t)
* 与 wording / format / notation 相关的 nuisance (n_t)

**干预变量**

* same-semantics 改写：改变 (n_t)，尽量保持 (r_t)
* semantic-flip 扰动：改变 (r_t)
* task-conditioning on/off
* transition feature on/off
* layer choice
* 可选：沿 verifier direction 的小幅 hidden-state intervention

**结果变量**

* step AUROC / F1
* earliest-error accuracy
* ECE / Brier
* invariance gap
* semantic sensitivity
* same-budget final utility

## 7.3 简化分析框架

我们用一个 nuisance-decomposition 来刻画问题：

[
s_t = g(r_t, n_t), \qquad y_t = f(r_t)
]

其中：

* (r_t) 是真实推理状态
* (n_t) 是表面实现噪声
* 文本步骤 (s_t) 同时反映 (r_t) 与 (n_t)
* 局部正确性 (y_t) 主要由 (r_t) 决定

文本 verifier 直接建模 (p(y_t \mid s_t))，因此必须同时学习语义与 nuisance。
我们提出的 latent verifier 改为建模：

[
z_t = \mathrm{concat}\big(P(h_t^{-}), P(h_t^{+}), P(\Delta h_t), e_{\text{task}}, e_{\text{meta}}\big), \qquad q_t = V_\theta(z_t)
]

这里 (P) 是低维投影，(e_{\text{task}}) 是任务条件嵌入。

## 7.4 关键评测量

**Invariance gap**
[
IG(V)=\mathbb{E}*{(a,b)\in \mathcal{C}*{same}} |V(a)-V(b)|
]

**Semantic sensitivity**
[
SS(V)=\mathbb{E}*{(a,b)\in \mathcal{C}*{flip}} [V(a)-V(b)]
]

一个好的 process verifier 应当同时满足：

* **低 (IG)**：对语义保持改写稳定
* **高 (SS)**：对语义翻转敏感

---

# 8. Research Plan

## 8.1 Data / task / benchmark

### A. 自然语言数学推理

**用途**

* 主 headline 域，检验文本 reasoning 中的 process verification

**数据与基准**

* 训练：公开 step-level math traces + 本地模型自生成推理轨迹
* 开发 / 测试：**ProcessBench**
* frontier OOD：**Hard2Verify** ([arXiv][6])

**为什么选它们**

* ProcessBench 直接测 earliest-error 与 step-level process assessment，是最贴近本问题的标准基准之一。([arXiv][6])
* Hard2Verify 专门测试 open-ended frontier math 上的 step verification，能最大程度暴露“看起来会验证”与“真的会验证”的差别。([arXiv][7])

### B. Lean 形式化推理

**用途**

* 作为 clean-room 域，减少自然语言标签噪声，检验“监督对象”而不是“文本风格”

**数据与基准**

* held-out theorem 集 + 自生成 proof attempts
* tactic-level labels 由 Lean elaboration / compile result 自动给出
* 若需要 outcome-level 辅助，可使用 MiniF2F / ProverBench 风格 held-out 集合 ([OpenReview][8])

**为什么选它们**

* Lean 能直接提供 fine-grained、可执行、可验证的过程反馈，这是自然语言推理中很难得到的。([OpenReview][2])

### C. 新构建数据：CTS（Counterfactual Transition Set）

**目的**

* 不是做一个更大 benchmark，而是做一个**小而锋利**的 stress test

**构建方式**

* 从 math 与 Lean 轨迹中抽取 step instances
* 为每个 step 构造两类 paired variants：

  * **same-semantics**：paraphrase、notation rewrite、verbosity rewrite、等价 tactic rewrite
  * **semantic-flip**：不等号翻转、量词扰动、符号号数反转、错用 lemma、局部条件破坏

**质控**

* Lean 部分由编译器验证
* 数学文本部分用规则检查 + API 辅助改写 + 人工抽样审计
* 首版规模控制在 **10k–20k step pairs**

## 8.2 Method

### 核心方法

**LTV: Task-Conditioned Latent Transition Verifier**

### 输入表示

对步骤 (t)，从层集合 (L={\ell_1,\ell_2,\ell_3}) 提取：

* (h_{t,\ell}^{-})：该步开始前 prefix 末 token 的 hidden state
* (h_{t,\ell}^{+})：该步结束后 prefix 末 token 的 hidden state
* (\Delta h_{t,\ell}=h_{t,\ell}^{+}-h_{t,\ell}^{-})

经低维投影 (P_\ell:\mathbb{R}^{d}\to\mathbb{R}^{256}) 后拼接：

[
z_t = \mathrm{concat}\big(P(h_t^-), P(h_t^+), P(\Delta h_t), e_{\text{task}}, e_{\text{meta}}\big)
]

其中 (e_{\text{meta}}) 包括 step position、trace length bucket 和 domain id。

### 输出

* (q_t^{loc}=V_\theta^{loc}(z_t))：局部步骤正确性
* (q_t^{path}=V_\theta^{path}(z_t))：路径可行性

  * 仅在 Lean 和 answer-checkable 子集上训练；若该头太噪，可降级为附加实验

### 损失函数

[
\mathcal{L}
===========

\mathcal{L}_{loc}

* \lambda \mathcal{L}_{path}
* \mu \mathcal{L}_{same}
* \nu \mathcal{L}_{flip}
* \rho \mathcal{L}_{calib}
  ]

其中：

* (\mathcal{L}_{loc})：局部正确性 BCE
* (\mathcal{L}_{path})：路径可行性 BCE
* (\mathcal{L}_{same})：same-semantics consistency loss
* (\mathcal{L}_{flip})：semantic-flip margin loss
* (\mathcal{L}_{calib})：校准正则项

**初始超参范围**

* (\lambda=0.3\sim0.7)
* (\mu=0.5\sim1.5)
* (\nu=0.2\sim1.0)
* (\rho=0.01\sim0.1)
* AdamW, lr (=5\times10^{-4}\sim10^{-3})
* batch size：2k–8k step instances
* 训练 epoch：10–20，按 dev IG + AUROC 早停

### 训练流程

1. 选定本地 generator，收集或生成 step traces
2. 解析 step boundary，提取 (h_t^{-}, h_t^{+})
3. 生成 same-semantics / semantic-flip 对
4. 构造 (y_t^{loc})，在可执行子集上构造 (y_t^{path})
5. 训练 LTV，并在 dev set 上选模型

### 推理流程

* **Reranking**：对完整轨迹聚合 step scores
* **Pruning**：对低路径可行性分支提前截断
* **Targeted revision**：在第一个低 (q_t^{loc}) 步附近局部重写

**重要约束**
主实验**不依赖生成更长 verifier CoT**。
我们刻意把 verification-time compute 控制住，避免把“监督对象改变”的收益与“测试时多花算力”的收益混在一起。

### 伪代码级描述

1. 输入问题 (x)，由 generator 产生轨迹 (\tau)
2. 对每个 step (t)，提取边界状态 (h_t^{-}, h_t^{+})
3. 计算特征 (z_t=[P(h_t^-),P(h_t^+),P(\Delta h_t),e_{task},e_{meta}])
4. 用 (V_\theta) 预测 (q_t^{loc}, q_t^{path})
5. 用 BCE + consistency + margin + calibration 训练
6. 推理时用 step scores 做 rerank / prune / local revise

### 复杂度与成本

* hidden-state extraction：(O(\text{总生成 token 数}))
* verifier 训练：近似 (O(N_{\text{steps}}\cdot d))
* 额外开销很小，因为只训练小 head，不训练主模型
* 若缓存投影后的 boundary features，而不是全激活，存储成本可大幅下降

**降级说明**
“用 LTV 进一步联合训练 generator（LoRA / RL）”是可选扩展，不应作为主线 novelty；若时间紧，应降级到附加实验或 appendix。

## 8.3 Theoretical / mechanistic analysis

### A. 非正式机制命题

若局部正确性主要由潜在推理状态 (r_t) 决定，而 same-semantics 改写主要改变表面 nuisance (n_t)，则：

* 文本 verifier 必须显式或隐式学会对 (n_t) 不变
* 当训练分布无法覆盖所有 rewrite family 时，text-only verifier 会承受额外 invariance risk
* 如果边界 hidden states 保留了与 (r_t) 相关的充分信息，则 transition-based verifier 在 matched sensitivity 下应能实现更低的 invariance gap

这不是形式证明，而是一个**可直接导出实验预测**的机制框架。

### B. 机制分析不是装饰，而是服务主张

我们会做三类机制分析：

* **Layer sweep**：信号最早在哪些层出现；若 transition signal 出现在中后层且早于完整答案输出，说明模型确实在“内部先知道”
* **Transition vs state**：检验“状态转移”而非“静态状态”是否是核心信息单元
* **Task geometry analysis**：比较 math 与 Lean 的 verifier subspace 相似性，判断 task conditioning 是否必要
* **可选 causal test**：沿 verifier direction 做小幅 forward intervention，观察局部正确 continuation 的概率是否变化

## 8.4 Expected empirical signatures

若 hypothesis 成立，应出现以下经验模式：

* LTV 在 **CTS** 上显著降低 same-semantics invariance gap
* 相对提升在 **Hard2Verify** 上大于在 easy in-domain 上
* **Transition features** 明显强于 post-state-only
* **Task-conditioned** 明显强于 universal probe
* LTV 的优势在 **Lean clean-room** 上更干净、更稳定
* 在 **same budget** 下，LTV 带来更好的 reranking / pruning 效果

---

# 9. Experimental Design

## 9.1 Models

### 主实验模型

* 一个 7B 级本地数学推理模型
* 一个 7B 级 distilled reasoning model
* 一个 14B 级 distilled reasoning model
* 一个 7B 级 Lean prover

**推荐起步实例**

* DeepSeek-R1-Distill-Qwen-7B
* DeepSeek-R1-Distill-Qwen-14B
* DeepSeek-Prover-V2-7B ([Hugging Face][9])

### 辅助模型

* 一个同规模但未显式做 reasoning distillation 的数学模型，用于检验“latent process signal 是否依赖特定后训练路径”
* 一个强 API 模型，仅用于 counterfactual 改写、数据审计或 bounded continuation 辅助，不作为最终 headline judge

### Judge / evaluator

* 优先使用 **可执行评测**：答案检查器、Lean 编译 / tactic validity
* LLM-as-a-judge 只用于辅助，不作为最终依据

## 9.2 Baselines

至少比较以下 5 类强基线：

1. **Discriminative text PRM**

   * 首选：Qwen2.5-Math-PRM-7B
   * 强的原因：这是公开可用、专为 step feedback 设计的强小规模 PRM，并报告了较强的 ProcessBench 表现。([Hugging Face][10])

2. **Generative PRM / verbalized verifier**

   * 首选：ThinkPRM
   * 强的原因：它用极少 process labels 就能做强验证，并且在 matched token budget 下也强调 verification-time reasoning 的优势。([arXiv][11])

3. **RL-trained generative judge**

   * 首选：StepWiser
   * 强的原因：它把 stepwise reward modeling 重新表述为 reasoning task 本身，是最接近“更强文本 judge”的竞争线。([arXiv][12])

4. **Hidden-state probe baselines**

   * linear probe / 2-layer MLP on (h_t^{+}) only
   * 强的原因：这是对“latent signal 是否真的来自 transition 而不是静态 state”的最直接挑战。([arXiv][5])

5. **Matched-budget critic / LLM-as-a-judge**

   * 强的原因：现实中经常是最强 nominal baseline，尤其在开放式题目上

6. **Counterfactual text baseline（必要控制）**

   * text PRM + 与我们相同的 same/flip regularizer
   * 强的原因：它能区分“latent supervision 的收益”与“只是因为加了 invariance regularization”的收益

**最难打败的 baseline**

* **ThinkPRM / StepWiser 家族**，因为它们会把更多 verification-time reasoning 变成优势；这也是为什么本 proposal 必须坚持 **same-budget** 对比，而不是只比 headline accuracy。([arXiv][11])

## 9.3 Main experiments

### Exp 1. Nominal local step verification

* **目的**：建立基本有效性
* **设置**：ProcessBench + Lean holdout
* **变量**：verifier 类型
* **指标**：AUROC、F1、earliest-error accuracy
* **预期现象**：LTV 至少不弱于最强文本 PRM；优势可能在 hard subset 更明显
* **若结果相反**：说明 latent 对象重定义在 nominal 条件下不成立或未被正确实例化

### Exp 2. Frontier / OOD verification

* **目的**：测 hardest regime
* **设置**：Hard2Verify + cross-generator transfer
* **变量**：train/test generator family，difficulty
* **指标**：AUROC、earliest-error accuracy
* **预期现象**：LTV 的相对增益在 Hard2Verify 上大于在 ProcessBench 上
* **若结果相反**：说明收益更像 in-domain fitting，而不是 robustness improvement

### Exp 3. Counterfactual invariance

* **目的**：直接检验“监督对象是否选错”
* **设置**：CTS
* **变量**：same-semantics vs semantic-flip；verifier 类型
* **指标**：IG、SS、matched-SS 下的 IG
* **预期现象**：LTV 在 matched sensitivity 下明显更低 IG
* **若结果相反**：说明文本 verifier 已足够语义化，或 latent states 同样强烈混入 nuisance

### Exp 4. Transition vs single-state vs text-only control

* **目的**：识别核心机制
* **设置**：(h_t^+)-only、((h_t^-,h_t^+,\Delta h_t))、text PRM、text PRM + same regularizer
* **指标**：AUROC、IG、ECE
* **预期现象**：transition features 最强；text-only control 无法完全追平
* **若结果相反**：说明收益可能来自 regularization 而不是对象转移

### Exp 5. Task-conditioning and geometry

* **目的**：检验 universal truth direction 是否足够
* **设置**：math + Lean joint training
* **变量**：global probe vs task-conditioned verifier
* **指标**：cross-task AUROC、ECE、subspace angle / CKA
* **预期现象**：task-conditioned 明显更稳
* **若结果相反**：说明 latent truth geometry 也许比预期更通用

### Exp 6. Fixed-budget utility

* **目的**：检验 measurement 是否能转化成 decision utility
* **设置**：best-of-N reranking、branch pruning、targeted revision
* **变量**：budget、reranker 类型
* **指标**：final answer accuracy、proof success、tokens consumed
* **预期现象**：在相同 token budget 下，LTV 提升 final utility；或在相同 utility 下减少 token
* **若结果相反**：说明它更像一个“好测量器”，还不是“好决策器”

### Exp 7. Lean clean-room

* **目的**：隔离自然语言标签噪声
* **设置**：Lean tactic-level soundness
* **变量**：text-style verifier vs latent verifier
* **指标**：local tactic accuracy、earliest-fail localization
* **预期现象**：LTV 在 Lean 上的机制信号更干净，增益更稳定
* **若结果相反**：说明 formal clean-room 不能提供更强证据，需缩小 claim

### Exp 8. Optional causal intervention

* **目的**：检验 verifier signal 是否只是相关而非因果
* **设置**：沿 positive/negative verifier direction 做小幅 forward intervention
* **指标**：正确 continuation 概率变化
* **预期现象**：存在小但稳定的方向性效应
* **若结果相反**：说明 verifier 更适合作 measurement，不宜过度宣称控制能力

## 9.4 Ablations

关键 ablation 维度：

* layer 选择：early / mid / late
* feature 组成：(h^{-})、(h^{+})、(\Delta h)
* task conditioning：on / off
* same-semantics consistency loss：on / off
* semantic-flip margin loss：on / off
* calibration term：on / off
* step boundary 规则：parser / delimiter / tactic boundary
* 训练数据量：25% / 50% / 100%
* label noise 注入：0 / 10% / 20%

## 9.5 Robustness / stress test

至少做三类：

1. **表面扰动鲁棒性**

   * notation、verbosity、paraphrase、format change

2. **跨模型迁移**

   * 在 generator A 上训练 verifier，在 generator B 上测试

3. **难度与长度分层**

   * easy / medium / hard
   * short / medium / long trace

4. **标签噪声应力测试**

   * 向训练标签中注入可控噪声，比较 LTV 与 text PRM 的退化曲线

## 9.6 Statistical validity

* 所有训练实验至少 **3 个 seed**
* 便宜的 probe / ablation 实验做 **5 个 seed**
* 主要结果报告 **95% bootstrap CI**
* 配对 accuracy 用 **McNemar** 或 paired randomization
* AUROC / ECE 用 paired bootstrap
* CTS 成对样本使用 paired bootstrap，避免把 pair 拆开
* 预先固定：

  * dev / test split
  * model-selection rule
  * compute budget
  * prompt templates
* 不在 test 上做 prompt 修补；避免 cherry-picking

---

# 10. Falsifiable Predictions

## Prediction 1

**Prediction**
在 matched nominal sensitivity 下，LTV 在 CTS 的 same-semantics 对上会显著低于最强文本 PRM / generative judge 的 invariance gap。

**How to test**
在 CTS 上比较 matched-SS 条件下的 IG。

**What failure would imply**
说明 text-based verifier 已经足够语义化，或者 latent representation 仍强烈混入 nuisance。

**How the theory would be revised**
将主张从“监督对象选错”修正为“监督对象可能没错，关键在于显式不变性训练”。

## Prediction 2

**Prediction**
LTV 相对文本 verifier 的增益，在 Hard2Verify 上会大于在 ProcessBench 上。

**How to test**
比较两个 benchmark 上的相对 AUROC / earliest-error 提升。

**What failure would imply**
说明 LTV 的收益不主要来自 OOD robustness，而更可能来自 in-domain regularization。

**How the theory would be revised**
把核心理论从“更接近语义对象”收缩为“更高效的局部表征”。

## Prediction 3

**Prediction**
((h_t^{-}, h_t^{+}, \Delta h_t)) 将显著优于 (h_t^{+})-only；而 text PRM + same regularizer 仍不能完全追平。

**How to test**
做 transition / state-only / text-only-control ablation。

**What failure would imply**
说明关键信号可能是静态 post-state，或收益主要来自 regularization 而非对象重定义。

**How the theory would be revised**
将“state transition hypothesis”修正为“latent state sufficiency hypothesis”。

## Prediction 4

**Prediction**
global universal probe 在 math + Lean 联合训练下会明显弱于 task-conditioned verifier。

**How to test**
比较 cross-task AUROC、ECE 与子空间相似性。

**What failure would imply**
说明存在比预期更统一的 truth-related geometry。

**How the theory would be revised**
将“task-specific subspace”修正为“shared core subspace + task-specific calibration”。

## Prediction 5

**Prediction**
在 Lean clean-room 中，LTV 相对文本 verifier 的优势会更稳定，方差更小。

**How to test**
比较 Lean 与自然语言数学上的 seed variance、IG 和 AUROC。

**What failure would imply**
说明自然语言标签噪声不是主要混杂源，或 formal domain 并未更好隔离对象问题。

**How the theory would be revised**
缩小 claims 的外推范围，不再强调 clean-room 优势。

## Prediction 6

**Prediction**
在相同 token budget 下，LTV 用于 reranking / pruning 将提升 final answer accuracy 或 proof success；或者在相同成功率下降低 token 成本。

**How to test**
固定 budget，比对不同 verifier 的 reranking / pruning utility curve。

**What failure would imply**
说明 LTV 改善了 measurement，但没有改善 downstream decision。

**How the theory would be revised**
把主贡献收缩为“新监督对象与评测视角”，而非“更好的搜索控制器”。

---

# 11. Risks, Failure Modes, and Plan B/C

## 11.1 理论风险

**风险**
hidden states 里编码的是最终答案信号，而不是 step-level local soundness；transition framing 可能过强。

**应对**
优先把 headline claim 放在 local step soundness 和 invariance 上，而不是 path viability 或 full control。

## 11.2 实验风险

**风险**

* step boundary 解析不稳定
* path viability 标签在开放式数学上过噪
* different model families 的 hidden states 不可比

**应对**

* 使用边界 token state，而不是全序列复杂 pooling
* 将 (q^{path}) 限定在 Lean 和 answer-checkable 子集
* 明确把 cross-family transfer 作为 robustness test，而不是主假设前提

## 11.3 Benchmark 风险

**风险**
CTS 可能带入 synthetic artifact，使模型在“识别改写器风格”而非“识别语义变化”。

**应对**

* 多种改写器来源
* Lean compile check
* 人工抽样审计
* 加入自然收集的 human paraphrase 小子集

## 11.4 识别 / 解释风险

**风险**
即使 LTV 更强，也可能只是因为 hidden states 暴露了 generator family 的 shortcut，而不是因为我们真的抓住了“正确监督对象”。

**应对**

* 加入 text PRM + 同样 regularizer 的控制基线
* 做 cross-model transfer
* 做 label-noise injection
* 做 optional causal intervention

## 11.5 工程风险

**风险**
大规模 hidden-state extraction 吞吐与存储压力较高。

**应对**

* 只提取 step boundary 的少数层 states
* 在线投影到 256 维后再缓存
* 优先缓存 features，不缓存全激活

## 11.6 Plan B

如果主假设没有转化为稳定的 utility 提升，但 invariance 结果清晰，则项目转向：

**Plan B：Counterfactual Invariance Stress Test for Process Verifiers**

主叙事变为：

* 当前 process supervision 的主要问题不只是模型弱，而是**评测缺维度**
* 现有 verifier 在 same-semantics / semantic-flip 下暴露系统性缺陷
* LTV 作为 diagnostic tool 证明了“监督对象错位”的可能性

这仍是可发表的 NeurIPS/ICML 风格 measurement + mechanism paper。

## 11.7 Plan C

如果自然语言数学标签与 CTS 构造都过噪，则转向：

**Plan C：Lean clean-room only**

主叙事变为：

* 在 formal theorem proving 中，比较 text-step supervision 与 latent-transition supervision
* 把论文收窄为“在干净 process oracle 下，什么才是正确监督对象”

范围更窄，但机制更干净，仍然具备顶会价值。

---

# 12. Feasibility Under Compute Constraints

## 12.1 模型规模

主线只用：

* 7B 级文本推理模型
* 14B 级文本推理模型
* 7B 级 Lean prover
* 一个小 verifier head

不做任何大规模预训练。主模型默认冻结；必要时只做轻量 LoRA，且 LoRA 不是主线。推荐起步实例可直接从本地可运行的 DeepSeek-R1-Distill-Qwen-7B/14B 与 DeepSeek-Prover-V2-7B 开始。([Hugging Face][9])

## 12.2 训练与推理成本估计

**核心主线总预算**：约 **50–80 GPU-days**
**包含可选扩展**：约 **80–110 GPU-days**

粗分解：

* hidden-state extraction（文本域）：12–18 GPU-days
* hidden-state extraction（Lean 域）：8–12 GPU-days
* verifier 训练 + sweep：4–8 GPU-days
* reranking / pruning / robustness eval：12–20 GPU-days
* optional intervention / LoRA：10–20 GPU-days

## 12.3 显存与并行策略

* 7B 模型：1×80GB 可跑，2×80GB 更稳
* 14B 模型：建议 2×80GB tensor parallel
* verifier head 训练：1×80GB 足够
* 机器 A：文本域 extraction + main eval
* 机器 B：Lean generation / compile / ablation

## 12.4 数据生成与 API 使用

API 预算只用在：

* counterfactual 改写候选生成
* 小规模审计
* bounded continuation oracle 的辅助部分

不会把闭源 API 作为最终 headline metric 的唯一来源。
这样做的好处是：即使 API 不可复用，主实验仍可由本地模型和可执行 checkers 复现。

## 12.5 为什么这在给定资源下可做

* 不训练大模型，只训练 verifier head
* 不依赖数千卡周级别 RL
* 不依赖长 verifier CoT
* 只抽取 step boundary 的少量层 states
* 缓存的是压缩后 features，而不是全激活

因此，这个 proposal 在 16×80GB A800 的资源约束下是**明显可执行**的。

---

# 13. Reproducibility and Engineering Plan

## 13.1 配置管理

* Hydra / YAML 管理所有实验配置
* 每个 run 记录：

  * model id
  * tokenizer version
  * layer set
  * projection dim
  * seed
  * decode budget
  * CTS version

## 13.2 实验记录

* W&B 或 MLflow 记录训练曲线、AUROC、IG、SS、ECE、token cost
* 每个 headline result 保存 bootstrap distribution

## 13.3 数据版本

* 原始 traces、step boundaries、CTS pairs、Lean compile logs 分开版本化
* 使用 DVC 或等价方案记录数据 revision
* 记录 counterfactual 生成 prompt 与生成 seed

## 13.4 随机种子

* 固定 3 个主 seed
* 便宜实验扩展到 5 个 seed
* 报告 seed mean ± CI，不报单次最优

## 13.5 Checkpoint 策略

* verifier 每个 epoch 存 checkpoint
* 只按预注册的 dev 指标选“best checkpoint”
* 不在 test 上反复试 checkpoint

## 13.6 评测脚本

* ProcessBench / Hard2Verify / Lean evaluation scripts 独立封装
* CTS 评测脚本单独发布
* paired bootstrap 与显著性检验脚本一并开源

## 13.7 建议发布的关键 artifacts

* step parser
* boundary hidden-state extractor
* CTS 构造脚本与审计规则
* verifier training code
* evaluation harness
* 预处理后的压缩 features（若许可证允许）
* 论文所用全部配置文件和结果 JSON

---

# 14. Timeline and Milestones

## Week 1

* 搭建 step parser 与 hidden-state extraction pipeline
* 跑通一个 7B 模型的边界状态缓存
* 完成一个最简 linear probe baseline

## Week 2

* 跑 ProcessBench / Lean 的 nominal baselines
* 构建 CTS v0
* 得到第一版 IG / SS 指标

## Week 3：最小闭环 + go/no-go

* 训练第一版 LTV
* 判定是否继续主线

**建议的 go/no-go 标准**

* dev 上 IG 至少优于最强 text baseline 一个明显量级，或
* earliest-error accuracy 至少提升 3–5 个点，或
* same-budget reranking 已出现稳定正增益

若三者都没有，立刻转 Plan B。

## Week 4–5

* 做 transition vs state、task-conditioning、loss ablations
* 清理 path-viability 头的可行子集

## Week 6

* 跑 Hard2Verify 与 cross-model transfer
* 形成主结果表初稿

## Week 7

* 跑 Lean clean-room
* 做 label-noise injection 与 robustness 分层

## Week 8

* 跑 fixed-budget reranking / pruning
* 可选：做 causal intervention

## Week 9

* 重跑关键结果
* 统一统计检验与图表

## Week 10

* 写作、附录、复现实验说明
* 整理 artifacts 与 release checklist

---

# 15. Paper Framing

## 15.1 Best-paper style one-sentence pitch

**The field has been supervising the wrong object: process supervision should target latent state transitions, not the surface text of chain-of-thought steps.**

## 15.2 Contribution bullets

* 提出一个新的问题定义：process supervision 的正确对象是 **latent state transition**，而非 textual step
* 提出 **task-conditioned latent transition verifier**，在不增加验证时长的前提下读取局部过程信号
* 提出 **counterfactual invariance / semantic sensitivity** 评测透镜，区分“学到语义”与“学到表面”
* 在 **自然语言数学 + Lean formal reasoning** 双域上做机制验证，区分监督对象与标签噪声
* 给出一组**可证伪预测**，把“process supervision 为什么重要却又脆弱”从经验现象推进到机制命题

## 15.3 Figure plan

1. **Figure 1：核心概念图**

   * 文本步骤只是潜在推理状态的表面实现
   * 显示 text supervision 与 latent supervision 的差别

2. **Figure 2：CTS 评测设计图**

   * same-semantics vs semantic-flip
   * 解释为什么 nominal accuracy 不够

3. **Figure 3：主结果表 / 图**

   * ProcessBench、Hard2Verify、Lean 上的 AUROC / earliest-error

4. **Figure 4：Invariance vs Sensitivity 曲线**

   * 比较 LTV 与 text PRM / generative judge

5. **Figure 5：Mechanism ablation**

   * transition vs state-only
   * task-conditioned vs universal
   * layer sweep

6. **Figure 6：Same-budget utility 曲线**

   * reranking / pruning 下的 final accuracy 或 proof success vs token budget

## 15.4 Related work organization

建议按“问题对象”而不是按“模型名字”组织 related work：

1. **Process supervision as textual verification**

   * Let’s Verify、ProcessBench、ThinkPRM、StepWiser

2. **Internal-state signals for correctness, behavior, and calibration**

   * hidden-state probing、behavior prediction、truth geometry

3. **Formal systems as process oracles**

   * Lean-STaR、DeepSeek-Prover-V2、Process-Verified RL

4. **What current evaluation misses**

   * nominal step accuracy 的局限
   * 为什么需要 counterfactual invariance lens

---

这份 proposal 的关键不在于“latent 比 text 更高级”，而在于它把一个更根本的问题做成了可执行、可证伪的研究计划：**如果 process supervision 一直不够稳，也许不是因为我们还没把文本步骤打分做得足够好，而是因为文本步骤从一开始就不是应该被监督的对象。**

[1]: https://arxiv.org/abs/2305.20050 "https://arxiv.org/abs/2305.20050"
[2]: https://openreview.net/forum?id=SOWZ59UyNc "https://openreview.net/forum?id=SOWZ59UyNc"
[3]: https://arxiv.org/abs/2310.01798 "https://arxiv.org/abs/2310.01798"
[4]: https://openreview.net/pdf/91262ee1de3d030de017da047257e50d6759a959.pdf "https://openreview.net/pdf/91262ee1de3d030de017da047257e50d6759a959.pdf"
[5]: https://arxiv.org/abs/2504.05419 "https://arxiv.org/abs/2504.05419"
[6]: https://arxiv.org/abs/2412.06559 "https://arxiv.org/abs/2412.06559"
[7]: https://arxiv.org/abs/2510.13744 "https://arxiv.org/abs/2510.13744"
[8]: https://openreview.net/pdf?id=P00k4DFaXF "https://openreview.net/pdf?id=P00k4DFaXF"
[9]: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B "https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
[10]: https://huggingface.co/Qwen/Qwen2.5-Math-PRM-7B "https://huggingface.co/Qwen/Qwen2.5-Math-PRM-7B"
[11]: https://arxiv.org/abs/2504.16828 "https://arxiv.org/abs/2504.16828"
[12]: https://arxiv.org/abs/2508.19229 "https://arxiv.org/abs/2508.19229"
