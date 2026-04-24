# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_teacher_distilled_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### aug_only

- count: `216`
- admissible_rate: `0.093`
- execute_rate: `0.171`
- ask_clarification_rate: `0.829`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 159, "correct": 20, "tool_choice_error": 37}`
- bucket_counts: `{"correct_non_execute": 20, "missed_execute_ask_clarification": 156, "wrong_non_execute_policy": 3, "wrong_tool_choice": 37}`

### seed_only

- count: `216`
- admissible_rate: `0.083`
- execute_rate: `0.194`
- ask_clarification_rate: `0.806`
- abstain_rate: `0.000`
- group_counts: `{"control_policy_error": 156, "correct": 18, "tool_choice_error": 42}`
- bucket_counts: `{"correct_non_execute": 18, "missed_execute_ask_clarification": 153, "wrong_non_execute_policy": 3, "wrong_tool_choice": 42}`

### teacher_distilled_bottleneck_scc

- count: `216`
- admissible_rate: `0.102`
- execute_rate: `0.162`
- ask_clarification_rate: `0.833`
- abstain_rate: `0.005`
- group_counts: `{"control_policy_error": 160, "correct": 22, "tool_choice_error": 34}`
- bucket_counts: `{"correct_execute": 1, "correct_non_execute": 21, "missed_execute_ask_clarification": 157, "wrong_non_execute_policy": 3, "wrong_tool_choice": 34}`

