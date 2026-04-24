# Boundary Evidence

- benchmark: `data/real_evolution_benchmark.json`
- methods: `semantic_embedding_capability_gate, semantic_clause_localization_capability_gate`
- seeds: `0, 1`

Counterfactual impossible shadows reuse each case's clean surface while swapping in the held-out negative admissible action.

## `semantic_embedding_capability_gate`

| Metric | Value |
| --- | ---: |
| `CAA` | 1.000 |
| `CAA+` | 1.000 |
| `NOS` | 1.000 |
| `POC` | 1.000 |
| `impossible_shadow_CAA` | 0.000 |
| `impossible_execute_rate` | 1.000 |
| `impossible_abstain_rate` | 0.000 |
| `impossible_ask_clarification_rate` | 0.000 |
| `visible_minus_impossible_gap` | 1.000 |

## `semantic_clause_localization_capability_gate`

| Metric | Value |
| --- | ---: |
| `CAA` | 0.861 |
| `CAA+` | 0.820 |
| `NOS` | 0.818 |
| `POC` | 0.820 |
| `impossible_shadow_CAA` | 0.136 |
| `impossible_execute_rate` | 0.864 |
| `impossible_abstain_rate` | 0.000 |
| `impossible_ask_clarification_rate` | 0.136 |
| `visible_minus_impossible_gap` | 0.682 |

