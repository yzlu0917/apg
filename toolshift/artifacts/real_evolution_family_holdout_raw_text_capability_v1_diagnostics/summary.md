# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_raw_text_capability_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### semantic_embedding_capability_gate

- count: `144`
- admissible_rate: `1.000`
- execute_rate: `0.847`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.014`
- group_counts: `{"correct": 144}`
- bucket_counts: `{"correct_execute": 122, "correct_non_execute": 22}`

### semantic_raw_text_capability_gate

- count: `144`
- admissible_rate: `0.847`
- execute_rate: `0.861`
- ask_clarification_rate: `0.125`
- abstain_rate: `0.014`
- group_counts: `{"control_policy_error": 10, "correct": 122, "tool_choice_error": 12}`
- bucket_counts: `{"correct_execute": 112, "correct_non_execute": 10, "missed_execute_ask_clarification": 10, "wrong_tool_choice": 12}`

