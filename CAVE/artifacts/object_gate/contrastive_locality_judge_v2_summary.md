# Contrastive Locality Judge Summary

Pairs judged: `10`
Verdicts: `{'accept': 2, 'reject': 8}`

## Per Pair

### code_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: multiple nearby repairs (e.g., conditional increment) pass the given unit tests, so the checker does not disambiguate the gold repair from plausible alternatives.']`
- Notes: The checker's test cases are insufficient to guarantee only the gold repair is correct.

### code_contrastive_locality_1202_harder_1

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Pair correctly instantiates contrastive_locality geometry.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: the gold repair is not uniquely determined by the checker. A repair that only enforces B before C (but not necessarily A before C) is also valid and yields the same answer, violating the locality requirement that only the gold repair should be checker-correct.']`
- Notes: The checker's constraint is satisfied by multiple ordering repairs, collapsing the geometry.

### plan_contrastive_locality_1202_harder

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker undercoverage: the constraints allow multiple valid orders, so the gold repair is not uniquely correct. A nearby alternative repair ('toast bread, brew coffee, butter toast') is also checker-correct."]`
- Notes: The family requires that only the gold repair should be checker-correct, but here the checker's constraints are insufficient to disambiguate.

### code_contrastive_locality_1301_harder

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Clear contrastive locality: a single-character change (0→1) fixes the bug, and the checker validates the intended behavior.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'fail'}`
- Blocking issues: `['Checker inconsistency between keep and revise', 'Revise trace does not actually violate the stated constraints from the question', 'Checker in revise adds new minimization requirement not present in keep']`
- Notes: The pair fails because the checker changes between examples, making the error artificial. The revise schedule is suboptimal but still valid under the original problem statement.

### code_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: nearby non-gold repairs (e.g., subtraction) could accidentally pass the given unit tests, violating the requirement that only the gold repair should be checker-correct.']`
- Notes: The unit tests do not guarantee that only multiplication yields the correct answer for all inputs; they only check specific cases. A subtraction repair could pass if the two largest odds differ by the expected product, which is not tested.

### plan_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Revise trace satisfies all stated constraints; no error exists. Checker is inconsistent with the claimed violation.']`
- Notes: The pair is invalid because the 'revise' example's initial trace is actually a valid total order. The constraint 'D must be after A but before C' is satisfied (A before D before C). B before C is satisfied (B before C). A before B is satisfied (A before B). Therefore A->D->B->C is valid, making the revision nonsensical.

### code_1601_0

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker undercoverage: nearby non-gold repair (e.g., 'not i % 15 == 0') is behaviorally equivalent to gold repair, so checker does not disambiguate uniquely."]`
- Notes: The pair is well-formed but fails the requirement that only the gold repair should be checker-correct; behaviorally equivalent alternatives exist.

### plan_1601_harder_contrastive

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Multiple valid total orders exist (e.g., A,B,D,C), so checker does not disambiguate gold repair from nearby plausible alternatives.']`
- Notes: Family requires only gold repair is checker-correct; here, other orders also satisfy constraints.
