# Saved Record Diagnostics

- Records: `artifacts/family_matched_budget_v2/records.json`
- Benchmark: `data/family_benchmark.json`

## case_holdout_cv

### aug_only

- count: `216`
- admissible_rate: `0.880`
- execute_rate: `0.667`
- ask_clarification_rate: `0.185`
- abstain_rate: `0.148`
- group_counts: `{"control_policy_error": 15, "correct": 190, "tool_choice_error": 11}`
- bucket_counts: `{"correct_execute": 133, "correct_non_execute": 57, "missed_execute_abstain": 2, "missed_execute_ask_clarification": 9, "wrong_non_execute_policy": 4, "wrong_tool_choice": 11}`

### scc_lite

- count: `216`
- admissible_rate: `0.880`
- execute_rate: `0.667`
- ask_clarification_rate: `0.185`
- abstain_rate: `0.148`
- group_counts: `{"control_policy_error": 15, "correct": 190, "tool_choice_error": 11}`
- bucket_counts: `{"correct_execute": 133, "correct_non_execute": 57, "missed_execute_abstain": 2, "missed_execute_ask_clarification": 9, "wrong_non_execute_policy": 4, "wrong_tool_choice": 11}`

## combo_holdout

### aug_only

- count: `216`
- admissible_rate: `0.972`
- execute_rate: `0.639`
- ask_clarification_rate: `0.194`
- abstain_rate: `0.167`
- group_counts: `{"control_policy_error": 6, "correct": 210}`
- bucket_counts: `{"correct_execute": 138, "correct_non_execute": 72, "missed_execute_ask_clarification": 6}`

### scc_lite

- count: `216`
- admissible_rate: `0.972`
- execute_rate: `0.639`
- ask_clarification_rate: `0.194`
- abstain_rate: `0.167`
- group_counts: `{"control_policy_error": 6, "correct": 210}`
- bucket_counts: `{"correct_execute": 138, "correct_non_execute": 72, "missed_execute_ask_clarification": 6}`

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

