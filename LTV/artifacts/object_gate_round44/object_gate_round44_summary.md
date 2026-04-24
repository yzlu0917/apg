# Round44: first state-first API generation batch

## Goal

Use the README-documented API route to generate the first batch of candidate tactics from the new state-first seed panel.

## Boundary

This round now includes the first legality replay of generated candidates.

## Verified result

- Used the README-documented Volcengine/Ark API route to generate the first batch.
- Generated batch:
  - `5` states
  - `40` candidate tactics
- Lean legality replay on that batch:
  - `32` replay-ok
  - `8` replay-error

## State-level legality snapshot

- `lean_and_comm_pos__step1`: `8/8` legal
- `lean_add_zero_right_pos__step0`: `7/8` legal
- `lean_zero_add_left_pos__step0`: `6/8` legal
- `lean_eq_comm_pos__step1`: `5/8` legal
- `lean_or_left_pos__step1`: `6/8` legal

## Typical replay failures

- arithmetic tactic mismatch:
  - `nlinarith`
- rewrite / induction mismatch:
  - `induction n with | zero => rfl | succ n ih => simp [Nat.add_succ, ih]`
- goal-shape mismatch:
  - `symmetry`
  - `symmetry at h`
  - `constructor 1`
  - `refine ⟨h, ?_⟩`

## Meaning

- The README API config is usable.
- The new state-first data path is no longer just a scaffold:
  - API generation works
  - Lean legality filtering works
- Human progress annotation is still the next missing layer.
