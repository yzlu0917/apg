# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_pair_text_capability_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_pair_text_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_pair_text_capability_gate | 0.743 | 0.780 | 0.909 | 0.780 | 0.986 | 0.261 | 1.000 |

## semantic_pair_text_capability_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `37`
- improved_distinct_views: `0`
- regressed_distinct_views: `20`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.333`
- CAA_negative: `-0.091`
- CAA_overall: `-0.257`
- CAA_positive: `-0.220`
- NOS: `-0.091`
- POC: `-0.220`
- contract_validity: `0.000`
- coverage: `0.000`
- negative_coverage: `0.000`
- selective_risk: `0.261`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 24, "negative_search_replacement": 2, "positive_version_migration": 11}`
- by_family_tag: `{"bitbucket": 6, "confluence": 6, "jira": 5, "notion": 2, "people": 6, "sheets": 2, "stripe": 10}`
- from_bucket: `{"correct_execute": 35, "correct_non_execute": 2}`

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

### semantic_pair_text_capability_gate

- `bitbucket`: `CAA=0.625` `CAA+=0.667` `NOS=1.000` `count=16`
- `confluence`: `CAA=0.625` `CAA+=1.000` `NOS=1.000` `count=16`
- `drive`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `jira`: `CAA=0.688` `CAA+=0.833` `NOS=1.000` `count=16`
- `notion`: `CAA=0.875` `CAA+=1.000` `NOS=0.500` `count=16`
- `people`: `CAA=0.625` `CAA+=0.667` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.875` `CAA+=0.667` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.375` `CAA+=0.000` `NOS=1.000` `count=16`
