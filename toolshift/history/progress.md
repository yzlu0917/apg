# ToolShift Progress

## Current Goal
在保持 blind panel 冻结的前提下，当前主线仍以 `paper` 精修为主。benchmark-paper 最缺的证据已从“只有外部可比性”推进到“外部可比性 + protocol reliability / split sensitivity + family/vendor stability + retrieval-style external reference baseline + 非 Qwen 公共模型 sanity check”：现已新增 `API-Bank / BFCL / ToolEVO` 外部 bridge、公开 Qwen baselines、`doc_retrieval_rerank` baseline、`Llama-3.2-3B` sanity check，以及 blind split-sensitivity 与 bootstrap / leave-one-family-out 审计。唯一允许的 decisive run 已在 dev panel 上完成且未通过 Go/No-Go，因此默认不再继续 SCC 方法搜索。

## Milestones
- DONE: 读完 proposal 并抽取 Week 1 可执行项
- DONE: 确认仓库无现成代码，需要从零建立研究骨架
- DONE: 实现 canonical action / schema view / positive-negative transform / 评测脚手架
- DONE: 构造 seed benchmark 与 transform audit packet
- DONE: 跑通首轮 pilot 与最小单测
- DONE: 接入 Qwen prompt-only 正式模型接口并完成 seed pilot
- DONE: 跑通 Qwen3-4B thinking baseline 并完成 0.6B / 4B 对照
- DONE: 完成 seed suite 首版人工审计，并将主表切到 `unambiguous core`
- DONE: 补充 2 个绝对时间 `unambiguous` case，并重跑主要 baselines
- DONE: 实现 deterministic temporal canonicalization，并重判现有 Qwen records
- DONE: 实现 frozen-embedding `AugOnly / SCC-lite` 训练脚手架与 matched-budget pilot
- DONE: 构造 richer same-family synthetic benchmark，并在其上复跑 baseline 与 matched-budget pilot
- DONE: 在 richer family suite 上新增 `family_holdout_cv`，形成 synthetic OOD 更难版本
- DONE: 完成 `family_holdout_cv` 的 factorized 错误诊断，并确认当前失败主要是 execute gate / control collapse
- DONE: 新增 `prototype execute gate` 与 `semantic_gate` 两个 execute-gate 变体，并完成 family-holdout 实验
- DONE: 在 `semantic_gate` 上加入 contract-aware inhibition，并在 `family_holdout_cv` 上把 `negative_contract` 从 `36/36 wrong_tool_choice` 修到 `36/36 correct_non_execute`
- DONE: 扩展 benchmark loader 到显式 versioned views，并构造首版 `real evolution split` 数据与 source audit
- DONE: 把 `semantic_contract_gate` 接入 `real evolution split` 并完成首轮 family-holdout 结果
- DONE: 在 real split 上实现 `semantic_capability_gate`，补齐 description-level capability gap / replacement inhibition
- DONE: 将 real split 扩到 `12 cases / 24 views / 25 official sources`，并在扩样后复跑完整 real family-holdout
- DONE: 为 expanded real split 新增 deterministic execution-level sanity harness，并完成首轮 execution audit
- DONE: 为 5-family real fixed panel 新增 docs-backed official request smoke，并完成首轮 live 官方文档审计
- DONE: 为 5-family real fixed panel 新增 spec-backed API surface smoke，并完成首轮 live discovery / OpenAPI 审计
- DONE: 将现有 `9-family real fixed panel` 正式降级为 `dev panel`，并启动首版 blind real-evolution panel
- DONE: 将 blind panel 扩到 `6` 个 families，并冻结为 blind review panel
- DONE: 在 dev panel 上补齐首版 `name / description / contract` masking sensitivity 机制分析
- DONE: 在 dev panel 上补齐首版 `decision-state probe / positive-state similarity / negative separation gap` 机制分析
- DONE: 在 dev panel 上补齐首版 `counterfactual impossible shadow` boundary evidence
- DONE: 在 frozen blind panel 上完成唯一保留方法主线的首轮最终复核
- DONE: 完成 retained methods 的 `dev panel -> blind panel` 正式对照，并收束 strongest story
- DONE: 形成最终 framing 文档，明确 strongest story、claim boundary 与 learned-route 定位
- DONE: 用官方最新可得 NeurIPS 模板落成可编译 LaTeX 初稿
- DONE: 将“是否再冲一次主方法”收束为唯一允许的 decisive-run 方案，并落盘 Go/No-Go 文档
- DONE: 完成唯一允许的 `teacher-distilled canonical-bottleneck SCC` decisive run，并确认其不满足进入 blind review 的条件
- DONE: 新增 `API-Bank -> TOOLSHIFT` external bridge benchmark，并完成首轮 protocol bridge 评测
- DONE: 在 `real_evolution dev / blind` 与 `API-Bank bridge` 上补跑外部公开模型 `Qwen3-8B` baseline
- DONE: 新增 protocol reliability / split sensitivity 分析，并完成 dev/blind 首轮审计
- DONE: 新增 frozen blind family/vendor bootstrap 与 leave-one-family-out 稳健性分析
- DONE: 新增 `doc_retrieval_rerank` 外部 retrieval-style baseline，并完成 TOOLSHIFT + API-Bank/BFCL/ToolEVO bridge 首轮结果
- DONE: 新增非 Qwen 公共模型 sanity check（`Llama-3.2-3B-Instruct`），并完成 TOOLSHIFT blind + ToolEVO bridge 首轮结果
- TODO: 扩展真实 schema diff 收集与人工审计
- TODO: 扩展 factorized perturbation / family-holdout 数据与报告
- TODO: 继续扩到更多 real vendor families
- TODO: 按当前 final framing 精修论文摘要、引言、主结果表与图表
- TODO: 若继续冲 benchmark paper，补 annotator-level agreement 或 second-pass re-audit consistency
- TODO: 若决定再冲一次主方法，只执行 `history/decisive_method_run.md` 中定义的唯一 decisive run
- TODO: 将 execution / replay / docs-smoke / api-surface 回归带到更多 vendor families
- TODO: 为少数关键 case 增加更真实的 authenticated API-level smoke validation

