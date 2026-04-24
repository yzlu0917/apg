# Object Gate Round15 Summary

Round15 tests a low-rank bilinear / energy-style conditional scorer on the main DeepSeek Lean object-gate setup.

This round asks:

- after raw concat fails and simple interaction only partially helps,
- can a structured conditional scorer over `(h^-, delta)` finally beat bare `delta`?

The new scorer is:

- `conditional_bilinear_prob`

with structure:

- `score(h, d) = linear(h) + linear(d) + <A h, B d>`

where `A` and `B` are learned low-rank projections.

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
- bilinear rank:
  - `32`

Compared against:

- `post_mlp_prob`
- `transition_mlp_prob`
- round13 raw concat baseline
- round14 interaction baseline

## Main result

The low-rank bilinear conditional scorer is a clear negative result on this setup.

It is worse than:

- bare `transition`
- best `post-state`
- the round14 interaction baseline

## Key comparison

- `post_mlp_prob`
  - `AUROC = 0.9499`
  - `accuracy = 0.9747`
  - `brier = 0.0267`
- `transition_mlp_prob`
  - `AUROC = 0.9837`
  - `accuracy = 0.9367`
  - `brier = 0.0567`
- `interaction_transition_mlp_prob`
  - `AUROC = 0.9563`
  - `accuracy = 0.9367`
  - `brier = 0.0652`
- `conditional_bilinear_prob`
  - `AUROC = 0.7145`
  - `accuracy = 0.8861`
  - `brier = 0.1139`
  - `earliest_fail = 0.6923`

This is not a marginal miss.

It is substantially worse than every competitive baseline in the current object-gate panel.

## Interpretation

Round15 does **not** support:

- “a more structured conditional scorer is enough”

At least on this single-point local-soundness protocol, the current bilinear scorer underperforms badly.

This does not prove that conditional scoring is wrong in principle.

But it does strongly suggest:

- continuing to improve conditional scorers inside the same single-point objective is now low-leverage

## Updated method reading

After rounds 13-15:

1. raw concat is a bad conditional baseline
2. simple interaction is better, but still below bare `delta`
3. low-rank bilinear scoring on the same objective fails badly

So the most plausible next move is no longer:

- better single-point conditional scorer engineering

It is:

- move to pairwise / contrastive objectives that directly optimize same/flip behavior

## Best next move

1. freeze current conditional baselines as:
   - raw concat: negative
   - interaction: stronger but insufficient
   - bilinear: negative
2. stop local scorer tinkering on this branch
3. if continuing, move directly to pairwise / contrastive training
