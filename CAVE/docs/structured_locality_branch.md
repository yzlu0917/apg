# Structured Locality Branch

Date: 2026-04-01

## Why this branch exists

`contrastive_locality` as a whole is still dragged down by early weak
free-generation batches. That makes it a poor container for judging whether the
exact structured sub-objects are themselves viable.

`structured_locality` is a clean spin-out branch that keeps only the exact,
search-constructed sub-objects:

- structured plan with exact adjacent-swap locality
- structured code with explicit nearby repair candidates

This is a branch split, not a retroactive rewrite of the old family.

## Scope

Included:

- `plan_local_repair_v1`
- `code_local_repair_v1`
- search-constructed candidates only
- reviewed frozen subpanels only

Excluded:

- early free-generation `contrastive_locality` batches
- prose-only plan checkers
- heuristic-only nearby-repair mining for code

## Claim hierarchy

Object claim:

- exact structured local-repair objects exist in both `plan` and `code`
- these objects can be search-constructed, deterministically checked, and
  frozen into a reviewed panel

Method claim:

- not yet supported
- no Audit / Conversion result is implied by the object result alone

Deployment claim:

- not supported

## Relationship to the old family

- `contrastive_locality`: still `Object bootstrap in progress`
- `structured_locality`: new clean branch focused only on the exact structured
  sub-objects

These are not the same evaluation ledger and should not be merged in reporting.
