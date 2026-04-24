# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v8/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `96`
- admissible_rate: `0.115`
- execute_rate: `0.177`
- ask_clarification_rate: `0.823`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 69, "correct": 11, "tool_choice_error": 16}`
- bucket_counts: `{"correct_execute": 1, "correct_non_execute": 10, "missed_execute_ask_clarification": 67, "wrong_non_execute_policy": 2, "wrong_tool_choice": 16}`

### semantic_capability_gate

- count: `96`
- admissible_rate: `1.000`
- execute_rate: `0.833`
- ask_clarification_rate: `0.146`
- abstain_rate: `0.021`
- group_counts: `{"correct": 96}`
- bucket_counts: `{"correct_execute": 80, "correct_non_execute": 16}`

### semantic_contract_gate

- count: `96`
- admissible_rate: `0.896`
- execute_rate: `0.938`
- ask_clarification_rate: `0.042`
- abstain_rate: `0.021`
- group_counts: `{"correct": 86, "tool_choice_error": 10}`
- bucket_counts: `{"correct_execute": 80, "correct_non_execute": 6, "wrong_tool_choice": 10}`

