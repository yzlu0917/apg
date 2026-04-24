# Round54: Putnam Harder-Domain Pilot

## Goal

Test whether the new `state-first -> Lean legality -> progress oracle -> frozen-hidden audit` pipeline still works on genuinely harder formal states, rather than the previous medium-difficulty slice that may still sit inside current prover comfort zones.

## New artifacts

- harder state extraction:
  - `scripts/extract_putnam_state_seeds.py`
  - `data/lean/state_first_putnam_seed_panel_v0.jsonl`
  - `artifacts/object_gate_round54/state_first_putnam_seed_panel_v0_summary.json`
- Putnam file-mode replay:
  - `scripts/replay_putnam_state_first_candidates.py`
- optional richer generation context:
  - `scripts/generate_state_first_candidates_with_api.py` now preserves `context_snippet`, `source_file`, `proof_state`, `project_root`, and related Putnam metadata
- tiny harder pilot:
  - `data/lean/state_first_putnam_seed_panel_v0_pilot.jsonl`
  - `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0.jsonl`
  - `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed.jsonl`
  - `artifacts/object_gate_round54/state_first_putnam_candidates_pilot_v0_replayed_summary.json`
  - `data/annotations/state_first_progress_oracle_putnam_pilot_v0.jsonl`
  - `artifacts/object_gate_round54/deepseek_putnam_pilot_sep.json`
  - `artifacts/object_gate_round54/goedel_putnam_pilot_sep.json`

## What changed

The previous round53 harder slice still came from the project’s own Lean states. This round switched the source itself:

- extracted real harder states from Putnam project files using **project-aware REPL file mode**
- stopped trying to force theorem statements through the old mathlib command-mode wrapper
- replayed candidate tactics directly on Putnam `proofState`s

## Harder seed extraction

Using:

- `Putnam/putnam_1976_b5_sol.lean`
- `Putnam/putnam_1993_a4_sol.lean`
- `Putnam/putnam_2013_b4_sol.lean`

the extractor produced:

- `14` nonempty harder seed states
- `4` from `putnam_1976_b5`
- `1` from `putnam_1993_a4`
- `9` from `putnam_2013_b4`

This is the first repo-owned harder-state source that is clearly beyond the previous medium panel.

## Tiny harder pilot

Pilot states:

- `coeff_X_sub_C_pow__sorry0`
- `finite_diff_identity__sorry1`
- `putnam_1993_a4__sorry0`
- `putnam_2013_b4__sorry4`

Candidate generation:

- `24` API-generated candidates total

Lean replay:

- `16 / 24` replay-ok
- `8 / 24` replay-error

Per-state replayability:

- `coeff_X_sub_C_pow__sorry0`: `3 / 6`
- `finite_diff_identity__sorry1`: `3 / 6`
- `putnam_1993_a4__sorry0`: `6 / 6`
- `putnam_2013_b4__sorry4`: `4 / 6`

So the harder pipeline is not empty or purely symbolic; it already supports candidate generation and legality filtering on real Putnam states.

## Tiny harder oracle

A first manual oracle was added for the `16` replay-ok candidates:

- `coeff_X_sub_C_pow__sorry0`
- `finite_diff_identity__sorry1`
- `putnam_1993_a4__sorry0`
- `putnam_2013_b4__sorry4`

This oracle is intentionally tiny and should be read as a pilot diagnosis, not a final panel.

Pair counts:

- gap task: `27` pairs
  - `19 ordered`
  - `8 equivalent`
- direction task: `38` examples

## Frozen-hidden audit on Putnam pilot

### DeepSeek

- gap:
  - linear AUROC `0.8783`
  - centroid AUROC `0.9013`
- direction:
  - linear AUROC `0.3324`
  - centroid AUROC `0.2659`

### Goedel

- gap:
  - linear AUROC `0.7961`
  - centroid AUROC `0.8980`
- direction:
  - linear AUROC `0.3352`
  - centroid AUROC `0.3573`

## Readout

This is the most important conclusion of round54:

- on genuinely harder Putnam-source states, **coarse gap signal still exists**
  - hidden can still separate `ordered` vs `equivalent` better than random
- but **fine direction signal collapses**
  - `better-minus-worse` vs `worse-minus-better` is now sub-random in both prover families

So compared with the earlier `17`-state project-owned oracle panel:

- the stronger claim no longer cleanly transfers
- the previous “hard” slice really was not hard enough to expose this failure mode

## Current interpretation

Round54 supports a more careful statement:

- latent progress signal is real
- but its robustness is **difficulty-dependent**
- on harder Putnam-source states, the signal seems to survive first as a **coarse progress / non-progress distinction**
- while the **directional ordering signal** is no longer robust

## Next step

The right next step is not to sweep more recipes yet. It is to:

1. expand the Putnam pilot from `4` to a somewhat larger hard oracle slice
2. check whether direction collapse is a tiny-sample artifact or a stable harder-domain boundary
3. only then decide whether to push method changes
