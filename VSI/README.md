# Research Workspace
- 你可以使用/cephfs/shared/hf_cache/hub/Qwen3* 系列的模型（开始实验可以使用1.7B或4B的模型），可以暂时不考虑多模型交叉（一定需要的话你可以告知用户，用户方下载）
- 需要的数据可以下载放到data目录下
- 可以使用的conda环境是infer（大部分环境已经装好了，如果还需要一些额外的包或者工具和用户确认）
- 如果你需要api调用来做数据或是别的这里也给你提供（需要给出用量和金额预算）
deepseek-v3.2:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  endpoint: ep-20251213141929-gk2jb
  api_key: 8da5e4ba-59ad-47af-8f87-005fd1d1641b

## Project bootstrap entry points

- phase-0 framing and gates: `docs/phase0_bootstrap.md`
- active status and resume point: `progress.md`
- reproducible result log: `results.md`
- first object-gate bootstrap:

```bash
python scripts/object_gate_bootstrap.py \
  --config configs/object_gate_microbench.json \
  --out artifacts/object_gate/bootstrap_summary.json
```

- first hybrid model-in-the-loop smoke test:

```bash
conda run -n infer python scripts/hybrid_object_gate.py \
  --config configs/hybrid_object_gate.json \
  --out artifacts/object_gate/hybrid_smoke.json
```

- API-backed hybrid smoke test:

```bash
VSI_API_KEY=... conda run -n infer python scripts/hybrid_object_gate.py \
  --config configs/hybrid_object_gate_api.json \
  --out artifacts/object_gate/hybrid_api_smoke.json
```

- API-backed mini-family run:

```bash
VSI_API_KEY=... conda run -n infer python scripts/hybrid_object_family.py \
  --config configs/hybrid_object_family_api.json \
  --out artifacts/object_gate/hybrid_api_family.json
```

- rewrite audit:

```bash
VSI_API_KEY=... conda run -n infer python scripts/rewrite_audit.py \
  --config configs/rewrite_audit_api.json \
  --out artifacts/object_gate/rewrite_audit_api.json
```

- exploitability code tasks:

```bash
VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_api.json \
  --out artifacts/object_gate/exploit_code_tasks_api.json
```

- non-arithmetic string ambiguity family:

```bash
VSI_API_KEY=... conda run -n infer python scripts/string_ambiguity_family.py \
  --config configs/string_ambiguity_family_api.json \
  --out artifacts/object_gate/string_ambiguity_family_api.json
```

- generate larger-sample configs:

```bash
python scripts/generate_string_ambiguity_tasks.py --out configs/string_ambiguity_family_large_api.json
python scripts/generate_exploit_code_tasks.py --out configs/exploit_code_tasks_large_api.json
```

- large-sample runs:

```bash
VSI_API_KEY=... conda run -n infer python scripts/string_ambiguity_family.py \
  --config configs/string_ambiguity_family_large_api.json \
  --out artifacts/object_gate/string_ambiguity_family_large_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/exploit_code_tasks_large_api.json
```

- frozen-slice summary:

```bash
python scripts/summarize_frozen_slices.py \
  --slices configs/frozen_slices_phase0.json \
  --string-artifact artifacts/object_gate/string_ambiguity_family_large_api.json \
  --exploit-artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/frozen_slices_summary.json
```

- minimal conversion protocols:

```bash
python scripts/conversion_string_ambiguity.py \
  --config configs/conversion_string_ambiguity.json \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/string_ambiguity_family_large_api.json \
  --out artifacts/object_gate/conversion_string_ambiguity.json

python scripts/conversion_exploit_routing.py \
  --config configs/conversion_exploit_routing.json \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_routing.json

python scripts/conversion_exploit_alternatives.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_alternatives.json

python scripts/conversion_exploit_learned.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_learned.json

python scripts/conversion_exploit_agreement.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_agreement.json

conda run -n infer python scripts/conversion_exploit_trained_verifier.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_trained_verifier.json
```

- narrow training-based conversion probe on the numeric exploit subset:

```bash
conda run -n infer python scripts/train_numeric_rule_solver.py \
  --slices configs/frozen_slices_phase0.json \
  --out artifacts/object_gate/train_numeric_rule_solver.json
```

- transfer probe for family coverage vs family shift:

```bash
conda run -n infer python scripts/train_numeric_rule_transfer.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/train_numeric_rule_transfer.json
```

- OOD held-out family probe:

```bash
conda run -n infer python scripts/train_numeric_rule_ood_family.py \
  --out artifacts/object_gate/train_numeric_rule_ood_family.json
```

- API-backed OOD exploit family plus training eval:

```bash
python scripts/generate_exploit_code_tasks_ood.py \
  --out configs/exploit_code_tasks_ood_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_ood_api.json \
  --out artifacts/object_gate/exploit_code_tasks_ood_api.json

conda run -n infer python scripts/train_numeric_rule_api_ood.py \
  --artifact artifacts/object_gate/exploit_code_tasks_ood_api.json \
  --out artifacts/object_gate/train_numeric_rule_api_ood.json
```

- non-numeric API-backed exploit family plus training eval:

```bash
python scripts/generate_exploit_string_tasks_ood.py \
  --out configs/exploit_string_tasks_ood_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_string_tasks_ood_api.json \
  --out artifacts/object_gate/exploit_string_tasks_ood_api.json

conda run -n infer python scripts/train_string_rule_api_ood.py \
  --artifact artifacts/object_gate/exploit_string_tasks_ood_api.json \
  --out artifacts/object_gate/train_string_rule_api_ood.json
```

- stronger semantic-v2 exploit family plus training eval:

```bash
python scripts/generate_exploit_string_tasks_v2.py \
  --out configs/exploit_string_tasks_v2_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/exploit_string_tasks_v2_api.json

conda run -n infer python scripts/train_string_rule_api_v2.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/train_string_rule_api_v2.json
```

- structured upper-bound probe for semantic-v2:

```bash
python scripts/train_string_rule_api_v2_library.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/train_string_rule_api_v2_library.json
```

- stronger learned neural decoder for semantic-v2:

```bash
conda run -n infer python scripts/train_string_rule_api_v2_neural.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --repeats 24 \
  --epochs 180 \
  --out artifacts/object_gate/train_string_rule_api_v2_neural.json
```

- no-coverage semantic transfer probe for semantic-v2:

```bash
conda run -n infer python scripts/train_string_rule_semantic_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --repeats 24 \
  --epochs 180 \
  --out artifacts/object_gate/train_string_rule_semantic_transfer.json
```

- small seq2seq / LM-style transfer probe:

```bash
conda run -n infer python scripts/train_string_seq2seq_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference,v1_to_v2_transfer \
  --repeats 6 \
  --epochs 40 \
  --out artifacts/object_gate/train_string_seq2seq_transfer_small.json

conda run -n infer python scripts/train_string_seq2seq_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference \
  --repeats 12 \
  --epochs 120 \
  --out artifacts/object_gate/train_string_seq2seq_coverage_only.json
```

- heavier decoder-only transformer LM probe:

```bash
conda run -n infer python scripts/train_string_transformer_lm_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference,v1_to_v2_transfer \
  --repeats 12 \
  --epochs 20 \
  --batch_size 64 \
  --out artifacts/object_gate/train_string_transformer_lm_transfer.json

conda run -n infer python scripts/train_string_transformer_lm_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference \
  --repeats 24 \
  --epochs 80 \
  --batch_size 64 \
  --out artifacts/object_gate/train_string_transformer_lm_coverage_only.json
```
