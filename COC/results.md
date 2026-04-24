# Results

## Status

当前已完成 phase 0 bootstrap，并产出 dev-slice 级别的 bootstrap 数值结果；但尚未形成 frozen final benchmark 结论。

## Frozen Before Running

- headline claim scope: `object`
- default domains: `math`, `code`
- active families: `substance_flip`, `style_flip`
- deferred family: `reasoning_fluff`
- primary metrics: `COC`, `worst-family miss`, `Hard-Error Recall`
- support metrics: `overall accuracy`, `family fidelity`, `miss overlap`

## Run Log Template

每次进入实验或可复现计算时，追加以下最小字段：

- date
- purpose
- command / script
- inputs
- outputs
- key metrics
- conclusion
- next action

## Bootstrap Entry

### 2026-03-31 phase0-bootstrap

- purpose: 将 proposal 收束为可执行项目骨架
- command / script: 无；本轮以文档与配置冻结为主
- outputs:
  - `docs/phase0_bootstrap.md`
  - `docs/object_gate.md`
  - `docs/family_construction_note.md`
  - `configs/object_gate.yaml`
  - `data/manifests/object_dev_v0_template.yaml`
  - `progress.md`
  - `results.md`
- conclusion: 已具备进入 `Object gate v0` 最小闭环的项目化前提
- next action: 生成 `object-dev-v0` manifest 和 family construction note

### 2026-03-31 model-driven-data-update

- purpose: 将 Object gate 的数据策略改为模型生成与模型审查优先
- command / script: 无；本轮以文档与配置冻结为主
- outputs:
  - `docs/phase0_bootstrap.md`
  - `docs/object_gate.md`
  - `docs/family_construction_note.md`
  - `configs/object_gate.yaml`
  - `data/manifests/object_dev_v0_template.yaml`
  - `progress.md`
- conclusion: family 样本将默认由 generator/reviewer models 生产和审查，verifier 退居 correctness guardrail
- next action: 补最小模型数据协议与首批 seed task

### 2026-03-31 object-gate-bootstrap-run-1

- purpose: 验证 `generator -> reviewer -> manifest` 的最小链路是否可跑通
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_candidates.jsonl --limit 2 --max-new-tokens 320`
- inputs:
  - `data/raw/object_seed_tasks_v0.json`
  - families: `substance_flip`, `style_flip`, `reasoning_fluff`
  - seeds: `math_001`, `math_002`
- outputs:
  - `data/interim/object_dev_v0_candidates.jsonl`
  - `artifacts/object_gate/bootstrap_generation_audit_2026-03-31.md`
- key metrics:
  - total candidates: `6`
  - reviewer decision counts: `pass=5`, `fail=1`
  - by family:
    - `style_flip`: `2/2 pass`
    - `substance_flip`: `1/2 clean enough`, `1/2 drifted`
    - `reasoning_fluff`: `0/2 convincingly clean by manual inspection`, despite reviewer passing both
- conclusion:
  - model-driven construction pipeline is runnable
  - current reviewer is too weak for `reasoning_fluff`
  - do not scale before reviewer/gate tightening
- next action:
  - decouple reviewer from generator
  - retry on code seeds
  - tighten reasoning-fluff acceptance

### 2026-03-31 reviewer-consistency-check

- purpose: 检查 reviewer 的结构化输出是否自洽
- command / script:
  - `python scripts/audit_model_data.py --input-file data/interim/object_dev_v0_candidates.jsonl`
  - `python scripts/audit_model_data.py --input-file data/interim/object_dev_v0_candidates_review8b.jsonl`
- inputs:
  - `data/interim/object_dev_v0_candidates.jsonl`
  - `data/interim/object_dev_v0_candidates_review8b.jsonl`
- outputs:
  - `scripts/audit_model_data.py`
  - `artifacts/object_gate/bootstrap_generation_audit_2026-03-31.md`
- key metrics:
  - 4B reviewer run: `1/6` records flagged for `review_contradiction_valid_but_fail`
  - 8B reviewer run: `3/3` records flagged for `review_contradiction_valid_but_fail`
- conclusion:
  - reviewer quality问题当前表现为 protocol inconsistency，而不只是 model strength
  - reviewer outputs cannot yet be used as final audit labels without consistency filtering
- next action:
  - treat reviewer as proposal generator, not final arbiter
  - add consistency-gated human review for borderline families

### 2026-03-31 api-reviewer-check

- purpose: 用 stronger API reviewer 检查本地 reviewer 的 family 审查是否能更稳定
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_candidates_api_review_v2.jsonl --limit 1 --max-new-tokens 256 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/audit_model_data.py --input-file data/interim/object_dev_v0_candidates_api_review_v2.jsonl`
- inputs:
  - seed: `math_001`
  - generator: `Qwen3-4B`
  - reviewer: project-provided API endpoint
- outputs:
  - `data/interim/object_dev_v0_candidates_api_review_v2.jsonl`
- key metrics:
  - `substance_flip`: `pass`
  - `style_flip`: `pass`
  - `reasoning_fluff`: `fail`
  - consistency audit: `flagged=0`
- conclusion:
  - API reviewer is materially more stable than the current local reviewer for Object-gate family audit
  - current bottleneck shifts back to generator quality, especially for `reasoning_fluff`
- next action:
  - expand API-backed review to code seeds
  - use API reviewer as default audit path for bootstrap, with local review as cheap prefilter

### 2026-03-31 code-slice-api-review

- purpose: 检查 API reviewer 下 `code` domain 的 family cleanliness
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_code_api_review.jsonl --domains code --limit 2 --max-new-tokens 256 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/audit_model_data.py --input-file data/interim/object_dev_v0_code_api_review.jsonl`
- inputs:
  - seeds: `code_001`, `code_002`
  - generator: `Qwen3-4B`
  - reviewer: project-provided API endpoint
- outputs:
  - `data/interim/object_dev_v0_code_api_review.jsonl`
- key metrics:
  - total candidates: `6`
  - reviewer decision counts: `pass=3`, `fail=3`
  - by family:
    - `style_flip`: `2/2 pass`
    - `substance_flip`: `1/2 pass`
    - `reasoning_fluff`: `2/2 fail`
  - consistency audit: `flagged=0`
- conclusion:
  - `style_flip` is currently the cleanest family across math and code
  - `reasoning_fluff` is currently unsupported by the generator and should not be treated as a passed object family
  - `substance_flip` is viable but still needs tighter reviewer/generator boundary on code
- next action:
  - rewrite reasoning-fluff generation prompts
  - keep API reviewer as default bootstrap auditor

### 2026-03-31 verifier-alignment-check

- purpose: 用程序化 verifier 检查当前 API-reviewed 样本是否真的和 gold label 对齐
- command / script:
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_candidates_api_review_v2.jsonl --output-file data/interim/object_dev_v0_candidates_api_review_v2_verified.jsonl`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_code_api_review.jsonl --output-file data/interim/object_dev_v0_code_api_review_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_candidates_api_review_v2_verified.jsonl`
  - `data/interim/object_dev_v0_code_api_review_verified.jsonl`
- key metrics:
  - `style_flip`: verifier/gold aligned on current kept samples
  - `substance_flip`: verifier/gold aligned on current kept samples
  - `reasoning_fluff`: verifier prefers `tie` on all current checked samples, so gold `A` is inconsistent
- conclusion:
  - verifier confirms `reasoning_fluff` is not yet a clean bootstrap family
  - bootstrap can safely proceed with `style_flip + substance_flip`
- next action:
  - stop local rescue of current `reasoning_fluff`
  - move to judge-pool evaluation on active families

### 2026-03-31 reasoning-fluff-stop-loss

- purpose: decide whether `reasoning_fluff` should remain in bootstrap scope
- evidence:
  - `math_001` verified: `reasoning_fluff` fails
  - `code_001` verified: `reasoning_fluff` fails
  - `code_002` verified: `reasoning_fluff` fails
  - `code_003` verified: `reasoning_fluff` fails
- conclusion:
  - current `reasoning_fluff` recipe repeatedly fails the same gate across multiple seeds
  - it is deferred from bootstrap rather than continued as an active family
- next action:
  - bootstrap mainline uses `style_flip + substance_flip`
  - reopen `reasoning_fluff` only if a materially different generation recipe appears

### 2026-03-31 judge-sanity-eval

- purpose: 在当前 verifier-clean active slice 上做第一批本地 judge sanity check
- command / script:
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_candidates_api_review_v2_verified.jsonl data/interim/object_dev_v0_code_api_review_verified.jsonl --output-file data/interim/object_dev_v0_active_slice.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice.jsonl --output-file data/interim/judge_eval_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice.jsonl --output-file data/interim/judge_eval_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice.jsonl --output-file data/interim/judge_eval_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice.jsonl --output-file data/interim/judge_eval_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
- outputs:
  - `data/interim/object_dev_v0_active_slice.jsonl`
  - `data/interim/judge_eval_qwen3_0p6b_base.jsonl`
  - `data/interim/judge_eval_qwen3_0p6b_critic.jsonl`
  - `data/interim/judge_eval_qwen3_4b_base.jsonl`
  - `data/interim/judge_eval_qwen3_4b_critic.jsonl`
  - `artifacts/object_gate/judge_sanity_summary_2026-03-31.md`
- key metrics:
  - active slice size: `5`
  - `Qwen3-0.6B base`: `2/5`
  - `Qwen3-0.6B critic`: `2/5`
  - `Qwen3-4B base`: `4/5`
  - `Qwen3-4B critic`: `3/5`
  - family breakdown:
    - both `0.6B` variants: `substance_flip=2/2`, `style_flip=0/3`
    - `4B base`: `substance_flip=2/2`, `style_flip=2/3`
    - `4B critic`: `substance_flip=2/2`, `style_flip=1/3`
- conclusion:
  - current active slice already induces non-trivial judge differentiation
  - the early separation is mainly on `style_flip`
  - prompt style changes family-wise behavior even at fixed model size
- next action:
  - expand the active slice
  - compute first-pass family-wise miss / early COC

### 2026-03-31 first-pass-coc

- purpose: 在扩展后的 active slice 上计算 first-pass overall accuracy、family miss 和 uniform COC
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_active_families_api_review.jsonl --families substance_flip style_flip --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_active_families_api_review.jsonl --output-file data/interim/object_dev_v0_active_families_api_review_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_active_families_api_review_verified.jsonl --output-file data/interim/object_dev_v0_active_slice_v2.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v2.jsonl --output-file data/interim/judge_eval_v2_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v2.jsonl --output-file data/interim/judge_eval_v2_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v2.jsonl --output-file data/interim/judge_eval_v2_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v2.jsonl --output-file data/interim/judge_eval_v2_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_judge_metrics.py --input-files data/interim/judge_eval_v2_qwen3_0p6b_base.jsonl data/interim/judge_eval_v2_qwen3_0p6b_critic.jsonl data/interim/judge_eval_v2_qwen3_4b_base.jsonl data/interim/judge_eval_v2_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_v2_2026-03-31.json`
- outputs:
  - `data/interim/object_dev_v0_active_families_api_review_verified.jsonl`
  - `data/interim/object_dev_v0_active_slice_v2.jsonl`
  - `artifacts/object_gate/judge_metrics_v2_2026-03-31.json`
  - `artifacts/object_gate/first_pass_coc_summary_2026-03-31.md`
