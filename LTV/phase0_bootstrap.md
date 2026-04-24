# Phase 0 Bootstrap

## 1. 当前阶段结论

这个项目当前不应把论文 headline 直接押在“方法已经更强”或“部署已经有效”上。基于 `proposal.md`，现阶段最稳的推进方式是：

- 先把 **object claim** 作为 headline
- 把 **method claim** 和 **deployment claim** 明确降为 conditional claim
- 用 gate 机制阻止项目在证据不足时直接跳到 utility/storytelling

当前默认路线：

- 主 headline：`process supervision` 可能在监督错误对象，正确对象更接近 **latent state transition**
- 最小执行闭环：先做 **Object gate**
- 最小干净域：**Lean clean-room**
- 最小 nuisance 检查：**CTS-mini**（小型 same-semantics / semantic-flip stress slice）

## 2. Claim Hierarchy

### 2.1 Object / measurement claim

**当前 headline claim**

局部推理正确性更自然地体现在**步骤边界前后的潜在状态转移**中，而不是文本步骤本身；因此，评估 process supervision 时，不能只看 nominal accuracy，还必须看 invariance 与 semantic sensitivity。

**当前允许说到的范围**

- latent transition 是一个值得单独检验的监督对象
- 这个对象应先在 clean-room 和 counterfactual stress test 下被验证
- headline 先停留在 object/measurement 层，不先承诺稳定 utility 增益

### 2.2 Method claim

**conditional claim**

一个 `task-conditioned latent transition verifier (LTV)`，如果读取步骤边界前后 hidden states 与 transition features，并在 matched-budget 下比较，应当比强文本 verifier 更稳健。

**只有在以下条件满足后才升级**

- Object gate 通过：对象信号存在
- Audit gate 通过：信号不是 parser/style/leakage artifact

### 2.3 Deployment / utility claim

**late-stage conditional claim**

如果 object 与 method 都成立，则 LTV 的测量信号应能在相同 token budget 下转化为更好的 reranking、pruning 或 targeted revision utility，并能扩展到 harder / OOD / second-domain 设置。

**只有在以下条件满足后才升级**

- Conversion gate 通过：测量真的转成 decision gain
- Scale gate 通过：收益不是单一 slice 偶然现象

### 2.4 当前明确不提前声称的内容

- 不提前声称“latent verifier 全面优于最强文本 judge”
- 不提前声称“跨任务存在统一 truth geometry”或“不存在统一 truth geometry”
- 不提前声称“measurement gain 一定能转成 control gain”
- 不提前声称“自然语言数学 headline 已经站稳”，在此之前 Lean 只作为 clean-room object gate

## 3. Fallback Paper Framing

## 3.1 Fallback A：measurement + mechanism paper

**建议 framing**

`Current process verifiers are evaluated on the wrong axes: counterfactual invariance reveals a supervision-object mismatch.`

**可交付内容**

- 一个小而锋利的 CTS-style stress test
- same-semantics / semantic-flip 下的 invariance/sensitivity 分析
- 证明当前文本 verifier 在 object 层面存在系统性缺口
- LTV 只作为 diagnostic probe，不强推它必须带来大规模 utility

**适用条件**

- Object gate 成立
- Conversion gate 不成立，或 utility 提升不稳定

## 3.2 Fallback B：Lean clean-room only

**建议 framing**

`In a clean executable process-oracle setting, latent transition supervision is a better object than textual step supervision.`

**可交付内容**

- Lean tactic-level local soundness 的 clean-room 比较
- transition vs post-state vs text-only 的机制分析
- 对自然语言噪声与风格混杂做更干净的隔离

**适用条件**

- 自然语言 math 侧标签与 CTS 构造噪声过高
- Lean 上 object signal 明显更干净

## 3.3 收束原则

- 若主方法失败，仍至少保住 benchmark/protocol/diagnosis/object-identification 之一
- 不为了保住“大主线”而事后放宽 gate、换指标或偷改 story

## 4. Gate Definitions

## 4.1 Object gate

**要回答的问题**

latent transition 是否比文本步骤更接近“局部正确性”这个对象？

**冻结范围**

- 一个 generator family
- 一个 clean-room 域：Lean mini slice
- 一个 counterfactual stress slice：CTS-mini
- 一个冻结模型族起步，不做多模型 sweep
- 不使用更长 verifier CoT 作为增益来源

**最小证据**

- transition probe 在下列信号里至少满足一项：
  - 在 matched semantic sensitivity 下，`IG` 相对强文本基线下降至少 `20%`
  - 在 Lean mini slice 上，`earliest-fail localization` 或局部 soundness 绝对提升至少 `3` 个点
  - `transition` 明显优于 `post-state-only`

**go**

- 信号稳定高于随机
- 至少一个 object-specific 指标过阈值
- 不依赖更长 verifier reasoning

**no-go**

- transition 与 post-state/text control 都无显著差别
- object 信号只在一个脆弱 slice 上出现，且无法复核

**no-go 后动作**

- 收缩为 `latent state sufficiency` 而不是 `transition superiority`
- 或直接转 Fallback A / Fallback B

## 4.2 Audit gate

**要回答的问题**

Object gate 看到的信号，是否可能只是 parser、rewriter、长度、位置或 generator-family artifact？

**最小审计项**

