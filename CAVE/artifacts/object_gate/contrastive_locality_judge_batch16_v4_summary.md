# Contrastive Locality Judge Summary

Pairs judged: `4`
Verdicts: `{'accept': 1, 'reject': 3}`

## Per Pair

### code_1701_harder_0

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': False, 'revise_error': 'AssertionError: ', 'probe_inputs': [[[5, 5, 4, 3]], [[3, 4, 5, 5]], [[5, 5, 4, 3, 4]], [[5, 5, 4]], [[-5, -5, -4, -3]], [[10]], [[10, 11]], [[-10]], [[10, 10, 10]], [[10, 10, 10, 11]], [[10, 10]], [[-10, -10, -10]]], 'keep_probe_outputs': {'[[5, 5, 4, 3]]': {'ok': True, 'value': 4}, '[[3, 4, 5, 5]]': {'ok': True, 'value': 4}, '[[5, 5, 4, 3, 4]]': {'ok': True, 'value': 4}, '[[5, 5, 4]]': {'ok': True, 'value': 4}, '[[-5, -5, -4, -3]]': {'ok': True, 'value': -4}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 10}, '[[-10]]': {'ok': True, 'value': None}, '[[10, 10, 10]]': {'ok': True, 'value': None}, '[[10, 10, 10, 11]]': {'ok': True, 'value': 10}, '[[10, 10]]': {'ok': True, 'value': None}, '[[-10, -10, -10]]': {'ok': True, 'value': None}}, 'keep_probe_error': None, 'revise_probe_outputs': {'[[5, 5, 4, 3]]': {'ok': True, 'value': 5}, '[[3, 4, 5, 5]]': {'ok': True, 'value': 5}, '[[5, 5, 4, 3, 4]]': {'ok': True, 'value': 5}, '[[5, 5, 4]]': {'ok': True, 'value': 5}, '[[-5, -5, -4, -3]]': {'ok': True, 'value': -3}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 11}, '[[-10]]': {'ok': True, 'value': None}, '[[10, 10, 10]]': {'ok': True, 'value': None}, '[[10, 10, 10, 11]]': {'ok': True, 'value': 11}, '[[10, 10]]': {'ok': True, 'value': None}, '[[-10, -10, -10]]': {'ok': True, 'value': None}}, 'revise_probe_error': None, 'reference_code': 'def find_second_largest(nums):\n    distinct = set(nums)\n    if len(distinct) < 2:\n        return None\n    sorted_distinct = sorted(distinct, reverse=True)\n    return sorted_distinct[1]', 'reference_usage': {'completion_tokens': 62, 'prompt_tokens': 161, 'total_tokens': 223, 'completion_tokens_details': {'accepted_prediction_tokens': None, 'audio_tokens': None, 'reasoning_tokens': 0, 'rejected_prediction_tokens': None}, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'reference_probe_outputs': {'[[5, 5, 4, 3]]': {'ok': True, 'value': 4}, '[[3, 4, 5, 5]]': {'ok': True, 'value': 4}, '[[5, 5, 4, 3, 4]]': {'ok': True, 'value': 4}, '[[5, 5, 4]]': {'ok': True, 'value': 4}, '[[-5, -5, -4, -3]]': {'ok': True, 'value': -4}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 10}, '[[-10]]': {'ok': True, 'value': None}, '[[10, 10, 10]]': {'ok': True, 'value': None}, '[[10, 10, 10, 11]]': {'ok': True, 'value': 10}, '[[10, 10]]': {'ok': True, 'value': None}, '[[-10, -10, -10]]': {'ok': True, 'value': None}}, 'reference_probe_error': None, 'keep_vs_reference_mismatches': [], 'revise_vs_reference_mismatches': ['[[5, 5, 4, 3]]', '[[3, 4, 5, 5]]', '[[5, 5, 4, 3, 4]]', '[[5, 5, 4]]', '[[-5, -5, -4, -3]]', '[[10, 11]]', '[[10, 10, 10, 11]]'], 'alternative_results': []}`
- Notes: Pair cleanly instantiates contrastive_locality: local error, checker distinguishes, gold repair is minimal and unique.

