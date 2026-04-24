# CIVIC-PRM: Auditing and Reducing Outcome Leakage in Process Verifiers

## 0. Proposal Overview

本 proposal 研究 process verifier 是否真的在看过程，以及如何对 outcome-sensitive shortcuts 进行严格审计和最小修复。整条主线围绕四个核心组件展开：

1. 一个主 benchmark：`AMCD`
2. 一个直接干预指标：`ASS`
3. 一个辅助压力测试集合：`VST`
4. 一个最小化 disentangled objective：
   - `step loss`
   - `local matched-pair ranking`
   - `conditional answer-swap invariance`
   - `hard-negative replay`

proposal 的中心不是构造更复杂的 PRM 配方，而是把 verifier 变成一个能被反事实审计、能被证伪、并能被最小修复的研究对象。

---

## 1. 一句话 thesis

> 在 answer-visible 的 process verification 设定里，verifier 总分会混合“局部过程有效性”和“最终答案一致性”两类信号；答案匹配的局部反事实审计可以暴露这类纠缠，而只对 process signal 施加条件 invariance 能部分修复 leakage 而不牺牲 utility。

---

## 2. 核心问题

很多所谓的 process verifier，在普通 step-level 指标上表现不错，但这并不等价于“它真的在看过程”。

一个 verifier 可能拿高分，只因为它在利用：

- 最终答案像不像对
- 成功轨迹常见的格式或措辞
- 长度、模板、语气、熟悉解题套路
- 某些与 correctness 共现的风格统计

如果是这样，那么后续一切依赖 verifier 的系统：

- reranking
- search
- RLVR / PRM
- compute control

都建立在脆弱信号之上。

因此本 proposal 的真正问题不是“怎么把 verifier 训得更强”，而是：

> **如何把 answer-visible process verification 变成一个能被反事实审计、能被证伪、并能被最小修复的科学对象。**

---

## 3. 研究边界

### 3.1 这条线不是什么

- 不是 reasoner training 主线
- 不是 general open-domain factuality 论文
- 不是 full-stack PRM / search / RL 系统论文

### 3.2 这条线是什么

它是一条 verifier 主线，主要研究三件事：

1. `diagnosis`
   verifier 在什么维度上错得很系统
2. `audit`
   如何构造 paired counterfactual 测试，避免只看普通 AUROC
3. `minimal repair`
   最小什么样的 invariant objective 能减少 leakage

### 3.3 Claim boundary

本 proposal 只主张对 **audited, executable, verifiable domains** 成立，优先包括：

- algebra
- graph / shortest path
- planning / blocksworld-like tasks
- formal-lite / rule-executable domains

对于自由生成、开放域、无状态可验的自然 CoT，本 proposal 只做小规模 transfer，不做强泛化承诺。

---

## 4. 关键定义

## 4.1 Step validity

设问题 `x` 对应一个可执行 latent state trajectory：

`s_0 -> s_1 -> ... -> s_T`

一个局部 reasoning step `v_t` 的 `step validity` 定义为：

> 该步是否实现了与正确 latent state transition 一致、且不会把当前轨迹带离合法可达解空间的更新。

这里的关键不是“这一步最后有没有导致答案对”，而是“这一步在局部状态语义上是否有效”。

### 4.2 Audited locus

每个反事实样本都会标记一个 `edited locus`，也就是被干预的关键位置。  
核心训练与主指标都围绕这个 locus 展开，而不是泛泛地给整条轨迹一个总分。

### 4.3 Delayed-repair 的处理

`Delayed-Repair` 很危险，因为它把两个问题混在一起：

- 该步局部是否错误
- 后续是否把错误修了回来

因此本版做明确切分：

- `Delayed-Repair` **不进入核心训练集**
- `Delayed-Repair` **不进入主指标 AMCD**
- 它只进入 `VST`，作为 recoverability stress subgroup

这能避免 step-level 与 trajectory-level 标签体系混乱。

### 4.4 Verifier 输入与 answer visibility

这一点必须定义清楚。

本 proposal 允许两种输入接口：

1. **answer-visible full-trace verifier**
   - 输入完整轨迹与待审计 locus
   - 这是主审计接口，因为它最接近现实中易泄漏的 verifier 设定

2. **answer-masked same-backbone verifier**
   - 对同一 backbone，把显式 final answer 或答案声明位置 mask 掉
   - 这是主 baseline，而不是次要对照

原因很明确：  
如果 same-backbone answer-masked baseline 已经解决了大部分问题，那么复杂 invariant recipe 的算法贡献必须降级。

这里还必须明确一点：

