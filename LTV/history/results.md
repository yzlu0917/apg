# Results Ledger

## 2026-04-08 Round49 Expansion Replay / Harder State Pool

**目标**

把 `state-first` 主线从当前 `11`-state oracle panel 继续扩到更大的 replayable harder-state 候选池，并筛出更适合人工 progress oracle 的 states。

**复查对象**

本轮直接继承并使用已有的 round49 expansion artifacts 作为 harder-state 候选池，未重新 live 重跑生成 / replay。对应文件：

- `data/lean/state_first_expansion_seed_panel_v1.jsonl`
- `artifacts/object_gate_round49/state_first_candidates_expansion_v1.jsonl`
- `artifacts/object_gate_round49/state_first_candidates_expansion_v1_replayed.jsonl`
- `artifacts/object_gate_round49/state_first_candidates_expansion_v1_replayed_summary.json`

**关键输出**

- expansion replay 摘要：
  - `num_states = 15`
  - `num_generated_candidates = 121`
  - `num_replay_ok = 100`
  - `num_replay_error = 21`
- 更适合 hard oracle 的 states 主要落在：
  - `lean_and_left_pos__step1`
  - `lean_double_neg_intro_pos__step2`
  - `lean_and_left_proj_simpa_pos__step1`
  - `lean_and_right_proj_simpa_pos__step1`
  - `lean_eq_trans_show_pos__step2`
  - 以及次一级的 `lean_or_right_pos__step1`

**结论**

- `state-first` 主线已经不再受限于最初 `11`-state panel
- round49 成功提供了一个更大、且包含更多 residual-goal 结构的 harder-state replay pool
- reflexivity / ex-falso 类 rows 仍大多是低信息量，不适合作为下一批主要 oracle 目标

## 2026-04-08 Round50 Hard Oracle Slice / Expanded Panel v2

**目标**

从 round49 harder-state replay pool 中挑出一批高区分度 states 做人工 progress oracle，并验证在更大、更难的 oracle panel 上，frozen hidden 的 pairwise separability 是否仍然成立。

**新增文件**

- `data/annotations/state_first_progress_oracle_batch_v2_hard.jsonl`
- `data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl`
- `artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl`
- `artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl`
- `artifacts/object_gate_round50/deepseek_state_first_panel_v2_sep.json`
- `artifacts/object_gate_round50/goedel_state_first_panel_v2_sep.json`
- `artifacts/object_gate_round50/object_gate_round50_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/evaluate_state_first_pairwise_separability.py
conda run -n infer python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round50/deepseek_state_first_panel_v2_sep.json --device cuda:0
conda run -n infer python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round50/goedel_state_first_panel_v2_sep.json --device cuda:0
```

**关键输出**

- hard oracle slice：
  - `num_states = 6`
  - `num_candidates = 37`
  - tier counts:
    - `solved = 13`
    - `strong_partial = 17`
    - `neutral = 7`
  - pair counts:
    - `ordered = 69`
    - `equivalent = 30`
- expanded panel v2：
  - `num_states = 17`
  - `num_candidates = 104`
  - tier counts:
    - `solved = 38`
    - `strong_partial = 46`
    - `weak_partial = 11`
    - `neutral = 9`
  - pair counts:
    - `ordered = 162`
    - `equivalent = 117`
- DeepSeek:
  - gap task:
    - `linear AUROC = 0.9301`
    - `centroid AUROC = 0.8275`
    - `1NN = 0.8925`
  - direction task:
    - `linear AUROC = 0.9373`
    - `centroid AUROC = 0.9510`
    - `1NN = 0.9630`
- Goedel:
  - gap task:
    - `linear AUROC = 0.8754`
    - `centroid AUROC = 0.8020`
    - `1NN = 0.8746`
  - direction task:
    - `linear AUROC = 0.9427`
    - `centroid AUROC = 0.9486`
    - `1NN = 0.9444`

**结论**

- 数据量变大、难度上升后，object signal 仍然成立
- 当前 object claim 已经不再只是 `11`-state panel 的偶然结果
- 更准确的阶段性结论是：
  - frozen hidden 中的 pairwise progress-difference information
  - 在更大、更难的 `17`-state oracle panel 上
  - 仍然 low-complexity readable，且跨两个 prover family 成立

## 2026-04-08 Round51 Second-Annotator Audit / Consensus Panel

**目标**

对当前 `17`-state oracle panel 引入第二标注员复核，量化 disagreement，并验证 object-level separability 是否会因第二标注员与最小 adjudication 而翻转。

**新增文件**

- `data/annotations/state_first_progress_oracle_panel_v2_second_annotator.jsonl`
- `artifacts/object_gate_round51/oracle_agreement_summary.json`
- `artifacts/object_gate_round51/oracle_disagreements.jsonl`
- `artifacts/object_gate_round51/oracle_adjudication_overrides.json`
- `data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl`
- `artifacts/object_gate_round51/deepseek_state_first_panel_v2_consensus_sep.json`
- `artifacts/object_gate_round51/goedel_state_first_panel_v2_consensus_sep.json`
- `artifacts/object_gate_round51/object_gate_round51_summary.md`

**已执行命令**

```bash
python scripts/compare_state_first_oracles.py --oracle-a data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl --oracle-b data/annotations/state_first_progress_oracle_panel_v2_second_annotator.jsonl --summary-out artifacts/object_gate_round51/oracle_agreement_summary.json --disagreements-out artifacts/object_gate_round51/oracle_disagreements.jsonl
python scripts/adjudicate_state_first_oracles.py --base-oracle data/annotations/state_first_progress_oracle_panel_v2_expanded.jsonl --overrides artifacts/object_gate_round51/oracle_adjudication_overrides.json --output data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl
conda run -n infer python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round51/deepseek_state_first_panel_v2_consensus_sep.json --device cuda:0
conda run -n infer python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round51/goedel_state_first_panel_v2_consensus_sep.json --device cuda:0
```

**关键输出**

- agreement:
  - `num_states = 17`
  - `num_candidates_compared = 104`
  - `candidate_agreement = 0.9135`
  - `agreement_count = 95`
  - `disagreement_count = 9`
- disagreement histogram:
  - exact match: `95`
  - one-tier disagreement: `8`
  - two-tier disagreement: `1`
- disagreement concentrated in:
  - `lean_and_comm_pos__step1`
  - `lean_imp_trans_pos__step3`
  - `lean_and_imp_elim_pos__step1`
  - `lean_and_to_imp_apply_pos__step1`
  - `lean_double_neg_intro_pos__step2`
- consensus panel DeepSeek:
  - gap task:
    - `linear AUROC = 0.9085`
    - `centroid AUROC = 0.8874`
  - direction task:
    - `linear AUROC = 0.9490`
    - `centroid AUROC = 0.9755`
- consensus panel Goedel:
  - gap task:
    - `linear AUROC = 0.8874`
    - `centroid AUROC = 0.8426`
  - direction task:
    - `linear AUROC = 0.9148`
    - `centroid AUROC = 0.9748`

**结论**

- 当前 oracle panel 不是脆弱的单标注员产物
- 第二标注员复核后只出现 `9 / 104` 个 candidate 级分歧
- 做完最小 adjudication 后，object-level separability 结论仍然成立，而且仍跨两个 prover family 成立
- 当前 object gate 已经从“单标注员正结果”升级成“第二标注员 audit 后仍然为正”

## 2026-04-08 Round52 First Pairwise Progress Scorer

**目标**

在 frozen `17`-state consensus oracle panel 上，训练第一版显式 pairwise progress scorer，把 object signal 转成方法层的最小可学习基线。

**新增文件**

- `scripts/train_state_first_progress_scorer.py`
- `artifacts/object_gate_round52/deepseek_state_first_progress_scorer.json`
- `artifacts/object_gate_round52/goedel_state_first_progress_scorer.json`
- `artifacts/object_gate_round52/object_gate_round52_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/train_state_first_progress_scorer.py
conda run -n infer python scripts/train_state_first_progress_scorer.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round52/deepseek_state_first_progress_scorer.json --device cuda:0
conda run -n infer python scripts/train_state_first_progress_scorer.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round52/goedel_state_first_progress_scorer.json --device cuda:0
```

**关键输出**

DeepSeek:

- linear scorer:
  - `ordered_pair_accuracy = 0.9576`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9974`
  - `equivalent_abs_gap_mean = 3.1510`
- MLP scorer:
  - `ordered_pair_accuracy = 0.9330`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9908`
  - `equivalent_abs_gap_mean = 2.2005`

Goedel:

- linear scorer:
  - `ordered_pair_accuracy = 0.9488`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9947`
  - `equivalent_abs_gap_mean = 2.2743`
- MLP scorer:
  - `ordered_pair_accuracy = 0.9237`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9896`
  - `equivalent_abs_gap_mean = 3.0379`

**结论**

- 方法层已经有 first positive baseline：
  - 在 held-out-state 设定下，当前 oracle ordering 已可被显式训练 scorer 恢复
- 当前最强 baseline 不是更复杂的 MLP，而是更简单的 linear scorer
- 主要剩余问题不是 ordered pair recovery，而是 equivalent-pair calibration：
  - 当前 scorer 对相同 tier 的候选仍拉得过开
- 因此 round52 的最合理读法是：
  - `Object gate`: 已过
  - `Method gate`: 已有 first positive baseline
  - `Conversion gate`: 还没开始

## 2026-03-31 Phase 0 Bootstrap / Object Gate Kick-off

**目标**

在不启动大实验的前提下，验证 phase 0 的最小可执行条件是否具备，并冻结 Object gate 的默认起步路线。

**已执行命令**

```bash
conda env list
find /cephfs/shared/hf_cache/hub -maxdepth 1 -type d | sed -e 's|.*/||' | rg 'Qwen3|DeepSeek|Prover|PRM' | sort | head -n 80
find /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B -maxdepth 2 -type d | sort | head -n 20
find /cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B -maxdepth 2 -type d | sort | head -n 20
conda run -n infer python -c "import torch, transformers; print('torch', torch.__version__); print('transformers', transformers.__version__)"
```

**关键输出**

- conda 环境存在：`infer`、`lean`
- `infer` 中 Python 依赖可导入：
  - `torch 2.9.1+cu126`
  - `transformers 4.57.6`
- 本地模型缓存可见：
  - `models--Qwen--Qwen3-1.7B`
  - `Qwen3-4B`
  - `models--deepseek-ai--DeepSeek-Prover-V2-7B`
  - `models--Gen-Verse--ReasonFlux-PRM-7B`
  - 以及若干 prover / reranker 相关模型
- 已定位到可直接使用的 snapshot 根：
  - `/cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b`
  - `/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

**结论**

- phase 0 不存在明显的环境级阻塞
- 当前可以直接进入 `Object gate` 的最小闭环设计与 smoke run 实现
- 默认先走 `Lean-first object loop`，并保留 `CTS-mini` 作为最小 invariance 审计切片

**当前冻结的 go/no-go**

- `Object gate` 通过前，不把 utility / deployment 写成 headline
- `Audit gate` 通过前，不把 object signal 当成已识别的机制结论
- 若 first-pass object signal 不成立，不继续堆更大 recipe，先收缩 claim 或转 fallback

**下一步**

- 冻结 `Lean-mini-v0`
- 跑 `20-50` steps 的 boundary hidden-state extraction smoke run
- 建立 text-only / post-state-only / transition 的最小 baseline 对照

## 2026-03-31 First Boundary Extraction Smoke Run

**目标**

在 `Lean-mini-v0` smoke slice 上，用单一 prover family 跑通第一条 `h^- / h^+ / Δh` 抽取链路，验证 `feature-spec-v0` 能真正落成 artifact。

**新增文件**

- `configs/object_gate/lean_mini_v0.yaml`
- `configs/object_gate/cts_mini_v0.yaml`
- `configs/object_gate/feature_spec_v0.yaml`
- `configs/object_gate/metric_spec_v0.yaml`
- `data/lean/lean_mini_v0_smoke.jsonl`
- `data/cts/cts_mini_v0_seed.jsonl`
- `scripts/extract_boundary_states_smoke.py`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/extract_boundary_states_smoke.py
conda run -n infer python -c "import json; from pathlib import Path; p=Path('data/lean/lean_mini_v0_smoke.jsonl'); rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]; print('records', len(rows)); print('steps', sum(len(r['steps']) for r in rows)); print('neg_steps', sum(1 for r in rows for y in r['local_sound'] if y==0))"
conda run -n infer python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_smoke.jsonl --output-dir artifacts/object_gate_smoke/deepseek_prover_v2_7b --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --device cuda:0
conda run -n infer python -c "import torch; xs=torch.load('artifacts/object_gate_smoke/deepseek_prover_v2_7b/boundary_states.pt'); print('entries', len(xs)); print('first_theorem', xs[0]['theorem_id']); print('first_step', xs[0]['step_index']); print('layers', sorted(xs[0]['h_minus'].keys())); print('dim29', tuple(xs[0]['h_minus']['29'].shape)); print('labels', [x['local_sound'] for x in xs])"
```

**关键输出**

- smoke slice 统计：
  - `records = 8`
  - `steps = 11`
  - `neg_steps = 3`
- DeepSeek-Prover-V2-7B 成功加载，模型层数：
  - `num_hidden_layers = 30`
- 相对层索引 `[-1, -8, -16]` 成功解析为：
  - `[29, 22, 14]`
- 特征抽取成功完成：
  - `steps_extracted = 11`
  - 每层向量维度均为 `4096`
- 产物已写出：
  - `artifacts/object_gate_smoke/deepseek_prover_v2_7b/manifest.json`
  - `artifacts/object_gate_smoke/deepseek_prover_v2_7b/boundary_states.pt`

**运行现象**

- extraction 成功，无需修改脚本逻辑
- 运行时出现 DeepSeek 配置相关 warning：
  - `torch_dtype is deprecated`
  - `rope_scaling` 若干字段类型 warning
- 这些 warning 未阻断 smoke；当前判断为模型配置兼容性提示，不是 phase 0 blocker

**结论**

- `Object gate` 已经从“文档计划”推进到“首条可执行 boundary extraction 管线”
- `feature-spec-v0` 的核心表示 `h^- / h^+ / Δh` 已成功落成 artifact
- 下一步可以直接进入：
  - text-only / post-state-only / transition 三个最小 baseline
  - 更真实的 `Lean-mini-v0` 扩容到 `20-50` steps
  - `CTS-mini-v0` first-pass invariance 读取

## 2026-03-31 First-Pass Object Signal on Lean-mini-v0

**目标**

把 `Lean-mini-v0` 从 smoke slice 扩到 first-pass 规模，并在 group-based leave-one-theorem-out 设置下比较 `text_only`、`post_state_only`、`transition_only` 三个最小 baseline。

**新增文件**

- `data/lean/lean_mini_v0_firstpass.jsonl`
- `scripts/run_object_gate_baselines.py`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/extract_boundary_states_smoke.py scripts/run_object_gate_baselines.py
conda run -n infer python -c "import json; from pathlib import Path; p=Path('data/lean/lean_mini_v0_firstpass.jsonl'); rows=[json.loads(x) for x in p.read_text().splitlines() if x.strip()]; print('records', len(rows)); print('steps', sum(len(r['steps']) for r in rows)); print('neg_steps', sum(1 for r in rows for y in r['local_sound'] if y==0))"
conda run -n infer python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_firstpass.jsonl --output-dir artifacts/object_gate_firstpass/deepseek_prover_v2_7b --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --device cuda:0
conda run -n infer python scripts/run_object_gate_baselines.py --features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --output artifacts/object_gate_firstpass/baseline_results.json
```

**关键输出**

- first-pass slice 统计：
  - `records = 20`
  - `steps = 34`
  - `neg_steps = 7`
- first-pass extraction 成功：
  - `steps_extracted = 34`
  - `resolved_layers = [29, 22, 14]`
- baseline 结果：
  - `text_only`:
    - `AUROC = 0.4762`
    - `accuracy = 0.6471`
    - `brier = 0.3441`
  - `post_state_only`:
    - `AUROC = 0.8095`
    - `accuracy = 0.7059`
    - `brier = 0.2941`
  - `transition_only`:
    - `AUROC = 0.9444`
    - `accuracy = 0.8824`
    - `brier = 0.1176`

**当前读法**

- 在这个 first-pass Lean slice 上，结果方向为：
  - `transition_only > post_state_only > text_only`
- 这支持“transition features 比 text-only 与 post-state-only 更接近 local soundness 对象”的初步方向性证据
- 但这还不是 `Object gate` 的正式通过结论，只能算 `first-pass diagnostic`

**重要 caveat**

- `earliest_fail_localization = 1.0` 对三个 baseline 都成立，当前不应解读为强结果
- 原因是当前 `7` 个负例 theorem 的失败位置几乎都在：
  - 单步 theorem 的唯一一步，或
  - 两步 theorem 的最后一步
- 这使得 earliest-fail 任务当前过于容易，尚不足以区分 baseline

**产物路径**

- first-pass feature artifact：
  - `artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt`
  - `artifacts/object_gate_firstpass/deepseek_prover_v2_7b/manifest.json`
- baseline 结果：
  - `artifacts/object_gate_firstpass/baseline_results.json`

**下一步**

- 扩充更有挑战性的负例位置分布，避免 earliest-fail 退化成末步检测
- 加入 `transition + h_plus` 与 `h_minus / h_plus / delta` 的更完整对照
- 开始在 `CTS-mini-v0` 上读取 first-pass `IG / SS`

## 2026-03-31 CTS-mini-v0 First-Pass Invariance / Sensitivity

**目标**

在不引入大规模数据和 sweep 的前提下，先把 `CTS-mini-v0` 的 paired evaluation 链路跑通，并读取第一版 `IG / SS` 风向。

**新增文件**

- `scripts/evaluate_cts_mini.py`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/evaluate_cts_mini.py
conda run -n infer python -c "import json; rows=[json.loads(x) for x in open('data/cts/cts_mini_v0_seed.jsonl') if x.strip()]; print('pairs', len(rows)); print('types', {k: sum(1 for r in rows if r['type']==k) for k in sorted(set(r['type'] for r in rows))})"
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_mini_eval.json --device cuda:0
```

**关键输出**

- `CTS-mini-v0` 当前 pair 数：
  - `same_semantics = 2`
  - `semantic_flip = 2`
- aggregated first-pass metrics：
  - `text_only`
    - `IG = 0.4552`
    - `SS = -0.2492`
  - `post_state_only`
    - `IG = 0.5000`
    - `SS ~= 0.0`
  - `transition_only`
    - `IG = 0.00046`
    - `SS = 0.9649`

**当前读法**

- 在这个极小 CTS first-pass 上，`transition_only` 同时满足：
  - 对 same-semantics pair 的 score gap 极小
  - 对 semantic-flip pair 的 source-vs-variant 区分显著
- 相比之下：
  - `text_only` 在 same pair 上明显不稳定
  - `post_state_only` 对 semantic flip 几乎没有敏感性
- 这与当前 object claim 的方向是对齐的，而且和 Lean local soundness first-pass 的结论一致

**重要 caveat**

- 当前只有 `4` 个 pair，统计量只能看方向，不能看稳定性
- 多个分数已出现 `0/1` 饱和，说明当前 probe 在这个极小设置上很容易过拟合
- evaluator 使用的是 `source theorem leave-out` 的 probe 打分，已经尽量减少直接记忆 source theorem，但仍不是正式 audit 结论

**逐对结果产物**

- `artifacts/object_gate_firstpass/cts_mini_eval.json`

**下一步**

- 把 `CTS-mini-v0` 从 `4` 对扩到至少一个真正可读方向的小面板

## 2026-03-31 CTS Family-Sliced Audit on Curated / Auto Panels

**目标**

在 provenance 与 family 标签已补齐之后，对 `CTS` 的 curated / auto panel 做 family-sliced audit，判断当前 `transition_only` 的优势到底落在哪些 rewrite / flip family 上，以及哪些 family 仍不支持 object claim。

**新增文件**

- `scripts/audit_cts_families.py`
- `artifacts/object_gate_firstpass/cts_family_audit_curated.json`
- `artifacts/object_gate_firstpass/cts_family_audit_auto.json`
- `artifacts/object_gate_firstpass/cts_family_audit_summary.md`

## 2026-03-31 CTS Round4 Targeted Expansion on Weak Families

**目标**

不再泛化扩量，而是围绕 family audit 暴露出的弱切片，定向补 `wrong_theorem_reference`、`wrong_composition`、`wrong_target_term`，并补一小批 harder same rewrites，然后重跑 CTS eval / family audit。

**新增文件**

- `data/cts/cts_mini_v0_source_steps_round4_targeted.jsonl`
- `data/cts/cts_mini_v0_source_steps_round4_unique.jsonl`
- `scripts/extract_cts_novel_rows.py`
- `artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl`
- `artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl`
- `artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round4.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round4_annotated.jsonl`
- `data/cts/cts_mini_v0_round4_novel_only.jsonl`
- `data/cts/cts_mini_v0_round4_novel_only_annotated.jsonl`
- `artifacts/object_gate_firstpass/cts_auto_panel_round4_eval.json`
- `artifacts/object_gate_firstpass/cts_auto_panel_round4_audit.json`

## 2026-03-31 CTS Round5 Composition Expansion

**目标**

针对 `wrong_composition` 继续做结构上更异质的扩数，不再只依赖 equality-symmetry 类模板；必要时小幅扩充 Lean source theorem，并重跑最小必要 extraction / eval / audit。

**新增文件**

- `data/lean/lean_mini_v0_round5.jsonl`
- `data/cts/cts_mini_v0_source_steps_round5_composition.jsonl`
- `data/cts/cts_mini_v0_round5_manual_only.jsonl`
- `data/cts/cts_mini_v0_round5_manual_only_annotated.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round5_seed.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round5_annotated.jsonl`
- `artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl`
- `artifacts/object_gate_round5/cts_round5_manual_only_eval.json`
- `artifacts/object_gate_round5/cts_round5_manual_only_audit.json`
- `artifacts/object_gate_round5/cts_auto_panel_round5_eval.json`
- `artifacts/object_gate_round5/cts_auto_panel_round5_audit.json`

## 2026-03-31 CTS Round6 Manual Stability Check

**目标**

继续推进 `wrong_composition`，但这一轮不再依赖 API，而是用 manual curated 的 non-equality composition rows 和新的 wrong-target-term rows，检查 round5 的 family 波动到底是不是 source mix 导致。

**新增文件**

- `data/lean/lean_mini_v0_round6.jsonl`
- `data/cts/cts_mini_v0_round6_manual_only.jsonl`
- `data/cts/cts_mini_v0_round6_manual_only_annotated.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round6_seed.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round6_annotated.jsonl`
- `artifacts/object_gate_round6/cts_round6_manual_only_eval.json`
- `artifacts/object_gate_round6/cts_round6_manual_only_audit.json`
- `artifacts/object_gate_round6/cts_auto_panel_round6_eval.json`
- `artifacts/object_gate_round6/cts_auto_panel_round6_audit.json`
- `artifacts/object_gate_round6/cts_round6_summary.md`

**已执行命令**

```bash
conda run -n infer python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_round6.jsonl --output-dir artifacts/object_gate_round6/deepseek_prover_v2_7b --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --device cuda:0
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_round6_manual_only.jsonl --output data/cts/cts_mini_v0_round6_manual_only_annotated.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel_round6_seed.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --output data/cts/cts_mini_v0_auto_panel_round6_annotated.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round6/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round6.jsonl --cts-seed data/cts/cts_mini_v0_round6_manual_only.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round6/cts_round6_manual_only_eval.json --device cuda:0
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round6/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round6.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round6_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round6/cts_auto_panel_round6_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round6/cts_round6_manual_only_eval.json --annotated-panel data/cts/cts_mini_v0_round6_manual_only_annotated.jsonl --output artifacts/object_gate_round6/cts_round6_manual_only_audit.json
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round6/cts_auto_panel_round6_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round6_annotated.jsonl --output artifacts/object_gate_round6/cts_auto_panel_round6_audit.json
```

**关键输出**

- round6 Lean source：
  - `32` records
  - `62` steps
  - `13` negative steps
- round6 full panel：
  - `50` rows
  - `22 same`
  - `28 flip`
- family 覆盖：
  - `wrong_composition = 8`
  - `wrong_target_term = 6`

**关键结果**

- round6 full panel overall：
  - `transition_only`: `IG = 0.3426`, `SS = 0.8057`
  - `post_state_only`: `IG = 0.4091`, `SS = 0.5357`
  - `concat_all`: `IG = 0.3193`, `SS = 0.5357`
- round6 manual-only：
  - `transition_only`: `IG = 0.8031`, `SS = 0.7758`
  - `post_state_only`: `IG = 0.7472`, `SS = 0.7500`
  - `concat_all`: `IG = 0.5000`, `SS = 0.5000`

**family-level 读法**

- `wrong_composition` 明显提升：
  - round5 full panel：
    - `transition_only SS = 0.1667`
  - round6 full panel：
    - `transition_only SS = 0.7294`
- `wrong_target_term` 在 round6 source base 上恢复：
  - round6 full panel：
    - `transition_only SS ~= 1.0`
- 但 same-family 明显变差：
  - full panel `transition_only IG = 0.3426`
  - `reflexivity_style` same-family 上 `transition_only` 的 invariance 很差
  - `other_same_rewrite` 也仍不稳

**结论**

- round6 说明 `transition_only` 在 flip-family 上的支持比之前更强了，特别是 `wrong_composition` 和 `wrong_target_term`
- 但它仍然更像一个强 failure detector，而不是一个干净的 semantic invariant
- 因此当前状态是：
  - flip-side evidence 变强；
  - same-side evidence 仍然不够；
  - `Audit gate` 依旧未过

**产物路径**

- `artifacts/object_gate_round6/cts_round6_summary.md`
- `artifacts/object_gate_round6/cts_round6_manual_only_eval.json`
- `artifacts/object_gate_round6/cts_round6_manual_only_audit.json`
- `artifacts/object_gate_round6/cts_auto_panel_round6_eval.json`
- `artifacts/object_gate_round6/cts_auto_panel_round6_audit.json`
- `artifacts/object_gate_round5/cts_round5_summary.md`

**脚本更新**

- `scripts/annotate_cts_panel.py`
  - `wrong_composition` 扩展为也接受 notes 中的 `composition / nesting / wrong direction`

**已执行命令**

