# Saved Record Diagnostics

- Records: `artifacts/real_evolution_family_holdout_cross_encoder_finetuned_smoke/records.json`
- Benchmark: `data/real_evolution_benchmark.json`

## family_holdout_cv

### semantic_cross_encoder_finetuned_capability_gate

- count: `72`
- admissible_rate: `0.792`
- execute_rate: `0.806`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.056`
- group_counts: `{"control_policy_error": 9, "correct": 57, "tool_choice_error": 6}`
- bucket_counts: `{"correct_execute": 52, "correct_non_execute": 5, "missed_execute_abstain": 2, "missed_execute_ask_clarification": 7, "wrong_tool_choice": 6}`

### semantic_embedding_capability_gate

- count: `72`
- admissible_rate: `1.000`
- execute_rate: `0.847`
- ask_clarification_rate: `0.139`
- abstain_rate: `0.014`
- group_counts: `{"correct": 72}`
- bucket_counts: `{"correct_execute": 61, "correct_non_execute": 11}`

