# CIVIC-PRM

Week 1 scaffold for the proposal in [02_civic_prm_answer_invariant_verifier.md](/cephfs/luyanzhen/apg/civic-prm/02_civic_prm_answer_invariant_verifier.md).

## Environment

- Use the `infer` conda environment for model-facing work.
- Shared model cache is available under `/cephfs/shared/hf_cache/hub`.
- A confirmed pilot model path is `/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots`.
可用模型缓存：`/cephfs/shared/hf_cache/hub/Qwen3*`

## API Judge Config

Do not delete this section. These values are required for Ark-based external judge runs in this workspace.

```bash
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b
```

## Current Default Benchmark

The default base benchmark is now:

- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

Legacy datasets are retained for reproduction only:

- `data/generated/craft_core_week1.jsonl`
- `data/generated/craft_core_hard.jsonl`

## External Step-Level Datasets

External step-level datasets are now wired into the repo through:

- `src/civic_prm/external_datasets.py`
- `scripts/import_external_dataset.py`

Current validated imports:

- `data/external/processbench_all.jsonl`
- `data/external/prm800k_train_sample32.jsonl`

These are connected as external-source inputs for the next benchmark pivot. They do **not** silently replace the current default benchmark yet.

List or import ProcessBench:

```bash
PYTHONPATH=src python scripts/import_external_dataset.py --dataset processbench --list-splits
PYTHONPATH=src python scripts/import_external_dataset.py --dataset processbench --split all
```

Import a PRM800K sample through the currently accessible Hub mirror:

```bash
PYTHONPATH=src python scripts/import_external_dataset.py --dataset prm800k --split train --limit 32 --streaming
```

Build a normalized `ProcessBench` whole-trace evaluation file:

```bash
PYTHONPATH=src python scripts/build_processbench_benchmark.py --split all
```

Build the `PB-Prefix` companion benchmark:

```bash
PYTHONPATH=src python scripts/build_processbench_prefix_benchmark.py
```

Run artifact audit on the normalized `ProcessBench` file:

```bash
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --output artifacts/external_datasets/processbench_eval_all_artifact_audit.json
```

Run a balanced visible-vs-masked API-judge pilot on `ProcessBench`:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/run_processbench_api_judge.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 8 \
  --seed 17 \
  --cache-output artifacts/external_datasets/processbench_api_judge_v3_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_api_judge_v3_summary.json'
```

Run frozen-backbone baselines on `ProcessBench` trace + prefix:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_frozen_baselines.py \
  --trace-dataset data/external/processbench_eval_all.jsonl \
  --prefix-dataset data/external/processbench_prefix_eval_all.jsonl \
  --prefix-source-limit-per-domain 200 \
  --output artifacts/external_datasets/processbench_frozen_baselines.json'
```

Run the first stronger-model whole-trace reranker on `ProcessBench`:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_reranker.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/external_datasets/processbench_reranker_8b.json \
  --batch-size 2 \
  --max-length 2048 \
  --seed 17'
```

This script scores the grouped `val + test` splits, reports final metrics on `test`, and also emits a `val -> test` threshold diagnostic in the JSON summary.

Aggregate the current `ProcessBench` main table:

```bash
PYTHONPATH=src python scripts/analyze_processbench_main_table.py
```

Build an external-source answer-swap pilot on maskable `ProcessBench` traces:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_processbench_answer_swap_pilot.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 8 \
  --seed 17 \
  --generation-cache-output artifacts/external_datasets/processbench_answer_swap_generation_rows.jsonl \
  --output data/external/processbench_answer_swap_pilot.jsonl \
  --summary-output artifacts/external_datasets/processbench_answer_swap_pilot_summary.json'
```

Run visible vs masked API-judge scoring on the answer-swap pilot:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_answer_swap_api_judge.py \
  --dataset data/external/processbench_answer_swap_pilot.jsonl \
  --cache-output artifacts/external_datasets/processbench_answer_swap_api_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_answer_swap_api_summary.json'
```

Build a small answer-matched repair-pair pilot from `ProcessBench` `invalid_correct` traces:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_processbench_repair_pilot.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 2 \
  --seed 17 \
  --min-audited-locus 1 \
  --generation-cache-output artifacts/external_datasets/processbench_repair_pd2_v3_generation_rows.jsonl \
  --output data/external/processbench_repair_pd2_v3_partial_pilot.jsonl \
  --summary-output artifacts/external_datasets/processbench_repair_pd2_v3_partial_pilot_summary.json'
```

