# Internal Blind Review: `blind_audit_hard_blindfix_v1`

Date: 2026-03-10

Scope:

- Reviewer packet only: `artifacts/audit/blind_audit_hard_blindfix_v1.md`
- No answer key, no summary, no results files
- Two independent internal subagent reviewers

Limitation:

- This is still not the proposal's external human blind audit.
- Treat it as an internal check on whether the blindfix branch removed the strongest synthetic-edit artifact.

## Main Outcome

The blindfix branch improved the packet, but did not clear the blind-audit bar.

- Compared with the earlier `blind_audit_hard_v2`, the strongest copied-ending artifact is largely reduced.
- Blocksworld now looks much more natural; reviewers no longer agree that its invalid traces are obviously synthetic.
- Algebra and graph/path remain easy to flag because they still rely on repeated single-step numeric corruption under an otherwise identical template.

## Reviewer Agreement

Exact agreement on `more_artificial`: `7/9`

Agreement profile:

- Algebra: `3/3` agreement, all still flagged as artificial
- Graph/path: `3/3` agreement, all still flagged as artificial
- Blocksworld: `1/3` agreement on `Neither`, `2/3` disputed at low confidence

## Item-Level Summary

| item_id | domain | reviewer_1 | reviewer_2 | interpretation |
|---|---|---|---|---|
| item-01 | algebra | Trace 2 | Trace 2 | still obvious single-step corruption |
| item-02 | blocksworld | Neither | Trace 1 | much weaker signal; not a clear synthetic tell |
| item-03 | graph_path | Trace 1 | Trace 1 | still obvious comparison-line corruption |
| item-04 | algebra | Trace 2 | Trace 2 | still obvious single-step corruption |
| item-05 | blocksworld | Neither | Neither | looks like two plausible plans |
| item-06 | graph_path | Trace 2 | Trace 2 | still obvious total/comparison corruption |
| item-07 | algebra | Trace 2 | Trace 2 | still obvious single-step corruption |
| item-08 | blocksworld | Neither | Trace 1 | disputed, but no longer a unanimous artifact |
| item-09 | graph_path | Trace 2 | Trace 2 | still obvious total corruption |

## Operational Conclusion

- `hard_blindfix_v1` is a real improvement over the first blind-audit packet.
- The improvement is domain-specific: blocksworld benefits strongly, while algebra and graph/path remain too templated.
- This branch should not yet replace the main benchmark or be sent to an external blind reviewer.
- The next hardening target is algebra/graph invalid-trace construction, especially repeated one-line numeric corruption under unchanged templates.
