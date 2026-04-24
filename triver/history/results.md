# TriVer Results Ledger

## 2026-03-09

### Entry: Week-1 arithmetic exact-checker setup

- Status: PARTIAL_GO
- Goal: 先完成 proposal Week 1 的第一域闭环，包括 oracle rollout、atlas、action-gap histogram、determinacy rate、crossing mass。
- Backbone: local `Qwen3-4B`
- Environment:
  - generation: `infer` conda env
  - plotting: base python env
- Output dirs:
  - `outputs/week1_run1/` (superseded)
  - `outputs/week1_run2/` (current)
- Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --output-dir outputs/week1_run2 \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --plot-only \
  --input-csv outputs/week1_run2/prefix_oracle_records.csv \
  --output-dir outputs/week1_run2
```

Run 1:
- Command: `outputs/week1_run1/`
- Result:
  - `num_prefixes = 9`
  - `crossing_mass_all = 0.6667`
  - `oracle_determinacy_rate = 0.0000`
- Diagnosis:
  - crossing 已出现，但 utility 惩罚过弱，top-2 action gap 太小，determinacy 失败
- Status: superseded by Run 2

Run 2:
- Command: `outputs/week1_run2/`
- Result:
  - `num_prefixes = 9`
  - `crossing_mass_all = 0.6667`
  - `oracle_determinacy_rate = 0.5556`
  - `invalid_prefix_rate = 0.5556`
  - `mean_action_gap = 0.0522`
  - `oracle action counts = {continue: 6, abstain: 3}`
- Artifacts:
  - `oracle_action_atlas.png`
  - `scalar_crossing.png`
  - `action_gap_histogram.png`
- Interpretation:
  - Week 1 的两个 Go/No-Go 信号已经在第一域上出现：crossing mass 非零，determinacy 不再过低
  - 但 `crossing_mass_high_determinacy = 0.0000`，说明当前 crossing 仍主要集中在低间隔区域，不能据此过度外推

Notes:
- 第一个域使用 fully parenthesized arithmetic reduction。
- `q_t` 先用 exact local invalidity indicator。
- scalar score 先用 `mu_continue` 做 Week-1 crossing 检查。
- Qwen3 需要 `chat_template + enable_thinking=False`，并改成逐行 rollout 才能稳定进入可检查轨迹。

### Entry: Week-1 second exact-checker domain (linear equations)

- Status: PARTIAL_GO
- Goal: 在第二个 exact-checker 域上复验 Week 1 的 oracle benchmark，并补足 `revise` 状态覆盖。
- Domain: `linear_equations`
- Key implementation:
  - 多域 oracle runner：`scripts/run_week1_oracle.py --env ...`
  - 受控 recoverable-prefix 扰动：`--augment-revise-prefixes`
  - 等式标准化：变量尽量放左侧，避免把简单 side-swap 误判成无效

Run A: `Qwen3-4B`, no perturb
- Output: `outputs/week1_linear_smoke/`
- Result:
  - `num_prefixes = 7`
  - `oracle_determinacy_rate = 0.4286`
  - `crossing_mass_all = 0.2857`
  - `crossing_mass_high_determinacy = 0.0000`
- Interpretation:
  - 第二域在 4B 上可跑通，但 revise 信号仍弱

Run B: `Qwen3-4B`, with recoverable-prefix perturbation
- Output: `outputs/week1_linear_run2/`
- Result:
  - `num_prefixes = 14`
  - `oracle_determinacy_rate = 0.5714`
  - `crossing_mass_all = 0.9286`
  - `crossing_mass_high_determinacy = 0.0000`
  - `oracle_action_counts = {abstain: 10, continue: 3, revise_1: 1}`
- Interpretation:
  - recoverable invalid prefix 已覆盖到，但 4B 仍明显偏向 `abstain`
  - 这说明第二域不是空的，但 4B backbone 下 revise 价值还不稳定

Run C: `Qwen3-8B`, with recoverable-prefix perturbation
- Output: `outputs/week1_linear_8b_smoke/`
- Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 4 \
  --num-rollouts 2 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_linear_8b_smoke \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --plot-only \
  --input-csv outputs/week1_linear_8b_smoke/prefix_oracle_records.csv \
  --output-dir outputs/week1_linear_8b_smoke
```

- Result:
  - `num_prefixes = 10`
  - `oracle_determinacy_rate = 0.9000`
  - `crossing_mass_all = 0.6000`
  - `crossing_mass_high_determinacy = 0.5556`
  - `invalid_prefix_rate = 0.5000`
  - `mean_action_gap = 0.3960`
  - `oracle_action_counts = {continue: 5, revise_1: 4, abstain: 1}`
  - `high_det_action_counts = {continue: 4, revise_1: 4, abstain: 1}`
- Interpretation:
  - 这是目前最接近 proposal killer result 的证据链
  - 在第二域上已经出现高确定性 `revise_1`，且高确定性 crossing 不再为零
  - 说明 `revise` 状态本身不是虚构的，4B 下更多是 backbone 能力瓶颈而非 benchmark 不成立

### Entry: Week-2 baseline initial test

- Status: INITIAL_SIGNAL
- Setting:
  - dataset: `outputs/week2_linear_8b_data_v1/`
  - env: `linear_equations`
  - backbone: `Qwen3-8B`
  - prefixes: `58`
  - high-determinacy subset used for training/eval: `41`
- Dataset summary:
  - `oracle_determinacy_rate = 0.7069`
  - `crossing_mass_all = 0.7414`
  - `crossing_mass_high_determinacy = 0.7561`
  - clean label distribution = `{abstain: 16, revise_1: 15, continue: 10}`
- Baseline script:
  - `scripts/run_week2_baselines.py`
  - `triver/baselines/week2.py`
- Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 20 \
  --num-rollouts 2 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v1 \
  --skip-plots

PYTHONPATH=. python scripts/run_week2_baselines.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --output-dir outputs/week2_linear_8b_baselines_v1 \
  --n-splits 5
```

- Result:
  - `ordered_scalar_mu`
    - action accuracy = `0.5833`
    - mean action regret = `0.3991`
  - `learned_1d_linear`
    - action accuracy = `0.7806`
    - mean action regret = `0.1533`
  - `direct_policy`
    - action accuracy = `0.7806`
    - mean action regret = `0.1533`
- Interpretation:
  - 这是第一轮直接支持 `ordered scalar insufficiency` 的 baseline 结果
  - 单一标量 `mu_continue` + ordered thresholds 明显劣于 learned-1D 和 direct-policy
  - 当前 learned-1D 与 direct-policy 持平，说明在这批特征与样本规模下，1D bottleneck 尚未显著吃亏
  - 这对 proposal 的含义是：
    - “原始 ordered scalar 不够”获得了初步支持
    - “TriVer factorization 优于 unstructured direct policy”还没有证据，不能提前写强 claim

### Entry: Week-2 cross-domain baseline extension

- Status: MIXED_SIGNAL
- Arithmetic dataset:
  - output: `outputs/week2_arithmetic_8b_data_v1/`
  - `num_prefixes = 62`
  - `oracle_determinacy_rate = 0.8548`
  - `crossing_mass_all = 0.8226`
  - `crossing_mass_high_determinacy = 0.7925`
- Arithmetic baseline:
  - output: `outputs/week2_arithmetic_8b_baselines_v1/`
  - `ordered_scalar_mu`
    - action accuracy = `0.7988`
    - mean action regret = `0.1642`
  - `direct_policy`
    - action accuracy = `0.6170`
    - mean action regret = `0.3272`
  - `learned_1d_linear`
    - action accuracy = `0.6188`
    - mean action regret = `0.3424`
- Comparison artifact:
  - `outputs/week2_domain_baseline_comparison.csv`
- Interpretation:
  - 这和 linear-equations 域形成明确分叉
  - 在 arithmetic 域，即使 crossing mass 很高，`mu_continue` ordered scalar 仍然是最强 baseline
  - 因此当前不能把 “ordered scalar insufficiency” 写成无条件结论；更准确的状态是：
    - 在 linear-equations 域上有强支持
    - 在 arithmetic 域上暂未成立，或当前特征/benchmark 还未把结构差异暴露出来

### Entry: Hidden-state baseline scaffolding

- Status: PIPELINE_READY
- New files:
  - `scripts/extract_prefix_hidden_states.py`
  - `triver/models/qwen_runner.py` 新增 last-hidden-state 提取
  - `scripts/run_week2_baselines.py --embedding-npz ...`
- Smoke validation:
  - hidden-state extraction on `outputs/week1_linear_8b_smoke/` succeeded
  - output: `outputs/week1_linear_8b_smoke/prefix_hidden_states.npz`
- Current boundary:
  - representation-based large-scale CV is not yet a stable reported result
  - until that finishes, current Week-2 conclusions should still be treated as tabular-feature baselines, not full proposal-grade hidden-state direct policy

### Entry: Representation-based baseline smoke

- Status: NEGATIVE_SMOKE
- Comparison artifact:
  - `outputs/week2_repr_vs_tabular_smoke.csv`
- Linear-equations, 2-fold same-split comparison:
  - tabular
    - `learned_1d_linear`: acc `0.5179`, regret `0.4181`
    - `direct_policy`: acc `0.3429`, regret `0.5819`
    - `ordered_scalar_mu`: acc `0.3429`, regret `0.5845`
  - hidden-state repr
    - `learned_1d_linear_repr`: acc `0.2917`, regret `0.5530`
    - `direct_policy_repr`: acc `0.1940`, regret `0.7216`
    - `ordered_scalar_mu_repr`: same as scalar baseline
- Arithmetic, 2-fold same-split comparison:
  - tabular
    - `ordered_scalar_mu`: acc `0.7913`, regret `0.1704`
    - `learned_1d_linear`: acc `0.5677`, regret `0.3895`
    - `direct_policy`: acc `0.5876`, regret `0.4184`
  - hidden-state repr
    - `ordered_scalar_mu_repr`: acc `0.7913`, regret `0.1704`
    - `direct_policy_repr`: acc `0.5085`, regret `0.4677`
    - `learned_1d_linear_repr`: acc `0.4338`, regret `0.4797`
- Interpretation:
  - 当前 hidden-state smoke 并没有提升 strongest baseline，反而弱于表格特征版
  - 这意味着“proposal-grade direct policy”还没有被当前实现逼到足够强
  - 因此现阶段不能用 representation smoke 去推翻表格特征版的跨域机制结论
  - 更稳妥的说法是：
    - strongest baseline 方向已接通，但尚未充分优化
    - 当前可信主结果仍是 tabular-feature baselines + 双域 oracle benchmark

### Entry: Week-2 factorized controller initial test

- Status: MECHANISTIC_SIGNAL
- Script:
  - `scripts/run_week2_factorized.py`
  - `triver/factorized/week2.py`
- Comparison artifact:
  - `outputs/week2_factorized_vs_baselines.csv`

Linear-equations:
- `factorized_exact_state`
  - accuracy = `0.7528`
  - regret = `0.1382`
- `factorized_predicted_state`
  - accuracy = `0.4889`
  - regret = `0.3130`
  - `q_auc = 0.8486`
  - `mu_rmse = 0.3851`
- Interpretation:
  - exact-state factorized controller 已接近甚至略优于当前最强 tabular baseline 的 regret
  - predicted-state factorized controller 明显更弱，说明主要瓶颈在 state identification，而不是 action-value head 结构本身

Arithmetic:
- `factorized_exact_state`
  - accuracy = `0.6806`
  - regret = `0.2984`
- `factorized_predicted_state`
  - accuracy = `0.2976`
  - regret = `0.5451`
  - `q_auc = 0.7756`
  - `mu_rmse = 0.4144`
- Interpretation:
  - 即使给 exact state，factorized controller 仍不如 `ordered_scalar_mu`
  - 这说明在 arithmetic 域，当前 `q / mu / nu` 这一组状态变量未必比 scalar 更有优势，或当前 value head 容量不足

Overall interpretation:
- 这批结果把 proposal 的问题进一步拆清楚了：
  - 在 `linear_equations` 域，TriVer 的 factorization 想法是有内容的，但当前弱在 state identification
  - 在 `arithmetic` 域，问题不只是 state identification，连 exact-state factorization 都未明显胜过 scalar
- 因此当前最合理的论文叙事已经非常清楚：
  - strongest universal claim 还不成立
  - 更稳的主线是条件性论文，核心问题变成：
    - 何时 exact state 足以带来更低 regret
    - 何时 scalar 仍然足够

### Entry: State-identification diagnostics for factorized controller

- Status: MECHANISTIC_SIGNAL
- Code changes:
  - `triver/models/qwen_runner.py`
  - `scripts/extract_prefix_hidden_states.py`
  - `triver/factorized/week2.py`
- New artifacts:
  - `outputs/week2_linear_8b_factorized_v2/`
  - `outputs/week2_arithmetic_8b_factorized_v2/`
  - `outputs/week2_linear_8b_data_v1/prefix_hidden_states_mean_content.npz`
  - `outputs/week2_linear_8b_factorized_mean_content_v1/`
  - `outputs/week2_factorized_state_id_diagnostics.csv`

Run A: hybrid exact-value diagnostic on existing `last_generation_prompt` embeddings

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_linear_8b_factorized_v2

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v1/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v2
```

Linear-equations:
- `factorized_exact_state`
  - accuracy = `0.7528`
  - regret = `0.1382`
- `factorized_predicted_state_exact_value`
  - accuracy = `0.6361`
  - regret = `0.2464`
  - `q_auc = 0.8486`
  - `mu_rmse = 0.3851`
- `factorized_predicted_state`
  - accuracy = `0.4889`
  - regret = `0.3130`

Arithmetic:
- `factorized_exact_state`
  - accuracy = `0.6806`
  - regret = `0.2984`
- `factorized_predicted_state_exact_value`
  - accuracy = `0.4627`
  - regret = `0.4895`
  - `q_auc = 0.7756`
  - `mu_rmse = 0.4144`
- `factorized_predicted_state`
  - accuracy = `0.2976`
  - regret = `0.5451`

Interpretation:
- 把 action-value head 固定在 canonical exact state 上后，predicted-state 结果在两域都明显变好。
- 这进一步支持当前主判断：主要损失来自 state reconstruction，而不是 factorized action-value head 本身。
- 线性方程域上，`0.2464` 的 regret 已经比旧版 predicted-state 明显更接近 exact-state `0.1382`；这个差距更像 state-ID gap，而不是 controller 架构无效。

Run B: `mean_content` prefix embedding probe on linear-equations

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --pooling mean_content \
  --output-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states_mean_content.npz

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v1/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v1/prefix_hidden_states_mean_content.npz \
  --output-dir outputs/week2_linear_8b_factorized_mean_content_v1
```

Linear-equations (`mean_content`):
- `factorized_predicted_state_exact_value`
  - accuracy = `0.5361`
  - regret = `0.3534`
  - `q_auc = 1.0000`
  - `mu_rmse = 0.5197`
- `factorized_predicted_state`
  - accuracy = `0.4861`
  - regret = `0.3823`

Interpretation:
- `mean_content` 并没有形成更好的统一 prefix representation。
- 它几乎把 `q` 做到了完美分离，但同时显著伤害了 `mu` 回归，导致 factorized controller 整体更差。
- 目前最合理的机制判断是：
  - `q` 与 `S` 并不一定共享同一个最优表示
  - 下一步应优先强化 `S-head`，而不是继续假设“同一 embedding + 线性头”自然足够

### Entry: Week-2 linear-equations v2 with Beta-posterior `S_t`

- Status: MECHANISTIC_SIGNAL
- Setting:
  - dataset: `outputs/week2_linear_8b_data_v2/`
  - env: `linear_equations`
  - backbone: `Qwen3-8B`
  - prefixes: `58`
  - oracle rollouts: `4`
- Code changes:
  - `triver/oracle/week1.py`
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
  - `triver/baselines/week2.py`
- Comparison artifact:
  - `outputs/week2_linear_8b_v2_controller_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
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
  --output-dir outputs/week2_linear_8b_data_v2 \
  --skip-plots

PYTHONPATH=. python scripts/run_week2_baselines.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --output-dir outputs/week2_linear_8b_baselines_v2 \
  --n-splits 5
```

Dataset summary:
- `oracle_determinacy_rate = 0.7414`
- `crossing_mass_all = 0.7414`
- `crossing_mass_high_determinacy = 0.7674`
- `mean_action_gap = 0.4921`
- `mu_continue` is no longer binary:
  - unique values = `{1/6, 5/6}`
- but `nu_continue` is still degenerate:
  - unique values = `{0.019841...}`

Baseline result:
- `direct_policy`
  - accuracy = `0.7278`
  - regret = `0.2199`
- `learned_1d_linear`
  - accuracy = `0.7056`
  - regret = `0.2575`
- `ordered_scalar_mu`
  - accuracy = `0.4944`
  - regret = `0.4228`

Interpretation:
- 在修正 `S_t` 平滑后，linear-equations 域上 `ordered_scalar_mu` 依然明显最差。
- 这说明之前的 scalar insufficiency 结论不依赖于 `mu` 恰好是 `0/1` 的伪二值化。
- 但 `nu` 仍为常数，意味着 proposal 里的完整 `S_t = (mu, nu)` 还没有在这个域上真正展开。

### Entry: Split-repr factorized probe on linear-equations v2

- Status: MECHANISTIC_SIGNAL
- New embeddings:
  - `outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz`
  - `outputs/week2_linear_8b_data_v2/prefix_hidden_states_mean_content.npz`
- Factorized outputs:
  - `outputs/week2_linear_8b_factorized_v3_last/`
  - `outputs/week2_linear_8b_factorized_v3_split_repr/`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --pooling mean_content \
  --output-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_mean_content.npz

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v3_last \
  --n-splits 5

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv \
  --q-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_mean_content.npz \
  --s-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v3_split_repr \
  --n-splits 5
```

Same representation (`last_generation_prompt` for both `q` and `S`):
- `factorized_exact_state`
  - accuracy = `0.7694`
  - regret = `0.1596`
- `factorized_predicted_state`
  - accuracy = `0.5889`
  - regret = `0.3401`
  - `q_auc = 0.8972`
  - `mu_rmse = 0.2866`
  - `nu_rmse ~= 0`

Split representation (`q = mean_content`, `S = last_generation_prompt`):
- `factorized_predicted_state`
  - accuracy = `0.6111`
  - regret = `0.3447`
  - `q_auc = 0.9778`
  - `mu_rmse = 0.2866`
  - `nu_rmse ~= 0`

Interpretation:
- split-repr 明显提升了 `q` 识别，但几乎没有改善 regret。
- 这说明在线性方程 v2 上，当前 controller gap 已不主要由 `q` 决定，而更像由 `S` 侧信息不足决定。
- `factorized_exact_state` 仍优于 tabular `direct_policy`，所以 factorization 在这个域上仍然有内容；问题主要是可学习状态没有把 exact-state 信号带过来。

### Entry: High-temperature `S_t` variance smoke

- Status: NEGATIVE_SMOKE
- Output:
  - `outputs/week2_linear_8b_s_variance_smoke/`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 8 \
  --num-rollouts 6 \
  --total-budget-tokens 64 \
  --temperature 1.0 \
  --top-p 0.95 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_s_variance_smoke \
  --skip-plots
```

Result:
- `mu_continue` unique values = `{0.125, 0.875}`
- `nu_continue` unique values = `{0.012152...}`

Interpretation:
- 即使提高随机度并增加 rollout 数，linear-equations 域上的 default continuation success 仍然几乎是“全成 / 全败”。
- 因此 `nu` 的退化并不主要来自后验平滑公式，也不主要来自温度过低，而更像是任务本身让 success-distribution 近确定性。
- 这对 proposal 的含义是：
  - 若坚持 `S_t` 为 success distribution，需要一个能产生更丰富默认继续不确定性的域
  - 或者把 `S_t` 改成更细粒度的 default-continue utility/distribution proxy

### Entry: Richer `S` proxy on linear-equations v3

- Status: POSITIVE_SIGNAL
- Goal:
  - test whether a richer default-continue utility/distribution proxy can recover some of the factorized gap that the degenerate `nu` could not
- New dataset:
  - `outputs/week2_linear_8b_data_v3/`
- New columns:
  - `continue_std_utility`
  - `continue_wrong_rate`
  - `continue_mean_tokens`
- Comparison artifact:
  - `outputs/week2_linear_8b_sproxy_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
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
```

Dataset check:
- `v3` and `v2` are identical on all pre-existing columns
- richer `S` proxy statistics are non-trivial:
  - `continue_wrong_rate` unique values = `{0.0, 0.5, 0.75, 1.0}`
  - `continue_mean_tokens` ranges from `0.0` to `20.5`
  - `continue_std_utility` ranges from `0.0` to `0.5369`

Factorized comparison:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v4_legacy \
  --n-splits 5 \
  --state-mode legacy

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v4_sproxy \
  --n-splits 5 \
  --state-mode s_proxy
```

Results:
- tabular baseline (`outputs/week2_linear_8b_baselines_v2/summary.csv`)
  - `direct_policy`: regret = `0.2199`
  - `ordered_scalar_mu`: regret = `0.4228`
- factorized, legacy state
  - `factorized_exact_state`: regret = `0.1596`
  - `factorized_predicted_state`: regret = `0.3401`
- factorized, richer `S` proxy
  - `factorized_exact_state`: regret = `0.1360`
  - `factorized_predicted_state`: regret = `0.2931`
  - `std_rmse = 0.1105`
  - `wrong_rate_rmse = 0.4745`
  - `mean_tok_rmse = 3.6884`

Interpretation:
- richer `S` proxy 首次在这个主域上给出了明确正信号：
  - predicted-state factorized 从 `0.3401` 降到 `0.2931`
  - exact-state factorized 从 `0.1596` 降到 `0.1360`
- 这说明 proposal 里“默认继续分布/价值侧信息”这一维是实的，只是当前 `nu` 本身不是一个足够有分辨率的载体。
- 但这个版本仍未超过 tabular `direct_policy = 0.2199`，所以 strongest factorization claim 依然不能写强。

Split-repr check with richer `S` proxy:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --q-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_mean_content.npz \
  --s-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v4_sproxy_split_repr \
  --n-splits 5 \
  --state-mode s_proxy
```

Result:
- `factorized_predicted_state`
  - regret = `0.3207`
  - `q_auc = 0.9778`

Interpretation:
- 再次验证了这条机制结论：
  - 更强的 `q` 识别本身不够
  - 当前改善主要来自 richer `S` proxy，而不是 `q` 表示增强

### Entry: Richer `S` proxy cross-domain extension on arithmetic

- Status: MIXED_SIGNAL
- Dataset:
  - `outputs/week2_arithmetic_8b_data_v2/`
- Comparison artifacts:
  - `outputs/week2_arithmetic_8b_sproxy_comparison.csv`
  - `outputs/week2_cross_domain_sproxy_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 20 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_arithmetic_8b_data_v2 \
  --skip-plots

PYTHONPATH=. python scripts/run_week2_baselines.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --output-dir outputs/week2_arithmetic_8b_baselines_v2 \
  --n-splits 5

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v5_legacy \
  --n-splits 5 \
  --state-mode legacy

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v5_sproxy \
  --n-splits 5 \
  --state-mode s_proxy
```

Dataset check:
- row order / problem / prefix trace are identical between `v1` and `v2`, so existing embeddings are safely reusable
- richer `S` proxy is non-trivial:
  - `mu_continue` has `3` values
  - `nu_continue` has `2` values
  - `continue_wrong_rate` has `{0.0, 1.0}`
  - `continue_mean_tokens` ranges from `0.0` to `41.5`

Baseline result:
- `ordered_scalar_mu`
  - regret = `0.1599`
- `direct_policy`
  - regret = `0.3272`

Factorized result:
- legacy
  - `factorized_exact_state`: regret = `0.2941`
  - `factorized_predicted_state`: regret = `0.4639`
- richer `S` proxy
  - `factorized_exact_state`: regret = `0.2147`
  - `factorized_predicted_state`: regret = `0.5113`

Interpretation:
- arithmetic 域上的 richer `S` proxy 不是没信号：
  - exact-state factorized 从 `0.2941` 改善到 `0.2147`
- 但 predicted-state 反而从 `0.4639` 恶化到 `0.5113`
- 这和 linear-equations 域形成了新的重要分叉：
  - linear 上 richer `S` proxy 同时帮助 exact-state 与 predicted-state
  - arithmetic 上 richer `S` proxy 只帮助 exact-state
- 最合理的机制判断是：
  - richer `S` proxy 本身是有信息量的
- 当前更大的问题是 arithmetic 域上的 `S-head` 学不到这部分状态
- 所以 cross-domain 叙事不再只是“scalar 是否足够”，还包括“哪些 `S` 状态是可学习的”

### Entry: State-head model sweep (`linear` vs `pca_enet`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New option:
  - `--state-head-model {linear,pca_ridge,pca_enet,rf}`
- Comparison artifact:
  - `outputs/week2_state_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v6_sproxy_pca_enet \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v5_sproxy_pca_enet \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

Arithmetic:
- default `linear` heads
  - `factorized_predicted_state_exact_value`: regret = `0.5113`
  - `factorized_predicted_state`: regret = `0.5113`
- `pca_enet` heads
  - `factorized_predicted_state_exact_value`: regret = `0.4616`
  - `factorized_predicted_state`: regret = `0.5313`

Linear-equations:
- default `linear` heads
  - `factorized_predicted_state`: regret = `0.2931`
