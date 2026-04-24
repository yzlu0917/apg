# TriVer: Prefix Process-State Control for Budgeted Reasoning

## 0. Proposal Overview

本 proposal 研究 test-time reasoning 中的算力分配问题。核心观点是：prefix compute allocation 不应被建模为单一 confidence score 的有序阈值控制，而应被建模为一个 **process-state control** 问题。

整条主线围绕四个核心组件展开：

1. `q_t`: local invalidity risk
2. `S_t`: default-continuation success distribution
3. `U(a | p_t, b_t ; pi_0)`: action-conditioned utility
4. 一个 prefix-level oracle action benchmark：
   - oracle action atlas
   - action regret
   - revision harm
   - compute value calibration

proposal 的中心不是堆更多打分头，而是证明：**有序单标量 confidence ordering** 不是 compute control 的充分统计量。

---

## 1. 一句话 thesis

> 在可验证推理中，prefix 的最优 compute 动作取决于两个可分离的过程状态——局部错误风险与动作可恢复性/边际算力价值；任何仅依赖 budget-conditioned 单调阈值式或有序分段式单标量 confidence ordering 的 controller，都无法稳定实现低 regret 的动作选择。

---

## 2. 核心问题

当前大多数 test-time reasoning 系统，本质上都在做一件过于粗糙的事：

- 用一个分数判断是否继续
- 用一个阈值决定是否 revise
- 用一个置信度决定是否 abstain

但同一个“低分 prefix”可能对应至少三种完全不同的状态：

1. 已经明显走错，最合理动作是 `revise`
2. 还没明显走错，但后续很不确定，最合理动作是 `branch`
3. 已经无可救药，最合理动作是 `abstain`

如果这些状态被压成一个单标量，那么控制策略只能用 threshold 把它们粗暴切开。这就是 TriVer 要回答的问题：

> **prefix compute allocation 是不是一个 process-state control 问题，而不是一个 scalar thresholding 问题？**

---

## 3. 研究边界

### 3.1 这条线不是什么

- 不是 verifier 训练主线
- 不是 reasoner post-training 主线
- 不是 open-world QA 通用 compute 控制

### 3.2 这条线是什么

它是一条 **verifiable reasoning** 的 inference-time control 主线，主要研究三件事：

1. `state identification`
   prefix 的关键状态量是否可分离
2. `action control`
   这些状态量是否足以低 regret 地决定主文中的 `continue / revise / abstain`，以及扩展设置中的 `branch`
3. `decision evaluation`
   最终不只看 accuracy，而是单独看动作质量

### 3.3 Claim boundary

本 proposal 只对可验证推理任务做强 claim，优先包括：

- synthetic verifiable environments
- math-mini / theorem-lite
- structured code reasoning（可选第二域）

对开放域、弱 verifier、不可稳定给 local validity 的任务，只做负例边界，不做强主张。

---

## 4. 关键定义

## 4.1 Prefix、预算与动作

定义 prefix：

`p_t = (x, z_1:t)`

定义剩余预算：

`b_t`

定义主文动作集合：

- `continue`
- `revise_m`
- `abstain`

定义扩展动作：

- `branch_K`

主文先固定三动作闭环 `{continue, revise_m, abstain}`；`branch_K` 只在主闭环稳定后作为 extension 引入。

## 4.2 固定 action operators

为了避免“收益来自某个 magic implementation”，本版固定如下：

- `continue`
  - 继续生成下一步或下一段 reasoning
- `revise_m`
  - 回滚最近 `m` 步，再基于剩余上下文重生成
- `abstain`
  - 直接拒答或输出“需要更多信息/无法在预算内可靠完成”

扩展动作：

- `branch_K`
  - 从当前 prefix 启动 `K` 个 continuation，再用固定 verifier bank/selector 选 best candidate

任何实验结论都必须在固定 operator 家族内报告，不能让实现细节偷偷改变定义。

## 4.3 Local invalidity risk

定义：

`q_t = P(local invalidity | p_t)`

它回答的问题是：

> 当前 prefix 是否已经包含足够明显的局部错误，以致继续沿这条路径推进很危险？

`q_t` 是 revise 相关信息的核心来源，但 **不等于动作价值本身**。

`q_t` 的监督必须按任务域分层说明：

- synthetic / code / theorem-lite：优先使用 exact local checker 或程序化规则
- math：只能使用程序化弱标签、近似规则或经审计的 proxy label，并必须与强可验证域结果分开报告

因此 TriVer 对 `q_t` 的强 claim 主要建立在强可验证域上，math 更适合作为 supporting domain，而不是唯一证据来源。

