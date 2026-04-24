# Saved Record Diagnostics

- Records: `artifacts/family_matched_budget_contract_gate/records.json`
- Benchmark: `data/family_benchmark.json`

## family_holdout_cv

### aug_only

- count: `216`
- admissible_rate: `0.181`
- execute_rate: `0.000`
- ask_clarification_rate: `0.755`
- abstain_rate: `0.245`
- group_counts: `{"control_policy_error": 177, "correct": 39}`
- bucket_counts: `{"correct_non_execute": 39, "missed_execute_abstain": 30, "missed_execute_ask_clarification": 114, "wrong_non_execute_policy": 33}`

### scc_lite

- count: `216`
- admissible_rate: `0.185`
- execute_rate: `0.000`
- ask_clarification_rate: `0.755`
- abstain_rate: `0.245`
- group_counts: `{"control_policy_error": 176, "correct": 40}`
- bucket_counts: `{"correct_non_execute": 40, "missed_execute_abstain": 29, "missed_execute_ask_clarification": 115, "wrong_non_execute_policy": 32}`

### semantic_contract_gate

- count: `216`
- admissible_rate: `0.972`
- execute_rate: `0.657`
- ask_clarification_rate: `0.194`
- abstain_rate: `0.148`
- group_counts: `{"control_policy_error": 6, "correct": 210}`
- bucket_counts: `{"correct_execute": 142, "correct_non_execute": 68, "missed_execute_ask_clarification": 2, "wrong_non_execute_policy": 4}`

### semantic_gate

- count: `216`
- admissible_rate: `0.806`
- execute_rate: `0.824`
- ask_clarification_rate: `0.028`
- abstain_rate: `0.148`
- group_counts: `{"control_policy_error": 6, "correct": 174, "tool_choice_error": 36}`
- bucket_counts: `{"correct_execute": 142, "correct_non_execute": 32, "missed_execute_ask_clarification": 2, "wrong_non_execute_policy": 4, "wrong_tool_choice": 36}`

