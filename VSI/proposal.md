# 1. Title

**主标题**
**Beyond Difficulty: Verification Structure as the Hidden Axis of Trainable Reasoning**

**备选标题 1**
**What Makes Reasoning Trainable? Verification Structure in Language Model Learning and Monitoring**

**备选标题 2**
**From Answers to Certificates: A Proposal for Studying Verification Structure in LLM Reasoning**

**备选标题 3**
**When Verifiers Work—and When They Don’t: Certifiability as a New Lens on Reasoning Models**

---

# 2. One-Paragraph Thesis Summary

这份 proposal 要解决的问题是：**为什么最近“reasoning 模型”的显著进展主要集中在数学、代码、定理证明等任务上，而没有稳定地外推成一种普适的“抽象推理跃迁”？** 我们的核心主张是，决定 verifier-based 训练、process supervision、自纠错和 CoT 监控何时有效的关键因素，往往不是任务本身有多难，而是任务是否具有良好的 **verification structure**：中间过程能否被较早、较可靠、较不易被利用地验证。为此，我们将提出一个可形式化、可测量、可证伪的概念框架，用 **VSI (Verification Structure Index)** 拆解并量化 certificate horizon、local ambiguity 和 exploitability；构建受控 benchmark **CertBench** 将“问题难度”和“可验证结构”解耦；并设计一个预算受限的训练策略 **SAVR** 作为 operational demo，验证该原则能否预测并改善 RLVR、PRM 和 CoT monitoring 的成败。如果结论成立，这项工作将把社区对 reasoning 的理解，从“模型会不会想”推进到“**什么样的问题结构使推理可学、可控、可监测**”。

---

# 3. Abstract

近一年，语言模型在数学、代码与形式化证明上的 reasoning 进展十分显著：自纠错 RL、verifier-assisted generation、过程奖励建模以及定理证明中的强化学习都取得了强结果；但与此同时，关于 RL 是否真正扩展了 base model 的推理边界、CoT 是否 faithful、以及 benchmark 是否已被污染的负结果也在迅速累积。现有研究仍主要把这些现象分别讨论：有的将成功归因于更强的后训练范式，有的将失败归因于 CoT 不忠实或 evaluator 不可靠，却缺少一个统一解释，说明**为什么某些任务上 verifier 有用，而另一些任务上它只会产生脆弱代理、奖励黑客或表面进步**。本 proposal 的核心假设是：近期 reasoning 进展的隐藏变量并非单纯“任务难度”，而是任务的 **verification structure**——即正确性证据出现得多早、过程是否存在大量语义等价但 token-level 不同的路径、以及弱 verifier 被策略性利用的空间有多大。我们将提出一个形式化指标 VSI，将 verification structure 分解为 certificate horizon、local ambiguity 与 exploitability，并构建一个新 benchmark CertBench，在固定求解难度下独立操纵这些因素。基于该框架，我们将系统比较 outcome-only RLVR、process reward、self-correction 与 verifier-assisted decoding，检验 VSI 是否比传统 difficulty 更能预测训练收益、reward hacking 与 CoT monitorability。作为方法层面的证明性实例，我们还将提出一种预算受限的 selective verification 策略 SAVR，用以按 VSI 动态分配 outcome / process / strong verification。该项目的目标不是再提出一个工程 recipe，而是建立一个新的研究对象与评测透镜：**reasoning 的可训练性与可监控性取决于 verification structure**。如果成功，它将改变社区设计 benchmark、reward、verifier 和 post-training 范式的原则。 ([OpenReview][1])

---

# 4. Motivation and Problem Statement

当前领域最值得认真对待的张力是：**reasoning 的“正结果”与“负结果”正在同时增长。** 一方面，SCoRe 表明在线 RL 能显著提升自纠错；verifier theory 开始给出 PAC 学习和 query complexity 框架；AlphaProof 则在 Lean 这一强可验证环境中展示了 RL + search 的威力。另一方面，近期研究也指出：当前 RLVR 更像是在提高采样效率，而未必诱导出超越 base model 支持集的新推理；而 CoT faithfulness 在 reasoning model 上依然偏低，并且在更难任务上进一步下降。换言之，社区已经看到了 reasoning 训练为何“有时很有用”，也看到了它为何“并不总是代表真正的机制跃迁”，但还没有一个统一变量把这两种现象接起来。 ([OpenReview][1])

主流范式的不足在于，它们往往把两个问题混在一起：
第一，**问题本身有多难**；第二，**问题的正确性在过程中有多容易被验证**。
当前很多 benchmark 报告的是最终准确率，却没有显式刻画 verifier 信号的结构；而动态 benchmark 的兴起恰恰说明，仅靠静态分数已经很难分辨“真能力”与“污染 / 过拟合 / evaluator 偏差”。LiveBench 通过持续更新与客观打分降低污染风险；MathArena 则用流式竞赛题和 proof-writing 评测指出传统数学 benchmark 已出现明显污染信号；OpenAI 在 2026 年更进一步公开表示 SWE-bench Verified 已越来越不适合作为前沿 coding 能力的度量。评测危机说明：**我们不仅需要更难的问题，还需要更正确的测量坐标系。** ([OpenReview][2])

