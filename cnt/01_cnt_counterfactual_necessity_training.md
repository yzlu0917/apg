# Counterfactual Necessity Training: Trajectory-Conditional Solvability Credit for Reasoning

## 0. Proposal Overview

本 proposal 研究 reasoning supervision 的核心对象应如何定义。核心观点是：在可验证推理中，局部步骤的监督信号不应只来自最终结果，也不应只来自观察性的 step quality，而应来自 **trajectory-conditional counterfactual solvability credit**。

为此，proposal 将局部信用拆分为三个彼此独立但相关的对象：

- `N`: success-conditioned necessity
- `H`: failure-conditioned harmfulness / repairability
- `S`: stability / confidence

其中主文只把 `N + S` 作为核心对象；`H` 保留为 failure-side analysis / appendix 候选。`S` 只作为 sample weight / filter，而不与 `N/H` 混成单一 value。整条主线围绕三个目标展开：

1. 定义并识别 trajectory-conditional 信用对象
2. 验证它是否能提升 trace faithfulness
3. 在严格 total-token accounting 下检验它是否改善 budgeted utility

这条线最危险、也最需要先被证伪的点是：

> `N` 是否真的更接近 necessity，而不是 continuator-relative local fragility 或 edit detectability。

---

## 1. 一句话 thesis

> 在可验证推理中，若经过 synthetic ground-truth 与跨 editor / continuator invariance audit 验证，**trajectory-conditional necessity** 比 outcome-only reward 或 observational step score 更可靠地监督 reasoning，从而提升 trace faithfulness，并在相同总推理预算下改善 accuracy-token frontier。

---

## 2. 核心问题

当前 reasoning post-training 的两个主流监督对象分别是：

- 最终结果是否正确
- 中间步骤看起来是否像好步骤

这两类对象都太粗：

- outcome-only 无法区分“真正决定成败的关键步骤”和“只是出现在成功轨迹里的 filler”
- observational step score 又容易把长度、模板、语气、解题套路气味误当作好步骤

CNT 的真正野心不是“再加一层 step reward”，而是重新定义：

> **在给定一条具体轨迹的条件下，到底什么样的局部步骤值得被奖励。**

本版刻意收窄：  
我们研究的不是“任务整体上哪个步骤最本质”，而是

> **在当前这条轨迹和当前这类 continuator 下，这个局部步骤对后续是否仍可解有多大边际贡献。**

这个对象更弱，但也更可识别、更可实验。

---

## 3. 研究边界

### 3.1 这条线不是什么

- 不是 verifier benchmark
- 不是 inference-time controller
- 不是通用 open-domain reasoning magic

### 3.2 这条线是什么

它是一条 reasoning supervision 主线，主要研究三件事：

1. `object identification`
   你定义的 step credit 到底是什么、能不能被稳定测到
2. `faithful training`
   这种 credit 能否训练出更 faithful 的 reasoning policy
3. `budgeted utility`
   在严格 total-token accounting 下，它是否真的提高 frontier

### 3.3 Claim boundary

本 proposal 只对 **verifiable, executable domains** 作强 claim，优先包括：

- math
- symbolic transformation
- graph / planning
- code 或 formal-lite 的一个第二域

对开放式、弱 verifier、长文自由推理任务，只做 failure boundary，不做强泛化承诺。

---

## 4. 关键定义

## 4.1 Trajectory-conditional object

给定：

- 问题 `x`
- 轨迹 `tau = (s_1, ..., s_T)`
- 冻结 continuator `pi_c`
- 结果 verifier `V`

我们研究的是：

> 在编辑某个局部步骤后，用 `pi_c` 续写、再由 `V` 判是否 solved，这个 solved probability 的变化。

因此，`necessity` 不是 task-global 真值，而是：

- trajectory-conditional
- continuator-dependent
- verifier-dependent

这不是缺点，而是需要被诚实承认并显式验证的对象定义。

## 4.2 Success-conditioned necessity

记位置 `t` 之前的前缀为：

`p_t = (x, s_1, ..., s_t)`

对成功轨迹 `tau+`，定义：

`N_t = p_{pi_c,V}(solve | x, p_t) - E_{e in E_drop/swap}[p_{pi_c,V}(solve | x, tilde_p_{t,e})]`

含义：

- 在一条成功轨迹中，从位置 `t` 的原始前缀继续时的可解概率，与把该步局部删除/替换后的编辑前缀继续时的可解概率之差

这衡量的是 **success trace 中该步的边际必要性**。

## 4.3 Failure-conditioned harmfulness / repairability（可选）

对 near-miss 失败轨迹 `tau-`，定义：