## 4.4 Default continuation success distribution

定义：

`S_t ~= P(eventual success | p_t, default-continue policy)`

用 Beta 分布表示：

`S_t ~ Beta(alpha_t, beta_t)`

得到：

- `mu_t`: 默认继续的成功均值
- `nu_t`: 默认继续的不确定性 / 方差

这里必须明确：
`S_t` 只描述 **默认继续** 的结果分布，它不是 recoverability 本身，也不是 controller 需要的最终量。

## 4.5 Action-conditioned utility

真正的控制对象应定义为：

`U(a | p_t, b_t ; pi_0)`

也就是：

> 在给定 prefix 和剩余预算时，先执行动作 `a`，再在固定 tail policy `pi_0` 下继续推进后的 counterfactual expected utility。

主文建议固定：

- `pi_0 = default-continue`

并把以下内容作为附加消融而非主定义：

- two-step backup
- receding-horizon controller handoff

建议 utility 统一定义为：

`u = 1[success] - lambda_tok * tokens - gamma * 1[unsafe wrong answer]`

对 `abstain`，可定义：

- utility = 0
- 或在 risk-coverage setting 中按应用约定赋值

关键点：  
TriVer 不再把 `mu_t / nu_t` 直接拿来替代 `U(a | p_t, b_t ; pi_0)`，而是把它们作为 action value head 的输入特征之一。

## 4.6 Ordered scalar controller class

TriVer 的核心反驳对象必须定义清楚。  
本 proposal 不反驳“任意一维编码都不可能表达最优策略”这种过强命题；它只反驳一类更可辩护、也更接近现实实践的 controller：

- 输入一个标量分数 `s_t = f(p_t, b_t)`
- 在每个 budget bucket 内，用单调阈值或有序分段 `c_b(s_t)` 把标量轴切成若干区间
- 每个区间映射到一个动作

也就是：

> **TriVer 的结构性负命题只针对 ordered scalar controller class，而不是任意一维表示。**

这一定义必须在论文中写死，否则“单标量不够”的主张会不严谨。

---

## 5. 核心命题：Scalar insufficiency

## 5.1 直观命题

如果存在一对 prefix：

- scalar verifier score 接近
- 但 oracle 最优动作不同

那么任何只依赖该 scalar score 做 **单调阈值式或有序分段式控制** 的 policy，都必然在这两类 prefix 上至少错掉一类，从而产生不可消除 regret。

这就是本 proposal 最核心的 falsification target。

## 5.2 Crossing mass 与 lower bound

除了 atlas 可视化，本 proposal 还应显式报告两个机制量：

- `crossing mass`
  - 在固定 budget 下，scalar score 接近但 oracle 最优动作不同的 prefix 占比
- `ordered-regret lower bound`
  - 若 crossing 区域上的 top-2 action gap 至少为 `Delta`，则 ordered scalar controller 会承受不可避免的 regret 下界

TriVer 不需要很重的理论，但至少需要一个与 atlas 对齐的 proposition 级结论：

> crossing mass 非零且 action gap 非平凡时，ordered scalar controller 的期望 regret 不可能为零。

## 5.3 需要观察到的 killer result

TriVer 不是靠多加一个头就能立住的。  
必须先观察到下面这个现象：

> **同一 scalar score 等高线附近，最优动作在二维状态平面上发生交叉。**

如果这个现象不存在，那么“单标量不够”的核心主张就不成立。

## 5.4 Oracle Action Atlas

因此本 proposal 的 Figure 1 不该先是 accuracy 表，而应是：

- 横轴：`q_t`
- 纵轴：`nu_t` 或 action-value-derived compute-value proxy
- 颜色：oracle 最优动作

再叠一条 scalar score 等高线，展示：

- 同 score 的 prefix，最优动作仍不同

这张图是整篇论文最重要的证据之一。

---

## 6. 方法：State Heads + Action Value Head

## 6.1 数据收集

在固定 backbone 上生成推理轨迹，并在每个样本中选择 `2–4` 个 decision points。

decision point 不应随意抽样，主文应采用分层策略，至少覆盖：

- prefix depth
- scalar score bins
- 预算区间
- 成功/失败或高/低不确定性区域

对每个 prefix `p_t` 与剩余预算 `b_t`：

1. 主文先枚举动作 `a in {continue, revise_m, abstain}`
2. 扩展实验再加入 `branch_K`
3. 对每个动作做 `N=4~8` 次 counterfactual rollout
4. 每次 rollout 都先执行 `a`，再跟随固定 tail policy `pi_0`
5. 用 exact checker / verifier 计算 utility
6. 取 Monte Carlo 估计：

