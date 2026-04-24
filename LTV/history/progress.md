# Progress

## 当前目标

将当前主线从实验推进切换到 **claim 收束与 proposal rewrite**：基于 round64 以前的全部结果，整理一版系统 synthesis，明确 object / boundary / system claim 以及当前不支持的更强主张。

## 里程碑

### DONE

- 读完 `AGENTS.md`、`README.md`、`proposal.md`
- 提炼 object / method / deployment claim hierarchy
- 写出 fallback paper framing
- 定义 `Object / Audit / Conversion / Scale` gate 与 go/no-go
- 确认本地 `infer` 环境和候选模型缓存可用
- 建立 `phase0_bootstrap.md`
- 建立 `history/results.md`
- 冻结 `Lean-mini-v0`、`CTS-mini-v0`、`feature-spec-v0`、`metric-spec-v0`
- 建立 `Lean-mini-v0` smoke slice 与 `CTS-mini-v0` seed pairs
- 跑通首条 boundary hidden-state extraction smoke run
- 将 `Lean-mini-v0` 扩到 first-pass 规模：`20` records / `34` steps
- 跑通 `text_only`、`post_state_only`、`transition_only` 三个最小 baseline
- 得到第一版 object signal：`transition_only` 明显优于其他两个最小对照
- 跑通 `CTS-mini-v0` first-pass paired evaluation
- 得到第一版 `IG / SS` 风向：`transition_only` 同时优于 `text_only` 与 `post_state_only`
- 建立 API 驱动的 CTS 扩展脚本与 provenance 流程
- 将 `CTS-mini-v0` 从 `4` 对扩到 `16` 对 panel，并重跑 paired evaluation
- 补齐 latent ablation：`pre_state_only`、`post_state_only`、`transition_only`、`concat_all`
- 做第二轮 API same-pair 扩展，并把 panel 扩到 `20` 对
- 重新跑 baseline v2 与 CTS panel v2
- 新增 `plausible_flip` prompt mode 并完成第三轮 API 扩量
- 构建 `28` 行的 CTS auto panel，并完成 noisy stress evaluation
- 清理 CTS provenance，生成 annotated curated/auto panel
- 为所有当前 CTS rows 补齐 same/flip family 标签
- 跑通 curated / auto panel 的 family-sliced audit
- 明确 `transition_only` 当前强 family 与弱 family 的边界
- 完成 round4 定向扩数，并把 weak-family auto panel 扩到 `36` rows
- 修复 API-derived `pair_id` 冲突，重建 round4 CTS 派生集
- 完成 round4 `novel_only` 与 updated auto panel 的 eval / family audit
- 完成 round5 Lean source 小扩展，并把 full panel 扩到 `42` rows
- 将 `wrong_composition` 的覆盖从 `3` 提到 `6`
- 完成 round5 composition `manual_only` 与 full panel 的 eval / family audit
- 完成 round6 manual stability check，并把 full panel 扩到 `50` rows
- 将 `wrong_composition` 的覆盖从 `6` 提到 `8`
- 将 `wrong_target_term` 的覆盖从 `4` 提到 `6`
- 完成 round6 `manual_only` 与 full panel 的 eval / family audit
- 完成 round7 hard same rewrite audit，并把 full panel 扩到 `58` rows
- 将 same-family 覆盖扩到：
  - `projection_style = 7`
  - `reflexivity_style = 7`
  - `other_same_rewrite = 6`
- 完成 round7 `manual_only` 与 full panel 的 eval / family audit
- 完成 round8 `reflexivity_style` dedicated control
- 将 `reflexivity_style` 拆成：
  - `reflexivity_pure_format`
  - `reflexivity_proof_keyword`
  - `reflexivity_target_term`
- 完成 round8 control 的 eval / subfamily audit
- 完成 round9 fixed-panel scoring audit
- 在固定 round8 control 上比较：
  - `linear_prob`
  - `linear_logit_z`
  - `mlp_prob`
  - `centroid_cosine`
- 完成 round10 broader-panel scoring audit
- 在 round7 full panel 上确认：
  - scorer 修复不是 fixed-panel 偶然
  - 但 `transition` 的修复并非独享，`post-state` 也一起改善

### DOING

- 收束 `round49–64` 的主线结论，形成可直接复用的 claim hierarchy / proposal rewrite 基础文档

### TODO

- 基于现有结果重写 proposal 主张：从“普适 latent progress verifier”改成“competence-scoped latent process supervision”
- 明确最终 claim hierarchy：
  - shared progress geometry in competence regime
  - local affordance geometry on hard states
  - competence / trust signal in `before hidden`
  - judge as canonical hard-domain signal
- 只有在出现真正新的对象假设时，才重开实验主线

### BLOCKED

- 当前无关键阻塞

## 最新进展

### 2026-03-31

- 将仓库重新定位为独立项目，而不是仅存 proposal 的工作目录
- 冻结 headline 只站在 object claim，method/deployment 改为 conditional claim
- 选定 `Lean-first object loop` 作为当前最小执行路线
- 把 fallback 明确为 `measurement + mechanism` 或 `Lean clean-room only`
- 验证了 `infer` 环境与本地模型缓存可用，当前不存在环境级阻塞
- 冻结了四个 v0 spec，并补了 smoke 数据与抽取脚本
- 用 `DeepSeek-Prover-V2-7B` 在 `11` 个 Lean steps 上成功抽取 `h^- / h^+ / Δh`
- 当前 artifact 已落在 `artifacts/object_gate_smoke/deepseek_prover_v2_7b/`
- 将 first-pass slice 扩到 `34` steps，并在 theorem-group CV 下得到首轮 baseline 对照
- 当前 first-pass 结果支持 `transition_only > post_state_only > text_only`
- 同时确认 earliest-fail 指标当前过于容易，暂不能作为 gate 证据
- 在 `CTS-mini-v0` 的 `2 same + 2 flip` 极小设置上，当前 first-pass 结果支持：
  - `transition_only` 低 `IG`
  - `transition_only` 高 `SS`
