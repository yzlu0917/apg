# Progress

## Current Goal

把 strong-judge boundary search 收窄到真正的 hard core，并明确哪些 clarify 子族值得继续。

## Milestones

- `DONE` 读取 `AGENTS.md`、`README.md`、`proposal.md`
- `DONE` 冻结 phase 0 的 claim hierarchy、fallback framing、gate 体系
- `DONE` 建立最小项目骨架：`docs/`、`configs/`、`data/`、`artifacts/`、`history/`
- `DONE` 启动 `Object gate v0`：冻结 scope、judge variants、最小 acceptance rule
- `DONE` 落地 `object-dev-v0` manifest 模板与 family construction note
- `DONE` 将数据策略冻结为 model-driven construction + model-driven review + verifier guardrail
- `DONE` 跑通首轮模型驱动生成链路，产出首批 `object_dev_v0` 候选
- `DONE` 补 reviewer 一致性审计脚本，发现 4B/8B reviewer 都存在结构化字段矛盾
- `DONE` 接入 API reviewer，并在 1-seed 对照上得到更稳定的 family 审查结果
- `DONE` 用 API reviewer 跑完首轮 code slice，对 family cleanliness 有了跨域初判
- `DONE` 新增 verifier 脚本并完成现有 API-reviewed 样本的 correctness 对齐检查
- `DONE` 基于 verifier-backed stop-loss，将 `reasoning_fluff` 从 bootstrap 主线转为 deferred family
- `DONE` 建立 active object slice，并跑通第一批本地 judge sanity eval
- `DONE` 扩展 active slice 到 7 条 verifier-clean 样本，并算出 first-pass family-wise miss / COC
- `DONE` 扩展 active slice 到 12 条 verifier-clean 样本，并形成正式 Object gate memo
- `DONE` 完成第一轮 order-swap audit，确认当前 Audit gate 明确未过
- `DONE` 补 order-balanced metrics，并确认 unbalanced prompt-gap 会被明显压缩
- `DONE` 完成 `style_flip` length audit，确认 `4B` 更像 shorter-answer bias 而不是 longer-answer bias
- `DONE` 实现 `style_flip controlled_v1` 并完成一轮 pilot；长度差下降，但 pass rate 仍偏低
- `DONE` 扩 `math` seed 到 `7` 条，并新增 `2` 条 verifier-clean 的 `substance_flip` math pairs
- `DONE` 试跑 `style_flip controlled_v2`；长度差继续下降，但 reviewer `0/7` 全拒
- `DONE` 找到 `style_flip controlled_v2.1`；math 上恢复到 `2/7` reviewer pass，且 kept pairs 对 `4B base` 是 tie-stable
- `DONE` 验证 `style_flip controlled_v2.1` 不能原样迁到 code；当前 code 侧主要退化成注释差异 recipe
- `DONE` 找到 code-specific `style_flip controlled_code_v1`；reviewer+verifier 保留 `4/5`，但 balanced pair-strict 仍只有 `0.5`
- `DONE` 将 code-side `style_flip` 收紧到 `controlled_code_v1_1`；保留 `2/5`，但在 kept subset 上 `4B base/critic` 都达到 balanced pair-strict `1.0`
- `DONE` 验证旧 seed 池剩余任务对 `substance_flip` 的净增长几乎为零；旧池基本耗尽
- `DONE` 补充 `4` 条新 seeds 和 verifier 支持；新 seed 刷新后新增 `3` 条 verifier-clean `substance_flip`
- `DONE` 将 clean merged slice 升到 `v2`：`8 substance + 4 style`
- `DONE` 诊断出 stubborn `substance_flip`` 的主 failure mode：wrong answer 只改最后输出 token
- `DONE` 新增 `substance_flip_targeted_v1`，并用 `Qwen3-8B` 修复 `math_003/007/009`
- `DONE` 将 clean merged slice 升到 `v3`；`4B base pair-strict=0.833`，`4B critic pair-strict=0.917`
- `DONE` 补齐 `clean_merged_slice_v3` 的 `0.6B` matched panel；两条 `0.6B` 仍为 balanced `pair-strict=0.0`
- `DONE` 验证 `substance_flip_targeted_v1` 在 fresh seeds 上也能稳定增长；新增 `3` 条 verifier-clean substance rows
- `DONE` 将 clean merged slice 升到 `v4`；`4B base pair-strict=0.867`，`4B critic=0.933`
- `DONE` 在第二批 fresh compact seeds 上再次验证 `substance_flip_targeted_v1`；复现 `3/4` reviewer+verifier 净增长
- `DONE` 将 clean merged slice 升到 `v5`；`4B base pair-strict=0.833`，`4B critic=0.944`
- `DONE` 将 future eval 协议冻结为 order-balanced paired protocol
- `DONE` 将 `style_flip` 主线冻结为 `math controlled_v2.1 + code controlled_code_v1_1` 的 audited 子集，暂不再开大规模 style sweep
- `DONE` 收紧 `controlled_code_v1` 里 loop-vs-comprehension 这类高波动 pair
- `DONE` 用 `controlled_code_v1_1` 并入下一轮 merged slice
- `DONE` 诊断 `clean_merged_slice_v2` 中仍不稳定的 `substance_flip` math items
- `DONE` 决定并完成在 `clean_merged_slice_v3` 上补跑 `0.6B`，形成完全 matched cross-cap panel
- `DONE` 在 `clean_merged_slice_v5` 上补跑 matched `0.6B`，形成新的 fully matched cross-cap panel
- `DONE` 整理 `v2/v3/v4/v5` 的 paper-facing comparison table
- `DONE` 用 `v5` 更新 object-gate memo，并将其定位为 current best fully matched slice
- `DONE` 给 `eval_judges.py` 补 API backend，并在 `clean_merged_slice_v5` 上完成单模型 API `critic` probe
- `DONE` 定义 strong-judge frontier boundary search protocol，并新增 `frontier_boundary_probe_v0`
- `DONE` 在 `frontier_boundary_probe_v0` 上跑完第一轮 API `critic` probe
- `DONE` 为 `clarify_required` 写 family note，并跑完更系统的 `frontier_boundary_probe_v1_clarify`
- `DONE` 收紧 `clarify_required` gold rule，并完成 `frontier_boundary_probe_v2_clarify`
- `DONE` 完成 `frontier_boundary_probe_v3_clarify_core`，并把 hard core 进一步定位到 `source_unit_missing / date_convention_missing`
- `DONE` 完成 `frontier_boundary_probe_v4_clarify_hardcore`，并确认 `source_unit_missing + date_convention_missing` 是当前 best frontier-hard slice
- `DONE` 完成 `v5 default-convention` 与 `v6 date-only`，并将对象收窄为 `default-convention boundary`
- `DONE` 完成 `v7 source-unit-only` fresh replication，并写出 `default-convention boundary` object memo
- `DONE` 完成 `v8 compact-date` fresh replication，并更新 short paper wording
- `TODO` 开始主文级 object wording 与表格整合，不再优先扩新 family

## Latest Updates

### 2026-03-31

- 将本目录正式收束为独立项目，而不是仅保留一份 proposal。
- 明确 headline 先放在 object claim，method / deployment 暂时降为 conditional claim。
- 明确 fallback paper framing，避免主方法失败时无收束出口。
- 定义 Object / Audit / Conversion / Scale 四个 gate 以及默认 go/no-go 阈值。
- 建立 phase 0 文档入口与结果账本入口。
- 建立 `object-dev-v0` manifest 模板与 `F1/F2/F3` family construction note。
- 根据用户反馈，将数据生产策略收束为模型优先，而不是规则优先。
- 用 `Qwen3-4B` 在两个 math seed 上跑通了 generator/reviewer 链路，并记录了首轮 family failure mode。
- 用 `Qwen3-8B` 做 reviewer 对照后确认：当前主要瓶颈是 reviewer protocol stability，而不只是 reviewer 强度。
- 接入 API reviewer 后，`substance_flip/style_flip` 能稳定通过，`reasoning_fluff` 脏样本会被拦下。
- 在 code slice 上，`style_flip` 仍最稳定；`reasoning_fluff` 继续失败，说明当前 object 还不在这个 family 上。
- verifier 对齐后确认：当前 clean object family 是 `style_flip`，可用 family 是 `substance_flip`，`reasoning_fluff` 应暂时摘除。
- 第一批 judge sanity eval 已跑通，当前差异主要集中在 `style_flip`：`Qwen3-4B base=4/5`，`Qwen3-4B critic=3/5`，`Qwen3-0.6B` 两个版本均为 `2/5`。
- active slice 扩充后，first-pass COC 结果为：`0.6B base=0.5`、`0.6B critic=0.5`、`4B base=0.9`、`4B critic=0.8`；当前 worst-family 全是 `style_flip`。
- active slice 进一步扩到 `12` 后，Object gate 进入 `GO but narrow` 状态：方向成立，但还没到强 headline。
- order-swap audit 表明：`0.6B` 基本是 A-position bias，`4B` 也存在明显 tie instability，所以 Audit gate 还没过。
- order-balanced 读法表明：`4B` 的 object signal 仍然存在，但 `4B base > 4B critic` 的差距被明显压缩；当前更稳的是 capacity gap，不是 prompt gap。
- style-specific length audit 表明：当前 `style_flip` 剩余 artifact 更像 shorter-answer / briefness bias，而不是更长答案偏好。
- `style_flip controlled_v1` pilot 表明：生成侧控制能压低长度差，但 reviewer pass rate 只有 `4/9`；在保留下来的 4 条上，`4B base` tie-stability 有改善，`4B critic` 仍不稳。
- 新增 `math_005-007` 后，`substance_flip` 新 math pilot 有 `2/3` 条 reviewer+verifier 通过，当前 verifier-clean `substance_flip` 池已到 `5` 条，说明扩 seed 是有效主线。
- `style_flip controlled_v2` 在 math 上把平均 gap 从 `60.5` 压到 `34.7`，但 reviewer `0/7` 全拒，说明当前 recipe 过约束。
- `style_flip controlled_v2.1` 在 math 上恢复到 `2/7` reviewer pass；这两条 kept pairs 的平均 gap 只有 `5.5`，而且 `4B base` 在 swap-balanced 读法下是 `2/2` tie-stable。
- `style_flip controlled_v2.1` 迁到 code 后只保留 `1/5`，失败样本大多是“代码 + 注释”式弱对比，因此 code 需要单独 recipe。
- `style_flip controlled_code_v1` 在 code 上恢复到 `4/5` reviewer+verifier 通过；但 `4B base/critic` 的 balanced pair-strict 仍只有 `0.5`，说明 code 侧还没过审计，只是有了当前 best recipe。
- `style_flip controlled_code_v1_1` 进一步去掉了高波动的大结构改写 pair；虽然 reviewer+verifier 只保留 `2/5`，但这两条在 `4B base/critic` 上都是 swap-stable `tie`，所以当前 code 侧应区分“高产 recipe”与“干净子集 recipe”。
- 对旧 seed 池剩余 `7` 条任务重跑 `substance_flip` 后，reviewer 只放过 `1` 条且 verifier-clean 为 `0`，说明旧池基本耗尽，不能继续靠同一批 seeds 挤增长。
- 新增 `math_008/009`、`code_006/007` 后，`substance_flip` 立即恢复到 `3/4` reviewer+verifier 通过，说明当前更有效的主线是“补 compact objective seeds”，不是继续在旧 seeds 上重采样。
- `clean_merged_slice_v2` 已达到 `12` 条：`8 substance + 4 audited style`。balanced 结果是：`0.6B base/critic` 仍为 `pair-strict=0.0`；`4B base=0.583`，`4B critic=0.667`。当前 style 子集基本站住，主瓶颈转为若干 stubborn `substance_flip` items。
- 进一步诊断表明，stubborn `substance_flip` 的关键问题不是 family 脏，而是 wrong answer 只改最后数字，导致 swapped 时 `4B` 仍会锚定第一答案。
- 本地 `Qwen3-4B` 无法稳定服从 `substance_flip_targeted_v1` 的 math 约束，但 `Qwen3-8B` 可以；修复后的 `math_003/007/009` 都把错误推进到了中间步骤。
- 用这些 targeted repairs 替换后，`clean_merged_slice_v3` 在 `4B` 上显著提升：`base pair-strict 0.583 -> 0.833`，`critic 0.667 -> 0.917`。当前 best high-cap slice 已从 `v2` 升到 `v3`。
- 补齐 matched `0.6B` panel 后，`v3` 的 cross-cap 读法更干净了：两条 `0.6B` 仍都是 `pair-strict=0.0`，说明 `v3` 的提升不是 slice 普遍变简单，而是高容量 judge 真正从 targeted substance repair 中受益。
- 在 fresh seeds 上，`Qwen3-8B + substance_flip_targeted_v1` 又新增了 `3` 条 verifier-clean substance rows，说明这条线已经不只是“修旧 pair”，而是当前最可持续的增长主线。
- `clean_merged_slice_v4` 扩到 `15` 条后，`4B base` 仍有 `0.867` pair-strict，`4B critic` 到 `0.933`。因此 high-cap slice 的提升没有因为扩样本而塌回去。
- 第二批 fresh compact seeds 上，`Qwen3-8B + substance_flip_targeted_v1` 再次取得 `3/4` reviewer+verifier 净增长；失败项 `math_012` 仍然暴露的是旧 failure mode，即错误只落在最后 token。
- `clean_merged_slice_v5` 已扩到 `18` 条：`14 substance + 4 style`。在 balanced `4B` 读法下，`base pair-strict=0.833`、`critic=0.944`；其中 `critic` 在 `substance_flip` 上仍保持 `1.0`，说明 `targeted_v1` 的扩大没有冲垮高容量 signal。
- `clean_merged_slice_v5` 的 matched `0.6B` 也已经补齐：两条 `0.6B` 仍然都是 balanced `pair-strict=0.0`，而 `4B base=0.833`、`4B critic=0.944`。这说明 `v5` 没有变成 generic easy slice，`v3` 上看到的 capacity split 在更大样本上依然成立。
- 当前最诚实的状态是：`v5` 已经可以替代 `v3` 成为 current best fully matched audit-controlled slice；下一步重点应转入 `v2/v3/v4/v5` 的 paper-facing comparison table，而不是继续盲扩到 `v6`。
- `v2/v3/v4/v5` comparison table 已经整理完成，当前 headline 选择规则也明确了：优先 audited、优先 fully matched、优先保留 capacity split 的更大 slice。
- 基于这个规则，`v5` 现在正式取代 `v3` 作为 current best matched reference；`v3` 保留为 first-breakthrough supporting slice，`v4` 保留为 larger 4B-only intermediate slice。
- 在 `clean_merged_slice_v5` 上补的单模型 API `critic` probe 结果是 balanced `pair-strict=1.0`，`style_flip/substance_flip` 都是 `1.0`。这说明 API judge 没有把 object signal 打没，而是直接吃满了当前 slice。
- 因此当前最准确的说法是：这个 object 确实 model-sensitive，但方向是能力越强越稳；同时也意味着 `v5` 作为 object slice 很好，但对 frontier API judge 来说可能已经不够难，后续若做 stronger-model story 需要更难 final slice。
- 已正式把主线切到 strong-judge boundary search，协议见 `docs/frontier_boundary_search_2026-04-01.md`。
- 第一轮 API `critic` hard-family probe 不是空跑：balanced `pair-strict=0.667`，而 `clarify_required` family 为 `0.0`。这说明 strongest judge 的首个可复现边界更像“该不该先澄清”的 epistemic boundary，而不是简单 code correctness boundary。
- 当前最有前景的 frontier-hard family 是 `clarify_required`；`constraint_edge_case` 和 `omission_critical` 在首轮 probe 上更像 control family，而不是 frontier boundary。
- `clarify_required v1` 已经把这个信号坐实了：在 8 条更系统的 probes 上，API `critic` 的 balanced `pair-strict` 只有 `0.25`。这说明 strongest judge 确实存在一个稳定边界：在欠定 prompt 下，它会过度奖励默认假设和直接作答。
- 当前最准确的 failure description 不是“不会 reasoning”，而是 **default-answer bias under underspecification**。这比“clarify before reasoning”更适合写进后续文档和论文表述。
- `clarify_required v2` 说明这不是一个松散的大类，而是一个可继续收窄的 frontier family：在更严格规则下，API `critic` 仍有 balanced `pair-strict=0.5`，但真正硬的部分主要集中在 `reference_frame_missing` 和 `convention_missing`，`sample_space_missing` 已经接近 control subtype。
- `clarify_required v3 core-only` 进一步表明：hard boundary 不是所有 clarify 子族共享的。当前 strongest API judge 真正稳定卡住的是 `source_unit_missing`，其次是 `date_convention_missing`；`timezone_reference_missing / measurement_convention_missing / clock_convention_missing` 在这一轮已更像 control。
- `clarify_required v4 hardcore-only` 则把 strongest boundary 压得更实了：balanced `pair-strict` 从 `0.6` 降到 `0.25`，而且 `source_unit_missing` 与 `date_convention_missing` 两个 hardest 子族在 paired 读法下同样都是 `0.25`。当前 best strong-judge slice 已经可以描述为 `clarify_required` 伞下的 default-convention boundary。
- `v5 default-convention` 用 fresh mixed prompts 复测后，strongest API `critic` 仍有 balanced `pair-strict=0.375`；其中 `source_unit_missing=0.0`，说明这条线最稳。
- `v6 date-only` 进一步澄清了日期约定子族不是消失了，而是 recipe 敏感：在 compact short-date ISO recipe 下，strongest API `critic` 的 balanced `pair-strict=0.0`。
- 因此当前最准确的工作对象已经不该再宽泛写成 `clarify_required`，而应写成更窄的 **default-convention boundary**，其 best current recipes 是 `source_unit_missing` 与 compact `date_convention_missing`。
- `v7 source-unit-only` fresh replication 进一步坐实：`source_unit_missing` 是当前最稳定的 hard subtype，balanced `pair-strict=0.25`，且 original / swapped 都只有 `1/4`，说明 strongest judge 会稳定默认 Celsius。
- 基于 `v4/v6/v7/v8`，当前最安全的主文对象表述已经可以写成：judge 会错误奖励依赖常见 source-unit 或 date-format 默认约定的直接答案。

## Blockers And Decisions

- 当前无关键阻塞。
- 默认不做大规模数据下载和 judge sweep，先做 `math + code + style_flip + substance_flip` 的最小 object slice。
- 默认先用本地小模型和 prompt variants 组成最小 judge pool，必要时再引入单一 API judge。
- 默认由 generator/reviewer models 生产和审查 family 样本，verifier 只做 correctness guardrail。

## Resume Point

下一启动点：

1. 将 `default-convention boundary` 的 paper-facing wording 和主文 object memo 继续压短，开始准备可直接进主文的版本。
2. 从 comparison table 抽出一版更接近论文主文的 object-gate 主表和 caption。
3. 把 `timezone_reference_missing / measurement_convention_missing / clock_convention_missing` 暂时保留为次级/对照子族，除非后续更窄样本重新把它们变硬。
4. 如需继续扩样，只优先补 compact `date_convention_missing` 的额外 fresh replications。
5. `style_flip` 主线继续保留 `math controlled_v2.1 + code controlled_code_v1_1` 的 audited 子集，不重新开大规模 style sweep。