```bash
python -m py_compile scripts/annotate_cts_panel.py scripts/generate_cts_with_api.py scripts/extract_boundary_states_smoke.py scripts/evaluate_cts_mini.py scripts/audit_cts_families.py scripts/build_cts_auto_panel.py scripts/extract_cts_novel_rows.py
conda run -n infer python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_round5.jsonl --output-dir artifacts/object_gate_round5/deepseek_prover_v2_7b --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --device cuda:0
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_round5.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps_round5_composition.jsonl --output artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --prompt-mode targeted_family --temperature 0.2 --sleep-seconds 0.5
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_round5_manual_only.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --output data/cts/cts_mini_v0_round5_manual_only_annotated.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel_round5_seed.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --output data/cts/cts_mini_v0_auto_panel_round5_annotated.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round5/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round5.jsonl --cts-seed data/cts/cts_mini_v0_round5_manual_only.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round5/cts_round5_manual_only_eval.json --device cuda:0
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round5/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round5.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round5_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round5/cts_auto_panel_round5_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round5/cts_round5_manual_only_eval.json --annotated-panel data/cts/cts_mini_v0_round5_manual_only_annotated.jsonl --output artifacts/object_gate_round5/cts_round5_manual_only_audit.json
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round5/cts_auto_panel_round5_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round5_annotated.jsonl --output artifacts/object_gate_round5/cts_auto_panel_round5_audit.json
```

**API 使用量**

- round5 composition API：`1991` tokens
- 当前累计：`22598` tokens

**关键输出**

- round5 Lean source：
  - `24` records
  - `48` steps
  - `9` negative steps
- round5 full panel：
  - `42` rows
  - `18 same`
  - `24 flip`
- `wrong_composition` 覆盖：
  - `3 -> 6`

**关键结果**

- round5 full panel overall：
  - `transition_only`: `IG = 0.1178`, `SS = 0.4897`
  - `concat_all`: `IG = 0.0556`, `SS = 0.3750`
  - `post_state_only`: `IG = 0.1510`, `SS = 0.3337`
- round5 manual-only composition slice：
  - `transition_only`: `IG = 0.0`, `SS = 0.3333`
  - `post_state_only`: `IG = 0.6667`, `SS = 0.3333`
  - `concat_all`: `IG = 0.3333`, `SS = 0.3333`

**family-level 读法**

- `wrong_composition`：
  - round4 full panel：
    - `transition_only SS ~= 0`
  - round5 full panel：
    - `transition_only SS = 0.1667`
    - `post_state_only SS = 0.1667`
    - `text_only SS = 0.1522`
  - round5 manual-only：
    - `transition_only SS = 0.3333`
    - `post_state_only SS = 0.3333`
    - `concat_all SS = 0.3333`
- 这说明 round5 对 `wrong_composition` 是**有改善的**，但还不是“transition 独占优势”的 clean result

**重要不稳定性**

- `wrong_theorem_reference` 继续改善：
  - round5 full panel `transition_only SS = 0.6256`
- 但 `wrong_target_term` 出现回摆：
  - round4 full panel `transition_only SS ~= 1.0`
  - round5 full panel `transition_only SS ~= 0`
  - round5 full panel `text_only SS = 0.9819`
- 这说明 family 结论仍然对 source mix / train slice 有明显敏感性

**结论**

- round5 没有让 `wrong_composition` 彻底过关，但确实把它从“几乎零信号”拉到了“有一点可读信号”
- 同时，`wrong_target_term` 的回摆说明当前 family-level object evidence 仍不稳定
- 因此当前最准确的状态仍然是：
  - `transition_only` 作为总体 flip-sensitive 表示仍然有竞争力；
  - 但 `Audit gate` 依旧未过，主因是 family-level 稳定性不足

**产物路径**

- `artifacts/object_gate_round5/cts_round5_summary.md`
- `artifacts/object_gate_round5/cts_round5_manual_only_eval.json`
- `artifacts/object_gate_round5/cts_round5_manual_only_audit.json`
- `artifacts/object_gate_round5/cts_auto_panel_round5_eval.json`
- `artifacts/object_gate_round5/cts_auto_panel_round5_audit.json`
- `artifacts/object_gate_firstpass/cts_round4_novel_eval.json`
- `artifacts/object_gate_firstpass/cts_round4_novel_audit.json`
- `artifacts/object_gate_firstpass/cts_round4_summary.md`

**脚本更新**

- `scripts/generate_cts_with_api.py`
  - 新增 `targeted_family` prompt mode
  - 支持 source-level `target_same_family` / `target_flip_family` / hint 字段
- `scripts/annotate_cts_panel.py`
  - 新增 `api_targeted_family` provenance 支持
  - 将 `wrong_theorem_reference` 扩展到 `mul_zero / zero_mul`
- `scripts/build_cts_auto_panel.py`
  - 修复 API-derived `pair_id` 冲突：改为 `source + prompt_mode + type + variant_hash`

**已执行命令**

```bash
python -m py_compile scripts/generate_cts_with_api.py scripts/annotate_cts_panel.py scripts/build_cts_auto_panel.py scripts/evaluate_cts_mini.py scripts/audit_cts_families.py scripts/extract_cts_novel_rows.py
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps_round4_targeted.jsonl --output artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl --prompt-mode targeted_family --temperature 0.2 --sleep-seconds 0.5
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps_round4_unique.jsonl --max-sources 5 --output artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl --prompt-mode targeted_family --temperature 0.2 --sleep-seconds 0.5
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps_round4_unique_tail.jsonl --output artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl --prompt-mode targeted_family --temperature 0.2 --sleep-seconds 0.5
conda run -n infer python scripts/build_cts_auto_panel.py --manual-panel data/cts/cts_mini_v0_panel.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl --output data/cts/cts_mini_v0_auto_panel_round4.jsonl
conda run -n infer python scripts/extract_cts_novel_rows.py --reference-panel data/cts/cts_mini_v0_auto_panel.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl --output data/cts/cts_mini_v0_round4_novel_only.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel_round4.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl --output data/cts/cts_mini_v0_auto_panel_round4_annotated.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_round4_novel_only.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl --output data/cts/cts_mini_v0_round4_novel_only_annotated.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_round4_novel_only.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_round4_novel_eval.json --device cuda:0
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round4.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_auto_panel_round4_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_firstpass/cts_round4_novel_eval.json --annotated-panel data/cts/cts_mini_v0_round4_novel_only_annotated.jsonl --output artifacts/object_gate_firstpass/cts_round4_novel_audit.json
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_firstpass/cts_auto_panel_round4_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round4_annotated.jsonl --output artifacts/object_gate_firstpass/cts_auto_panel_round4_audit.json
```

**API 使用量**

- round4 targeted: `4743` tokens
- round4 unique weak: `3045` tokens
- round4 unique tail: `1695` tokens
- round4 合计: `9483` tokens
- 当前累计: `20607` tokens

**关键输出**

- round4 之后的 auto panel：
  - `36` rows
  - `15 same`
  - `21 flip`
- round4 novel-only slice：
  - `8` rows
  - `2 same`
  - `6 flip`
- 弱 family 覆盖提升：
  - `wrong_theorem_reference`: `2 -> 6`
  - `wrong_composition`: `2 -> 3`
  - `wrong_target_term`: `3 -> 4`

**关键结果**

- updated auto panel overall：
  - `transition_only`: `IG = 0.2000`, `SS = 0.6422`
  - `concat_all`: `IG = 0.1333`, `SS = 0.3338`
  - `text_only`: `IG = 0.2270`, `SS = 0.1401`
- round4 novel-only slice：
  - `transition_only`: `IG = 0.0`, `SS = 0.1667`
  - `concat_all`: `IG = 0.0`, `SS = 0.6667`
  - `text_only`: `IG = 0.4849`, `SS = 0.4841`

**family-level 读法**

- 变好的部分：
  - `wrong_theorem_reference` 在 full auto panel 上从几乎无 `transition_only` 信号，提升到：
    - `transition_only SS = 0.5000`
  - `wrong_target_term` 在 full auto panel 上变成：
    - `transition_only SS = 0.99996`
  - `wrong_projection`、`ill_typed_or_malformed`、`goal_mismatch_direct_use` 仍然支持 `transition_only`
- 仍然没解决的部分：
  - `wrong_composition` 依旧几乎没有 `transition_only` 信号：
    - full auto panel：
      - `transition_only SS ~= 0`
      - `text_only SS = 0.0183`
    - round4 novel-only：
      - `transition_only SS = 0`
      - `text_only SS = 0.0858`
- same-family 仍然不干净：
  - 多个 family 的低 `IG` 依然被 `pre_state_only` 或 `concat_all` 吃走
  - 当前不能把 same-family 结果直接解释成更好的 object alignment

**重要 caveat**

- round4 期间发现了 API-derived `pair_id` 冲突；在修复为 `variant_hash` 方案后，已重建并重跑所有 round4 artifact。
- 任何未带 hash 的中间 round4 eval 均应视为 superseded，不用于后续 audit 或结论。
- 当前 same-family 的结论仍高度受小样本与“退化 invariance”影响。

**结论**

- round4 没有推翻主线，但它把结论改得更精确：
  - `transition_only` 在多类 flip family 上确实更强，尤其是 theorem-reference / target-term / projection / ill-typed；
  - 但 `wrong_composition` 仍然是当前最清晰的未解 family；
  - same-family 侧的 object evidence 仍不够干净，`Audit gate` 还不能过。

**产物路径**

- `artifacts/object_gate_firstpass/cts_round4_summary.md`
- `artifacts/object_gate_firstpass/cts_round4_novel_eval.json`
- `artifacts/object_gate_firstpass/cts_round4_novel_audit.json`
- `artifacts/object_gate_firstpass/cts_auto_panel_round4_eval.json`
- `artifacts/object_gate_firstpass/cts_auto_panel_round4_audit.json`

**已执行命令**

```bash
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_firstpass/cts_mini_panel_eval_v2.json --annotated-panel data/cts/cts_mini_v0_panel_annotated.jsonl --output artifacts/object_gate_firstpass/cts_family_audit_curated.json
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_firstpass/cts_auto_panel_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_annotated.jsonl --output artifacts/object_gate_firstpass/cts_family_audit_auto.json
```

**关键输出**

- curated panel：
  - `num_pairs = 20`
  - overall：
    - `transition_only`: `IG = 0.2000`, `SS = 0.6003`
    - `concat_all`: `IG = 0.0`, `SS = 0.5`
    - `text_only`: `IG = 0.2091`, `SS = -0.1308`
- auto panel：
  - `num_pairs = 28`
  - overall：
    - `transition_only`: `IG = 0.0769`, `SS = 0.4418`
    - `concat_all`: `IG = 0.3893`, `SS = 0.4667`
    - `text_only`: `IG = 0.1739`, `SS = 0.0546`

**当前读法**

- `transition_only` 的优势是 family-conditional，不是“对所有 semantic flip 都更好”。
- 当前最支持 `transition_only` 的 same-family 主要出现在 auto panel：
  - `projection_style`
  - `eliminator_style`
  - `reflexivity_style`
- 当前最支持 `transition_only` 的 flip-family 主要是：
  - `wrong_branch`
  - `ill_typed_or_malformed`
  - `goal_mismatch_direct_use`
- 当前不支持把 `transition_only` 写成“全局最优 object representation”，因为它在以下 family 上仍然弱或不稳定：
  - `wrong_theorem_reference`
  - `wrong_composition`
  - `wrong_target_term`
  - 部分 `constructor_notation` same-family

**重要 caveat**

- 多个 family 的样本仍然只有 `1-3` 对，当前 slice 结果只能作为 audit diagnosis，不能当作稳定统计结论。
- `concat_all` 在 curated panel 上出现了 `IG = 0.0` 的漂亮 aggregate，但这不能直接解读为更好的 object signal；它更像是一个需要逐对检查的高风险表示。
- `pre_state_only` 的低 `IG` 在多个 slice 上主要来自“近乎无响应”，不是强 object evidence。

**结论**

- 当前 `Object gate` 还没有被 family-audit 意义下充分通过。
- 更准确的表述是：
  - `transition_only` 对一部分 local soundness / semantic-flip family 确实更贴近目标对象；
  - 但 object claim 仍然是有边界的，尤其在 theorem-reference / composition / target-term 一类 flip 上证据不足。
- 因此下一轮不应继续盲目做大 sweep，而应优先：
  - 增补这些弱 family 的样本；
  - 提高 same/flip family 的难度与异质性；
  - 再判断是否进入更强的 `Audit gate`。

**产物路径**

- `artifacts/object_gate_firstpass/cts_family_audit_curated.json`
- `artifacts/object_gate_firstpass/cts_family_audit_auto.json`
- `artifacts/object_gate_firstpass/cts_family_audit_summary.md`

## 2026-03-31 CTS-mini-v0 Panel Expansion with API

**目标**

把 `CTS-mini-v0` 从原始 `4` 对扩成一个带 provenance 的小 panel，并重新读取 `IG / SS`，看看 first-pass 方向在更真实的 panel 上是否仍然成立。

**新增文件**

- `data/cts/cts_mini_v0_source_steps.jsonl`
- `data/cts/cts_mini_v0_panel.jsonl`
- `scripts/generate_cts_with_api.py`

**API 生成说明**

- 使用了仓库 README 中已有的 endpoint 配置
- 只对 `10` 个 source steps 做了小批量生成
- 当前保留了：
  - 原始 API 候选：`artifacts/cts_generation/cts_mini_v0_api_full.jsonl`
  - 扩展 panel：`data/cts/cts_mini_v0_panel.jsonl`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/generate_cts_with_api.py
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps.jsonl --output artifacts/cts_generation/cts_mini_v0_api_full.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_panel.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_mini_panel_eval.json --device cuda:0
```

**API 使用量**

- source steps: `10`
- API 原始候选行数: `10`
- API 总 token 使用量: `3754`
- 当前未计算货币成本；本轮先以 token 用量记账

**panel 规模**

- 原始 seed `4` 对
- 扩展后 panel `16` 对：
  - `same_semantics = 8`
  - `semantic_flip = 8`

**扩展 panel 的 first-pass 指标**

- `text_only`
  - `IG = 0.1601`
  - `SS = -0.3327`
- `post_state_only`
  - `IG = 0.2497`
  - `SS = 0.3750`
- `transition_only`
  - `IG = 0.2500`
  - `SS = 0.6250`

**当前读法**

- 扩展 panel 之后，结果比 `4` 对 seed 明显更混杂，也更像真实 stress test
- `transition_only` 不再有“几乎零 IG”的漂亮结果，但它仍然给出当前最强的正向 `SS`
- `text_only` 的 `IG` 看起来更低，但其 `SS` 为负，说明它并不是在“稳定地保留语义”，而更像是 source/variant 一起误判
- 因此当前更合理的读法是：
  - `transition_only` 在扩展 panel 上表现为**最平衡的候选**
  - 但 object claim 仍未到“panel 扩大后依然稳定通过”的程度

**重要 caveat**

- panel 里部分 API pair 只做了轻量人工筛入，没有编译器级验证
- API same pair 的 rewrite-source 仍较单一，离 Audit gate 需要的 provenance 多样性还有距离
- 某些分数仍存在 `0/1` 饱和，first-pass probe 容易过拟合

**产物路径**

- API 候选：`artifacts/cts_generation/cts_mini_v0_api_full.jsonl`
- 扩展 panel 评测：`artifacts/object_gate_firstpass/cts_mini_panel_eval.json`

**下一步**

- 补更难、更异质的 same pair，避免 current panel 主要是“简单语法同义改写”
- 为 panel 增加 provenance 字段：rewrite source、manual/API、template family
- 开始补 latent 完整 ablation：`h_minus`、`h_plus`、`delta`、concat

## 2026-03-31 Latent Ablation v2 + CTS Panel v2

**目标**

补齐 latent 表示对照，并继续扩展 CTS panel 的 same-pair 异质性，检查当前 object signal 是否仍然主要由 `delta` 支撑，而不是任意 latent 拼接都能达到相同效果。

**新增文件**

- `data/cts/cts_mini_v0_source_steps_round2.jsonl`
- `artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl`

**脚本更新**

- `scripts/run_object_gate_baselines.py`
  - 新增 `pre_state_only`
  - 新增 `concat_all = [h_minus, h_plus, delta_h]`
- `scripts/evaluate_cts_mini.py`
  - 新增 `pre_state_only`
  - 新增 `concat_all`
- `scripts/generate_cts_with_api.py`
  - 新增 `prompt_mode`
  - 支持 `diverse_same` 模式并记录 provenance

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/run_object_gate_baselines.py scripts/evaluate_cts_mini.py scripts/generate_cts_with_api.py
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps_round2.jsonl --output artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl --prompt-mode diverse_same
conda run -n infer python scripts/run_object_gate_baselines.py --features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --output artifacts/object_gate_firstpass/baseline_results_v2.json
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_panel.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_mini_panel_eval_v2.json --device cuda:0
```

**API 使用量（round 2）**

- source steps: `7`
- API 原始候选行数: `7`
- API 总 token 使用量: `3147`
- 与上一轮合计 token 使用量: `6901`

**Lean first-pass baseline v2**

- `text_only`
  - `AUROC = 0.3915`
- `pre_state_only`
  - `AUROC = 0.8069`
- `post_state_only`
  - `AUROC = 0.8889`
- `transition_only`
  - `AUROC = 0.9444`
- `concat_all`
  - `AUROC = 0.8889`

**当前读法（baseline v2）**

- 在当前 first-pass Lean slice 上，`transition_only` 仍是最强单一表示
- `concat_all` 没有自动优于 `delta`，说明“小样本下把所有 latent 都拼起来”并不能替代 transition 表示
- `pre_state_only` 明显强于 text-only，但弱于 `h_plus` 和 `delta`

**CTS panel v2**

- 当前 panel 规模：
  - `same = 10`
  - `flip = 10`
- aggregated paired metrics：
  - `text_only`
    - `IG = 0.2091`
    - `SS = -0.1308`
  - `pre_state_only`
    - `IG ~= 0`
    - `SS ~= 0`
  - `post_state_only`
    - `IG = 0.4000`
    - `SS = 0.3000`
  - `transition_only`
    - `IG = 0.2000`
    - `SS = 0.6003`
  - `concat_all`
    - `IG = 0.0`
    - `SS = 0.5`

**当前读法（CTS v2）**

- `pre_state_only` 的 `IG ~= 0` 不是好结果，因为它同时 `SS ~= 0`，更像“对 source/variant 都没反应”
- `concat_all` 给出 `IG = 0.0` 且 `SS = 0.5`，表面上好看，但逐对结果显示它常把整对样本一起压到极端值，当前不能直接解释为更强语义表征
- 在当前 panel 上，`transition_only` 仍然是最稳妥的平衡点：
  - 比 `text_only` 有更好的正向 `SS`
  - 比 `post_state_only` 有更低的 `IG`
  - 不像 `pre_state_only` 那样退化成“无响应”

**重要 caveat**

- round 2 的 same pairs 里确实补到了更异质的例子，如：
  - `exact h.elim`
  - `exact Eq.refl n`
- 但 panel 仍然偏向短、局部、可模板化的单行 Lean step
- `concat_all` 的异常漂亮 `IG` 提示当前 panel/训练规模仍然太小，不能把 aggregate 指标直接当成机制真相

**产物路径**

- baseline v2：`artifacts/object_gate_firstpass/baseline_results_v2.json`
- CTS v2：`artifacts/object_gate_firstpass/cts_mini_panel_eval_v2.json`

**下一步**

- 为 same pairs 增加真正不同风格的 rewrite family，而不只是 theorem-application 改写
- 开始把 panel 中最关键的 pair 做更强验证，至少区分：
  - local type-correct but wrong
  - directly ill-typed
- 若继续扩 panel，应优先提升 pair family 多样性，而不是盲目加数量

## 2026-03-31 CTS Auto Panel Expansion

**目标**

在保留 curated panel 的同时，构建一个更大的 provenance-aware auto panel，用于检验当前 object-signal 结论在更噪数据上是否直接翻掉。

**新增文件**

- `scripts/build_cts_auto_panel.py`
- `data/cts/cts_mini_v0_auto_panel.jsonl`
- `artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl`

**脚本更新**

- `scripts/generate_cts_with_api.py`
  - 新增 `plausible_flip` prompt mode

**已执行命令**

```bash
conda run -n infer python scripts/generate_cts_with_api.py --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --sources-jsonl data/cts/cts_mini_v0_source_steps.jsonl --output artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl --prompt-mode plausible_flip
conda run -n infer python scripts/build_cts_auto_panel.py --manual-panel data/cts/cts_mini_v0_panel.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl --output data/cts/cts_mini_v0_auto_panel.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_firstpass/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_firstpass.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_firstpass/cts_auto_panel_eval.json --device cuda:0
```

**API 使用量（round 3）**

- source steps: `10`
- API 原始候选行数: `10`
- API 总 token 使用量: `4223`
- 当前累计 API token 使用量: `11124`

**auto panel 规模**

- manual panel rows: `20`
- API rows merged: `27`
- 去重后 auto panel rows: `28`
  - `same = 13`
  - `flip = 15`

**auto panel 聚合指标**

- `text_only`
  - `IG = 0.1739`
  - `SS = 0.0546`
- `pre_state_only`
  - `IG ~= 0`
  - `SS ~= 0`
- `post_state_only`
  - `IG = 0.2308`
  - `SS = 0.2667`
- `transition_only`
  - `IG = 0.0769`
  - `SS = 0.4418`
- `concat_all`
  - `IG = 0.3893`
  - `SS = 0.4667`

**当前读法**

- 在更大的 auto panel 上，结论没有翻掉：
  - `transition_only` 仍然保持了最好的 `IG/SS` 平衡
- `concat_all` 的 `SS` 略高于 `transition_only`，但 `IG` 大幅变差，说明它更容易被 panel 噪声拉偏
- `text_only` 在 auto panel 上终于出现了正向 `SS`，但幅度明显弱于 latent-transition 表示
- `pre_state_only` 继续表现为低响应，不支持“只看前态就够了”

**重要 caveat**

- auto panel 是“扩量优先”的面板，不是干净评测集
- 由于早期 API artifact 没完整记录 `prompt_mode`，auto panel 中少量行的 provenance 会显示为 `unknown`
- 这不影响当前把它作为 noisy stress panel 使用，但说明 provenance 链还不够整洁

**产物路径**

- auto panel：`data/cts/cts_mini_v0_auto_panel.jsonl`
- auto panel eval：`artifacts/object_gate_firstpass/cts_auto_panel_eval.json`

**下一步**

- 清理 early-round provenance，把 `unknown` 行补成明确来源
- 针对 auto panel 中最有价值的 flip pairs，加上 family 标签：
  - wrong theorem
  - wrong branch
  - wrong projection
  - ill-typed / malformed
- 若要继续扩量，优先做 family coverage，而不是继续堆近重复 pair

## 2026-03-31 CTS Provenance Cleanup + Family Labeling

**目标**

把当前 CTS curated/auto panel 从“可跑”推进到“可审计”：补齐 provenance，清掉历史遗留的 `unknown` lineage，并显式加入 same/flip family 标签。

**新增文件**

