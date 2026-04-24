# Paper Assembly: Main Text / Appendix Mapping

## 0. Purpose

这份文档不是新的 proposal，也不是新的实验计划。它的目标是把当前已经成立的证据链压缩成可直接写 paper 的装配清单：

1. 主文写什么
2. 每个主图 / 主表从哪里取数
3. 哪些话可以写强，哪些只能写弱
4. 哪些结果必须下放 appendix

默认前提：当前 paper 走 `benchmark + mechanism + budgeted decision quality` 主线，而不是继续做 controller family 搜索。

---

## 1. Main-Text Claim Boundary

## 1.1 Claims To Write Strong

1. 在可验证推理里，prefix 级 compute allocation 更像 process-state control，而不是 ordered scalar thresholding。
2. prefix-level oracle benchmark 是必要的，因为：
   - crossing 是可测且非平凡的
   - determinacy 足够高，crossing 不是纯 MC 噪声
3. exact-state 与 predicted-state 之间的稳定 gap 说明主瓶颈在 state identification / noisy deployment。

## 1.2 Claims To Write Weak

1. ordered scalar insufficiency 是 conditional 的，不是 universal theorem。
2. factorization 在 exact-state 下有明确价值，但 deployable predicted-state 表现强域依赖。
3. direct policy 仍是 hardest-to-beat baseline，不能写成已被统一击败。
4. 当前 richer `S` proxy 不再等于 proposal 原始的 `S_t`；主文应改写为 continuation outcome statistics。

## 1.3 Claims To Avoid

1. “TriVer factorization universally beats direct policy”
2. “单一 scalar 在所有域都不够”
3. “当前 richer proxy 就是完整 `S_t`”
4. “cross-domain routing 是 paper 主问题”

---

## 2. Main Figures

## Figure 1. Oracle Benchmark / Action Crossing

### What it should show

1. 两个 exact-checker 域都存在非平凡 action crossing
2. crossing 在高 determinacy 子集里仍然存在

### Recommended source artifacts

- linear:
  - source metrics: [summary.json](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_data_v2/summary.json)
  - source records: [prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv)
  - current visual prototype: [oracle_action_atlas.png](/cephfs/luyanzhen/apg/triver/outputs/week1_linear_8b_smoke/oracle_action_atlas.png)
  - current visual prototype: [scalar_crossing.png](/cephfs/luyanzhen/apg/triver/outputs/week1_linear_8b_smoke/scalar_crossing.png)
- arithmetic:
  - source metrics: [summary.json](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v2/summary.json)
  - source records: [prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv)
  - current visual prototype: [oracle_action_atlas.png](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v1/oracle_action_atlas.png)
  - current visual prototype: [scalar_crossing.png](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v1/scalar_crossing.png)

### Numbers to cite

- linear:
  - `oracle_determinacy_rate = 0.7414`
  - `crossing_mass_all = 0.7414`
  - `crossing_mass_high_determinacy = 0.7674`
- arithmetic:
  - `oracle_determinacy_rate = 0.8548`
  - `crossing_mass_all = 0.8065`
  - `crossing_mass_high_determinacy = 0.7925`

### Note

linear 的现成 atlas/crossing 图目前来自 smoke run；paper 最终版应从 [prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv) 重新出图，保证图与主表口径一致。

## Figure 2. Determinacy / Action Gap

### What it should show

1. crossing 不是低 determinacy 噪声区里的伪现象
2. action-gap 与 determinacy 支撑 oracle benchmark 的可靠性

### Recommended source artifacts

- linear:
  - source records: [prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv)
  - current visual prototype: [action_gap_histogram.png](/cephfs/luyanzhen/apg/triver/outputs/week1_linear_8b_smoke/action_gap_histogram.png)
- arithmetic:
  - source records: [prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv)
  - current visual prototype: [action_gap_histogram.png](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_data_v1/action_gap_histogram.png)

### Numbers to cite

- linear: `mean_action_gap = 0.4921`
- arithmetic: `mean_action_gap = 0.6625`

## Figure 3. Deployment Gap Decomposition

### What it should show

1. factorization 在 exact-state 下有价值
2. predicted-state 部署 gap 明显存在
3. paper 的 deployment bottleneck 是 state identification / noisy deployment

### Recommended source artifacts

- baseline class comparison:
  - [summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_baselines_v2/summary.csv)
  - [summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_baselines_v2/summary.csv)
- exact / predicted factorized anchor:
  - linear exact-state source: [summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_factorized_v4_sproxy/summary.csv)
  - arithmetic exact-state source: [summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_factorized_v21_uncertainty_conditional_lowrank_covariance/summary.csv)
- paper main-text deployment summary:
  - [budget_axis_domain_overall_main.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/budget_axis_domain_overall_main.csv)
  - [within_domain_repeatability_summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_maintext_repeatability_v1/within_domain_repeatability_summary.csv)

### Numbers to cite

- small-data anchor:
  - linear:
    - `ordered_scalar_mu = 0.4228`
    - `learned_1d_linear = 0.2575`
    - `direct_policy = 0.2199`
    - `factorized_exact_state = 0.1360`
    - `factorized_predicted_state = 0.2931`
  - arithmetic:
    - `ordered_scalar_mu = 0.1599`
    - `direct_policy = 0.3272`
    - `learned_1d_linear = 0.3381`
    - `factorized_exact_state = 0.1553`
    - best deployable predicted-state anchor near `0.3388`

### Paper-safe wording

