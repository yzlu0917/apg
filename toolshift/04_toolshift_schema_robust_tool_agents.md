# ToolShift: Canonical Action Invariance Under Schema Evolution

## 0. Proposal Overview

本 proposal 研究 tool-use agent 是否真正学会了工具语义，而不是只学会了 schema 外观。核心观点是：优秀 agent 应在 **schema-preserving transformation family** 上保持 canonical semantic action 的等价类不变，并在 **near-orbit semantic shift** 上改变动作或拒绝执行。

整条主线围绕四个组件展开：

1. `set-valued canonical action`
2. `positive transformation family / negative near-orbit family`
3. `Schema-Contrastive Consistency (SCC)`
4. `real evolution split`

主证据链收敛为：

`loss -> representation invariance -> name sensitivity down -> OOD robustness up`

---

## 1. 一句话 thesis

> Tool schema 应被形式化为 tool semantics 的观测视图；优秀 agent 应在语义保持的 schema transformation family 上保持 **canonical action admissible set** 不变，并在最小 contract 变化时正确改变动作或拒绝执行。

---

## 2. 问题定义

### 2.1 核心问题

当前很多 tool-use agent 并没有真正学会工具语义，而是在学习：

- tool name 的 lexical prior
- argument name 的表面匹配
- documentation 的常见模板
- 字段顺序与固定格式

因此一旦发生真实部署中常见的 schema 演化：

- rename
- alias
- paraphrase
- distractor insertion
- version bump
- contract change

模型就可能把“schema 外观”误当成“tool 语义”，从而在 shifted setting 下迅速塌陷。

### 2.2 本 proposal 的核心主张

这个问题不应被描述成“字符串鲁棒性”问题，而应被描述成：

> **canonical semantic action 在 schema-preserving transformation family 上的不变性问题。**

也就是说，真正值得研究的不是“名字换了还会不会调用”，而是：

- 在 **语义保持** 的 schema 视图下，模型是否还能做出同一个 admissible canonical action
- 在 **语义变化** 或 **关键信息删除** 的 near-orbit 视图下，模型是否会正确改变 action 或选择 abstain / ask clarification

---

## 3. Canonical Semantic Action 的正式定义

为了让整条主线成立，必须先定义一个不依赖 schema 表面形式的动作空间。

### 3.1 Canonical schema

对每个任务实例，定义一个 canonical schema `S*`，其中每个工具包含：

- canonical tool id
- canonical argument schema
- type / range / dependency constraints
- minimal semantic description

### 3.2 Canonical semantic action

定义 canonical action 的基本单元为：

- canonical tool id
- normalized arguments
- optional control tag：`execute / abstain / ask_clarification`

注意：这里的 canonical action 不是运行时真实调用字符串，而是脱离具体 schema 呈现形式后的**语义动作表示**。

### 3.3 Set-valued admissible action set

主表不再假设每个请求都只有唯一 gold action。  
对每个任务实例，定义：

`A*(x) = {a_1*, a_2*, ..., a_k*}`

其中每个元素都表示一个 **admissible canonical action**。  
这允许以下情况进入主评测而不被错判：

- 多个工具都能等价完成任务
- 多个参数归一化后语义等价
- `ask_clarification` 与 `abstain` 在少数边界样本上存在可审计的并列可接受策略

若无法可靠定义 `A*(x)`，样本进入 `ambiguous split`，不进入主表。

### 3.4 Rendered action

在某个 schema 视图 `S_i` 下，`A*(x)` 中的每个 admissible action 都会被渲染成一个或多个具体调用。  
模型看到的是 `(x, S_i)`，输出的是 schema-specific call；但评测时会先 canonicalize 回 admissible canonical action，再判定是否落在 `A*(x)` 中。

### 3.5 Equivalence checker

本 proposal 不依赖 LLM judge 定义“等价调用”。等价关系由三部分组成：

1. canonical tool id 一致
2. canonicalized arguments 一致
3. control tag 合法
4. contract-compatible

这样 equivalence checker 是 **deterministic canonicalizer + deterministic contract verifier**，而不是隐式 semantic oracle。