Run visible vs masked API-judge scoring on the repair-pair pilot:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_repair_api_judge.py \
  --dataset data/external/processbench_repair_pd2_v3_partial_pilot.jsonl \
  --cache-output artifacts/external_datasets/processbench_repair_pd2_v3_api_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_repair_pd2_v3_api_summary.json'
```

Current status of this pilot:
- selected sources `= 8`
- successful repair pairs `= 8`
- current readout: visible `local_amcd = 0.375`, masked `local_amcd = 0.5`
- benchmark construction now works on this small pilot, but the external local-`AMCD` result is still negative-to-inconclusive for visible advantage

Materialize the canonical `ProcessBench` package summary and manifests:

```bash
PYTHONPATH=src python scripts/build_processbench_suite.py
```

Canonical package outputs:
- `artifacts/external_datasets/processbench_suite.json`
- `artifacts/external_datasets/processbench_suite.md`
- `artifacts/external_datasets/processbench_manifest.json`
- `artifacts/external_datasets/processbench_split_manifest.json`

Benchmark spec:
- `docs/processbench_benchmark.md`

## Week 1 Commands

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py --per-domain 12'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --quartets-per-domain 2 \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2b.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_rows.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v2.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2d.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_summary.json \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py \
  --difficulty hard_blindfix_v3 \
  --output data/generated/craft_core_hard_blindfix_v3.jsonl \
  --summary-output artifacts/audit/craft_core_hard_blindfix_v3_summary.json \
  --blind-audit-output artifacts/audit/blind_audit_hard_blindfix_v3_seedpacket.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v3.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2f_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2f_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairprune_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --max-candidates-per-role-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_ensemble_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_max'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_advmax_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --regenerate-from-candidate-input \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage2_regen.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage1_localprune.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_reviews.jsonl \
  --candidate-output-mode pruned \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 3 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.9 \
  --max-pair-detectability 0.8 \
  --reviewer-backend local_qwen'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage2_advmax.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k3_top2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 3 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_r2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 2 \
  --pair-regeneration-top-k 1 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_critic_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend local_qwen \
  --reviewer-model-root /cephfs/shared/hf_cache/hub/models--m-a-p--CriticLeanGPT-Qwen3-8B-RL/snapshots/2f9e8aa0e4965cfbd9ad9c0985c5fa1e944b4f40'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 1 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairgen_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --max-candidates-per-role-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairadv_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_paircontrast_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-contrast-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2f.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_summary.json \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py --max-quartets 6'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/run_api_judge_pilot.py --dataset data/generated/craft_core_hard.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_naturalized_slice.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_natural_transfer.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_generated_answer_swap_transfer.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_counterfactual_slice.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_natural_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --output artifacts/generated/model_generated_counterfactual_transfer.json \
  --feature-cache-dir artifacts/generated/counterfactual_features'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --max-quartets 9 \
  --output artifacts/generated/model_generated_counterfactual_qwen.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py \
  --domains graph_path \
  --require-auditable-original \
  --max-retries 4 \
  --output data/generated/craft_core_hard_model_generated_graph_v1.jsonl \
  --summary-output artifacts/generated/model_generated_graph_v1_summary.json \
  --cache-output artifacts/generated/model_generated_graph_v1_rows.jsonl \
  --attempt-log-output artifacts/generated/model_generated_graph_v1_attempts.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python scripts/merge_generated_eval_slices.py \
  --base-dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --keep-domains algebra \
  --append-dataset data/generated/craft_core_hard_model_generated_graph_counterfactual_v1.jsonl \
  --output data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --summary-output artifacts/generated/model_generated_hybrid_counterfactual_v1_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/run_api_judge_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --max-quartets 12 \
  --cache-output artifacts/generated/model_generated_hybrid_counterfactual_v1_api_rows.jsonl \
  --summary-output artifacts/generated/model_generated_hybrid_counterfactual_v1_api_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py \
  --domains blocksworld \
  --require-auditable-original \
  --use-blocksworld-scaffold \
  --max-retries 4 \
  --output data/generated/craft_core_hard_model_generated_blocksworld_v2.jsonl \
  --summary-output artifacts/generated/model_generated_blocksworld_v2_summary.json \
  --cache-output artifacts/generated/model_generated_blocksworld_v2_rows.jsonl \
  --attempt-log-output artifacts/generated/model_generated_blocksworld_v2_attempts.jsonl'
```