- `pca_enet` heads
  - `factorized_predicted_state`: regret = `0.3433`

Interpretation:
- arithmetic 域上，`pca_enet` 说明 state head 本身还有改进空间：
  - exact-value diagnostic 明显变好（`0.5113 -> 0.4616`）
- 但 end-to-end predicted-state 反而更差（`0.5113 -> 0.5313`）
- 这把当前瓶颈进一步拆开了：
  - state identification 不是完全死局
  - 但 action-value head 在 noisy predicted state 上的训练/拟合同样是问题
- linear 域上 `pca_enet` 反而变差，说明更强/更复杂的 state-head 不是跨域统一更优；现在还不能把这类 head 直接升成新默认。

### Entry: Value-head training-mode formalization (`exact` vs `predicted` vs `OOF` vs `exact+OOF`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
- Comparison artifact:
  - `outputs/week2_value_head_train_mode_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v7_value_modes \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v6_value_modes \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

Arithmetic (`s_proxy + pca_enet`):
- `factorized_exact_state`: regret = `0.2147`
- `factorized_predicted_state_train_exact`: regret = `0.4616`
- `factorized_predicted_state_train_predicted`: regret = `0.5313`
- `factorized_predicted_state_train_exact_plus_oof`: regret = `0.6054`
- `factorized_predicted_state_train_predicted_oof`: regret = `0.6847`

Linear-equations (`s_proxy + pca_enet`):
- `factorized_exact_state`: regret = `0.1360`
- `factorized_predicted_state_train_exact_plus_oof`: regret = `0.2598`
- `factorized_predicted_state_train_exact`: regret = `0.3044`
- `factorized_predicted_state_train_predicted`: regret = `0.3433`
- `factorized_predicted_state_train_predicted_oof`: regret = `0.4121`

Interpretation:
- 这一步把之前“value head 可能是瓶颈”的离线判断正式升级成了 pipeline 结果。
- arithmetic 域上，最好的 predicted-state value head 训练方式仍是 `train_exact`；这说明当前更像是 predicted-state noise 直接污染训练，而不是简单的 train/test mismatch。
- linear 域上，`train_exact_plus_oof` 优于纯 `train_exact`，说明适量暴露 predicted-state noise 可能有帮助，但纯 `predicted` 或纯 `OOF` 训练仍明显更差。
- 跨域合起来看，训练模式确实重要，但仅靠切换 train-mode 还不足以让 predicted-state factorization 稳定追平 tabular `direct_policy`。

### Entry: Robust value-head sweep (`huber` vs `noise_weighted_ridge`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New option:
  - `--value-head-model {ridge,huber,noise_weighted_ridge}`
- Comparison artifact:
  - `outputs/week2_robust_value_head_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v8_huber \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model huber

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v8_noise_weighted \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model noise_weighted_ridge

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v7_huber \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model huber

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v7_noise_weighted \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model noise_weighted_ridge
```

Arithmetic:
- ridge best predicted-state mode:
  - `train_exact`: regret = `0.4616`
- huber:
  - `train_exact`: regret = `0.5096`
  - `train_predicted`: regret = `0.5569`
- noise-weighted ridge:
  - `train_exact`: regret = `0.4616`
  - `train_exact_plus_oof`: regret = `0.5158`
  - `train_predicted_oof`: regret = `0.6651`

Linear-equations:
- ridge best predicted-state mode:
  - `train_exact_plus_oof`: regret = `0.2598`
- huber:
  - `train_exact`: regret = `0.2720`
  - `train_exact_plus_oof`: regret = `0.3078`
- noise-weighted ridge:
  - `train_exact_plus_oof`: regret = `0.3078`
  - `train_predicted_oof`: regret = `0.3569`

Interpretation:
- `huber` 在线性域上对 `train_exact` 有帮助（`0.3044 -> 0.2720`），说明 utility regression 确实存在一部分残差/outlier 敏感性。
- 但 `huber` 在 arithmetic 域和 exact-state 上都明显更差，说明“label outlier”不是主导问题，至少不是跨域主解。
- `noise_weighted_ridge` 在 arithmetic 域能小幅拉回最差的 OOF / exact+OOF 设定，说明 exact-vs-pred discrepancy 做 sample weighting 方向是有信号的。
- 但它没有改变任何域上的最优 predicted-state 排序，也没有把 predicted-state factorization 拉回到 tabular `direct_policy` 之上。
- 最合理的结论是：简单 robust regression 只能局部修正，下一步要么改 value-head 结构，要么改 action-value target/interface。

### Entry: Structured value-head sweep (`pairwise_logit`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New option:
  - `--value-head-model pairwise_logit`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v9_pairwise \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_logit

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v8_pairwise \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_logit
```

Arithmetic:
- `factorized_exact_state`: regret = `0.1847`
- `factorized_predicted_state_train_exact`: regret = `0.4759`
- `factorized_predicted_state_train_predicted`: regret = `0.5225`
- `factorized_predicted_state_train_exact_plus_oof`: regret = `0.5804`

Linear-equations:
- `factorized_exact_state`: regret = `0.1297`
- `factorized_predicted_state_train_exact`: regret = `0.3478`
- `factorized_predicted_state_train_predicted`: regret = `0.3514`
- `factorized_predicted_state_train_exact_plus_oof`: regret = `0.3484`

Interpretation:
- pairwise head 在两个域上都改善了 exact-state，说明“每个动作独立回归 point utility”确实不是最贴合控制目标的 value target。
- 但 pairwise head 没有改善 predicted-state，尤其在线性域上比 `ridge + train_exact_plus_oof = 0.2598` 明显更差。
- 这把结论进一步收紧了：
  - value target/interface 的确重要
  - 但 deployable predicted-state gap 仍主要受 state-noise 主导
- 因此下一步最合理的方向不是继续换一般性的 target，而是把 uncertainty / predicted-state reliability 显式并入 value head。

### Entry: Nonlinear interaction value-head sweep (`interaction_ridge` / `pairwise_interaction_logit`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model interaction_ridge`
  - `--value-head-model pairwise_interaction_logit`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v10_interaction_ridge \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model interaction_ridge

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v10_pairwise_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_interaction_logit

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v9_interaction_ridge \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model interaction_ridge

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v9_pairwise_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_interaction_logit
```

Arithmetic:
- `interaction_ridge`
  - `factorized_predicted_state_train_exact`: regret = `0.4193`
  - `factorized_predicted_state_train_predicted`: regret = `0.4602`
- `pairwise_interaction_logit`
  - `factorized_predicted_state_train_exact`: regret = `0.3727`
  - `factorized_predicted_state_train_predicted`: regret = `0.5064`

Linear-equations:
- `interaction_ridge`
  - `factorized_exact_state`: regret = `0.0689`
  - `factorized_predicted_state_train_exact`: regret = `0.3557`
- `pairwise_interaction_logit`
  - `factorized_exact_state`: regret = `0.1185`
  - `factorized_predicted_state_train_exact`: regret = `0.3917`

Interpretation:
- 二阶交互显式进入 value head 后，确实暴露出更多结构信号：
  - arithmetic 域 predicted-state 首次明显变好，最好到 `0.3727`
  - linear 域 exact-state 大幅变好，`interaction_ridge` 到 `0.0689`
- 但这些提升没有统一迁移到双域 deployable predicted-state：
  - arithmetic 仍输给 `direct_policy = 0.3272`
  - linear 的 predicted-state 仍不如 `ridge + train_exact_plus_oof = 0.2598`
- 最合理的结论是：
  - value-head 的非线性容量和 feature interaction 确实重要
  - 但 predicted-state 的剩余 gap 仍需要显式 uncertainty/noise-aware 机制，而不是只靠更高阶多项式特征

### Entry: Uncertainty-aware value-head sweep (committee disagreement features)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model uncertainty_interaction_ridge`
  - `--value-head-model uncertainty_pairwise_interaction_logit`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v11_uncertainty_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_interaction_ridge

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v11_uncertainty_pairwise_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_interaction_logit

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v10_uncertainty_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_interaction_ridge

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v10_uncertainty_pairwise_interaction \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_interaction_logit
```

Arithmetic:
- `uncertainty_interaction_ridge`
  - `train_exact`: regret = `0.4342`
  - `train_predicted`: regret = `0.5112`
- `uncertainty_pairwise_interaction_logit`
  - `train_exact`: regret = `0.3840`
  - `train_predicted`: regret = `0.5138`

Linear-equations:
- `uncertainty_interaction_ridge`
  - `train_predicted`: regret = `0.3050`
  - `train_exact`: regret = `0.3122`
- `uncertainty_pairwise_interaction_logit`
  - `train_predicted`: regret = `0.2835`
  - `train_predicted_oof`: regret = `0.3305`

Interpretation:
- committee disagreement 作为 reliability feature 在线性域是有实质价值的：
  - `pairwise_interaction_logit + train_predicted`: `0.4271 -> 0.2835`
  - `interaction_ridge + train_predicted`: `0.3708 -> 0.3050`
- 但 arithmetic 域没有继续变好，反而略差于无 uncertainty 的 best interaction head：
  - `pairwise_interaction_logit + train_exact`: `0.3727`
  - `uncertainty_pairwise_interaction_logit + train_exact`: `0.3840`
- 这说明：
  - 显式 reliability 信号本身是有用的
  - 但把 uncertainty 仅作为附加特征还不够，跨域 deployable gap 仍没有被统一解决
- 下一步更合理的方向是：
  - 做 joint state-value head
  - 或做显式 heteroscedastic / uncertainty-calibrated valuation，而不是继续只堆 feature augmentation

### Entry: Joint state-value gate probe (`joint_pairwise_gate`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New option:
  - `--value-head-model joint_pairwise_gate`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v12_joint_gate \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model joint_pairwise_gate

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v11_joint_gate \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model joint_pairwise_gate
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.2213`
  - accuracy = `0.7521`
- `factorized_predicted_state_joint_gate`
  - regret = `0.5427`
  - accuracy = `0.4376`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1185`
  - accuracy = `0.8611`
- `factorized_predicted_state_joint_gate`
  - regret = `0.2594`
  - accuracy = `0.6611`

Interpretation:
- 这轮 probe 的 exact-state 分支沿用了 pairwise-interaction exact head，所以 exact-state 结果保持在当前已知较强水平；真正被测试的是 deployable 的 joint routing。
- 在线性方程域上，joint gate 只给出非常小的正向增益：
  - 旧 best predicted-state：`ridge + train_exact_plus_oof = 0.2598`
  - 新 `joint_pairwise_gate`：`0.2594`
- 在 arithmetic 域上，joint gate 明显失败：
  - 当前 best predicted-state：`pairwise_interaction_logit + train_exact = 0.3727`
  - `joint_pairwise_gate`：`0.5427`
- 因此这轮结果说明：
  - “把 exact-trained 分支和 uncertainty-aware predicted 分支用简单 gate 混合”不是跨域通用修复
  - gate 的校准目标与路由分布本身也带有强域依赖
  - 如果继续沿 proposal 推进，下一步更值得做的是更强的 joint state-value / heteroscedastic 设计，而不是继续刷简单 mixture-of-experts

### Entry: Per-pair error-calibrated valuation (`pairwise_error_calibrated`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New option:
  - `--value-head-model pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v13_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v12_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.2213`
  - accuracy = `0.7521`
- `factorized_predicted_state_pairwise_error_calibrated`
  - regret = `0.3379`
  - accuracy = `0.5927`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1185`
  - accuracy = `0.8611`
- `factorized_predicted_state_pairwise_error_calibrated`
  - regret = `0.3861`
  - accuracy = `0.5000`

Interpretation:
- 这版 head 的设计不是整行 gating，而是：
  - 先用 exact-state `pairwise_interaction_logit` 学 base pairwise preference
  - 再用 OOF predicted-state prefixes 上的 pairwise probability error 训练误差头
  - 在部署时按 predicted-state risk 对每个动作对的 margin 做 shrinkage
- arithmetic 域上，这是目前最强的一次 factorized predicted-state 改善：
  - 旧 best：`pairwise_interaction_logit + train_exact = 0.3727`
  - 新 `pairwise_error_calibrated`：`0.3379`
  - 它也显著优于 simple gate：`0.5427`
  - 与 tabular `direct_policy = 0.3272` 的差距缩到 `0.0107`
- linear 域上，它明显过度收缩了已有的有用 margin：
  - 旧 best：`joint_pairwise_gate = 0.2594`，`ridge + train_exact_plus_oof = 0.2598`
  - 新 `pairwise_error_calibrated`：`0.3861`
- 因此这轮结果说明：
  - predicted-state noise 的确可以通过 pairwise-level calibration 被部分吸收
  - 但是否需要 shrinkage、需要多强 shrinkage，本身就是域依赖问题
  - 如果继续沿 proposal 推进，下一步更合理的是“条件化 shrinkage 强度”的 joint state-value / heteroscedastic 设计，而不是继续使用单一全局校准规则

### Entry: Conditional pairwise calibration wrappers (`pairwise_meta_calibrated` / `pairwise_selective_calibrated`)

- Status: NEGATIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model pairwise_meta_calibrated`
  - `--value-head-model pairwise_selective_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v14_pairwise_meta_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_meta_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v13_pairwise_meta_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_meta_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v15_pairwise_selective_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_selective_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v14_pairwise_selective_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model pairwise_selective_calibrated
```

`pairwise_meta_calibrated`:
- Arithmetic:
  - predicted-state regret = `0.5640`
  - accuracy = `0.3809`
- Linear-equations:
  - predicted-state regret = `0.3261`
  - accuracy = `0.5667`

`pairwise_selective_calibrated`:
- Arithmetic:
  - predicted-state regret = `0.3840`
  - accuracy = `0.5576`
- Linear-equations:
  - predicted-state regret = `0.3392`
  - accuracy = `0.5889`

Interpretation:
- 这两版都试图把“校准强度条件化”做得更细：
  - `pairwise_meta_calibrated` 直接让 meta-classifier 结合 `base_prob + predicted-state features + uncertainty` 预测 pairwise winner
  - `pairwise_selective_calibrated` 只在 gate 认为 calibrated margin 优于 base margin 时启用 shrinkage
- 但结果没有形成跨域支配：
  - `pairwise_meta_calibrated` 比固定 shrinkage 更能保住 linear（`0.3861 -> 0.3261`），却把 arithmetic 明显压坏到 `0.5640`
  - `pairwise_selective_calibrated` 比 direct meta 稳一些，但 arithmetic `0.3840`、linear `0.3392` 都不如各自当前 best
- 因此这轮结果的意义是：
  - post-hoc wrapper 式 conditional calibration 已经被较充分地探索过
  - 它们能带来局部修正，但没有给出跨域统一最优的 deployable factorized controller
  - proposal 的下一步不该继续围绕 base pairwise head 外挂更多 calibration wrapper，而应转向更原生的 joint state-value / heteroscedastic 参数化

### Entry: Native heteroscedastic value head (`uncertainty_heteroscedastic_interaction`)

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model heteroscedastic_interaction`
  - `--value-head-model uncertainty_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v16_uncertainty_heteroscedastic \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v15_uncertainty_heteroscedastic \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1820`
  - accuracy = `0.7791`
- predicted-state best:
  - `train_exact`: regret = `0.3824`
  - accuracy = `0.5576`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.0860`
  - accuracy = `0.8806`
- predicted-state best:
  - `train_predicted`: regret = `0.2786`
  - accuracy = `0.6306`

Interpretation:
- 这版不是 post-hoc calibration wrapper，而是直接让 uncertainty 进入底层 value 参数化：
  - 每个动作各自拟合 utility mean
  - 同时拟合 log-variance
  - 决策时用 variance-adjusted pairwise win-prob 组合动作分数
- 结果说明：
  - 在线性域上，native heteroscedastic head 是当前最强的“非-wrapper” predicted-state 结果：`0.2786`
  - 它优于 wrapper 变体 `pairwise_meta_calibrated = 0.3261`、`pairwise_selective_calibrated = 0.3392`、`pairwise_error_calibrated = 0.3861`
  - 但它仍不如当前 overall best `joint_pairwise_gate = 0.2594`
- arithmetic 域上，它没有超过当前 best deployable factorized：
  - `pairwise_error_calibrated = 0.3379`
  - `uncertainty_heteroscedastic_interaction` best predicted-state = `0.3824`
  - 不过它把 exact-state factorized 提升到 `0.1820`，明显优于很多旧的 factorized exact-state 版本
- 因此这轮结果说明：
  - 更原生的 joint state-value / heteroscedastic 参数化比 wrapper 更接近 proposal 的方向
  - 它在 linear 域上确实更有效
  - 但 arithmetic 域仍需要更强的 action-conditional heteroscedastic / covariance-aware 建模，当前“独立动作方差”版本还不够

### Entry: Native pairwise-difference heteroscedastic head (`uncertainty_pairwise_heteroscedastic_interaction`)

- Status: NEGATIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model pairwise_heteroscedastic_interaction`
  - `--value-head-model uncertainty_pairwise_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v17_uncertainty_pairwise_heteroscedastic \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v16_uncertainty_pairwise_heteroscedastic \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_pairwise_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.2553`
  - accuracy = `0.6806`
- predicted-state best:
  - `train_exact`: regret = `0.4058`
  - accuracy = `0.5376`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1285`
  - accuracy = `0.7944`
- predicted-state best:
  - `train_predicted`: regret = `0.2980`
  - accuracy = `0.6111`

Interpretation:
- 这版 head 直接对每个动作对的 utility difference 拟合 mean / log-variance：
  - 不再先做独立动作均值与方差，再组合 pairwise win-prob
  - 而是把 uncertainty 原生写进动作对差值
- 结果并没有支持“更多 pairwise 自由度”就是当前主解：
  - linear 域上，它优于 wrapper 家族，但仍差于独立动作方差版 `uncertainty_heteroscedastic_interaction = 0.2786`
  - arithmetic 域上，它同时输给独立动作方差版 `0.3824` 和当前 best `pairwise_error_calibrated = 0.3379`
  - exact-state 也没有比独立动作方差版更强
- 因此这轮结果说明：
  - 当前 native uncertainty 路线的问题不只是“是否建模动作间耦合”
  - 在当前样本规模下，完全独立的 pairwise-difference mean/variance 头会引入明显的样本效率损失
  - proposal 的下一步更像需要“有共享结构的 covariance-aware / low-rank heteroscedastic 参数化”，而不是直接把每个动作对都拆开单独建模

### Entry: Shared-structure covariance-aware head (`uncertainty_shared_covariance_heteroscedastic_interaction`)

- Status: NEGATIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model shared_covariance_heteroscedastic_interaction`
  - `--value-head-model uncertainty_shared_covariance_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v18_uncertainty_shared_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_shared_covariance_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v17_uncertainty_shared_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_shared_covariance_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.2038`
  - accuracy = `0.7591`
- predicted-state best:
  - `train_exact`: regret = `0.3824`
  - accuracy = `0.5576`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.0860`
  - accuracy = `0.8806`
- predicted-state best:
  - `train_predicted`: regret = `0.2786`
  - accuracy = `0.6306`

Interpretation:
- 这版 head 在独立动作均值之外，引入了：
  - 一个共享 covariance template
  - 一个样本级 scale
  - 用它们来近似动作差值的不确定性
- 结果没有支持“简单共享协方差模板”就是当前缺口：
  - linear 域上，它几乎与独立动作方差版 `uncertainty_heteroscedastic_interaction` 完全打平
  - arithmetic 域上，predicted-state 没有超过独立动作方差版，exact-state 还略差
- 因此这轮结果说明：
  - “共享结构”方向本身是合理的，但当前单模板 + 单scale 的结构太弱
  - proposal 的下一步更像需要 low-rank/shared-latent 的更丰富共享结构，而不是简单的 covariance template 缩放

### Entry: Low-rank/shared-latent heteroscedastic head (`uncertainty_lowrank_heteroscedastic_interaction`)

- Status: POSITIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model lowrank_heteroscedastic_interaction`
  - `--value-head-model uncertainty_lowrank_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v19_uncertainty_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_lowrank_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v18_uncertainty_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_lowrank_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1784`
  - accuracy = `0.7791`
- predicted-state best:
  - `train_exact`: regret = `0.3388`
  - accuracy = `0.5976`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.0725`
  - accuracy = `0.9056`
- predicted-state best:
  - `train_predicted`: regret = `0.3108`
  - accuracy = `0.6056`

Interpretation:
- 这版 head 在独立动作 mean/log-variance 之外，再加一个 rank-1 shared latent uncertainty factor：
  - 让动作差值的不确定性不再只依赖独立方差
  - 但仍保留共享结构和样本效率
- arithmetic 域上，它是目前最强的 native shared-structure 结果：
  - 独立动作方差版 best predicted-state：`0.3824`
  - 共享 template 版：`0.3824`
  - 新 low-rank 版：`0.3388`
  - 与当前 overall best deployable factorized `pairwise_error_calibrated = 0.3379` 的差距只剩 `0.0009`
- linear 域上，它没有继续变好：
  - 新 low-rank best predicted-state：`0.3108`
  - 独立动作方差版 / shared-template 版：`0.2786`
  - `joint_pairwise_gate`：`0.2594`
- 因此这轮结果说明：
  - “更强的共享 latent 结构”确实比单模板共享协方差更有价值
  - 它在 harder/noisier 域上能明显改善 native factorized controller
  - 但这种结构仍不是跨域统一最优；下一步更合理的是多因子 / 条件化 shared-latent 参数化，而不是再回到模板缩放或完全 pairwise 头

### Entry: Rank-2 / multi-factor low-rank heteroscedastic head (`uncertainty_rank2_lowrank_heteroscedastic_interaction`)

- Status: POSITIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model rank2_lowrank_heteroscedastic_interaction`
  - `--value-head-model uncertainty_rank2_lowrank_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v20_uncertainty_rank2_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_rank2_lowrank_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v19_uncertainty_rank2_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_rank2_lowrank_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1800`
  - accuracy = `0.7591`
- predicted-state best:
  - `train_exact`: regret = `0.3606`
  - accuracy = `0.5776`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.0356`
  - accuracy = `0.9528`
- predicted-state best:
  - `train_predicted`: regret = `0.3125`
  - accuracy = `0.5806`

Interpretation:
- 这版 head 把 rank-1 shared latent 扩成 rank-2 / multi-factor：
  - 允许 shared uncertainty 结构捕捉不止一个主方向
  - 但仍保留 low-rank/shared-latent 的样本效率
- arithmetic 域上，它没有延续 rank-1 low-rank 的 deployable 优势：
  - rank-1 best predicted-state：`0.3388`
  - rank-2 best predicted-state：`0.3606`
  - `pairwise_error_calibrated`：`0.3379`
  - exact-state 也仅为 `0.1800`，略差于 rank-1 的 `0.1784`
- linear 域上，它把 exact-state 推到当前全局最佳：
  - rank-1 exact-state：`0.0725`
  - rank-2 exact-state：`0.0356`
  - 但 predicted-state 仍不如 deployable best：`0.3125` vs `joint_pairwise_gate = 0.2594`
- 因此这轮结果说明：
  - 继续固定地增加 latent rank，主要会买到 oracle exact-state 容量
  - 它不会自动缩小 predicted-state deployable gap
  - 下一步更合理的是 conditional / input-dependent latent activation，而不是继续无条件加 rank

### Entry: Conditional / input-dependent low-rank heteroscedastic head (`uncertainty_conditional_lowrank_heteroscedastic_interaction`)

- Status: POSITIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_heteroscedastic_interaction`
  - `--value-head-model uncertainty_conditional_lowrank_heteroscedastic_interaction`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v21_uncertainty_conditional_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_conditional_lowrank_heteroscedastic_interaction

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v20_uncertainty_conditional_lowrank_covariance \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model uncertainty_conditional_lowrank_heteroscedastic_interaction
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state best:
  - `train_exact`: regret = `0.3388`
  - accuracy = `0.5976`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state best:
  - `train_predicted`: regret = `0.2617`
  - accuracy = `0.6528`

Interpretation:
- 这版 head 不再固定使用全局 rank-2 latent：
  - 先从 standardized residual 中抽出两套 rank-1 latent template
  - 再用 feature-conditioned gate 决定每个 prefix 更像哪一种相关性结构
- arithmetic 域上，它没有超过 hard-domain 当前 overall best deployable factorized：
  - `pairwise_error_calibrated`：`0.3379`
  - 新 conditional low-rank：`0.3388`
  - 但它把 exact-state 推到新的全局最佳：`0.1553`，优于 `ordered_scalar_mu = 0.1599`
- linear 域上，它给出了目前最强的 native deployable 结果之一：
  - rank-1 low-rank：`0.3108`
  - 独立动作方差版：`0.2786`
  - 新 conditional low-rank：`0.2617`
  - 与当前 best `joint_pairwise_gate = 0.2594` 只差 `0.0023`
- 因此这轮结果说明：
  - input-dependent latent orientation 比继续加固定 latent rank 更有价值
  - 它已经基本解决了 easy-domain 上的 native deployable gap
  - hard-domain 上还缺最后一小步，更合理的方向是把 conditional latent 与有效的 pairwise shrinkage 结合，而不是再做固定-rank sweep

### Entry: Conditional-lowrank + per-pair shrinkage hybrid (`conditional_lowrank_pairwise_error_calibrated`)

