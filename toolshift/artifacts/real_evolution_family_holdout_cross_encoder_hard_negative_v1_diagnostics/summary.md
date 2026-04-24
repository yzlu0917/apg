# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_cross_encoder_hard_negative_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### semantic_cross_encoder_hard_negative_capability_gate

- count: `144`
- admissible_rate: `0.736`
- execute_rate: `0.764`
- ask_clarification_rate: `0.181`
- abstain_rate: `0.056`
- group_counts: `{"control_policy_error": 25, "correct": 106, "tool_choice_error": 13}`
- bucket_counts: `{"correct_execute": 97, "correct_non_execute": 9, "missed_execute_abstain": 4, "missed_execute_ask_clarification": 21, "wrong_tool_choice": 13}`

### semantic_embedding_capability_gate

- count: `144`
- admissible_rate: `1.000`
- execute_rate: `0.847`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.014`
- group_counts: `{"correct": 144}`
- bucket_counts: `{"correct_execute": 122, "correct_non_execute": 22}`