- key metrics:
  - active slice size: `7`
  - `Qwen3-0.6B base`: overall=`0.286`, COC=`0.5`, worst-family miss=`1.0`
  - `Qwen3-0.6B critic`: overall=`0.286`, COC=`0.5`, worst-family miss=`1.0`
  - `Qwen3-4B base`: overall=`0.857`, COC=`0.9`, worst-family miss=`0.2`
  - `Qwen3-4B critic`: overall=`0.714`, COC=`0.8`, worst-family miss=`0.4`
- conclusion:
  - current object signal is real enough to distinguish judges on active families
  - the separation is driven almost entirely by `style_flip`
  - `Qwen3-0.6B` currently behaves like a no-tie judge on style-equivalent cases
- next action:
  - expand the active slice further
  - start an explicit Object gate go/no-go memo

### 2026-03-31 expanded-active-slice-v3

- purpose: 扩大 active families 的 seed 覆盖面，检查 first-pass COC 信号是否稳定
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_active_families_api_review_v3.jsonl --families substance_flip style_flip --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_active_families_api_review_v3.jsonl --output-file data/interim/object_dev_v0_active_families_api_review_v3_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_active_families_api_review_v3_verified.jsonl --output-file data/interim/object_dev_v0_active_slice_v3.jsonl`
- outputs:
  - `data/interim/object_dev_v0_active_families_api_review_v3.jsonl`
  - `data/interim/object_dev_v0_active_families_api_review_v3_verified.jsonl`
  - `data/interim/object_dev_v0_active_slice_v3.jsonl`
- key metrics:
  - total generated rows: `18`
  - active slice size: `12`
  - family counts in active slice:
    - `style_flip = 9`
    - `substance_flip = 3`
- conclusion:
  - active slice expands cleanly
  - `style_flip` remains the dominant clean family
  - `substance_flip` is still usable but not yet equally mature
- next action:
  - rerun judge metrics on `v3`
  - write formal Object gate memo

### 2026-03-31 v3-judge-metrics

- purpose: 在 expanded active slice 上复测 judge differentiation 和 first-pass COC
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3.jsonl --output-file data/interim/judge_eval_v3_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3.jsonl --output-file data/interim/judge_eval_v3_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3.jsonl --output-file data/interim/judge_eval_v3_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3.jsonl --output-file data/interim/judge_eval_v3_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_judge_metrics.py --input-files data/interim/judge_eval_v3_qwen3_0p6b_base.jsonl data/interim/judge_eval_v3_qwen3_0p6b_critic.jsonl data/interim/judge_eval_v3_qwen3_4b_base.jsonl data/interim/judge_eval_v3_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_v3_2026-03-31.json`
- outputs:
  - `artifacts/object_gate/judge_metrics_v3_2026-03-31.json`
  - `docs/object_gate_memo_2026-03-31.md`
- key metrics:
  - `Qwen3-0.6B base`: overall=`0.25`, COC=`0.5`, worst-family miss=`1.0`
  - `Qwen3-0.6B critic`: overall=`0.25`, COC=`0.5`, worst-family miss=`1.0`
  - `Qwen3-4B base`: overall=`0.833`, COC=`0.889`, worst-family miss=`0.222`
  - `Qwen3-4B critic`: overall=`0.667`, COC=`0.778`, worst-family miss=`0.444`
- conclusion:
  - v2 -> v3 扩展后，judge ordering and family-wise pattern remain stable
  - current differentiation is still driven almost entirely by `style_flip`
  - Object gate can continue, but the claim should remain narrow
- next action:
  - expand `substance_flip`
  - start explicit audit controls

### 2026-03-31 order-swap-audit

- purpose: 检查当前 active-family signal 是否被 answer order artifact 污染
- command / script:
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_active_slice_v3.jsonl --output-file data/interim/object_dev_v0_active_slice_v3_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_v3_swapped_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_v3_swapped_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_v3_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_v3_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_order_audit.py --original-file data/interim/judge_eval_v3_qwen3_0p6b_base.jsonl --swapped-file data/interim/judge_eval_v3_swapped_qwen3_0p6b_base.jsonl --output-file artifacts/object_gate/order_audit_qwen3_0p6b_base_v3.json`
  - `python scripts/compute_order_audit.py --original-file data/interim/judge_eval_v3_qwen3_0p6b_critic.jsonl --swapped-file data/interim/judge_eval_v3_swapped_qwen3_0p6b_critic.jsonl --output-file artifacts/object_gate/order_audit_qwen3_0p6b_critic_v3.json`
  - `python scripts/compute_order_audit.py --original-file data/interim/judge_eval_v3_qwen3_4b_base.jsonl --swapped-file data/interim/judge_eval_v3_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/order_audit_qwen3_4b_base_v3.json`
  - `python scripts/compute_order_audit.py --original-file data/interim/judge_eval_v3_qwen3_4b_critic.jsonl --swapped-file data/interim/judge_eval_v3_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/order_audit_qwen3_4b_critic_v3.json`
- outputs:
  - `artifacts/object_gate/order_audit_qwen3_0p6b_base_v3.json`
  - `artifacts/object_gate/order_audit_qwen3_0p6b_critic_v3.json`
  - `artifacts/object_gate/order_audit_qwen3_4b_base_v3.json`
  - `artifacts/object_gate/order_audit_qwen3_4b_critic_v3.json`
  - `artifacts/object_gate/order_audit_summary_2026-03-31.md`
- key metrics:
  - `Qwen3-0.6B base`: expected_swap_rate=`0.083`, tie_stability=`0.0`, non_tie_flip=`0.0`
  - `Qwen3-0.6B critic`: expected_swap_rate=`0.083`, tie_stability=`0.0`, non_tie_flip=`0.0`
  - `Qwen3-4B base`: expected_swap_rate=`0.5`, tie_stability=`0.333`, non_tie_flip=`0.667`
  - `Qwen3-4B critic`: expected_swap_rate=`0.583`, tie_stability=`0.333`, non_tie_flip=`0.667`
- conclusion:
  - low-cap judges are dominated by answer-position bias
  - even 4B judges are still substantially order-sensitive on style-equivalent cases
  - Audit gate is currently not passed
- next action:
  - shift future evaluation to order-balanced or order-randomized protocols
  - avoid over-claiming from current style_flip-only signal

### 2026-03-31 balanced-order-metrics

- purpose: 在 `original + swapped` 配对协议下重读当前 `v3` judge 结果，得到 audit-controlled 指标
- command / script:
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_v3_qwen3_0p6b_base.jsonl data/interim/judge_eval_v3_qwen3_0p6b_critic.jsonl data/interim/judge_eval_v3_qwen3_4b_base.jsonl data/interim/judge_eval_v3_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_v3_swapped_qwen3_0p6b_base.jsonl data/interim/judge_eval_v3_swapped_qwen3_0p6b_critic.jsonl data/interim/judge_eval_v3_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_v3_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_v3_balanced_2026-03-31.json`
- outputs:
  - `scripts/compute_balanced_judge_metrics.py`
  - `artifacts/object_gate/judge_metrics_v3_balanced_2026-03-31.json`
  - `artifacts/object_gate/balanced_metrics_summary_2026-03-31.md`
