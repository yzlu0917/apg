# ToolShift Results

## 2026-03-09 Seed Benchmark Bootstrap

### Goal
跑通 proposal Week 1 所需的最小闭环：canonical action、positive/negative orbit、审计包导出、首轮 pilot。

### Environment
- Python 3.12.4
- `infer` conda 环境可用 `torch 2.9.1+cu126` 与 `transformers 4.57.6`
- 当前 seed benchmark 为 synthetic bootstrapping suite，尚非 real evolution split

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py`
- `PYTHONPATH=src python scripts/export_audit_packet.py`

### Results
- Audit packet exported to `artifacts/audit/transform_validity.jsonl`
- Seed pilot summary exported to `artifacts/seed_pilot/summary.json`
- Seed pilot detail records exported to `artifacts/seed_pilot/records.json`

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.833 |
| lexical_shortcut | 0.278 | 0.222 | 0.167 | 0.000 | 0.639 |
| description_grounded | 0.722 | 0.444 | 1.000 | 0.167 | 1.000 |

补充观察：
- `lexical_shortcut` 在 positive orbit 明显塌陷，说明 rename / combo shift 会打断表面 schema 匹配。
- `description_grounded` 在 `NOS` 上明显更强，说明显式读取 contract / deprecation 信号后，near-orbit 可被正确切换到 `ask_clarification`。
- 但 `description_grounded` 的 `POC=0.167` 仍低，说明当前 seed baseline 还远没达到 proposal 目标，只够做 harness sanity check。

### Qwen Smoke Test
- 命令：`source /root/miniconda3/etc/profile.d/conda.sh && conda run -n infer python -c "from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained('/cephfs/shared/hf_cache/hub/Qwen3-0.6B', trust_remote_code=True); print(type(tok).__name__); print(tok.eos_token)"`
- 结果：成功加载 `Qwen2TokenizerFast`，`eos_token=<|im_end|>`
- 命令：`source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python - <<'PY' ... AutoModelForCausalLM.from_pretrained('/cephfs/shared/hf_cache/hub/Qwen3-0.6B', torch_dtype='auto').to('cuda') ... PY`
- 结果：GPU 可用（`torch.cuda.is_available() == True`，8 张卡），模型可成功生成文本；最小生成输出为 `'Return exactly one word: ready.\nTo the problem, what is the'`
- 结论：本地缓存路径、GPU 与 `infer` 环境均可直接进入 prompt-only / SFT pilot

### Notes
- 本结果只验证研究骨架与评测协议，不构成正式 paper 主表。
- `negative_deprecate` 在 seed suite 中使用 set-valued admissible control：`abstain` 与 `ask_clarification`。

## 2026-03-09 Qwen Prompt-Only Seed Pilot

### Goal
把本地 `Qwen3-0.6B` 接入 ToolShift 评测协议，获得首个真实模型 prompt-only baseline，并比较 thinking / non-thinking 模式。

### Commands
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --disable-thinking --output-dir artifacts/qwen_seed_pilot_no_think`

### Artifacts
- `artifacts/qwen_seed_pilot/summary.json`
- `artifacts/qwen_seed_pilot/records.json`
- `artifacts/qwen_seed_pilot_no_think/summary.json`
- `artifacts/qwen_seed_pilot_no_think/records.json`

### Results

| Mode | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-0.6B thinking | 0.417 | 0.333 | 0.500 | 0.333 | 0.333 | 0.694 |
| Qwen3-0.6B non-thinking | 0.389 | 0.167 | 0.056 | 1.000 | 0.000 | 0.861 |

### Interpretation
- thinking 模式明显更适合作为后续 baseline：
  `CAA+` 从 `0.056 -> 0.500`，`POC` 从 `0.000 -> 0.333`
- non-thinking 模式的 `NOS=1.000` 不是好消息，而是 refusal gaming：
  它大量输出 `ask_clarification`，导致 clean 与 positive orbit 基本失效
- 0.6B thinking 依然很弱：
  clean 只有 `0.333`，说明当前 prompt-only baseline 仍受能力瓶颈影响，不能直接拿来代表方法上限

### Failure Modes
- 正向 orbit 下仍会因为 rename/combo shift 直接 abstain，尤其在 reminder / calendar / search 样本中明显。
- 参数 grounding 会被模型“重写”成绝对时间或自选表述，导致 canonical argument 不匹配。
- negative near-orbit 上，thinking 模式仍会对部分 contract mutation 或 deprecate 样本盲执行。

### Decision
- 后续默认使用 thinking 模式继续做 Qwen prompt-only baseline。
- 若要判断 prompt-only ceiling，优先升级到 `Qwen3-4B`，而不是继续在 0.6B 上调 prompt 细节。

## 2026-03-09 Qwen3-4B Thinking Seed Pilot

### Goal
用更强的 `Qwen3-4B` 复跑同一套 ToolShift seed suite，区分 0.6B 的问题究竟是能力不足还是 prompt / protocol 本身失效。

### Commands
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --device-map auto --output-dir artifacts/qwen_seed_pilot_4b`
- `python scripts/compare_eval_runs.py artifacts/qwen_seed_pilot/records.json artifacts/qwen_seed_pilot_4b/records.json`

### Artifacts
- `artifacts/qwen_seed_pilot_4b/summary.json`
- `artifacts/qwen_seed_pilot_4b/records.json`

### Results

| Model | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Selective Risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-0.6B thinking | 0.417 | 0.333 | 0.500 | 0.333 | 0.333 | 0.694 | 0.480 |
| Qwen3-4B thinking | 0.472 | 0.667 | 0.500 | 0.333 | 0.333 | 0.444 | 0.188 |

按 transform 拆分：

| Transform | 0.6B CAA | 4B CAA | 0.6B Coverage | 4B Coverage |
| --- | ---: | ---: | ---: | ---: |
| clean | 0.333 | 0.667 | 0.833 | 0.667 |
| positive_rename | 0.500 | 0.333 | 0.667 | 0.500 |
| positive_paraphrase | 0.500 | 0.667 | 1.000 | 0.667 |
| positive_combo | 0.500 | 0.500 | 0.500 | 0.500 |
| negative_contract | 0.167 | 0.000 | 0.500 | 0.000 |
| negative_deprecate | 0.500 | 0.667 | 0.667 | 0.333 |

### Interpretation
- 4B 说明 `prompt / protocol` 不是完全失效：
  clean 从 `0.333 -> 0.667`，整体 `CAA` 从 `0.417 -> 0.472`
- 但 4B 没有把 proposal 的核心现象完全拉清：
  `CAA+`、`NOS`、`POC` 基本不变，说明更大模型并没有自然学会 “该稳时稳、该变时变”
- 4B 更像“更保守但更准”的模型：
  coverage 从 `0.694 -> 0.444`，但 selective risk 从 `0.480 -> 0.188`
- `negative_contract` 全部掉到 `CAA=0.0`，原因不是盲执行，而是大量 `abstain`：
  这提示当前 seed policy 可能把一部分 near-orbit control 边界写得过窄，需要按 proposal 的 `ambiguous split` 思路重新审计

### Runtime Note
- `Qwen3-4B` 单次全量 seed pilot 用时约 7 分钟量级，明显高于 0.6B。

### Decision
- 当前可以排除“0.6B 全部问题都只是 prompt 写坏了”这一解释。
- 下一步不该继续盲调 prompt，而应优先做人审与 split 清理，尤其是 `negative_contract` 和 argument canonicalization 边界。

## 2026-03-09 Seed Audit And Audited Main Table

### Goal
把 seed suite 的主表真正收敛到 proposal 所要求的 `unambiguous core`，并把 `ambiguous split` 显式剥离出来。

### Audit Files
- `data/seed_audit.json`
- `history/seed_audit.md`

### Audit Decisions
- `reminder_tax_form::{clean, positive_*, negative_contract}` 移入 `ambiguous split`
- `calendar_toolshift_sync::{clean, positive_*, negative_contract}` 移入 `ambiguous split`
- 所有 `negative_deprecate` view 统一改为 `abstain-only`

最终 split：
- `core = 26`
- `ambiguous = 10`
- `impossible = 6`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --output-dir artifacts/seed_pilot_audited`
- `PYTHONPATH=src python scripts/rejudge_saved_records.py --records artifacts/qwen_seed_pilot/records.json --output-dir artifacts/qwen_seed_pilot_audited_from_saved`
- `PYTHONPATH=src python scripts/rejudge_saved_records.py --records artifacts/qwen_seed_pilot_4b/records.json --output-dir artifacts/qwen_seed_pilot_4b_audited_from_saved`

### Audited Main Table

| Model / Agent | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.769 |
| Lexical shortcut | 0.308 | 0.750 | 0.250 | 0.200 | 0.000 | 0.615 |
| Description grounded | 0.538 | 1.000 | 0.500 | 0.400 | 0.250 | 1.000 |
| Qwen3-0.6B thinking | 0.538 | 0.500 | 0.750 | 0.300 | 0.500 | 0.846 |
| Qwen3-4B thinking | 0.654 | 1.000 | 0.750 | 0.400 | 0.500 | 0.615 |

### Interpretation
- audit 之后，主表终于更像 proposal 想要的 `unambiguous core`：
  Qwen 的 `CAA+` 从旧主表的 `0.500` 上升到 audited 主表的 `0.750`
- `lexical shortcut` 仍然在 positive orbit 上显著落后，这继续支持 schema shortcut 诊断
- `Qwen3-4B` 仍然表现为“更保守但更准”：
  `CAA=0.654` 高于 `0.6B`，但 coverage 从 `0.846` 降到 `0.615`
- audited `NOS` 依然不高：
  `0.6B = 0.300`，`4B = 0.400`
  这说明 proposal 里“该稳时稳、该变时变是不同能力”这一主张仍然成立

### What Changed Relative To Pre-Audit
- 旧主表混入了 10 个 under-specified view，污染了 clean / positive / negative 的解释
- 新主表把这些 view 挪到 `ambiguous split`，因此当前分数更适合支持 proposal 机制判断
- 但这不是放宽标准：
  真正被放宽的是 evaluator 自己的噪声，不是模型任务本身

### Status
- superseded by the expanded audited suite below

## 2026-03-09 Expanded Unambiguous Near-Orbit Seed Suite

### Goal
补入绝对时间的 reminder / calendar case，扩大 `unambiguous core` 的 near-orbit 样本量，减少 `NOS` 被少量边界样本主导的问题。

### New Cases
- `reminder_tax_form_absolute`
- `calendar_toolshift_sync_absolute`

### Updated Split
- `core = 38`
- `ambiguous = 10`
- `impossible = 8`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --output-dir artifacts/seed_pilot_audited_v2`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --device-map cuda:0 --output-dir artifacts/qwen_seed_pilot_0p6b_v2`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --device-map auto --output-dir artifacts/qwen_seed_pilot_4b_v2`

### Main Table

| Model / Agent | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.789 |
| Lexical shortcut | 0.316 | 0.833 | 0.278 | 0.143 | 0.000 | 0.684 |
| Description grounded | 0.605 | 1.000 | 0.500 | 0.571 | 0.167 | 1.000 |
| Qwen3-0.6B thinking | 0.447 | 0.333 | 0.556 | 0.357 | 0.333 | 0.684 |
| Qwen3-4B thinking | 0.526 | 0.667 | 0.500 | 0.500 | 0.333 | 0.447 |

### Interpretation
- 扩样后，near-orbit 指标变得更有分辨率：
  `description_grounded NOS = 0.571`，高于此前的小主表结果
- `Qwen3-4B` 仍然比 `0.6B` 更敏感也更保守：
  `NOS 0.357 -> 0.500`，但 coverage `0.684 -> 0.447`
- `Qwen3-4B` 没有在 positive orbit 上同步变强：
  `CAA+` 仍只有 `0.500`
- 这进一步支持 proposal：
  `positive invariance` 和 `near-orbit sensitivity` 是不同能力，不会被更大模型自动统一解决

### Failure Modes Exposed By New Cases
- 绝对时间样本让 tool choice 更清楚，但暴露出更细的 argument grounding 失败：
  模型会把 `datetime + timezone` 混写进一个字段
- `reminder_tax_form_absolute` 上，两个 Qwen 都明显更倾向 abstain，说明 reminder 类 slot grounding仍弱
- `calendar_toolshift_sync_absolute` 上，0.6B 偶尔能在 `positive_combo` 通过，但 clean/rename/paraphrase 仍不稳，说明不是简单的字符串重命名问题

### Runtime Note
- `Qwen3-4B` 在扩样后的 suite 上单次全量运行约 10 分钟量级。

## 2026-03-09 Deterministic Temporal Canonicalization

### Goal
修正 absolute-time 样本中的 deterministic slot-boundary 伪失败：模型把 `ISO datetime + timezone` 合并写进 `*_datetime` 字段，而不是拆成 `*_datetime` 与 `timezone` 两个参数。

### Implementation
- 在 canonicalizer 中新增严格模式：
  仅当工具同时存在 `*_datetime` 与 `timezone` 参数，且输出匹配 `ISO datetime + IANA timezone / UTC±hh:mm` 时，才做 deterministic split。
- 代码见 `src/toolshift/eval.py`
- 重判工具修正为重新走 canonicalizer，而不是复用旧的 `predicted_action`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/rejudge_saved_records.py --records artifacts/qwen_seed_pilot_0p6b_v2/records.json --output-dir artifacts/qwen_seed_pilot_0p6b_v2_rejudged_temporal`
- `PYTHONPATH=src python scripts/rejudge_saved_records.py --records artifacts/qwen_seed_pilot_4b_v2/records.json --output-dir artifacts/qwen_seed_pilot_4b_v2_rejudged_temporal`

### Results

| Model | Before CAA | After CAA | Before CAA_clean | After CAA_clean | Before CAA+ | After CAA+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-0.6B thinking | 0.447 | 0.526 | 0.333 | 0.500 | 0.556 | 0.667 |
| Qwen3-4B thinking | 0.526 | 0.526 | 0.667 | 0.667 | 0.500 | 0.500 |

具体被修正的 view：
- `reminder_tax_form_absolute::positive_paraphrase`
- `calendar_toolshift_sync_absolute::clean`
- `calendar_toolshift_sync_absolute::positive_paraphrase`

### Interpretation
- 这次 canonicalization 修复没有改变 4B，说明 4B 当前主要问题不在 slot-boundary，而在真实的保守决策 / refusal。
- 0.6B 的提升完全来自 deterministic temporal split，说明之前有一部分 absolute-time 失败并不是 proposal 关心的语义失败，而是 canonicalizer 太死。
- 这使得当前主表更接近 proposal 的 thesis：
  `deterministic canonicalizer + deterministic contract verifier` 应该尽量剥离 schema-surface 级噪声。

## 2026-03-09 Matched-Budget AugOnly vs SCC-lite Pilot

### Goal
在不改 evaluator 的前提下，第一次把 proposal 的方法层主张落成可复现 pilot：
同一个 frozen encoder、同一批 audited seed data、同一训练预算，只比较 `AugOnly` 与 `SCC-lite` 是否有独立增量。

### Method
- encoder: frozen `Qwen3-Embedding-0.6B`
- policy: linear action bottleneck + control head + tool head
- `AugOnly`: `L_ctl + L_ce`
- `SCC-lite`: `L_ctl + L_ce + lambda_inv * L_inv + lambda_ctr * L_ctr`
- execution: deterministic argument renderer，继续复用现有 `CAA / POC / NOS`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --output-dir artifacts/matched_budget_pilot_v2 --seeds 0 1 --torch-threads 8`

### Artifacts
- `artifacts/matched_budget_pilot_v2/summary.json`
- `artifacts/matched_budget_pilot_v2/records.json`

### Main Results

#### 1. Combo Holdout
训练时移除 `positive_combo`，其余 audited core main examples 全保留。

| Method | CAA | CAA+ | NOS | POC | Coverage | Action-State Similarity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.974 | 0.944 | 1.000 | 0.833 | 0.789 | 0.974 |
| SCC-lite | 0.974 | 0.944 | 1.000 | 0.833 | 0.789 | 0.970 |

#### 2. Case-Holdout CV
按 `case_id` 做 8-fold case holdout；每个 fold 只在其他 case 的 audited core main examples 上训练。

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Action-State Similarity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.237 | 0.000 | 0.000 | 0.643 | 0.000 | 0.605 | 0.972 |
| SCC-lite | 0.237 | 0.000 | 0.000 | 0.643 | 0.000 | 0.605 | 0.963 |

### Interpretation
- 在当前 fair pilot 设置下，`SCC-lite` 没有观察到相对 `AugOnly` 的独立增量。
- `combo_holdout` 已经几乎饱和：
  当前 seed suite 对 frozen embedding policy 来说太容易，无法支撑 proposal 想要的 matched-budget 方法区分。
- `case_holdout_cv` 又明显过难：
  `CAA_clean = 0.0`、`CAA+ = 0.0`，但 `NOS = 0.643`，说明模型主要学到了保守 control，而不是可迁移的 tool semantics。
- `SCC-lite` 的 action-state similarity 也没有高于 `AugOnly`：
  当前 pilot 不支持 proposal 的 `SCC -> action-state more invariant -> OOD robustness up` 机制链。

### Hyperparameter Sanity Check
- 初始运行使用 `lambda_inv = 0.5`、`lambda_ctr = 0.5`，产物在 `artifacts/matched_budget_pilot/`
- 该设置会把 `SCC-lite` 推向更保守的控制：
  `combo_holdout` 上从 `AugOnly CAA = 0.974` 掉到 `SCC-lite CAA = 0.947`
- 将权重降到 `0.1 / 0.1` 后，`SCC-lite` 与 `AugOnly` 持平，而不是更差
- 因此 `artifacts/matched_budget_pilot/` 视为 superseded sanity run，当前主结果以 `artifacts/matched_budget_pilot_v2/` 为准

### Decision
- 当前可以排除一种乐观解释：
  不是“只要把 SCC-lite 接上 frozen embedding，就会在 seed suite 上自然超过 augmentation”
- proposal 主线没有被否掉，但下一步必须换更有效的 split：
  当前 seed suite 在 matched-budget 上同时暴露了 `easy split saturation` 和 `hard split collapse`

## 2026-03-09 Richer Same-Family Synthetic Suite

### Goal
补一个比 8-case seed 更有区分度的 synthetic split，让 matched-budget 比较不再卡在“combo 太易、case-holdout 太难”的死区。

### Implementation
- 新增生成器：`scripts/generate_family_benchmark.py`
- 从 `data/seed_benchmark.json` 复用 canonical tools，派生 18 个 unambiguous cases
- 覆盖 6 个 primary tool families，每个 family 3 个 cases：
  `weather / finance / documents / email / reminders_absolute / calendar_absolute`
- 自动生成 `data/family_audit.json`，把所有 `negative_deprecate` 固定为 `abstain-only`
- benchmark loader 现在会优先解析同 stem 的 audit 文件，因此 `family_benchmark.json -> family_audit.json` 可自动拾取

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/generate_family_benchmark.py`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_seed_pilot`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget --seeds 0 1 --torch-threads 8`

### Benchmark Stats
- `cases = 18`
- `examples = 126`
- `core main examples = 108`
- `impossible = 18`
- `ambiguous = 0`

### Heuristic Baselines

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.833 |
| Lexical shortcut | 0.287 | 0.241 | 0.139 | 0.000 | 0.694 |
| Description grounded | 0.639 | 0.556 | 0.639 | 0.167 | 0.935 |

这说明 richer family suite 仍然保留了 proposal 关心的 shortcut 诊断信号，不是“扩大数据后就失去分辨率”。

### Matched-Budget Main Results

#### 1. Combo Holdout

| Method | CAA | CAA+ | NOS | POC | Coverage | Action-State Similarity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.972 | 0.944 | 1.000 | 0.833 | 0.833 | 0.964 |
| SCC-lite | 0.972 | 0.944 | 1.000 | 0.833 | 0.833 | 0.962 |

#### 2. Same-Family Case Holdout CV
这里的 `case_holdout_cv` 已不再是跨-family 全新 case，因为每个 primary tool family 有 3 个 cases；因此它更接近 proposal 需要的 same-family OOD。

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Action-State Similarity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.880 | 0.861 | 0.944 | 0.792 | 0.833 | 0.852 | 0.960 |
| SCC-lite | 0.880 | 0.861 | 0.944 | 0.792 | 0.833 | 0.852 | 0.954 |

### Factorized Observations
- `case_holdout_cv` 下，`positive_rename` 与 `positive_combo` 都达到 `18/18`
- `positive_paraphrase` 为 `15/18`
- `clean` 为 `15/18`
- hardest families 是 `weather` 与 `finance`

这说明 richer split 已经比旧 seed 更接近“中等难度”：
不是全面崩掉，而是集中暴露在少数 family 和 `paraphrase / clean` 上。

### Interpretation
- richer same-family split 成功修复了旧 seed 的核心问题：
  `case_holdout_cv` 不再出现 `CAA_clean = 0`、`CAA+ = 0` 的整体崩塌。
- 但 `SCC-lite` 仍然没有超过 `AugOnly`：
  不论 `combo_holdout` 还是 same-family `case_holdout_cv`，两者主指标完全持平，且 `action-state similarity` 还略低。
- 因此当前可以更强地说：
  `没有 gap` 不能再简单归因于 “旧 split 太差”；至少在这个 richer synthetic pilot 上，当前 `SCC-lite` 目标还没有带来独立增量。

### Decision
- richer family suite 现在可以作为后续 factorized / same-family synthetic 主工作台
- proposal 主线仍对齐，但方法学 claim 仍未成立：
  下一步应优先尝试更强的 action bottleneck / slot head，或者进入 real evolution split，而不是继续只调当前 `L_inv / L_ctr` 权重

## 2026-03-10 Family-Holdout OOD On Richer Synthetic Suite

### Goal
把 richer family suite 从 same-family case holdout 再推进到更困难的 `family-holdout OOD`，检验当前 `SCC-lite` 是否会在跨-family synthetic OOD 上出现独立增量。

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_v2 --seeds 0 1 --torch-threads 8`

### Artifacts
- `artifacts/family_matched_budget_v2/summary.json`
- `artifacts/family_matched_budget_v2/records.json`

### Main Results

| Regime | Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Action-State Similarity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| combo_holdout | AugOnly | 0.972 | 1.000 | 0.944 | 1.000 | 0.833 | 0.833 | 0.964 |
| combo_holdout | SCC-lite | 0.972 | 1.000 | 0.944 | 1.000 | 0.833 | 0.833 | 0.962 |
| case_holdout_cv | AugOnly | 0.880 | 0.861 | 0.944 | 0.792 | 0.833 | 0.852 | 0.960 |
| case_holdout_cv | SCC-lite | 0.880 | 0.861 | 0.944 | 0.792 | 0.833 | 0.852 | 0.954 |
| family_holdout_cv | AugOnly | 0.181 | 0.000 | 0.000 | 0.542 | 0.000 | 0.755 | 0.972 |
| family_holdout_cv | SCC-lite | 0.185 | 0.000 | 0.000 | 0.556 | 0.000 | 0.755 | 0.967 |

### Interpretation
- `family_holdout_cv` 证明 richer family suite 里确实存在真正困难的 synthetic OOD：
  一旦整个 primary tool family 被拿掉，当前 frozen-embedding policy 的 `CAA_clean` 和 `CAA+` 都掉到 `0.0`。
- 因而 richer suite 现在形成了一个更合理的难度梯度：
  `combo_holdout` 近饱和 -> `case_holdout_cv` 中等难度 -> `family_holdout_cv` 真正困难
- `SCC-lite` 确实出现了一个很小的数字增量：
  `CAA 0.181 -> 0.185`，`NOS 0.542 -> 0.556`
- 但这个增量不支持 proposal 的强方法 claim：
  它没有改善 `CAA_clean / CAA+ / POC`，而且 `action-state similarity` 反而略低

### Where The Tiny Gain Comes From
- 对 `seed_0`，`AugOnly` 与 `SCC-lite` 的 family-holdout 结果完全相同
- 对 `seed_1`，唯一差异是：
  `email_demo_confirmation::negative_deprecate`
  `AugOnly -> ask_clarification`，`SCC-lite -> abstain`
- 也就是说，这个正增量只来自一个 `negative_deprecate` control 决策，而不是跨-family tool semantics 或 positive orbit invariance

### Decision
- 这轮更强地说明：当前 `SCC-lite` 还没有学到 proposal 想要的 semantic invariance / sensitivity 机制
- 但 benchmark 路线是对的：
  richer family suite 现在已经能给出 `easy / medium / hard` 三档 synthetic OOD
- 下一步不该继续围绕这点 `NOS` 微增量做文章，而应进入：
  1. factorized family-holdout 诊断
  2. 更强的 action bottleneck / slot head
  3. real evolution split

## 2026-03-10 Factorized Diagnosis For Family Holdout

### Goal
把 `family_holdout_cv` 的失败从总分拆成显式错误类型，确认当前瓶颈到底在 `tool choice / argument grounding / control policy` 哪一层，并据此决定 proposal 下一步该改哪里。

### Implementation
- 新增可复用诊断模块：`src/toolshift/diagnostics.py`
- 新增离线诊断脚本：`scripts/diagnose_saved_records.py`
- 诊断基于已保存的 `records.json`，不需要重跑模型
- taxonomy 固定区分：
  `correct_execute / correct_non_execute / missed_execute_{abstain|ask_clarification} / wrong_non_execute_policy / wrong_tool_choice / argument_grounding_error / invalid_execute_contract`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/family_matched_budget_v2/records.json --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_v2_diagnostics`

### Artifacts
- `artifacts/family_matched_budget_v2_diagnostics/summary.json`
- `artifacts/family_matched_budget_v2_diagnostics/summary.md`

### Main Findings

#### 1. Same-Family `case_holdout_cv` 还在学语义，不只是保守拒绝

| Method | Admissible | Execute Rate | Correct Execute | Tool Choice Error | Control Policy Error |
| --- | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.880 | 0.667 | 133 | 11 | 15 |
| SCC-lite | 0.880 | 0.667 | 133 | 11 | 15 |

- `case_holdout_cv` 的主要错误不是 argument/contract，而是：
  `wrong_tool_choice = 11`，`control_policy_error = 15`
- factorized 到 transform 后：
  - `positive_rename = 36/36 correct_execute`
  - `positive_combo = 36/36 correct_execute`
  - `clean` 主要掉在 `missed_execute_ask_clarification = 5`
  - `positive_paraphrase` 主要掉在 `missed_execute = 6`
  - `negative_contract` 的主要问题是 `wrong_tool_choice = 9`

这说明 same-family OOD 下，模型仍然会执行工具，剩余难点是少量 description / contract grounding 和 near-orbit 误执行。

#### 2. Cross-Family `family_holdout_cv` 是纯 control collapse，不是 wrong tool / wrong args

| Method | Admissible | Execute Rate | Correct Execute | Tool Choice Error | Argument/Contract Error | Control Policy Error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.181 | 0.000 | 0 | 0 | 0 | 177 |
| SCC-lite | 0.185 | 0.000 | 0 | 0 | 0 | 176 |

- 两个方法在 `family_holdout_cv` 上的 `execute_rate` 都是 `0.000`
- 所有 `clean / positive_rename / positive_paraphrase / positive_combo` 样本都被错判成 `abstain` 或 `ask_clarification`
- 当前没有任何 `wrong_tool_choice`、`argument_grounding_error`、`invalid_execute_contract`
- 也就是说，`family_holdout_cv` 下的失败并不是“选错工具”，而是“从不尝试执行 held-out family”

factorized 到 transform：
- `clean`：`missed_execute_abstain = 8`，`missed_execute_ask_clarification = 28`
- `positive_rename`：`missed_execute_ask_clarification = 32`，`missed_execute_abstain = 4`
- `positive_paraphrase`：`missed_execute_ask_clarification = 24`，`missed_execute_abstain = 12`
- `positive_combo`：`missed_execute_ask_clarification = 30/31`，`missed_execute_abstain = 6/5`
- 6 个 primary families 的 aggregate `execute_rate` 全部为 `0.0`

#### 3. `SCC-lite` 的微小增量仍然只是 negative control policy

- `SCC-lite` 相对 `AugOnly` 的唯一变化仍然在 `negative_deprecate`
- 诊断后可见：`wrong_non_execute_policy` 从 `33 -> 32`，`correct_non_execute` 从 `39 -> 40`
- 这不是 tool semantics，也不是 argument grounding；它只是把一条 `ask_clarification` 改成了 admissible `abstain`

### Decision
- 这轮把下一步方向收紧了：
  当前最需要改的不是 `slot head`，因为 family-holdout 下根本没有进入 execute / argument 阶段
- 更贴 proposal 的下一步应优先尝试：
  1. 更强的 `execute-vs-non-execute` semantic trigger / action bottleneck
  2. 保留现有 factorized 诊断作为新方法的验收面板
  3. 再决定是否进入 real evolution split 或继续扩 synthetic OOD

## 2026-03-10 Execute-Gate Iteration On Family Holdout

### Goal
在 richer synthetic `family_holdout_cv` 上，直接验证“当前主误差是不是 execute gate collapse”，并尝试一个能把 `execute_rate` 从 `0.0` 拉起来的新方法。

### Implementation
- 新增 `prototype execute gate`：
  在训练后的 action-state 上拟合 `execute / non-execute` prototypes，并用它替代原 control head 的 execute 判定
- 新增 `semantic_gate`：
  直接用 frozen encoder 计算 `request ↔ visible tool contract` 的语义相似度，并按 train fold 校准 execute threshold
- `scripts/run_matched_budget_pilot.py` 现在支持 `--methods` / `--regimes`
- 新增 `scripts/diagnose_saved_records.py` 继续作为固定验收面板

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_proto_gate_smoke --methods aug_only scc_lite aug_proto_gate scc_proto_gate --regimes family_holdout_cv --seeds 0 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/family_matched_budget_proto_gate_smoke/records.json --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_proto_gate_smoke_diagnostics --regime family_holdout_cv`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_semantic_gate --methods aug_only scc_lite semantic_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/family_matched_budget_semantic_gate/records.json --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_semantic_gate_diagnostics --regime family_holdout_cv`

### Prototype Gate Smoke: Negative Result
- `aug_proto_gate` 与 `scc_proto_gate` 在 `family_holdout_cv` 上都未能把 `execute_rate` 从 `0.0` 拉起
- `aug_proto_gate`：
  `CAA=0.167`，`CAA+=0.000`，`NOS=0.500`，`POC=0.000`
- `scc_proto_gate`：
  `CAA=0.176`，`CAA+=0.000`，`NOS=0.528`，`POC=0.000`
- factorized 诊断显示：它们和 baseline 一样，错误仍然 100% 落在 control policy，而不是 tool choice / args

这说明：
`action-state prototype gate` 本身不足以修复跨-family execute collapse；问题不只是 control head 的线性可分性。

### Semantic Gate: Formal Two-Seed Result

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.181 | 0.000 | 0.000 | 0.542 | 0.000 | 0.755 |
| SCC-lite | 0.185 | 0.000 | 0.000 | 0.556 | 0.000 | 0.755 |
| SemanticGate | 0.806 | 1.000 | 0.981 | 0.444 | 0.944 | 0.852 |

