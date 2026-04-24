# Protocol Reliability

- benchmark: `data/real_evolution_benchmark.json`
- methods: `none`

## Structure

- counts: `{"cases": 36, "families": 9, "sources": 63, "vendors": 10, "views": 72}`
- family_counts: `{"bitbucket": 4, "confluence": 4, "drive": 4, "jira": 4, "notion": 4, "people": 4, "sheets": 4, "slack": 4, "stripe": 4}`
- vendor_counts: `{"bitbucket": 4, "confluence": 4, "drive": 4, "drive+sheets": 1, "jira": 4, "notion": 4, "people": 4, "sheets": 3, "slack": 4, "stripe": 4}`
- action_size_histogram: `{"1": 62, "2": 10}`
- control_signature_histogram: `{"abstain": 1, "abstain+ask_clarification": 10, "execute": 61}`
- multi_action_view_fraction: `0.139`
- multi_action_negative_fraction: `0.909`
- case_source_summary: `{"kind_count_histogram": {"1": 2, "2": 34}, "max_source_count": 4, "mean_source_count": 2.5833333333333335, "min_source_count": 1, "mixed_kind_cases": 34, "mixed_vendor_cases": 1, "source_count_histogram": {"1": 2, "2": 14, "3": 17, "4": 3}, "vendor_count_histogram": {"1": 35, "2": 1}}`

## `canonical`

- variant_details: `{}`

## `single_action_only`

- variant_details: `{}`

## `ask_only_negative`

- variant_details: `{}`

## `abstain_only_negative`

- variant_details: `{}`