- 当前 paired result 仍只算 diagnostic，不算正式 gate 通过
- 使用 API 把 `CTS-mini-v0` 扩到 `16` 对 panel 后，结果变得更真实也更混杂
- 当前更合理的结论是：`transition_only` 仍是最平衡候选，但 panel 扩大后稳定性仍不够
- baseline v2 显示 `transition_only` 仍优于 `pre_state_only` 与 `concat_all`
- CTS v2 显示 `pre_state_only` 容易退化成“无响应”，`concat_all` 的漂亮 aggregate 需要谨慎解读
- 更大的 auto panel 结果没有推翻当前方向：`transition_only` 仍是最平衡候选
- 但 auto panel 也暴露出 provenance 早期不整齐的问题，需要清理后再进入更强审计
- provenance 清理和 family 标签已完成，当前更适合进入 family-sliced 审计
- family-sliced audit 已完成，当前更准确的结论是：`transition_only` 只在部分 family 上有清晰优势
- 最主要的薄弱点已经定位到 `wrong_theorem_reference` / `wrong_composition` / `wrong_target_term`
- 因此下一轮不该泛化 sweep，而该围绕这些薄弱 family 定向补数据
- round4 已经把 `wrong_theorem_reference` 和 `wrong_target_term` 的 family 读数拉到了更可解释的水平
- 当前剩下最清晰的未解 family 是 `wrong_composition`
- same-family 侧的 object evidence仍然不够干净，低 `IG` 常常被退化 invariance 吃掉
- round5 说明 `wrong_composition` 确实能被拉起一点，但还不够形成 clean win
- round5 同时暴露了 `wrong_target_term` 的 family-level 回摆，说明结论仍对 source mix 敏感
- round6 表明 flip-family 侧其实可以更强，`wrong_composition` 与 `wrong_target_term` 都被重新拉起来了
- 当前最大的瓶颈已经从“flip 不够强”转成“same-family invariance 太差”
- round7 进一步说明 same-family 问题不是简单的 coverage gap：
  - `projection_style` 明显改善了
  - `other_same_rewrite` 只部分改善
  - `reflexivity_style` 仍然是最硬的失败点
- 当前最合理的读法是：`transition_only` 仍是强 failure-sensitive 表示，但还不是稳定 semantic invariant
- round8 进一步确认 `reflexivity_style` 的失败不是 target-term 专属问题：
  - `pure_format` 也失败
  - `proof_keyword` 也失败
  - `target_term` 仍失败
- 因此，当前最合理的收束是：
  - 把 `reflexivity_style` 视为 hard negative / diagnosis branch
  - 把 headline object claim 收缩到已稳定 family，而不是继续同类 sweep
- round9 改写了上面这条结论的强度：
  - 在 fixed round8 control 上，`mlp_prob` 几乎把 `transition` 的 same-side 问题救回来了
  - 说明 round8 的强负结果高度依赖 scorer 选择
  - 当前更准确的读法是：`reflexivity_style` 不能再被简单判成表示层 hard negative
- round10 进一步说明：
  - 这个 scorer 效应在 broader panel 上仍成立
  - 但它不是 `transition` 独享的，`post-state` 也会一起被救回
  - 因此当前最核心的未决问题变成：在更合理 scorer 下，`transition` 还是否有独特对象优势
- round11 把这个问题推进到了主 Lean object gate：
  - `linear_prob` 读法下 `post-state > transition`
  - `mlp_prob` 读法下 `transition` 在 `AUROC / earliest_fail` 上重新占优
  - 但 `post-state` 仍在 `accuracy / brier` 上更强
  - `centroid_cosine` 不支持 `transition` 的独特优势
- 因此当前最准确的 object-level 状态是：
  - scorer 选择会直接改变 `post-state vs transition` 的主结论
  - 该比较仍是 scorer-conditional open question，而非已决胜负
- round12 又把这个问题推进到第二个 prover：
  - 在 Goedel 上，`linear_prob` 读法直接从 DeepSeek 的 `post > transition` 反转成 `transition > post`
  - `mlp_prob` 下仍然是 split reading：
    - `transition` 在 `AUROC / earliest_fail` 上更强
    - `post-state` 在 `accuracy / brier` 上更强
  - `centroid_cosine` 仍不支持 `transition` 的独特优势
- 因此当前最准确的 object-level 状态进一步变成：
  - `post-state vs transition` 不只是 scorer-conditional
  - 也是 model-conditional
  - “模型是否学到该 invariant” 已经成为活跃且被支持的解释分支
- round13 测了一个最小 conditional-transition 版本：
  - `conditional_transition = [h^- ; delta]`
  - 结果没有带来改善，反而通常弱于裸 `transition`
  - 也弱于最佳 `post-state` 读法
- 因此当前方法层的读法更新为：
  - “需要条件化” 仍然是活跃假设
  - 但最朴素的 raw concatenation 不是正确实现
  - 如果继续这条线，应转向更结构化的 conditional scorer，而不是继续堆 generic concat + MLP
- round14 又往前推了一步：
  - `interaction_transition = [delta ; h^- * delta]`
  - 这比 raw concat 明显更好
  - 但仍然没有超过裸 `transition`
- 因此当前方法层的状态是：
  - 条件化方向仍活跃
  - 但简单 feature engineering 已经接近边际收益区
  - 如果继续，应优先转向 bilinear / energy-style scorer，而不是继续加更多手工拼接特征
- round15 直接试了低秩 bilinear conditional scorer：
  - `conditional_bilinear_prob = linear(h) + linear(delta) + low_rank_bilinear(h, delta)`
  - 结果显著劣于 `transition_mlp_prob`
  - 也劣于 round14 的 interaction baseline
- 因此当前方法层的状态进一步收束为：
  - 在 single-point local-soundness 目标上继续调 conditional scorer，当前已经是低杠杆方向
  - 如果还要推进 conditional branch，下一步应直接转向 pairwise / contrastive objective
  - 当前这条 single-point conditional-scorer 支线可以视为阶段性收束
- round16 借了一个更像前人方法的 CLUE-style 几何 baseline：
  - `transition_clue_proto = normalized delta_h + per-class kmeans prototypes + nearest-prototype gap`
  - 结果优于 `transition_centroid_cosine`
  - 但仍明显弱于 `transition_mlp_prob`
- 因此当前方法层的状态进一步细化为：
  - 借前人 verifier 结构是有帮助的
  - 但最小 CLUE-style 移植版在 step-level Lean object gate 上还不是最优判别器
  - 如果继续借前人路线，下一步应转向 pairwise / contrastive objective，而不是继续发明单点 classifier 变体
- round17 正式切到了 pairwise objective：
  - `post_pairwise_margin`
  - `transition_pairwise_margin`

### 2026-04-08

- 旧 CTS 已经正式降级成辅助审计集，不再作为主数据来源
- 新主线已切成：
  - `before state`
  - API candidate generation
  - Lean legality filtering
  - human progress oracle
  - frozen-hidden separability audit
- round49 把 replayable harder-state 池扩到：
  - `15` states
  - `121` generated candidates
  - `100` replay-ok
- round50 从中补了一个 `6`-state 的 hard oracle slice，并把 panel 扩到：
  - `17` states
  - `104` annotated candidates
  - `162 ordered / 117 equivalent` pairs
- 在这个更大、更难的 panel 上，hidden separability 仍然明显成立：
  - DeepSeek:
    - gap `linear AUROC = 0.9301`
    - direction `linear AUROC = 0.9373`
  - Goedel:
    - gap `linear AUROC = 0.8754`
    - direction `linear AUROC = 0.9427`