- meta-only baseline：只用 step position / length / domain id
- post-state-only baseline
- `text PRM + same/flip regularizer` 控制
- hold-out rewriter 或不同改写来源的小审计
- 至少一个 leakage 检查：例如 prompt template / style source 隔离

**go**

- object 优势在至少 `2/3` 个关键审计项下仍保留
- meta-only baseline 无法追平主结果
- hold-out rewriter 下结果方向不翻转

**no-go**

- gains 在控制后基本消失
- meta-only 或 rewriter-source 解释力接近主方法

**no-go 后动作**

- headline 改写为 benchmark/artifact diagnosis
- 暂停向 utility 和 scale 扩张

## 4.3 Conversion gate

**要回答的问题**

更好的 measurement 能否在相同预算下带来更好的 decision utility？

**最小设置**

- 单域
- 单一 best-of-N rerank 或 pruning 任务
- 冻结 generator
- matched token budget

**go**

- final utility 绝对提升至少 `2-3` 个点，或
- 在 matched utility 下 token 成本下降至少 `15%`

**no-go**

- IG/AUROC 变好，但 utility 没有稳定正增益

**no-go 后动作**

- 论文主张收缩为 measurement/mechanism
- 不把 control / search gain 写成 headline

## 4.4 Scale gate

**要回答的问题**

是否值得扩大到更大模型、第二域、OOD benchmark 和 recipe sweep？

**前提**

- Conversion gate 已通过

**go**

- 至少一个 robustness 维度成立：
  - harder benchmark
  - second generator family
  - Lean / math 双域之一的外推
- seed variance 不吞没主增益

**no-go**

- 只在单一 dev slice 成立
- 扩展后收益方向不稳定

**no-go 后动作**

- 停止大 sweep
- 收束为单域或 clean negative / partial-result branch

## 5. Object Gate Minimal Loop

## 5.1 默认最小闭环

默认先走 `Lean-first object loop`，原因是它最容易回答“对象是否存在”，而不是先把结果混进自然语言噪声里。

**Loop-O0 组成**

- 域：Lean clean-room
- 模型：一个本地 prover family 起步
- 表示：`h^-` / `h^+` / `Δh`
- 对照：
  - text-only step baseline
  - post-state-only baseline
- 指标：
  - local soundness AUROC / F1
  - earliest-fail localization
- 附加小审计：
  - 一个小型 `CTS-mini` 或等价 tactic rewrite slice，用来测 same/flip 的最小 invariance

## 5.2 当前冻结决策

- headline 先不押自然语言数学
- path-viability 不是 phase 0 必需项
- LoRA / RL / generator 联训明确不进 phase 0
- 多模型交叉不是 phase 0 必需项

## 5.3 已确认的本地可用性

根据本地检查，当前已经确认：

- `infer` conda 环境存在
- 本地缓存里可见 `Qwen3-1.7B`、`Qwen3-4B`、`DeepSeek-Prover-V2-7B`、`ReasonFlux-PRM-7B`

这意味着 phase 0 不存在明显的环境级阻塞。

## 5.4 Object gate 的第一批冻结物

在真正跑训练前，必须先冻结以下最小对象：

1. `Lean-mini-v0`
   - 规模：`200-500` 个 tactic step
   - 标签：可执行 local soundness
   - 用途：object existence

2. `CTS-mini-v0`
   - 规模：`100-200` same pairs + `100-200` flip pairs
   - 用途：最小 invariance / sensitivity stress test

3. `feature-spec-v0`
   - 层数：先用少量 boundary layers
   - 表示：`h^-`、`h^+`、`Δh`
   - 不做全序列 pooling

4. `metric-spec-v0`
   - 主指标：AUROC、earliest-fail localization、IG、SS
   - 接受规则：只认预先写下的 go/no-go

## 6. 接下来 5-7 天的最小执行计划

## Day 1

- 冻结 `Lean-mini-v0`、`CTS-mini-v0`、`feature-spec-v0`、`metric-spec-v0`
- 用最小 smoke run 验证本地模型加载、hidden-state 读取、step boundary 表达是通的

## Day 2

- 实现或整理 step boundary parser / extractor
- 在 `20-50` 个 Lean steps 上跑通边界特征缓存
- 写入第一条真正的可复现命令与输出路径

## Day 3

- 构建 `Lean-mini-v0`
- 做标签核查与失败样例抽样
- 建立 text-only / post-state-only / transition 三个最小 baseline

## Day 4

- 跑第一版 object-only probe
- 先看 local soundness 与 earliest-fail，不急着追 nominal 大表

## Day 5

- 构建 `CTS-mini-v0`
- 跑 first-pass `IG / SS`
- 判断是否达到 Object gate 的最小 go/no-go 阈值

## Day 6

- 若 Object gate 有信号：补最小 Audit controls
- 若 Object gate 无信号：立即收缩 claim，不继续堆更大 recipe

## Day 7

- 写 phase 0.5 决策 memo
- 明确进入 `Audit gate` 还是转 `Fallback A / B`

## 7. 当前默认假设与影响

- 默认先用 Lean 作为 object gate 起点；影响是 headline 自然语言 math 会后置，但能显著减少噪声和返工
- 默认 path-viability 不进入第一轮；影响是当前只验证对象存在性，不验证更强的控制能力
- 默认 phase 0 先用单模型族；影响是跨模型泛化不会在本轮得出结论
