# Request Replay Sanity

- Benchmark: `data/real_evolution_benchmark.json`
- count: `40`
- pass_rate: `1.000`
- execute_render_pass_rate: `1.000`
- negative_block_pass_rate: `1.000`
- positive_equivalence_rate: `1.000`

## By Transform

| Transform | Count | Pass | Emit |
| --- | ---: | ---: | ---: |
| `clean` | 20 | 1.000 | 1.000 |
| `negative_deprecate` | 1 | 1.000 | 0.000 |
| `negative_legacy_identifier_removed` | 1 | 1.000 | 0.000 |
| `negative_parent_scope_change` | 1 | 1.000 | 0.000 |
| `negative_removed_capability` | 1 | 1.000 | 0.000 |
| `negative_search_replacement` | 1 | 1.000 | 0.000 |
| `negative_shortcut_replacement` | 1 | 1.000 | 0.000 |
| `negative_source_removed` | 1 | 1.000 | 0.000 |
| `positive_version_migration` | 13 | 1.000 | 1.000 |
