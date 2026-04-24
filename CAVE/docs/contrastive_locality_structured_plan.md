# Contrastive Locality Structured Plan Object

Date: 2026-03-31

## Purpose

Replace brittle prose planning constraints with a structured local-repair object
 that can be checked programmatically.

This is a versioned object-design move inside the `contrastive_locality`
 family. It is not yet a gate pass.

## Object definition

Each plan pair uses:

- a compact order string such as `A -> D -> B -> C`
- a structured checker JSON string in `checker.reference`
- a local repair budget of exactly one adjacent swap

The checker schema is:

```json
{
  "schema": "plan_local_repair_v1",
  "tasks": ["A", "B", "C", "D"],
  "edges": [["A", "B"], ["B", "C"], ["D", "C"]],
  "locality": {"kind": "adjacent_swap", "max_swaps": 1}
}
```

## Acceptance geometry

For a candidate pair to count as a valid structured-plan object:

- `keep` order satisfies all precedence edges
- `revise` order violates the precedence edges
- the adjacent-swap neighborhood of `revise` has at least two candidates
- exactly one adjacent-swap neighbor is valid
- that unique valid neighbor is exactly the `keep` order

This makes the local repair object programmatically auditable and removes the
old ambiguity about whether a prose checker really singled out the gold repair.

## Why this is better than prose plan

- no ambiguity about what the checker means
- no hidden reliance on informal notions like "reasonable" or "immediately"
- no need for the judge to infer schedule semantics from free-form text
- local repair geometry is testable by enumeration rather than by language
  interpretation

## Current status

As of 2026-03-31:

- the object design itself is cleaner than the earlier prose-plan path
- `judge_v4` can analyze it deterministically as `structured_local_repair`
- direct API generation still fails often because the model keeps producing
  revise orders that are actually valid under the edges
- generator-side family-semantic validation now rejects those cases at
  generation time
- a search-constructed path can already produce clean accepted pairs for this
  object
- an initial frozen reviewed subpanel now exists for this sub-object

So the current branch state is:

- `object design improved`
- `search path viable`
- `subpanel frozen`
- `direct generator still unstable`
- `not Object-bootstrap ready`
