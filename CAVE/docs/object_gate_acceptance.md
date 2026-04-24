# Object Gate Acceptance Rule

Date: 2026-03-31

## Current rule

The first reviewed dev panel is accepted only if all of the following hold:

- pair consistency is 100 percent after deterministic validation,
- at least 80 percent of reviewed pairs satisfy:
  - `label_clear`
  - `localizable`
  - `repair_plausible`
- at least two domains remain viable after review,
- no dominant artifact explains the gold action,
- the accepted panel still represents verifier-mediated action decisions rather
  than raw correctness-only labeling.

## Review outcomes

Possible review decisions:

- `accept`: suitable for the reviewed dev panel
- `reject`: not reliable enough for the frozen panel
- `revise_prompt`: failure is mostly due to generation prompt weakness and
  should be retried with stronger instructions

## Batch 01 status

Source:

- `artifacts/object_gate/batch01_candidates.jsonl`

Outcome:

- reviewed pairs: 6
- accepted pairs: 4
- rejected pairs: 2
- acceptance rate: 66.7 percent
- viable domains after review: 3

Decision:

`Object gate not yet passed.`

Reason:

The batch preserves domain viability and passes deterministic checks, but it
misses the 80 percent review threshold because two pairs have weak localization
or weak repair representations.

## Immediate action

Use the rejected-pair failure modes to tighten the generation prompt, then
generate the next small batch. Do not move to baseline comparisons yet.

## Frozen review set status

After prompt tightening, the first frozen review set is:

- `artifacts/object_gate/batch02_candidates.jsonl`
- `artifacts/object_gate/batch04_plan_candidates.jsonl`
- `artifacts/object_gate/batch05_sym_candidates.jsonl`

Accepted into the frozen panel:

- `sym_0`
- `code_pair_0`
- `plan_pair_0_301`
- `sym_pair_0`

Rejected from the frozen review set:

- `plan_pair_0`

Frozen-set outcome:

- reviewed pairs: 5
- accepted pairs: 4
- acceptance rate: 80.0 percent
- viable domains after review: 3

Decision:

`Bootstrap Object gate: GO`

Interpretation:

The project now has a minimally frozen reviewed panel that satisfies the phase-0
Object gate acceptance rule. This is a bootstrap-level pass, not evidence for
method superiority. The next gate is Audit, not Conversion.
