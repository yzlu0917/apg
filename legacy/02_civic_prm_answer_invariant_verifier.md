# CIVIC-PRM: Answer-Invariant and Exploit-Resistant Process Verification

## 0. 合并说明

这份 proposal 以 `idea/8.md` 为主干，保留其最有辨识度的中心命题: **当前 verifier/PRM 的核心 shortcut 是 outcome leakage**。在此基础上做三处有选择的吸收:

- 吸收 `idea/2.md` 的 `Verifier Stress Test (VST)` 与 counterfactual invariance 训练视角，把评测从普通 step accuracy 升级为 **style-preserving but correctness-flipping** 压力测试。
- 吸收 `idea/3.md` 的 `CF-TraceBench-mini` 与 RLVR 接口，把 proposal 从“好评测”推进到“可进入 reranking 与 training loop 的 verifier”。
- 吸收 `idea/1.md` 的 exploit/hack 视角与校准思路，但只保留 **hard-negative mining + hackability evaluation**，不引入过重的 conformal 全家桶。

最终收敛后的定位是:

> **这是一条 verifier 主线，不是 reasoner 训练主线。它要回答的是: 怎样训练一个真正看过程、而不是偷看答案的 process verifier。**

---

## 1. 一句话主张

> 用由 symbolic / formal state trajectory 生成的“答案匹配反事实 reasoning traces”训练 answer-invariant verifier，可以显著降低 outcome leakage，提升跨域泛化、校准与 test-time selection 的可靠性，并让 verifier 真正成为可复现实验对象，而非脆弱启发式评分器。

---

## 2. Proposal 摘要

大量 verifier/PRM 工作看起来在判断“过程是否正确”，但实际上很可能在判断:

- 最终答案像不像对
- 轨迹格式是否像训练集中常见的成功轨迹
- 某些长度、措辞、模板是否高频共现

这就是 `outcome leakage`。如果不打掉这个 shortcut，再大的 verifier 也可能只是一个会看答案气味的 judge，而不是 process verifier。

为解决这个问题，本 proposal 把三件事情打包成一条主线:

1. **新问题定义**: answer-invariant verification
2. **新数据协议**: CRAFT + CF-TraceBench
3. **新训练与评测**: matched-pair ranking + answer adversary + exploit hard negatives

这条线的核心贡献不是“又一个更强 PRM loss”，而是让 verifier 真正被约束去学习 **step validity**，并且可以用反事实协议稳定地审计它到底学没学到。

---

## 3. 为什么这条线必须独立保留

这条主线和 CNT 的区别很大:

- CNT 关注的是 **如何给 reasoner 训练 credit**
- CIVIC-PRM 关注的是 **如何训练与评估 verifier**

和 TriVer 的区别也很大:

- TriVer 关注的是 **如何做 continue / revise / branch 控制**
- CIVIC-PRM 关注的是 **如何得到一个可信 process signal**

如果不单独保留 verifier 主线，compute control 和 process training 两条线都会失去一个可靠的中间基础设施。

---

## 4. 研究问题与可证伪预测

### 4.1 Research Questions

1. `RQ1` 当前强 verifier 在答案匹配反事实对上是否显著崩溃?
2. `RQ2` answer-invariant 训练是否真的降低了 hidden-state 中对 final answer correctness 的泄漏?
3. `RQ3` 更好的 process verifier 能否转化成更高的 best-of-N selection gain 与更低的 exploitability?
4. `RQ4` 如果只做普通 step BCE，而不做 matched-pair / adversarial / group-DRO，是否足够?

### 4.2 Falsifiable Predictions

- `P1` 现成 PRM 在普通指标上不差，但在 `AMCD/VST` 上会明显掉点。
- `P2` answer-invariant 训练后，hidden-state 对 final answer correctness 的可预测性下降，但对 step validity 的可预测性上升。
- `P3` 在同样 candidate pool 下，CIVIC-PRM 的 selection gain 应优于标准 PRM，尤其在“答案偶然对、过程其实错”的集合上。
- `P4` exploit hard negatives 会让模型更抗 `high-score wrong trace`，而不是只在干净分布上变强。

---

## 5. 方法设计

### 5.1 CRAFT: Counterfactual Reasoning Audits for Faithful Traces

数据构造原则很简单:

1. 先在可验证环境中拿到精确状态轨迹
2. 再把状态转移 verbalize 成自然语言 reasoning steps
3. 对同一轨迹做最小干预，构造不同反事实类型

核心反事实类型:

- `Invalid-Step`: 中间关键步做局部错误变换
- `Delayed-Repair`: 中间出错、后面修回来
- `Lucky-Answer`: 过程错但答案被强行改对
- `Answer-Swap`: 过程不变，只换 final answer
- `Paraphrase`: 语义不变，只换表述

其中最关键的是 **答案匹配反事实对**，也就是固定最终答案，只改中间过程；这样 verifier 就无法再靠“答案像不像对”做捷径。

### 5.2 训练目标

verifier backbone 使用 1.5B/3B 做 MVE，7B 做主结果。输入为:

- `problem`
- `reasoning prefix up to step t`
- `candidate current step`

输出为 step validity logit，整条轨迹分数由 step logits 聚合得到。

损失由四部分组成:

