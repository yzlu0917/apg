# ToolShift Insights

## Patterns

- `true deprecate` 类 near-orbit 不应被硬编码成单一 gold control。
  当 schema 明确表明旧工具不可再用、且无直接替代时，`abstain` 与 `ask_clarification` 都可能是可审计的 admissible canonical action。seed suite 若强行只收 `abstain`，会把合法控制策略错判成错误，污染 `NOS`。

- 负向 near-orbit 的 contract signal 需要显式进入 agent / evaluator。
  仅靠 rename/paraphrase 风格鲁棒性不足以支撑 `NOS`；只要 arg type/range mutation 不进入决策，agent 就会在 `G-` 上“稳错”。

- Qwen3 的 non-thinking 模式会在 ToolShift seed suite 上显著滑向保守控制。
  在 `enable_thinking=False` 下，模型大量输出 `ask_clarification`，把 `NOS` 顶到 1.0，但同时 `CAA_clean=0.167`、`CAA+=0.056`、`POC=0.0`。这正是 proposal 里需要防的 refusal gaming，后续主表必须联合报告 coverage / selective risk。

- 非 Qwen 公共模型 sanity check 值得保留，即使它不是 strongest baseline。
  `Llama-3.2-3B-Instruct` 在 TOOLSHIFT blind 上只有 `CAA=0.625 / NOS=0.273`，在 ToolEVO bridge 上则表现成 `NOS=1.0 / POC=0.125 / coverage=0.438` 的过保守 blocker。它的价值不在于分数强，而在于排除“外部 comparability 只来自 Qwen 家族”的质疑。

- 小模型会主动“重写参数”而不是保持 canonical argument surface。
  `Qwen3-0.6B` 在 reminder / calendar 类样本里会把 `tomorrow 9am` 改写成绝对时间字符串，或把 `Beijing time` 直接写成 `Beijing`。这类输出在执行上未必完全错误，但在 ToolShift 的 canonical action 评测里会被判为 argument grounding failure。

- `negative_contract` 的 admissible control policy 需要更细的人审。
  在当前 seed suite 中，这类样本默认要求 `ask_clarification`。但 `Qwen3-4B` 倾向于输出 `abstain`，导致 `negative_contract` 的 `CAA=0.0`。这提示一部分样本可能不够 `unambiguous core`，后续进入 real split 前必须做 policy audit，决定是否把部分样本移到 `ambiguous split`。

- `unambiguous core / ambiguous split` 一旦真的落盘，主表信号会明显变干净。
  把 `reminder_tax_form` 和 `calendar_toolshift_sync` 的不稳定 views 移出主表后，Qwen3-0.6B thinking 从 `CAA=0.417 -> 0.538`，Qwen3-4B thinking 从 `CAA=0.472 -> 0.654`，而且 `CAA_positive` 统一拉到 `0.75`。这说明之前的主表确实被 under-specified 样本污染了。

- `negative_deprecate` 需要固定为单一 control policy，否则主表会被 evaluator 自己的宽松定义污染。
  对当前 seed suite，`deprecated + no substitute in schema` 足以支持 `abstain-only`。这比把 `ask_clarification` 一起放进 admissible set 更符合“主表只保留稳定 policy”的 proposal 原则。

- 新增 truly unambiguous near-orbit 样本后，`NOS` 的解释确实更稳定了。
  `description_grounded` 的 `NOS` 从 `0.400 -> 0.571`，`Qwen3-4B` 的 `NOS` 从 `0.400 -> 0.500`。这说明之前 near-orbit 主表过小，容易被个别 borderline policy 样本主导。

- 时间类工具的难点不只是 tool choice，还包括 slot boundary。
  Qwen 常把 `2026-03-12T15:00:00 Asia/Shanghai` 整体塞进 `start_datetime`，而不是分成 `start_datetime=2026-03-12T15:00:00` 与 `timezone=Asia/Shanghai`。这在 ToolShift 里应算作 argument grounding failure，而不是 schema invariance 失败。

- 这类时间 slot-boundary 错误适合用 deterministic canonicalizer 修，不该混进方法贡献。
  当工具同时存在 `*_datetime` 与 `timezone` 两个参数，且模型输出满足严格模式 `ISO datetime + IANA timezone` 时，可以安全拆分。重判后，Qwen3-0.6B 的 `CAA` 从 `0.447 -> 0.526`，`CAA_clean` 从 `0.333 -> 0.500`，`CAA+` 从 `0.556 -> 0.667`。命中的都是 absolute-time views，而不是语义错误样本。

- 当前 8-case audited seed suite 对 matched-budget 方法比较还不够“甜点区”。
  对 frozen embedding bottleneck 来说，`combo_holdout` 几乎饱和；而 `case_holdout_cv` 又直接把 `CAA_clean / CAA+` 打到 0。也就是说它同时缺少能区分方法的中等难度 split。

- `SCC-lite` 的强正则会优先把模型推向更保守的 control，而不是自动提升 invariance。
  在 `lambda_inv = lambda_ctr = 0.5` 时，`SCC-lite` 在 `combo_holdout` 上从 `CAA = 0.974` 掉到 `0.947`；降到 `0.1 / 0.1` 后，只能和 `AugOnly` 持平，仍无独立增量。后续若继续做方法比较，必须先修 split 或 action bottleneck，而不是盲目加大一致性权重。

- 当前 frozen embedding pilot 学到的主要不是 transferable tool semantics，而是 conservative control。
  在 `case_holdout_cv` 上，两种方法都表现为 `CAA_clean = 0.0`、`CAA+ = 0.0`，但 `NOS = 0.643`、coverage 仍在 `0.605` 左右。这个模式说明模型在 OOD case 上会先退到 `ask_clarification / abstain`，不能把它误读成 near-orbit sensitivity 学对了。

