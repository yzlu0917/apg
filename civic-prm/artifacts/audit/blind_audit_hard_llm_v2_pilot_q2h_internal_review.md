# Internal Blind Review: `blind_audit_hard_llm_v2_pilot_q2h`

Date: 2026-03-10

Scope:

- Reviewer packet only: `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h.md`
- No answer key, no summary, no history files, no code
- Two independent internal subagent reviewers

Limitation:

- This is still not the proposal's external human blind audit.
- `q2h` is a small `2 quartets/domain` pilot.

## Main Outcome

`q2h` improves algebra coverage relative to `q2f`, but it still does not clear the blind-audit bar and it does not replace `q2f` as the default blind-review packet.

- Exact reviewer agreement stays at `4/6`, the same as `q2f`.
- Algebra remains a hard failure mode.
- Graph/path is now mixed rather than universally high-signal.
- Blocksworld regresses slightly from the `q2f` blind-review profile.

## Reviewer Agreement

Exact agreement on `more_artificial`: `4/6`

Agreement profile:

- Algebra: `2/2` exact agreement, both items still clearly flagged as artificial
- Graph/path: `2/2` exact agreement, but only one item is clearly flagged and one is neutral
- Blocksworld: `0/2` exact agreement; both items are low-to-medium signal but reviewers still lean toward the more templated trace

## Item-Level Summary

| item_id | domain | reviewer_1 | reviewer_2 | interpretation |
|---|---|---|---|---|
| item-01 | algebra | Trace 2 | Trace 2 | vague bridge text and number drift still read like a patched algebra ending |
| item-02 | blocksworld | Neither | Trace 2 | low-signal overall, but one reviewer still sees a mechanical clear-and-rebuild template |
| item-03 | graph_path | Trace 2 | Trace 2 | one shifted route total still creates an obvious edited-trace smell |
| item-04 | algebra | Trace 1 | Trace 1 | intermediate numbers do not support the final conclusion, so the trace looks stitched |
| item-05 | blocksworld | Neither | Trace 2 | semantics are plausible, but one trace still feels more templated than naturally written |
| item-06 | graph_path | Neither | Neither | both traces are plain and formulaic, but neither stands out on smell alone |

## Operational Conclusion

- `q2h` is best understood as a coverage-recovery branch:
  - it raises rewritten traces from `64/72` (`q2f`) to `66/72`
  - it recovers algebra coverage from `16` to `18`
- That coverage gain does not translate into a stronger blind-audit-facing packet:
  - reviewer agreement does not improve beyond `q2f`
  - algebra remains the dominant bottleneck
  - blocksworld loses some of the low-signal behavior that `q2f` had reached
- `q2h` should therefore be recorded as a useful algebra-coverage fix, not as the new benchmark-v2 default.
