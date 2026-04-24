# Benchmark-V3 PairAdv Ensemble Smoke Internal Review

Dataset: `data/generated/craft_core_benchmark_v3_pairadv_ensemble_smoke.jsonl`

Packet: `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_blind.md`

Review policy:

- reviewer only sees masked blind packet
- no answer key
- task: identify which trace looks more artificially templated / hand-edited / patched, or choose `Neither`

## Reviewer A

- `item-01 | algebra-hard-0010`: `Trace 2`
  - reason: 前后数字承接有断裂，像局部改写后没有抹平
- `item-02 | blocksworld-hard-0008`: `Trace 2`
  - reason: 连接词和状态复述更像固定骨架填槽
- `item-03 | graph-hard-0007`: `Trace 2`
  - reason: 句式和记号像在母版上做过局部替换

Overall:

- not suitable as a promoted strict smoke sample
- stable surface asymmetry remains across all `3/3` items

## Reviewer B

- `item-01`: `Trace 2`
  - reason: patched feel and local rewrite asymmetry
- `item-02`: `Trace 1`
  - reason: overt discourse scaffolding (`First/Next/Then/...`)
- `item-03`: `Trace 2`
  - reason: mixed wording / notation and local splice feel

Overall:

- not blind-clean enough
- at least `2/3` items still show obvious style asymmetry or rewrite seams

## Summary

- exact agreement: `2/3`
- both reviewers reject the packet as a strict promoted sample
- outcome: `internal_negative`

Interpretation:

- the `api + local_qwen` ensemble reviewer can pass the current scalar strict gate
- but the resulting promoted families still fail blind-facing human-proxy review
- current bottleneck is no longer only generator quality; reviewer aggregation itself is too permissive
