# Order Audit Summary 2026-03-31

## Setup

- original slice: `data/interim/object_dev_v0_active_slice_v3.jsonl`
- swapped slice: `data/interim/object_dev_v0_active_slice_v3_swapped.jsonl`
- size: `12`
- families:
  - `style_flip = 9`
  - `substance_flip = 3`

## Metrics

### Qwen3-0.6B base

- expected swap rate: `0.083`
- tie stability rate: `0.0`
- non-tie flip rate: `0.0`

Interpretation:

- severe A-position bias
- almost never behaves as if swapping order changed semantics

### Qwen3-0.6B critic

- expected swap rate: `0.083`
- tie stability rate: `0.0`
- non-tie flip rate: `0.0`

Interpretation:

- same severe A-position bias as 0.6B base

### Qwen3-4B base

- expected swap rate: `0.5`
- tie stability rate: `0.333`
- non-tie flip rate: `0.667`

Interpretation:

- materially better than 0.6B
- still substantially order-sensitive on tie cases

### Qwen3-4B critic

- expected swap rate: `0.583`
- tie stability rate: `0.333`
- non-tie flip rate: `0.667`

Interpretation:

- slightly better than 4B base on order response overall
- still fails to stabilize tie judgments under swap

## Main Finding

- The current active-family signal is real enough for Object gate continuation.
- But Audit gate is clearly not passed:
  - low-capacity judges are dominated by position bias
  - even 4B judges show substantial order sensitivity on `style_flip`

## Consequence

From this point on:

- all future judge evaluation should be order-balanced or at least order-randomized
- `style_flip` should not be treated as a fully audited family yet
- any object-level claim must be phrased as provisional until order controls are added