- `scripts/annotate_cts_panel.py`
- `data/cts/cts_mini_v0_panel_annotated.jsonl`
- `data/cts/cts_mini_v0_auto_panel_annotated.jsonl`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/annotate_cts_panel.py
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_panel.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl --output data/cts/cts_mini_v0_panel_annotated.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl --output data/cts/cts_mini_v0_auto_panel_annotated.jsonl
```

**做了什么**

- 只对 provenance 不明确的 API 行做回填，保留已有明确 lineage
- 新增 `pair_id_clean`，用于替代历史上带 `__unknown__` 的原始 `pair_id`
- 为 every row 补：
  - `provenance_clean`
  - `prompt_mode`
  - `prompt_version`
  - `same_family` 或 `flip_family`

**curated panel 结果**

- 行数：`20`
- provenance：
  - `manual_seed_v0 = 4`
  - `api_round1_curated = 12`
  - `api_round2_diverse = 4`
- family coverage：
  - same: `constructor_notation / theorem_application_style / symmetry_style / projection_style / eliminator_style / reflexivity_style`
  - flip: `wrong_projection / wrong_theorem_reference / wrong_composition / wrong_branch / ill_typed_or_malformed / wrong_target_term`

**auto panel 结果**

- 行数：`28`
- provenance：
  - `manual_seed_v0 = 4`
  - `api_round1_curated = 12`
  - `api_round2_diverse = 4`
  - `api_default = 3`
  - `api_plausible_flip = 5`
- family coverage：
  - same: `constructor_notation / theorem_application_style / symmetry_style / projection_style / eliminator_style / reflexivity_style / identity_duplicate`
  - flip: `wrong_projection / wrong_theorem_reference / wrong_composition / wrong_branch / ill_typed_or_malformed / wrong_target_term / goal_mismatch_direct_use`

**关键验证**

- `pair_id_clean` 中 `unknown = 0`
- 缺 family 标签的行数 `= 0`

**当前读法**

- 现在最大的改进不是“分数更高”，而是 panel 已经变成更适合进入 Audit gate 的数据对象
- 早期历史行仍保留原始 `pair_id` 和 `provenance`，所以 lineage 可追溯；同时 `pair_id_clean` 与 `provenance_clean` 已可直接用于后续分析

**下一步**

- 基于 `flip_family` 做 family-sliced `IG / SS`
- 优先补 family coverage 缺口，而不是再无差别扩量
- 若进入 Audit gate，建议用 annotated panel 作为默认输入，而不是原始 panel

## 2026-03-31 Round7 Hard Same Rewrite Audit

**目标**

专打 round6 暴露的 same-family invariance 瓶颈，不继续扩 flip-family。round7 只补 manual curated 的 hard same rewrites，重点覆盖：

- `reflexivity_style`
- `projection_style`
- `other_same_rewrite`

**新增文件**

- `data/lean/lean_mini_v0_round7.jsonl`
- `data/cts/cts_mini_v0_round7_manual_only.jsonl`
- `data/cts/cts_mini_v0_round7_manual_only_annotated.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- `artifacts/object_gate_round7/deepseek_prover_v2_7b/manifest.json`
- `artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- `artifacts/object_gate_round7/cts_round7_manual_only_eval.json`
- `artifacts/object_gate_round7/cts_round7_manual_only_audit.json`
- `artifacts/object_gate_round7/cts_auto_panel_round7_eval.json`
- `artifacts/object_gate_round7/cts_auto_panel_round7_audit.json`
- `artifacts/object_gate_round7/cts_round7_summary.md`

**已执行命令**

```bash
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_round7_manual_only.jsonl --output data/cts/cts_mini_v0_round7_manual_only_annotated.jsonl
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_full.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --output data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl
conda run -n infer python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_round7.jsonl --output-dir artifacts/object_gate_round7/deepseek_prover_v2_7b --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --device cuda:0
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_round7_manual_only.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round7/cts_round7_manual_only_eval.json --device cuda:0
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round7/cts_auto_panel_round7_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round7/cts_round7_manual_only_eval.json --annotated-panel data/cts/cts_mini_v0_round7_manual_only_annotated.jsonl --output artifacts/object_gate_round7/cts_round7_manual_only_audit.json
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round7/cts_auto_panel_round7_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round7/cts_auto_panel_round7_audit.json
```

**关键规模**

- round7 Lean source：
  - `40` records
  - `79` steps
  - `13` negative steps
- round7 manual-only：
  - `16` rows
  - `12 same`
  - `4 flip`
- round7 full panel：
  - `58` rows
  - `30 same`
  - `28 flip`

**manual-only 聚合指标**

- `text_only`
  - `IG = 0.5160`
  - `SS = 0.4990`
- `pre_state_only`
  - `IG ~= 0`
  - `SS ~= 0`
- `post_state_only`
  - `IG = 0.5000`
  - `SS = 1.0000`
- `transition_only`
  - `IG = 0.7500`
  - `SS = 0.7867`
- `concat_all`
  - `IG = 0.4167`
  - `SS = 0.7500`

**full panel 聚合指标**

- `text_only`
  - `IG = 0.3884`
  - `SS = 0.2169`
- `pre_state_only`
  - `IG ~= 0`
  - `SS ~= 0`
- `post_state_only`
  - `IG = 0.3813`
  - `SS = 0.6429`
- `transition_only`
  - `IG = 0.3127`
  - `SS = 0.7145`
- `concat_all`
  - `IG = 0.2979`
  - `SS = 0.6071`

**相对 round6 的 family 变化（`transition_only` / full panel）**

- `projection_style`
  - round6: `IG = 0.2500`
  - round7: `IG = 0.0467`
- `other_same_rewrite`
  - round6: `IG = 0.5000`
  - round7: `IG = 0.3439`
- `reflexivity_style`
  - round6: `IG = 0.8845`
  - round7: `IG = 0.9982`

**当前读法**

- round7 没有把 `transition_only` 变成干净的 same-side invariant。
- manual-only round7 slice 很明确地给出负面证据：
  - 新补的 hard same rewrites 并没有把 `transition_only` 的 `IG` 拉下来
  - `transition_only` 在 round7 manual-only 上仍然更像 failure-sensitive detector
- full panel 上，round7 只带来了有限改善：
  - overall `transition_only IG` 从 round6 的 `0.3426` 降到 `0.3127`
  - 但 `SS` 也从 `0.8057` 降到 `0.7145`
- family 层面最重要的结论是：
  - `projection_style` 已明显改善
  - `other_same_rewrite` 有改善但仍不稳
  - `reflexivity_style` 依然是最清晰的 hard failure family

**Gate 读法**

- `Object gate`
  - 仍然只有部分支持
- `Audit gate`
  - 仍未通过

**下一步**

- 不再做 generic same expansion
- 直接把 `reflexivity_style` 拆成更细的 control slice：
  - token/format shift
  - target-term substitution
  - proof-keyword substitution
- 若这条 dedicated control 仍然失败，应把它视为表示上限信号，而不是继续解释成 coverage gap

## 2026-03-31 Round8 Reflexivity Dedicated Control

**目标**

把 `reflexivity_style` 从 round7 的 same-family 汇总里单独剥离出来，判断当前失败到底主要来自：

- 纯 format shift
- proof-keyword substitution
- target-term binding

**新增文件**

- `data/cts/cts_reflexivity_control_round8.jsonl`
- `data/cts/cts_reflexivity_control_round8_annotated.jsonl`
- `artifacts/object_gate_round8/cts_reflexivity_control_eval.json`
- `artifacts/object_gate_round8/cts_reflexivity_control_audit.json`
- `artifacts/object_gate_round8/cts_round8_summary.md`

**脚本最小增强**

- `scripts/annotate_cts_panel.py`
  - 新增 `same_subfamily`
- `scripts/audit_cts_families.py`
  - 新增 `same_subfamily` / `flip_subfamily` 切片汇总

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/annotate_cts_panel.py scripts/audit_cts_families.py
conda run -n infer python scripts/annotate_cts_panel.py --panel data/cts/cts_reflexivity_control_round8.jsonl --output data/cts/cts_reflexivity_control_round8_annotated.jsonl
conda run -n infer python scripts/evaluate_cts_mini.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_reflexivity_control_round8.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round8/cts_reflexivity_control_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round8/cts_reflexivity_control_eval.json --annotated-panel data/cts/cts_reflexivity_control_round8_annotated.jsonl --output artifacts/object_gate_round8/cts_reflexivity_control_audit.json
```

**设计**

- control rows: `13`
- `same = 9`
- `flip = 4`
- same-side 平衡拆成：
  - `reflexivity_pure_format = 3`
  - `reflexivity_proof_keyword = 3`
  - `reflexivity_target_term = 3`
- flip-side 全部是 `wrong_target_term`

**聚合指标**

- `text_only`
  - `IG = 0.6682`
  - `SS = 0.9981`
- `pre_state_only`
  - `IG ~= 0`
  - `SS ~= 0`
- `post_state_only`
  - `IG = 0.5556`
  - `SS = 0.9456`
- `transition_only`
  - `IG = 0.9943`
  - `SS = 1.0000`
- `concat_all`
  - `IG = 0.5556`
  - `SS = 1.0000`

**subfamily 结果（`transition_only`）**

- `reflexivity_pure_format`
  - `IG = 0.9830`
- `reflexivity_proof_keyword`
  - `IG = 1.0000`
- `reflexivity_target_term`
  - `IG = 1.0000`

**当前读法**

- round8 给出了一个很强的负结果：
  - `transition_only` 不只是被 explicit target-term binding 击穿
  - 它连 `rfl -> exact rfl` 这类 pure-format rewrite 也无法保持稳定
- 因此，`reflexivity_style` 上的问题当前更像：
  - 表示层面的系统性不 invariant
  - 而不是“还没覆盖到足够 rewrite family”

**Gate 读法**

- `Object gate`
  - 仍然只是部分支持
- `Audit gate`
  - 仍未通过

**推荐收束**

- 不再继续做 generic same expansion
- 将 `reflexivity_style` 视为当前主线下的 hard negative / diagnosis branch
- headline object claim 只保留在已稳定支持的 family 上；若要重开 reflexivity 分支，需要新的表示思路，而不是继续积累 rewrite rows

## 2026-03-31 Round9 Scoring Audit on Fixed Reflexivity Control

**目标**

验证 round8 的强负结果到底来自：

- `transition` 表示本身
- 还是当前 `linear probe -> sigmoid` 映射过于粗糙

这轮固定：

- 同一数据：`cts_reflexivity_control_round8`
- 同一特征：round7 `boundary_states.pt`
- 同一模型：`DeepSeek-Prover-V2-7B`

只改 scorer。

**新增文件**

- `scripts/evaluate_cts_scoring_audit.py`
- `artifacts/object_gate_round9/cts_scoring_audit_eval.json`
- `artifacts/object_gate_round9/cts_scoring_audit.json`
- `artifacts/object_gate_round9/cts_round9_summary.md`

**已执行命令**

```bash
conda run -n infer python -m py_compile scripts/evaluate_cts_scoring_audit.py
conda run -n infer python scripts/evaluate_cts_scoring_audit.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_reflexivity_control_round8.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round9/cts_scoring_audit_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round9/cts_scoring_audit_eval.json --annotated-panel data/cts/cts_reflexivity_control_round8_annotated.jsonl --output artifacts/object_gate_round9/cts_scoring_audit.json
```

**比较的 scorer**

对 `post-state` 与 `transition` 两类表示，分别比较：

- `linear_prob`
- `linear_logit_z`
- `mlp_prob`
- `centroid_cosine`

**关键结果（固定 round8 reflexivity control）**

`transition` 表示：

- `transition_linear_prob`
  - `IG = 0.7778`
  - `SS = 1.0000`
- `transition_linear_logit_z`
  - `IG = 0.5722`
  - `SS = 2.7894`
- `transition_centroid_cosine`
  - `IG = 0.2896`
  - `SS = 0.5918`
- `transition_mlp_prob`
  - `IG = 0.0444`
  - `SS = 1.0000`

`post-state` 表示：

- `post_linear_prob`
  - `IG = 0.8750`
  - `SS = 1.0000`
- `post_linear_logit_z`
  - `IG = 0.6345`
  - `SS = 2.9705`
- `post_centroid_cosine`
  - `IG = 0.4265`
  - `SS = 0.8107`
- `post_mlp_prob`
  - `IG = 0.0347`
  - `SS = 1.0000`

**subfamily 结果（`transition_mlp_prob`）**

- `reflexivity_pure_format`
  - `IG = 0.0000`
- `reflexivity_proof_keyword`
  - `IG = 0.1136`
- `reflexivity_target_term`
  - `IG = 0.0196`

**相对 round8 的读法修正**

- round8 的结论“`transition_only` 在 reflexivity 上几乎完全失败”过于依赖单一 scorer。
- round9 表明：
  - scorer 选择会主导 `reflexivity_style` 上的 same-side 结论
  - `transition` 表示本身没有在 fixed control 上被判死刑
- 特别是：
  - `pure_format` 从 round8 的 `IG = 0.9830`
  - 变成 round9 `transition_mlp_prob` 的 `IG = 0.0000`

**当前读法**

- 这轮最强的结论不是“object gate 已过”。
- 更准确的是：
  - round8 暴露的是 `representation + scorer` 组合的问题
  - 其中 scorer 不是次要细节，而是第一阶设计变量
- 因此，当前不能再把 `reflexivity_style` 简单收束成“表示本身 hard negative”

**下一步**

- 在更大的 same-family panel 上复跑至少两类 scorer：
  - `mlp_prob`
  - 一个 geometry scorer（如 `centroid_cosine`）
- 若 round9 的修复只在 fixed control 上成立，则说明这是 panel-specific rescue
- 若在 broader panel 上也成立，则 same-side claim 应重新开放，Audit 读法需要更新

## 2026-03-31 Round10 Broader-Panel Scoring Audit

**目标**

检查 round9 的 scorer 修复是不是只在 fixed reflexivity control 上成立，还是能扩展到更大的 round7 full panel。

**新增文件**

- `artifacts/object_gate_round10/cts_auto_panel_scoring_audit_eval.json`
- `artifacts/object_gate_round10/cts_auto_panel_scoring_audit.json`
- `artifacts/object_gate_round10/cts_round10_summary.md`

**已执行命令**

```bash
conda run -n infer python scripts/evaluate_cts_scoring_audit.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round10/cts_auto_panel_scoring_audit_eval.json --device cuda:0
conda run -n infer python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round10/cts_auto_panel_scoring_audit_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round10/cts_auto_panel_scoring_audit.json
```

**规模**

- round7 full panel：
  - `58` pairs
  - `30 same`
  - `28 flip`

**关键结果**

`transition` scorer 比较：

- `transition_linear_prob`
  - `IG = 0.4007`
  - `SS = 0.7852`
- `transition_linear_logit_z`
  - `IG = 0.3633`
  - `SS = 1.5262`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`
- `transition_centroid_cosine`
  - `IG = 0.1204`
  - `SS = 0.2224`

`post-state` scorer 比较：

- `post_linear_prob`
  - `IG = 0.4335`
  - `SS = 0.6451`
- `post_linear_logit_z`
  - `IG = 0.4332`
  - `SS = 1.6160`
- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `post_centroid_cosine`
  - `IG = 0.1786`
  - `SS = 0.2898`

**family 读法（same-family）**

- `projection_style`
  - round7 `transition_only`: `IG = 0.0467`
  - round10 `transition_mlp_prob`: `IG = 0.000009`
- `reflexivity_style`
  - round7 `transition_only`: `IG = 0.9982`
  - round10 `transition_mlp_prob`: `IG = 0.0096`
- `other_same_rewrite`
  - round7 `transition_only`: `IG = 0.3439`
  - round10 `transition_mlp_prob`: `IG = 0.3138`
  - round10 `transition_centroid_cosine`: `IG = 0.0799`
- `eliminator_style`
  - round7 `transition_only`: `IG = 0.0010`
  - round10 `transition_mlp_prob`: `IG = 0.4915`
  - round10 `transition_centroid_cosine`: `IG = 0.0854`

**当前读法**

- round9 的 scorer 修复不是 fixed-panel 偶然；它在 broader round7 panel 上仍然成立。
- 但这个修复不是 `transition` 独享的：
  - `post_mlp_prob` 也同样变好了
- 因此 round10 的主要结论不是“transition 已经赢了”，而是：
  - scorer 是一个一阶混杂变量
  - 在更合理 scorer 下，`transition vs post-state` 的对象比较重新变成 open question
- 这也意味着：
  - `reflexivity_style` 不能再被简单视为 hard negative
  - same-side 结论必须写成 scorer-conditional

**下一步**

- 用 `post_mlp_prob / transition_mlp_prob / 一个 geometry scorer` 重跑主 object-gate 比较
- 重新整理 family claim 表，不再把 `reflexivity_style` 写成 unconditional negative
- 再判断 `transition` 是否仍保有独特对象优势

## 2026-03-31 Round11 Lean Object-Gate Scorer Comparison

**目标**

检查 round9/10 发现的 scorer 混杂，是否也会改变主 Lean object-gate 上 `post-state vs transition` 的比较。

**新增文件**

- `scripts/run_object_gate_scorer_comparison.py`
- `artifacts/object_gate_round11/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round11/object_gate_round11_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round11/object_gate_scorer_comparison.json
```

**固定设置**

- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 特征：`artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- 规模：
  - `79` step examples
  - `40` theorems
  - `66` positive
  - `13` negative
- 协议：leave-one-theorem-out grouped CV
- 表示：
  - `post-state`
  - `transition`
- scorer：
  - `linear_prob`
  - `mlp_prob`
  - `centroid_cosine`

**关键结果**

`linear_prob` 下：

- `post_linear_prob`
  - `AUROC = 0.9848`
  - `accuracy = 0.9114`
  - `brier = 0.0809`
  - `earliest_fail = 1.0`
- `transition_linear_prob`
  - `AUROC = 0.9406`
  - `accuracy = 0.8608`
  - `brier = 0.1265`
  - `earliest_fail = 0.9231`

`mlp_prob` 下：

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
  - `earliest_fail = 0.9231`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
  - `earliest_fail = 1.0`

`centroid_cosine` 下：

- `post_centroid_cosine`
  - `AUROC = 0.9033`
- `transition_centroid_cosine`
  - `AUROC = 0.7716`

**当前读法**

- scorer 选择不仅影响 CTS same-side 审计，也会改变主 Lean object-gate 上的 `post-state vs transition` 结论。
- `linear_prob` 支持 `post-state > transition`。
- `mlp_prob` 把读法改成：
  - `transition` 在 ranking / earliest-fail 上更强
  - `post-state` 在 calibrated probability 指标上更强
- `centroid_cosine` 不支持 `transition` 的独特优势。

因此，round11 后最准确的 object-level 结论是：

- 当前不存在 scorer-robust 的 `transition > post-state` 结论
- 也不存在 scorer-robust 的 `post-state > transition` 结论
- `post-state vs transition` 仍是 scorer-conditional open question

**下一步**

- 先做 `mlp_prob` 的 seed-stability 检查
- 再把同一套 scorer-conditioned object-gate 比较迁移到至少一个额外 prover
- 之后再重写 object claim table

## 2026-03-31 Round12 Goedel Cross-Model Object-Gate Comparison

**目标**

将 round11 的 scorer-conditioned Lean object-gate 对照迁移到第二个 prover，检查 `post-state vs transition` 的读法是否跨模型稳定。

**新增文件**

- `artifacts/object_gate_round12/goedel_prover_v2_8b/manifest.json`
- `artifacts/object_gate_round12/goedel_prover_v2_8b/boundary_states.pt`
- `artifacts/object_gate_round12/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round12/object_gate_round12_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/extract_boundary_states_smoke.py --input data/lean/lean_mini_v0_round7.jsonl --output-dir artifacts/object_gate_round12/goedel_prover_v2_8b --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --device cuda:0
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round12/goedel_prover_v2_8b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round12/object_gate_scorer_comparison.json
```

**固定设置**

- 模型：`Goedel-Prover-V2-8B`
- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 规模：
  - `79` step examples
  - `40` theorems
  - `66` positive
  - `13` negative
- extraction layers：
  - `[-1, -8, -16] -> [35, 28, 20]`
- hidden size：
  - `4096`
- scorer：
  - `linear_prob`
  - `mlp_prob`
  - `centroid_cosine`

**关键结果**

`linear_prob` 下：

- `post_linear_prob`
  - `AUROC = 0.9674`
  - `accuracy = 0.8987`
  - `brier = 0.0914`
  - `earliest_fail = 1.0`
- `transition_linear_prob`
  - `AUROC = 0.9883`
  - `accuracy = 0.9241`
  - `brier = 0.0719`
  - `earliest_fail = 1.0`

`mlp_prob` 下：

- `post_mlp_prob`
  - `AUROC = 0.8869`
  - `accuracy = 0.9494`
  - `brier = 0.0522`
  - `earliest_fail = 0.8462`
- `transition_mlp_prob`
  - `AUROC = 0.9149`
  - `accuracy = 0.9367`
  - `brier = 0.0658`
  - `earliest_fail = 0.9231`

`centroid_cosine` 下：

- `post_centroid_cosine`
  - `AUROC = 0.8683`
- `transition_centroid_cosine`
  - `AUROC = 0.7739`

**跨模型读法**

和 round11 的 DeepSeek 对比：

- DeepSeek `linear_prob`：
  - `post > transition`
- Goedel `linear_prob`：
  - `transition > post`

这是当前最重要的 round12 结果。

它说明主 object-gate 读法现在同时依赖：

- scorer choice
- model choice

**当前读法**

- round12 是一个正向识别结果：
  - 当前分歧不是单模型内的 scorer artifact
  - 模型依赖性是真实存在的
- 但它仍不支持：
  - scorer-robust 且 model-robust 的 `transition > post-state`
  - scorer-robust 且 model-robust 的 `post-state > transition`

因此当前最准确的结论是：

- `post-state vs transition` 现在是 scorer-conditional 且 model-conditional open question
- “也许当前模型没有把该 invariant 学好” 现在是活跃且被证据支持的假设

**下一步**

- 对 DeepSeek 和 Goedel 都做 `mlp_prob` seed-stability 检查
- 若稳定，再迁移到第三个 prover family
- 之后再决定是转向 multi-model diagnosis branch，还是进一步收窄 object claim

## 2026-03-31 Round13 Minimal Conditional-Transition Test

**目标**

测试一个最小 conditional-transition 表示，检查“给 `delta` 加上下文”是否能比裸 `Δh` 更接近 object gate。

**改动**

- 扩展 `scripts/run_object_gate_scorer_comparison.py`
- 新增表示：
  - `conditional_transition = concat(h_minus, delta_h)`

**新增文件**

- `artifacts/object_gate_round13/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round13/object_gate_round13_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round13/object_gate_scorer_comparison.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 特征：`artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- 协议：leave-one-theorem-out grouped CV
- 表示：
  - `post-state`
  - `transition`
  - `conditional_transition = [h^- ; delta]`
- scorer：
  - `linear_prob`
  - `mlp_prob`
  - `centroid_cosine`

**关键结果**

`linear_prob` 下：

- `post_linear_prob`
  - `AUROC = 0.9848`
- `transition_linear_prob`
  - `AUROC = 0.9406`
- `conditional_transition_linear_prob`
  - `AUROC = 0.9487`
  - `accuracy = 0.8101`
  - `brier = 0.1899`

`mlp_prob` 下：

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
- `conditional_transition_mlp_prob`
  - `AUROC = 0.9272`
  - `accuracy = 0.9114`
  - `brier = 0.0897`

`centroid_cosine` 下：

- `post_centroid_cosine`
  - `AUROC = 0.9033`
- `transition_centroid_cosine`
  - `AUROC = 0.7716`
- `conditional_transition_centroid_cosine`
  - `AUROC = 0.7319`

**当前读法**

- 这轮是一个 clean negative baseline。
- 它不说明“上下文不重要”。
- 它说明：
  - 最朴素的条件化方式 `concat(h^-, delta)` 不够好
  - 甚至在当前设置下通常劣于裸 `transition`
  - 也劣于最佳 `post-state` 读法

因此，round13 的方法结论应写成：

- 如果更好的 conditional transition feature 存在，它需要比 raw concatenation 更结构化
- 当前不应把 `concat(h^-, delta)` 当成“更本质对象”的实现

**下一步**

- 把 `concat(h^-, delta)` 固定为 negative baseline
- 若继续这条线，优先试：
  - `h^- * delta` 一类 interaction features
  - bilinear / energy-style scorer
  - directly pairwise / contrastive objectives

## 2026-03-31 Round14 Structured Interaction Conditional Test

**目标**

测试一个比 raw concat 更结构化的 conditional-transition 特征，检查它是否能优于裸 `Δh`。

**改动**

- 扩展 `scripts/run_object_gate_scorer_comparison.py`
- 新增表示：
  - `interaction_transition = concat(delta_h, h_minus * delta_h)`

**新增文件**

- `artifacts/object_gate_round14/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round14/object_gate_round14_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round14/object_gate_scorer_comparison.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 特征：`artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- 协议：leave-one-theorem-out grouped CV
- 表示：
  - `post-state`
  - `transition`
  - `conditional_transition = [h^- ; delta]`
  - `interaction_transition = [delta ; h^- * delta]`
- scorer：
  - `linear_prob`
  - `mlp_prob`
  - `centroid_cosine`

**关键结果**

`mlp_prob` 下：

- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
  - `earliest_fail = 1.0`
- `conditional_transition_mlp_prob`
  - `AUROC = 0.9272`
  - `accuracy = 0.9114`
  - `brier = 0.0897`
  - `earliest_fail = 0.9231`
- `interaction_transition_mlp_prob`
  - `AUROC = 0.9563`
  - `accuracy = 0.9367`
  - `brier = 0.0652`
  - `earliest_fail = 1.0`

`linear_prob` 下：

- `transition_linear_prob`
  - `AUROC = 0.9406`
- `interaction_transition_linear_prob`
  - `AUROC = 0.9190`
  - `accuracy = 0.8228`
  - `brier = 0.1772`

`centroid_cosine` 下：

- `transition_centroid_cosine`
  - `AUROC = 0.7716`
- `interaction_transition_centroid_cosine`
  - `AUROC = 0.7622`

**当前读法**

- 这轮是 partial positive result，不是方法胜利。
- 它说明：
  - 结构化 interaction 确实比 raw concat 更好
  - 但仍未超过裸 `transition`

因此，round14 后最准确的方法读法是：

- 条件化方向本身仍然活跃
- 但“更本质的 conditional object”不能靠简单 feature engineering 就获得
- 如果继续这条线，下一步应转向 scorer 结构，而不是继续堆 concat / interaction feature

**下一步**

- 保留：
  - `concat(h^-, delta)` 作为 negative baseline
  - `concat(delta, h^- * delta)` 作为 stronger-but-still-insufficient baseline
- 若继续，优先试：
  - bilinear / energy-style scorer
  - explicit interaction weighting
  - pairwise / contrastive objective

## 2026-03-31 Round15 Low-Rank Bilinear Conditional Scorer

**目标**

测试一个更结构化的 conditional scorer，而不是继续堆 feature 拼接，检查 `(h^-, delta)` 的低秩 bilinear 打分能否超过裸 `delta`。

**改动**

- 扩展 `scripts/run_object_gate_scorer_comparison.py`
- 新增 scorer：
  - `conditional_bilinear_prob`
- 结构：
  - `linear(h_minus) + linear(delta_h) + low_rank_bilinear(h_minus, delta_h)`
- rank：
  - `32`

**新增文件**

- `artifacts/object_gate_round15/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round15/object_gate_round15_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round15/object_gate_scorer_comparison.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 特征：`artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- 协议：leave-one-theorem-out grouped CV
- bilinear rank：
  - `32`

**关键结果**

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
- `interaction_transition_mlp_prob`
  - `AUROC = 0.9563`
  - `accuracy = 0.9367`
  - `brier = 0.0652`
- `conditional_bilinear_prob`
  - `AUROC = 0.7145`
  - `accuracy = 0.8861`
  - `brier = 0.1139`
  - `earliest_fail = 0.6923`

**当前读法**

- 这轮是 clear negative result。
- 它说明：
  - 在当前 single-point local-soundness 目标下
  - 低秩 bilinear conditional scorer 没有超过裸 `delta`
  - 甚至显著劣于当前所有竞争性 baseline

因此，round15 后最准确的方法读法是：

- 继续在单点 object-gate 上微调 conditional scorer，当前已经是低杠杆方向
- 如果还要推进 conditional branch，下一步应直接转向 pairwise / contrastive objective

**下一步**

- 冻结当前 conditional baselines：
  - raw concat：negative
  - interaction：stronger but insufficient
  - bilinear：negative
- 停止在这条 single-point conditional scorer 分支上继续调参
- 若继续，直接试 pairwise / contrastive training

## 2026-04-01 Round16 CLUE-Style Geometric Baseline

**目标**

借一条已发表方法思路，测试 CLUE-style 的 hidden-state clustering verifier 在当前 step-level Lean object-gate 里是否比我们自己调的几何 baseline 更强。

**改动**

- 扩展 `scripts/run_object_gate_scorer_comparison.py`
- 新增 baseline：
  - `transition_clue_proto`
- 结构：
  - `normalized delta_h + per-class kmeans prototypes + nearest-prototype distance gap`
- 当前配置：
  - 每类 `4` 个 prototype

**新增文件**

- `artifacts/object_gate_round16/object_gate_scorer_comparison.json`
- `artifacts/object_gate_round16/object_gate_round16_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/run_object_gate_scorer_comparison.py --features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round16/object_gate_scorer_comparison.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/lean/lean_mini_v0_round7.jsonl`
- 特征：`artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt`
- 协议：leave-one-theorem-out grouped CV
- CLUE-style config：
  - `delta_h` only
  - `4` prototypes per class

**关键结果**

- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
- `transition_centroid_cosine`
  - `AUROC = 0.7716`
  - `accuracy_at_zero = 0.7089`
- `transition_clue_proto`
  - `AUROC = 0.8217`
  - `accuracy_at_zero = 0.7342`
  - `earliest_fail = 1.0`