- Status: POSITIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v22_conditional_lowrank_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v21_conditional_lowrank_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state:
  - regret = `0.3239`
  - accuracy = `0.6142`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state:
  - regret = `0.4479`
  - accuracy = `0.4917`

Interpretation:
- 这版 head 把 conditional-lowrank base bundle 与 per-pair error shrinkage 直接结合：
  - base margin 由 conditional latent uncertainty 给出
  - shrinkage 强度由 calibration prefixes 上的 per-pair error regressor 预测
- arithmetic 域上，它首次把 deployable factorized 刷到新的最佳：
  - 旧 best：`pairwise_error_calibrated = 0.3379`
  - 新 hybrid：`0.3239`
- linear 域上，它明显失效：
  - conditional lowrank 本体：`0.2617`
  - 新 hybrid：`0.4479`
- 因此这轮结果说明：
  - conditional latent 与 shrinkage 在 hard-domain 上确实互补
  - 但 easy-domain 上仍然需要显式的 no-shrink / capped-shrink 机制，否则会被过度收缩压坏

### Entry: Conditional-lowrank + selective shrinkage hybrid (`conditional_lowrank_selective_pairwise_error_calibrated`)

- Status: NEGATIVE
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_selective_pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v23_conditional_lowrank_selective_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_selective_pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v22_conditional_lowrank_selective_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_selective_pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state:
  - regret = `0.3388`
  - accuracy = `0.5976`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state:
  - regret = `0.4479`
  - accuracy = `0.4917`

Interpretation:
- 这版尝试用 per-pair gate 只在“校准比 base 更好”时启用 shrinkage。
- 结果没有实现预期目标：
  - arithmetic 退回到 conditional lowrank 本体的 `0.3388`
  - linear 仍然停在 `0.4479`
- 这说明 simple selective gate 并没有真正学会“何时不 shrink”；同一类 calibration signal 不足以恢复 easy-domain 表现。

### Entry: Conditional-lowrank + capped shrinkage hybrid (`conditional_lowrank_capped_pairwise_error_calibrated`)

- Status: POSITIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_capped_pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v24_conditional_lowrank_capped_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_capped_pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v23_conditional_lowrank_capped_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_capped_pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state:
  - regret = `0.3239`
  - accuracy = `0.6142`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state:
  - regret = `0.4081`
  - accuracy = `0.5167`

Interpretation:
- 这版在 conditional-lowrank hybrid 外显式加入了两条先验：
  - 高置信 pair 直接 no-op
  - 低置信 pair 的 shrinkage 不能超过一个 retention floor
- arithmetic 域上，它稳定保住了当前 hybrid deployable 最优：
  - `conditional_lowrank_pairwise_error_calibrated = 0.3239`
  - 新 capped 版本：`0.3239`
- linear 域上，它确实缓解了过度收缩，但不够：
  - 非 capped hybrid：`0.4479`
  - 新 capped 版本：`0.4081`
  - conditional-lowrank base：`0.2617`
- 因此这轮结果说明：
  - 显式 cap / bypass 先验是对的，至少能部分缓解 easy-domain 崩坏
  - 但连续型 capped shrink 还不足以恢复到 base controller 水平
  - 下一步更合理的是真正的 no-op / banded regime-aware calibration，而不是继续细调 shrinkage 系数

### Entry: Conditional-lowrank + banded/no-op calibration (`conditional_lowrank_banded_pairwise_error_calibrated`)

- Status: NEGATIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_banded_pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v25_conditional_lowrank_banded_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_banded_pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v24_conditional_lowrank_banded_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_banded_pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state:
  - regret = `0.3239`
  - accuracy = `0.6142`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state:
  - regret = `0.4123`
  - accuracy = `0.4944`

Interpretation:
- 这版把 calibration 明确拆成三段：
  - 高置信：no-op
  - 中置信：capped shrink
  - 低置信：full shrink
- arithmetic 域上，它继续稳定保住了当前 hybrid 的 deployable 最优 `0.3239`
- linear 域上，它没有超过 capped 版本：
  - capped：`0.4081`
  - banded：`0.4123`
  - conditional-lowrank base：`0.2617`
- 因此这轮结果说明：
  - 共享的 banded/no-op calibration 规则仍然不足以恢复 easy-domain
  - 到这一步，`conditional latent + shared shrinkage` 家族的边界已经基本画清
  - 下一步更合理的是 per-env / clustered calibration，而不是继续共享阈值微调

### Entry: Conditional-lowrank + 2-cluster calibration (`conditional_lowrank_clustered_pairwise_error_calibrated`)

- Status: NEGATIVE_MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_factorized.py`
- New options:
  - `--value-head-model conditional_lowrank_clustered_pairwise_error_calibrated`
- Comparison artifact:
  - `outputs/week2_value_head_model_comparison.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_factorized_v26_conditional_lowrank_clustered_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_clustered_pairwise_error_calibrated

PYTHONPATH=. python scripts/run_week2_factorized.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_factorized_v25_conditional_lowrank_clustered_pairwise_error_calibrated \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --value-head-model conditional_lowrank_clustered_pairwise_error_calibrated
```

Arithmetic:
- `factorized_exact_state`
  - regret = `0.1553`
  - accuracy = `0.8173`
- predicted-state:
  - regret = `0.3239`
  - accuracy = `0.6142`

Linear-equations:
- `factorized_exact_state`
  - regret = `0.1071`
  - accuracy = `0.8833`
- predicted-state:
  - regret = `0.4252`
  - accuracy = `0.5167`

Interpretation:
- 这版尝试按 `pairwise meta features` 做 2-cluster 校准：
  - 每个 cluster 独立从 `no-op / full shrink / capped shrink` 中选最优策略
  - 目标是让 easy/hard prefix 不再共享同一套 shrinkage 规则
- arithmetic 域上，它继续稳定保住了当前 hybrid deployable 最优 `0.3239`
- linear 域上，它没有超过 capped/banded 版本：
  - capped：`0.4081`
  - banded：`0.4123`
  - clustered：`0.4252`
  - conditional-lowrank base：`0.2617`
- 因此这轮结果说明：
  - shared calibration 这条主线已经基本见顶
  - 即使引入 2-cluster per-pair 规则，也没有恢复 easy-domain
  - 如果继续推进 controller，下一步更合理的是显式 domain-specific / per-env 路线，而不是继续在 shared calibration 家族里增加复杂度

### Entry: Pooled cross-domain shared vs specialist portfolio, plus env-conditioned shared controller

- Status: MIXED_SIGNAL
- New code:
  - `triver/factorized/week2.py`
  - `scripts/run_week2_cross_domain_portfolio.py`
- New options:
  - `scripts/run_week2_cross_domain_portfolio.py --include-env-feature`
- New output dirs:
  - `outputs/week2_pooled_portfolio_shared_conditional_lowrank/`
  - `outputs/week2_pooled_portfolio_shared_hybrid/`
  - `outputs/week2_pooled_portfolio_env_conditioned_shared_conditional_lowrank/`
  - `outputs/week2_pooled_portfolio_env_conditioned_shared_hybrid/`
- Comparison artifacts:
  - `outputs/week2_pooled_specialist_vs_shared_comparison.csv`
  - `outputs/week2_pooled_specialist_vs_shared_deployable_best.csv`

Repro command:

```bash
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
```

Reference pooled shared baselines without env feature:
- `outputs/week2_pooled_portfolio_shared_conditional_lowrank/`
- `outputs/week2_pooled_portfolio_shared_hybrid/`

Specialist portfolio configuration:
- arithmetic specialist = `conditional_lowrank_pairwise_error_calibrated`
- linear specialist = `joint_pairwise_gate`

Key results:
- Without env feature:
  - pooled shared `uncertainty_conditional_lowrank_heteroscedastic_interaction`
    - best deployable predicted-state regret = `0.4630`
  - pooled shared `conditional_lowrank_pairwise_error_calibrated`
    - deployable predicted-state regret = `0.4531`
  - specialist portfolio predicted-state regret = `0.3563`
- With env feature:
  - pooled shared `uncertainty_conditional_lowrank_heteroscedastic_interaction`
    - exact-state regret = `0.1650`
    - best deployable predicted-state regret = `0.4049`
    - accuracy = `0.5321`
  - pooled shared `conditional_lowrank_pairwise_error_calibrated`
    - exact-state regret = `0.1650`
    - deployable predicted-state regret = `0.4444`
    - accuracy = `0.5011`
  - specialist portfolio predicted-state regret = `0.3563`
    - accuracy = `0.5842`

Interpretation:
- 显式 `env_is_linear` feature 是有用的：
  - pooled shared exact-state 从 `0.1914` 改善到 `0.1650`
  - pooled shared deployable best 从 `0.4630` 改善到 `0.4049`
- 但这还不够追平显式 specialist portfolio：
  - env-conditioned pooled shared best = `0.4049`
  - specialist portfolio predicted-state = `0.3563`
- 这说明 pooled shared controller 的失败不只是“没看到 domain label”：
  - 单一 shared head 即使显式看到 env，也仍明显弱于 per-env 专家组合
  - 更合理的当前结论是：shared controller 可以被 env conditioning 明显改善，但 deployable 最优仍然更像显式 domain-specific / per-env routing，而不是单一共享 controller

### Entry: Pooled learned expert router over domain specialists

- Status: NEGATIVE_SIGNAL
- New code:
  - `scripts/run_week2_cross_domain_router.py`
- New output dirs:
  - `outputs/week2_pooled_learned_router_no_env/`
  - `outputs/week2_pooled_learned_router_with_env/`
- Comparison artifacts:
  - `outputs/week2_pooled_controller_family_summary.csv`
  - `outputs/week2_pooled_controller_family_best.csv`

Repro command:

```bash
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

Portfolio setup:
- arithmetic specialist = `conditional_lowrank_pairwise_error_calibrated`
- linear specialist = `joint_pairwise_gate`
- router family:
  - `learned_specialist_router_predicted_state`: 全局二选一 logistic router
  - `env_override_specialist_router_predicted_state`: 以 hard per-env specialist 为默认，只学习何时 override

Key results:
- hard specialist portfolio:
  - regret = `0.3563`
  - accuracy = `0.5842`
- always-linear specialist:
  - regret = `0.3836`
  - accuracy = `0.5632`
- learned global router:
  - no env feature: regret = `0.3894`
  - with env feature: regret = `0.4024`
- env-override router:
  - no env feature: regret = `0.4534`
  - with env feature: regret = `0.4534`

Interpretation:
- learned router 没有追平 hard per-env specialist，甚至没超过简单的 `always_linear_specialist`
- `env_override` 版本更差，说明“以 env specialist 为默认，再学少量偏离”在当前样本规模下也不稳
- 这轮结果把边界进一步钉死：
  - 当前 cross-domain deployable 最优不是 learned router
  - 而是直接的 hard per-env specialist portfolio
- 如果后续还要继续做 routing，更合理的方向不是再加一个小 router，而是：
  - 改 routing target / supervision
  - 或扩大数据规模
  - 否则当前最稳的主结论就应当是显式 domain-specific controller

### Entry: Oracle expert-selector diagnostics over the fixed two-expert pool

- Status: POSITIVE_DIAGNOSTIC_SIGNAL
- Reused code:
  - `scripts/run_week2_cross_domain_router.py`
- New output dir:
  - `outputs/week2_pooled_learned_router_with_env_oracle_diag/`
- New artifacts:
  - `router_sample_results.csv`
  - `router_diagnostics_summary.csv`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_oracle_diag \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Key results:
- fixed-pool oracle expert selector:
  - regret = `0.2528`
  - accuracy = `0.6995`
- hard specialist portfolio:
  - regret = `0.3563`
  - accuracy = `0.5842`
- learned global router:
  - regret = `0.4024`
  - accuracy = `0.5526`

Diagnostics summary (`router_diagnostics_summary.csv`):
- all samples:
  - `oracle_prefers_linear_rate = 0.2292`
  - `oracle_tie_rate = 0.6354`
  - `hard_matches_oracle_rate = 0.8646`
  - `learned_router_matches_oracle_rate = 0.8333`
  - `hard_to_oracle_utility_gap = 0.1028`
  - `learned_to_oracle_utility_gap = 0.1484`
- arithmetic:
  - `hard_matches_oracle_rate = 0.8302`
  - `hard_to_oracle_utility_gap = 0.1368`
- linear_equations:
  - `hard_matches_oracle_rate = 0.9070`
  - `hard_to_oracle_utility_gap = 0.0609`

Interpretation:
- 这轮结果非常关键，因为它把 routing 问题分成了两层：
  - fixed 两专家池本身仍有明显 headroom：oracle selector `0.2528` 明显优于 hard specialist `0.3563`
  - 但当前 lightweight router 没有学到这部分 headroom
- `oracle_tie_rate = 0.6354` 说明大多数样本上两专家等效；真正的 routing 决策空间是一个相对稀疏但高价值的子集
- hard specialist 已经在 `86.5%` 的样本上与 oracle 一致，所以它不是“很差的 heuristic”；但剩下那部分错误选择仍然足够大，能带来约 `0.10` 的平均 utility gap
- 因此当前最准确的结论不是“routing 没必要”，而是：
  - routing 是有明显价值空间的
  - 但当前 router supervision / feature interface 还远远没有把这部分空间学出来

### Entry: Routing supervision/interface follow-ups on the fixed expert pool

- Status: BOUNDARY_CLARIFIED
- Goal: 在不更换 expert pool 的前提下，测试 routing supervision / interface 是否还能把 learned router 推近 oracle selector。
- Updated code:
  - `scripts/run_week2_cross_domain_router.py`
- New comparison artifacts:
  - `outputs/week2_router_supervision_interface_comparison.csv`
  - `outputs/week2_pooled_controller_family_best.csv`

Repro commands:

```bash
PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_margin_weighted \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_margin_weighted \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_score_interface \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_score_interface \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_gap_regression \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_gap_regression \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

Key results:
- hard specialist portfolio:
  - regret = `0.3563`
  - accuracy = `0.5842`
- oracle expert selector:
  - regret = `0.2528`
  - accuracy = `0.6995`
- margin-weighted classification router:
  - regret = `0.4241`
  - accuracy = `0.5111`
- score-interface logistic router:
  - regret = `0.3866`
  - accuracy = `0.5632`
- utility-gap regression router:
  - regret = `0.3746`
  - accuracy = `0.5737`

Diagnostics / interpretation:
- 直接用 `oracle margin` 做分类 sample-weight 没有帮助；它比原始 learned router 更差，说明“把高价值样本加权”并不足以修复 tie-heavy supervision。
- 把 specialist 内部 `action score / top-2 gap` 暴露给 router 后，learned router 从 `0.3894` 改善到 `0.3866`。这说明 interface 确实有信息量，但单靠看到专家置信度还不够。
- 把 router supervision 从二分类改成直接回归 `linear_utility - arithmetic_utility` 后，deployable regret 进一步降到 `0.3746`，而且 `gap_router_matches_oracle_rate = 0.8542`，已经接近 hard specialist 的 `0.8646`。
- 但即使是当前最强的 learned shared router，也仍然输给 hard specialist `0.3563`，更远输给 oracle selector `0.2528`。
- 当前最准确的结论是：
  - routing label form 和 router interface 都重要
  - 但在这批数据和两专家池上，improved shared learned routing 仍然不足以替代 hard per-env specialist
  - cross-domain 主结果仍应以 hard per-env specialist 为 deployable best，把 learned router 视为“有 headroom 但尚未学成”的负对照

### Entry: Nonlinear router-capacity follow-up on the same score interface

- Status: STRONGER_BUT_STILL_SUBOPTIMAL
- Goal: 测试 learned routing 的剩余差距是否主要来自 router 容量不足。
- Reused code:
  - `scripts/run_week2_cross_domain_router.py`
- New output dirs:
  - `outputs/week2_pooled_learned_router_with_env_rf_capacity/`
  - `outputs/week2_pooled_learned_router_no_env_rf_capacity/`

Repro command:

```bash
PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_rf_capacity \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_rf_capacity \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Key results:
- hard specialist portfolio:
  - regret = `0.3563`
- best shared learned router before this round:
  - `utility_gap_specialist_router_predicted_state = 0.3746`
- `rf_specialist_router_predicted_state`:
  - no env feature: regret = `0.3627`
  - with env feature: regret = `0.3663`
- `rf_utility_gap_specialist_router_predicted_state`:
  - no env feature: regret = `0.3837`
  - with env feature: regret = `0.3772`

Interpretation:
- 这轮是正信号，因为它第一次把 shared learned router 推到非常接近 hard specialist：`0.3627` vs `0.3563`。
- 这说明 learned routing 的剩余差距不只是 label form / interface，router 容量本身也重要。
- 但结果同样很清楚：即使换成更强的非线性 router，deployable best 仍然没有超过 hard per-env specialist。
- `no-env` 版本仍然略优于 `with-env`，说明在已经暴露 specialist `score/gap` 的情况下，显式 `env_is_linear` 并不是主要缺口。
- 更细看域内 gap：
  - RF router 在线性域几乎追平甚至略优于 hard specialist
  - 但 arithmetic 域仍然更差
- 因此当前最准确的结论更新为：
  - learned routing 的确还能通过更强 router 再向前推
  - 但在现有数据规模下，它仍不足以推翻 hard per-env specialist 作为 cross-domain deployable best

### Entry: Larger-data routing follow-up (40-sample oracle refresh per domain)

- Status: SCALE_CHANGES_THE_REGIME
- Goal: 扩大 routing supervision 的有效样本量，检验 learned routing 在更大数据下是否还能继续逼近或超过 hard specialist。
- New datasets:
  - `outputs/week2_arithmetic_8b_data_v3_40s/`
  - `outputs/week2_linear_8b_data_v4_40s/`
- New embeddings:
  - `outputs/week2_arithmetic_8b_data_v3_40s/prefix_hidden_states.npz`
  - `outputs/week2_linear_8b_data_v4_40s/prefix_hidden_states_last_prompt.npz`
- New router outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_40s/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_40s/`
- New comparison artifact:
  - `outputs/week2_router_data_scale_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 40 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_arithmetic_8b_data_v3_40s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_arithmetic_8b_data_v3_40s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_arithmetic_8b_data_v3_40s/prefix_hidden_states.npz

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 40 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v4_40s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v4_40s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v4_40s/prefix_hidden_states_last_prompt.npz \
  --pooling last_generation_prompt

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_40s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_40s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_40s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_40s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_40s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_40s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_40s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_40s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_40s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_40s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Dataset summary:
- arithmetic:
  - `116` prefixes
  - `oracle_determinacy_rate = 0.8793`
  - `crossing_mass_high_determinacy = 0.7843`
- linear_equations:
  - `124` prefixes
  - `oracle_determinacy_rate = 0.8387`
  - `crossing_mass_high_determinacy = 0.6538`

Key routing results:
- no env feature:
  - oracle selector: regret = `0.1651`
  - hard specialist: regret = `0.2608`
  - learned logistic router: regret = `0.2701`
  - RF router: regret = `0.2721`
- with env feature:
  - oracle selector: regret = `0.1562`
  - hard specialist: regret = `0.2639`
  - learned logistic router: regret = `0.2686`
  - RF router: regret = `0.2636`

Interpretation:
- 这轮最重要的新信息是：扩数据的收益比继续扫小 router 更大。所有主要 routing baseline 都显著优于之前的小数据结果。
- `with-env + RF` 首次在同表里几乎追平并极小幅度优于当次 hard specialist：`0.2636` vs `0.2639`。但这个优势非常小，而且 `no-env` 版本并没有复现。
- 因此当前不能把“shared learned routing 已经稳健超过 hard specialist”写成结论；更准确的写法是：
  - 扩数据后，shared learned routing 已经进入与 hard specialist 同一量级
  - 但优势还不稳健，当前最保守的 deployable 结论仍应保留 hard per-env specialist
- 同时，这轮也强烈支持一个新判断：如果还要继续推进 learned routing，优先级应该是数据/监督规模，而不是继续微调小模型结构。

### Entry: Larger-data routing follow-up (60-sample oracle refresh per domain)

- Status: SCALE_FLIPS_THE_RANKING
- Goal: 在 40-sample 已接近打平后，继续扩大 routing supervision，检验 shared learned routing 是否会稳定超过 hard specialist。
- New datasets:
  - `outputs/week2_arithmetic_8b_data_v3_60s/`
  - `outputs/week2_linear_8b_data_v4_60s/`
- New embeddings:
  - `outputs/week2_arithmetic_8b_data_v3_60s/prefix_hidden_states.npz`
  - `outputs/week2_linear_8b_data_v4_60s/prefix_hidden_states_last_prompt.npz`
- New router outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_60s/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_60s/`
- Updated comparison artifacts:
  - `outputs/week2_router_supervision_interface_comparison.csv`
  - `outputs/week2_pooled_controller_family_best.csv`
  - `outputs/week2_router_data_scale_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 60 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_arithmetic_8b_data_v3_60s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_arithmetic_8b_data_v3_60s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_arithmetic_8b_data_v3_60s/prefix_hidden_states.npz

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 60 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v4_60s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v4_60s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v4_60s/prefix_hidden_states_last_prompt.npz \
  --pooling last_generation_prompt

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_60s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_60s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_60s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_60s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_60s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_60s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_60s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_60s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_60s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_60s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Dataset summary:
- arithmetic:
  - `156` prefixes
  - `oracle_determinacy_rate = 0.8718`
  - `crossing_mass_high_determinacy = 0.7868`
- linear_equations:
  - `194` prefixes
  - `oracle_determinacy_rate = 0.8402`
  - `crossing_mass_high_determinacy = 0.6687`

Key routing results:
- no env feature:
  - oracle selector: regret = `0.1190`
  - hard specialist: regret = `0.2111`
  - learned logistic router: regret = `0.2058`
  - best learned router: `rf_utility_gap_specialist_router_predicted_state = 0.2014`
- with env feature:
  - oracle selector: regret = `0.1158`
  - hard specialist: regret = `0.2079`
  - learned logistic router: regret = `0.2055`
  - best learned router: `margin_weighted_specialist_router_predicted_state = 0.1974`

Interpretation:
- 这轮第一次把 cross-domain routing 的主结论翻了过来：在更大 supervision 下，shared learned routing 不再只是“接近” hard specialist，而是在 `no-env` 和 `with-env` 两个设置里都实际超过了它。
- 更重要的是，这个反超不只来自单个花哨变体。普通 learned logistic router 在两种设置里也都已优于 hard specialist，说明数据规模已经把 learned routing 推过了 specialist 门槛。
- 但 `env` feature 仍然不是主决定项：`no-env` 与 `with-env` 都能赢，只是最优 router 变体不同。这进一步支持“数据/监督规模比继续扫小 router 结构更重要”。
- 当前更准确的结论更新为：
  - small/medium data 下，hard per-env specialist 是更保守的 deployable best
  - 到 60-sample 这一档后，shared learned routing 已经成为新的 deployable best
  - 但它与 oracle selector 之间仍有明显 gap（约 `0.082~0.092` regret），所以 routing headroom 远未吃满

### Entry: Larger-data routing follow-up (80-sample oracle refresh per domain)

- Status: STILL_IMPROVING
- Goal: 在 60-sample 已翻转 ranking 后，继续扩大 routing supervision，检验 learned routing 是否继续改善，还是开始接近平台。
- New datasets:
  - `outputs/week2_arithmetic_8b_data_v3_80s/`
  - `outputs/week2_linear_8b_data_v4_80s/`
- New embeddings:
  - `outputs/week2_arithmetic_8b_data_v3_80s/prefix_hidden_states.npz`
  - `outputs/week2_linear_8b_data_v4_80s/prefix_hidden_states_last_prompt.npz`
- New router outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_80s/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_80s/`
- Updated comparison artifacts:
  - `outputs/week2_router_supervision_interface_comparison.csv`
  - `outputs/week2_pooled_controller_family_best.csv`
  - `outputs/week2_router_data_scale_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 80 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_arithmetic_8b_data_v3_80s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_arithmetic_8b_data_v3_80s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_arithmetic_8b_data_v3_80s/prefix_hidden_states.npz

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 80 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v4_80s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v4_80s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v4_80s/prefix_hidden_states_last_prompt.npz \
  --pooling last_generation_prompt

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_80s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_80s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_80s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_80s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_80s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_80s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_80s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_80s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_80s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_80s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Dataset summary:
- arithmetic:
  - `192` prefixes
  - `oracle_determinacy_rate = 0.8646`
  - `crossing_mass_high_determinacy = 0.7952`
- linear_equations:
  - `258` prefixes
  - `oracle_determinacy_rate = 0.8488`
  - `crossing_mass_high_determinacy = 0.6484`

Key routing results:
- no env feature:
  - oracle selector: regret = `0.0998`
  - hard specialist: regret = `0.1921`
  - learned logistic router: regret = `0.2027`
  - best learned router: `rf_specialist_router_predicted_state = 0.1844`
- with env feature:
  - oracle selector: regret = `0.0998`
  - hard specialist: regret = `0.1883`
  - learned logistic router: regret = `0.2080`
  - best learned router: `rf_specialist_router_predicted_state = 0.1829`

