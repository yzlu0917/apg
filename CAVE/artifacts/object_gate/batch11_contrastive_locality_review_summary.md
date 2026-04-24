# Batch 11 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`

## Accepted

- `code_contrastive_locality_0`
  - local count-update bug with several plausible nearby wrong repairs
  - unit tests are strong enough to single out the correct fix
- `plan_contrastive_locality_0`
  - dependency-and-parallelism schedule where the wrong local assumption is
    plausible
  - repair suffix explicitly restores the missing blocking condition

## Rejected

- `code_contrastive_locality_1202_harder_1`
  - rejected because the natural-language spec says “divisible by a or b, but
    not by both”, while the unit test target `233168` corresponds to the
    inclusive-or version
  - this breaks the one-intended-answer requirement
- `plan_contrastive_locality_1202_harder`
  - rejected because the task is too trivial and does not really instantiate
    the intended contrastive-locality geometry
  - generic retry is unlikely to need verifier content to choose the right fix

## Outcome

- reviewed pairs: `4`
- accepted pairs: `2`
- rejected pairs: `2`
- acceptance rate: `50.0 percent`

Decision:

`Do not use this batch as the family bootstrap panel.`

Interpretation:

- the family idea looks viable
- but the first prompt still underspecifies checker disambiguation and plan
  difficulty
- next step is a tightened follow-up batch, not a gate decision
