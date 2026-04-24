# TriVer

- 你可以使用/cephfs/shared/hf_cache/hub/Qwen3* 系列的模型（开始实验可以使用1.7B或4B的模型），可以暂时不考虑多模型交叉（一定需要的话你可以告知用户，用户方下载）
- 需要的数据可以下载放到data目录下
- 可以使用的conda环境是infer（大部分环境已经装好了，如果还需要一些额外的包或者工具和用户确认）
- 如果你需要api调用来做数据或是别的这里也给你提供（需要给出用量和金额预算）
deepseek-v3.2:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  endpoint: ep-20251213141929-gk2jb
  api_key: 8da5e4ba-59ad-47af-8f87-005fd1d1641b

## Week 1 Entry Point

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --output-dir outputs/week1_run2 \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --plot-only \
  --input-csv outputs/week1_run2/prefix_oracle_records.csv \
  --output-dir outputs/week1_run2
```

第二域示例：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --augment-revise-prefixes \
  --output-dir outputs/week1_linear_8b_smoke \
  --skip-plots
```

输出写到你指定的 `--output-dir`，并同步维护 `history/progress.md` 与 `history/results.md`。

### API-backed rollout generation

如果要直接用 API 跑 prefix rollout / revise 数据构造，推荐先把 API 配置放到环境变量里，再复用同一条 `run_week1_oracle.py`：

```bash
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 4 \
  --num-rollouts 4 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --output-dir outputs/week1_api_smoke \
  --skip-plots
```

说明：
- `--backend api` 只替换 rollout / revise 的 generation backend；现有 exact-checker env 仍然负责 trace checking 与 utility 计算。
- `--model-path` 在 API 模式下默认作为 tokenizer fallback，用于 token counting；如需分离，可显式传 `--tokenizer-path`。
- `--prompt-style api_strict` 会启用更强的格式/单步变换约束；当前它适合作为 paired ablation，不应直接替代默认 prompt。
- `--prompt-style api_revise_focus` 只强化 `revise_1` 的 rollback/replace 语义；它更像 action-construction probe，而不是全局格式 prompt。
- `--prompt-style api_revise_candidates` 会在 `revise_1` 中显式列出合法一步候选；这更强，也更容易改变 action prior，目前只应作为 candidate-guided ablation 使用。
- `--prompt-style api_revise_invalid_focus` 只在前缀已经无效时启用更强的 revise 语义；它是当前更平衡的默认候选。
- `--recoverable-style local_changed_token` 会优先扰动当前步骤里新引入的数字；它是 recoverable-prefix 构造的 paired ablation，目前不应替代默认 `recoverable-style=default`。
- 目前 API backend 走 OpenAI-compatible `POST /chat/completions`。
- 如果环境里没有 `matplotlib`，脚本会在 summary 与 CSV/JSON 写完后自动跳过画图，而不是让整次 run 失败。

### Judge-Based Supporting Benchmark

如果要补更宽的 supporting benchmark，而不是继续只在 exact-checker toy 域里造数据，可以使用：

```bash
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_judged_benchmark.py \
  --dataset gsm8k \
  --dataset-config main \
  --dataset-split test \
  --num-samples 3 \
  --max-decision-points 2 \
  --num-rollouts 2 \
  --total-budget-tokens 160 \
  --temperature 0 \
  --judge-ensemble-mode dual \
  --augment-revise-prefixes \
  --output-dir outputs/week1_gsm8k_judged_smoke_v1
```

说明：
- 这条线是 `judge_based_supporting`，不是 exact-checker 主证据。
- generation 和 judge 都走 API；judge 负责：
  - prefix risk `q_t`
  - final-answer correctness
- 当前默认 demo 数据源是 `gsm8k`。
- `--base-traces-json` 可用于 replay 已缓存的 `base_traces.json`，这样 judge/utility probe 能在固定 generation 的前提下做真正 paired 的比较。
- 如果运行环境没有 `transformers`，该脚本也可以不传 tokenizer，直接使用粗粒度 token fallback。
- 当前 repo 里 `datasets` 在系统 Python 下可直接用；如果 `infer` 环境里缺 `datasets`，先用 `PYTHONPATH=. python ...` 跑 smoke 即可。
- `--judge-ensemble-mode dual` 比 `single` 更稳；在固定 base traces 的 replay probe 上，`--judge-ensemble-mode dual_consensus` 进一步把 mean action gap 从 `0.1339` 拉到 `0.1879`，且不降低 determinacy，所以它是当前 broad judged smoke 更强的 judge-stability 候选。
- `--generation-style compact_final` 是 broad judged benchmark 的 generation-side paired ablation；它能提高 `Final answer` 完整率，但当前 GSM8K smoke 上并没有提升 determinacy / action gap，所以不应替代默认 `generation-style=default`。
- `--gamma-wrong 1.0` 在 replay 固定 `v2_dual` base traces 后仍没有提升 determinacy，因此 broad judged 线当前也不应优先通过更重的 wrong-penalty 来拉开 action gap。