`hat U(a | p_t, b_t ; pi_0)`

7. 先计算 action gap 与置信区间重叠情况
8. 定义 oracle action：

`a*(p_t, b_t) = argmax_a hat U(a | p_t, b_t ; pi_0)`

9. 若 top-2 动作 gap 过小，或 MC 置信区间明显重叠，则将该 prefix 标记为 `ambiguous`

主文必须同时报告：

- `oracle determinacy rate`
- action-gap histogram
- 结果对 rollout 数 `N` 的敏感性

这样 oracle benchmark 才不会被 MC 噪声污染成伪机制结论。

这一步生成的不是普通训练标签，而是 prefix-level action oracle benchmark。

## 6.2 监督对象

### `q`-head

输入：prefix representation  
输出：`q_t = P(local invalidity | p_t)`

### `S`-head

输入：prefix representation  
输出：`alpha_t, beta_t` 或 `(mu_t, nu_t)`

注意：`S`-head 只近似默认继续的 success 分布，不宣称直接给动作价值。

### Action value head

输入 feature:

`g_t = [q_t, mu_t, nu_t, verifier_disagreement, confidence_spread, cross_family_disagreement, depth_t, b_t]`

输出：

`U_eta(a | g_t)`

这是 TriVer 的核心输出。

## 6.3 为什么要保留 factorization

最自然的反驳是：

> 你为什么不直接用 hidden state + verifier features 训练一个 action/Q-value 头？

这就是 `unstructured direct policy` baseline。  
TriVer 的立场不是否认这个 baseline，而是要正面比较：

- 如果 direct policy 完全更好，TriVer 的结构性 claim 必须降级
- 如果 TriVer 在相同容量下更稳、更可解释，factorization 才有存在理由

因此 factorization 不是默认成立的，而是本 proposal 要证明的对象之一。

## 6.4 推理时 policy

推理规则非常简单：

1. 计算 `q_t, mu_t, nu_t` 与 verifier 特征
2. 形成 `g_t`
3. 选择 `argmax_a U_eta(a | g_t)`
4. 执行动作
5. 更新 prefix 与预算

这保证 TriVer 的主贡献集中在：

- state identification
- action valuation

而不是复杂在线 search engineering。

---

## 7. 主 baselines

最强 baseline 必须包括：

1. **Unstructured direct action-value policy**
   - 同样输入 hidden state + verifier features + budget
   - 直接预测 `U(a | p_t, b_t ; pi_0)` 或 action label

2. **Calibrated scalar PRM controller**
   - 单一 score + calibration + budget-conditioned ordered thresholds / ordered partitions

3. **Uncertainty-only controller**
   - 只基于 entropy / disagreement / rollout variance 决策

4. **Uniform best-of-N / self-consistency + final verifier**

5. **Fixed revise heuristic / self-correction policy**

其中 hardest-to-beat baseline 是 `unstructured direct policy`。  
如果它完全打平或优于 TriVer，那么 factorization claim 不能再强写。

此外，主表里的单标量对照不能只用 PRM threshold。  
必须包含：

- learned 1D bottleneck + ordered partitions

否则“ordered scalar insufficiency”并没有被真正检验。

---

## 8. 核心指标

TriVer 不能只看 accuracy，必须单独测 controller 质量。

### 8.1 主指标

- `Action Regret@Budget`
- `Oracle action accuracy`
- `Revision Harm Rate`
- `Compute Value Calibration`
- `Oracle determinacy rate`
- `crossing mass`

### 8.2 系统指标

- accuracy / utility vs token budget frontier
- wasted branching rate
- abstain on answerable rate
- risk-coverage-compute

### 8.3 机制指标

- same score, different action crossing frequency
- representation separability
- causal intervention response

---

## 9. Minimum Viable Experiments

1. `Oracle Action Atlas`
   证明同 scalar score 下最优动作交叉存在。

2. `Learned 1D Scalar vs TriVer vs Direct Policy`
   这是最重要主表之一。

3. `Equal-token frontier`
   严格 matched budget 下比较 accuracy / utility。

4. `Revision Harm`
   看 TriVer 是否真的减少“把本来能成的前缀改坏”。

5. `Compute Value Calibration`
   预测的 EI / utility 是否和真实 gain 单调一致。

6. `Verifier blind-spot stress`
   same-family vs cross-family verifier，对 action control 尤其是 branching extension 的影响是否不同。

