# BFCL Bridge Audit

This file records the source anchors and deterministic import policy for the ToolShift BFCL bridge benchmark.

## Source Benchmark

- Benchmark: BFCL v4
- Raw root: `https://raw.githubusercontent.com/ShishirPatil/gorilla/main/berkeley-function-call-leaderboard/bfcl_eval/data`
- Source repository: `https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard`

## Import Policy

- Categories imported: `simple_python`, `multiple`, `live_simple`, `irrelevance`, `live_irrelevance`
- Per-category sampling: first scalar-compatible cases in source order
- Scalar-compatible means every visible top-level parameter is one of `string/integer/float/boolean`
- Execute categories keep BFCL possible answers as set-valued admissible actions
- Irrelevance categories map to `abstain`-only admissible actions

## Selected Counts

- `simple_python`: 10
- `multiple`: 10
- `live_simple`: 10
- `irrelevance`: 10
- `live_irrelevance`: 10
