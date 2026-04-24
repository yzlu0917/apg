# TriVer: Process-State Estimation for Continue / Revise / Branch Control

## 0. 合并说明

这份 proposal 以 `idea/12.md` 为主干，保留其最关键的分解:

- `local invalidity`
- `continuation uncertainty`

在此基础上吸收:

- `idea/9.md` 的 `marginal action value` 视角，把 TriVer 从“双头打分器”升级为 **面向动作选择的 controller**。
- `idea/10.md` 的 `verifiability` 分解，把“何时值得花 verification budget”融入 TriVer 的 compute policy。
- `idea/4.md` 的 `Risk-Coverage-Compute` 报告方式，但只把它作为评测语言，而不是把整套 conformal 搜索框架搬进来。

因此，整合后的主线是:

> **TriVer 不是一个新的 verifier，也不是新的 reasoner training recipe，而是一个 inference-time controller: 它估计当前 prefix 的过程状态，并据此决定 continue / revise / branch / abstain。**

---

## 1. 一句话主张

> 把 process-level 的“局部错误概率”和“后续成功不确定性”分开建模，并把它们进一步转成 action value，可以让 test-time compute 从盲目多想变成可解释、可校准、可测 regret 的控制问题。

---

## 2. Proposal 摘要

当前很多 inference-time 方法都把复杂决策压成一个标量:

- 低分就 revise
- 高分就继续
- 低置信就 abstain

这个假设过于粗糙。真实系统里至少存在三类 prefix:

1. 现在已经够好了，继续算纯浪费
2. 现在不够好，但再算一步大概率能救回来
3. 现在不够好，而且再算也基本没救

如果只用一个标量，`2` 和 `3` 很容易混在一起。TriVer 要解决的就是这个问题: 不再只问“当前分高不高”，而是显式估计当前 prefix 的 **process state**，并把它转成是否值得继续投入 compute 的动作决策。

---

## 3. 这条主线与其他三条线的边界

- 和 CNT 不同: CNT 关注训练时该用什么 credit。TriVer 关注推理时该如何分配 compute。
- 和 CIVIC-PRM 不同: CIVIC-PRM 关注 verifier 应该学什么。TriVer 默认 verifier 或 local checker 已存在，重点是如何用这些信号做动作控制。
- 和 ToolShift 不同: ToolShift 关注外部工具接口的鲁棒性。TriVer 关注 reasoning prefix 的内部状态与 compute policy。

也就是说，这条线保留的理由是它研究的是 **inference-time control law**。

---

## 4. 研究问题与可证伪预测

### 4.1 Research Questions

1. `RQ1` 单标量 verifier score 是否足以支持 `continue / revise / branch` 这类动作选择?
2. `RQ2` local invalidity 与 continuation uncertainty 是否真是可分离、可学习、且对应不同行动后果的两个状态量?
3. `RQ3` 把这两个状态量进一步转成 action value，是否能在等预算下优于 uniform best-of-N、uncertainty-only、PRM-only?
4. `RQ4` TriVer 的收益主要来自 raw accuracy，还是来自降低 `revision harm` 与 `wasted branching`?

### 4.2 Falsifiable Predictions

- `P1` 真正“额外 compute 最值钱”的 prefix，不是最低 PRM score 的那一批，而是 **中等成功均值 + 高不确定性** 的那一批。
- `P2` 两个 prefix 若 PRM score 接近，但 uncertainty 不同，最优动作经常不同。
- `P3` TriVer 主要改善的是 `Action Regret@Budget`、`Revision Harm Rate` 与 `Compute Value Calibration`，而不是单纯更会刷 best-of-N。
- `P4` error feature 与 uncertainty feature 在 hidden state 中应表现出可分离性；否则“双头分解”只是多了复杂度，没有带来真正机制增量。

---

## 5. 方法设计

### 5.1 过程状态建模

对每个 prefix `p_t = (x, z_1:t)`，TriVer 估计两个量:

1. `q_t = P(step t invalid | p_t)`
2. `S_t ~ Beta(alpha_t, beta_t) ~= P(eventual success | p_t)`

其中:

- `q_t` 表示这个 prefix 是否已经走错了，偏向支持 `revise`
- `S_t` 的均值与方差表示“继续走下去成功的概率与不确定性”，偏向支持 `continue` 或 `branch`

### 5.2 从 process state 到 action value

仅有双头还不够。吸收 `idea/9.md` 后，TriVer 显式定义动作集合:

- `continue`
- `revise`
- `branch_K`
- `abstain`

然后把 process state 映射成每个动作的预期效用:

- `U(continue)` 由当前 `mu_t` 与当前 local risk 决定
- `U(revise)` 在 `q_t` 高时上升
- `U(branch_K)` 由 `expected improvement` 与 cost 决定
- `U(abstain)` 在错误风险高且 recoverability 低时上升

这一步是整合后最大的升级。原始 `idea/12.md` 偏向“状态估计器”；现在它变成了一个真正的 **controller**。

### 5.3 Expected Improvement 与 verifiability 融合

为了避免 branch 退化成“多采样就完了”，吸收 `idea/10.md` 的 verifiability 语言:

- `coverage`: 当前候选池里是否可能有正确解
- `detectability`: 错误候选是否容易被辨别
- `blind-spot overlap`: 当前 reasoner 与 verifier 是否共享盲点