- 当前最强结论已经不是“easy batch 上有信号”，而是：
  - pairwise progress-difference information
  - 在更大、更难的 human-oracle panel 上
  - 仍然 low-complexity readable，并跨模型成立
- round51 又把这个 object claim 往前推了一步：
  - second annotator 对 `17`-state panel 的 candidate-level agreement 达到 `91.35%`
  - 分歧只集中在 `9 / 104` 个 candidates 上，而且主要是 `weak_partial vs strong_partial` 边界
  - 最小 adjudication 后，consensus panel 上的 separability 仍然很强：
    - DeepSeek:
      - gap `linear AUROC = 0.9085`
      - direction `linear AUROC = 0.9490`
    - Goedel:
      - gap `linear AUROC = 0.8874`
      - direction `linear AUROC = 0.9148`
- 当前 object gate 已经不是单标注员 artifact，已经过了最小 second-annotator audit
- round52 正式进入 method 层：
  - 在 frozen `17`-state consensus panel 上训练了第一版 pairwise progress scorer
  - DeepSeek / Goedel 都出现了正结果
  - 当前最强 baseline 是 simple linear scorer，而不是 MLP
  - ordered pairs 基本已经能恢复，但 equivalent-pair calibration 仍偏弱
  - same: minimize score gap
  - flip: enforce margin
- 结果表明：
  - pairwise 训练会显著改变 same/flip tradeoff
  - `transition_pairwise_margin` 把 `IG` 压低了
  - 但 `SS` 明显塌掉
- 因此当前方法层的状态更新为：
  - objective mismatch 是真的
  - 但 scalar pairwise margin 仍然太 blunt
  - 如果继续 pairwise 方向，下一步应转向 embedding-style contrastive，而不是继续调同类 scalar margin loss
- round18 已把这条线推进到第一版 embedding-style contrastive：
  - 相比 round17，`transition` 的 `SS` 明显恢复
  - 同时 `IG` 仍保持在较低水平
  - 说明 pairwise 方向不是死路，round17 的主要问题确实部分来自 scalar-objective 过于粗糙
- 但 round18 仍没有形成 clean win：
  - `post_contrastive / transition_contrastive` 都没有超过 round10 最佳 single-point baseline 的 `SS`
  - 因此当前最准确的状态是：
    - contrastive 是 credible baseline
    - 但还不是新的最好方法
    - `transition` 也还没有在 contrastive 读法下恢复独特总体优势
- family-level 上，round18 的读法是：
  - `transition_contrastive` 在 `reflexivity_style / projection_style / constructor_notation` 上很稳
  - 但在 `other_same_rewrite / eliminator_style / theorem_application_style` 上没有 clean 优势
  - flip-family 侧则继续呈现 `post / transition` split reading
- 因此当前方法层的主线进一步更新为：
  - scalar pairwise margin 可视为 superseded
  - embedding-style contrastive 是当前 pairwise 主线
  - 若继续推进，应优先试：
    - asymmetric same/flip weighting
    - harder negatives
    - goal-conditioned contrastive scoring
- round19 已经把最直接的 asymmetric weighting 试掉了：
  - `flip_weight = 2`
  - `flip_weight = 4`
- 结果是一个 clean negative：
  - 两个版本都没有把 round18 的 `SS` 拉回来
  - `flip2` 只得到很小的 `IG` 改善，但 `SS` 更低
  - `flip4` 则进一步确认“单一全局 flip 倍率”不是正确修复方向
- family-level 读法也一致：
  - 没有出现新的 clean flip-family rescue
  - `transition` 仍主要保住 `wrong_composition`
  - `post` 仍在更多 flip-family 上更强
- 因此当前方法层的主线再次收束为：
  - weighted contrastive 可视为 negative branch
  - 如果继续 pairwise 主线，不该再做 global weight tuning
  - 下一步应优先转向：
    - harder negatives
    - goal-conditioned contrastive scoring
- round20 已经把 `harder negatives` 试出来了，而且这是 pairwise 主线里第一条真正的正向方法结果：
  - `hardneg_transition_contrastive` 同时改善了：
    - `IG: 0.0648 -> 0.0147`
    - `SS: 0.4199 -> 0.4829`
  - 说明 weak negative construction 确实是 round18 的真实瓶颈
- 更重要的是，round20 和 round19 形成了清晰对照：
  - global weight tuning 不行
  - hard negative construction 行得通
- family-level 读法也明显变好了：
  - `hardneg_transition_contrastive` 在 same-family 上几乎全面变干净
  - 但 flip-family 仍然是 `post / transition` split reading
- 因此当前方法层的主线进一步更新为：
  - round20 是当前最强的 pairwise / contrastive 结果
  - current bottleneck 已从“pairwise objective 是否有用”转成：
    - 能否通过更结构化的 conditioning 缩小 flip-family 分裂
  - 下一步应优先转向：
    - goal-conditioned contrastive scoring
    - 更有针对性的 flip-family hard negatives
- round21 已经把最小 goal conditioning 试出来了：
  - 用 theorem header 的 hidden-state 向量做 concat + interaction conditioning
  - 结果是：
    - `IG` 进一步降低
    - 但 `SS` 低于 round20
- 因此 round21 的读法不是“conditioning 无效”，而是：
  - minimal header-conditioning 更像 stabilizer
  - 它没有把 flip-family bottleneck 打开
- family-level 上，round21 的状态是：
  - same-family 更干净了
  - 但 flip-family 没有形成 round20 之上的 clean 改善
- 因此当前方法层的主线再次收束为：
  - round20 仍是当前最强结果
  - round21 可视为 conditioning diagnostic
  - 如果继续，不应继续做 generic conditioning sweep
  - 下一步更应该优先：
    - 更有针对性的 flip-family hard negatives
    - 或把 round20 recipe 先迁移到第二个 prover
- round22 已经把 round20 的 gain 拆成了机制差：
  - `transition` 的 hard-negative 增益主要来自 same-side cleanup
  - `post-state` 的 hard-negative 增益主要来自 broad flip amplification
  - 这说明 hard negatives 不是 generic boost，而是在改变两种表示的几何与 failure mode
- round22 也把当前主问题进一步收束成：
  - `wrong_composition` 为什么对 `transition` 仍然不稳定
  - 这种机制分裂是否会在第二个 prover 上复现
- 因此当前主线不应继续调全局权重或 generic conditioning，而应优先做：
  - family-targeted hard negatives
  - round20 机制的跨模型复查
