# Round48: combined dev+medium oracle panel separability audit

## Goal

Test whether the positive object-gate result survives after adding a medium-difficulty oracle slice.

## Combined Panel

- oracle file:
  - `data/annotations/state_first_progress_oracle_panel_v1_combined.jsonl`
- generated states:
  - `artifacts/object_gate_round48/state_first_candidates_panel_v1_generated.jsonl`
- replayed states:
  - `artifacts/object_gate_round48/state_first_candidates_panel_v1_replayed.jsonl`

## Panel Size

- `num_states = 11`
- `num_candidates = 67`
- tier counts:
  - `solved = 25`
  - `strong_partial = 29`
  - `weak_partial = 11`
  - `neutral = 2`
- pair counts:
  - `ordered = 93`
  - `equivalent = 87`

## Main Result

The positive separability result not only survives the medium expansion; it becomes stronger.

### DeepSeek-Prover-V2-7B

- gap task:
  - `linear AUROC = 0.8802`
  - `centroid AUROC = 0.8215`
- direction task:
  - `linear AUROC = 0.8806`
  - `centroid AUROC = 0.9733`

### Goedel-Prover-V2-8B

- gap task:
  - `linear AUROC = 0.8910`
  - `centroid AUROC = 0.8171`
- direction task:
  - `linear AUROC = 0.9269`
  - `centroid AUROC = 0.9761`

## Geometry

### DeepSeek

- gap task:
  - `centroid_gap = 0.1540`
  - `fisher_ratio = 0.0329`
  - `loo_1nn_acc = 0.8556`
- direction task:
  - `centroid_gap = 0.6800`
  - `fisher_ratio = 0.2426`
  - `loo_1nn_acc = 0.9355`

### Goedel

- gap task:
  - `centroid_gap = 0.1692`
  - `fisher_ratio = 0.0442`
  - `loo_1nn_acc = 0.8444`
- direction task:
  - `centroid_gap = 0.8014`
  - `fisher_ratio = 0.3885`
  - `loo_1nn_acc = 0.9355`

## Interpretation

- The initial positive result was not an artifact of the easy 5-state batch.
- After adding medium-difficulty states, both:
  - ordered-vs-equivalent gap detection
  - better-vs-worse direction detection
  remain strongly separable in frozen hidden states.
- This is now substantially stronger object evidence than the original proxy-only CTS story.

## Limits

- still single-annotator
- still small enough to count as a small final panel, not a large benchmark
- tactic generation occasionally violates format (`9` candidates instead of `8`, composite forms, unsupported tactics), so upstream generation normalization can still improve

## Next

- freeze this panel as `small final oracle panel v1`
- optionally add a second annotator for disagreement audit
- only after that, consider moving from object gate toward method conversion