本 proposal 真正想问的研究问题不是“如何再做一个更强的 RLVR / PRM 方法”，而是：
**什么样的任务结构，使 verifier-based 学习与监控真正有信息价值？什么样的任务结构，使它们只是在放大脆弱代理信号？**
如果这个问题被回答，影响会超出一个方法点数提升：

* 它会改变我们如何设计 reasoning benchmark；
* 改变我们何时应该相信 process reward / self-correction；
* 改变我们如何理解 CoT 监控与 faithfulness 的边界；
* 也可能改变社区对“reasoning progress”本身的定义。

---

# 5. Core Hypothesis and Research Claims

## 主假设

### **H0: Verification Structure Hypothesis**

* **Claim**：在 verifier-based 训练、过程监督和 CoT 监控中，性能提升、monitorability 与 reward hacking 风险的主要解释变量，不是原始任务难度本身，而是任务的 **verification structure**。
* **Intuition**：如果正确性证据出现得早、过程歧义小、弱 verifier 难以被利用，那么过程信号就更接近“真监督”；反之，同样难度的任务也可能因为证据太晚、过程歧义太大或 verifier 易被钻空子而使 RL/PRM 退化为 noisy optimization。
* **Testability**：构造 difficulty-matched 任务对，显式操纵 verification structure；比较 VSI 与传统 difficulty 对训练收益、faithfulness 与 exploitability 的解释力。

## 子假设 / 研究命题

### **H1: Certificate Horizon Claim**

* **Claim**：在其他条件匹配时，**certificate horizon 越短**，process supervision 和 verifier-guided training 的收益越高。
* **Intuition**：若中间前缀已含有足够的正确性证据，则过程奖励不再是稀疏噪声。
* **Testability**：在相同求解深度与 base difficulty 下，仅改变“前缀何时可判定最终可达性”，比较 PRM / RLVR 增益曲线。

### **H2: Ambiguity Claim**

* **Claim**：在其他条件匹配时，**local ambiguity 越高**，token/step-level 过程奖励越容易退化，且其退化幅度大于 outcome-only reward。
* **Intuition**：当存在多条语义等价但表面不同的正确轨迹时，canonical process label 会变成系统性标签噪声。
* **Testability**：通过等价重写生成多条正确过程，比较弱 verifier 与强 verifier 的一致性，以及 PRM 与 ORM 的收益差。

### **H3: Exploitability Claim**

* **Claim**：在其他条件匹配时，**exploitability 越高**，优化 weak verifier 越容易产生 reward gap 与隐藏式错误；而 selective routing 到 stronger verification 能显著抑制该现象。
* **Intuition**：不是所有 verifier 都是“奖励函数”，有些只是在给策略暴露 exploitable interface。
* **Testability**：在不完备测试、弱 judge 或局部规则 checker 下，比较 weak/strong verifier gap 与实际正确率。

### **H4: Monitorability Claim**

* **Claim**：即使最终准确率相近，**VSI 更高** 的任务其 CoT reveal rate / faithfulness 会更低。
* **Intuition**：当验证结构差时，模型更可能在表面上输出合理解释，而真实决策依赖未显化的捷径、暗示或隐式状态。
* **Testability**：在 hint-injection / hidden shortcut 设置中测 CoT verbalization 与 counterfactual faithfulness。

### **H5: Transfer Claim**

* **Claim**：在受控 synthetic 任务上测得的 VSI 规律，能够迁移到真实锚点领域：Lean/可执行代码类任务应更接近低 VSI 区，而开放式、长依赖、状态隐含任务应更接近高 VSI 区。
* **Intuition**：若 verification structure 真是核心变量，它不应只存在于玩具任务。
* **Testability**：将 MathArena objective 子集、LiveBench objective 子集、Lean 小规模证明集和状态追踪任务投影到同一 phase diagram 中。

---

# 6. Why This Proposal is Novel

## 6.1 Closest prior work

**第一类：RLVR / self-correction / verifier-guided reasoning**
代表工作包括 SCoRe，以及对 RLVR 边界的系统性反思。SCoRe 证明在线 RL 可以显著提升自纠错，但近期研究也指出，当前 RLVR 更多提高 sampling efficiency，而未必扩展出新的 reasoning pattern。 ([OpenReview][1])

**第二类：verifier 理论与 process reward / reward reasoning**
近期已有 PAC 式 verifier 学习框架、verifier-assisted generation 的 query complexity 理论，以及 ThinkPRM、P-GRPO、RRM/RM-R1 这类过程奖励与 reasoning reward 的新范式。它们共同表明 verifier / reward 设计正在成为 post-training 的核心问题。 ([OpenReview][3])

**第三类：faithfulness / monitorability / evaluation crisis**
Anthropic 的 CoT faithfulness 研究、CoT in the Wild、Walk the Talk，以及动态 benchmark 方向（LiveBench、MathArena）共同指出：accuracy 不等于 faithful reasoning，公开静态 benchmark 也越来越难可靠度量前沿能力。 ([Anthropic 品牌门户][4])

## 6.2 What they achieved

这些工作已经分别解决了三个重要子问题：

* 证明 verifier-based RL 和 self-correction 可以在特定任务上显著有效；
* 为 verifier 的可学习性与推理辅助效应提供了理论支架；
* 揭示了 CoT 不总是 faithful、以及 benchmark 污染会扭曲能力测量。 ([OpenReview][1])