1. `L_step`: step-level BCE
2. `L_pair`: 在 answer-matched 正负轨迹对上做 pairwise ranking
3. `L_adv`: gradient reversal，抑制表征中的 final-answer correctness 泄漏
4. `L_gdro`: 针对 natural / invalid-step / delayed-repair / lucky-answer / answer-swap 等 group 做 worst-group 优化

### 5.3 从 1/2/3 吸收后的增强设计

整合后不再是单纯的 CIVIC-PRM，而是一个更完整的 verifier stack:

- 来自 `idea/2.md`: `VST` 作为统一压力测试协议
- 来自 `idea/3.md`: `CF-TraceBench-mini` 作为轻量先行 benchmark 与 RLVR 接口
- 来自 `idea/1.md`: 引入 exploit hard negatives，也就是让攻击者专门生成高 verifier 分但最终错误的轨迹，用来补足自然分布看不出的漏洞

但这里刻意 **不** 把 `idea/1.md` 的 conformal 风险控制完整吸进来。原因是那会把 proposal 从“verifier 训练与评测”拖向“search-time risk control”，边界会变脏。

### 5.4 可选校准层

为了把 verifier 变成可用系统组件，而不仅仅是 benchmark model，保留一个轻量校准层:

- temperature scaling
- split conformal thresholding

校准层的作用只有两个:

- 让 selection / abstain 更可控
- 让 exploitability report 更可信

这里不追求重理论，只追求把 verifier 输出变成可以用于 downstream 决策的概率化信号。

---

## 6. 评测设计

### 6.1 核心指标

- `AMCD`: Answer-Matched Counterfactual Discrimination
- `VST`: Verifier Stress Test
- `Step validity AUROC`
- `Selection gain @ N`
- `ECE / Brier / AURC`
- `Exploitability rate`
- `OOD transfer drop`

### 6.2 Baselines

至少需要以下五类:

1. 标准 PRM
2. PQM / ranking-style PRM
3. 强 frontier judge / strong reasoning evaluator
4. Hidden-state probe verifier
5. Outcome-only verifier / reference-based reward

### 6.3 Minimum Viable Experiments

1. `Shortcut audit`
   对现有 PRM / judge / probe 同时跑普通 step accuracy 与 AMCD/VST。
2. `Core ablation`
   比较 `step-only`、`+pair`、`+answer adversary`、`+group-DRO`。
3. `Best-of-N reranking`
   固定 generator，比较不同 verifier 的 selection gain。
4. `Calibration and selective abstention`
   看 answer-invariance 是否转化成更好的 calibration。
5. `Cross-domain transfer`
   train on algebra + graph + planning，test on held-out family / code / formal-lite。
6. `Exploit hard negatives`
   比较标准 PRM 与 CIVIC-PRM 在 `high-score wrong trace` 攻击下的差异。
7. `Mechanistic validation`
   用 probe 测 hidden-state 中的 answer leakage 是否真的降低。

---

## 7. 预期论文贡献

如果主假设成立，这条主线会形成一个很完整的 paper package:

1. 一个新的 verifier 问题定义: `answer-invariant verification`
2. 一个新的数据资产: `CRAFT / CF-TraceBench`
3. 一组新的评测指标: `AMCD / VST / exploitability`
4. 一个新的训练 recipe: `pair ranking + adversary + group-DRO`
5. 一条很强的机制结论: **当前 verifier 的主要 shortcut 是 outcome leakage**

这类贡献很适合冲“benchmark + mechanism + method”的强 paper，而不是纯工程改分。

---

## 8. 风险与备选路线

### 风险 1

symbolic / formal verbalization 过于模板化，导致模型学到的是数据风格而不是真正的 process validity。

应对:

- 多 verbalizer、多风格 paraphrase
- 数据审计前置
- 在真实模型生成 CoT 上做少量 alignment 检查

### 风险 2

AMCD 很强，但对最终系统指标提升有限。

应对:

- 把论文重心转为“新的 verifier evaluation principle + benchmark”
- 方法结果做 supporting result，而不是唯一卖点

### 风险 3

adversarial head 过强，误删了对下游 selection 有用的信息。

应对:

- 用 conditional orthogonality 或 HSIC regularization 代替暴力 adversary
- 只在 matched-pair 上施加强不变性约束

---

## 9. 执行计划

### Phase 1: 两周 Go / No-Go

- 做 `CRAFT-mini`
- 跑一组现有 verifier 的 `AMCD/VST`
- 验证 outcome leakage gap 是否真实存在

### Phase 2: 四到六周主结果

- 训练 7B CIVIC-PRM
- 做 reranking、OOD、calibration、exploitability
- 固化 `CF-TraceBench v1`

### Phase 3: 加分项

- 接入小规模 RLVR / verifier-guided training
- 做更强机制分析
- 扩到 code / formal-lite

---

## 10. 最终收敛后的 proposal 形态

这份整合稿相对于原始 idea 的优化很明确:

- 不再有 `1/2/3/8` 四篇互相争夺“counterfactual verifier 主线”
- 统一成一篇 **问题定义最清楚、评测最硬、方法最有边界感** 的 proposal
- 保留了来自其他稿子的优点，但把过重、过散、过理论化的部分拿掉

最终版本的核心就是一句话:

> **先把 verifier 训练成真正看过程的 verifier，再谈 process reward、search 和 compute control。**
