# Masking Sensitivity

- benchmark: `data/real_evolution_benchmark.json`
- methods: `aug_only, teacher_distilled_bottleneck_scc`
- masks: `unmasked, name_mask, description_mask, contract_mask`
- seeds: `0, 1, 2`

## `aug_only`

| Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `unmasked` | 0.093 | 0.000 | 0.606 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `name_mask` | 0.097 | 0.000 | 0.636 | 0.000 | 1.000 | 0.005 | 0.000 | 0.030 | 0.000 |
| `description_mask` | 0.093 | 0.000 | 0.576 | 0.000 | 1.000 | 0.000 | 0.000 | -0.030 | 0.000 |
| `contract_mask` | 0.093 | 0.000 | 0.576 | 0.000 | 1.000 | 0.000 | 0.000 | -0.030 | 0.000 |

## `teacher_distilled_bottleneck_scc`

| Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `unmasked` | 0.102 | 0.000 | 0.636 | 0.000 | 0.995 | 0.000 | 0.000 | 0.000 | 0.000 |
| `name_mask` | 0.111 | 0.013 | 0.697 | 0.013 | 0.986 | 0.009 | 0.013 | 0.061 | 0.013 |
| `description_mask` | 0.102 | 0.000 | 0.606 | 0.000 | 1.000 | 0.000 | 0.000 | -0.030 | 0.000 |
| `contract_mask` | 0.102 | 0.000 | 0.606 | 0.000 | 1.000 | 0.000 | 0.000 | -0.030 | 0.000 |