## 6.3 What is still missing

缺失的不是“更多 verifier 方法”，而是一个更高层的问题定义：
**为什么这些方法只在某些任务结构上稳定有效？**
现有工作大多把“任务难度”“verifier 质量”“过程标签密度”“faithfulness”“benchmark 污染”分开讨论，缺少一个统一的机制变量来解释它们何时同向、何时冲突。于是社区很容易把“在强可验证任务上的进步”误解成“对任意复杂推理的通用跃迁”。这正是 proposal 的切入点。

## 6.4 What is irreducibly new here

本 proposal 的不可替代贡献不是“更系统地比较已有方法”，而是以下四者的组合：

1. **新问题定义**：把 reasoning 的核心研究对象从“任务有多难”转为“任务是否具有良好的 verification structure”。
2. **新机制框架**：把 verification structure 分解为 certificate horizon、local ambiguity、exploitability 三个可干预机制变量。
3. **新评测视角**：构建一个能把 difficulty 与 verification structure 解耦的 benchmark，而非再发一个静态数据集。
4. **新方法原则**：提出 SAVR 作为原则的 operationalization，证明“不是所有任务都值得同样的过程监督和 verifier 开销”。

**明确说明**：如果这项工作最后只剩“新 benchmark + 一个 routing heuristic”，那 novelty 会降到 datasets / empirical study 级别，不足以支撑强顶会主叙事。它必须以“**新原则 + 可证伪预测 + 机制解释**”为核心，benchmark 和方法只是证据链的一部分。

---

# 7. Conceptual Framework

## 7.1 研究对象

* 任务：(x \sim \mathcal{X})
* 推理轨迹：(\tau = (s_1, s_2, \dots, s_T))
* 最终答案：(y)
* 最终正确性：(c(x,\tau) \in {0,1})

## 7.2 机制变量

### **(1) Difficulty (D(x))**

* 任务本身的求解难度
* 可由 base model accuracy、最短解深度、搜索分支因子、或人类/solver 复杂度近似

### **(2) Certificate Horizon (H(x,\tau))**

* 定义：在前缀 (\tau_{\le t}) 上，最早何时能以高置信判定最终正确/不可达
* 归一化到 ([0,1])，越大表示证据越晚出现

### **(3) Local Ambiguity (A(x,\tau))**

* 定义：对语义等价重写集合 (\tilde{\tau}\sim\mathcal{E}(\tau))，弱 verifier 在这些正确轨迹上的不一致率
* 越大表示过程监督越容易被表面形式噪声污染

### **(4) Exploitability (E(x))**

* 定义：策略优化 weak verifier 后，其评分与 strong verifier / oracle 评分的期望偏差
* 越大表示弱 verifier 越容易被策略性利用

## 7.3 观测量

* 最终准确率 (Acc)
* 训练增益 (\Delta Acc)
* weak-strong reward gap (G)
* CoT reveal / faithfulness (R)
* verifier cost (C_v)
* reward hacking 率 (Hack)

## 7.4 干预变量

* 训练范式 (I \in {\text{SFT}, \text{ORM/RLVR}, \text{PRM}, \text{Self-Correction}, \text{SAVR}})
* verifier 强度 (V \in {\text{weak}, \text{strong}, \text{hybrid}})
* 优化压力 (\lambda)
* 等价重写扰动 (\mathcal{E})

## 7.5 结果变量

* 训练收益：(\Delta Acc)
* 预算归一化收益：(\Delta Acc / C_v)
* 监控有效性：(R)
* 稳健性：跨 verifier / 跨重写 / 跨 family 泛化

## 7.6 核心指标

定义
[
\text{VSI}(x,\tau) = w_H \hat H(x,\tau) + w_A \hat A(x,\tau) + w_E \hat E(x)
]

其中 (w_H,w_A,w_E) 由开发集确定，或先使用等权设置进行主分析，再在附录报告学习权重结果。

## 7.7 因果图（文字版）

* (D) 影响 base accuracy
* (H,A,E) 影响 verifier-based 信号的信息质量
* 干预 (I,V,\lambda) 改变策略如何利用这些信号
* 结果表现为 (\Delta Acc, G, R, Hack)

更具体地说：

[
(D,H,A,E) \rightarrow \text{signal quality} \rightarrow (\Delta Acc, R, Hack)
]

proposal 的核心不是“提出一个万能训练法”，而是证明：
**当我们把 (D) 与 (H/A/E) 分开后，reasoning 训练与监控的许多正负结果会落到同一坐标系中。**

---

# 8. Research Plan

## 8.1 Data / task / benchmark

### A. 主 benchmark：**CertBench**

核心原则：**固定求解难度，独立操纵 verification structure。**

#### 任务家族设计

1. **Early-certifiable family**

   * 正确性证据较早出现
   * 例：可执行状态更新、精确算术、可逐步检查的程序生成

2. **Delayed-certifiable family**

   * 只有较晚前缀或最终结果才能验证
   * 例：长依赖隐藏状态、延迟暴露错误的组合推理

3. **High-ambiguity family**

   * 存在多条语义等价但 token-level 差异显著的正确轨迹
   * 例：代数变形、程序重构、等价 tactic 序列

