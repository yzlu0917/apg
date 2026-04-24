# Progress

Current goal:
Run a two-branch strategy:

- keep `structured_locality` as the clean anchor branch
- define `semantic_locality` as the weaker-program-dependence next branch.

## Milestones

DONE

- Read scoped instructions and source docs (`AGENTS.md`, `README.md`,
  `proposal.md`)
- Narrow the headline to the object claim
- Define fallback framing and four research gates
- Create the minimum project skeleton
- Start the Object gate with a reproducible seed and validator
- Establish the hybrid generation workflow and first frozen reviewed panel
- Reach a bootstrap-level Object gate `GO`

DOING

- Preserve `audit_final_v0` and `audit_final_v1` as the comparison anchors
- Keep `contrastive_locality`, `structured_locality`, and `semantic_locality` as separate ledgers
- Tighten `structured_locality` Audit controls before any final slice
- Define the first object-design target for `semantic_locality`

TODO

- Decide whether `abstain` is stage-1 or stage-2
- Decide whether the old mixed `contrastive_locality` branch should be paused
  as a weak branch now that the structured spin-out exists
- Decide the first minimal `semantic_locality` object family for `code`
- Decide whether `semantic_locality` needs a separate `plan` branch at all

BLOCKED

- Current final-slice evidence does not show a meaningful
  `gold_signal > matched_shuffle` separation after checker repair
- `contrastive_locality` generation still has low semantic acceptance despite
  improved schema validity
- the whole-family acceptance ledger is still dragged down by early weak
  free-generation batches even after the two structured sub-objects turned
  viable

## Latest updates

### 2026-04-01

- Designed a matching structured-code object in
  [contrastive_locality_structured_code.md](/cephfs/luyanzhen/apg/CAVE/docs/contrastive_locality_structured_code.md):
  structured checker JSON plus explicit nearby repair candidates.
- Extended
  [judge_contrastive_locality_candidates.py](/cephfs/luyanzhen/apg/CAVE/scripts/judge_contrastive_locality_candidates.py)
  so `judge_v4` can deterministically `auto_accept` exact
  `code_local_repair_v1` pairs without requiring an API call when execution
  already proves gold-only local-repair uniqueness.
- Added
  [build_structured_code_locality_pairs.py](/cephfs/luyanzhen/apg/CAVE/scripts/build_structured_code_locality_pairs.py)
  as a search-constructed code-side counterpart to the structured-plan builder.
- The first attempt to build `4` structured-code pairs only produced `3`,
  which exposed behaviorally equivalent wrong candidates in two earlier specs.
- Tightened the builder by replacing those brittle specs with exact count/sum
  variants whose nearby wrong repairs are behaviorally distinct.
- Ran `batch22_structured_code_search`; validator passed, `judge_v4`
  auto-accepted `3 / 3`, and human review also accepted `3 / 3`.
- Ran `batch23_structured_code_search`; validator passed, `judge_v4`
  auto-accepted `5 / 5`, and human review also accepted `5 / 5`.
- Froze
  [frozen_structured_code_subpanel_v0.jsonl](/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl)
  with `8` accepted structured-code pairs.
- The current family aggregate is now `19 accepted / 36 valid reviewed`
  pairs. This still does not make the whole family Object-bootstrap ready, but
  it does show that both structured sub-objects are now panel-viable.
- Split out a clean
  [structured_locality_branch.md](/cephfs/luyanzhen/apg/CAVE/docs/structured_locality_branch.md)
  branch so the exact structured sub-objects are no longer judged through the
  old mixed-family ledger.
- Froze
  [frozen_structured_locality_panel_v0.jsonl](/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl)
  by combining the structured-plan and structured-code reviewed subpanels.
- Defined fresh Object criteria in
  [structured_locality_object_gate.md](/cephfs/luyanzhen/apg/CAVE/docs/structured_locality_object_gate.md)
  and marked the new spin-out branch as `Object gate: GO`.
- The old `contrastive_locality` branch remains `Object bootstrap in progress`;
  this is a branch split, not a retroactive success rewrite.
- Froze a new Audit dev slice
  [audit_dev_v3.jsonl](/cephfs/luyanzhen/apg/CAVE/artifacts/audit/audit_dev_v3.jsonl)
  for the clean `structured_locality` branch, with same-domain matched shuffle
  controls and a zero-risk artifact report.
- Ran the first local empirical audit on `audit_dev_v3` with `Qwen3-8B`:
  `direct=0.875`, `procedure_retry=0.8125`, `gold_signal=1.000`,
  `matched_shuffle=0.750` checker pass.