TriVer 不需要把这三项都重建成完整理论对象，但会把它们转成三个可操作特征:

- current disagreement
- verifier confidence spread
- cross-family verifier disagreement

这些特征与 `mu_t / nu_t / q_t` 一起输入 controller，用来估计 branch 的真实收益。

### 5.4 推理规则

默认规则如下:

- 若 `q_t > tau_bad`: `revise`
- 若 `EI_t(K) > lambda_cost * cost_t`: `branch_K`
- 若 `mu_t` 足够高且 `nu_t` 足够低: `continue`
- 若错误风险高且 recoverability 低: `abstain`

其中 `EI_t(K)` 是根据 `Beta(alpha_t, beta_t)` 计算的 expected improvement。

### 5.5 来自 4 的融合: 评测与报告方式

TriVer 不直接吞并 `idea/4.md` 的完整 conformal 理论，但明确采用它最有价值的部分:

- `Risk-Coverage-Compute` 作为统一报告语言
- 对 `certified abstain / uncertified answer` 做明确区分

这样做的好处是:

- 保留可报告性
- 不把主线拖入过重的 selective conformal 技术细节

---

## 6. 数据与实验设计

### 6.1 训练与评测环境

按从易到难的顺序推进:

1. `Synthetic verifiable environments`
2. `Math reasoning`
3. `Formal-lite / theorem-lite`
4. 可选: `structured code reasoning`

第一阶段优先选那些可以稳定给出:

- local validity label
- prefix rollout success count

的环境。

### 6.2 Baselines

至少比较以下四类:

1. `Calibrated PRM`
2. `UHeads / uncertainty-only`
3. `SCoRe / PAG-like self-correction policy`
4. `Uniform best-of-N / self-consistency + final verifier`

### 6.3 核心指标

- `Action Regret@Budget`
- `Revision Harm Rate`
- `Compute Value Calibration`
- `Accuracy vs token budget`
- `Risk-Coverage-Compute`
- `Wasted branching rate`
- `Abstain on answerable rate`

### 6.4 Minimum Viable Experiments

1. `Oracle action prediction`
   小规模标出 oracle action，看 TriVer 是否优于 PRM-only / UQ-only。
2. `Equal-token budget curves`
   比较 TriVer 与 uniform best-of-N / revise heuristics 的 accuracy-budget 曲线。
3. `Revision Harm`
   看 revise 是否真的更少把本可成功的 prefix 改坏。
4. `Compute Value Calibration`
   验证预测的 expected improvement 是否和真实收益一致。
5. `Ablation`
   去掉 invalidity head、去掉 uncertainty head、去掉 calibration。
6. `Cross-domain transfer`
   synthetic + math 训练，formal-lite 测试。
7. `Mechanistic validation`
   分析 error feature 与 uncertainty feature 是否可分离。

---

## 7. 预期贡献

这条线整合完成后，预期贡献不再只是“一个双头模型”，而是四层:

1. 一个新的 inference-time 问题定义: `process-state control`
2. 一组新的指标: `Action Regret / Revision Harm / Compute Value Calibration`
3. 一个新的 controller recipe: `state heads + action value + budgeted policy`
4. 一组关于 test-time compute 的机制结论: **为什么不是所有低分 prefix 都值得继续算**

如果结果理想，TriVer 可以成为“后训练推理模型如何做 compute allocation”的核心主线之一。

---

## 8. 风险与备选路线

### 风险 1

双头分解在真实任务上不稳定，最后不比单标量强。

应对:

- 先在干净 synthetic / formal-lite 环境中证明“单标量不足”
- 再扩到自然语言 math

### 风险 2

action value 学得很好，但 raw accuracy 增益有限。

应对:

- 把论文转成 `new benchmark + new decision metrics + lightweight controller`
- 强调 `Action Regret` 和 `Revision Harm` 的新评测价值

### 风险 3

对开放域问答无效，local validity label 太噪。

应对:

- 明确边界: 本方法主打 `verifiable reasoning`
- 不追求无边界泛化

---

## 9. 执行计划

### Phase 1: 两周 Go / No-Go

- 在 synthetic 环境上跑出 oracle-action gap
- 验证双头是否优于单头
- 跑第一版 `Action Regret@Budget`

### Phase 2: 四到六周主结果

- 扩到 math / theorem-lite
- 补齐所有强 baseline
- 固化 controller 与 compute frontier 图

### Phase 3: 加分项

- 引入 stronger verifier bank
- 加入轻量 selective certification
- 做机制分析与干预实验

---

## 10. 最终收敛后的 proposal 形态

相对于原始 `9/10/12/4` 的分散状态，收敛后的 TriVer 更干净:

- 保留了 `12` 的核心: error vs uncertainty decomposition
- 吸收了 `9` 的价值函数视角，让它真正能做动作选择
- 吸收了 `10` 的 verifiability 语言，让 branch 更有理论解释
- 采用了 `4` 的风险-覆盖-算力报告方式，但不过度背负理论包袱

最后这条线可以概括为:

> **不是所有“低分前缀”都该重做，真正该投入额外 compute 的，是那些局部未必错、但仍有高边际收益的状态。**
