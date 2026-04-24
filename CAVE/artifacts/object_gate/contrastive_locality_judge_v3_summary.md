# Contrastive Locality Judge Summary

Pairs judged: `10`
Verdicts: `{'accept': 1, 'reject': 9}`

## Per Pair

### code_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Checker undercoverage: a nearby non-gold repair (e.g., 'count += 0') would also pass the provided unit tests, failing to disambiguate."]`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'count += 1', 'passes': True, 'error': None, 'matches_keep_text': True}, {'alt_span': 'count -= 1', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}]}`
- Notes: The unit tests are insufficient to uniquely identify the correct increment value.

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
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['Checker undercoverage: does not disambiguate between the gold repair and a nearby alternative that also violates the constraint but in a different way.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [('A', 'C'), ('B', 'C'), ('C', 'D')], 'keep_order': ['A', 'B', 'C', 'A', 'B', 'D', 'C', 'A', 'B', 'C', 'D'], 'revise_order': ['A', 'B', 'C', 'A', 'B', 'D', 'C', 'A', 'C', 'D'], 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: The checker is too weak; it allows a plausible alternative repair that is also incorrect, breaking the locality geometry.

### plan_contrastive_locality_1202_harder

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['checker_undercoverage', 'gold_repair_not_local']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: Checker fails to specify that coffee must be brewed before toasting, allowing multiple valid orders. Gold repair is a complete replacement, not a local edit.

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
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['keep trace does not satisfy the written precedence constraints']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'order_sequence', 'edges': [('A', 'B'), ('B', 'C')], 'keep_order': ['A', 'B', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'A', 'C', 'B'], 'revise_order': ['A', 'B', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'A', 'C', 'B'], 'keep_valid': False, 'revise_valid': False, 'valid_order_count_limited': 1}`
- Notes: Auto-rejected from structured plan findings.

### code_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'alternative_results': [{'alt_span': 'odds[0] * odds[1]', 'passes': True, 'error': None, 'matches_keep_text': True}, {'alt_span': 'odds[0] - odds[1]', 'passes': False, 'error': 'AssertionError: ', 'matches_keep_text': False}]}`
- Notes: Clear contrastive locality with a single-character operator error.

### plan_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise trace already satisfies the written precedence constraints', 'written constraints allow multiple valid total orders']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'order_sequence', 'edges': [('A', 'B'), ('A', 'D'), ('B', 'C'), ('D', 'C')], 'keep_order': ['A', 'B', 'D', 'C'], 'revise_order': ['A', 'D', 'B', 'C'], 'keep_valid': True, 'revise_valid': True, 'valid_order_count_limited': 2}`
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
- Blocking issues: `["Checker undercoverage: constraint 'C before D' is not validated, allowing alternative invalid orders like A, B, D, C to pass unchecked."]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'order_sequence', 'edges': [('A', 'B'), ('A', 'D'), ('B', 'C'), ('C', 'D')], 'keep_order': ['A', 'B', 'C', 'D'], 'revise_order': ['A', 'C', 'B', 'D'], 'keep_valid': True, 'revise_valid': False, 'valid_order_count_limited': 1}`
- Notes: Checker's reference list includes 'C before D', but its validation logic is unspecified, creating ambiguity and potential for non-gold repairs to be considered correct.