### Factorized Diagnosis
- `semantic_gate` aggregate：
  - `execute_rate = 0.824`
  - `correct_execute = 142`
  - `wrong_tool_choice = 36`
  - `correct_non_execute = 32`
  - `control_policy_error = 6`
- transform breakdown：
  - `clean = 36/36 correct_execute`
  - `positive_rename = 36/36 correct_execute`
  - `positive_paraphrase = 36/36 correct_execute`
  - `positive_combo = 34/36 correct_execute`, 仅 `2` 条 `missed_execute_ask_clarification`
  - `negative_contract = 36/36 wrong_tool_choice`
  - `negative_deprecate = 32/36 correct_non_execute`, `4` 条 `wrong_non_execute_policy`

### Interpretation
- 这轮第一次真正证明了前一节 diagnosis 的核心判断：
  `family_holdout_cv` 的 baseline 失败主要是 execute gate collapse，而不是 tool semantics 完全不可恢复
- 一旦 gate 直接读 `request ↔ visible tool contract`，cross-family `clean / positive orbit` 基本被救回：
  `CAA_clean = 1.0`，`CAA+ = 0.981`
- 但错误也发生了明确迁移：
  现在主失败不再是“不敢执行”，而是 `negative_contract` 上的系统性误执行

### Decision
- 这轮研究主线继续对齐 proposal，但结论需要写准确：
  `semantic_gate` 证明了 visible contract semantics 能显著缓解 cross-family OOD 的 execute collapse
- 但它还不是 proposal 的最终方法胜利，因为：
  - 当前提升来自一个 targeted semantic gate，而不是公平 matched-budget 下的 `SCC > AugOnly`
  - `negative_contract` 仍然全错，说明 contract-aware inhibition 还没有学会
- 下一步应收敛到：
  1. 把 `semantic_gate` 与 contract mutation / deprecate signal 结合
  2. 专门优化 `negative_contract` 的 inhibition，而不是再纠结 `clean / positive`
  3. 再决定是否把这条方法线带入 real evolution split

## 2026-03-10 Contract-Aware Inhibition On Top Of Semantic Gate

### Goal
在 `semantic_gate` 已经救回 cross-family `clean / positive` 的基础上，继续解决它在 `negative_contract` 上的系统性误执行，验证 `contract-aware inhibition` 是否能把错误从 `wrong_tool_choice` 压成 admissible non-execute。

### Implementation
- 在 `SemanticGateAgent` 上新增 `contract_aware_inhibition` 开关：
  执行前先检查 top active tool 的 rendered contract 是否与当前 slot values 兼容；若不兼容，则直接输出 `ask_clarification`
- 新增方法名：`semantic_contract_gate`
- 兼容性规则完全读取 schema-visible signal：
  `arg_type / enum_values / minimum / maximum / required`
- 对应逻辑位于 `src/toolshift/embedding_policy.py`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_contract_gate --methods aug_only scc_lite semantic_gate semantic_contract_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/family_matched_budget_contract_gate/records.json --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_contract_gate_diagnostics --regime family_holdout_cv`

### Main Results

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.181 | 0.000 | 0.000 | 0.542 | 0.000 | 0.755 |
| SCC-lite | 0.185 | 0.000 | 0.000 | 0.556 | 0.000 | 0.755 |
| SemanticGate | 0.806 | 1.000 | 0.981 | 0.444 | 0.944 | 0.852 |
| SemanticContractGate | 0.972 | 1.000 | 0.981 | 0.944 | 0.944 | 0.852 |

### Factorized Diagnosis
- `semantic_gate`
  - `execute_rate = 0.824`
  - `wrong_tool_choice = 36`
  - 这 `36` 条全部来自 `negative_contract`
- `semantic_contract_gate`
  - `execute_rate = 0.657`
  - `wrong_tool_choice = 0`
  - `correct_non_execute = 68`
  - `negative_contract = 36/36 correct_non_execute`
  - `negative_deprecate = 32/36 correct_non_execute`, 剩余 `4` 条仍是 `wrong_non_execute_policy`

transform breakdown for `semantic_contract_gate`：
- `clean = 36/36 correct_execute`
- `positive_rename = 36/36 correct_execute`
- `positive_paraphrase = 36/36 correct_execute`
- `positive_combo = 34/36 correct_execute`, 仅 `2` 条 `missed_execute_ask_clarification`
- `negative_contract = 36/36 correct_non_execute`
- `negative_deprecate = 32/36 correct_non_execute`, `4` 条 policy mismatch

### Interpretation
- 这轮是 proposal-aligned 的强机制证据：
  一旦把 visible contract semantics 同时接入 `execute` 和 `inhibition`，`family_holdout_cv` 不再是“要么不敢执行、要么乱执行”的两难
- 最关键的变化不是 overall CAA 本身，而是 error mass 的迁移：
  `negative_contract` 从 `36/36 wrong_tool_choice` 直接变成 `36/36 correct_non_execute`
- 同时 `clean / positive` 基本保持不动：
  `CAA_clean = 1.0`、`CAA+ = 0.981`、`POC = 0.944`
- 这说明 richer synthetic family-holdout 上，proposal 想要的两种能力已经首次在同一方法里同时出现：
  `该稳时稳` 和 `该变时变`

### Limits
- 这仍然不是 proposal 的最终主结论：
  - 当前方法是 targeted `semantic_contract_gate`，不是 matched-budget `SCC > AugOnly`
  - 结果仍停留在 synthetic suite，尚未进入 `real evolution split`
  - `negative_deprecate` 还剩 4 条 `policy mismatch`

### Decision
- 这轮已经把 richer synthetic `family_holdout_cv` 基本打穿，继续在同一 synthetic split 上小修小补的边际价值开始下降
- 更对齐 proposal 的下一步是：
  1. 把 `semantic_contract_gate` 带入 `real evolution split`
  2. 或先补一小批真实 schema diff / version diff 审计数据，再复用当前 diagnosis pipeline

## 2026-03-10 Real Evolution Split V1 Bootstrap

### Goal
把研究从 synthetic family suite 推进到首版 `real evolution split`，要求：
- 数据来自官方 changelog / reference，可审计
- benchmark 支持显式 versioned views，而不是继续依赖 synthetic transform 生成
- 现有 `run_seed_pilot.py` / `run_matched_budget_pilot.py` / `diagnose_saved_records.py` 可直接复用

### Implementation
- 在 `src/toolshift/schema.py` 上新增 `SchemaView.from_dict`
- 在 `src/toolshift/benchmark.py` 上新增显式 `views` 加载分支，并为 `TaskCase` 增加 `family_tag`
- `scripts/run_matched_budget_pilot.py` 的 `family_holdout_cv` 现在优先按 `case.family_tag` 分组，而不是硬编码 `primary_action.tool_id`
- 新增生成脚本：
  `scripts/generate_real_evolution_benchmark.py`
- 新增数据与审计产物：
  - `data/real_evolution_benchmark.json`
  - `data/real_evolution_audit.json`
  - `history/real_evolution_audit.md`
- 新增回归测试：
  `tests/test_real_evolution_benchmark.py`

real split v1 规模：
- `6 cases`
- `12 views`
- `3 vendor families`：`notion / slack / stripe`
- `12 core / 0 ambiguous / 0 impossible`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout --methods aug_only semantic_contract_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_diagnostics --regime family_holdout_cv`

### Heuristic Baselines On Real Split

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.917 |
| LexicalShortcut | 0.667 | 0.667 | 0.667 | 0.667 | 0.917 |
| DescriptionGrounded | 0.750 | 1.000 | 0.000 | 1.000 | 1.000 |

这说明 real split v1 已经有信息量：
- `description_grounded` 在 real positive migrations 上保持满分
- 但在 real negatives 上直接退化成 `NOS = 0.0`
- 也就是说，real split 开始暴露 synthetic suite 没完全压出来的 failure mode

### Real Family-Holdout Result

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Action-State Sim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.167 | 0.000 | 0.000 | 0.667 | 0.000 | 1.000 | 0.986 |
| SemanticContractGate | 0.833 | 1.000 | 1.000 | 0.333 | 1.000 | 0.917 | na |

### Factorized Diagnosis
- `AugOnly`
  - `execute_rate = 0.000`
  - `ask_clarification_rate = 1.000`
  - `group_counts = {"control_policy_error": 20, "correct": 4}`
  - 依然是 familiar 的 `execute collapse`
- `SemanticContractGate`
  - `execute_rate = 0.917`
  - `group_counts = {"correct": 20, "tool_choice_error": 4}`
  - `clean = 12/12 correct_execute`
  - `positive_version_migration = 6/6 correct_execute`
  - `negative_deprecate = 2/2 correct_non_execute`
  - `negative_search_replacement = 0/2`，全部 `wrong_tool_choice`
  - `negative_removed_capability = 0/2`，全部 `wrong_tool_choice`

代表性失败：
- `notion_list_shared_databases::negative_search_replacement`
  `semantic_contract_gate` 仍执行 `notion.databases.list_shared`
- `stripe_list_customers_total_count::negative_removed_capability`
  `semantic_contract_gate` 仍执行 `stripe.customers.list_with_total_count`

### Interpretation
- 这轮是 proposal-aligned 的真实世界 bootstrap：
  `semantic_contract_gate` 已经能在 vendor-family holdout 下保持 `clean / positive` 全对，说明 synthetic 上学到的正向 invariance 不是纯 benchmark 记忆
- 但 real negatives 暴露了新的缺口：
  当前 inhibition 主要依赖 `required / type / enum / range / deprecated` 这类 schema-visible hard signal
- 一旦 capability removal 主要体现在 tool description 或 endpoint replacement semantics，而不是 arg-level incompatibility，当前 gate 就会误执行
- `AugOnly` 的 `action_state_similarity = 0.986` 与 `CAA_clean = 0.0` 再次说明：
  `representation 看起来稳定` 不能替代真实 OOD 行为验证

### Decision
- real evolution split 已经正式接通，后续不应再回到“只有 synthetic”的状态
- 下一步最该做的是：
  1. 在 `semantic_contract_gate` 上加入 `description-aware capability gap / replacement inhibition`
  2. 扩 real split 的 audited cases，尤其补更多 `removed capability / replacement semantics` negatives
  3. 对部分 real cases 加执行级 sanity check，避免只停在 schema-side reconstruction

## 2026-03-10 Description-Aware Capability Gate On Real Split

### Goal
在 `semantic_contract_gate` 已经保持 real `clean / positive` 的前提下，继续修复 real negative 里的 `replacement semantics / removed capability` 误执行，并确认不会破坏上一轮 synthetic family-holdout 已成立的结果。

### Implementation
- 在 `src/toolshift/embedding_policy.py` 上新增：
  - `description_aware_inhibition` 开关
  - `semantic_capability_gate` 方法名
  - `_tool_has_description_capability_gap(...)`，用显式 negative cue + request/description capability token overlap 检测 description-level contract gap
- 新增 real negative capability-gap 单测到 `tests/test_embedding_policy_utils.py`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_capability_gate --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_capability_gate/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_capability_gate_diagnostics --regime family_holdout_cv`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_capability_gate --methods semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`

### Real Split Main Result

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.167 | 0.000 | 0.000 | 0.667 | 0.000 | 1.000 |
| SemanticContractGate | 0.833 | 1.000 | 1.000 | 0.333 | 1.000 | 0.917 |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.917 |

### Factorized Diagnosis
- `semantic_contract_gate`
  - `execute_rate = 0.917`
  - `group_counts = {"correct": 20, "tool_choice_error": 4}`
  - 这 `4` 条全部来自：
    - `notion_list_shared_databases::negative_search_replacement`
    - `stripe_list_customers_total_count::negative_removed_capability`
- `semantic_capability_gate`
  - `execute_rate = 0.750`
  - `group_counts = {"correct": 24}`
  - transform breakdown：
    - `clean = 12/12 correct_execute`
    - `positive_version_migration = 6/6 correct_execute`
    - `negative_deprecate = 2/2 correct_non_execute`
    - `negative_search_replacement = 2/2 correct_non_execute`
    - `negative_removed_capability = 2/2 correct_non_execute`

### Synthetic Sanity Check
- richer synthetic `family_holdout_cv` 未回退：
  - `SemanticContractGate = SemanticCapabilityGate`
  - `CAA = 0.972`
  - `CAA+ = 0.981`
  - `NOS = 0.944`
  - `POC = 0.944`

### Interpretation
- 这轮证明上一轮 real split 的剩余缺口确实不是 execute gate 本身，而是 `description-level capability gap`
- 一旦把 description 里的 negative cue 和 request capability token 显式接入 inhibition，当前 real fixed panel 上的剩余 `wrong_tool_choice` 可以全部压成 admissible non-execute
- 同时 synthetic sanity 不变，说明这次修复不是简单拿 real panel 做 case-specific tradeoff

### Limits
- 当前 real split 只有 `6 cases / 12 views`，已经被新方法打穿；它现在更适合作为 fixed regression panel，而不是主结论终点
- 当前 `description-aware` 仍然是显式 heuristic，不是 proposal 最终形态的 learned capability-gap model

### Decision
- 下一步不应继续在这个 6-case panel 上微调
- 更对齐 proposal 的方向是：
  1. 扩 real evolution split，尤其补更多真实 `replacement semantics / removed capability` 样本
  2. 对部分 case 做执行级 sanity check
  3. 再判断这套 description-aware inhibition 是否稳定，而不是只在当前 panel 上满分

## 2026-03-10 Expanded Real Evolution Split V2

### Goal
把 real split 从一个容易饱和的 `6-case / 12-view` fixed panel 扩成更像真实研究集的平衡版本，并检验 `semantic_capability_gate` 是否仍然成立。

### Implementation
- 扩充 `scripts/generate_real_evolution_benchmark.py`
- real split 现已扩到：
  - `12 cases`
  - `24 views`
  - `25 official source anchors`
  - `3 vendor families x 4 cases`
- 新增的真实 case 包括：
  - Notion：`database.query -> data_source.query`
  - Notion：`database parent -> data_source parent`
  - Slack：`channels.create -> conversations.create`
  - Slack：`channels.list -> conversations.list`
  - Stripe：`subscription_data[coupon] -> discounts`
  - Stripe：`subscription source removed`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v2`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v3 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v3/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v3_diagnostics --regime family_holdout_cv`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_capability_gate_v2 --methods semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`

### Heuristic Baselines On Expanded Real Split

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.958 |
| LexicalShortcut | 0.667 | 0.714 | 0.600 | 0.714 | 0.958 |
| DescriptionGrounded | 0.750 | 1.000 | 0.000 | 1.000 | 1.000 |

这说明扩样后 real split 仍然保留了 proposal 需要的诊断信号：
- positive migrations 仍不难
- 真实 negative replacements / removals 依然会把 naive grounding 方法打穿

### Expanded Real Family-Holdout Result

| Method | CAA | CAA_clean | CAA+ | CAA_negative | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.167 | 0.000 | 0.000 | 0.800 | 0.800 | 0.000 | 0.938 |
| SemanticContractGate | 0.833 | 1.000 | 1.000 | 0.200 | 0.200 | 1.000 | 0.958 |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.958 |

### Factorized Diagnosis
- `AugOnly`
  - `execute_rate = 0.000`
  - `group_counts = {"control_policy_error": 40, "correct": 8}`
- `SemanticContractGate`
  - `group_counts = {"correct": 40, "tool_choice_error": 8}`
  - 失败都落在新增 real negatives：
    - `negative_parent_scope_change`
    - `negative_removed_capability`
    - `negative_search_replacement`
    - `negative_source_removed`
- `SemanticCapabilityGate`
  - `group_counts = {"correct": 48}`
  - transform breakdown：
    - `clean = 24/24 correct_execute`
    - `positive_version_migration = 14/14 correct_execute`
    - `negative_deprecate = 2/2 correct_non_execute`
    - `negative_parent_scope_change = 2/2 correct_non_execute`
    - `negative_removed_capability = 2/2 correct_non_execute`
    - `negative_search_replacement = 2/2 correct_non_execute`
    - `negative_source_removed = 2/2 correct_non_execute`

### Synthetic Sanity Check
- richer synthetic `family_holdout_cv` 仍然不回退：
  - `SemanticContractGate = SemanticCapabilityGate`
  - `CAA = 0.972`
  - `CAA+ = 0.981`
  - `NOS = 0.944`
  - `POC = 0.944`

### Interpretation
- 扩样后的 panel 首先暴露了一个真实新问题：
  `clause-only` 的 description detector 会漏掉 `database parent -> data_source parent`
- 修正为“negative cue 触发后，读取整段工具描述的 capability overlap”后，`semantic_capability_gate` 重新在 expanded real panel 上成立
- 这说明当前方法不是只记住最初的 6-case panel；它至少对同一 vendor families 内的新 real changes 还有外推能力

### Limits
- expanded real split 虽然更像研究集，但仍然只覆盖 `Notion / Slack / Stripe`
- 当前方法还是 explicit heuristic gate，不是 learned capability-gap model
- 继续只在这 3 家供应商内部扩样，边际价值会逐步下降

### Decision
- 下一步应该把 real split 扩到新 vendor families，或者给关键 case 加 execution-level sanity check
- 当前 `semantic_capability_gate` 可以保留为 real fixed-panel baseline，但不该被误写成 proposal 的最终方法结论

## 2026-03-10 Execution-Level Sanity On Expanded Real Split

### Goal
给 expanded real split 增加一条独立的 execution audit 证据链，验证：
- clean / positive views 的 canonical primary action 确实能在 mock environment 中满足请求
- negative views 的旧 canonical execute action 确实会在 evolved schema semantics 下失败或被阻断
- positive migrations 在 clean / positive view 间保持 effect equivalence

### Implementation
- 新增模块：
  `src/toolshift/execution_sanity.py`
- 新增 runner：
  `scripts/run_execution_sanity.py`
- 新增测试：
  `tests/test_execution_sanity.py`

mock execution state 覆盖：
- Notion：blocks / shared databases / data-source entries / page creation
- Slack：channels / group DMs / file uploads
- Stripe：customers / checkout sessions / subscriptions

执行规则不是直接重用 evaluator 分数，而是：
1. 在当前 view 上尝试执行 case 的 canonical primary action
2. 对 clean / positive 检查 request 是否被满足
3. 对 negative 检查旧 action 是否被阻断或不再满足请求
4. 对 positive 检查 clean / positive 的 effect fingerprint 是否一致

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity`

### Main Result

| Metric | Value |
| --- | ---: |
| count | 24 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |

transform breakdown：
- `clean = 12/12 pass`
- `positive_version_migration = 7/7 pass`
- `negative_deprecate = 1/1 pass`
- `negative_parent_scope_change = 1/1 pass`
- `negative_removed_capability = 1/1 pass`
- `negative_search_replacement = 1/1 pass`
- `negative_source_removed = 1/1 pass`

### Interpretation
- 这条 execution audit 说明 expanded real split 当前不是“只靠 schema 文本写出来的标签”
- 对 clean / positive，canonical primary action 的语义效果在 mock environment 中确实成立
- 对 negative，old execute action 的失败也不是 evaluator 自己拍出来的，而是会在 execution model 里触发 capability block
- 这让 real split 从“有审计来源的 schema benchmark”进一步升级成“带最小 execution sanity 的 benchmark”

### Limits
- 当前 execution harness 仍然是 deterministic mock，不是真实第三方 API
- 它的角色是 sanity check，不是替代主评测或真实在线执行

### Decision
- 下一步若继续沿 proposal 往前推，最值得做的是：
  1. 把 execution sanity 扩到新 vendor family
  2. 或为少数关键 case 接更真实的 API-level replay / smoke validation

## 2026-03-10 Add Google Drive Family To Real Split

### Goal
把 expanded real split 从 `Notion / Slack / Stripe` 扩到新的官方 vendor family，并保持：
- source-audited version/change evidence
- fixed-panel family-holdout 可复跑
- execution-level sanity 继续闭合

这轮选择了 `Google Drive`，因为官方文档同时提供了：
- positive migrations：
  - `teamDriveId / includeTeamDriveItems / supportsTeamDrives -> driveId / includeItemsFromAllDrives / supportsAllDrives`
  - `parents.insert -> files.update?addParents`
  - `parents.delete -> files.update?removeParents`
- negative near-orbit：
  - `multiple folders no longer supported; use shortcuts instead`

### Implementation
- 扩展 `scripts/generate_real_evolution_benchmark.py`：
  - 新增 `drive` source anchors、canonical tools、cases、views
- 扩展 `src/toolshift/execution_sanity.py`：
  - 新增 Drive mock state 与 deterministic semantics
- 扩展测试：
  - `tests/test_real_evolution_benchmark.py`
  - `tests/test_execution_sanity.py`
  - `tests/test_embedding_policy_utils.py`

扩容后的 real split 规模：
- `16 cases`
- `32 views`
- `34 official sources`
- `4 vendor families`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v4`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v3`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v4 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v4/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v4_diagnostics --regime family_holdout_cv`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v6 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v6/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v6_diagnostics --regime family_holdout_cv`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/family_benchmark.json --output-dir artifacts/family_matched_budget_capability_gate_v3 --methods semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`

### Heuristic Baselines On 4-Family Real Split

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.969 |
| LexicalShortcut | 0.531 | 0.500 | 0.667 | 0.500 | 0.844 |
| DescriptionGrounded | 0.719 | 1.000 | 0.167 | 1.000 | 1.000 |

### Execution Sanity On 4-Family Real Split

| Metric | Value |
| --- | ---: |
| count | 32 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |

### Initial Failure Signal (Superseded By V6)

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.156 | 0.000 | 0.833 | 0.000 | 1.000 |
| SemanticContractGate | 0.812 | 0.800 | 0.333 | 0.800 | 0.969 |
| SemanticCapabilityGate | 0.938 | 0.800 | 1.000 | 0.800 | 0.969 |

factorized diagnosis（`artifacts/real_evolution_family_holdout_v4_diagnostics`）：
- `semantic_capability_gate` 只剩 `4` 个 `control_policy_error`
- 错误全部集中在 held-out Drive 的 positive migrations：
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
- 失败模式不是 `wrong_tool_choice`，而是 `ask_clarification`

### Semantic Rescue Fix
仅改 gate 逻辑，不改 split / labels / admissible policy：
- 对 `best_active_score` 略低于 threshold 的 active tool，允许一个窄范围 execute rescue
- 条件是：
  - `contract compatible`
  - `no description capability gap`
  - `request/tool capability overlap >= 2`
  - `best-vs-second lead >= 0.01`

### Final 4-Family Real Family-Holdout Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.156 | 0.000 | 0.833 | 0.000 | 1.000 |
| SemanticContractGate | 0.875 | 1.000 | 0.333 | 1.000 | 0.969 |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.969 |

factorized diagnosis（`artifacts/real_evolution_family_holdout_v6_diagnostics`）：
- `semantic_capability_gate`
  - `admissible = 1.000`
  - `execute_rate = 0.812`
  - `group_counts = {"correct": 64}`
- `semantic_contract_gate`
  - `group_counts = {"correct": 56, "tool_choice_error": 8}`

### Synthetic Sanity Check
- richer synthetic `family_holdout_cv` 不回退：
  - `SemanticContractGate = SemanticCapabilityGate`
  - `CAA = 0.972`
  - `CAA+ = 0.981`
  - `NOS = 0.944`
  - `POC = 0.944`

### Interpretation
- Drive family 是有效扩容，不是重复旧 panel：
  它先暴露了一个此前没看到的失败面：`generic update-style positive migration` 会被 gate 低估，从而 under-execute
- 只改 benchmark description 不够，问题在 gate 本身
- 一个窄范围的 `contract-compatible + no-gap + overlap` semantic rescue 足以把这类正迁移救回
- rescue 没有打开 negative floodgate：
  real `NOS` 仍是 `1.0`
  synthetic sanity 也不回退

### Decision
- 当前 `semantic_capability_gate` 已经在 `4 vendor families / 32 views / execution sanity` 的 fixed panel 上重新闭合
- 下一步最该做的是：
  1. 再扩一个新的 real vendor family，验证 rescue 不是 Drive-specific
  2. 给少数关键 real case 补 API-level replay / smoke validation

## 2026-03-10 Add Jira Family To Real Split

### Goal
继续沿 proposal 主线把 real fixed panel 扩到新的 vendor family，并验证：
- 新 family 不是只在 benchmark 文件里存在
- heuristic baseline 的难度真的上升
- `semantic_capability_gate` 不是只对 `Notion / Slack / Stripe / Drive` 生效

这轮选用 `Jira Cloud`，因为官方 source chain 同时给出了：
- `username / userKey -> accountId` 的身份迁移
- `username -> query` 的 user-search 迁移
- `username / userKey are no longer supported` 的 legacy identifier negative

### Implementation
- 扩展 `scripts/generate_real_evolution_benchmark.py`
  - 新增 `jira` source anchors、canonical tools、cases、views
- 扩展 `src/toolshift/execution_sanity.py`
  - 新增 Jira assignee / watcher / assignable-user mock semantics
- 扩展测试：
  - `tests/test_real_evolution_benchmark.py`
  - `tests/test_execution_sanity.py`
  - `tests/test_embedding_policy_utils.py`

扩容后的 real split：
- `20 cases`
- `40 views`
- `41 official sources`
- `5 vendor families`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v5`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v4`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v7 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v7/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v7_diagnostics --regime family_holdout_cv`

### Heuristic Baselines On 5-Family Real Split

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.975 |
| LexicalShortcut | 0.500 | 0.462 | 0.714 | 0.462 | 0.875 |
| DescriptionGrounded | 0.650 | 0.846 | 0.286 | 0.846 | 1.000 |

对比 4-family panel，这次 baseline 进一步变难了：
- `LexicalShortcut` 从 `CAA 0.531 -> 0.500`
- `DescriptionGrounded` 从 `CAA 0.719 -> 0.650`
- `DescriptionGrounded` 的 `CAA+` 也从 `1.000 -> 0.846`

### Execution Sanity On 5-Family Real Split

| Metric | Value |
| --- | ---: |
| count | 40 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |

### 5-Family Real Family-Holdout Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.138 | 0.077 | 0.571 | 0.077 | 1.000 |
| SemanticContractGate | 0.875 | 1.000 | 0.286 | 1.000 | 0.975 |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.975 |

### Factorized Diagnosis
- `AugOnly`
  - `admissible = 0.138`
  - `execute_rate = 0.263`
  - `group_counts = {"control_policy_error": 51, "correct": 11, "tool_choice_error": 18}`
- `SemanticContractGate`
  - `admissible = 0.875`
  - `execute_rate = 0.950`
  - `group_counts = {"correct": 70, "tool_choice_error": 10}`
  - 新增 Jira negative `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed` 也落在 `wrong_tool_choice`
- `SemanticCapabilityGate`
  - `admissible = 1.000`
  - `execute_rate = 0.825`
  - `group_counts = {"correct": 80}`
  - by-transform：
    - `clean = 20/20 correct_execute`
    - `positive_version_migration = 13/13 correct_execute`
    - 所有 `7` 个 negatives 全部 `correct_non_execute`

### Interpretation
- Jira family 不是冗余扩样，它确实让 heuristic baseline 继续掉分
- 当前 real fixed panel 已经从 `4 families / 32 views` 扩到 `5 families / 40 views`，但 `semantic_capability_gate` 仍未回退
- 新增 Jira negative 说明 description-level capability gap 不是只对 `Notion / Stripe / Drive` 生效；它也能处理 “legacy identifier removed” 这种 privacy-driven API evolution

### Decision
- 当前 `semantic_capability_gate` 已在 `5 vendor families / 40 views / execution sanity` 的 fixed panel 上保持闭合
- 下一步最该做的是：
  1. 再加 1 个不同风格的 vendor family，继续压测
  2. 或对少数关键 real cases 增加 API-level replay / smoke validation，减少对 mock execution 的依赖

## 2026-03-10 Request-Level Replay Sanity On 5-Family Real Split

### Goal
在现有 `execution_sanity` 之外，再补一条更接近 API surface 的验证链：
- clean / positive views 不只是 effect-level 等价，还能渲染成具体的抽象 HTTP request
- negative views 不只是 “执行效果不成立”，而是在 request replay 层就应被阻断
- replay 直接复用当前 real benchmark，不另起样例集

### Implementation
- 新增模块：
  `src/toolshift/request_replay.py`
- 新增 runner：
  `scripts/run_request_replay.py`
- 新增测试：
  `tests/test_request_replay.py`

这条 replay harness 的逻辑是：
1. 复用 real benchmark 当前 view 的 rendered tool surface
2. 尝试把 case 的 canonical primary action 渲染成 provider-specific 抽象请求：
   - method
   - path
   - query
   - body
3. 对 clean / positive 检查 request 是否成功渲染
4. 对 positive 再检查 clean / positive 的 `effect_signature` 是否一致
5. 对 negative 检查 request replay 是否被 `deprecated / contract mismatch / capability gap` 阻断

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `PYTHONPATH=src python scripts/run_request_replay.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_request_replay_v1`

### Main Result

| Metric | Value |
| --- | ---: |
| count | 40 |
| pass_rate | 1.000 |
| execute_render_pass_rate | 1.000 |
| negative_block_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| emit_rate | 0.825 |

transform breakdown：
- `clean = 20/20 rendered`
- `positive_version_migration = 13/13 rendered`
- 所有 `7` 个 negatives 都是 `0/7 emitted`

### Representative Replay Evidence
- Drive `parents.insert -> files.update addParents`
  - clean:
    - `POST /drive/v2/files/file_brief/parents`
    - body = `{"id": "fld_reports"}`
  - positive:
    - `PATCH /drive/v3/files/file_brief?addParents=fld_reports`
  - 两者 `effect_signature` 相同：
    `{"op":"drive.add_parent","file_id":"file_brief","parent_id":"fld_reports"}`

- Jira `name -> accountId`
  - clean:
    - `PUT /rest/api/2/issue/ENG-7/assignee`
    - body = `{"name": "acct_alice"}`
  - positive:
    - `PUT /rest/api/3/issue/ENG-7/assignee`
    - body = `{"accountId": "acct_alice"}`
  - `effect_signature` 一致：
    `{"op":"jira.assign_user","issue_key":"ENG-7","user_ref":"acct_alice"}`

- Jira legacy identifier negative
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - replay 结果：
    - `emitted = false`
    - `reason = tool description exposes a capability gap for the original request`

### Interpretation
- 这条 request replay 说明当前 5-family real panel 已经不只是 “schema + docs + mock effect”
- 对 clean / positive，current rendered surface 确实能被渲染成合理的 provider-specific request
- 对 negative，旧 canonical execute action 在 request-shape 层就应该被拦住，而不是等到 effect 层才发现问题
- execution sanity 和 request replay 是互补的：
  - `execution_sanity` 回答 “做出来有没有正确 effect”
  - `request_replay` 回答 “当前 schema surface 下到底会发出什么请求”

### Limits
- 这仍然是 deterministic abstract request replay，不是真实在线 API 调用
- path/query/body 是研究用途的最小抽象，不追求 100% 覆盖各家 SDK/transport 细节

### Decision
- 当前 fixed panel 现在同时具备：
  1. source audit
  2. benchmark evaluation
  3. execution sanity
  4. request-level replay sanity
- 下一步最有价值的是：
  1. 选 1 到 2 个关键 case 做更真实的 API-level smoke validation
  2. 或继续扩一个新的 non-privacy real vendor family