Interpretation:
- 这轮不是平台期。best deployable shared router 继续从 60-sample 的 `0.2014 / 0.1974` 改善到 `0.1844 / 0.1829`，说明继续扩大 routing supervision 仍然有明显收益。
- 但 ranking 也发生了新变化：普通 learned logistic 已不再是最优，当前最强 router 变成了 `rf_specialist_router_predicted_state`。这说明一旦数据规模继续扩大，router 容量又重新变得重要。
- `env` feature 这轮只带来很小的额外收益：`0.1844 -> 0.1829`。因此当前更准确的判断是：
  - 数据规模仍然是主导因素
  - 容量决定在更大数据下谁能吃到这部分收益
  - 单独的 `env` label 不是主要瓶颈
- 当前主结论进一步更新为：
  - best shared learned routing 仍在继续改善，没有出现明显平台
  - hard specialist 已经不再是 deployable best
  - 但当前距离 oracle selector 仍有约 `0.083` regret gap，所以下一步应继续追 oracle gap，而不是回到 specialist 对比

### Entry: Larger-data routing follow-up (100-sample oracle refresh per domain)

- Status: MIXED_PLATEAU_SIGNAL
- Goal: 在 80-sample 已明显改善后，继续扩大 routing supervision，检验改进是否还在单调持续，还是开始出现平台/抖动。
- New datasets:
  - `outputs/week2_arithmetic_8b_data_v3_100s/`
  - `outputs/week2_linear_8b_data_v4_100s/`
- New embeddings:
  - `outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz`
  - `outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz`
- New router outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s/`
- Updated comparison artifacts:
  - `outputs/week2_router_supervision_interface_comparison.csv`
  - `outputs/week2_pooled_controller_family_best.csv`
  - `outputs/week2_router_data_scale_comparison.csv`

Repro command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 100 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_arithmetic_8b_data_v3_100s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 100 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --output-dir outputs/week2_linear_8b_data_v4_100s \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --pooling last_generation_prompt

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Dataset summary:
- arithmetic:
  - `240` prefixes
  - `oracle_determinacy_rate = 0.8500`
  - `crossing_mass_high_determinacy = 0.7990`
- linear_equations:
  - `320` prefixes
  - `oracle_determinacy_rate = 0.8688`
  - `crossing_mass_high_determinacy = 0.6367`

Key routing results:
- no env feature:
  - oracle selector: regret = `0.1093`
  - hard specialist: regret = `0.1884`
  - best learned router: `sparse_override_specialist_router_predicted_state = 0.1833`
- with env feature:
  - oracle selector: regret = `0.1078`
  - hard specialist: regret = `0.1921`
  - best learned router: `learned_specialist_router_predicted_state = 0.1926`

Interpretation:
- 这轮没有给出“继续单调明显变好”的证据。`no-env` 最优从 `0.1844` 小幅改到 `0.1833`，但 `with-env` 反而从 `0.1829` 回到 `0.1921~0.1926`。
- 因此更准确的结论不再是“继续扩数据就会明显继续降”，而是：`80 -> 100` 已经出现平台/抖动信号。当前 curve 更像开始围绕 `0.18~0.19` 波动，而不是保持早期那种大幅下降。
- 这轮也说明 best router family 仍不稳定：`80-sample` 时最强是 `rf_specialist_router`，到了 `100-sample no-env` 则变成 `sparse_override`；而 `with-env` 下 shared learned routing 甚至没有稳定超过 hard specialist。
- 当前最准确的更新是：
  - raw scaling 仍可能带来小收益，但边际收益已经显著变小
  - 若继续推进，不应再盲目只加数据点，而应转向更强 router / 更稳定的大数据复验 / 更针对 oracle gap 的 supervision

### Entry: Oracle-like routing supervision + 100-sample repeatability probe

- Status: HIGH_SEED_SENSITIVITY
- Goal: 同时推进两件事：
  - 用更贴近 oracle selector 的 routing supervision 检查是否能带来额外收益
  - 在 `100-sample` 规模上做独立 seed replicate，判断之前的“平台/抖动”是不是单次采样现象
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `direct_utility_specialist_router_predicted_state`
  - 新增 `rf_direct_utility_specialist_router_predicted_state`
- Minimal verify:

```bash
python -m compileall scripts/run_week2_cross_domain_router.py
```

- New outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_v2/`
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed29/`
  - `outputs/week2_linear_8b_data_v4_100s_seed29/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v2/`
  - `outputs/week2_router_repeatability_oracle_supervision_comparison.csv`

Repro command:

```bash
python -m compileall scripts/run_week2_cross_domain_router.py

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v2 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_v2 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 100 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --seed 29 \
  --output-dir outputs/week2_arithmetic_8b_data_v3_100s_seed29 \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_hidden_states.npz

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --num-samples 100 \
  --num-rollouts 4 \
  --total-budget-tokens 64 \
  --top-p 0.8 \
  --lambda-tok 0.01 \
  --gamma-wrong 1.0 \
  --augment-revise-prefixes \
  --seed 29 \
  --output-dir outputs/week2_linear_8b_data_v4_100s_seed29 \
  --skip-plots

PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
  --input-csv outputs/week2_linear_8b_data_v4_100s_seed29/prefix_oracle_records.csv \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --output-npz outputs/week2_linear_8b_data_v4_100s_seed29/prefix_hidden_states_last_prompt.npz \
  --pooling last_generation_prompt

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed29/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed29/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v2 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed29/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed29/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v2 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --include-env-feature
```

Original 100-sample rerun with new supervision:
- no env:
  - oracle selector: regret = `0.1124`
  - hard specialist: regret = `0.1912`
  - best learned router: `hard_specialist_portfolio_predicted_state` is still effectively best on this rerun
  - `direct_utility`: regret = `0.2071`
  - `rf_direct_utility`: regret = `0.1982`
- with env:
  - oracle selector: regret = `0.1107`
  - best learned router: `learned_specialist_router = 0.1909`
  - hard specialist: regret = `0.1917`
  - `direct_utility`: regret = `0.1994`
  - `rf_direct_utility`: regret = `0.2055`

Independent `seed=29` 100-sample replicate:
- dataset sizes:
  - arithmetic: `216` prefixes
  - linear_equations: `340` prefixes
- no env:
  - oracle selector: regret = `0.0941`
  - hard specialist: regret = `0.1952`
  - best learned router: `utility_gap_specialist_router = 0.1592`
  - `direct_utility`: regret = `0.1667`
- with env:
  - oracle selector: regret = `0.0884`
  - hard specialist: regret = `0.1896`
  - best learned router: `utility_gap_specialist_router = 0.1569`
  - `direct_utility`: regret = `0.1635`

Interpretation:
- “更贴近 oracle selector”的 direct-utility supervision 是有价值的，但还不是当前最优。它在 replicate 上明显优于 hard specialist，却仍然输给 `utility_gap` supervision。
- 更大的结论是 repeatability：同样是 `100-sample`，original rerun 大约落在 `0.191` 左右，而 `seed=29` replicate 可以到 `0.1569~0.1592`。这说明之前把 `100-sample` 写成“平台”是过强结论。
- 当前更准确的状态是：
  - `100-sample` 区间存在很强的 seed / data sensitivity
  - single-run frontier claim 不可靠，必须开始按 multi-seed 报告
  - 当前 best observed 100-sample controller 仍然是 `utility_gap` family，而不是 direct-utility family

### Entry: 100-sample multi-seed aggregate (`seed=31/37`) + learned-routing mean/std summary

Goal:
- 把 `100-sample` cross-domain routing 从 single-run / double-run 结论推进到 multi-seed aggregate
- 明确判断：`100-sample` 的 shared learned routing 是稳定优于 hard specialist，还是只是 seed-29 一次性异常值

Artifacts:
- new oracle data:
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed31/`
  - `outputs/week2_linear_8b_data_v4_100s_seed31/`
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed37/`
  - `outputs/week2_linear_8b_data_v4_100s_seed37/`
- new pooled routers:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v2/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v2/`
- multi-seed summaries:
  - `outputs/week2_router_multiseed_100s_per_run.csv`
  - `outputs/week2_router_multiseed_100s_summary.csv`
  - `outputs/week2_router_multiseed_100s_best_by_run.csv`
  - `outputs/week2_router_multiseed_100s_win_counts.csv`
- reusable tooling:
  - `scripts/aggregate_week2_router_multiseed.py`

Commands:
```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in 31 37; do
  CUDA_VISIBLE_DEVICES=0 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env arithmetic \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=1 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env linear_equations \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_linear_8b_data_v4_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=2 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz"

  CUDA_VISIBLE_DEVICES=3 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --pooling last_generation_prompt
done

for seed in 31 37; do
  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet \
    --include-env-feature
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v2/router_summary.csv \
  --summary original_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v2/router_summary.csv \
  --summary seed29_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed29_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed31_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed31_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed37_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v2/router_summary.csv \
  --summary seed37_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v2/router_summary.csv \
  --output-csv outputs/week2_router_multiseed_100s_summary.csv \
  --per-run-csv outputs/week2_router_multiseed_100s_per_run.csv
```

New seed-level oracle data:
- `seed=31`
  - arithmetic: `num_prefixes = 246`, `determinacy = 0.8130`, `crossing_all = 0.8415`, `crossing_high_det = 0.8300`
  - linear: `num_prefixes = 342`, `determinacy = 0.8480`, `crossing_all = 0.5702`, `crossing_high_det = 0.6103`
- `seed=37`
  - arithmetic: `num_prefixes = 230`, `determinacy = 0.8261`, `crossing_all = 0.8870`, `crossing_high_det = 0.8632`
  - linear: `num_prefixes = 346`, `determinacy = 0.8786`, `crossing_all = 0.6532`, `crossing_high_det = 0.6743`

New seed-level router results:
- `seed=31`
  - no env:
    - oracle selector: `0.1267`
    - hard specialist: `0.1965`
    - best learned router: no learned router beats hard specialist; closest is `learned_specialist = 0.2011`
  - with env:
    - oracle selector: `0.1240`
    - hard specialist: `0.1911`
    - best learned router: no learned router beats hard specialist; closest is `rf_specialist = 0.1978`
- `seed=37`
  - no env:
    - oracle selector: `0.1259`
    - hard specialist: `0.2009`
    - best learned router: `rf_direct_utility = 0.1785`
  - with env:
    - oracle selector: `0.1278`
    - hard specialist: `0.1990`
    - best learned router: `rf_utility_gap_fallback = 0.1869`

4-run `100-sample` multi-seed aggregate:
- no env:
  - oracle selector mean regret: `0.1148 +/- 0.0153`
  - best learned mean regret: `rf_specialist_router = 0.1892 +/- 0.0116`
  - hard specialist mean regret: `0.1960 +/- 0.0040`
- with env:
  - oracle selector mean regret: `0.1128 +/- 0.0178`
  - best learned mean regret: `rf_specialist_router = 0.1880 +/- 0.0122`
  - hard specialist mean regret: `0.1929 +/- 0.0042`

Per-run winner instability:
- no env winners across four runs:
  - `hard_specialist`: `2/4`
  - `utility_gap_fallback`: `1/4`
  - `rf_direct_utility`: `1/4`
- with env winners across four runs:
  - `utility_gap_fallback`: `1/4`
  - `rf_utility_gap_fallback`: `1/4`
  - `learned_specialist`: `1/4`
  - `hard_specialist`: `1/4`

Interpretation:
- `100-sample` 确实是 high-variance regime，但 multi-seed mean/std 已经把结论收紧到比 single-run 更稳的版本：
  - shared learned routing 在均值上仍然优于 hard specialist
  - 但优势只有 `~0.005-0.007` regret，远小于 single-run seed-29 给人的印象
- seed-29 现在更像 “强正向 seed”，不是新的默认 frontier；把它单独拿来代表 `100-sample` 会夸大 learned-routing 的当前实力。
- 另一个新边界是 family instability：best learned router family 会随 seed 切换。当前应该报告 “multi-seed mean winner + per-run win counts”，而不是把单个 seed winner 升格成最终架构结论。

### Entry: 100-sample multi-seed aggregate extension (`seed=41/43`) -> 6-run summary

Goal:
- 把上一轮的 `4-run` aggregate 扩到 `6-run`
- 判断 `rf_specialist` 的均值优势是否会随着更多 seeds 保持，还是被额外 seeds 冲掉

Artifacts:
- new oracle data:
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed41/`
  - `outputs/week2_linear_8b_data_v4_100s_seed41/`
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed43/`
  - `outputs/week2_linear_8b_data_v4_100s_seed43/`
- new pooled routers:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v2/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v2/`
- updated multi-seed summaries (supersedes prior 4-run aggregate):
  - `outputs/week2_router_multiseed_100s_per_run.csv`
  - `outputs/week2_router_multiseed_100s_summary.csv`
  - `outputs/week2_router_multiseed_100s_best_by_run.csv`
  - `outputs/week2_router_multiseed_100s_win_counts.csv`

Commands:
```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in 41 43; do
  CUDA_VISIBLE_DEVICES=0 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env arithmetic \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=1 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env linear_equations \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_linear_8b_data_v4_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=2 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz"

  CUDA_VISIBLE_DEVICES=3 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --pooling last_generation_prompt

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet \
    --include-env-feature
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v2/router_summary.csv \
  --summary original_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v2/router_summary.csv \
  --summary seed29_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed29_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed31_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed31_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed37_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v2/router_summary.csv \
  --summary seed37_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v2/router_summary.csv \
  --summary seed41_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v2/router_summary.csv \
  --summary seed41_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v2/router_summary.csv \
  --summary seed43_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v2/router_summary.csv \
  --summary seed43_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v2/router_summary.csv \
  --output-csv outputs/week2_router_multiseed_100s_summary.csv \
  --per-run-csv outputs/week2_router_multiseed_100s_per_run.csv
```

New seed-level oracle data:
- `seed=41`
  - arithmetic: `num_prefixes = 238`, `determinacy = 0.8445`, `crossing_all = 0.8151`, `crossing_high_det = 0.7910`
  - linear: `num_prefixes = 328`, `determinacy = 0.8750`, `crossing_all = 0.5640`, `crossing_high_det = 0.5889`
- `seed=43`
  - arithmetic: `num_prefixes = 244`, `determinacy = 0.8730`, `crossing_all = 0.8525`, `crossing_high_det = 0.8310`
  - linear: `num_prefixes = 340`, `determinacy = 0.9029`, `crossing_all = 0.5912`, `crossing_high_det = 0.5993`

New router highlights:
- `seed=41`
  - no env:
    - oracle selector: `0.0636`
    - hard specialist: `0.2096`
    - best learned router: `rf_direct_utility = 0.1731`
  - with env:
    - oracle selector: `0.0667`
    - hard specialist: `0.2129`
    - best learned router: `rf_direct_utility = 0.1784`
- `seed=43`
  - no env:
    - oracle selector: `0.0440`
    - hard specialist: worse than learned frontier
    - best learned router: `rf_specialist = 0.1833`
  - with env:
    - oracle selector: `0.0459`
    - hard specialist: worse than learned frontier
    - best learned router: `rf_specialist = 0.1860`

Updated 6-run `100-sample` aggregate:
- no env:
  - oracle selector mean regret: `0.0945 +/- 0.0342`
  - best learned mean regret: `rf_specialist = 0.1866 +/- 0.0100`
  - hard specialist mean regret: `0.1993 +/- 0.0064`
- with env:
  - oracle selector mean regret: `0.0939 +/- 0.0329`
  - best learned mean regret: `rf_specialist = 0.1867 +/- 0.0098`
  - hard specialist mean regret: `0.1982 +/- 0.0092`

Updated winner counts:
- no env:
  - `rf_direct_utility`: `2/6`
  - `hard_specialist`: `2/6`
  - `utility_gap_fallback`: `1/6`
  - `rf_specialist`: `1/6`
- with env:
  - `rf_direct_utility`: `1/6`
  - `rf_specialist`: `1/6`
  - `rf_utility_gap_fallback`: `1/6`
  - `utility_gap_fallback`: `1/6`
  - `learned_specialist`: `1/6`
  - `hard_specialist`: `1/6`

Interpretation:
- 这轮新增的 `seed41/43` 不是在冲淡 learned-routing 的均值优势，反而把它变得更稳了：`rf_specialist` 现在在 `no-env / with-env` 都成为 6-run mean winner。
- 同时，winner instability 仍在。per-seed winner 依然会在 `rf_direct_utility / rf_specialist / utility_gap_fallback / hard_specialist` 之间切换，说明当前最稳的主结论仍应是 “mean/std ranking”，而不是某个单 seed 的最优 family。
- 新 seeds 还把 oracle 均值继续压低到 `~0.094`，说明 expert-pool routing 的 headroom 其实比之前想的更大；当前 learned-routing 虽然已经稳定超过 hard specialist，但距离 oracle 仍有 `~0.092` 的平均 regret gap。

### Entry: 100-sample multi-seed aggregate extension (`seed=47/53`) -> 8-run summary

Goal:
- 继续扩 `100-sample` multi-seed aggregate，检验 `rf_specialist` 的 mean win 在更多 seeds 下是否继续成立
- 判断新增强正向 seed 会不会把 mean winner 继续稳定化，还是重新打散

Artifacts:
- new oracle data:
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed47/`
  - `outputs/week2_linear_8b_data_v4_100s_seed47/`
  - `outputs/week2_arithmetic_8b_data_v3_100s_seed53/`
  - `outputs/week2_linear_8b_data_v4_100s_seed53/`
- new pooled routers:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed47_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed47_v2/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v2/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v2/`
- updated multi-seed summaries (supersedes prior 6-run aggregate):
  - `outputs/week2_router_multiseed_100s_per_run.csv`
  - `outputs/week2_router_multiseed_100s_summary.csv`
  - `outputs/week2_router_multiseed_100s_best_by_run.csv`
  - `outputs/week2_router_multiseed_100s_win_counts.csv`

Commands:
```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in 47 53; do
  CUDA_VISIBLE_DEVICES=0 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env arithmetic \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=1 PYTHONPATH=. python scripts/run_week1_oracle.py \
    --env linear_equations \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --num-samples 100 \
    --num-rollouts 4 \
    --total-budget-tokens 64 \
    --top-p 0.8 \
    --lambda-tok 0.01 \
    --gamma-wrong 1.0 \
    --augment-revise-prefixes \
    --seed "${seed}" \
    --output-dir "outputs/week2_linear_8b_data_v4_100s_seed${seed}" \
    --skip-plots

  CUDA_VISIBLE_DEVICES=2 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz"

  CUDA_VISIBLE_DEVICES=3 PYTHONPATH=. python scripts/extract_prefix_hidden_states.py \
    --input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --model-path /cephfs/shared/hf_cache/hub/Qwen3-8B \
    --output-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --pooling last_generation_prompt

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed${seed}_v2" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet \
    --include-env-feature
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v2/router_summary.csv \
  --summary original_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v2/router_summary.csv \
  --summary seed29_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed29_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v2/router_summary.csv \
  --summary seed31_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed31_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v2/router_summary.csv \
  --summary seed37_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v2/router_summary.csv \
  --summary seed37_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v2/router_summary.csv \
  --summary seed41_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v2/router_summary.csv \
  --summary seed41_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v2/router_summary.csv \
  --summary seed43_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v2/router_summary.csv \
  --summary seed43_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v2/router_summary.csv \
  --summary seed47_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed47_v2/router_summary.csv \
  --summary seed47_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed47_v2/router_summary.csv \
  --summary seed53_no_env=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v2/router_summary.csv \
  --summary seed53_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v2/router_summary.csv \
  --output-csv outputs/week2_router_multiseed_100s_summary.csv \
  --per-run-csv outputs/week2_router_multiseed_100s_per_run.csv
```

New seed-level oracle data:
- `seed=47`
  - arithmetic: `num_prefixes = 262`, `determinacy = 0.7824`, `crossing_all = 0.8931`, `crossing_high_det = 0.8829`
  - linear: `num_prefixes = 342`, `determinacy = 0.8363`, `crossing_all = 0.6550`, `crossing_high_det = 0.6748`
- `seed=53`
  - arithmetic: `num_prefixes = 248`, `determinacy = 0.8387`, `crossing_all = 0.8790`, `crossing_high_det = 0.8606`
  - linear: `num_prefixes = 348`, `determinacy = 0.8793`, `crossing_all = 0.5805`, `crossing_high_det = 0.6111`

New router highlights:
- `seed=47`
  - no env:
    - oracle selector: `0.1460`
    - hard specialist: `0.2266`
    - best learned router: `rf_specialist = 0.2034`
  - with env:
    - oracle selector: `0.1505`
    - hard specialist: `0.2192`
    - best learned router: `rf_specialist = 0.2016`
- `seed=53`
  - no env:
    - oracle selector: `0.0949`
    - hard specialist: `0.1733`
    - best learned router: `sparse_override = 0.1661`
  - with env:
    - oracle selector: `0.0931`
    - hard specialist: worse than learned frontier
    - best learned router: `rf_direct_utility = 0.1626`

Updated 8-run `100-sample` aggregate:
- no env:
  - oracle selector mean regret: `0.1010 +/- 0.0342`
  - best learned mean regret: `rf_specialist = 0.1872 +/- 0.0115`
  - hard specialist mean regret: `0.1995 +/- 0.0152`
- with env:
  - oracle selector mean regret: `0.1009 +/- 0.0343`
  - best learned mean regret: `rf_specialist = 0.1857 +/- 0.0133`
  - hard specialist mean regret: `0.1970 +/- 0.0158`

Updated mean gaps vs hard specialist:
- no env: `+0.0123` regret in favor of `rf_specialist`
- with env: `+0.0114` regret in favor of `rf_specialist`

Updated winner counts:
- no env:
  - `rf_direct_utility`: `2/8`
  - `rf_specialist`: `2/8`
  - `hard_specialist`: `2/8`
  - `utility_gap_fallback`: `1/8`
  - `sparse_override`: `1/8`
- with env:
  - `rf_direct_utility`: `2/8`
  - `rf_specialist`: `2/8`
  - `utility_gap_fallback`: `1/8`
  - `rf_utility_gap_fallback`: `1/8`
  - `learned_specialist`: `1/8`
  - `hard_specialist`: `1/8`

Interpretation:
- 继续补 seed 之后，`rf_specialist` 的 mean win 没有被冲掉，反而进一步稳住了：它现在仍然是 `no-env / with-env` 两边的 8-run mean winner。
- 但 per-seed winner 仍然没有收敛到单一 family，尤其 `seed53` 再次把 no-env 的 winner 切到了 `sparse_override`。这说明主表仍然应该报告 `mean/std + win counts`，不能把某个 per-seed winner 升格成最终架构。
- 当前 `100-sample` 结论已经比 4-run/6-run 更稳：learned routing 的均值优势真实存在，而且量级基本稳定在 `~0.011-0.012` regret；但距离 oracle selector 仍有 `~0.085-0.086` 的平均 gap。

### Entry: `rf_specialist` family pilot (`rf_high_capacity` vs `rf_specialist_fallback`)

- Status: FAMILY_PILOT
- Goal: 在不改 fixed expert-pool、不中断 `100-sample` 评估口径的前提下，只沿 `rf_specialist` family 做一次同族增强，判断是否值得把 plain `rf_specialist` 升级成更强 RF 版本。
- Key code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `_fit_rf_router_high_capacity`
  - 新增 `rf_high_capacity_specialist_router_predicted_state`
  - 新增 `rf_specialist_fallback_router_predicted_state`
- Output dirs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v3_rf_family/`
- Aggregate artifacts:
  - `outputs/week2_rf_family_pilot_summary.csv`
  - `outputs/week2_rf_family_pilot_per_run.csv`
  - `outputs/week2_rf_family_pilot_deployable_best_by_run.csv`
  - `outputs/week2_rf_family_pilot_deployable_win_counts.csv`
- Repro commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in 29 41 43 53; do
  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v3_rf_family" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv" \
    --arithmetic-embedding-npz "outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz" \
    --linear-input-csv "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv" \
    --linear-embedding-npz "outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz" \
    --output-dir "outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed${seed}_v3_rf_family" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet \
    --include-env-feature
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary seed29_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v3_rf_family/router_summary.csv \
  --summary seed29_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v3_rf_family/router_summary.csv \
  --summary seed41_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v3_rf_family/router_summary.csv \
  --summary seed41_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v3_rf_family/router_summary.csv \
  --summary seed43_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v3_rf_family/router_summary.csv \
  --summary seed43_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v3_rf_family/router_summary.csv \
  --summary seed53_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v3_rf_family/router_summary.csv \
  --summary seed53_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v3_rf_family/router_summary.csv \
  --output-csv outputs/week2_rf_family_pilot_summary.csv \
  --per-run-csv outputs/week2_rf_family_pilot_per_run.csv
