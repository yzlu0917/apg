# CAVE

CAVE is a standalone research workspace for studying causal verifier usage in
language-model self-correction.

## Current phase

The project is in `phase 0 bootstrap`. The immediate objective is to turn the
proposal into an executable research program without starting large-scale
training or sweeps.

Primary references:

- `proposal.md`: long-form proposal and motivation
- `docs/phase0_bootstrap.md`: claim hierarchy, fallback framing, gates, and
  near-term plan
- `docs/object_gate_min_loop.md`: first reproducible Object gate loop
- `progress.md`: current milestone tracker
- `results.md`: reproducible result log

## Environment

- Conda environment: `infer`
- Local models: `/cephfs/shared/hf_cache/hub/Qwen3*`
- Data root: `data/`
- Lightweight artifacts: `artifacts/`
- Ask before introducing new packages or paid API usage

## Layout

- `docs/`: project docs and phase plans
- `scripts/`: lightweight validation and bootstrap utilities
- `data/object_gate_seed/`: seed assets for the first Object gate loop
- `artifacts/object_gate/`: generated reports for the Object gate
- `history/`: archival notes if the project branches or major decisions change

## Working rule

Until the Object gate passes, the headline claim stays at the object level:
whether verifier-mediated revision is a distinct and measurable object, not yet
whether the proposed method or downstream deployment claims hold.