- `audited locus` 只是一种 **scientific instrument**
- 它服务于 audit-time object identification
- deployment-time verifier 不应依赖 locus oracle

因此，主文需要同时报告两种设定：

1. audit-time：给定 locus，直接测局部 process discrimination
2. deployment-time：不给 locus，对全 trace 扫描局部 process score，再聚合成 `G_proc`

### 4.5 Process signal 与 consistency signal

本 proposal 不再把 verifier 分数当作一个不可分的标量。  
最小可解释分解是：

- `G_proc`
  - 过程信号
  - 目标是评估 audited locus 或局部 transition 是否有效
- `G_cons`
  - 一致性信号
  - 目标是表示过程与最终答案是否自洽

对应总分：

`G_total = G_proc + alpha * G_cons`

关键点是：

- `AMCD` 主要审计 `G_proc`
- `ASS` 用来测 `G_proc` 与 `G_total` 各自对 final answer 的直接敏感性
- 条件 invariance 只作用于 `G_proc`，而不是无条件压扁整个 `G_total`

---

## 5. CRAFT-Core：主数据协议

### 5.1 数据来源

`CRAFT-Core` 只保留最干净的三到四类域：

- algebra
- graph/path
- planning
- 可选 formal-lite

每题至少用 `2–3` 个 verbalizer，把同一 latent trajectory verbalize 成不同自然语言步骤，以降低 style artifact。

### 5.2 Counterfactual families

主结果只使用四类：

1. `local-invalid`
   只改一个关键 state transition，造成局部错误
2. `answer-swap`
   过程不变，只换 final answer
3. `lucky-answer`
   过程错，但 final answer 被改对
4. `paraphrase`
   语义不变，只改风格与措辞

`Delayed-Repair` 只进 stress suite，不进主训练与主指标。

这四类 family 可组合成最小 quartet：

- `tau_valid^a`
- `tau_invalid^a`
- `tau_valid^a'`
- `tau_invalid^a'`

其中：

- `a` 与 `a'` 只改变 final answer surface
- valid / invalid 只在 audited locus 附近翻转局部 correctness

### 5.3 Artifact audit

这是 CIVIC-PRM v2 的硬门槛。

每个 matched family 都必须过以下审计：

1. `shallow classifier`
   不能仅靠 n-gram、长度、标点等浅特征高精度识别 counterfactual type
2. `length-only baseline`
   不能只靠长度差区分正负样本
3. `human blind audit`
   人类盲审不能轻松一眼看出“这是人工错轨迹”
4. `multi-verbalizer consistency`
   结果不能只依赖某一种 verbalizer 风格

若某个样本在 artifact audit 中暴露强伪迹，应直接剔除。

---

## 6. 核心指标与 stress suite

### 6.1 主指标：AMCD

`AMCD` = `Answer-Matched Counterfactual Discrimination`

定义：

- 对一对 matched traces，保持 final answer 与整体风格近似一致
- 只在 audited locus 附近翻转局部 correctness
- verifier 需正确判别 valid vs invalid

AMCD 是主 benchmark，因为它最直接地测：

> **在答案不再提供区分度时，verifier 是否仍能看懂过程差异。**

### 6.2 直接干预指标：ASS

`ASS` = `Answer-Swap Sensitivity`

它直接测：

- 固定过程，仅 swap 最终答案时
- verifier 分数变化有多大

主文的公共报告至少包含：

- `ASS_total`
  - `G_total` 对 answer swap 的敏感性

若方法显式分离了 process / consistency 通道，则额外报告：

- `ASS_proc`
  - `G_proc` 对 answer swap 的敏感性
- 这是 method-specific 机制诊断，而不是所有 baseline 都必须具备的公共 benchmark 指标

若一个 verifier 的 `ASS_total` 很大，这不自动等于 leakage；  
真正危险的是：

- `ASS_proc` 也很大
- 且这种敏感性与 `AMCD` 下降、`exploitability` 上升相关

### 6.3 Stress suite：VST

`VST` 不是主 benchmark，而是辅助压力测试，包含：

- answer-swap sensitivity
- lucky-answer
- delayed-repair
- paraphrase robustness
- exploit hard negatives

### 6.4 Downstream utility 指标

用于证明 audit 结果不是纯“漂亮 benchmark”：

- `selection gain @ N`
- `exploitability rate`
- `ECE / Brier / AURC`
- `OOD transfer drop`

---

## 7. 方法：Minimal Disentangled Verifier

## 7.1 设计目标

原始 full recipe 太像 bundle。  
整个方法收敛成一个两阶段 pipeline。