## 2026-03-10 Official-Docs Request Smoke On 5-Family Real Split

### Goal
在 `request_replay` 之上再补一层“官方文档证据”：
- 对 selected clean / positive views，确认 replay 出来的 method/path/query/body 与官方 reference / migration guide 的关键 marker 对齐
- 对 selected negative views，确认官方文档里确实存在明确的 replacement / removal / privacy cue，且 replay 层不会错误发请求
- 保持验证成本低，不引入真实认证或在线 API 调用

### Implementation
- 复用现有模块：
  `src/toolshift/official_request_smoke.py`
- 新增 runner：
  `scripts/run_official_request_smoke.py`
- 新增测试：
  `tests/test_official_request_smoke.py`

当前 smoke panel 固定为 `7` 个高价值 real views：
- Drive
  - `drive_add_parent_to_file::clean`
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_add_file_to_second_folder::negative_shortcut_replacement`
- Jira
  - `jira_assign_issue_user_ref::clean`
  - `jira_assign_issue_user_ref::positive_version_migration`
  - `jira_search_assignable_user_query::positive_version_migration`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/run_official_request_smoke.py`
- `PYTHONPATH=src python scripts/run_official_request_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_official_request_smoke_v1`

### Main Result

| Metric | Value |
| --- | ---: |
| count | 7 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.714 |

provider breakdown：
- `drive = 3/3 pass`
- `jira = 4/4 pass`

### Representative Official-Docs Evidence
- Drive positive migration:
  - view: `drive_add_parent_to_file::positive_version_migration`
  - doc markers hit:
    - `parents.insert`
    - `files.update`
    - `addParents`
  - replayed request:
    - `PATCH /drive/v3/files/file_brief?addParents=fld_reports`

- Drive negative shortcut replacement:
  - view: `drive_add_file_to_second_folder::negative_shortcut_replacement`
  - doc markers hit:
    - `adding files to multiple folders is no longer supported. use shortcuts instead`
    - `a file can only have one parent folder`
    - `link to other files or folders on google drive`
  - replay result:
    - `emitted = false`
    - `reason = tool description exposes a capability gap for the original request`

- Jira positive migration:
  - view: `jira_assign_issue_user_ref::positive_version_migration`
  - doc markers hit:
    - `/rest/api/3/issue/{issueIdOrKey}/assignee`
    - `accountId`
  - replayed request:
    - `PUT /rest/api/3/issue/ENG-7/assignee`
    - body = `{"accountId": "acct_alice"}`

- Jira legacy identifier negative:
  - view: `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - doc markers hit:
    - `remove personal data from the api that is used to identify users`
    - `` `username` and `userKey` ``
    - `accountId`
  - replay result:
    - `emitted = false`
    - `reason = tool description exposes a capability gap for the original request`

### Interpretation
- 这条 docs-backed smoke 让 fixed panel 多了一层“官方 source 与 rendered request 是否同向”的验证，而不只是本地 abstract replay
- 它同时覆盖了：
  - positive migration 的 request-shape 迁移证据
  - negative capability-gap 的官方 removal / replacement 证据
- 当前 `5-family real panel` 的关键 Drive / Jira case 已经在：
  1. source audit
  2. benchmark evaluation
  3. execution sanity
  4. request replay
  5. official-doc smoke
  五层证据上闭合

### Limits
- 这仍然不是 authenticated live API invocation
- 文档 smoke 依赖 marker 匹配；目标是验证“官方文档确实支持当前 request/negative claim”，不是做全文抽取

### Decision
- 当前对 `Drive + Jira` 的 request-level 证据已经足够硬，可以开始挑 1 到 2 个 case 进入更真实的 API-level smoke
- 后续固定回归面板应扩成三条并行 sanity：
  1. `scripts/diagnose_saved_records.py`
  2. `scripts/run_request_replay.py`
  3. `scripts/run_official_request_smoke.py`

## 2026-03-10 Spec-Backed API Surface Smoke On 5-Family Real Split

### Goal
在 `official-doc smoke` 之上，再补一层更接近 provider machine-readable API surface 的 live 审计：
- 对 emitted requests，直接对齐官方 discovery / OpenAPI 的 method/path/query/body-key surface
- 对 negative requests，继续保留官方 removal / replacement 文档 cue，避免把 “still mentioned in spec but semantically removed” 误判成可执行
- 保持无需凭证，不伪装成真实在线变更

### Implementation
- 新增模块：
  `src/toolshift/api_surface_smoke.py`
- 新增 runner：
  `scripts/run_api_surface_smoke.py`
- 新增测试：
  `tests/test_api_surface_smoke.py`

当前 `7` 个 fixed smoke views 分成三类：
- `drive_discovery`
  - `drive_add_parent_to_file::clean`
  - `drive_add_parent_to_file::positive_version_migration`
- `jira_openapi`
  - `jira_assign_issue_user_ref::clean`
  - `jira_assign_issue_user_ref::positive_version_migration`
  - `jira_search_assignable_user_query::positive_version_migration`
- `negative_docs`
  - `drive_add_file_to_second_folder::negative_shortcut_replacement`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`

说明：
- Drive emitted requests 对齐 live discovery docs：
  - `https://www.googleapis.com/discovery/v1/apis/drive/v2/rest`
  - `https://www.googleapis.com/discovery/v1/apis/drive/v3/rest`
- Jira emitted requests 对齐 live OpenAPI JSON：
  - v2: `https://developer.atlassian.com/cloud/jira/platform/swagger.v3.json`
  - v3: `https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json`

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/run_api_surface_smoke.py`
- `PYTHONPATH=src python scripts/run_api_surface_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_api_surface_smoke_v1`

### Main Result

| Metric | Value |
| --- | ---: |
| count | 7 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.714 |

kind breakdown：
- `drive_discovery = 2/2 pass`
- `jira_openapi = 3/3 pass`
- `negative_docs = 2/2 pass`

provider breakdown：
- `drive = 3/3 pass`
- `jira = 4/4 pass`

### Representative Spec Evidence
- Drive clean:
  - request:
    - `POST /drive/v2/files/file_brief/parents`
    - body = `{"id": "fld_reports"}`
  - live discovery hit:
    - `parents.insert`
    - `httpMethod = POST`
    - `path = files/{fileId}/parents`
    - request schema contains `ParentReference.id`

- Drive positive migration:
  - request:
    - `PATCH /drive/v3/files/file_brief?addParents=fld_reports`
  - live discovery hit:
    - `files.update`
    - `httpMethod = PATCH`
    - `path = files/{fileId}`
    - parameters contain `addParents`

- Jira clean:
  - request:
    - `PUT /rest/api/2/issue/ENG-7/assignee`
    - body = `{"name": "acct_alice"}`
  - live OpenAPI hit:
    - `/rest/api/2/issue/{issueIdOrKey}/assignee`
    - `put`
    - request body schema `User` contains `name`

- Jira positive migration:
  - request:
    - `PUT /rest/api/3/issue/ENG-7/assignee`
    - body = `{"accountId": "acct_alice"}`
  - live OpenAPI hit:
    - `/rest/api/3/issue/{issueIdOrKey}/assignee`
    - request body schema `User` contains `accountId`

- Jira query migration:
  - request:
    - `GET /rest/api/3/user/assignable/search?project=ENG&query=acct_alice`
  - live OpenAPI hit:
    - `/rest/api/3/user/assignable/search`
    - parameters contain `project` and `query`

- 两个 negatives 继续被正确阻断：
  - `drive_add_file_to_second_folder::negative_shortcut_replacement`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`

### Interpretation
- 这轮把当前 fixed panel 的验证链从 “官方文档文字命中” 推进到 “machine-readable API surface 命中”
- 对 positive request-shape migration，当前 replayed request 已经能被 live discovery / OpenAPI 直接接住
- 对 negative capability-gap，machine-readable spec 本身不够，因此仍需要 official-doc cue 与 non-execute 一起判
- 当前 Drive / Jira 关键 case 现在已经在：
  1. source audit
  2. benchmark evaluation
  3. execution sanity
  4. request replay
  5. official-doc smoke
  6. spec-backed API surface smoke
  六层证据上闭合

### Limits
- 这仍然不是 authenticated real API invocation
- Jira v2 / v3 需要分开读取两个官方 swagger JSON，不能假设一个 spec 同时覆盖两个版本
- negative capability removal 仍然需要文档 cue；只看 OpenAPI surface 会漏掉 semantically removed 但仍残留兼容字段的情况

### Decision
- 当前 `Drive + Jira` 已经达到 “request replay -> official-doc smoke -> machine-readable surface smoke” 的连续验证
- 下一步最合理的是：
  1. 为 1 到 2 个关键 case 做带真实 HTTP round-trip 的最小 authenticated smoke
  2. 或再扩一个带公开 discovery/OpenAPI 的新 vendor family

## 2026-03-10 - Expand Real Fixed Panel To 6 Families With Google Sheets

### Goal
- 在没有本地 Drive / Jira 凭证的前提下，不阻塞主线，继续沿 real split 扩容一个带公开 machine-readable surface 的新 vendor family。
- 要求新 family 同时接入：
  1. real evolution benchmark
  2. execution sanity
  3. request replay
  4. official-doc smoke
  5. api-surface smoke
  6. real `family_holdout_cv` 主实验

### Decision
- 本地未发现可用的 Drive / Jira authenticated smoke 凭证，因此不空等凭证，直接转向 public-spec family 扩展。
- 选择 `Google Sheets v3 -> v4`，因为官方 migration guide、reference docs 和 discovery surface 都公开可访问，且同时包含：
  - positive request-shape migration
  - negative capability-gap / scope-replacement

### Main Changes
- `scripts/generate_real_evolution_benchmark.py`
  - 新增 Google Sheets family
  - 当前 real fixed panel 扩为 `24 cases / 48 views / 45 official sources / 6 families`
- `src/toolshift/request_replay.py`
  - 新增 Sheets v3/v4 request rendering
- `src/toolshift/execution_sanity.py`
  - 新增 Sheets effect-level mock execution
- `src/toolshift/official_request_smoke.py`
  - 新增 Sheets docs-backed smoke specs
- `src/toolshift/api_surface_smoke.py`
  - 新增 Sheets discovery-backed smoke specs
  - 修正 Google discovery query param 校验：method params 与 top-level params 取并集

### New Sheets Cases
- `sheets_get_sheet_titles`
  - positive: `worksheets.feed -> spreadsheets.get(fields=sheets.properties.title)`
- `sheets_append_row`
  - positive: `list.feed.insert -> spreadsheets.values.append`
- `sheets_update_formula`
  - positive: `cells.feed.update -> spreadsheets.values.update`
- `sheets_list_accessible_spreadsheets`
  - negative: `spreadsheets.feed -> drive.files.list` 不是当前 sheets tool 的 drop-in replacement

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/generate_real_evolution_benchmark.py scripts/run_execution_sanity.py scripts/run_request_replay.py scripts/run_official_request_smoke.py scripts/run_api_surface_smoke.py`
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v6`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v5`
- `PYTHONPATH=src python scripts/run_request_replay.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_request_replay_v2`
- `PYTHONPATH=src python scripts/run_official_request_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_official_request_smoke_v2`
- `PYTHONPATH=src python scripts/run_api_surface_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_api_surface_smoke_v2`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v8 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v8/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v8_diagnostics --regime family_holdout_cv`

### Verification
- 全量单测：`66` 个通过
- `compileall` 通过
- benchmark / execution / replay / docs-smoke / api-surface / family-holdout 全部已实际重跑

### Heuristic Real Pilot On Expanded 6-Family Panel

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.979 |
| LexicalShortcut | 0.458 | 0.375 | 0.750 | 0.375 | 0.875 |
| DescriptionGrounded | 0.708 | 0.875 | 0.375 | 0.875 | 1.000 |

说明：
- 新增 Sheets 后，heuristic baseline 继续保持明显区分度
- `DescriptionGrounded` 在 positive migrations 上依旧强于 lexical shortcut，但 negatives 仍会漏掉 capability-gap

### Execution Sanity

| Metric | Value |
| --- | ---: |
| count | 48 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 16 |

新增 transform 命中：
- `negative_drive_scope_replacement = 1/1 pass`

### Request Replay

| Metric | Value |
| --- | ---: |
| count | 48 |
| pass_rate | 1.000 |
| execute_render_pass_rate | 1.000 |
| negative_block_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 16 |

Sheets 代表性 replay：
- positive migration:
  - `POST /v4/spreadsheets/sh_budget/values/ws_hours:append?valueInputOption=RAW`
- negative replacement:
  - `sheets_list_accessible_spreadsheets::negative_drive_scope_replacement` 被正确 block

### Official-Doc Smoke

| Metric | Value |
| --- | ---: |
| count | 11 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.727 |

provider breakdown：
- `drive = 3/3 pass`
- `jira = 4/4 pass`
- `sheets = 4/4 pass`

注意：
- 首轮 Sheets negative 曾失败一次，原因是 rendered description 对 replacement/capability-gap cue 的 token overlap 不够
- 将描述改成显式包含 `does not provide this specific operation` 与 `Drive API Files.list` 后，rerun 恢复为 `1.000`

### API-Surface Smoke

| Metric | Value |
| --- | ---: |
| count | 11 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.727 |

kind breakdown：
- `drive_discovery = 2/2 pass`
- `jira_openapi = 3/3 pass`
- `sheets_discovery = 3/3 pass`
- `negative_docs = 3/3 pass`

关键修复：
- `sheets_get_sheet_titles::positive_version_migration` 首轮 live discovery 失败在 `query_keys`
- 原因是 Google discovery 的 `fields` 放在 top-level global params，而不是 method-local params
- 修复后，validator 以 `spec_doc["parameters"] ∪ method["parameters"]` 校验 query keys，rerun 通过

### Real Family-Holdout Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage | ActionStateSim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.115 | 0.031 | 0.625 | 0.031 | 1.000 | 0.974 |
| SemanticContractGate | 0.896 | 1.000 | 0.375 | 1.000 | 0.979 | - |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.979 | - |

### Diagnostics
- `AugOnly`
  - `admissible=0.115`
  - `execute_rate=0.177`
  - `group_counts={"control_policy_error": 69, "correct": 11, "tool_choice_error": 16}`
- `SemanticContractGate`
  - `admissible=0.896`
  - `execute_rate=0.938`
  - `group_counts={"correct": 86, "tool_choice_error": 10}`
- `SemanticCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.833`
  - `group_counts={"correct": 96}`

### Interpretation
- 这轮扩到公开可审计的 `Google Sheets` family 后，主结论没有回退：
  - `SemanticCapabilityGate` 在 expanded 6-family real `family_holdout_cv` 上仍是 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`
- 当前 6-family panel 已同时具备：
  1. source audit
  2. benchmark evaluation
  3. execution sanity
  4. request replay
  5. official-doc smoke
  6. api-surface smoke
  7. family-holdout method test
- 这说明当前方法并不只对 `Drive / Jira` 局部特化；加入新的 public-spec migration family 后仍可保持闭合

### Limits
- 这仍然不是 authenticated real HTTP invocation
- Sheets negative 说明 deterministic inhibition 对 description wording 仍有一定依赖；rendered description 必须保留足够 capability-gap cue
- 当前 6-family panel 依然是 fixed regression panel，不应当被误写成 final-scale benchmark

### Decision
- 当前最合理的下一步仍是二选一：
  1. 若凭证出现，为 1 到 2 个 Drive / Jira case 增加最小 authenticated smoke
  2. 若无凭证，继续引入新的 public-spec real family，并复用 execution / replay / docs / api-surface / family-holdout 五路回归

## 2026-03-10 - Expand Real Fixed Panel To 7 Families With Google Contacts -> People API

### Goal
- 在仍无本地 Drive / Jira authenticated smoke 凭证的前提下，继续沿 public-spec 路线扩一类新的 real family。
- 新 family 必须同时接入：
  1. benchmark generation
  2. execution sanity
  3. request replay
  4. official-doc smoke
  5. api-surface smoke
  6. real `family_holdout_cv` 主实验

### Decision
- 继续不等待凭证，直接扩 `Google Contacts API -> People API`。
- 选择该 family 的原因是：
  - 有官方 migration guide
  - People API discovery surface 公开
  - 同时包含 positive migration 与真实 negative capability gap
    - `Other Contacts` 在 People API 中是 read-only

### Main Changes
- `scripts/generate_real_evolution_benchmark.py`
  - 新增 `people` family
  - 当前 real fixed panel 扩为 `28 cases / 56 views / 51 official sources / 7 families`
- `src/toolshift/request_replay.py`
  - 新增 People request rendering
- `src/toolshift/execution_sanity.py`
  - 新增 People mock semantics
- `src/toolshift/official_request_smoke.py`
  - 新增 People docs-backed smoke specs
- `src/toolshift/api_surface_smoke.py`
  - 新增 People discovery-backed smoke specs
  - 修正 path-template matcher，支持 Google discovery 的 `{+resourceName}` full-path expansion

### New People Cases
- `people_list_my_contacts`
  - positive: `contacts.feed -> people.connections.list`
- `people_create_contact`
  - positive: `contacts.feed.insert -> people.createContact`
- `people_list_contact_groups`
  - positive: `groups.feed -> contactGroups.list`
- `people_update_other_contact_email`
  - negative: `Other Contacts` 在 People API 中为 read-only，必须先复制到 `My Contacts`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/generate_real_evolution_benchmark.py scripts/run_execution_sanity.py scripts/run_request_replay.py scripts/run_official_request_smoke.py scripts/run_api_surface_smoke.py`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v7`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v6`
- `PYTHONPATH=src python scripts/run_request_replay.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_request_replay_v3`
- `PYTHONPATH=src python scripts/run_official_request_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_official_request_smoke_v3`
- `PYTHONPATH=src python scripts/run_api_surface_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_api_surface_smoke_v3`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v9 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v9/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v9_diagnostics --regime family_holdout_cv`

### Verification
- 全量单测：`72` 个通过
- `compileall` 通过
- benchmark / execution / replay / docs-smoke / api-surface / family-holdout / diagnostics 全部已实际重跑

### Heuristic Real Pilot On Expanded 7-Family Panel

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.982 |
| LexicalShortcut | 0.446 | 0.368 | 0.778 | 0.368 | 0.857 |
| DescriptionGrounded | 0.696 | 0.842 | 0.333 | 0.842 | 1.000 |

说明：
- 新增 People family 后，heuristic baseline 继续掉分，panel 仍保持诊断性
- `DescriptionGrounded` 仍然在 positive migrations 上更强，但对 negatives 的 inhibition 仍不够

### Execution Sanity

| Metric | Value |
| --- | ---: |
| count | 56 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 19 |

新增 transform 命中：
- `negative_other_contacts_read_only = 1/1 pass`

### Request Replay

| Metric | Value |
| --- | ---: |
| count | 56 |
| pass_rate | 1.000 |
| execute_render_pass_rate | 1.000 |
| negative_block_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 19 |

People 代表性 replay：
- positive migration:
  - `GET /v1/people/me/connections?pageSize=10&personFields=names,emailAddresses`
- negative read-only:
  - `people_update_other_contact_email::negative_other_contacts_read_only` 被正确 block

### Official-Doc Smoke

| Metric | Value |
| --- | ---: |
| count | 15 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.733 |

provider breakdown：
- `drive = 3/3 pass`
- `jira = 4/4 pass`
- `people = 4/4 pass`
- `sheets = 4/4 pass`

People negative docs cue：
- migration guide 命中 `add the other contact as a my contact`
- migration guide / ref 命中 `copyOtherContactToMyContactsGroup`

### API-Surface Smoke

| Metric | Value |
| --- | ---: |
| count | 15 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.733 |

kind breakdown：
- `drive_discovery = 2/2 pass`
- `jira_openapi = 3/3 pass`
- `people_discovery = 3/3 pass`
- `sheets_discovery = 3/3 pass`
- `negative_docs = 4/4 pass`

关键修复：
- People discovery 使用了 `v1/{+resourceName}/connections`
- 旧的 segment-count matcher 无法匹配 `/v1/people/me/connections`
- 改成 full-path regex matcher 后，`people.connections.list` 的 live discovery 校验恢复通过

### Real Family-Holdout Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage | ActionStateSim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.116 | 0.026 | 0.667 | 0.026 | 0.991 | 0.965 |
| SemanticContractGate | 0.893 | 1.000 | 0.333 | 1.000 | 0.982 | - |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.982 | - |

### Diagnostics
- `AugOnly`
  - `admissible=0.116`
  - `execute_rate=0.161`
  - `group_counts={"control_policy_error": 82, "correct": 13, "tool_choice_error": 17}`
- `SemanticContractGate`
  - `admissible=0.893`
  - `execute_rate=0.946`
  - `group_counts={"correct": 100, "tool_choice_error": 12}`
- `SemanticCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.839`
  - `group_counts={"correct": 112}`

People-specific failure split：
- `AugOnly / people.other_contacts.update_email`
  - `2 x missed_execute_ask_clarification`
  - `2 x correct_non_execute`
- `SemanticContractGate / people.other_contacts.update_email`
  - `2 x correct_execute`
  - `2 x wrong_tool_choice`
- `SemanticCapabilityGate / people.other_contacts.update_email`
  - `2 x correct_execute`
  - `2 x correct_non_execute`

### Interpretation
- 这轮新增 `Google Contacts -> People API` 后，主结论仍未回退：
  - `SemanticCapabilityGate` 在 expanded 7-family real `family_holdout_cv` 上仍是 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`
- 新 family 还带来了一个新的真实 negative 风格：
  - `read-only but copy-first workaround exists`
- 这进一步说明当前 capability gate 学到的不是某几个 vendor 的 surface 特例，而是更一般的 description-level capability-gap inhibition

### Limits
- 这仍然不是 authenticated real HTTP invocation
- People family 的 positive surface 依赖 Google discovery 里 `{+resourceName}` 这类 full-path expansion；若只做 segment 级匹配，会低估 live spec evidence
- 当前 7-family panel 仍然是 fixed regression panel，不应被误写成最终规模 benchmark

### Decision
- 当前最合理的下一步仍是二选一：
  1. 若凭证出现，为 1 到 2 个 Drive / Jira case 增加最小 authenticated smoke
  2. 若无凭证，继续引入新的 public-spec real family，并保持 execution / replay / docs / api-surface / family-holdout 五路固定回归

## 2026-03-10 - Expand Real Fixed Panel To 8 Families With Confluence v1 -> v2

### Goal
在不引入任何外部凭证的前提下，继续扩 real fixed panel，把 `Confluence Cloud REST v1 -> v2` 接入现有五路无凭证验证链，并复跑 `family_holdout_cv` 主实验。

### Environment
- Python 3.12.4
- 无外部凭证；本轮只使用 public docs / public OpenAPI / local replay + execution harness
- `data/real_evolution_benchmark.json` 已重生成为 `32 cases / 64 views / 57 official sources / 8 vendor families`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest tests.test_real_evolution_benchmark tests.test_execution_sanity tests.test_request_replay tests.test_official_request_smoke tests.test_api_surface_smoke tests.test_embedding_policy_utils`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/generate_real_evolution_benchmark.py scripts/run_execution_sanity.py scripts/run_request_replay.py scripts/run_official_request_smoke.py scripts/run_api_surface_smoke.py`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v8`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v7`
- `PYTHONPATH=src python scripts/run_request_replay.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_request_replay_v4`
- `PYTHONPATH=src python scripts/run_official_request_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_official_request_smoke_v4`
- `PYTHONPATH=src python scripts/run_api_surface_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_api_surface_smoke_v4`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v10 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v10/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v10_diagnostics --regime family_holdout_cv`

### Artifacts
- `artifacts/real_evolution_seed_pilot_v8/summary.json`
- `artifacts/real_evolution_execution_sanity_v7/summary.json`
- `artifacts/real_evolution_request_replay_v4/summary.json`
- `artifacts/real_evolution_official_request_smoke_v4/summary.json`
- `artifacts/real_evolution_api_surface_smoke_v4/summary.json`
- `artifacts/real_evolution_family_holdout_v10/summary.json`
- `artifacts/real_evolution_family_holdout_v10_diagnostics/summary.json`

### Heuristic Pilot

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.984 |
| lexical_shortcut | 0.469 | 0.409 | 0.800 | 0.409 | 0.844 |
| description_grounded | 0.688 | 0.818 | 0.300 | 0.818 | 1.000 |

### Execution Sanity

| Metric | Value |
| --- | ---: |
| count | 64 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 22 |

新增 transform 命中：
- `negative_space_key_lookup_split = 1/1 pass`

### Request Replay

| Metric | Value |
| --- | ---: |
| count | 64 |
| pass_rate | 1.000 |
| execute_render_pass_rate | 1.000 |
| negative_block_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 22 |

Confluence 代表性 replay：
- positive migration:
  - `GET /wiki/api/v2/pages/2001?body-format=storage`
  - `PUT /wiki/api/v2/pages/2001/title`
  - `GET /wiki/api/v2/pages/2001/children`
- negative split:
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split` 被正确 block

### Official-Doc Smoke

| Metric | Value |
| --- | ---: |
| count | 19 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.737 |

provider breakdown：
- `confluence = 4/4 pass`
- `drive = 3/3 pass`
- `jira = 4/4 pass`
- `people = 4/4 pass`
- `sheets = 4/4 pass`

Confluence negative docs cue：
- deprecation notice 命中 `/rest/api/space/<spacekey>`
- v2 docs / notice 命中 `/api/v2/spaces?keys=<spacekey>`
- v2 docs 命中 `spaceId`

### API-Surface Smoke

| Metric | Value |
| --- | ---: |
| count | 19 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.737 |

kind breakdown：
- `confluence_openapi = 3/3 pass`
- `drive_discovery = 2/2 pass`
- `jira_openapi = 3/3 pass`
- `people_discovery = 3/3 pass`
- `sheets_discovery = 3/3 pass`
- `negative_docs = 5/5 pass`

关键修复：
- Confluence OpenAPI 的 live request 验证不能只匹配裸 `paths`
- 需要同时解析 `servers[].url` 里的 `/wiki/api/v2` 前缀
- `PUT /pages/{id}/title` 的 body 还使用 `#/components/requestBodies/...`，因此 validator 需要解析 requestBody `$ref`
- 修完后，Confluence 三个 positive migration 全部通过 machine-readable surface 审计

### Real Family-Holdout Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage | ActionStateSim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.117 | 0.023 | 0.700 | 0.023 | 1.000 | 0.962 |
| SemanticContractGate | 0.891 | 1.000 | 0.300 | 1.000 | 0.984 | - |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.984 | - |

### Diagnostics
- `AugOnly`
  - `admissible=0.117`
  - `execute_rate=0.172`
  - `group_counts={"control_policy_error": 92, "correct": 15, "tool_choice_error": 21}`
- `SemanticContractGate`
  - `admissible=0.891`
  - `execute_rate=0.953`
  - `group_counts={"correct": 114, "tool_choice_error": 14}`
- `SemanticCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.844`
  - `group_counts={"correct": 128}`

Confluence-specific split：
- `semantic_contract_gate / confluence.pages.list_by_space_key`
  - held-out negative `spaceKey -> spaceId lookup split` 仍会误执行
- `semantic_capability_gate / confluence.pages.list_by_space_key`
  - 对应 negative 被稳定压成 admissible non-execute

### Interpretation
- 这轮新增 `Confluence v1 -> v2` 后，real fixed panel 已扩到 `8 families`，但主结论没有回退：
  - `SemanticCapabilityGate` 仍在 expanded `family_holdout_cv` 上保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`
- 新 family 带来的关键新负样本风格是：
  - `spaceKey` 仍可通过额外 lookup 间接恢复，但 current page-list endpoint 本身只接受 `spaceId`
  - 这类 “related workaround exists, but not drop-in” negative 仍然会让 `semantic_contract_gate` 误执行
- 同时，这轮也暴露了 machine-readable validator 的一个真实坑：
  - public OpenAPI smoke 不能假设 path template 直接等于 request path，还要处理 `servers` 前缀和 requestBody refs

### Limits
- 这仍然不是 authenticated real HTTP invocation
- 当前 `official_request_smoke` / `api_surface_smoke` 只覆盖 selected high-value views，而不是全 64 views
- 当前 8-family panel 仍是 fixed regression panel，不应被误写成最终规模 benchmark

### Decision
- 在无外部凭证约束下，public-spec family 扩展仍然是最合理主线
- 下一步应继续引入新的 public-spec real family，并保持 execution / replay / docs / api-surface / family-holdout 五路固定回归

## 2026-03-11 - Supervised Cross-Encoder Pair Model on Frozen 9-Family Panel

### Goal
- 严格按当前主线，把 `semantic_cross_encoder_capability_gate` 从 “现成 reranker + threshold calibration” 推进到 “带训练信号的 cross-encoder / pair model”。
- 验收面固定不变，继续使用 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `semantic_cross_encoder_supervised_capability_gate`
  - 新增 `CROSS_ENCODER_FEATURE_NAMES`
  - 新增 `_cross_encoder_feature_map(...)`
  - `CrossEncoderSemanticGateAgent` 现在支持 supervised `capability_scorer`
- `tests/test_embedding_policy_utils.py`
  - 新增 `_cross_encoder_feature_map(...)` 的 cue-free focused test

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_supervised_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_supervised_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_supervised_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderSupervisedCapabilityGate | 0.806 | 0.720 | 0.455 | 0.720 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_supervised_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_supervised_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_supervised_capability_gate`
  - `admissible=0.806`
  - `execute_rate=0.819`
  - `group_counts={"control_policy_error": 16, "correct": 116, "tool_choice_error": 12}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=28`
  - `strictly_regressed_views=14`

Representative regressions:
- positive/control regressions
  - `drive_add_parent_to_file::positive_version_migration -> missed_execute_abstain`
  - `drive_remove_parent_from_file::positive_version_migration -> missed_execute_abstain`
  - `people_list_contact_groups::positive_version_migration -> missed_execute_ask_clarification`
  - `people_list_my_contacts::positive_version_migration -> missed_execute_ask_clarification`
  - `sheets_append_row::positive_version_migration -> missed_execute_ask_clarification`
  - `sheets_get_sheet_titles::positive_version_migration -> missed_execute_ask_clarification`
  - `sheets_update_formula::positive_version_migration -> missed_execute_ask_clarification`
- negative/tool-choice regressions
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `notion_list_shared_databases::negative_search_replacement`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Train-Side Signal
- supervised cross-encoder fold metrics暴露了一个新问题：
  - `clause_localizer_threshold` 在所有 family fold 上都变成了 `1.000001`
  - `clause_localizer_train_positive_recall = 0.0`
- 这意味着当前 localizer 在训练阶段直接塌成 “从不选 clause”，后续 inhibition scorer 实际上主要在用 `full_capability_score / localized_capability_score` 的弱差异做决策，而没有真正学到 negative clause localization。

### Interpretation
- 这轮是清晰的主线负结果：
  - 训练信号已经真正接进 cross-encoder / pair model
  - 但当前实现仍未追平 `semantic_embedding_capability_gate`
- 相比上一轮 `semantic_cross_encoder_capability_gate`
  - 不是单纯 threshold calibration 了
  - 但 negative-localization supervision 仍然没有被模型吃进去
