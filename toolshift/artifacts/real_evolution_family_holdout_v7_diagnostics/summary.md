# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v7/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `80`
- admissible_rate: `0.138`
- execute_rate: `0.263`
- ask_clarification_rate: `0.738`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 51, "correct": 11, "tool_choice_error": 18}`
- bucket_counts: `{"correct_execute": 3, "correct_non_execute": 8, "missed_execute_ask_clarification": 49, "wrong_non_execute_policy": 2, "wrong_tool_choice": 18}`

### semantic_capability_gate

- count: `80`
- admissible_rate: `1.000`
- execute_rate: `0.825`
- ask_clarification_rate: `0.150`
- abstain_rate: `0.025`
- group_counts: `{"correct": 80}`
- bucket_counts: `{"correct_execute": 66, "correct_non_execute": 14}`

### semantic_contract_gate

- count: `80`
- admissible_rate: `0.875`
- execute_rate: `0.950`
- ask_clarification_rate: `0.025`
- abstain_rate: `0.025`
- group_counts: `{"correct": 70, "tool_choice_error": 10}`
- bucket_counts: `{"correct_execute": 66, "correct_non_execute": 4, "wrong_tool_choice": 10}`