- richer same-family synthetic split 能把旧 seed 的“全崩 / 全饱和”死区拉回中等难度。
  扩到 18 cases、每个 primary family 3 个实例后，`case_holdout_cv` 从旧 seed 的 `CAA = 0.237` 提到 `0.880`，`CAA+` 从 `0.000` 提到 `0.944`，`NOS` 也稳定在 `0.792`。这说明 proposal 的 same-family OOD 方向是对的，问题主要出在旧 split 太小。

- 但 split 修好以后，当前 `SCC-lite` 仍然没有显示独立增量。
  在 richer family suite 上，`AugOnly` 与 `SCC-lite` 在 `combo_holdout` 和 same-family `case_holdout_cv` 上完全持平，而 `action-state similarity` 还略低于 `AugOnly`。这意味着当前没有 gap 已经不能再只怪 benchmark 太差；更可能是 bottleneck / loss 设计还不够贴 thesis。

- richer suite 里的剩余难点主要集中在 `clean / positive_paraphrase`，而不是 rename。
  same-family `case_holdout_cv` 下，`positive_rename` 和 `positive_combo` 都是 `18/18`，但 `clean` 和 `positive_paraphrase` 只有 `15/18`。这提示后续 factorized 诊断应该重点看 description / contract grounding，而不是继续纠结名字表面变化。

- richer family suite 现在已经形成了有用的 synthetic OOD 难度梯度。
  `combo_holdout` 近饱和，`case_holdout_cv` 中等难度，`family_holdout_cv` 则直接把 `CAA_clean / CAA+` 打到 0。这个梯度比旧 8-case seed 更符合 proposal 里“逐层外推”的实验逻辑。

- 当前 `family_holdout_cv` 的失败本质上是跨-family tool semantics 不迁移，而不是 positive orbit 小修小补。
  在 family-holdout 下，两种方法的 `clean / positive_rename / positive_paraphrase / positive_combo` 全部失败，只剩部分 negative control 还能做对。也就是说现在模型靠的是“保守拒绝”，不是 semantic generalization。

- `SCC-lite` 在 family-holdout 上的微小正增量不足以支持方法学 claim。
  这次唯一新增正确样本是 `email_demo_confirmation::negative_deprecate`，从 `ask_clarification` 变成了 admissible 的 `abstain`。这种增量只能算 control policy 微调，不能算 proposal 所要求的 tool semantics 增量。

- 对 saved `records.json` 做 factorized 诊断，能快速区分“不会选工具”和“根本不敢执行”。
  在 richer synthetic 的 `family_holdout_cv` 上，`AugOnly / SCC-lite` 的 `execute_rate` 都是 `0.0`，而 `wrong_tool_choice / argument_grounding_error / invalid_execute_contract` 也都是 `0`。这说明当前主误差源不是 tool head 或 slot head，而是 execute gate / semantic trigger 先塌了。后续若继续改方法，先修这层才对齐 proposal。

- `action-state similarity` 高，不等于 execute gate 在跨-family OOD 上可用。
  `prototype execute gate` 在 train fold 上可做到近乎完美的 execute/non-execute 拟合，但在 `family_holdout_cv` 上依然 `execute_rate = 0.0`。这说明“representation 看起来很稳”并不自动推出 “gate 可泛化”；proposal 后续若谈 representation invariance，必须始终配合真正的行为级 OOD 验证。

- direct `request ↔ visible tool contract` semantic matching 能显著修复 cross-family execute collapse。
  `semantic_gate` 在 richer `family_holdout_cv` 上把 `CAA_clean` 拉到 `1.0`、`CAA+` 拉到 `0.981`、`POC` 拉到 `0.944`，同时 `execute_rate` 从 `0.0` 提到 `0.824`。这说明 visible contract semantics 本身足够强，当前欠缺的不是“完全不会泛化”，而是缺少把 schema semantics 直接接入 action gating 的机制。

- 一旦 execute gate 被修好，主误差会从 under-execute 转移到 contract-aware inhibition。
  `semantic_gate` 把 `clean / positive_*` 基本救回后，剩下最大的错误面立刻变成 `negative_contract = 36/36 wrong_tool_choice`。这提示下一步不该再优化 positive retrieval，而该显式建模 `contract mutation -> non-execute` 的 inhibition。

- schema-visible contract compatibility 本身足以修复 richer synthetic 上的大部分 near-orbit inhibition。
  在 `semantic_gate` 上加一个简单的 rendered-contract compatibility 检查后，`family_holdout_cv` 的 `negative_contract` 从 `36/36 wrong_tool_choice` 直接变成 `36/36 correct_non_execute`，同时 `CAA_clean` 仍是 `1.0`、`CAA+` 仍是 `0.981`。这说明当前 synthetic OOD 上，contract inhibition 不一定需要更复杂的 latent machinery，关键是把 schema-visible incompatibility 真正接入决策。

- 当 `CAA+` 和 `NOS` 已在 synthetic family-holdout 上同时接近饱和，下一步应尽快转入 real split。
  `semantic_contract_gate` 已达到 `CAA=0.972`、`NOS=0.944`、`POC=0.944`。继续只在同一 synthetic suite 上微调，价值会越来越低，更可能学到 benchmark-specific heuristics，而不是 proposal 真正关心的现实迁移能力。

- `schema-hard-signal inhibition` 能打穿 synthetic near-orbit，但不足以覆盖 real capability removal。
  在 real split v1 上，`semantic_contract_gate` 已经保持 `CAA_clean = 1.0`、`CAA+ = 1.0`，并且能正确处理显式 `deprecated` 的 Slack `files.upload`。但它仍会误执行 Notion `search` 替代旧数据库列表、以及 Stripe `total_count` 能力移除这两类 case。原因不是 arg type/range，而是“能力缺口”主要写在 description / replacement semantics 里。real split 下一阶段必须显式建模这类 description-level contract gap。

- description-level negative cue 与 request capability overlap 可以作为 real split 的有效 bootstrap inhibition。
  在当前 real split v1 上，把 `no longer / does not exactly / not supported` 这类 description cue 与 request capability token overlap 接入 gate 后，`semantic_capability_gate` 从 `CAA=0.833 / NOS=0.333` 提升到 `CAA=1.0 / NOS=1.0`，同时 richer synthetic `family_holdout_cv` 不回退。这说明在 learned model 之前，显式 capability-gap detector 是一个合格的 bootstrap 靶点。

