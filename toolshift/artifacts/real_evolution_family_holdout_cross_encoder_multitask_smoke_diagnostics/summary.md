# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_cross_encoder_multitask_smoke/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### semantic_cross_encoder_multitask_capability_gate

- count: `72`
- admissible_rate: `0.806`
- execute_rate: `0.847`
- ask_clarification_rate: `0.097`
- abstain_rate: `0.056`
- group_counts: `{"control_policy_error": 7, "correct": 58, "tool_choice_error": 7}`
- bucket_counts: `{"correct_execute": 54, "correct_non_execute": 4, "missed_execute_abstain": 2, "missed_execute_ask_clarification": 5, "wrong_tool_choice": 7}`

### semantic_embedding_capability_gate

- count: `72`
- admissible_rate: `1.000`
- execute_rate: `0.847`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.014`
- group_counts: `{"correct": 72}`
- bucket_counts: `{"correct_execute": 61, "correct_non_execute": 11}`

