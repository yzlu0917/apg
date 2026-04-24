# Round45: first human progress oracle batch

## Goal

Manually annotate the first replay-ok state-first batch with a small human progress oracle.

## Scope

- Only replay-ok candidates are annotated.
- Lean legality remains upstream and fixed.
- This is a first single-annotator oracle, not yet an agreement study.

## Files

- `configs/object_gate/human_progress_oracle_v0.yaml`
- `data/annotations/state_first_progress_oracle_batch_v0.jsonl`

## Batch Statistics

- `num_states = 5`
- `num_candidates = 32`
- state-level counts:
  - `lean_and_comm_pos__step1 = 8`
  - `lean_add_zero_right_pos__step0 = 7`
  - `lean_zero_add_left_pos__step0 = 6`
  - `lean_eq_comm_pos__step1 = 5`
  - `lean_or_left_pos__step1 = 6`
- tier counts:
  - `solved = 17`
  - `strong_partial = 10`
  - `weak_partial = 4`
  - `neutral = 1`

## Representative Judgments

- `lean_and_comm_pos__step1`
  - `exact ⟨h.right, h.left⟩` -> `solved`
  - `constructor` / `apply And.intro` / `refine ⟨?_, ?_⟩` -> `strong_partial`
  - `rcases h with ⟨hp, hq⟩` -> `weak_partial`
- `lean_eq_comm_pos__step1`
  - `exact Eq.symm h` / `rw [h]` -> `solved`
  - `apply Eq.symm` / `rewrite [h]` -> `strong_partial`
  - `calc b = a := ?_` -> `neutral`
- `lean_or_left_pos__step1`
  - `exact Or.inl h` -> `solved`
  - `apply Or.inl` / `refine Or.inl ?_` / `left` -> `strong_partial`

## Interpretation

- This batch is the first project-owned human progress oracle on the new state-first pipeline.
- It is suitable for a first pairwise separability audit on frozen hidden states.
- It is not yet a final progress benchmark because:
  - only `5` states are covered
  - annotation is single-rater
  - the current scheme uses derived pairwise preferences rather than direct agreement-checked comparisons

## Next

- derive state-local pairwise preferences from the tiered oracle
- run the first frozen-hidden separability audit on the derived pairwise labels