4. **High-exploitability family**

   * weak verifier 容易被利用
   * 例：不完备单元测试、局部规则 judge、易被模式匹配欺骗的判别器

#### benchmark 构建方式

* 程序化生成器生成实例
* 用 exact solver / symbolic checker 提供 strong oracle
* 用 partial tests / model-based judge / 局部规则提供 weak verifier
* 通过 base model accuracy、最短解长度、搜索分支因子匹配 difficulty
* 只保留难度相近但 (H/A/E) 差异显著的 paired instances

### B. 真实锚点任务

1. **MathArena objective / proof-writing 子集**
   用于验证在低污染、动态数学任务中的外推性。MathArena 明确强调流式竞赛题、proof-writing 和对 AIME 2024 的污染迹象分析。 ([OpenReview][5])

2. **LiveBench objective math / coding / reasoning 子集**
   用于验证在月更、客观打分、污染受限条件下的外推性。 ([OpenReview][2])

3. **Lean 小规模证明子集**
   用于强可验证 regime 的锚定。AlphaProof 证明了 Lean 类环境是 reasoning + RL 的高信号区。 ([Nature][6])

### C. 不作为主评测的方向

* **RefactorBench / 全功能 code agent**：高价值，但工程与环境噪声重，容易冲淡主叙事；建议作为附加实验或 follow-up，而不是主证据链。
* **开放式写作 / 无客观答案任务**：更适合作为边界讨论，不适合作为主验证场。

## 8.2 Method

### 核心方法

proposal 的方法部分分两层：

#### 层 1：**测量层**

为每个任务/轨迹估计

* (D): 难度
* (H): certificate horizon
* (A): ambiguity
* (E): exploitability
* (VSI): 合成指标

#### 层 2：**干预层**

比较不同训练/推理范式在不同 VSI 区域的效果，并提出 **SAVR (Selective Adaptive Verification Routing)** 作为原则化 demo。

### SAVR 的直觉

* 低 VSI：weak verifier 或 outcome reward 已足够，没必要重 verifier
* 中 VSI：应加入稀疏前缀检查或 success-conditioned process reward
* 高 VSI：应减少对弱过程信号的优化，更多使用 strong verification、拒绝更新或转入 rejection buffer

### 训练流程

1. 用正确答案或正确轨迹做轻量 SFT warm start
2. rollout 生成多条轨迹
3. 用 strong / weak verifier + 等价重写估计 (H,A,E)
4. 计算 VSI
5. 依据 VSI 选择：

   * outcome-only reward
   * process reward
   * strong verification
   * skip / reject update
6. 用 GRPO/PPO 风格目标更新策略

### 推理流程

* 评测时统一采用固定采样预算
* 分别比较

  * greedy / pass@k
  * verifier-assisted reranking
  * SAVR-trained policy

### 伪代码级描述

```text
for each task x in batch:
    sample trajectories τ1...τK from πθ
    for each τ:
        compute weak reward rw
        estimate H via prefix-certifiability
        estimate A via equivalent-rewrite disagreement
        estimate E via weak-strong reward gap or predicted exploitability
        VSI = wH*H + wA*A + wE*E

        if VSI < η1:
            reward = rw
        elif η1 <= VSI < η2:
            reward = rw + λp * sparse_process_checks
        else:
            reward = strong_verifier_score - γ * exploitability_penalty
            if verifier uncertainty high:
                skip update or send to rejection buffer

update policy with GRPO/PPO objective + KL regularization
```

### 复杂度

若标准 RLVR 代价约为 (O(BK)) verifier calls，则 SAVR 代价为：

[
O(BK + BK\cdot M + \rho BK \cdot C_{\text{strong}})
]

其中：

* (M) = 等价重写数
* (\rho) = 高 VSI 样本比例
* (C_{\text{strong}}) = strong verifier 单次成本

这保证 strong verification 只在最需要的区域触发。

## 8.3 Theoretical / mechanistic analysis

### 命题 1：Prefix-certifiability lower bound

若在前 (t < h) 步，前缀与最终正确性的条件互信息接近 0，则任何 prefix-level reward 在该区间都近似为噪声监督。
**作用**：解释为什么某些任务上 process reward 不会比 outcome reward 更好。

### 命题 2：Ambiguity-induced irreducible noise

若存在大量 token-distinct 但语义等价的正确过程，而过程标签绑定 canonical path，则 step-level labeling 存在不可约噪声。
**作用**：解释 PRM 在高歧义任务上为何退化。

### 命题 3：Exploitability gap

当 weak verifier 与 oracle 的一致性只在静态分布上成立时，策略优化可放大其盲点，从而产生训练分数与真实正确率的系统偏离。
**作用**：解释 reward hacking / obfuscation 风险，而不是把它们当作孤立的安全问题。近期监控研究也表明，把 CoT monitor 直接纳入强优化目标可能诱导 obfuscated reward hacking。 ([OpenAI][7])

## 8.4 Expected empirical signatures

如果主假设成立，应出现以下模式：

* 在 difficulty 匹配条件下，**VSI 比 difficulty 更能解释 (\Delta Acc)**
* 低 (H) 任务中，PRM / prefix checks 增益更大
* 高 (A) 任务中，step-level PRM 更容易退化
* 高 (E) 任务中，weak verifier reward 与真实正确率明显脱钩
* 高 VSI 区域中，CoT reveal / faithfulness 更低
* Lean / 可执行代码更靠近低 VSI 区域，开放长依赖任务更靠近高 VSI 区域