- 当前失败模式也更明确：
  - 一部分回退重新落在 `positive under-execute`
  - 另一部分仍是 `negative wrong_tool_choice`
  - 根因不是 “pair model 做不到”，而是 “当前 clause localizer 训练直接塌掉”

### Decision
- 这条 supervised cross-encoder 变体不进入当前 strongest-method 主线
- 继续沿主线时，不再尝试同级别的 threshold / linear aggregator 小修
- 下一步应直接针对 `cross-encoder localizer collapse` 做：
  - 更强的 ranking-style localizer objective
  - 或真正的 fine-tuned cross-encoder pair model

## 2026-03-11 - Ranking-Style Cross-Encoder Localizer on Frozen 9-Family Panel

### Goal
- 继续严格沿主线推进，把 `semantic_cross_encoder_supervised_capability_gate` 的 localizer 从独立 binary threshold 改成 ranking-style objective，避免再次塌成 “永不选 clause”。
- 验收面仍固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - `CrossEncoderClauseLocalizer` 新增 `selection_mode`
  - 新增 `_cross_encoder_clause_ranking(...)`
  - 新增 `semantic_cross_encoder_ranked_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 `selection_mode=\"top\"` 的 cue-free focused test

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_ranked_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_ranked_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_ranked_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderRankedCapabilityGate | 0.792 | 0.720 | 0.455 | 0.720 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_ranked_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_ranked_capability_gate`
  - `admissible=0.792`
  - `execute_rate=0.806`
  - `group_counts={"control_policy_error": 18, "correct": 114, "tool_choice_error": 12}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=30`
  - `strictly_regressed_views=15`

Representative regressions:
- clean / positive under-execute
  - `bitbucket_get_legacy_account::clean`
  - `drive_add_parent_to_file::clean`
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
  - `people_list_contact_groups::positive_version_migration`
  - `people_list_my_contacts::positive_version_migration`
  - `sheets_append_row::positive_version_migration`
  - `sheets_get_sheet_titles::positive_version_migration`
  - `sheets_update_formula::positive_version_migration`
- negative tool-choice regressions
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `notion_list_shared_databases::negative_search_replacement`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Train-Side Signal
- ranking route 确实修掉了上一轮 “全负阈值塌陷”：
  - `clause_localizer_threshold = 0.0`
  - `clause_localizer_train_positive_rate = 1.0`
- 但它没有转化成有用的 localization：
  - `clause_localizer_train_accuracy` 只有 `0.000 ~ 0.167`
  - `clause_localizer_train_positive_recall` 只有 `0.000 ~ 0.083`
- 也就是说，ranking-style top selection 只是强行选了一个 clause，但 top-ranked clause 很少真的是 capability-gap clause。

### Interpretation
- 这轮仍然是主线负结果，而且比上一轮 supervised cross-encoder 略差：
  - supervised: `CAA=0.806`
  - ranked: `CAA=0.792`
- 但它提供了一个更干净的机制结论：
  - 问题不只是 binary threshold collapse
  - 即使强制改成 ranking-style top selection，现成 reranker 也没有学会把 negative capability-gap clause 排到前面
- 所以当前 cross-encoder 路线的真正瓶颈已经收敛到：
  - `pair relevance != capability-gap localization`
  - 仅靠 pretrained reranker + 轻量后处理，仍然学不到正确的 clause ranking

### Decision
- 这条 ranking-style cross-encoder 变体同样不进入当前 strongest-method 主线
- 当前主线不再继续做 localizer threshold / top-selection 小修
- 下一步应直接转向：
  - 带显式正负采样的 pairwise / listwise localizer training
  - 或真正 fine-tuned cross-encoder pair model

## 2026-03-11 - Pairwise-Sampled Cross-Encoder Localizer on Frozen 9-Family Panel

### Goal
- 继续严格沿主线推进，把 `semantic_cross_encoder_ranked_capability_gate` 升级成显式正负采样的 pairwise localizer training，不再只做 top-selection。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `CROSS_ENCODER_CLAUSE_FEATURE_NAMES`
  - 新增 `_cross_encoder_clause_feature_map(...)`
  - 新增 `_fit_pairwise_clause_ranker(...)`
  - 新增 `semantic_cross_encoder_pairwise_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 pairwise localizer 的 cue-free focused tests

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_pairwise_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_pairwise_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_pairwise_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderPairwiseCapabilityGate | 0.812 | 0.720 | 0.500 | 0.720 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_pairwise_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_pairwise_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_pairwise_capability_gate`
  - `admissible=0.812`
  - `execute_rate=0.812`
  - `group_counts={"control_policy_error": 16, "correct": 117, "tool_choice_error": 11}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=27`
  - `strictly_regressed_views=14`

Representative regressions:
- clean / positive under-execute
  - `bitbucket_get_legacy_account::clean`
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
  - `people_list_contact_groups::positive_version_migration`
  - `people_list_my_contacts::positive_version_migration`
  - `sheets_append_row::positive_version_migration`
  - `sheets_get_sheet_titles::positive_version_migration`
  - `sheets_update_formula::positive_version_migration`
- negative tool-choice regressions
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `notion_list_shared_databases::negative_search_replacement`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Train-Side Signal
- 相对前两轮 cross-encoder localizer 路线，pairwise sampling 确实带来了小幅但真实的训练信号增量：
  - `clause_localizer_train_accuracy` 提升到 `0.143 ~ 0.333`
  - `clause_localizer_train_positive_recall` 提升到 `0.059 ~ 0.167`
  - 对应 test 端 `NOS` 从 `0.455` 提升到 `0.500`
- 但这个增量还远远不够：
  - top-ranked clause 仍然经常不是正确的 capability-gap clause
  - `CAA+ / POC` 仍停在 `0.720`
  - relative to strongest baseline，仍然没有任何 improved pairs

### Interpretation
- 这轮是“有价值但仍为负”的主线结果：
  - pairwise localizer 明显好于纯 threshold / top-selection
  - 但仍然无法替代当前 strongest baseline `semantic_embedding_capability_gate`
- 当前最重要的研究结论变得更清楚：
  - cross-encoder localizer 的确需要显式正负采样
  - 但仅靠轻量 pairwise ranker 仍不足以学会稳定的 capability-gap clause ranking
- 现在真正剩下的主线问题，已经不是 “要不要 ranking signal”，而是：
  - `pairwise` 是否还不够，应该升级到 `listwise`
  - 或者必须真正 fine-tune cross-encoder 本体，而不是只训练上层 ranker

### Decision
- `semantic_cross_encoder_pairwise_capability_gate` 仍不进入当前 strongest-method 主线
- 但它是到目前为止最有价值的 cross-encoder localizer 负结果，因为它首次把 train-side localization 指标和 test-side `NOS` 一起往前推了一步
- 下一步不再回退到 threshold/top-selection 路线，直接转向：
  - listwise localizer training
  - 或真正 fine-tuned cross-encoder pair model

## 2026-03-11 - Listwise-Sampled Cross-Encoder Localizer on Frozen 9-Family Panel

### Goal
- 继续严格沿主线推进，把 `semantic_cross_encoder_pairwise_capability_gate` 升级成显式 `listwise` clause localizer training。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `_fit_listwise_clause_ranker(...)`
  - 新增 `train_listwise_cross_encoder_semantic_gate_agent(...)`
  - 接通 `semantic_cross_encoder_listwise_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 listwise ranker focused test

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_listwise_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_listwise_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_listwise_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderListwiseCapabilityGate | 0.812 | 0.720 | 0.500 | 0.720 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_listwise_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_listwise_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_listwise_capability_gate`
  - `admissible=0.812`
  - `execute_rate=0.812`
  - `group_counts={"control_policy_error": 16, "correct": 117, "tool_choice_error": 11}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=27`
  - `strictly_regressed_views=14`

Representative regressions:
- clean / positive under-execute
  - `bitbucket_get_legacy_account::clean`
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
  - `people_list_contact_groups::positive_version_migration`
  - `people_list_my_contacts::positive_version_migration`
  - `sheets_append_row::positive_version_migration`
  - `sheets_get_sheet_titles::positive_version_migration`
  - `sheets_update_formula::positive_version_migration`
- negative tool-choice regressions
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `notion_list_shared_databases::negative_search_replacement`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Train-Side Signal
- 相对上一轮 pairwise route，listwise objective 的确把 localizer 训练指标再往上推了一点：
  - `clause_localizer_train_accuracy` mean 从 `0.185` 升到 `0.218`
  - `clause_localizer_train_positive_recall` mean 从 `0.085` 升到 `0.100`
- 但 test 端 aggregate 完全没动：
  - `CAA / CAA+ / NOS / POC / coverage` 与 pairwise route 全部相同
- 手工对照两轮 records，`144` 个 seed-view 里只有 `2` 个预测不同，而且只是 `notion_create_page_in_database::negative_parent_scope_change` 在两个 seed 上互换了 `ask_clarification` / `execute`

### Interpretation
- 这轮仍然是主线负结果，而且说明已经更清楚：
  - `listwise objective` 本身不是当前瓶颈的解
  - 它能稍微改善 train-side localization 指标，但还不足以穿透到 fixed-panel test
- 所以当前剩下的主线问题已经进一步收敛到：
  - 不是 `pairwise` 还是 `listwise`
  - 而是现成 reranker 本体在 low-sample fold 上仍学不会稳定的 capability-gap clause ranking

### Decision
- `semantic_cross_encoder_listwise_capability_gate` 不进入当前 strongest-method 主线
- cross-encoder 路线里，`pairwise` 和 `listwise` 都已证明：只换 ranking objective 不够
- 下一步不再继续同级别 localizer objective 小修，直接转向：
  - 真正 fine-tuned cross-encoder pair model
  - 或更强的 pair-model training，而不是继续换上层 ranker loss

## 2026-03-11 - Fine-Tuned Cross-Encoder Capability Pair Model on Frozen 9-Family Panel

### Goal
- 严格沿主线继续，不再做 localizer loss 小修，直接实现第一版真正更新 reranker 参数的 `fine-tuned cross-encoder pair model`。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `FineTunedQwenRerankerCrossEncoder`
  - 新增 `_configure_cross_encoder_finetuning(...)`
  - 新增 `_load_qwen_reranker_model_uncached(...)`
  - 新增 `_finetune_cross_encoder_binary_classifier(...)`
  - 新增 `train_finetuned_cross_encoder_capability_gate_agent(...)`
  - 接通 `semantic_cross_encoder_finetuned_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 fine-tune parameter selection focused test

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_finetuned_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_finetuned_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_finetuned_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderFinetunedCapabilityGate | 0.819 | 0.900 | 0.364 | 0.900 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_finetuned_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_finetuned_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_finetuned_capability_gate`
  - `admissible=0.819`
  - `execute_rate=0.861`
  - `group_counts={"control_policy_error": 12, "correct": 118, "tool_choice_error": 14}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=26`
  - `strictly_regressed_views=17`

Representative regressions:
- clean / positive execute regressions
  - `bitbucket_get_legacy_account::clean`
  - `confluence_get_page_storage::clean`
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
  - `stripe_create_checkout_session_with_coupon::clean`
  - `stripe_create_checkout_session_with_coupon::positive_version_migration`
  - `stripe_create_customer_with_tax_id::clean`
  - `stripe_update_subscription_source::clean`
- negative capability-gap leaks
  - `bitbucket_get_legacy_account::negative_account_object_removed`
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `notion_list_shared_databases::negative_search_replacement`
  - `people_update_other_contact_email::negative_other_contacts_read_only`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Train-Side Signal
- 这轮不是只训练上层线性 ranker，而是真正更新 reranker 参数：
  - `cross_encoder_tunable_param_count = 171,041,024`
  - `cross_encoder_tune_last_n_layers = 1`
- 但 train-side capability inhibition 仍然偏弱：
  - `capability_gate_train_accuracy` mean `0.878`
  - `capability_gate_train_inhibit_recall` mean `0.151`
  - `capability_gate_train_inhibit_rate` mean `0.031`
- 相比现有 cross-encoder 路线：
  - relative to `pairwise / listwise`，它把 `CAA+ / POC` 从 `0.720` 拉到 `0.900`
  - 但 `NOS` 从 `0.500` 掉到 `0.364`
  - relative to zero-shot `semantic_cross_encoder_capability_gate`，它把 `NOS` 从 `0.273` 拉到 `0.364`，但 `CAA+ / POC` 从 `0.920` 小幅掉到 `0.900`

### Interpretation
- 这轮是主线里的有价值负结果：
  - 真正 fine-tuned pair model 已经落地，不再是 frozen / threshold / ranker-loss 变体
  - 但当前这版 capability-only fine-tune 仍未追平 strongest baseline `semantic_embedding_capability_gate`
- 当前最重要的新信息是：
  - 问题已经不只是 “loss 形式不对” 或 “没有更新 cross-encoder 参数”
  - 即使放开 `171M` 参数，这条 capability-only fine-tune 仍然主要学成了 `positive execute` 和 `negative inhibition` 的 tradeoff，而不是稳定的 capability-gap detector

### Decision
- `semantic_cross_encoder_finetuned_capability_gate` 不进入当前 strongest-method 主线
- 但它给主线带来了新的收敛判断：
  - 只做 capability-only pair fine-tune 还不够
  - 下一步不再继续做 threshold / ranking-loss 小修，而应转向：
    - hard-negative / class-balanced fine-tuned pair model
    - 或 joint `capability + localization` multitask fine-tune

## 2026-03-11 - Joint Capability+Localization Multitask Fine-Tune on Frozen 9-Family Panel

### Goal
- 继续严格沿主线推进，不再只做 capability-only fine-tune，而是把 `capability + localization` 一起接进同一个 cross-encoder 的 multitask fine-tune。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `CrossEncoderBinaryTaskSpec`
  - 新增 `_flatten_cross_encoder_binary_tasks(...)`
  - 新增 `_finetune_cross_encoder_multitask_binary_classifier(...)`
  - 新增 `train_multitask_cross_encoder_capability_gate_agent(...)`
  - 接通 `semantic_cross_encoder_multitask_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 multitask task-flattening focused test

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_multitask_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_multitask_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_multitask_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderMultitaskCapabilityGate | 0.812 | 0.840 | 0.364 | 0.840 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_multitask_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_multitask_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_multitask_capability_gate`
  - `admissible=0.812`
  - `execute_rate=0.854`
  - `group_counts={"control_policy_error": 13, "correct": 117, "tool_choice_error": 14}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=27`

### Train-Side Signal
- 这轮最重要的新信号是：multitask 的确学会了 localizer，但没有把它转成更好的 fixed-panel behavior。
- 相比 capability-only fine-tune：
  - `clause_localizer_train_accuracy` mean `0.000 -> 0.691`
  - `clause_localizer_train_positive_recall` mean `0.000 -> 0.619`
  - `capability_gate_train_inhibit_recall` mean `0.151 -> 0.217`
- 但 test 端反而没有受益：
  - `NOS` 完全没升，仍是 `0.364`
  - `CAA+ / POC` 从 `0.900` 掉到 `0.840`

### Interpretation
- 这轮仍然是主线负结果，但它非常有信息量：
  - multitask supervision 确实把 localization 学起来了
  - 可是 “学会 localization” 并没有自动变成更好的 capability-gap inhibition
- 所以当前主线进一步收敛到一个更具体的判断：
  - 不是 `localization` 缺失导致 fine-tuned route 失败
  - 而是当前 multitask objective 仍然在把模型推向 execute-friendly tradeoff，而不是稳定的 negative inhibition

### Decision
- `semantic_cross_encoder_multitask_capability_gate` 不进入当前 strongest-method 主线
- 当前主线不再继续做 capability-only vs multitask 这种同级别 supervision 组合小修
- 下一步应直接转向：
  - hard-negative / class-balanced fine-tuned pair model
  - 或更强的 calibration / decision rule，专门抑制 multitask 下的 negative leak

## 2026-03-11 - Frozen Pair-Text Capability Gate (Negative Result)

### Goal
- 严格沿主线继续，把 learned route 从失败的 generic interaction / calibrated head 推到更强的 pair-model 方向。
- 最小可行版本选为 frozen encoder 上的 joint pair-text scorer：
  - train-time 继续用 cue extraction 产生 clause supervision
  - inference 不直接调用 `_capability_cue_clauses()`

### Code / Artifacts
- code:
  - `src/toolshift/embedding_policy.py`
  - `tests/test_embedding_policy_utils.py`
- artifacts:
  - `artifacts/real_evolution_family_holdout_pair_text_capability_v1`
  - `artifacts/real_evolution_family_holdout_pair_text_capability_v1_diagnostics`
  - `artifacts/real_evolution_factorized_compare_pair_text_vs_embedding_v1`

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_pair_text_capability_v1 --methods semantic_embedding_capability_gate semantic_pair_text_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_pair_text_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_pair_text_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_pair_text_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_pair_text_capability_gate --output-dir artifacts/real_evolution_factorized_compare_pair_text_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticPairTextCapabilityGate | 0.743 | 0.780 | 0.909 | 0.780 | 0.986 |

### Diagnostics
- `SemanticEmbeddingCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`
- `SemanticPairTextCapabilityGate`
  - `admissible=0.743`
  - `execute_rate=0.618`
  - `group_counts={"control_policy_error": 35, "correct": 107, "tool_choice_error": 2}`

Shift breakdown for `SemanticPairTextCapabilityGate`:
- `clean`
  - `admissible=0.667`
  - `execute_rate=0.667`
  - `group_counts={"correct": 48, "control_policy_error": 24}`
- `positive_orbit`
  - `admissible=0.780`
  - `execute_rate=0.780`
  - `group_counts={"correct": 39, "control_policy_error": 11}`
- `negative_near_orbit`
  - `admissible=0.909`
  - `execute_rate=0.091`
  - `group_counts={"correct": 20, "tool_choice_error": 2}`

Paired comparison against embedding baseline:
- `improved_pair_count=0`
- `regressed_pair_count=37`
- `strictly_regressed_views=20`

Representative regressions:
- execute collapse on positives / clean:
  - `people_create_contact::clean`
  - `people_create_contact::positive_version_migration`
  - `stripe_create_customer_with_tax_id::clean`
  - `stripe_create_customer_with_tax_id::positive_version_migration`
  - `bitbucket_list_workspace_repositories::clean`
  - `bitbucket_list_workspace_repositories::positive_version_migration`
- residual wrong-tool negative leak:
  - `notion_list_shared_databases::negative_search_replacement`

### Interpretation
- 这条 frozen pair-text 路线是主线对齐的，因为它真的把方法推进到了 joint pair-text scorer，而不是继续调线性 overlap 特征。
- 但结果是清晰负证据：
  - `pair_text` 没有追平 `semantic_embedding_capability_gate`
  - 主要错误不是 negative inhibition 全面失效，而是大面积 `missed_execute_ask_clarification`
  - 也就是它重新学成了更保守的 execute gate
- 和上一轮 `semantic_clause_localization_capability_gate` 相比：
  - `CAA: 0.875 -> 0.743`
  - `CAA+: 0.820 -> 0.780`
  - `NOS: 0.864 -> 0.909`
  当前 frozen encoder 上的 joint pair embedding 更像“多守住一点 negative，但明显压坏 clean / positive”

### Decision
- `semantic_pair_text_capability_gate` 不进入当前 strongest-method 主线
- 当前 strongest baseline 仍然是 `semantic_embedding_capability_gate`
- 主线下一步不再是 frozen encoder + linear pair head，而应直接升级到更强的：
  - cross-encoder / pair model
  - 或带显式选择监督的更强 clause-localizer + pair head

## 2026-03-11 - Pair-Text MLP Gate (Partial Recovery, Still Negative)

### Goal
- 沿主线继续，不再做 frozen encoder + linear pair head 的小修补。
- 直接把上一轮 joint pair-text scorer 升级成更强的 non-linear pair model，检验“pair model 表达能力不够”是否是主因。

### Code / Artifacts
- code:
  - `src/toolshift/embedding_policy.py`
  - `tests/test_embedding_policy_utils.py`
- artifacts:
  - `artifacts/real_evolution_family_holdout_pair_text_mlp_v1`
  - `artifacts/real_evolution_family_holdout_pair_text_mlp_v1_diagnostics`
  - `artifacts/real_evolution_factorized_compare_pair_text_mlp_vs_embedding_v1`

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_pair_text_mlp_v1 --methods semantic_embedding_capability_gate semantic_pair_text_mlp_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_pair_text_mlp_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_pair_text_mlp_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_pair_text_mlp_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_pair_text_mlp_capability_gate --output-dir artifacts/real_evolution_factorized_compare_pair_text_mlp_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticPairTextMLPCapabilityGate | 0.868 | 0.920 | 0.682 | 0.920 | 0.986 |

### Diagnostics
- `SemanticEmbeddingCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`
- `SemanticPairTextMLPCapabilityGate`
  - `admissible=0.868`
  - `execute_rate=0.812`
  - `group_counts={"control_policy_error": 12, "correct": 125, "tool_choice_error": 7}`

Shift breakdown for `SemanticPairTextMLPCapabilityGate`:
- `clean`
  - `admissible=0.889`
  - `execute_rate=0.889`
  - `group_counts={"correct": 64, "control_policy_error": 8}`
- `positive_orbit`
  - `admissible=0.920`
  - `execute_rate=0.920`
  - `group_counts={"correct": 46, "control_policy_error": 4}`
- `negative_near_orbit`
  - `admissible=0.682`
  - `execute_rate=0.318`
  - `group_counts={"correct": 15, "tool_choice_error": 7}`

Paired comparison against embedding baseline:
- `improved_pair_count=0`
- `regressed_pair_count=19`
- `strictly_fixed_views=[]`

Relative to the previous linear pair-text gate:
- `CAA: 0.743 -> 0.868`
- `CAA+: 0.780 -> 0.920`
- `NOS: 0.909 -> 0.682`
- `POC: 0.780 -> 0.920`

Representative regressions:
- residual negative leaks:
  - `notion_list_shared_databases::negative_search_replacement`
  - `stripe_list_customers_total_count::negative_removed_capability`
- remaining execute collapse:
  - a small set of `clean / positive` views, especially around `people`, `bitbucket`, and `stripe`

### Interpretation
- 这轮结果比 frozen linear pair-text 明显更强，说明“pair model 表达能力太弱”确实是上一轮失败的主要来源之一。
- 但它仍没有追平 `semantic_embedding_capability_gate`。
- 更具体地说：
  - MLP pair head 大幅救回了 `clean / positive`
  - 但代价是 negative inhibition 明显回退，`NOS` 从 `0.909` 掉到 `0.682`
- 所以当前结论不是 “更强 pair model 已经成功”，而是：
  - `non-linear pair head > linear pair head`
  - 但 `frozen encoder + small MLP pair head` 仍然不够

### Decision
- `semantic_pair_text_mlp_capability_gate` 不进入当前 strongest-method 主线
- 这轮结果支持下一步继续沿 pair-model 主线推进，但必须更进一步：
  - 不是再调 frozen pair head
  - 而是直接上更强的 cross-encoder / pair model

## 2026-03-11 - Cross-Encoder Capability Gate (True Pair Model, Still Negative)

### Goal
- 严格按主线继续，不再停在 frozen encoder + small head。
- 直接实现真正的 cross-encoder / pair model，用本地 `Qwen3-Reranker-0.6B` 做 joint pair scoring，并继续用 frozen `9-family real fixed panel` 做硬验收。

### Code / Artifacts
- code:
  - `src/toolshift/embedding_policy.py`
  - `tests/test_embedding_policy_utils.py`
  - `scripts/run_matched_budget_pilot.py`
- artifacts:
  - `artifacts/real_evolution_family_holdout_cross_encoder_v1`
  - `artifacts/real_evolution_family_holdout_cross_encoder_v1_diagnostics`
  - `artifacts/real_evolution_factorized_compare_cross_encoder_vs_embedding_v1`

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderCapabilityGate | 0.861 | 0.920 | 0.273 | 0.920 | 0.944 |

### Diagnostics
- `SemanticEmbeddingCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`
- `SemanticCrossEncoderCapabilityGate`
  - `admissible=0.861`
  - `execute_rate=0.931`
  - `group_counts={"control_policy_error": 4, "correct": 124, "tool_choice_error": 16}`

Shift breakdown for `SemanticCrossEncoderCapabilityGate`:
- `clean`
  - `admissible=1.000`
  - `execute_rate=1.000`
  - `group_counts={"correct": 72}`
- `positive_orbit`
  - `admissible=0.920`
  - `execute_rate=0.920`
  - `group_counts={"correct": 46, "control_policy_error": 4}`
- `negative_near_orbit`
  - `admissible=0.273`
  - `execute_rate=0.727`
  - `group_counts={"correct": 6, "tool_choice_error": 16}`

Paired comparison against embedding baseline:
- `improved_pair_count=0`
- `regressed_pair_count=20`
- `strictly_regressed_views=10`

Representative regressions:
- positive misses:
  - `drive_add_parent_to_file::positive_version_migration`
  - `drive_remove_parent_from_file::positive_version_migration`
- negative leaks:
  - `bitbucket_get_legacy_account::negative_account_object_removed`
  - `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
  - `notion_list_shared_databases::negative_search_replacement`
  - `people_update_other_contact_email::negative_other_contacts_read_only`
  - `stripe_list_customers_total_count::negative_removed_capability`
  - `stripe_update_subscription_source::negative_source_removed`

### Interpretation
- 这轮确实实现了真正更强的 pair model：不是 frozen embedding 上的后接小头，而是直接用 `Qwen3-Reranker-0.6B` 做 joint pair scoring。
- 结果说明：
  - cross-encoder 把 `clean` 全守住了
  - `positive` 也基本守住
  - 但 `negative capability-gap inhibition` 明显失守，`NOS` 只有 `0.273`
- 相对 `semantic_pair_text_mlp_capability_gate`：
  - `CAA` 略差 (`0.868 -> 0.861`)
  - `CAA+` 持平 (`0.920`)
  - `NOS` 大幅更差 (`0.682 -> 0.273`)
  所以当前这版 cross-encoder 更像“强相关性执行器”，而不是稳定的 capability-gap inhibitor。

### Decision
- `semantic_cross_encoder_capability_gate` 也不进入当前 strongest-method 主线
- 这轮结果说明：
  - 真正更强的 pair model 方向是对的，已经能稳定跑通并提供新信息
  - 但当前 zero/few-shot reranker + threshold calibration 还不够
- 下一步如果继续严格按主线推进，就不该再停在 threshold-calibrated reranker，而要做：
  - 带训练信号的 cross-encoder / pair model
  - 或显式的 negative-localization-aware cross-encoder

## 2026-03-11 - Embedding-Feature Capability Gate on Frozen 9-Family Panel

### Commands

```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_embedding_capability_v1 --methods semantic_continuous_capability_gate semantic_embedding_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_embedding_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_embedding_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_embedding_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_continuous_capability_gate semantic_embedding_capability_gate --output-dir artifacts/real_evolution_factorized_compare_embedding_vs_continuous_v1
```

### Main Result

| Method | Features | CAA | CAA+ | NOS | POC | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SemanticContinuousCapabilityGate | `description_overlap / max_cue_overlap / total_cue_overlap` | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticEmbeddingCapabilityGate | `description_similarity / max_cue_similarity / mean_cue_similarity` | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |

### Diagnostics
- `SemanticContinuousCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`
- `SemanticEmbeddingCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`
- paired compare
  - `improved_pairs=0`
  - `regressed_pairs=0`
  - `strictly_fixed_views=[]`

### Interpretation
- 这轮把 capability inhibition 从 `3` 个 hand-crafted overlap 统计，继续推进成 `3` 个 embedding similarity 特征，而且在 frozen `9-family real fixed panel` 上没有任何逐 view 回退。
- 这说明当前 fixed panel 上的 negative capability-gap 边界，不必依赖 token-overlap 计数，也能在更原生的 text-feature 空间里表达出来。
- 但这还不是完全摆脱 hand-crafted inductive bias：
  - `semantic_embedding_capability_gate` 仍然依赖 `_capability_cue_clauses()` 去抽取 negative cue clause，再计算 `max/mean cue similarity`
  - 因此它更像 “embedding-backed cue scorer”，还不是完全 raw-text 的 learned pair scorer
- 现阶段最准确的结论是：
  - `semantic_embedding_capability_gate` 成功追平 `semantic_continuous_capability_gate`
  - 但没有显示独立增量，也还没有证明可以去掉 cue-clause extraction

### Limits
- 当前 acceptance 仍是 frozen `9-family` fixed panel，不是新的 OOD panel
- `semantic_embedding_capability_gate` 仍用 deterministic cue-clause extraction 定位可能的 capability-gap 描述
- 本轮没有新增 vendor family，也没有更改 request replay / execution / docs / api-surface 验证链

### Decision
- fixed panel 现在足以作为后续方法层 regression surface；下一步不再扩 family
- 下一步应继续削减 `_capability_cue_clauses()` 这一层 hand-crafted extraction，尝试 whole-description / raw text-pair scorer，同时保持当前 fixed-panel 验收不变

## 2026-03-11 - Removing Cue-Clause Extraction on Frozen 9-Family Panel

### Commands

```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_raw_text_capability_v1 --methods semantic_embedding_capability_gate semantic_raw_text_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_raw_text_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_raw_text_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_raw_text_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_raw_text_capability_gate --output-dir artifacts/real_evolution_factorized_compare_raw_text_vs_embedding_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_description_pool_capability_v1 --methods semantic_embedding_capability_gate semantic_description_pool_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_description_pool_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_description_pool_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_description_pool_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_description_pool_capability_gate --output-dir artifacts/real_evolution_factorized_compare_description_pool_vs_embedding_v1
```

### Main Result

| Method | Features | CAA | CAA+ | NOS | POC | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | `description_similarity / max_cue_similarity / mean_cue_similarity` | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticRawTextCapabilityGate | `tool_similarity / description_similarity / argument_similarity` | 0.847 | 1.000 | 0.455 | 1.000 | 0.986 |
| SemanticDescriptionPoolCapabilityGate | `tool_similarity / description_similarity / argument_similarity / max(mean) description clause similarity` | 0.889 | 0.880 | 0.545 | 0.880 | 0.986 |

### Diagnostics
- `SemanticRawTextCapabilityGate`
  - `admissible=0.847`
  - `execute_rate=0.861`
  - `group_counts={"control_policy_error": 10, "correct": 122, "tool_choice_error": 12}`
  - paired compare vs embedding: `improved_pairs=0 / regressed_pairs=22`
- `SemanticDescriptionPoolCapabilityGate`
  - `admissible=0.889`
  - `execute_rate=0.875`
  - `group_counts={"control_policy_error": 6, "correct": 128, "tool_choice_error": 10}`
  - paired compare vs embedding: `improved_pairs=0 / regressed_pairs=16`