- round23 已经把最小 `wrong_composition` family-targeted hard negatives 试掉了：
  - 对 `transition`：
    - `IG` 从 `0.0147` 回退到 `0.0537`
    - `SS` 只从 `0.4829` 到 `0.5018`
    - `wrong_composition` 本身没有净改善
  - 对 `post-state`：
    - `wrong_composition` 有轻微增益
    - 但 overall `SS` 低于 round20
- 因此 round23 是一个 clean negative mechanism result：
  - naive family-targeted weighting 不是 `wrong_composition` 的正确修复
  - 它对 `transition` 主要造成了 same-side geometry 破坏
- 当前主线进一步收束为：
  - 不应继续做 bucket-level family weighting
  - 如果继续机制线，应优先：
    - 拆 `wrong_composition` subfamily
    - 或先做 round20 的跨模型复查
- round24 已经把 round20 recipe 迁到第二个 prover：
  - `Goedel-Prover-V2-8B`
  - 在 near-protocol-matched (`epochs = 200`) 设置下：
    - `post = (IG 0.0474, SS 0.6311)`
    - `transition = (IG 0.0103, SS 0.6101)`
- 这轮最重要的结论是：
  - round20 的核心机制分裂不是纯 DeepSeek artifact
  - `transition` 仍然是更 invariant 的 same-side readout
  - 但 `wrong_composition` 仍不是 `transition` 的 clean win
- 因此当前主线再次收束为：
  - 当前最顽固未解问题已经稳定落在 `wrong_composition`
  - 而且这是跨模型保留下来的问题
  - 如果继续机制线，不应再做泛化 sweep，而应优先：
    - 拆 `wrong_composition` subfamily
    - 做 DeepSeek / Goedel 的 composition geometry 对照

## 待决策

- 暂无必须立即由用户拍板的方向性问题

## Resume Point

下一次启动时，直接进入：

1. 将 `concat(h^-, delta)` 固定为 negative baseline
2. 将 `concat(delta, h^- * delta)` 固定为 stronger-but-insufficient baseline
3. 将 `conditional_bilinear_prob` 固定为 negative baseline
4. 将 `transition_clue_proto` 固定为当前最强 geometry baseline
5. 将 round17 固定为第一版 pairwise baseline
6. 将 round18 固定为第一版 contrastive baseline
7. 将 round19 固定为 weighted-contrastive negative result
8. 下一步优先试：
   - 更有针对性的 flip-family hard negatives
9. 将 round20 固定为当前最强的 pairwise / contrastive 结果
10. 将 round21 固定为 goal-conditioning diagnostic
11. 下一步优先试：
   - 更有针对性的 flip-family hard negatives
   - 或将 round20 recipe 迁移到第二个 prover
12. 将 round22 固定为 mechanism audit，而不是新 recipe
13. 下一步优先做：
   - `wrong_composition` family-targeted hard negatives
   - round20 机制在第二个 prover 上的复现检查
14. 将 round23 固定为 `wrong_composition` targeted negative branch
15. 下一步优先做：
   - 拆 `wrong_composition` subfamily，而不是整体加权
   - 或把 round20 recipe 迁移到第二个 prover
16. 将 round24 固定为 cross-model mechanism replication
17. 下一步优先做：
   - `wrong_composition` subfamily 拆分
   - DeepSeek / Goedel composition geometry 对照
18. 并行保留 DeepSeek / Goedel 的 `mlp_prob` seed-stability 检查

- round25 已经把 `wrong_composition` 从粗 bucket 拆成了 3 个更细机制：
  - `application_argument_swap`
  - `transitivity_fabrication`
  - `transitivity_order_swap`
- 这轮最重要的结论是：
  - `wrong_composition` 不是单一失败模式
  - `transitivity_fabrication` 整体上并不坏，甚至常常是 transition-positive
  - `application_argument_swap` 里只有一部分是 persistent hard case
  - `transitivity_order_swap` 则是独立且明显更偏 post-state 的 slice
- 当前真正未解的 composition-specific 问题已经进一步收束到：
  - `cts_round5_flip_imp_trans_1`
  - `cts_flip_eq_comm_api_1`
  - `transitivity_order_swap` 这个 singleton slice
- 因此当前主线再次收束为：
  - 不应再把 `wrong_composition` 当成一个整体 family 去干预
  - 如果继续机制线，应优先做这几个 slice 的 geometry audit


- round26 已完成 `wrong_composition` unresolved slices 的 raw geometry audit：
  - `cts_round5_flip_eq_trans_1`
  - `cts_round5_flip_imp_trans_1`
  - `cts_flip_eq_comm_api_1`
- 这轮最重要的结论是：
  - `wrong_composition` 剩余问题不是一个机制
  - `transitivity_order_swap` 是最像真正 transition blind spot 的 slice
  - `cts_round5_flip_imp_trans_1` 是被 `lean_imp_trans_bad_comp:3` 强模板吸住的局部歧义
  - `cts_flip_eq_comm_api_1` 更像 scorer/model alignment split，不像 raw latent impossibility
- 因此当前主线再次收束为：
  - 不再做 `wrong_composition` 的 family-level intervention
  - 若继续机制线，优先三条更小支线：
    - `transitivity_order_swap` micro-panel
    - `lean_imp_trans_bad_comp` template-controlled audit
    - `eq_comm_api_1` scorer-alignment comparison


- round27 已完成 `application_argument_swap` 的 template-controlled audit
- 这轮最重要的结论是：
  - `lean_imp_trans_bad_comp` 不是整个 subfamily 的通用负模板锚点
  - 真正稳定被这个模板吸住的只有 `cts_round5_flip_imp_trans_1`
  - 其余三条 pair 已经由 theorem-local bad template 充分解释
- 因此当前主线再次收束为：
  - `application_argument_swap` 不再是优先未解 family
  - 若继续机制线，更值得做：
    - `lean_imp_trans_bad_comp` micro-panel
    - 或切回 `transitivity_order_swap` / `eq_comm_api_1`


- round28 已完成 `transitivity_order_swap` 的 controlled `eq_trans` micro-panel
- 这轮最重要的结论是：
  - `transitivity_order_swap` 不是模板层面的 intrinsic blind spot
  - 同一 frozen hard-negative recipe 在受控微面板上可把 order-swap flips 稳定拉开
  - 因此 round26 的 singleton 更像 broader panel context / neighborhood artifact
- 因此当前主线再次收束为：
  - 不把 `transitivity_order_swap` 冻结成 diagnosis branch
  - 若继续机制线，更值得做：
    - 对比 round26 singleton 与 round28 micro-panel 的 neighborhood 差异
    - 或切回 `eq_comm_api_1`


- round29 已完成 `eq_comm` micro-panel
- 这轮最重要的结论是：
  - `eq_comm_api_1` 不是 theorem-local 的稳定 model/scorer split
  - 在受控 `eq_comm` 微面板上，DeepSeek / Goedel 都能稳定分开 fabrication flips
  - 因此 round26 的 `eq_comm_api_1` 更像 broader panel / neighborhood artifact
