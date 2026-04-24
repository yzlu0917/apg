# Contrastive Locality Bootstrap Summary

Date: 2026-04-01

## Goal

Test whether a genuinely different family can produce reviewed pairs where:

- several nearby local repairs look plausible
- only one repair is checker-correct
- verifier content should matter more than generic retry

## Reviewed batches

- `batch11_contrastive_locality`
  - reviewed pairs: `4`
  - accepted pairs: `2`
  - status: mixed but promising
- `batch12_contrastive_locality`
  - reviewed pairs: `2`
  - accepted pairs: `0`
  - status: rejected for equivalent code alternatives and trivial plan geometry
- `batch13_contrastive_locality_code`
  - reviewed pairs: `0`
  - accepted pairs: `0`
  - status: invalid before review because revise repair suffix was empty
- `batch14_contrastive_locality`
  - reviewed pairs: `2`
  - accepted pairs: `0`
  - status: rejected for code checker undercoverage and false plan violation
- `batch15_contrastive_locality`
  - reviewed pairs: `2`
  - accepted pairs: `0`
  - status: rejected for checker inconsistency in code and trivial linear-chain
    plan geometry
- `batch16_contrastive_locality`
  - reviewed pairs: `4`
  - accepted pairs: `1`
  - status: one new acceptable code pair, but plan generation still rejected for
    false violations and collapsed geometry
- `batch17_contrastive_locality_plan`
  - reviewed pairs: `3`
  - accepted pairs: `0`
  - status: plan-specific prompt override removed some false-violation drift,
    but checker ambiguity and undercoverage still blocked every pair
- `batch18_contrastive_locality_structured_plan`
  - reviewed pairs: `3`
  - accepted pairs: `0`
  - status: structured checker removed prose ambiguity, but the model still
    produced revise orders that were actually valid under the edges
- `batch19_contrastive_locality_structured_plan`
  - reviewed pairs: `0`
  - accepted pairs: `0`
  - status: after adding generator-side semantic validation, the API model
    could not produce even the first valid structured pair within 6 attempts
- `batch20_structured_plan_search`
  - reviewed pairs: `3`
  - accepted pairs: `3`
  - status: search-constructed structured-plan path produced the first stable
    clean plan sub-object in this family
- `batch21_structured_plan_search`
  - reviewed pairs: `5`
  - accepted pairs: `5`
  - status: diversified search-constructed structured-plan path remained stable
    under validator, judge, and review
- `batch22_structured_code_search`
  - reviewed pairs: `3`
  - accepted pairs: `3`
  - status: first structured-code search slice reviewed cleanly and established
    a matching exact code-side sub-object
- `batch23_structured_code_search`
  - reviewed pairs: `5`
  - accepted pairs: `5`
  - status: diversified structured-code search path remained stable under
    validator, deterministic judge, and review

## Aggregate status

- valid reviewed pairs so far: `36`
- accepted pairs so far: `19`
- aggregate acceptance rate over reviewed valid pairs: `52.8 percent`

Accepted pairs so far:

- `code_contrastive_locality_0`
- `plan_contrastive_locality_0`
- `code_1701_harder_0`
- `plan_structured_search_2101`
- `plan_structured_search_2102`
- `plan_structured_search_2103`
- `plan_structured_search_2201`
- `plan_structured_search_2202`
- `plan_structured_search_2203`
- `plan_structured_search_2204`
- `plan_structured_search_2205`
- `code_structured_search_3101`
- `code_structured_search_3102`
- `code_structured_search_3103`
- `code_structured_search_3201`
- `code_structured_search_3202`
- `code_structured_search_3203`
- `code_structured_search_3204`
- `code_structured_search_3205`

## Current diagnosis

- the family idea is not empty; batch11 produced two accepted examples
- batch16 shows the new workflow can still surface an additional acceptable code
  pair
- batch17 shows that a plan-specific prompt override improves formatting but
  does not solve plan-side checker geometry
- batch18 shows that a structured plan checker removes ambiguity but also makes
  the remaining generator failure mode crisp: revise traces are often still
  valid
- batch19 shows that once this structured geometry is enforced at generation
  time, the current API generator cannot reliably produce valid pairs
- batch20 shows that the same structured plan object becomes viable under a
  search-constructed generation path
- batch21 shows that this search path is not a one-off and can sustain a small
  reviewed panel with better diversity
- batch22 shows the code side can be given a matching exact structured object
  rather than relying on free-form generation and heuristic repair mining
- batch23 shows this structured-code path is also not a one-off and can sustain
  a small reviewed panel
- but generation quality is not yet stable enough to claim a new Object
  bootstrap
- the main blockers have shifted from schema defects to semantic drift:
  - equivalent or underdetermined code repairs
  - plan revise traces that do not actually violate the intended checker
  - plan generators that cannot satisfy gold-only local repair geometry even
    under structured checking
  - whole-family acceptance remains held back by the older weak batches, even
    though both structured sub-objects are now viable

## Current gate status

`contrastive_locality` is `Object bootstrap in progress`, not `Object GO`.

This branch should currently be framed as:

- a new family attempt with partial viability
- a branch with one viable frozen structured-plan subpanel
- a branch with one viable frozen structured-code subpanel
- not yet evidence that the old Audit failure can be rescued by a different
  family

## Next action

Current evidence suggests the judge pipeline is now good enough for default
pre-screening, but generation quality still is not.

The next step should be to decide whether to:

- continue this family by deciding whether to combine the two structured
  sub-objects into a cleaner branch with fresh Object criteria
- or pause the family as a weak branch despite improved code-side screening