Representative regressions:
- raw-text
  - negative leak: `bitbucket_get_legacy_account::negative_account_object_removed`
  - negative leak: `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
  - positive/clean under-execute: `jira_add_issue_watcher_user_ref::clean`, `people_create_contact::clean`, `sheets_append_row::clean`
- description-pool
  - negative leak: `bitbucket_get_legacy_account::negative_account_object_removed`
  - negative leak: `notion_list_shared_databases::negative_search_replacement`
  - positive under-execute: `people_list_my_contacts::positive_version_migration`, `sheets_get_sheet_titles::positive_version_migration`, `sheets_update_formula::positive_version_migration`

### Interpretation
- 这轮的核心问题已经很清楚：当前 frozen panel 上，`whole-description / raw text-pair scorer` 还不足以替代 cue-specific localization。
- 只用 `tool / description / argument` 相似度时，方法同时出现两类回退：
  - `negative` capability-gap 泄漏成 `wrong_tool_choice`
  - `clean / positive` 被过度压成 `ask_clarification`
- 把 whole-description 进一步做 generic clause pooling 后，结果有所改善，但仍明显差于 `semantic_embedding_capability_gate`：
  - `regressed_pairs: 22 -> 16`
  - `NOS: 0.455 -> 0.545`
  - 但仍未恢复到 `1.0`
- 这说明当前真正不可随意拿掉的 scaffold，不是 clause granularity 本身，而是 `negative clause localization`：
  - generic whole-description 太粗
  - generic all-clause pooling 也还不够
  - cue-specific clause extraction 目前仍然在 frozen panel 上提供了独立必要信息

### Limits
- 这轮是固定 panel 上的方法 ablation，不是新 benchmark
- 两个新方法都是负结果，不应误写成 proposal 方法已经 fully learned
- `semantic_raw_text_capability_gate` 和 `semantic_description_pool_capability_gate` 都仍是轻量 linear scorer，不是 cross-encoder / pairwise interaction model

### Decision
- 当前不应继续盲删 scaffold；`_capability_cue_clauses()` 仍是 frozen panel 上的有效必要部件
- 下一步若还要继续对齐 proposal 的 learned-method 方向，应转向：
  - learned clause localization
  - 或 raw text-pair cross interaction scorer
  而不是继续只用 linear whole-text similarity 替代 cue localization

## 2026-03-11 - Linear Interaction Scorer on Localized Generic Clauses

### Commands

```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_interaction_capability_v1 --methods semantic_embedding_capability_gate semantic_interaction_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_interaction_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_interaction_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_interaction_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_interaction_capability_gate --output-dir artifacts/real_evolution_factorized_compare_interaction_vs_embedding_v1
```

### Main Result

| Method | Features | CAA | CAA+ | NOS | POC | Coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | cue-specific clause similarity | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticInteractionCapabilityGate | top generic clause interaction + scalar tail | 0.688 | 0.680 | 0.818 | 0.680 | 0.986 |

### Diagnostics
- `SemanticInteractionCapabilityGate`
  - `admissible=0.688`
  - `execute_rate=0.590`
  - `group_counts={"control_policy_error": 41, "correct": 99, "tool_choice_error": 4}`
  - paired compare vs embedding: `improved_pairs=0 / regressed_pairs=45`

### Interpretation
- 这条线比 generic whole-text / description-pool 更接近 “learned interaction”，但在当前 low-sample fold 设定下，学到的主要不是更好的 capability localization，而是更保守的 non-execute policy。
- 证据很直接：
  - `NOS` 仍有 `0.818`
  - 但 `CAA+ / POC` 一起掉到 `0.680`
  - `execute_rate` 从 embedding baseline 的 `0.847` 掉到 `0.590`
- 所以这不是 “interaction 成功学会了 localization”，而是 “interaction linear scorer 过度抑制 execute”。
- 与上一条负结果合在一起看，当前 frozen panel 给出的信号已经很一致：
  - generic whole-text 不够
  - generic clause pooling 不够
  - 简单 linear interaction 也不够
  - 现阶段真正缺的是更强的 localization / pair modeling，而不是继续在线性 scorer 上加小特征

### Decision
- `semantic_interaction_capability_gate` 作为当前 low-sample linear baseline 不成立，不应继续作为主线反复调参
- 下一步若继续对齐 proposal，更合理的方向是：
  - learned clause localization with explicit selection supervision
  - 或更强的 pair model / cross encoder
  而不是继续堆 linear interaction tail feature

## 2026-03-11 - Learned Clause Localization Gate

### Commands

```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_clause_localization_capability_v1 --methods semantic_embedding_capability_gate semantic_clause_localization_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_clause_localization_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_clause_localization_capability_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_clause_localization_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_clause_localization_capability_gate --output-dir artifacts/real_evolution_factorized_compare_clause_localization_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticClauseLocalizationCapabilityGate | 0.875 | 0.820 | 0.864 | 0.820 | 0.986 |

### Diagnostics
- `SemanticClauseLocalizationCapabilityGate`
  - `admissible=0.875`
  - `execute_rate=0.764`
  - `group_counts={"control_policy_error": 15, "correct": 126, "tool_choice_error": 3}`
  - paired compare vs embedding: `improved_pairs=0 / regressed_pairs=18`

Representative regressions:
- positive / clean under-execute
  - `drive_remove_parent_from_file::clean`
  - `drive_remove_parent_from_file::positive_version_migration`
  - `drive_add_file_to_second_folder::clean`
- residual negative leaks
  - `notion_create_page_in_database::negative_parent_scope_change`
  - `stripe_update_subscription_source::negative_source_removed`

### Interpretation
- 这轮是当前最接近 proposal “learned clause localization” 的一次推进，而且相对上一轮 `semantic_interaction_capability_gate` 明显回升：
  - `CAA: 0.688 -> 0.875`
  - `CAA+: 0.680 -> 0.820`
  - `regressed_pairs: 45 -> 18`
- 但它仍然没有追平 `semantic_embedding_capability_gate`，主要剩余问题是：
  - positive/clean 的 under-execute
  - 少量 hard negative 的 residual leak
- 更关键的是训练信号暴露出明显过拟合：
  - clause localizer train accuracy/recalI 基本是 `1.0`
  - dense capability scorer train accuracy/recall 也几乎 `1.0`
  这说明“learned localization”方向本身是对的，但当前 low-sample 线性实现太强、泛化太差。

### Decision
- learned clause localization 比 generic interaction 更像正确方向，但当前实现仍不够好，不能替代现有 embedding baseline
- 下一步若继续严格对齐 proposal，应优先处理：
  - localizer 的过拟合 / regularization
  - 更强的 pair model，而不是继续试 generic whole-text baselines

## 2026-03-11 - Calibrated Clause-Localization Scalar Head

### Commands

```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/run_matched_budget_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_clause_localization_calibrated_v1 --methods semantic_embedding_capability_gate semantic_clause_localization_calibrated_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_clause_localization_calibrated_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_clause_localization_calibrated_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_clause_localization_calibrated_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_clause_localization_calibrated_gate --output-dir artifacts/real_evolution_factorized_compare_clause_localization_calibrated_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticClauseLocalizationCalibratedGate | 0.840 | 0.760 | 0.773 | 0.760 | 0.986 |

### Diagnostics
- `SemanticClauseLocalizationCalibratedGate`
  - `admissible=0.840`
  - `execute_rate=0.757`
  - `group_counts={"control_policy_error": 18, "correct": 121, "tool_choice_error": 5}`
  - paired compare vs embedding: `improved_pairs=0 / regressed_pairs=23`

### Interpretation
- 这轮尝试把 learned clause localization 的高维 interaction head，压缩成低维 calibrated scalar head，希望减少过拟合。
- 结果表明这条校准路线没有成功：
  - 相对 `semantic_clause_localization_capability_gate`，分数进一步下降
  - under-execute 没有被修好
  - negative 端还新增了一些 leak
- 也就是说，当前问题不是“head 太大所以只要降维就行”，而是当前 localizer + head 的联合建模本身还不够稳。

### Decision
- `semantic_clause_localization_calibrated_gate` 不应继续作为主线迭代
- 当前最强 learned-route 仍然是上一轮的 `semantic_clause_localization_capability_gate`
- 下一步若继续推进 proposal，更合理的是：
  - localizer 的更强 regularization / calibration strategy
  - 或直接升级到更强 pair model

## 2026-03-10 - Continuous Cue-Overlap Capability Scorer On Frozen 9-Family Panel

### Goal
在 `semantic_sparse_capability_gate` 已经去掉外层 cue guard 的基础上，继续削减显式 cue 依赖，测试是否还能去掉 `has_gap_rule / cue_clause_count / is_deprecated` 这类显式 binary cue 特征，只保留连续 overlap 特征。

### Feature Profiling
- frozen panel 上：
  - `clean / positive`: `max_cue_overlap = 0`, `total_cue_overlap = 0`
  - `negative_near_orbit`: `max_cue_overlap > 0`, `total_cue_overlap > 0`
- 这说明当前 panel 上，连续 cue-overlap 特征本身已经足够提供分隔信息；binary cue 不是唯一可用信号。

### Changes
- 更新 `src/toolshift/embedding_policy.py`
  - 新增 `CAPABILITY_CONTINUOUS_FEATURE_NAMES`
  - 新增 `semantic_continuous_capability_gate`
- 更新 `tests/test_embedding_policy_utils.py`
  - 新增 continuous feature set focused test

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/run_matched_budget_pilot.py`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_continuous_capability_v1 --methods semantic_sparse_capability_gate semantic_continuous_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_continuous_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_continuous_capability_v1_diagnostics --regime family_holdout_cv`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_continuous_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_sparse_capability_gate semantic_continuous_capability_gate --output-dir artifacts/real_evolution_factorized_compare_continuous_vs_sparse_v1`

### Outputs
- `artifacts/real_evolution_family_holdout_continuous_capability_v1/summary.json`
- `artifacts/real_evolution_family_holdout_continuous_capability_v1_diagnostics/summary.json`
- `artifacts/real_evolution_factorized_compare_continuous_vs_sparse_v1/summary.json`

### Main Result
- `SemanticSparseCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- `SemanticContinuousCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- paired compare：
  - `improved_pairs = 0`
  - `regressed_pairs = 0`
  - `strictly_fixed_views = []`
- diagnostics：
  - 两者都是 `group_counts={"correct": 144}`
  - 两者 `execute_rate = 0.847`

### Training Signal
- `semantic_continuous_capability_gate` 每个 fold 都只用 `3` 个连续特征：
  - `description_overlap`
  - `max_cue_overlap`
  - `total_cue_overlap`
- `capability_require_cue = 0`
- training accuracy 仍稳定在 `0.984` 左右，但 held-out `family_holdout_cv` 全对

### Interpretation
- 这比 `semantic_sparse_capability_gate` 更进一步：
  - 外层 cue guard 已经没了
  - 显式 binary cue 特征也已经没了
  - 当前只剩连续 cue-overlap 统计还在支撑 capability inhibition
- 也就是说，当前 frozen panel 上已经可以把 inhibition 子问题压缩成非常小的 continuous feature space。
- 但要写准确：
  - 这说明 current panel 上，binary cue 不是必需的
  - 不说明我们已经摆脱了 cue-driven inductive bias，因为 `max_cue_overlap / total_cue_overlap` 仍然是 hand-crafted cue statistics

### Limits
- 当前 `semantic_continuous_capability_gate` 仍然依赖 hand-crafted overlap features
- 当前 frozen panel 上连续 overlap 特征对正负仍然过于干净，尚不足以证明更弱先验下的真实困难 OOD
- 下一步若要继续对齐 proposal，更合理的是减少显式 overlap statistics，转向更原生的 learned text-feature scorer

### Decision
- 冻结 `semantic_continuous_capability_gate` 为当前最弱先验的 learning-oriented baseline
- 下一步优先尝试把 hand-crafted overlap statistics 再往下削，而不是回去继续扩 family

## 2026-03-10 - Sparse Cue-Feature Capability Scorer On Frozen 9-Family Panel

### Goal
继续推进 learning-oriented capability inhibition，不满足于 `semantic_learned_capability_gate v2` 仍依赖外层 `cue-triggered` guard；目标是把这层显式 trigger 往里收，改成 scorer 自己只看 cue-family 特征，在 frozen `9-family real fixed panel` 上验证是否仍能追平 rule gate。

### Feature Profiling
- frozen panel 的 capability feature 画像：
  - `clean`: `cue_clause_count = 0` on `36/36`
  - `positive_orbit`: `cue_clause_count = 0` on `25/25`
  - `negative_near_orbit`: `cue_clause_count >= 1` on `11/11`
- 也就是说，v1 的 regression 不是因为 negative cue 本身不足，而是因为 scorer 混入了 `best_active_score / score_margin / tool_overlap` 这类泛用 execute 特征。

### Changes
- 更新 `src/toolshift/embedding_policy.py`
  - 新增 `CAPABILITY_CUE_FEATURE_NAMES`
  - 新增 `semantic_sparse_capability_gate`
  - 让 learned scorer 支持可配置 feature 子集
- 更新 `tests/test_embedding_policy_utils.py`
  - 新增 `CAPABILITY_CUE_FEATURE_NAMES` 的 focused test

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/run_matched_budget_pilot.py`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_sparse_capability_v1 --methods semantic_capability_gate semantic_learned_capability_gate semantic_sparse_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_sparse_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_sparse_capability_v1_diagnostics --regime family_holdout_cv`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_sparse_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_capability_gate semantic_sparse_capability_gate --output-dir artifacts/real_evolution_factorized_compare_sparse_vs_capability_v1`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_sparse_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_learned_capability_gate semantic_sparse_capability_gate --output-dir artifacts/real_evolution_factorized_compare_sparse_vs_learned_v1`

### Outputs
- `artifacts/real_evolution_family_holdout_sparse_capability_v1/summary.json`
- `artifacts/real_evolution_family_holdout_sparse_capability_v1_diagnostics/summary.json`
- `artifacts/real_evolution_factorized_compare_sparse_vs_capability_v1/summary.json`
- `artifacts/real_evolution_factorized_compare_sparse_vs_learned_v1/summary.json`

### Main Result
- `SemanticCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- `SemanticLearnedCapabilityGate v2 = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- `SemanticSparseCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- paired compare:
  - sparse vs capability: `improved_pairs=0 / regressed_pairs=0`
  - sparse vs learned v2: `improved_pairs=0 / regressed_pairs=0`
- diagnostics：
  - 三者都是 `group_counts={"correct": 144}`
  - 三者 `execute_rate` 都是 `0.847`

### Training Signal
- `semantic_sparse_capability_gate` 每个 fold 都只用 `6` 个 cue-family features，且 `capability_require_cue = 0`
- training accuracy 虽然不是 `1.0`，但稳定在 `0.984` 左右；held-out `family_holdout_cv` 仍然全部正确

### Interpretation
- 这轮比 `semantic_learned_capability_gate v2` 更核心，因为它把“外层显式 cue guard”收进了 scorer 自己的 feature space。
- 更准确地说：
  - `v2` 证明了 learned scorer 需要 cue-triggered safety
  - `sparse v1` 进一步证明：只要 feature 选得对，这层 safety 不一定要作为外部 if-statement 存在
- 但它仍然不是 fully learned end-to-end：
  - `CAPABILITY_CUE_FEATURE_NAMES` 本身仍然是 hand-designed
  - 当前 frozen panel 上，cue-bearing negatives 和 cue-free positives 分离得过于干净，因此还不能证明这个 scorer 在更难的 ambiguous real negatives 上也一样稳

### Limits
- 当前 sparse scorer 仍然依赖显式 cue-family feature engineering
- 当前 panel 上 `cue_clause_count` 对正负几乎线性可分，因此 “去掉外层 guard” 不代表已经去掉了人造 inductive bias
- 下一步若要更接近 proposal 的强方法结论，需要继续减少显式 binary cue 依赖，或引入更难的 real capability-gap negatives

### Decision
- 冻结 `semantic_sparse_capability_gate` 为当前更强的 learning-oriented baseline
- 下一步优先尝试去掉 `has_gap_rule / cue_clause_count` 这类显式 binary 触发特征，而不是回去继续扩 family

## 2026-03-10 - Learning-Oriented Capability Inhibition On Frozen 9-Family Panel

### Goal
在不继续扩 benchmark 的前提下，把当前 rule-like `semantic_capability_gate` 推进一步，做一个 learning-oriented `semantic_learned_capability_gate`，并在冻结的 `9-family real fixed panel` 上看它能否追平现有 rule gate。

### Changes
- 更新 `src/toolshift/embedding_policy.py`
  - 新增 `LearnedCapabilityScorer`
  - 新增 `semantic_learned_capability_gate`
  - 新增 capability feature map 和 logistic scorer 训练分支
- 更新 `tests/test_embedding_policy_utils.py`
  - 新增 capability feature map 的 negative / positive 单测

### Commands
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/run_matched_budget_pilot.py`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_learned_capability_v1 --methods semantic_contract_gate semantic_capability_gate semantic_learned_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_learned_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_learned_capability_v1_diagnostics --regime family_holdout_cv`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_learned_capability_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_capability_gate semantic_learned_capability_gate --output-dir artifacts/real_evolution_factorized_compare_learned_vs_capability_v1`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_learned_capability_v2 --methods semantic_capability_gate semantic_learned_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_learned_capability_v2/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_learned_capability_v2_diagnostics --regime family_holdout_cv`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_learned_capability_v2/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_capability_gate semantic_learned_capability_gate --output-dir artifacts/real_evolution_factorized_compare_learned_vs_capability_v2`

### Outputs
- `artifacts/real_evolution_family_holdout_learned_capability_v1/summary.json`
- `artifacts/real_evolution_family_holdout_learned_capability_v1_diagnostics/summary.json`
- `artifacts/real_evolution_factorized_compare_learned_vs_capability_v1/summary.json`
- `artifacts/real_evolution_family_holdout_learned_capability_v2/summary.json`
- `artifacts/real_evolution_family_holdout_learned_capability_v2_diagnostics/summary.json`
- `artifacts/real_evolution_factorized_compare_learned_vs_capability_v2/summary.json`

### v1 Result
- `SemanticLearnedCapabilityGate v1 = CAA 0.993 / CAA+ 0.980 / NOS 1.000 / POC 0.980 / coverage 0.986`
- 对比 `SemanticCapabilityGate`：
  - `improved_pairs = 0`
  - `regressed_pairs = 1`
  - 唯一 regression 是 `sheets_update_formula::positive_version_migration`
  - 误差类型为 `correct_execute -> missed_execute_ask_clarification`

### v1 Diagnosis
- 这个 regression 不来自 negative inhibition 漏掉，而是 learned scorer 对一个 `cue_clause_count = 0` 的正迁移也触发了 over-inhibition。
- 具体地，`sheets_update_formula::positive_version_migration` 的 tool description 没有 negative cue：
  - `cue_clause_count = 0`
  - `has_gap_rule = 0`
- 因此 v1 的问题不是 feature 不足，而是 scorer 应用范围太宽。

### v2 Fix
- 将 learned scorer 收紧成 `cue-triggered inhibition`：
  - 只有在 tool description 里确实出现 negative cue clause 时，才调用 learned scorer
  - 无 cue 的 positive migrations 继续走原本 execute path

### v2 Main Result
- `SemanticCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- `SemanticLearnedCapabilityGate v2 = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- paired compare：
  - `improved_pairs = 0`
  - `regressed_pairs = 0`
  - `strictly_fixed_views = []`
- diagnostics：
  - `semantic_capability_gate -> group_counts={"correct": 144}`
  - `semantic_learned_capability_gate -> group_counts={"correct": 144}`
  - `execute_rate` 两者同为 `0.847`

### Training Signal
- 每个 held-out family fold 上，learned scorer 的 train stats 都稳定：
  - `capability_gate_train_accuracy = 1.000`
  - `capability_gate_train_inhibit_recall = 1.000`
  - `capability_gate_train_inhibit_rate` 落在 `0.113 - 0.143`

### Interpretation
- 这是一个 proposal 更核心层面的正结果：当前 `semantic_capability_gate` 的 capability-gap inhibition，已经可以被一个轻量 learned scorer 吸收，而不是只能靠硬编码 `if gap then inhibit`。
- 但这个 learned scorer 还不是 fully learned end-to-end 方法：
  - 它仍然依赖 hand-designed feature map
  - 它还需要 `cue-triggered` guard 才能稳住 positive
- 所以当前最准确的定位是：
  - `已证明 capability inhibition 可以向 learning-oriented 方向迈一步`
  - `尚未证明可以完全去掉 rule trigger`

### Limits
- 这轮 learned scorer 仍然建立在 explicit feature engineering 上
- v2 的成功依赖 `cue-triggered` 应用范围；若去掉这层 guard，v1 证明仍会出现 positive over-inhibition
- 当前结果只说明 frozen `9-family` panel 上可追平 rule gate，不代表已经得到更强的 OOD 方法

### Decision
- 冻结当前 `semantic_learned_capability_gate v2` 作为 learning-oriented baseline
- 下一步优先研究如何放松 `cue-triggered` guard，而不重新引入 positive regressions

## 2026-03-10 - Freeze 9-Family Fixed Panel And Factorize Contract vs Capability Gate

### Goal
不再继续扩 family，而是冻结当前 `9-family real fixed panel`，把 proposal 更核心的方法差异正式拆出来：`semantic_contract_gate` 和 `semantic_capability_gate` 到底差在哪一类视图、哪一类错误、哪几个 vendor family。

### Changes
- 新增 `src/toolshift/fixed_panel_compare.py`
- 新增 `scripts/compare_fixed_panel_methods.py`
- 新增 `tests/test_fixed_panel_compare.py`
- 产出 `artifacts/real_evolution_factorized_compare_v1/summary.json`
- 产出 `artifacts/real_evolution_factorized_compare_v1/summary.md`

### Commands
- `PYTHONPATH=src python -m unittest tests.test_fixed_panel_compare`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/compare_fixed_panel_methods.py`
- `PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_v11/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_contract_gate semantic_capability_gate --output-dir artifacts/real_evolution_factorized_compare_v1`

### Outputs
- `artifacts/real_evolution_factorized_compare_v1/summary.json`
- `artifacts/real_evolution_factorized_compare_v1/summary.md`

### Main Results
- overall:
  - `SemanticContractGate = CAA 0.889 / CAA+ 1.000 / NOS 0.273 / POC 1.000 / coverage 0.986`
  - `SemanticCapabilityGate = CAA 1.000 / CAA+ 1.000 / NOS 1.000 / POC 1.000 / coverage 0.986`
- paired delta:
  - `improved_pairs = 16`
  - `regressed_pairs = 0`
  - `improved_distinct_views = 8`
  - `strictly_fixed_views = 8`
- shift-level split:
  - `clean`: contract / capability 都是 `72/72 correct_execute`
  - `positive_orbit`: contract / capability 都是 `50/50 correct_execute`
  - `negative_near_orbit`: contract 只有 `6/22 correct_non_execute`，capability 是 `22/22 correct`
- incremental fix source:
  - 全部 `16/16` improvements 都来自 `wrong_tool_choice -> correct_non_execute`
  - `from_group = {"tool_choice_error": 16}`
  - `from_bucket = {"wrong_tool_choice": 16}`
- improved families:
  - `bitbucket = 2`
  - `confluence = 2`
  - `jira = 2`
  - `notion = 4`
  - `people = 2`
  - `stripe = 4`
- already-solved families under contract-only:
  - `drive / sheets / slack` 在 negative slice 上已经是 `NOS = 1.000`

### Strictly Fixed Views
- `bitbucket_get_legacy_account::negative_account_object_removed`
- `confluence_list_pages_by_space_key::negative_space_key_lookup_split`
- `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed`
- `notion_create_page_in_database::negative_parent_scope_change`
- `notion_list_shared_databases::negative_search_replacement`
- `people_update_other_contact_email::negative_other_contacts_read_only`
- `stripe_list_customers_total_count::negative_removed_capability`
- `stripe_update_subscription_source::negative_source_removed`

### Interpretation
- 当前 `9-family` fixed panel 上，`semantic_contract_gate` 已经把 `clean / positive` 全部做满；它不是还没学会跨-family positive invariance。
- `semantic_capability_gate` 的独立增量完全集中在 `negative capability-gap` 上，而不是继续提升 positive retrieval：
  - `CAA_positive` 没变化
  - `POC` 没变化
  - `coverage` 没变化
  - 只有 `CAA_negative / NOS` 大幅提升了 `+0.727`
- 因此当前更核心的方法结论是：
  - `contract compatibility` 已经足以解决 cross-family positive execute
  - 真正剩下的 proposal 核心难点，是 `related but not drop-in replacement` 的 description-aware inhibition
- 这也说明继续无限扩 family 的边际价值已经下降；当前更该在 frozen panel 上研究如何把这层 inhibition 变成更可学习、而不是规则堆叠的机制

### Limits
- 这轮是 fixed-panel factorized comparison，不是新的 held-out benchmark
- `compare_fixed_panel_methods.py` 当前做的是 records-level paired comparison，不直接包含训练期 `action_state_similarity`
- 当前结论仍然建立在 no-credential public-spec panel 上，不是 authenticated online API invocation

### Decision
- 冻结当前 `9-family real fixed panel` 作为方法回归面板
- 后续优先做 learning-oriented capability inhibition / scoring，而不是继续扩 family

## 2026-03-10 - Expand Real Fixed Panel To 9 Families With Bitbucket Teams -> Workspaces

### Goal
在不使用任何外部凭证的前提下，继续扩 real fixed panel，把 `Bitbucket Cloud teams -> workspaces` 与 `v1 legacy account object removal` 接入现有五路无凭证验证链，并复跑 `family_holdout_cv` 主实验。

### Environment
- Python 3.12.4
- 无外部凭证；本轮只使用 public docs / public swagger / local replay + execution harness
- `data/real_evolution_benchmark.json` 已重生成为 `36 cases / 72 views / 63 official sources / 9 vendor families`

### Commands
- `PYTHONPATH=src python scripts/generate_real_evolution_benchmark.py`
- `PYTHONPATH=src python -m unittest discover -s tests`
- `python -m compileall src tests scripts/generate_real_evolution_benchmark.py scripts/run_execution_sanity.py scripts/run_request_replay.py scripts/run_official_request_smoke.py scripts/run_api_surface_smoke.py`
- `PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_seed_pilot_v9`
- `PYTHONPATH=src python scripts/run_execution_sanity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_execution_sanity_v8`
- `PYTHONPATH=src python scripts/run_request_replay.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_request_replay_v5`
- `PYTHONPATH=src python scripts/run_official_request_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_official_request_smoke_v5`
- `PYTHONPATH=src python scripts/run_api_surface_smoke.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_api_surface_smoke_v5`
- `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v11 --methods aug_only semantic_contract_gate semantic_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8`
- `PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_v11/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_v11_diagnostics --regime family_holdout_cv`

### Artifacts
- `artifacts/real_evolution_seed_pilot_v9/summary.json`
- `artifacts/real_evolution_execution_sanity_v8/summary.json`
- `artifacts/real_evolution_request_replay_v5/summary.json`
- `artifacts/real_evolution_official_request_smoke_v5/summary.json`
- `artifacts/real_evolution_api_surface_smoke_v5/summary.json`
- `artifacts/real_evolution_family_holdout_v11/summary.json`
- `artifacts/real_evolution_family_holdout_v11_diagnostics/summary.json`

### Heuristic Pilot

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| lexical_shortcut | 0.472 | 0.480 | 0.818 | 0.480 | 0.861 |
| description_grounded | 0.681 | 0.840 | 0.364 | 0.840 | 1.000 |

### Execution Sanity

| Metric | Value |
| --- | ---: |
| count | 72 |
| pass_rate | 1.000 |
| execute_expected_pass_rate | 1.000 |
| negative_guard_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 25 |

新增 transform 命中：
- `negative_account_object_removed = 1/1 pass`

### Request Replay

| Metric | Value |
| --- | ---: |
| count | 72 |
| pass_rate | 1.000 |
| execute_render_pass_rate | 1.000 |
| negative_block_pass_rate | 1.000 |
| positive_equivalence_rate | 1.000 |
| positive_equivalence_count | 25 |

Bitbucket 代表性 replay：
- positive migration:
  - `GET /2.0/workspaces/eng-team`
  - `GET /2.0/repositories/eng-team`
  - `GET /2.0/workspaces/eng-team/members`
- negative split:
  - `bitbucket_get_legacy_account::negative_account_object_removed` 被正确 block

### Official-Doc Smoke

| Metric | Value |
| --- | ---: |
| count | 23 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.739 |

provider breakdown：
- `bitbucket = 4/4 pass`
- `confluence = 4/4 pass`
- `drive = 3/3 pass`
- `jira = 4/4 pass`
- `people = 4/4 pass`
- `sheets = 4/4 pass`

Bitbucket negative docs cue：
- v1 deprecation notice 命中 `/1.0/users/{accountname}`
- 同一 notice 命中 `not available in 2.0`
- current workspace ref / notice 命中 `/2.0/workspaces/{workspace}`

### API-Surface Smoke

| Metric | Value |
| --- | ---: |
| count | 23 |
| pass_rate | 1.000 |
| emit_expected_pass_rate | 1.000 |
| block_expected_pass_rate | 1.000 |
| emit_rate | 0.739 |

kind breakdown：
- `bitbucket_swagger = 3/3 pass`
- `confluence_openapi = 3/3 pass`
- `drive_discovery = 2/2 pass`
- `jira_openapi = 3/3 pass`
- `people_discovery = 3/3 pass`
- `sheets_discovery = 3/3 pass`
- `negative_docs = 6/6 pass`

关键修复：
- Bitbucket `swagger.json` 仍是 Swagger 2.0 结构，不提供 `servers`
- validator 需要读取 `basePath=/2.0`，否则 `/workspaces/{workspace}` 这类 path 会和真实请求 `/2.0/workspaces/...` 错位
- 修完后，Bitbucket 三个 positive migration 全部通过 machine-readable surface 审计

### Real Family-Holdout Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage | ActionStateSim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AugOnly | 0.090 | 0.000 | 0.591 | 0.000 | 1.000 | 0.965 |
| SemanticContractGate | 0.889 | 1.000 | 0.273 | 1.000 | 0.986 | - |
| SemanticCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | - |

### Diagnostics
- `AugOnly`
  - `admissible=0.090`
  - `execute_rate=0.174`
  - `group_counts={"control_policy_error": 106, "correct": 13, "tool_choice_error": 25}`
- `SemanticContractGate`
  - `admissible=0.889`
  - `execute_rate=0.958`
  - `group_counts={"correct": 128, "tool_choice_error": 16}`
- `SemanticCapabilityGate`
  - `admissible=1.000`
  - `execute_rate=0.847`
  - `group_counts={"correct": 144}`

Bitbucket-specific split：
- `AugOnly`
  - `bitbucket.workspaces.get = 4/4 missed_execute_ask_clarification`
  - `bitbucket.repositories.list_workspace = 4/4 missed_execute_ask_clarification`
  - `bitbucket.workspaces.list_members = 4/4 missed_execute_ask_clarification`
  - `bitbucket.accounts.get_legacy_account = 4/4 wrong_tool_choice`
- `SemanticContractGate`
  - 3 个 Bitbucket positive tools 全部 `4/4 correct_execute`
  - `bitbucket.accounts.get_legacy_account = 2/2 correct_execute + 2/2 wrong_tool_choice`
- `SemanticCapabilityGate`
  - 3 个 Bitbucket positive tools 仍然全部 `4/4 correct_execute`
  - `bitbucket.accounts.get_legacy_account = 2/2 correct_execute + 2/2 correct_non_execute`

### Interpretation
- 这轮新增 `Bitbucket teams -> workspaces` 后，real fixed panel 已扩到 `9 families`，但主结论仍未回退：
  - `SemanticCapabilityGate` 继续在 expanded `family_holdout_cv` 上保持 `CAA=1.0 / CAA+=1.0 / NOS=1.0 / POC=1.0`
- 新 family 带来的关键新负样本风格是：
  - legacy account object 可以返回 `user or team` union
  - current APIs 把 `users` 和 `workspaces` 拆开了，因此 related APIs 仍存在，但不再是单步 drop-in replacement
- 这进一步支持当前研究判断：
  - `semantic_contract_gate` 足以救回 cross-family positive execute
  - 但要稳住这种 “union object removed / resolution split” negative，仍然需要 description-aware capability inhibition

### Limits
- 这仍然不是 authenticated real HTTP invocation
- 当前 `official_request_smoke` / `api_surface_smoke` 只覆盖 selected high-value views，而不是全 72 views
- 当前 9-family panel 仍是 fixed regression panel，不应被误写成最终规模 benchmark

### Decision
- 在无外部凭证约束下，public-spec family 扩展仍然是最合理主线
- 下一步应继续引入新的 public-spec real family，并保持 execution / replay / docs / api-surface / family-holdout 五路固定回归

## 2026-03-11 - Hard-Negative / Class-Balanced Fine-Tuned Pair Model on Frozen 9-Family Panel

### Goal
- 严格沿主线继续，不再只做 capability-only 或 multitask fine-tune，而是验证 `hard-negative / class-balanced` weighting 能否把 fine-tuned pair model 的 `negative inhibition` 真正拉起来。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `CrossEncoderCapabilityTrainingRow`
  - 新增 `_prepare_cross_encoder_capability_training_rows(...)`
  - 新增 `_build_class_balanced_hard_negative_weights(...)`
  - 新增 `train_hard_negative_finetuned_cross_encoder_capability_gate_agent(...)`
  - `_finetune_cross_encoder_binary_classifier(...)` 现支持 weighted BCE / weighted threshold
  - 接通 `semantic_cross_encoder_hard_negative_capability_gate`
- `tests/test_embedding_policy_utils.py`
  - 新增 weighted threshold focused test
  - 新增 class-balanced hard-negative weighting focused test
- `scripts/run_matched_budget_pilot.py`
  - 新增 `--cross-encoder-class-balance-power`
  - 新增 `--cross-encoder-hard-negative-multiplier`

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_hard_negative_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_hard_negative_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_hard_negative_vs_embedding_v1
```