### 7.2 Stage A：构造 audited matched families

1. 在可执行环境中采样问题 `x` 和真状态轨迹
2. verbalize 成自然语言 reasoning traces
3. 构造 `local-invalid / answer-swap / lucky-answer / paraphrase`
4. 对每个 family 做 artifact audit
5. 只保留通过审计的 paired families

### 7.3 Stage B：训练 minimal invariant verifier

输入：

- `problem x`
- `full trace` 或 `prefix + locus`
- `edited locus t`

输出：

- `z_t^proc`
  - locus-local process validity logit
- `z^cons`
  - answer-process consistency logit
- `G_proc`
  - 由全 trace 上的局部 process logits 聚合得到
- `G_total = G_proc + alpha * z^cons`

其中 deployment-time 默认不提供 audited locus。  
因此 `G_proc` 需要由逐步扫描得到的局部 process score 聚合而成。主文默认使用 `softmin` 聚合，并对以下替代项做 ablation：

- `mean`
- `min`
- `Noisy-OR` 风格聚合

总损失只保留四项：

1. `L_step`
   对 `z_t^proc` 做普通 step validity BCE

2. `L_local-pair`
   对 `local-invalid` paired samples，在编辑位置附近施加 local ranking
   要求 `G_proc(valid) > G_proc(invalid)`

3. `L_cond-swap`
   对 `answer-swap` twins，只要求 `G_proc` 基本不变
   不要求 `G_total` 无条件不变，以免惩罚合法一致性信号

4. `L_hard-neg`
   对 attacker 生成的 high-score wrong traces 做 replay

总损失：

`L = L_step + lambda_1 * L_local-pair + lambda_2 * L_cond-swap + lambda_3 * L_hard-neg`

### 7.4 设计原则

- 不把所有稳妥组件都抬成核心机制
- 把 **局部因果约束** 放在中心
- 把 process signal 与合法 consistency signal 分开
- 保持训练目标可解释、可拆分

### 7.5 降权的组件

以下内容不再是主方法核心：

- adversarial debiasing head
- group-DRO 作为 headline contribution
- calibration layer

它们最多作为：

- reweighting
- appendix ablation
- downstream utility enhancement

---

## 8. 强 baselines

主表第一排 baseline 必须包含：

1. **same-backbone answer-masked PRM**
   最简单、最致命的反驳

2. **same-backbone pairwise-ranking verifier**
   有更强监督，但不做 answer-matched pairing

3. **frontier API judge / strong closed evaluator**
   工程上真实可用的替代品

4. **hard-negative-only baseline**
   用来拆出“抗攻击提升是否只是多看了攻击数据”

补充 baseline：

5. standard step-only BCE verifier
6. hidden-state probe verifier

---

## 9. 实验设计

### 9.1 Leakage audit 主图

画出：

- ordinary step AUROC
- AMCD

的散点图，展示“普通指标强，但 AMCD 崩”的裂缝。

### 9.2 Answer-swap intervention

固定过程，替换 final answer，比较不同 verifier 的分数变化。  
这直接测模型是否在用 answer-sensitive signal。

必须同时报告：

- `ASS_proc`
- `ASS_total`

### 9.3 Core ablation

至少比较：

- `step-only`
- `answer-masked`
- `+ local-pair`
- `+ cond-swap`
- `+ hard-neg`
- `dual-head disentangled`

### 9.4 Probe + mediation

不仅做 hidden-state probe，还要做：

- `ASS_proc / ASS_total`
- `AMCD / ordinary AUROC` 与 exploitability 的相关
- `ASS -> AMCD -> selection gain / exploitability` 的 mediation 分析

否则 probe 只能证明信息存在，不能证明模型在使用它。

### 9.5 Best-of-N reranking

固定 generator 与 candidate pool，比 selection gain @ N。  
关键 slice 是：

- 答案偶然对、过程其实错
- 风格像成功样本，但局部 transition 错

### 9.6 Multi-attacker transfer

对 exploit hard negatives，至少做：

- 自家 attacker
- 另一个 family attacker
- black-box / white-box mix

否则“exploit-reduced”都说不稳，更别说“resistant”。

### 9.7 OOD 与 natural transfer

必须做两种：

1. held-out task family
2. 更自然的 model-generated traces / natural CoT 小样本

若第二类完全崩，则 claim 必须缩回 audited domains。

### 9.8 Failure slices

按以下维度分组报告：

- counterfactual type
- verbalizer family
- length bucket
- difficulty bucket

明确报告模型仍会在哪些 slice 上错。

---

## 10. 预期贡献