**当前读法**

- 这轮是一个有价值的 borrowed baseline result。
- 它说明：
  - 借已发表方法思路是有帮助的
  - `transition_clue_proto` 确实优于最简单的单质心几何 baseline
  - 但它仍明显弱于当前最佳 learned `transition_mlp_prob`

因此，round16 后最准确的方法读法是：

- 当前最强的 borrowed geometry baseline 是 `transition_clue_proto`
- 当前最强的 single-point learned baseline 仍然是 `transition_mlp_prob`
- 这也提示：
  - CLUE-style 思路可能更天然适合 trace-level / candidate-level verification
  - 在我们这里的 step-level local-soundness setting 上，最小移植版还不足以成为最优判别器

**下一步**

- 保留 `transition_clue_proto` 作为当前最强的 geometry baseline
- 停止继续发明更多单点 classifier 变体
- 若继续“借前人方法”路线，优先转向 pairwise / contrastive objective

## 2026-04-01 Round17 CTS Pairwise Margin Baseline

**目标**

从 single-point local-soundness 目标切到直接 pairwise 目标，检查“直接按 same/flip 训练”是否能比现有单点 readout 更对题。

**新增文件**

- `scripts/evaluate_cts_pairwise_margin.py`
- `artifacts/object_gate_round17/cts_pairwise_margin_eval.json`
- `artifacts/object_gate_round17/cts_pairwise_margin_audit.json`
- `artifacts/object_gate_round17/object_gate_round17_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/evaluate_cts_pairwise_margin.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round17/cts_pairwise_margin_eval.json --device cuda:0
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round17/cts_pairwise_margin_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round17/cts_pairwise_margin_audit.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 协议：
  - leave-one-source-theorem-out
- 新目标：
  - same pairs: minimize score gap
  - flip pairs: enforce `source > variant` by margin
- 表示：
  - `post-state`
  - `transition`

**关键结果**

round10 的 single-point 参考值：

- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`

round17 的 pairwise baseline：

- `post_pairwise_margin`
  - `IG = 0.0691`
  - `SS = 0.5990`
- `transition_pairwise_margin`
  - `IG = 0.0518`
  - `SS = 0.1843`

**当前读法**

- objective mismatch 确实存在：
  - pairwise 训练会明显改变 same/flip tradeoff
- 但当前这版 scalar pairwise margin 不是 clean win：
  - `post` 稍微改善了 `IG`，但 `SS` 下降
  - `transition` 的 `IG` 改善很大，但 `SS` 明显塌掉

family audit 也支持同样读法：

- `transition_pairwise_margin` 在一些 same-family 上更稳
- 但在主要 flip-family 上普遍弱于 `post_pairwise_margin`
  - 尤其 `wrong_projection / wrong_theorem_reference / wrong_composition / wrong_branch`

因此，round17 后最准确的方法读法是：

- pairwise 方向本身是对题的
- 但这版 scalar margin objective 太 blunt
- 下一步应转向 embedding-style contrastive，而不是继续调同一类 scalar margin loss

**下一步**

- 把 round17 固定为第一版 pairwise baseline
- 若继续这条线，优先试：
  - contrastive embedding objective
  - same/flip loss 的非对称权重
  - goal-conditioned pairwise latent scoring

## 2026-04-01 Round18 CTS Contrastive Embedding Baseline

**目标**

在固定 round7 CTS full panel 的前提下，把 pairwise 路线从 scalar margin scorer 升级成 embedding-style contrastive objective，检查是否能比 round17 更平衡地兼顾 same-side invariance 和 flip-side sensitivity。

**新增文件**

- `scripts/evaluate_cts_contrastive.py`
- `artifacts/object_gate_round18/cts_contrastive_eval.json`
- `artifacts/object_gate_round18/cts_contrastive_audit.json`
- `artifacts/object_gate_round18/object_gate_round18_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python scripts/evaluate_cts_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round18/cts_contrastive_eval.json --device cuda:0
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round18/cts_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round18/cts_contrastive_audit.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 协议：
  - leave-one-source-theorem-out
- 表示：
  - `post-state`
  - `transition`
- 新目标：
  - same pairs: pull source / variant embeddings together
  - flip pairs: push source / variant embeddings apart by a margin
- 读分方式：
  - item embedding 到正例质心与负例质心的距离差
  - 经 `sigmoid` 映成 `0-1` 分数，和 round10 / round17 保持可比

**关键结果**

round10 的 single-point 参考值：

- `post_mlp_prob`
  - `IG = 0.0720`
  - `SS = 0.7645`
- `transition_mlp_prob`
  - `IG = 0.1042`
  - `SS = 0.7576`

round17 的 scalar pairwise 参考值：

- `post_pairwise_margin`
  - `IG = 0.0691`
  - `SS = 0.5990`
- `transition_pairwise_margin`
  - `IG = 0.0518`
  - `SS = 0.1843`

round18 的 contrastive 结果：

- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

**当前读法**

- 这轮比 round17 更平衡：
  - `transition` 的 `SS` 从 `0.1843` 恢复到 `0.4199`
  - 同时 `IG` 仍显著优于 round10 的 `transition_mlp_prob`
- 但这仍不是 clean win：
  - `post_contrastive` 和 `transition_contrastive` 都没有超过 round10 的最佳 single-point `SS`
  - 当前 minimal contrastive recipe 仍然在 same-side 改善和 flip-side discrimination 之间做了明显 tradeoff

family audit 的主读法也一致：

- `transition_contrastive` 在 same-family 上很强：
  - `reflexivity_style = 0.0079`
  - `projection_style = 0.0035`
  - `constructor_notation = 0.0019`
- 但在 harder same-family 上没有形成 clean 优势：
  - `other_same_rewrite`
  - `eliminator_style`
  - `theorem_application_style`
- flip-family 侧则是 split reading：
  - `transition` 更强：
    - `wrong_theorem_reference`
    - `wrong_composition`
    - `goal_mismatch_direct_use`
  - `post` 更强：
    - `wrong_projection`
    - `wrong_branch`
    - `ill_typed_or_malformed`
    - `wrong_target_term`

因此，round18 后最准确的方法读法是：

- pairwise 方向仍然活着，而且比 round17 的 scalar margin 更像对题
- 但当前这版 embedding-style contrastive 还只是第一版 credible baseline
- 它还没有形成“优于当前最佳 single-point baseline”的主结论

**下一步**

- 固定 round18 为第一版 contrastive baseline
- 停止继续调 scalar pairwise margin
- 若继续这条线，优先试：
  - same/flip loss 的非对称权重
  - harder negatives
  - goal-conditioned contrastive latent scoring

## 2026-04-01 Round19 Weighted Contrastive on Fixed CTS Panel

**目标**

在不改数据、不改模型、不改 contrastive 主体结构的前提下，测试最小的 `same/flip` 非对称权重是否能把 round18 仍偏低的 `SS` 拉回来。

**新增文件**

- `artifacts/object_gate_round19/cts_contrastive_flip2_eval.json`
- `artifacts/object_gate_round19/cts_contrastive_flip2_audit.json`
- `artifacts/object_gate_round19/cts_contrastive_flip4_eval.json`
- `artifacts/object_gate_round19/cts_contrastive_flip4_audit.json`
- `artifacts/object_gate_round19/object_gate_round19_summary.md`

**修改文件**

- `scripts/evaluate_cts_contrastive.py`
  - 新增：
    - `--same-weight`
    - `--flip-weight`
    - `--baseline-prefix`
  - 默认行为保持 round18 不变

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python -m py_compile scripts/evaluate_cts_contrastive.py
python scripts/evaluate_cts_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round19/cts_contrastive_flip2_eval.json --device cuda:0 --same-weight 1.0 --flip-weight 2.0 --baseline-prefix flip2
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round19/cts_contrastive_flip2_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round19/cts_contrastive_flip2_audit.json
python scripts/evaluate_cts_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round19/cts_contrastive_flip4_eval.json --device cuda:0 --same-weight 1.0 --flip-weight 4.0 --baseline-prefix flip4
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round19/cts_contrastive_flip4_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round19/cts_contrastive_flip4_audit.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 协议：
  - leave-one-source-theorem-out
- 表示：
  - `post-state`
  - `transition`
- 对照：
  - round18 symmetric contrastive
  - round19 `flip_weight = 2`
  - round19 `flip_weight = 4`

**关键结果**

round18 基线：

- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

round19 `flip_weight = 2`：

- `flip2_post_contrastive`
  - `IG = 0.0642`
  - `SS = 0.4342`
- `flip2_transition_contrastive`
  - `IG = 0.0615`
  - `SS = 0.3938`

round19 `flip_weight = 4`：

- `flip4_post_contrastive`
  - `IG = 0.0643`
  - `SS = 0.4056`
- `flip4_transition_contrastive`
  - `IG = 0.0660`
  - `SS = 0.4067`

**当前读法**

- 这轮是一个 clean negative：
  - 单纯提高 flip loss 权重，没有把 round18 的 `SS` 拉回来
- 更具体地说：
  - `flip2` 基本是用很小的 `IG` 改善换来 `SS` 下降
  - `flip4` 甚至连 `transition` 的总体 `IG` 都不再优于 round18
- family audit 也没有出现新的 clean rescue：
  - `transition` 仍主要保住 `wrong_composition`
  - `post` 仍在更多 flip-family 上更强
  - same-family 侧也没有超过 round18 的广义改善

因此，round19 后最准确的方法读法是：

- round18 的问题不只是“flip 权重太小”
- naive 的全局 flip-upweighting 不是当前 contrastive 分支的正确修复方式
- 如果继续这条线，应优先转向：
  - harder negatives
  - goal-conditioned contrastive scoring
  - 或更结构化的非对称 objective

**下一步**

- 固定 round19 为 weighted-contrastive negative result
- 停止继续调单一全局权重
- 若继续 pairwise 主线，优先试：
  - harder negatives
  - goal-conditioned contrastive latent scoring

## 2026-04-01 Round20 Hard-Negative Contrastive on Fixed CTS Panel

**目标**

在固定 round7 CTS full panel 的前提下，检查 round18 的主要瓶颈是否来自 negative construction，而不是 global loss weighting。

**新增文件**

- `scripts/evaluate_cts_hardneg_contrastive.py`
- `artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json`
- `artifacts/object_gate_round20/cts_hardneg_contrastive_audit.json`
- `artifacts/object_gate_round20/object_gate_round20_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python -m py_compile scripts/evaluate_cts_hardneg_contrastive.py
python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --device cuda:0 --hardneg-weight 1.0 --baseline-prefix hardneg
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round20/cts_hardneg_contrastive_audit.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 协议：
  - leave-one-source-theorem-out
- 表示：
  - `post-state`
  - `transition`
- 新目标：
  - 保留 round18 的 contrastive embedding objective
  - 额外加入 same-pair 相对最近 flip negative 的 triplet-style hard-negative 约束

**关键结果**

round18 参考值：

- `post_contrastive`
  - `IG = 0.0657`
  - `SS = 0.4480`
- `transition_contrastive`
  - `IG = 0.0648`
  - `SS = 0.4199`

round20 hard-negative 结果：

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

**当前读法**

- 这轮是 round18 之后第一条真正的正向方法结果：
  - `hardneg_post_contrastive` 提高了 `SS`，但以更差 `IG` 为代价
  - `hardneg_transition_contrastive` 则同时改善了：
    - `IG: 0.0648 -> 0.0147`
    - `SS: 0.4199 -> 0.4829`
- 因此，hard negatives 和 round19 的 global weight tuning 不同：
  - 它不是单纯重配 tradeoff
  - 而是真的把 `transition` 的 same/flip frontier 往前推了一步

family audit 的主读法也支持这个结论：

- `hardneg_transition_contrastive` 在 same-family 上几乎全面变干净：
  - `reflexivity_style = 0.0006`
  - `projection_style = 0.0008`
  - `constructor_notation = 0.0007`
  - `other_same_rewrite = 0.0327`
  - `theorem_application_style = 0.0423`
  - `eliminator_style = 0.0506`
- flip-family 侧仍然是 split reading：
  - `transition` 更强：
    - `wrong_composition`
    - `wrong_branch`
    - `goal_mismatch_direct_use`
  - `post` 更强：
    - `wrong_projection`
    - `wrong_theorem_reference`
    - `ill_typed_or_malformed`
    - `wrong_target_term`

因此，round20 后最准确的方法读法是：

- weak negative construction 确实是 round18 的真实瓶颈之一
- harder negatives 明显优于 round19 那种 naive loss reweighting
- 当前 pairwise 分支第一次出现了“方法改动本身带来 clean 正向增益”的结果
- 但它还没有彻底解决：
  - `post vs transition` 的 flip-family 分裂
  - 以及相对 round10 best single-point baseline 的 `SS` 差距

**下一步**

- 固定 round20 为当前最强的 pairwise / contrastive 结果
- 若继续这条线，优先试：
  - goal-conditioned contrastive scoring
  - 更有针对性的 flip-family hard negative construction
  - 将同一 hard-negative recipe 迁移到第二个 prover

## 2026-04-01 Round21 Goal-Conditioned Hard-Negative Contrastive

**目标**

在 round20 的 hard-negative contrastive 基础上，引入最小 goal conditioning，检查 theorem header 是否能帮助缩小剩余的 flip-family 分裂。

**新增文件**

- `scripts/evaluate_cts_goal_hardneg_contrastive.py`
- `artifacts/object_gate_round21/cts_goal_hardneg_contrastive_eval.json`
- `artifacts/object_gate_round21/cts_goal_hardneg_contrastive_audit.json`
- `artifacts/object_gate_round21/object_gate_round21_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python -m py_compile scripts/evaluate_cts_goal_hardneg_contrastive.py
python scripts/evaluate_cts_goal_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round21/cts_goal_hardneg_contrastive_eval.json --device cuda:0 --hardneg-weight 1.0 --baseline-prefix goalhardneg --epochs 200
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round21/cts_goal_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round21/cts_goal_hardneg_contrastive_audit.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 协议：
  - leave-one-source-theorem-out
- 表示：
  - `post-state`
  - `transition`
- 基础方法：
  - round20 hard-negative contrastive
- 新条件化：
  - theorem header 的 last-token hidden states
  - 与主特征做 concat + interaction
- 运行备注：
  - 初版 `epochs = 400` 过慢
  - 本轮实际固定为 `epochs = 200`，不改变方法方向，只收紧训练成本

**关键结果**

round20 参考值：

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

round21 goal-conditioned 结果：

- `goalhardneg_post_contrastive`
  - `IG = 0.0513`
  - `SS = 0.4611`
- `goalhardneg_transition_contrastive`
  - `IG = 0.0085`
  - `SS = 0.3979`

**当前读法**

- 这轮不是新的最好方法，更像一个 conditioning diagnostic：
  - `post` 变得更稳了，但 `SS` 掉了
  - `transition` 的 `IG` 进一步降低，但 `SS` 明显低于 round20
- 因此，最小 header-based goal conditioning 当前更像：
  - 一个 stabilizer
  - 而不是一个更强的 flip discriminator

family audit 的读法也一致：

- `goalhardneg_transition_contrastive` 在 same-family 上非常干净：
  - `reflexivity_style = 0.0015`
  - `projection_style = 0.0010`
  - `constructor_notation = 0.0004`
  - `other_same_rewrite = 0.0285`
  - `eliminator_style = 0.0186`
- 但 flip-family 侧没有形成 clean 改善：
  - `wrong_composition`
  - `wrong_branch`
  - `wrong_target_term`
  - `goal_mismatch_direct_use`
  等关键切片都没有超过 round20

因此，round21 后最准确的方法读法是：

- minimal goal conditioning 是可用的
- 但当前这版 `header concat + interaction` 并没有解决 flip-family 主瓶颈
- round20 仍然是当前 pairwise / contrastive 主线的最好结果

**下一步**

- 固定 round21 为 conditioning diagnostic
- 保持 round20 为当前最强的 pairwise / contrastive 结果
- 若继续，优先试：
  - 更有针对性的 flip-family hard negatives
  - 更 selective 的 goal conditioning
  - 或先把 round20 recipe 迁移到第二个 prover

## 2026-04-01 Round22 Mechanism Audit for Round20 Gain

**目标**

不新增 recipe，只分析 round20 相对 round18 到底改了什么机制，判断 hard negatives 是 generic boost 还是 family-specific geometry change。

**新增文件**

- `scripts/analyze_cts_mechanism_delta.py`
- `artifacts/object_gate_round22/transition_mechanism_delta.json`
- `artifacts/object_gate_round22/post_mechanism_delta.json`
- `artifacts/object_gate_round22/object_gate_round22_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/analyze_cts_mechanism_delta.py
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round18/cts_contrastive_eval.json --after-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline transition_contrastive --after-baseline hardneg_transition_contrastive --output artifacts/object_gate_round22/transition_mechanism_delta.json
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round18/cts_contrastive_eval.json --after-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline post_contrastive --after-baseline hardneg_post_contrastive --output artifacts/object_gate_round22/post_mechanism_delta.json
```

**固定设置**

- before：
  - round18 contrastive
- after：
  - round20 hard-negative contrastive
- 数据：
  - `data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl`
- 规模：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 比较对象：
  - `transition`
  - `post-state`

**关键结果**

transition 机制差分：

- same gap：
  - `0.0648 -> 0.0147`
  - `mean improvement = +0.0501`
  - `27 / 30` same pairs improved
- flip margin：
  - `0.4199 -> 0.4829`
  - `mean improvement = +0.0630`
  - `19 / 28` flip pairs improved

transition 的主要 same-side 改善集中在：

- `eliminator_style`：
  - `0.2887 -> 0.0506`
- `other_same_rewrite`：
  - `0.1650 -> 0.0327`
- `theorem_application_style`：
  - `0.0961 -> 0.0423`
- `reflexivity_style`：
  - `0.0079 -> 0.0006`
- `projection_style`：
  - `0.0035 -> 0.0008`

transition 的 flip-side 增益是选择性的：

- `wrong_branch`：
  - `0.6113 -> 0.7498`
- `goal_mismatch_direct_use`：
  - `0.6126 -> 0.7465`
- `wrong_target_term`：
  - `0.3789 -> 0.5017`
- `wrong_projection`：
  - `0.4550 -> 0.5276`
- `wrong_theorem_reference`：
  - `0.3175 -> 0.3676`
- `wrong_composition`：
  - `0.4582 -> 0.4631`
  - 仅小幅净改善，仍是最不稳定 flip family

代表性 transition 改善 pair：

- same：
  - `cts_same_false_elim_api_2`
    - `0.5773 -> 0.0975`
  - `cts_round6_same_false_of_imp_false_1`
    - `0.5886 -> 0.1461`
- flip：
  - `lean_mul_zero_right_pos__...2798d541`
    - `0.4791 -> 0.7487`
  - `lean_eq_refl_pos__...79e2da93`
    - `0.4943 -> 0.7460`
  - `cts_flip_eq_comm_api_1`
    - `0.4831 -> 0.7022`

transition 的代表性残留失败：

- `cts_round5_flip_double_neg_1`
  - `0.4587 -> 0.0359`
- `cts_flip_add_zero_1`
  - `0.4296 -> 0.0279`
- `cts_round5_flip_imp_trans_1`
  - `0.3475 -> 0.0164`

post-state 机制差分：

- same gap：
  - `0.0657 -> 0.0748`
  - `mean improvement = -0.0090`
- flip margin：
  - `0.4480 -> 0.5500`
  - `mean improvement = +0.1020`
  - `21 / 28` flip pairs improved

post-state 的主机制不是 same cleanup，而是 broad flip amplification：

- `wrong_target_term`：
  - `0.4391 -> 0.5931`
- `wrong_projection`：
  - `0.5843 -> 0.7160`
- `goal_mismatch_direct_use`：
  - `0.6062 -> 0.7351`
- `wrong_theorem_reference`：
  - `0.2936 -> 0.4054`
- `ill_typed_or_malformed`：
  - `0.5858 -> 0.6917`
- `wrong_branch`：
  - `0.6534 -> 0.7488`

但 post-state 也出现了 same-side 回退：

- `theorem_application_style`：
  - `0.0815 -> 0.1907`
- `eliminator_style`：
  - `0.2948 -> 0.3267`
- `symmetry_style`：
  - `0.0191 -> 0.0397`

**当前读法**

这轮最关键的结论不是“round20 更强”本身，而是：

- hard negatives 不是 generic score booster
- 它们对 `transition` 和 `post-state` 触发了不同机制
- `transition` 的收益主要来自：
  - same-side cleanup
  - 再加 selective flip gains
- `post-state` 的收益主要来自：
  - 更激进的 flip-margin amplification
  - 但伴随轻度 same-side 代价

因此，round20 后最准确的方法读法是：

- `post` 和 `transition` 不是在同一种机制上竞争
- 当前 pairwise 主线的核心未解问题已收束为：
  - `wrong_composition` 为什么仍然不稳定
  - 以及这种机制分裂是否能跨模型复现

**下一步**

- 若继续机制线，优先做：
  - `wrong_composition` 的 family-targeted hard negatives
  - 将 round20 recipe 迁移到第二个 prover
  - 直接检查 representation geometry，而不是只看 scalar `IG / SS`

## 2026-04-01 Round23 Wrong-Composition Targeted Hard Negatives

**目标**

在 round20 的 hard-negative contrastive 基础上，只对 `wrong_composition` flip family 增加强化约束，检查当前最顽固 family 能否被定向打通。

**新增文件**

- `scripts/evaluate_cts_family_hardneg_contrastive.py`
- `artifacts/object_gate_round23/cts_family_hardneg_eval.json`
- `artifacts/object_gate_round23/cts_family_hardneg_audit.json`
- `artifacts/object_gate_round23/transition_mechanism_delta.json`
- `artifacts/object_gate_round23/post_mechanism_delta.json`
- `artifacts/object_gate_round23/object_gate_round23_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python -m py_compile scripts/evaluate_cts_family_hardneg_contrastive.py
python scripts/evaluate_cts_family_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round23/cts_family_hardneg_eval.json --device cuda:0 --hardneg-weight 1.0 --target-flip-family wrong_composition --target-weight 2.0 --baseline-prefix comphardneg
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round23/cts_family_hardneg_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round23/cts_family_hardneg_audit.json
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --after-eval artifacts/object_gate_round23/cts_family_hardneg_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline hardneg_transition_contrastive --after-baseline comphardneg_transition_contrastive --output artifacts/object_gate_round23/transition_mechanism_delta.json
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --after-eval artifacts/object_gate_round23/cts_family_hardneg_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline hardneg_post_contrastive --after-baseline comphardneg_post_contrastive --output artifacts/object_gate_round23/post_mechanism_delta.json
```

**固定设置**

- 模型：`DeepSeek-Prover-V2-7B`
- 数据：`data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- panel：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 目标 family：
  - `wrong_composition`
- 最小 targeted 方案：
  - targeted flip loss weight = `2.0`
  - targeted hard-negative pool 也只对 `wrong_composition` 追加约束

**关键结果**

round20 参考值：

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

round23 targeted 结果：

- `comphardneg_post_contrastive`
  - `IG = 0.0712`
  - `SS = 0.5389`
- `comphardneg_transition_contrastive`
  - `IG = 0.0537`
  - `SS = 0.5018`

目标 family `wrong_composition`：

- `transition`
  - `0.4631 -> 0.4613`
  - 净变化：略差
  - `3 / 8` improved, `5 / 8` worsened
- `post-state`
  - `0.4556 -> 0.4594`
  - 净变化：略好
  - `7 / 8` improved, `1 / 8` worsened

transition 相对 round20 的机制差分：

- same gap：
  - `0.0147 -> 0.0537`
  - `mean improvement = -0.0390`
- flip margin：
  - `0.4829 -> 0.5018`
  - `mean improvement = +0.0189`

transition 的主要回退发生在 same-side：

- `eliminator_style`
  - `0.0506 -> 0.3230`
- `other_same_rewrite`
  - `0.0327 -> 0.1027`
- `theorem_application_style`
  - `0.0423 -> 0.1099`

与此同时，target family 并没有被打通：

- `wrong_composition`
  - `0.4631 -> 0.4613`

post-state 相对 round20 的机制差分：

- same gap：
  - `0.0748 -> 0.0712`
- flip margin：
  - `0.5500 -> 0.5389`

post-state 有局部 same-side 修复：

- `theorem_application_style`
  - `0.1907 -> 0.0126`

但 overall `SS` 仍低于 round20。

**当前读法**

这轮是一个 clean negative mechanism result：

- naive family-targeted weighting 不是当前 `wrong_composition` 的正确解法
- 对 `transition` 来说，它没有定向打通目标 family
- 反而破坏了 round20 已经建立起来的 same-side cleanup
- 对 `post-state` 来说，targeted 压力带来了一点 `wrong_composition` 增益，但不足以形成更强总体结果

因此，round23 后最准确的方法读法是：

- 问题不再是“是否需要更多 `wrong_composition` 压力”
- 而是“`wrong_composition` 需要怎样更细的结构化 hard negatives，才不会破坏 same-side geometry”

**下一步**

- 若继续，优先做：
  - 将 `wrong_composition` 拆成更细 subfamily，而不是整体加权
  - 直接看 composition failures 的 geometry
  - 或先把 round20 recipe 迁移到第二个 prover，再判断这是不是 DeepSeek-specific

## 2026-04-02 Round24 Goedel Cross-Model Hard-Negative Check

**目标**

把 round20 hard-negative contrastive recipe 迁移到第二个 prover，检查 round20 的机制分裂是否会在 Goedel 上复现。

**新增文件**

- `artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json`
- `artifacts/object_gate_round24/cts_hardneg_contrastive_audit.json`
- `artifacts/object_gate_round24/transition_cross_model_delta.json`
- `artifacts/object_gate_round24/post_cross_model_delta.json`
- `artifacts/object_gate_round24/object_gate_round24_summary.md`

**脚本更新**

- `scripts/evaluate_cts_hardneg_contrastive.py`
  - 新增 `--epochs`
  - 默认值保持 `400`
  - 本轮 cross-model 运行固定为 `200`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer
python -m py_compile scripts/evaluate_cts_hardneg_contrastive.py
python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --device cuda:0 --hardneg-weight 1.0 --baseline-prefix goedelhardneg --epochs 200
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round24/cts_hardneg_contrastive_audit.json
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --after-eval artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline hardneg_transition_contrastive --after-baseline goedelhardneg_transition_contrastive --output artifacts/object_gate_round24/transition_cross_model_delta.json
python scripts/analyze_cts_mechanism_delta.py --before-eval artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --after-eval artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --before-baseline hardneg_post_contrastive --after-baseline goedelhardneg_post_contrastive --output artifacts/object_gate_round24/post_cross_model_delta.json
```

**固定设置**

- 模型：
  - `Goedel-Prover-V2-8B`
- 数据：
  - `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`
- panel：
  - `58` pairs
  - `30 same`
  - `28 flip`
- 说明：
  - 为控制运行成本，本轮用 `epochs = 200`
  - 因此这轮应读作 near-protocol-matched cross-model diagnostic，而不是 strict apples-to-apples leaderboard replacement

**关键结果**

Goedel round24：

- `goedelhardneg_post_contrastive`
  - `IG = 0.0474`
  - `SS = 0.6311`
- `goedelhardneg_transition_contrastive`
  - `IG = 0.0103`
  - `SS = 0.6101`

对照 DeepSeek round20：

- `hardneg_post_contrastive`
  - `IG = 0.0748`
  - `SS = 0.5500`
- `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`

这轮最重要的读法是：

- Goedel 上两种 readout 的 overall `SS` 都更高
- `transition` 仍然明显比 `post-state` 更 invariant

same-family 侧，Goedel 继续支持：

- `transition` 是更干净的 same-side readout

例如：

- `other_same_rewrite`
  - `post = 0.1144`
  - `transition = 0.0045`
- `eliminator_style`
  - `post = 0.3188`
  - `transition = 0.1268`
- `projection_style`
  - `post = 0.0036`
  - `transition = 0.0019`
- `reflexivity_style`
  - `post = 0.0019`
  - `transition = 0.0010`

flip-family 侧，机制分裂继续存在：

- `post-state` 更强：
  - `wrong_theorem_reference`
  - `wrong_composition`
  - `wrong_target_term`
  - `goal_mismatch_direct_use`
- `transition` 更强：
  - `wrong_projection`
  - `wrong_branch`
  - `ill_typed_or_malformed`

最关键的 carry-over 是：

- `wrong_composition` 仍不是 `transition` 的 win：
  - `post = 0.5252`
  - `transition = 0.4509`

**当前读法**

这轮是一个正向 cross-model mechanism result：

- round20 的核心机制分裂不是纯 DeepSeek artifact
- `transition` 作为更 invariant same-side 表示，这个角色在 Goedel 上保住了
- 但 `wrong_composition` 作为 `transition` 的 stubborn non-win，也一起保住了

因此，round24 后最准确的方法读法是：

- 模型会改变部分 flip family 的强弱
- 但不会抹掉当前主边界
- 当前最顽固的未解问题仍是：
  - `wrong_composition` 为什么跨模型都不成为 `transition` 的 clean win

**下一步**

- 若继续，优先做：
  - 将 `wrong_composition` 拆成更细 subfamily
  - 对 DeepSeek / Goedel 做 composition geometry 对照
  - 再决定是否值得重开新的 family-specific intervention


## 2026-04-02 Round25 Wrong-Composition Subfamily Audit

**目标**

把 `wrong_composition` 从粗 family 拆成更细 subfamily，并基于现有 round20 / round24 结果定位真正的 composition-specific 机制瓶颈。

**脚本更新**

- `scripts/annotate_cts_panel.py`
  - 为 `wrong_composition` 新增 `flip_subfamily`：
    - `application_argument_swap`
    - `transitivity_fabrication`
    - `transitivity_order_swap`

**新增文件**

- `artifacts/object_gate_round25/round20_subfamily_audit.json`
- `artifacts/object_gate_round25/round24_subfamily_audit.json`
- `artifacts/object_gate_round25/object_gate_round25_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/annotate_cts_panel.py
python scripts/annotate_cts_panel.py --panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --api-jsonl artifacts/cts_generation/cts_mini_v0_api_round1.jsonl artifacts/cts_generation/cts_mini_v0_api_round2_diverse.jsonl artifacts/cts_generation/cts_mini_v0_api_round3_plausible.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_targeted.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_weak.jsonl artifacts/cts_generation/cts_mini_v0_api_round4_unique_tail.jsonl artifacts/cts_generation/cts_mini_v0_api_round5_composition.jsonl --output data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round25/round20_subfamily_audit.json
python scripts/audit_cts_families.py --eval-json artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --output artifacts/object_gate_round25/round24_subfamily_audit.json
```

**关键结果**

`wrong_composition` 当前被拆成：

- `application_argument_swap = 4`
- `transitivity_fabrication = 3`
- `transitivity_order_swap = 1`

round20 DeepSeek：

- `application_argument_swap`
  - `post = 0.5481`
  - `transition = 0.3800`
- `transitivity_fabrication`
  - `post = 0.4811`
  - `transition = 0.7277`
- `transitivity_order_swap`
  - `post = 0.0088`
  - `transition = 0.0019`

round24 Goedel：

- `application_argument_swap`
  - `post = 0.5510`
  - `transition = 0.5288`
- `transitivity_fabrication`
  - `post = 0.4366`
  - `transition = 0.4901`
- `transitivity_order_swap`
  - `post = 0.6872`
  - `transition = 0.0215`

pair-level 读法最关键的是：

- `transitivity_fabrication` 不是整体坏 family；其中两条 `eq_comm -> trans` 变体在两个模型上都还是 transition-positive
- 但 `cts_flip_eq_comm_api_1` 是 model-unstable case：
  - round20 transition: `0.7022`
  - round24 transition: `0.0118`
- `application_argument_swap` 也不是整体坏：
  - `cts_round6_flip_and_imp_elim_1`
  - `cts_round6_flip_false_of_imp_false_1`
  在两个模型上都高分
- 真正 persistent 的 hard case 是：
  - `cts_round5_flip_imp_trans_1`
    - round20 transition: `0.0164`
    - round24 transition: `0.0127`
- `transitivity_order_swap` 当前是独立机制：
  - 在 DeepSeek 上几乎两边都不会
  - 在 Goedel 上变成强 post-state win

**当前读法**

这轮最关键的结论是：

- `wrong_composition` 作为一个总桶太粗
- round23 的 family-targeted 失败，主要是因为它把几类不同机制一起加权了
- 当前真正该盯的不是整个 `wrong_composition`，而是：
  - `transitivity_order_swap`
  - `cts_round5_flip_imp_trans_1`
  - `cts_flip_eq_comm_api_1`

**下一步**

- 若继续，优先做：
  - 这三个 slice 的 geometry audit
  - 而不是重开 bucket-level family intervention


## 2026-04-02 Round26: composition geometry audit on unresolved slices

**目标**

- 不新增 recipe，直接解释 round25 剩下的 3 个 `wrong_composition` unresolved slices：
  - `cts_round5_flip_eq_trans_1`
  - `cts_round5_flip_imp_trans_1`
  - `cts_flip_eq_comm_api_1`
- 用 frozen raw latent geometry 对照：
  - DeepSeek round20
  - Goedel round24

**输入/产物**

- `scripts/analyze_cts_slice_geometry.py`
- `artifacts/object_gate_round26/deepseek_composition_geometry.json`
- `artifacts/object_gate_round26/goedel_composition_geometry.json`
- `artifacts/object_gate_round26/object_gate_round26_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/analyze_cts_slice_geometry.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/analyze_cts_slice_geometry.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --eval-json artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --pair-id cts_round5_flip_eq_trans_1 --pair-id cts_round5_flip_imp_trans_1 --pair-id cts_flip_eq_comm_api_1 --output artifacts/object_gate_round26/deepseek_composition_geometry.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/analyze_cts_slice_geometry.py --train-features artifacts/object_gate_round12/goedel_prover_v2_8b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --eval-json artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --pair-id cts_round5_flip_eq_trans_1 --pair-id cts_round5_flip_imp_trans_1 --pair-id cts_flip_eq_comm_api_1 --output artifacts/object_gate_round26/goedel_composition_geometry.json
```

**关键结果**

本轮把 round25 的 residual composition 问题进一步拆成了 3 种不同机制：

1. `cts_round5_flip_eq_trans_1` / `transitivity_order_swap`
   - 在两个模型上，`h_plus` 和 `delta_h` 都是近乎同向塌缩：
     - DeepSeek `source_variant_cosine`: `post 0.8894`, `delta 0.8746`
     - Goedel `source_variant_cosine`: `post 0.8790`, `delta 0.8654`
   - learned gap：
     - DeepSeek: `post 0.0088`, `transition 0.0019`
     - Goedel: `post 0.6872`, `transition 0.0215`
   - 当前读法：这是最像真正 `transition` blind spot 的 slice；Goedel 只能在 learned post-state readout 里把它拉开。

2. `cts_round5_flip_imp_trans_1` / persistent `application_argument_swap`
   - source / variant 在两个模型、两个字段上都高度重合：
     - DeepSeek `source_variant_cosine`: `post 0.9655`, `delta 0.9663`
     - Goedel `source_variant_cosine`: `post 0.9642`, `delta 0.9633`
   - variant 的最近负例都锁定到同一个坏模板 `lean_imp_trans_bad_comp:3`：
     - DeepSeek: `post 0.9950`, `delta 0.9933`
     - Goedel: `post 0.9967`, `delta 0.9962`
   - 当前读法：这不是 family-wide abstraction failure，而是一个强模板吸附的局部几何歧义。

3. `cts_flip_eq_comm_api_1` / unstable `transitivity_fabrication`
   - 它和另外两个 unresolved slice 不同，不是近乎塌缩：
     - DeepSeek `source_variant_cosine`: `post 0.7265`, `delta 0.7067`
     - Goedel `source_variant_cosine`: `post 0.7629`, `delta 0.7198`
   - learned gap 却强烈分叉：
     - DeepSeek: `transition 0.7022`
     - Goedel: `transition 0.0118`
   - 当前读法：这更像 scorer/model-alignment split，不是 raw latent impossibility。

**当前读法**

- `wrong_composition` 不是一个 family，也不是一个机制。
- 当前 residual composition 问题可更精确地写成：
  - `transitivity_order_swap` 是最像 transition-side blind spot 的 slice
  - `imp_trans` 是 negative-template anchoring 问题
  - `eq_comm_api_1` 是 scorer/model alignment split
- 因此下一步不应再做 family weighting。


## 2026-04-02 Round27: template-controlled audit for `application_argument_swap`

**目标**

- 判断 `lean_imp_trans_bad_comp` 是否是整个 `application_argument_swap` subfamily 的通用负模板锚点
- 或者它只是 `cts_round5_flip_imp_trans_1` 这条 persistent hard case 的局部陷阱

**输入/产物**

- `artifacts/object_gate_round27/deepseek_application_argument_swap_geometry.json`
- `artifacts/object_gate_round27/goedel_application_argument_swap_geometry.json`
- `artifacts/object_gate_round27/object_gate_round27_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/analyze_cts_slice_geometry.py --train-features artifacts/object_gate_round7/deepseek_prover_v2_7b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --eval-json artifacts/object_gate_round20/cts_hardneg_contrastive_eval.json --pair-id cts_round5_flip_imp_trans_1 --pair-id cts_round5_flip_double_neg_1 --pair-id cts_round6_flip_and_imp_elim_1 --pair-id cts_round6_flip_false_of_imp_false_1 --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round27/deepseek_application_argument_swap_geometry.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/analyze_cts_slice_geometry.py --train-features artifacts/object_gate_round12/goedel_prover_v2_8b/boundary_states.pt --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl --eval-json artifacts/object_gate_round24/cts_hardneg_contrastive_eval.json --pair-id cts_round5_flip_imp_trans_1 --pair-id cts_round5_flip_double_neg_1 --pair-id cts_round6_flip_and_imp_elim_1 --pair-id cts_round6_flip_false_of_imp_false_1 --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round27/goedel_application_argument_swap_geometry.json
```

**关键结果**

- `lean_imp_trans_bad_comp` 不是整个 `application_argument_swap` 的统一吸附中心。
- 它只在 `cts_round5_flip_imp_trans_1` 上形成稳定的对称模板陷阱：
  - DeepSeek / Goedel、`post` / `delta`、source / variant 四路最近负例都锁到 `lean_imp_trans_bad_comp:3`
  - variant cosine 逼近 `1.0`
  - learned gap 仍几乎为 `0`
- 其余三条 pair 都不是这个机制：
  - `cts_round5_flip_double_neg_1` 只有弱吸附，且跨模型最近负例已分叉
  - `cts_round6_flip_and_imp_elim_1` 会稳定落到 theorem-local bad template `lean_and_imp_elim_bad_comp:1`
  - `cts_round6_flip_false_of_imp_false_1` 的 variant 会稳定落到 `lean_false_of_imp_false_bad_comp:2`
- 当前最准确的读法是：
  - `application_argument_swap` 基本已解释清楚
  - 唯一稳定未解点是 `imp_trans` 这一条 singleton-style template trap


## 2026-04-02 Round28: `transitivity_order_swap` micro-panel

**目标**

- 判断 round26 的 `cts_round5_flip_eq_trans_1` 是否代表 `eq_trans` 顺序交换模板本身的稳定 blind spot
- 或者它只是 broader panel context 下的 singleton failure

**输入/产物**

- `data/cts/cts_transitivity_order_micro_round28.jsonl`
- `artifacts/object_gate_round28/deepseek_transitivity_order_micro_eval.json`
- `artifacts/object_gate_round28/goedel_transitivity_order_micro_eval.json`
- `artifacts/object_gate_round28/object_gate_round28_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_transitivity_order_micro_round28.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round28/deepseek_transitivity_order_micro_eval.json --baseline-prefix round28deepseek --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_mini_v0_round7.jsonl --cts-seed data/cts/cts_transitivity_order_micro_round28.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round28/goedel_transitivity_order_micro_eval.json --baseline-prefix round28goedel --epochs 200 --device cuda:0
```

**关键结果**

受控 `eq_trans` 微面板上的结果非常干净：

DeepSeek：
- `post`: `IG = 0.00089`, `SS = 0.75821`
- `transition`: `IG = 0.00080`, `SS = 0.75828`

Goedel：
- `post`: `IG = 0.00022`, `SS = 0.75671`
- `transition`: `IG = 0.00030`, `SS = 0.75671`

而且这不是只对一种 flip 写法成立：
- `exact hbc.trans hab`
- `exact Eq.trans hbc hab`
- `simpa using Eq.trans hbc hab`

都能在两个模型上被稳定分开，同时 same rewrites 几乎不动。

**当前读法**

- `transitivity_order_swap` 不是模板层面的 intrinsic blind spot。
- round26 的 singleton 更像 broader panel context / negative neighborhood 下的 failure。
- 因此当前不应该把 `transitivity_order_swap` 冻结成 clean diagnosis branch。


## 2026-04-02 Round29: `eq_comm` micro-panel

**目标**

- 判断 round26 的 `cts_flip_eq_comm_api_1` 是否代表 `eq_comm` 局部模板上的稳定 model/scorer split
- 或者它只是 frozen round7 panel neighborhood 下的 singleton artifact

**输入/产物**

- `data/cts/cts_eq_comm_micro_round29.jsonl`
- `data/cts/cts_eq_comm_micro_round29_2theorem.jsonl`
- `data/lean/lean_eq_comm_micro_round29_raw.jsonl`
- `artifacts/object_gate_round29/deepseek_eq_comm_micro_eval.json`
- `artifacts/object_gate_round29/goedel_eq_comm_micro_eval.json`
- `artifacts/object_gate_round29/object_gate_round29_summary.md`

**协议说明**

- `lean_eq_comm_pos` 只有一个 theorem id，无法直接做 leave-one-theorem-out。
- 本轮使用一个临时 clone theorem：
  - `lean_eq_comm_pos`
  - `lean_eq_comm_pos_clone`
- 这只用于让 frozen evaluator 在微面板上可运行，不改变局部 proof template。

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_eq_comm_micro_round29_raw.jsonl --cts-seed data/cts/cts_eq_comm_micro_round29_2theorem.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round29/deepseek_eq_comm_micro_eval.json --baseline-prefix round29deepseek --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_hardneg_contrastive.py --raw-jsonl data/lean/lean_eq_comm_micro_round29_raw.jsonl --cts-seed data/cts/cts_eq_comm_micro_round29_2theorem.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round29/goedel_eq_comm_micro_eval.json --baseline-prefix round29goedel --epochs 200 --device cuda:0
```

**关键结果**

DeepSeek：
- `post`: `IG = 0.00023`, `SS = 0.75944`
- `transition`: `IG = 0.00022`, `SS = 0.75945`

Goedel：
- `post`: `IG = 0.00016`, `SS = 0.75816`
- `transition`: `IG = 0.00015`, `SS = 0.75816`

这说明在 theorem-local `eq_comm` micro-panel 上：
- same symmetry rewrites 基本不动
- fabrication-style transitivity flips 都能被稳定拉开
- DeepSeek / Goedel 不再复现 round26 的分叉

**当前读法**

- `eq_comm_api_1` 不是 theorem-local 模板难点。
- round26 的分叉更像 broader panel / neighborhood artifact。
- 到这里，`wrong_composition` 里原来最像 residual failure 的两个 slice：
  - `transitivity_order_swap`
  - `eq_comm_api_1`
  都已经被降级为 context-sensitive artifact，而不是 intrinsic template blind spot。


## 2026-04-02 Round30: neighborhood delta audit

**目标**

- 比较 round26 的坏 singleton 与 round28/29 的好 micro-panel
- 回答：为什么 frozen round7 panel 会坏，而 theorem-local micro-panel 会好

**输入/产物**

- `artifacts/object_gate_round30/deepseek_round28_flip_geometry.json`
- `artifacts/object_gate_round30/goedel_round28_flip_geometry.json`
- `artifacts/object_gate_round30/deepseek_round29_flip_geometry.json`
- `artifacts/object_gate_round30/goedel_round29_flip_geometry.json`
- `artifacts/object_gate_round30/neighborhood_delta_summary.json`
- `artifacts/object_gate_round30/object_gate_round30_summary.md`

**关键结果**

这轮最关键的结论是：

- round26 的坏 singleton 和 round28/29 的好 micro-panel，在 local geometry 上其实非常接近
- 真正大幅变化的不是 local template geometry，而是 frozen scorer 在不同 panel context 下给出的 margin / score gap

最有信息量的 3 个读法是：

1. `score gap` 大幅变化，但 `source_variant_cosine` 变化很小
   - `eq_trans` DeepSeek:
     - round26 singleton `transition gap = 0.0019`
     - round28 micro mean `transition gap = 0.4546`
     - 但 `delta source_variant_cosine` 仅从 `0.8746 -> 0.8520`
   - `eq_comm` Goedel:
     - round26 singleton `transition gap = 0.0118`
     - round29 micro mean `transition gap = 0.4549`
     - 但 `delta source_variant_cosine` 仅从 `0.7198 -> 0.7345`

2. nearest-negative identity 大体不变
   - `eq_trans` 的 `delta` 在 singleton 和 micro-panel 都主要映到 `lean_eq_trans_bad_comp`
   - `eq_comm` 的 `delta` 在 singleton 和 micro-panel 都主要映到 `lean_and_comm_bad_order`
   - 所以坏点不是因为落进了完全不同的 negative class

3. 最大差异是 `margin_drop` 的方向
   - `eq_trans` DeepSeek `h_plus`:
     - round26 singleton `-0.0081`
     - round28 micro mean `+0.0042`
   - `eq_comm` Goedel `delta`:
     - round26 singleton `-0.0587`
     - round29 micro mean `+0.0276`
   - 当前读法：micro-panel 把 variant 推到“更负”一侧，而 round26 singleton 没稳定做到这一点

**当前读法**

- 这条支线里，大部分 apparent failures 已经不再像 intrinsic template failure
- 更准确地说，它们是 context-sensitive scorer / neighborhood artifact
- 到 round30，这条 local rescue 支线已经可以冻结成 clean audit result


## 2026-04-02 Round31: neighborhood scorer branch

**目标**

- 停止继续做 local rescue / template micro-panel
- 直接试一个 genuinely new scorer：local-neighborhood readout
- 回答：简单 neighborhood scorer 能否修复 round30 暴露出的 context-sensitive calibration 问题

**输入/产物**

- `scripts/evaluate_cts_knn_local.py`
- `artifacts/object_gate_round31/deepseek_knn_local_eval.json`
- `artifacts/object_gate_round31/object_gate_round31_summary.md`

**关键结果**

这轮最重要的结论是：

- naive Euclidean RBF neighborhood scorer 在当前高维 frozen feature 上完全退化
- scale-free cosine neighborhood scorer 虽然不再退化，但明显弱于当前 contrastive / hard-negative 主线
- 因此 round30 暴露出的 context-sensitive calibration 问题，不能靠一个简单 nonparametric neighborhood scorer 直接救回来

DeepSeek round31 aggregate：

- `post_knn_local_prob`: `IG = 0.0`, `SS = 0.0`
- `transition_knn_local_prob`: `IG = 0.0`, `SS = 0.0`
- `post_knn_local_cosine_prob`: `IG = 0.1747`, `SS = 0.2777`
- `transition_knn_local_cosine_prob`: `IG = 0.1374`, `SS = 0.2264`

RBF branch 的退化原因已单独核实：

- leave-one-theorem-out train split 仍有正常 `pos / neg` 样本
- `h_plus / delta_h` 也有正常方差
- 但 test points 到两类邻域的标准化欧氏距离都在 `76-128` 量级
- 所以 `exp(-d^2)` 全下溢成 `0`，正负局部密度同时塌为 `0`，最终所有 pair 都得到 `margin = 0`, `prob = 0.5`

**当前读法**

- `RBF local density`：clean negative control
- `cosine local margin`：clean negative baseline
- 这条新 scorer 分支目前不值得扩到第二模型


## 2026-04-02 Round32: calibration-aware hard-negative contrastive

**目标**

- 在 round20 hard-negative contrastive 主线上试一个 genuinely new objective-level modification
- 不改 panel / 不加新数据 / 不做 sweep
- 回答：显式 score calibration 是否能缓解 round30 暴露的 context-sensitive calibration 问题

**输入/产物**

- `scripts/evaluate_cts_calibrated_hardneg_contrastive.py`
- `artifacts/object_gate_round32/cts_calhardneg_eval.json`
- `artifacts/object_gate_round32/cts_calhardneg_audit.json`
- `artifacts/object_gate_round32/object_gate_round32_summary.md`

**关键结果**

这轮最重要的结论是：

- calibration-aware objective 不是 clean win，但也不是无效改动
- 它把 `transition` 的 flip sensitivity 往前推了一步，同时牺牲了部分 same-side cleanliness
- 因此 round32 最准确的读法是：controlled tradeoff branch，不是新的默认主线

整体结果：

- round20 `hardneg_post_contrastive`: `IG = 0.0748`, `SS = 0.5500`
- round32 `calhardneg_post_contrastive`: `IG = 0.0857`, `SS = 0.5609`

- round20 `hardneg_transition_contrastive`: `IG = 0.0147`, `SS = 0.4829`
- round32 `calhardneg_transition_contrastive`: `IG = 0.0300`, `SS = 0.5191`

所以：

- `post`: `SS` 小幅上升，但 `IG` 更差
- `transition`: `SS` 明显上升，但 `IG` 不再像 round20 那样干净

family audit 说明这个代价是局部的，不是全局塌缩：

- `transition same-side`
  - `reflexivity_style: 0.0006 -> 0.0022`
  - `projection_style: 0.0008 -> 0.0016`
  - `other_same_rewrite: 0.0327 -> 0.1334`
  - `eliminator_style: 0.0506 -> 0.0239`
- `transition flip-side`
  - `wrong_projection: 0.5276 -> 0.5732`
  - `wrong_branch: 0.7498 -> 0.7545`
  - `wrong_composition: 0.4631 -> 0.4693`
  - `wrong_target_term: 0.5017 -> 0.5089`
  - `wrong_theorem_reference: 0.3676 -> 0.4984`
  - `ill_typed_or_malformed: 0.3855 -> 0.3794`

**当前读法**

- 显式 score calibration 确实会系统性改变行为，不是空操作
- 但它目前更像“flip booster with concentrated same-side cost”
- 因此 round20 仍是 same-side 更干净的 pairwise 主结果；round32 只是可比较的 tradeoff 分支


## 2026-04-03 Round33: general-method reframe

**目标**

- 停止沿旧 branch 继续做 case rescue / scorer patching
- 回到 proposal 原始主张，冻结新的 general mainline
- 明确下一轮应该实现什么，而不是继续局部补丁

**输入/产物**

- `artifacts/object_gate_round33/object_gate_round33_summary.md`

**关键结果**

这轮不是新实验，而是主线重构结论。

最重要的判断是：

- 前面的 case 工作已经完成其诊断职责
- 它证明了 signal 存在，但没有给出一个足够 general 的方法原则
- 因此当前项目必须从“找更好的 scorer / 救更多 case”切换到“学习一个 task-conditioned 的 transition principle”

round33 正式冻结的新 mainline 是：

- **Task-Conditioned Transition Energy Model (TC-TEM)**

它的核心读法是：

- 对象不再是 textual step score
- 对象是 `conditioned transition compatibility`
- 训练目标必须统一包含：
  - local correctness
  - same consistency
  - flip separation
  - calibration
- family audit 以后只保留为 diagnostics，不再作为方法主线

**当前读法**

- round20 仍是旧 pairwise 分支的默认 mainline
- round33 则是新 general 主线的正式起点
- 若继续推进，下一轮应直接实例化最小 TC-TEM，而不是回到旧 branch 修补



## 2026-04-03 Round34: minimal TC-TEM first pass

**目标**

- 实例化 round33 冻结的新 general mainline
- 不再继续旧 branch 的 case rescue / scorer patching
- 跑出第一版最小 `Task-Conditioned Transition Energy Model (TC-TEM)` 可执行结果

**输入/产物**

- 脚本：`scripts/evaluate_cts_tctem.py`
- 输出：`artifacts/object_gate_round34/cts_tctem_eval.json`
- 审计：`artifacts/object_gate_round34/cts_tctem_audit.json`
- 摘要：`artifacts/object_gate_round34/object_gate_round34_summary.md`

**命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_tctem.py   --raw-jsonl data/lean/lean_mini_v0_round7.jsonl   --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl   --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b   --output artifacts/object_gate_round34/cts_tctem_eval.json   --device cuda:0   --epochs 20