`H_t = E_{e in E_repair}[p_{pi_c,V}(solve | x, tilde_p_{t,e})] - p_{pi_c,V}(solve | x, p_t^-)`

含义：

- 在一条失败轨迹中，如果对该步做最小修复，未来可解概率能提高多少

注意：`H_t` 不是“负的 necessity”，它是另一个对象。  
它更接近 recoverable vs irrecoverable state 的区分，而不应与 `N_t` 直接混成同一语义。

本版不把 `H_t` 作为主文成立的前提；只有当 near-miss 定义、repair 质量与统计稳定性都足够扎实时，`H_t` 才进入主结果。

## 4.4 Stability / confidence

定义：

`S_t = exp(-Var_{e in E_editor, pi_c in C}[hat N_t^(e,pi_c)] / sigma^2)`

或在 failure trace 上对应地定义 `hat H_t` 的稳定性。

`S_t` 的角色只有两个：

- 过滤高噪声样本
- 给 pair weight / sample weight

它**不是 value 本身**，因此本版不再使用 `c_t = u_t * (n_t + lambda_h h_t)` 这种混合标量。

## 4.5 Recoverable vs irrecoverable

这来自原 proposal 中最值得保留、也最容易被误用的部分。

本版明确把 recoverability 只绑定在 failure trace 上：

- 高 `H_t`：当前失败更可能是局部可修复的
- 低 `H_t`：更接近 irrecoverable state

这为 compute 解释提供支撑，但不反过来定义 `N_t`。

---

## 5. CounterTrace v2：主数据协议

### 5.1 两层 benchmark

#### Layer 1: Synthetic ground-truth benchmark

必须先做：

- graph planning / symbolic algebra DAG
- 已知最小充分步骤集、minimal cut，或等价的程序化 indispensability 定义
- 显式加入 decoy / filler / redundant-path 结构，使 observational score 更容易被误导
- 可程序化编辑

作用：

- 验证 `N_t` 是否真的比 PRM / entropy / future-success score 更接近 ground-truth importance
- 回答“你测到的到底是不是必要性”
- 专门测试 `N_t` 能否避开 filler / style / redundancy 诱导

这一步必须在 **detectability-controlled** 设定下报告。  
如果控制 edit detectability 后，`N_t` 仍不能稳定优于 matched PRM / future-success，那么主对象定义必须降级。

#### Layer 2: CounterTrace-mini / full

再做真实目标域：

- math 为主
- code 或 formal-lite 作为第二域

### 5.2 编辑协议

主文编辑只保留三类：

- `Drop`
- `Swap`
- `Paraphrase`

failure-side 可选编辑：

- `Repair`

但本版做两个关键收紧：

1. **每种编辑都要求 naturalness audit**
2. **至少使用多个 editor family**

### 5.3 Candidate step selection

每条轨迹不再“全步骤开挖”，而是按以下分层采样：

- position
- length
- entropy
- verifier margin / difficulty

每条轨迹选 `4–6` 个步骤，控制成本并减少高噪声尾部步骤。

### 5.4 Naturalness / artifact audit

对每个编辑 family，必须做：

1. shallow classifier
2. length-only classifier
3. 多 editor 家族一致性
4. 小规模人类 spot-check
5. `corr(N, detectability)` 检查

如果 edit type 很容易被浅层特征识别，则该 family 不能进入主训练。

---

## 6. 方法：N+S Mainline, H as Optional Analysis

## 6.1 Stage A：对象估计

1. 用冻结 `pi_ref` 生成成功轨迹 `tau+`
2. 对选中步骤构造 `Drop / Swap / Paraphrase` edits
3. 用 train continuator 与 held-out continuator 分别从前缀 `p_t` / `tilde_p_{t,e}` 续写 `K` 次
4. 用 verifier `V` 估计 solve probability
5. 计算 `N_t`, `S_t`
6. 只有在 failure-side pilot 足够稳定时，才额外估计 `H_t`
7. 低 `S_t` 或自然性差样本直接丢弃

这一步主文得到的是 `N + S`，而不是一个混合 credit。

## 6.2 Stage B：within-prefix matched training

训练样本只在同一前缀下配对，避免把题目难度、风格、长度差异混进目标。

构造两类主文 pairs：

1. `necessity pair`
   - `(original step s_t, edited step s'_t)`
   - 若 `N_t` 高，则要求模型显式偏好原始必要步骤而不是破坏该步骤后的版本

2. `paraphrase consistency pair`
   - 对语义保持的 paraphrase，要求偏好差异接近 0
   - 用于证明模型不是在学 surface form preference