- 对 real capability-gap，`cue clause` 本身不一定包含完整任务语义；一旦看到 negative cue，应该读整段工具描述。
  在 expanded real split v2 上，`database parent -> data_source parent` 这类 case 会让 clause-only detector 漏报，因为负向子句只写了 “database identifier no longer identifies the exact parent”，没有重复 “create page”。把 overlap 范围放宽到整段工具描述后，这类 parent-scope change 才会被稳定捕获。

- execution sanity 最有价值的不是“更真实”，而是把标签和 effect 绑在一起。
  对 expanded real split，deterministic mock execution 已经足够回答一个关键问题：clean / positive 的 canonical primary action 是否真的保留了同一 effect，negative 的 old action 是否真的不再满足请求。即使它不是真实在线 API，也能防止 benchmark 退化成“只看 schema 描述、没有 effect grounding”的纸上推理。

- 新 vendor family 最容易暴露的，不一定是 negative inhibition 漏洞，也可能是 generic `update`-style positive migration 的 under-execute。
  在 Google Drive family 里，`parents.insert/delete -> files.update add/removeParents` 首轮并没有变成 `wrong_tool_choice`，而是被 gate 压成了 `ask_clarification`。这说明 current panel 的下一类风险不是“又乱执行了”，而是“generic current method name 让正迁移过阈值失败”。

- 对这类 near-threshold 正迁移，description-only 调整不一定够；更稳的是窄范围 semantic rescue。
  当 active tool 同时满足 `contract compatible`、`no description capability gap`、`request/tool overlap 足够高` 且 `best-vs-second` 有明确领先时，可以允许一次低于 threshold 少量余量的 execute rescue。Google Drive family 里，这把 `CAA+` 从 `0.8` 拉回 `1.0`，同时 real negatives 和 synthetic family-holdout 都没有回退。

- 新增 vendor family 最有价值的信号之一，是看 heuristic baseline 会不会继续掉分。
  Jira family 接进来之后，`LexicalShortcut` 从 `CAA 0.531` 掉到 `0.500`，`DescriptionGrounded` 从 `CAA 0.719` 掉到 `0.650`，而且 `CAA+` 也从 `1.000` 掉到 `0.846`。这说明 fixed panel 不是靠方法特化“打穿”了，而是在扩到新 family 后仍然保持诊断性。

- privacy / identity migration 是一类独立于 field-removal 的 real capability gap。
  Jira 的 `username/userKey -> accountId/query` 不只是参数改名；当请求仍依赖 legacy username 时，当前 schema 虽然还有 `query` surface，但 old intent 已不再直接可执行。这类 negative 更像 “identifier semantics removed” 而不是 “field removed”，但 description-aware inhibition 同样能处理。

- request-level replay 和 execution-level sanity 不应混成一件事。
  request replay 关注的是 “当前 rendered surface 到底会发出什么 path/query/body”；execution sanity 关注的是 “发出去以后 effect 是否还成立”。在当前 5-family real panel 上，两者都做到 `1.0`，说明 benchmark 现在同时覆盖了 surface correctness 和 effect correctness。

- positive migration 的一个强信号，是 request shape 变了但 effect signature 不变。
  Drive `parents.insert -> files.update addParents`、Jira `name -> accountId` 都属于这种情况。把它们显式落成 replay artifact，比只说 “positive orbit 不变” 更能防止研究退化成抽象语义口号。

- 官方文档 smoke 应该抓稳定 marker，不该押整句叙述文案。
  Drive shortcuts 页面会保留 `one parent`、`shortcuts`、`link to other files or folders` 这类稳定 cue，但整句产品文案会漂移。对 official-doc smoke，method/path/param/negative-cue 这类 marker 比长句 quote 更适合作为回归锚点。

- machine-readable API smoke 也要尊重 provider 的版本分裂，不能默认“一份 spec 走天下”。
  Jira Cloud 的 v2 与 v3 官方 JSON surface 分别落在 `swagger.v3.json` 和 `swagger-v3.v3.json`。如果用一份 v3 spec 去验证 v2 clean request，会把真正的 version migration 误写成 surface mismatch。

- 对 negative capability-gap，machine-readable spec 和 docs cue 是互补关系，不是替代关系。
  OpenAPI / discovery 能很好验证 positive request shape 是否落在官方 surface 上，但像 `legacy username removed` 这种语义收缩，machine-readable spec 里可能还残留兼容字段。要稳住 near-orbit negative，仍然需要 `non-execute + official removal cue` 联判。

- 带官方 migration guide 和 discovery/OpenAPI surface 的 family，是扩 real fixed panel 的高性价比入口。
  Google Sheets 这类 provider 可以用一组公开 source 同时支撑 benchmark generation、request replay、official-doc smoke 和 machine-readable api-surface smoke，不需要等待凭证或私有样例就能把新 family 接进完整验证链。

- `retrieval + rerank` 文档基线值得保留成独立 baseline bucket，但不要误当成 strongest method。
  它在 `schema-visible`、documentation-heavy benchmark（例如 API-Bank bridge）上会明显强于 prompt-only public model，但在 BFCL / ToolEVO / TOOLSHIFT blind 上并不占优。更合理的定位是：它能证明 benchmark 不只是难倒“作者自家方法”，同时也说明单纯文档检索并不能替代 capability-gap inhibition。

- description-aware deterministic inhibition 仍需要 request-token 级 overlap，不能只靠抽象负向措辞。
  在 Sheets negative 里，仅写 “not supported” 不够稳定；一旦 rendered description 明确包含 `does not provide this specific operation`、`Drive API Files.list` 这类 replacement/capability token，official-doc smoke 和 main evaluator 才能稳定联动到 `correct_non_execute`。

