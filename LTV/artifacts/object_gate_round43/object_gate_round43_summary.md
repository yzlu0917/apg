# Round43: state-first generation scaffold

## Goal

Switch the main data path from old CTS repair to a state-first candidate-generation workflow:

- choose a clean set of Lean before-states
- generate candidate tactics from those states
- let Lean filter legality
- reserve human annotation as the progress oracle

## Outcome

- Added generation config:
  - `configs/object_gate/state_first_candidate_generation_v0.yaml`
- Added prompt scaffold:
  - `prompts/object_gate/state_first_candidate_generation_v0.txt`
- Added seed-builder:
  - `scripts/build_state_first_seed_panel.py`
- Built the first seed panel:
  - `data/lean/state_first_seed_panel_v0.jsonl`

## Verified result

- seed states: `26`
- unique theorems: `26`
- max step index: `4`
- seed source:
  - replay-ok source states from `artifacts/object_gate_round41/cts_variant_replay_full.jsonl`

## Current environment status

- No external generation API key was found in the current shell for:
  - `OPENAI_API_KEY`
  - `DEEPSEEK_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DASHSCOPE_API_KEY`
  - `OPENROUTER_API_KEY`

## Meaning

- The new mainline is now explicit and repo-owned.
- Candidate generation can start as soon as an API backend is available.
- Human annotation remains the intended progress oracle; generation is only for candidate proposal.
