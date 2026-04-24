# Internal Blind Review: `blind_audit_hard_llm_v2_pilot_q2f`

Date: 2026-03-10

Scope:

- Reviewer packet only: `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f.md`
- No answer key, no summary, no history files
- Two independent internal subagent reviewers

Limitation:

- This is still not the proposal's external human blind audit.
- `q2f` is a small `2 quartets/domain` pilot and now trades lower shallow style leakage for lower algebra coverage.

## Main Outcome

`q2f` is the current best blind-audit-facing surface-hardening point in the benchmark-v2 branch, but it still does not clear the blind-audit bar.

- Graph/path and blocksworld are now mostly low-signal under internal review.
- Algebra remains the dominant failure mode.
- The dominant algebra artifact has changed again: it is no longer mainly bare-equation shells or copied endings, but sentence-stitching / splice artifacts in stepwise rewrites.

## Reviewer Agreement

Exact agreement on `more_artificial`: `4/6`

Agreement profile:

- Algebra: `2/2` agreement, both items still strongly flagged as artificial
- Graph/path: `1/2` agreement; one item is still flagged, the other is now low-confidence / disputed
- Blocksworld: `1/2` agreement on `Neither`, `1/2` disputed at low-to-medium confidence

## Item-Level Summary

| item_id | domain | reviewer_1 | reviewer_2 | interpretation |
|---|---|---|---|---|
| item-01 | algebra | Trace 2 | Trace 2 | obvious sentence splice around the last step |
| item-02 | blocksworld | Neither | Neither | both traces look like ordinary constrained state-transition logs |
| item-03 | graph_path | Trace 2 | Neither | graph is now much lower-signal; one reviewer still leans toward the anomalous total |
| item-04 | algebra | Trace 1 | Trace 1 | duplicated / stitched algebra phrasing still looks synthetic |
| item-05 | blocksworld | Neither | Trace 2 | remaining signal is mostly repetitive sentence framing, not semantic patching |
| item-06 | graph_path | Trace 2 | Trace 2 | still mildly templated, but much weaker than the older graph packets |

## Operational Conclusion

- `q2f` materially improves the benchmark-v2 branch outside algebra:
  - graph/path no longer exposes the earlier arithmetic back-fill seam as strongly
  - blocksworld is mostly low-signal
- The remaining benchmark-v2 bottleneck is now concentrated in algebra.
- Further tightening the same rewrite/validation stack appears to push the branch onto a new frontier:
  - cleaner surface artifacts
  - but lower algebra coverage
- The next hardening step should therefore be algebra-specific, not another full-domain rewrite round.