```bash
bash -lc 'python scripts/merge_generated_eval_slices.py \
  --base-dataset data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --append-dataset data/generated/craft_core_hard_model_generated_blocksworld_counterfactual_v2.jsonl \
  --output data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --summary-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json \
  --feature-cache-dir artifacts/generated/full_hybrid_repair_features_v1'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_naturalized_slice.py \
  --source-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --use-all-records \
  --output data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --summary-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_summary.json \
  --cache-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_rows.jsonl \
  --max-retries 0'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json \
  --feature-cache-dir artifacts/generated/full_hybrid_counterfactual_natural_repair_features_v1'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_mechanism_analysis.py \
  --output artifacts/generated/mechanism_analysis_full_hybrid.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_dual_head_transfer.py \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_dual_head.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_scanned_dual_head_transfer.py \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_scanned_dual_head.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_full_hybrid_structured.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_full_hybrid_natural.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-4B \
  --output artifacts/week4/qwen3_reranker_4b_full_hybrid_natural.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week5/qwen3_reranker_8b_hard.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week5_robustness.py \
  --output artifacts/week5/week5_robustness.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week6_reproduction.py \
  --output artifacts/week6/week6_reproduction.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run old:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_reviews.jsonl \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_acceptance_compare.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4_blocksworld_0008_bw1_only.jsonl \
  --output data/generated/craft_core_benchmark_v3_blocksworld_0008_accept_bw1.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run bw1:artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_summary.json:artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_acceptance_compare.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4_algebra_0010_alg1_only.jsonl \
  --output data/generated/craft_core_benchmark_v3_algebra_0010_accept_alg1.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run alg1:artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_summary.json:artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_acceptance_compare.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept_integrated.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run integrated:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_acceptance_compare.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_integrated.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl \
  --quartets-per-domain 2 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run integrated_smoke:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --run miniset:artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_acceptance_compare.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_reviews.jsonl \
  --quartets-per-domain 2 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax \
  --acceptance-mode ignore_semantic_only'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --quartets-per-domain 6 \
  --verbalizers-per-quartet 3 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax \
  --acceptance-mode ignore_semantic_only'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run midset:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run midset:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/export_benchmark_v3_from_acceptance.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_candidates.jsonl \
  --acceptance-analysis artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json \
  --run-label midset \
  --mode ignore_semantic_only \
  --output data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json'
```

Authoritative mid-scale benchmark-v3 export now lives at:

- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json`
- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

## Benchmark-V3 Default Mainline

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/audit/artifact_audit_benchmark_v3_midset.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/audit/blind_audit_benchmark_v3_midset.md \
  --answer-key-output artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --response-form-output artifacts/audit/blind_audit_benchmark_v3_midset_form.csv \
  --summary-output artifacts/audit/blind_audit_benchmark_v3_midset_summary.json \
  --sample-quartets 9 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/score_blind_audit.py \
  --answer-key artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --responses reviewer_a.csv reviewer_b.csv \
  --output artifacts/audit/blind_audit_benchmark_v3_midset_scored.json \
  --markdown-output artifacts/audit/blind_audit_benchmark_v3_midset_scored.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --batch-size 2 \
  --max-length 2048'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_benchmark_v3_robustness.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --baseline-artifact artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
  --reranker-artifact artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --output artifacts/benchmark_v3/benchmark_v3_robustness_summary.json'

bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset_seed23.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset \
  --seed 23'

bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset_seed31.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset \
  --seed 31'

bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_reproduction.py \
  --baseline-artifacts \
    artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
    artifacts/baselines/week2_baselines_benchmark_v3_midset_seed23.json \
    artifacts/baselines/week2_baselines_benchmark_v3_midset_seed31.json \
  --reranker-artifact artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --output artifacts/benchmark_v3/benchmark_v3_reproduction_summary.json'
```

## Resource Notes

- Data downloads should go under `data/`.
- `scripts/score_blind_audit.py` scores returned reviewer CSVs against the hidden key and emits JSON + markdown summaries.
- Local Week 4 model roots:
  - `/cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B`
  - `/cephfs/shared/hf_cache/hub/Qwen3-Reranker-4B`
  - `/cephfs/shared/hf_cache/hub/Qwen3-8B`
  - `/cephfs/shared/hf_cache/hub/Qwen3-4B`
- If later stages need external API usage or a larger model, record the planned budget first.