- Google discovery 里的 `{+resourceName}` 不能用 segment-count path matcher 验证。
  People API 的 `people.connections.list` 使用 `v1/{+resourceName}/connections`，实际请求会展开成 `/v1/people/me/connections` 这类跨 segment path。若 validator 先按 `/` 切段再逐段比对，会把真实存在的 positive request 误报为 surface mismatch。对 discovery-backed smoke，full-path regex matcher 更稳。

- `read-only but workaround exists` 是一类独立于 `removed field` / `deprecated endpoint` 的 negative capability gap。
  People API 的 Other Contacts 不是简单“字段删了”，而是“必须先 copy 到 My Contacts 才能改”。`semantic_contract_gate` 会把这类 case 误当成可执行 related tool，而 `semantic_capability_gate` 能把它压回 admissible non-execute。后续扩 family 时，应主动寻找这类有 workaround 但非 drop-in replacement 的 negative。

- OpenAPI-backed smoke 不能只看 `paths`，也不能假设 requestBody 总是内联。
  Confluence v2 把 `/wiki/api/v2` 放在 `servers[].url`，同时 `PUT /pages/{id}/title` 的 body 通过 `components/requestBodies` 间接引用。machine-readable validator 若忽略这两层，会把真实 positive migration 误判成 surface mismatch。对 public-spec family，`servers` 前缀和 requestBody `$ref` 都应作为默认支持。

- 不能把 Swagger 2.0 family 当成 “低配 OpenAPI” 直接硬套。
  Bitbucket 这类 provider 仍把请求前缀放在 `basePath`，而不是 `servers`。如果 validator 不把 `basePath` 拼进 candidate templates，`/2.0/workspaces/...` 这类真实 request 会全部 miss。对 public-spec family，`servers` 和 `basePath` 都应该进入统一 path-prefix 逻辑。

- 做 fixed-panel 方法比较时，vendor-level 结论必须回到 benchmark `family_tag`，不能直接拿旧 diagnostics 的 `by_family`。
  现有 `diagnose_saved_records.py` 的 `by_family` 实际是按 `primary_tool_id` 分组；如果直接拿它回答 “哪个 vendor family 还没守住 negative”，会把 tool-level 和 family-level 混在一起。对 frozen panel 的方法比较，应该先把 `records.json` join 回 benchmark metadata。

- 当 `clean / positive` 已经饱和时，最有信息量的对比不是总 `CAA`，而是 paired negative flips。
  当前 `semantic_contract_gate -> semantic_capability_gate` 的全部独立增量，都来自 `wrong_tool_choice -> correct_non_execute` 的 negative capability-gap views，而且 `regressed_pairs = 0`。这种 paired delta 比继续加 family 更能直接回答 proposal 里“方法到底多学会了什么”。

- raw learned inhibitor 如果对所有 execute 候选都启用，很容易过度压制 cue-free positives。
  在 frozen `9-family` panel 上，`semantic_learned_capability_gate v1` 只回退了 `1` 条样本：`sheets_update_formula::positive_version_migration`。这个样本的关键特征是 `cue_clause_count = 0`、`has_gap_rule = 0`。这说明 learned scorer 的第一层保护不是更高阈值，而是先收紧应用范围。

- 对 capability inhibition，`cue-triggered learned scorer` 是一个有效的中间形态。
  先用稳定 negative cue 决定 “是否进入 inhibition 子问题”，再让轻量 learned scorer 决定是否真的 non-execute，可以在当前 fixed panel 上追平 rule gate，同时避免 v1 的 positive over-inhibition。这比一上来让 scorer 接管所有 execute 候选更稳。

- 当前 frozen `9-family` panel 上，`cue_clause_count` 对正负几乎是完美分隔符：
  `clean / positive` 全为 `0`，`negative_near_orbit` 全为 `>=1`。这意味着如果把 generic execute 特征和 cue-family 特征混在一起训练，scorer 反而可能被泛用特征带偏；先裁掉 `best_active_score / score_margin / tool_overlap`，再看能不能去 guard，更稳。

- 当 raw scorer 的回退来自 feature pollution，而不是 supervision 不足时，优先做 feature pruning，比继续堆 guard 更有价值。
  `semantic_sparse_capability_gate` 只保留 `6` 个 cue-family features，就能在当前 frozen panel 上追平 `semantic_capability_gate`，同时去掉外层 `capability_require_cue`。这说明这一步的关键不是更复杂的模型，而是把 inhibition 子问题和 execute 子问题真正解耦。

- 如果连续 cue-overlap 特征已经把正负干净分开，就可以继续删掉显式 binary cue。
  当前 frozen panel 上，`max_cue_overlap / total_cue_overlap` 对 `clean / positive` 全为 `0`，对 `negative_near_orbit` 全为正值。于是 `semantic_continuous_capability_gate` 只用 `3` 个连续特征，也能追平 `semantic_sparse_capability_gate`。这说明 binary cue 不是当前 panel 上的必需条件。

- 但 “去掉 binary cue” 不等于 “摆脱 cue-driven inductive bias”。
  `semantic_continuous_capability_gate` 依然依赖 hand-crafted overlap statistics。只是在当前 panel 上，这比 `has_gap_rule / cue_clause_count` 更弱。下一步若还想更接近 proposal 的方法学结论，就该继续削 overlap 特征，转向更原生的 learned text features。

- 在当前 frozen `9-family` panel 上，cue-clause embedding similarity 已经足够替换 overlap 统计。
  用 `description_similarity / max_cue_similarity / mean_cue_similarity` 这 `3` 个 embedding 特征，可以让 `semantic_embedding_capability_gate` 追平 `semantic_continuous_capability_gate`，而且 `improved_pairs=0 / regressed_pairs=0`。这说明当前 panel 的 inhibition boundary 已经不依赖 token-overlap 计数本身。

