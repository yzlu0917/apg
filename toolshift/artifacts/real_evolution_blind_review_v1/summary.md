# Blind Review

- dev benchmark: `data/real_evolution_benchmark.json`
- blind benchmark: `data/real_evolution_blind_benchmark.json`
- methods: `semantic_embedding_capability_gate, semantic_clause_localization_capability_gate`
- seeds: `0, 1`

Frozen blind panel is used here only for final review; no method selection is performed on these results.

## `semantic_embedding_capability_gate`

| Metric | Value |
| --- | ---: |
| `CAA` | 0.917 |
| `CAA_clean` | 0.958 |
| `CAA+` | 1.000 |
| `NOS` | 0.727 |
| `POC` | 1.000 |
| `coverage` | 0.979 |

| Family | CAA | CAA+ | NOS | POC | Coverage | Views |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `github_rest` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 8 |
| `gitlab_rest` | 0.875 | 1.000 | 0.500 | 1.000 | 1.000 | 8 |
| `slack_auth` | 0.875 | 1.000 | 0.000 | 1.000 | 1.000 | 8 |
| `trello` | 0.875 | 1.000 | 0.500 | 1.000 | 1.000 | 8 |
| `youtube` | 1.000 | 1.000 | 1.000 | 1.000 | 0.875 | 8 |
| `youtube_channels` | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 | 8 |

## `semantic_clause_localization_capability_gate`

| Metric | Value |
| --- | ---: |
| `CAA` | 0.781 |
| `CAA_clean` | 0.708 |
| `CAA+` | 0.885 |
| `NOS` | 0.818 |
| `POC` | 0.885 |
| `coverage` | 0.979 |

| Family | CAA | CAA+ | NOS | POC | Coverage | Views |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `github_rest` | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 | 8 |
| `gitlab_rest` | 0.688 | 1.000 | 0.500 | 1.000 | 1.000 | 8 |
| `slack_auth` | 0.750 | 1.000 | 1.000 | 1.000 | 1.000 | 8 |
| `trello` | 0.625 | 0.750 | 0.750 | 0.750 | 1.000 | 8 |
| `youtube` | 0.938 | 1.000 | 0.750 | 1.000 | 0.875 | 8 |
| `youtube_channels` | 0.750 | 0.500 | 1.000 | 0.500 | 1.000 | 8 |

