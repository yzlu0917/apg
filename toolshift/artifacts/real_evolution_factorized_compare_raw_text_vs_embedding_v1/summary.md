# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_raw_text_capability_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_raw_text_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_raw_text_capability_gate | 0.847 | 1.000 | 0.455 | 1.000 | 0.986 | 0.155 | 1.000 |

## semantic_raw_text_capability_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `22`
- improved_distinct_views: `0`
- regressed_distinct_views: `11`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.139`
- CAA_negative: `-0.545`
- CAA_overall: `-0.153`
- CAA_positive: `0.000`
- NOS: `-0.545`
- POC: `0.000`
- contract_validity: `0.000`
- coverage: `0.000`
- negative_coverage: `0.000`
- selective_risk: `0.155`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 10, "negative_account_object_removed": 2, "negative_legacy_identifier_removed": 2, "negative_parent_scope_change": 2, "negative_removed_capability": 2, "negative_search_replacement": 2, "negative_space_key_lookup_split": 2}`
- by_family_tag: `{"bitbucket": 2, "confluence": 2, "jira": 4, "notion": 4, "people": 2, "sheets": 4, "slack": 2, "stripe": 2}`
- from_bucket: `{"correct_execute": 10, "correct_non_execute": 12}`

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

### semantic_raw_text_capability_gate

- `bitbucket`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `confluence`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `drive`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `jira`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `notion`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `people`: `CAA=0.875` `CAA+=1.000` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.750` `CAA+=1.000` `NOS=1.000` `count=16`
- `slack`: `CAA=0.875` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.875` `CAA+=1.000` `NOS=0.500` `count=16`
