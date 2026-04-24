# Counterfactual Necessity Training (CNT)

## 0. 合并说明

这份 proposal 以 `idea/11.md` 为主干，保留其最核心的科学对象: **step necessity / harmfulness / stability**。同时吸收两条可兼容但不应单独成线的内容:

- 来自 `idea/9.md` 的 `marginal action value` 视角: 用来强化 CNT 的 **compute-normalized evaluation**，回答“学到 necessity 之后，额外一步推理到底值不值”。
- 来自 `idea/10.md` 的 `verifiability` 视角: 用来补强 CNT 的 **误差分解与评测语言**，尤其是“有正确候选但没被利用”与“根本无可救状态”的区分。

本 proposal **不** 吸收 `idea/12.md` 的双头 controller 结构，因为那已经是另一条完整主线。这里的定位很明确: **CNT 是训练目标与监督对象的重构，不是 inference controller**。

---

## 1. 一句话主张

> 在可验证推理任务上，优化“反事实必要步骤”比优化“最终是否答对”或“观察性 step score”更能提升准确率、faithfulness 与 test-time compute 效率；因为 necessity 比 outcome-only reward 更接近真正的因果 credit。

---

## 2. Proposal 摘要

当前 reasoning post-training 有两个主流监督对象:

- 只看最终结果是否正确
- 对中间步骤做观察性打分

两者都有根本缺陷。前者无法区分“真正推动解题的关键步骤”和“只是出现在成功轨迹里的装饰性步骤”；后者又容易把长度、措辞、模板熟悉度误当作 step quality。CNT 的核心改动，是把 step supervision 的对象从 **observational quality** 改成 **interventional necessity**:

- 删除这一步会不会让原本能成功的轨迹失败
- 修复这一步会不会让原本失败的轨迹转正
- 只改写表述而不改语义时，这一步的重要性是否稳定

由此得到的 step credit，不再是“这一步看起来像不像好步骤”，而是“这一步对最终可解性有没有边际因果贡献”。这会让整个 proposal 同时具备三种价值:

1. 一个新的科学对象: `necessity / harmfulness / stability`
2. 一个新的 benchmark 资产: `CounterTrace`
3. 一个新的训练 recipe: `SFT + necessity pairwise loss + optional light RL refinement`

---

## 3. 为什么这条线值得保留

我保留 CNT 作为一条独立主线，原因不是它“分高”，而是它和其他想法的 **研究对象** 真正不同。

- 相对 verifier/PRM 线: 那些工作主要是在问“如何判断轨迹是否好”。CNT 问的是“轨迹里哪一步真的重要”。
- 相对 compute control 线: 那些工作主要是在问“现在要不要继续算”。CNT 问的是“模型应该被什么样的 dense credit 训练”。
- 相对 agent/tool 线: 那些工作主要是在问“外部接口如何更鲁棒”。CNT 完全聚焦于 reasoning training 本身。

如果这条线做成，它的贡献不是“又一个后训练 recipe”，而是把 reasoning supervision 的对象从结果信号改成 **局部干预下会改变成败的步骤**。这非常像一个可以立住的 scientific object。

---

## 4. 核心研究问题与可证伪预测

### 4.1 Research Questions

1. `RQ1` 反事实 necessity 是否比 outcome-only reward 或观察性 step score 更接近真正的 step importance?
2. `RQ2` 用 necessity 训练出来的模型，是否能在 **相同 token budget** 下获得更高准确率?
3. `RQ3` necessity supervision 是否能显著降低 verbosity reward hacking 和“长但空”的伪推理?
4. `RQ4` necessity 是否能跨数学、代码、formal-lite 任务迁移，还是只是一种 math-specific trick?

### 4.2 Falsifiable Predictions

