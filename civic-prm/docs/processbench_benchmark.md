# ProcessBench Benchmark Spec

## Purpose

`ProcessBench` is the repo's external-source benchmark package for
process-verification corroboration. It is meant to answer:

- does the main answer-leakage story survive on real step-level traces,
- do visible and masked views behave differently on external-source data,
- can we build small external-source counterfactual stresses without returning
  to self-generated source problems.

It is **not** a matched-quartet replacement for `CRAFT`.

## Data Sources

- raw import: `data/external/processbench_all.jsonl`
- normalized whole-trace benchmark: `data/external/processbench_eval_all.jsonl`
- normalized prefix benchmark: `data/external/processbench_prefix_eval_all.jsonl`

The source label semantics follow `ProcessBench`:

- `label == -1`: no incorrect step annotated, treat as `process_valid = true`
- `label >= 0`: first incorrect step index, treat as `process_valid = false`

## Tasks

### 1. PB-Trace

Whole-trace process-validity scoring.

Primary metrics:
- AUROC
- accuracy
- invalid-answer gap

### 2. PB-Prefix

Prefix-level error-onset detection.

Primary metrics:
- AUROC
- accuracy
- boundary-drop mean

### 3. External Answer Swap

Observed/swapped pairs that keep the reasoning fixed and change only the final
answer span.

Primary metric:
- visible vs masked mean absolute score delta

Role:
- external-source `ASS` stress

### 4. External Local Repair

Observed/repaired pairs built from `invalid_correct` traces while keeping the
final answer span fixed.

Primary metric:
- visible vs masked local discrimination

Role:
- minimal external-source local-`AMCD` style stress

## Current Standard Artifacts

- trace summary:
  - `artifacts/external_datasets/processbench_eval_all_summary.json`
- prefix summary:
  - `artifacts/external_datasets/processbench_prefix_eval_all_summary.json`
- main table:
  - `artifacts/external_datasets/processbench_main_table.json`
  - `artifacts/external_datasets/processbench_main_table.md`
- answer-swap summary:
  - `artifacts/external_datasets/processbench_answer_swap_api_summary.json`
- local-repair summary:
  - `artifacts/external_datasets/processbench_repair_pd2_v3_api_summary.json`
- package summary:
  - `artifacts/external_datasets/processbench_suite.json`
  - `artifacts/external_datasets/processbench_suite.md`
- package manifest:
  - `artifacts/external_datasets/processbench_manifest.json`
- split manifest:
  - `artifacts/external_datasets/processbench_split_manifest.json`

## Recommended Commands

Aggregate the current benchmark package:

```bash
PYTHONPATH=src python scripts/build_processbench_suite.py
```

This command does not rerun models. It reads the current authoritative
artifacts and produces:

- `processbench_suite.json`
- `processbench_suite.md`
- `processbench_manifest.json`
- `processbench_split_manifest.json`

The split manifest pins the canonical grouped split used by the current frozen
and reranker evaluations, including the prefix-source cap used for `PB-Prefix`.

## Current Interpretation

`ProcessBench` is now mature enough to serve as an external-source benchmark
package:

- `PB-Trace` and `PB-Prefix` are stable
- external answer-swap stress is working
- the current local-repair pilot now fully materializes on its selected subset

What it still does **not** do:

- replace `CRAFT` matched quartets,
- provide a full external-source `AMCD/ASS` benchmark identical to the CRAFT
  counterfactual protocol,
- replace the `CRAFT-Deploy` deployment stress benchmark.

## Intended Role in the Paper

- `CRAFT-Deploy`: main deployment benchmark
- `CRAFT-Clean`: cleaner counterfactual audit benchmark
- `ProcessBench`: external-source corroboration benchmark package