- 但 cue-clause extraction 仍然是方法里的最后一层显式 hand-crafted scaffold。
  `semantic_embedding_capability_gate` 虽然摆脱了 `description_overlap / max_cue_overlap / total_cue_overlap`，仍然先用 `_capability_cue_clauses()` 定位负向描述子句，再做 similarity scoring。后续如果要更接近 proposal 的“learned method”叙事，下一步应优先去掉这层 clause extraction，而不是继续压缩已经饱和的 fixed panel 分数。

- 直接把 cue-specific clause extraction 拿掉，会同时损伤 negative inhibition 和 positive execute。
  `semantic_raw_text_capability_gate` 只用 `tool / description / argument` 相似度时，frozen panel 上会同时出现 `wrong_tool_choice` negative leak 和 `missed_execute_ask_clarification`。这说明当前问题不是“cue clause 太细”，而是 whole-description 表征过粗，无法稳定定位 capability-gap 语义。

- generic all-clause pooling 比 whole-description 好，但仍不足以替代 cue-specific localization。
  `semantic_description_pool_capability_gate` 把 `regressed_pairs` 从 `22` 降到 `16`，说明 clause granularity 本身有帮助；但它仍明显落后于 `semantic_embedding_capability_gate`。当前真正提供独立价值的，不只是 clause 粒度，而是对负向 capability-gap 子句的有针对性定位。

- 当前 frozen panel 给出的最清晰下一步，不是继续删规则，而是把 “定位哪一段描述在说 capability gap” 变成 learned subproblem。
  换句话说，下一步该尝试的是 learned clause localization 或带 cross interaction 的 pair scorer，而不是继续在线性 whole-text similarity 上做小修补。

- 但 “换成 interaction” 本身并不自动解决问题；在 low-sample fold 上，linear interaction 很容易学成更保守的 execute gate。
  `semantic_interaction_capability_gate` 把 `NOS` 维持在 `0.818`，却把 `CAA+ / POC` 一起压到 `0.680`，`execute_rate` 也掉到 `0.590`。这说明如果 pair model 不够强，interaction route 只会把错误从 `wrong_tool_choice` 变成 `missed_execute`。

- 当前 frozen panel 已经给出很明确的 model-selection结论：
  1. linear whole-text similarity 不够
  2. linear generic clause-pooling 不够
  3. linear localized interaction 也不够
  下一步若还想继续靠“更 learned”的方法替代 cue-specific scaffold，模型类本身就必须升级，不能继续只在线性 scorer 上加特征。

- train-time supervised clause localization 确实比 generic interaction 更接近正确方向。
  `semantic_clause_localization_capability_gate` 把 `CAA` 从 `0.688` 拉回 `0.875`，`regressed_pairs` 从 `45` 降到 `18`。这说明 “先学会选哪一条描述子句，再决定 inhibit” 的结构是有价值的。

- 但当前 low-sample 线性 localizer 仍然明显过拟合。
  当前 fold train metrics 里，clause localizer 和 dense scorer 几乎都是 `100%` accuracy / recall，而 test 端仍然保留明显的 Drive under-execute 和少量 hard negative leak。下一步的主问题不再是 “有没有 localization”，而是 “如何让 learned localization 泛化”。

- proposal-aligned 的下一步优先级已经更清楚了：
  1. 先做 localizer regularization / calibration
  2. 如果仍不够，再升级到更强的 pair model
  3. 不再回去试 generic whole-text baseline

- 但“把 head 降成低维 calibrated scalar”并不是有效的 regularization。
  `semantic_clause_localization_calibrated_gate` 比高维 interaction 版更差，说明当前 learned route 的问题不只是 interaction 维度过高。简单降维会同时伤到 positive execute 和 negative inhibition。

- frozen encoder 上的 joint pair-text embedding 不能自动替代 cue-specific localization。
  `semantic_pair_text_capability_gate` 虽然把 request 和 localized clause 真正拼成 joint input，但在 fixed panel 上主要学成了更保守的 execute gate：`clean / positive` 大量 under-execute，而 `negative` 只保住了大部分 capability-gap inhibition。对这个任务来说，pair input 本身不是解；真正关键的是 pair model 的表达能力。

- stronger pair head 确实比 linear pair head 更好，但仍会暴露明显的 positive/negative tradeoff。
  `semantic_pair_text_mlp_capability_gate` 把 linear pair-text 的 `CAA / CAA+ / POC` 明显拉回来了，但 `NOS` 从 `0.909` 掉到 `0.682`。这说明当前任务里，frozen encoder pair embedding 的瓶颈不只是 head 太弱；如果 pair model 不足够强，提升表达能力会先放松 negative inhibition，再救回 positive execute。

- 现成 pretrained reranker 不能直接当作 capability-gap inhibitor 用。
  `semantic_cross_encoder_capability_gate` 用 `Qwen3-Reranker-0.6B` 做 joint pair scoring 时，`clean / positive` 基本可用，但 `negative_near_orbit` 大面积退化成 `tool_choice_error`。这说明 retrieval/reranking relevance 和 capability-gap inhibition 不是同一任务；pair model 需要显式的 negative-localization supervision，而不只是 threshold calibration。

- global hard-negative / class-balanced weighting 确实会把 fine-tuned pair model 往 negative inhibition 推，但它本身不是最终解。
  当前 `semantic_cross_encoder_hard_negative_capability_gate` 把 `capability_gate_train_inhibit_recall` 从 `0.151` 拉到 `0.456`，test 端 `NOS` 也从 `0.364` 拉到 `0.409`；但 `CAA+ / POC` 同时从 `0.900` 掉到 `0.760`。这说明 hard-negative weighting 方向是对的，但如果没有单独保护 positive execute，它只会把模型推成更保守的 inhibitor。

- class balance 不只是 loss 权重，还会被 decision threshold 抵消。
  这轮一开始只改 weighted BCE，smoke 结果仍然偏 execute-friendly；把 threshold selection 一起切成 weighted 之后，`NOS` 才真正抬起来，但 full-strength inverse-frequency 也会马上把 `clean / positive` 压塌。后续如果继续沿主线推进，需要把 “training objective” 和 “decision calibration” 视为同一个设计问题来处理。

