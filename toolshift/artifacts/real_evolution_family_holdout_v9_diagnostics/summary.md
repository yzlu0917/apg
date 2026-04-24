# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v9/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `112`
- admissible_rate: `0.116`
- execute_rate: `0.161`
- ask_clarification_rate: `0.830`
- abstain_rate: `0.009`
- group_counts: `{"control_policy_error": 82, "correct": 13, "tool_choice_error": 17}`
- bucket_counts: `{"correct_execute": 1, "correct_non_execute": 12, "missed_execute_abstain": 1, "missed_execute_ask_clarification": 79, "wrong_non_execute_policy": 2, "wrong_tool_choice": 17}`

### semantic_capability_gate

- count: `112`
- admissible_rate: `1.000`
- execute_rate: `0.839`
- ask_clarification_rate: `0.143`
- abstain_rate: `0.018`
- group_counts: `{"correct": 112}`
- bucket_counts: `{"correct_execute": 94, "correct_non_execute": 18}`

### semantic_contract_gate

- count: `112`
- admissible_rate: `0.893`
- execute_rate: `0.946`
- ask_clarification_rate: `0.036`
- abstain_rate: `0.018`
- group_counts: `{"correct": 100, "tool_choice_error": 12}`
- bucket_counts: `{"correct_execute": 94, "correct_non_execute": 6, "wrong_tool_choice": 12}`