其中 `execute / abstain / ask_clarification` 的边界 policy 必须预先写成可审计 guideline；若该 policy 在某类样本上无法稳定给出单一判定，则该类样本进入 `ambiguous split`。

### 3.6 Unambiguous core 与 ambiguous split

为了避免 canonical action 单值假设污染主结论，评测显式拆成两部分：

- `unambiguous core`
  - `A*(x)` 可以高置信定义
  - 进入主表和主要结论
- `ambiguous split`
  - 存在多个 admissible actions，或 control tag policy 不够稳定
  - 单独报告，不拿来支撑主结论

---

## 4. Positive Transformation Families 与 Negative Near-Orbits

这是本版最关键的修正。

### 4.1 Positive transformation family

这些变换应保持 canonical action 不变：

- `Rename`
- `Alias`
- `Reorder`
- `Paraphrase`
- `Distractor insertion`
- 语义保持的 doc reformat

它们共同定义 `G+`。对 `g in G+`，应满足：

`pi(x, g(S*))` canonicalizes to the same admissible action class in `A*(x)`

### 4.2 Negative near-orbits

这些变换不应被当作 invariance 正样本，因为它们改变了语义或可用信息：

- `True deprecate`
- `Type/range mutation`
- `Required-field semantic deletion`
- `Behavior-changing version shift`
- `Critical contract mutation`
- schema/doc/contract 可观察到的 behavior shift

它们共同定义 `G-`。对 `g in G-`，模型应：

- 改变 canonical action
- 或明确 abstain / ask clarification

若行为变化 **不可从 schema/doc/contract 观察到**，则不进入 `G-` 主评测，而进入 `impossible split`。  
ToolShift 的强 claim 只覆盖 **schema-visible evolution**，不覆盖不可观测后端行为变化。

### 4.3 为什么必须拆分

如果把 `drop/mask/deprecate` 也当成 invariance 正样本，训练目标本身就会脏掉。  
这会把“语义不变干扰”与“信息缺失/语义变化”混成一类，从而让训练目标与评测目标同时变脏：

- 你到底在训练鲁棒性
- 还是在训练模型对真实语义变化麻木

因此 ToolShift 的第一原则就是：

> **positive transformation family 学不变性，negative near-orbit family 学敏感性。**

---

## 5. 研究问题与可证伪预测

### 5.1 Research Questions

1. 当前 tool-use agent 的 shifted failure 中，有多少是由 schema shortcut 导致，而不是 planning / memory / context overload 导致？
2. matched-data、matched-budget 下，augmentation-only 是否足够？还是显式 SCC 才能带来 compositional shift 的增量？
3. SCC 学到的增益，是否确实体现在 canonical action state 上，而不是 verifier/repair 的补丁效应？
4. `name sensitivity down -> OOD robustness up` 是否成立？若不成立，则“semantic grounding”机制主张失败。
5. synthetic SES 是否能转移到 real evolution split？若不能，则 benchmark moat 站不住。

这里的 `orbit` 只是简写，不要求严格群作用；更精确的对象是：

- schema-preserving transformation family
- near-orbit transformation family

### 5.2 Falsifiable Predictions

- `P1` 在 matched transformed-data budget 下，SCC 相比 augmentation-only 应在 unseen compositional SES 和 real evolution split 上有稳定优势；若 gap 约等于 0，则一致性原则失败。
- `P2` Across methods，`name masking sensitivity` 的下降应与 OOD schema robustness 提升显著相关；若无相关，机制主张失败。
- `P3` verifier 主要修 `validity`，SCC 主要修 `tool choice + argument grounding`；若不是这样，则 contribution separation 不成立。
- `P4` 在 positive orbit 上 SCC 应稳定，在 negative near-orbit 上 SCC 不应把模型训练得“更钝”；否则它只是 robustness regularization，不是 semantic invariance。

### 5.3 主指标

为了显式区分“该稳时稳”和“该变时变”，主文引入三个核心指标：

- `CAA`
  - Canonical Action Accuracy
  - 输出 canonicalize 后是否落在 `A*(x)` 中
