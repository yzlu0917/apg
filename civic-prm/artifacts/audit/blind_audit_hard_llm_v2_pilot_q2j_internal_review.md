# Internal Blind Review: `blind_audit_hard_llm_v2_pilot_q2j`

Date: 2026-03-10

Scope:

- Reviewer packet only: `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j.md`
- No answer key, no summary, no history files, no code
- Two independent internal subagent reviewers

Limitation:

- This is still not the proposal's external human blind audit.
- `q2j` is a small `2 quartets/domain` pilot.

## Main Outcome

`q2j` is a strong coverage-recovery result but a bad blind-audit result.

- Coverage rises to `72/72`, including algebra `24/24`.
- Exact reviewer agreement rises to `6/6`, which is worse, not better.
- The packet fails because the preserved invalid arithmetic is now too easy for humans to spot.

## Reviewer Agreement

Exact agreement on `more_artificial`: `6/6`

Agreement profile:

- Algebra: `2/2` exact agreement, both invalid traces still clearly flagged
- Graph/path: `2/2` exact agreement, both invalid traces are now easy to spot from wrong route totals
- Blocksworld: `2/2` exact agreement on `Neither`

## Item-Level Summary

| item_id | domain | reviewer_1 | reviewer_2 | interpretation |
|---|---|---|---|---|
| item-01 | algebra | Trace 2 | Trace 2 | the wrong `15 -> 4 -> 1` progression is visibly inconsistent |
| item-02 | blocksworld | Neither | Neither | both traces read like ordinary constrained move logs |
| item-03 | graph_path | Trace 1 | Trace 1 | the wrong `17` total is easy to detect from the edge list |
| item-04 | algebra | Trace 2 | Trace 2 | the wrong `-24 -> -3 -> -6` chain is also visibly inconsistent |
| item-05 | blocksworld | Neither | Neither | low-signal for both reviewers |
| item-06 | graph_path | Trace 2 | Trace 2 | the wrong final route total is easy to check from the problem statement |

## Operational Conclusion

- `q2j` succeeds on the rewrite-robustness objective:
  - it restores full coverage
  - it keeps algebra invalid traces faithful to the intended local corruption
- `q2j` fails on the blind-audit objective:
  - by preserving the wrong arithmetic exactly, it makes the invalid traces human-checkable and therefore easy to flag
- Operationally, `q2j` is not the new benchmark-v2 default.
- `q2f` remains the current best blind-audit-facing packet even though its coverage is lower.
