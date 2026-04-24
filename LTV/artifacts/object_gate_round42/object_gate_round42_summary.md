# Round42: replay-data audit

## Goal

Audit the full round41 replay bucket and determine whether the current CTS rows are clean enough for pairwise progress judging.

## Main findings

1. The current CTS scaffold is **not** clean enough to send directly to a progress judge.
2. The main issue is not only hard-invalid variants; it is also that some current `semantic_flip` rows remain fully replayable in Lean.
3. Therefore the current proxy label `source_better_strong` is not reliable after replay.

## Verified breakdown

- total pairs: `58`
- same pairs:
  - `29` replayable
  - `1` wrapper-level holdout
- flip pairs:
  - `25` Lean hard errors
  - `3` replayable

## Critical interpretation

The `3` replayable flip rows are currently:

- `cts_flip_add_zero_1`
- `cts_flip_zero_add_left_api_1`
- `lean_mul_zero_right_pos__step0__targeted_family__flip__2798d541`

All three are labeled as `wrong_theorem_reference`, but under actual Lean replay they still close the goal. So under the replay protocol they are **not usable as clean flip-progress pairs**.

## Additional issue

The only same-side replay error is:

- `lean_false_elim_pos__step1__plausible_flip__same__811e22f0`

Its variant is `exfalso; exact h`, which fails only because the current wrapper treats semicolon-composed tactics as a single tactic command. This is a wrapper normalization issue, not a semantic failure.

## Meaning

Before pairwise progress judging, the data should be repartitioned into:

- hard-invalid bucket
- replayable-but-needs-relabel bucket
- wrapper-normalization holdout bucket

The current `same/flip` proxy split is no longer trustworthy once Lean replay is introduced.