failure-side pair 只在 `H_t` 站稳后作为附加分析加入。

训练损失：

- `L_sft`
- `L_pref^N(original > edited)`
- `L_equiv^para`

总损失：

`L = L_sft + lambda_N * L_pref^N + lambda_inv * L_equiv^para`

其中样本权重：

`w_t = clip(N_t * S_t, 0, 1)`

### 6.3 为什么不用单一 scalar credit

本版明确反对把 `N/H/S` 压扁成一个 `c_t`，原因有三：

1. `N` 定义在 success trace，`H` 定义在 failure trace，语义不同
2. `S` 是跨 editor / continuator 的不变性与置信度，不是 value
3. 混成一个标量会使 object identification 与 training target 一起变脏

### 6.4 Critic 的角色

另训一个 critic：

`q_phi(prefix, step) -> (N, H, S)`

但 critic 只用于：

- 分析
- 可选预算控制实验

critic 不进入主训练主张，不作为主线上必须成功的模块。

### 6.5 RL refinement 的位置

RL refinement 只保留为可选 Stage C：

- 若 offline CNT 已站住，再用轻量 RL 做 bonus
- 若 RL 伤害 CTF 或 frontier，则不进入主文

---

## 7. 主 baselines

最强 baseline 必须包括：

1. outcome-only RLVR / 2-GRPO / GRPO + length penalty
2. matched-data observational PRM
3. CRM / OAR / PURE-style outcome-linked dense credit baseline
4. self-consistency / verifier rerank / GenRM-style rerank（严格 total-token 匹配）

这四类 baseline 分别对应最常见的反驳：

- 也许最终奖励就够
- 也许普通 dense reward 就够
- 也许 outcome-linked dense credit 已经覆盖了你
- 也许 inference-time rerank 更划算

---

## 8. 核心指标

### 8.1 Object-level metrics

- synthetic necessity recovery
- cross-editor stability
- held-out continuator stability
- top-k necessity overlap
- deletion-paraphrase asymmetry gap
- equal-label-budget recovery gap

### 8.2 Faithfulness metrics

- `CTF`
- `MSTL`
- top-k deletion loss
- paraphrase loss

其中主文建议显式定义：

- `CTF@k`
  - 删除模型认为最关键的 top-`k` 步骤后，verified solve rate 的下降
  - 并与 random / PRM-high / entropy-high deletion 做对照
- `MSTL`
  - 在保持 verified solve 不变的前提下，可保留的最小充分轨迹长度
  - 用贪心删除 low-necessity steps 近似估计

并同时报告以下 anti-gaming 对照：

- random deletion loss
- PRM-high deletion loss
- entropy-high deletion loss

否则更短、更脆的 trace 也可能伪装成“更 faithful”。

### 8.3 Utility metrics

- verified accuracy
- pass@1
- verbosity exploitation rate
- recoverable vs irrecoverable AUC
- accuracy vs total tokens frontier

### 8.4 Compute accounting

所有 compute result 必须统计：

- sampled continuations
- 被丢弃分支
- verifier / rerank token
- repair token
- continuation token

同时明确：

- 主结果中的 label estimation 与 rollout 不得依赖更强 API continuator
- API 最多用于 paraphrase 候选、额外 audit、red-team 或附加分析
- 主表必须能用本地 continuator family 重现

否则 compute claim 无效。

---

## 9. Minimum Viable Experiments

1. `Synthetic ground-truth necessity recovery`
   证明 `N_t` 不是换名的 entropy / PRM / future-success score。

2. `Edit detectability audit`
   检查 shallow/length detectability，以及 `N_t` 与 detectability 的相关性。

3. `Cross-editor invariance`
   比较不同 editor family 下 top-k necessity overlap 与排名稳定性。

4. `Held-out continuator stability`
   检验对象不是某个 `pi_c` 的局部脆弱性。

5. `Math main result`
   对比 CNT(N+S)、observational PRM、2-GRPO-lite、GenRM/self-consistency。

6. `Matched-data control`
   证明 gains 来自 necessity，而不是多了 dense labels。

7. `Equal-label-budget control`
   在相同 prefix 数、相同 pair 数、相同 continuation 预算下比较 CNT 与 matched baselines。

8. `Deletion–paraphrase asymmetry`
   验证删高 `N_t` 步骤更伤、paraphrase 更稳。

9. `Verbosity stress`
   验证模型是否更抗 filler / 空洞长推理。

10. `Compute frontier`
   在 equal total tokens 下看 frontier 是否外移。

11. `Recoverable vs irrecoverable`
   看 `H_t` 是否真能区分可修复失败状态。