- 因此当前主线再次收束为：
  - `wrong_composition` 的 residual template-level failures 进一步减少
  - 若继续机制线，更值得做：
    - 直接比较 round26 singleton 与 round28/29 micro-panels 的 neighborhood 差异
    - 或停止 local rescue，把这一支收束成 context-sensitive audit result


- round30 已完成 round26 singleton vs round28/29 micro-panel 的 neighborhood delta audit
- 这轮最重要的结论是：
  - 坏 singleton 和好 micro-panel 在 local geometry 上差异不大
  - 大差异主要来自 frozen scorer 在不同 panel context 下的 margin calibration
  - 因此这一支线最准确的收束是：context-sensitive audit result
- 因此当前主线再次收束为：
  - 可以停止继续做 local rescue
  - 若继续更有价值的工作，应转去：
    - 总结当前 branch 的 claim boundary
    - 或进入新的 gate / 新对象问题


- round31 已完成 neighborhood scorer branch
- 这轮最重要的结论是：
  - round30 暴露出的 context-sensitive calibration 问题，不能被简单 local-neighborhood scorer 直接修复
  - Euclidean RBF local density 在当前 frozen high-dimensional feature 上完全退化
  - cosine local margin 虽然不退化，但明显弱于 round18/20 的 contrastive / hard-negative 主线
- 因此当前主线再次收束为：
  - 不再继续扩 simple neighborhood scorer
  - 若继续找 genuinely new way，更值得做：
    - stronger calibration-aware contrastive objective
    - 或直接进入新的 gate / 新对象问题


- round32 已完成 calibration-aware hard-negative contrastive
- 这轮最重要的结论是：
  - 显式 score calibration 不是无效 add-on；它能把 `transition` 的 flip sensitivity 往前推
  - 但它没有 cleanly 超过 round20，而是引入了集中在 `other_same_rewrite` 的 same-side 成本
- 因此当前主线再次收束为：
  - round20 仍是默认 pairwise mainline
  - round32 作为 controlled tradeoff branch 保留
  - 若继续找新办法，更值得做：
    - targeted calibration that preserves same-side cleanliness
    - 或直接进入新的 gate / 新对象问题


- round33 已完成 general-method reframe
- 这轮最重要的结论是：
  - case rescue / scorer patching 已到边际收益很低的阶段
  - proposal 的真正 general 主线应恢复为 task-conditioned latent transition verifier
  - 新 mainline 正式冻结为 `Task-Conditioned Transition Energy Model (TC-TEM)`
- 因此当前主线再次收束为：
  - 停止继续扩旧 branch
  - 下一轮直接实现最小 TC-TEM
  - family audit 只保留为 diagnostics，不再做主线 story-saving



- round34 已完成最小 TC-TEM first pass
- 这轮最重要的结论是：
  - 新 general mainline 已经有可执行实例，不再只是 framing
  - `TC-TEM` 在 frozen round7 CTS panel 上给出实质信号：`IG = 0.0578`, `SS = 0.5108`
  - 但 first-pass 分数明显饱和，尚不足以替代 round20 作为默认主结果
- 因此当前主线再次收束为：
  - 保留 round20 作为旧 pairwise 分支的默认最好结果
  - 保留 round34 作为新的 general-method first executable branch
  - 若继续推进，应优先解决 TC-TEM 的 saturation / calibration，而不是回到旧 branch 做 case rescue


- round35 已完成 pairwise separability audit
- 这轮最重要的结论是：
  - 当前更窄的 object 问题得到了正向支持：frozen hidden state 里确实存在低复杂度可分的 progress-difference 信息
  - `post_linear_sep` 已达 `AUROC = 0.8964`, `accuracy = 0.8793`
  - `post_centroid_sep` 已达 `AUROC = 0.9226`
- 一个关键代数结果也已冻结：
  - 在固定 pre-state 的 pairwise 任务里，`Δh(source) - Δh(variant) = h^+_source - h^+_variant`
  - 因此 pairwise object 下 `post-state` 与 `transition` 差分会塌成同一个比较对象
- 因此当前主线再次收束为：
  - object gate 现在应优先围绕 pairwise separability 来写
  - 暂不继续扩大 big-judge recipe
  - 若继续，应研究更强的 progress 标签或更干净的 pairwise protocol，而不是回到旧 branch 做 scorer patching


- round36 已完成 Goedel cross-model pairwise separability audit
- 这轮最重要的结论是：
  - round35 的更窄 object claim 不是单模型现象，在第二个 prover 上也成立
  - `post_linear_sep` 在 Goedel 上更强：`AUROC = 0.9304`, `accuracy = 0.9310`
  - 因此 object gate 现在已有跨模型支持的正向证据
- 一个稳定结论继续成立：
  - 在固定 pre-state 的 pairwise 任务里，`Δh(source) - Δh(variant) = h^+_source - h^+_variant`
  - 所以当前 pairwise object 下，`post-state` 与 `transition` 差分不是两个独立对象
- 因此当前主线再次收束为：
  - 优先围绕 pairwise separability 写 object claim
  - 暂不回到 big-judge / old branch
  - 若继续，最值得做的是更强的 pairwise progress 标签或更严格的 final frozen panel


- round37 已完成 stronger pairwise progress label spec
- 这轮最重要的结论是：
  - 当前 round35/36 使用的 `same/flip` 只能算 proxy label，不能再被当成 final pairwise progress label
  - 新 schema 已冻结到 `configs/object_gate/pairwise_progress_label_v0.yaml`
  - 现有 round7 CTS panel 已通过 scaffold 对齐到新 schema，但 `58/58` 都还是 `proxy_only`
- 因此当前主线再次收束为：
  - object claim 继续以 round35/36 的 proxy-based pairwise separability 为准
  - 下一步必须先补 proof-state extraction / variant replay 字段
  - 在此之前不再把 stronger progress label 当作“已经有了”的东西


- round38 已完成 Lean replay environment hook
- 这轮最重要的结论是：
  - 当前仓库本身不是 Lean workspace，不应在 repo 内部伪造一个新的局部环境
  - 复用 `/root/mathlib4-4.15.0` 与其 `repl` 子项目是当前最干净的接入方式
  - 项目侧 wrapper 已经能稳定跑通一次最小 tactic-mode smoke
- 因此当前主线再次收束为：
  - 环境接入已不再是 blocker
  - 下一步应直接在这条 hook 上实现 project-owned replay / extraction smoke
  - stronger pairwise progress label 仍未可用，object claim 仍以 round35/36 的 proxy-based separability 为准