---

# 9. Experimental Design

## 9.1 Models

### 主实验模型

* **1.5B dense LM**
* **3B dense LM**
* **7B dense LM（确认性实验）**

选择理由：

* 足以支持 SFT、LoRA/QLoRA-RL、过程奖励实验
* 能在 16×80GB A800 下做多 seed、多条件比较
* 避免将结论建立在“超大模型才成立”上

### 辅助模型

* 小型 prefix verifier / classifier
* weak model-based verifier
* strong API model 仅用于少量语义重写、faithfulness 审核和误差分析

### Judge / evaluator

* **主指标必须以 objective scoring 为主**

  * symbolic oracle
  * exact execution
  * hidden full tests
  * Lean checker
* LLM judge 仅用于辅助分析，不作为主结论依据
  这点与 LiveBench 的设计原则一致，也能避免 judge bias。 ([OpenReview][2])

## 9.2 Baselines

1. **SFT-only**

   * 最基本对照
   * 验证 gains 是否真的来自 verifier-based training

2. **Outcome-only RLVR / GRPO**

   * 必须比较的强基线
   * 当前 reasoning post-training 的默认范式之一；近期工作也专门质疑它是否超出 base model 能力边界。 ([OpenReview][8])

3. **ThinkPRM-style generative PRM**

   * 代表高质量 process reward 建模路线
   * 数据效率和 step verification 都很强。 ([OpenReview][9])

4. **P-GRPO / success-conditioned process reward**

   * 代表“只在成功结果上奖励过程”的更稳健路线
   * 是本 proposal 最难打败的方法类之一。 ([OpenReview][10])

5. **Always-strong-verifier**

   * 在相同 verifier budget 下对所有样本都调用强 verifier
   * 这是 **最难打败的 baseline**：如果 selective routing 没有额外价值，它应当支配 SAVR

**可选附加 baseline（特定子任务）**

* **SCoRe-style self-correction RL**
* **Best-of-N + strong verifier reranking**

## 9.3 Main experiments

| 实验                                        | 目的                              | 设置                                         | 变量                         | 指标                               | 预期现象                                                  | 若结果相反说明什么                                      |
| ----------------------------------------- | ------------------------------- | ------------------------------------------ | -------------------------- | -------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| **E1** Difficulty-matched horizon test    | 检验 (H) 是否独立影响训练收益               | 配对 synthetic tasks，仅改证书出现时间                | (H)                        | (\Delta Acc), learning curve     | 低 (H) 显著更利于 PRM/RLVR                                  | 说明 H 不是关键变量，或测量方式不对                            |
| **E2** Ambiguity stress test              | 检验 (A) 对 step reward 的破坏        | 多个语义等价正确过程                                 | (A)                        | verifier disagreement, PRM gain  | 高 (A) 下 PRM 退化大于 ORM                                  | 说明 ambiguity 不是主导噪声源                           |
| **E3** Exploitability test                | 测试 weak verifier 是否可被利用         | partial tests / weak judge / hidden oracle | (E), optimization pressure | weak-strong gap, Hack rate       | 高 (E) 下弱奖励显著脱钩                                        | 说明 exploitability 或 weak verifier 构造过弱         |
| **E4** Predictive law test                | 比较 VSI 与 difficulty 的解释力        | 跨全部 synthetic family                       | VSI, D                     | mixed-effects (R^2), effect size | VSI 优于 D 解释 (\Delta Acc) / (R) / Hack                 | 说明框架未优于传统 difficulty                           |
| **E5** SAVR equal-budget comparison       | 检验 selective verification 是否有价值 | 固定总 verifier budget                        | training regime            | Acc, Acc/cost                    | SAVR 优于 outcome-only / always-process / always-strong | 说明 routing 没有额外信息价值                            |
| **E6** Faithfulness / monitorability test | 检验 VSI 与 CoT 监控关系               | hint injection / hidden shortcut           | VSI                        | reveal rate, causal faithfulness | 高 VSI 下 reveal rate 更低                                | 说明 monitorability 可能独立于 verification structure |
| **E7** Real-anchor transfer               | 验证 synthetic 规律能否迁移             | MathArena / LiveBench / Lean 子集            | domain                     | rank correlation, transfer slope | formal/executable 任务更接近低 VSI 区                        | 说明理论只适用于受控环境                                   |

## 9.4 Ablations

关键 ablation 维度：

* VSI 组件：只用 (H) / 只用 (A) / 只用 (E) / 全部
* difficulty matching 的严格程度
* weak verifier 类型：规则型 vs 小模型 judge
* strong verifier 强度
* SAVR 阈值 (\eta_1,\eta_2)
* verifier budget
* rollout 数 (K)
* rewrite 数 (M)
* 模型规模：1.5B / 3B / 7B

**建议降级到 appendix 的 ablation**

* RL 算法细节的大量替换（GRPO vs PPO 的全套网格）
* 过细的 decoding trick ablation
  这些不应成为主论文叙事中心。

## 9.5 Robustness / stress test

至少做以下三类：