- key metrics:
  - `Qwen3-0.6B base`: balanced directional=`0.125`, pair-strict=`0.0`, balanced COC pair-strict=`0.0`
  - `Qwen3-0.6B critic`: balanced directional=`0.125`, pair-strict=`0.0`, balanced COC pair-strict=`0.0`
  - `Qwen3-4B base`: balanced directional=`0.667`, pair-strict=`0.417`, balanced COC pair-strict=`0.5`
  - `Qwen3-4B critic`: balanced directional=`0.583`, pair-strict=`0.417`, balanced COC pair-strict=`0.5`
  - balanced family pair-strict:
    - `substance_flip = 0.667` for both `4B` judges
    - `style_flip = 0.333` for both `4B` judges
- conclusion:
  - order-balanced 后，`4B` 与 `0.6B` 的能力级差仍然存在，所以 object 不是纯顺序幻觉
  - 但 `4B base > 4B critic` 的差距在 pair-strict 读法下被压缩掉，prompt-style effect 目前不够稳
  - future gate 读数应优先采用 order-balanced paired protocol
- next action:
  - 扩 `substance_flip` 样本
  - 对 `style_flip` 做显式 length / verbosity audit

### 2026-03-31 style-length-audit

- purpose: 判断当前 `style_flip` 剩余 signal 是否主要来自长度/verbosity 偏置
- command / script:
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_active_slice_v3.jsonl --swapped-slice data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --original-eval data/interim/judge_eval_v3_qwen3_0p6b_base.jsonl --swapped-eval data/interim/judge_eval_v3_swapped_qwen3_0p6b_base.jsonl --output-file artifacts/object_gate/style_length_audit_qwen3_0p6b_base_v3.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_active_slice_v3.jsonl --swapped-slice data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --original-eval data/interim/judge_eval_v3_qwen3_0p6b_critic.jsonl --swapped-eval data/interim/judge_eval_v3_swapped_qwen3_0p6b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_qwen3_0p6b_critic_v3.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_active_slice_v3.jsonl --swapped-slice data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --original-eval data/interim/judge_eval_v3_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_v3_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_qwen3_4b_base_v3.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_active_slice_v3.jsonl --swapped-slice data/interim/object_dev_v0_active_slice_v3_swapped.jsonl --original-eval data/interim/judge_eval_v3_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_v3_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_qwen3_4b_critic_v3.json`
- outputs:
  - `scripts/compute_style_length_audit.py`
  - `artifacts/object_gate/style_length_audit_qwen3_0p6b_base_v3.json`
  - `artifacts/object_gate/style_length_audit_qwen3_0p6b_critic_v3.json`
  - `artifacts/object_gate/style_length_audit_qwen3_4b_base_v3.json`
  - `artifacts/object_gate/style_length_audit_qwen3_4b_critic_v3.json`
  - `artifacts/object_gate/style_length_audit_summary_2026-03-31.md`
- key metrics:
  - `Qwen3-0.6B base`: tie rate=`0.0`, choose longer among non-tie=`0.444`, choose shorter=`0.556`
  - `Qwen3-0.6B critic`: tie rate=`0.0`, choose longer among non-tie=`0.444`, choose shorter=`0.556`
  - `Qwen3-4B base`: tie rate=`0.611`, choose longer among non-tie=`0.143`, choose shorter=`0.857`
  - `Qwen3-4B critic`: tie rate=`0.5`, choose longer among non-tie=`0.222`, choose shorter=`0.778`
- conclusion:
  - `0.6B` 的主问题仍是 position bias，不是稳定的长度偏好
  - `4B` 在非 tie 时更常偏向更短答案，所以当前 `style_flip` 剩余 artifact 更像 briefness / prompt-fit bias，而不是 verbosity bias
  - 下一轮 `style_flip` audit 应转向 length-controlled / instruction-controlled recipe
- next action:
  - 设计长短差受控的 `style_flip` pair
  - 检查在去掉 `brief explanation` 诱导后，style signal 是否仍存在

### 2026-03-31 style-flip-controlled-pilot-v1

- purpose: 将 `style_flip` 从“更长更 polished”改成长度受控、指令更对称的 recipe，并做最小 pilot
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_api_review_v1.jsonl --families style_flip --style-flip-mode controlled_v1 --style-flip-max-char-gap 40 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_api_review_v1_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_style_flip_controlled_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v1_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v1_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_style_controlled_v1_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v1_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_style_controlled_v1_2026-03-31.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v1_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v1_qwen3_4b_base.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v1_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v1_qwen3_4b_critic.json`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_api_review_v1_verified.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_active_slice_v1.jsonl`
  - `artifacts/object_gate/judge_metrics_style_controlled_v1_2026-03-31.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_v1_qwen3_4b_base.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_v1_qwen3_4b_critic.json`
  - `artifacts/object_gate/style_flip_controlled_pilot_summary_2026-03-31.md`
- key metrics:
  - generated rows=`9`, reviewer pass=`4`, fail=`5`
  - generated avg char gap=`40.8` vs prior style baseline=`72.3`
  - verifier-clean active rows=`4`
  - `Qwen3-4B base`: balanced directional=`0.875`, pair-strict=`0.75`
  - `Qwen3-4B critic`: balanced directional=`0.625`, pair-strict=`0.25`
  - controlled length audit:
    - `4B base`: tie rate=`0.875`
    - `4B critic`: tie rate=`0.625`, choose shorter among non-tie=`0.667`
- conclusion:
  - controlled generation is directionally useful: it reduces verbosity gap and makes `4B base` much more tie-stable on kept pairs
  - but the recipe is not yet stable enough to replace the mainline: reviewer pass rate is low and `4B critic` remains noisy
  - current best next step is `controlled_v2`, not full migration
- next action:
  - tighten math length control
  - constrain code style pairs to lighter formatting/naming differences
  - expand `substance_flip` in parallel so object progress does not hinge on one family

### 2026-03-31 substance-new-math-expansion-v1

- purpose: 用低成本的新 math seeds 扩 `substance_flip`，降低当前 active object 对 `style_flip` 的依赖
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_newmath_api_review_v1.jsonl --families substance_flip --source-task-ids math_division_001 math_percentage_001 math_linear_y_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_newmath_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_newmath_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_newmath_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_newmath_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/expansion_and_controlled_v2_summary_2026-03-31.md`
- key metrics:
  - generated rows=`3`
  - reviewer pass=`2`
  - verifier-clean kept=`2`
  - kept items=`math_006__substance_flip`, `math_007__substance_flip`
- conclusion:
  - 新 math seeds 能稳定产出可用的 `substance_flip`
  - 这条线应继续扩，而不是只围绕 `style_flip` 调参
- next action:
  - 将这批新 substance rows 并入下一轮 active slice
  - 继续补更多 objective math seeds

### 2026-03-31 style-flip-controlled-v2-math-pilot