- This is enough to open Audit empirical work on the new branch, but not enough
  to pass Audit, because the observed shuffle penalty is concentrated in the
  structured-plan half.

### 2026-03-31

- Converted the proposal into a claim hierarchy with explicit object, method,
  and deployment layers.
- Chose the default paper fallback: benchmark/protocol plus diagnostic study if
  the method story fails.
- Defined go / no-go criteria for Object, Audit, Conversion, and Scale gates.
- Built the first project skeleton with docs, seed data, validator, and logs.
- Started the Object gate with three paired intervention examples across
  `sym`, `code`, and `plan`.
- Added a hybrid bootstrap workflow: model generation, deterministic validation,
  and review queue construction.
- Verified a minimal API-assisted generation pass with one pair per domain and
  produced review artifacts for the next manual audit step.
- Tightened generation prompts after exploratory review failures.
- Built a frozen reviewed panel `v0.2` from post-tightening batches and marked
  the bootstrap Object gate as `GO`.
- Expanded the frozen panel to `v0.3`, adding enough `code` and `plan` pairs to
  support same-domain matched shuffles in every active domain.
- Upgraded Audit gate status from entry-ready to protocol baseline-ready.
- Implemented and ran the first API-based audit baseline on `audit_dev_v1`.
- Observed a real but small `gold_signal` vs `matched_shuffle` gap, with strong
  procedure effect still dominating the first pass.
- Improved shuffle matching, expanded to a harder `audit_dev_v2` slice, and
  increased the empirical `gold_signal` vs `matched_shuffle` separation.
- Added source-bank-aware shuffle control construction plus local-model support
  for candidate generation and audit baselines.
- Ran two local harder generation attempts and rejected them as held-out subset
  sources because the reviewed pairs did not preserve one shared intended
  answer plus a real local error.
- Replicated the `audit_dev_v2` audit on local `Qwen3-8B`; `gold_signal`
  stayed perfect while `matched_shuffle` checker pass dropped to `0.545`.
- Restored API generation, reviewed a held-out harder batch, and froze
  `audit_final_v0`.
- Ran the first API audit on the frozen final slice; the main new blocker is
  not sample coverage but brittle `plan` canonicalization, with `gold_signal`
  checker pass only `0.667`.
- Opened `audit_final_v1` with versioned `plan` checker metadata only.
- Re-ran the final API audit on `audit_final_v1`; the checker confound shrank,
  but `gold_signal` and `matched_shuffle` both landed at `0.833`, while
  `procedure_retry` reached `1.000`.
- Opened a new `contrastive_locality` family branch to test a genuinely
  different task geometry instead of continuing to patch the old family.
- Reviewed `batch11`; accepted 2 of 4 pairs, enough to show the family idea is
  not empty but not enough to freeze a new panel.
- Reviewed `batch12`; accepted 0 of 2 pairs because the code alternative was
  behaviorally equivalent to the gold fix and the plan case collapsed to a
  trivial sequential order.
- `batch13` exposed a generator defect: deletion-style revise cases could still
  emit empty `gold_repair_suffix`, so the generator was tightened to validate
  normalized records before writing output.
- Reviewed `batch14`; accepted 0 of 2 pairs because code tests undercovered the
  natural-language spec and the plan revise trace was actually valid under its
  own constraints.
- Reviewed `batch15`; accepted 0 of 2 pairs because the code checker target was
  internally inconsistent and the plan case again collapsed to a unique linear
  order.
- Current `contrastive_locality` aggregate is 2 accepted pairs out of 10 valid
  reviewed pairs, so the new family is still bootstrap-in-progress rather than
  a fresh Object-gate `GO`.
- Added `judge_contrastive_locality_candidates.py` plus
  [contrastive_locality_acceptance.md](/cephfs/luyanzhen/apg/CAVE/docs/contrastive_locality_acceptance.md)
  to move the branch from single-pass generation to
  generation -> deterministic validation -> blind model-judge -> human review.
- Ran `judge_v1` on 10 reviewed pairs and found it unusable: it accepted all 10
  because it was still too exposed to candidate framing.
- Tightened the judge into a blind pre-screen (`judge_v2`) and reran it on the
  same 10 pairs; it accepted 2 and rejected 8, correctly filtering the later
  obviously bad pairs while still disagreeing with human review on several
  earlier borderline cases.
- Upgraded the judge to execution-backed `v3` and refined it into `v3.1`:
  code pairs now run actual unit tests plus heuristic alternative probes, and
  simple plan-order pairs now run structured precedence checks before any model
  call.
