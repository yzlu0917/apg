# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_cross_encoder_dual_threshold_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_cross_encoder_dual_threshold_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_cross_encoder_dual_threshold_capability_gate | 0.736 | 0.760 | 0.409 | 0.760 | 0.944 | 0.250 | 1.000 |

## semantic_cross_encoder_dual_threshold_capability_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `38`
- improved_distinct_views: `0`
- regressed_distinct_views: `28`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.181`
- CAA_negative: `-0.591`
- CAA_overall: `-0.264`
- CAA_positive: `-0.240`
- NOS: `-0.591`
- POC: `-0.240`
- contract_validity: `0.000`
- coverage: `-0.042`
- negative_coverage: `-0.091`
- selective_risk: `0.250`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 13, "negative_account_object_removed": 2, "negative_legacy_identifier_removed": 2, "negative_parent_scope_change": 2, "negative_removed_capability": 2, "negative_search_replacement": 2, "negative_source_removed": 1, "negative_space_key_lookup_split": 2, "positive_version_migration": 12}`
- by_family_tag: `{"bitbucket": 5, "confluence": 6, "drive": 5, "jira": 4, "notion": 5, "sheets": 2, "slack": 2, "stripe": 9}`
- from_bucket: `{"correct_execute": 25, "correct_non_execute": 13}`

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

### semantic_cross_encoder_dual_threshold_capability_gate

- `bitbucket`: `CAA=0.688` `CAA+=0.667` `NOS=0.000` `count=16`
- `confluence`: `CAA=0.625` `CAA+=0.833` `NOS=0.000` `count=16`
- `drive`: `CAA=0.688` `CAA+=0.167` `NOS=1.000` `count=16`
- `jira`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `notion`: `CAA=0.688` `CAA+=1.000` `NOS=0.000` `count=16`
- `people`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.875` `CAA+=0.833` `NOS=1.000` `count=16`
- `slack`: `CAA=0.875` `CAA+=0.833` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.438` `CAA+=0.500` `NOS=0.250` `count=16`