- purpose: 在 math 上把 `style_flip` 进一步收紧为更短、更对称的 `controlled_v2`
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_v2_math_api_review_v1.jsonl --families style_flip --domains math --style-flip-mode controlled_v2 --style-flip-max-char-gap 25 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_v2_math_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_math_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_v2_math_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_v2_math_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/expansion_and_controlled_v2_summary_2026-03-31.md`
- key metrics:
  - generated rows=`7`
  - reviewer pass=`0`
  - verifier-clean kept=`0`
  - avg gap=`34.7`
  - comparison:
    - `controlled_v1` math avg gap=`60.5`, pass=`2/4`
    - `controlled_v2` math avg gap=`34.7`, pass=`0/7`
- conclusion:
  - `controlled_v2` 把长度差压下来了，但已经过约束
  - reviewer 当前更常因 `weak_contrast` / `style_leakage` 拒绝，而不是因为长度太大
  - 下一版应是 `controlled_v2.1`，而不是继续原样放大
- next action:
  - 放宽到“短且对称，但有明确 style marker”的带宽
  - 暂不把 `controlled_v2` 替换主线

### 2026-03-31 style-flip-controlled-v2_1-math-pilot

- purpose: 把 `style_flip` 从过约束的 `controlled_v2` 调回一个 reviewer 可接受、但仍保持 brevity symmetry 的带宽
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1.jsonl --families style_flip --domains math --style-flip-mode controlled_v2_1 --style-flip-max-char-gap 25 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_style_controlled_v2_1_math_2026-03-31.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v2_1_math_qwen3_4b_base.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v2_1_math_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v2_1_math_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v2_1_math_qwen3_4b_critic.json`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_v2_1_math_active_slice_v1.jsonl`
  - `artifacts/object_gate/judge_metrics_style_controlled_v2_1_math_2026-03-31.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_v2_1_math_qwen3_4b_base.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_v2_1_math_qwen3_4b_critic.json`
  - `artifacts/object_gate/style_flip_controlled_v2_1_summary_2026-03-31.md`
- key metrics:
  - generated rows=`7`
  - reviewer pass=`2`
  - avg generated gap=`28.9`
  - comparison:
    - `controlled_v2`: pass=`0/7`, avg gap=`34.7`
    - `controlled_v2.1`: pass=`2/7`, avg gap=`28.9`
  - verifier-clean active rows=`2`
  - kept-pair avg gap=`5.5`
  - `Qwen3-4B base`: balanced directional=`1.0`, pair-strict=`1.0`
  - `Qwen3-4B critic`: balanced directional=`0.75`, pair-strict=`0.5`
- conclusion:
  - `controlled_v2.1` 恢复了非零通过率，并产出了真正 briefness-symmetric 的 clean math style pairs
  - 对 `4B base`，这两条 kept pairs 已经是 swap-balanced tie-stable
  - 但样本仍太小，只能当 recipe-direction signal，不能直接替换主线
- next action:
  - 在更多 math seeds 上复现 `v2.1`
  - 再迁到 code，检查是否重新引入 briefness bias

### 2026-03-31 style-flip-controlled-v2_1-code-pilot

- purpose: 检查 `style_flip controlled_v2.1` 能否不经修改地迁到 code
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1.jsonl --families style_flip --domains code --style-flip-mode controlled_v2_1 --style-flip-max-char-gap 25 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_style_controlled_v2_1_code_2026-03-31.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v2_1_code_qwen3_4b_base.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_v2_1_code_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_v2_1_code_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_style_controlled_v2_1_code_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_v2_1_code_qwen3_4b_critic.json`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_v2_1_code_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/judge_metrics_style_controlled_v2_1_code_2026-03-31.json`
  - `artifacts/object_gate/style_flip_controlled_v2_1_code_summary_2026-03-31.md`
- key metrics:
  - generated rows=`5`
  - reviewer pass=`1`
  - verifier-clean kept=`1`
  - generated avg gap=`48.4`
  - kept pair gap=`66`
  - `Qwen3-4B base`: balanced pair-strict=`1.0` on the single kept pair
  - `Qwen3-4B critic`: balanced pair-strict=`0.0` on the single kept pair
- conclusion:
  - `controlled_v2.1` does not transfer cleanly to code
  - the current code recipe mostly degenerates into comment-vs-no-comment weak contrasts
  - code needs its own style recipe; reuse of math-side `v2.1` is not sufficient
- next action:
  - design a code-specific controlled recipe around layout, naming, and mirrored harmless comments
  - keep math-side `v2.1` as the best current style recipe

### 2026-03-31 style-flip-controlled-code-v1-pilot

- purpose: 为 code 单独设计可用的 `style_flip` recipe，摆脱 `comment-vs-no-comment` 退化
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1.jsonl --families style_flip --domains code --style-flip-mode controlled_code_v1 --style-flip-max-char-gap 25 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_style_controlled_code_v1_2026-03-31.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_code_v1_qwen3_4b_base.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_code_v1_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_style_controlled_code_v1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_code_v1_qwen3_4b_critic.json`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_code_v1_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/judge_metrics_style_controlled_code_v1_2026-03-31.json`
  - `artifacts/object_gate/style_flip_controlled_code_v1_summary_2026-03-31.md`
- key metrics:
  - generated rows=`5`
  - reviewer pass=`4`
  - verifier-clean kept=`4`
  - generated avg gap=`34.4`
  - `Qwen3-4B base`: balanced directional=`0.75`, pair-strict=`0.5`
  - `Qwen3-4B critic`: balanced directional=`0.75`, pair-strict=`0.5`
  - length audit:
    - tie rate=`0.75`
    - all non-tie swapped decisions choose the shorter answer
- conclusion:
  - `controlled_code_v1` is the first code-side recipe with useful reviewer/verifier yield
  - but it still has audit instability on loop-vs-comprehension style pairs
  - treat it as current best code-side recipe, not as fully audited
- next action:
  - tighten the unstable subset to reduce swapped shorter-answer preference
  - keep using math-side `controlled_v2.1` separately rather than forcing one unified recipe

### 2026-03-31 style-flip-controlled-code-v1_1-pilot

- purpose: 在 `controlled_code_v1` 基础上收紧 code-side `style_flip`，剔除高波动的大结构改写 pair
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1.jsonl --families style_flip --domains code --style-flip-mode controlled_code_v1_1 --style-flip-max-char-gap 25 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl --output-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1_swapped.jsonl --output-file data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_style_controlled_code_v1_1_2026-03-31.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_base.jsonl --swapped-eval data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_base.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_code_v1_1_qwen3_4b_base.json`
  - `python scripts/compute_style_length_audit.py --original-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1.jsonl --swapped-slice data/interim/object_dev_v0_style_flip_controlled_code_v1_1_active_slice_v1_swapped.jsonl --original-eval data/interim/judge_eval_style_controlled_code_v1_1_qwen3_4b_critic.jsonl --swapped-eval data/interim/judge_eval_style_controlled_code_v1_1_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/style_length_audit_style_controlled_code_v1_1_qwen3_4b_critic.json`
- outputs:
  - `data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/judge_metrics_style_controlled_code_v1_1_2026-03-31.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_code_v1_1_qwen3_4b_base.json`
  - `artifacts/object_gate/style_length_audit_style_controlled_code_v1_1_qwen3_4b_critic.json`
  - `artifacts/object_gate/style_flip_controlled_code_v1_1_summary_2026-03-31.md`
- key metrics:
  - generated rows=`5`
  - reviewer pass=`2`
  - verifier-clean kept=`2`
  - generated avg gap=`32.4`
  - kept items=`code_003__style_flip`, `code_005__style_flip`
  - kept-pair avg gap=`7.5`
  - `Qwen3-4B base`: balanced directional=`1.0`, pair-strict=`1.0`
  - `Qwen3-4B critic`: balanced directional=`1.0`, pair-strict=`1.0`
  - length audit:
    - base tie rate=`1.0`
    - critic tie rate=`1.0`
    - non-tie decisions=`0`
- conclusion:
  - `controlled_code_v1_1` trades throughput for cleanliness
  - it is the current best clean code-side subset, but not a replacement for the higher-yield `controlled_code_v1`
  - code-side style recipe should now be treated as a two-tier setup: `v1` for yield, `v1.1` for audit-sensitive eval
- next action:
  - use `controlled_code_v1` to keep expanding code candidates
  - use `controlled_code_v1_1` when building the next balanced clean slice
  - continue expanding `substance_flip` so Object gate is not carried by style alone

### 2026-03-31 substance-remaining-old-pool-check

