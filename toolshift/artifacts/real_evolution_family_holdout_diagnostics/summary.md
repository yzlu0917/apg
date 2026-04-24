# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `24`
- admissible_rate: `0.167`
- execute_rate: `0.000`
- ask_clarification_rate: `1.000`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 20, "correct": 4}`
- bucket_counts: `{"correct_non_execute": 4, "missed_execute_ask_clarification": 18, "wrong_non_execute_policy": 2}`

### semantic_contract_gate

- count: `24`
- admissible_rate: `0.833`
- execute_rate: `0.917`
- ask_clarification_rate: `0.000`
- abstain_rate: `0.083`
- group_counts: `{"correct": 20, "tool_choice_error": 4}`
- bucket_counts: `{"correct_execute": 18, "correct_non_execute": 2, "wrong_tool_choice": 4}`