1. **Rewrite robustness**

   * 对正确轨迹做语义等价重写
   * 检验 VSI 与 verifier 判断是否稳定

2. **Verifier swap robustness**

   * 更换 weak verifier / strong verifier 实现
   * 检验结论是否依赖单个 judge

3. **Distribution shift robustness**

   * 训练于部分 synthetic families，测试于 hold-out family 和新近真实题目
   * 检验规律是否能跨 family 外推

4. **Optimization pressure scaling**

   * 改变 RL 强度 / update 步数
   * 观察 exploitability 与 obfuscation 是否加剧

## 9.6 Statistical validity

* **Seeds**

  * synthetic 核心实验：5 seeds
  * 3B/7B 与真实锚点实验：3 seeds
* **置信区间**

  * 95% bootstrap CI
  * paired bootstrap 比较主要方法
* **显著性与建模**

  * mixed-effects regression
  * family 作为 random effect
  * 同时报告 effect size 与 p-value
* **避免 cherry-picking**

  * 预先固定主指标：(\Delta Acc)、Acc/cost、weak-strong gap、reveal rate
  * 开发集只用于权重与阈值确定
  * 主文报告所有 family 的 aggregate 与 per-family 结果
  * 不按最佳 seed 报告

---

# 10. Falsifiable Predictions

## **Prediction 1**

* **Prediction**：在 difficulty-matched 条件下，VSI 对训练收益的解释力显著高于传统 difficulty。
* **How to test**：对全部 synthetic 实验拟合 (\Delta Acc \sim VSI + D + \text{model size} + \text{family random effect})。
* **What failure would imply**：核心框架没有抓住决定性变量；reasoning gain 仍主要由传统难度或其他未建模因素决定。
* **How the theory would be revised**：把 thesis 从“VSI 是主轴”修正为“VSI 只是特定 verifier-based setting 的次级调节变量”，并补充遗漏轴，如 search branching 或 solver support。

## **Prediction 2**

* **Prediction**：低 certificate horizon 任务上，PRM / prefix-level verification 的收益显著高于高 certificate horizon 任务。
* **How to test**：仅操纵 (H)，固定 base accuracy 与 solution depth。
* **What failure would imply**：prefix-certifiability 不是过程奖励有效性的关键，或我们对 (H) 的 operationalization 错了。
* **How the theory would be revised**：将 (H) 从 token-prefix 改为 latent-state certifiability，而不是表面推理步前缀。

## **Prediction 3**

* **Prediction**：高 ambiguity 任务上，process reward 相比 outcome reward 的相对优势会缩小，甚至反转。
* **How to test**：生成语义等价但 token-level 差异大的多条正确轨迹，比较 ORM/PRM/SAVR。
* **What failure would imply**：过程监督退化并非主要由等价路径噪声引起。
* **How the theory would be revised**：把 ambiguity 进一步拆分为 syntactic ambiguity 与 semantic branching，检查真正起作用的是哪一种。

## **Prediction 4**

* **Prediction**：高 exploitability 条件下，优化 weak verifier 将显著增大 weak-strong reward gap，且这种 gap 会随优化压力上升。
* **How to test**：在不完备测试/弱 judge 环境中逐步增加 RL 更新强度。
* **What failure would imply**：reward hacking 风险被夸大，或 weak verifier 设计过强、不足以暴露差异。
* **How the theory would be revised**：把 exploitability 从“结构性变量”收缩为“verifier misspecification 的极端特例”。

## **Prediction 5**

* **Prediction**：即使最终准确率匹配，高 VSI 任务上的 CoT reveal rate / faithfulness 仍更低。
* **How to test**：在 matched-accuracy 子集上做 hint injection 与 counterfactual faithfulness 测试。
* **What failure would imply**：monitorability 与 verification structure 并无直接联系。
* **How the theory would be revised**：把 faithfulness 从统一框架中拆出，作为独立但相关的第二轴。

## **Prediction 6**

* **Prediction**：Lean / 可执行代码等强可验证锚点任务在 VSI 空间中会聚集于较低区域，并对应更大的 verifier-based 训练收益。
* **How to test**：对 Lean 小规模集、MathArena objective 子集、LiveBench objective 子集做 VSI 估计和 gain 测量。
* **What failure would imply**：synthetic 规律不具有外部效度，或真实任务的 structure 被其他复杂因素覆盖。
* **How the theory would be revised**：将主张收窄为“该原则解释受控 reasoning 环境中的训练可学性”，而不再声称覆盖开放真实任务。

---

# 11. Risks, Failure Modes, and Plan B/C

## 理论风险

**风险**：VSI 过于 ad hoc，三个分量并不足以描述真实任务。
**应对**：主文先把 VSI 作为可操作近似，同时在附录保留三维 phase diagram；若合成单指标效果差，则退回 phase diagram 叙事。

## 实验风险

**风险**：difficulty matching 做得不干净，导致 H/A/E 与难度仍然纠缠。
**应对**：用多重匹配准则：

* base model pass rate
* 最短解长度
* solver branching factor
* human spot-check
  必要时只在 paired instances 上做主结论。

## benchmark 风险

**风险**：synthetic 任务过于“人造”，无法迁移到真实 reasoning。
**应对**：真实锚点必须在中期就加入，不等到最后；Lean / MathArena / LiveBench 至少选两个做主文，第三个可作为确认实验。 ([Nature][6])

