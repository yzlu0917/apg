# Local Generation Attempts Summary

Date: 2026-03-31

Purpose:

- probe whether local Qwen3-8B generation is already good enough to produce a
  held-out harder subset for Audit replication without relying on API access.

Sources:

- `artifacts/object_gate/batch08_local_harder_candidates.jsonl`
- `artifacts/object_gate/batch09_local_harder_candidates.jsonl`

## Batch 08

Command profile:

- local `Qwen3-8B`
- `profile=harder`
- `temperature=0.2`

Outcome:

- deterministic validator: failed
- frozen pairs accepted: `0`

Main failure modes:

- `checker` sometimes collapsed to a bare string instead of an object
- `sym` revise examples changed task semantics instead of inserting a wrong
  local computation
- `code` revise examples sometimes kept the same semantics or changed the
  intended problem
- `plan` constraints were too weak to certify a real violation

## Batch 09

Command profile:

- local `Qwen3-8B`
- prompt tightened after Batch 08
- `profile=harder`
- `temperature=0.05`

Outcome:

- deterministic validator: passed
- reviewed pairs: `3`
- frozen pairs accepted: `0`

Rejected pairs:

- `sym_pair_0`
  - revise fail span points to a correct multiplication step
  - repair suffix is tautological and does not repair a real error
- `code_pair_0`
  - revise condition changes the task from summing evens to summing odds
  - checker and expected answer were changed to fit the new task, so the pair
    no longer shares one intended correct answer
- `plan_pair_0`
  - revise trace still satisfies the written ordering constraint
  - fail span does not isolate a true violation under the checker

## Decision

`No held-out final-like subset is frozen from the current local generator.`

Interpretation:

- local Qwen3-8B is usable for backend-side audit replication once slices are
  frozen
- it is not yet reliable enough as the source for new frozen object/audit
  pairs
- the next held-out subset should come from either restored API generation or
  a stronger local generation backend
