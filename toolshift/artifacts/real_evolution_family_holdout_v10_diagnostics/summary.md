# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v10/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `128`
- admissible_rate: `0.117`
- execute_rate: `0.172`
- ask_clarification_rate: `0.828`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 92, "correct": 15, "tool_choice_error": 21}`
- bucket_counts: `{"correct_execute": 1, "correct_non_execute": 14, "missed_execute_ask_clarification": 90, "wrong_non_execute_policy": 2, "wrong_tool_choice": 21}`

### semantic_capability_gate

- count: `128`
- admissible_rate: `1.000`
- execute_rate: `0.844`
- ask_clarification_rate: `0.141`
- abstain_rate: `0.016`
- group_counts: `{"correct": 128}`
- bucket_counts: `{"correct_execute": 108, "correct_non_execute": 20}`

### semantic_contract_gate

- count: `128`
- admissible_rate: `0.891`
- execute_rate: `0.953`
- ask_clarification_rate: `0.031`
- abstain_rate: `0.016`
- group_counts: `{"correct": 114, "tool_choice_error": 14}`
- bucket_counts: `{"correct_execute": 108, "correct_non_execute": 6, "wrong_tool_choice": 14}`

