# Round40: first CTS variant replay smoke

## Goal

Replay a smoke subset of CTS source/variant candidates from the same shared pre-state and bucket them by Lean replay outcome.

## Outcome

- Added a project-owned CTS replay script:
  - `scripts/run_cts_variant_replay_smoke.py`
- Produced a smoke replay bucket:
  - `artifacts/object_gate_round40/cts_variant_replay_smoke.jsonl`
- Produced a smoke summary:
  - `artifacts/object_gate_round40/cts_variant_replay_smoke_summary.json`

## Intended proof

- The project can take a CTS row plus its raw theorem trace,
- reconstruct the shared pre-state from theorem header + prefix steps + `sorry`,
- replay source and variant separately,
- and record:
  - shared before-goals
  - source replay status / after-goals
  - variant replay status / after-goals

## Verified result

- smoke subset size: `8` pairs
- `shared_pre_state_ok = 8/8`
- `source_replay_ok = 8/8`
- `variant_replay_ok = 6/8`
- `variant_lean_error = 2/8`
- current Lean-error examples:
  - `cts_flip_and_comm_1`
  - `cts_flip_eq_comm_api_1`

## Boundary

- This is still a smoke subset, not full CTS replay coverage.
- It is only intended to prove that CTS can now be turned into Lean replay buckets from inside the repo.
