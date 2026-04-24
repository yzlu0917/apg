# Object Gate Seed

This directory contains the first hand-built paired interventions for the CAVE
Object gate.

## File

- `cave_object_seed.jsonl`

## Schema

Each JSONL record contains:

- `id`: unique example id
- `pair_id`: pair identifier shared by the keep and revise variants
- `domain`: one of `sym`, `code`, `plan`
- `question`: task statement
- `initial_trace`: initial answer, reasoning trace, or candidate solution
- `gold_fail_span`: object with `text` and `kind`
- `gold_action`: one of `keep`, `revise`, `abstain`
- `gold_repair_suffix`: minimal repair or empty string
- `expected_final_answer`: canonical target after a correct action
- `checker`: object describing the automatic checker
- `utility_delta`: relative utility for `keep`, `revise`, and `abstain`
- `notes`: short explanation

## Review rule

For stage 0, each `pair_id` should contain:

- one `keep` example,
- one `revise` example,
- the same task with only a local intervention changed.

`abstain` is allowed by schema but is not required in the first bootstrap seed.
