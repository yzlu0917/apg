# ToolShift Final Framing

## One-Line Verdict

ToolShift 当前最强结论不是 “SCC 已经被验证成功”，而是：

`schema-visible API evolution` 下，tool-use agent 的关键难点集中在 `negative capability-gap inhibition`；当前最强 retained method 是 `semantic_embedding_capability_gate`，而更 learned 的 pair-model 路线尚未在 held-out family 上稳定替代它。

## Recommended Paper Story

### Main Contribution

1. `set-valued canonical action + deterministic evaluator`
   - 将 `clean / positive near-orbit / negative near-orbit / impossible boundary` 明确拆开
   - 主表只统计 audited `unambiguous core`

2. `audited real evolution benchmark`
   - `dev panel`: `36 cases / 72 views / 63 official sources / 9 vendor families`
   - `blind panel`: `24 cases / 48 views / 42 official sources / 6 family tags across 5 vendors`
   - blind panel 已冻结，只做最终复核

3. `multi-layer validation chain`
   - evaluator correctness
   - execution sanity
   - request replay
   - official-doc smoke
   - api-surface smoke
   - frozen blind review

4. `strong scaffold baseline + diagnosis`
   - strongest retained method：`semantic_embedding_capability_gate`
   - retained learned route：`semantic_clause_localization_capability_gate`
   - 结论：localized description / contract cue 目前仍是稳定 negative inhibition 的关键

### Strongest Empirical Claim

当前最准确的主张是：

`schema-visible capability-gap inhibition` 在真实 API evolution 下可以被稳定评测，并且 description/contract-aware scaffold 能同时拿住 positive invariance 与 negative inhibition。

### What The Paper Should Not Claim

1. 不应 claim：
   - `hidden backend shift` 已被解决
   - `SCC / learned invariance method` 已经被实证验证成功
   - blind panel 上已经得到通用满分解

2. 必须明确写出边界：
   - 当前 strongest result 依赖 `schema-visible description / contract cue`
   - impossible shadow 分析显示，一旦去掉可观察 cue，最强 scaffold baseline 会回到 execute

## Final Method Positioning

### Strongest Retained Method

`semantic_embedding_capability_gate`

- dev panel:
  - `CAA=1.000`
  - `CAA+=1.000`
  - `NOS=1.000`
  - `POC=1.000`
- frozen blind panel:
  - `CAA=0.917`
  - `CAA_clean=0.958`
  - `CAA+=1.000`
  - `NOS=0.727`
  - `POC=1.000`

Interpretation:
- blind drop 主要集中在 `NOS`
- positive retention 在 blind 上仍然完整保住
- 当前最明显 blind 压力点是 `slack_auth`

### Retained Learned Route

`semantic_clause_localization_capability_gate`

- dev panel:
  - `CAA=0.875`
  - `CAA_clean=0.917`
  - `CAA+=0.820`
  - `NOS=0.864`
  - `POC=0.820`
- frozen blind panel:
  - `CAA=0.781`
  - `CAA_clean=0.708`
  - `CAA+=0.885`
  - `NOS=0.818`
  - `POC=0.885`

Interpretation:
- blind `NOS` 更稳
- 但 `CAA_clean / CAA+ / POC` 仍明显弱于 strongest scaffold baseline
- 它更适合作为 learned-route diagnostic / future work，而不是当前主方法

## Mechanism Evidence Already In Hand

### Masking

- `name_mask` 几乎不伤 strongest scaffold baseline 和 retained learned route
- `description_mask / contract_mask` 都会显著掉分

Interpretation:
- 当前真正关键的不是 raw tool/arg 名字
- 而是 localized description / contract cue

### Decision-State Probe

`semantic_embedding_capability_gate` 比 retained learned route 有：

- 更高的 `positive_state_similarity`
- 更大的 `state_separation_gap`
- 更强的 negative probe performance

Interpretation:
- strongest scaffold baseline 不是只在行为上更好
- 它在 internal decision state 上也更稳定地区分了 positive orbit 与 negative near-orbit

### Boundary Evidence

在 `counterfactual impossible shadow` 上：

- `semantic_embedding_capability_gate`
  - `impossible_shadow_CAA=0.000`
  - `impossible_execute_rate=1.000`
- `semantic_clause_localization_capability_gate`
  - `impossible_shadow_CAA=0.136`
  - `impossible_execute_rate=0.864`

Interpretation:
- strongest story 必须明确限定为 `schema-visible evolution`
- 当前方法不能外推成 hidden shift robustness

## Blind Review Takeaway

blind review 的结论不是 “dev 满分在 blind 也成立”，而是：

1. strongest scaffold baseline 仍是 blind 上的最优 retained method
2. blind review 是必要的，因为 dev-perfect 确实会在 blind family 上掉分
3. `slack_auth` 证明 auth/scope/permission semantics 是当前最硬的 blind stress family

## Recommended Framing Decision

当前最稳的论文定位是：

`benchmark / protocol + diagnosis + strong scaffold baseline`

而不是：

`SCC method paper already validated`

## Future Work Positioning

如果要保留 learned route，建议只写成：

1. pair-model 路线已经系统尝试过：
   - frozen pair head
   - cross-encoder threshold/supervised/ranked/pairwise/listwise
   - fine-tuned capability-only
   - multitask
   - hard-negative
   - asymmetric calibration / objective
   - dual-threshold

2. 当前统一结论：
   - 仅换 loss 不够
   - 仅 fine-tune 不够
   - 仅 localization supervision 不够
   - 仅 hard-negative weighting 不够

3. 更合理的 future work 是：
   - stronger learned localization
   - richer supervision
   - blind-level validation before any new method claim

## Citation Pointers

- blind review:
  - `artifacts/real_evolution_blind_review_v1/summary.json`
- dev-vs-blind comparison:
  - `artifacts/real_evolution_dev_vs_blind_v1/summary.json`
- masking:
  - `artifacts/real_evolution_masking_sensitivity_v1/summary.json`
- decision-state probe:
  - `artifacts/real_evolution_decision_probe_v1/summary.json`
- boundary evidence:
  - `artifacts/real_evolution_boundary_evidence_v1/summary.json`
