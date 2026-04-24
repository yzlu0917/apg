# Submission Checklist

## Locked

- main experimental line through Week 6
- mechanism result: `ASS -> AMCD -> utility`
- deployment headline: masked `Qwen3-Reranker-8B` is strongest on the main naturalized full-hybrid slice
- benchmark-v3 default benchmark replacement at mid-scale under proposal-aligned acceptance
- benchmark-v3 mainline runs:
  - artifact audit
  - blind packet generation
  - Week 2 baselines
  - Week 4 reranker
  - same-dataset robustness
- blind-audit scoring pipeline

## Writing State

- main prose draft: [paper_draft.md](/cephfs/luyanzhen/apg/civic-prm/history/paper_draft.md)
- outline: [paper_outline.md](/cephfs/luyanzhen/apg/civic-prm/history/paper_outline.md)
- claim hierarchy: [final_summary.md](/cephfs/luyanzhen/apg/civic-prm/history/final_summary.md)
- main table spec: [main_table.md](/cephfs/luyanzhen/apg/civic-prm/history/main_table.md)

## Still External

- external human blind audit on benchmark-v3
- venue-specific formatting / bibliography / figure production

## Do Not Reopen Without Strong Reason

- universal strict pair indistinguishability as the benchmark pass criterion
- masked-vs-visible deployment conclusion on the naturalized full-hybrid main slice
- Week 3 interpretation as mechanism success rather than simple-method victory

## If Resuming Work

1. collect external reviewer CSVs
2. score them with [score_blind_audit.py](/cephfs/luyanzhen/apg/civic-prm/scripts/score_blind_audit.py)
3. insert final blind-audit result into [paper_draft.md](/cephfs/luyanzhen/apg/civic-prm/history/paper_draft.md)
4. polish prose for target venue
