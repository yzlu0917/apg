# Paper Reframe: Align Back to Proposal

## 0. Goal

这份文档的目标不是继续找新的最强小模型，而是把现有结果重新压回 proposal 的主线：

1. prefix-level oracle benchmark
2. ordered scalar insufficiency
3. budgeted decision quality

当前最重要的不是“再赢一个 baseline”，而是把已经成立的证据链整理成一篇边界清楚、主张可信的 paper。

---

## 1. One-Sentence Paper

> In verifiable reasoning, prefix compute allocation is better understood as process-state control than as ordered scalar thresholding: ordered scalar controllers exhibit non-trivial action crossing on exact-checker benchmarks, while the main deployment bottleneck for structured controllers is state identification under noisy predicted state.

中文工作版：

> 在可验证推理中，prefix 级算力分配更像是一个 process-state control 问题，而不是单一 ordered scalar thresholding；其最直接证据是 exact-checker benchmark 上稳定存在的 action crossing，而结构化 controller 的主要部署瓶颈则来自 noisy predicted state 下的 state identification。

---

## 2. Claim Hierarchy

## 2.1 Strong Claims

这些是主文可以写强的部分：

1. ordered scalar controller class 不是 compute control 的充分统计量
2. prefix-level oracle benchmark 是必要的，因为 action crossing 与 oracle determinacy 都是可测且非平凡的
3. exact-state 和 predicted-state 的差距说明主瓶颈在 state identification / noisy deployment，而不是单纯 value regression 不够

## 2.2 Conditional Claims

这些要写弱，不能写成 universal theorem：

1. factorization 在 exact-state 下有明确价值
2. deployable predicted-state factorization 的表现强域依赖
3. direct policy 仍是 hardest-to-beat baseline，不能写成已经被统一击败
4. richer continuation-outcome features 有帮助，但不等于 proposal 原教旨版本的 `S_t`

## 2.3 Claims To Avoid

这些现在不该写进主文主结论：

1. “TriVer factorization universally beats direct policy”
2. “单标量一定不够”  
   更准确是：单标量在部分域失效，在部分域仍可工作
3. “当前的 richer proxy 就是完整 `S_t`”
4. “cross-domain router 是主问题”

---

## 3. Current Evidence That Supports The Paper

## 3.1 Oracle Benchmark And Mechanism

Proposal 需要的核心机制证据已经具备：

1. 两个 exact-checker 域都已完成
2. crossing mass / high-determinacy crossing 已有实证
3. oracle determinacy rate 已经足够高到可以支持机制结论

代表性结果：

- linear-equations:
  - `oracle_determinacy_rate = 0.7069`
  - `crossing_mass_high_determinacy = 0.7561`
- arithmetic:
  - `oracle_determinacy_rate = 0.8548`
  - `crossing_mass_high_determinacy = 0.7925`

出处：
- [history/results.md](./history/results.md)
- [03_triver_process_state_compute_control.md](./03_triver_process_state_compute_control.md)

## 3.2 Ordered Scalar vs Learned-1D vs Direct Policy

这部分已经足以支撑“ordered scalar insufficiency 是条件性真实问题”：

- linear-equations:
  - `ordered_scalar_mu = 0.4228`
  - `learned_1d_linear = 0.2575`
  - `direct_policy = 0.2199`
- arithmetic:
  - `ordered_scalar_mu = 0.1599`
  - `direct_policy = 0.3272`

这说明：

1. linear 域明显支持 scalar insufficiency
2. arithmetic 域不支持把它写成 universal claim
3. 因此主文应写成 conditional scalar insufficiency，而不是 unconditional insufficiency

## 3.3 Factorized Exact-State vs Predicted-State Gap

这条证据链很强，应该进主文：

- linear-equations:
  - `factorized_exact_state = 0.1360`
  - `factorized_predicted_state = 0.2931`
  - `direct_policy = 0.2199`
- arithmetic:
  - `factorized_exact_state = 0.2147`
  - `factorized_predicted_state` 远弱于 exact-state

最重要的解释不是“value head 还不够强”，而是：

1. exact-state 下 factorization 有内容
2. predicted-state 部署差距很大
3. 主瓶颈是 state identification / noisy deployment

---

## 4. Main Paper Structure

## 4.1 Main Text

主文应只保留四个板块：

1. Problem and benchmark
2. Mechanism: ordered scalar insufficiency
3. Structured controller under exact vs predicted state
4. Budgeted decision quality

## 4.2 Main Figures

### Figure 1. Oracle Action Atlas

内容：

- 两个 exact-checker 域的 oracle action atlas
- scalar score 等高线
- crossing region 标注

目标：

