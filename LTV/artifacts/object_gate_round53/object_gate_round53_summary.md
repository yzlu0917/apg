## Round53 Summary

### Goal

Test two mechanism questions on the new `state-first -> Lean legality -> human oracle` mainline:

1. Does the hidden progress signal materially weaken on the harder `v2_hard` slice?
2. Does `before hidden` itself carry state-level value / hardness information?

### Inputs

- Hard slice oracle: `data/annotations/state_first_progress_oracle_batch_v2_hard.jsonl`
- Consensus panel oracle: `data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl`
- Generated candidates: `artifacts/object_gate_round50/state_first_candidates_panel_v2_generated.jsonl`
- Replayed candidates: `artifacts/object_gate_round50/state_first_candidates_panel_v2_replayed.jsonl`

### New artifacts

- `artifacts/object_gate_round53/deepseek_state_first_hard_slice_sep.json`
- `artifacts/object_gate_round53/goedel_state_first_hard_slice_sep.json`
- `artifacts/object_gate_round53/deepseek_before_state_value.json`
- `artifacts/object_gate_round53/goedel_before_state_value.json`

### Hard-slice separability

The harder 6-state slice remains strongly separable.

DeepSeek:
- gap task linear AUROC = `0.8913`
- direction task linear AUROC = `0.9926`

Goedel:
- gap task linear AUROC = `0.8592`
- direction task linear AUROC = `0.9702`

Relative to the full `17`-state consensus panel:
- gap task weakens a bit
  - DeepSeek: `0.9085 -> 0.8913`
  - Goedel: `0.8874 -> 0.8592`
- direction task does **not** weaken
  - DeepSeek: `0.9490 -> 0.9926`
  - Goedel: `0.9148 -> 0.9702`

Interpretation:
- harder states do not collapse the candidate-level progress signal
- the main cost is only on `ordered vs equivalent` gap discrimination
- `better vs worse` ordering remains extremely clean

### Before-hidden state-value audit

`before hidden` carries real but weaker state-level signal.

State-level targets:
- binary hardness = `1 iff the state has at least one neutral/weak_partial candidate`
- mean tier regression = average oracle tier over replay-ok candidates

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

Interpretation:
- `before hidden` is not empty
- it does carry a state-level hardness / value signal
- but this signal is clearly weaker than the candidate-level `after hidden` progress signal

### Current read

Round53 supports a cleaner mechanism split:

- `after hidden` / candidate-local hidden contains the strong pairwise progress signal
- `before hidden` contains a weaker state-value / hardness signal
- the current positive results are therefore not just a trivial `before-state` shortcut

### Implication

The most natural next method question is no longer "is there signal?" but:

> should the next scorer combine a weak state-value head from `before hidden`
> with the stronger candidate-progress head from `after hidden`?