- purpose: 检查原始 12-seed 池剩余任务是否还能继续提供净增长的 `substance_flip`
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_remaining_api_review_v1.jsonl --families substance_flip --source-task-ids math_triangle_area_001 math_rectangle_perimeter_001 math_division_001 code_reverse_string_001 code_unique_preserve_order_001 code_count_uppercase_001 code_first_nonzero_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_remaining_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_remaining_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_remaining_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_remaining_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/substance_seed_refresh_summary_2026-03-31.md`
- key metrics:
  - generated rows=`7`
  - reviewer pass=`1`
  - verifier-clean kept=`0`
  - notable failure:
    - `code_005` reviewer pass but verifier tie, due current tests not exposing the `is not 0` bug
- conclusion:
  - the original seed pool is close to exhausted for low-cost `substance_flip` expansion
  - continuing to resample only the old pool is low-yield
- next action:
  - add a small batch of new compact objective seeds
  - keep the remaining old-pool file as a negative-result branch

### 2026-03-31 substance-new-seed-refresh-v1

- purpose: 用小批新 seeds 恢复 `substance_flip` 的 verifier-clean 增长
- command / script:
  - edited:
    - `data/raw/object_seed_tasks_v0.json`
    - `scripts/verify_object_candidates.py`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_newseeds_api_review_v1.jsonl --families substance_flip --source-task-ids math_percentage_002 math_linear_z_001 code_count_negatives_001 code_last_even_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_newseeds_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_newseeds_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_newseeds_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_newseeds_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/substance_seed_refresh_summary_2026-03-31.md`
- key metrics:
  - generated rows=`4`
  - reviewer pass=`3`
  - verifier-clean kept=`3`
  - kept items:
    - `math_009__substance_flip`
    - `code_006__substance_flip`
    - `code_007__substance_flip`
- conclusion:
  - the main problem was seed-pool exhaustion, not total generator collapse
  - compact objective seed refresh is an effective `substance_flip` growth path
- next action:
  - rebuild the clean merged slice with the refreshed substance pool

### 2026-03-31 clean-merged-slice-v2

- purpose: 用 refreshed `substance_flip` pool 重建 audit-controlled merged slice，并重新计算 balanced judge metrics
- command / script:
  - `python - <<'PY' ... -> data/interim/object_dev_v0_substance_clean_pool_v2.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_substance_clean_pool_v2.jsonl data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl --output-file data/interim/judge_eval_clean_merged_v2_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl --output-file data/interim/judge_eval_clean_merged_v2_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl --output-file data/interim/judge_eval_clean_merged_v2_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2.jsonl --output-file data/interim/judge_eval_clean_merged_v2_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v2_swapped_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v2_swapped_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v2_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v2_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v2_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v2_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v2_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v2_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v2_swapped_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v2_swapped_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v2_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v2_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v2_2026-03-31.json`
- outputs:
  - `data/interim/object_dev_v0_substance_clean_pool_v2.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v2.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v2_swapped.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v2_2026-03-31.json`
  - `artifacts/object_gate/clean_merged_slice_v2_summary_2026-03-31.md`
- key metrics:
  - slice size=`12` with `substance_flip=8`, `style_flip=4`
  - `Qwen3-0.6B base`: balanced directional=`0.333`, pair-strict=`0.0`
  - `Qwen3-0.6B critic`: balanced directional=`0.333`, pair-strict=`0.0`
  - `Qwen3-4B base`: balanced directional=`0.792`, pair-strict=`0.583`
  - `Qwen3-4B critic`: balanced directional=`0.833`, pair-strict=`0.667`
  - family pair-strict:
    - `4B base`: `substance=0.375`, `style=1.0`
    - `4B critic`: `substance=0.625`, `style=0.75`
- conclusion:
  - refreshed `substance_flip` keeps the clean merged slice at useful size without relying on unaudited style rows
  - low-cap judges still collapse under swap-balanced reading, while `4B` remains materially better
  - the main bottleneck is now a small cluster of `substance_flip` items, not broad style contamination
- next action:
  - inspect the stubborn `substance_flip` items that still fail pair-strict under `4B`
  - keep adding compact objective seeds rather than reopening broad style sweeps

### 2026-03-31 substance-targeted-repair-v1

- purpose: 修复 `clean_merged_slice_v2` 中“只改最后输出 token”的 stubborn `substance_flip` 项
- command / script:
  - edited:
    - `scripts/bootstrap_object_data.py`
    - `docs/family_construction_note.md`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_targeted_v1_api_review_v1.jsonl --families substance_flip --substance-flip-mode targeted_v1 --source-task-ids math_fraction_of_number_001 math_percentage_001 math_linear_y_001 math_linear_z_001 code_count_negatives_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_targeted_v1_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_targeted_v1_api_review_v1_verified.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_targeted_v1_math_qwen3_8b_api_review_v1.jsonl --families substance_flip --substance-flip-mode targeted_v1 --source-task-ids math_fraction_of_number_001 math_percentage_001 math_linear_y_001 math_linear_z_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_targeted_v1_math_qwen3_8b_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_targeted_v1_math_qwen3_8b_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_targeted_v1_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_targeted_v1_api_review_v1_verified.jsonl`
  - `data/interim/object_dev_v0_substance_targeted_v1_math_qwen3_8b_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_targeted_v1_math_qwen3_8b_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/substance_targeted_repair_summary_2026-03-31.md`
- key metrics:
  - local `Qwen3-4B` targeted run:
    - generated rows=`5`
    - reviewer pass=`1`
    - math repair success=`0/4`
  - `Qwen3-8B` targeted math run:
    - generated rows=`4`
    - reviewer pass=`3`
    - verifier-clean kept=`3`
    - kept items:
      - `math_003__substance_flip`
      - `math_007__substance_flip`
      - `math_009__substance_flip`
- conclusion:
  - the targeted repair idea is correct, but local `4B` generation is not reliable enough for the math repairs
  - `Qwen3-8B` can follow the targeted error-locus constraint well enough to repair the stubborn math subset
- next action:
  - replace the weak math substance rows in the clean merged slice with the repaired versions

### 2026-03-31 clean-merged-slice-v3-4b

- purpose: 用 targeted substance repairs 替换 `v2` 中的弱 math rows，并检查 `4B` 的 balanced pair-strict 是否实质改善
- command / script:
  - `python - <<'PY' ... -> data/interim/object_dev_v0_substance_clean_pool_v3.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_substance_clean_pool_v3.jsonl data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl --output-file data/interim/judge_eval_clean_merged_v3_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl --output-file data/interim/judge_eval_clean_merged_v3_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v3_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v3_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v3_4b_only_2026-03-31.json`
- outputs:
  - `data/interim/object_dev_v0_substance_clean_pool_v3.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v3.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v3_4b_only_2026-03-31.json`
  - `artifacts/object_gate/clean_merged_slice_v3_summary_2026-03-31.md`
- key metrics:
  - `Qwen3-4B base`:
    - balanced directional=`0.917`
    - pair-strict=`0.833`
    - substance pair-strict=`0.75`
  - `Qwen3-4B critic`:
    - balanced directional=`0.958`
    - pair-strict=`0.917`
    - substance pair-strict=`1.0`
  - v2 -> v3:
    - base pair-strict: `0.583 -> 0.833`
    - critic pair-strict: `0.667 -> 0.917`
- conclusion:
  - moving the error locus into the intermediate semantic step materially fixes the stubborn substance failures
  - `clean_merged_slice_v3` is the current best high-capacity merged slice
  - a fully matched cross-capacity comparison would still require rerunning `0.6B` on `v3`
- next action:
  - rerun `0.6B` on `v3` to form a fully matched cross-capacity panel
  - continue growing `substance_flip` with targeted error-locus control

### 2026-03-31 clean-merged-slice-v3-fullpanel

- purpose: 在 `clean_merged_slice_v3` 上补齐 `0.6B` judge，验证 targeted repair 的收益是否真是 capacity-sensitive
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl --output-file data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3.jsonl --output-file data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v3_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v3_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v3_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v3_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v3_fullpanel_2026-03-31.json`
- outputs:
  - `data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_base.jsonl`
  - `data/interim/judge_eval_clean_merged_v3_qwen3_0p6b_critic.jsonl`
  - `data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_base.jsonl`
  - `data/interim/judge_eval_clean_merged_v3_swapped_qwen3_0p6b_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v3_fullpanel_2026-03-31.json`
  - `artifacts/object_gate/clean_merged_slice_v3_fullpanel_summary_2026-03-31.md`
- key metrics:
  - `Qwen3-0.6B base`: balanced directional=`0.333`, pair-strict=`0.0`
  - `Qwen3-0.6B critic`: balanced directional=`0.333`, pair-strict=`0.0`
  - `Qwen3-4B base`: balanced directional=`0.917`, pair-strict=`0.833`
  - `Qwen3-4B critic`: balanced directional=`0.958`, pair-strict=`0.917`
