# Benchmark-V3 Strict Smoke Internal Review

Date: 2026-03-10

Packet:

- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_blind.md`

Hidden key:

- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_blind_key.json`

Reviewer A:

- `item-01` algebra: `Trace 1` (`confidence = 3`)
  - note: more uniformly tutor-scripted and polished
- `item-02` blocksworld: `Trace 2` (`confidence = 4`)
  - note: repeated passive phrasing and rigid slot-filled pattern
- `item-03` graph_path: `Trace 1` (`confidence = 5`)
  - note: heavy sequence markers and overt scaffolding

Reviewer B:

- `item-01` algebra: `Trace 2` (`confidence = 5`)
  - note: numeric discontinuity and patched phrasing
- `item-02` blocksworld: `Trace 2` (`confidence = 4`)
  - note: more rigid slot-filled sentence pattern
- `item-03` graph_path: `Trace 1` (`confidence = 4`)
  - note: heavy sequence markers and polished compare-summary cadence

Against the hidden key:

- `item-01`
  - `Trace 1 = valid_correct`
  - `Trace 2 = invalid_correct`
- `item-02`
  - `Trace 1 = valid_correct`
  - `Trace 2 = invalid_correct`
- `item-03`
  - `Trace 1 = valid_correct`
  - `Trace 2 = invalid_correct`

Summary:

- exact reviewer agreement: `2/3`
- invalid trace picked by both reviewers: `1/3`
  - blocksworld
- valid trace picked by both reviewers: `1/3`
  - graph_path
- split decision: `1/3`
  - algebra

Interpretation:

- the strict smoke selector did not yet produce a blind-clean packet
- blocksworld invalidity is still too easy to spot
- graph/path can now fail the opposite way, where the valid trace looks more synthetic than the invalid trace
- the current selector therefore needs a stronger absolute-detectability gate, not only a penalty on invalid-trace picks
