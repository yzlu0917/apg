# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_teacher_distilled_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `aug_only, teacher_distilled_bottleneck_scc`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| aug_only | 0.093 | 0.000 | 0.606 | 0.000 | 1.000 | 0.907 | 1.000 |
| teacher_distilled_bottleneck_scc | 0.102 | 0.000 | 0.636 | 0.000 | 0.995 | 0.902 | 1.000 |

## teacher_distilled_bottleneck_scc vs aug_only

- improved_pair_count: `2`
- regressed_pair_count: `0`
- improved_distinct_views: `2`
- regressed_distinct_views: `0`
- strictly_fixed_views: `["stripe_update_subscription_source::negative_source_removed"]`

### Delta Metrics

- CAA_clean: `0.009`
- CAA_negative: `0.030`
- CAA_overall: `0.009`
- CAA_positive: `0.000`
- NOS: `0.030`
- POC: `0.000`
- contract_validity: `0.000`
- coverage: `-0.005`
- negative_coverage: `-0.030`
- selective_risk: `-0.005`

### Incremental Fixes

- by_transform: `{"clean": 1, "negative_source_removed": 1}`
- by_family_tag: `{"stripe": 2}`
- by_primary_tool_id: `{"stripe.subscriptions.update_default_source": 2}`
- from_group: `{"tool_choice_error": 2}`
- from_bucket: `{"wrong_tool_choice": 2}`

### Regressions

- by_transform: `{}`
- by_family_tag: `{}`
- from_bucket: `{}`

### Representative Fixes

- `stripe_update_subscription_source::clean` (stripe / clean / stripe.subscriptions.update_default_source): `wrong_tool_choice -> correct_execute`
- `stripe_update_subscription_source::negative_source_removed` (stripe / negative_source_removed / stripe.subscriptions.update_default_source): `wrong_tool_choice -> correct_non_execute`

## By Family

### aug_only

- `bitbucket`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `confluence`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `drive`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `jira`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `notion`: `CAA=0.250` `CAA+=0.000` `NOS=1.000` `count=24`
- `people`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `sheets`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `slack`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `stripe`: `CAA=0.083` `CAA+=0.000` `NOS=0.333` `count=24`

### teacher_distilled_bottleneck_scc

- `bitbucket`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `confluence`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `drive`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `jira`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `notion`: `CAA=0.250` `CAA+=0.000` `NOS=1.000` `count=24`
- `people`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `sheets`: `CAA=0.125` `CAA+=0.000` `NOS=1.000` `count=24`
- `slack`: `CAA=0.000` `CAA+=0.000` `NOS=0.000` `count=24`
- `stripe`: `CAA=0.167` `CAA+=0.000` `NOS=0.500` `count=24`