- `POC`
  - Positive Orbit Consistency
  - 同一请求在 positive orbit 内是否稳定落在同一 admissible canonical action 等价类
- `NOS`
  - Near-Orbit Sensitivity
  - 当进入 `G-` 时，模型是否正确改变动作、或输出 `ask_clarification / abstain`

为了避免模型通过过度拒绝刷高 `NOS`，主文必须联合报告：

- coverage
- selective risk
- `NOS@matched-coverage`

主文不会只报成功率，而是至少同时报告 `CAA + POC + NOS`。

---

## 6. 方法设计

## 6.1 数据构造

每个样本包含：

- 用户请求 `x`
- canonical schema `S*`
- admissible canonical action set `A*(x)`
- 一组 positive orbit 视图 `{S_i+}`
- 一组 negative near-orbit 视图 `{S_j-}`

对每个 schema 视图，通过已知映射把 `A*(x)` 渲染成该视图下的 admissible target calls。

### 6.2 模型输入与作用点

模型输入为 `(x, S_i)`。  
关键修正：**SCC 不对整段生成 hidden states 盲目对齐，只对 action state / decision bottleneck 对齐**。

这里的 action state 指：

- tool choice head 的 pooled representation
- argument grounding state
- 生成 tool call 前的决策状态
- control tag 决策状态

原因很简单：如果对全序列 hidden states 粗暴做 invariance，极易约束错对象。

### 6.3 训练目标

训练损失分四部分：

1. `L_ce`
   对 schema-specific rendered action 的标准监督损失。

2. `L_inv`
   在 positive orbit 视图之间，对 canonical action state 做一致性约束。

3. `L_ctr`
   对 negative near-orbit 做对比/分离损失，保证模型不会因为“更鲁棒”而失去语义敏感性。

4. `L_ctl`
   对 `execute / abstain / ask_clarification` 的 control tag 做显式监督，避免模型用过度拒绝逃避 near-orbit。

5. `L_con`
   对 contract violation 加局部惩罚。

总损失：

`L = L_ce + lambda_inv * L_inv + lambda_ctr * L_ctr + lambda_ctl * L_ctl + lambda_con * L_con`

### 6.4 SCC 的真正目标

这里必须强调，SCC 不等价于“多视图 augmentation”。

augmentation-only 的逻辑是：

- 多看一些变换数据，希望模型自己学会归纳

SCC 的逻辑是：

- 明确告诉模型：这些 positive views 在 canonical semantic action 上应一致
- 同时明确告诉模型：negative near-orbits 不应被压扁成同一个 action

因此，本 proposal 的方法学贡献能否成立，完全取决于：

> **在严格 matched-data 条件下，SCC 是否优于 augmentation-only。**

### 6.5 Contract verifier 与 repair 的边界

contract verifier 只允许做：

- JSON syntax 检查
- type 检查
- range 检查
- dependency 检查
- 缺省值补全

repair 只允许 **局部修复**：

- 类型修正
- 缺省字段补齐
- 无歧义依赖修复

repair **不允许**：

- 重选工具
- 重写完整 argument plan
- 语义级重新规划

这样可以避免 verifier / repair 偷走主方法贡献。

### 6.6 Optional canonical bottleneck embodiment

若需要把方法写得更具象，可以把 action-state 具体化为一个显式 canonical bottleneck：

- `z_tool`
- `z_slot`
- `z_ctl`

并用轻量 renderer 把 canonical prediction 渲染回当前 schema view。  
这不是主 proposal 必须项，但它是比 full-sequence consistency 更贴近 thesis 的实现方式。

---

## 7. Benchmark 设计

### 7.1 主 benchmark: ToolShift-Static

主结果只做静态 structured function calling，优先：

1. BFCL
2. StableToolBench 子集

原因：

- schema shortcut 最干净
- planning/memory 干扰最小
- 更利于机制归因

### 7.2 SES 轴

按强度划分：

- `SES-1`: 单一 positive shift
- `SES-2`: 双重组合 positive shift
- `SES-3`: 多重组合 + distractors

负向测试单独报告：

- `NearOrbit-1`: contract mutation
- `NearOrbit-2`: semantic deletion
- `NearOrbit-3`: true deprecate / behavior change

