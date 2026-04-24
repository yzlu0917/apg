# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v4/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `64`
- admissible_rate: `0.156`
- execute_rate: `0.156`
- ask_clarification_rate: `0.844`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 44, "correct": 10, "tool_choice_error": 10}`
- bucket_counts: `{"correct_non_execute": 10, "missed_execute_ask_clarification": 42, "wrong_non_execute_policy": 2, "wrong_tool_choice": 10}`

### semantic_capability_gate

- count: `64`
- admissible_rate: `0.938`
- execute_rate: `0.750`
- ask_clarification_rate: `0.219`
- abstain_rate: `0.031`
- group_counts: `{"control_policy_error": 4, "correct": 60}`
- bucket_counts: `{"correct_execute": 48, "correct_non_execute": 12, "missed_execute_ask_clarification": 4}`

### semantic_contract_gate

- count: `64`
- admissible_rate: `0.812`
- execute_rate: `0.875`
- ask_clarification_rate: `0.094`
- abstain_rate: `0.031`
- group_counts: `{"control_policy_error": 4, "correct": 52, "tool_choice_error": 8}`
- bucket_counts: `{"correct_execute": 48, "correct_non_execute": 4, "missed_execute_ask_clarification": 4, "wrong_tool_choice": 8}`