### Superseded Smoke
- full-strength inverse-frequency weighting (`cross_encoder_class_balance_power=1.0`)
  - `CAA=0.458`
  - `CAA+=0.320`
  - `NOS=0.636`
  - `POC=0.320`
- 这版明显把 `NOS` 拉起来了，但把 `clean / positive` execute 压塌，已 superseded 为当前 `power=0.5` 的正式设置。

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderHardNegativeCapabilityGate | 0.736 | 0.760 | 0.409 | 0.760 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_hard_negative_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_hard_negative_capability_gate`
  - `admissible=0.736`
  - `execute_rate=0.764`
  - `group_counts={"correct": 106, "control_policy_error": 25, "tool_choice_error": 13}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=38`
  - `strictly_fixed_views=[]`

### Train-Side Signal
- 这轮最重要的新信号是：hard-negative / class-balanced weighting 的确把 inhibition 学起来了，但方式太 blunt。
- 相比 capability-only fine-tune：
  - `capability_gate_train_inhibit_recall` mean `0.151 -> 0.456`
  - `NOS` 从 `0.364 -> 0.409`
  - 但 `CAA+ / POC` 从 `0.900 -> 0.760`
- 正式设置的平均权重：
  - `cross_encoder_class_balance_power = 0.5`
  - `cross_encoder_hard_negative_multiplier = 1.5`
  - `mean_inhibit_weight = 2.853`
  - `mean_execute_weight = 0.728`

### Interpretation
- 这轮仍然是主线负结果，但它比 capability-only / multitask 更清楚地回答了当前瓶颈：
  - current fine-tuned pair model 并不是完全学不到 negative inhibition
  - 一旦显式强调 hard negatives，它确实能把 `train_inhibit_recall` 和 test `NOS` 往上推
  - 但当前 weighting 还是过于粗糙，主要通过压低 `clean / positive execute` 来换 `NOS`
- 所以当前主线进一步收敛到：
  - 问题已经不只是 “缺 hard-negative weighting”
  - 而是还缺一层显式的 positive-retention / asymmetric decision calibration

### Decision
- `semantic_cross_encoder_hard_negative_capability_gate` 不进入当前 strongest-method 主线
- 但它给主线带来了新的收敛判断：
  - hard-negative / class-balanced weighting 是对方向的，`NOS` 会升
  - 但直接全局加权仍然太 blunt，不足以成为最终方法
- 下一步不再做同级别的小范围权重搜索，而应转向：
  - hard-negative weighting + explicit positive-retention calibration
  - 或更结构化的 asymmetric decision rule / objective

## 2026-03-11 - Explicit Positive-Retention / Asymmetric Decision Calibration on Frozen 9-Family Panel

### Goal
- 严格沿主线继续，在当前 `hard-negative / class-balanced` fine-tuned pair model 上加入显式 `positive-retention` 约束，验证单纯的 asymmetric decision calibration 能否同时保住 `CAA+ / POC` 和已经拉起来的 `NOS`。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `_best_asymmetric_binary_threshold(...)`
  - 新增 `train_asymmetric_hard_negative_finetuned_cross_encoder_capability_gate_agent(...)`
  - 接通 `semantic_cross_encoder_asymmetric_capability_gate`
  - `EmbeddingPolicyConfig` 新增 `cross_encoder_positive_retention_target`
- `tests/test_embedding_policy_utils.py`
  - 新增 asymmetric threshold focused test
- `scripts/run_matched_budget_pilot.py`
  - 新增 `--cross-encoder-positive-retention-target`

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_asymmetric_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_asymmetric_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_asymmetric_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderAsymmetricCapabilityGate | 0.833 | 0.920 | 0.273 | 0.920 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_asymmetric_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_asymmetric_capability_gate`
  - `admissible=0.833`
  - `execute_rate=0.903`
  - `group_counts={"correct": 120, "control_policy_error": 8, "tool_choice_error": 16}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=24`
  - `strictly_fixed_views=[]`

### Comparison to Hard-Negative Route
- relative to `semantic_cross_encoder_hard_negative_capability_gate`
  - `CAA / CAA+ / POC` all recover:
    - `CAA 0.736 -> 0.833`
    - `CAA+ 0.760 -> 0.920`
    - `POC 0.760 -> 0.920`
  - but `NOS` falls back:
    - `0.409 -> 0.273`
- train-side signal shows the same collapse:
  - `capability_gate_train_inhibit_recall mean 0.456 -> 0.049`
  - current calibration config:
    - `cross_encoder_class_balance_power = 0.5`
    - `cross_encoder_hard_negative_multiplier = 1.5`
    - `cross_encoder_positive_retention_target = 0.95`

### Interpretation
- 这轮仍然是主线负结果，但它给出了很清楚的因果判断：
  - explicit positive-retention calibration 的确能把 `clean / positive execute` 拉回去
  - 但如果只靠单一 post-hoc threshold constraint，它也会把 hard-negative weighting 刚学到的 inhibition 几乎全部撤掉
- 所以当前主线进一步收敛到：
  - 问题已经不只是 “缺 positive-retention calibration”
  - 而是当前 single-threshold asymmetric rule 太弱，无法同时保住 positive execute 和 negative inhibition

### Decision
- `semantic_cross_encoder_asymmetric_capability_gate` 不进入当前 strongest-method 主线
- 当前主线不再继续做单阈值 calibration / retention target 小修
- 下一步应直接转向：
  - train-time asymmetric objective
  - 或 dual-threshold / abstain-band decision rule

## 2026-03-11 - Train-Time Asymmetric Objective on Frozen 9-Family Panel

### Goal
- 严格沿主线继续，在当前 `hard-negative / class-balanced` fine-tuned pair model 上把 `positive-retention` 约束写进训练目标，而不是继续依赖 post-hoc threshold calibration。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `_cross_encoder_execute_margin_penalty(...)`
  - 新增 `train_asymmetric_objective_finetuned_cross_encoder_capability_gate_agent(...)`
  - 接通 `semantic_cross_encoder_asymmetric_objective_capability_gate`
  - `EmbeddingPolicyConfig` 新增 `cross_encoder_execute_margin` / `cross_encoder_execute_margin_weight`
- `tests/test_embedding_policy_utils.py`
  - 新增 execute-margin penalty focused test
- `scripts/run_matched_budget_pilot.py`
  - 新增 `--cross-encoder-execute-margin`
  - 新增 `--cross-encoder-execute-margin-weight`

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_smoke --methods semantic_embedding_capability_gate semantic_cross_encoder_asymmetric_objective_capability_gate --regimes family_holdout_cv --seeds 0 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_asymmetric_objective_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_asymmetric_objective_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_asymmetric_objective_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderAsymmetricObjectiveCapabilityGate | 0.694 | 0.680 | 0.364 | 0.680 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_asymmetric_objective_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_asymmetric_objective_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_asymmetric_objective_capability_gate`
  - `admissible=0.694`
  - `execute_rate=0.736`
  - `group_counts={"correct": 100, "control_policy_error": 30, "tool_choice_error": 14}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=44`
  - `strictly_fixed_views=[]`

### Comparison to Neighboring Mainline Routes
- relative to `semantic_cross_encoder_hard_negative_capability_gate`
  - `CAA 0.736 -> 0.694`
  - `CAA+ 0.760 -> 0.680`
  - `NOS 0.409 -> 0.364`
  - `POC 0.760 -> 0.680`
- relative to `semantic_cross_encoder_asymmetric_capability_gate`
  - `CAA 0.833 -> 0.694`
  - `CAA+ 0.920 -> 0.680`
  - `NOS 0.273 -> 0.364`
  - `POC 0.920 -> 0.680`

### Train-Side Signal
- 这轮最关键的新信号是：train-time asymmetric objective 并没有真正改变 hard-negative route 学到的 inhibit dynamics。
- 相比 hard-negative route：
  - `capability_gate_train_accuracy mean 0.715 -> 0.712`
  - `capability_gate_train_inhibit_recall mean 0.456 -> 0.446`
  - `capability_gate_train_inhibit_rate mean 0.252 -> 0.248`
- 当前正式配置：
  - `cross_encoder_class_balance_power = 0.5`
  - `cross_encoder_hard_negative_multiplier = 1.5`
  - `cross_encoder_execute_margin = 0.0`
  - `cross_encoder_execute_margin_weight = 0.5`

### Interpretation
- 这轮仍然是主线负结果，而且比 `hard-negative` 和 `single-threshold asymmetric calibration` 都更差。
- train-side inhibit stats 基本保持在 hard-negative 同一量级，但 held-out family test 明显回退，说明当前 execute-margin penalty 没有形成更好的 asymmetric structure，只是在低样本 fold 上引入了额外的不稳定性。
- 更具体地说：
  - 它没有像 single-threshold calibration 那样把 inhibit signal 全部冲掉
  - 但也没有把这个 signal 转成更好的 `CAA+ / POC` 保持
  - 最终既没保住 hard-negative 的 `NOS`，也没保住 asymmetric-threshold 的 `CAA+ / POC`

### Decision
- `semantic_cross_encoder_asymmetric_objective_capability_gate` 不进入当前 strongest-method 主线
- 当前主线不再继续做 execute-margin / retention target 同级别小修
- 下一步应直接转向：
  - dual-threshold / abstain-band decision rule

## 2026-03-12 - Dual-Threshold / Abstain-Band Decision Rule on Frozen 9-Family Panel

### Goal
- 严格沿主线继续，在当前 `hard-negative / class-balanced` fine-tuned pair model 上测试 `dual-threshold / abstain-band decision rule`，看它能否在不改训练目标的前提下，把一部分 borderline non-execute 从单阈值硬切换成更安全的 `abstain`。
- 验收面继续固定为 frozen `9-family real fixed panel` 的 `family_holdout_cv`。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `_dual_threshold_control(...)`
  - 新增 `_best_dual_threshold_band(...)`
  - 新增 `_cross_encoder_decide_capability_control(...)`
  - 新增 `train_dual_threshold_finetuned_cross_encoder_capability_gate_agent(...)`
  - 接通 `semantic_cross_encoder_dual_threshold_capability_gate`
  - `CrossEncoderCapabilityGate` 新增 `abstain_threshold`
- `tests/test_embedding_policy_utils.py`
  - 新增 dual-threshold focused test

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/compare_fixed_panel_methods.py scripts/diagnose_saved_records.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_smoke --methods semantic_embedding_capability_gate semantic_cross_encoder_dual_threshold_capability_gate --regimes family_holdout_cv --seeds 0 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1 --methods semantic_embedding_capability_gate semantic_cross_encoder_dual_threshold_capability_gate --regimes family_holdout_cv --seeds 0 1 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods semantic_embedding_capability_gate semantic_cross_encoder_dual_threshold_capability_gate --output-dir artifacts/real_evolution_factorized_compare_cross_encoder_dual_threshold_vs_embedding_v1
```

### Main Result

| Method | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| SemanticEmbeddingCapabilityGate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 |
| SemanticCrossEncoderDualThresholdCapabilityGate | 0.736 | 0.760 | 0.409 | 0.760 | 0.944 |

Artifacts:
- `artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1`
- `artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1_diagnostics`
- `artifacts/real_evolution_factorized_compare_cross_encoder_dual_threshold_vs_embedding_v1`

### Diagnostics
- `semantic_cross_encoder_dual_threshold_capability_gate`
  - `admissible=0.736`
  - `execute_rate=0.764`
  - `group_counts={"correct": 106, "control_policy_error": 25, "tool_choice_error": 13}`
- paired compare vs baseline
  - `improved_pair_count=0`
  - `regressed_pair_count=38`
  - `strictly_fixed_views=[]`

### Key Signal
- 这轮最关键的新信息不是总分，而是 dual-threshold search 在两个 seed 上都退化成了零宽度 band：
  - `capability_gate_abstain_threshold == capability_gate_threshold`
  - `capability_gate_train_abstain_rate = 0.0`
- 也就是说，当前 control-aware threshold search 并没有在训练折上找到任何值得保留的 `abstain band`；最终决策规则等价于上一轮 `hard-negative` 的单阈值 route。

### Comparison to Neighboring Mainline Routes
- relative to `semantic_cross_encoder_hard_negative_capability_gate`
  - aggregate metrics 完全持平：
    - `CAA = 0.736`
    - `CAA+ = 0.760`
    - `NOS = 0.409`
    - `POC = 0.760`
- relative to `semantic_cross_encoder_asymmetric_objective_capability_gate`
  - `CAA 0.694 -> 0.736`
  - `CAA+ 0.680 -> 0.760`
  - `NOS 0.364 -> 0.409`
  - `POC 0.680 -> 0.760`

### Interpretation
- 这轮仍然是主线负结果，但它给出了一个很明确的结构性结论：
  - 当前 fixed panel 上，plain dual-threshold / abstain-band search 不会自动带来更好的 control policy
  - 如果不额外加入 `abstain` 偏好或更强的 control-aware objective，最优解会直接塌回 hard-negative 单阈值
- 换句话说，当前问题不只是 “缺 dual-threshold rule”，而是当前训练信号没有给 abstain band 独立存在的理由。

### Decision
- `semantic_cross_encoder_dual_threshold_capability_gate` 不进入当前 strongest-method 主线
- 当前主线不再继续做 plain threshold-search 小修
- 下一步若继续沿这条 decision-rule 路线推进，需要的是：
  - explicit abstain-band prior / control-aware objective

## 2026-03-12 - Blind Real-Evolution Panel v1 and Dev-vs-Blind Split

### Goal
- 停止继续把当前 `9-family real fixed panel` 当作唯一 test 面板使用，正式将其降级为 `dev panel`。
- 启动一个新的 blind real-evolution asset，先落首个 public-spec family，并只做结构验证，不立即用于 learned-method sweep。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 blind benchmark generator，当前收录首个 `trello` family
  - 生成 `data/real_evolution_blind_benchmark.json`
  - 生成 `data/real_evolution_blind_audit.json`
  - 生成 `history/real_evolution_blind_audit.md`
- `tests/test_real_evolution_blind_benchmark.py`
  - 新增 blind benchmark focused tests
- `src/toolshift/agents.py`
  - 修正 `OracleAgent`，显式 view 下 optional arguments 缺失时不再抛 `KeyError`

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v1
```

### Blind Panel Asset
- blind panel v1:
  - `4 cases`
  - `8 views`
  - `9 official source anchors`
  - `1 vendor family`
- family coverage:
  - `trello`
- view coverage:
  - positive migration
    - application compliance route -> plugin compliance route
  - negative near-orbit
    - SCIM groups -> related enterprise workspace endpoints
    - SCIM users -> related enterprise member query endpoints

Artifacts:
- `data/real_evolution_blind_benchmark.json`
- `data/real_evolution_blind_audit.json`
- `history/real_evolution_blind_audit.md`
- `artifacts/real_evolution_blind_seed_pilot_v1`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| lexical_shortcut | 0.250 | 0.000 | 1.000 | 0.000 | 0.750 |
| description_grounded | 0.125 | 0.000 | 0.000 | 0.000 | 1.000 |

### Verification
- infer 环境全量测试：
  - `119` 个通过
- blind benchmark focused tests：
  - `5` 个通过
- `OracleAgent` 在 blind panel 上恢复满分：
  - `CAA=1.000 / CAA+=1.000 / NOS=1.000 / POC=1.000`

### Interpretation
- 这轮不是新的方法搜索，而是研究治理与资产建设。
- 当前最重要的变化是：
  - `data/real_evolution_benchmark.json` 现在被明确视为 `dev panel`
  - 新的 `data/real_evolution_blind_benchmark.json` 被明确视为 blind asset
- blind panel v1 目前只做结构验证，不参与 learned-method 选择；这样可以避免继续把同一个 9-family panel 同时当作 dev 和 final test。
- Trello family 也提供了和现有 dev panel 不同的 negative style：
  - related REST endpoints exist
  - but they are not a drop-in replacement for the old SCIM contract

### Decision
- 当前 `9-family real fixed panel` 正式降级为 `dev panel`
- blind panel v1 已可独立生成、加载、审计和跑最小 seed pilot
- 下一步不在 blind panel 上继续做 method sweep；先继续收 blind families，把 blind panel 扩到足以承接最终方法结论的规模

## 2026-03-12 - Blind Real-Evolution Panel v2 (YouTube Expansion)

### Goal
- 沿 blind-panel 主线继续推进，在不触碰方法搜索的前提下为 blind benchmark 新增第二个 public-spec family。
- 目标不是刷 blind panel 分数，而是让 blind asset 开始覆盖第二种明显不同的 negative style。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 `youtube` sources / tools / cases / views
- `tests/test_real_evolution_blind_benchmark.py`
  - blind focused tests 从 `5` 条扩到 `8` 条

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v2
```

### Blind Panel Asset
- blind panel v2:
  - `8 cases`
  - `16 views`
  - `17 official source anchors`
  - `2 vendor families`
- current families:
  - `trello`
  - `youtube`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.938 |
| lexical_shortcut | 0.188 | 0.000 | 0.750 | 0.000 | 0.625 |
| description_grounded | 0.375 | 0.250 | 0.250 | 0.250 | 1.000 |

Artifacts:
- `artifacts/real_evolution_blind_seed_pilot_v2`

### Verification
- infer 环境全量测试：
  - `122` 个通过
- blind benchmark focused tests：
  - `8` 个通过
- blind benchmark generation：
  - 成功更新 `data/real_evolution_blind_benchmark.json`
  - 成功更新 `data/real_evolution_blind_audit.json`
  - 成功更新 `history/real_evolution_blind_audit.md`

### Interpretation
- 这轮仍然不是方法实验，而是 blind asset 扩容。
- `youtube` family 带来的新信息是：blind panel 不再只有 “related REST endpoint exists but not drop-in” 这一种 negative。
- 当前它还增加了另一类更贴近 real API evolution 的 boundary：
  - same endpoint but critical parameter removed
  - legacy moderation method no longer supported
- blind seed pilot 也表明这个扩容不是空壳：
  - `description_grounded` 在双 family blind panel 上已经不再像 oracle 那样 trivially 满分
  - 但我们仍然只把它当 blind structural smoke，不把它拿来做方法选择

### Decision
- blind panel 当前推进到 v2
- 继续保持：blind panel 只做结构验证，不做 learned-method sweep
- 下一步应继续补新的 blind family / negative style，而不是在 blind panel 上做方法调参

## 2026-03-12 - Blind Real-Evolution Panel v3 (YouTube Lineage Expansion)

### Goal
- 继续沿 blind-panel 主线推进，在不触碰方法搜索的前提下为 blind benchmark 新增第三个 family tag。
- 这轮不强求新 vendor，而是验证“新的 version lineage / diff template”是否也能作为 blind family 增加 negative-style 多样性。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 `youtube_channels` lineage family 的 sources / tools / cases / views
- `tests/test_real_evolution_blind_benchmark.py`
  - blind focused tests 从 `8` 条扩到 `11` 条

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v3
```

### Blind Panel Asset
- blind panel v3:
  - `12 cases`
  - `24 views`
  - `20 official source anchors`
  - `3 family tags across 2 vendors`
- current families:
  - `trello`
  - `youtube`
  - `youtube_channels`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.958 |
| lexical_shortcut | 0.208 | 0.000 | 0.833 | 0.000 | 0.667 |
| description_grounded | 0.458 | 0.500 | 0.333 | 0.500 | 1.000 |

Artifacts:
- `artifacts/real_evolution_blind_seed_pilot_v3`

### Verification
- infer 环境全量测试：
  - `125` 个通过
- blind benchmark focused tests：
  - `11` 个通过
- blind benchmark generation：
  - 成功更新 `data/real_evolution_blind_benchmark.json`
  - 成功更新 `data/real_evolution_blind_audit.json`
  - 成功更新 `history/real_evolution_blind_audit.md`

### Interpretation
- 这轮仍然不是方法实验，而是 blind asset 扩容。
- `youtube_channels` 带来的新信息不是新 vendor，而是新 lineage family：
  - `legacy feed -> channels.list` 的正迁移
  - `single-step feed -> playlist lookup split` 的负迁移
  - `recommendations-only home feed -> broader activity feed` 的负迁移
- 这说明 blind 多样性不一定只能靠加 vendor；只要 `family_tag` 与 negative style 明显不同，同 vendor 的新 version lineage 也能贡献真正的新 blind signal。
- blind seed pilot v3 继续表明这个扩容不是空壳：
  - `description_grounded` 提升到 `CAA=0.458 / CAA+=0.500 / POC=0.500`
  - 但它仍明显落后 `oracle`
  - 因此当前 blind panel 仍有结构诊断性，但还没有被拿来做方法选择

### Decision
- blind panel 当前推进到 v3
- 继续保持：blind panel 只做结构验证，不做 learned-method sweep
- 下一步应继续补新的 blind family / negative style，优先扩到 `4-6` 个 families 后再考虑承接最终方法结论

## 2026-03-15 - Blind Real-Evolution Panel v4 (GitHub REST Expansion)

### Goal
- 继续沿 blind-panel 主线推进，在不触碰方法搜索的前提下新增第 4 个 blind family。
- 这轮优先补一种和 `trello / youtube / youtube_channels` 都不同的 negative style，而不是继续复制 lookup-split 模板。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 `github_rest` family 的 sources / tools / cases / views
- `tests/test_real_evolution_blind_benchmark.py`
  - blind focused tests 从 `11` 条扩到 `14` 条

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v4
```

### Blind Panel Asset
- blind panel v4:
  - `16 cases`
  - `32 views`
  - `29 official source anchors`
  - `4 family tags across 3 vendors`
- current families:
  - `trello`
  - `youtube`
  - `youtube_channels`
  - `github_rest`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.969 |
| lexical_shortcut | 0.406 | 0.250 | 0.875 | 0.250 | 0.719 |
| description_grounded | 0.594 | 0.625 | 0.500 | 0.625 | 1.000 |

Artifacts:
- `artifacts/real_evolution_blind_seed_pilot_v4`

### Verification
- infer 环境全量测试：
  - `128` 个通过
- blind benchmark focused tests：
  - `14` 个通过
- blind benchmark generation：
  - 成功更新 `data/real_evolution_blind_benchmark.json`
  - 成功更新 `data/real_evolution_blind_audit.json`
  - 成功更新 `history/real_evolution_blind_audit.md`

### Interpretation
- 这轮仍然不是方法实验，而是 blind asset 扩容。
- `github_rest` 带来的新 blind signal 主要不是简单 deprecate，而是两种新的 negative style：
  - `generic endpoint -> resource-context split`
  - `API route -> out-of-band replacement`
- 相比 v3，这轮 blind seed pilot 的 heuristic 分数明显抬高：
  - `lexical_shortcut CAA: 0.208 -> 0.406`
  - `description_grounded CAA: 0.458 -> 0.594`
  - `description_grounded CAA+: 0.500 -> 0.625`
- 这不是 panel 变简单的直接证据；更准确的解释是，GitHub v4 family 里的 positive path migration 更偏 path/name migration，而两类 negative 仍然保持非平凡区分度。

### Decision
- blind panel 当前推进到 v4
- 继续保持：blind panel 只做结构验证，不做 learned-method sweep
- 下一步应继续补第 `5` 个 blind family，优先找更偏 contract/body/response semantics 的 negative style

## 2026-03-15 - Blind Real-Evolution Panel v5 (GitLab REST Expansion)

### Goal
- 继续沿 blind-panel 主线推进，新增第 5 个 blind family。
- 这轮优先补 `contract/body/response semantics` 风格，而不是继续加 path 或 lookup 类迁移。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 `gitlab_rest` family 的 sources / tools / cases / views
- `tests/test_real_evolution_blind_benchmark.py`
  - blind focused tests 从 `14` 条扩到 `17` 条

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v5
```

### Blind Panel Asset
- blind panel v5:
  - `20 cases`
  - `40 views`
  - `32 official source anchors`
  - `5 family tags across 4 vendors`
- current families:
  - `trello`
  - `youtube`
  - `youtube_channels`
  - `github_rest`
  - `gitlab_rest`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.975 |
| lexical_shortcut | 0.375 | 0.200 | 0.900 | 0.200 | 0.775 |
| description_grounded | 0.625 | 0.700 | 0.400 | 0.700 | 1.000 |

Artifacts:
- `artifacts/real_evolution_blind_seed_pilot_v5`

### Verification
- infer 环境全量测试：
  - `131` 个通过
- blind benchmark focused tests：
  - `17` 个通过
- blind benchmark generation：
  - 成功更新 `data/real_evolution_blind_benchmark.json`
  - 成功更新 `data/real_evolution_blind_audit.json`
  - 成功更新 `history/real_evolution_blind_audit.md`

### Interpretation
- 这轮仍然不是方法实验，而是 blind asset 扩容。
- `gitlab_rest` 补上的 blind signal 重点不在 path migration，而在：
  - `response-field positive migration`
    - `merged_by -> merge_user`
    - `merge_status -> detailed_merge_status`
  - `response/body negative near-orbit`
    - single merge-request changes endpoint -> diffs listing split
    - ambiguous `namespace` -> `namespace_id / namespace_path`
- 相比 v4，blind seed pilot v5 继续抬高了 heuristic structural smoke：
  - `lexical_shortcut CAA: 0.406 -> 0.375` 略回落，但 `NOS: 0.875 -> 0.900`
  - `description_grounded CAA: 0.594 -> 0.625`
  - `description_grounded CAA+: 0.625 -> 0.700`
  - `description_grounded POC: 0.625 -> 0.700`
- 这说明 blind panel 现在开始同时包含：
  - path/name migration
  - parameter removal
  - lookup split
  - resource-context split
  - out-of-band replacement
  - response/body semantics migration

### Decision
- blind panel 当前推进到 v5
- 继续保持：blind panel 只做结构验证，不做 learned-method sweep
- blind panel 已经达到 `5` 个 families，下一步可以开始讨论何时冻结 blind panel 并把它作为最终方法结论的复核面板

## 2026-03-15 - Blind Real-Evolution Panel v6 (Slack Auth Expansion)

### Goal
- 继续沿 blind-panel 主线推进，新增第 6 个 blind family。
- 这轮优先补 `auth/scope/permission semantics`，而不是继续加普通 endpoint path migration。

### Code
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 新增 `slack_auth` family 的 sources / tools / cases / views
- `tests/test_real_evolution_blind_benchmark.py`
  - blind focused tests 从 `17` 条扩到 `20` 条

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_v6
```

### Blind Panel Asset
- blind panel v6:
  - `24 cases`
  - `48 views`
  - `42 official source anchors`
  - `6 family tags across 5 vendors`
- current families:
  - `trello`
  - `youtube`
  - `youtube_channels`
  - `github_rest`
  - `gitlab_rest`
  - `slack_auth`

### Structural Smoke

| Agent | CAA | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| oracle | 1.000 | 1.000 | 1.000 | 1.000 | 0.979 |
| lexical_shortcut | 0.396 | 0.308 | 0.818 | 0.308 | 0.750 |
| description_grounded | 0.625 | 0.692 | 0.364 | 0.692 | 1.000 |

Artifacts:
- `artifacts/real_evolution_blind_seed_pilot_v6`

### Verification
- infer 环境全量测试：
  - `134` 个通过
- blind benchmark focused tests：
  - `20` 个通过
- blind benchmark generation：
  - 成功更新 `data/real_evolution_blind_benchmark.json`
  - 成功更新 `data/real_evolution_blind_audit.json`
  - 成功更新 `history/real_evolution_blind_audit.md`

### Interpretation
- 这轮仍然不是方法实验，而是 blind asset 扩容。
- `slack_auth` 补上的 blind signal 重点在：
  - OAuth flow migration
    - `oauth.access -> oauth.v2.access`
  - scope narrowing / positive semantic retention
    - `users:read -> users:read + users:read.email`
    - `channels.history -> conversations.history` with unified scope model
  - permission inventory negative split
    - `apps.permissions.info -> apps.permissions.scopes.list + apps.permissions.resources.list`
- 相比 v5，这轮 blind seed pilot 的 heuristic 整体没有继续单向抬高：
  - `description_grounded CAA` 保持 `0.625`
  - `description_grounded CAA+` 从 `0.700` 微降到 `0.692`
  - `description_grounded NOS` 从 `0.400` 降到 `0.364`
- 这个信号是有价值的：blind panel 加入 auth/scope semantics 后，没有继续朝“更容易的 heuristic panel”单调漂移。

### Decision
- blind panel 当前推进到 v6
- 继续保持：blind panel 只做结构验证，不做 learned-method sweep
- blind panel 现在已经覆盖 path/name migration、parameter removal、lookup split、resource-context split、out-of-band replacement、response/body semantics、以及 auth/scope/permission semantics；可以开始考虑冻结 blind panel，用于后续最终方法结论的复核

## 2026-03-15 - Blind Real-Evolution Panel Freeze / Governance Guard

### Goal
- 停止继续扩 blind family，并把当前 blind v6 明确冻结为最终复核资产。
- 用代码级护栏明确：blind panel 不参与方法搜索，且 family 不得与 dev panel 重叠。

### Code
- `src/toolshift/blind_panel.py`
  - 新增 frozen blind panel summary / validation helper
