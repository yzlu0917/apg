# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_cross_encoder_ranked_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_cross_encoder_ranked_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_cross_encoder_ranked_capability_gate | 0.792 | 0.720 | 0.455 | 0.720 | 0.944 | 0.191 | 1.000 |

## semantic_cross_encoder_ranked_capability_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `30`
- improved_distinct_views: `0`
- regressed_distinct_views: `15`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.056`
- CAA_negative: `-0.545`
- CAA_overall: `-0.208`
- CAA_positive: `-0.280`
- NOS: `-0.545`
- POC: `-0.280`
- contract_validity: `0.000`
- coverage: `-0.042`
- negative_coverage: `-0.091`
- selective_risk: `0.191`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 4, "negative_legacy_identifier_removed": 2, "negative_parent_scope_change": 2, "negative_removed_capability": 2, "negative_search_replacement": 2, "negative_source_removed": 2, "negative_space_key_lookup_split": 2, "positive_version_migration": 14}`
- by_family_tag: `{"bitbucket": 2, "confluence": 2, "drive": 6, "jira": 2, "notion": 4, "people": 4, "sheets": 6, "stripe": 4}`
- from_bucket: `{"correct_execute": 18, "correct_non_execute": 12}`

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

### semantic_cross_encoder_ranked_capability_gate

- `bitbucket`: `CAA=0.875` `CAA+=1.000` `NOS=1.000` `count=16`
- `confluence`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `drive`: `CAA=0.625` `CAA+=0.333` `NOS=1.000` `count=16`
- `jira`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `notion`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `people`: `CAA=0.750` `CAA+=0.333` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.625` `CAA+=0.000` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