- conclusion:
  - `v3` gains are capacity-sensitive rather than generic slice easing
  - low-capacity judges do not benefit from the targeted repair, while high-capacity judges do
  - `clean_merged_slice_v3` is now a fully matched cross-capacity panel, not just a 4B-only result
- next action:
  - keep expanding `substance_flip` with targeted error-locus control
  - prepare a matched `v2 -> v3` comparison table if needed for paper-facing presentation

### 2026-03-31 substance-targeted-growth-v2

- purpose: 检查 `substance_flip_targeted_v1` 在 fresh compact seeds 上是否也能稳定带来净增长
- command / script:
  - edited:
    - `data/raw/object_seed_tasks_v0.json`
    - `scripts/verify_object_candidates.py`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_targeted_v1_newseeds_qwen3_8b_api_review_v1.jsonl --families substance_flip --substance-flip-mode targeted_v1 --source-task-ids math_percentage_003 math_linear_x_002 code_count_positives_001 code_first_even_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_targeted_v1_newseeds_qwen3_8b_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_targeted_v1_newseeds_qwen3_8b_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_targeted_v1_newseeds_qwen3_8b_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_targeted_v1_newseeds_qwen3_8b_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/substance_targeted_growth_summary_2026-03-31.md`
- key metrics:
  - generated rows=`4`
  - reviewer pass=`3`
  - verifier-clean kept=`3`
  - kept items:
    - `math_011__substance_flip`
    - `code_008__substance_flip`
    - `code_009__substance_flip`
- conclusion:
  - `substance_flip_targeted_v1` continues to produce net-new clean rows on fresh seeds
  - targeted error-locus control is now a scalable growth path, not just a local repair
- next action:
  - fold the new substance rows into the next clean merged slice

### 2026-03-31 clean-merged-slice-v4-4b

- purpose: 检查 fresh targeted substance growth 是否能在更大 merged slice 上保持 high-cap stability
- command / script:
  - `python - <<'PY' ... -> data/interim/object_dev_v0_substance_clean_pool_v4.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_substance_clean_pool_v4.jsonl data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v4.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_clean_merged_slice_v4.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v4_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v4.jsonl --output-file data/interim/judge_eval_clean_merged_v4_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v4.jsonl --output-file data/interim/judge_eval_clean_merged_v4_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v4_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v4_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v4_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v4_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v4_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v4_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v4_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v4_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v4_4b_only_2026-03-31.json`
- outputs:
  - `data/interim/object_dev_v0_substance_clean_pool_v4.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v4.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v4_swapped.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v4_4b_only_2026-03-31.json`
  - `artifacts/object_gate/clean_merged_slice_v4_summary_2026-03-31.md`
- key metrics:
  - slice size=`15` with `substance_flip=11`, `style_flip=4`
  - `Qwen3-4B base`: balanced directional=`0.933`, pair-strict=`0.867`, substance pair-strict=`0.818`
  - `Qwen3-4B critic`: balanced directional=`0.967`, pair-strict=`0.933`, substance pair-strict=`1.0`
- conclusion:
  - the targeted substance path scales at least one step further without collapsing
  - expanding from `12` to `15` rows does not erase the gains from `v3`
  - current best high-cap slice is now `v4`
- next action:
  - decide whether `v4` deserves a matched `0.6B` rerun
  - continue targeted substance expansion on fresh seeds

### 2026-03-31 substance-targeted-growth-v3

- purpose: 检查 `substance_flip_targeted_v1` 在第二批 fresh compact seeds 上是否仍能稳定带来净增长
- command / script:
  - edited:
    - `data/raw/object_seed_tasks_v0.json`
    - `scripts/verify_object_candidates.py`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/bootstrap_object_data.py --seed-file data/raw/object_seed_tasks_v0.json --output-file data/interim/object_dev_v0_substance_targeted_v1_newseeds2_qwen3_8b_api_review_v1.jsonl --families substance_flip --substance-flip-mode targeted_v1 --source-task-ids math_percentage_004 math_linear_t_001 code_count_odds_001 code_last_positive_001 --max-new-tokens 320 --generator-model-path /cephfs/shared/hf_cache/hub/Qwen3-8B --reviewer-backend api`
  - `python scripts/verify_object_candidates.py --seed-file data/raw/object_seed_tasks_v0.json --input-file data/interim/object_dev_v0_substance_targeted_v1_newseeds2_qwen3_8b_api_review_v1.jsonl --output-file data/interim/object_dev_v0_substance_targeted_v1_newseeds2_qwen3_8b_api_review_v1_verified.jsonl`
- outputs:
  - `data/interim/object_dev_v0_substance_targeted_v1_newseeds2_qwen3_8b_api_review_v1.jsonl`
  - `data/interim/object_dev_v0_substance_targeted_v1_newseeds2_qwen3_8b_api_review_v1_verified.jsonl`
  - `artifacts/object_gate/substance_targeted_growth_v2_summary_2026-03-31.md`
- key metrics:
  - generated rows=`4`
  - reviewer pass=`3`
  - verifier-clean kept=`3`
  - kept items:
    - `math_013__substance_flip`
    - `code_010__substance_flip`
    - `code_011__substance_flip`
  - rejected item:
    - `math_012__substance_flip`
    - failure mode=`wrong answer still only changes the final token 15 -> 16`
- conclusion:
  - `substance_flip_targeted_v1` reproduces the same `3/4` fresh-seed growth pattern on a second batch
  - targeted error-locus control now looks like a stable expansion protocol, not just a repair heuristic
- next action:
  - fold the new substance rows into the next clean merged slice
  - decide whether the project should keep sweeping or start table-making

### 2026-03-31 clean-merged-slice-v5-4b

- purpose: 检查第二批 targeted substance growth 折入后，merged slice 能否继续保持 strong high-cap balanced readout
- command / script:
  - `python - <<'PY' ... -> data/interim/object_dev_v0_substance_clean_pool_v5.jsonl`
  - `python scripts/build_active_object_slice.py --input-files data/interim/object_dev_v0_substance_clean_pool_v5.jsonl data/interim/object_dev_v0_style_flip_controlled_v2_1_math_api_review_v1_verified.jsonl data/interim/object_dev_v0_style_flip_controlled_code_v1_1_api_review_v1_verified.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/judge_eval_clean_merged_v5_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/judge_eval_clean_merged_v5_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-4B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v5_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v5_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v5_4b_only_2026-03-31.json`
- outputs:
  - `data/interim/object_dev_v0_substance_clean_pool_v5.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v5.jsonl`
  - `data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v5_4b_only_2026-03-31.json`
  - `artifacts/object_gate/clean_merged_slice_v5_summary_2026-03-31.md`
- key metrics:
  - slice size=`18` with `substance_flip=14`, `style_flip=4`
  - `Qwen3-4B base`: balanced directional=`0.917`, pair-strict=`0.833`, substance pair-strict=`0.786`
  - `Qwen3-4B critic`: balanced directional=`0.972`, pair-strict=`0.944`, substance pair-strict=`1.0`
  - vs `v4`:
    - base pair-strict: `0.867 -> 0.833`
    - critic pair-strict: `0.933 -> 0.944`
- conclusion:
  - the targeted substance path scales one more step without collapsing the high-cap object signal
  - `4B critic` remains perfect on the enlarged substance subset
  - `4B base` remains robust but not monotonic, so the honest state is “stable with a few residual hard pairs,” not “fully saturated”
- next action:
  - decide whether `v5` deserves a matched `0.6B` rerun
  - prepare a `v2/v3/v4/v5` comparison table for paper-facing use

### 2026-04-01 clean-merged-slice-v5-fullpanel