- round39 已完成 first replay / extraction smoke pass
- 这轮最重要的结论是：
  - 当前项目已经能从 repo 内部把最小 tactic replay 变成结构化 artifact
  - step-level `before_goals / after_goals / proofState` 链已经能被稳定记录
  - 因此 round37 里缺失的 proof-state extraction 不再是“完全没有入口”，而是已经有了最小 smoke 原型
- 因此当前主线再次收束为：
  - 下一个真正有价值的动作不是再做环境工作
  - 而是把这个 smoke 原型扩成第一个 variant replay / extraction pass
  - object claim 仍以 round35/36 的 proxy-based pairwise separability 为准，stronger labels 仍未生成


- round40 已完成 first CTS variant replay smoke
- 这轮最重要的结论是：
  - CTS 现在已经能被项目内脚本落成 Lean replay bucket，而不再只是文本级 pair 候选池
  - smoke 子集上，`8/8` rows 都能重建 shared pre-state，`8/8` source replay 成功，`6/8` variant replay 成功
  - 当前已明确出现一个独立的 hard-failure bucket：`variant_lean_error`
- 因此当前主线再次收束为：
  - 下一步可以停止纯 smoke，开始扩到更大的 replay slice
  - 合法性与 progress 现在可以正式分层：Lean 先分桶，judge 只看合法 pair
  - stronger progress labels 仍未生成，但第一批可 judge 的 replay-ok pair 已经有了


- round41 已完成 full CTS replay bucket
- 这轮最重要的结论是：
  - 当前 `58`-pair scaffold 已全部接通 shared pre-state replay
  - `source` 在 full slice 上 `58/58` replay 成功
  - `variant` 分成三个桶：
    - replay-ok：`32`
    - Lean hard error：`26`
    - 其中包含 `1` 条 wrapper-normalization holdout，而不是语义 invalidity
- 因此当前主线再次收束为：
  - Lean legality 分桶已经够稳定，可以作为下一步 judge 前置层
  - 下一步不应直接全量 judge，而应先做最小 tactic normalization
  - judge 入口应限定在 replayable pair 子集上


- round42 已完成 replay-data audit
- 这轮最重要的结论是：
  - 当前数据不只是“有 hard-invalid rows”，而是 `same/flip` proxy 与 Lean replay 语义已经发生错位
  - `28` 条 flip 里只有 `3` 条 replayable，而这 `3` 条在 Lean replay 下仍然能关掉 goal，因此不应继续当 clean flip 使用
  - 当前唯一 same-side replay error 是 wrapper normalization 问题，不是语义 invalidity
- 因此当前主线再次收束为：
  - 现在不能直接接 judge
  - 必须先做最小 tactic normalization + replay-aware relabel
  - judge 数据入口应改成 replay-clean pairs，而不是旧 CTS proxy split


- round43 已完成 state-first generation scaffold
- 这轮最重要的结论是：
  - 新主线已经从口头策略变成 repo-owned 数据入口
  - 第一版 `before-state` seed panel 已生成，共 `26` 个干净 states
  - 生成 prompt 和 schema 已冻结，human annotation 被明确保留为 progress oracle
  - 当前环境里没有现成 API key，因此这轮只搭 scaffold，不伪造 live generation
- 因此当前主线再次收束为：
  - 旧 CTS 主线降级为辅助审计集
  - 新主线改成：state-first generation -> Lean legality -> human oracle
  - 下一步一旦接上 API backend，就直接从这 `26` 个 states 开始生成候选 tactic


- round44 已完成 first state-first API generation batch
- 这轮最重要的结论是：
  - README 中记录的 API 路径是可用的
  - 新主线已经形成首个真实 batch，而不再只是 schema/prompt/scaffold
  - 在 `5` 个 states 上共生成 `40` 条候选，其中 `32` 条可通过 Lean replay
- 因此当前主线再次收束为：
  - 新主线已经变成：state-first generation -> Lean legality，并且已跑通第一批
  - 下一步不该再回旧 CTS，也不该继续纠缠文本 proxy
  - 下一步应在 replay-ok 候选上组织 human pairwise progress oracle


- round45 已完成 first human progress oracle batch
- 这轮最重要的结论是：
  - 新主线第一次拥有了真正的人工 progress oracle，而不再只有 API generation + Lean legality
  - 当前批次覆盖 `5` 个 `before states`、`32` 个 replay-ok 候选
  - tier 分布为：`17 solved / 10 strong_partial / 4 weak_partial / 1 neutral`
  - 当前 oracle 仍是 `manual_single_annotator_v0`，定位是 first annotation batch，不是最终标准
- 因此当前主线再次收束为：
  - 旧 CTS 继续留在辅助审计位
  - 新主线已变成：state-first generation -> Lean legality -> human progress oracle
  - 下一步不该扩新题或回大 judge，而应先由 tier 导出 state-local pairwise preferences
  - 然后直接在这批 human oracle 上做 first frozen-hidden separability audit


- round46 已完成 first frozen-hidden separability audit on the new human oracle batch
- 这轮最重要的结论是：
  - 新的 state-first human oracle 数据不是“只能人工看出差别”，而是低复杂度 hidden readout 也能分
  - 在 `5` 个 states 上导出的 `89` 个 gap pairs 与 `64` 个 direction examples 上，DeepSeek 和 Goedel 都给出稳定高于随机的 separability
  - object-level claim 因此进一步升级：新的 `Lean legality + human progress oracle` 主线也支持 hidden separability
- 因此当前主线再次收束为：
  - object gate 目前是正的，而且不再只依赖旧 CTS proxy
  - 下一步不该回大 judge，也不该继续修旧 CTS
  - 下一步应冻结一个 small final oracle panel，并补一层 medium-difficulty states
  - 然后在扩后的 final panel 上复跑同一 pairwise separability 协议


- round47 已完成 medium-difficulty state expansion
- 这轮最重要的结论是：
  - 新主线已经不再只依赖 easy/dev states
  - `6` 个 medium states 上共生成 `49` 条候选，其中 `35` 条 replay-ok
  - 这些 state 明显带来了更丰富的 partial-order 结构，而不是“几乎全 solved”
- 因此当前主线再次收束为：
  - medium slice 值得进入 human oracle，而不是停留在 legality replay
  - 下一步应把 dev + medium 合成更像 final 的 oracle panel
  - 然后继续用同一 frozen-hidden separability 协议复查 object claim


- round48 已完成 combined dev+medium oracle panel audit
- 这轮最重要的结论是：
  - 先前的正结果不是 easy batch artifact
  - 在 `11` 个 states、`93 ordered / 87 equivalent` 的更大 panel 上，DeepSeek 和 Goedel 仍都给出强 separability
  - object gate 现在已经不只“初步为正”，而是有了一个更像 final panel 的正结果