- explicit positive-retention calibration 不是只要加一个 execute-recall 约束就够。
  当前 `semantic_cross_encoder_asymmetric_capability_gate` 把 `CAA+ / POC` 从 hard-negative route 的 `0.760` 拉回到 `0.920`，但 `NOS` 同时从 `0.409` 掉回 `0.273`，而且 train-side `capability_gate_train_inhibit_recall` 也从 `0.456` 掉到 `0.049`。这说明 single-threshold constrained calibration 会直接把 hard-negative 学到的 inhibition 信号冲掉。

- 现在训练目标和决策规则已经都试到了：缺的不是再加一个后处理约束，而是更强的 asymmetric structure。
  当前证据链已经覆盖：
  - capability-only fine-tune
  - multitask supervision
  - hard-negative / class-balanced weighting
  - explicit positive-retention constrained calibration
  结论是：只在这几个轴上做同级别小修都不够。下一步更可能有效的是 train-time asymmetric objective，或者带 abstain band 的 dual-threshold decision rule。

- 但 train-time execute-margin penalty 也不会自动形成更好的 asymmetric structure。
  当前 `semantic_cross_encoder_asymmetric_objective_capability_gate` 的 train-side `capability_gate_train_inhibit_recall` 仍与 hard-negative route 基本同级（`0.456 -> 0.446`），可 test 端却同时弱于 hard-negative 和 single-threshold asymmetric calibration。这说明在 single-score fine-tuned pair model 上，execute-retention pressure 会优先表现成泛化噪声，而不是 proposal 需要的双能力闭环。

- 当 hard-negative、single-threshold asymmetric calibration、以及 train-time asymmetric objective 都跑过之后，下一步不该再做同级别 margin/weight 微调。
  这条证据链已经足够说明：当前真正缺的不是更多 scalar calibration，而是更结构化的 decision rule，例如 dual-threshold / abstain-band。

- 但 plain dual-threshold / abstain-band threshold search 也不会自动长出一个有用的 band。
  当前 `semantic_cross_encoder_dual_threshold_capability_gate` 在两个 seed 上都学到 `abstain_threshold == ask_threshold`、`train_abstain_rate = 0.0`，最终完全退化成 `hard-negative` 单阈值。这说明如果训练信号里没有显式的 abstain 偏好，control-aware threshold search 会自然塌回更简单的 binary decision。

- 当 single-threshold calibration、train-time asymmetric objective、和 plain dual-threshold search 都跑过之后，下一步不该继续扫 threshold。
  如果还想沿 decision-rule 路线推进，必须把 `abstain` 当成一类有独立偏好的结构化输出，而不是希望它从 binary inhibit score 里“自然长出来”。

- 一旦同一个 fixed panel 被连续用于方法选择，它就不再是可信的 blind test。
  最稳的治理方式是：把该面板显式降级成 `dev panel`，继续承担回归和诊断；另建新的 blind families，只做结构验证，直到 blind panel 规模足够再承接最终方法结论。

- blind panel 不能只堆 family 数，还要刻意拉开 negative style。
  目前 Trello 提供的是 “related REST endpoint exists but not drop-in”，而 YouTube 补的是 “same endpoint capability/parameter removed or method unsupported”。这种风格多样性比继续复制同一种 route-replacement 模板更重要。

- blind family 的扩容不一定要求新 vendor；新的 version lineage 也可以是有效 blind family。
- blind panel 到 `4-6` 个 families 之后，应该立刻冻结成治理资产。
  只靠文档约定不够，最好同时写入 benchmark metadata，并用单独的校验脚本强制检查 `method_selection_allowed=false`、blind/dev family disjoint、以及 audit 路径存在。
  当前 `youtube_channels` 与已有 `youtube` 虽然同属 YouTube vendor，但它引入的是不同的 family tag 和不同的负样本机制：`single-step feed -> lookup split`、`recommendations-only -> broader surface`。只要 lineage 与 negative style 都足够不同，这类 family 仍然能为 blind panel 增加真正的新信号。

- blind negative style 里要刻意补“resource-context split”和“out-of-band replacement”。
  `github_rest` 说明 blind panel 不能只靠 parameter removal 或 lookup split。像 `delete reaction by id -> resource-specific delete endpoints` 这种需要额外上下文的迁移，以及 `source imports -> migration guide / CLI / non-REST path` 这种 API 外替代，都会给 evaluator 带来不同于现有 families 的边界压力。

- blind panel 也需要显式补 response/body semantics，而不是只覆盖 route 和 parameter 迁移。
  `gitlab_rest` 这轮证明了两类新信号都有价值：一类是 `merged_by -> merge_user`、`merge_status -> detailed_merge_status` 这种 response-field migration；另一类是 `changes endpoint -> diffs listing`、`namespace -> namespace_id / namespace_path` 这种 response/body contract split。没有这类 family，blind panel 会过度偏向 surface-level route changes。

- blind panel 如果不显式补 auth/scope/permission semantics，会默认偏向“只看 surface contract”的世界。
  `slack_auth` 这轮提供了三种此前缺失的 blind 信号：OAuth flow migration（`oauth.access -> oauth.v2.access`）、scope narrowing（`users:read -> users:read + users:read.email`）、以及 one-shot permission inventory split（`apps.permissions.info -> scopes.list + resources.list`）。这类 family 能检验 agent 是否会把“同一语义动作但权限模型变了”与“权限语义已拆分、不再 drop-in”区分开来。

- 给 cross-encoder 加训练信号，如果 localizer 仍然按独立 binary threshold 去切，也可能直接塌成 “永不选 clause”。
  当前 `semantic_cross_encoder_supervised_capability_gate` 在所有 family fold 上都出现 `clause_localizer_threshold=1.000001`、`train_positive_recall=0.0`。这说明对稀疏正例的 clause-localization 子问题，独立阈值优化很容易被类别不平衡推到全负解；下一步需要 ranking-style objective 或显式正负采样，而不是继续调阈值。

