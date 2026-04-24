# Structured Locality Object Gate

Date: 2026-04-01

## Purpose

Freeze a fresh Object-gate rule for the `structured_locality` spin-out branch,
using only exact structured sub-objects.

## Acceptance rule

`structured_locality` gets an Object `GO` only if all are true:

- the frozen panel passes deterministic validation with `100 percent`
  pair consistency
- both `plan` and `code` are represented
- every included pair comes from a reviewed accepted structured subpanel
- the combined frozen panel has at least `12` pairs total
- each domain contributes at least `6` accepted pairs
- the object geometry is exact and programmatically checkable:
  - `plan`: unique valid adjacent-swap repair under `plan_local_repair_v1`
  - `code`: unique passing local repair under `code_local_repair_v1`

## Frozen panel

The first frozen panel for this branch is:

- `artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl`

It is assembled from:

- `artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl`
- `artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl`

## Gate decision

Current status:

`Object gate: GO`

Reason:

- both domains now have exact structured sub-objects
- both domains have frozen reviewed subpanels
- the combined panel is large enough for a fresh object branch
- the old weak free-generation batches are explicitly excluded instead of being
  silently reinterpreted

## Limits

This gate pass supports only the object claim for `structured_locality`.

It does not establish:

- Audit success
- method superiority
- deployment readiness
