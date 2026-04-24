# Object Gate Round16 Summary

Round16 ports a CLUE-style non-parametric geometric verifier into the current DeepSeek Lean object-gate setup.

This round asks:

- instead of inventing more single-point scorers,
- does a borrowed hidden-state clustering verifier work better?

The new baseline is:

- `transition_clue_proto`

with structure:

- normalize `delta_h`
- build separate success / failure prototype sets with per-class k-means
- score by nearest-prototype distance gap

This is a minimal CLUE-style adaptation, not a full reproduction of the paper.

## Setup

- model: `DeepSeek-Prover-V2-7B`
- fixed data: `data/lean/lean_mini_v0_round7.jsonl`
- fixed features: round7 `boundary_states.pt`
- size:
  - `79` step examples
  - `40` theorems
  - `66` positive
  - `13` negative
- grouped CV:
  - leave-one-theorem-out
- CLUE-style config:
  - `delta_h` only
  - `4` prototypes per class

## Main result

The borrowed CLUE-style baseline is useful, but not dominant.

It is better than the simplest geometry baseline:

- `transition_centroid_cosine`

but still clearly worse than:

- `transition_mlp_prob`

## Key comparison

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

So the CLUE-style move helps relative to a single-centroid geometry readout, but does not beat the learned `transition` head.

## Interpretation

Round16 supports two narrower conclusions:

1. borrowing prior verifier structure is better than continuing blind local scorer tinkering
2. in this step-level Lean local-soundness setting, the minimal CLUE-style adaptation is not yet the best discriminator

This is a meaningful result because it separates two questions:

- was our own scorer search missing something obvious?
- yes, there was a better non-parametric geometry baseline to try

and

- does that baseline solve the object-gate problem here?
- not yet

## Updated method reading

After round16, the most accurate reading is:

- the best current single-point discriminator on this setup is still `transition_mlp_prob`
- the best borrowed geometry-style discriminator is `transition_clue_proto`
- but it remains below the best learned transition readout

This suggests a likely task mismatch:

- CLUE is naturally closer to trace-level / candidate-level experience verification
- our current benchmark is step-level local-soundness discrimination

## Best next move

1. keep `transition_clue_proto` as the strongest current geometry baseline
2. stop local single-point scorer tinkering
3. if continuing the “borrowed method” route, move to pairwise / contrastive objectives rather than more classifier variants