- purpose: 在 `clean_merged_slice_v5` 上补齐 `0.6B` judge，判断 `v5` 是否能替代 `v3` 成为当前 best fully matched slice
- command / script:
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_base.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style base`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --input-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_critic.jsonl --model-path /cephfs/shared/hf_cache/hub/Qwen3-0.6B --judge-style critic`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v5_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v5_qwen3_4b_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_base.jsonl data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_critic.jsonl data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_base.jsonl data/interim/judge_eval_clean_merged_v5_swapped_qwen3_4b_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v5_fullpanel_2026-04-01.json`
- outputs:
  - `data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_base.jsonl`
  - `data/interim/judge_eval_clean_merged_v5_qwen3_0p6b_critic.jsonl`
  - `data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_base.jsonl`
  - `data/interim/judge_eval_clean_merged_v5_swapped_qwen3_0p6b_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v5_fullpanel_2026-04-01.json`
  - `artifacts/object_gate/clean_merged_slice_v5_fullpanel_summary_2026-04-01.md`
- key metrics:
  - `Qwen3-0.6B base`: balanced directional=`0.389`, pair-strict=`0.0`, balanced COC pair-strict=`0.0`
  - `Qwen3-0.6B critic`: balanced directional=`0.389`, pair-strict=`0.0`, balanced COC pair-strict=`0.0`
  - `Qwen3-4B base`: balanced directional=`0.917`, pair-strict=`0.833`, balanced COC pair-strict=`0.893`
  - `Qwen3-4B critic`: balanced directional=`0.972`, pair-strict=`0.944`, balanced COC pair-strict=`0.875`
  - vs `v3` fullpanel:
    - `0.6B base`: pair-strict `0.0 -> 0.0`
    - `0.6B critic`: pair-strict `0.0 -> 0.0`
    - `4B base`: pair-strict `0.833 -> 0.833`
    - `4B critic`: pair-strict `0.917 -> 0.944`
- conclusion:
  - `v5` does not behave like a generically easier slice, because the larger sample still leaves both `0.6B` judges at balanced `pair-strict=0.0`
  - the cross-cap separation seen on `v3` survives on a larger merged slice
  - `clean_merged_slice_v5` should replace `v3` as the current best fully matched audit-controlled slice
- next action:
  - prepare a paper-facing comparison table across `v2/v3/v4/v5`
  - write a concise object-gate note using `v5` as the main matched-slice reference

### 2026-04-01 object-gate-synthesis

- purpose: 将冻结的 `v2/v3/v4/v5` 结果整理成 paper-facing comparison table，并用 `v5` 刷新 object-gate memo
- command / script:
  - no new experiment
  - synthesis from:
    - `artifacts/object_gate/clean_merged_slice_v2_summary_2026-03-31.md`
    - `artifacts/object_gate/clean_merged_slice_v3_fullpanel_summary_2026-03-31.md`
    - `artifacts/object_gate/clean_merged_slice_v4_summary_2026-03-31.md`
    - `artifacts/object_gate/clean_merged_slice_v5_fullpanel_summary_2026-04-01.md`
- outputs:
  - `docs/object_gate_comparison_table_2026-04-01.md`
  - `docs/object_gate_memo_2026-04-01.md`
  - `history/2026-04-01_object_gate_synthesis.md`
- key conclusions:
  - `v2` = first clean merged slice after audited style control
  - `v3` = first fully matched breakthrough slice
  - `v4` = larger high-cap intermediate, but not paper-facing main slice because it is not matched
  - `v5` = current best fully matched audit-controlled slice
- conclusion:
  - current object-gate headline should anchor on `v5`, not `v3` or `v4`
  - `v3` remains useful as first-breakthrough support, but `v5` is now the best main-table reference
- next action:
  - compress the comparison table into a paper-main-table version with caption and minimal wording

### 2026-04-01 api-judge-probe-v5

- purpose: 直接检查单个 stronger API judge 加入后，`v5` 上的 object signal 会不会消失
- command / script:
  - edited:
    - `scripts/eval_judges.py`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/object_dev_v0_clean_merged_slice_v5.jsonl --output-file data/interim/judge_eval_clean_merged_v5_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 192 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/object_dev_v0_clean_merged_slice_v5_swapped.jsonl --output-file data/interim/judge_eval_clean_merged_v5_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 192 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_clean_merged_v5_api_critic.jsonl --swapped-files data/interim/judge_eval_clean_merged_v5_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_clean_merged_v5_api_critic_probe_2026-04-01.json`
- outputs:
  - `data/interim/judge_eval_clean_merged_v5_api_critic.jsonl`
  - `data/interim/judge_eval_clean_merged_v5_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_clean_merged_v5_api_critic_probe_2026-04-01.json`
  - `artifacts/object_gate/api_judge_probe_v5_summary_2026-04-01.md`
- key metrics:
  - original accuracy=`18/18`
  - swapped accuracy=`18/18`
  - balanced directional=`1.0`
  - pair-strict=`1.0`
  - `substance_flip pair-strict=1.0`
  - `style_flip pair-strict=1.0`
- conclusion:
  - the API judge does not make the object disappear
  - instead, the current `v5` slice is fully solved by the stronger API `critic`
  - this strengthens the model-sensitivity story, but also suggests `v5` is not hard enough for a stronger-model final benchmark
- next action:
  - keep `v5` as the current object-claim slice
  - if the project wants a stronger-model story, plan a harder final slice than `v5`

### 2026-04-01 frontier-boundary-probe-v0-api

- purpose: 开始真正的 strong-judge boundary search，检查当前 strongest API judge 是否在新 hard families 上出现非平凡 miss
- command / script:
  - edited:
    - `docs/frontier_boundary_search_2026-04-01.md`
    - `data/raw/frontier_boundary_probe_v0.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v0.jsonl --output-file data/interim/frontier_boundary_probe_v0_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v0.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v0_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 192 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v0_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v0_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 192 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v0_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v0_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v0_api_critic_2026-04-01.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v0_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v0_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v0_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v0_api_critic_2026-04-01.json`
  - `artifacts/object_gate/frontier_boundary_probe_v0_api_summary_2026-04-01.md`
- key metrics:
  - total pairs=`6`
  - balanced directional=`0.75`
  - pair-strict=`0.667`
  - family pair-strict:
    - `constraint_edge_case=1.0`
    - `omission_critical=1.0`
    - `clarify_required=0.0`
  - strongest failures:
    - `fbp_005__clarify_required`
    - `fbp_006__clarify_required`
- conclusion:
  - the first concrete frontier boundary signal is real and not merely a weak-model phenomenon
  - the strongest current API judge is vulnerable on `clarify_required` prompts, where literal answering competes with epistemic caution
  - current code edge-case families are useful controls but did not yet expose the API boundary
- next action:
  - expand `clarify_required` into a more diverse and more tightly audited frontier-hard family

### 2026-04-01 frontier-boundary-probe-v1-clarify-api

- purpose: 检查 `clarify_required` 是否真是 strongest API judge 的稳定边界，而不只是两条手工样例的偶然现象
- command / script:
  - edited:
    - `docs/clarify_required_family_note_2026-04-01.md`
    - `data/raw/frontier_boundary_probe_v1_clarify.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v1_clarify.jsonl --output-file data/interim/frontier_boundary_probe_v1_clarify_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v1_clarify.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v1_clarify_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v1_clarify_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v1_clarify_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v1_clarify_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v1_clarify_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v1_clarify_api_critic_2026-04-01.json`
- outputs:
  - `docs/clarify_required_family_note_2026-04-01.md`
  - `data/interim/frontier_boundary_probe_v1_clarify_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v1_clarify_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v1_clarify_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v1_clarify_api_critic_2026-04-01.json`
  - `artifacts/object_gate/frontier_boundary_probe_v1_clarify_api_summary_2026-04-01.md`
- key metrics:
  - total pairs=`8`
  - balanced directional=`0.438`
  - pair-strict=`0.25`
  - family pair-strict:
    - `clarify_required=0.25`
  - representative failures:
    - `fbc_001`: probability with missing sample space
    - `fbc_003`: degree conversion with missing source unit
    - `fbc_005`: indexing/convention ambiguity
    - `fbc_008`: pass-rate prompt with missing counts
- conclusion:
  - `clarify_required` is a real strong-judge boundary family, not just a small anecdotal effect
  - the current strongest API judge systematically over-rewards direct default answers under underspecified prompts
  - the more precise failure description is `default-answer bias under underspecification`
- next action:
  - expand `clarify_required` while making its gold rule even narrower and more audit-friendly

### 2026-04-02 frontier-boundary-probe-v2-clarify-api

