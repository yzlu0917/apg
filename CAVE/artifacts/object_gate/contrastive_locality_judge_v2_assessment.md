# Contrastive Locality Judge V2 Assessment

Date: 2026-03-31

## Purpose

Assess whether the new blind model-judge is useful as a pre-screen for
`contrastive_locality`, not as a replacement for human review.

## Headline

`judge_v1` was unusable because it accepted all reviewed pairs.

`judge_v2` is materially better:

- it rejected `8 / 10` reviewed pairs
- it correctly flagged the later obviously bad pairs from `batch14` and
  `batch15`
- but it still disagrees with human review on several earlier borderline pairs

## Agreement snapshot

Using existing human review as the reference on the 10 valid reviewed pairs:

- clear agreement on later bad pairs:
  - `plan_contrastive_locality_0` from batch12
  - `code_1501_0`
  - `plan_1501_0`
  - `code_1601_0`
  - `plan_1601_harder_contrastive`
- disagreement remains on earlier borderline pairs:
  - `code_contrastive_locality_0`
  - `code_contrastive_locality_1202_harder_1`
  - `plan_contrastive_locality_0` from batch11
  - `code_contrastive_locality_1301_harder`

## What judge_v2 seems good at

- catching explicit checker inconsistency
- catching revise traces that do not actually violate written constraints
- catching plan cases with multiple checker-valid orders
- catching code cases where the checker obviously undercovers the claimed gold
  repair

## What judge_v2 is still bad at

- it can over-reject code pairs by imagining overly broad alternative repairs
- it can still over-accept some semantically equivalent code fixes
- it does not yet use execution or symbolic checking, only textual reasoning

## Operational conclusion

Keep `judge_v2` as a pre-screen only.

Recommended usage:

- `reject`: do not send to frozen panel
- `accept`: still require human review

Do not use `judge_v2` alone to grant Object-bootstrap acceptance.