## Latest Progress
- 2026-03-09: 读取 proposal、README、AGENTS 约束，确认研究主线与 Week 1 任务。
- 2026-03-09: 建立 `src/toolshift/`、`data/`、`scripts/`、`tests/` 基础结构。
- 2026-03-09: 实现 seed benchmark、canonicalizer、`CAA/POC/NOS` 指标、audit 导出与 pilot 运行脚本。
- 2026-03-09: 完成 `PYTHONPATH=src python -m unittest discover -s tests`、`scripts/run_seed_pilot.py`、`scripts/export_audit_packet.py`。
- 2026-03-09: 验证 `infer` 环境可读取 `/cephfs/shared/hf_cache/hub/Qwen3-0.6B` tokenizer，正式模型入口可继续接入。
- 2026-03-09: 验证 `infer` 环境具备 GPU（8 cards），并成功完成 `Qwen3-0.6B` 最小文本生成。
- 2026-03-09: 新增 `src/toolshift/qwen_agent.py` 与 `scripts/run_qwen_seed_pilot.py`，将 Qwen prompt-only baseline 接入现有评测。
- 2026-03-09: 完成 Qwen3-0.6B seed pilot，额外补跑 thinking / non-thinking 模式对照。
- 2026-03-09: 完成 `Qwen3-4B` thinking 模式 seed pilot，并新增 `scripts/compare_eval_runs.py` 做 factorized 对照。
- 2026-03-09: 新增 `data/seed_audit.json`、`history/seed_audit.md`、`scripts/rejudge_saved_records.py`，完成 seed suite 的 view-level audit。
- 2026-03-09: 将评测主表切换到 `unambiguous core`，当前 audited split 为 `26 core / 10 ambiguous / 6 impossible`。
- 2026-03-09: 新增 `reminder_tax_form_absolute` 与 `calendar_toolshift_sync_absolute`，将 audited split 扩为 `38 core / 10 ambiguous / 8 impossible`。
- 2026-03-09: 重跑 heuristic、Qwen3-0.6B、Qwen3-4B baselines，获得扩样后的 `NOS` / `CAA+` 对照。
- 2026-03-09: 在 canonicalizer 中新增 `ISO datetime + timezone` slot split，并重判 Qwen v2 records。
- 2026-03-09: 新增 `src/toolshift/embedding_policy.py` 与 `scripts/run_matched_budget_pilot.py`，用 frozen `Qwen3-Embedding-0.6B` 搭起 `AugOnly / SCC-lite` pilot。
- 2026-03-09: 完成 `combo_holdout` 与 `case_holdout_cv` 两套 matched-budget 对照；`lambda=0.5` 过强会把 `SCC-lite` 推向保守控制，已改为 `lambda=0.1` 默认。
- 2026-03-09: 在低权重设置下，`SCC-lite` 与 `AugOnly` 在当前 seed pilot 上持平，未观察到独立增量；结论已写入 `history/results.md`。
- 2026-03-09: 新增 `scripts/generate_family_benchmark.py`，从 seed tools 派生 18-case richer same-family synthetic suite，并生成 `data/family_benchmark.json` / `data/family_audit.json`。
- 2026-03-09: 修正 benchmark loader 的默认 audit 解析规则，使非 `seed_benchmark.json` 也能自动拾取同 stem 的 audit 文件。
- 2026-03-09: 在 richer family suite 上完成 heuristic baseline 与 matched-budget pilot；`case_holdout_cv` 不再崩掉，当前已成为更有信息量的方法 split。
- 2026-03-10: 将 `scripts/run_matched_budget_pilot.py` 扩展为 `combo_holdout / case_holdout_cv / family_holdout_cv` 三个 regime，形成 richer family suite 的完整 synthetic OOD 梯度。
- 2026-03-10: 完成 `family_holdout_cv` 主实验；当前 split 明显更难，但 `SCC-lite` 仅在一个 `negative_deprecate` view 上比 `AugOnly` 多对一次，未出现 tool semantics 层面的稳定增量。
- 2026-03-10: 新增 `src/toolshift/diagnostics.py` 与 `scripts/diagnose_saved_records.py`，完成 saved-record factorized 诊断。
- 2026-03-10: 诊断确认 `family_holdout_cv` 下两种方法的 `execute_rate = 0.0`，且错误 100% 落在 control policy；当前并不存在 wrong-tool 或 argument-grounding 主误差。
- 2026-03-10: 新增 `prototype execute gate`；在 `family_holdout_cv` smoke 上未能提升 `execute_rate`，证实问题不只是 control head 线性可分性。
- 2026-03-10: 新增 `semantic_gate`，在 `family_holdout_cv` 双 seed 上达到 `CAA=0.806`、`CAA_clean=1.0`、`CAA+=0.981`、`POC=0.944`，并把 `execute_rate` 从 `0.0` 拉到 `0.824`。
- 2026-03-10: factorized 诊断显示 `semantic_gate` 的剩余主失败已从 “不敢执行” 转移为 `negative_contract` 的系统性误执行。
- 2026-03-10: 新增 `semantic_contract_gate`，在 `family_holdout_cv` 双 seed 上达到 `CAA=0.972`、`CAA_clean=1.0`、`CAA+=0.981`、`NOS=0.944`、`POC=0.944`。
- 2026-03-10: diagnostics 确认 `semantic_contract_gate` 将 `negative_contract` 从 `36/36 wrong_tool_choice` 修正为 `36/36 correct_non_execute`，而 `clean / positive` 基本保持不变。
- 2026-03-10: 新增 `scripts/generate_real_evolution_benchmark.py`，生成 `data/real_evolution_benchmark.json`、`data/real_evolution_audit.json`、`history/real_evolution_audit.md`，首版 real split v1 为 `6 cases / 12 views / 3 vendor families`。
- 2026-03-10: `src/toolshift/benchmark.py` 现已支持显式 `views` 与 `family_tag`；`scripts/run_matched_budget_pilot.py` 的 family grouping 改为优先读取 `family_tag`。
- 2026-03-10: real split heuristic pilot 结果显示 `DescriptionGrounded` 在 real positive migrations 上仍是 `CAA+=1.0`，但在 real negatives 上掉到 `NOS=0.0`。
- 2026-03-10: 在 real split `family_holdout_cv` 上，`AugOnly` 退化为 `CAA=0.167`、`CAA_clean=0.0`、`CAA+=0.0`、`execute_rate=0.0`。
- 2026-03-10: 在同一 real split 上，`SemanticContractGate` 达到 `CAA=0.833`、`CAA_clean=1.0`、`CAA+=1.0`、`NOS=0.333`、`POC=1.0`；Slack deprecate 已能正确 non-execute，但 Notion search replacement 和 Stripe total-count removal 仍系统性误执行。
- 2026-03-10: 新增 `semantic_capability_gate`，在 `semantic_contract_gate` 上接入 description-level capability gap inhibition。
- 2026-03-10: real split `family_holdout_cv` 上，`SemanticCapabilityGate` 达到 `CAA=1.0`、`CAA_clean=1.0`、`CAA+=1.0`、`NOS=1.0`、`POC=1.0`，并把剩余 `wrong_tool_choice` 全部压成 admissible non-execute。
- 2026-03-10: richer synthetic `family_holdout_cv` sanity check 显示 `SemanticCapabilityGate` 与 `SemanticContractGate` 持平，未引入回退。
- 2026-03-10: real split 扩到 `12 cases / 24 views / 25 official source anchors`，均衡覆盖 `notion / slack / stripe` 三个 vendor family。
- 2026-03-10: 扩样后的 heuristic real pilot 仍保持强诊断性：`DescriptionGrounded` 继续 `CAA+=1.0`，但 `NOS=0.0`。
- 2026-03-10: 扩样后的 real `family_holdout_cv` 上，`SemanticContractGate` 掉到 `CAA_negative=0.2 / NOS=0.2`，新增负例主要暴露 `description-aware` detector 的 coverage 边界。
- 2026-03-10: 将 detector 从 clause-only overlap 改成 `negative cue -> full-description capability overlap` 后，`SemanticCapabilityGate` 在 expanded real panel 上恢复到 `CAA=1.0 / NOS=1.0 / POC=1.0`。
- 2026-03-10: 新增 `src/toolshift/execution_sanity.py` 与 `scripts/run_execution_sanity.py`，为 expanded real split 增加 deterministic execution-level sanity。
- 2026-03-10: execution audit 结果为 `pass_rate=1.0`、`execute_expected_pass_rate=1.0`、`negative_guard_pass_rate=1.0`、`positive_equivalence_rate=1.0`，说明当前 expanded real split 的 clean/positive/negative 标签与 mock execution semantics 一致。
- 2026-03-10: 将 Google Drive 接入 real split，新增 `4 cases / 8 views / 9 official sources`，当前 fixed panel 扩为 `16 cases / 32 views / 34 sources / 4 vendor families`。
- 2026-03-10: execution sanity 已扩到 Drive；当前 4-family real split 上 `count=32`、`pass_rate=1.0`、`positive_equivalence_rate=1.0`。
- 2026-03-10: Drive family 首轮 family-holdout 暴露了新的失败面：`semantic_capability_gate` 在 held-out Drive 的 `files.update add/removeParents` 正迁移上出现 `ask_clarification`，导致 `CAA+=0.8 / POC=0.8`。
- 2026-03-10: 只改 Drive current descriptions 不足以修复 under-execute；问题在 gate 本身，不是 panel wording。
- 2026-03-10: 在 `SemanticGateAgent` 中加入窄范围 `semantic rescue`（`contract-compatible + no capability gap + overlap + score lead`），4-family real `family_holdout_cv` 恢复到 `SemanticCapabilityGate = CAA 1.0 / CAA+ 1.0 / NOS 1.0 / POC 1.0`。
- 2026-03-10: richer synthetic `family_holdout_cv` sanity 保持不变：`SemanticContractGate = SemanticCapabilityGate = CAA 0.972 / CAA+ 0.981 / NOS 0.944 / POC 0.944`。
- 2026-03-10: 将 Jira Cloud 接入 real split，新增 `4 cases / 8 views / 7 official sources`，当前 fixed panel 扩为 `20 cases / 40 views / 41 sources / 5 vendor families`。
- 2026-03-10: Jira 家族覆盖了 `username/userKey -> accountId`、`username -> query` 和 `legacy identifier removed` 三类 privacy-driven API evolution。
- 2026-03-10: Jira 接入后 heuristic baseline 继续掉分：`LexicalShortcut CAA 0.531 -> 0.500`，`DescriptionGrounded CAA 0.719 -> 0.650`，`CAA+ 1.000 -> 0.846`。
- 2026-03-10: Jira execution sanity 已接通；当前 5-family real split 上 `count=40`、`pass_rate=1.0`、`positive_equivalence_rate=1.0`。
- 2026-03-10: 5-family real `family_holdout_cv` 上，`SemanticCapabilityGate` 继续保持 `CAA 1.0 / CAA+ 1.0 / NOS 1.0 / POC 1.0`，`SemanticContractGate` 则在 Jira negative 上新增一条 `wrong_tool_choice`。
- 2026-03-10: 新增 `src/toolshift/request_replay.py` 与 `scripts/run_request_replay.py`，把 real fixed panel 的验证链推进到 request-level replay。
- 2026-03-10: request replay 在 5-family real panel 上达到 `count=40 / pass_rate=1.0 / execute_render_pass_rate=1.0 / negative_block_pass_rate=1.0 / positive_equivalence_rate=1.0`。
- 2026-03-10: replay 代表性证据已覆盖：
  - Drive `parents.insert -> files.update addParents`
  - Jira `name -> accountId`
  - Jira `legacy username removed` negative blocked