12. `Cross-domain`
   至少做一个 code 或 formal-lite 第二域。

13. `Failure boundary`
   报告开放式 / 弱 verifier / 高冗余任务上的预期失败。

---

## 10. 预期贡献

如果成功，这条线最有价值的贡献不是“更复杂的 post-training recipe”，而是：

1. **新对象**
   `trajectory-conditional solvability credit`

2. **对象拆分**
   主文中的 `N + S` 与可选的 `H` 不再混同

3. **新 benchmark**
   synthetic truth + decoy/filler-aware CounterTrace 双层协议

4. **新评测语言**
   faithfulness + total-token frontier

5. **方法贡献**
   一个 object-first 的 offline training scheme，先验证对象，再把对象转成实际性能

---

## 11. 风险与 Plan B / C

### 风险 1：synthetic 上都识别不出 necessity

若 CNT 在 synthetic truth 上打不过 matched PRM / entropy，则对象本身站不住。

Plan B：

- 改 synthetic tasks
- 收缩到 success-conditioned `N_t`
- 暂时移除 `H_t`

### 风险 2：跨 editor / continuator 不稳定

若 ranking 对 editor/continuator 很敏感，则说明测到的是 model-relative fragility。

Plan B：

- 只保留稳定 edit families
- 把对象更诚实地命名为 local solvability credit

### 风险 2.5：teacher scale 偷渡

若主要正结果只有依赖更强 API continuator 才成立，则 object claim 会被削弱。

Plan B：

- 主表全部改为本地 continuator family
- API 只保留给 audit / red-team / paraphrase 候选

### 风险 3：CTF 涨但 accuracy 不涨

说明 object 有，但转不成 training utility。

Plan B：

- 把论文重心转向 faithful supervision + benchmark
- accuracy 只作支持性结果

### 风险 3.5：CTF / MSTL 被 metric gaming

如果 random deletion 也同样很伤，或模型明显变得更短但更脆：

Plan B：

- 加强 paraphrase consistency 与 random-deletion control
- 降低对 frontier 的主张强度
- 把重点收回 object validity 与 faithful supervision

### 风险 4：compute frontier 不动

说明模型只是更 faithful，没有更高预算效率。

Plan B：

- 删掉强 compute claim
- 保留 frontier 图作为 supporting evidence

### 风险 5：`H_t` 噪声太大

这是最现实的风险。

Plan B：

- 主文只保留 `N_t + S_t`
- `H_t` 降为分析对象，不进训练主线

---

## 12. 六周执行计划

### Week 1

- 搭建 synthetic ground-truth benchmark
- 实现 edit / continue / verify pipeline
- 明确 CTF / MSTL 与 deletion-paraphrase asymmetry 计算
- 加入 decoy / filler / redundancy synthetic suite

Go / No-Go：

- synthetic necessity recovery 必须明显优于 PRM / entropy
- `N_t` 与 detectability 不能高度正相关

### Week 2

- 做 CounterTrace-mini(math)
- 做 cross-editor 自然性与稳定性审计
- 做 held-out continuator 稳定性审计
- 跑 3B / 小 7B pilot

Go / No-Go：

- top-k deletion 效果显著 > random / PRM
- paraphrase effect 小

### Week 3

- 7B math 主训练：CNT(N+S) vs observational PRM vs 2-GRPO-lite
- 做 equal-label-budget 对照

Go / No-Go：

- CNT 至少在 CTF 或 compute-normalized acc 上赢主要 baseline

### Week 4

- 系统 ablations：
  - N/S 与可选 H 拆分
  - length matching
  - same vs external continuator
  - rollout K sweep

Go / No-Go：

- 优势在 held-out editor + 长度匹配下仍保留

### Week 5

- 做 equal-token frontier
- 做 equal-token rerank baseline
- 做 recoverable vs irrecoverable（仅当 H pilot 站得住）
- 做一个第二域

Go / No-Go：

- 至少一个预算点明显优势
- 第二域非负

### Week 6

- 只在前面信号强时做轻量 RL refinement
- 补失败边界和统计显著性
- 锁论文叙事：object + benchmark + offline training
- 明确报告 detectability-controlled synthetic 结果与 random-deletion controls

---

## 13. Proposal Summary

这条主线的核心不是提出另一种更复杂的 step reward，而是定义并验证一种可被识别、可被审计、可被训练利用的 **trajectory-conditional necessity object**。如果 synthetic truth、held-out editor/continuator、deletion-paraphrase asymmetry 和 total-token frontier 四条证据链同时成立，那么 CNT 就不只是一个训练技巧，而会成为 reasoning supervision 中一个更清晰、可操作的研究对象。
