# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_clause_localization_calibrated_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_clause_localization_calibrated_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_clause_localization_calibrated_gate | 0.840 | 0.760 | 0.773 | 0.760 | 0.986 | 0.162 | 1.000 |

## semantic_clause_localization_calibrated_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `23`
- improved_distinct_views: `0`
- regressed_distinct_views: `15`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.083`
- CAA_negative: `-0.227`
- CAA_overall: `-0.160`
- CAA_positive: `-0.240`
- NOS: `-0.227`
- POC: `-0.240`
- contract_validity: `0.000`
- coverage: `0.000`
- negative_coverage: `0.000`
- selective_risk: `0.162`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 6, "negative_parent_scope_change": 1, "negative_search_replacement": 2, "negative_source_removed": 2, "positive_version_migration": 12}`
- by_family_tag: `{"drive": 4, "jira": 2, "notion": 3, "people": 2, "sheets": 6, "stripe": 6}`
- from_bucket: `{"correct_execute": 18, "correct_non_execute": 5}`

### Representative Fixes

- none

## By Family

### semantic_embedding_capability_gate

- `bitbucket`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `confluence`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `drive`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `jira`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `notion`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `people`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `sheets`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`

### semantic_clause_localization_calibrated_gate

- `bitbucket`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `confluence`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `drive`: `CAA=0.750` `CAA+=0.833` `NOS=1.000` `count=16`
- `jira`: `CAA=0.875` `CAA+=0.833` `NOS=1.000` `count=16`
- `notion`: `CAA=0.812` `CAA+=1.000` `NOS=0.250` `count=16`
- `people`: `CAA=0.875` `CAA+=0.667` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.625` `CAA+=0.000` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.625` `CAA+=0.500` `NOS=0.500` `count=16`
