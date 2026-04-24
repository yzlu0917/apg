# Saved Record Diagnostics

- Records: `artifacts/family_matched_budget_semantic_gate_smoke/records.json`
- Benchmark: `data/family_benchmark.json`

## family_holdout_cv

### aug_only

- count: `108`
- admissible_rate: `0.185`
- execute_rate: `0.000`
- ask_clarification_rate: `0.750`
- abstain_rate: `0.250`
- group_counts: `{"control_policy_error": 88, "correct": 20}`
- bucket_counts: `{"correct_non_execute": 20, "missed_execute_abstain": 15, "missed_execute_ask_clarification": 57, "wrong_non_execute_policy": 16}`

### scc_lite

- count: `108`
- admissible_rate: `0.185`
- execute_rate: `0.000`
- ask_clarification_rate: `0.750`
- abstain_rate: `0.250`
- group_counts: `{"control_policy_error": 88, "correct": 20}`
- bucket_counts: `{"correct_non_execute": 20, "missed_execute_abstain": 15, "missed_execute_ask_clarification": 57, "wrong_non_execute_policy": 16}`

### semantic_gate

- count: `108`
- admissible_rate: `0.806`
- execute_rate: `0.824`
- ask_clarification_rate: `0.028`
- abstain_rate: `0.148`
- group_counts: `{"control_policy_error": 3, "correct": 87, "tool_choice_error": 18}`
- bucket_counts: `{"correct_execute": 71, "correct_non_execute": 16, "missed_execute_ask_clarification": 1, "wrong_non_execute_policy": 2, "wrong_tool_choice": 18}`