- `scripts/validate_blind_panel.py`
  - 新增 blind panel 冻结校验入口，并可导出 summary json
- `scripts/generate_real_evolution_blind_benchmark.py`
  - benchmark payload 现会写入 `metadata.panel_role/panel_state/counts/family_tags/vendor_tags/audit_path`
  - blind audit markdown 现明确写成 frozen blind test asset
- `tests/test_blind_panel.py`
  - 新增 blind freeze focused tests

### Commands
```bash
PYTHONPATH=src python scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/validate_blind_panel.py --output-json artifacts/real_evolution_blind_panel_freeze_v1/summary.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_blind_panel tests.test_real_evolution_blind_benchmark
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
python -m compileall src tests scripts/generate_real_evolution_blind_benchmark.py scripts/validate_blind_panel.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_seed_pilot_frozen_v1
```

### Frozen Blind Summary
- `panel_role=blind_test`
- `panel_state=frozen`
- `method_selection_allowed=false`
- counts:
  - `24 cases`
  - `48 views`
  - `42 source anchors`
- families:
  - `github_rest`
  - `gitlab_rest`
  - `slack_auth`
  - `trello`
  - `youtube`
  - `youtube_channels`
- vendors:
  - `github`
  - `gitlab`
  - `slack`
  - `trello`
  - `youtube`
- `dev_family_overlap=[]`

Artifacts:
- `artifacts/real_evolution_blind_panel_freeze_v1/summary.json`
- `artifacts/real_evolution_blind_seed_pilot_frozen_v1`

### Verification
- infer 环境 focused tests：
  - `23` 个通过
- infer 环境全量测试：
  - `137` 个通过
- blind validation script：
  - 成功验证 `method_selection_allowed=false`
  - 成功验证 blind/dev family 不重叠
  - 成功验证全部样本保持 `unambiguous_core`
- frozen blind structural smoke：
  - `oracle = 1.000 / 1.000 / 1.000 / 1.000 / 0.979`
  - `lexical_shortcut = 0.396 / 0.308 / 0.818 / 0.308 / 0.750`
  - `description_grounded = 0.625 / 0.692 / 0.364 / 0.692 / 1.000`

### Interpretation
- 这轮不是继续扩 blind family，而是把 blind panel 从“持续增长的资产”切成“受治理的冻结复核面板”。
- `validate_blind_panel.py` 让 blind panel 的几个关键约束不再只存在于 README 文案里：
  - blind/dev family disjoint
  - blind panel 不参与方法搜索
  - blind audit 路径必须存在
  - blind samples 必须继续停留在 `unambiguous_core`
- frozen blind structural smoke 与 v6 一致，说明这次治理收束没有悄悄改动 blind benchmark 本体，也没有降低 blind asset 的难度。

## 2026-03-15 - Dev-Panel Masking Sensitivity v1

### Goal
- 在 blind panel 冻结后，回到 dev panel 补 proposal 缺的机制证据。
- 首版只做 `name / description / contract` 三类 masking sensitivity，对比 strongest scaffold baseline 与唯一保留的 learned route。

### Code
- `src/toolshift/masking.py`
  - 新增 `unmasked / name_mask / description_mask / contract_mask` 的 test-time view masking helper
- `scripts/run_masking_sensitivity.py`
  - 新增 held-out family test-time masking 分析入口
- `tests/test_masking.py`
  - 新增 masking focused tests

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_masking
python -m compileall src tests scripts/run_masking_sensitivity.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_masking_sensitivity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_masking_sensitivity_v1 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Methods
- strongest scaffold baseline:
  - `semantic_embedding_capability_gate`
- retained learned route:
  - `semantic_clause_localization_capability_gate`

### Results

| Method | Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | `unmasked` | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 |
| `semantic_embedding_capability_gate` | `name_mask` | 0.986 | 1.000 | 0.909 | 1.000 | 0.986 | -0.014 | 0.000 | -0.091 | 0.000 |
| `semantic_embedding_capability_gate` | `description_mask` | 0.632 | 0.540 | 0.636 | 0.540 | 0.986 | -0.368 | -0.460 | -0.364 | -0.460 |
| `semantic_embedding_capability_gate` | `contract_mask` | 0.618 | 0.540 | 0.545 | 0.540 | 1.000 | -0.382 | -0.460 | -0.455 | -0.460 |
| `semantic_clause_localization_capability_gate` | `unmasked` | 0.868 | 0.880 | 0.818 | 0.880 | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 |
| `semantic_clause_localization_capability_gate` | `name_mask` | 0.861 | 0.880 | 0.773 | 0.880 | 0.986 | -0.007 | 0.000 | -0.045 | 0.000 |
| `semantic_clause_localization_capability_gate` | `description_mask` | 0.500 | 0.440 | 0.636 | 0.440 | 0.986 | -0.368 | -0.440 | -0.182 | -0.440 |
| `semantic_clause_localization_capability_gate` | `contract_mask` | 0.486 | 0.440 | 0.545 | 0.440 | 1.000 | -0.382 | -0.440 | -0.273 | -0.440 |

Artifacts:
- `artifacts/real_evolution_masking_sensitivity_v1/summary.json`
- `artifacts/real_evolution_masking_sensitivity_v1/summary.md`
- `artifacts/real_evolution_masking_sensitivity_v1/records.json`

### Verification
- masking focused tests：
  - `3` 个通过
- infer 环境全量测试：
  - `140` 个通过
- 正式 masking 分析：
  - `2 methods x 4 masks x 2 seeds`
  - held-out family 训练只跑一次，masking 只发生在 test-time view

### Interpretation
- 这轮最重要的机制信号很明确：`name_mask` 几乎不伤两条路线，但 `description_mask / contract_mask` 会显著拉低 `CAA+ / POC / NOS`。
- strongest scaffold baseline 和保留 learned route 的跌幅方向高度一致，说明当前核心不是 raw tool-name sensitivity，而是 localized description / contract cue grounding。
- `contract_mask` 比 `description_mask` 进一步更差，说明显式 status/deprecation/contract cue 仍然在当前 strongest scaffold baseline 里承担了额外抑制信号。

## 2026-03-15 - Dev-Panel Decision-State Probe v1

### Goal
- 在 dev panel 上继续补机制证据，不再只看行为分数。
- 对 strongest scaffold baseline 与 retained learned route 做 decision-state probe、positive-state similarity 和 negative separation 分析。

### Code
- `src/toolshift/decision_probe.py`
  - 新增 semantic gate decision-state extraction、linear probe、positive/negative state similarity helper
- `scripts/run_decision_probe.py`
  - 新增 dev-panel decision-state probe 分析入口
- `tests/test_decision_probe.py`
  - 新增最小 probe focused test

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_decision_probe
python -m compileall src tests scripts/run_decision_probe.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_decision_probe.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_decision_probe_v1 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Methods
- strongest scaffold baseline:
  - `semantic_embedding_capability_gate`
- retained learned route:
  - `semantic_clause_localization_capability_gate`

### Results

| Method | CAA | CAA+ | NOS | POC | probe_accuracy | probe_negative_recall | positive_state_similarity | negative_state_similarity | state_separation_gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | 1.000 | 1.000 | 1.000 | 1.000 | 0.972 | 0.889 | 0.997 | -0.325 | 1.322 |
| `semantic_clause_localization_capability_gate` | 0.840 | 0.780 | 0.818 | 0.780 | 0.826 | 0.833 | 0.615 | -0.445 | 1.060 |

Artifacts:
- `artifacts/real_evolution_decision_probe_v1/summary.json`
- `artifacts/real_evolution_decision_probe_v1/summary.md`

### Verification
- probe focused tests：
  - 默认环境 `1` 个跳过（无 torch）
- infer 环境全量测试：
  - `141` 个通过
- 正式 decision-state 分析：
  - `2 methods x 2 seeds`
  - family-holdout 训练后，对 held-out family 直接抽取 decision-state 并训练/eval probe

### Interpretation
- 这轮把机制证据再往前推进了一步：最强 scaffold baseline 不只是行为分数更高，它的内部 state 也更稳定。
- `semantic_embedding_capability_gate` 的 `positive_state_similarity=0.997`，几乎把 clean/positive orbit 压成同一个 decision manifold；retained learned route 只有 `0.615`。
- 两条路线对 negative near-orbit 都形成了分离，但 strongest scaffold baseline 的 `state_separation_gap` 更大（`1.322 > 1.060`），说明它不只是“更会执行”，而是更稳定地区分了 positive invariance 和 negative inhibition。

## 2026-03-15 - Dev-Panel Boundary Evidence v1

### Goal
- 在 blind panel 冻结后，继续补 proposal 缺的 boundary evidence，而不是继续做方法 sweep。
- 用 dev panel 现有 negative near-orbit views 派生 `counterfactual impossible shadow`，量化当前 strongest scaffold baseline 的 hidden-shift 边界。

### Code
- `src/toolshift/boundary.py`
  - 新增 `build_impossible_shadow_examples`
  - 新增 impossible shadow 结果汇总 helper
- `scripts/run_boundary_evidence.py`
  - 新增 dev-panel boundary analysis 入口
- `tests/test_boundary.py`
  - 新增 impossible shadow focused tests

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_boundary
python -m compileall src tests scripts/run_boundary_evidence.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_boundary_evidence.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_boundary_evidence_v1 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Methods
- strongest scaffold baseline:
  - `semantic_embedding_capability_gate`
- retained learned route:
  - `semantic_clause_localization_capability_gate`

### Results

| Method | CAA | CAA+ | NOS | POC | impossible_shadow_CAA | impossible_execute_rate | impossible_ask_clarification_rate | visible_minus_impossible_gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 |
| `semantic_clause_localization_capability_gate` | 0.861 | 0.820 | 0.818 | 0.820 | 0.136 | 0.864 | 0.136 | 0.682 |

Artifacts:
- `artifacts/real_evolution_boundary_evidence_v1/summary.json`
- `artifacts/real_evolution_boundary_evidence_v1/summary.md`
- `artifacts/real_evolution_boundary_evidence_v1/records.json`

### Verification
- boundary focused tests：
  - `2` 个通过
- infer 环境全量测试：
  - `143` 个通过
- 正式 boundary 分析：
  - `2 methods x 2 seeds`
  - `11` 个 impossible shadows，全部由 dev panel 的 negative near-orbit 派生

### Interpretation
- 这轮把 boundary 证据正式落地了：当前 strongest scaffold baseline 在 visible negatives 上是 `NOS=1.000`，但一旦把同样的 negative admissible action 放回 clean surface，它会 `100%` 回到 execute。
- retained learned route 也没有越过这条边界，只是偶尔会把 shadow 样本压成 `ask_clarification`，`impossible_shadow_CAA` 也只有 `0.136`。
- 所以当前最强 empirical claim 必须明确限定为：`schema-visible description / contract cue` 足以支撑 real API evolution 下的 positive invariance 与 negative inhibition；它不能被表述成“已经解决 hidden backend shift”。

## 2026-03-15 - Frozen Blind Review v1

### Goal
- 在 blind panel 已冻结后，停止继续扩 family 或做 blind-side 方法搜索。
- 只对唯一保留的方法主线做首轮最终复核：strongest scaffold baseline 与 retained learned route。

### Code
- `src/toolshift/blind_review.py`
  - 新增 blind review 的 train-example selection 与 per-family summary helper
- `scripts/run_blind_review.py`
  - 新增 `dev panel` 训练、`frozen blind panel` 复核入口
- `tests/test_blind_review.py`
  - 新增 blind review focused tests

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_blind_review
python -m compileall src tests scripts/run_blind_review.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_blind_review.py --dev-benchmark data/real_evolution_benchmark.json --blind-benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_review_v1 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Methods
- strongest scaffold baseline:
  - `semantic_embedding_capability_gate`
- retained learned route:
  - `semantic_clause_localization_capability_gate`

### Results

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | 0.917 | 0.958 | 1.000 | 0.727 | 1.000 | 0.979 |
| `semantic_clause_localization_capability_gate` | 0.781 | 0.708 | 0.885 | 0.818 | 0.885 | 0.979 |

Per-family highlights:
- `semantic_embedding_capability_gate`
  - `github_rest`: `CAA=1.000 / NOS=1.000`
  - `youtube`: `CAA=1.000 / NOS=1.000`
  - `slack_auth`: `CAA=0.875 / NOS=0.000`
  - `gitlab_rest`: `CAA=0.875 / NOS=0.500`
  - `trello`: `CAA=0.875 / NOS=0.500`
- `semantic_clause_localization_capability_gate`
  - `github_rest`: `CAA=0.938 / NOS=1.000`
  - `slack_auth`: `CAA=0.750 / NOS=1.000`
  - `trello`: `CAA=0.625 / CAA+=0.750 / NOS=0.750`
  - `youtube_channels`: `CAA=0.750 / CAA+=0.500 / NOS=1.000`

Artifacts:
- `artifacts/real_evolution_blind_review_v1/summary.json`
- `artifacts/real_evolution_blind_review_v1/summary.md`
- `artifacts/real_evolution_blind_review_v1/records.json`

### Verification
- blind review focused tests：
  - `3` 个通过
- infer 环境全量测试：
  - `146` 个通过
- blind review 正式设置：
  - `dev panel` 全量 core examples 训练
  - `frozen blind panel` 一次性复核
  - `2 methods x 2 seeds`

### Interpretation
- strongest scaffold baseline 在 frozen blind panel 上仍然是当前主线最强方法，但 dev-panel 的满分在 blind 上被明显拉回，说明 blind review 是必要的，不是形式步骤。
- retained learned route 的 blind `NOS` 更高（`0.818 > 0.727`），但这是用更差的 `CAA_clean / CAA+ / POC` 换来的；它没有推翻 strongest scaffold baseline 的主线地位。
- 当前 blind review 给出的最准确结论是：`semantic_embedding_capability_gate` 仍是 strongest retained method，但 strongest empirical story 也必须如前所述严格限定在 `schema-visible capability-gap inhibition`，并承认 blind `auth/scope/permission` family 仍是明显压力点。

## 2026-03-15 - Dev vs Blind Retained Methods v1

### Goal
- 在 frozen blind review 之后，不再新增方法分支，而是把 retained methods 的 `dev panel -> blind panel` 落差正式量化。
- 用统一的 comparison artifact 收束最终 framing： strongest scaffold baseline 的 blind 掉点到底来自哪里，retained learned route 又保住了什么。

### Code
- `src/toolshift/panel_review.py`
  - 新增 dev/blind summary 统一读取与 family-level metric helper
  - 增加 family metric alias 映射，避免 blind family `CAA` 与 aggregate `CAA_overall` 混名
- `scripts/compare_dev_blind_retained_methods.py`
  - 新增 retained methods 的 dev-vs-blind comparison 入口
- `tests/test_panel_review.py`
  - 新增 comparison helper focused tests

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_panel_review
python -m compileall src tests scripts/compare_dev_blind_retained_methods.py
PYTHONPATH=src python scripts/compare_dev_blind_retained_methods.py --dev-summary artifacts/real_evolution_family_holdout_clause_localization_capability_v1/summary.json --blind-summary artifacts/real_evolution_blind_review_v1/summary.json --output-dir artifacts/real_evolution_dev_vs_blind_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Methods
- strongest scaffold baseline:
  - `semantic_embedding_capability_gate`
- retained learned route:
  - `semantic_clause_localization_capability_gate`

### Results

| Method | Dev CAA | Blind CAA | dCAA | Dev CAA_clean | Blind CAA_clean | dCAA_clean | Dev CAA+ | Blind CAA+ | dCAA+ | Dev NOS | Blind NOS | dNOS | Dev POC | Blind POC | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | 1.000 | 0.917 | -0.083 | 1.000 | 0.958 | -0.042 | 1.000 | 1.000 | 0.000 | 1.000 | 0.727 | -0.273 | 1.000 | 1.000 | 0.000 |
| `semantic_clause_localization_capability_gate` | 0.875 | 0.781 | -0.094 | 0.917 | 0.708 | -0.208 | 0.820 | 0.885 | +0.065 | 0.864 | 0.818 | -0.045 | 0.820 | 0.885 | +0.065 |

Blind family minima:
- `semantic_embedding_capability_gate`
  - lowest blind `NOS`: `slack_auth = 0.000`
  - lowest blind `CAA_overall`: `gitlab_rest = 0.875`
- `semantic_clause_localization_capability_gate`
  - lowest blind `NOS`: `gitlab_rest = 0.500`
  - lowest blind `CAA_positive`: `youtube_channels = 0.500`
  - lowest blind `CAA_overall`: `trello = 0.625`

Artifacts:
- `artifacts/real_evolution_dev_vs_blind_v1/summary.json`
- `artifacts/real_evolution_dev_vs_blind_v1/summary.md`

### Verification
- panel-review focused tests：
  - `3` 个通过
- infer 环境全量测试：
  - `148` 个通过
- comparison 正式设置：
  - dev summary 读取 `artifacts/real_evolution_family_holdout_clause_localization_capability_v1/summary.json`
  - blind summary 读取 `artifacts/real_evolution_blind_review_v1/summary.json`
  - 仅比较两条 retained methods，不在 blind panel 上做新方法选择

### Interpretation
- strongest scaffold baseline 的 blind drop 主要不是 `CAA+ / POC`，而是 `NOS`：从 dev `1.000` 掉到 blind `0.727`，并且最明显的压力来自 `slack_auth`。
- retained learned route 的 blind `NOS` 更稳，`dev -> blind` 只掉了 `0.045`；但这不是更强方法，因为它从一开始就用更差的 `CAA_clean / CAA+ / POC` 换来了更保守的决策。
- 因此当前最终 framing 应写成：
  - strongest retained method 仍是 `semantic_embedding_capability_gate`
  - strongest empirical story 是 `schema-visible capability-gap inhibition`
  - blind review 说明这条 story 真实成立，但在 `auth/scope/permission semantics` 上仍有明显压力点

## 2026-03-16 - Teacher-Distilled Bottleneck SCC Decisive Run v1

### Goal
- 按 `history/decisive_method_run.md` 的唯一允许路线，完成一次正式 `3-seed` dev-panel decisive run。
- 固定对照为 `SeedOnly / AugOnly / TeacherDistilledBottleneckSCC`，确认是否值得进入 blind review。

### Code
- `src/toolshift/embedding_policy.py`
  - 新增 `teacher_distilled_bottleneck_scc`
  - 在 `ActionBottleneckModel` 上增加 `slot / gap` 头，并蒸馏 strongest scaffold teacher 的 `control / tool / slot / gap`
  - 新增 `seed_only` control 分支
- `scripts/run_matched_budget_pilot.py`
  - 接入 `lambda_slot / lambda_distill_*` 配置
- `src/toolshift/decision_probe.py`
  - 新增 `EmbeddingPolicyAgent` 的 decision-state 提取
- `scripts/run_decision_probe.py`
  - 从只支持 `SemanticGateAgent` 改为支持本轮 bottleneck agent
- `tests/test_embedding_policy_utils.py`
  - 新增 `seed_only` 与 `teacher_distilled_bottleneck_scc` focused tests
- `tests/test_decision_probe.py`
  - 新增 `EmbeddingPolicyAgent` probe focused test

### Commands
```bash
python -m compileall src tests scripts/run_matched_budget_pilot.py scripts/run_decision_probe.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_embedding_policy_utils
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_decision_probe
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_matched_budget_pilot.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_teacher_distilled_v1 --methods seed_only aug_only teacher_distilled_bottleneck_scc --regimes family_holdout_cv --seeds 0 1 2 --torch-threads 8
PYTHONPATH=src python scripts/diagnose_saved_records.py --records artifacts/real_evolution_family_holdout_teacher_distilled_v1/records.json --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_family_holdout_teacher_distilled_v1_diagnostics --regime family_holdout_cv
PYTHONPATH=src python scripts/compare_fixed_panel_methods.py --records artifacts/real_evolution_family_holdout_teacher_distilled_v1/records.json --benchmark data/real_evolution_benchmark.json --regime family_holdout_cv --methods aug_only teacher_distilled_bottleneck_scc --output-dir artifacts/real_evolution_factorized_compare_teacher_distilled_vs_aug_only_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_masking_sensitivity.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_masking_sensitivity_teacher_v1 --methods aug_only teacher_distilled_bottleneck_scc --seeds 0 1 2 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_decision_probe.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_decision_probe_teacher_v1 --methods aug_only teacher_distilled_bottleneck_scc --seeds 0 1 2 --torch-threads 8
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Results

Main dev table (`family_holdout_cv`, `72` core views per seed / `216` paired eval views aggregate):

| Method | CAA | CAA_clean | CAA+ | NOS | POC | Coverage | Selective Risk | Action-State Sim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `seed_only` | 0.083 | 0.000 | 0.000 | 0.545 | 0.000 | 1.000 | 0.917 | 0.985 |
| `aug_only` | 0.093 | 0.000 | 0.000 | 0.606 | 0.000 | 1.000 | 0.907 | 0.965 |
| `teacher_distilled_bottleneck_scc` | 0.102 | 0.009 | 0.000 | 0.636 | 0.000 | 0.995 | 0.902 | 0.943 |

Main takeaways:
- 相对 `AugOnly`，`TeacherDistilledBottleneckSCC` 只带来极小的 overall lift：
  - `CAA: 0.093 -> 0.102`
  - `NOS: 0.606 -> 0.636`
  - `CAA+ / POC: 0.000 -> 0.000`
- `coverage` 反而略降：`1.000 -> 0.995`
- 这轮没有满足 decisive run 的 go-to-blind 条件；尤其 `CAA+` 与 `POC` 完全没有被救回

Diagnostics:
- `seed_only`
  - `group_counts={"control_policy_error":156,"correct":18,"tool_choice_error":42}`
  - `bucket_counts={"missed_execute_ask_clarification":153,"wrong_tool_choice":42,"correct_non_execute":18,"wrong_non_execute_policy":3}`
- `aug_only`
  - `group_counts={"control_policy_error":159,"correct":20,"tool_choice_error":37}`
  - `bucket_counts={"missed_execute_ask_clarification":156,"wrong_tool_choice":37,"correct_non_execute":20,"wrong_non_execute_policy":3}`
- `teacher_distilled_bottleneck_scc`
  - `group_counts={"control_policy_error":160,"correct":22,"tool_choice_error":34}`
  - `bucket_counts={"missed_execute_ask_clarification":157,"wrong_tool_choice":34,"correct_non_execute":21,"wrong_non_execute_policy":3,"correct_execute":1}`

Paired compare (`teacher_distilled_bottleneck_scc` vs `aug_only`):
- `improved_pair_count=2`
- `regressed_pair_count=0`
- 唯一明显修复集中在 `stripe_update_subscription_source`
  - `clean`: `wrong_tool_choice -> correct_execute`
  - `negative_source_removed`: `wrong_tool_choice -> correct_non_execute`
- `strictly_fixed_views=['stripe_update_subscription_source::negative_source_removed']`

Masking sensitivity (`AugOnly` vs `TeacherDistilled`):
- `aug_only`
  - `unmasked`: `CAA=0.093 / CAA+=0.000 / NOS=0.606 / POC=0.000`
  - `name_mask`: `CAA=0.097 / NOS=0.636`
  - `description_mask`: `CAA=0.093 / NOS=0.576`
  - `contract_mask`: `CAA=0.093 / NOS=0.576`
- `teacher_distilled_bottleneck_scc`
  - `unmasked`: `CAA=0.102 / CAA+=0.000 / NOS=0.636 / POC=0.000`
  - `name_mask`: `CAA=0.111 / CAA+=0.013 / NOS=0.697 / POC=0.013`
  - `description_mask`: `CAA=0.102 / NOS=0.606`
  - `contract_mask`: `CAA=0.102 / NOS=0.606`

Decision-state probe (`AugOnly` vs `TeacherDistilled`):

| Method | CAA | CAA+ | NOS | POC | Probe Acc | Probe Neg Recall | Pos Sim | Neg Sim | Gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `aug_only` | 0.093 | 0.000 | 0.606 | 0.000 | 0.611 | 0.278 | 0.944 | 0.906 | 0.038 |
| `teacher_distilled_bottleneck_scc` | 0.102 | 0.000 | 0.636 | 0.000 | 0.602 | 0.333 | 0.882 | 0.858 | 0.024 |

Artifacts:
- `artifacts/real_evolution_family_holdout_teacher_distilled_v1/summary.json`
- `artifacts/real_evolution_family_holdout_teacher_distilled_v1/records.json`
- `artifacts/real_evolution_family_holdout_teacher_distilled_v1_diagnostics/summary.json`
- `artifacts/real_evolution_factorized_compare_teacher_distilled_vs_aug_only_v1/summary.json`
- `artifacts/real_evolution_masking_sensitivity_teacher_v1/summary.json`
- `artifacts/real_evolution_decision_probe_teacher_v1/summary.json`

### Verification
- `tests.test_embedding_policy_utils`：通过
- `tests.test_decision_probe`：通过
- infer 环境全量测试：`153` 个通过
- 正式实验设置：
  - benchmark：`data/real_evolution_benchmark.json`
  - regime：`family_holdout_cv`
  - methods：`seed_only / aug_only / teacher_distilled_bottleneck_scc`
  - seeds：`0 1 2`

### Interpretation
- 这次 decisive run 已经足够给出 `No-Go` 结论：`TeacherDistilledBottleneckSCC` 没有满足任何值得进入 blind 的关键门槛。
- 失败不是工程没通，而是方法形态本身没有解决 proposal 想要的双目标：
  - `NOS` 只比 `AugOnly` 小幅增加 `+0.030`
  - `CAA+ / POC` 仍然完全为 `0`
- diagnostics 说明主失败仍然是 `missed_execute_ask_clarification`，不是 teacher supervision 不足以拟合 train fold；train 端 `tool / slot / gap` 几乎全对，但 held-out family 上没有转成 execute retention。
- masking 进一步说明这条路线没有学到 strongest scaffold baseline 的核心 inductive bias：
  - `name_mask` 不伤，甚至略有提升
  - `description_mask / contract_mask` 也几乎不伤 `CAA / POC`
  - 这不是 “更鲁棒”，而是说明它根本还没进入 description/contract grounded regime
- decision-state probe 也没有形成更强的 positive/negative 几何结构：
  - `probe_neg_recall` 虽然略高于 `AugOnly`
  - 但 `positive_state_similarity` 更低、`state_separation_gap` 更小
- 因此，`teacher_distilled canonical-bottleneck SCC` 这次唯一允许的 decisive run 已经完成且失败。后续不再继续扩展 SCC 主方法线；当前 paper 主线应正式收束为：
  - `benchmark / protocol + diagnosis + strong scaffold baseline`

## 2026-03-16 External Benchmark + Baseline Strengthening

### Goal
- 正面回应 benchmark-paper review 里最致命的两条缺口：
  1. 缺少社区 benchmark/case 的 protocol bridge
  2. 缺少外部公开模型 baseline

### Asset Survey
- `ToolEVO / ToolQA-D`
  - 公开 repo 与数据：`https://github.com/Chen-GX/ToolEVO`
  - 优点：最贴 `tool/API evolution`
  - 当前阻碍：公开 `test_data` 仅发布 question-answer pairs；真正的 API 演化逻辑主要在环境代码 `inference/src/api_vary.py` / `inference_gpt/src/api_vary.py` 里，缺少可直接桥接成 canonical action case 的公开 tool-call traces
  - 结论：保留为后续 evolution-specific bridge 候选，但不作为第一条可复现实装路径
- `API-Bank`
  - 公开 repo 与数据：`https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank`
  - 优点：样本是 runnable tool-use dialogues，显式包含 `API` turns、`api_name`、`param_dict`
  - 结论：作为第一条 community benchmark bridge
- `BFCL / Gorilla`
  - 公开 repo：`https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard`
  - 优点：社区可比性强、测试类别丰富
  - 当前定位：更适合作为 baseline / ecosystem 对照，而不是直接作为 first-pass canonical-action import source
- `ToolBench`
  - 公开 repo：`https://github.com/OpenBMB/ToolBench`
  - 优点：规模大、真实 API 丰富
  - 当前阻碍：原生评测依赖 RapidAPI/toolenv 和长轨迹 answer data，接入成本显著高于 API-Bank
  - 结论：保留为后续 larger-scale external bridge 候选

### Code
- `src/toolshift/api_bank_import.py`
  - 新增 `API-Bank -> TOOLSHIFT` 桥接逻辑
  - 从公开 sample dialogues 提取 final API action、dialogue context、tool specs 与 tool bundles
- `scripts/import_api_bank_benchmark.py`
  - 生成 `data/api_bank_toolshift_benchmark.json` 与 `history/api_bank_import_audit.md`
- `tests/test_api_bank_import.py`
  - 新增 focused tests，验证 imported suite 计数、family tags、view generation 与 oracle correctness
- `scripts/run_qwen_seed_pilot.py`
  - 现可作为通用 benchmark runner 使用，不再只限定 seed benchmark
  - 支持 `--agent-name`

### Commands
```bash
PYTHONPATH=src python scripts/import_api_bank_benchmark.py
PYTHONPATH=src python -m unittest tests.test_api_bank_import
python -m compileall src tests scripts/import_api_bank_benchmark.py scripts/run_qwen_seed_pilot.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/api_bank_toolshift_benchmark.json --output-dir artifacts/api_bank_seed_pilot_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --benchmark data/real_evolution_benchmark.json --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --output-dir artifacts/real_evolution_qwen3_8b_v1 --device-map cuda:0 --disable-thinking --agent-name qwen3_8b_prompt_real
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --output-dir artifacts/real_evolution_blind_qwen3_8b_v1 --device-map cuda:1 --disable-thinking --agent-name qwen3_8b_prompt_blind
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --benchmark data/api_bank_toolshift_benchmark.json --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --output-dir artifacts/api_bank_qwen3_8b_v1 --device-map cuda:2 --disable-thinking --agent-name qwen3_8b_prompt_api_bank
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Results

#### API-Bank bridge benchmark
- generated asset:
  - `data/api_bank_toolshift_benchmark.json`
  - `history/api_bank_import_audit.md`
- structure:
  - `12 cases`
  - `19 tools`
  - `84 views`
  - `72 core + 12 impossible`
  - family tags: `api_bank_organizer / api_bank_service / api_bank_utility`

`artifacts/api_bank_seed_pilot_v1/summary.json`

| method | CAA | CAA+ | NOS | POC | coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| `oracle` | 1.000 | 1.000 | 1.000 | 1.000 | 0.833 |
| `lexical_shortcut` | 0.458 | 0.417 | 0.542 | 0.417 | 0.847 |
| `description_grounded` | 0.778 | 0.722 | 0.875 | 0.667 | 1.000 |

Main takeaways:
- imported external benchmark bridge 不是空壳；当前 `description_grounded` 与 `lexical_shortcut` 之间有明显可测差异
- `description_grounded` 在 static external bridge 上表现出强 `NOS`，但仍未达到 oracle；这说明 bridge benchmark 既非 trivial，也不只是在复写 TOOLSHIFT 原生 panel

#### External open-model baseline: `Qwen3-8B`

`artifacts/real_evolution_qwen3_8b_v1/summary.json`
- `CAA=0.931 / CAA_clean=0.972 / CAA+=0.960 / NOS=0.727 / POC=0.960 / coverage=0.917`

`artifacts/real_evolution_blind_qwen3_8b_v1/summary.json`
- `CAA=0.875 / CAA_clean=0.958 / CAA+=0.923 / NOS=0.636 / POC=0.923 / coverage=0.854`

`artifacts/api_bank_qwen3_8b_v1/summary.json`
- `CAA=0.486 / CAA_clean=0.667 / CAA+=0.667 / NOS=0.125 / POC=0.667 / coverage=0.986`

Comparison against strongest retained scaffold baseline:
- on `real_evolution dev panel`
  - strongest scaffold baseline: `CAA=1.000 / CAA+=1.000 / NOS=1.000 / POC=1.000`
  - `Qwen3-8B`: `CAA=0.931 / CAA+=0.960 / NOS=0.727 / POC=0.960`
- on frozen blind panel
  - strongest scaffold baseline: `CAA=0.917 / CAA+=1.000 / NOS=0.727 / POC=1.000`
  - `Qwen3-8B`: `CAA=0.875 / CAA+=0.923 / NOS=0.636 / POC=0.923`

Interpretation:
- external open-model baseline 现在不再缺席，而且结果不是 trivial fail
- `Qwen3-8B` 在 `CAA_clean / CAA+ / POC` 上明显强于早期 learned-route attempts，但在 `NOS` 上仍明显落后于 strongest scaffold baseline
- blind panel 上也维持同样模式：不是完全崩掉，但仍没有超过 strongest scaffold baseline
- 这让当前 strongest story 更可信：
  - TOOLSHIFT 不只是“对自家 retained methods 难”
  - 它也对公开强模型 baseline 提出了真实的 negative inhibition 压力

### Verification
- `tests.test_api_bank_import`：通过
- infer 环境全量测试：`169` 个通过
- `python -m compileall src tests scripts/import_api_bank_benchmark.py scripts/run_qwen_seed_pilot.py`：通过

### Notes
- superseded external baseline path:
  - 2026-03-16 尝试直接使用公开 `Gorilla OpenFunctions` hosted endpoint
  - `http://luigi.millennium.berkeley.edu:8000/v1/chat/completions`
  - 返回 `HTTP 502`
  - 因而没有把 hosted endpoint 作为主结果；当前主结果改用可在本地复现的 `Qwen3-8B`