- `P1` 删除高 necessity 步骤造成的性能下降，应显著大于删除随机步骤或高 entropy 步骤。
- `P2` 只做 paraphrase-control 时，模型对高 necessity 步骤的 credit 应基本稳定；否则说明学到的是表面形式。
- `P3` 在 fixed token budget 下，CNT 的优势主要来自 **减少无效冗长推理**，而不只是把答案写得更长。
- `P4` 若 necessity 真是更好的训练对象，则它应同时提升 `faithfulness` 和 `compute efficiency`；若只提准确率、不提 faithfulness，这条线的说服力会明显下降。

---

## 5. 方法设计

### 5.1 数据对象

每个样本由以下元素组成:

- 问题 `x`
- 一条推理轨迹 `tau = (s_1, ..., s_T)`
- 最终结果验证器 `V(x, tau)`，取值为 `{0,1}` 或 `[0,1]`

为了避免对每一步做人类标注，CNT 只要求最终结果可验证，这使它天然适配:

- 数学推理
- 代码题与单元测试
- theorem-lite / formal-lite
- 可执行规则规划任务

### 5.2 CounterTrace: 反事实步骤编辑协议

对某个步骤 `s_t`，构造以下局部干预:

- `Drop`: 删除该步并让模型续写
- `Swap`: 用同前缀下另一条轨迹的步骤替换
- `Repair`: 对该步做最小修复后续写
- `Paraphrase-control`: 只改写表述，不改语义

这些操作生成一组编辑后轨迹 `tilde_tau_t^(o)`，让我们可以从“如果这一步不存在/被替换/被修复/只改写”四个角度定义 step credit。

### 5.3 Necessity / Harmfulness / Stability

定义:

- `n_t = V(x, tau) - E_o[V(x, tilde_tau_t^(drop or swap))]`
- `h_t = E[V(x, tilde_tau_t^(repair))] - V(x, tau)`
- `u_t = 1 - |V(x, tau) - E[V(x, tilde_tau_t^(paraphrase))]|`

其中:

- `n_t` 衡量“这一步有多必要”
- `h_t` 衡量“这一步是否是一个有害但可修复的错误”
- `u_t` 衡量“这一步的 credit 是否稳定，而不是受表述噪声驱动”

最终 step credit:

`c_t = u_t * (n_t + lambda_h * h_t)`

这里最重要的设计原则是: **只有在反事实下会改变成败的步骤，才配得到高 credit**。

### 5.4 训练目标

在同一前缀 `p_t = (x, s_<t)` 下，构造:

- 正样本步骤 `s_t^+`: 高 credit
- 负样本步骤 `s_t^-`: 低 credit 或 harmful step

训练损失由三部分组成:

1. `L_sft`: 保持基本行为能力
2. `L_step`: 基于 necessity pair 的 pairwise ranking loss
3. `L_credit-reg`: 训练小 critic 预测 `c_t`，供后续 inference 或轻量 RL 使用

总损失:

`L = lambda_sft * L_sft + lambda_step * L_step + lambda_crit * L_credit-reg`

第一阶段只做离线训练。只有在离线结果站得住时，才进入可选的第二阶段:

- 用 critic 预测的 `hat c_t` 做小规模 2-GRPO / RL refinement
- 奖励函数中同时考虑最终正确性、necessity credit 与长度惩罚

### 5.5 与来自 9/10 的融合点

为了让 proposal 不止是“训练 recipe”，这里明确吸收两点:

- 从 `idea/9.md` 融入 **Step Value of Extra Compute**: 在评测时看 necessity 是否能更好预测“多一步推理的真实收益”，而不是只看最终 accuracy。
- 从 `idea/10.md` 融入 **recoverable vs irrecoverable state** 语言: 当某一步 necessity 很低但 future recoverability 很高时，模型应学会继续修正；当 necessity 低且 recoverability 也低时，应避免继续浪费 compute。

这两点只作为 **评测和解释层** 融入，不改变 CNT 的主问题定义。

---

## 6. 数据与实验设计

### 6.1 任务族

第一阶段只做可验证任务，优先级如下:

1. `Math`: MATH-500 / AIME-style / AMC-style
2. `Code`: HumanEval / MBPP / 小规模可复现实例
3. `Formal-lite`: 可执行规则推理、graph planning、symbolic transformation

### 6.2 Baselines

必须至少覆盖四类强基线:

1. Outcome-only RLVR / Dr.GRPO / 2-GRPO 类
2. Dense reward baseline: PRIME 类
3. Fine-grained credit baseline: PURE / Stop Summation 类
4. Strong inference-time baseline: GenRM / verifier rerank / Heimdall-guided rerank

### 6.3 核心指标

- `Pass@1`
- `Verified accuracy`
- `Counterfactual Trace Faithfulness (CTF)`
- `Minimal Sufficient Trace Length (MSTL)`
- `Compute-normalized accuracy`
- `Step importance rank correlation`
- `Verbosity exploitation rate`

### 6.4 Minimum Viable Experiments

1. `Synthetic necessity recovery`
   目标是证明 necessity 不是换个名字的 entropy 或 PRM score。
2. `Main-task accuracy`
   在相同模型规模和训练预算下，对比主流 post-training baseline。
3. `CTF / MSTL`
   删除 top-k necessity steps、随机 steps、paraphrase-control 三组对比。
4. `Reward hacking / verbosity stress test`
   注入冗长但空洞的中间步骤，看模型是否被“长推理”骗。
5. `Compute-efficiency frontier`
   固定 token budget，比较 CNT 与 self-consistency / verifier rerank。
6. `Cross-domain transfer`
   在 code 或 theorem-lite 上验证 necessity 是否保留。

---

## 7. 预期贡献

如果主假设成立，这篇 paper 的贡献应同时落在四层:

1. **新监督对象**: necessity / harmfulness / stability
2. **新 benchmark**: CounterTrace
3. **新训练 recipe**: necessity-driven post-training
4. **新评测语言**: faithfulness 与 compute efficiency 的统一报告

理想状态下，CNT 会成为一个比“outcome-only RLVR”更具有解释性的训练范式。次优状态下，它也至少会成为一篇很强的 benchmark + failure analysis + training recipe paper。

---

## 8. 主要风险与备选路线

### 风险 1

局部编辑协议可能带 artifact，导致模型学到的是编辑痕迹而非 necessity。

应对:

- 使用多编辑器、多模板 paraphrase
- 固定一部分人工 spot-check
- 把“编辑痕迹检测”做成 sanity check

### 风险 2

necessity 强于 faithfulness，但对最终 accuracy 提升有限。

应对:

- 把论文重心转向 `faithful supervision` + `compute-normalized evaluation`
- 保留 accuracy 作为 supporting result，而不是唯一主结果

### 风险 3

跨域迁移不强，只在 math 上成立。

应对:

- 先把 math 做深做透
- 第二域只选一个工程最稳的 code/formal-lite 设置，不强求广泛横跳

---

## 9. 执行计划

### Phase 1: 两周 Go / No-Go

- 搭建 CounterTrace-mini
- 跑 necessity recovery
- 跑至少一个 math 主任务
- 看 CTF 与 verbosity stress test 是否明显优于基线

### Phase 2: 四到六周主结果

- 完成 7B 主模型训练
- 做 main baselines 对比
- 做 compute frontier 与 cross-domain 验证
- 固化 CounterTrace v1

### Phase 3: 加分项

- 轻量 RL refinement
- 机制分析: SAE / attribution / circuit evidence
- 14B 趋势复验

---

## 10. 最终收敛后的 proposal 形态

这份整合后的 CNT proposal，已经不再是原始 `idea/11` 的“单线训练法”，而是一个更完整的主线:

- 主问题更尖锐: **监督对象到底应该是什么**
- 评测更完整: **faithfulness + compute efficiency**
- 与其他三条主线边界更清楚:
  - 它不是 verifier benchmark
  - 不是 inference controller
  - 不是 tool-use robustness

如果四条主线里只能选一条最像“新的 scientific object”，我仍然会把这一条排在第一位。
