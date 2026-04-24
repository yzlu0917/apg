# Dev vs Blind Retained Methods

- dev summary: `artifacts/real_evolution_family_holdout_clause_localization_capability_v1/summary.json`
- blind summary: `artifacts/real_evolution_blind_review_v1/summary.json`
- methods: `semantic_embedding_capability_gate, semantic_clause_localization_capability_gate`

| Method | Dev CAA | Blind CAA | dCAA | Dev CAA+ | Blind CAA+ | dCAA+ | Dev NOS | Blind NOS | dNOS | Dev POC | Blind POC | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_embedding_capability_gate` | 1.000 | 0.917 | -0.083 | 1.000 | 1.000 | 0.000 | 1.000 | 0.727 | -0.273 | 1.000 | 1.000 | 0.000 |
| `semantic_clause_localization_capability_gate` | 0.875 | 0.781 | -0.094 | 0.820 | 0.885 | 0.065 | 0.864 | 0.818 | -0.045 | 0.820 | 0.885 | 0.065 |

## `semantic_embedding_capability_gate`

- lowest blind `NOS` family: `slack_auth (0.000)`
- lowest blind `CAA+` family: `github_rest (1.000)`

## `semantic_clause_localization_capability_gate`

- lowest blind `NOS` family: `gitlab_rest (0.500)`
- lowest blind `CAA+` family: `youtube_channels (0.500)`