## Week 2 Baselines

```bash
PYTHONPATH=. python scripts/run_week2_baselines.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --output-dir outputs/week2_linear_8b_baselines_v1
```

Representation-based baseline 准备：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states.npz

# Optional: probe different prefix representations.
PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --pooling mean_content \
  --output-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states_mean_content.npz

PYTHONPATH=. python scripts/run_week2_baselines.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_linear_8b_baselines_repr_v1
```

Factorized controller：

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_linear_8b_factorized_v2

# Optional: use different prefix representations for q-head and S-head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --q-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_mean_content.npz \
  --s-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v3_split_repr

# Optional: richer S-side proxy using continue utility spread / wrong-rate / token-cost.
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 20 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v3 \
  --skip-plots

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v4_sproxy \
  --state-mode s_proxy

# Optional: stronger state heads for diagnosis.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v6_sproxy_pca_enet \
  --state-mode s_proxy \
  --state-head-model pca_enet

# Optional: robust value-head diagnostics.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v7_huber \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model huber

# Optional: structured value-head diagnostic.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v8_pairwise \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_logit

# Optional: nonlinear interaction value-head diagnostics.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v10_pairwise_interaction \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_interaction_logit

# Optional: uncertainty-aware value-head diagnostics.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v10_uncertainty_pairwise_interaction \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_interaction_logit

# Optional: joint state-value gate probe.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v11_joint_gate \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model joint_pairwise_gate

# Optional: per-pair error-calibrated valuation.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v13_pairwise_error_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_error_calibrated

# Optional: conditional pairwise calibration probe.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v14_pairwise_selective_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_selective_calibrated

# Optional: native heteroscedastic value head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v15_uncertainty_heteroscedastic \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_heteroscedastic_interaction

# Optional: native pairwise-difference heteroscedastic head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v16_uncertainty_pairwise_heteroscedastic \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_heteroscedastic_interaction

# Optional: shared-covariance heteroscedastic head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v17_uncertainty_shared_covariance \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_shared_covariance_heteroscedastic_interaction

# Optional: low-rank/shared-latent heteroscedastic head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v19_uncertainty_lowrank_covariance \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_lowrank_heteroscedastic_interaction

# Optional: rank-2 / multi-factor low-rank heteroscedastic head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v19_uncertainty_rank2_lowrank_covariance \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_rank2_lowrank_heteroscedastic_interaction

# Optional: conditional / input-dependent low-rank heteroscedastic head.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v20_uncertainty_conditional_lowrank_covariance \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_conditional_lowrank_heteroscedastic_interaction

# Optional: conditional-lowrank + per-pair shrinkage hybrid.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v22_conditional_lowrank_pairwise_error_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_pairwise_error_calibrated

# Optional: conditional-lowrank + capped pairwise shrinkage hybrid.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v23_conditional_lowrank_capped_pairwise_error_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_capped_pairwise_error_calibrated

# Optional: conditional-lowrank + banded/no-op pairwise calibration.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v24_conditional_lowrank_banded_pairwise_error_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_banded_pairwise_error_calibrated

# Optional: conditional-lowrank + 2-cluster pairwise calibration.
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v25_conditional_lowrank_clustered_pairwise_error_calibrated \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_clustered_pairwise_error_calibrated

# Optional: pooled cross-domain shared-vs-specialist comparison with explicit env feature.
PYTHONPATH=. python scripts/run_week2_cross_domain_portfolio.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_portfolio_env_conditioned_shared_conditional_lowrank \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --shared-value-head-model uncertainty_conditional_lowrank_heteroscedastic_interaction \
  --include-env-feature

PYTHONPATH=. python scripts/run_week2_cross_domain_portfolio.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_portfolio_env_conditioned_shared_hybrid \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --shared-value-head-model conditional_lowrank_pairwise_error_calibrated \
  --include-env-feature

# Optional: pooled learned router over domain specialists.
PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```