```

- Verification:
  - `PYTHONPATH=. python -m compileall scripts/run_week2_cross_domain_router.py`
- Pilot aggregate:
  - no env:
    - oracle selector: `0.0736 +/- 0.0242`
    - `rf_high_capacity`: `0.1722 +/- 0.0105`
    - plain `rf_specialist`: `0.1753 +/- 0.0078`
    - `rf_specialist_fallback`: `0.1753 +/- 0.0078`
    - hard specialist: `0.1915 +/- 0.0182`
  - with env:
    - oracle selector: `0.0722 +/- 0.0249`
    - `learned_specialist`: `0.1762 +/- 0.0100`
    - `rf_high_capacity`: `0.1771 +/- 0.0075`
    - plain `rf_specialist`: `0.1771 +/- 0.0060`
    - `rf_specialist_fallback`: `0.1771 +/- 0.0060`
    - hard specialist: `0.1933 +/- 0.0178`
- Per-run highlights:
  - `seed41_noenv`: `rf_high_capacity` 成为 overall winner，regret `0.1672`
  - `seed29_noenv`: `rf_high_capacity` 明显优于 plain `rf_specialist`（`0.1733` vs `0.1783`），但仍输给 `rf_utility_gap_fallback = 0.1690`
  - `seed29_env`: `rf_high_capacity` 优于 plain `rf_specialist`（`0.1726` vs `0.1763`），但仍输给 `direct_utility = 0.1567`
  - `seed43_noenv` / `seed43_env`: `rf_specialist_fallback` 的“胜出”只是与 plain `rf_specialist` 完全同分后的字母序结果，没有真实增益
  - `seed53_noenv`: `rf_high_capacity` 再次成为 overall winner，regret `0.1621`
- Interpretation:
  - `rf_specialist_fallback` 基本可以退役：它在 4 个 seed 上没有一次产生独立 regret 改善，所有“胜出”都来自与 plain `rf_specialist` 同分的 tie。
  - `rf_high_capacity` 是唯一还活着的同族升级方向：在 no-env 的 family aggregate 上，它把 regret 从 `0.1753` 压到 `0.1722`，并在 `seed41_noenv`、`seed53_noenv` 上成为 overall winner。
  - 但 `rf_high_capacity` 还不是新的统一主线：with-env aggregate 上它基本只和 plain `rf_specialist` 打平，而且仍略弱于 `learned_specialist = 0.1762`。
  - 当前最合理的收敛是：plain `rf_specialist` 继续保留为 multi-seed 主表默认 family；如果要继续做同族升级，只值得把 `rf_high_capacity` 扩到完整 multi-seed，`rf_specialist_fallback` 不值得再扫。

### Entry: Full multi-seed `rf_specialist` family extension

- Status: FAMILY_PROMOTE
- Goal: 把 `rf_high_capacity` 从 4-seed pilot 扩到完整 `100-sample` multi-seed，判断它是否应正式取代 plain `rf_specialist` 成为默认 learned-router family。
- New output dirs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed47_v3_rf_family/`
  - `outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed47_v3_rf_family/`
- Full aggregate artifacts:
  - `outputs/week2_rf_family_multiseed_100s_summary.csv`
  - `outputs/week2_rf_family_multiseed_100s_per_run.csv`
  - `outputs/week2_rf_family_multiseed_100s_deployable_best_by_run.csv`
  - `outputs/week2_rf_family_multiseed_100s_deployable_win_counts.csv`
- Repro commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in original 31 37 47; do
  if [ "${seed}" = "original" ]; then
    ARITH_CSV="outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv"
    ARITH_NPZ="outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz"
    LINEAR_CSV="outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv"
    LINEAR_NPZ="outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz"
    OUT_NOENV="outputs/week2_pooled_learned_router_no_env_bigdata_100s_v3_rf_family"
    OUT_ENV="outputs/week2_pooled_learned_router_with_env_bigdata_100s_v3_rf_family"
  else
    ARITH_CSV="outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv"
    ARITH_NPZ="outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz"
    LINEAR_CSV="outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv"
    LINEAR_NPZ="outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz"
    OUT_NOENV="outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v3_rf_family"
    OUT_ENV="outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed${seed}_v3_rf_family"
  fi

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "${ARITH_CSV}" \
    --arithmetic-embedding-npz "${ARITH_NPZ}" \
    --linear-input-csv "${LINEAR_CSV}" \
    --linear-embedding-npz "${LINEAR_NPZ}" \
    --output-dir "${OUT_NOENV}" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "${ARITH_CSV}" \
    --arithmetic-embedding-npz "${ARITH_NPZ}" \
    --linear-input-csv "${LINEAR_CSV}" \
    --linear-embedding-npz "${LINEAR_NPZ}" \
    --output-dir "${OUT_ENV}" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet \
    --include-env-feature
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v3_rf_family/router_summary.csv \
  --summary original_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v3_rf_family/router_summary.csv \
  --summary seed29_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v3_rf_family/router_summary.csv \
  --summary seed29_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v3_rf_family/router_summary.csv \
  --summary seed31_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v3_rf_family/router_summary.csv \
  --summary seed31_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v3_rf_family/router_summary.csv \
  --summary seed37_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v3_rf_family/router_summary.csv \
  --summary seed37_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v3_rf_family/router_summary.csv \
  --summary seed41_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v3_rf_family/router_summary.csv \
  --summary seed41_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v3_rf_family/router_summary.csv \
  --summary seed43_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v3_rf_family/router_summary.csv \
  --summary seed43_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v3_rf_family/router_summary.csv \
  --summary seed47_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed47_v3_rf_family/router_summary.csv \
  --summary seed47_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed47_v3_rf_family/router_summary.csv \
  --summary seed53_noenv=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v3_rf_family/router_summary.csv \
  --summary seed53_env=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v3_rf_family/router_summary.csv \
  --output-csv outputs/week2_rf_family_multiseed_100s_summary.csv \
  --per-run-csv outputs/week2_rf_family_multiseed_100s_per_run.csv
```

- Full 8-run aggregate:
  - no env:
    - oracle selector: `0.1004 +/- 0.0348`
    - `rf_high_capacity`: `0.1841 +/- 0.0150`
    - plain `rf_specialist`: `0.1861 +/- 0.0135`
    - `rf_specialist_fallback`: `0.1861 +/- 0.0135`
    - hard specialist: `0.1961 +/- 0.0163`
  - with env:
    - oracle selector: `0.1015 +/- 0.0373`
    - `rf_high_capacity`: `0.1868 +/- 0.0132`
    - plain `rf_specialist`: `0.1879 +/- 0.0141`
    - `rf_specialist_fallback`: `0.1879 +/- 0.0141`
    - hard specialist: `0.1984 +/- 0.0147`
- Mean deltas:
  - vs plain `rf_specialist`
    - no env: `+0.0020` regret in favor of `rf_high_capacity`
    - with env: `+0.0011` regret in favor of `rf_high_capacity`
  - vs hard specialist
    - no env: `+0.0120` regret in favor of `rf_high_capacity`
    - with env: `+0.0116` regret in favor of `rf_high_capacity`
- Deployable win counts:
  - no env:
    - `rf_high_capacity`: `3/8`
    - hard specialist: `2/8`
    - `rf_utility_gap_fallback`: `2/8`
    - `rf_specialist_fallback`: `1/8` (tie artifact)
  - with env:
    - hard specialist: `2/8`
    - `rf_high_capacity`: `1/8`
    - `direct_utility`: `1/8`
    - `rf_direct_utility`: `1/8`
    - `rf_utility_gap_fallback`: `1/8`
    - `rf_specialist_fallback`: `1/8` (tie artifact)
    - `sparse_override`: `1/8`
- Interpretation:
  - `rf_high_capacity` 现在已经完成了 full multi-seed 验证，并在 `no-env / with-env` 两边都成为新的 mean winner。
  - 提升幅度不大，但它跨过了最关键的门槛：不再只是 pilot/no-env 的局部现象，而是在完整 8-run 主表上稳定优于 plain `rf_specialist`。
  - `rf_specialist_fallback` 继续没有任何独立价值；full aggregate 下它仍与 plain `rf_specialist` 完全同分，应该正式退役。
  - 当前最合理的主线更新是：把 `rf_high_capacity` 升格成默认 learned-router family；后续如果继续强化 router，应从这条线继续，而不是再回到 plain `rf_specialist` 或 fallback 微调。

### Entry: `rf_high_capacity_margin` representative no-env filter

- Status: NEGATIVE_REPRESENTATIVE
- Goal: 在 `rf_high_capacity` family 内测试更激进的 hard-margin sample weighting，判断它是否值得扩到完整 `100-sample` 主表。
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `rf_high_capacity_margin_specialist_router_predicted_state`
- Representative outputs:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_margin/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v4_rf_highcap_margin/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v4_rf_highcap_margin/`
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v4_rf_highcap_margin/`
  - `outputs/week2_rf_highcap_margin_representative_noenv_summary.csv`
  - `outputs/week2_rf_highcap_margin_representative_noenv_per_run.csv`
- Repro commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for seed in original 31 41 53; do
  if [ "${seed}" = "original" ]; then
    ARITH_CSV="outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv"
    ARITH_NPZ="outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz"
    LINEAR_CSV="outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv"
    LINEAR_NPZ="outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz"
    OUT_NOENV="outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_margin"
  else
    ARITH_CSV="outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_oracle_records.csv"
    ARITH_NPZ="outputs/week2_arithmetic_8b_data_v3_100s_seed${seed}/prefix_hidden_states.npz"
    LINEAR_CSV="outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_oracle_records.csv"
    LINEAR_NPZ="outputs/week2_linear_8b_data_v4_100s_seed${seed}/prefix_hidden_states_last_prompt.npz"
    OUT_NOENV="outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed${seed}_v4_rf_highcap_margin"
  fi

  PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
    --arithmetic-input-csv "${ARITH_CSV}" \
    --arithmetic-embedding-npz "${ARITH_NPZ}" \
    --linear-input-csv "${LINEAR_CSV}" \
    --linear-embedding-npz "${LINEAR_NPZ}" \
    --output-dir "${OUT_NOENV}" \
    --n-splits 5 \
    --state-mode s_proxy \
    --state-head-model pca_enet
done

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_margin/router_summary.csv \
  --summary seed31=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v4_rf_highcap_margin/router_summary.csv \
  --summary seed41=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v4_rf_highcap_margin/router_summary.csv \
  --summary seed53=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v4_rf_highcap_margin/router_summary.csv \
  --output-csv outputs/week2_rf_highcap_margin_representative_noenv_summary.csv \
  --per-run-csv outputs/week2_rf_highcap_margin_representative_noenv_per_run.csv
```

- Representative 4-seed aggregate:
  - `rf_high_capacity`: `0.1833 +/- 0.0137`
  - plain `rf_specialist`: `0.1836 +/- 0.0115`
  - `rf_high_capacity_margin`: `0.1847 +/- 0.0153`
  - `rf_utility_gap`: `0.1900 +/- 0.0244`
  - hard specialist: `0.1905 +/- 0.0157`
- Per-seed deltas vs `rf_high_capacity`:
  - `original`: `+0.0059` regret for `rf_high_capacity_margin`
  - `seed31`: `-0.0012` regret for `rf_high_capacity_margin`
  - `seed41`: `+0.0054` regret for `rf_high_capacity_margin`
  - `seed53`: `-0.0046` regret for `rf_high_capacity_margin`
- Interpretation:
  - hard-margin weighting 没有形成清晰升级：4-seed representative aggregate 上它劣于 plain `rf_high_capacity`，也没有超过 plain `rf_specialist`。
  - 这不是“完全没信号”的负结果，因为它在 `seed31/53` 上确实改善了 `rf_high_capacity`；但它会明显压坏 already-good seeds（尤其 `original/seed41`）。
  - 当前最合理的收敛是：`rf_high_capacity_margin` 不值得直接扩到 full 主表。后续如果继续沿 weighting 线做，只值得测试更温和的 tempered weighting，而不是继续 hard-margin 扩容。

### Entry: `rf_highcap_only` soft-margin runtime probe

- Status: EXECUTION_BLOCKED
- Goal: 在不改变 `100-sample` 口径的前提下，先用 `rf_highcap_only` family-mode 跑通 `rf_high_capacity_soft_margin` 的 representative filter，验证“只裁 baseline 数量”能否把 same-family sweep 拉回到可接受时延。
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `--router-family-mode {full,rf_highcap_only}`
  - 新增 `rf_high_capacity_soft_margin_specialist_router_predicted_state`
- Probe command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v5b_rf_highcap_soft_margin_family \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet \
  --router-family-mode rf_highcap_only
```

- Result:
  - 编译验证通过：`PYTHONPATH=. python -m compileall scripts/run_week2_cross_domain_router.py`
  - 单个 `original/no-env` family-only run 在 `8m40s` wall-clock 后仍无 `router_summary.csv`
  - 同期进程统计：约 `4h27m` CPU time，`%CPU ≈ 3086`
  - 该 probe 被主动终止，没有写入最终 summary artifact
- Interpretation:
  - `rf_highcap_only` 虽然避免了后半段 baseline 全并发，但它没有解决主瓶颈。
  - 当前 same-family sweep 的主耗时不在 router baseline 数量，而在 `_build_router_training_set` 里的 specialist OOF generation。
  - 因此下一步不该继续只做 baseline 裁剪；要真正加速 `rf_high_capacity` family，必须引入可复用 cache，或把 specialist-side 中间产物从 router-head sweep 里拆出来。

### Entry: `rf_highcap_only` fold-cache implementation + tiny smoke

- Status: INFRA_READY
- Goal: 给 `rf_high_capacity` family 加入可复用 fold cache，验证 specialist-side 中间产物可以跨同族 router sweep 复用，而不是每次重新生成。
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `--router-cache-dir`
  - `rf_highcap_only` 路径现在会按 outer fold 落盘：
    - `train_router_x.pkl`
    - `train_targets.pkl`
    - `test_router_x.pkl`
    - `test_support.pkl`
- Tiny smoke inputs:
  - arithmetic: `outputs/week2_router_cache_smoke_tiny/arithmetic/`
  - linear: `outputs/week2_router_cache_smoke_tiny/linear/`
  - 由 `40-sample` 数据裁出 `8` 个 `sample_id` 组，仅用于执行验证，不用于主结论
- Repro commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_router_cache_smoke_tiny/arithmetic/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_router_cache_smoke_tiny/arithmetic/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_router_cache_smoke_tiny/linear/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_router_cache_smoke_tiny/linear/prefix_hidden_states.npz \
  --output-dir outputs/week2_router_cache_smoke_tiny_run1 \
  --router-cache-dir outputs/week2_router_cache_smoke_tiny_run1/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 2 \
  --state-mode s_proxy \
  --state-head-model pca_enet

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_router_cache_smoke_tiny/arithmetic/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_router_cache_smoke_tiny/arithmetic/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_router_cache_smoke_tiny/linear/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_router_cache_smoke_tiny/linear/prefix_hidden_states.npz \
  --output-dir outputs/week2_router_cache_smoke_tiny_run2 \
  --router-cache-dir outputs/week2_router_cache_smoke_tiny_run1/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 2 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

- Smoke result:
  - run1 成功写出两折 cache：
    - `outputs/week2_router_cache_smoke_tiny_run1/cache/fold_01/`
    - `outputs/week2_router_cache_smoke_tiny_run1/cache/fold_02/`
  - run2 直接命中同一 cache，并在 `ELAPSED=11.025` 秒完成
  - `run1` 与 `run2` 的 `router_summary.csv` 主指标逐项一致
- Tiny smoke summary:
  - `oracle_expert_selector = 0.0000`
  - hard specialist `= 0.5027`
  - `rf_specialist = 0.5996`
  - `rf_high_capacity = 0.6227`
  - `rf_high_capacity_soft_margin = 0.6227`
  - `rf_high_capacity_margin = 0.6481`
- Interpretation:
  - cache 路径已经真正打通：同一个 fold 的 specialist-side 成本现在可以跨同族 router 变体复用。
  - `soft-margin` 在 tiny smoke 上没有优于 plain `rf_high_capacity`，但这个 smoke 的用途只是执行验证，不应作为主结果外推。
  - 当前最重要的变化不是 tiny 指标，而是后续终于可以在 `100-sample` 上做 cache-backed 的 `rf_high_capacity_soft_margin` representative filter，而不必每次重复付 OOF 成本。

### Entry: cache-backed `rf_high_capacity_soft_margin` representative `100-sample / no-env`

- Status: MIXED_SIGNAL
- Goal: 在真实 `100-sample` 代表性 `no-env` seeds 上，用 cache-backed `rf_highcap_only` 路径评估 tempered weighting（`sample_weight = 1 + margin`）是否值得让 `rf_high_capacity_soft_margin` 取代 plain `rf_high_capacity`。
- Code path:
  - `scripts/run_week2_cross_domain_router.py`
  - mode: `--router-family-mode rf_highcap_only`
  - cache: `--router-cache-dir .../cache`
- Representative seeds:
  - `original`
  - `seed31`
  - `seed41`
  - `seed53`
- Repro commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed31/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed31/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed31/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed31/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v4_rf_highcap_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v4_rf_highcap_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed41/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed41/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed41/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed41/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v4_rf_highcap_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v4_rf_highcap_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed53/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed53/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed53/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed53/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v4_rf_highcap_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v4_rf_highcap_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_repr/router_summary.csv \
  --summary seed31=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v4_rf_highcap_repr/router_summary.csv \
  --summary seed41=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v4_rf_highcap_repr/router_summary.csv \
  --summary seed53=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v4_rf_highcap_repr/router_summary.csv \
  --output-csv outputs/week2_rf_highcap_soft_margin_representative_noenv_summary.csv \
  --per-run-csv outputs/week2_rf_highcap_soft_margin_representative_noenv_per_run.csv
```

- Real-run timings:
  - `original`: `ELAPSED=617.686`
  - `seed31`: `ELAPSED=591.015`
  - `seed41`: `ELAPSED=579.032`
  - `seed53`: `ELAPSED=605.862`
- Infrastructure check:
  - 四个真实 `100-sample` runs 都成功写出 `cache/fold_01` 到 `cache/fold_05`
  - 说明 `rf_highcap_only + router-cache-dir` 在真实规模上已可稳定执行，当前问题只是 wall-clock，不再是实现错误
- Aggregate artifact:
  - `outputs/week2_rf_highcap_soft_margin_representative_noenv_summary.csv`
  - `outputs/week2_rf_highcap_soft_margin_representative_noenv_per_run.csv`
  - `outputs/week2_rf_highcap_soft_margin_representative_noenv_best_by_run.csv`
  - `outputs/week2_rf_highcap_soft_margin_representative_noenv_win_counts.csv`
- Representative 4-seed aggregate:
  - `rf_high_capacity`: `0.1815 +/- 0.0119`
  - `rf_high_capacity_soft_margin`: `0.1817 +/- 0.0149`
  - plain `rf_specialist`: `0.1828 +/- 0.0116`
  - `rf_high_capacity_margin`: `0.1843 +/- 0.0162`
  - hard specialist: `0.1869 +/- 0.0168`
- Best-by-run:
  - `original`: hard specialist `0.1811`
  - `seed31`: hard specialist `0.1923`
  - `seed41`: `rf_high_capacity_soft_margin = 0.1747`
  - `seed53`: `rf_high_capacity_soft_margin = 0.1651`
- Interpretation:
  - `soft-margin` 不是空信号：它在 `seed41/53` 上确实翻成了 per-run winner，也明显优于 hard specialist。
  - 但 representative aggregate 上，它仍然略输 plain `rf_high_capacity`，差约 `+0.0002` regret。
  - 这说明 tempered weighting 比 hard-margin 明显更稳，但还不足以把 `rf_high_capacity` 的默认 family 再往前推一代。
  - 当前最合理的收敛是：保留 `rf_high_capacity_soft_margin` 作为 appendix 级 mixed-signal 分支，不升格为新的默认 learned-router family；`rf_high_capacity` 继续保持默认。

### Entry: cache-hit `rf_high_capacity_extra_trees` representative `100-sample / no-env`

- Status: GO_CANDIDATE
- Goal: 在不重算 specialist OOF 的前提下，测试一个纯 router-capacity 升级是否能在 representative `100-sample / no-env` 上稳定优于 plain `rf_high_capacity`。
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 `rf_high_capacity_extra_trees_specialist_router_predicted_state`
  - 参数化：`ExtraTreesClassifier(n_estimators=768, criterion=log_loss, min_samples_leaf=2, max_features=sqrt, class_weight=balanced)`
- Compile verification:

```bash
PYTHONPATH=. python -m compileall scripts/run_week2_cross_domain_router.py
```

- Cache-hit repro pattern:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v5_rf_highcap_extratrees_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v4_rf_highcap_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

- Representative seeds:
  - `original`
  - `seed31`
  - `seed41`
  - `seed53`
- Cache-hit timings:
  - `original`: `ELAPSED=40.019`
  - `seed31`: `ELAPSED=38.840`
  - `seed41`: `ELAPSED=39.499`
  - `seed53`: `ELAPSED=38.911`
- Aggregate artifact:
  - `outputs/week2_rf_highcap_extratrees_representative_noenv_summary.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_noenv_per_run.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_noenv_best_by_run.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_noenv_win_counts.csv`
- Representative 4-seed aggregate:
  - `rf_high_capacity_extra_trees`: `0.1799 +/- 0.0141`
  - `rf_high_capacity`: `0.1815 +/- 0.0119`
  - `rf_high_capacity_soft_margin`: `0.1817 +/- 0.0149`
  - plain `rf_specialist`: `0.1828 +/- 0.0116`
  - hard specialist: `0.1869 +/- 0.0168`
  - delta vs plain `rf_high_capacity`: `-0.0016` regret
- Best-by-run:
  - `original`: `rf_high_capacity_extra_trees = 0.1799`
  - `seed31`: hard specialist `0.1923`
  - `seed41`: `rf_high_capacity_soft_margin = 0.1747`
  - `seed53`: `rf_high_capacity_extra_trees = 0.1630`
- Interpretation:
  - 这是目前第一条在 representative aggregate 上真正超过 plain `rf_high_capacity` 的后续同族升级线。
  - 它的信号也比 `soft-margin` 更干净：`soft-margin` 只做到 mixed-signal aggregate 打平附近，而 `extra_trees` 已经把均值真正往下压。
  - 同时，这一步验证了 fold-cache 的真正价值：same-family rerun 已从十分钟级重算降到四十秒级 cache-hit，后续同类筛选可以按 representative aggregate 快速推进。
  - 但它目前仍只是 `no-env / representative 4-seed` 的正向候选，还不能据此直接改写全局默认 family。当前最合理的下一步是把 `rf_high_capacity_extra_trees` 升格成下一个 full-family 扩展候选，而不是立刻宣称替代 `rf_high_capacity` 主表。

### Entry: `rf_high_capacity_extra_trees` full `8-run no-env` extension

- Status: NOENV_MEAN_WIN
- Goal: 把 `rf_high_capacity_extra_trees` 从 `4-seed representative / no-env` 候选扩到完整 `8-run no-env`，判断它是否能通过更硬的 multi-seed 主表筛选。
- Existing cache-hit seeds:
  - `original`
  - `seed31`
  - `seed41`
  - `seed53`
- Newly completed full runs:
  - `seed29`
  - `seed37`
  - `seed43`
  - `seed47`
- Repro commands for new seeds follow the same `rf_highcap_only` pattern; representative example:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed29/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed29/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original=outputs/week2_pooled_learned_router_no_env_bigdata_100s_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed29=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed31=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed37=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed37_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed41=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed41_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed43=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed43_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed47=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed47_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed53=outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed53_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --output-csv outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_summary.csv \
  --per-run-csv outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_per_run.csv
```

- New full-run timings:
  - `seed29`: `ELAPSED=586.171`
  - `seed37`: `ELAPSED=598.676`
  - `seed43`: `ELAPSED=626.120`
  - `seed47`: `ELAPSED=599.843`
- Full 8-run no-env aggregate:
  - `rf_high_capacity_extra_trees`: `0.1824 +/- 0.0131`
  - `rf_high_capacity`: `0.1838 +/- 0.0109`
  - `rf_high_capacity_soft_margin`: `0.1842 +/- 0.0143`
  - plain `rf_specialist`: `0.1850 +/- 0.0110`
  - `rf_high_capacity_margin`: `0.1857 +/- 0.0152`
  - hard specialist: `0.1954 +/- 0.0168`
  - delta vs plain `rf_high_capacity`: `-0.0014` regret
- Artifacts:
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_summary.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_per_run.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_best_by_run.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_noenv_win_counts.csv`
- Best-by-run / win counts:
  - `extra_trees`: `3/8`
  - `soft_margin`: `2/8`
  - `margin`: `1/8`
  - plain `rf_high_capacity`: `1/8`
  - hard specialist: `1/8`
- Interpretation:
  - `extra_trees` 已经通过了比 representative filter 更硬的一道门槛：它不只是 `4-seed` 偶然翻转，而是在完整 `8-run no-env` 上仍然保持 mean win。
  - 这个结果也把路线进一步收紧了：capacity-only 升级现在明显比 weighting-only 升级更值得继续。
  - 但它仍然只是在 `no-env` setting 上成立。当前还不能据此直接改写全局默认 family；下一步应优先测试 `with-env`，而不是继续在 `no-env` 内部扫更多小变体。

### Entry: `rf_high_capacity_extra_trees` `with-env` representative gate and full `8-run` extension

- Status: GLOBAL_MEAN_WIN
- Goal: 先用 `original / seed31 / seed41 / seed53` 的 representative `with-env` aggregate 检查 `rf_high_capacity_extra_trees` 是否值得扩到 full multi-seed；若通过，再补完 `seed29 / seed37 / seed43 / seed47`，判断它能否在 `with-env` 上也成为 mean winner。
- Representative commands:

```bash
TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed31/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed31/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed31/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed31/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr/cache \
  --include-env-feature \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed31=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed41=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed53=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --output-csv outputs/week2_rf_highcap_extratrees_representative_withenv_summary.csv \
  --per-run-csv outputs/week2_rf_highcap_extratrees_representative_withenv_per_run.csv
```

