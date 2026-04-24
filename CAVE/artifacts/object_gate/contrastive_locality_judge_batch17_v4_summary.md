# Contrastive Locality Judge Summary

Pairs judged: `3`
Verdicts: `{'reject': 3}`

## Per Pair

### plan_contrastive_locality_1801_0

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker constraint (1) is ambiguous regarding whether 'frosting step' refers to making frosting or applying it. This leaves open a nearby plausible alternative repair (e.g., keep 'make frosting' before 'cool' but ensure assembly occurs after cooling) that might also satisfy the constraint as written, violating the requirement that only the gold repair should be checker-correct."]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: The pair is well-structured, but checker ambiguity undermines the contrastive locality geometry.

### plan_contrastive_locality_1802_1

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: multiple valid orders exist, not just the gold repair.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: The checker fails to enforce that 'Prepare frosting' must be done before 'Bake cake layers', leaving a nearby plausible alternative repair that is also checker-correct.

### plan_contrastive_locality_1803_2

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: multiple nearby repairs satisfy constraints, not just the gold one.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: Family requires only gold repair to be checker-correct, but alternative valid order exists.
