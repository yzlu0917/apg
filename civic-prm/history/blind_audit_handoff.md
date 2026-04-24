# Blind Audit Handoff

## Goal

Run an external human blind audit on the current benchmark-v3 packet without leaking labels and without reverting to the over-strict "semantic wrongness must be invisible" criterion.

## Send These Files To Reviewers

- packet: [blind_audit_benchmark_v3_midset.md](/cephfs/luyanzhen/apg/civic-prm/artifacts/audit/blind_audit_benchmark_v3_midset.md)
- response form: [blind_audit_benchmark_v3_midset_form.csv](/cephfs/luyanzhen/apg/civic-prm/artifacts/audit/blind_audit_benchmark_v3_midset_form.csv)

Do not send:

- [blind_audit_benchmark_v3_midset_key.json](/cephfs/luyanzhen/apg/civic-prm/artifacts/audit/blind_audit_benchmark_v3_midset_key.json)

## Reviewer Instruction

The reviewer question is:

- not "which trace is mathematically wrong?"
- but "which trace looks more artificially templated, hand-edited, or obviously synthetic?"

This distinction matters. Pure semantic wrongness visibility is not the benchmark failure criterion.

## Packet Facts

- packet summary: [blind_audit_benchmark_v3_midset_summary.json](/cephfs/luyanzhen/apg/civic-prm/artifacts/audit/blind_audit_benchmark_v3_midset_summary.json)
- items: `9`
- domain balance: algebra `3`, blocksworld `3`, graph_path `3`
- eligible quartets in the source benchmark: `18`

## Scoring Returned CSVs

Use:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/score_blind_audit.py \
  --answer-key artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --responses reviewer_a.csv reviewer_b.csv \
  --output artifacts/audit/blind_audit_benchmark_v3_midset_scored.json \
  --markdown-output artifacts/audit/blind_audit_benchmark_v3_midset_scored.md'
```

Outputs:

- machine-readable summary JSON
- markdown report with per-reviewer breakdown and pairwise agreement

## What To Read In The Scored Output

Primary read:

- `invalid_trace_flag_rate`
- `valid_trace_flag_rate`
- `invalid_minus_valid_flag_rate`
- `both_flag_rate`
- `neither_rate`

Secondary read:

- by-domain breakdown
- pairwise agreement between reviewers

## How To Interpret It

Use the proposal-aligned criterion:

- a failure is evidence that one side looks artificially edited or templated
- a non-failure does not require semantic wrongness to be invisible

Therefore:

- high invalid-vs-valid flag gap is suspicious
- high `Neither` rate is good
- `Both` can indicate packet-level awkwardness rather than invalid-only artifacting
- algebra may still show semantic visibility that should not be over-read as pure artifact failure

## Current Status

- packet exists
- hidden key exists
- scoring pipeline exists
- remaining blocker is external reviewer return