- 但把 localizer 改成 ranking-style top selection，本身也不够。
  当前 `semantic_cross_encoder_ranked_capability_gate` 虽然不再塌成全负解，`clause_localizer_threshold=0.0`、`train_positive_rate=1.0`，但 `train_positive_recall` 仍只有 `0.000 ~ 0.083`。这说明问题不只是 threshold 形式，而是现成 reranker 的相关性排序本身没有学会 capability-gap clause ranking。

- 显式正负采样的 pairwise localizer training 确实比 top-selection 更有用，但增量仍然有限。
  当前 `semantic_cross_encoder_pairwise_capability_gate` 把 `clause_localizer_train_positive_recall` 提到 `0.059 ~ 0.167`，`NOS` 也从 `0.455` 提到 `0.500`。这说明 ranking signal 本身是必要的；但如果只训练一个轻量 pairwise ranker，仍然学不到足够稳的 capability-gap localization。下一步若继续沿主线推进，优先级应是 listwise objective 或直接 fine-tune cross-encoder 本体。

- listwise objective 并不会自动把 train-side ranking 增益转成 fixed-panel test 增益。
  当前 `semantic_cross_encoder_listwise_capability_gate` 把 localizer 的 train mean 又小幅抬高到 `train_accuracy=0.218`、`train_positive_recall=0.100`，但 `CAA / CAA+ / NOS / POC` 与 pairwise route 完全相同。这说明当前瓶颈已经不在 ranking loss 形式，而在 reranker 本体的表示能力；下一步应直接转向真正 fine-tuned cross-encoder pair model。

- 真正 fine-tune cross-encoder 参数，也不等于自动学会 capability-gap inhibition。
  当前 `semantic_cross_encoder_finetuned_capability_gate` 直接更新了 `171M` 个 reranker 参数，但结果只是把 `CAA+ / POC` 拉到 `0.900`，同时把 `NOS` 压到 `0.364`。这说明当前瓶颈已经不只是 “有没有 trainable capacity”，而是训练信号本身仍然在把模型推向正负 tradeoff。

- capability-only pair fine-tune 会天然偏向正样本占优的执行策略。
  这轮的 `capability_gate_train_inhibit_rate` mean 只有 `0.031`、`train_inhibit_recall` mean 只有 `0.151`，对应 test 端大量 `negative capability-gap` 继续漏执行。后续如果继续沿主线推进，fine-tune 路线必须显式做 hard-negative / class-balanced weighting，或者把 localization 作为辅助任务一起训进去。

- teacher-distilled canonical bottleneck 即使在 train fold 上把 `tool / slot / gap` 蒸馏到近乎满分，也不会自动带来 held-out family 的 positive retention。
  当前 `TeacherDistilledBottleneckSCC` 在 decisive run 里只把 `NOS` 从 `0.606` 小幅推到 `0.636`，但 `CAA+ / POC` 仍然都是 `0.0`，错误桶仍然几乎全是 `missed_execute_ask_clarification`。这说明“把 strongest scaffold teacher 的最终决策蒸馏进 bottleneck”并不足以复制 teacher 的真正 inductive bias。

- 如果一个 candidate SCC 方法在 `name_mask` 下不掉分，而在 `description_mask / contract_mask` 下也几乎不掉分，这通常不是“更语义化”，而是根本还没进入 grounded regime。
  当前 `TeacherDistilledBottleneckSCC` 的 masking 结果就是这个形态：`name_mask` 甚至略微升分，`description_mask / contract_mask` 也只让 `NOS` 掉 `0.03`。结合 `CAA+ / POC = 0.0`，更合理的解释是它仍处于 execute-collapse / over-abstain 区，而不是已经学会 description-grounded invariance。

- 但把 localization 作为辅助任务一起训进去，也不会自动解决 negative inhibition。
  当前 `semantic_cross_encoder_multitask_capability_gate` 把 `clause_localizer_train_accuracy` 直接拉到 `0.691`、`clause_localizer_train_positive_recall` 拉到 `0.619`，说明 multitask 的确学到了 clause localization；但 test 端 `NOS` 仍卡在 `0.364`。这说明当前主问题已经不是 “有没有 localization supervision”，而是 decision objective 仍然偏向 execute-friendly tradeoff。

- 当前 fine-tuned cross-encoder 主线最缺的不是更多 task，而是更强的 negative weighting。
  capability-only 和 multitask 两条 fine-tune 路线都把 `CAA+ / POC` 拉高了，却没有把 `NOS` 拉起来。后续如果继续沿主线推进，优先级应切到 hard-negative / class-balanced weighting，而不是继续叠 supervision task。

- 外部公开强模型在社区静态 function-calling benchmark 上表现良好，并不意味着它们会自然转移到 real API evolution。
  当前 `Qwen3-8B` 在 BFCL bridge 上达到 `CAA=0.840`，在 `simple_python / multiple` 上都为 `1.0`；但放到 TOOLSHIFT frozen blind panel 时仍掉到 `CAA=0.875 / CAA+=0.923 / NOS=0.636 / POC=0.923`。这说明 “静态 function-calling competency” 和 “schema-visible capability-gap inhibition” 需要分开表述。

- 公开 evolving-tool benchmark 更适合作为辅助 portability 证据，而不是 TOOLSHIFT blind panel 的替代物。
  `ToolEVO / ToolQA-D` 这类公开资产在 schema drift 和 explicit deprecation 上很有价值，也能桥接成 TOOLSHIFT-compatible views；但它们天然更偏正迁移和显式替换，不会自动覆盖 TOOLSHIFT 里 `slack_auth / gitlab_rest / youtube_channels` 这类 capability-gap negatives。

- 外部 execute-heavy baseline 能暴露 evaluator 里以前被内部 abstain-heavy 方法掩盖的隐含假设。
  这轮 `Qwen3-8B` blind run 第一次触发了 execute path 对 view-visible helper arguments 的 evaluator 崩溃。修复后，canonicalizer 现在会忽略不属于 canonical action 空间的 helper arg，而不是在内部抛错。后续凡是接入更强外部 baseline，都应优先检查 evaluator 是否隐式依赖了“模型通常会 abstain”。

