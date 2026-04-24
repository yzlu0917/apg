# Internal Blind Review: `blind_audit_hard_llm_v2_pilot_q2d`

Date: 2026-03-10

Scope:

- Reviewer packet only: `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d.md`
- No answer key, no summary, no history files
- Two independent internal subagent reviewers

Limitation:

- This is still not the proposal's external human blind audit.
- The packet is only a `2 quartets/domain` pilot and one algebra verbalizer family is incomplete in the underlying dataset.

## Main Outcome

`q2d` fixes the stepwise-rewrite truncation bug and materially improves artifact audit, but it still does not clear the substantive blind-audit bar.

- No one-step traces remain in the packet.
- Reviewers agreed on all `6/6` items.
- Algebra and graph/path remain easy to flag because they still expose local patched seams.
- Blocksworld is now mixed rather than uniformly suspicious: one item is neutral, one item is still flagged because of overt discourse-marker scaffolding.

## Reviewer Agreement

Exact agreement on `more_artificial`: `6/6`

Agreement profile:

- Algebra: `2/2` agreement, both items flagged as artificial
- Graph/path: `2/2` agreement, both items flagged as artificial
- Blocksworld: `1/2` agreement on `Neither`, `1/2` agreement on `Trace 1`

## Item-Level Summary

| item_id | domain | reviewer_1 | reviewer_2 | interpretation |
|---|---|---|---|---|
| item-01 | algebra | Trace 2 | Trace 2 | bare equation chain still looks patched after local value drift |
| item-02 | blocksworld | Neither | Neither | both traces look plausible and neither exposes a clear edit seam |
| item-03 | graph_path | Trace 1 | Trace 1 | templated route scaffold plus anomalous total still looks synthetic |
| item-04 | algebra | Trace 1 | Trace 1 | compressed shell with inconsistent values remains easy to flag |
| item-05 | blocksworld | Trace 1 | Trace 1 | overt `First/Next/Then/Now/Finally` scaffolding reads more canned than Trace 2 |
| item-06 | graph_path | Trace 2 | Trace 2 | one route total still creates a visible patched seam |

## Operational Conclusion

- `q2d` is a valid replacement for the broken `q2c` run.
- It improves the shallow style signal substantially relative to `q2b`, but human-style review still catches patched algebra/graph invalid traces.
- The next benchmark-v2 hardening target is narrower now:
  - algebra invalid traces need less “clean shell + local numeric drift”
  - graph/path invalid traces need less “one anomalous total inside a rigid route template”
  - blocksworld mainly needs lighter discourse scaffolding, not semantic reconstruction
