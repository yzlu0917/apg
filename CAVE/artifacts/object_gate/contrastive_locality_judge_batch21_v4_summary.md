# Contrastive Locality Judge Summary

Pairs judged: `5`
Verdicts: `{'accept': 5}`

## Per Pair

### plan_structured_search_2201

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('A', 'C')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['B', 'A', 'C', 'D'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['A', 'B', 'C', 'D'], ['B', 'C', 'A', 'D'], ['B', 'A', 'D', 'C']], 'valid_local_repairs': [['A', 'B', 'C', 'D']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Geometry is correct: one local error, multiple plausible swaps, only gold repair satisfies dependencies.

### plan_structured_search_2202

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'B'), ('B', 'D')], 'keep_order': ['A', 'B', 'D', 'C'], 'revise_order': ['A', 'D', 'B', 'C'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['D', 'A', 'B', 'C'], ['A', 'B', 'D', 'C'], ['A', 'D', 'C', 'B']], 'valid_local_repairs': [['A', 'B', 'D', 'C']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Geometry is correct: one gold repair among multiple plausible local swaps, with checker ensuring only the correct dependency order passes.

### plan_structured_search_2203

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'C'), ('A', 'B')], 'keep_order': ['A', 'C', 'B', 'D'], 'revise_order': ['C', 'A', 'B', 'D'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['A', 'C', 'B', 'D'], ['C', 'B', 'A', 'D'], ['C', 'A', 'D', 'B']], 'valid_local_repairs': [['A', 'C', 'B', 'D']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Clean contrastive locality: one local swap fixes the error, and only that swap yields a valid order.

### plan_structured_search_2204

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'C'), ('C', 'D')], 'keep_order': ['A', 'C', 'D', 'B'], 'revise_order': ['A', 'D', 'C', 'B'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['D', 'A', 'C', 'B'], ['A', 'C', 'D', 'B'], ['A', 'D', 'B', 'C']], 'valid_local_repairs': [['A', 'C', 'D', 'B']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Clean contrastive locality: one plausible local swap (D->A) fails, gold repair is unique and correct.

### plan_structured_search_2205

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'structured_local_repair', 'tasks': ['A', 'B', 'C', 'D'], 'edges': [('A', 'D'), ('A', 'B')], 'keep_order': ['A', 'D', 'B', 'C'], 'revise_order': ['D', 'A', 'B', 'C'], 'locality': {'kind': 'adjacent_swap', 'max_swaps': 1}, 'candidate_neighbors': [['A', 'D', 'B', 'C'], ['D', 'B', 'A', 'C'], ['D', 'A', 'C', 'B']], 'valid_local_repairs': [['A', 'D', 'B', 'C']], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 3, 'neighbor_count': 3, 'valid_local_repair_count': 1, 'keep_is_unique_local_repair': True}`
- Notes: Clean contrastive locality: one local error, one correct repair among plausible adjacent swaps.