- 直接视觉化 “same score, different optimal action”

### Figure 2. High-Determinacy Crossing And Gap

内容：

- crossing mass
- high-determinacy crossing mass
- action-gap histogram
- oracle determinacy rate

目标：

- 说明 crossing 不是 MC 噪声造成的伪现象

### Figure 3. Deployment Gap Decomposition

内容：

- exact-state
- predicted-state-exact-value
- predicted-state

目标：

- 把问题定位到 state identification，而不是泛泛地说“模型还不够强”

### Figure 4. Budgeted Decision Quality

内容：

- Action Regret@Budget
- equal-token frontier
- risk-coverage-compute / abstain utility curve

目标：

- 把 paper 从 prefix tagging 拉回 budgeted reasoning

## 4.3 Main Tables

### Table 1. Controller Class Comparison

每个域主文只放这几类：

1. ordered scalar controller
2. learned-1D ordered controller
3. unstructured direct policy
4. factorized exact-state upper bound
5. best deployable predicted-state factorized controller

### Table 2. Action-Quality Metrics

必须以 decision-quality 为中心：

1. Action Regret@Budget
2. Oracle action accuracy
3. Revision Harm
4. Compute Value Calibration
5. Oracle determinacy rate
6. crossing mass

### Table 3. Repeatability Check

不用 full 8-run everywhere，但主文至少要给关键 within-domain 对照的 repeatability check：

1. 选最关键的一组 linear
2. 选最关键的一组 arithmetic
3. 报 `mean/std`

这样才不会出现“router 讲 multi-seed，主结论却只讲 single-run”的不对称。

---

## 5. Appendix Structure

以下内容应明显下放 appendix：

1. value-head family 全部 sweep  
   ridge / huber / pairwise / interaction / heteroscedastic / low-rank / conditional latent / calibration wrappers

2. richer `S` proxy 的演化链  
   主文只保留“为什么要改名/为什么它不是原教旨 `S_t`”

3. cross-domain routing  
   只保留 family-level 结论：
   - fallback 退役
   - `rf_high_capacity_extra_trees` 是当前默认 learned-router family
   - 报告方式固定为 `mean/std + win counts`

4. negative probes  
   尤其是所有 clearly no-go 的 same-family 或 wrapper 分支

---

## 6. Terminology Fixes

## 6.1 Rename `S_t`

当前最推荐的修正：

- `q_t`: local invalidity risk
- `continuation outcome statistics` 或 `default-continue outcome features`
- `U(a | p_t, b_t ; pi_0)`: 真正的控制对象

不要再让 richer proxy 和 proposal 原始 `S_t ~ Beta(alpha, beta)` 混在一起。

## 6.2 Write The Boundary Explicitly

主文必须明确写：

1. TriVer 的结构性负命题只反驳 ordered scalar controller class
2. 不反驳任意一维编码的存在性
3. factorization 的 strongest claim 目前是 conditional，不是 universal

---

## 7. Minimal Missing Experiments Before Writing

现在最该补的不是新 head，而是 proposal 里缺席的主表指标。

## 7.1 Must Add

1. `Action Regret@Budget`
2. equal-token frontier
3. `Revision Harm`
4. `Compute Value Calibration`

## 7.2 Should Add

1. 一个最小 repeatability check for within-domain main tables
2. abstain / risk-coverage-compute 设定说明

## 7.3 Do Not Prioritize

1. 新 value head family
2. 新 router family
3. 再开新的 same-family micro-sweep

---

## 8. Writing Order

推荐写作顺序：

1. 引言  
   从 “compute control 不是单标量阈值问题” 切入

2. Problem setup and oracle benchmark  
   定义 prefix action oracle、ordered scalar controller class、核心指标

3. Mechanism section  
   Atlas + crossing + determinacy

4. Controller comparison  
   ordered scalar / learned-1D / direct policy / factorized

5. Deployment gap section  
   exact-state vs predicted-state

6. Budgeted decision quality  
   regret / frontier / revision harm / calibration

7. Extension  
   cross-domain routing

8. Limitations  
   conditional claim、`S_t` 退化、domain dependence

---

## 9. Executive Decision

从现在开始，paper 打磨的默认原则应改成：

1. 主文优先 benchmark + scalar insufficiency + budgeted decision quality
2. factorization 写成 conditional claim
3. routing 只保留 extension 地位
4. 新实验优先补 proposal 主指标，而不是继续扫架构

如果后续只能再做少量工作，优先级应是：

1. 补 `Action Regret@Budget` / equal-token frontier
2. 补 `Revision Harm` / `Compute Value Calibration`
3. 做 minimal repeatability check
4. 开始正式写 paper