## 识别/解释风险

**风险**：观察到的 gain 只是 stronger verifier 更强，而不是 verification structure 在起作用。
**应对**：必须做 equal-budget、verifier-swap 和 random-routing 对照；否则难以识别“结构”与“力量”的差异。

## 工程风险

**风险**：RL 不稳定、强 verifier 开销大、rewrite pipeline 噪声高。
**应对**：

* 前期只在 1.5B/3B 上做稳定性验证
* strong verifier 缓存
* rewrite generator 先程序化，LLM 只做少量辅助

## Plan B

若 SAVR 方法收益不明显，但 VSI 的预测规律成立：

* 将论文主贡献收缩为 **新原则 + 新 benchmark + predictive law**
* 方法部分降级为示范性 instantiation
  这仍然有顶会价值。

## Plan C

若真实锚点迁移较弱，但 synthetic 结果非常清楚：

* 把论文定位为 **controlled mechanistic study of trainable reasoning**
* 强调它对 benchmark 设计和 verifier 研究的意义
* 将真实任务外推降级为 future work / appendix

---

# 12. Feasibility Under Compute Constraints

默认资源：**16×80GB A800**。
该项目不依赖大规模预训练，主要成本来自中小模型后训练、多条件对照和 evaluator 计算。

## 模型规模

* 1.5B / 3B：主开发与大部分主实验
* 7B：少量确认性实验
* 不依赖 >7B 全参数训练

## 训练时长与 GPU-days（估计）

| 组件                                          | 估计 GPU-days |
| ------------------------------------------- | ----------: |
| 1.5B / 3B SFT warm-up                       |        8–15 |
| synthetic 主实验（ORM/PRM/SAVR，多 family，多 seed） |       45–70 |
| verifier / prefix models                    |        8–15 |
| 7B 确认性实验（LoRA/QLoRA 优先）                     |       20–35 |
| 真实锚点迁移实验                                    |       15–25 |
| **总计**                                      |  **96–160** |

这个量级在 16 卡 A800 上是可行的，且允许返工一轮。

## 数据生成成本

* CertBench 主体：CPU + symbolic solver 为主
* 等价重写：程序化为主，API 为辅
* faithfulness 辅助审核：少量 API 使用

## API 使用位置

* 语义等价重写提案
* CoT verbalization / faithfulness 辅助判读
* 少量 error analysis
* **不用于主指标评分**

## 并行策略

* **机器 A**：rollout + weak verifier + evaluator cache
* **机器 B**：训练 + prefix verifier + 7B confirmatory run
* 使用 FSDP/DeepSpeed 或 LoRA 进行资源管理

**为什么可做**：

1. 主体是中小模型后训练，不是大规模预训练；
2. 大部分 benchmark 可程序生成；
3. strong verifier 只在 selective 路径中调用；
4. 真实锚点采用精选子集，不追求全 leaderboard 式穷举。

---

# 13. Reproducibility and Engineering Plan

## 配置管理

* Hydra / OmegaConf
* 所有实验以 config 驱动
* 每个实验记录：

  * 模型版本
  * 训练范式
  * verifier 版本
  * budget
  * seed
  * benchmark family

## 实验记录

* W&B / MLflow
* 保存：

  * 训练日志
  * per-instance metrics
  * weak/strong verifier outputs
  * computed (H, A, E, VSI)

## 数据版本

* DVC 或等价版本管理
* CertBench generator 版本号化，而非只发布静态样本
* 真实锚点子集清单固定并版本化

## 随机种子

* 固定 seed 列表
* 主文报告全部 seed 汇总，不挑最好 run

## Checkpoint 策略

* SFT / RL 关键阶段保存
* 保留 best-dev 与 last checkpoint
* 记录 exact tokenizer / prompt template / reward config

## 评测脚本

* objective scoring scripts
* weak/strong verifier wrappers
* bootstrap / mixed-effects 统计脚本
* figure reproduction notebooks

## 建议发布 artifacts

至少发布以下内容：

1. CertBench generator
2. 强/弱 verifier 定义
3. 计算 VSI 的脚本
4. 训练与评测 configs
5. 每个实验的 raw per-instance results
6. 主要 checkpoint（至少 1.5B/3B）
7. analysis notebook 与 figure scripts

---

# 14. Timeline and Milestones

## Week 1

* 确定 CertBench 四个 family 的生成器原型
* 实现 strong/weak verifier 接口
* 跑通 SFT baseline

## Week 2

* 实现 (H, A, E) 的首版估计器
* 完成 difficulty matching pipeline
* 1.5B 上做首轮小规模 ORM vs PRM 信号验证

## Week 3 — **最小闭环 / Go-No-Go**

* 跑 E1 + E2 的最小版
* 判断：

  * VSI 是否优于 difficulty 解释训练收益
  * high-A 是否真的伤害 PRM
* **若无明显信号，立即转 Plan B：以 phase diagram + benchmark 为主，方法降级**

## Week 4–5

* 完整实现 SAVR
* 做 E3 exploitability 与 E5 equal-budget comparison
* 加入 faithfulness / reveal rate 实验原型

## Week 6