## 2026-03-16 External Comparability: BFCL Bridge + Qwen3-8B

### Why
- 当前 benchmark-paper 风险已经很明确：外部 baseline 与社区 benchmark 可比性不足。
- 这轮目标是同时补两条证据：
  1. 用公开社区 benchmark 数据构造一个 TOOLSHIFT protocol bridge
  2. 用公开强模型 baseline 跑 TOOLSHIFT blind panel，而不是只比较自家方法族

### Code
- `src/toolshift/bfcl_bridge.py`
  - 新增 BFCL v4 JSONL 拉取、scalar-compatible 过滤、possible-answer 展开、TOOLSHIFT schema/case/view 生成
- `scripts/generate_bfcl_bridge_benchmark.py`
  - 生成 `data/bfcl_bridge_benchmark.json`、`data/bfcl_bridge_audit.json`、`history/bfcl_bridge_audit.md`
- `scripts/run_bfcl_bridge_pilot.py`
  - 在 BFCL bridge 上统一跑 `Oracle / LexicalShortcut / DescriptionGrounded / QwenPromptAgent`
- `scripts/run_qwen_seed_pilot.py`
  - 从 seed-only 文案改成通用 benchmark runner，并新增 `--agent-name`
- `src/toolshift/eval.py`
  - execute path 现在会忽略 view-visible 但不属于 canonical action 的 helper argument，避免外部 execute-heavy baseline 触发 evaluator 内部崩溃
- `tests/test_bfcl_bridge_benchmark.py`
  - 新增 BFCL bridge focused tests
- `tests/test_audit_overrides.py`
  - 新增 non-canonical helper-argument focused test

### Commands
```bash
PYTHONPATH=src python scripts/generate_bfcl_bridge_benchmark.py
PYTHONPATH=src python -m unittest tests.test_bfcl_bridge_benchmark tests.test_audit_overrides
python -m compileall src tests scripts/generate_bfcl_bridge_benchmark.py scripts/run_bfcl_bridge_pilot.py scripts/run_qwen_seed_pilot.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_bfcl_bridge_pilot.py --benchmark data/bfcl_bridge_benchmark.json --output-dir artifacts/bfcl_bridge_pilot_qwen3_8b_v1 --qwen-model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --disable-thinking --device-map cuda:0 --max-new-tokens 256
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_seed_pilot.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_qwen3_8b_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --disable-thinking --device-map cuda:0 --max-new-tokens 256 --agent-name qwen3_8b_blind
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Results

BFCL bridge asset:
- `50 cases / 50 views / 66 tools`
- categories:
  - `simple_python = 10`
  - `multiple = 10`
  - `live_simple = 10`
  - `irrelevance = 10`
  - `live_irrelevance = 10`
- selection policy:
  - first scalar-compatible cases in source order
  - execute categories keep BFCL possible answers as set-valued admissible actions
  - irrelevance categories map to `abstain`

BFCL bridge pilot (`CAA / coverage / selective_risk / contract_validity`):

| Method | CAA | Coverage | Selective Risk | Contract Validity |
| --- | ---: | ---: | ---: | ---: |
| `oracle` | 1.000 | 0.600 | 0.000 | 1.000 |
| `lexical_shortcut` | 0.780 | 0.740 | 0.243 | 1.000 |
| `description_grounded` | 0.580 | 1.000 | 0.420 | 1.000 |
| `qwen3-8b` | 0.840 | 0.640 | 0.250 | 1.000 |

BFCL bridge category breakdown:
- `oracle`
  - `simple_python=1.0`
  - `multiple=1.0`
  - `live_simple=1.0`
  - `irrelevance=1.0`
  - `live_irrelevance=1.0`
- `qwen3-8b`
  - `simple_python=1.0`
  - `multiple=1.0`
  - `live_simple=0.4`
  - `irrelevance=0.9`
  - `live_irrelevance=0.9`

TOOLSHIFT frozen blind (`qwen3_8b_blind`):
- `CAA=0.875`
- `CAA_clean=0.958`
- `CAA+=0.923`
- `NOS=0.636`
- `POC=0.923`
- `coverage=0.854`
- `negative_coverage=0.455`
- `selective_risk=0.122`
- `contract_validity=1.000`

Blind family breakdown for `qwen3_8b_blind`:
- `github_rest`: `CAA=1.0 / CAA+=1.0 / NOS=1.0`
- `gitlab_rest`: `CAA=0.75 / CAA+=1.0 / NOS=0.0`
- `slack_auth`: `CAA=0.875 / CAA+=1.0 / NOS=0.0`
- `trello`: `CAA=0.875 / CAA+=1.0 / NOS=1.0`
- `youtube`: `CAA=0.875 / CAA+=0.5 / NOS=1.0`
- `youtube_channels`: `CAA=0.875 / CAA+=1.0 / NOS=0.5`

Comparison against retained blind methods:
- strongest scaffold baseline (`semantic_embedding_capability_gate`):
  - `CAA=0.917 / CAA+=1.000 / NOS=0.727 / POC=1.000`
- retained learned route (`semantic_clause_localization_capability_gate`):
  - `CAA=0.781 / CAA+=0.885 / NOS=0.818 / POC=0.885`
- external public model (`qwen3_8b_blind`):
  - `CAA=0.875 / CAA+=0.923 / NOS=0.636 / POC=0.923`

This places `Qwen3-8B`:
- clearly above the retained learned route on `CAA / CAA+ / POC`
- but still below the strongest scaffold baseline on all main blind metrics
- and under the same hardest blind families (`slack_auth`, `gitlab_rest`) rather than exposing a completely different failure distribution

Artifacts:
- `data/bfcl_bridge_benchmark.json`
- `data/bfcl_bridge_audit.json`
- `history/bfcl_bridge_audit.md`
- `artifacts/bfcl_bridge_pilot_qwen3_8b_v1/summary.json`
- `artifacts/bfcl_bridge_pilot_qwen3_8b_v1/records.json`
- `artifacts/real_evolution_blind_qwen3_8b_v1/summary.json`
- `artifacts/real_evolution_blind_qwen3_8b_v1/records.json`

### Verification
- `tests.test_bfcl_bridge_benchmark`：通过
- `tests.test_audit_overrides`：通过
- infer 环境全量测试：`169` 个通过

### Interpretation
- BFCL bridge 说明外部公开强模型不是“弱到没有参考意义”的 strawman：
  `Qwen3-8B` 在社区 function-calling benchmark 子集上明显强于内部 lexical/description heuristics，并在 `simple_python / multiple` 上达到 `1.0`。
- 但把同一个公开强模型放到 TOOLSHIFT frozen blind panel 时，结果仍明显落后于 strongest scaffold baseline，尤其在 `slack_auth` 和 `gitlab_rest` 上与 strongest scaffold baseline 暴露相同压力点。
- 因此，当前 TOOLSHIFT 的 blind 难点并不能被解释成“只对作者自家方法族难”；至少一个公开强模型 family 也会在同一批 schema-visible capability-gap cases 上掉分。
- 同时，BFCL bridge 也提供了更可防守的社区可比性：现在可以明确区分
  - 社区静态 function-calling competency
  - 与 real API evolution / capability-gap inhibition competency
- 当前 benchmark-paper strongest claim 仍应保持克制：
  - TOOLSHIFT 不证明自己已经“定义了普适 tool robustness”
  - 但已经能比纯内部对照更有力地说明：real API evolution 下的 schema-visible capability-gap inhibition 是一个和静态 function-calling 不同、且外部公开强模型也会掉分的对象

## 2026-03-16 External Evidence v3: ToolEVO Bridge + Public Qwen Baselines

### Files
- `scripts/generate_toolevo_bridge_benchmark.py`
  - 新增从公开 `ToolEVO / ToolQA-D` 版本映射与 few-shot traces 生成 TOOLSHIFT-compatible external bridge benchmark 的脚本
- `scripts/run_qwen_benchmark.py`
  - 新增通用 public Qwen baseline runner，可直接对任意 TOOLSHIFT benchmark 产出 summary/records
- `tests/test_toolevo_bridge_benchmark.py`
  - 新增 ToolEVO bridge focused tests
- `src/toolshift/eval.py`
  - 新增 graph-edge bundle canonicalization，支持 `NodeInfos / CheckInfos` 这类公开 evolving-tool surface
- `src/toolshift/agents.py`
  - `OracleAgent` 现在会从 `slot_values` 回填 explicit-view optional slots，避免 ToolEVO bridge 这类 bundle-style public surface 产生假性漏参
- `scripts/generate_real_evolution_blind_benchmark.py`
  - 修复 blind GitLab `merge_requests.get_with_changes` 的 canonical slot 漏记：补上 optional `page / page_size`

### Commands
```bash
PYTHONPATH=src python scripts/generate_toolevo_bridge_benchmark.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_toolevo_bridge_benchmark tests.test_real_evolution_blind_benchmark tests.test_blind_panel
python -m compileall src tests scripts/generate_toolevo_bridge_benchmark.py scripts/run_qwen_benchmark.py scripts/generate_real_evolution_blind_benchmark.py
PYTHONPATH=src python scripts/run_seed_pilot.py --benchmark data/toolevo_bridge_benchmark.json --output-dir artifacts/toolevo_bridge_seed_pilot_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/toolevo_bridge_benchmark.json --output-dir artifacts/toolevo_bridge_qwen_prompt_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --disable-thinking --device-map cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/toolevo_bridge_benchmark.json --output-dir artifacts/toolevo_bridge_qwen_prompt_4b_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --disable-thinking --device-map cuda:0 --name qwen_prompt_toolevo_bridge_4b
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_qwen_prompt_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --disable-thinking --device-map cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_qwen_prompt_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --disable-thinking --device-map cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_qwen_prompt_4b_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --disable-thinking --device-map cuda:0 --name qwen_prompt_real_evolution_4b
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_qwen_prompt_4b_v1 --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --disable-thinking --device-map cuda:0 --name qwen_prompt_real_evolution_blind_4b
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Results

ToolEVO bridge asset:
- `11 cases / 44 views / 11 canonical tools / 7 public sources`
- family tags:
  - `toolevo_agenda`
  - `toolevo_scirex`
  - `toolevo_database`
  - `toolevo_graph`
  - `toolevo_code`
- selection policy:
  - requests anchored to public ToolQA-D few-shot traces where available
  - each case exposes `clean legacy`, `positive version1`, `positive version2`, and `negative deprecated legacy surface`
  - negative view policy is `ask_clarification` or `abstain` when only the deprecated legacy contract is visible

ToolEVO bridge structural smoke:
- `oracle`: `CAA=1.000 / CAA+=1.000 / NOS=1.000 / POC=1.000 / coverage=1.000`
- `lexical_shortcut`: `CAA=0.341 / CAA+=0.182 / NOS=0.818 / POC=0.091 / coverage=0.295`
- `description_grounded`: `CAA=0.795 / CAA+=0.727 / NOS=1.000 / POC=0.727 / coverage=0.636`

Public Qwen baselines on ToolEVO bridge:
- `Qwen3-0.6B`:
  - `CAA=0.318 / CAA_clean=0.091 / CAA+=0.091 / NOS=1.000 / POC=0.091 / coverage=1.000`
- `Qwen3-4B`:
  - `CAA=0.844 / CAA_clean=1.000 / CAA+=0.938 / NOS=0.500 / POC=0.875 / coverage=0.875`

Public Qwen baselines on TOOLSHIFT dev/blind:
- `Qwen3-0.6B` dev:
  - `CAA=0.208 / CAA_clean=0.083 / CAA+=0.120 / NOS=0.818 / POC=0.120 / coverage=1.000`
- `Qwen3-0.6B` blind:
  - `CAA=0.292 / CAA_clean=0.125 / CAA+=0.077 / NOS=0.909 / POC=0.077 / coverage=1.000`
- `Qwen3-4B` dev:
  - `CAA=0.847 / CAA_clean=0.944 / CAA+=0.960 / NOS=0.273 / POC=0.960 / coverage=0.972`
- `Qwen3-4B` blind:
  - `CAA=0.812 / CAA_clean=0.958 / CAA+=0.923 / NOS=0.364 / POC=0.923 / coverage=0.917`

Blind family breakdown for `Qwen3-4B`:
- `github_rest`: `CAA=0.875 / CAA+=1.000 / NOS=0.500`
- `gitlab_rest`: `CAA=0.750 / CAA+=1.000 / NOS=0.000`
- `slack_auth`: `CAA=0.875 / CAA+=1.000 / NOS=0.000`
- `trello`: `CAA=0.750 / CAA+=1.000 / NOS=0.500`
- `youtube`: `CAA=0.875 / CAA+=0.500 / NOS=1.000`
- `youtube_channels`: `CAA=0.750 / CAA+=1.000 / NOS=0.000`

Blind GitLab compatibility fix:
- `Qwen3-4B` blind run first exposed a latent protocol bug:
  - `merge_requests.diffs.list` surfaced optional `page / per_page`
  - the bridge benchmark had `per_page -> page_size` but missed canonical slot `page`
- after regenerating blind data with optional `page / page_size` on `gitlab.merge_requests.get_with_changes`, the public-model run completed normally

Artifacts:
- `data/toolevo_bridge_benchmark.json`
- `data/toolevo_bridge_audit.json`
- `history/toolevo_bridge_audit.md`
- `artifacts/toolevo_bridge_seed_pilot_v1/summary.json`
- `artifacts/toolevo_bridge_qwen_prompt_v1/summary.json`
- `artifacts/toolevo_bridge_qwen_prompt_4b_v1/summary.json`
- `artifacts/real_evolution_qwen_prompt_v1/summary.json`
- `artifacts/real_evolution_blind_qwen_prompt_v1/summary.json`
- `artifacts/real_evolution_qwen_prompt_4b_v1/summary.json`
- `artifacts/real_evolution_blind_qwen_prompt_4b_v1/summary.json`

### Verification
- `tests.test_toolevo_bridge_benchmark`：通过
- `tests.test_real_evolution_blind_benchmark`：通过
- `tests.test_blind_panel`：通过
- infer 环境全量测试：`169` 个通过

### Interpretation
- BFCL bridge 已经提供了“外部静态 function-calling benchmark + 强公开模型”的一条证据链；ToolEVO bridge 现在补上了一个更贴 evolving-tool setting 的公开 benchmark 源。
- ToolEVO bridge 的 public results 说明：公开模型在明确的 public evolving-tool surface 上可以拿到很高的 `CAA+`，但 `NOS` 仍会在更 drift-heavy 的 view 上下降。它更像 external portability evidence，而不是 TOOLSHIFT blind panel 的替代品。
- `Qwen3-4B` 在 TOOLSHIFT dev/blind 上的结果说明：
  - 外部公开模型并不是弱 strawman
  - 它可以把 `CAA_clean / CAA+ / POC` 拉到接近强 retained baselines 的水平
  - 但在 blind negatives 上仍会在 `slack_auth / gitlab_rest / youtube_channels` 这些 capability-gap families 失守
- 因而，当前 TOOLSHIFT 的 hardest object 不能被解释成“只对作者自家方法族难”；至少一个公开强模型也在同一批 schema-visible capability-gap cases 上掉分。

## 2026-03-16 Protocol Reliability + Blind Stability

### Files
- `src/toolshift/reliability.py`
  - 新增 benchmark protocol / record loading 公共分析 helper
- `src/toolshift/protocol_reliability.py`
  - 新增 split-sensitivity 与 benchmark structure 审计逻辑
- `src/toolshift/panel_stability.py`
  - 新增 family/vendor cluster bootstrap 与 leave-one-group-out 稳健性分析
- `scripts/run_protocol_reliability.py`
  - 新增 protocol structure + split-sensitivity runner
- `scripts/run_panel_stability.py`
  - 新增 blind family/vendor bootstrap runner
- `tests/test_protocol_reliability.py`
  - 新增 protocol reliability focused tests
- `tests/test_panel_stability.py`
  - 新增 panel stability focused tests

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_protocol_reliability tests.test_panel_stability
python -m compileall src tests scripts/run_protocol_reliability.py scripts/run_panel_stability.py
PYTHONPATH=src python scripts/run_protocol_reliability.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_protocol_reliability_dev_v1
PYTHONPATH=src python scripts/run_protocol_reliability.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_protocol_reliability_blind_v1 --nested-record scaffold=artifacts/real_evolution_blind_review_v1/records.json:semantic_embedding_capability_gate --flat-record qwen3_8b=artifacts/real_evolution_blind_qwen3_8b_v1/records.json --flat-record qwen3_4b=artifacts/real_evolution_blind_qwen_prompt_4b_v1/records.json
PYTHONPATH=src python scripts/run_panel_stability.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_stability_v1 --nested-record scaffold=artifacts/real_evolution_blind_review_v1/records.json:semantic_embedding_capability_gate --flat-record qwen3_8b=artifacts/real_evolution_blind_qwen3_8b_v1/records.json --flat-record qwen3_4b=artifacts/real_evolution_blind_qwen_prompt_4b_v1/records.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Results

#### 1. Protocol structure is now explicit and auditable

Dev panel (`artifacts/real_evolution_protocol_reliability_dev_v1/summary.json`):
- `36 cases / 72 views / 63 sources / 9 families / 10 vendor signatures`
- action-set histogram:
  - `62` single-action views
  - `10` multi-action views
- all `10` multi-action views are `negative_near_orbit`
- `multi_action_negative_fraction = 10 / 11 = 0.909`
- source support:
  - mean `2.58` official sources per case
  - `34 / 36` cases use mixed source kinds (`reference + guide/changelog`)
  - only `2` cases are single-kind

Blind panel (`artifacts/real_evolution_protocol_reliability_blind_v1/summary.json`):
- `24 cases / 48 views / 42 sources / 6 families / 5 vendors`
- action-set histogram:
  - `38` single-action views
  - `10` multi-action views
- again, all `10` multi-action views are `negative_near_orbit`
- `multi_action_negative_fraction = 10 / 11 = 0.909`
- source support:
  - mean `2.75` official sources per case
  - `23 / 24` cases use mixed source kinds
  - all `24 / 24` cases have at least `2` official sources

This does **not** provide inter-annotator agreement; it does provide a concrete answer to two review questions that were previously under-specified:
- how many views depend on set-valued admissible actions
- how much official-source support backs each case

#### 2. Split sensitivity is material, and it argues for set-valued negative evaluation

Blind split-sensitivity (`artifacts/real_evolution_protocol_reliability_blind_v1/summary.json`):

Canonical protocol:
- `scaffold`: `CAA=0.917 / CAA+=1.000 / NOS=0.727 / POC=1.000 / coverage=0.979`
- `Qwen3-8B`: `CAA=0.875 / CAA+=0.923 / NOS=0.636 / POC=0.923 / coverage=0.854`
- `Qwen3-4B`: `CAA=0.812 / CAA+=0.923 / NOS=0.364 / POC=0.923 / coverage=0.917`

`single_action_only` projection:
- excludes exactly the `10` dual-admissible negative views, leaving `38` core views and `10` ambiguous views
- all three methods jump to `NOS=1.000`
- therefore, a single-action-only core would make blind negative inhibition look artificially solved

`ask_only_negative` projection:
- `scaffold`: `NOS=0.727`
- `Qwen3-8B`: `NOS=0.182`
- `Qwen3-4B`: `NOS=0.091`

`abstain_only_negative` projection:
- `scaffold`: `NOS=0.091`
- `Qwen3-8B`: `NOS=0.545`
- `Qwen3-4B`: `NOS=0.364`

Interpretation:
- absolute `NOS` is highly sensitive to whether dual-control negatives allow `ask_clarification`, `abstain`, or both
- this is exactly why TOOLSHIFT needs a set-valued canonical evaluator rather than an abstain-only protocol
- at the same time, the protocol does **not** hide that choice: the review concern is real, and the sensitivity is now quantified instead of implicit

#### 3. Blind conclusions are family-sensitive, but not single-family artifacts

Blind stability (`artifacts/real_evolution_blind_stability_v1/summary.json`):

Family-cluster bootstrap CIs for `NOS`:
- `scaffold`: point `0.727`, family CI `[0.444, 0.917]`, vendor CI `[0.375, 0.933]`
- `Qwen3-8B`: point `0.636`, family CI `[0.273, 0.917]`, vendor CI `[0.222, 0.917]`
- `Qwen3-4B`: point `0.364`, family CI `[0.091, 0.667]`, vendor CI `[0.111, 0.500]`

Leave-one-family-out:
- `scaffold`:
  - remove `slack_auth` -> `NOS=0.800`
  - remove `gitlab_rest` -> `NOS=0.778`
  - remove `trello` -> `NOS=0.778`
  - remove `youtube` -> `NOS=0.667`
- `Qwen3-8B`:
  - remove `gitlab_rest` -> `NOS=0.778`
  - remove `slack_auth` -> `NOS=0.700`
  - remove `youtube_channels` -> `NOS=0.667`
- `Qwen3-4B`:
  - remove `gitlab_rest` -> `NOS=0.444`
  - remove `slack_auth` -> `NOS=0.400`
  - remove `youtube` -> `NOS=0.222`

Interpretation:
- the review is right that blind conclusions are not “large-N stable”
- but the strongest scaffold baseline’s blind pressure is **not** explained by a single pathological family
- `slack_auth` is the largest single pressure point, yet removing it does not erase the gap; `gitlab_rest` and `trello` still move `NOS` materially

### Verification
- `tests.test_protocol_reliability`: 通过
- `tests.test_panel_stability`: 通过
- infer 环境全量测试：`175` 个通过

### Interpretation
- current TOOLSHIFT still does **not** have annotator-agreement evidence; that remains a real benchmark-paper gap
- but the benchmark is no longer relying on implicit protocol choices:
  - action-set multiplicity is explicit
  - split-policy sensitivity is quantified
  - family/vendor uncertainty is quantified
- the strongest defensible claim becomes narrower and stronger:
  - TOOLSHIFT is a small but now more auditable benchmark for `schema-visible capability-gap inhibition`
  - absolute negative scores depend on whether dual-control negatives permit both `ask_clarification` and `abstain`
  - even under that sensitivity, blind pressure is not a one-family accident, and public Qwen baselines still miss the same hard families

## 2026-03-16 External Evidence v5: Document Retrieval + Rerank Reference Baseline

### Goal
Add one more reviewer-facing external baseline bucket beyond prompt-only public models:
- not another retained internal gate family
- but a `retrieval + rerank` style document-grounded reference system that can run on TOOLSHIFT and the external bridges under the same evaluator

### Code / Outputs
- `src/toolshift/agents.py`
  - new `DocumentRetrievalRerankAgent`
- `src/toolshift/__init__.py`
  - exports the new agent
- `scripts/run_retrieval_baseline.py`
  - generic runner for any TOOLSHIFT-compatible benchmark
- `tests/test_retrieval_baseline.py`
  - focused behavior checks on seed clean / negative views

Artifacts:
- `artifacts/real_evolution_doc_retrieval_v1/summary.json`
- `artifacts/real_evolution_blind_doc_retrieval_v1/summary.json`
- `artifacts/api_bank_doc_retrieval_v1/summary.json`
- `artifacts/toolevo_bridge_doc_retrieval_v1/summary.json`
- `artifacts/bfcl_bridge_doc_retrieval_v1/summary.json`

### Commands
```bash
PYTHONPATH=src python -m unittest tests.test_retrieval_baseline
python -m compileall src tests scripts/run_retrieval_baseline.py
PYTHONPATH=src python scripts/run_retrieval_baseline.py --benchmark data/real_evolution_benchmark.json --output-dir artifacts/real_evolution_doc_retrieval_v1
PYTHONPATH=src python scripts/run_retrieval_baseline.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_doc_retrieval_v1
PYTHONPATH=src python scripts/run_retrieval_baseline.py --benchmark data/api_bank_toolshift_benchmark.json --output-dir artifacts/api_bank_doc_retrieval_v1
PYTHONPATH=src python scripts/run_retrieval_baseline.py --benchmark data/toolevo_bridge_benchmark.json --output-dir artifacts/toolevo_bridge_doc_retrieval_v1
PYTHONPATH=src python scripts/run_retrieval_baseline.py --benchmark data/bfcl_bridge_benchmark.json --output-dir artifacts/bfcl_bridge_doc_retrieval_v1
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Main Results
TOOLSHIFT dev:
- `CAA=0.764 / CAA_clean=0.861 / CAA+=0.840 / NOS=0.273 / POC=0.840 / coverage=0.889`

TOOLSHIFT blind:
- `CAA=0.812 / CAA_clean=0.958 / CAA+=1.000 / NOS=0.273 / POC=1.000 / coverage=0.958`

API-Bank bridge:
- `CAA=0.806 / CAA_clean=0.833 / CAA+=0.833 / NOS=0.750 / POC=0.833 / coverage=0.972`

ToolEVO bridge:
- `CAA=0.719 / CAA_clean=0.875 / CAA+=0.625 / NOS=0.750 / POC=0.625 / coverage=0.688`

BFCL bridge:
- `CAA=0.580 / coverage=1.000 / selective_risk=0.420`

### Interpretation
This baseline is useful, but it does **not** become a new strongest method.

What it adds:
- it directly addresses the review request for a `retrieval + rerank` document-style reference system
- it can be run unchanged on TOOLSHIFT and the imported external bridges
- it shows a different failure profile from prompt-only public models

What it shows:
- on TOOLSHIFT blind, `doc_retrieval_rerank` preserves positive execution surprisingly well (`CAA+=1.000 / POC=1.000`) but still under-inhibits negatives (`NOS=0.273`)
- on API-Bank bridge, the same baseline is strong (`CAA=0.806`) and clearly above the public Qwen3-8B prompt baseline (`CAA=0.486`)
- on ToolEVO bridge and BFCL bridge, however, it does **not** dominate public Qwen:
  - ToolEVO: `0.719` vs Qwen3-4B `0.844`
  - BFCL: `0.580` vs Qwen3-8B `0.840`

Current read:
- retrieval-style doc grounding is a meaningful external baseline bucket and should be reported
- but it does **not** overturn the current paper story
- it behaves more like a `schema-visible documentation retriever` than a robust general tool-use model

### Verification
- `tests.test_retrieval_baseline`: passed
- infer full test suite: `177` passed

### Paper impact
This result is worth surfacing in the benchmark-paper framing because it answers a review concern more directly:
- TOOLSHIFT is now compared not only against retained internal methods and prompt-only public models,
- but also against a document retrieval + rerank reference system,
- and the external evidence still points to the same conclusion:
  current systems can preserve positive execution better than they inhibit negative capability gaps, while the scaffold baseline remains strongest on blind review.

## 2026-03-16 External Evidence v6: Non-Qwen Public Family Sanity Check

### Goal
Add one lightweight non-Qwen public-model sanity check, so the external story does not rest entirely on Qwen-family prompt baselines.

### Code / Outputs
- `src/toolshift/qwen_agent.py`
  - parser now accepts both `arguments` and `parameters` tool-call payloads, which is necessary for some non-Qwen chat models
- `tests/test_qwen_agent_utils.py`
  - new parser coverage for `parameters`

Artifacts:
- `artifacts/real_evolution_blind_llama32_3b_v1/summary.json`
- `artifacts/toolevo_bridge_llama32_3b_v1/summary.json`

### Commands
```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest tests.test_qwen_agent_utils
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/real_evolution_blind_benchmark.json --output-dir artifacts/real_evolution_blind_llama32_3b_v1 --model-path /cephfs/shared/hf_cache/hub/Llama-3.2-3B-Instruct --disable-thinking --device-map cuda:0 --max-new-tokens 256 --name llama32_3b_blind
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python scripts/run_qwen_benchmark.py --benchmark data/toolevo_bridge_benchmark.json --output-dir artifacts/toolevo_bridge_llama32_3b_v1 --model-path /cephfs/shared/hf_cache/hub/Llama-3.2-3B-Instruct --disable-thinking --device-map cuda:0 --max-new-tokens 256 --name llama32_3b_toolevo
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && PYTHONPATH=src python -m unittest discover -s tests
```

### Main Results
TOOLSHIFT blind:
- `Llama-3.2-3B`: `CAA=0.625 / CAA_clean=0.750 / CAA+=0.692 / NOS=0.273 / POC=0.692 / coverage=0.833`

ToolEVO bridge:
- `Llama-3.2-3B`: `CAA=0.500 / CAA_clean=0.250 / CAA+=0.375 / NOS=1.000 / POC=0.125 / coverage=0.438`

### Interpretation
This is not a strong baseline, but it is useful.

What it adds:
- the external evidence is no longer Qwen-only
- a second public model family also fails sharply on the same benchmark family

What it shows:
- on TOOLSHIFT blind, a non-Qwen public model also struggles with the same general pattern: weak overall canonical-action retention and poor negative inhibition (`NOS=0.273`)
- on ToolEVO bridge, the model behaves as an over-conservative blocker: `NOS=1.000` is achieved together with `POC=0.125` and very low coverage

Current read:
- the benchmark difficulty is not an artifact of one public-model family
- public open models remain unstable under evolving-tool evaluation, even before we compare them to the strongest scaffold baseline

### Verification
- `tests.test_qwen_agent_utils`: passed
- infer full test suite: `178` passed
