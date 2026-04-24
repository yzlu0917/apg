# Contrastive Locality Judge Summary

Pairs judged: `3`
Verdicts: `{'reject': 3}`

## Per Pair

### plan_contrastive_locality_1901_0

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise order already satisfies structured precedence constraints', 'structured local neighborhood has 2 valid repairs instead of exactly 1', 'keep order is not the unique valid local repair from revise order']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('B', 'C'), ('D', 'C')], 'keep_order': ['A', 'B', 'D', 'C'], 'revise_order': ['A', 'D', 'B', 'C'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['D', 'A', 'B', 'C'], ['A', 'B', 'D', 'C'], ['A', 'D', 'C', 'B']], 'valid_local_repairs': [['D', 'A', 'B', 'C'], ['A', 'B', 'D', 'C']], 'keep_valid': True, 'revise_valid': True, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 2, 'keep_is_unique_local_repair': False}`
- Notes: Auto-rejected from structured local-repair plan findings.

### plan_contrastive_locality_1902_1

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise order already satisfies structured precedence constraints']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('B', 'C'), ('D', 'C')], 'keep_order': ['A', 'D', 'B', 'C'], 'revise_order': ['A', 'B', 'D', 'C'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['B', 'A', 'D', 'C'], ['A', 'D', 'B', 'C'], ['A', 'B', 'C', 'D']], 'valid_local_repairs': [['A', 'D', 'B', 'C']], 'keep_valid': True, 'revise_valid': True, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Auto-rejected from structured local-repair plan findings.

### plan_contrastive_locality_2_1903

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise order already satisfies structured precedence constraints']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('B', 'C'), ('D', 'C')], 'keep_order': ['A', 'D', 'B', 'C'], 'revise_order': ['A', 'B', 'D', 'C'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['B', 'A', 'D', 'C'], ['A', 'D', 'B', 'C'], ['A', 'B', 'C', 'D']], 'valid_local_repairs': [['A', 'D', 'B', 'C']], 'keep_valid': True, 'revise_valid': True, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Auto-rejected from structured local-repair plan findings.