- `judge_v3.1` currently acts like a high-precision veto tool: it accepts only
  `code_1501_0`, auto-rejects clear checker failures, and no longer misclassifies
  the batch12 plan case as a simple total-order artifact.
- Extended `judge_v3.2` with a minimal schedule semantics checker for
  duration/start-time prose. This recovers the batch11 schedule-style accepted
  plan pair while still rejecting the batch12 buffered schedule case with
  explicit makespan evidence.
- Upgraded the pre-screen to `judge_v4` by adding execution-backed code
  semantics: synthesized reference solutions from the task text, probe-input
  generation from written tests, and keep/revise/nearby-repair comparison on
  those probes.
- `judge_v4` now matches the current human review ledger on all 10 reviewed
  `contrastive_locality` pairs, including the key correction that
  `code_1501_0` should be rejected for code-side checker undercoverage rather
  than accepted as a good pair.
- Ran a new API batch `batch16_contrastive_locality` under the `judge_v4`
  workflow. Deterministic validation passed on 4 new pairs.
- Reviewed `batch16`; accepted `1 / 4`. The new acceptable pair is
  `code_1701_harder_0`, while both new plan pairs were rejected for the same
  old failure modes: false violations and collapsed geometry.
- This pushed the family aggregate to `3 accepted / 14 valid reviewed` pairs
  before the plan-only follow-up.
- Added a `contrastive_locality + plan` prompt override in
  `generate_object_gate_candidates.py` to suppress the most common plan-side
  failure modes without changing schema or acceptance rules.
- Ran a plan-only follow-up `batch17_contrastive_locality_plan`; validation
  passed on 3 pairs but review accepted `0 / 3`.
- The new override improved surface quality by avoiding obvious false revise
  claims, but the deeper blocker remains: plan checkers still under-specify the
  gold-only local repair geometry.
- The current family aggregate is now `3 accepted / 17 valid reviewed` pairs,
  so the branch remains far from a fresh Object bootstrap.
- Designed a new structured plan object in
  [contrastive_locality_structured_plan.md](/cephfs/luyanzhen/apg/CAVE/docs/contrastive_locality_structured_plan.md):
  structured checker JSON plus an exact one-adjacent-swap local repair budget.
- Extended `judge_contrastive_locality_candidates.py` to analyze this object
  deterministically as `structured_local_repair`.
- Ran `batch18_contrastive_locality_structured_plan`; validation passed, but
  all `3 / 3` pairs were rejected because the model still generated revise
  orders that were valid under the structured edges.
- Moved the same structured geometry into generator-side family validation.
- Ran `batch19_contrastive_locality_structured_plan`; generation failed before
  producing even the first pair because all 6 attempts violated the same
  semantic rule: revise order already satisfied the edges.
- Added a new search-based builder in
  [build_structured_plan_locality_pairs.py](/cephfs/luyanzhen/apg/CAVE/scripts/build_structured_plan_locality_pairs.py)
  so structured plan pairs no longer rely on free generation.
- Ran `batch20_structured_plan_search`; validator passed and `judge_v4`
  accepted `3 / 3`.
- Human review also accepted `3 / 3`, giving the first stable positive signal
  for the structured-plan sub-object.
- Upgraded the search builder to prefer more diverse keep orders, fail spans,
  and edge sets.
- Ran `batch21_structured_plan_search`; validator passed, `judge_v4` accepted
  `5 / 5`, and human review also accepted `5 / 5`.
- Froze
  [frozen_structured_plan_subpanel_v0.jsonl](/cephfs/luyanzhen/apg/CAVE/artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl)
  with `8` accepted structured-plan pairs.
- The current family aggregate is now `11 accepted / 28 valid reviewed`
  pairs. This still does not make the whole family Object-bootstrap ready, but
  it does show that the structured-plan search path is now panel-viable.

### 2026-04-07

- Wrote down a formal two-branch strategy in
  [two_branch_strategy.md](/cephfs/luyanzhen/apg/CAVE/docs/two_branch_strategy.md).
- Kept `structured_locality` explicitly positioned as the clean benchmark /
  audit anchor branch rather than the final deployment story.
- Opened a new design-only branch
  [semantic_locality_branch.md](/cephfs/luyanzhen/apg/CAVE/docs/semantic_locality_branch.md)
  for reduced-program-dependence local verifier objects.
- This new branch currently carries no inherited gate credit: no frozen panel,
  no Object `GO`, and no Audit claim yet.

## Resume point

Next session should use
`docs/two_branch_strategy.md` together with
`docs/semantic_locality_branch.md` to choose the first minimal
`semantic_locality` object proposal, while continuing to tighten
`structured_locality` matched-shuffle controls before opening any final slice.
