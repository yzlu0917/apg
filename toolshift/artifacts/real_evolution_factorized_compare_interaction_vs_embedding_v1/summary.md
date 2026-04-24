# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_interaction_capability_v1/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_embedding_capability_gate, semantic_interaction_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_embedding_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |
| semantic_interaction_capability_gate | 0.688 | 0.680 | 0.818 | 0.680 | 0.986 | 0.317 | 1.000 |

## semantic_interaction_capability_gate vs semantic_embedding_capability_gate

- improved_pair_count: `0`
- regressed_pair_count: `45`
- improved_distinct_views: `0`
- regressed_distinct_views: `26`
- strictly_fixed_views: `[]`

### Delta Metrics

- CAA_clean: `-0.347`
- CAA_negative: `-0.182`
- CAA_overall: `-0.312`
- CAA_positive: `-0.320`
- NOS: `-0.182`
- POC: `-0.320`
- contract_validity: `0.000`
- coverage: `0.000`
- negative_coverage: `0.000`
- selective_risk: `0.317`

### Incremental Fixes

- by_transform: `{}`
- by_family_tag: `{}`
- by_primary_tool_id: `{}`
- from_group: `{}`
- from_bucket: `{}`

### Regressions

- by_transform: `{"clean": 25, "negative_source_removed": 2, "negative_space_key_lookup_split": 2, "positive_version_migration": 16}`
- by_family_tag: `{"bitbucket": 8, "confluence": 4, "drive": 2, "jira": 8, "notion": 4, "people": 5, "sheets": 4, "slack": 6, "stripe": 4}`
- from_bucket: `{"correct_execute": 41, "correct_non_execute": 4}`

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

### semantic_interaction_capability_gate

- `bitbucket`: `CAA=0.500` `CAA+=0.500` `NOS=1.000` `count=16`
- `confluence`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `drive`: `CAA=0.875` `CAA+=0.833` `NOS=1.000` `count=16`
- `jira`: `CAA=0.500` `CAA+=0.333` `NOS=1.000` `count=16`
- `notion`: `CAA=0.750` `CAA+=0.500` `NOS=1.000` `count=16`
- `people`: `CAA=0.688` `CAA+=0.667` `NOS=1.000` `count=16`
- `sheets`: `CAA=0.750` `CAA+=0.667` `NOS=1.000` `count=16`
- `slack`: `CAA=0.625` `CAA+=0.667` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.750` `CAA+=1.000` `NOS=0.500` `count=16`