- 因此当前主线再次收束为：
  - object gate 当前是明确正的
  - 下一步不该回大 judge，也不该继续 repair old CTS
  - 下一步应把这 `11`-state panel 冻为 `small final oracle panel v1`
  - 然后再决定是否做第二标注员复核，或进入 method / conversion 阶段


- round53 已完成 harder-slice audit 与 before-hidden state-value audit
- 这轮最重要的结论是：
  - 在 `6`-state harder slice 上，candidate-level progress signal 仍然很强
  - 相比 full consensus panel，真正变弱的是 `ordered vs equivalent` gap 区分；`better vs worse` 排序没有塌
  - `before hidden` 本身也带 state-level hardness / value signal，但明显弱于 `after hidden` 上的 candidate progress signal
- 因此当前主线再次收束为：
  - object gate 不只是“存在 progress signal”，还出现了更清楚的机制分层
  - 当前更像：
    - `before hidden` = 弱 state value / hardness
    - `after hidden` = 强 candidate progress
  - 所以下一步若继续 method，最自然的是测试 `before-state value + after-state progress` 的双头 scorer


- round54 已完成 first Putnam harder-domain pilot
- 这轮最重要的结论是：
  - 真 harder formal source 已经接通，不再只是项目内 medium/hard slice
  - Putnam file-mode extraction 成功产出 `14` 个 harder seed states
  - tiny pilot 上 `24` 个候选里 `16` 个可 replay，说明 harder 管线可执行
  - 但更关键的是 hidden audit 出现新的分裂：
    - `ordered vs equivalent` gap signal 仍然存在
    - `better vs worse` direction signal 在 DeepSeek / Goedel 上都明显塌掉
- 因此当前主线再次收束为：
  - 之前的 “hard” 确实还不够硬
  - latent progress signal 的结论现在要改成 difficulty-dependent
  - 下一步不该直接做 recipe sweep，而应先扩一个更大的 Putnam hard oracle slice，确认 direction collapse 是小样本现象还是稳定边界


- round55 已完成 expanded Putnam hard oracle slice audit
- 这轮最重要的结论是：
  - round54 的 tiny Putnam pilot 确实过于乐观
  - 扩到 `7` 个 harder Putnam states、`27` 个 replay-ok candidates、`40 gap / 62 direction` examples 后，DeepSeek 和 Goedel 上的 frozen-hidden separability 都明显失稳
  - 不只是 fine direction 继续塌，连 coarse `ordered vs equivalent` gap 也开始接近反向
- 因此当前主线再次收束为：
  - object gate 在 easy-to-medium human-oracle panel 上仍为正
  - 但在 genuinely hard Putnam states 上，当前 frozen-hidden pairwise progress claim 不再成立
  - 当前最重要的不是继续 recipe sweep，而是承认 object claim 的 difficulty boundary 已经被逼出来
  - 下一步更值得做：
    - Putnam slice 的 second-annotator / disagreement audit，或
    - 同一 Putnam panel 上做 hidden scorer vs external LLM after-state judge 的 head-to-head


- round56 已完成 Putnam hard slice 上的 external-judge head-to-head
- 这轮最重要的结论是：
  - 在与 round55 完全相同的 Putnam panel 上，外部 pairwise after-state judge 仍然稳
  - gap AUROC = `0.7903`，direction AUROC = `0.9708`
  - 这与 frozen hidden 在同面板上的塌缩形成了清楚对照
- 因此当前主线再次收束为：
  - latent progress signal 的 object claim 不能再写成“普适可转移”
  - 更准确的是：它在模型能力范围内为正，在 genuinely hard Putnam states 上出现明显边界
  - 如果目标是 hardest states 上的最强监督信号，external after-state judge 当前明显更优
  - 如果目标是 internal latent reward，则下一步不该继续盲扫 recipe，而该决定：
    - 是否训练 latent scorer 去蒸馏 external judge，或
    - 是否明确把 latent claim 范围限定在 competence regime


- round57 已完成 `before hidden` trust audit 与 trust-gated hybrid
- 这轮最重要的结论是：
  - `before hidden` 里确实有 state-level trust / competence signal
  - 用 easy+medium consensus panel 与 Putnam hard slice 合起来做 state-level trust prediction，DeepSeek / Goedel 都能明显高于随机
  - 在 Putnam 上，trust-gated hybrid 明显优于 latent-only，但仍明显不如 judge-only
- 因此当前主线再次收束为：
  - latent failure on hard states 不是纯噪声，而是部分可预测的 competence-boundary phenomenon
  - `before hidden` 更像 boundary detector，而不是 hard-state ranking replacement
  - 现在最自然的下一步不再是继续做 latent recipe sweep，而是：
    - 用 external judge 蒸馏 hard-slice latent scorer，或
    - 把项目的主 claim 明确改写成 competence-regime-scoped latent supervision


- round58 已完成 Putnam hard slice 的 `within-state vs cross-state` locality audit
- 这轮最重要的结论是：
  - Putnam 上 latent 不是“完全没对象”
  - 在同一个 hard state 内，within-state ranking signal 依然很强
  - 真正塌掉的是跨 state 的共享几何 / transfer
- 因此当前主线再次收束为：
  - hard-domain 失败不该再被表述成“latent progress 不存在”
  - 更准确的是：在 hard states 上，latent object 变成了局部的、state-specific 的
  - 现在最有价值的问题不再是 recipe sweep，也不只是 routing，而是：
    - 什么结构决定了这种 local geometry
    - 为什么它不能跨 harder states 统一起来


- round59 已完成 Putnam hard slice 的 local-geometry 来源与 judge 对照机制分析
- 这轮最重要的结论是：
  - hard-state latent `better-minus-worse` 原型在每个 state 内都是真实存在的，但跨 state 几乎不对齐
  - DeepSeek / Goedel 的 prototype off-diagonal mean cosine 都接近 `0` 且出现明显负值，说明 harder-domain 问题不是“没对象”，而是“没有共享全局几何”
  - 外部 judge 则呈现出更稳定的跨-state 标度：其正确概率随 oracle tier gap 单调上升，更像 canonical progress scalar
  - 局部 latent 几何的来源不只是 tactic 表面家族；更关键的是候选是否围绕同一个 local proof bottleneck，形成 state-specific affordance axis
- 因此当前主线再次收束为：
  - easy/medium 与 hard Putnam 的差别，不是有无信号，而是 **global alignment vs local affordance**
  - latent 更像 state-local affordance geometry
  - judge 更像跨-state canonical geometry
  - 下一步若继续深挖，最值得的是：
    - 哪些具体 proof bottleneck 会诱发单一 affordance axis
    - 能否把 hard-state 的局部 latent 几何按 state type / bottleneck type 重新对齐