### 7.3 Real evolution split

这是本 proposal 的硬要求，不再是“可选加分项”。

需要构建小规模真实 split：

- 从真实 API / tool schema 版本对中收集 rename、alias、doc rewrite、contract change
- 对每个 diff 标注是 `positive orbit` 还是 `negative near-orbit`
- 同时标注哪些 diff 进入 `unambiguous core`，哪些进入 `ambiguous split`
- 对少量样本做执行验证，避免 canonicalizer policy 与真实行为脱节
- 按 tool family / version lineage 做 holdout，避免同 family 泄漏

没有 real evolution split，这篇 paper 很容易被打成“人造鲁棒 benchmark”。

### 7.4 Impossible split

额外单列：

- hidden behavior change, but schema/doc/contract unchanged

这部分预期失败，而且应该失败。  
它不是主表，而是 boundary result，用来明确 ToolShift 只解决 **schema-visible evolution**。

### 7.5 Human audit

第一周就必须对 transform validity 做人工审计，至少回答：

- positive orbit 是否真的语义保持
- negative near-orbit 是否真的改了语义/信息量

目标是：

- positive orbit 审计有效率 > 95%
- negative near-orbit 标签一致性足够高

---

## 8. 实验设计

### 8.1 Hard baselines

最难打的 baseline 必须包括：

1. Same-base `augmentation-only SFT`
2. Hammer-style robust function-calling
3. PA-Tool-style schema adaptation
4. Tool-description rewriting / repaired schema baseline
5. full-sequence multi-view consistency baseline
6. schema normalization / name anonymization baseline
7. Constrained decoding + deterministic contract verifier
8. Verifier-only / repair-only pipeline

### 8.2 主结果

必须给：

1. clean vs SES 主表
2. success vs SES severity 曲线
3. augmentation-only vs SCC matched-data 对照
4. tool selection / arg grounding / contract violation 误差分解
5. pre-repair / post-repair 双指标
6. `CAA / POC / NOS` 三指标主表
7. real evolution split 主表
8. coverage-controlled `NOS` / selective risk 表

### 8.3 机制证据链

至少三层：

1. `name masking sensitivity`
2. `description/contract masking sensitivity`
3. `action-state orbit similarity / probe`
4. `POC up, NOS not down`

希望形成的证据链是：

`SCC -> action-state more invariant on G+ -> name sensitivity down -> OOD robustness up`

### 8.4 Dynamic transfer

`tau-bench / tau²-bench / FAIL-TALMS / AgentNoiseBench` 不进入主表，只做：

- external validity
- failure boundary
- appendix stress tests

这样才能避免主归因被 planning / memory / simulator variance 弄脏。

---

## 9. Minimum Viable Experiments

1. `Transform validity audit`
   验证 positive orbit 与 negative near-orbit 的标签是否可靠。

2. `Main table: clean vs SES`
   vanilla SFT、AugOnly、SCC-lite 三者对比。

3. `Matched-budget proof`
   严格控制 transformed-data 数量与训练预算，检验 SCC 是否真有独立增量。

4. `Factorized perturbation`
   逐项测 rename、paraphrase、distractor，再测组合 shift。

5. `Error decomposition`
   把错误拆成 tool selection、argument extraction、contract violation。

6. `Mechanism masking`
   对 tool names、descriptions、contracts 做遮蔽，看各方法敏感性如何变化。

7. `Representation analysis`
   看 positive orbit 视图下 action-state 的相似性是否提升。

8. `Real evolution split`
   验证 synthetic SES 的 gains 是否转移到真实版本变化。

9. `Verifier complementarity`
   比较 no verifier / verifier-only / SCC / SCC+verifier。

10. `Family-holdout OOD`
   对未见 tool families / version lineage 做外推。

11. `Impossible split + failure boundary`
   特别报告 hidden behavior change、极弱 doc、semantic deletion、dynamic tasks 等失败设置。

---

## 10. 预期贡献

如果主假设成立，这篇 paper 的贡献应收敛成四个最核心的点：

1. **新问题定义**
   tool-use 中的 schema evolution 应被形式化为 set-valued canonical semantic action 的 orbit invariance 问题。