* 跑 E4 全量 predictive regression
* 加入 3B 模型
* 锁定主图与主表指标

## Week 7

* 真实锚点迁移：MathArena / LiveBench / Lean 子集
* 做 E7 transfer 实验
* 视时间决定是否加 appendix 中的 state-tracking / refactor 子实验

## Week 8

* 7B 确认性实验
* 全量 ablation 与 robustness
* 补理论部分 proof sketch

## Week 9

* 写作初稿
* 固定 Figures 1–5
* 统计复查、误差分析、失败案例整理

## Week 10

* 清理代码
* 开源准备
* 完成 rebuttal-ready appendix

---

# 15. Paper Framing

## 15.1 Best-paper style one-sentence pitch

**Recent reasoning progress is best understood not as a generic leap in abstract deliberation, but as progress on tasks with favorable verification structure—and that hidden axis can be measured, tested, and exploited.**

## 15.2 Contribution bullets

* 提出 **verification structure** 作为 reasoning 可训练性与可监控性的核心研究对象。
* 定义 **VSI**，将任务结构拆分为 certificate horizon、local ambiguity 与 exploitability。
* 构建 **CertBench**，首次在受控环境下将 task difficulty 与 verification structure 解耦。
* 给出可证伪的理论与机制命题，解释 PRM / RLVR / CoT monitoring 何时有效、何时失效。
* 提出 **SAVR** 作为预算受限的原则化干预，验证“不是所有任务都值得同样的 verifier 强度”。
* 用真实锚点任务表明该框架不仅解释 synthetic 设置，也能解释 formal/code/math reasoning 的差异。

## 15.3 Figure plan

1. **Figure 1: Difficulty vs VSI**
   同等 difficulty 下，不同 VSI 的训练收益显著不同。
   目的：一图讲清“不是难度决定一切”。

2. **Figure 2: Verification phase diagram**
   以 (H) 和 (A) 为坐标，颜色表示 exploitability 或 gain。
   目的：展示不同任务族落在不同结构区域。

3. **Figure 3: SAVR schematic**
   weak verifier → VSI estimation → routing → selective updates。
   目的：说明方法只是原则的 instantiation。

4. **Figure 4: Faithfulness / hacking vs VSI**
   展示 reveal rate、weak-strong gap、hack rate 随 VSI 的变化。
   目的：统一 accuracy、monitorability、reward hacking 三类现象。

5. **Figure 5: Real-task anchors**
   MathArena、LiveBench、Lean 子集投影到 VSI 空间。
   目的：证明不是只对 synthetic 玩具任务成立。

6. **Table 1: Baseline comparison under equal verifier budget**
   SFT / ORM / PRM / P-GRPO / always-strong / SAVR。
   目的：给出主要量化结论。

## 15.4 Related work organization

建议按“问题张力”而不是按模块堆砌：

1. **Reasoning gains under verifier-based training**

   * RLVR, self-correction, theorem proving

2. **Learning and analyzing verifiers**

   * PAC learning, query complexity, process verification

3. **Process rewards and reward reasoning**

   * PRM, success-conditioned rewards, reasoning reward models

4. **Faithfulness and monitorability**

   * CoT faithfulness, counterfactual explanation faithfulness, obfuscation risk

5. **Evaluation under contamination and objective scoring**

   * LiveBench, MathArena, post-static-benchmark evaluation

这样组织 related work 的好处是：它自然服务于论文主问题——**为什么 verifier-based progress 只在某些结构上可靠**，而不是把相关工作拆成零散组件清单。

---

这份 proposal 的最关键一句话，不是“我们提出了 SAVR”，而是：**我们提出了一个新的解释变量，使 reasoning 的成功、失败和误测第一次可以放进同一坐标系。**

[1]: https://openreview.net/forum?id=CjwERcAU7w "https://openreview.net/forum?id=CjwERcAU7w"
[2]: https://openreview.net/pdf?id=sKYHBTAxVa "https://openreview.net/pdf?id=sKYHBTAxVa"
[3]: https://openreview.net/forum?id=5ODlY0KYCx "https://openreview.net/forum?id=5ODlY0KYCx"
[4]: https://assets.anthropic.com/m/71876fabef0f0ed4/original/reasoning_models_paper.pdf "https://assets.anthropic.com/m/71876fabef0f0ed4/original/reasoning_models_paper.pdf"
[5]: https://openreview.net/forum?id=y0zL9IZxZ7 "https://openreview.net/forum?id=y0zL9IZxZ7"
[6]: https://www.nature.com/articles/s41586-025-09833-y "https://www.nature.com/articles/s41586-025-09833-y"
[7]: https://cdn.openai.com/pdf/34f2ada6-870f-4c26-9790-fd8def56387f/CoT_Monitoring.pdf "https://cdn.openai.com/pdf/34f2ada6-870f-4c26-9790-fd8def56387f/CoT_Monitoring.pdf"
[8]: https://openreview.net/pdf?id=4OsgYD7em5 "https://openreview.net/pdf?id=4OsgYD7em5"
[9]: https://openreview.net/pdf?id=V727xqBYIW "https://openreview.net/pdf?id=V727xqBYIW"
[10]: https://openreview.net/forum?id=koTNDE8hl0 "https://openreview.net/forum?id=koTNDE8hl0"