- Representative 4-seed aggregate:
  - `rf_high_capacity_extra_trees`: `0.1807 +/- 0.0118`
  - `rf_high_capacity`: `0.1822 +/- 0.0135`
  - `rf_high_capacity_soft_margin`: `0.1831 +/- 0.0105`
  - plain `rf_specialist`: `0.1836 +/- 0.0096`
  - `rf_high_capacity_margin`: `0.1853 +/- 0.0169`
  - hard specialist: `0.1902 +/- 0.0126`
  - delta vs plain `rf_high_capacity`: `-0.0015` regret
- Representative artifacts:
  - `outputs/week2_rf_highcap_extratrees_representative_withenv_summary.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_withenv_per_run.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_withenv_best_by_run.csv`
  - `outputs/week2_rf_highcap_extratrees_representative_withenv_win_counts.csv`
- Representative best-by-run:
  - `original`: `extra_trees`
  - `seed31`: hard specialist
  - `seed41`: plain `rf_high_capacity`
  - `seed53`: `rf_high_capacity_margin`
- Representative interpretation:
  - representative gate 通过，但信号明显比 `no-env` 更 mixed；`extra_trees` 是 mean winner，但 per-seed winner 已开始分散。
  - 因为 representative aggregate 仍然明确优于 plain `rf_high_capacity` 和 hard specialist，所以继续扩到 full `8-run with-env` 是合理的。

- Full extension commands for new seeds follow the same `rf_highcap_only + --include-env-feature` pattern; representative example:

```bash
TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed29/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s_seed29/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s_seed29/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr/cache \
  --include-env-feature \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet

PYTHONPATH=. python scripts/aggregate_week2_router_multiseed.py \
  --summary original=outputs/week2_pooled_learned_router_with_env_bigdata_100s_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed29=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed29_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed31=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed37=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed37_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed41=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed41_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed43=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed43_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed47=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed47_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --summary seed53=outputs/week2_pooled_learned_router_with_env_bigdata_100s_seed53_v5_rf_highcap_extratrees_repr/router_summary.csv \
  --output-csv outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_summary.csv \
  --per-run-csv outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_per_run.csv
```

- New full-run timings:
  - `seed29`: `ELAPSED=585.701`
  - `seed37`: `ELAPSED=602.554`
  - `seed43`: `ELAPSED=616.416`
  - `seed47`: `ELAPSED=603.096`
- Full 8-run with-env aggregate:
  - `rf_high_capacity_extra_trees`: `0.1828 +/- 0.0128`
  - `rf_high_capacity_soft_margin`: `0.1851 +/- 0.0117`
  - `rf_high_capacity`: `0.1852 +/- 0.0132`
  - plain `rf_specialist`: `0.1852 +/- 0.0122`
  - `rf_high_capacity_margin`: `0.1864 +/- 0.0142`
  - hard specialist: `0.1975 +/- 0.0147`
  - delta vs plain `rf_high_capacity`: `-0.0023` regret
- Full with-env artifacts:
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_summary.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_per_run.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_best_by_run.csv`
  - `outputs/week2_rf_highcap_extratrees_multiseed_100s_withenv_win_counts.csv`
- Full with-env best-by-run / win counts:
  - `extra_trees`: `3/8`
  - plain `rf_specialist`: `2/8`
  - hard specialist: `1/8`
  - plain `rf_high_capacity`: `1/8`
  - `rf_high_capacity_margin`: `1/8`
- Interpretation:
  - `extra_trees` 现在不只是 `no-env` 的 aggregate-positive 升级线，而是已经在 `with-env` 上也通过 full `8-run` multi-seed 筛选。
  - 这把 family 级结论真正收口了：当前应把默认 learned-router family 从 plain `rf_high_capacity` 更新为 `rf_high_capacity_extra_trees`。
  - 同时，这也把 same-family sweep 的经验写得更清楚：capacity-only 升级可以跨 setting 泛化，而 weighting-only 升级更容易停留在 mixed-signal。

### Entry: `rf_high_capacity_extra_trees_full_features` early no-go probe

- Status: NO_GO_EARLY
- Goal: 在不改变监督与 specialist 特征的前提下，只沿 `rf_high_capacity_extra_trees` 做一个更强的同家族容量升级：保留 ExtraTrees，但把 `max_features` 从 `"sqrt"` 改成 `None`，先过 representative gate 再决定是否扩 full multi-seed。
- Code change:
  - `scripts/run_week2_cross_domain_router.py`
  - 新增 baseline: `rf_high_capacity_extra_trees_full_features_specialist_router_predicted_state`
- Verification:

```bash
PYTHONPATH=. python -m compileall scripts/run_week2_cross_domain_router.py
```

- Valid completed probe:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_v6_rf_highcap_extratrees_fullfeat_repr/`
- Repro command:

```bash
TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_cross_domain_router.py \
  --arithmetic-input-csv outputs/week2_arithmetic_8b_data_v3_100s/prefix_oracle_records.csv \
  --arithmetic-embedding-npz outputs/week2_arithmetic_8b_data_v3_100s/prefix_hidden_states.npz \
  --linear-input-csv outputs/week2_linear_8b_data_v4_100s/prefix_oracle_records.csv \
  --linear-embedding-npz outputs/week2_linear_8b_data_v4_100s/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v6_rf_highcap_extratrees_fullfeat_repr \
  --router-cache-dir outputs/week2_pooled_learned_router_no_env_bigdata_100s_v5_rf_highcap_extratrees_repr/cache \
  --router-family-mode rf_highcap_only \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model pca_enet
```

- `original/no-env` result:
  - plain `rf_high_capacity_extra_trees`: `0.193675`
  - `rf_high_capacity_extra_trees_full_features`: `0.195545`
  - hard specialist: `0.193711`
  - delta vs plain `extra_trees`: `+0.001870` regret
  - wall-clock: `ELAPSED=625.281`
- Interpretation:
  - 这个 probe 在第一个 cache-backed `original/no-env` run 上就已经给出明显负信号：效果落后于当前默认 `extra_trees`，同时 wall-clock 仍是十分钟级，不符合“same-family cheap gate”的预期。
  - 因此这条线没有继续扩 representative 4-seed，更没有扩 full multi-seed；当前最合理的结论是 early no-go。

- Cache audit follow-up:
  - `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v5_rf_highcap_extratrees_repr/cache` 只有 `fold_01` 完整，`fold_02-05` 缺失；因此后续 `seed31` rerun 会退回 specialist OOF generation，而不是纯 cache-hit。
  - 这说明并不是脚本忽略旧 cache，而是历史 `v5` cache 资产本身不完整。当前 partial directory `outputs/week2_pooled_learned_router_no_env_bigdata_100s_seed31_v6_rf_highcap_extratrees_fullfeat_repr/` 是中断产物，不应纳入任何 aggregate。
- Final conclusion:
  - `full_features` 这条容量升级当前不值得继续。
  - 下一步如果还沿 `extra_trees` 往下做，优先级应回到别的容量线或更多 multi-seed 压方差，而不是继续这条 `max_features=None` 分支。

### Entry: Week-2 budget-axis evaluation v1 (`Action Regret@Budget` + equal-token frontier)

- Status: PAPER_CLOSEOUT_BASE
- Goal: 按 [paper_reframe.md](/cephfs/luyanzhen/apg/triver/paper_reframe.md) 的主文收口要求，先把 proposal 里最缺的预算轴指标补齐：`Action Regret@Budget` 和 equal-token frontier；保持主文 controller 集合简洁可解释，不回到 appendix 级 wrapper/router sweep。
- Main-text controller set:
  - `ordered_scalar_mu`
  - `learned_1d_linear`
  - `direct_policy`
  - `factorized_exact_state`
  - one selected deployable factorized controller per domain,统一命名为 `factorized_predicted_state_selected`
- Code changes:
  - `triver/baselines/week2.py`
    - 新增 `build_policy_sample_records(...)`
    - 新增 `run_group_cv_with_samples(...)`
  - `triver/factorized/week2.py`
    - 新增 `run_factorized_cv_with_samples(...)`
  - `scripts/run_week2_budget_eval.py`
    - 生成 per-sample / per-budget budget-axis artifacts
  - `scripts/aggregate_week2_budget_eval.py`
    - 聚合双域 `budget_summary_main` 与 `combined_sample_results`
- Verification:

```bash
PYTHONPATH=. python -m compileall \
  scripts/run_week2_budget_eval.py \
  scripts/aggregate_week2_budget_eval.py \
  triver/baselines/week2.py \
  triver/factorized/week2.py
```

- Repro commands:

```bash
TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_budget_eval.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_linear_8b_budget_eval_v1 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear

TIMEFORMAT='ELAPSED=%3R'; time PYTHONPATH=. python scripts/run_week2_budget_eval.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_arithmetic_8b_budget_eval_v1 \
  --n-splits 5 \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic

PYTHONPATH=. python scripts/aggregate_week2_budget_eval.py \
  --linear-dir outputs/week2_linear_8b_budget_eval_v1 \
  --arithmetic-dir outputs/week2_arithmetic_8b_budget_eval_v1 \
  --output-dir outputs/week2_budget_axis_v1
```

- Runtime:
  - linear budget eval: `ELAPSED=24.794`
  - arithmetic budget eval: `ELAPSED=46.315`
- Output dirs:
  - `outputs/week2_linear_8b_budget_eval_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_v1/`
  - `outputs/week2_budget_axis_v1/`
- Key artifacts:
  - per-domain:
    - `action_regret_at_budget.csv`
    - `equal_token_frontier.csv`
    - `budget_summary_main.csv`
    - `combined_sample_results.csv`
  - cross-domain:
    - `budget_axis_domain_comparison.csv`
    - `budget_axis_domain_overall.csv`
    - `budget_axis_domain_overall_main.csv`
    - `budget_axis_domain_budget_winners.csv`
    - `action_regret_at_budget_by_domain.csv`
    - `equal_token_frontier_by_domain.csv`

- Cross-domain overall main summary:
  - arithmetic:
    - `ordered_scalar_mu`: accuracy `0.7925`, regret `0.1649`
    - `factorized_exact_state`: accuracy `0.7358`, regret `0.2153`
    - `direct_policy`: accuracy `0.6226`, regret `0.3217`
    - `learned_1d_linear`: accuracy `0.6226`, regret `0.3349`
    - `factorized_predicted_state_selected`: accuracy `0.4340`, regret `0.5047`
  - linear:
    - `factorized_exact_state`: accuracy `0.7674`, regret `0.1356`
    - `direct_policy`: accuracy `0.7209`, regret `0.2226`
    - `learned_1d_linear`: accuracy `0.6977`, regret `0.2619`
    - `factorized_predicted_state_selected`: accuracy `0.5349`, regret `0.3709`
    - `ordered_scalar_mu`: accuracy `0.4884`, regret `0.4274`

- Budget-bin winner counts (`budget_axis_domain_budget_winners.csv`):
  - arithmetic:
    - `direct_policy`: `6` bins
    - `ordered_scalar_mu`: `4` bins
    - `factorized_exact_state`: `4` bins
    - `learned_1d_linear`: `2` bins
    - `factorized_predicted_state_selected`: `1` bin
  - linear:
    - `direct_policy`: `8` bins
    - `factorized_exact_state`: `5` bins
    - `factorized_predicted_state_selected`: `1` bin
    - `ordered_scalar_mu`: `0` bins

- Interpretation:
  - 预算轴结果和之前的域间分叉是一致的，而且更贴 proposal 的 compute-control 叙事：
    - arithmetic 里 `ordered_scalar_mu` 仍是 overall best main-text controller；
    - linear 里 `factorized_exact_state` 和 `direct_policy` 主导 budget bins，而 `ordered_scalar_mu` 在 main budget table 里最差。
  - `factorized_predicted_state_selected` 在两个域里都明显落后于 exact-state 上界，直接把 deployment gap 从“overall regret”推进到了“budget-conditioned regret”层。
  - 因此 paper 的 strongest main-text 结论仍应写成条件性：
    - scalar insufficiency 在 linear 域上清楚成立；
    - arithmetic 域更支持“何时 scalar 足够、何时不足”的 conditional framing。

- Paper-closeout consequence:
  - `Action Regret@Budget` 和 equal-token frontier 的基础表已经具备，可直接进入主文收口。
  - 预算轴接下来最该补的只剩 proposal 里另外两类动作质量指标：
    - `Revision Harm`
    - `Compute Value Calibration`

### Entry: Week-2 action-quality metrics v1 (`Revision Harm` + `Compute Value Calibration`)

- Status: PAPER_CLOSEOUT_BASE
- Goal: 在上一轮 budget-axis artifact 的同一套 sample-level CV 输出上，补 proposal 主文剩余的两类动作质量指标：
  - `Revision Harm`
  - `Compute Value Calibration`
- Definitions used in v1:
  - `Revision Harm`
    - harmful revise := controller 选择 `revise_1`，但 oracle action 是 `continue`
    - 报告 `revision_harm_rate_overall`、`revision_harm_rate_among_revise`、`mean_revision_harm_gap`
  - `Compute Value Calibration`
    - true compute value := `max(continue_utility, revise_utility) - abstain_utility`
    - controller-native proxy:
      - `ordered_scalar_mu` -> `mu_continue`
      - `learned_1d_linear` -> learned scalar score
      - `direct_policy` -> `1 - p(abstain)` as confidence proxy
      - factorized controllers -> predicted utility margin `max(score_continue, score_revise) - score_abstain`
    - 报告：
      - `spearman_rho`
      - `pearson_r`
      - `utility_scale_rmse`（仅对 utility-scale proxy 有意义）
- Code changes:
  - `triver/baselines/week2.py`
    - `build_policy_sample_records(...)` 支持 per-row `extra_columns`
    - 新增 `extract_policy_proxy_columns(...)`
  - `triver/factorized/week2.py`
    - `run_factorized_cv_with_samples(...)` 现写出 predicted action scores / proxy columns
    - 新增 `build_factorized_proxy_columns(...)`
  - `scripts/run_week2_budget_eval.py`
    - 新增 `combined_sample_results_main.csv`
    - 新增 `revision_harm_summary.csv`
    - 新增 `revision_harm_at_budget.csv`
    - 新增 `compute_value_calibration_summary.csv`
    - 新增 `compute_value_calibration_bins.csv`
  - `scripts/aggregate_week2_budget_eval.py`
    - 新增跨域：
      - `revision_harm_by_domain.csv`
      - `revision_harm_at_budget_by_domain.csv`
      - `compute_value_calibration_summary_by_domain.csv`
      - `compute_value_calibration_bins_by_domain.csv`
- Verification:

```bash
PYTHONPATH=. python -m compileall \
  scripts/run_week2_budget_eval.py \
  scripts/aggregate_week2_budget_eval.py \
  triver/baselines/week2.py \
  triver/factorized/week2.py
```

- Repro commands:
  - 与上一条 budget-axis entry 相同；本轮是在同一命令下重跑 budget eval，并在同一输出目录内新增 action-quality artifacts。

- Output dirs reused:
  - `outputs/week2_linear_8b_budget_eval_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_v1/`
  - `outputs/week2_budget_axis_v1/`

- Key artifacts:
  - per-domain:
    - `combined_sample_results_main.csv`
    - `revision_harm_summary.csv`
    - `revision_harm_at_budget.csv`
    - `compute_value_calibration_summary.csv`
    - `compute_value_calibration_bins.csv`
  - cross-domain:
    - `revision_harm_by_domain.csv`
    - `revision_harm_at_budget_by_domain.csv`
    - `compute_value_calibration_summary_by_domain.csv`
    - `compute_value_calibration_bins_by_domain.csv`

- Revision Harm summary:
  - linear:
    - `factorized_exact_state`: overall harm `0.0465`, among-revise harm `0.0952`
    - `factorized_predicted_state_selected`: overall harm `0.0465`, among-revise harm `0.0800`
    - `direct_policy`, `learned_1d_linear`, `ordered_scalar_mu`: `0.0000`
  - arithmetic:
    - `factorized_predicted_state_selected`: overall harm `0.0189`, among-revise harm `0.0625`
    - `direct_policy`, `factorized_exact_state`, `learned_1d_linear`, `ordered_scalar_mu`: `0.0000`
- Revision Harm interpretation:
  - harmful revise 不是普遍高发，但在 factorized controllers 上确实出现，尤其 deployable predicted-state 仍有 residual harm。
  - 这和 earlier deployment-gap diagnosis 是一致的：主要问题不是“不会 revise”，而是 noisy state 下 revise timing/selection 还不稳。

- Compute Value Calibration summary:
  - linear:
    - `factorized_exact_state`: `spearman_rho = 0.8049`, `utility_scale_rmse = 0.4369`
    - `direct_policy`: `spearman_rho = 0.6512`
    - `ordered_scalar_mu`: `spearman_rho = 0.6284`
    - `factorized_predicted_state_selected`: `spearman_rho = 0.1280`, `utility_scale_rmse = 0.9067`
    - `learned_1d_linear`: `spearman_rho = -0.6483`
  - arithmetic:
    - `ordered_scalar_mu`: `spearman_rho = 0.6103`
    - `factorized_exact_state`: `spearman_rho = 0.5891`, `utility_scale_rmse = 0.7258`
    - `direct_policy`: `spearman_rho = 0.5249`
    - `factorized_predicted_state_selected`: `spearman_rho = -0.0307`, `utility_scale_rmse = 1.0994`
    - `learned_1d_linear`: `spearman_rho = -0.5350`
- Calibration interpretation:
  - `factorized_exact_state` 在 linear 上给出当前最强的 compute-value calibration，和其 regret 上界地位一致。
  - `factorized_predicted_state_selected` 在两个域上 calibration 都明显塌掉，这把 deployment gap 从 action regret 推进到了 “predicted compute value 不再和真实 gain 对齐”。
  - `learned_1d_linear` 在两个域上都出现负相关，说明 learned 1D scalar 并没有稳定学到 proposal 所需的 compute-value ordering。

- Paper-closeout consequence:
  - proposal 主文里四类 decision-quality 指标现在都已有 `v1` artifact：
    - `Action Regret@Budget`
    - equal-token frontier
    - `Revision Harm`
    - `Compute Value Calibration`
  - 接下来主线不该再补新 head，而应转到：
    - minimal repeatability check
    - 主图 / 主表组装

### Entry: Within-domain main-text repeatability v1 (`100-sample`, representative 4-run)

- Status: PAPER_CLOSEOUT_REPEATABILITY_V1
- Goal: 给主文最关键的 within-domain controller 对照补一个最小 repeatability check，避免继续依赖 single-run / small-data 排名来写 strongest claim。
- Scope:
  - domains:
    - `linear`
    - `arithmetic`
  - runs:
    - `original`
    - `seed31`
    - `seed41`
    - `seed53`
  - main-text controller set only:
    - `ordered_scalar_mu`
    - `learned_1d_linear`
    - `direct_policy`
    - `factorized_exact_state`
    - `factorized_predicted_state_selected`
- Route change:
  - 初始计划是直接复用 full `run_week2_budget_eval.py` 在 `100-sample` 数据上做 repeatability。
  - 实测 original `100-sample` runtime 过重，尤其 arithmetic：
    - linear original: `ELAPSED=234.956`
    - arithmetic original: `ELAPSED=732.950`
  - 因此本轮没有降级目标，而是改成更 lean 的 `--maintext-only` repeatability 路线：保留主文 controller 集合，剪掉 appendix 级 factorized predicted-state sweep。
- Code changes:
  - `triver/factorized/week2.py`
    - `run_factorized_cv_with_samples(...)` 新增 `predicted_baselines` 参数，支持只评估指定 predicted-state baseline。
  - `scripts/run_week2_budget_eval.py`
    - 新增 `--maintext-only`，只跑主文 controller 集合。
  - `scripts/aggregate_week2_maintext_repeatability.py`
    - 新增 within-domain repeatability 聚合脚本，输出：
      - `within_domain_repeatability_per_run.csv`
      - `within_domain_repeatability_summary.csv`
      - `within_domain_repeatability_best_by_run.csv`
      - `within_domain_repeatability_win_counts.csv`
      - `within_domain_repeatability_summary.json`
- Verification:

```bash
PYTHONPATH=. python -m compileall \
  scripts/run_week2_budget_eval.py \
  scripts/aggregate_week2_maintext_repeatability.py \
  triver/factorized/week2.py
```

- Representative rerun commands:

```bash
PYTHONPATH=. python scripts/run_week2_budget_eval.py \
  --data-dir outputs/week2_linear_8b_data_v4_100s_seed31 \
  --embedding-npz outputs/week2_linear_8b_data_v4_100s_seed31/prefix_embeddings_last.npz \
  --output-dir outputs/week2_linear_8b_budget_eval_100s_seed31_repeat_v1 \
  --selected-predicted-baseline factorized_predicted_state_selected \
  --maintext-only

PYTHONPATH=. python scripts/run_week2_budget_eval.py \
  --data-dir outputs/week2_arithmetic_8b_data_v3_100s_seed31 \
  --embedding-npz outputs/week2_arithmetic_8b_data_v3_100s_seed31/prefix_embeddings_last.npz \
  --output-dir outputs/week2_arithmetic_8b_budget_eval_100s_seed31_repeat_v1 \
  --selected-predicted-baseline factorized_predicted_state_selected \
  --maintext-only
```

- Aggregate command:

```bash
PYTHONPATH=. python scripts/aggregate_week2_maintext_repeatability.py \
  --run original=outputs/week2_linear_8b_budget_eval_100s_v1 \
  --run original=outputs/week2_arithmetic_8b_budget_eval_100s_v1 \
  --run seed31=outputs/week2_linear_8b_budget_eval_100s_seed31_repeat_v1 \
  --run seed31=outputs/week2_arithmetic_8b_budget_eval_100s_seed31_repeat_v1 \
  --run seed41=outputs/week2_linear_8b_budget_eval_100s_seed41_repeat_v1 \
  --run seed41=outputs/week2_arithmetic_8b_budget_eval_100s_seed41_repeat_v1 \
  --run seed53=outputs/week2_linear_8b_budget_eval_100s_seed53_repeat_v1 \
  --run seed53=outputs/week2_arithmetic_8b_budget_eval_100s_seed53_repeat_v1 \
  --output-dir outputs/week2_maintext_repeatability_v1
```

- Output dirs:
  - `outputs/week2_linear_8b_budget_eval_100s_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_100s_v1/`
  - `outputs/week2_linear_8b_budget_eval_100s_seed31_repeat_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_100s_seed31_repeat_v1/`
  - `outputs/week2_linear_8b_budget_eval_100s_seed41_repeat_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_100s_seed41_repeat_v1/`
  - `outputs/week2_linear_8b_budget_eval_100s_seed53_repeat_v1/`
  - `outputs/week2_arithmetic_8b_budget_eval_100s_seed53_repeat_v1/`
  - `outputs/week2_maintext_repeatability_v1/`

- Runtime notes:
  - lean reroute 仍未消除 arithmetic 的主瓶颈，但 representative 4-run batch 已完整跑通：
    - linear:
      - `seed31 = 221.444s`
      - `seed41 = 168.496s`
      - `seed53 = 226.657s`
    - arithmetic:
      - `seed31 = 641.823s`
      - `seed41 = 489.702s`
      - `seed53 = 733.181s`
  - 这进一步确认：within-domain main-text repeatability 已可完成，但 arithmetic `100-sample` factorized CV 仍是当前 paper-closeout 阶段的 wall-clock 主瓶颈。

- Main summary (`within_domain_repeatability_summary.csv`):
  - arithmetic:
    - `direct_policy`: regret `0.1191 +/- 0.0268`, accuracy `0.8645`
    - `learned_1d_linear`: regret `0.1218 +/- 0.0330`, accuracy `0.8620`
    - `ordered_scalar_mu`: regret `0.1357 +/- 0.0288`, accuracy `0.8387`
    - `factorized_exact_state`: regret `0.1402 +/- 0.0193`, accuracy `0.8215`, calibration rho `0.7129`
    - `factorized_predicted_state_selected`: regret `0.3226 +/- 0.0522`, accuracy `0.6130`, revision harm `0.0296`
  - linear:
    - `learned_1d_linear`: regret `0.0624 +/- 0.0197`, accuracy `0.9385`
    - `direct_policy`: regret `0.0653 +/- 0.0207`, accuracy `0.9360`
    - `factorized_exact_state`: regret `0.0662 +/- 0.0171`, accuracy `0.8967`, calibration rho `0.8499`
    - `factorized_predicted_state_selected`: regret `0.1264 +/- 0.0263`, accuracy `0.7751`, revision harm `0.1115`
    - `ordered_scalar_mu`: regret `0.1448 +/- 0.0459`, accuracy `0.8643`

- Best-by-run / win-count summary:
  - arithmetic:
    - `direct_policy` wins `2/4`
    - `learned_1d_linear` wins `2/4`
    - 没有任何 run 由 `ordered_scalar_mu` 或 factorized controller 取胜
  - linear:
    - `direct_policy` wins `2/4`
    - `factorized_exact_state` wins `1/4`
    - `learned_1d_linear` wins `1/4`
    - `ordered_scalar_mu` / `factorized_predicted_state_selected` 为 `0/4`

