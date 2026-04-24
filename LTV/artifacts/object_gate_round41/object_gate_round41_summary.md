# Round41: full CTS replay bucket

## Goal

Scale the first CTS replay smoke from `8` pairs to the full current `58`-pair scaffold and measure the legality buckets needed before pairwise progress judging.

## Outcome

- Produced a full-slice CTS replay bucket:
  - `artifacts/object_gate_round41/cts_variant_replay_full.jsonl`
- Produced a full-slice summary:
  - `artifacts/object_gate_round41/cts_variant_replay_full_summary.json`

## Verified result

- `num_pairs_attempted = 58`
- `shared_pre_state_ok = 58/58`
- `source_replay_ok = 58/58`
- `variant_replay_ok = 32/58`
- `variant_lean_error = 26/58`
- split by current proxy pair type:
  - `same`: `29 ok / 1 error`
  - `flip`: `3 ok / 25 error`

## Important boundary

- The current replay wrapper is already good enough to separate a large hard-failure bucket from replayable candidates.
- But it is still a **single-tactic** replay wrapper.
- At least one `same` pair fails for wrapper-level reasons rather than semantic invalidity:
  - `lean_false_elim_pos__step1__plausible_flip__same__811e22f0`
  - variant tactic: `exfalso; exact h`
  - current REPL wrapper treats it as a single tactic command and gets `expected end of input`

## Meaning

- Lean legality and progress judging can now be formally split:
  - Lean replay first
  - judge only on replayable pairs
- Before that judge stage, we still need one normalization step for multi-tactic variants.