7. `Causal prefix intervention`
   分别干预“修正局部错误”和“提高后续不确定性”，看动作价值变化是否有选择性。

8. `第二 exact-checker 域复现`
   主文至少需要两个 exact-checker 域；math 只作为 supporting domain。

9. `OOD transfer`
   synthetic + theorem-lite / structured code 训练，longer-horizon 或 supporting math 测试。

10. `Label-noise robustness`
   控制 local label 噪声，看 q-head 与 regret 是否平滑退化。

11. `Negative domains`
   在 open QA / short deterministic tasks 上明确报告预期失败。

---

## 10. 预期贡献

如果主假设成立，这篇 paper 的贡献应集中在五点：

1. **新问题定义**
   prefix process-state control

2. **新 benchmark**
   prefix-level oracle action benchmark

3. **新指标**
   Action Regret / Revision Harm / Compute Value Calibration

4. **新机制结论**
   有序单标量 confidence ordering 不是 compute control 的充分统计量

5. **轻量 controller**
   一个 budgeted、可解释、可分析的 action-value controller

这比“又一个更强的 adaptive reasoning heuristic”更像一条能站住的主线。

---

## 11. 风险与 Plan B / C

### 风险 1：双头不可分

如果 `q_t` 与 recoverability 高度共线，TriVer 会退化。

Plan B：

- 把论文转成“何时单标量足够、何时不足”的条件性论文

### 风险 2：direct policy 完全更强

如果 unstructured direct policy 在 matched-capacity 下明显更优：

Plan B：

- 主打 benchmark + mechanism
- 弱化 factorization algorithm claim

### 风险 3：raw accuracy 提升有限

即使如此，也不能直接判失败。

Plan B：

- 把主贡献切到 `Action Regret / Revision Harm / Calibration`
- 作为 compute-safety / decision-quality 论文来写

### 风险 4：branch 价值估计失真

若分支高度相关、EI 失真：

Plan B：

- 引入 relatedness correction
- 或先退成 `{continue, revise, abstain}` 三动作控制

### 风险 5：local labels 太噪

Plan B：

- 收缩到程序可验证域
- 把 math 只作为 supporting domain

### 风险 6：oracle ambiguity 太高

如果 top-2 action gap 普遍很小、结果随 rollout 数 `N` 明显波动：

Plan B：

- 对主指标只保留 high-determinacy prefix
- 用 pairwise action preference 或 soft labels 替代硬 action label

---

## 12. 六周执行计划

### Week 1

- 定义 action oracle
- 搭第一个 exact-checker synthetic env
- 固定 backbone / 主文三动作 operator
- 出第一版 oracle action atlas
- 出 action-gap histogram 与 oracle determinacy rate

Go / No-Go：

- crossing mass 必须非平凡，且 oracle determinacy 不能过低

### Week 2

- 训练 `q` 头、`S` 头
- 建立 calibrated scalar baseline、learned 1D bottleneck baseline 与 direct-policy baseline
- 做 scalar insufficiency 初测

Go / No-Go：

- 至少 learned 1D bottleneck 不能轻易打平主方法；否则主张必须收缩

### Week 3

- 训练 action-value head
- 上 conservative controller
- 跑第一个 exact-checker 域 + 第二 exact-checker 域 equal-budget curves

Go / No-Go：

- 在至少一个 exact-checker 域上优于 learned-1D，且 revision harm 下降；若只在 supporting math 上成立，不足以支撑主 claim

### Week 4

- 在前三周主闭环稳定后再扩展到 `branch`
- 加 verifiability 特征
- 做 same-family vs cross-family verifier stress
- 做 compute value calibration

### Week 5

- 做 causal prefix interventions
- 做 representation separability
- 做 OOD transfer 与 label-noise robustness

### Week 6

- 全量 ablation
- negative domains
- 锁 paper narrative：
  - oracle benchmark
  - scalar insufficiency
  - lightweight controller

---

## 13. Proposal Summary

这条主线的核心不是再造一个双头打分器，而是定义 prefix-level action oracle、严格限定 ordered scalar controller class、证明有序单标量 thresholding 的局限，并给出一个围绕 `q_t`、`S_t` 和 `U(a | p_t, b_t ; pi_0)` 的轻量 controller。如果 oracle atlas、learned-1D 与 direct-policy 对照、以及 equal-budget frontier 三条证据链同时成立，那么 TriVer 就能把 test-time reasoning 的核心问题从“怎么继续多想”改写为“如何低 regret 地分配算力”。
