# Execution Sanity

- Benchmark: `data/real_evolution_benchmark.json`
- count: `24`
- pass_rate: `1.000`
- execute_expected_pass_rate: `1.000`
- negative_guard_pass_rate: `1.000`
- positive_equivalence_rate: `1.000`

## By Transform

| Transform | Count | Pass | Execute | Satisfied |
| --- | ---: | ---: | ---: | ---: |
| `clean` | 12 | 1.000 | 1.000 | 1.000 |
| `negative_deprecate` | 1 | 1.000 | 0.000 | 0.000 |
| `negative_parent_scope_change` | 1 | 1.000 | 0.000 | 0.000 |
| `negative_removed_capability` | 1 | 1.000 | 0.000 | 0.000 |
| `negative_search_replacement` | 1 | 1.000 | 0.000 | 0.000 |
| `negative_source_removed` | 1 | 1.000 | 0.000 | 0.000 |
| `positive_version_migration` | 7 | 1.000 | 1.000 | 1.000 |
