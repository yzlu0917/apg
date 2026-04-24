# Contrastive Locality Judge Summary

Pairs judged: `10`
Verdicts: `{'accept': 2, 'reject': 8}`

## Per Pair

### code_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker undercoverage: alternative repairs like 'count += 0' would also pass the given unit tests, violating the requirement that only the gold repair should be checker-correct."]`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'count += 1', 'passes': True, 'error': None, 'matches_keep_text': True}, {'alt_span': 'count -= 1', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}]}`
- Notes: The pair fails because the checker does not guarantee uniqueness of the correct repair. The unit tests are insufficient to distinguish the correct increment from other values.

### code_contrastive_locality_1202_harder_1

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'borderline', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['keep trace fails the written unit tests', 'revise trace already passes the written unit tests']`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': False, 'keep_error': 'AssertionError: ', 'revise_passes': True, 'revise_error': None, 'alternative_results': [{'alt_span': 'if (i % a != 0) or (i % b != 0):', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}, {'alt_span': 'if (i % a == 0) and (i % b == 0):', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}]}`
- Notes: Auto-rejected from execution-backed code findings.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'schedule', 'edges': [('A', 'C'), ('B', 'C'), ('C', 'D')], 'keep_order': ['A', 'B', 'C', 'A', 'B', 'D', 'C', 'A', 'B', 'C', 'D'], 'revise_order': ['A', 'B', 'C', 'A', 'B', 'D', 'C', 'A', 'C', 'D'], 'durations': {'A': 10, 'B': 15, 'C': 30, 'D': 20}, 'keep_starts': {'A': 0, 'B': 0, 'C': 15, 'D': 45}, 'revise_starts': {'A': 0, 'B': 0, 'C': 10, 'D': 40}, 'minimal_makespan': 65, 'keep_valid': True, 'revise_valid': False, 'keep_issues': [], 'revise_issues': ['C starts before B finishes', 'makespan 60 is not minimal 65'], 'keep_makespan': 65, 'revise_makespan': 60, 'valid_order_count_limited': None}`
- Notes: Pair cleanly instantiates contrastive_locality: local ordering error, checker disambiguates, gold repair is the unique fix.

### plan_contrastive_locality_1202_harder

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: multiple orders satisfy constraints, not just the gold repair.', 'Gold repair is identical to keep trace, not a distinct local fix.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: Plan geometry collapses; multiple valid orders exist, violating locality requirement.

### code_contrastive_locality_1301_harder

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'borderline', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['heuristic alternative repairs also pass unit tests: if digit % 2 != 0:']`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'if digit % 2 != 0:', 'passes': True, 'error': None, 'matches_keep_text': False}, {'alt_span': 'if digit % 2 == 1:', 'passes': True, 'error': None, 'matches_keep_text': True}]}`
- Notes: Auto-rejected from execution-backed code findings.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker adds a new constraint ('immediately after') not present in the original problem statement, creating a spec/checker disagreement.", 'The geometry collapses: the only plausible local repair is the gold repair itself, violating the requirement for at least one nearby plausible alternative.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'schedule', 'edges': [('A', 'B'), ('B', 'C')], 'keep_order': ['A', 'B', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'A', 'C', 'B'], 'revise_order': ['A', 'B', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'A', 'C', 'B'], 'durations': {'A': 5, 'B': 10, 'C': 15}, 'keep_starts': {'A': 0, 'B': 5, 'C': 15}, 'revise_starts': {'A': 0, 'B': 10, 'C': 20}, 'minimal_makespan': 30, 'keep_valid': True, 'revise_valid': False, 'keep_issues': [], 'revise_issues': ['makespan 35 is not minimal 30'], 'keep_makespan': 30, 'revise_makespan': 35, 'valid_order_count_limited': None}`
- Notes: The revise trace violates the checker's added 'immediately' rule, but the original question only required sequential order and minimization. The gold repair is the only correct schedule, so there is no contrastive locality.

### code_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'odds[0] * odds[1]', 'passes': True, 'error': None, 'matches_keep_text': True}, {'alt_span': 'odds[0] - odds[1]', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}]}`
- Notes: Pair cleanly instantiates contrastive_locality geometry.

### plan_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise trace already satisfies the written precedence constraints', 'written constraints allow multiple valid total orders']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'order_sequence', 'edges': [('A', 'B'), ('A', 'D'), ('B', 'C'), ('D', 'C')], 'keep_order': ['A', 'B', 'D', 'C'], 'revise_order': ['A', 'D', 'B', 'C'], 'durations': {}, 'keep_valid': True, 'revise_valid': True, 'valid_order_count_limited': 2}`
- Notes: Auto-rejected from structured plan findings.

### code_1601_0

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'borderline', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['keep trace fails the written unit tests']`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': False, 'keep_error': 'AssertionError: ', 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'i % 15 != 0', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': True}]}`
- Notes: Auto-rejected from execution-backed code findings.

### plan_1601_harder_contrastive

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Only one valid total order exists, violating the requirement for at least one nearby plausible local repair besides the gold repair.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'order_sequence', 'edges': [('A', 'B'), ('A', 'D'), ('B', 'C'), ('C', 'D')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['A', 'C', 'B', 'D'], 'durations': {}, 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 1}`
- Notes: Program findings show valid_order_count_limited = 1. The geometry collapses to a single linear order, making the gold repair the only possible fix.
