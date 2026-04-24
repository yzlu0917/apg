# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v6/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `64`
- admissible_rate: `0.156`
- execute_rate: `0.156`
- ask_clarification_rate: `0.844`
- abstain_rate: `0.000`
- group_counts: `{"argument_or_contract_error": 1, "control_policy_error": 44, "correct": 10, "tool_choice_error": 9}`
- bucket_counts: `{"correct_non_execute": 10, "invalid_execute_contract": 1, "missed_execute_ask_clarification": 42, "wrong_non_execute_policy": 2, "wrong_tool_choice": 9}`

### semantic_capability_gate

- count: `64`
- admissible_rate: `1.000`
- execute_rate: `0.812`
- ask_clarification_rate: `0.156`
- abstain_rate: `0.031`
- group_counts: `{"correct": 64}`
- bucket_counts: `{"correct_execute": 52, "correct_non_execute": 12}`

### semantic_contract_gate

- count: `64`
- admissible_rate: `0.875`
- execute_rate: `0.938`
- ask_clarification_rate: `0.031`
- abstain_rate: `0.031`
- group_counts: `{"correct": 56, "tool_choice_error": 8}`
- bucket_counts: `{"correct_execute": 52, "correct_non_execute": 4, "wrong_tool_choice": 8}`