python scripts/audit_cts_families.py   --eval-json artifacts/object_gate_round34/cts_tctem_eval.json   --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl   --output artifacts/object_gate_round34/cts_tctem_audit.json
```

**协议说明**

- `epochs=300` 和 `epochs=80` 的尝试都因 leave-one-theorem-out 代价过高而中止，未作为正式结果保留
- round34 正式记录的是 `epochs=20` 的 first-pass 运行；这也对齐 proposal 原始 `10–20` epoch head-training 范围

**关键结果**

round34 首次把 general mainline 做成了可执行实例，但不是 clean win。

整体结果：

- `tctem_energy`
  - `IG = 0.0578`
  - `SS = 0.5108`

对比：

- round20 `hardneg_transition_contrastive`
  - `IG = 0.0147`
  - `SS = 0.4829`
- round32 `calhardneg_transition_contrastive`
  - `IG = 0.0300`
  - `SS = 0.5191`
- round34 `tctem_energy`
  - `IG = 0.0578`
  - `SS = 0.5108`

所以：

- 相比 round20，round34 提高了 `SS`，但明显牺牲了 `IG`
- 相比 round32，round34 仍略低于其 `SS`，同时 `IG` 也更差
- 因此 round34 的价值在于“general mainline 已可执行”，而不是“已成为新的默认最好方法”

**family audit**

same-side：

- 很干净：
  - `reflexivity_style = 0.0`
  - `projection_style = 0.0`
  - `constructor_notation ~= 0.0`
  - `theorem_application_style ~= 0.0005`
- 主要弱点集中在：
  - `other_same_rewrite = 0.1660`
  - `eliminator_style = 0.3680`

flip-side：

- 较强：
  - `wrong_projection = 0.6680`
  - `wrong_theorem_reference = 0.5657`
  - `wrong_composition = 0.4978`
  - `wrong_branch ~= 1.0`
  - `transitivity_fabrication ~= 0.9902`
- 较弱：
  - `wrong_target_term = 0.3205`
  - `ill_typed_or_malformed = 0.0003`
  - `transitivity_order_swap = 0.0`

**附加诊断**

分数已经显示出明显饱和：

- 共 `116` 个 source/variant 分数
- `95` 个 `> 0.999`
- `11` 个 `< 1e-3`

这说明当前 first-pass TC-TEM 很可能把置信度压得过满；这能解释它为什么会在某些 family 上极干净、但在另一些 family 上表现出 brittle all-or-nothing 行为。

**当前读法**

- round33 的 general-method 转向是对的
- round34 证明 TC-TEM mainline 不是空想，已经能跑出实质信号
- 但 round34 还太饱和，不能替代 round20 作为默认主结果
- 因此当前最准确的定位是：`promising first executable general-method branch`


## 2026-04-03 Round35: pairwise separability audit

**目标**

- 回到更窄的 object 问题：frozen hidden state 里是否存在“pair 是否有真实 progress difference”的低复杂度可分信息
- 不再训练大 judge，只做 weak-readout separability audit

**输入/产物**

- 脚本：`scripts/evaluate_cts_pairwise_separability.py`
- 输出：`artifacts/object_gate_round35/cts_pairwise_separability_eval.json`
- 摘要：`artifacts/object_gate_round35/object_gate_round35_summary.md`

**命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_pairwise_separability.py   --raw-jsonl data/lean/lean_mini_v0_round7.jsonl   --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl   --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl   --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b   --output artifacts/object_gate_round35/cts_pairwise_separability_eval.json   --device cuda:0
```

**任务定义**

- 每条 CTS pair 都共享同一个 theorem / pre-state
- pair label：
  - `1 = semantic_flip`，表示这对里存在真实 progress difference
  - `0 = same_semantics`，表示这对里不该存在 progress difference
- pair representation：`d = φ(source) - φ(variant)`

**关键结果**

整体结果：

- `post_linear_sep`
  - `AUROC = 0.8964`
  - `accuracy = 0.8793`
  - `brier = 0.1207`
  - `same_mean_prob = 0.0667`
  - `flip_mean_prob = 0.8214`
  - `same_flip_gap = 0.7548`
- `post_centroid_sep`
  - `AUROC = 0.9226`
  - `accuracy = 0.8103`
  - `brier = 0.1624`
  - `same_mean_prob = 0.0655`
  - `flip_mean_prob = 0.6621`
  - `same_flip_gap = 0.5966`

**重要代数结论**

在这个固定 pre-state 的 pairwise 任务里：

- `Δh(source) - Δh(variant) = h^+_source - h^+_variant`

所以 round35 中 `transition` 与 `post-state` 的 pair-difference 本质上是同一个对象；这也是为什么 `post_*` 与 `transition_*` 指标完全一致。这个结果是对象定义带来的，不是实现 bug。

**几何指标**

- `centroid_gap = 0.4023`
- `fisher_ratio = 0.0940`
- `leave-one-out 1NN accuracy = 0.8448`

这说明：

- signal 不只存在于重模型或重目标里
- 用弱 readout 已经能把 `same` 和 `flip` 大体分开

**family 读法**

`linear_diff_probe`：

- same-side 大多很低：
  - `reflexivity_style = 0.0`
  - `projection_style = 0.0`
  - `theorem_application_style = 0.0`
- 主要弱点：
  - `eliminator_style = 0.5`
  - `other_same_rewrite = 0.1667`

flip-side 大多很高：

- `goal_mismatch_direct_use = 1.0`
- `wrong_branch = 1.0`
- `wrong_projection = 1.0`
- `wrong_target_term = 1.0`
- `wrong_composition = 0.875`

仍弱：

- `ill_typed_or_malformed = 0.5`
- `wrong_theorem_reference = 0.5`

**当前读法**

- round35 对 object question 给出了更直接的正向证据
- 如果问题是“hidden 里是否存在可分的 progress-difference 信息”，当前答案是：有
- 而且这个结论不需要大 judge；弱 readout 就已经能读出来
- 但这还不是 deployable verifier 结论；它只说明 object-level separability 已被支持


## 2026-04-03 Round36: cross-model pairwise separability audit (Goedel)

**目标**

- 检查 round35 的更窄 object claim 是否跨模型成立
- 保持同一 pairwise separability 协议，只换第二个 prover family

**输入/产物**

- 脚本：`scripts/evaluate_cts_pairwise_separability.py`
- 输出：`artifacts/object_gate_round36/cts_pairwise_separability_eval.json`
- 摘要：`artifacts/object_gate_round36/object_gate_round36_summary.md`

**命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_cts_pairwise_separability.py   --raw-jsonl data/lean/lean_mini_v0_round7.jsonl   --cts-seed data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl   --annotated-panel data/cts/cts_mini_v0_auto_panel_round7_annotated.jsonl   --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a   --output artifacts/object_gate_round36/cts_pairwise_separability_eval.json   --device cuda:0
```

**关键结果**

Goedel 上：

- `post_linear_sep`
  - `AUROC = 0.9304`
  - `accuracy = 0.9310`
  - `brier = 0.0690`
  - `same_mean_prob = 0.1000`
  - `flip_mean_prob = 0.9643`
  - `same_flip_gap = 0.8643`
- `post_centroid_sep`
  - `AUROC = 0.8976`
  - `accuracy = 0.8103`
  - `brier = 0.1716`
  - `same_mean_prob = 0.1988`
  - `flip_mean_prob = 0.8110`
  - `same_flip_gap = 0.6122`

与 round35 DeepSeek 对比：

- `linear_diff_probe`
  - DeepSeek: `AUROC = 0.8964`, `accuracy = 0.8793`
  - Goedel: `AUROC = 0.9304`, `accuracy = 0.9310`
- `centroid_diff_scorer`
  - DeepSeek: `AUROC = 0.9226`, `accuracy = 0.8103`
  - Goedel: `AUROC = 0.8976`, `accuracy = 0.8103`

所以：

- 更窄的 pairwise object claim 在第二个 prover 上也成立
- 线性弱读头在 Goedel 上反而更强
- 几何质心 baseline 不是 universally 最强，但仍明显高于随机

**几何读法**

Goedel：

- `centroid_gap = 0.4834`
- `fisher_ratio = 0.1481`
- `leave-one-out 1NN accuracy = 0.7241`

对比 DeepSeek：

- 全局类间间隔更强：`centroid_gap 0.4023 -> 0.4834`
- 全局类间相对可分性更强：`fisher_ratio 0.0940 -> 0.1481`
- 但局部最近邻一致性更弱：`1NN acc 0.8448 -> 0.7241`

这说明 Goedel 更像“全局上线性可分更强、局部 neighborhood 更散”的几何。

**重要代数结论继续成立**

在固定 pre-state 的 pairwise 任务里：

- `Δh(source) - Δh(variant) = h^+_source - h^+_variant`

所以 round36 中 `post-state` 与 `transition` 的 pair-difference 仍然是同一个对象；`post_*` 与 `transition_*` 指标一致是 expected behavior。

**family 读法**

`linear_diff_probe` 下：

- same-side 继续接近 0：
  - `reflexivity_style = 0.0`
  - `projection_style = 0.0`
  - `theorem_application_style = 0.0`
- flip-side 继续接近 1：
  - `goal_mismatch_direct_use = 1.0`
  - `wrong_branch = 1.0`
  - `wrong_projection = 1.0`
  - `wrong_target_term = 1.0`
- Goedel 更强：
  - `wrong_composition: 0.875 -> 1.0`
  - `wrong_theorem_reference: 0.5 -> 1.0`
- 仍有弱 same family：
  - `eliminator_style = 0.5`
  - `other_same_rewrite = 0.3333`

**当前读法**

- round35 的 object-level separability 不是单模型偶然现象
- 当前更干净的问题“hidden 里有没有 low-complexity progress-difference 信息”已经得到跨模型正向支持
- 这比 round34 那种 big-judge 结果更直接回答核心 object question
- 但它仍然不是 deployable verifier 结论，只是更强的 object-gate 证据


## 2026-04-03 Round37: stronger pairwise progress label spec

**目标**

- 把 round35/36 之后的“更强 pairwise progress 标签”需求冻结成正式 schema
- 明确当前数据缺什么，避免继续把 `same/flip` proxy 当 final pairwise label 使用

**输入/产物**

- 规范：`configs/object_gate/pairwise_progress_label_v0.yaml`
- scaffold 脚本：`scripts/scaffold_pairwise_progress_panel.py`
- scaffold 数据：`data/cts/cts_pairwise_progress_round37_scaffold.jsonl`
- 摘要：`artifacts/object_gate_round37/object_gate_round37_summary.md`

**检查结果**

当前 Lean raw rows 只有：

- `theorem_id`
- `header`
- `steps`
- `local_sound`
- `notes`

缺失的 proof-state / replay 字段包括：

- `before_goal_count`
- `after_goal_count`
- `main_goal_solved`
- `spawned_goal_count`
- `before_main_goal_pp`
- `after_main_goal_pp`
- `before_total_goal_tokens`
- `after_total_goal_tokens`
- `parser_status`

所以当前 round35/36 仍只能算 proxy-based object evidence，不能当 final pairwise progress evidence。

**新 schema**

`pairwise_progress_label_v0.yaml` 冻结了三层内容：

1. candidate-level progress classes
- `solved`
- `reduced`
- `equivalent`
- `ambiguous`
- `regressed`
- `unsound`

2. pair-level labels
- `no_progress_difference`
- `source_better_weak`
- `source_better_strong`
- `variant_better_weak`
- `variant_better_strong`
- `incomparable`

3. label status
- `final_usable`
- `proxy_only`
- `needs_proof_state_extraction`
- `ambiguous_holdout`

**当前 CTS v0 映射状态**

用 scaffold 脚本把现有 round7 CTS panel 映到新 schema 后：

- `num_pairs = 58`
- `proxy_only_pairs = 58`
- `needs_proof_state_extraction_pairs = 58`
- `same_pairs = 30`
- `source_better_strong_pairs = 28`

这说明：

- 当前 panel 已经 schema-aligned
- 但没有任何一条 pair 已满足 `final_usable`
- 下一步必须先补 proof-state extraction，再谈 stronger final labels

**当前读法**

- round37 不是新实验结果
- 它的作用是冻结 object gate 下一阶段的标签边界
- 从现在开始，`same/flip` 只能当 proxy label；不能再被默默当成 final pairwise progress label 使用


## 2026-04-07 Round38: Lean replay environment hook

**目标**

- 把 Lean replay 环境正式接进当前项目
- 用项目侧 wrapper 跑通一次最小 REPL smoke
- 为后续 proof-state extraction / pairwise progress 数据构造准备可复用入口

**新增文件**

- `configs/object_gate/lean_replay_env_v0.yaml`
- `data/lean/repl_smoke_v0.in`
- `scripts/run_lean_repl_smoke.py`
- `artifacts/object_gate_round38/object_gate_round38_summary.md`

**环境检查**

当前仓库 `/cephfs/luyanzhen/apg/LTV` 本身不是 Lean 项目，因此本轮不新建本地 workspace，而是复用现有 Mathlib 工作区：

- `mathlib root = /root/mathlib4-4.15.0`
- `repl root = /root/mathlib4-4.15.0/repl`
- `toolchain = leanprover/lean4:v4.15.0`
- `lake = /root/.elan/bin/lake`

已确认：

- `/root/mathlib4-4.15.0/lean-toolchain` 与当前 `lake/lean` 版本匹配
- `/root/mathlib4-4.15.0` 可成功 `lake build Mathlib`
- `/root/mathlib4-4.15.0/repl` 的 `lake exe repl` 可正常工作

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && which lake && which lean
cd /root/mathlib4-4.15.0 && source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && lake env lean --version && lake build Mathlib > /tmp/ltv_mathlib_build.log 2>&1; tail -n 20 /tmp/ltv_mathlib_build.log
cd /root/mathlib4-4.15.0/repl && printf '%s\n\n%s\n\n%s\n' '{"cmd" : "def f (x : Unit) : Nat := by sorry"}' '{"tactic": "apply Int.natAbs", "proofState": 0}' '{"tactic": "exact -37", "proofState": 1}' | /root/.elan/bin/lake exe repl
python -m py_compile scripts/run_lean_repl_smoke.py
python scripts/run_lean_repl_smoke.py --input data/lean/repl_smoke_v0.in --output artifacts/object_gate_round38/repl_smoke_output.txt --summary artifacts/object_gate_round38/repl_smoke_summary.json
```

**关键输出**

- 项目侧 smoke wrapper 成功跑通：
  - `returncode = 0`
  - `num_responses = 3`
  - `num_sorry_responses = 1`
  - `proof_states_returned = [1, 2]`
  - `final_goals_count = 0`
- raw REPL 输出已落盘：
  - `artifacts/object_gate_round38/repl_smoke_output.txt`
- 结构化 smoke 摘要已落盘：
  - `artifacts/object_gate_round38/repl_smoke_summary.json`

**当前读法**

- 这轮证明的是：
  - 当前项目已经能从 repo 内部稳定调用外部 Lean+Mathlib REPL 环境
  - 后续可以在此基础上做 replay / proof-state extraction
- 这轮没有证明：
  - proof-state extraction 已实现
  - stronger pairwise progress labels 已可用

**下一步**

- 在这条环境 hook 上实现第一个 project-owned replay / extraction smoke pass


## 2026-04-07 Round39: first replay / extraction smoke pass

**目标**

- 在 round38 的环境 hook 上实现第一个 project-owned replay / extraction smoke pass
- 证明项目内已经可以结构化拿到 step-level `before/after goals`

**新增文件**

- `data/lean/replay_extraction_smoke_v0.json`
- `scripts/run_lean_replay_extraction_smoke.py`
- `artifacts/object_gate_round39/object_gate_round39_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/run_lean_replay_extraction_smoke.py
python scripts/run_lean_replay_extraction_smoke.py --input data/lean/replay_extraction_smoke_v0.json --output artifacts/object_gate_round39/replay_extraction_smoke_v0.json --raw-output artifacts/object_gate_round39/replay_extraction_smoke_v0.raw.txt
```

**关键输出**

- smoke spec：
  - `theorem_id = repl_smoke_unit_natabs`
  - `header_cmd = def f (x : Unit) : Nat := by sorry`
  - tactics:
    - `apply Int.natAbs`
    - `exact -37`
- extraction artifact 成功落盘：
  - `artifacts/object_gate_round39/replay_extraction_smoke_v0.json`
- raw transcript 成功落盘：
  - `artifacts/object_gate_round39/replay_extraction_smoke_v0.raw.txt`
- 结构化结果：
  - `returncode = 0`
  - `initial_env = 0`
  - `initial_proof_state = 0`
  - `initial_goals = ["x : Unit\n⊢ Nat"]`
  - step 0:
    - `before_goals = ["x : Unit\n⊢ Nat"]`
    - `after_goals = ["x : Unit\n⊢ Int"]`
    - `after_proof_state = 1`
  - step 1:
    - `before_goals = ["x : Unit\n⊢ Int"]`
    - `after_goals = []`
    - `after_proof_state = 2`
  - `final_goals = []`
  - `replay_status = ok`

**当前读法**

- 这轮证明的是：
  - 项目侧 wrapper 已不只是能调用 REPL
  - 还已经能把 tactic-mode replay 结构化成 step-level `before/after proof state` artifact
- 这轮没有证明：
  - 已经能批量 replay CTS rows
  - variant replay 已接通
  - stronger pairwise progress label 已可自动生成

**下一步**

- 在这个 smoke pass 上扩成第一个 project-owned variant replay / extraction pass


## 2026-04-07 Round40: first CTS variant replay smoke

**目标**

- 在 round39 的 extraction 原型上，实现第一个 CTS source/variant replay smoke
- 验证 CTS rows 能否被 Lean 分桶成 `shared pre-state + source replay + variant replay`

**新增文件**

- `scripts/run_cts_variant_replay_smoke.py`
- `artifacts/object_gate_round40/object_gate_round40_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/run_cts_variant_replay_smoke.py
python scripts/run_cts_variant_replay_smoke.py --cts-panel data/cts/cts_pairwise_progress_round37_scaffold.jsonl --lean-raw data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round40/cts_variant_replay_smoke.jsonl --summary artifacts/object_gate_round40/cts_variant_replay_smoke_summary.json --max-pairs 8
```

**关键输出**

- smoke subset：`8` pairs
- all `8/8` rows 在 `lean_mini_v0_round7` 中都能找到 theorem context
- replay bucket：
  - `shared_pre_state_ok = 8/8`
  - `source_replay_ok = 8/8`
  - `variant_replay_ok = 6/8`
  - `variant_lean_error = 2/8`
  - `missing_context = 0/8`
- 当前 Lean-error pair IDs：
  - `cts_flip_and_comm_1`
  - `cts_flip_eq_comm_api_1`

**样例读法**

- `cts_same_and_comm_1`
  - source / variant 都 replay 成功
  - `before_goals` 完全一致：
    - `P Q : Prop\nh : P ∧ Q\n⊢ Q ∧ P`
  - 两边都 `after_goals = []`
- `cts_flip_and_comm_1`
  - source replay 成功
  - variant 返回 Lean type mismatch error
- `cts_flip_eq_comm_api_1`
  - source `exact h.symm` replay 成功
  - variant `exact h.trans rfl` 返回 Lean type mismatch error

**当前读法**

- 这轮证明的是：
  - CTS 已经不只是“文本 pair 候选池”
  - 项目内已经能把 CTS row 落成 Lean replay bucket
  - `same pre-state / source replay / variant replay` 这三层分桶已经打通
- 这轮没有证明：
  - 已完成全量 CTS replay
  - 已生成最终 pairwise progress labels
  - 已接入 LLM pairwise progress judge

**下一步**

- 把这个 smoke pass 扩到更大的 CTS replay slice，再引入合法 pair 上的 progress judge


## 2026-04-07 Round41: full CTS replay bucket

**目标**

- 将 round40 的 `8`-pair smoke replay 扩到当前 `58`-pair full scaffold
- 先读清 Lean legality bucket，再决定 judge 子集

**新增文件**

- `artifacts/object_gate_round41/object_gate_round41_summary.md`

**已执行命令**

```bash
python scripts/run_cts_variant_replay_smoke.py --cts-panel data/cts/cts_pairwise_progress_round37_scaffold.jsonl --lean-raw data/lean/lean_mini_v0_round7.jsonl --output artifacts/object_gate_round41/cts_variant_replay_full.jsonl --summary artifacts/object_gate_round41/cts_variant_replay_full_summary.json --max-pairs 58
```

**关键输出**

- full slice：
  - `num_pairs_attempted = 58`
  - `shared_pre_state_ok = 58/58`
  - `source_replay_ok = 58/58`
  - `variant_replay_ok = 32/58`
  - `variant_lean_error = 26/58`
  - `missing_context = 0/58`
- 进一步按当前 proxy pair type 分桶：
  - `same_total = 30`
  - `same_variant_ok = 29`
  - `same_variant_error = 1`
  - `flip_total = 28`
  - `flip_variant_ok = 3`
  - `flip_variant_error = 25`

**代表性读法**

- 合法 same：
  - `cts_same_and_comm_1`
  - source / variant 都 replay 成功，shared pre-state 一致，二者都 `after_goals = []`
- 非法 flip：
  - `cts_flip_and_comm_1`
  - variant `exact And.intro h.left h.right` 返回 Lean type mismatch
- 非法 flip：
  - `cts_flip_eq_comm_api_1`
  - variant `exact h.trans rfl` 返回 Lean type mismatch

**重要 caveat**

- 当前唯一的 `same_variant_error` 不是语义 invalidity，而是 wrapper-level normalization 问题：
  - pair:
    - `lean_false_elim_pos__step1__plausible_flip__same__811e22f0`
  - variant:
    - `exfalso; exact h`
  - 当前单步 wrapper 把它当单个 tactic command，触发：
    - `expected end of input`
- 因此在进入 judge 前，还需要一层最小 tactic normalization，至少处理复合 tactic 写法

**当前读法**

- 这轮已经把 CTS 从 “候选文本 pair” 推进成了一个真正的 Lean legality bucket
- 当前可以清楚分成：
  - replayable pairs
  - hard failure pairs
  - wrapper-normalization holdout
- 这为下一步的 LLM pairwise progress judge 提供了一个明确入口：
  - 只在 replayable pairs 上 judge

**下一步**

- 做最小 tactic normalization，先清掉当前这类 multi-tactic same holdout
- 然后在 replayable pair 子集上接 LLM pairwise progress judge


## 2026-04-07 Round42: replay-data audit

**目标**

- 审计 round41 的 full replay bucket
- 判断当前 CTS rows 是否已经足够干净，可以直接进入 pairwise progress judge

**新增文件**

- `artifacts/object_gate_round42/object_gate_round42_summary.md`

**关键发现**

- 当前数据 **不能** 直接进入 judge
- 问题不只是存在大量 Lean hard failures，而是：
  - 一部分当前标成 `semantic_flip` 的 rows，在 Lean replay 下仍然是 fully replayable 的
  - 因此 `source_better_strong` 这个 proxy label 在 replay 后不再可靠

**核对结果**

- round41 full bucket：
  - total = `58`
  - same:
    - `29` replayable
    - `1` wrapper-level holdout
  - flip:
    - `25` Lean hard errors
    - `3` replayable

**最关键的问题行**

当前 `3` 条 replayable flip 是：

- `cts_flip_add_zero_1`
- `cts_flip_zero_add_left_api_1`
- `lean_mul_zero_right_pos__step0__targeted_family__flip__2798d541`

它们都属于 `wrong_theorem_reference`，但在实际 Lean replay 下依然能把 goal 关掉。  
所以在 replay protocol 下，它们不再是 clean flip-progress pairs，而是需要 **relabel** 的行。

**额外问题**

当前唯一的 same-side replay error：

- `lean_false_elim_pos__step1__plausible_flip__same__811e22f0`

其 variant 是：

- `exfalso; exact h`

这个错误来自 wrapper 当前把分号复合 tactic 当成单条 tactic 命令处理，因此属于 **wrapper normalization 问题**，不是语义 invalidity。

**当前读法**

- round41 已经把合法性层打通
- round42 进一步说明：
  - 当前 CTS 的 `same/flip` 文本 proxy 与 Lean replay 语义并不一致
  - 因此不能直接用 round41 的 replay-ok 子集去接 judge，而不先做 relabel

**下一步**

- 先做最小 tactic normalization
- 再把 replayable flip rows 重新标成 `needs_relabel`
- judge 只接：
  - replayable same
  - replayable 且经 replay 后仍保有真实 progress difference 的 pairs


## 2026-04-07 Round43: state-first generation scaffold

**目标**

- 正式切掉“继续修旧 CTS 当主数据”的思路
- 搭建新的 `state-first candidate-generation + human-oracle` 主线入口

**新增文件**

- `configs/object_gate/state_first_candidate_generation_v0.yaml`
- `prompts/object_gate/state_first_candidate_generation_v0.txt`
- `scripts/build_state_first_seed_panel.py`
- `artifacts/object_gate_round43/object_gate_round43_summary.md`

**已执行命令**

```bash
python - <<'PY'
import os
keys=['OPENAI_API_KEY','DEEPSEEK_API_KEY','ANTHROPIC_API_KEY','DASHSCOPE_API_KEY','OPENROUTER_API_KEY']
for k in keys:
    print(k, 'present' if os.environ.get(k) else 'missing')
PY
python -m py_compile scripts/build_state_first_seed_panel.py
python scripts/build_state_first_seed_panel.py --replay-bucket artifacts/object_gate_round41/cts_variant_replay_full.jsonl --lean-raw data/lean/lean_mini_v0_round7.jsonl --output data/lean/state_first_seed_panel_v0.jsonl
```

**关键输出**

- 当前 shell 中未检测到现成 API key：
  - `OPENAI_API_KEY`
  - `DEEPSEEK_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DASHSCOPE_API_KEY`
  - `OPENROUTER_API_KEY`
- 第一版 state-first seed panel 已生成：
  - `data/lean/state_first_seed_panel_v0.jsonl`
- seed panel 统计：
  - `num_seed_states = 26`
  - `unique_theorems = 26`
  - `max_step_index = 4`

**seed panel 口径**

- 来源：
  - `artifacts/object_gate_round41/cts_variant_replay_full.jsonl`
  - 只取 `source replay ok` 的唯一 before-states
- 当前每个 state row 包含：
  - `state_id`
  - `theorem_id`
  - `step_index`
  - `header`
  - `prefix_steps`
  - `before_goals`
  - `gold_tactic`
  - `notes`
  - `candidate_generation_status`
  - `oracle_label_status`

**当前读法**

- 这轮不是 live API generation
- 它的作用是：
  - 正式把新主线冻结成 repo-owned schema + prompt + seed panel
  - 让后续 candidate generation 可以直接接外部 API
