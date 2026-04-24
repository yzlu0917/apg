# Object Gate Minimum Loop

Date: 2026-03-31

## Goal

Start the Object gate without large experiments. The target is to show that the
project can already represent a non-trivial causal-verification object in a
reproducible way.

## Loop definition

1. Freeze a seed schema for paired interventions.
2. Create paired examples where a local change flips the gold action between
   `keep` and `revise`.
3. Validate the schema with a deterministic local script.
4. Review whether the object remains local, checkable, and distinct from plain
   correctness scoring.
5. Record the outcome and next expansion step.

## Assets

- Seed data:
  `data/object_gate_seed/cave_object_seed.jsonl`
- Schema and review notes:
  `data/object_gate_seed/README.md`
- Validator:
  `scripts/validate_object_gate_seed.py`

## Validation command

```bash
python scripts/validate_object_gate_seed.py data/object_gate_seed/cave_object_seed.jsonl
```

## Review checklist

- Does each pair share the same task and differ by a local intervention?
- Is the gold action automatically defensible from the checker?
- For `revise`, is there a plausible local repair suffix?
- For `keep`, would revising create unnecessary cost or risk?
- Does the example test verifier-mediated action, not just answer accuracy?

## Current bootstrap seed

The seed currently contains three pairs:

- `sym_pair_001`: arithmetic expression with a single local arithmetic error
- `code_pair_001`: Python function with a single-line bug
- `plan_pair_001`: dependency-constrained ordering with a local ordering error

This seed is not enough to pass the Object gate. It is enough to start it.

## Expected success criterion for this loop

The loop succeeds if:

- the validator passes,
- all examples satisfy pair consistency,
- the team can point to a concrete next step for scaling the dev panel.

If the loop fails, the likely failure modes are:

- schema instability,
- action ambiguity,
- locality that is too weak for suffix-style repair.