- execute-heavy public baselines 也能继续暴露 benchmark 里的 canonical-slot 漏记。
  这轮 `Qwen3-4B` blind run 首次命中了 GitLab `merge_requests.get_with_changes` 的 `page / per_page` 分页参数路径，从而暴露出 blind asset 少记了 optional canonical slot `page`。说明外部 baseline 不只是“比较对象”，也是 benchmark protocol 的 fuzzing 工具。

- dev panel 上真正关键的不是 raw tool/arg names，而是 localized description / contract cue。
  当前 `semantic_embedding_capability_gate` 与 `semantic_clause_localization_capability_gate` 在 `name_mask` 下几乎不掉分，但在 `description_mask / contract_mask` 下都会明显掉分。这说明 proposal 的机制链后半段更该围绕 description/contract grounding，而不是 name sensitivity 本身。

- strongest scaffold baseline 的优势不只体现在行为分数，也体现在 decision-state geometry。
  当前 `semantic_embedding_capability_gate` 比 retained learned route 有更高的 `positive_state_similarity` 和更大的 `state_separation_gap`。这说明它不是单纯靠阈值“碰巧做对”，而是在内部 state 上更稳定地区分了 positive orbit 与 negative near-orbit。

- strongest scaffold baseline 的 claim 边界必须明确限定为 `schema-visible evolution`。
  当把 dev panel 的 negative near-orbit admissible action 放回 clean surface，构造成 `counterfactual impossible shadow` 时，`semantic_embedding_capability_gate` 会 `100%` 回到 execute，`impossible_CAA=0.000`。这说明当前 strongest result 证明的是 “会读 description / contract cue 并据此抑制误执行”，而不是 “能在无可观察线索的 hidden backend shift 上泛化”。

- 外部 benchmark 的 first-pass protocol bridge，优先级应放在“公开样本是否显式暴露 tool call”，不只看主题是否贴 evolution。
  `ToolEVO` 虽然最贴 API evolution，但公开 `ToolQA-D` test split 只放出了 question-answer pairs；真正的 API version shift 主要藏在环境代码 `api_vary.py` 里，缺少直接可桥接的公开 tool-call traces。相比之下，`API-Bank` 的公开 dialogues 明确包含 `API` turns、`api_name` 和 `param_dict`，因此更适合作为第一条 `TOOLSHIFT-compatible` external benchmark bridge。

- 公开 hosted function-calling endpoint 不一定适合作为 benchmark-paper 的主结果 baseline。
  2026-03-16 直接调用 `Gorilla OpenFunctions` 公共 endpoint 返回 `HTTP 502`。如果目标是写进 benchmark 论文主结果，优先选择可在本地 GPU + 公开权重上完全复现的 open baseline，例如 `Qwen3-8B`，而不是把 hosted service availability 变成结果瓶颈。

- blind panel 对 strongest scaffold baseline 仍然有必要，哪怕 dev panel 已经补了 masking / state / boundary 证据。
  当前 `semantic_embedding_capability_gate` 在 dev panel 上是满分，但 frozen blind review 掉到 `CAA=0.917 / NOS=0.727`，最明显的新压力来自 `slack_auth` 的 permission inventory split。说明 dev-perfect 只够做 mechanism evidence，不够替代 blind final review。

- retained learned route 在 blind panel 上会表现成 “negative 更保守、positive 更脆弱” 的 tradeoff。
  `semantic_clause_localization_capability_gate` 的 blind `NOS` 高于 strongest scaffold baseline（`0.818 > 0.727`），但 `CAA_clean / CAA+ / POC` 都更差。后续如果还要继续 learned route，不能再只看 dev-panel `NOS` 或 negative-localization signal，必须联合盯 blind positive retention。

- dev-vs-blind retained-method comparison 必须同时看 `NOS` 和 `CAA_clean / CAA+ / POC`，不能只看 blind 总分或单独一侧指标。
  当前 strongest scaffold baseline 的 blind drop 主要集中在 `NOS`，而 retained learned route 的 blind `NOS` 更稳，却是以更低的 `CAA_clean / CAA+ / POC` 为代价。blind 上的 “更保守” 不等于 “更强”。

- blind `auth/scope/permission` families 会优先暴露 scaffold baseline 的 negative inhibition 边界，而不是 positive retention 边界。
  `slack_auth` 这类 family 在当前 strongest scaffold baseline 上首先把 `NOS` 压穿到 `0.0`，但 `CAA+ / POC` 仍然保持满分。后续如果要扩 blind review 或补 final figures，这类 family 应该被视为首要压力测试，而不是普通补充案例。

- 如果 benchmark 的 negative admissible set 同时允许 `ask_clarification` 和 `abstain`，就必须显式报告 split sensitivity；否则 `NOS` 排名会被 protocol choice 隐性主导。
  当前 TOOLSHIFT blind panel 的 `10 / 11` negative views 都是 dual-control admissible。把它们压成 `single_action_only` 会让所有方法的 `NOS` 人为变成 `1.0`；压成 `ask_only` 会明显奖励 ask-heavy scaffold，压成 `abstain_only` 又会明显奖励 abstain-heavy public baselines。对这类 benchmark，set-valued evaluator 不是可选装饰，而是必须公开分析的协议核心。

- 小 blind panel 最值得先补的统计，不是追求漂亮显著性，而是做 family/vendor cluster bootstrap 和 leave-one-family-out。
  这轮 frozen blind 的 bootstrap/leave-one-out 说明了两件事：第一，区间确实宽，reviewer 对 small-N 的担心是合理的；第二，strongest scaffold baseline 的 blind 压力也并不是单个 family 一删就消失。对于当前规模的 benchmark，这类“不确定性 + 非单点依赖”证据比再报几位小数更有防守力。
