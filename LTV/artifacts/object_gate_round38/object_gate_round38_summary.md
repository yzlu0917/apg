# Round38: Lean replay environment hook

## Goal

Connect a reusable Lean+Mathlib replay environment into the project without creating a new local Lean workspace.

## Outcome

- Verified that the repository itself is **not** a Lean project and should not be treated as one.
- Reused the existing local Mathlib workspace at `/root/mathlib4-4.15.0`.
- Reused the REPL subproject at `/root/mathlib4-4.15.0/repl`.
- Added a project-owned smoke harness:
  - `configs/object_gate/lean_replay_env_v0.yaml`
  - `data/lean/repl_smoke_v0.in`
  - `scripts/run_lean_repl_smoke.py`

## What this proves

- The project can call an external Lean+Mathlib REPL from a repo-owned wrapper.
- The minimal tactic-mode smoke interaction works end-to-end.
- The current project-owned smoke run produced:
  - `returncode = 0`
  - `num_responses = 3`
  - `proof_states_returned = [1, 2]`
  - `final_goals_count = 0`

## What this does not prove

- Proof-state extraction is not implemented yet.
- Pairwise progress labels are still `proxy_only`.
- Variant replay for CTS rows has not been wired up yet.

## Next step

Build the first project-owned replay / extraction pass on top of this environment hook.
