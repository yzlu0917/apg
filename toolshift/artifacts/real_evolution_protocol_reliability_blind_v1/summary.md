# Protocol Reliability

- benchmark: `data/real_evolution_blind_benchmark.json`
- methods: `qwen3_8b, qwen3_4b, scaffold`

## Structure

- counts: `{"cases": 24, "families": 6, "sources": 42, "vendors": 5, "views": 48}`
- family_counts: `{"github_rest": 4, "gitlab_rest": 4, "slack_auth": 4, "trello": 4, "youtube": 4, "youtube_channels": 4}`
- vendor_counts: `{"github": 4, "gitlab": 4, "slack": 4, "trello": 4, "youtube": 8}`
- action_size_histogram: `{"1": 38, "2": 10}`
- control_signature_histogram: `{"abstain": 1, "abstain+ask_clarification": 10, "execute": 37}`
- multi_action_view_fraction: `0.208`
- multi_action_negative_fraction: `0.909`
- case_source_summary: `{"kind_count_histogram": {"1": 1, "2": 18, "3": 5}, "max_source_count": 4, "mean_source_count": 2.75, "min_source_count": 2, "mixed_kind_cases": 23, "mixed_vendor_cases": 0, "source_count_histogram": {"2": 11, "3": 8, "4": 5}, "vendor_count_histogram": {"1": 24}}`

## `canonical`

- variant_details: `{"excluded_view_count": 0, "relabeled_negative_view_count": 0}`

| Method | CAA | CAA+ | NOS | POC | Coverage | Core | Ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3_8b` | 0.875 | 0.923 | 0.636 | 0.923 | 0.854 | 48 | 0 |
| `qwen3_4b` | 0.812 | 0.923 | 0.364 | 0.923 | 0.917 | 48 | 0 |
| `scaffold` | 0.917 | 1.000 | 0.727 | 1.000 | 0.979 | 48 | 0 |

## `single_action_only`

- variant_details: `{"excluded_view_count": 10, "relabeled_negative_view_count": 0}`

| Method | CAA | CAA+ | NOS | POC | Coverage | Core | Ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3_8b` | 0.947 | 0.923 | 1.000 | 0.923 | 0.947 | 38 | 10 |
| `qwen3_4b` | 0.947 | 0.923 | 1.000 | 0.923 | 0.974 | 38 | 10 |
| `scaffold` | 0.974 | 1.000 | 1.000 | 1.000 | 0.974 | 38 | 10 |

## `ask_only_negative`

- variant_details: `{"excluded_view_count": 0, "relabeled_negative_view_count": 10}`

| Method | CAA | CAA+ | NOS | POC | Coverage | Core | Ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3_8b` | 0.771 | 0.923 | 0.182 | 0.923 | 0.854 | 48 | 0 |
| `qwen3_4b` | 0.750 | 0.923 | 0.091 | 0.923 | 0.917 | 48 | 0 |
| `scaffold` | 0.917 | 1.000 | 0.727 | 1.000 | 0.979 | 48 | 0 |

## `abstain_only_negative`

- variant_details: `{"excluded_view_count": 0, "relabeled_negative_view_count": 10}`

| Method | CAA | CAA+ | NOS | POC | Coverage | Core | Ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `qwen3_8b` | 0.854 | 0.923 | 0.545 | 0.923 | 0.854 | 48 | 0 |
| `qwen3_4b` | 0.812 | 0.923 | 0.364 | 0.923 | 0.917 | 48 | 0 |
| `scaffold` | 0.771 | 1.000 | 0.091 | 1.000 | 0.979 | 48 | 0 |

