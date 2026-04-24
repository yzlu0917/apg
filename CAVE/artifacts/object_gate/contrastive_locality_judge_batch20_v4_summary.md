# Contrastive Locality Judge Summary

Pairs judged: `3`
Verdicts: `{'accept': 3}`

## Per Pair

### plan_structured_search_2101

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('A', 'C')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['B', 'A', 'C', 'D'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['A', 'B', 'C', 'D'], ['B', 'C', 'A', 'D'], ['B', 'A', 'D', 'C']], 'valid_local_repairs': [['A', 'B', 'C', 'D']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Geometry fits: one plausible local swap, only gold repair satisfies dependencies.

### plan_structured_search_2102

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('A', 'D')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['B', 'A', 'C', 'D'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['A', 'B', 'C', 'D'], ['B', 'C', 'A', 'D'], ['B', 'A', 'D', 'C']], 'valid_local_repairs': [['A', 'B', 'C', 'D']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Clean contrastive_locality example: one adjacent swap yields three neighbors, only the gold repair satisfies all dependencies.

### plan_structured_search_2103

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('B', 'C')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['A', 'C', 'B', 'D'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['C', 'A', 'B', 'D'], ['A', 'B', 'C', 'D'], ['A', 'C', 'D', 'B']], 'valid_local_repairs': [['A', 'B', 'C', 'D']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Clean adjacency swap with clear single valid repair.