- Interpretation:
  - repeatability v1 强化了 deployment-gap 主张，而不是弱化它：
    - `factorized_predicted_state_selected` 在两个域里都持续明显差于 `factorized_exact_state`
    - 它在两个域里都带来更差 calibration，并且在 linear 上保留最高的 revision harm (`0.1115`)
  - 但它也强迫主文 controller 排名写得更保守：
    - linear 域上，最稳的说法不再是“某个单一 controller 明显统治”，而是：
      - `ordered_scalar_mu` 稳定最差；
      - `learned_1d_linear` / `direct_policy` / `factorized_exact_state` 构成一个更强的前列 cluster；
      - `factorized_exact_state` 仍在 calibration 上最强。
    - arithmetic 域上，`100-sample` repeatability 下 `direct_policy` 与 `learned_1d_linear` 已经系统性优于 `ordered_scalar_mu`；因此 paper 不该再把 arithmetic 简单写成“scalar-best” 域，而应改写成：
      - arithmetic 仍不支持 universal scalar insufficiency；
      - 但 stronger controllers 在更大数据 / repeatability setting 下可以超过简单 scalar rule。
  - 这使 paper strongest claim 进一步收紧为：
    - benchmark + ordered-scalar insufficiency / non-universality 的机制结论是稳的；
    - deployable factorization 的主要缺口仍是 state identification / noisy deployment；
    - controller-family ranking 必须按 domain 和 repeatability setting 报告，不能再引用早期 single-run frontier 做总论断。

- Paper-closeout consequence:
  - minimal within-domain repeatability check 已完成，主文 now has:
    - budget-axis
    - revision harm
    - compute value calibration
    - within-domain repeatability
  - 下一个最高优先级不再是新实验，而是：
    - 主图 / 主表 / appendix 组装
    - claim wording 收紧

### Entry: State-identification phase 1 (`high-determinacy` vs `pairwise preference`)

- Status: MIXED_SIGNAL
- Goal: 先钉死 predicted-state 部署差距里有多少来自 target noise，有多少更像 state identification 本身。
- Scope:
  - 只沿当前 paper frozen predicted-state row 推进
  - 不换 state-head family，不扩 value-head sweep
  - 先做两条诊断线：
    - `high-determinacy only`
    - `pairwise preference`
- Scripts:
  - `scripts/run_state_identification_phase1.py`
  - `scripts/aggregate_state_identification_phase1.py`
- Code change:
  - `triver/factorized/week2.py`
  - 新增 predicted-state value training filter:
    - `predicted_train_filter_mode = {all, high_determinacy}`
    - `high_det_gap_quantile`
- Verification:

```bash
PYTHONPATH=. python -m compileall \
  scripts/run_state_identification_phase1.py \
  scripts/aggregate_state_identification_phase1.py \
  triver/factorized/week2.py
```

- Repro commands:

```bash
PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_baseline_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_pairwise_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_baseline_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_pairwise_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit

PYTHONPATH=. python scripts/aggregate_state_identification_phase1.py \
  --run-dir outputs/week2_stateid_linear_baseline_v1 \
  --run-dir outputs/week2_stateid_linear_highdet_v1 \
  --run-dir outputs/week2_stateid_linear_pairwise_v1 \
  --run-dir outputs/week2_stateid_arithmetic_baseline_v1 \
  --run-dir outputs/week2_stateid_arithmetic_highdet_v1 \
  --run-dir outputs/week2_stateid_arithmetic_pairwise_v1 \
  --output-dir outputs/week2_state_identification_phase1_v1
```

- Output dirs:
  - `outputs/week2_stateid_linear_baseline_v1/`
  - `outputs/week2_stateid_linear_highdet_v1/`
  - `outputs/week2_stateid_linear_pairwise_v1/`
  - `outputs/week2_stateid_arithmetic_baseline_v1/`
  - `outputs/week2_stateid_arithmetic_highdet_v1/`
  - `outputs/week2_stateid_arithmetic_pairwise_v1/`
  - `outputs/week2_state_identification_phase1_v1/`

- Main summary (`overall_by_domain.csv`):
  - linear:
    - baseline selected predicted-state (`ridge`, `all`): regret `0.3709`, accuracy `0.5349`
    - `high-determinacy` (`ridge`, top-half gap): regret `0.3933`, accuracy `0.5814`
    - `pairwise preference` (`pairwise_logit`): regret `0.3244`, accuracy `0.6279`
  - arithmetic:
    - baseline selected predicted-state (`ridge`, `all`): regret `0.5047`, accuracy `0.4340`
    - `high-determinacy` (`ridge`, top-half gap): regret `0.4126`, accuracy `0.5283`
    - `pairwise preference` (`pairwise_logit`): regret `0.4681`, accuracy `0.4906`

- Gap-recovery vs current paper baseline:
  - linear baseline gap:
    - exact-state `0.1356`
    - predicted-state `0.3709`
    - gap `0.2353`
  - linear:
    - `high-determinacy`: worse than baseline (`-0.0223` regret; `-9.5%` gap recovery)
    - `pairwise`: improves by `0.0465` regret (`19.8%` gap recovery)
  - arithmetic baseline gap:
    - exact-state `0.2153`
    - predicted-state `0.5047`
    - gap `0.2894`
  - arithmetic:
    - `high-determinacy`: improves by `0.0921` regret (`31.8%` gap recovery)
    - `pairwise`: improves by `0.0366` regret (`12.6%` gap recovery)

- Revision harm (`revision_harm_by_domain.csv`):
  - linear:
    - baseline ridge: `0.0465`
    - `high-determinacy`: `0.0000`
    - `pairwise`: `0.0000`
  - arithmetic:
    - baseline ridge: `0.0189`
    - `high-determinacy`: `0.0000`
    - `pairwise`: `0.0000`

- Compute-value calibration (`compute_value_calibration_by_domain.csv`):
  - linear:
    - baseline ridge: `rho = 0.1280`, `rmse = 0.9067`
    - `high-determinacy`: `rho = 0.1365`, `rmse = 1.0645`
    - `pairwise`: `rho = 0.2111`, `rmse = 1.0534`
  - arithmetic:
    - baseline ridge: `rho = -0.0307`, `rmse = 1.0994`
    - `high-determinacy`: `rho = -0.1458`, `rmse = 1.3519`
    - `pairwise`: `rho = 0.1054`, `rmse = 1.1436`

- Interpretation:
  - target noise is real, but it is not the whole story
  - arithmetic:
    - stricter high-determinacy filtering gives the strongest regret gain (`31.8%` baseline-gap recovery)
    - this points to label ambiguity / MC noise as a live issue on this domain
  - linear:
    - high-determinacy filtering does not help regret
    - pairwise preference gives the strongest deployable improvement (`19.8%` baseline-gap recovery)
    - this points to target formulation mismatch rather than simple ambiguity filtering
  - both domains:
    - revision harm collapses to `0.0` under both rescue variants
    - but neither rescue line closes a majority of the deployment gap across both domains
  - current read:
    - label-side cleanup matters
    - but state identification remains the main bottleneck, because the gains are partial, domain-dependent, and far from exact-state

- Next-step consequence:
  - proceed to phase-1 step 3: exact-state teacher distillation
  - do not return to broad value-head search

### Entry: State-identification phase 1 step 3 (`exact-state teacher distillation`)

- Date: 2026-03-16
- Goal: 检查 predicted-state 部署差距能否通过 exact-state teacher imitation 明显回收，从而区分“state estimator 真不行”与“只差更干净 supervision”的边界。
- Scope:
  - 沿 current paper frozen predicted-state row 推进
  - 不引入新 router / 新 value-head family
  - 只做 `OOF exact-state teacher -> predicted-state student`

- Code changes:
  - `triver/factorized/week2.py`
    - 新增 `build_oof_exact_teacher_score_frame(...)`
    - 新增 `build_teacher_distilled_train_variant(...)`
    - `run_factorized_cv_with_samples(...)` 新增 `teacher_distill_mode`
  - `scripts/run_state_identification_phase1.py`
    - 新增 `--teacher-distill-mode {none, exact_oof_scores}`
  - `scripts/aggregate_state_identification_phase1.py`
    - 聚合表新增 `teacher_distill_mode`

- Verification:
```bash
PYTHONPATH=. python -m compileall \
  scripts/run_state_identification_phase1.py \
  scripts/aggregate_state_identification_phase1.py \
  triver/factorized/week2.py
```

- Commands:
```bash
PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_teacher_ridge_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_teacher_pairwise_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_teacher_ridge_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_teacher_pairwise_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/aggregate_state_identification_phase1.py \
  --run-dir outputs/week2_stateid_linear_baseline_v1 \
  --run-dir outputs/week2_stateid_linear_highdet_v1 \
  --run-dir outputs/week2_stateid_linear_pairwise_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_ridge_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_pairwise_v1 \
  --run-dir outputs/week2_stateid_arithmetic_baseline_v1 \
  --run-dir outputs/week2_stateid_arithmetic_highdet_v1 \
  --run-dir outputs/week2_stateid_arithmetic_pairwise_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_ridge_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_pairwise_v1 \
  --output-dir outputs/week2_state_identification_phase2_v1
```

- Output dirs:
  - `outputs/week2_stateid_linear_teacher_ridge_v1/`
  - `outputs/week2_stateid_linear_teacher_pairwise_v1/`
  - `outputs/week2_stateid_arithmetic_teacher_ridge_v1/`
  - `outputs/week2_stateid_arithmetic_teacher_pairwise_v1/`
  - `outputs/week2_state_identification_phase2_v1/`

- Main summary (`overall_by_domain.csv`):
  - linear:
    - baseline ridge: regret `0.3709`
    - `pairwise` label cleanup: `0.3244`
    - `teacher-distill (ridge)`: `0.3295`
    - `teacher-distill (pairwise)`: `0.3807`
  - arithmetic:
    - baseline ridge: regret `0.5047`
    - `high-determinacy` cleanup: `0.4126`
    - `teacher-distill (pairwise)`: `0.4079`
    - `teacher-distill (ridge)`: `0.5498`

- Gap-recovery vs current paper baseline:
  - linear baseline gap:
    - exact-state `0.1356`
    - predicted-state `0.3709`
    - gap `0.2353`
  - linear teacher-distill:
    - ridge: improves by `0.0414` regret (`17.6%` gap recovery)
    - pairwise: worse than baseline
  - arithmetic baseline gap:
    - exact-state `0.2153`
    - predicted-state `0.5047`
    - gap `0.2894`
  - arithmetic teacher-distill:
    - pairwise: improves by `0.0968` regret (`33.4%` gap recovery)
    - ridge: worse than baseline

- Revision harm (`revision_harm_by_domain.csv`):
  - linear:
    - baseline ridge: `0.0465`
    - teacher-distill ridge: `0.0233`
    - teacher-distill pairwise: `0.0000`
  - arithmetic:
    - baseline ridge: `0.0189`
    - teacher-distill ridge: `0.0000`
    - teacher-distill pairwise: `0.0000`

- Compute-value calibration (`compute_value_calibration_by_domain.csv`):
  - linear:
    - baseline ridge: `rho = 0.1280`, `rmse = 0.9067`
    - teacher-distill ridge: `rho = 0.1290`, `rmse = 0.8752`
    - teacher-distill pairwise: `rho = 0.1395`, `rmse = 1.1502`
  - arithmetic:
    - baseline ridge: `rho = -0.0307`, `rmse = 1.0994`
    - teacher-distill pairwise: `rho = 0.0401`, `rmse = 1.1962`
    - teacher-distill ridge: `rho = -0.0902`, `rmse = 1.1117`

- Interpretation:
  - exact-state teacher distillation is a real positive signal, but it is not a universal fix
  - linear:
    - teacher-distill helps only in the `ridge` student, and still trails the simpler `pairwise` cleanup run
  - arithmetic:
    - teacher-distill helps only in the `pairwise` student, and slightly exceeds the `high-determinacy` cleanup run
  - therefore:
    - predicted-state gap is not purely about noisy final labels
    - but the best student target form remains domain-dependent
    - state identification is still the dominant bottleneck, because even the best teacher-distilled student only partially recovers the exact-state gap

- Go / no-go consequence:
  - this is not enough to reopen a strong algorithmic paper claim
  - but it is enough to keep the state-identification follow-up alive
  - if a next-step combo (`best cleanup + teacher`) still fails to stably recover a large additional fraction of the exact-state gap, the algorithm rescue line should stop and remain appendix / follow-up only

### Entry: State-identification phase 1 step 4 (`best cleanup + teacher` combos)

- Date: 2026-03-16
- Goal: 检查“各域当前 best cleanup + exact-state teacher”能否继续稳定回收 deployment gap；若不能，则按 proposal 的 go/no-go 停止算法 rescue。

- Commands:
```bash
PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_teacher_ridge_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5 \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_linear_8b_data_v3/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_linear_8b_data_v2/prefix_hidden_states_last_prompt.npz \
  --output-dir outputs/week2_stateid_linear_teacher_pairwise_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact_plus_oof \
  --domain-tag linear \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5 \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_teacher_ridge_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model ridge \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5 \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/run_state_identification_phase1.py \
  --input-csv outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv \
  --embedding-npz outputs/week2_arithmetic_8b_data_v1/prefix_hidden_states.npz \
  --output-dir outputs/week2_stateid_arithmetic_teacher_pairwise_highdet_v1 \
  --selected-predicted-baseline factorized_predicted_state_train_exact \
  --domain-tag arithmetic \
  --state-mode s_proxy \
  --state-head-model linear \
  --value-head-model pairwise_logit \
  --predicted-train-filter-mode high_determinacy \
  --high-det-gap-quantile 0.5 \
  --teacher-distill-mode exact_oof_scores

PYTHONPATH=. python scripts/aggregate_state_identification_phase1.py \
  --run-dir outputs/week2_stateid_linear_baseline_v1 \
  --run-dir outputs/week2_stateid_linear_highdet_v1 \
  --run-dir outputs/week2_stateid_linear_pairwise_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_ridge_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_pairwise_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_ridge_highdet_v1 \
  --run-dir outputs/week2_stateid_linear_teacher_pairwise_highdet_v1 \
  --run-dir outputs/week2_stateid_arithmetic_baseline_v1 \
  --run-dir outputs/week2_stateid_arithmetic_highdet_v1 \
  --run-dir outputs/week2_stateid_arithmetic_pairwise_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_ridge_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_pairwise_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_ridge_highdet_v1 \
  --run-dir outputs/week2_stateid_arithmetic_teacher_pairwise_highdet_v1 \
  --output-dir outputs/week2_state_identification_phase3_v1
```

- Output dirs:
  - `outputs/week2_stateid_linear_teacher_ridge_highdet_v1/`
  - `outputs/week2_stateid_linear_teacher_pairwise_highdet_v1/`
  - `outputs/week2_stateid_arithmetic_teacher_ridge_highdet_v1/`
  - `outputs/week2_stateid_arithmetic_teacher_pairwise_highdet_v1/`
  - `outputs/week2_state_identification_phase3_v1/`

- Main summary (`overall_by_domain.csv`):
  - linear:
    - best prior rescue: `pairwise cleanup = 0.3244`
    - `teacher-distill (ridge) = 0.3295`
    - `teacher-distill (ridge) + high-determinacy = 0.3444`
    - `teacher-distill (pairwise) + high-determinacy = 0.4274`
  - arithmetic:
    - best prior rescue: `teacher-distill (pairwise) = 0.4079`
    - `high-determinacy cleanup = 0.4126`
    - `teacher-distill (ridge) + high-determinacy = 0.4581`
    - `teacher-distill (pairwise) + high-determinacy = 0.4628`

- Revision harm:
  - all combo runs keep `revision_harm_rate_overall = 0.0`
  - but this no longer distinguishes them from the already-better rescue variants

- Compute-value calibration:
  - combo variants do not produce a compensating calibration win
  - linear:
    - `teacher + high-det ridge`: `rho = 0.0328`, worse than both baseline ridge and teacher-ridge
  - arithmetic:
    - `teacher + high-det pairwise`: `rho = -0.1798`, clearly worse than prior pairwise teacher

- Go / no-go conclusion:
  - combination rescue does **not** stack
  - the best rescue remains domain-specific and single-step:
    - linear: `pairwise cleanup`
    - arithmetic: `pairwise teacher distill`
  - even these best rescues still remain worse than current `learned_1d_linear` baselines on the same domain slice:
    - linear: best rescue `0.3244` vs `learned_1d_linear = 0.2619`
    - arithmetic: best rescue `0.4079` vs `learned_1d_linear = 0.3349`
  - therefore the proposal go/no-go is now negative for the **algorithm-rescue** line:
    - predicted-state rescue did not recover enough of the exact-state gap
    - it did not beat `learned_1d_linear` on either exact-checker domain
    - the paper should remain fixed as benchmark / mechanism / deployment-diagnosis, and further algorithmic rescue should stop unless the task is explicitly reopened as a new follow-up project

## 2026-03-16: API-backed Week-1 oracle generation infrastructure

Implemented an OpenAI-compatible API runner and wired `scripts/run_week1_oracle.py` to support `--backend api` for rollout / revise generation.

### Code changes

- Added `triver/models/api_runner.py`
  - minimal OpenAI-compatible `POST /chat/completions` backend
  - supports `generate(...)` and `count_tokens(...)`
  - uses a local tokenizer path as token-count fallback
- Updated `scripts/run_week1_oracle.py`
  - added `--backend {local,api}`
  - added `--api-model`, `--api-base-url`, `--api-key`, `--api-timeout-sec`
  - added `--tokenizer-path`
  - exposed `--step-max-new-tokens` so API models are not forced into the old 24-token single-step cap
- Updated `README.md`
  - added an API-backed Week-1 example

### Verification

Compile check:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=. python -m compileall scripts/run_week1_oracle.py triver/models/api_runner.py triver/oracle/week1.py
```

Minimal API smoke (using the repo's current API config via env vars):

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 1 \
  --num-rollouts 1 \
  --max-decision-points 1 \
  --total-budget-tokens 32 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --output-dir outputs/week1_api_smoke \
  --skip-plots
```

Smoke outputs:
- `outputs/week1_api_smoke/prefix_oracle_records.csv`
- `outputs/week1_api_smoke/base_traces.json`
- `outputs/week1_api_smoke/summary.json`

Smoke outcome:
- first attempt with the old implicit `step_max_new_tokens=24` produced `0 prefixes` because the API model truncated the first arithmetic reduction
- after exposing `--step-max-new-tokens` and rerunning with `64`, the API backend produced a valid base trace and one prefix record
- resulting smoke summary:
  - `num_prefixes = 1`
  - `oracle_determinacy_rate = 0.0`
  - the record is ambiguous, but the end-to-end API-backed generation path is now confirmed working

Current interpretation:
- API-backed rollout / revise generation is now technically live
- the next issue is no longer backend wiring, but prompt/config tuning and scale
- for API models, `step_max_new_tokens` needs to be treated as a first-class knob

### Small-batch exact-checker API generation (`v1`)

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 4 \
  --num-rollouts 2 \
  --max-decision-points 2 \
  --total-budget-tokens 48 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_arithmetic_v1 \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 4 \
  --num-rollouts 2 \
  --max-decision-points 2 \
  --total-budget-tokens 48 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_linear_v1 \
  --skip-plots
```

Outputs:
- `outputs/week1_api_arithmetic_v1/`
- `outputs/week1_api_linear_v1/`

Results:
- arithmetic:
  - `num_prefixes = 10`
  - `oracle_determinacy_rate = 0.20`
  - `crossing_mass_all = 0.80`
  - `crossing_mass_high_determinacy = 0.00`
  - `invalid_prefix_rate = 0.50`
  - `mean_action_gap = 0.2076`
  - action mix: `continue=4`, `revise_1=2`, `abstain=4`
  - ambiguity is still high: `8/10`
- linear_equations:
  - `num_prefixes = 12`
  - `oracle_determinacy_rate = 0.50`
  - `crossing_mass_all = 0.00`
  - `crossing_mass_high_determinacy = 0.00`
  - `invalid_prefix_rate = 0.50`
  - `mean_action_gap = 0.4933`
  - action mix: `continue=6`, `revise_1=6`
  - ambiguity: `6/12`

Interpretation:
- the API-backed exact-checker pipeline now works on both existing domains
- this is already enough to start generating benchmark data without local HF inference
- the immediate bottleneck is no longer backend integration, but benchmark quality under the API model:
  - arithmetic currently shows heavy ambiguity and weak high-determinacy coverage
  - linear is cleaner on determinacy, but currently shows no crossing at this small scale
- the next tuning target should be benchmark quality rather than infrastructure:
  - more samples
  - more rollouts
  - possibly higher total budget
  - prompt/backend-specific generation tuning

### Rollout-count tuning (`v2r`): 2 -> 4 rollouts

Goal: test whether simply increasing Monte Carlo rollouts improves API-benchmark quality on the current exact-checker prompts.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 4 \
  --num-rollouts 4 \
  --max-decision-points 2 \
  --total-budget-tokens 48 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_arithmetic_v2r \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 4 \
  --num-rollouts 4 \
  --max-decision-points 2 \
  --total-budget-tokens 48 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_linear_v2r \
  --skip-plots
```

Outputs:
- `outputs/week1_api_arithmetic_v2r/`
- `outputs/week1_api_linear_v2r/`

Comparison against `v1` (`num_rollouts=2`):

- arithmetic:
  - `num_prefixes`: `10 -> 12`
  - `oracle_determinacy_rate`: `0.20 -> 0.1667`
  - `crossing_mass_all`: `0.80 -> 0.75`
  - `mean_action_gap`: `0.2076 -> 0.2495`
  - ambiguity: `8/10 -> 10/12`
  - interpretation: more rollouts slightly increase the mean gap, but do **not** improve determinacy or ambiguity in a meaningful way

- linear_equations:
  - `num_prefixes`: `12 -> 12`
  - `oracle_determinacy_rate`: `0.50 -> 0.50`
  - `crossing_mass_all`: `0.00 -> 0.00`
  - `mean_action_gap`: `0.4933 -> 0.4943`
  - ambiguity: unchanged at `6/12`
  - interpretation: more rollouts are essentially neutral on this prompt/domain combination

Conclusion:
- for the current API exact-checker setup, simply increasing `num_rollouts` from `2` to `4` is **not** the next high-leverage tuning knob
- the next iteration should focus on:
  - better sample coverage
  - prompt / action-construction quality
  - possibly larger total budgets or different decision-point selection
  - not just more Monte Carlo replications

### Coverage/budget tuning (`v3cov`): more samples, more decision points, longer budget

Goal: test whether benchmark quality improves more from broader prefix coverage than from extra Monte Carlo replications.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_arithmetic_v3cov \
  --skip-plots

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_api_linear_v3cov \
  --skip-plots
```

Outputs:
- `outputs/week1_api_arithmetic_v3cov/`
- `outputs/week1_api_linear_v3cov/`

Comparison against `v1` and `v2r`:

- arithmetic:
  - `num_prefixes`: `10 -> 12 -> 28`
  - `oracle_determinacy_rate`: `0.20 -> 0.1667 -> 0.2857`
  - `crossing_mass_all`: `0.80 -> 0.75 -> 0.7857`
  - `crossing_mass_high_determinacy`: `0.00 -> 0.00 -> 0.875`
  - `mean_action_gap`: `0.2076 -> 0.2495 -> 0.2414`
  - action mix:
    - `v1`: `continue=4, revise_1=2, abstain=4`
    - `v3cov`: `continue=10, revise_1=9, abstain=9`
  - interpretation:
    - coverage/budget tuning materially improves benchmark usefulness
    - high-determinacy crossing is now non-trivial instead of collapsing to zero

- linear_equations:
  - `num_prefixes`: `12 -> 12 -> 24`
  - `oracle_determinacy_rate`: `0.50 -> 0.50 -> 0.4583`
  - `crossing_mass_all`: `0.00 -> 0.00 -> 0.5833`
  - `crossing_mass_high_determinacy`: `0.00 -> 0.00 -> 1.00`
  - `mean_action_gap`: `0.4933 -> 0.4943 -> 0.4765`
  - action mix:
    - `v1`: `continue=6, revise_1=6`
    - `v3cov`: `continue=9, revise_1=11, abstain=4`
  - interpretation:
    - broader coverage finally exposes non-trivial crossing
    - the domain is not intrinsically “zero-crossing”; the earlier issue was benchmark coverage

Takeaway:
- this is the first clearly positive API tuning result
- for the current API setup, coverage/budget is a much higher-leverage knob than `num_rollouts`
- the next tuning target should be prompt / action-construction quality, with rollout count kept modest

### Prompt/action tuning (`v4strict`): opt-in stricter API prompts

Goal: test whether stronger formatting and one-step legality instructions improve benchmark quality beyond the `v3cov` coverage/budget setting.

Implementation:
- added `--prompt-style {default,api_strict}` to [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py)
- threaded `prompt_style` through [triver/oracle/week1.py](/cephfs/luyanzhen/apg/triver/triver/oracle/week1.py)
- added opt-in strict prompts to:
  - [triver/envs/arithmetic.py](/cephfs/luyanzhen/apg/triver/triver/envs/arithmetic.py)
  - [triver/envs/linear_equations.py](/cephfs/luyanzhen/apg/triver/triver/envs/linear_equations.py)
- made plotting best-effort: if `matplotlib` is absent, [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py) now skips plots after writing summary/artifacts

Commands (same as `v3cov`, only changing prompt style):

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_strict \
  --output-dir outputs/week1_api_arithmetic_v4strict

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_strict \
  --output-dir outputs/week1_api_linear_v4strict
```