若成功，这篇论文最有价值的贡献不是“一个更复杂 PRM”，而是四件事：

1. **新问题定义**
   answer-invariant verification 作为独立研究问题

2. **新评测协议**
   以 `AMCD` 为中心、`VST` 为 stress suite 的 verifier audit framework

3. **新机制结论**
   现有 verifier 的总分会纠缠 process validity 与 answer consistency，因此可以在普通指标上看起来很强，却在 answer-matched counterfactuals 上系统性失真

4. **最小修复**
   一个比原始 bundle 更小、更可解释的 conditional invariant objective，能部分减少 leakage 并改善 downstream utility

---

## 11. 风险与 Plan B / C

### 风险 1：AMCD gap 不大

如果 strongest simple baseline 在 AMCD 上并没有明显崩，则“outcome leakage 是关键 shortcut family”这一主张需要降级。

Plan B：

- 把主张改成“important shortcut family”
- 把论文收成 systematized verifier shortcut taxonomy

### 风险 2：artifact 太强

如果 shallow classifier 或 blind human audit 能轻松区分 counterfactual 类型，那说明 benchmark 本身不干净。

Plan B：

- 重做 verbalization 与 paraphrase
- 把论文转成“如何构造无伪迹 verifier stress test”

### 风险 3：answer-masked baseline 太强

如果 same-backbone answer-masked PRM 已基本追平主方法，则算法贡献应降级。

Plan B：

- 诚实承认 masking 是强 baseline
- 将论文重心切到 evaluation principle + benchmark

### 风险 4：synthetic -> natural transfer 弱

如果自然 CoT 上收益明显缩水：

- 缩窄 claim 到 audited/executable domains
- 把自然分布结果降为 supporting evidence

### 风险 5：invariance 伤 utility

如果 AMCD 提升但 reranking / exploitability / calibration 没改善，说明 metric 与 utility 脱节。

Plan B：

- 调整 `G_proc / G_total` 聚合或 conditional invariance
- 或承认存在 faithfulness-utility Pareto frontier

### 风险 6：合法 consistency 与 leakage 仍未分开

如果 `ASS_total` 大但 `ASS_proc` 小，且 utility 改善存在，那么答案信号的一部分是合法的。

Plan B：

- 将论文明确写成 disentangling paper，而不是去答案 paper
- 把 headline 从 “remove leakage” 改成 “separate process signal from consistency signal”

---

## 12. 六周执行计划

### Week 1

- 明确 `step validity` 与 `Delayed-Repair` 语义
- 构建 `CRAFT-Core`
- 定义 quartet families 与 `ASS`
- 完成 artifact audit 第一版
- 用 `3B` backbone 跑最小 pilot，不直接上 `7B`

Go / No-Go：

- artifact classifier 不能高得离谱
- paired examples 必须过人工盲审

### Week 2

- 跑 strongest simple baselines：
  - step-only
  - answer-masked
  - pairwise ranking
  - frontier judge
- 出 ordinary AUROC vs AMCD 主图
- 出 `ASS_total` pilot 图
- 对显式分离方法额外出 `ASS_proc` pilot 图

Go / No-Go：

- 至少两个域出现明显 leakage gap

### Week 3

- 跑 minimal variants：
  - `+ local-pair`
  - `+ cond-swap`
  - `+ hard-neg`
  - `dual-head disentangled`
- 做 answer-swap intervention、probe 与 mediation

Go / No-Go：

- 存在一个简单版本明显优于 answer-masked baseline
- 或至少证明 `ASS -> AMCD -> utility` 这条链成立

### Week 4

- 在 `3B` 闭环成立后上 `7B` 主模型
- 做 reranking、calibration、exploitability

### Week 5

- 做 multi-attacker transfer
- 做 held-out family 与 natural CoT transfer
- 做 worst-group / verbalizer robustness

### Week 6

- 3 seeds 复现关键表
- paired bootstrap CI
- 收缩 paper 叙事，只保留一个主 benchmark（AMCD）和一个 stress suite（VST）

---

## 13. Proposal Summary

这条主线的重点不是提出另一个更复杂的 verifier，而是建立一套围绕 `AMCD + ASS` 的 verifier 审计协议，并配套一个足够小、足够清晰的 conditional invariant objective。若 ordinary metric 与 AMCD 的裂缝、`ASS_proc / ASS_total` 的分离、以及 downstream utility 三条证据链同时成立，那么 CIVIC-PRM 将给出一个更扎实的结论：answer-visible process verification 必须先把 process signal 与答案一致性信号分开，才适合继续作为 reranking、search 和 compute control 的基础设施。