不要写成“factorization 已经赢了 direct policy”。应写成：
- exact-state 上界说明 factorization 有内容
- predicted-state 部署 gap 是稳定主问题

## Figure 4. Budgeted Decision Quality

### What it should show

1. `Action Regret@Budget`
2. equal-token frontier
3. budget-conditioned controller ranking

### Recommended source artifacts

- [action_regret_at_budget_by_domain.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/action_regret_at_budget_by_domain.csv)
- [equal_token_frontier_by_domain.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/equal_token_frontier_by_domain.csv)
- [budget_axis_domain_budget_winners.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/budget_axis_domain_budget_winners.csv)

### Numbers to cite

- arithmetic budget-bin wins:
  - `direct_policy = 6`
  - `ordered_scalar_mu = 4`
  - `factorized_exact_state = 4`
- linear budget-bin wins:
  - `direct_policy = 8`
  - `factorized_exact_state = 5`
  - `ordered_scalar_mu = 0`

---

## 3. Main Tables

## Table 1. Controller Class Comparison

### Rows

1. `ordered_scalar_mu`
2. `learned_1d_linear`
3. `direct_policy`
4. `factorized_exact_state`
5. `factorized_predicted_state_selected`

### Sources

- overall main table:
  - [budget_axis_domain_overall_main.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/budget_axis_domain_overall_main.csv)
- repeatability:
  - [within_domain_repeatability_summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_maintext_repeatability_v1/within_domain_repeatability_summary.csv)
- selected predicted baseline metadata:
  - linear: [run_config.json](/cephfs/luyanzhen/apg/triver/outputs/week2_linear_8b_budget_eval_v1/run_config.json)
  - arithmetic: [run_config.json](/cephfs/luyanzhen/apg/triver/outputs/week2_arithmetic_8b_budget_eval_v1/run_config.json)

### Important note

`factorized_predicted_state_selected` 不是同一个底层配置跨域通用：
- linear uses `factorized_predicted_state_train_exact_plus_oof`
- arithmetic uses `factorized_predicted_state_train_exact`

主文里必须把它表述为“one selected deployable factorized controller per domain”。

## Table 2. Action-Quality Metrics

### Metrics

1. overall regret
2. oracle action accuracy
3. revision harm
4. compute value calibration

### Sources

- overall main metrics:
  - [budget_axis_domain_overall_main.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/budget_axis_domain_overall_main.csv)
- revision harm:
  - [revision_harm_by_domain.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/revision_harm_by_domain.csv)
- calibration:
  - [compute_value_calibration_summary_by_domain.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_budget_axis_v1/compute_value_calibration_summary_by_domain.csv)

### Stable takeaways

1. linear 上 `factorized_exact_state` calibration 最强
2. `factorized_predicted_state_selected` 在两个域上 calibration 明显更差
3. revision harm 主要残留在 factorized controllers，尤其 deployable predicted-state

## Table 3. Within-Domain Repeatability

### Purpose

修正 single-run 叙事，不再把局部 frontier 当成 paper 主结论。

### Sources

- [within_domain_repeatability_summary.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_maintext_repeatability_v1/within_domain_repeatability_summary.csv)
- [within_domain_repeatability_best_by_run.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_maintext_repeatability_v1/within_domain_repeatability_best_by_run.csv)
- [within_domain_repeatability_win_counts.csv](/cephfs/luyanzhen/apg/triver/outputs/week2_maintext_repeatability_v1/within_domain_repeatability_win_counts.csv)

### Paper-safe takeaway

1. linear:
   - `ordered_scalar_mu` 稳定最差
   - `learned_1d_linear / direct_policy / factorized_exact_state` 是更强前列 cluster
2. arithmetic:
   - `direct_policy / learned_1d_linear` 在 `100-sample` repeatability 下已系统性优于 `ordered_scalar_mu`
3. 因此 controller ranking 必须按 domain 和 data/repeatability setting 报告

---

## 4. Appendix Mapping

这些结果保留，但不进入主文主线。

## 4.1 Value-Head Sweep

保留到 appendix：
- ridge / huber / noise-weighted
- pairwise / interaction
- heteroscedastic / low-rank / conditional latent
- calibration wrappers

role：
- 证明“我们已经认真追过 deployable factorization”
- 但不让它们接管主文

## 4.2 Continuation Outcome Features

保留 richer `S` proxy 演化，但主文统一改名为：
- `continuation outcome statistics`
- `default-continue outcome features`

不要再把 richer proxy 与原始 `S_t` 直接等同。

## 4.3 Cross-Domain Routing

保留为 extension，只报告 family-level 结论：

1. shared learned routing 在足够 supervision 下可在均值上优于 hard specialist
2. `rf_high_capacity_extra_trees` 是当前默认 learned-router family
3. router 结果必须报告 `mean/std + win counts`

不要让 routing 重新进入主文核心。

---

## 5. Immediate Writing Order

1. 用这份文档锁定主文图表集合。
2. 先写 main results section：
   - oracle benchmark
   - controller comparison
   - deployment gap
   - budgeted decision quality
3. 再写 limitations / conditional claim section。
4. 最后把 value-head 与 routing sweep 下放 appendix。

---

## 6. Handoff Note

如果下一轮直接开始写 paper，本文件应作为唯一装配入口；默认不再重新搜索结果目录，除非：

1. 需要把 smoke prototype 重新渲染成 final figure
2. 需要补充更精细的 caption 数字
3. 需要把 appendix 中的某个 family sweep 单独拉出来解释