Outputs:
- `outputs/week1_api_arithmetic_v4strict/`
- `outputs/week1_api_linear_v4strict/`
- paired comparison: [outputs/week1_api_prompt_style_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_api_prompt_style_comparison.csv)

Comparison against `v3cov`:

- arithmetic:
  - `num_prefixes`: `28 -> 18`
  - `oracle_determinacy_rate`: `0.2857 -> 0.3333`
  - `crossing_mass_all`: `0.7857 -> 0.6667`
  - `crossing_mass_high_determinacy`: `0.875 -> 0.0000`
  - `mean_action_gap`: `0.2414 -> 0.3626`
  - ambiguity: `20/28 -> 12/18`
  - interpretation:
    - stricter prompts increase per-prefix gap and slightly improve determinacy
    - but they reduce coverage and collapse high-determinacy crossing

- linear_equations:
  - `num_prefixes`: `24 -> 16`
  - `oracle_determinacy_rate`: `0.4583 -> 0.5000`
  - `crossing_mass_all`: `0.5833 -> 0.0000`
  - `crossing_mass_high_determinacy`: `1.0000 -> 0.0000`
  - `mean_action_gap`: `0.4765 -> 0.4954`
  - ambiguity: `13/24 -> 8/16`
  - interpretation:
    - stricter prompts make traces cleaner and slightly less ambiguous
    - but they eliminate the crossing signal that made `v3cov` mechanism-useful

Conclusion:
- `api_strict` is a mixed/no-go prompt variant for the current benchmark objective
- it improves cleanliness and gaps, but at the cost of coverage and crossing
- the default prompt with broader coverage remains the better benchmark-construction setting
- next tuning should target action construction / revise recoverability, not stricter formatting alone

### Action-construction tuning (`v5revise`): revise-focused rollback/replace prompts

Goal: test whether a revise-focused action construction can improve benchmark quality without the coverage/crossing collapse seen in `api_strict`.

Implementation:
- extended [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py) with `--prompt-style api_revise_focus`
- added revise-only prompt variants in:
  - [triver/envs/arithmetic.py](/cephfs/luyanzhen/apg/triver/triver/envs/arithmetic.py)
  - [triver/envs/linear_equations.py](/cephfs/luyanzhen/apg/triver/triver/envs/linear_equations.py)
- `continue` remains on the default prompt; only `revise_1` gets stronger rollback / replacement semantics

Commands (same as `v3cov`, only changing prompt style):

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_focus \
  --output-dir outputs/week1_api_arithmetic_v5revise

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_focus \
  --output-dir outputs/week1_api_linear_v5revise
```

Outputs:
- `outputs/week1_api_arithmetic_v5revise/`
- `outputs/week1_api_linear_v5revise/`
- paired comparison: [outputs/week1_api_revise_action_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_api_revise_action_comparison.csv)

Comparison against `v3cov`:

- arithmetic:
  - `num_prefixes`: `28 -> 28`
  - `oracle_determinacy_rate`: `0.2857 -> 0.3571`
  - `crossing_mass_all`: `0.7857 -> 0.7857`
  - `crossing_mass_high_determinacy`: `0.875 -> 0.9000`
  - `mean_action_gap`: `0.2414 -> 0.2608`
  - ambiguity: `20/28 -> 18/28`
  - `mean revise_gain`: `0.2080 -> 0.2369`
  - interpretation:
    - benchmark quality improves without losing coverage
    - revise utility becomes slightly stronger on average
    - invalid-prefix rate rises (`0.50 -> 0.6071`), so the gain is not uniformly “clean”

- linear_equations:
  - `num_prefixes`: `24 -> 24`
  - `oracle_determinacy_rate`: `0.4583 -> 0.5417`
  - `crossing_mass_all`: `0.5833 -> 0.5833`
  - `crossing_mass_high_determinacy`: `1.0000 -> 1.0000`
  - `mean_action_gap`: `0.4765 -> 0.5078`
  - ambiguity: `13/24 -> 11/24`
  - `mean revise_gain`: `0.4482 -> 0.4379`
  - interpretation:
    - this is a clear benchmark-quality improvement
    - revise-focused prompts preserve crossing while improving determinacy and gap
    - direct revise utility does not increase, so the effect is more “cleaner control signal” than “bigger revise win”

Conclusion:
- `api_revise_focus` is a positive/passing action-construction variant for the current benchmark objective
- unlike `api_strict`, it preserves coverage and crossing while improving determinacy and ambiguity
- it should be treated as the next default candidate for API exact-checker data generation
- the next step should continue along action construction / revise recoverability, not go back to stricter formatting

### Candidate-guided revise tuning (`v6cand`): explicit valid-next-step candidates

Goal: test whether exposing exact-checker one-step candidates directly inside the `revise_1` prompt improves recoverability beyond `api_revise_focus`.

Implementation:
- extended [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py) with `--prompt-style api_revise_candidates`
- for `revise_1`, the prompt now lists exact valid one-step candidates from the rollback state:
  - [triver/envs/arithmetic.py](/cephfs/luyanzhen/apg/triver/triver/envs/arithmetic.py)
  - [triver/envs/linear_equations.py](/cephfs/luyanzhen/apg/triver/triver/envs/linear_equations.py)
- `continue` remains unchanged

Commands (same as `v3cov`, only changing prompt style):

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_candidates \
  --output-dir outputs/week1_api_arithmetic_v6cand

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_candidates \
  --output-dir outputs/week1_api_linear_v6cand
```

Outputs:
- `outputs/week1_api_arithmetic_v6cand/`
- `outputs/week1_api_linear_v6cand/`
- paired comparison: [outputs/week1_api_revise_candidate_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_api_revise_candidate_comparison.csv)

Comparison against `v5revise`:

- arithmetic:
  - `num_prefixes`: `28 -> 32`
  - `oracle_determinacy_rate`: `0.3571 -> 0.2812`
  - `crossing_mass_all`: `0.7857 -> 0.7812`
  - `crossing_mass_high_determinacy`: `0.9000 -> 0.8889`
  - `mean_action_gap`: `0.2608 -> 0.2314`
  - `mean revise_gain`: `0.2369 -> 0.2259`
  - action mix shifts toward more `revise_1` / `abstain`

- linear_equations:
  - `num_prefixes`: `24 -> 32`
  - `oracle_determinacy_rate`: `0.5417 -> 0.5312`
  - `crossing_mass_all`: `0.5833 -> 0.6562`
  - `crossing_mass_high_determinacy`: `1.0000 -> 1.0000`
  - `mean_action_gap`: `0.5078 -> 0.4614`
  - `invalid_prefix_rate`: `0.5833 -> 0.6562`
  - `mean revise_gain`: `0.4379 -> 0.4387`
  - action mix shifts toward more `revise_1` / `abstain`

Conclusion:
- `api_revise_candidates` is mixed/no-go as the next default
- it increases coverage and pushes more mass toward revise/abstain
- but it does not improve determinacy or gap over `api_revise_focus`, and it makes the action prior more intervention-heavy
- current default candidate should remain `v3cov + api_revise_focus`

### Conditional revise tuning (`v7ifocus`): stronger revise semantics only on invalid prefixes

Goal: recover the positive signal from `api_revise_focus` without its side effects on clean/base prefixes.

Implementation:
- extended [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py) with `--prompt-style api_revise_invalid_focus`
- in both envs, stronger revise semantics now activate only when the current prefix is already invalid:
  - [triver/envs/arithmetic.py](/cephfs/luyanzhen/apg/triver/triver/envs/arithmetic.py)
  - [triver/envs/linear_equations.py](/cephfs/luyanzhen/apg/triver/triver/envs/linear_equations.py)
- clean prefixes still use the default `revise_1` prompt

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_invalid_focus \
  --output-dir outputs/week1_api_arithmetic_v7ifocus

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_invalid_focus \
  --output-dir outputs/week1_api_linear_v7ifocus
```

Outputs:
- `outputs/week1_api_arithmetic_v7ifocus/`
- `outputs/week1_api_linear_v7ifocus/`
- paired comparison: [outputs/week1_api_revise_conditional_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_api_revise_conditional_comparison.csv)

Comparison against `v5revise`:

- arithmetic:
  - `num_prefixes`: `28 -> 32`
  - `oracle_determinacy_rate`: `0.3571 -> 0.3125`
  - `crossing_mass_all`: `0.7857 -> 0.7812`
  - `crossing_mass_high_determinacy`: `0.9000 -> 0.9000`
  - `invalid_prefix_rate`: `0.6071 -> 0.5000`
  - `mean_action_gap`: `0.2608 -> 0.2453`
  - `mean revise_gain`: `0.2369 -> 0.2652`
  - interpretation:
    - it gives up a bit of determinacy/gap to recover a much cleaner invalid-prefix profile
    - revise utility improves further on average

- linear_equations:
  - `num_prefixes`: `24 -> 24`
  - `oracle_determinacy_rate`: `0.5417 -> 0.5000`
  - `crossing_mass_all`: `0.5833 -> 0.5833`
  - `crossing_mass_high_determinacy`: `1.0000 -> 1.0000`
  - `invalid_prefix_rate`: unchanged at `0.5833`
  - `mean_action_gap`: `0.5078 -> 0.4877`
  - `mean revise_gain`: `0.4379 -> 0.4095`
  - interpretation:
    - it is weaker than `v5revise` on the clean linear setting
    - but it remains better than `v3cov` on determinacy/gap while avoiding the heavier action-prior shift of `v6cand`

Conclusion:
- `api_revise_invalid_focus` is the most balanced default candidate so far
- compared with `v5revise`, it is slightly weaker on linear but cleaner and more stable on arithmetic
- compared with `v6cand`, it avoids the candidate-guided action-prior distortion
- current default candidate should update to `v3cov + api_revise_invalid_focus`

### Recoverable-style tuning (`v8local`): perturb the newly introduced token only

- Status: MIXED_SIGNAL / NO_GO
- Change:
  - extended [scripts/run_week1_oracle.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_oracle.py) with `--recoverable-style {default, local_changed_token}`
  - added shared helper [triver/envs/common.py](/cephfs/luyanzhen/apg/triver/triver/envs/common.py) to perturb the integer token that is newly introduced by the current step
  - threaded the new recoverable-style through:
    - [triver/envs/arithmetic.py](/cephfs/luyanzhen/apg/triver/triver/envs/arithmetic.py)
    - [triver/envs/linear_equations.py](/cephfs/luyanzhen/apg/triver/triver/envs/linear_equations.py)
- Goal:
  - keep the current `api_revise_invalid_focus` prompt semantics fixed
  - change only the recoverable-prefix construction, to test whether more local corruptions improve revise recoverability without changing action priors

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export TRIVER_API_BASE_URL="..."
export TRIVER_API_MODEL="..."
export TRIVER_API_KEY="..."

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env arithmetic \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --top-p 0.9 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_invalid_focus \
  --recoverable-style local_changed_token \
  --output-dir outputs/week1_api_arithmetic_v8local

PYTHONPATH=. python scripts/run_week1_oracle.py \
  --backend api \
  --env linear_equations \
  --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B \
  --num-samples 8 \
  --num-rollouts 2 \
  --max-decision-points 3 \
  --total-budget-tokens 64 \
  --step-max-new-tokens 64 \
  --temperature 0 \
  --top-p 0.9 \
  --api-timeout-sec 30 \
  --augment-revise-prefixes \
  --prompt-style api_revise_invalid_focus \
  --recoverable-style local_changed_token \
  --output-dir outputs/week1_api_linear_v8local
```

Outputs:
- `outputs/week1_api_arithmetic_v8local/`
- `outputs/week1_api_linear_v8local/`
- comparison artifact: [outputs/week1_api_recoverable_style_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_api_recoverable_style_comparison.csv)

Comparison against current default candidate `v7ifocus`:

- arithmetic:
  - `num_prefixes`: `32 -> 28`
  - `oracle_determinacy_rate`: `0.3125 -> 0.3214`
  - `crossing_mass_all`: `0.7812 -> 0.7857`
  - `crossing_mass_high_determinacy`: `0.9000 -> 0.8889`
  - `invalid_prefix_rate`: unchanged at `0.5000`
  - `mean_action_gap`: `0.2453 -> 0.2261`
  - `mean revise_gain`: `0.2652 -> 0.2406`
  - interpretation:
    - slightly cleaner on determinacy and ambiguity
    - but clearly weaker on action gap and revise gain

- linear_equations:
  - `num_prefixes`: `24 -> 26`
  - `oracle_determinacy_rate`: unchanged at `0.5000`
  - `crossing_mass_all`: `0.5833 -> 0.6154`
  - `crossing_mass_high_determinacy`: unchanged at `1.0000`
  - `invalid_prefix_rate`: `0.5833 -> 0.6154`
  - `mean_action_gap`: `0.4877 -> 0.4766`
  - `mean revise_gain`: `0.4095 -> 0.4630`
  - interpretation:
    - revise utility improves
    - but invalid-prefix rate rises and action gap does not improve

Conclusion:
- `local_changed_token` is a useful recoverable-prefix ablation, not a new default
- it improves some local diagnostics, especially linear revise gain, but does not cleanly dominate `api_revise_invalid_focus`
- current default candidate remains `v3cov + api_revise_invalid_focus` with `recoverable-style=default`

### Judge-based supporting benchmark smoke (`gsm8k`)

- Status: PIPELINE_READY / LOW-DETERMINACY_SMOKE
- Goal:
  - open a broader benchmark tier beyond the current exact-checker toy domains
  - keep the exact-checker line as the main benchmark, while adding a `judge_based_supporting` pipeline for external-validity probes
- New files:
  - [scripts/run_week1_judged_benchmark.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_judged_benchmark.py)
  - [triver/oracle/judged_benchmark.py](/cephfs/luyanzhen/apg/triver/triver/oracle/judged_benchmark.py)
- Protocol:
  - dataset: `gsm8k`
  - base trace generation: API model, one short step per line, end with `Final answer: ...`
  - actions: `{continue, revise_1, abstain}`
  - `revise_1`: rollback one line, then continue from the rollback prefix
  - judge: API model returns
    - prefix risk `q_t`
    - final-answer correctness
  - benchmark tier is explicitly `judge_based_supporting`, not exact-checker

Command:

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
  --top-p 0.9 \
  --augment-revise-prefixes \
  --output-dir outputs/week1_gsm8k_judged_smoke_v1
```

Outputs:
- [outputs/week1_gsm8k_judged_smoke_v1/base_traces.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v1/base_traces.json)
- [outputs/week1_gsm8k_judged_smoke_v1/prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v1/prefix_oracle_records.csv)
- [outputs/week1_gsm8k_judged_smoke_v1/summary.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v1/summary.json)

Smoke summary:
- `num_prefixes = 8`
- `oracle_determinacy_rate = 0.1250`
- `crossing_mass_all = 0.8750`
- `crossing_mass_high_determinacy = 0.0000`
- `invalid_prefix_rate = 0.1250`
- `mean_action_gap = 0.1094`
- action mix:
  - `continue = 5`
  - `revise_1 = 3`
  - `abstain = 0`
- ambiguity:
  - `7/8` prefixes are ambiguous

Interpretation:
- the API-judge pipeline itself is now live: broader dataset -> API generation -> prefix extraction -> action rollout -> API judge -> prefix-level oracle records
- but this first smoke is clearly a weak-evidence tier:
  - determinacy is low
  - action gaps are small
  - high-determinacy crossing is still `0`
- so this supporting benchmark should be used as an external-validity layer, not mixed with the exact-checker main evidence

Engineering note:
- `datasets` is available in system Python but not in the `infer` conda env
- `transformers` is available in `infer` but not guaranteed in system Python
- the judged benchmark script was updated so tokenizer usage is optional; when `transformers` is absent it falls back to coarse token counting

### Judge stability probe (`gsm8k`, `dual` ensemble)

- Status: POSITIVE_SIGNAL / STILL_LOW_EVIDENCE
- Goal:
  - improve judged-benchmark stability without changing dataset, sample count, rollout count, or action protocol
  - test whether a tiny judge ensemble is enough to lift determinacy on the broad supporting benchmark
- Change:
  - extended [triver/oracle/judged_benchmark.py](/cephfs/luyanzhen/apg/triver/triver/oracle/judged_benchmark.py) with `JudgeConfig.ensemble_mode`
  - added `--judge-ensemble-mode {single, dual}` to [scripts/run_week1_judged_benchmark.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_judged_benchmark.py)
  - `dual` mode now aggregates:
    - two prefix-risk prompts (`strict_process`, `revision_need`)
    - two correctness prompts (`strict_grade`, `extract_then_compare`)

Command:

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
  --top-p 0.9 \
  --augment-revise-prefixes \
  --judge-ensemble-mode dual \
  --output-dir outputs/week1_gsm8k_judged_smoke_v2dual
```

Outputs:
- [outputs/week1_gsm8k_judged_smoke_v2dual/summary.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v2dual/summary.json)
- [outputs/week1_gsm8k_judged_smoke_v2dual/prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v2dual/prefix_oracle_records.csv)
- comparison artifact: [outputs/week1_gsm8k_judge_stability_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judge_stability_comparison.csv)

Comparison against `v1_single`:
- `num_prefixes`: `8 -> 9`
- `oracle_determinacy_rate`: `0.1250 -> 0.2222`
- `crossing_mass_all`: `0.8750 -> 0.8889`
- `crossing_mass_high_determinacy`: unchanged at `0.0000`
- `invalid_prefix_rate`: `0.1250 -> 0.1111`
- `mean_action_gap`: `0.1094 -> 0.1339`
- action mix:
  - `continue`: `5 -> 5`
  - `revise_1`: `3 -> 4`
- ambiguity:
  - non-ambiguous prefixes: `1 -> 2`

Interpretation:
- this is a real judge-stability improvement:
  - determinacy nearly doubles
  - action-gap increases
  - invalid-prefix rate falls slightly
- but the judged benchmark is still clearly weak evidence:
  - determinacy remains low
  - `high-determinacy crossing` is still `0`
- so `dual` is a better stability candidate than `single`, but it does not upgrade this benchmark tier beyond supporting evidence

### Broad judged benchmark generation-side probe (`gsm8k`, `compact_final`)

- Status: MIXED / NO_GO
- Goal:
  - test whether the next bottleneck after `dual` judge stability is generation-side trace completion
  - improve `Final answer` termination reliability without changing dataset size, judge protocol, or action set
- Change:
  - extended [triver/oracle/judged_benchmark.py](/cephfs/luyanzhen/apg/triver/triver/oracle/judged_benchmark.py) with `GenerationConfig.style`
  - added `--generation-style {default, compact_final}` to [scripts/run_week1_judged_benchmark.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_judged_benchmark.py)
  - `compact_final` enforces:
    - plain-text traces
    - shorter reasoning chains
    - explicit non-truncated `Final answer: <answer>` termination
  - added base-trace termination statistics to `summary.json`:
    - `base_trace_terminal_rate`
    - `base_trace_nonterminal_count`
    - `base_trace_mean_steps`

Command:

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
  --top-p 0.9 \
  --augment-revise-prefixes \
  --judge-ensemble-mode dual \
  --generation-style compact_final \
  --output-dir outputs/week1_gsm8k_judged_smoke_v3compact
```

Outputs:
- [outputs/week1_gsm8k_judged_smoke_v3compact/summary.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v3compact/summary.json)
- [outputs/week1_gsm8k_judged_smoke_v3compact/base_traces.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v3compact/base_traces.json)
- [outputs/week1_gsm8k_generation_stability_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_generation_stability_comparison.csv)

Comparison against `v2_dual`:
- `num_prefixes`: `9 -> 9`
- `oracle_determinacy_rate`: `0.2222 -> 0.1111`
- `crossing_mass_all`: unchanged at `0.8889`
- `crossing_mass_high_determinacy`: unchanged at `0.0000`
- `invalid_prefix_rate`: `0.1111 -> 0.2222`
- `mean_action_gap`: `0.1339 -> 0.1159`
- `base_trace_terminal_rate`: `0.6667 -> 1.0000`
- `base_trace_nonterminal_count`: `1 -> 0`
- `base_trace_mean_steps`: `7.3333 -> 6.6667`

Interpretation:
- `compact_final` successfully fixes the visible trace-completion issue:
  - all three GSM8K base traces now terminate with `Final answer: ...`
  - traces are shorter and cleaner
- but the benchmark-quality metrics move the wrong way:
  - determinacy falls
  - invalid-prefix rate rises
  - action gaps shrink
- so generation-side completion is a real issue, but “shorter/cleaner traces” is not a free improvement for judged-benchmark quality
- current default for the broad judged benchmark remains:
  - `judge_ensemble_mode=dual`
  - `generation_style=default`

### Broad judged benchmark action-utility probe (`gsm8k`, stronger wrong-penalty)

- Status: NO_GO
- Goal:
  - test whether the remaining low determinacy on the broad judged benchmark is mainly an action-utility separation problem
  - increase `gamma_wrong` while holding `dual` judge and default generation fixed
- Change:
  - reused cached base traces from [outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json) via the new `--base-traces-json` support in [scripts/run_week1_judged_benchmark.py](/cephfs/luyanzhen/apg/triver/scripts/run_week1_judged_benchmark.py)
  - reran the benchmark with `--gamma-wrong 1.0` instead of the default `0.5`

Command:

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
  --top-p 0.9 \
  --augment-revise-prefixes \
  --judge-ensemble-mode dual \
  --generation-style default \
  --gamma-wrong 1.0 \
  --base-traces-json outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json \
  --output-dir outputs/week1_gsm8k_judged_smoke_v4gwrong_replay
```

Outputs:
- [outputs/week1_gsm8k_judged_smoke_v4gwrong_replay/summary.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v4gwrong_replay/summary.json)
- [outputs/week1_gsm8k_judged_smoke_v4gwrong_replay/prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v4gwrong_replay/prefix_oracle_records.csv)
- comparison artifact: [outputs/week1_gsm8k_action_utility_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_action_utility_comparison.csv)

Comparison against `v2_dual` on fixed base traces:
- `num_prefixes`: unchanged at `9`
- `oracle_determinacy_rate`: `0.2222 -> 0.1111`
- `crossing_mass_all`: unchanged at `0.8889`
- `crossing_mass_high_determinacy`: unchanged at `0.0000`
- `invalid_prefix_rate`: unchanged at `0.1111`
- `mean_action_gap`: `0.1339 -> 0.1246`

Interpretation:
- the low-determinacy problem on this broad judged benchmark is not solved by simply increasing the unsafe-wrong penalty
- with generation held fixed, stronger wrong-penalty still reduces determinacy and slightly shrinks the average action gap
- therefore the next lever should not be “heavier utility penalties”; it remains:
  - judge stability
  - ambiguity handling
  - possibly richer action-level utility definitions

Engineering note:
- the first non-replay `gamma_wrong` run at [outputs/week1_gsm8k_judged_smoke_v4gwrong](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v4gwrong) was confounded by fresh API generation variance and is superseded by the replay-backed result above

### Broad judged benchmark consensus-aggregation probe (`gsm8k`, replay)

- Status: POSITIVE_SIGNAL / STILL_LOW_EVIDENCE
- Goal:
  - test whether the remaining low determinacy is partly caused by a too-lenient correctness aggregation rule in `dual`
  - keep the same two correctness prompts, but require consensus instead of `>= 0.5` voting
- Change:
  - extended [triver/oracle/judged_benchmark.py](/cephfs/luyanzhen/apg/triver/triver/oracle/judged_benchmark.py) with `judge_ensemble_mode=dual_consensus`
  - in `dual_consensus`, correctness and `final_answer_present` now require unanimous positive votes from the two existing judge styles
  - reused cached base traces from [outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json) to keep generation fixed

Command:

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
  --top-p 0.9 \
  --augment-revise-prefixes \
  --judge-ensemble-mode dual_consensus \
  --generation-style default \
  --base-traces-json outputs/week1_gsm8k_judged_smoke_v2dual/base_traces.json \
  --output-dir outputs/week1_gsm8k_judged_smoke_v5consensus_replay
```

Outputs:
- [outputs/week1_gsm8k_judged_smoke_v5consensus_replay/summary.json](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v5consensus_replay/summary.json)
- [outputs/week1_gsm8k_judged_smoke_v5consensus_replay/prefix_oracle_records.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judged_smoke_v5consensus_replay/prefix_oracle_records.csv)
- comparison artifact: [outputs/week1_gsm8k_judge_consensus_comparison.csv](/cephfs/luyanzhen/apg/triver/outputs/week1_gsm8k_judge_consensus_comparison.csv)

Comparison against `v2_dual` on fixed base traces:
- `num_prefixes`: unchanged at `9`
- `oracle_determinacy_rate`: unchanged at `0.2222`
- `crossing_mass_all`: `0.8889 -> 0.7778`
- `crossing_mass_high_determinacy`: unchanged at `0.0000`
- `invalid_prefix_rate`: unchanged at `0.1111`
- `mean_action_gap`: `0.1339 -> 0.1879`

Interpretation:
- requiring consensus does not magically solve the evidence-tier problem:
  - determinacy is still low
  - `high-determinacy crossing` remains `0`
- but it is a real stability improvement over plain `dual` on fixed generation:
  - same determinacy
  - larger average action gap
  - lower overall crossing mass
- so `dual_consensus` becomes the current stronger judge-stability candidate for this broad judged benchmark, while the benchmark tier itself remains supporting-only