### code_1702_1

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `auto_reject`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'borderline', 'retry_vulnerable': 'pass'}`
- Blocking issues: `['revise trace already passes the written unit tests']`
- Program findings: `{'supported': True, 'checker_type': 'unit_test', 'keep_passes': True, 'keep_error': None, 'revise_passes': True, 'revise_error': None, 'probe_inputs': [[[3, 1, 4, 1, 5, 9]], [[9, 5, 1, 4, 1, 3]], [[3, 1, 4, 1, 5, 9, 10]], [[3, 1, 4, 1, 5]], [[-3, -1, -4, -1, -5, -9]], [[-5, -5, -2, -8]], [[-8, -2, -5, -5]], [[-5, -5, -2, -8, -7]], [[-5, -5, -2]], [[5, 5, 2, 8]], [[10]], [[10, 11]]], 'keep_probe_outputs': {'[[3, 1, 4, 1, 5, 9]]': {'ok': True, 'value': 5}, '[[9, 5, 1, 4, 1, 3]]': {'ok': True, 'value': 5}, '[[3, 1, 4, 1, 5, 9, 10]]': {'ok': True, 'value': 9}, '[[3, 1, 4, 1, 5]]': {'ok': True, 'value': 4}, '[[-3, -1, -4, -1, -5, -9]]': {'ok': True, 'value': -3}, '[[-5, -5, -2, -8]]': {'ok': True, 'value': -5}, '[[-8, -2, -5, -5]]': {'ok': True, 'value': -5}, '[[-5, -5, -2, -8, -7]]': {'ok': True, 'value': -5}, '[[-5, -5, -2]]': {'ok': True, 'value': -5}, '[[5, 5, 2, 8]]': {'ok': True, 'value': 5}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 10}}, 'keep_probe_error': None, 'revise_probe_outputs': {'[[3, 1, 4, 1, 5, 9]]': {'ok': True, 'value': 5}, '[[9, 5, 1, 4, 1, 3]]': {'ok': True, 'value': 5}, '[[3, 1, 4, 1, 5, 9, 10]]': {'ok': True, 'value': 9}, '[[3, 1, 4, 1, 5]]': {'ok': True, 'value': 4}, '[[-3, -1, -4, -1, -5, -9]]': {'ok': True, 'value': -3}, '[[-5, -5, -2, -8]]': {'ok': True, 'value': -5}, '[[-8, -2, -5, -5]]': {'ok': True, 'value': -5}, '[[-5, -5, -2, -8, -7]]': {'ok': True, 'value': -5}, '[[-5, -5, -2]]': {'ok': True, 'value': -5}, '[[5, 5, 2, 8]]': {'ok': True, 'value': 5}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 10}}, 'revise_probe_error': None, 'reference_code': 'def find_second_largest(nums):\n    distinct = set(nums)\n    if len(distinct) < 2:\n        return None\n    sorted_distinct = sorted(distinct, reverse=True)\n    return sorted_distinct[1]', 'reference_usage': {'completion_tokens': 62, 'prompt_tokens': 151, 'total_tokens': 213, 'completion_tokens_details': {'accepted_prediction_tokens': None, 'audio_tokens': None, 'reasoning_tokens': 0, 'rejected_prediction_tokens': None}, 'prompt_tokens_details': {'audio_tokens': None, 'cached_tokens': 0}}, 'reference_probe_outputs': {'[[3, 1, 4, 1, 5, 9]]': {'ok': True, 'value': 5}, '[[9, 5, 1, 4, 1, 3]]': {'ok': True, 'value': 5}, '[[3, 1, 4, 1, 5, 9, 10]]': {'ok': True, 'value': 9}, '[[3, 1, 4, 1, 5]]': {'ok': True, 'value': 4}, '[[-3, -1, -4, -1, -5, -9]]': {'ok': True, 'value': -3}, '[[-5, -5, -2, -8]]': {'ok': True, 'value': -5}, '[[-8, -2, -5, -5]]': {'ok': True, 'value': -5}, '[[-5, -5, -2, -8, -7]]': {'ok': True, 'value': -5}, '[[-5, -5, -2]]': {'ok': True, 'value': -5}, '[[5, 5, 2, 8]]': {'ok': True, 'value': 5}, '[[10]]': {'ok': True, 'value': None}, '[[10, 11]]': {'ok': True, 'value': 10}}, 'reference_probe_error': None, 'keep_vs_reference_mismatches': [], 'revise_vs_reference_mismatches': [], 'alternative_results': []}`
- Notes: Auto-rejected from execution-backed code findings.

### plan_1701_0

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'fail'}`
- Blocking issues: `['Checker does not disambiguate repairs; gold repair is the only correct order, no nearby plausible alternative exists.']`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: The plan geometry collapses to a single linear order, violating the contrastive_locality requirement for multiple plausible local repairs.

### plan_1702_harder_1

- Source: `/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- Verdict: `reject`
- Mode: `model_with_program_findings`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'fail', 'gold_repair_informative': 'fail', 'retry_vulnerable': 'pass'}`
- Blocking issues: `["Revise trace does not violate the written constraints; water is boiled first, so adding pasta after sauté still satisfies 'water must be boiling before pasta is added'. The gold repair is not the only valid fix."]`
- Program findings: `{'supported': True, 'checker_type': 'constraint_check', 'representation': 'other', 'edges': [], 'keep_order': [], 'revise_order': [], 'durations': {}, 'keep_valid': None, 'revise_valid': None, 'valid_order_count_limited': None}`
- Notes: The pair fails because the revise trace is actually valid under the given constraints, breaking the contrastive locality requirement.