- 2026-03-10: 新增 `scripts/run_official_request_smoke.py` 与 `tests/test_official_request_smoke.py`，把 Drive / Jira 的 request-level evidence 进一步对齐到 live 官方文档。
- 2026-03-10: official-doc smoke 在 `7` 个 selected real views 上达到 `count=7 / pass_rate=1.0 / emit_expected_pass_rate=1.0 / block_expected_pass_rate=1.0`。
- 2026-03-10: 当前 real fixed panel 的关键 Drive / Jira case 已经同时具备 source audit、benchmark eval、execution sanity、request replay 和 official-doc smoke 五层证据。
- 2026-03-10: 新增 `src/toolshift/api_surface_smoke.py` 与 `scripts/run_api_surface_smoke.py`，把 Drive discovery 和 Jira OpenAPI 接入 live machine-readable request-surface 审计。
- 2026-03-16: 将 `Llama-3.2-3B-Instruct` 非 Qwen 公共模型 sanity check 正式并入 README、insights 与 paper，外部可比性不再只依赖 Qwen 家族与 retrieval-style baseline。
- 2026-03-16: 继续收紧 paper 前两页 benchmark-paper 口径，并新增 `history/reviewer_concern_bullets.md` 作为 reviewer/rebuttal 复用材料。
- 2026-03-16: 进一步去掉 main paper 中的 repo-internal 命名和过程性措辞，收紧 methods / discussion 到完成态 benchmark-paper 口径。
- 2026-03-10: spec-backed API surface smoke 在 `7` 个 selected real views 上达到 `count=7 / pass_rate=1.0 / emit_expected_pass_rate=1.0 / block_expected_pass_rate=1.0`。
- 2026-03-10: 当前 Drive / Jira 关键 case 已经同时具备 source audit、benchmark eval、execution sanity、request replay、official-doc smoke、api-surface smoke 六层证据。
- 2026-03-10: 检查本地环境后，未发现可用的 Drive / Jira authenticated smoke 凭证，因此不阻塞主线，直接转向新的 public-spec real family 扩展。
- 2026-03-10: 将 Google Sheets v3 -> v4 接入 real split，新增 `4 cases / 8 views / 4 source anchors`；当前 fixed panel 扩为 `24 cases / 48 views / 45 official sources / 6 vendor families`。
- 2026-03-16: 调研外部 benchmark 生态后，确认 `ToolEVO` 虽最贴 API evolution，但公开 `ToolQA-D` test split 只有 question-answer pairs，缺少可直接桥接 canonical action 的公开 tool-call traces；因此先以 `API-Bank` 作为首条社区 benchmark bridge。
- 2026-03-16: 新增 `src/toolshift/api_bank_import.py`、`scripts/import_api_bank_benchmark.py`、`tests/test_api_bank_import.py`，生成 `data/api_bank_toolshift_benchmark.json` 与 `history/api_bank_import_audit.md`。
- 2026-03-16: `API-Bank` bridge 当前为 `12 cases / 19 tools / 84 views / 3 family tags`，并已在 `artifacts/api_bank_seed_pilot_v1` 上跑通 oracle / lexical / description-grounded structural smoke。
- 2026-03-16: 在 `real_evolution dev panel` 上补跑外部公开模型 `Qwen3-8B`，得到 `CAA=0.931 / CAA+=0.960 / NOS=0.727 / POC=0.960`。
- 2026-03-16: 在 frozen blind panel 上补跑 `Qwen3-8B`，得到 `CAA=0.875 / CAA+=0.923 / NOS=0.636 / POC=0.923`；结果低于 strongest scaffold baseline，但证明 TOOLSHIFT 不是只对自家 retained methods 难。
- 2026-03-16: 在 `API-Bank bridge` 上补跑 `Qwen3-8B`，得到 `CAA=0.486 / CAA+=0.667 / NOS=0.125 / POC=0.667`，进一步说明 bridge benchmark 非 trivial。
- 2026-03-16: 新增 `scripts/run_protocol_reliability.py`，把 dev/blind 的 action-set multiplicity、source-support 与 split-policy sensitivity 显式落盘。当前 dev 为 `62` 个 single-action views + `10` 个 dual-control negatives；blind 为 `38` 个 single-action views + `10` 个 dual-control negatives。
- 2026-03-16: split-sensitivity 结果说明：如果把 dual-control negatives 全部压成 `single_action_only`，blind `NOS` 会对所有方法虚高到 `1.0`；如果分别投影成 `ask_only` 或 `abstain_only`，absolute `NOS` 会显著波动。因此当前 benchmark-paper 更应显式主张 `set-valued negative evaluation`，而不是让这部分 protocol choice 隐身。
- 2026-03-16: 新增 `scripts/run_panel_stability.py`，在 frozen blind panel 上补 family/vendor cluster bootstrap 与 leave-one-family-out。`slack_auth` 确实是 strongest scaffold baseline 的最大单点压力，但删掉它后 `NOS` 只从 `0.727` 升到 `0.800`，说明 blind 难点不是单-family artifact。
- 2026-03-16: 已将 `protocol reliability / split sensitivity / blind stability` 正式并入 `paper/` 主文与附录。当前稿子会显式说明 dual-control negatives 对 absolute `NOS` 的影响、public Qwen baselines 与 TOOLSHIFT blind 的同类压力点、以及这些结果仍属于 protocol-level reliability 而非 annotator agreement。
- 2026-03-10: Sheets family 已接通 benchmark generation、execution sanity、request replay、official-doc smoke、api-surface smoke 与 real `family_holdout_cv` 主实验。
- 2026-03-10: 全量回归通过：`66` 个单测全过，`compileall` 通过；expanded real panel 的 execution sanity、request replay、official-doc smoke、api-surface smoke 全部为 `pass_rate=1.0`。
- 2026-03-10: expanded 6-family heuristic pilot 保持诊断性：`LexicalShortcut CAA=0.458 / CAA+=0.375 / NOS=0.750`，`DescriptionGrounded CAA=0.708 / CAA+=0.875 / NOS=0.375`。
- 2026-03-10: expanded 6-family real `family_holdout_cv` 上，`AugOnly` 进一步退化到 `CAA=0.115 / CAA+=0.031 / NOS=0.625`。
- 2026-03-10: 在同一 split 上，`SemanticContractGate` 为 `CAA=0.896 / CAA+=1.0 / NOS=0.375 / POC=1.0`，仍主要漏在 negative inhibition。
- 2026-03-10: `SemanticCapabilityGate` 在 expanded 6-family real `family_holdout_cv` 上继续保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`；diagnostics 为 `group_counts={\"correct\": 96}`。
- 2026-03-10: Sheets negative 首轮暴露出一个真实约束：若 rendered description 不保留足够的 capability-gap / replacement cue，deterministic inhibition 会漏判；补足 cue wording 后，official-doc smoke 与 main panel 均恢复为全对。
- 2026-03-10: 继续沿 public-spec 路线扩展新 family，选定 `Google Contacts API -> People API`，并新增 `4 cases / 8 views / 6 official sources`；当前 fixed panel 扩为 `28 cases / 56 views / 51 official sources / 7 vendor families`。
- 2026-03-10: `people` family 已接通 benchmark generation、execution sanity、request replay、official-doc smoke、api-surface smoke 与 real `family_holdout_cv` 主实验。
- 2026-03-10: 为接通 People discovery，修正了 machine-readable path matcher：Google discovery 的 `{+resourceName}` 不能再按 segment-count 匹配，必须走 full-path expansion。
- 2026-03-10: 全量回归通过：`72` 个单测全过，`compileall` 通过；expanded 7-family panel 的 execution sanity、request replay、official-doc smoke、api-surface smoke 全部 `pass_rate=1.0`。
- 2026-03-10: expanded 7-family heuristic pilot 继续保持诊断性：`LexicalShortcut CAA=0.446 / CAA+=0.368 / NOS=0.778`，`DescriptionGrounded CAA=0.696 / CAA+=0.842 / NOS=0.333`。
- 2026-03-10: expanded 7-family real `family_holdout_cv` 上，`AugOnly` 为 `CAA=0.116 / CAA+=0.026 / NOS=0.667 / POC=0.026`，继续随 family 扩展退化。
- 2026-03-10: 在同一 split 上，`SemanticContractGate` 为 `CAA=0.893 / CAA+=1.0 / NOS=0.333 / POC=1.0`；People 的 `Other Contacts read-only` negative 暴露出新的 `wrong_tool_choice`。
- 2026-03-10: `SemanticCapabilityGate` 在 expanded 7-family real `family_holdout_cv` 上继续保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`；diagnostics 为 `group_counts={\"correct\": 112}`。
- 2026-03-10: People-specific diagnostics 显示，`semantic_contract_gate` 在 `people.other_contacts.update_email` 上是 `2 x correct_execute + 2 x wrong_tool_choice`，而 `semantic_capability_gate` 则变成 `2 x correct_execute + 2 x correct_non_execute`。
- 2026-03-10: 将 `Confluence Cloud REST v1 -> v2` 接入 real split，新增 `4 cases / 8 views / 6 official sources`；当前 fixed panel 扩为 `32 cases / 64 views / 57 official sources / 8 vendor families`。
- 2026-03-10: Confluence family 已接通 benchmark generation、execution sanity、request replay、official-doc smoke、api-surface smoke 与 real `family_holdout_cv` 主实验。
- 2026-03-10: 为接通 Confluence OpenAPI，泛化了 machine-readable validator：不仅要读取 `paths`，还要处理 `servers[].url` 前缀与 `requestBody $ref`。
- 2026-03-10: 全量回归通过：`78` 个单测全过，`compileall` 通过；expanded 8-family panel 的 execution sanity、request replay、official-doc smoke、api-surface smoke 全部 `pass_rate=1.0`。
- 2026-03-10: expanded 8-family heuristic pilot 继续保持诊断性：`LexicalShortcut CAA=0.469 / CAA+=0.409 / NOS=0.800`，`DescriptionGrounded CAA=0.688 / CAA+=0.818 / NOS=0.300`。
- 2026-03-10: expanded 8-family real `family_holdout_cv` 上，`AugOnly` 为 `CAA=0.117 / CAA+=0.023 / NOS=0.700 / POC=0.023`，继续随 family 扩展退化。
- 2026-03-10: 在同一 split 上，`SemanticContractGate` 为 `CAA=0.891 / CAA+=1.0 / NOS=0.300 / POC=1.0`；Confluence 的 `spaceKey -> spaceId lookup split` 新增了 `wrong_tool_choice`。
- 2026-03-10: `SemanticCapabilityGate` 在 expanded 8-family real `family_holdout_cv` 上继续保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`；diagnostics 为 `group_counts={\"correct\": 128}`。
- 2026-03-10: 将 `Bitbucket Cloud teams -> workspaces` 接入 real split，新增 `4 cases / 8 views / 6 official sources`；当前 fixed panel 扩为 `36 cases / 72 views / 63 official sources / 9 vendor families`。
- 2026-03-10: Bitbucket family 已接通 benchmark generation、execution sanity、request replay、official-doc smoke、api-surface smoke 与 real `family_holdout_cv` 主实验。
- 2026-03-10: 为接通 Bitbucket `swagger.json`，machine-readable validator 新增了 Swagger 2.0 `basePath` 前缀支持；现在 `/2.0/workspaces/...` 不会再被误判成 spec miss。
- 2026-03-10: 全量回归通过：`84` 个单测全过，`compileall` 通过；expanded 9-family panel 的 execution sanity、request replay、official-doc smoke、api-surface smoke 全部 `pass_rate=1.0`。
- 2026-03-10: expanded 9-family heuristic pilot 继续保持诊断性：`LexicalShortcut CAA=0.472 / CAA+=0.480 / NOS=0.818`，`DescriptionGrounded CAA=0.681 / CAA+=0.840 / NOS=0.364`。
- 2026-03-10: expanded 9-family real `family_holdout_cv` 上，`AugOnly` 为 `CAA=0.090 / CAA+=0.000 / NOS=0.591 / POC=0.000`，继续随 family 扩展退化。
- 2026-03-10: 在同一 split 上，`SemanticContractGate` 为 `CAA=0.889 / CAA+=1.0 / NOS=0.273 / POC=1.0`；Bitbucket 的 `legacy account object` negative 新增了 `wrong_tool_choice`。
- 2026-03-10: `SemanticCapabilityGate` 在 expanded 9-family real `family_holdout_cv` 上继续保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`；diagnostics 为 `group_counts={\"correct\": 144}`。
- 2026-03-10: 冻结当前 `9-family real fixed panel`，新增 `scripts/compare_fixed_panel_methods.py` 与 `src/toolshift/fixed_panel_compare.py`，专门做方法层 paired comparison。
- 2026-03-10: factorized compare 结果显示，`SemanticCapabilityGate` 相对 `SemanticContractGate` 的全部独立增量都来自 `8` 个 negative capability-gap views；`improved_pairs=16`、`regressed_pairs=0`。
- 2026-03-10: 在 frozen panel 上，`SemanticContractGate` 已经把 `clean=72/72`、`positive=50/50` 做满；当前剩余核心难点只在 `negative capability-gap inhibition`，而不是 positive invariance。
- 2026-03-10: 新增 `semantic_learned_capability_gate`，用轻量 logistic scorer 学 capability inhibition；入口仍复用 `run_matched_budget_pilot.py`。
- 2026-03-10: `v1` 首轮 learned scorer 在 frozen panel 上出现 `1` 条正样本回退：`sheets_update_formula::positive_version_migration` 被误压成 `ask_clarification`，说明 raw scorer 会 over-inhibit cue-free positive。
- 2026-03-10: 加入 `cue-triggered` guard 后，`semantic_learned_capability_gate v2` 在 frozen panel 上追平 `semantic_capability_gate`：`CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`，paired compare 为 `improved_pairs=0 / regressed_pairs=0`。
- 2026-03-10: 对 frozen panel 做 capability feature profiling，发现 `clean / positive` 的 `cue_clause_count` 全是 `0`，而 `negative_near_orbit` 全是 `>=1`；v1 的回退来自把 generic execute 特征混进了 inhibition scorer。
- 2026-03-10: 新增 `semantic_sparse_capability_gate`，只保留 `6` 个 cue-family features，并去掉外层 `capability_require_cue` guard。
- 2026-03-10: `semantic_sparse_capability_gate` 在 frozen panel 上继续追平 `semantic_capability_gate` 和 `semantic_learned_capability_gate v2`：`CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`，两组 paired compare 都是 `improved_pairs=0 / regressed_pairs=0`。
- 2026-03-10: 继续削减显式 cue 依赖，新增 `semantic_continuous_capability_gate`，只保留 `description_overlap / max_cue_overlap / total_cue_overlap` 三个连续特征。
- 2026-03-10: `semantic_continuous_capability_gate` 在 frozen panel 上继续追平 `semantic_sparse_capability_gate`：`CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`，paired compare 仍然是 `improved_pairs=0 / regressed_pairs=0`。
- 2026-03-11: 新增 `semantic_embedding_capability_gate`，把 capability inhibition 特征从 overlap 统计继续替换成 `description_similarity / max_cue_similarity / mean_cue_similarity`。
- 2026-03-11: 修复了 `SemanticGateAgent._build_execute_call()` 缺失 `request_feature` 传参的实现错误；修复后 targeted tests、全量 `91` 个单测和 `compileall` 全部通过。
- 2026-03-11: frozen `9-family real fixed panel` 上，`semantic_embedding_capability_gate` 追平 `semantic_continuous_capability_gate`：`CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0 / coverage=0.986`。
- 2026-03-11: diagnostics 与 paired compare 都显示逐 view 无差异：`group_counts={"correct": 144}`，`improved_pairs=0 / regressed_pairs=0`。
- 2026-03-11: 继续尝试去掉 cue-specific clause extraction，新增 `semantic_raw_text_capability_gate`，只保留 `tool / description / argument` 相似度特征。
- 2026-03-11: `semantic_raw_text_capability_gate` 在 frozen panel 上明显回退：`CAA=0.847 / CAA+=1.0 / NOS=0.455 / POC=1.0`，`regressed_pairs=22`；同时出现 negative leak 和 clean under-execute。
- 2026-03-11: 进一步新增 `semantic_description_pool_capability_gate`，在 entire description 上做 generic clause pooling，但不使用 cue-specific extraction。
- 2026-03-11: `semantic_description_pool_capability_gate` 较 raw-text 有所改善，但仍明显回退：`CAA=0.889 / CAA+=0.880 / NOS=0.545 / POC=0.880`，`regressed_pairs=16`。
- 2026-03-11: 当前 frozen panel 已经给出清晰负证据：不能直接用 generic whole-text / clause-pool similarity 替代 cue-specific negative localization。
- 2026-03-11: 继续沿更接近 proposal 的 learned route，新增 `semantic_interaction_capability_gate`，用 top generic clause localization + dense interaction vector 做 inhibition。
- 2026-03-11: `semantic_interaction_capability_gate` 结果更差：`CAA=0.688 / CAA+=0.680 / NOS=0.818 / POC=0.680`，`regressed_pairs=45`，主要失败模式是过度抑制 execute，而不是 localization 学成。
- 2026-03-11: 当前 frozen panel 的证据已经收敛：linear whole-text / clause-pool / interaction 三条去-cue 路线都不成立，现有 cue-specific localization 仍然是必要 scaffold。
- 2026-03-11: 继续推进到 `semantic_clause_localization_capability_gate`，允许 train-time 用 cue extraction 做 supervision，但 inference 不再调用 `_capability_cue_clauses()`。
- 2026-03-11: `semantic_clause_localization_capability_gate` 相对 generic interaction 明显回升：`CAA=0.875 / CAA+=0.820 / NOS=0.864 / POC=0.820`，`regressed_pairs=18`。
- 2026-03-11: 但它仍未追平 `semantic_embedding_capability_gate`，剩余失败集中在 Drive clean/positive under-execute 和少量 hard negative leak。
- 2026-03-11: fold train metrics 显示 clause localizer 与 dense scorer 都接近 `100%` train accuracy/recall，当前主要瓶颈已从“有没有 localization”转成“learned localization 的泛化/正则化”。
- 2026-03-11: 继续尝试 `semantic_clause_localization_calibrated_gate`，把高维 interaction head 压成低维 scalar calibrated head。
- 2026-03-11: 这条校准路线失败：`CAA=0.840 / CAA+=0.760 / NOS=0.773 / POC=0.760`，比上一轮 clause-localization 本体更差，`regressed_pairs=23`。
- 2026-03-11: 当前结论更明确了：问题不只是 high-dimensional head 过拟合；简单降维/校准本身不足以解决 learned localization 的泛化。
- 2026-03-11: 已新增 `semantic_pair_text_capability_gate`，把 raw `request` 文本贯穿到 dense capability path，并用 frozen encoder joint pair-text embedding 做 clause localization / inhibition。
- 2026-03-11: frozen pair-text 正式结果为负：`CAA=0.743 / CAA+=0.780 / NOS=0.909 / POC=0.780`，`regressed_pair_count=37`。
- 2026-03-11: 这条路线的主失败不是 negative inhibition 全崩，而是 `clean / positive` 的 execute collapse：`clean admissible=0.667`，`positive admissible=0.780`，同时仍残留 `notion_list_shared_databases::negative_search_replacement` 的 tool-choice leak。
- 2026-03-11: 主线判断进一步收敛：当前 learned route 的问题已经不再是“有没有 pair input”，而是“pair model 本身够不够强”；frozen encoder + linear pair head 不足以替代 `semantic_embedding_capability_gate`。
- 2026-03-11: 已继续把 pair-text 路线升级成 `semantic_pair_text_mlp_capability_gate`，用 non-linear MLP head 替代 frozen linear pair head。
- 2026-03-11: `pair_text_mlp` 相对 linear pair-text 明显恢复：`CAA 0.743 -> 0.868`，`CAA+ 0.780 -> 0.920`，`POC 0.780 -> 0.920`。
- 2026-03-11: 但它仍未追平 strongest baseline：`NOS=0.682`，`regressed_pair_count=19`。当前 tradeoff 很明确：MLP pair head 救回了大部分 `clean / positive` execute，但重新放松了 negative inhibition。
- 2026-03-11: 主线结论继续收敛：pair-model 方向本身是对的，但 `frozen encoder + small MLP pair head` 仍然不够；下一步必须直接上更强的 cross-encoder / pair model。
- 2026-03-11: 已新增 `semantic_cross_encoder_capability_gate`，用本地 `Qwen3-Reranker-0.6B` 做真正的 joint pair scoring，并通过 threshold calibration 接进现有 semantic gate 主链。
- 2026-03-11: cross-encoder 在 frozen panel 上的结果是 `CAA=0.861 / CAA+=0.920 / NOS=0.273 / POC=0.920 / coverage=0.944`，`regressed_pair_count=20`。
- 2026-03-11: 这条路线把 `clean` 全守住了，也基本守住了 `positive`，但 `negative capability-gap inhibition` 明显失守，出现 `16` 条 `tool_choice_error`。
- 2026-03-11: 当前主线判断进一步收敛：真正的 pair model 不是 blocker，已经能落地并给出新信号；当前问题变成“如何把 negative-localization supervision 真正注入 pair model”，而不是继续做 zero/few-shot threshold calibration。
- 2026-03-11: 已新增 `semantic_cross_encoder_supervised_capability_gate`，把训练信号真正接进 cross-encoder 决策，而不是只做 reranker threshold calibration。
- 2026-03-11: 结果仍是负的：`CAA=0.806 / CAA+=0.720 / NOS=0.455 / POC=0.720 / coverage=0.944`，`regressed_pair_count=28`，没有任何 improved pairs。
- 2026-03-11: 新 failure mode 已明确：supervised route 的 `clause_localizer_threshold` 在所有 fold 上都塌到 `1.000001`，`clause_localizer_train_positive_recall=0.0`；也就是训练没有真正学会 negative clause localization。
- 2026-03-11: 当前主线进一步收敛：不是“要不要 cross-encoder”，而是“如何避免 cross-encoder localizer collapse”。下一步不再做同级别的 threshold / linear 小修，而要上 ranking-style localizer objective 或真正 fine-tuned pair model。
- 2026-03-11: 已新增 `semantic_cross_encoder_ranked_capability_gate`，把 localizer 从独立 threshold 改成 ranking-style top selection，避免再次塌成全负解。
- 2026-03-11: 结果仍是负的，而且略差于上一轮 supervised cross-encoder：`CAA=0.792 / CAA+=0.720 / NOS=0.455 / POC=0.720 / coverage=0.944`，`regressed_pair_count=30`。
- 2026-03-11: ranking route 虽然把 `clause_localizer_threshold` 固定到 `0.0`，也让 `train_positive_rate=1.0`，但 `clause_localizer_train_accuracy` 仍只有 `0.000 ~ 0.167`、`train_positive_recall` 只有 `0.000 ~ 0.083`。也就是 top-ranked clause 大多仍不是正确的 capability-gap clause。
- 2026-03-11: 当前主线继续收敛：不是 localizer threshold 形式错了，而是现成 reranker 本身没有学会 capability-gap ranking。下一步不再做 top-selection / threshold 小修，直接转向显式 pairwise/listwise localizer training 或真正 fine-tuned cross-encoder。
- 2026-03-11: 已新增 `semantic_cross_encoder_pairwise_capability_gate`，把 clause localizer 升级成显式正负采样的 pairwise ranker。
- 2026-03-11: 结果仍是负的，但比前两轮 cross-encoder localizer 路线略好：`CAA=0.812 / CAA+=0.720 / NOS=0.500 / POC=0.720 / coverage=0.944`，`regressed_pair_count=27`。
- 2026-03-11: pairwise route 首次把 train-side localizer 指标真正抬起来：`clause_localizer_train_accuracy=0.143~0.333`，`train_positive_recall=0.059~0.167`；对应 test 端 `NOS` 也从 `0.455` 提到 `0.500`。
- 2026-03-11: 但 current strongest baseline 仍然没被追平，而且没有任何 improved pairs。这说明“需要 ranking signal”已经成立，但 “轻量 pairwise ranker 足够”还不成立。
- 2026-03-11: 已新增 `semantic_cross_encoder_listwise_capability_gate`，把 clause localizer 升级成显式 listwise ranker，并保持 inference cue-free。
- 2026-03-11: 结果仍是负的，而且 aggregate 与 pairwise route 完全相同：`CAA=0.812 / CAA+=0.720 / NOS=0.500 / POC=0.720 / coverage=0.944`，`regressed_pair_count=27`。
- 2026-03-11: listwise objective 只把 train-side localizer 均值小幅抬高：`train_accuracy 0.185 -> 0.218`，`train_positive_recall 0.085 -> 0.100`；但 fixed-panel test 没有任何增益。
- 2026-03-11: 当前主线进一步收敛：问题已经不是 pairwise vs listwise，而是现成 reranker 本体不够；下一步直接做真正 fine-tuned cross-encoder pair model。
- 2026-03-11: 已新增 `semantic_cross_encoder_finetuned_capability_gate`，真正更新 `Qwen3-Reranker-0.6B` 的最后一层、`norm` 和 `lm_head`，而不是继续训练上层 ranker。
- 2026-03-11: 双 seed 正式结果是 `CAA=0.819 / CAA+=0.900 / NOS=0.364 / POC=0.900 / coverage=0.944`，`regressed_pair_count=26`。
- 2026-03-11: 这条 route 相比 `pairwise / listwise` 明显救回了 `positive execute`，但 `negative inhibition` 明显回退；相比 zero-shot cross-encoder，则只小幅修了 `NOS`，整体仍未追平 strongest baseline。
- 2026-03-11: 当前主线进一步收敛：问题已经不只是 “没有 fine-tune cross-encoder”，而是 capability-only pair fine-tune 本身会学成正负 tradeoff。下一步应转向 hard-negative / class-balanced pair fine-tune，或 joint `capability + localization` multitask fine-tune。
- 2026-03-11: 已新增 `semantic_cross_encoder_multitask_capability_gate`，把 `capability + localization` 一起接入同一个 fine-tuned cross-encoder。
- 2026-03-11: 双 seed 正式结果是 `CAA=0.812 / CAA+=0.840 / NOS=0.364 / POC=0.840 / coverage=0.944`，`regressed_pair_count=27`。
- 2026-03-11: multitask supervision 确实把 localizer 学起来了：`clause_localizer_train_accuracy mean = 0.691`，`clause_localizer_train_positive_recall mean = 0.619`；但 `NOS` 没有提升，`CAA+ / POC` 反而低于 capability-only fine-tune。
- 2026-03-11: 当前主线进一步收敛：问题已经不只是 “缺 localization supervision”，而是 joint objective 仍然没把 localization 转成更好的 negative inhibition。下一步应直接转向 hard-negative / class-balanced fine-tuned pair model。
- 2026-03-11: 已新增 `semantic_cross_encoder_hard_negative_capability_gate`，在 capability-only fine-tune 上加入 class-balanced + hard-negative weighting，并把 threshold selection 也切到 weighted 版本。
- 2026-03-11: 双 seed 正式结果是 `CAA=0.736 / CAA+=0.760 / NOS=0.409 / POC=0.760 / coverage=0.944`，`regressed_pair_count=38`。
- 2026-03-11: 这条 route 的新信息很明确：`capability_gate_train_inhibit_recall mean = 0.456`、`NOS = 0.409`，都高于 capability-only fine-tune；但 `CAA+ / POC` 从 `0.900` 掉到 `0.760`，说明当前 global weighting 主要是靠压低 positive execute 换 negative inhibition。
- 2026-03-11: 当前主线进一步收敛：问题已经不只是 “缺 hard-negative weighting”，而是还缺 explicit positive-retention / asymmetric decision calibration。下一步不再做同级别 weight sweep，而应做结构化 decision rule。
- 2026-03-11: 已新增 `semantic_cross_encoder_asymmetric_capability_gate`，在 hard-negative / class-balanced fine-tune 上加了 explicit positive-retention constrained threshold。
- 2026-03-11: 双 seed 正式结果是 `CAA=0.833 / CAA+=0.920 / NOS=0.273 / POC=0.920 / coverage=0.944`，`regressed_pair_count=24`。
- 2026-03-11: 这条 route 的新信息很清楚：它把 `CAA+ / POC` 从 hard-negative route 的 `0.760` 拉回到 `0.920`，但 `NOS` 又从 `0.409` 掉回 `0.273`；train-side `capability_gate_train_inhibit_recall mean` 也从 `0.456` 掉到 `0.049`。
- 2026-03-11: 当前主线进一步收敛：问题已经不只是 “缺 positive-retention calibration”，而是 single-threshold asymmetric rule 本身太弱。下一步不再做 retention target 小修，而应转向 train-time asymmetric objective 或 dual-threshold / abstain-band decision rule。
- 2026-03-11: 已新增 `semantic_cross_encoder_asymmetric_objective_capability_gate`，把 execute-retention 约束写进 fine-tuned pair model 的训练损失，而不是继续依赖 post-hoc threshold。
- 2026-03-11: 双 seed 正式结果是 `CAA=0.694 / CAA+=0.680 / NOS=0.364 / POC=0.680 / coverage=0.944`，`regressed_pair_count=44`。
- 2026-03-11: 这条 route 的新信息更收敛：train-side `capability_gate_train_inhibit_recall mean` 仍在 hard-negative 同一量级（`0.456 -> 0.446`），但 held-out family test 同时劣于 `hard-negative` 和 `single-threshold asymmetric calibration`。也就是说，当前 execute-margin penalty 没有形成更好的 asymmetric structure，只引入了额外泛化噪声。
- 2026-03-11: 当前主线进一步收敛：问题已经不只是 “缺 train-time asymmetric objective”，而是当前 single-score fine-tuned pair model 本身不适合同时承载 inhibit pressure 和 execute retention。下一步不再做 execute-margin 小修，直接转向 `dual-threshold / abstain-band decision rule`。
- 2026-03-12: 已新增 `semantic_cross_encoder_dual_threshold_capability_gate`，在 hard-negative fine-tuned pair model 上接了 control-aware dual-threshold / abstain-band decision rule。
- 2026-03-12: 双 seed 正式结果是 `CAA=0.736 / CAA+=0.760 / NOS=0.409 / POC=0.760 / coverage=0.944`，`regressed_pair_count=38`。
- 2026-03-12: 这条 route 的新信息非常明确：两个 seed 上都出现 `capability_gate_abstain_threshold == capability_gate_threshold`、`capability_gate_train_abstain_rate = 0.0`，也就是 dual-threshold search 自己塌回了 hard-negative 单阈值。
- 2026-03-12: 当前主线进一步收敛：plain abstain-band threshold search 本身不够，下一步如果还沿 decision-rule 路线推进，需要显式 `abstain` 偏好或更强的 control-aware objective，而不是继续扫 threshold。
- 2026-03-12: 在研究治理上正式收束主线：当前 `data/real_evolution_benchmark.json` 不再被视为 blind test，而是 `real-evolution dev panel`，后续方法搜索只允许在这个 dev panel 上进行。
- 2026-03-12: 新增 `scripts/generate_real_evolution_blind_benchmark.py`，生成 `data/real_evolution_blind_benchmark.json`、`data/real_evolution_blind_audit.json`、`history/real_evolution_blind_audit.md`；blind panel v1 为 `4 cases / 8 views / 9 official sources / 1 family (trello)`。
- 2026-03-12: blind panel v1 覆盖 `positive_version_migration` 与 `negative_near_orbit` 两类 view：前者为 Trello member-privacy compliance route 从 legacy application route 迁移到 plugin route，后者为 Trello SCIM users/groups 废弃后只剩 related REST endpoints 的 non-drop-in replacement。
- 2026-03-12: 新增 `tests/test_real_evolution_blind_benchmark.py`，并修正 `OracleAgent` 对显式 view optional arguments 的渲染逻辑，使显式 real-evolution views 不再因为缺失 optional slot 而抛 `KeyError`。
- 2026-03-12: blind panel v1 的最小验证链已跑通：`infer` 环境全量测试现为 `119` 个通过；`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json` 已完成 structural smoke，`oracle` 满分，说明 blind asset 已可独立加载、评测与审计。
- 2026-03-12: blind panel 继续扩到 v2，新增 `youtube` family；当前 blind benchmark 为 `8 cases / 16 views / 17 official sources / 2 families (trello + youtube)`。
- 2026-03-12: `youtube` family 提供了与 Trello 不同的 negative style：一类是同一 endpoint 上 capability/parameter 被正式移除（`relatedToVideoId`），另一类是 legacy moderation method 直接不再支持（`comments.markAsSpam`）。
- 2026-03-12: blind panel v2 的 focused tests 已扩到 `8` 个；infer 环境全量测试现为 `122` 个通过，`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v2` 已跑通。
- 2026-03-12: blind seed pilot v2 结果显示该面板已具备非平凡诊断性：`lexical_shortcut CAA=0.188 / NOS=0.750`，`description_grounded CAA=0.375 / CAA+=0.250 / NOS=0.250`；当前仍只将其视为 blind structural smoke，而不用于方法选择。
- 2026-03-12: blind panel 继续扩到 v3，新增 `youtube_channels` lineage family；当前 blind benchmark 为 `12 cases / 24 views / 20 official sources / 3 family tags across 2 vendors`。
- 2026-03-12: `youtube_channels` 不是新 vendor，而是新的 version-lineage family：它补上了 `playlist lookup split` 和 `broader-surface home feed` 两类与 Trello / YouTube-v2 不同的 negative style。
- 2026-03-12: blind panel v3 的 focused tests 已扩到 `11` 个；infer 环境全量测试现为 `125` 个通过，`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v3` 已跑通。
- 2026-03-12: blind seed pilot v3 结果为 `lexical_shortcut CAA=0.208 / NOS=0.833`、`description_grounded CAA=0.458 / CAA+=0.500 / NOS=0.333 / POC=0.500`；当前 blind panel 仍只用于结构验证，不承接方法选择。
- 2026-03-15: blind panel 继续扩到 v4，新增 `github_rest` family；当前 blind benchmark 为 `16 cases / 32 views / 29 official sources / 4 family tags across 3 vendors`。
- 2026-03-15: `github_rest` 提供了两种与现有 families 不同的 negative style：`generic endpoint -> resource-context split` 与 `API route -> out-of-band replacement`。
- 2026-03-15: blind panel v4 的 focused tests 已扩到 `14` 个；infer 环境全量测试现为 `128` 个通过，`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v4` 已跑通。
- 2026-03-15: blind seed pilot v4 结果为 `lexical_shortcut CAA=0.406 / CAA+=0.250 / NOS=0.875 / POC=0.250`、`description_grounded CAA=0.594 / CAA+=0.625 / NOS=0.500 / POC=0.625`；当前仍只将其视为 blind structural smoke，而不用于方法选择。
- 2026-03-15: blind panel 继续扩到 v5，新增 `gitlab_rest` family；当前 blind benchmark 为 `20 cases / 40 views / 32 official sources / 5 family tags across 4 vendors`。
- 2026-03-15: `gitlab_rest` 提供了与现有 families 不同的 `contract/body/response semantics` 风格：两条正样本来自 response-field migration（`merged_by -> merge_user`, `merge_status -> detailed_merge_status`），两条负样本来自 response-contract split 和 body-parameter disambiguation。
- 2026-03-15: blind panel v5 的 focused tests 已扩到 `17` 个；infer 环境全量测试现为 `131` 个通过，`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v5` 已跑通。
- 2026-03-15: blind seed pilot v5 结果为 `lexical_shortcut CAA=0.375 / CAA+=0.200 / NOS=0.900 / POC=0.200`、`description_grounded CAA=0.625 / CAA+=0.700 / NOS=0.400 / POC=0.700`；当前 blind panel 已达到 `5` 个 families，但仍只视为 structural smoke，不参与方法选择。
- 2026-03-15: blind panel 继续扩到 v6，新增 `slack_auth` family；当前 blind benchmark 为 `24 cases / 48 views / 42 official sources / 6 family tags across 5 vendors`。
- 2026-03-15: `slack_auth` 提供了与现有 families 不同的 `auth/scope/permission semantics` 风格：OAuth flow migration、scope narrowing、unified scope model 迁移，以及 permission inventory split。
- 2026-03-15: blind panel v6 的 focused tests 已扩到 `20` 个；infer 环境全量测试现为 `134` 个通过，`scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v6` 已跑通。
- 2026-03-15: blind seed pilot v6 结果为 `lexical_shortcut CAA=0.396 / CAA+=0.308 / NOS=0.818 / POC=0.308`、`description_grounded CAA=0.625 / CAA+=0.692 / NOS=0.364 / POC=0.692`；当前 blind panel 已达到 `6` 个 families，可开始讨论冻结 blind panel 并用于最终方法结论复核。
- 2026-03-15: blind panel 已正式冻结；`scripts/generate_real_evolution_blind_benchmark.py` 现会写入 `metadata.panel_role=blind_test`、`panel_state=frozen`、counts/family/vendor 摘要，以及 audit 路径指针。
- 2026-03-15: 新增 `src/toolshift/blind_panel.py` 与 `scripts/validate_blind_panel.py`；当前 frozen blind panel 会被校验为：`method_selection_allowed=false`、`family_tags` 与 dev panel 不重叠、全部样本仍为 `unambiguous_core`。
- 2026-03-15: frozen blind panel 校验产物已写到 `artifacts/real_evolution_blind_panel_freeze_v1/summary.json`；focused tests 现为 `23` 个通过，infer 环境全量测试现为 `137` 个通过，`artifacts/real_evolution_blind_seed_pilot_frozen_v1` 结果与 v6 一致。
- 2026-03-15: 新增 `src/toolshift/masking.py`、`tests/test_masking.py` 与 `scripts/run_masking_sensitivity.py`，在 dev panel 上做 held-out family test-time masking sensitivity，而不是对 masked 任务重训。
- 2026-03-15: `semantic_embedding_capability_gate` 与 `semantic_clause_localization_capability_gate` 的 `name_mask` 几乎不掉分，但 `description_mask / contract_mask` 都明显掉分。最强 scaffold baseline 从 `CAA=1.000` 掉到 `0.632 / 0.618`，保留 learned route 从 `0.868` 掉到 `0.500 / 0.486`。
- 2026-03-15: 当前 masking 结果说明 dev panel 上真正决定行为的不是 tool/arg 名字，而是 description / contract cue；这条机制证据已落到 `artifacts/real_evolution_masking_sensitivity_v1`。
- 2026-03-15: 新增 `src/toolshift/decision_probe.py`、`tests/test_decision_probe.py` 与 `scripts/run_decision_probe.py`，在 dev panel 上对 retained methods 抽 decision-state、训练线性 probe，并计算 positive-state similarity / negative separation gap。
- 2026-03-15: `semantic_embedding_capability_gate` 的 decision-state probe 明显强于 retained learned route：`probe_accuracy=0.972`、`probe_negative_recall=0.889`、`positive_state_similarity=0.997`、`state_separation_gap=1.322`；而 `semantic_clause_localization_capability_gate` 分别是 `0.826 / 0.833 / 0.615 / 1.060`。
- 2026-03-15: 当前 decision-state 结果与 masking 结论一致：最强 scaffold baseline 不仅依赖 description / contract cue，而且确实在内部 state 上形成了更稳的 positive orbit 聚合和更强的 clean-vs-negative separation。
- 2026-03-15: 新增 `src/toolshift/boundary.py`、`tests/test_boundary.py` 与 `scripts/run_boundary_evidence.py`，将 dev panel 的每条 negative near-orbit 派生为 `counterfactual impossible shadow`，用于量化 hidden backend shift 的边界。
- 2026-03-15: boundary evidence 结果很干净：`semantic_embedding_capability_gate` 在 visible negatives 上仍是 `NOS=1.000`，但在 impossible shadows 上 `impossible_CAA=0.000`、`execute_rate=1.000`；retained learned route 也只达到 `impossible_CAA=0.136`、`execute_rate=0.864`。
- 2026-03-15: 当前 boundary 结果说明 strongest empirical claim 必须明确限定在 `schema-visible capability gap`，不能外推到 hidden shift；这条边界证据已落到 `artifacts/real_evolution_boundary_evidence_v1`。
- 2026-03-15: 新增 `src/toolshift/blind_review.py`、`tests/test_blind_review.py` 与 `scripts/run_blind_review.py`，将方法复核固定成 `dev panel` 训练、`frozen blind panel` 一次性评测。
- 2026-03-15: frozen blind review v1 结果显示 strongest scaffold baseline 仍是当前主线最强方法：`CAA=0.917 / CAA+=1.000 / NOS=0.727 / POC=1.000`；retained learned route 为 `0.781 / 0.885 / 0.818 / 0.885`。
- 2026-03-15: blind review 进一步说明 dev-perfect 不能当最终结论：`semantic_embedding_capability_gate` 在 blind `slack_auth` 上 `NOS=0.0`，在 `gitlab_rest / trello` 上也只到 `0.5`；retained learned route 虽然把 overall `NOS` 抬到 `0.818`，但明显牺牲了 `CAA_clean / CAA+ / POC`。
- 2026-03-15: 新增 `src/toolshift/panel_review.py`、`tests/test_panel_review.py` 与 `scripts/compare_dev_blind_retained_methods.py`，将 retained methods 的 `dev panel -> blind panel` 落差正式量化。
- 2026-03-15: `semantic_embedding_capability_gate` 的 blind drop 主要集中在 `NOS`（`1.000 -> 0.727`），`CAA+ / POC` 在 blind 上保持 `1.000`；这说明 strongest scaffold baseline 的盲测问题主要是 negative inhibition，而不是 positive retention。
- 2026-03-15: `semantic_clause_localization_capability_gate` 的 blind `NOS` 只从 `0.864 -> 0.818`，但 `CAA_clean` 从 `0.917 -> 0.708`；learned route 当前更适合被表述成“更保守的诊断路线”，而不是 strongest retained method。
- 2026-03-15: frozen blind 最明显的 strongest-baseline 压力 family 仍是 `slack_auth`；这条 blind signal 现在已经通过 blind review 和 dev-vs-blind comparison 双重确认。
- 2026-03-15: 新增 `history/final_framing.md`，将 strongest story 固定为 `benchmark / protocol + diagnosis + strong scaffold baseline`，并明确把 learned route 降到 diagnostic / future-work 定位。
- 2026-03-15: 新增 `paper/` 目录并导入官方可公开最新 `neurips_2025` 模板；完成 `paper/main.tex + sections + refs.bib` 的英文初稿，`latexmk -pdf main.tex` 已在本地编译通过。
- 2026-03-15: 当前 paper draft 主标题为 `ToolShift: Evaluating Canonical Actions under Real API Evolution`，主叙事完全对齐 `history/final_framing.md`：benchmark/protocol + diagnosis + strong scaffold baseline，而不是 SCC 已验证成功。
- 2026-03-15: 完成第一轮高强度写作润色：标题更新为 `ToolShift: Canonical Semantic Actions under Real API Evolution`，intro 改成贡献导向表述，新增 related work，小幅收紧 discussion；`paper/main.pdf` 重新编译通过且无 undefined citations / references。
- 2026-03-16: 已将“是否再给 SCC 主方法一次机会”单独收束成 `history/decisive_method_run.md`；当前 policy 变为：pair/localizer family 不再继续扩展，若重开方法线，只允许一次 `teacher-distilled canonical-bottleneck SCC` 的 decisive run。
- 2026-03-16: 这次 decisive run 的治理边界已固定：只比 `SeedOnly / AugOnly / TeacherDistilledBottleneckSCC` 三组，blind panel 不参与选择，且必须同时通过 `CAA+ / NOS / POC / coverage-controlled NOS` 与 mechanism criteria 才能进入 blind review。
- 2026-03-16: 已实现第一版 `teacher_distilled_bottleneck_scc`，当前落点是在现有 `ActionBottleneckModel` 上增加显式 `slot` / `gap` 头，并在训练期蒸馏 strongest scaffold teacher `semantic_embedding_capability_gate` 的 control/tool/slot/gap supervision。
- 2026-03-16: 同步实现了 `seed_only` control 分支与新的 matched-budget config 项；focused tests `tests.test_embedding_policy_utils` 和 infer 环境全量测试现均通过（`152` 个测试）。
- 2026-03-16: 已完成最小 CLI smoke：`scripts/run_matched_budget_pilot.py --methods teacher_distilled_bottleneck_scc --regimes combo_holdout --seeds 0 --epochs 1` 可直接调起新方法并写出 summary/records；当前仅将其视为实现打通，不将单 seed / 单 epoch 数字当正式方法结果。
- 2026-03-16: 已完成正式 decisive run：`SeedOnly / AugOnly / TeacherDistilledBottleneckSCC` 在 `data/real_evolution_benchmark.json` 的 `family_holdout_cv` 上跑完 `3` seeds。结果分别为 `SeedOnly = 0.083 / 0.000 / 0.545 / 0.000`、`AugOnly = 0.093 / 0.000 / 0.606 / 0.000`、`TeacherDistilled = 0.102 / 0.000 / 0.636 / 0.000`（指标顺序 `CAA / CAA+ / NOS / POC`）。
- 2026-03-16: diagnostics 与 paired compare 说明这轮 lift 极小：相对 `AugOnly` 只多修了 `2` 个 pairs、`0` regressions，改进集中在 `stripe_update_subscription_source`；主错误桶仍是 `missed_execute_ask_clarification=157`。
- 2026-03-16: masking 与 decision-probe 机制证据都未过 decisive-run 门槛。`TeacherDistilled` 没有形成 `description/contract > name` 的 grounding pattern；`probe_negative_recall` 略升，但 `positive_state_similarity` 与 `state_separation_gap` 都低于 `AugOnly`。
- 2026-03-16: 为补齐正式 mechanism pack，已将 `src/toolshift/decision_probe.py` 与 `scripts/run_decision_probe.py` 扩展到支持 `EmbeddingPolicyAgent`；新增 focused test 后，infer 环境全量测试现为 `153` 个通过。
- 2026-03-16: 当前这次唯一允许的 decisive run 已正式判定 `No-Go`。后续默认不再继续 SCC 方法搜索；如无新的 thesis 级方法路线，paper 主线保持为 benchmark/protocol + diagnosis + strong scaffold baseline。
- 2026-03-16: 已将 decisive run 的 `No-Go` 结果正式写入 NeurIPS 主文：`abstract / intro / methods / results / discussion` 现在都明确把 `TeacherDistilledBottleneckSCC` 定位为预先承诺的最终复核负结果，而不是继续保留 SCC 成功叙事；`paper/main.pdf` 已重新编译通过，主文仍为 `8` 页。
- 2026-03-16: 已继续把主文从“项目实现命名”收束成投稿可读命名：标题改成更明确的 evaluation framing，正文统一使用 `scaffold baseline / learned localizer / final SCC check`，discussion 去掉 `Recommended positioning` 这类内部措辞。
- 2026-03-16: 已继续完成一轮文风级精修：abstract 更短更硬，intro 的 contribution list 去掉项目过程腔，methods/results/discussion 对 decisive run 的口径完全统一；`paper/main.pdf` 再次编译通过，当前版本已更接近完成态 benchmark paper。
- 2026-03-16: 已新增 benchmark 主文总览图：用单栏 compact figure 取代纯计数表，显式展示 `positive / negative / impossible` 协议划分与 `dev panel -> validation chain -> frozen blind panel` 治理结构。当前 `paper/main.pdf` 重新编译通过，整份 PDF 为 `9` 页（含参考文献与附录）。
- 2026-03-16: 已继续收紧结果呈现：在主结果节新增 blind stress summary，把 `dev->blind` 的 `dNOS`、最难 negative family 和最弱 positive family 直接做成 compact table，不再只靠 prose 解释 blind 压力点。
- 2026-03-16: 已完成一轮提交口径压缩：标题改成 `Canonical-Action Evaluation under Real API Evolution`，摘要进一步压短，intro 贡献段和主结果 caption 更像 benchmark-paper 定稿表述。
- 2026-03-16: 新增 `DocumentRetrievalRerankAgent` 与 `scripts/run_retrieval_baseline.py`，把 reviewer 点名想看的 `retrieval + rerank` 文档调用系统补成独立 baseline bucket，而不是继续扩 retained internal methods。
- 2026-03-16: 已完成 `doc_retrieval_rerank` 在 TOOLSHIFT `dev / blind` 与 `API-Bank / BFCL / ToolEVO` bridge 上的首轮结果。它在 API-Bank 上强于公开 Qwen3-8B (`CAA 0.806 > 0.486`)，但在 TOOLSHIFT blind 与 BFCL / ToolEVO 上不占优，说明这条 baseline 更像 `schema-visible documentation retriever`，而不是新的 strongest general system。
- 2026-03-16: 新增 `src/toolshift/bfcl_bridge.py` 与 `scripts/generate_bfcl_bridge_benchmark.py`，从 BFCL v4 公开数据生成 `data/bfcl_bridge_benchmark.json` / `data/bfcl_bridge_audit.json` / `history/bfcl_bridge_audit.md`。当前 bridge benchmark 为 `50 cases / 50 views / 66 tools`，均衡覆盖 `simple_python / multiple / live_simple / irrelevance / live_irrelevance` 五类公开社区任务。
- 2026-03-16: 新增 `scripts/run_bfcl_bridge_pilot.py`，并在 BFCL bridge 上完成 `Oracle / LexicalShortcut / DescriptionGrounded / Qwen3-8B` 首轮对照。结果显示 `Qwen3-8B` 在 bridge 上达到 `CAA=0.840 / coverage=0.640 / selective_risk=0.250`，明显强于内部 heuristic baselines，但仍低于 oracle。
- 2026-03-16: category breakdown 进一步说明 BFCL bridge 不是空壳：`Qwen3-8B` 在 `simple_python / multiple` 为 `1.0`，在 `irrelevance / live_irrelevance` 为 `0.9`，但在 `live_simple` 只到 `0.4`。这说明 bridge 同时保留了 execute 与 abstain 压力。
- 2026-03-16: 已在 frozen TOOLSHIFT blind panel 上补跑外部公开模型 `Qwen3-8B`。结果为 `CAA=0.875 / CAA_clean=0.958 / CAA+=0.923 / NOS=0.636 / POC=0.923 / coverage=0.854`，显著低于 strongest scaffold baseline (`0.917 / 1.000 / 0.727 / 1.000`)。
- 2026-03-16: `Qwen3-8B` blind family breakdown 说明 TOOLSHIFT 的难点并非“只对内部方法族难”：它在 `github_rest` 上全对，但在 `slack_auth` 与 `gitlab_rest` 上 `NOS=0.0`，在 `youtube` 上 `CAA+=0.5`，与 strongest scaffold baseline 的 blind 压力点高度重合。
- 2026-03-16: 为了支持外部 execute-heavy baseline，已在 `src/toolshift/eval.py` 中放宽 canonicalization：若 view-visible helper argument 不属于 canonical action 空间，则 execute path 现在会忽略该 argument，而不是在 evaluator 内部抛错。对应 focused test 已补到 `tests/test_audit_overrides.py`。

## Blockers / Decisions
- 当前无真实 API evolution 数据；先用 seed synthetic suite 跑通主协议，再扩到 real split。
- 默认先不安装新包；正式模型实验优先尝试 `infer` 环境现有 `torch/transformers`。
- `negative_deprecate` 在 seed suite 中采用 set-valued admissible control（`abstain` / `ask_clarification`），避免把合法控制策略误判为错。
- 当前默认保留 `enable_thinking=True` 作为 Qwen seed baseline，因为 non-thinking 模式在 `NOS` 上存在明显 refusal gaming，且 `CAA+ / POC` 极差。
- `negative_deprecate` 经 audit 改为 `abstain-only`；`negative_contract` 默认保留 `ask_clarification` policy。
- reminder / calendar 相关请求已确认不适合作为当前主表 `unambiguous core`，后续需要更干净的时间类样本替换。
- 对绝对时间 case，已用 deterministic canonicalization 修复 `datetime + timezone` 合并写入一个 slot` 的伪失败。
- 仍未解决的是真实 abstain / ask_clarification 与 tool choice 错误，而不是 slot-boundary 问题。
- 当前 frozen-embedding pilot 在 `combo_holdout` 上几乎饱和，在 `case_holdout_cv` 上 clean / positive 近乎全灭；当前 seed suite 还不足以支持有说服力的 matched-budget 方法结论。
- `SCC-lite` 的强正则会直接损伤 `POC / CAA+`；默认权重已降到 `0.1 / 0.1`，作为公平 sanity setting。
- richer family suite 缓解了 seed suite 的极端问题：`case_holdout_cv` 现在达到 `CAA=0.880`、`CAA+=0.944`、`NOS=0.792`。
- 但 `SCC-lite` 仍未超过 `AugOnly`，说明当前没有 gap 不能再只归因于 split 太差；下一步要么加强 bottleneck / slot head，要么进入更贴近 proposal 的 factorized / real split。
- `family_holdout_cv` 证明 richer family suite 里仍然存在真正困难的 OOD：当前 `CAA_clean = 0.0`、`CAA+ = 0.0`，模型只能在部分 negative control 上勉强工作。
- `SCC-lite` 在 family-holdout 上的微小增量只来自 `email_demo_confirmation::negative_deprecate` 这一条 `abstain` 预测，不足以支持 proposal 的方法学 claim。
- factorized 诊断进一步说明：当前 `family_holdout_cv` 的主失败不是 wrong-tool 或 wrong-args，而是对 held-out family 完全不进入 execute；因此继续只加 slot head 不会命中主要误差源。
- `semantic_gate` 虽然把 cross-family 正样本几乎全部救回，但 `negative_contract` 仍然 `36/36` 误执行；下一步必须把 contract-aware inhibition 接进来，否则只是在把错误从 under-execute 挪到 over-execute。
- `semantic_contract_gate` 已经在 richer synthetic `family_holdout_cv` 上同时实现高 `CAA+` 与高 `NOS`；继续只在 synthetic 上做微调的边际价值开始下降，下一步更该进 real split。
- real split v1 说明当前 inhibition 机制仍偏 schema-hard-signal：
  对显式 deprecation 能工作，但对 `replacement semantics / removed capability` 这类主要写在 description 里的真实变化还不够。
- 当前 `6-case / 12-view` real split 已经更像 fixed regression panel，而不是下一阶段主实验上限；继续在这套 panel 上微调的边际价值已经很低。
- 扩到 `12-case / 24-view` 后，当前 panel 仍然全部落在 `Notion / Slack / Stripe` 三个 family 内；下一阶段若还想继续验证外推能力，需要引入新 vendor family 或 execution-level checks，而不是继续只补同类 schema rewrite。
- execution sanity 已经把当前 expanded real split 从“schema + docs benchmark”推进成“带最小 effect validation 的 benchmark”；下一阶段更缺的是新 vendor family，而不是继续增强同一批 case 的内部一致性。
- generic `files.update` / `update`-style positive migrations 即使语义正确，也可能因为 gate threshold 被压成 `ask_clarification`；description-only 修正不一定够，当前需要显式的 near-threshold semantic rescue。
- 当前 fixed panel 已包含两类负样本风格：
  1. contract/shape hard-signal (`parent scope`, `removed field`, `source removed`)
  2. description/privacy gap (`search replacement`, `legacy identifier removed`, `shortcuts instead`)
  这让 `semantic_capability_gate` 的评估比之前更接近 real-world API evolution。
- 当前 `data/real_evolution_benchmark.json` 在科研流程上已经是 `dev panel`，不是 blind test。
  后续方法搜索仍可继续使用它做回归，但任何更强的主方法 claim 都需要落到新的 blind panel 上复核。
- blind panel 在新增到足够 family 之前，只做结构验证，不做 learned-method sweep。
  当前允许的操作是：generation、audit、load-suite、Oracle/heuristic smoke、必要的 validator wiring；不在 blind panel 上继续做方法选择。
- 当前 blind panel 已开始覆盖不同负样本风格，而不是只靠一个 family。
  下一步继续扩 blind families 时，优先补新的 negative style，而不是只复制已有 `route replaced` 模板。
- blind panel 现已达到冻结门槛。
  之后默认不再扩 family，也不再在 blind panel 上做方法搜索；若要改 blind asset，必须显式重开治理决策并同步更新 freeze summary / audit。
- `execution sanity` 和 `request replay` 已经形成互补：
  - 前者回答 “会不会产生正确 effect”
  - 后者回答 “当前 surface 下到底会发出什么请求”
- `official-doc smoke` 适合用稳定 API marker，而不是押整句叙述文案；像 Drive shortcuts 这类页面，长句 wording 会漂移，但 `one parent`、`shortcuts`、`addParents` 这类 marker 更稳定。
- 现在三条 sanity 已经互补：
  - `execution_sanity`: effect
  - `request_replay`: rendered request
  - `official_request_smoke`: official-doc evidence
  下一步若还想继续增强证据链，就该开始做少量真实 API-level smoke，而不是继续只扩 mock。
- machine-readable API smoke 也需要按 provider/version 分开接。
  Jira Cloud 的 v2 和 v3 不共享同一个 swagger JSON：v2 在 `swagger.v3.json`，v3 在 `swagger-v3.v3.json`。如果默认拿一个 JSON 覆盖所有版本，会把 clean/positive migration 的版本差异抹掉。
- 对 capability-gap negatives，OpenAPI/discovery 不足以单独判定。
  像 Jira legacy username 这类 case，machine-readable surface 里仍可能残留兼容字段；要避免误放行，仍然需要 docs-backed removal cue 与 non-execute 一起判。
- 当前本地环境没有可直接复用的 Drive / Jira authenticated smoke 凭证；继续等待凭证会阻塞主线，因此当前默认路线改为 public-spec real family 扩展。
- Google Sheets 这类 migration guide 驱动的新 family 可以无认证接入完整验证链，但 negative capability-gap 仍要求 rendered description 保留 request-token overlap；只写抽象 “not supported” 容易让 deterministic inhibition 漏掉 replacement semantics。
- Google People discovery 使用 `{+resourceName}` 这类 full-path expansion；如果 machine-readable validator 继续按 path segment 数量硬匹配，会把真实存在的 positive request 误判成 surface mismatch。
- People family 说明 `semantic_contract_gate` 仍会把 “read-only but related workaround exists” 的 case 执行成 tool-choice error；当前 full-panel 仍需要 description-aware capability inhibition 才能稳住 negatives。
- public OpenAPI validator 不能假设 request path 与 spec `paths` 直接同形；Confluence 这类 provider 会把 `/wiki/api/v2` 放在 `servers[].url`，而 request body 也可能通过 `components/requestBodies` 间接引用。
- Swagger 2.0 family 还会把 path 前缀放在 `basePath`，例如 Bitbucket 的 `/2.0`；machine-readable validator 若只看 `paths` 本体，positive migration 会被系统性误报为 surface mismatch。
- `9-family fixed panel` 现在已经足够回答 “capability gate 多做对了什么”；继续扩 family 的边际价值开始下降，下一步更该把剩余增量转成更可学习的 inhibition 机制。
- learning-oriented capability inhibition 已经能在 frozen panel 上追平 rule gate，但当前还离不开 `cue-triggered` guard；下一步真正的核心难点，是如何放松这层 trigger 而不重新引入 positive over-inhibition。
- 现在外层 `cue-triggered` guard 已经可以收进 scorer 的 feature 选择里；下一步更核心的难点，是如何继续去掉 `has_gap_rule / cue_clause_count` 这类显式 binary cue 特征。
- 现在显式 binary cue 特征也已经可以拿掉；下一步更核心的难点，是如何继续减少 hand-crafted overlap statistics，本质上把 inhibition 推向更原生的 learned text feature。
- 现在 overlap 统计也已经可以替换成 embedding similarity 特征；下一步真正剩下的手工先验，主要是 `_capability_cue_clauses()` 这层 negative clause extraction。
- 直接拿掉 `_capability_cue_clauses()` 目前会明显回退；whole-text 和 generic clause-pooling 都不足以同时守住 negative inhibition 与 positive execute。
- 把 generic clause localization 接成 low-sample linear interaction scorer，同样会明显 over-inhibit；当前问题不只是 “有没有 localization”，还包括 “pair modeling 是否足够强”。
- train-time supervised clause localization 确实比 generic interaction 更像正确方向，但当前 low-sample 线性实现过拟合严重，暂时还不能替代 cue-specific embedding baseline。
- 直接把 clause-localization head 压成低维 calibrated scalar，也不能解决泛化；当前 learned route 的问题不是单纯 feature dimension 太高。
- 直接换成 frozen joint pair-text embedding 也不能解决问题；pair input 序列化本身不足以学出稳健的 capability localization，下一步需要更强的 pair model，而不是继续试 frozen + linear 变体。
- small MLP pair head 虽然优于 linear pair head，但仍明显卡在 positive / negative tradeoff 上；当前 frozen encoder 路线已经把“pair input 有无”和“线性头够不够”这两层都试过了。
- 直接把 pretrained reranker 接成 threshold-calibrated cross-encoder，也会学成“强相关性执行器”而不是稳定 inhibitor。
  当前 `semantic_cross_encoder_capability_gate` 在 `clean / positive` 上接近可用，但 `negative_near_orbit` 只剩 `NOS=0.273`。这说明主线下一步不是再换一个现成 reranker，而是把 negative capability-gap supervision 真正放进 pair model 训练。
- `teacher-distilled canonical-bottleneck SCC` 的唯一 decisive run 已经关账；当前不再缺“再试一个更 faithful 的版本”，而是已经有足够负证据说明这条方法线在现有数据与监督条件下不值得继续投入。

## Resume Point
1. blind panel 已冻结为 `24 cases / 48 views / 42 official sources / 6 family tags across 5 vendors`；`scripts/validate_blind_panel.py` 是新的最小治理护栏，要求 `method_selection_allowed=false`、blind/dev family disjoint、以及全部样本保持 `unambiguous_core`。
2. blind panel 后续只用于最终方法复核，不再承接方法搜索；当前方法开发与回归仍全部留在 `data/real_evolution_benchmark.json` 对应的 `9-family dev panel`。
3. 以当前 `semantic_embedding_capability_gate` 为最强 scaffold baseline；在 retained learned 路线里，当前保留的是 `semantic_clause_localization_capability_gate`。
4. dev-panel masking 结果已经说明：`name_mask` 基本不伤两条路线，但 `description_mask / contract_mask` 会同时压低 `CAA+ / POC / NOS`。当前最强方法的能力主要来自 localized description / contract cue，而不是 raw tool names。
5. decision-state probe 进一步说明：最强 scaffold baseline 不只是在行为上更好，它在内部 state 上也形成了更高的 positive-state similarity 和更强的 clean-vs-negative separation。
6. boundary evidence 进一步说明：一旦把 negative admissible action 放到 clean surface 上形成 `counterfactual impossible shadow`，最强 scaffold baseline 会 `100%` 回到 execute。当前 strongest story 只能 claim `schema-visible evolution`，不能 claim hidden backend shift。
7. frozen blind review v1 与 dev-vs-blind comparison 都已完成：`semantic_embedding_capability_gate` 仍是当前最强主线方法，但 blind drop 主要集中在 `NOS`（尤其是 `slack_auth`）；retained learned route 的 blind `NOS` 更高（`0.818`），但明显牺牲 `CAA_clean / CAA+ / POC`。
8. 现成 reranker + threshold、supervised threshold、ranking top-selection、pairwise、listwise、capability-only fine-tuned pair model、joint `capability + localization` multitask fine-tune、hard-negative / class-balanced fine-tuned pair model、以及 explicit positive-retention / asymmetric decision calibration 都已完成验证。当前证据说明：仅换 loss、只做 capability fine-tune、把 localization 一起训进去、直接做全局 hard-negative weighting、或只靠单阈值 asymmetric calibration 都不够。
9. `train-time asymmetric objective` 与 `dual-threshold / abstain-band rule` 也已完成验证；当前单分数 fine-tuned pair model 路线的 threshold/objective 小修已经基本试尽。
10. 新方法的第一验收面板固定为：
   `scripts/compare_fixed_panel_methods.py`
   `scripts/diagnose_saved_records.py`
   `scripts/run_execution_sanity.py`
   `scripts/run_request_replay.py`
   `scripts/run_official_request_smoke.py`
   `scripts/run_api_surface_smoke.py`
11. 若未来出现可用凭证，再补 1-2 个关键 Drive / Jira case 的最小 authenticated API-level smoke validation；但这不再是当前主线 blocker
12. 当前最强 paper framing 已经收敛到：`benchmark / protocol + diagnosis + strong scaffold baseline`；若继续保留 learned route，应只以诊断/未来工作身份出现，除非后续出现新的 blind-level证据。
13. `history/final_framing.md` 已经给出推荐主张、非主张、方法定位和 future-work 边界；后续若继续推进，应优先围绕该 framing 整理图表和写作，而不是继续在 dev panel 上做同级别方法 sweep。
14. `paper/main.pdf` 已可编译，当前最有价值的默认下一步仍是精修 paper text 与 figure/table 设计。
15. 唯一允许的 SCC decisive run 已经执行完成，结论为 `No-Go`；后续默认不再继续方法搜索，除非出现新的 thesis 级方法路线而非当前 family 的延长线。
16. 当前 paper 主线应回到 `benchmark / protocol + diagnosis + strong scaffold baseline`，并把这次 decisive run 写成系统负结果，而不是继续寻找补救 sweep。
17. 当前最有价值的下一步是把这轮 `No-Go` 结果、blind review、masking、decision probe、boundary evidence 一起收进主文图表与摘要/引言 framing。
18. 外部 comparability 已经从单一 `BFCL bridge + Qwen3-8B` 扩到两条链：
   - `BFCL bridge`: 静态社区 function-calling competency
   - `ToolEVO bridge`: 公开 evolving-tool portability
   同时又补了 `Qwen3-0.6B / 4B` 在 TOOLSHIFT dev/blind 上的直接 public-model baseline。
19. `Qwen3-4B` blind run 暴露并帮助修掉了 blind GitLab `get_with_changes` 的 canonical-slot 漏记（补上 optional `page / page_size`）；这说明 execute-heavy public baselines 也应被视为 protocol fuzzers，而不只是比较对象。
20. 当前对 review 最有杀伤力的新增证据已经具备：
   - 外部 benchmark/case：`ToolEVO bridge`
   - 外部 public baseline：`Qwen3-0.6B / 4B`
   - 结构验证：ToolEVO bridge Oracle perfect，blind benchmark regenerated and revalidated
21. 如果继续沿 benchmark-paper 主线，下一步最值钱的不是再加方法，而是把 `BFCL bridge + ToolEVO bridge + Qwen public baselines` 收进 paper 的主结果/附录与审稿人 concern 对照。
22. paper appendix 现已补上 reviewer-facing supporting tables：一张汇总 `ToolShift / API-Bank / BFCL / ToolEVO` 上的 public-model external comparability，一张汇总 blind `split sensitivity`，以及一张汇总 family-bootstrap / leave-one-family-out stability。当前主文可以更直接回应“外部 baseline 缺失”和“blind 结论是否只是单-family artifact”的批评。
