# Round52 Summary

## Goal

Enter the method layer on top of the frozen consensus oracle panel and train the first explicit **pairwise progress scorer**.

## Method

Instead of training a large semantic judge, round52 trains a state-local latent value model:

- input: frozen `h_plus` candidate representation
- target: oracle progress tier on the current `before state`
- loss:
  - pointwise tier regression
  - ordered-pair ranking
  - equivalent-pair consistency

Evaluation is leave-one-state-out on the frozen `17`-state consensus panel.

## Files

- Training / evaluation script: [train_state_first_progress_scorer.py](/cephfs/luyanzhen/apg/LTV/scripts/train_state_first_progress_scorer.py)
- DeepSeek result: [deepseek_state_first_progress_scorer.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round52/deepseek_state_first_progress_scorer.json)
- Goedel result: [goedel_state_first_progress_scorer.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round52/goedel_state_first_progress_scorer.json)

## Key Results

DeepSeek:

- linear scorer:
  - `ordered_pair_accuracy = 0.9576`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9974`
  - `equivalent_abs_gap_mean = 3.1510`
- MLP scorer:
  - `ordered_pair_accuracy = 0.9330`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9908`
  - `equivalent_abs_gap_mean = 2.2005`

Goedel:

- linear scorer:
  - `ordered_pair_accuracy = 0.9488`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9947`
  - `equivalent_abs_gap_mean = 2.2743`
- MLP scorer:
  - `ordered_pair_accuracy = 0.9237`
  - `top1_max_tier_hit_rate = 1.0000`
  - `mean_ndcg = 0.9896`
  - `equivalent_abs_gap_mean = 3.0379`

## Readout

The first method-layer result is positive:

- a trainable pairwise progress scorer can be fit on top of the current oracle panel
- it generalizes under held-out-state evaluation
- and the simplest scorer (`linear`) is currently the strongest baseline in both prover families

This is a useful update in framing:

> we are no longer only showing that hidden states are separable; we now have a first trainable latent progress scorer that recovers the oracle ordering under leave-one-state-out evaluation.

The main remaining weakness is calibration on equivalent pairs: the scorer separates ordered pairs well, but its absolute score gaps within equivalent sets are still too large.
