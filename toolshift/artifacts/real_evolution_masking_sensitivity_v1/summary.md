# Masking Sensitivity

- benchmark: `data/real_evolution_benchmark.json`
- methods: `semantic_embedding_capability_gate, semantic_clause_localization_capability_gate`
- masks: `unmasked, name_mask, description_mask, contract_mask`
- seeds: `0, 1`

## `semantic_embedding_capability_gate`

| Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `unmasked` | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 |
| `name_mask` | 0.986 | 1.000 | 0.909 | 1.000 | 0.986 | -0.014 | 0.000 | -0.091 | 0.000 |
| `description_mask` | 0.632 | 0.540 | 0.636 | 0.540 | 0.986 | -0.368 | -0.460 | -0.364 | -0.460 |
| `contract_mask` | 0.618 | 0.540 | 0.545 | 0.540 | 1.000 | -0.382 | -0.460 | -0.455 | -0.460 |

## `semantic_clause_localization_capability_gate`

| Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `unmasked` | 0.868 | 0.880 | 0.818 | 0.880 | 0.986 | 0.000 | 0.000 | 0.000 | 0.000 |
| `name_mask` | 0.861 | 0.880 | 0.773 | 0.880 | 0.986 | -0.007 | 0.000 | -0.045 | 0.000 |
| `description_mask` | 0.500 | 0.440 | 0.636 | 0.440 | 0.986 | -0.368 | -0.440 | -0.182 | -0.440 |
| `contract_mask` | 0.486 | 0.440 | 0.545 | 0.440 | 1.000 | -0.382 | -0.440 | -0.273 | -0.440 |