- human annotation 仍是计划中的 progress oracle；生成模型只负责提候选 tactic

**下一步**

- 一旦有可用 API backend，就直接用这 26 个 before-states 生成第一批 candidate tactics
- 然后走：
  - Lean legality replay
  - human pairwise progress oracle


## 2026-04-08 Round44: first state-first API generation batch

**目标**

- 用 README 中现成 API 配置，给新的 state-first seed panel 生成第一批 candidate tactics
- 立即用 Lean 做合法性过滤，确认这条新主线不是空 scaffold

**新增文件**

- `scripts/generate_state_first_candidates_with_api.py`
- `scripts/replay_state_first_candidates.py`
- `artifacts/object_gate_round44/object_gate_round44_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/generate_state_first_candidates_with_api.py
LTV_API_BASE_URL='https://ark.cn-beijing.volces.com/api/v3' LTV_API_MODEL='ep-20251213141929-gk2jb' LTV_API_KEY='***' python scripts/generate_state_first_candidates_with_api.py --seed-panel data/lean/state_first_seed_panel_v0.jsonl --output artifacts/object_gate_round44/state_first_candidates_batch_v0.jsonl --max-states 5 --num-candidates 8 --temperature 0.6
python -m py_compile scripts/replay_state_first_candidates.py
python scripts/replay_state_first_candidates.py --generated artifacts/object_gate_round44/state_first_candidates_batch_v0.jsonl --output artifacts/object_gate_round44/state_first_candidates_batch_v0_replayed.jsonl --summary artifacts/object_gate_round44/state_first_candidates_batch_v0_replayed_summary.json
```

**关键输出**

- README 中记录的 API 路径可用，首批生成成功：
  - `5` states
  - 每个 state `8` 个候选
  - 共 `40` 条 candidate tactics
- Lean legality replay 结果：
  - `num_replay_ok = 32`
  - `num_replay_error = 8`

**state-level 合法率**

- `lean_and_comm_pos__step1`: `8/8`
- `lean_add_zero_right_pos__step0`: `7/8`
- `lean_zero_add_left_pos__step0`: `6/8`
- `lean_eq_comm_pos__step1`: `5/8`
- `lean_or_left_pos__step1`: `6/8`

**代表性 replay failure**

- `nlinarith`
- `symmetry`
- `symmetry at h`
- `constructor 1`
- `refine ⟨h, ?_⟩`

这些失败说明：
- 模型确实在提多样候选
- 但 Lean 过滤是必要的，不能把生成候选直接当有效数据

**当前读法**

- 新主线已经不再是“只搭 scaffold”
- 它已经形成了首个真实 batch：
  - `before-state`
  - API candidate generation
  - Lean legality filtering
- 目前唯一还缺的主层是：
  - human pairwise progress oracle

**下一步**

- 扩大 state-first 生成批次
- 在 replay-ok 候选上组织人工 pairwise progress 标注


## 2026-04-08 Round45: first human progress oracle batch on replay-ok state-first candidates

**目标**

- 在新的 state-first 主线上，为第一批 `replay-ok` 候选补上人工 progress oracle
- 不再依赖旧 CTS 文本 `same/flip` proxy；只在共享 `before state` 内比较合法 `after states`

**新增文件**

- `configs/object_gate/human_progress_oracle_v0.yaml`
- `data/annotations/state_first_progress_oracle_batch_v0.jsonl`
- `artifacts/object_gate_round45/object_gate_round45_summary.md`

**已执行核查**

```bash
python -m py_compile scripts/generate_state_first_candidates_with_api.py scripts/replay_state_first_candidates.py scripts/build_state_first_seed_panel.py
python - <<'PY'
import json
from collections import Counter
path='data/annotations/state_first_progress_oracle_batch_v0.jsonl'
num_states=0
num_candidates=0
tiers=Counter()
with open(path) as f:
    for line in f:
        row=json.loads(line)
        num_states+=1
        num_candidates+=len(row['candidates'])
        for c in row['candidates']:
            tiers[c['progress_tier']]+=1
print(num_states, num_candidates, dict(tiers))
PY
```

**标注协议**

- oracle 来源：`manual_single_annotator_v0`
- 只标注 `Lean replay-ok` 候选
- tier 定义：
  - `solved`
  - `strong_partial`
  - `weak_partial`
  - `neutral`
  - `uncertain`（本批次未使用）
- pairwise preference 暂不手写；后续只在同一 `before state` 内由 tier 自动导出

**批次统计**

- `num_states = 5`
- `num_candidates = 32`
- state-level 候选数：
  - `lean_and_comm_pos__step1`: `8`
  - `lean_add_zero_right_pos__step0`: `7`
  - `lean_zero_add_left_pos__step0`: `6`
  - `lean_eq_comm_pos__step1`: `5`
  - `lean_or_left_pos__step1`: `6`
- tier 分布：
  - `solved = 17`
  - `strong_partial = 10`
  - `weak_partial = 4`
  - `neutral = 1`

**代表性人工判断**

- `lean_and_comm_pos__step1`
  - `exact ⟨h.right, h.left⟩` -> `solved`
  - `constructor` / `apply And.intro` / `refine ⟨?_, ?_⟩` -> `strong_partial`
  - `rcases h with ⟨hp, hq⟩` / `have hp := h.left` -> `weak_partial`
- `lean_eq_comm_pos__step1`
  - `exact Eq.symm h` / `rw [h]` -> `solved`
  - `apply Eq.symm` / `rewrite [h]` -> `strong_partial`
  - `calc b = a := ?_` -> `neutral`
- `lean_or_left_pos__step1`
  - `exact Or.inl h` -> `solved`
  - `apply Or.inl` / `refine Or.inl ?_` / `left` -> `strong_partial`

**当前读法**

- 现在主线第一次有了真正的 `human progress oracle`
- 这批 oracle 仍然是首批、小规模、单标注员版本，因此更适合作为：
  - first separability audit 的 object-gate 评测集
  - human-label protocol smoke
- 还不适合直接写成“最终 progress 标准”

**下一步**

- 由 tier 自动导出 state-local pairwise preference labels
- 用这些人工 oracle pair 跑 first frozen hidden separability audit
- 之后再决定是否扩充 medium-difficulty states 或做第二标注员复核


## 2026-04-08 Round46: first frozen-hidden separability audit on human progress oracle

**目标**

- 用 round45 的人工 progress oracle 跑第一版 frozen-hidden separability audit
- 验证这批新主线数据不只是“可人工排序”，而是低复杂度 hidden readout 也能分

**新增文件**

- `scripts/evaluate_state_first_pairwise_separability.py`
- `artifacts/object_gate_round46/deepseek_state_first_pairwise_sep.json`
- `artifacts/object_gate_round46/goedel_state_first_pairwise_sep.json`
- `artifacts/object_gate_round46/object_gate_round46_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/evaluate_state_first_pairwise_separability.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_batch_v0.jsonl --generated artifacts/object_gate_round44/state_first_candidates_batch_v0.jsonl --replayed artifacts/object_gate_round44/state_first_candidates_batch_v0_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round46/deepseek_state_first_pairwise_sep.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_batch_v0.jsonl --generated artifacts/object_gate_round44/state_first_candidates_batch_v0.jsonl --replayed artifacts/object_gate_round44/state_first_candidates_batch_v0_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round46/goedel_state_first_pairwise_sep.json --device cuda:0
```

**任务定义**

- `gap task`
  - 在同一 `before state` 内，区分：
    - `ordered` pairs：人工 oracle tiers 不同
    - `equivalent` pairs：人工 oracle tiers 相同
- `direction task`
  - 只在 `ordered` pairs 上，区分：
    - `better-minus-worse`
    - `worse-minus-better`
- 只用 frozen hidden + 弱读头：
  - linear probe
  - centroid scorer

**批次规模**

- `num_states = 5`
- `num_gap_pairs = 89`
  - `ordered = 32`
  - `equivalent = 57`
- `num_direction_examples = 64`

**DeepSeek 结果**

- gap task:
  - `linear AUROC = 0.8591`
  - `linear accuracy = 0.7753`
  - `centroid AUROC = 0.7341`
- direction task:
  - `linear AUROC = 0.7090`
  - `linear accuracy = 0.6875`
  - `centroid AUROC = 0.7637`

**Goedel 结果**

- gap task:
  - `linear AUROC = 0.7881`
  - `linear accuracy = 0.7978`
  - `centroid AUROC = 0.8114`
- direction task:
  - `linear AUROC = 0.7109`
  - `linear accuracy = 0.7188`
  - `centroid AUROC = 0.8228`

**几何证据**

- DeepSeek:
  - gap `loo_1nn_acc = 0.8652`
  - direction `loo_1nn_acc = 0.8125`
- Goedel:
  - gap `loo_1nn_acc = 0.8315`
  - direction `loo_1nn_acc = 0.7813`

**当前读法**

- 这批人工 oracle 数据不仅“可以人工区分”，而且 frozen hidden 也能低复杂度读出来
- object-level claim 因此进一步变硬：
  - 不只是旧 CTS proxy 上可分
  - 而是在新的 `state-first -> Lean legality -> human oracle` 主线上也可分
- 这个结论已经跨两个 prover family 成立

**方法边界**

- 当前任务是 object-gate separability，不是 deployable verifier
- 在 fixed before-state 的 pairwise 比较里，`post-state` 差分和 `transition` 差分塌成同一个对象，因此本轮只报告 pairwise `h_plus` 结果

**下一步**

- 冻结 small final oracle panel
- 补 medium-difficulty states，减少“全 solved”题占比
- 在扩后的 panel 上复跑同一 separability 协议


## 2026-04-08 Round47: medium-difficulty state-first expansion slice

**目标**

- 在新的 state-first 主线上补一层 medium-difficulty states
- 避免 object-gate 只由 easy/dev batch 支撑

**新增文件**

- `configs/object_gate/state_first_panel_split_v0.yaml`
- `data/lean/state_first_dev_panel_v0.jsonl`
- `data/lean/state_first_medium_seed_panel_v0.jsonl`
- `artifacts/object_gate_round47/state_first_candidates_medium_v0.jsonl`
- `artifacts/object_gate_round47/state_first_candidates_medium_v0_replayed.jsonl`
- `artifacts/object_gate_round47/state_first_candidates_medium_v0_replayed_summary.json`
- `artifacts/object_gate_round47/object_gate_round47_summary.md`

**已执行命令**

```bash
LTV_API_BASE_URL='https://ark.cn-beijing.volces.com/api/v3' LTV_API_MODEL='ep-20251213141929-gk2jb' LTV_API_KEY='***' python scripts/generate_state_first_candidates_with_api.py --seed-panel data/lean/state_first_medium_seed_panel_v0.jsonl --output artifacts/object_gate_round47/state_first_candidates_medium_v0.jsonl --num-candidates 8 --temperature 0.6
python scripts/replay_state_first_candidates.py --generated artifacts/object_gate_round47/state_first_candidates_medium_v0.jsonl --output artifacts/object_gate_round47/state_first_candidates_medium_v0_replayed.jsonl --summary artifacts/object_gate_round47/state_first_candidates_medium_v0_replayed_summary.json
```

**medium state 选择**

- `lean_imp_trans_pos__step3`
- `lean_eq_trans_pos__step2`
- `lean_and_imp_elim_pos__step1`
- `lean_false_of_imp_false_pos__step2`
- `lean_and_to_imp_apply_pos__step1`
- `lean_imp_chain_four_pos__step4`

这些 state 主要覆盖：
- implication composition
- equality transitivity
- projection-plus-application
- nested implication chain

**生成 + replay 结果**

- `num_states = 6`
- `num_generated_candidates = 49`
- `num_replay_ok = 35`
- `num_replay_error = 14`

**按 state 的 replay 质量**

- `lean_imp_trans_pos__step3`: `6 ok / 2 err`
- `lean_eq_trans_pos__step2`: `4 ok / 5 err`
- `lean_and_imp_elim_pos__step1`: `7 ok / 1 err`
- `lean_false_of_imp_false_pos__step2`: `6 ok / 2 err`
- `lean_and_to_imp_apply_pos__step1`: `8 ok / 0 err`
- `lean_imp_chain_four_pos__step4`: `4 ok / 4 err`

**当前读法**

- 这批 medium slice 明显比首批 easy/dev batch 更有层级结构：
  - 不是“全 solved”
  - 包含 solve / strong partial / weak setup / hard failure 混合
- 因此它值得进入下一轮人工 progress oracle，而不是只停在 legality replay

**下一步**

- 给这 `35` 条 replay-ok medium candidates 做人工 progress oracle
- 与 round45 的 dev batch 合并成更像 final 的 panel
- 在合并 panel 上复跑同一 separability 协议


## 2026-04-08 Round48: combined dev+medium oracle panel still supports hidden separability

**目标**

- 在补入 medium-difficulty states 后，复查 object-level hidden separability 是否仍然成立

**新增文件**

- `data/annotations/state_first_progress_oracle_batch_v1_medium.jsonl`
- `data/annotations/state_first_progress_oracle_panel_v1_combined.jsonl`
- `artifacts/object_gate_round48/state_first_candidates_panel_v1_generated.jsonl`
- `artifacts/object_gate_round48/state_first_candidates_panel_v1_replayed.jsonl`
- `artifacts/object_gate_round48/deepseek_state_first_panel_v1_sep.json`
- `artifacts/object_gate_round48/goedel_state_first_panel_v1_sep.json`
- `artifacts/object_gate_round48/object_gate_round48_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v1_combined.jsonl --generated artifacts/object_gate_round48/state_first_candidates_panel_v1_generated.jsonl --replayed artifacts/object_gate_round48/state_first_candidates_panel_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round48/deepseek_state_first_panel_v1_sep.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_panel_v1_combined.jsonl --generated artifacts/object_gate_round48/state_first_candidates_panel_v1_generated.jsonl --replayed artifacts/object_gate_round48/state_first_candidates_panel_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round48/goedel_state_first_panel_v1_sep.json --device cuda:0
```

**合并 panel 规模**

- `num_states = 11`
- `num_candidates = 67`
- tier 分布：
  - `solved = 25`
  - `strong_partial = 29`
  - `weak_partial = 11`
  - `neutral = 2`
- pair 分布：
  - `ordered = 93`
  - `equivalent = 87`

**DeepSeek 结果**

- gap task:
  - `linear AUROC = 0.8802`
  - `centroid AUROC = 0.8215`
- direction task:
  - `linear AUROC = 0.8806`
  - `centroid AUROC = 0.9733`

**Goedel 结果**

- gap task:
  - `linear AUROC = 0.8910`
  - `centroid AUROC = 0.8171`
- direction task:
  - `linear AUROC = 0.9269`
  - `centroid AUROC = 0.9761`

**几何证据**

- DeepSeek:
  - gap `loo_1nn_acc = 0.8556`
  - direction `loo_1nn_acc = 0.9355`
- Goedel:
  - gap `loo_1nn_acc = 0.8444`
  - direction `loo_1nn_acc = 0.9355`

**当前读法**

- 先前的正结果不是 easy batch artifact
- 补入 medium-difficulty states 之后：
  - `ordered vs equivalent`
  - `better vs worse`
 这两类 hidden separability 都仍然强
- object gate 因此进一步变硬：
  - 不只在旧 proxy 上成立
  - 不只在 5-state dev batch 上成立
  - 而是在更像 final 的 `Lean legality + human oracle` panel 上仍成立

**方法边界**

- 当前仍是 object-gate result，不是 deployable verifier
- still single-annotator
- upstream generation 还存在格式噪声（如一条返回 `9` candidates）

**下一步**

- 将这 `11`-state panel 冻结为 `small final oracle panel v1`
- 可选补第二标注员 disagreement audit
- 再决定是否进入 method/conversion 阶段

## 2026-04-08 Round53: hard-slice audit + before-hidden state-value audit

**新增文件**

- `artifacts/object_gate_round53/deepseek_state_first_hard_slice_sep.json`
- `artifacts/object_gate_round53/goedel_state_first_hard_slice_sep.json`
- `artifacts/object_gate_round53/deepseek_before_state_value.json`
- `artifacts/object_gate_round53/goedel_before_state_value.json`
- `artifacts/object_gate_round53/object_gate_round53_summary.md`

**已执行命令**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_batch_v2_hard.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round53/deepseek_state_first_hard_slice_sep.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_batch_v2_hard.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round53/goedel_state_first_hard_slice_sep.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_before_state_value.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round53/deepseek_before_state_value.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_before_state_value.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round53/goedel_before_state_value.json --device cuda:0
```

**hard-slice separability**

在 `6`-state harder oracle slice 上，candidate-level progress signal 仍然很强。

DeepSeek:
- gap linear AUROC = `0.8913`
- direction linear AUROC = `0.9926`

Goedel:
- gap linear AUROC = `0.8592`
- direction linear AUROC = `0.9702`

相对 round51 的 full consensus panel:
- gap task 略弱
  - DeepSeek: `0.9085 -> 0.8913`
  - Goedel: `0.8874 -> 0.8592`
- direction task 不弱，反而更高
  - DeepSeek: `0.9490 -> 0.9926`
  - Goedel: `0.9148 -> 0.9702`

结论：
- 当前正结果不是只停留在 easy/dev states
- harder slice 没有把 candidate-level progress signal 打塌
- 真正略变难的是 `ordered vs equivalent` 的 gap 区分，不是 `better vs worse` 排序

**before-hidden state-value audit**

在同一个 `17`-state consensus panel 上，`before hidden` 也带 state-level signal，但明显更弱。

binary hardness 定义：
- `1 iff the state has at least one neutral/weak_partial candidate`

DeepSeek:
- hardness AUROC = `0.6736`
- hardness accuracy = `0.6471`
- mean-tier Pearson = `0.3762`
- mean-tier Spearman = `0.4271`

Goedel:
- hardness AUROC = `0.8056`
- hardness accuracy = `0.7647`
- mean-tier Pearson = `0.4106`
- mean-tier Spearman = `0.6326`

结论：
- `before hidden` 不是空的
- 它确实有 state-level hardness / value information
- 但它远弱于 candidate-local `after hidden` 上的 pairwise progress signal

**当前读法**

round53 进一步支持一个更清楚的机制分层：
- `after hidden` 承载强的 candidate-level progress signal
- `before hidden` 承载弱但真实的 state-value / hardness signal
- 所以当前 object/method 正结果不太像只是 trivial `before-state shortcut`

**下一步**

- 若继续 method，最自然的是测试 `before-state value + after-state progress` 的双头 scorer
- 若继续 object/audit，则可补一个更难的 hard slice，但当前必要性已经下降

## 2026-04-08 Round54: Putnam harder-domain pilot

**目标**

用真正更难的 Putnam formal states 替代先前仍可能处于 prover 舒适区的 medium/hard slice，检查 hidden progress signal 在更难域上是否还能成立。

**新增文件**

- `scripts/extract_putnam_state_seeds.py`
- `scripts/replay_putnam_state_first_candidates.py`
- `data/lean/state_first_putnam_seed_panel_v0.jsonl`
- `data/lean/state_first_putnam_seed_panel_v0_pilot.jsonl`
- `data/annotations/state_first_progress_oracle_putnam_pilot_v0.jsonl`
- `artifacts/object_gate_round54/state_first_putnam_seed_panel_v0_summary.json`
- `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl`
- `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed.jsonl`
- `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed_summary.json`
- `artifacts/object_gate_round54/deepseek_putnam_pilot_sep.json`
- `artifacts/object_gate_round54/goedel_putnam_pilot_sep.json`
- `artifacts/object_gate_round54/object_gate_round54_summary.md`

**已执行命令**

```bash
python -m py_compile scripts/extract_putnam_state_seeds.py scripts/replay_putnam_state_first_candidates.py scripts/generate_state_first_candidates_with_api.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/extract_putnam_state_seeds.py --output data/lean/state_first_putnam_seed_panel_v0.jsonl --summary artifacts/object_gate_round54/state_first_putnam_seed_panel_v0_summary.json
python - <<'PY'
import json
from pathlib import Path
src = Path('data/lean/state_first_putnam_seed_panel_v0.jsonl')
out = Path('data/lean/state_first_putnam_seed_panel_v0_pilot.jsonl')
keep = {
    'coeff_X_sub_C_pow__sorry0',
    'finite_diff_identity__sorry1',
    'putnam_1993_a4__sorry0',
    'putnam_2013_b4__sorry4',
}
rows=[]
for line in src.read_text(encoding='utf-8').splitlines():
    if line.strip():
        row=json.loads(line)
        if row['state_id'] in keep:
            rows.append(row)
with out.open('w', encoding='utf-8') as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False)+'\n')
PY
LTV_API_BASE_URL='https://ark.cn-beijing.volces.com/api/v3' LTV_API_MODEL='ep-20251213141929-gk2jb' LTV_API_KEY='***' python scripts/generate_state_first_candidates_with_api.py --seed-panel data/lean/state_first_putnam_seed_panel_v0_pilot.jsonl --output artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl --num-candidates 6 --temperature 0.6 --sleep-seconds 0.2
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/replay_putnam_state_first_candidates.py --generated artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl --output artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed.jsonl --summary artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed_summary.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_putnam_pilot_v0.jsonl --generated artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl --replayed artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round54/deepseek_putnam_pilot_sep.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_putnam_pilot_v0.jsonl --generated artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl --replayed artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round54/goedel_putnam_pilot_sep.json --device cuda:0
```

**更难种子提取**

- Putnam project-aware file mode 成功提取 `14` 个 nonempty harder seed states
- 来源：
  - `putnam_1976_b5_sol.lean`: `4` states
  - `putnam_1993_a4_sol.lean`: `1` state
  - `putnam_2013_b4_sol.lean`: `9` states

**tiny Putnam pilot**

- pilot states = `4`
- generated candidates = `24`
- replay ok = `16`
- replay error = `8`

按 state：
- `coeff_X_sub_C_pow__sorry0`: `3 / 6`
- `finite_diff_identity__sorry1`: `3 / 6`
- `putnam_1993_a4__sorry0`: `6 / 6`
- `putnam_2013_b4__sorry4`: `4 / 6`

**tiny Putnam oracle**

- `27` gap pairs:
  - `19 ordered`
  - `8 equivalent`
- `38` direction examples

**frozen-hidden audit**

DeepSeek:
- gap:
  - linear AUROC = `0.8783`
  - centroid AUROC = `0.9013`
- direction:
  - linear AUROC = `0.3324`
  - centroid AUROC = `0.2659`

Goedel:
- gap:
  - linear AUROC = `0.7961`
  - centroid AUROC = `0.8980`
- direction:
  - linear AUROC = `0.3352`
  - centroid AUROC = `0.3573`

**结论**

- 这轮支持用户的质疑：先前的 “hard” 确实不够硬
- 在真实 Putnam-source harder states 上：
  - `ordered vs equivalent` 的粗粒度 progress gap 仍然存在
  - 但 `better vs worse` 的方向信号在两个 prover 上都明显变差
- 所以当前最准确的 object claim 应更新为：
  - latent progress signal 是真的
  - 但其可读性是 difficulty-dependent
  - 更难域上，coarse progress distinction 先保住，fine directional ordering 先塌

**下一步**

- 扩一个比当前 `4`-state pilot 稍大的 Putnam hard oracle slice
- 先确认 direction collapse 是 tiny-sample artifact 还是 harder-domain 边界
- 在这一步前，不建议直接切回 method sweep

## 2026-04-08 Round55: Expanded Putnam hard oracle slice reverses the earlier tiny-pilot read

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_state_first_pairwise_separability.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round55/deepseek_putnam_v1_sep.json --device cuda
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_state_first_pairwise_separability.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round55/goedel_putnam_v1_sep.json --device cuda
```

**Input slice**

- `7` harder Putnam states
- `27` replay-ok candidates
- `40` gap pairs:
  - `31 ordered`
  - `9 equivalent`
- `62` direction examples

Oracle:
- [data/annotations/state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)

Generated / replay:
- [artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl)
- [artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)

**Frozen-hidden audit**

DeepSeek:
- gap:
  - linear AUROC = `0.3405`
  - centroid AUROC = `0.1989`
  - linear mean gap = `-0.3082`
- direction:
  - linear AUROC = `0.3502`
  - centroid AUROC = `0.4984`
  - linear mean gap = `-0.2344`

Goedel:
- gap:
  - linear AUROC = `0.3728`
  - centroid AUROC = `0.2330`
  - linear mean gap = `-0.3403`
- direction:
  - linear AUROC = `0.3007`
  - centroid AUROC = `0.5463`
  - linear mean gap = `-0.3548`

Results:
- [artifacts/object_gate_round55/deepseek_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/deepseek_putnam_v1_sep.json)
- [artifacts/object_gate_round55/goedel_putnam_v1_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/goedel_putnam_v1_sep.json)
- [artifacts/object_gate_round55/object_gate_round55_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/object_gate_round55_summary.md)

**Conclusion**

- Round54's tiny Putnam pilot was too optimistic.
- After expanding to a `7`-state harder-domain oracle slice, both coarse `ordered vs equivalent` gap and fine `better vs worse` direction separability fail to generalize across states.
- Current object claim boundary tightens further:
  - supported on easy-to-medium oracle panels
  - not supported on genuinely hard Putnam states under the current frozen-hidden protocol

**Important note**

- This round also fixed a script compatibility issue in [scripts/evaluate_state_first_pairwise_separability.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_state_first_pairwise_separability.py):
  - `from_pretrained(..., dtype=...)` -> `from_pretrained(..., torch_dtype=...)`
- This was an environment compatibility fix only; task definition and evaluation protocol were unchanged.

## 2026-04-08 Round56: External pairwise judge stays strong on Putnam where frozen hidden collapses

**Command**

```bash
LTV_API_BASE_URL='https://ark.cn-beijing.volces.com/api/v3' LTV_API_MODEL='ep-20251213141929-gk2jb' LTV_API_KEY='***' python scripts/judge_state_first_pairwise_with_api.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --rows-output artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --summary-output artifacts/object_gate_round56/putnam_v1_judge_summary.json --temperature 0.0 --sleep-seconds 0.2
```

**Input panel**

Same harder-domain panel as round55:
- `7` states
- `40` unordered gap pairs
- `31` ordered pairs

**External judge metrics**

Gap task:
- AUROC = `0.7903`
- accuracy = `0.7750`
- positive mean prob = `0.9274`
- negative mean prob = `0.8389`
- mean gap = `+0.0885`

Direction task:
- AUROC = `0.9708`
- accuracy = `0.9355`
- positive mean prob = `0.8460`
- negative mean prob = `0.2254`
- mean gap = `+0.6206`

