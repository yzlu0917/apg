# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v3/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `48`
- admissible_rate: `0.167`
- execute_rate: `0.000`
- ask_clarification_rate: `0.938`
- abstain_rate: `0.062`
- group_counts: `{"control_policy_error": 40, "correct": 8}`
- bucket_counts: `{"correct_non_execute": 8, "missed_execute_abstain": 2, "missed_execute_ask_clarification": 36, "wrong_non_execute_policy": 2}`

### semantic_capability_gate

- count: `48`
- admissible_rate: `1.000`
- execute_rate: `0.792`
- ask_clarification_rate: `0.167`
- abstain_rate: `0.042`
- group_counts: `{"correct": 48}`
- bucket_counts: `{"correct_execute": 38, "correct_non_execute": 10}`

### semantic_contract_gate

- count: `48`
- admissible_rate: `0.833`
- execute_rate: `0.958`
- ask_clarification_rate: `0.000`
- abstain_rate: `0.042`
- group_counts: `{"correct": 40, "tool_choice_error": 8}`
- bucket_counts: `{"correct_execute": 38, "correct_non_execute": 2, "wrong_tool_choice": 8}`