- purpose: 在更严格的 `clarify_required` gold rule 下，检查 strongest API judge 的边界是否仍然存在，以及哪些 clarify 子族是真正的 hard core
- command / script:
  - edited:
    - `docs/clarify_required_family_note_2026-04-01.md`
    - `data/raw/frontier_boundary_probe_v2_clarify.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v2_clarify.jsonl --output-file data/interim/frontier_boundary_probe_v2_clarify_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v2_clarify.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v2_clarify_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v2_clarify_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v2_clarify_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v2_clarify_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v2_clarify_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v2_clarify_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v2_clarify_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v2_clarify_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v2_clarify_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v2_clarify_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v2_clarify_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`8`
  - balanced directional=`0.625`
  - pair-strict=`0.5`
  - subfamily pair-strict:
    - `sample_space_missing=1.0`
    - `reference_frame_missing=0.333`
    - `convention_missing=0.333`
- conclusion:
  - tightening the gold rule does not erase the frontier boundary
  - but it sharpens it: the true hard core is not all clarify-first prompts, but underdetermined prompts where a hidden frame or convention changes the concrete output
  - `sample_space_missing` is currently too easy to be treated as the main hard subtype, while `reference_frame_missing` and `convention_missing` remain frontier-hard
- next action:
  - continue clarify search with emphasis on `reference_frame_missing` and `convention_missing`


### 2026-04-02 frontier-boundary-probe-v3-clarify-core-api

- purpose: 将 `clarify_required` 收窄到 core-only 工作集，检查 strongest API judge 的 frontier boundary 是否集中在更窄的默认约定子族上
- command / script:
  - edited:
    - `docs/clarify_required_family_note_2026-04-01.md`
    - `data/raw/frontier_boundary_probe_v3_clarify_core.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v3_clarify_core.jsonl --output-file data/interim/frontier_boundary_probe_v3_clarify_core_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v3_clarify_core.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v3_clarify_core_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v3_clarify_core_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v3_clarify_core_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v3_clarify_core_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v3_clarify_core_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v3_clarify_core_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`10`
  - balanced directional=`0.7`
  - pair-strict=`0.6`
  - subfamily pair-strict:
    - `source_unit_missing=0.0`
    - `date_convention_missing=0.333`
    - `timezone_reference_missing=1.0`
    - `measurement_convention_missing=1.0`
    - `clock_convention_missing=1.0`
- conclusion:
  - the frontier boundary remains real, but it is narrower than a broad `clarify_required` label suggests
  - the strongest current API judge is still stably vulnerable when a direct answer relies on a culturally common default unit or date convention
  - current hardest subtypes are `source_unit_missing` and `date_convention_missing`; the other tested clarify subtypes now look more like controls
- next action:
  - continue boundary search with new probes concentrated on `source_unit_missing` and `date_convention_missing`


### 2026-04-02 frontier-boundary-probe-v4-clarify-hardcore-api

- purpose: 只保留 `clarify_required` 里当前最硬的两类子族，检查 strongest API judge 的 frontier boundary 能否进一步压低到论文主线候选强度
- command / script:
  - created:
    - `data/raw/frontier_boundary_probe_v4_clarify_hardcore.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v4_clarify_hardcore.jsonl --output-file data/interim/frontier_boundary_probe_v4_clarify_hardcore_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v4_clarify_hardcore.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v4_clarify_hardcore_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v4_clarify_hardcore_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v4_clarify_hardcore_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v4_clarify_hardcore_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v4_clarify_hardcore_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v4_clarify_hardcore_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`8`
  - balanced directional=`0.5625`
  - pair-strict=`0.25`
  - subfamily pair-strict:
    - `source_unit_missing=0.25`
    - `date_convention_missing=0.25`
- conclusion:
  - this is the strongest frontier-hard result so far after the pivot to strong-judge boundary search
  - the current best hard slice is no longer broad `clarify_required`, but the narrower default-convention boundary inside it
  - the strongest current API judge still fails non-trivially when a direct answer rides on a culturally common source-unit or date-format default
- next action:
  - continue with fresh probes concentrated on `source_unit_missing` and `date_convention_missing`, and start drafting paper-facing wording for this narrower object


### 2026-04-02 frontier-boundary-probe-v5-default-convention-api

- purpose: 用 fresh mixed prompts 复测当前 `default-convention boundary` 是否仍然卡 strongest API judge
- command / script:
  - created:
    - `data/raw/frontier_boundary_probe_v5_default_convention.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v5_default_convention.jsonl --output-file data/interim/frontier_boundary_probe_v5_default_convention_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v5_default_convention.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v5_default_convention_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v5_default_convention_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v5_default_convention_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v5_default_convention_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v5_default_convention_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v5_default_convention_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`8`
  - balanced directional=`0.625`
  - pair-strict=`0.375`
  - subfamily pair-strict:
    - `source_unit_missing=0.0`
    - `date_convention_missing=0.75`
- conclusion:
  - the fresh mixed slice still exposes a real frontier boundary
  - `source_unit_missing` is currently the most stable hard subtype
  - `date_convention_missing` looks recipe-sensitive and should be re-tested in a narrower form
- next action:
  - run a fresh date-only probe with compact ambiguous short-date strings

### 2026-04-02 frontier-boundary-probe-v6-date-convention-api

- purpose: 单独检查 `date_convention_missing` 是否仍是 strong-judge hard subtype，避免被 mixed-slice 读法误伤
- command / script:
  - created:
    - `data/raw/frontier_boundary_probe_v6_date_convention.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v6_date_convention.jsonl --output-file data/interim/frontier_boundary_probe_v6_date_convention_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v6_date_convention.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v6_date_convention_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v6_date_convention_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v6_date_convention_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v6_date_convention_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v6_date_convention_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v6_date_convention_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`4`
  - balanced directional=`0.125`
  - pair-strict=`0.0`
  - subfamily pair-strict:
    - `date_convention_missing=0.0`
- conclusion:
  - `date_convention_missing` remains genuinely frontier-hard under the right recipe
  - the best current date-side recipe is compact ambiguous short-date strings with direct ISO conversion
  - the working object should now be described as a `default-convention boundary`, not just generic `clarify_required`
- next action:
  - continue with fresh `source_unit_missing` and compact `date_convention_missing` probes, then draft paper-facing wording for the narrower object


### 2026-04-02 frontier-boundary-probe-v7-source-unit-api

- purpose: 用 fresh source-unit-only slice 复测 strongest API judge 是否会稳定默认 Celsius
- command / script:
  - created:
    - `data/raw/frontier_boundary_probe_v7_source_unit.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v7_source_unit.jsonl --output-file data/interim/frontier_boundary_probe_v7_source_unit_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v7_source_unit.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v7_source_unit_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v7_source_unit_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v7_source_unit_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v7_source_unit_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v7_source_unit_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v7_source_unit_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`4`
  - balanced directional=`0.25`
  - pair-strict=`0.25`
  - subfamily pair-strict:
    - `source_unit_missing=0.25`
- conclusion:
  - `source_unit_missing` remains the most stable current hard subtype
  - the failure is not mainly due to pair order, since original and swapped are both `1/4`
  - this subtype can serve as the anchor recipe for the current `default-convention boundary`
- next action:
  - keep expanding compact date-side replications while using source-unit as the stable anchor subtype


### 2026-04-02 frontier-boundary-probe-v8-date-convention-compact-api

- purpose: 对 compact `date_convention_missing` recipe 做第二次 fresh replication，确认 date-side hard signal 是否可重复
- command / script:
  - created:
    - `data/raw/frontier_boundary_probe_v8_date_convention_compact.jsonl`
  - `python scripts/make_swapped_order_slice.py --input-file data/raw/frontier_boundary_probe_v8_date_convention_compact.jsonl --output-file data/interim/frontier_boundary_probe_v8_date_convention_compact_swapped.jsonl`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/raw/frontier_boundary_probe_v8_date_convention_compact.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && python scripts/eval_judges.py --backend api --input-file data/interim/frontier_boundary_probe_v8_date_convention_compact_swapped.jsonl --output-file data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_swapped_api_critic.jsonl --judge-style critic --api-config-file README.md --max-new-tokens 320 --temperature 0.0`
  - `python scripts/compute_balanced_judge_metrics.py --original-files data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_api_critic.jsonl --swapped-files data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_swapped_api_critic.jsonl --output-file artifacts/object_gate/judge_metrics_frontier_boundary_probe_v8_date_convention_compact_api_critic_2026-04-02.json`
- outputs:
  - `data/interim/frontier_boundary_probe_v8_date_convention_compact_swapped.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_api_critic.jsonl`
  - `data/interim/judge_eval_frontier_boundary_probe_v8_date_convention_compact_swapped_api_critic.jsonl`
  - `artifacts/object_gate/judge_metrics_frontier_boundary_probe_v8_date_convention_compact_api_critic_2026-04-02.json`
  - `artifacts/object_gate/frontier_boundary_probe_v8_date_convention_compact_api_summary_2026-04-02.md`
- key metrics:
  - total pairs=`4`
  - balanced directional=`0.125`
  - pair-strict=`0.0`
  - subfamily pair-strict:
    - `date_convention_missing=0.0`
- conclusion:
  - compact `date_convention_missing` is now a replicated hard recipe, not a one-off slice
  - date-side evidence is now strong enough to sit beside `source_unit_missing` in the main object claim
- next action:
  - shift effort from new exploratory probes to paper-facing wording and table integration
