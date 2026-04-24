# Proxy Blind Audit: `benchmark-v3 midset`

Date: 2026-03-15

Scope:

- packet only: `artifacts/audit/blind_audit_benchmark_v3_midset.md`
- hidden key used only after review for scoring
- `3` independent model-based proxy reviewers

Limitation:

- this is not the proposal's external human blind audit
- treat it as an internal proxy blind-audit baseline

## Main Outcome

The proxy reviewers still find the packet easy to flag overall, but the failure shape is no longer uniform across domains.

- algebra is unanimously high-signal
- graph_path is still mostly high-signal, but now includes `Both` / `Neither` behavior rather than one-sided obvious patching
- blocksworld is mixed: proxy reviewers often disagree on which trace looks more artificial, and some flags fall on the valid trace

## Pooled Summary

- reviewers: `3`
- items per reviewer: `9`
- pooled invalid-trace flag rate: `0.7778`
- pooled valid-trace flag rate: `0.1111`
- pooled both rate: `0.0741`
- pooled neither rate: `0.037`
- invalid-minus-valid flag-rate gap: `0.6667`

## Domain Breakdown

- algebra:
  - invalid-trace flag rate: `1.0`
  - valid-trace flag rate: `0.0`
  - all `9/9` proxy judgments point to the invalid trace
- blocksworld:
  - invalid-trace flag rate: `0.6667`
  - valid-trace flag rate: `0.3333`
  - signal is partly about stylistic directness / clearing templates rather than invalid-only artifacting
- graph_path:
  - invalid-trace flag rate: `0.6667`
  - both rate: `0.2222`
  - neither rate: `0.1111`
  - the remaining signal looks more like rigid route-template detectability than copied-ending style corruption

## Agreement

- reviewer A vs B: `0.5556`
- reviewer A vs C: `0.5556`
- reviewer B vs C: `1.0`

This means two proxy reviewers converge on a nearly identical reading, while one is systematically more willing to blame the valid blocksworld trace for looking templated.

## Operational Read

- the packet does not yet look blind-clean to model-based proxy reviewers
- the strongest remaining problem is still algebra
- benchmark-v3 should continue to be described as accepted under the proposal-aligned artifact criterion, not as universally blind-clean
- the next decisive evidence must come from external human blind audit rather than more internal proxy review
