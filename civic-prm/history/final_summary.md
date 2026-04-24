# Final Summary

## Project Status

The main experimental line in the proposal is now complete through Week 6, but only as a **conditional empirical package**. The project should not be treated as fully closed at the benchmark-validity level.

Completed:

- Week 1 benchmark bootstrap and artifact audit
- Week 2 strongest simple baselines and held-out verbalizer stress tests
- Week 3 minimal repair variants and mechanism analysis
- Week 4 stronger reranker evaluation for reranking / calibration / exploitability
- Week 5 robustness analysis with transfer, multi-attacker transfer, and worst-group slices
- Week 6 `3`-seed reproduction and paired bootstrap confidence intervals on the main comparison set

Still open:

- human blind audit review
- benchmark-validity closure
- a stronger benchmark redesign path beyond the current `benchmark-v2` hardening attempts
- final venue-specific manuscript polish

The manuscript itself is no longer missing:

- an anonymous NeurIPS-style LaTeX draft now exists under `paper/`
- it currently uses the latest official public NeurIPS style available at build time (`neurips_2025.sty`) as the submission base
- `paper/main.tex` compiles successfully to `paper/main.pdf`
- the remaining writing work is now polish and final result insertion, not first-pass drafting

## Benchmark Status

The benchmark story is now two-layered rather than simply unresolved.

- The original executable benchmark still underwrites the historical Week 1-6 package, and its external human blind audit is still pending.
- The `LLM-assisted benchmark v2` path remains informative but not strong enough to become the replacement benchmark.
- The `benchmark-v3` path is now usable at mid-scale under the proposal-aligned acceptance rule:
  - `52 / 54` accepted families
  - `208` exported records
  - balanced domain coverage `72 / 72 / 64`
- A benchmark-v3-specific reproduction pass now also supports the same read:
  - frozen-head quartet metrics stay strong across `3` seeds
  - the masked reranker keeps an `AMCD` edge and a clearly lower `ASS_total`
  - utility remains tied on the cleaner benchmark regime
- External human blind audit on the replacement benchmark is still pending, so benchmark-v3 should be described as a usable audited benchmark package rather than a fully closed replacement benchmark.

This means the strongest defensible read is:

- the main empirical conclusions are no longer tied only to the legacy benchmark
- but the benchmark package still has one open external validation gate

## Main Conclusion

The proposal is supported most strongly in its audit and disentangling framing, not in its strongest simple-repair headline.

The current evidence supports the following final reading:

1. answer-sensitive judging and trained verifier behavior must be separated empirically
2. `AMCD` is a much better proxy for downstream utility than ordinary AUROC
3. simple repair terms can move the faithfulness-utility frontier, but they do not dominate it on naturalized OOD
4. the best current deployment configuration is a stronger reranker in the masked condition, not a visible verifier and not the current frozen-head repair
5. the new benchmark-v3 regime behaves differently from the deployment-oriented full-hybrid regime and should be treated as a complementary process-faithfulness benchmark

These conclusions should be framed as conditional on the current benchmark package, not as benchmark-independent facts.

## Claim Hierarchy

### Supported

- `AMCD + ASS + same-backbone masked baseline` is a useful verifier audit protocol.
- Judge-style evaluators are strongly answer-sensitive.
- Local answer sensitivity harms local `AMCD`, and this damage propagates to selection utility and exploitability.
- A stronger model scale does not make answer-visible verification safe by default.
- On the current main slice, `Qwen3-Reranker-8B` in masked mode is the strongest deployment model.

### Supported With Narrow Scope

- Conditional invariance repair is empirically relevant.
  Evidence: `visible_cond_swap` improves faithfulness and sometimes `AMCD`, especially on harder structured OOD slices.
- The main remaining weak slice for the best model is planning-style naturalized blocksworld.
- Calibration remains weaker than ranking utility and should stay a secondary downstream result rather than a core mechanism claim.

### Not Supported Strongly Enough

- "Outcome leakage is the dominant shortcut for all trained verifiers."
- "A simple repair variant already dominates the answer-masked baseline everywhere."
- "The current dual-head disentangled design successfully separates process and consistency signals at this scale."
- "Calibration is solved."

These claims should not be used as paper headlines.

## Main Comparison Set

The final main-table comparison set should be:

- `Qwen3-Reranker-8B` masked
- `Qwen3-Reranker-8B` visible
- seed-averaged `visible_bce`
- seed-averaged `masked_bce`
- seed-averaged `pairwise_visible`
- seed-averaged `visible_cond_swap`

On the naturalized full-hybrid main slice:

- `reranker8_masked`: `ordinary_auroc = 0.6795`, `amcd = 0.8529`, `ass_total = 0.0184`, `selection_gain_at4 = 0.3824`, `exploitability_rate = 0.0588`
- `reranker8_visible`: `0.5398`, `0.5294`, `0.2128`, `0.3235`, `0.1765`
- `masked_bce`: `0.5969`, `0.7647`, `0.1041`, `0.2647`, `0.1765`
- `visible_bce`: `0.5926`, `0.7059`, `0.0941`, `0.2647`, `0.2353`
- `pairwise_visible`: `0.5753`, `0.7353`, `0.0848`, `0.2059`, `0.2941`
- `visible_cond_swap`: `0.5640`, `0.7059`, `0.0377`, `0.2059`, `0.2353`

The cleanest bootstrap comparison is `reranker8_masked` vs `reranker8_visible`:

- `ordinary_auroc` diff `+0.1397`, CI `[0.0644, 0.2608]`
- `amcd` diff `+0.3235`, CI `[0.1818, 0.4583]`
- `ass_total` diff `-0.1944`, CI `[-0.2485, -0.1355]`

## Recommended Paper Framing

The strongest current framing is:

> Outcome-sensitive behavior is severe in judge-style process evaluation, and verifier deployment should be audited with `AMCD`, answer-swap sensitivity, and same-backbone masked baselines. On audited executable domains and naturalized OOD transfer, a stronger reranker works best when answer access is removed.

This is stronger and more defensible than a pure "repair solves leakage" framing.

The paper should also state clearly that benchmark replacement is only partially closed:

> We can now audit verifier behavior on both the original executable benchmark and a benchmark-v3 mid-scale replacement accepted under a proposal-aligned artifact criterion, but external human blind audit on the replacement benchmark is still pending.

## Recommended Main Figures / Tables

Main table:

- naturalized full-hybrid comparison set
- columns:
  - ordinary AUROC
  - AMCD
  - ASS_total
  - selection gain @ 4
  - exploitability rate

Main figure:

- mechanism figure for `ASS -> AMCD -> utility`

Main robustness table:

- Week 5 transfer summary
- mixed-attacker transfer
- worst-group slices by domain

Appendix:

- calibration
- seed table
- bootstrap intervals
- verbalizer-family table
- dual-head negative results

## Remaining Non-Experimental Work

- get a human reviewer to complete the blind audit packet
- do final venue-specific prose, figure, and bibliography polish on top of the existing LaTeX draft in `paper/`
- decide whether the next benchmark phase should scale benchmark-v3 beyond the current mid-scale package as a follow-on project
- cut optional details that are now clearly appendix material:
  - calibration layer story
  - dual-head implementation details
  - extra replay variants