- round60 已完成 Putnam hard slice 的 goal-aligned feature 对照
- 这轮最重要的结论是：
  - 只要把 candidate feature 改成直接对 `before/after goals` 做 mean-pooled relational embedding，hard Putnam 上的 **coarse cross-state gap signal** 就能明显恢复
  - DeepSeek / Goedel 都从 `gap cross AUROC ≈ 0.34/0.37` 抬到 `≈ 0.64/0.65`
  - 但 `better vs worse` 的 **cross-state direction** 仍然不稳，最多只恢复到 `≈ 0.40-0.45`
- 因此当前主线再次收束为：
  - hard-domain 的 shared structure 并没有完全消失
  - proof-state-aligned feature 能恢复 **ordered vs equivalent** 这类粗粒度边界
  - 真正没有恢复的是 finer-grained canonical ranking direction
  - 当前最有价值的问题进一步变成：
    - 哪些 proof bottleneck / state types 共享 coarse progress boundary
    - 为什么这些 type 仍然不能共享更细的 ranking-level geometry


- round61 已完成 mixed-panel hybrid reranking conversion test
- 这轮最重要的结论是：
  - 当前发现已经不只是 object / mechanism insight，而是第一次转成了明确 utility
  - 在 `17` 个 easy/medium states + `7` 个 Putnam hard states 的 mixed panel 上，latent-only 已明显优于弱 baseline
  - judge-only 仍是最强信号
  - 但 round57 的 trust signal 与 latent reranker 组合后，hybrid 已经能吃到大部分 judge 增益
- 因此当前主线再次收束为：
  - latent 的正确系统角色不是 hard-domain 全局 judge
  - 更准确的是：
    - `after hidden` 负责便宜的 local reranking
    - `before hidden` 负责 trust / competence gating
    - external judge 负责 hard / untrusted 区域的 canonical scoring
  - 现在 round55–61 这条线已经形成了完整 gate progression：
    - object gate: easy/medium 为正
    - mechanism gate: hard Putnam 上 global geometry 塌为 local affordance
    - conversion gate: trust-gated hybrid 在 mixed panel 上取得 first positive result
  - 若继续推进，下一步不该再做 feature hunt，而应考虑：
    - 把这套 hybrid 结构放进更真实的 candidate reranking / search setting
    - 或正式收束成 proposal-level claim hierarchy


- round62 已完成更接近 search 的 budgeted `k-candidate` reranking 评测
- 这轮最重要的结论是：
  - round61 的 utility 结果不是 full-pool artifact
  - 但 round62 的 subset protocol 本身明显偏 easy：`k=6` 没有 Putnam，`k=4` 也几乎全被 easy subsets 主导
  - 因此它支持的是 mixed/easy-heavy regime 下的质量-成本 tradeoff，而不是 hard-domain budgeted success
  - hard-only sanity check 继续维持老边界：Putnam 上 latent-only 仍明显弱，judge/hybrid 才稳
- 因此当前主线再次收束为：
  - 这套结构的真正价值已经不是“latent 能不能替代 judge”
  - 而是：
    - `after hidden` 作为 cheap local reranker
    - `before hidden` 作为 judge budget controller / trust gate
    - external judge 作为 sparse fallback
  - 到 round62 为止，这条线已经过了：
    - object gate
    - mechanism gate
    - first conversion gate
    - first budgeted utility gate（但当前只对 mixed/easy-heavy regime 可信）
  - 若继续推进，下一步最自然的不是继续离线刷分，而是：
    - 做一个真正 hard-aware 的 budgeted protocol，而不是让 easy subsets 主导
    - 或放进更真实的 candidate search / beam / best-of-k loop
    - 或正式收束成 claim hierarchy / proposal rewrite


- round63 已完成 hard-aware / stratified budgeted reranking 修正评测
- 这轮最重要的结论是：
  - round62 的乐观读法已被修正：Putnam-only、state-balanced 指标下，latent-only 仍明显弱
  - hybrid 在 hard 上之所以稳，不是因为 latent 变强，而是因为 trust gate 基本把 Putnam 路由给了 judge
  - easy 上的 utility 故事仍成立：latent 很强，hybrid 用极少 judge 保住质量
- 因此当前主线再次收束为：
  - 这条线真正支持的系统结构是 **regime separation**
  - 不是：
    - latent 在 hard 上也能 budgeted rerank
  - 而是：
    - easy/medium: latent reranking + cheap trust gate
    - hard Putnam: judge fallback
  - 到 round63 为止，当前 picture 已经相当完整：
    - object gate: easy/medium 正
    - mechanism gate: hard 上 local geometry 仍在，global geometry 塌
    - conversion gate: mixed/easy-heavy regime 有 utility
    - hard-aware budgeted gate: hard 上 hybrid 的价值来自正确升级，不是 latent 变强
  - 若继续推进，下一步不该再做同类离线 slicing，而应二选一：
    - 放进真实 search / beam loop，看 trust 是否真的减少 judge 调用
    - 或正式收束成 claim hierarchy / proposal rewrite


- round64 已完成 Putnam hard states 的 bottleneck-conditioned geometry audit
- 这轮最重要的结论是：
  - 一个最小的 coarse bottleneck taxonomy 仍然不能恢复 hard-state shared latent geometry
  - same-type prototype alignment 没有系统性优于 global alignment；多数 type 平均甚至更差
  - judge 在这些 type 上仍比较稳，latent 则继续呈现强局部性
- 因此当前主线再次收束为：
  - hard 上 latent 的局部性比“proof bottleneck type”还更细
  - 当前最合理的对象读法不是：
    - type-conditioned shared geometry
  - 而是：
    - state-specific / micro-structure-specific affordance geometry
  - 到 round64 为止，hard-side mechanism picture 已经进一步闭合：
    - not global
    - not rescued by coarse type grouping
    - still local
  - 若继续推进，下一步已经不该再做更多同类离线 taxonomy slicing，而应二选一：
    - 收束成 claim hierarchy / proposal rewrite
    - 或只在真正新的对象层假设上重开主线


- 已新增一份系统总结文档：
  - [artifacts/object_gate_synthesis_v1.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_synthesis_v1.md)
- 这份 synthesis 将 round1–64 的主线收束为：
  - 为什么从 CTS/proxy 转到 `state-first -> Lean legality -> human oracle`
  - easy/medium 上 shared latent progress geometry 的正结果
  - Putnam hard 上 global geometry collapse + local affordance 保留
  - `before hidden` 的 trust / competence signal
  - judge 作为更 canonical 的 hard-domain progress scalar
- 因此当前最合理的项目状态是：
  - 实验主线已阶段性闭合
  - 后续优先做 claim formalization / proposal rewrite
  - 不再继续低边际的 feature / taxonomy / budget slicing