2. **新评测协议**
   严格区分 positive orbit 与 negative near-orbit，并引入 `unambiguous core / ambiguous split / real evolution split / impossible split`。

3. **新训练原则**
   SCC 不只是 augmentation，而是围绕 decision bottleneck 的显式 invariance + sensitivity 约束。

4. **机制结论**
   鲁棒性提升伴随模型从 lexical shortcut 转向 description / contract grounding。

这是最接近 best-paper 风格的表述方式；而不是“我们又做了一个更 robust 的 tool agent”。

---

## 11. 风险与 Plan B / C

### 风险 1：synthetic SES 不转移到真实 API 演化

后果：

- benchmark moat 变弱
- 机制主张仍可保留，但真实部署价值会被削弱

Plan B：

- 强化 real evolution split
- 把 paper 收敛成 benchmark + diagnosis + partial method

### 风险 2：augmentation-only 追平 SCC

后果：

- 方法学增量直接受损

Plan B：

- 增强 `L_ctr` 与 action-state alignment
- 若仍无增量，诚实转成“augmentation 已足够”的负结果 + benchmark paper

### 风险 3：verifier / repair 吃掉主要提升

后果：

- semantic gain 不清

Plan B：

- 强制报告 pre-repair / post-repair 双指标
- 把 verifier 降为 appendix 或系统补层

### 风险 4：canonical action 非唯一过多

后果：

- 单值 gold 假设会污染主结论

Plan B：

- 主表只保留 `unambiguous core`
- ambiguous cases 单列 appendix

### 风险 5：机制证据弱

后果：

- 论文会退回到普通 robustness paper

Plan B：

- 加 probe + masking + mediation analysis
- 若仍弱，则收缩 claim，不再强调强机制

### 风险 6：`NOS` 被 refusal gaming

后果：

- 模型通过更保守来“显得更敏感”

Plan B：

- 强制报告 coverage-controlled `NOS`
- 把 `ask_clarification / abstain` 的 utility 代价显式写入主表

---

## 12. 六周执行计划

### Week 1

- 定义 admissible canonical action set、canonicalizer、unambiguous core / ambiguous split
- 实现 positive orbit 生成器
- 做 200 条人工审计
- 跑 clean baseline 与 rename/paraphrase/distractor pilot

Go / No-Go：

- baseline 在组合 shift 下至少明显掉点
- positive orbit 审计有效率足够高

### Week 2

- 训练 7B/8B 的 SFT / AugOnly / SCC-lite
- 加基础 contract verifier
- 做第一版 error taxonomy

Go / No-Go：

- SCC 相比 AugOnly 在组合 shift 上至少有稳定优势

### Week 3

- 上 hardest baselines：Hammer-style、PA-Tool-style、schema rewriting、full-seq consistency、name anonymization、constrained decoding
- 做 factorized perturbation

Go / No-Go：

- SCC 至少在组合 shift 上领先一类 hardest baseline

### Week 4

- 做机制分析：name/description masking、probe、orbit similarity
- 开始 real evolution split 标注

Go / No-Go：

- 机制指标与 OOD robustness 方向一致

### Week 5

- 跑 real evolution split
- 跑 family-holdout
- 跑 StableToolBench transfer
- 跑 impossible split
- 选一小部分动态 benchmark 做 external validity

Go / No-Go：

- real split 或 cross-benchmark 至少有一项强阳性

### Week 6

- 补失败边界与统计显著性
- verifier / risk gate 只做 appendix
- 整理 paper figures

---

## 13. Proposal Summary

这条主线的核心不是把 benchmark、regularizer、verifier 和 gate 堆在一起，而是建立一个围绕 **set-valued canonical action** 的明确问题定义：tool agent 应对 schema-preserving orbit 保持不变、对 contract-changing near-orbit 保持敏感，并在不可观测变化上诚实失败。只要 `CAA/POC/NOS`、matched-data SCC、real evolution split 和 impossible split 四条证据链同时成立，ToolShift 就能从一般性的鲁棒性工作收敛为一个更清晰的机制型 proposal。
