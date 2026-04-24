# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_v11/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `144`
- admissible_rate: `0.090`
- execute_rate: `0.174`
- ask_clarification_rate: `0.826`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 106, "correct": 13, "tool_choice_error": 25}`
- bucket_counts: `{"correct_non_execute": 13, "missed_execute_ask_clarification": 104, "wrong_non_execute_policy": 2, "wrong_tool_choice": 25}`

### semantic_capability_gate

- count: `144`
- admissible_rate: `1.000`
- execute_rate: `0.847`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.014`
- group_counts: `{"correct": 144}`
- bucket_counts: `{"correct_execute": 122, "correct_non_execute": 22}`

### semantic_contract_gate

- count: `144`
- admissible_rate: `0.889`
- execute_rate: `0.958`
- ask_clarification_rate: `0.028`
- abstain_rate: `0.014`
- group_counts: `{"correct": 128, "tool_choice_error": 16}`
- bucket_counts: `{"correct_execute": 122, "correct_non_execute": 6, "wrong_tool_choice": 16}`

