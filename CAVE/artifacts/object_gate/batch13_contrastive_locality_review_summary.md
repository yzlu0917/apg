# Batch 13 Contrastive Locality Review Summary

Date: 2026-03-31

Source:

- `artifacts/object_gate/batch13_contrastive_locality_code_candidates.jsonl`

## Outcome

- reviewed pairs: `0`
- accepted pairs: `0`
- rejected pairs: `0`
- invalid pairs before review: `1`

Invalid pair:

- `code_contrastive_locality_0`
  - the revise example leaves `gold_repair_suffix` empty even though the notes
    describe a deletion-style local repair
  - this is a generator-side validity failure, not a family acceptance failure

Decision:

`Do not count this batch toward family review statistics.`

Interpretation:

- the example idea is directionally closer to the intended family than batch12
- but the pipeline was still allowing invalid revise records through
- after this batch, `generate_object_gate_candidates.py` was tightened to
  validate normalized records before writing output and to require non-empty
  continuations for deletion-style repairs