Files:
- [artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl)
- [artifacts/object_gate_round56/putnam_v1_judge_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_summary.json)
- [artifacts/object_gate_round56/object_gate_round56_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/object_gate_round56_summary.md)

**Comparison**

Against round55 on the same Putnam slice:
- frozen hidden:
  - DeepSeek gap/direction AUROC = `0.3405 / 0.3502`
  - Goedel gap/direction AUROC = `0.3728 / 0.3007`
- external judge:
  - gap/direction AUROC = `0.7903 / 0.9708`

**Conclusion**

- On genuinely hard Putnam states, external after-state judging remains robust.
- Frozen hidden no longer provides reliable cross-state pairwise progress separability on the same slice.
- Current practical boundary is now clear:
  - latent supervision looks useful inside the model competence regime
  - external judging remains stronger beyond that regime

## 2026-04-09 Round57: `before hidden` partially predicts latent failure, and trust-gated hybrid beats latent-only on Putnam

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_state_first_trust_gating.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_state_first_trust_gating.py --easy-oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --easy-generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --easy-replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --easy-sep artifacts/object_gate_round51/deepseek_state_first_panel_v2_consensus_sep.json --putnam-oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --putnam-generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --putnam-replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --putnam-sep artifacts/object_gate_round55/deepseek_putnam_v1_sep.json --putnam-judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round57/deepseek_trust_gating.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_state_first_trust_gating.py --easy-oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --easy-generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --easy-replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --easy-sep artifacts/object_gate_round51/goedel_state_first_panel_v2_consensus_sep.json --putnam-oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --putnam-generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --putnam-replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --putnam-sep artifacts/object_gate_round55/goedel_putnam_v1_sep.json --putnam-judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round57/goedel_trust_gating.json --device cuda:0
```

**Trust definition**

Per-state, model-specific:
- `trust = 1` iff direction mean gap > 0 and gap mean gap > 0 when gap negatives exist
- else `trust = 0`

This is a minimal proxy for:
- "can we trust latent ranking on this state?"

**Trust prediction from `before hidden`**

DeepSeek:
- linear AUROC = `0.7037`
- centroid AUROC = `0.8222`

Goedel:
- linear AUROC = `0.8481`
- centroid AUROC = `0.8444`

**Putnam hybrid**

DeepSeek gap:
- latent-only AUROC = `0.3405`
- judge-only AUROC = `0.7903`
- hybrid AUROC = `0.6362`

DeepSeek direction:
- latent-only AUROC = `0.3502`
- judge-only AUROC = `0.9750`
- hybrid AUROC = `0.7492`

Goedel gap:
- latent-only AUROC = `0.3728`
- judge-only AUROC = `0.7903`
- hybrid AUROC = `0.7652`

Goedel direction:
- latent-only AUROC = `0.3007`
- judge-only AUROC = `0.9750`
- hybrid AUROC = `0.7529`

Files:
- [artifacts/object_gate_round57/deepseek_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/deepseek_trust_gating.json)
- [artifacts/object_gate_round57/goedel_trust_gating.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/goedel_trust_gating.json)
- [artifacts/object_gate_round57/object_gate_round57_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round57/object_gate_round57_summary.md)

**Conclusion**

- `before hidden` carries a real, partially predictive competence/trust signal.
- That trust signal is useful enough to improve over latent-only routing on Putnam.
- But it still does not match judge-only quality.

So the current strongest system-level read is:
- latent progress = competence-regime internal signal
- before-hidden trust = partial competence-boundary detector
- external judge = still the stronger hard-state supervisor

## 2026-04-09 Round58: Putnam hard failure is a cross-state geometry failure, not a total loss of local signal

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/analyze_state_first_locality.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_state_first_locality.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round58/deepseek_putnam_locality.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_state_first_locality.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round58/goedel_putnam_locality.json --device cuda:0
```

**Design**

Same Putnam v1 panel as round55, but compare:
- cross-state: leave-one-state-out
- within-state: leave-one-pair-out inside each state

For direction, both orientations of the same unordered pair are held out together to avoid leakage.

**Results**

DeepSeek gap:
- cross linear AUROC = `0.3405`
- within linear AUROC = `0.7796`

DeepSeek direction:
- cross linear AUROC = `0.3502`
- within linear AUROC = `0.9355`

Goedel gap:
- cross linear AUROC = `0.3728`
- within linear AUROC = `0.7186`

Goedel direction:
- cross linear AUROC = `0.3007`
- within linear AUROC = `0.8824`

Files:
- [artifacts/object_gate_round58/deepseek_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/deepseek_putnam_locality.json)
- [artifacts/object_gate_round58/goedel_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/goedel_putnam_locality.json)
- [artifacts/object_gate_round58/object_gate_round58_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/object_gate_round58_summary.md)

**Conclusion**

- Hard Putnam does **not** eliminate latent progress signal entirely.
- What collapses is **cross-state transfer / shared geometry**.
- A strong **within-state local ordering signal** still survives in both DeepSeek and Goedel.

This sharpens the previous boundary:
- round55: hard Putnam breaks frozen-hidden separability
- round58: the break is specifically a **global geometry** failure, not a total loss of local object signal

## 2026-04-09 Round59: Putnam hard locality is a state-specific affordance geometry; external judge is closer to a cross-state canonical scalar

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/analyze_putnam_mechanism.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_putnam_mechanism.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --locality-json artifacts/object_gate_round58/deepseek_putnam_locality.json --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round59/deepseek_putnam_mechanism.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_putnam_mechanism.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --locality-json artifacts/object_gate_round58/goedel_putnam_locality.json --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round59/goedel_putnam_mechanism.json --device cuda:0
```

**Design**

On the same Putnam v1 hard panel:
- attach simple state-structure features
- build per-state latent `better-minus-worse` prototypes from `h_plus`
- compare each ordered pair against:
  - its own state prototype
  - a leave-one-state-out global prototype
- compare this to external judge behavior across the same states

**Results**

DeepSeek prototype alignment:
- off-diagonal prototype mean cosine = `-0.0097`
- min/max off-diagonal cosine = `-0.3562 / 0.1236`

Goedel prototype alignment:
- off-diagonal prototype mean cosine = `-0.0161`
- min/max off-diagonal cosine = `-0.3791 / 0.2750`

Representative locality gap:
- `putnam_1993_a4__sorry0`
  - DeepSeek within/global prototype cosine = `0.9642 / -0.0226`
  - Goedel within/global prototype cosine = `0.9545 / -0.0186`
- `putnam_2013_b4__sorry2`
  - DeepSeek within/global = `0.8695 / 0.0021`
  - Goedel within/global = `0.8422 / 0.0396`

Judge global pattern on the same panel:
- mean direction correct probability = `0.8115`
- mean gap correct probability = `0.7550`
- direction correct probability by oracle tier gap:
  - gap `1` -> `0.7985`
  - gap `2` -> `0.8584`
  - gap `3` -> `0.9000`

Files:
- [scripts/analyze_putnam_mechanism.py](/cephfs/luyanzhen/apg/LTV/scripts/analyze_putnam_mechanism.py)
- [artifacts/object_gate_round59/deepseek_putnam_mechanism.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round59/deepseek_putnam_mechanism.json)
- [artifacts/object_gate_round59/goedel_putnam_mechanism.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round59/goedel_putnam_mechanism.json)
- [artifacts/object_gate_round59/object_gate_round59_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round59/object_gate_round59_summary.md)

**Conclusion**

- Putnam hard latent failure is not “no object”; it is **loss of cross-state alignment**.
- Each hard state still carries a real local affordance direction in latent space.
- Those local directions are almost orthogonal on average across states, so no transferable global geometry emerges.
- The external judge is more stable because it behaves more like a **cross-state canonical scalar**, with confidence tracking oracle tier gaps across different states.

## 2026-04-09 Round60: Goal-aligned proof-state features recover coarse hard cross-state geometry, but not canonical ranking direction

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_putnam_goal_features.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_putnam_goal_features.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round60/deepseek_putnam_goal_features.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_putnam_goal_features.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round60/goedel_putnam_goal_features.json --device cuda:0
```

**Design**

Replace the full-prompt candidate representation with proof-state-aligned mean-pooled features:
- `goal_after_mean`
- `goal_delta_mean`
- `goal_concat_rel = [before ; after ; delta]`

Evaluate the same Putnam v1 hard panel on:
- gap task: ordered vs equivalent
- direction task: better vs worse

**Results**

DeepSeek:
- baseline `h_plus` cross AUROC:
  - gap = `0.3405`
  - direction = `0.3502`
- `goal_after_mean`:
  - gap cross = `0.6362`
  - direction cross = `0.2425`
- `goal_concat_rel`:
  - gap cross = `0.6362`
  - direction cross = `0.4527`

Goedel:
- baseline `h_plus` cross AUROC:
  - gap = `0.3728`
  - direction = `0.3007`
- `goal_after_mean`:
  - gap cross = `0.6487`
  - direction cross = `0.2950`
- `goal_concat_rel`:
  - gap cross = `0.6452`
  - direction cross = `0.3970`

Files:
- [scripts/evaluate_putnam_goal_features.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_putnam_goal_features.py)
- [artifacts/object_gate_round60/deepseek_putnam_goal_features.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round60/deepseek_putnam_goal_features.json)
- [artifacts/object_gate_round60/goedel_putnam_goal_features.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round60/goedel_putnam_goal_features.json)
- [artifacts/object_gate_round60/object_gate_round60_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round60/object_gate_round60_summary.md)

**Conclusion**

- Hard Putnam does contain recoverable **coarse cross-state structure** when the feature is anchored directly to proof-state text.
- That structure is enough to improve `ordered vs equivalent` substantially on both models.
- But it still does **not** recover a stable cross-state ranking direction for `better vs worse`.

So the harder-domain geometry picture sharpens further:
- full-prompt latent = strongly local
- goal-aligned proof-state features = coarse cross-state boundary
- judge = still the strongest canonical cross-state ranking signal

## 2026-04-09 Round61: Mixed-panel hybrid reranking converts latent signal into real utility

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && LTV_API_BASE_URL='https://ark.cn-beijing.volces.com/api/v3' LTV_API_MODEL='ep-20251213141929-gk2jb' LTV_API_KEY='8da5e4ba-59ad-47af-8f87-005fd1d1641b' python scripts/judge_state_first_pairwise_with_api.py --oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --rows-output artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl --summary-output artifacts/object_gate_round61/panel_v2_consensus_judge_summary.json --temperature 0.0 --sleep-seconds 0.05
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_hybrid_reranking.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_hybrid_reranking.py --easy-oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --easy-generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --easy-replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --easy-judge-rows artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl --putnam-oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --putnam-generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --putnam-replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --putnam-judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --trust-json artifacts/object_gate_round57/deepseek_trust_gating.json --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round61/deepseek_hybrid_reranking.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_hybrid_reranking.py --easy-oracle data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl --easy-generated artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl --easy-replayed artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl --easy-judge-rows artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl --putnam-oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --putnam-generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --putnam-replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --putnam-judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --trust-json artifacts/object_gate_round57/goedel_trust_gating.json --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round61/goedel_hybrid_reranking.json --device cuda:0
```

**Design**

Build a mixed utility panel with:
- `17` easy/medium consensus oracle states
- `7` Putnam hard oracle states
- `24` states total
- `131` replay-ok candidates total

Compare:
- weak baseline
- latent-only reranking
- judge-only reranking
- trust-gated hybrid reranking

The trust gate is reused from round57:
- state-level trust predicted from `before hidden`
- latent ranking used in trusted regions
- external judge ranking used in untrusted regions

**Judge coverage**

Easy/medium external judge on the consensus panel:
- gap AUROC = `0.9429`
- direction AUROC = `1.0000`

Files:
- [artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/panel_v2_consensus_judge_rows.jsonl)
- [artifacts/object_gate_round61/panel_v2_consensus_judge_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/panel_v2_consensus_judge_summary.json)

**Results**

DeepSeek:
- baseline:
  - top1 hit = `0.2917`
  - top2 hit = `0.5000`
  - mean NDCG = `0.8366`
- latent-only:
  - top1 hit = `0.7500`
  - top2 hit = `0.8333`
  - mean NDCG = `0.9256`
- judge-only:
  - top1 hit = `0.9583`
  - top2 hit = `1.0000`
  - mean NDCG = `0.9914`
- centroid-trust hybrid:
  - top1 hit = `0.9583`
  - top2 hit = `1.0000`
  - mean NDCG = `0.9901`

Goedel:
- baseline:
  - top1 hit = `0.2917`
  - top2 hit = `0.5000`
  - mean NDCG = `0.8366`
- latent-only:
  - top1 hit = `0.8333`
  - top2 hit = `0.9167`
  - mean NDCG = `0.9509`
- judge-only:
  - top1 hit = `0.9583`
  - top2 hit = `1.0000`
  - mean NDCG = `0.9914`
- centroid-trust hybrid:
  - top1 hit = `0.9583`
  - top2 hit = `1.0000`
  - mean NDCG = `0.9852`

Files:
- [scripts/evaluate_hybrid_reranking.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_hybrid_reranking.py)
- [artifacts/object_gate_round61/deepseek_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/deepseek_hybrid_reranking.json)
- [artifacts/object_gate_round61/goedel_hybrid_reranking.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/goedel_hybrid_reranking.json)
- [artifacts/object_gate_round61/object_gate_round61_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round61/object_gate_round61_summary.md)

**Conclusion**

- This is the first positive `conversion gate` result.
- Latent-only ranking already has real utility beyond the weak baseline on the mixed easy+hard panel.
- Judge-only remains the strongest overall signal.
- But trust-gated hybrid closes most of the gap, especially with the centroid trust predictor.

Current best system reading:
- `after hidden` = cheap local reranker
- `before hidden` = trust / competence gate
- external judge = fallback canonical scorer beyond the latent regime

## 2026-04-09 Round62: Budgeted k-candidate reranking shows strong quality-cost tradeoff

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_budgeted_hybrid_reranking.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_budgeted_hybrid_reranking.py --result-json artifacts/object_gate_round61/deepseek_hybrid_reranking.json --trust-json artifacts/object_gate_round57/deepseek_trust_gating.json --output artifacts/object_gate_round62/deepseek_budgeted_hybrid.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_budgeted_hybrid_reranking.py --result-json artifacts/object_gate_round61/goedel_hybrid_reranking.json --trust-json artifacts/object_gate_round57/goedel_trust_gating.json --output artifacts/object_gate_round62/goedel_budgeted_hybrid.json
```

**Design**

Use the round61 mixed-panel ranking outputs directly and evaluate exact candidate subsets of size:
- `k = 4`
- `k = 6`

Compare:
- baseline
- latent-only
- judge-only
- centroid-trust hybrid

Judge cost is measured as pairwise judge comparisons:
- judge-only cost = `C(k, 2)` per subset
- hybrid cost = `C(k, 2)` only on untrusted states

Files:
- [scripts/evaluate_budgeted_hybrid_reranking.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_budgeted_hybrid_reranking.py)
- [artifacts/object_gate_round62/deepseek_budgeted_hybrid.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round62/deepseek_budgeted_hybrid.json)
- [artifacts/object_gate_round62/goedel_budgeted_hybrid.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round62/goedel_budgeted_hybrid.json)
- [artifacts/object_gate_round62/object_gate_round62_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round62/object_gate_round62_summary.md)

**Results**

DeepSeek, `k = 4`:
- latent-only:
  - top1 max-tier hit = `0.9675`
  - top1 solved hit = `0.7378`
- judge-only:
  - top1 max-tier hit = `0.9977`
  - top1 solved hit = `0.7401`
  - mean judge pair calls = `6.0`
- centroid hybrid:
  - top1 max-tier hit = `0.9838`
  - top1 solved hit = `0.7401`
  - mean judge pair calls = `0.8213`
  - judge-cost ratio = `0.1369`

DeepSeek, `k = 6`:
- latent-only:
  - top1 max-tier hit = `1.0000`
  - top1 solved hit = `0.8649`
- judge-only:
  - top1 max-tier hit = `1.0000`
  - top1 solved hit = `0.8649`
  - mean judge pair calls = `15.0`
- centroid hybrid:
  - top1 max-tier hit = `1.0000`
  - top1 solved hit = `0.8649`
  - mean judge pair calls = `1.0811`
  - judge-cost ratio = `0.0721`

Goedel, `k = 4`:
- latent-only:
  - top1 max-tier hit = `0.9211`
  - top1 solved hit = `0.7309`
- judge-only:
  - top1 max-tier hit = `0.9977`
  - top1 solved hit = `0.7401`
  - mean judge pair calls = `6.0`
- centroid hybrid:
  - top1 max-tier hit = `0.9304`
  - top1 solved hit = `0.7309`
  - mean judge pair calls = `0.8213`
  - judge-cost ratio = `0.1369`

Goedel, `k = 6`:
- latent-only:
  - top1 max-tier hit = `0.9459`
  - top1 solved hit = `0.8649`
- judge-only:
  - top1 max-tier hit = `1.0000`
  - top1 solved hit = `0.8649`
  - mean judge pair calls = `15.0`
- centroid hybrid:
  - top1 max-tier hit = `0.9459`
  - top1 solved hit = `0.8649`
  - mean judge pair calls = `1.0811`
  - judge-cost ratio = `0.0721`

**Conclusion**

- Round61's mixed-panel utility result survives a more search-like `k`-candidate subset evaluation.
- Latent-only remains far above baseline.
- Judge-only remains strongest.
- The centroid-trust hybrid preserves most of the quality while using only about:
  - `13.7%` of judge-only pairwise calls at `k = 4`
  - `7.2%` of judge-only pairwise calls at `k = 6`

So the current system picture becomes sharper:
- latent = cheap local reranker
- trust = judge budget controller
- judge = sparse fallback for hard / untrusted states

**Post-hoc scope correction**

Round62 is useful, but the budgeted subset protocol is strongly easy-dominated:
- `k = 4`: easy subsets = `422`, Putnam subsets = `9`
- `k = 6`: easy subsets = `111`, Putnam subsets = `0`

So round62 should **not** be cited as hard-domain budgeted success.

Hard-only sanity check on the `k = 4` Putnam subsets:

DeepSeek:
- latent-only:
  - top1 max-tier hit = `0.1111`
  - top1 solved hit = `0.0000`
- judge-only:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`
- hybrid:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`

Goedel:
- latent-only:
  - top1 max-tier hit = `0.4444`
  - top1 solved hit = `0.1111`
- judge-only:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`
- hybrid:
  - top1 max-tier hit = `0.8889`
  - top1 solved hit = `0.1111`

Correct reading:
- round62 supports utility in the current mixed/easy-heavy regime
- it does not overturn the earlier hard-Putnam boundary

## 2026-04-09 Round63: Hard-aware stratified budgeted evaluation restores the true hard/easy split

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/evaluate_stratified_budgeted_hybrid.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_stratified_budgeted_hybrid.py --result-json artifacts/object_gate_round61/deepseek_hybrid_reranking.json --trust-json artifacts/object_gate_round57/deepseek_trust_gating.json --output artifacts/object_gate_round63/deepseek_stratified_budgeted.json
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/evaluate_stratified_budgeted_hybrid.py --result-json artifacts/object_gate_round61/goedel_hybrid_reranking.json --trust-json artifacts/object_gate_round57/goedel_trust_gating.json --output artifacts/object_gate_round63/goedel_stratified_budgeted.json
```

**Design**

Correct the round62 protocol by:
- splitting `easy` vs `putnam`
- using state-balanced macro averages
- restricting hard-side budgets to valid `k = 3, 4`

Files:
- [scripts/evaluate_stratified_budgeted_hybrid.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_stratified_budgeted_hybrid.py)
- [artifacts/object_gate_round63/deepseek_stratified_budgeted.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round63/deepseek_stratified_budgeted.json)
- [artifacts/object_gate_round63/goedel_stratified_budgeted.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round63/goedel_stratified_budgeted.json)
- [artifacts/object_gate_round63/object_gate_round63_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round63/object_gate_round63_summary.md)

**Results**

DeepSeek, Putnam-only:
- `k = 3`
  - latent-only:
    - top1 max-tier = `0.3429`
    - top1 solved = `0.0000`
  - judge-only:
    - top1 max-tier = `0.8929`
    - top1 solved = `0.1071`
  - hybrid:
    - top1 max-tier = `0.8929`
    - top1 solved = `0.1071`
- `k = 4`
  - latent-only:
    - top1 max-tier = `0.0400`
    - top1 solved = `0.0000`
  - judge-only:
    - top1 max-tier = `0.8000`
    - top1 solved = `0.2000`
  - hybrid:
    - top1 max-tier = `0.8000`
    - top1 solved = `0.2000`

Goedel, Putnam-only:
- `k = 3`
  - latent-only:
    - top1 max-tier = `0.5643`
    - top1 solved = `0.1071`
  - judge-only:
    - top1 max-tier = `0.8929`
    - top1 solved = `0.1071`
  - hybrid:
    - top1 max-tier = `0.8929`
    - top1 solved = `0.1071`
- `k = 4`
  - latent-only:
    - top1 max-tier = `0.4800`
    - top1 solved = `0.2000`
  - judge-only:
    - top1 max-tier = `0.8000`
    - top1 solved = `0.2000`
  - hybrid:
    - top1 max-tier = `0.8000`
    - top1 solved = `0.2000`

Easy-only sanity check:
- DeepSeek easy `k = 4`:
  - latent-only top1 max-tier = `0.9950`
  - hybrid mean judge calls = `0.7059` vs judge-only `6.0`
- Goedel easy `k = 4`:
  - latent-only top1 max-tier = `0.9723`
  - hybrid mean judge calls = `0.7059` vs judge-only `6.0`

**Conclusion**

- The concern about round62 was correct: its aggregate was strongly easy-dominated.
- Hard-only budgeted evaluation preserves the earlier boundary:
  - latent-only is still weak on Putnam
  - judge-only is still strong
  - hybrid works by routing hard states to judge
- So the real utility story is:
  - easy/medium -> latent + trust gives strong savings
  - hard Putnam -> trust should escalate, not trust latent ranking

## 2026-04-09 Round64: Coarse bottleneck typing does not recover shared latent hard geometry

**Commands**

```bash
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python -m py_compile scripts/analyze_putnam_bottleneck_types.py
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_putnam_bottleneck_types.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --typing-json configs/object_gate/putnam_bottleneck_types_v0.json --model-path /cephfs/shared/hf_cache/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B/snapshots/a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b --output artifacts/object_gate_round64/deepseek_putnam_bottleneck_types.json --device cuda:0
source /root/miniconda3/etc/profile.d/conda.sh && conda activate lean && python scripts/analyze_putnam_bottleneck_types.py --oracle data/annotations/state_first_progress_oracle_putnam_v1.jsonl --generated artifacts/object_gate_round55/state_first_putnam_candidates_v1.jsonl --replayed artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl --judge-rows artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl --typing-json configs/object_gate/putnam_bottleneck_types_v0.json --model-path /cephfs/shared/hf_cache/hub/models--Goedel-LM--Goedel-Prover-V2-8B/snapshots/dfd02e6271a58375dfbf3ece0175277cf6b6a89a --output artifacts/object_gate_round64/goedel_putnam_bottleneck_types.json --device cuda:0
```

**Design**

Manually type the `7` Putnam hard states into:
- `structural_reduction`
- `algebraic_normalization`
- `setup_extraction`

Then test whether type-conditioned prototypes restore cross-state directionality better than the global pool.

Files:
- [configs/object_gate/putnam_bottleneck_types_v0.json](/cephfs/luyanzhen/apg/LTV/configs/object_gate/putnam_bottleneck_types_v0.json)
- [scripts/analyze_putnam_bottleneck_types.py](/cephfs/luyanzhen/apg/LTV/scripts/analyze_putnam_bottleneck_types.py)
- [artifacts/object_gate_round64/deepseek_putnam_bottleneck_types.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round64/deepseek_putnam_bottleneck_types.json)
- [artifacts/object_gate_round64/goedel_putnam_bottleneck_types.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round64/goedel_putnam_bottleneck_types.json)
- [artifacts/object_gate_round64/object_gate_round64_summary.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round64/object_gate_round64_summary.md)

**Results**

Prototype alignment:

DeepSeek:
- within-type off-diagonal mean cosine = `-0.0414`
- cross-type off-diagonal mean cosine = `0.0030`

Goedel:
- within-type off-diagonal mean cosine = `-0.0502`
- cross-type off-diagonal mean cosine = `-0.0024`

DeepSeek type means:
- `algebraic_normalization`:
  - same-type direction AUROC = `0.2170`
  - global direction AUROC = `0.4022`
- `structural_reduction`:
  - same-type direction AUROC = `0.5056`
  - global direction AUROC = `0.7885`

Goedel type means:
- `algebraic_normalization`:
  - same-type direction AUROC = `0.1141`
  - global direction AUROC = `0.2044`
- `structural_reduction`:
  - same-type direction AUROC = `0.6022`
  - global direction AUROC = `0.7918`

Judge by type stays relatively stable:
- `algebraic_normalization` direction correct prob = `0.7641`
- `setup_extraction` = `0.7778`
- `structural_reduction` = `0.8650`

**Conclusion**

- This coarse bottleneck taxonomy does not recover shared latent hard-state geometry.
- Hard Putnam latent structure is therefore more local than:
  - global geometry
  - and also more local than this first-pass type grouping
- So the updated reading is:
  - easy/medium -> shared latent progress geometry
  - hard -> state-local affordance geometry
  - coarse hard-state typing is still insufficient to restore shared latent ranking structure

## 2026-04-09 Synthesis v1: Consolidated object / boundary / system picture

**Goal**

Consolidate the full object-gate line into one internal document:

- original question
- why CTS was replaced
- `state-first -> Lean legality -> human oracle`
- easy/medium object result
- hard Putnam boundary
- current claim hierarchy
- proposal rewrite direction

**File**

- [artifacts/object_gate_synthesis_v1.md](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_synthesis_v1.md)

**Conclusion**

The current strongest synthesis is:

- easy/medium -> shared latent progress geometry exists and is low-complexity readable
- hard Putnam -> cross-state latent geometry collapses, but within-state local ordering remains
- `after hidden` is best read as candidate-level local progress / affordance signal
- `before hidden` is best read as competence / trust signal
- external judge behaves like a more canonical hard-domain progress scalar
- coarse bottleneck typing does not recover shared hard latent geometry

So the proposal should now be framed as:

- **competence-scoped latent process supervision**

rather than:

- universal latent replacement for hard-domain judging
