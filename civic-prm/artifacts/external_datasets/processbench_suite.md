# ProcessBench Benchmark Suite

## Role

- External-source corroboration benchmark package.
- Not a matched-quartet replacement for CRAFT.
- Canonical spec: `docs/processbench_benchmark.md`

## PB-Trace

- Records: `3400`
- Best model by AUROC: `frozen_step_only` (`0.8759`)
- Canonical split counts: train `2380`, val `510`, test `510`

## PB-Prefix

- Records: `25697`
- Best model by AUROC: `frozen_step_only` (`0.6918`)
- Canonical split counts: train `4003`, val `827`, test `891`

## External Counterfactuals

- Answer-swap pairs: `31`
- Answer-swap mean abs delta: visible `0.3226`, masked `0.0645`, gap `0.2581`
- Local-repair pairs: `8 / 8`
- Local repair discrimination: visible `0.3750`, masked `0.5000`, gap `-0.1250`

## Takeaways

- Best trace verifier: `frozen_step_only`
- Best prefix verifier: `frozen_step_only`
- Best reranker: `reranker8_visible`
- Visible reranker accuracy: default `0.3490`, val-tuned `0.6980`
- Answer sensitivity transfers: `True`
- Local repair construction closed on current pilot: `True`
- Visible local-repair advantage observed: `False`
