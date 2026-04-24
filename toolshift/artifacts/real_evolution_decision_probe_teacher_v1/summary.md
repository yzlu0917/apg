# Decision-State Probe

- benchmark: `data/real_evolution_benchmark.json`
- methods: `aug_only, teacher_distilled_bottleneck_scc`
- seeds: `0, 1, 2`

## `aug_only`

| Metric | Value |
| --- | ---: |
| `CAA` | 0.093 |
| `CAA+` | 0.000 |
| `NOS` | 0.606 |
| `POC` | 0.000 |
| `probe_accuracy` | 0.611 |
| `probe_negative_recall` | 0.278 |
| `positive_state_similarity` | 0.944 |
| `negative_state_similarity` | 0.906 |
| `state_separation_gap` | 0.038 |

## `teacher_distilled_bottleneck_scc`

| Metric | Value |
| --- | ---: |
| `CAA` | 0.102 |
| `CAA+` | 0.000 |
| `NOS` | 0.636 |
| `POC` | 0.000 |
| `probe_accuracy` | 0.602 |
| `probe_negative_recall` | 0.333 |
| `positive_state_similarity` | 0.882 |
| `negative_state_similarity` | 0.858 |
| `state_separation_gap` | 0.024 |

