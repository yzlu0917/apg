# Results

## 2026-03-31 Phase 0 Bootstrap

Question:
- Can the project be turned into a clean claim-bearing research workspace before any large experiment starts?

Actions:
- Read the project instructions and proposal.
- Extracted the claim hierarchy, fallback framing, and gate sequence.
- Created the minimal Object-gate protocol, frozen pilot config, and bootstrap script.
- Ran `conda run -n infer python scripts/bootstrap_object_gate.py`.
- Installed `reasoning-gym==0.1.25` into `infer`.
- Froze the first family split and prompt protocol for Object gate.
- Ran `python scripts/generate_object_gate_manifests.py` inside `infer`.
- Sample-checked the generated prompt rows.
- Added `scripts/collect_object_gate_traces.py` for manifest-driven live sampling.
- Tried `vllm` first and found a `flash_attn` load failure caused by missing `GLIBC_2.32`.
- Added a `transformers` fallback plus assistant-prefill control for Qwen3.
- Regenerated manifests under the `v2_prefill_reasoning` protocol.
- Added `scripts/collect_api_calibration_traces.py` for tiny API calibration batches.
- Added `project/intervention_schema.md` and `scripts/build_intervention_templates.py`.

Environment checks:
- Default Python:
  - `reasoning_gym`: missing
  - `datasets`: present
  - `transformers`: missing
- `infer` environment:
  - `reasoning_gym`: present
  - `transformers`: present
  - `vllm`: present
  - `vllm` runtime status: blocked by local `flash_attn` binary compatibility

Artifacts created:
- `project/phase0_bootstrap.md`
- `project/object_gate.md`
- `project/prompt_protocol.md`
- `configs/object_gate.json`
- `scripts/bootstrap_object_gate.py`
- `scripts/generate_object_gate_manifests.py`
- `scripts/collect_object_gate_traces.py`
- `progress.md`
- `artifacts/object_gate/run_state.json`
- `artifacts/object_gate/manifest.template.json`
- `artifacts/object_gate/samples/dev_manifest.jsonl`
- `artifacts/object_gate/samples/final_manifest.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_000.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_001.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_002.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_003.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_004.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_005.jsonl`
- `artifacts/object_gate/rollouts/dev_trace_smoke_006.jsonl`

Manifest summary:
- Dev manifest size: 48 prompts
- Final manifest size: 96 prompts
- High-dependency families: `tower_of_hanoi`, `countdown`
- Shallow families: `basic_arithmetic`, `gcd`
- Prompt protocol: procedural task instance plus thin wrapper with `<reasoning>` and `<final>` tags, stabilized by assistant prefill

Smoke-trace summary:
- `dev_trace_smoke_000`: native Qwen thinking caused runaway `<think>` output; no usable tags.
- `dev_trace_smoke_001`: disabling native thinking gave direct final answer but no reasoning tags.
- `dev_trace_smoke_003`: assistant prefill recovered a shallow sample with verifier score `1.0`.
- `dev_trace_smoke_005`: high-dependency sample achieved `format_ok=1`, proving the interface can close both tags.
- `dev_trace_smoke_006`: regenerated manifest plus assistant prefill achieved `format_ok=1` and score `1.0` on a shallow sample.
- `dev_mixed_smoke_batch_000`: 4-prompt mixed batch achieved `format_ok=4/4`; `tower_of_hanoi` was `0/2` on verifier score, `basic_arithmetic` was `1/2`.

API calibration summary:
- Probe request to the provided endpoint succeeded with a minimal tagged response.
- `api_highdep_calibration_000`: first 2-prompt high-dependency batch got `format_ok=1/2`, `nonzero_score_count=1`, `total_tokens=1560`.
- `api_highdep_calibration_001`: after enforcing very short reasoning, the same 2-prompt high-dependency batch got `format_ok=2/2`, `nonzero_score_count=1`, `total_tokens=1120`.
- Completion-token usage dropped from `986` to `498` between the two API calibration runs.

Intervention-schema summary:
- `draft_candidates_v0.jsonl` contains 9 drafted candidate steps.
- `ready`: 7
- `review_needed`: 2
- By source:
  - API `tower_of_hanoi`: 4 ready
  - local `basic_arithmetic`: 3 ready
  - local `tower_of_hanoi`: 2 review-needed

Interpretation:
- The readiness heuristic is doing the intended job.
- API-calibrated high-dependency traces are clean enough for first-pass interventions.
- Local high-dependency traces are still unsuitable for the first clean intervention loop.

Generated-candidate summary:
- `generated_candidates_v0.jsonl` contains paraphrase and distractor candidates for all 7 ready steps.
- Family mix:
  - `tower_of_hanoi`: 4
  - `basic_arithmetic`: 3
- Generation token use: `1881`

Quality note:
- Paraphrases are generally strong enough for a first micro-batch.
- Some distractors are weak rather than ideal negatives, especially when they remain close to a valid planning style.
- This is acceptable for the first small intervention pass, but those distractors should be reviewed or re-generated before any larger sweep.

Packaged micro-batch summary:
- `micro_batch_v0.jsonl` contains 21 rollout-ready intervention records.
- Breakdown:
  - `delete`: 7
  - `paraphrase`: 7
  - `distractor`: 7
- `needs_review=true` is assigned to all distractor variants by default.
- Family mix:
  - `tower_of_hanoi`: 12
  - `basic_arithmetic`: 9

Interpretation:
- The project now has a concrete first intervention batch rather than only schema and candidate placeholders.
- The next execution step is continuation rollout, not more format debugging.

Intervention rollout smoke summary:
- `intervention_rollout_smoke_000.jsonl` contains 6 rollout results:
  - 3 variants for one API high-dependency source
  - 3 variants for one local shallow source
- All 6 variants returned a final answer.
- All 6 variants received non-zero verifier scores.

Observed outcome:
- High-dependency source:
  - `delete = 0.7143`
  - `paraphrase = 0.7143`
  - `distractor = 0.7143`
- Shallow source:
  - `delete = 1.0`
  - `paraphrase = 1.0`
  - `distractor = 1.0`

Interpretation:
- The rollout pipeline itself works end-to-end.
- But the current rollout definition is too weak as a causal test, because it conditions on the full modified reasoning draft before asking for the final answer.
- Under this setup, variant effects are washed out; delete/paraphrase/distractor do not separate at all.
- This is a protocol issue, not an execution failure.

Prefix-based rollout smoke summary:
- `intervention_prefix_rollout_smoke_000.jsonl` reran the same 6 variants, but only provided a reasoning prefix up to the intervention point.
- Results:
  - high-dependency `tower_of_hanoi`
    - `delete = 0.0`
    - `paraphrase = 1.0`
    - `distractor = 0.7143`
  - shallow `basic_arithmetic`
    - `delete = 0.0166`
    - `paraphrase = 0.1515`
    - `distractor = 0.0`

Interpretation:
- Prefix-based continuation is the first rollout definition that produces separation.
- The direction is sensible: paraphrase is best, distractor is worse, delete is worst or near-worst.
- This is still a tiny smoke batch, not a claim-level result, but it is enough to justify expanding the Object-gate micro-batch.

Expanded prefix-based batch summary:
- `intervention_prefix_rollout_batch_000.jsonl` covers the full current ready-only batch:
  - 21 variants
  - 7 source groups
  - 21/21 final answers present
  - 13/21 non-zero verifier scores
- Family coverage:
  - `tower_of_hanoi`: 12 variants
  - `basic_arithmetic`: 9 variants

Corrected source-level ordering after fixing intervention-id collisions:
- Weak ordering `paraphrase >= distractor >= delete` with `paraphrase > delete`: `2/7` source groups
- Strict ordering `paraphrase > distractor > delete`: `0/7`

Observed patterns:
- High-dependency early planning steps can show useful contrast:
  - one source gave `delete = 0.0`, `paraphrase = 1.0`, `distractor = 1.0`
  - another gave `delete = 0.0`, `paraphrase = 0.7143`, `distractor = 0.7143`
- High-dependency late check-style steps often saturate:
  - one source gave all three variants `0.7143`
  - another source gave all three variants `0.0`
- Shallow arithmetic sources show partial contrast:
  - `delete` low partial credit
  - `paraphrase` higher partial credit
  - `distractor` zero
  - but these do not satisfy strict ordering because distractor drops below delete rather than landing between paraphrase and delete

Interpretation:
- The object signal is real enough to keep going, but not yet stable enough for a clean Object-gate pass.
- Step choice matters: early planning steps are more diagnostic than late verification/check lines.
- Distractor quality still needs work. Some distractors collapse performance to zero, while others remain too strong.
- The next improvement should be qualitative, not just more scale: better step selection and stronger matched distractors.

Refined second-pass batch summary:
- `scripts/refine_intervention_candidates.py` was upgraded to a validated regeneration loop:
  - the API must return `distractor` plus `error_mode`
  - arithmetic distractors are rejected if they collapse to algebraically equivalent rewrites such as `add -N` versus `subtract N`
  - Tower-of-Hanoi distractors are rejected unless they contain a concrete wrong commitment such as moving the largest disk too early
- New artifacts:
  - `artifacts/object_gate/interventions/generated_candidates_v1.jsonl`
  - `artifacts/object_gate/interventions/micro_batch_v1.jsonl`
  - `artifacts/object_gate/analysis/intervention_prefix_rollout_batch_v1_000.jsonl`
  - `scripts/analyze_intervention_rollout.py`
- `intervention_prefix_rollout_batch_v1_000.jsonl` covers the refined second-pass batch:
  - 12 variants
  - 4 source groups
  - 12/12 final answers present
  - 8/12 non-zero verifier scores
- Source-level ordering:
  - weak ordering `paraphrase >= distractor >= delete` with `paraphrase > delete`: `3/4`
  - strict ordering `paraphrase > distractor > delete`: `0/4`

Matched-group comparison versus the corresponding v0 groups:
- `tower_of_hanoi` / `dev-high_dependency-tower_of_hanoi-001`:
  - v0: `delete = 0.0`, `paraphrase = 1.0`, `distractor = 1.0`
  - v1: `delete = 0.0`, `paraphrase = 1.0`, `distractor = 0.0`
  - Effect: the paraphrase-vs-distractor gap improved by `+1.0`
- `tower_of_hanoi` / `dev-high_dependency-tower_of_hanoi-000`:
  - unchanged at `delete = 0.0`, `paraphrase = 0.7143`, `distractor = 0.7143`
- `basic_arithmetic` / `dev-shallow-basic_arithmetic-001`:
  - unchanged at `delete = 0.0230`, `paraphrase = 0.0606`, `distractor = 0.0`
- `basic_arithmetic` / `dev-shallow-basic_arithmetic-000`:
  - v0: `delete = 0.0166`, `paraphrase = 0.1515`, `distractor = 0.0`
  - v1: `delete = 0.0166`, `paraphrase = 0.1515`, `distractor = 0.1515`
  - Effect: the distractor became too weak and tied the paraphrase

Interpretation:
- The second-pass refinement improved the cleaner batch overall: weak ordering rose to `3/4` source groups on the selected slice.
- The gain is concentrated in high-dependency early-planning sources, where stronger distractors can now cleanly separate from paraphrases.
- Shallow arithmetic remains unstable under local `Qwen3-1.7B` continuation: one distractor still collapses to the same score as the paraphrase, which suggests model insensitivity rather than prompt-format failure.
- This is still not enough for an Object-gate pass because strict ordering is absent and the current refined slice keeps only first/only steps, so raw-progress and position proxies are degenerate on this batch.
- The next comparison should therefore be a tiny proxy-control batch with paired early/late or otherwise varied-progress steps, not another blind scale-up.

Paired-step proxy-control summary:
- `scripts/refine_intervention_candidates.py` was parameterized so the same validated generator can select different step roles and family subsets.
- New control artifacts:
  - `artifacts/object_gate/interventions/generated_candidates_proxy_v0.jsonl`
  - `artifacts/object_gate/interventions/micro_batch_proxy_v0.jsonl`
  - `artifacts/object_gate/analysis/intervention_prefix_rollout_proxy_v0_000.jsonl`
- The control batch uses only API-backed `tower_of_hanoi` traces and pairs first-step planning with last-step legality checks from the same source prompts.
- `intervention_prefix_rollout_proxy_v0_000.jsonl` covers:
  - 12 variants
  - 4 source groups
  - 12/12 final answers present
  - 6/12 non-zero verifier scores
- Ordering on the paired-step control slice:
  - weak ordering `paraphrase >= distractor >= delete` with `paraphrase > delete`: `2/4`
  - strict ordering `paraphrase > distractor > delete`: `0/4`

Within-prompt early-versus-late contrast:
- `dev-high_dependency-tower_of_hanoi-000`
  - first step: `delete = 0.0`, `paraphrase = 0.7143`, `distractor = 0.7143`
  - last step: `delete = 0.7143`, `paraphrase = 0.7143`, `distractor = 0.7143`
- `dev-high_dependency-tower_of_hanoi-001`
  - first step: `delete = 0.0`, `paraphrase = 1.0`, `distractor = 0.0`
  - last step: `delete = 0.0`, `paraphrase = 0.0`, `distractor = 0.0`

Interpretation:
- The proxy-control slice resolves the main ambiguity from the cleaner first-step batch: the current signal is not “generic step credit.”
- On the same high-dependency prompts, early planning steps can carry non-trivial matched-counterfactual signal, while late legality-check steps either saturate at one shared score or collapse entirely.
- This means a raw-progress story does not rescue the current object: later steps are not consistently higher-credit just because they are later.
- The supported headline is therefore narrower than the original broad phrasing. Right now the evidence supports an early-planning object on high-dependency tasks, not a universal step-credit claim across all reasoning lines.

Second-family check: `countdown`
- Added a tiny dedicated manifest slice:
  - `artifacts/object_gate/samples/dev_countdown_manifest.jsonl`
- API calibration:
  - `api_countdown_calibration_000.jsonl`: `2 prompts`, `format_ok = 1/2`, `nonzero_score_count = 1`
  - `api_countdown_calibration_001.jsonl`: `4 prompts`, `format_ok = 2/4`, `nonzero_score_count = 2`
- The usable `countdown` traces were both correct and long enough to segment, yielding:
  - `artifacts/object_gate/interventions/draft_candidates_countdown_v0.jsonl`
  - `artifacts/object_gate/interventions/generated_candidates_countdown_v1.jsonl`
  - `artifacts/object_gate/interventions/micro_batch_countdown_v1.jsonl`
  - `artifacts/object_gate/analysis/intervention_prefix_rollout_countdown_v1_000.jsonl`

`countdown` rollout summary:
- `12 variants`
- `4 source groups`
- `12/12 final answers present`
- `12/12 non-zero verifier scores`
- weak ordering `paraphrase >= distractor >= delete` with `paraphrase > delete`: `0/4`
- strict ordering `paraphrase > distractor > delete`: `0/4`

Group-level outcomes:
- `dev-high_dependency-countdown-001`, first step:
  - `delete = 1.0`, `paraphrase = 1.0`, `distractor = 1.0`
- `dev-high_dependency-countdown-001`, last step:
  - `delete = 1.0`, `paraphrase = 1.0`, `distractor = 1.0`
- `dev-high_dependency-countdown-003`, first step:
  - `delete = 1.0`, `paraphrase = 1.0`, `distractor = 0.01`
- `dev-high_dependency-countdown-003`, last step:
  - `delete = 1.0`, `paraphrase = 1.0`, `distractor = 1.0`

Interpretation:
- `countdown` does not replicate the current `tower_of_hanoi` object behavior under the same rollout definition.
- In this family, the model usually recovers a correct expression even after deleting or replacing the selected step, which suggests the task admits many alternative valid continuations under the current budget.
- The one low distractor score (`0.01`) came from a distractor continuation that ran long and failed to finish cleanly, so it is not strong positive evidence for the object.
- The immediate headline therefore should be narrowed again: the supported signal is not “high-dependency early-planning credit” in general, but a family-selective early-planning signal that is currently strongest on structured planning tasks like `tower_of_hanoi`.

Exploratory structured-family check: `quantum_lock`
- Built a tiny exploratory slice:
  - `artifacts/object_gate/samples/dev_quantum_lock_manifest.jsonl`
- Calibration run:
  - `artifacts/object_gate/rollouts/api_quantum_lock_calibration_000.jsonl`
  - `4 prompts`
  - `format_ok = 0/4`
  - `nonzero_score_count = 0`
- Failure pattern:
  - all 4 completions opened `<reasoning>` and then consumed the full completion budget without closing tags
  - the model treated the task as long search/simulation rather than a short tagged plan

Interpretation:
- `quantum_lock` is structurally promising as a planning family, but under the current wrapper it fails before the intervention stage.
- This matters for governance: there is no evidence right now that a simple wrapper tweak will rescue a broader structured-family story.
- Combined with the `countdown` negative replication, this is enough to stop broadening the Object headline in the current branch.
- The supported story should now be frozen as family-selective diagnosis plus protocol, not a generic object spanning mixed high-dependency families.

Family-specific rescue attempt: `quantum_lock_shortplan`
- Updated `scripts/collect_api_calibration_traces.py` with a `protocol_mode` option.
- Added a dedicated `quantum_lock_shortplan` mode that:
  - forbids long sequence simulation inside `<reasoning>`
  - asks for at most 2 short reasoning lines
  - pushes the model to emit the final button sequence directly
- Rerun:
  - `artifacts/object_gate/rollouts/api_quantum_lock_calibration_001.jsonl`
  - `4 prompts`
  - `format_ok = 1/4`
  - `nonzero_score_count = 0`

Interpretation:
- The rescue branch improved the formatting failure only marginally: `0/4 -> 1/4` tagged completions.
- It did not recover usable task performance: even the one tagged completion produced an incorrect sequence.
- This is enough to say the broad object story is not just waiting for a tiny prompt fix on `quantum_lock`; rescuing that family would require a more substantial protocol redesign.

New protocol branch: `quantum_lock` as state search
- Added protocol spec:
  - `project/quantum_lock_protocol.md`
- Added a new branch collector:
  - `scripts/collect_quantum_lock_answer_only.py`
- Added a new branch trace converter:
  - `scripts/derive_quantum_lock_transition_traces.py`

Branch idea:
- collect only the final button sequence
- recover step units from simulator transitions rather than from free-form natural-language reasoning
- treat `State value/color -> button -> next_value/next_color` as the new step unit

Branch result:
- `artifacts/object_gate/rollouts/api_quantum_lock_answer_only_000.jsonl`
  - `4 prompts`
  - `final_present = 4/4`
  - `nonzero_score_count = 0`
- `artifacts/object_gate/rollouts/api_quantum_lock_transition_000.jsonl`
  - kept `0` usable traces at `min_score = 0.5`

Interpretation:
- The state-search branch fixed the formatting problem but not the task-solving problem.
- This is informative: for `quantum_lock`, the bottleneck is not only how we externalize traces. Under the current model/API, the model also fails to produce correct or near-correct shortest sequences reliably.
- So the right conclusion is not “the new branch failed because the trace object was wrong.” It is “this family currently fails before the step-credit stage.”
- That makes the branch a useful diagnostic, but not a viable second family for broadening the main Object claim.

Interpretation:
- API is materially better than local 1.7B at keeping high-dependency outputs structurally separated into reasoning and final sections.
- API does not automatically solve task correctness; one Tower-of-Hanoi sample still scored `0.0`.
- The gain is mainly in controllability and reasoning/final separation, which is exactly what the calibration branch needed to test.

Budget note:
- Total API use in this turn was tiny: one 24-token probe plus two 2-sample calibration runs totaling `2704` tokens.
- Local config does not include unit pricing, so only token usage is recorded here.

Observed failure pattern:
- The calibrated interface fixes tag closure.
- On high-dependency `tower_of_hanoi`, the model still tends to duplicate final-format move sequences inside `<reasoning>`, which is bad for later step intervention.
- On shallow arithmetic, the current wrapper is already usable for Object-gate trace collection.
- API reduces the duplication problem when the reasoning budget is explicitly capped, but does not guarantee correct final plans.
- The first intervention batch should start from API high-dependency traces plus local shallow traces, not from local high-dependency traces.
- The first populated intervention batch now exists and is ready to be turned into rollout records.
- The first rollout records now exist, but the rollout definition must be tightened before Object-gate claims can start.
- The tightened prefix-based rollout now provides the first non-trivial variant separation signal.
- The expanded ready-only batch confirms the signal is not a one-off, but also shows the current intervention construction is not yet stable enough.

Conclusion:
- Phase 0 framing is complete enough to prevent direction drift.
- Object gate has a frozen minimal protocol and can be initialized immediately.
- The primary task source is now connected.
- Prompt construction is frozen as: procedural task instance plus thin model wrapper with assistant prefill; semantic interventions remain model-first.
- The live trace interface is now calibrated enough to start a small mixed dev batch.
- The next bottleneck is no longer formatting. It is family-specific reasoning quality on high-dependency tasks.
- API is justified as a calibration and semantic-generation tool, not as the main evidence path.
- Intervention drafting has started; the next technical bottleneck is candidate generation for paraphrase and distractor variants.
- Candidate generation is now in place; the next bottleneck is intervention quality control plus rollout packaging.
- Rollout packaging is now complete; the next bottleneck is running and scoring the first delete/paraphrase/distractor continuations.
- End-to-end rollout execution is complete; the next bottleneck is making the rollout definition sensitive enough to expose variant differences.
- Prefix-based continuation resolves that bottleneck for the small smoke case.
- Prefix-based continuation remains the correct rollout definition for this project.

Next action:
- Build a second-pass candidate set that prioritizes early planning steps and regenerates stronger distractors for high-dependency families.
- Re-run prefix rollouts on that cleaner batch before making any stronger Object-gate statement.

Object redefinition note:
- Added `project/object_redefinition_memo.md`.
- This memo explicitly separates text lines, surface steps, decision-bearing units, and execution/bookkeeping units.
- Working conclusion: the next Object branch should test decision-bearing state updates rather than arbitrary reasoning lines, and should compare decision-unit interventions against execution/bookkeeping interventions before any further family sweep.

## 2026-04-07 Object Redefinition Branch Freeze

Question:
- Before expanding experiments again, can the project freeze a better scientific unit than line-level reasoning steps?

Actions:
- Added project/decision_unit_segmentation_spec.md.
- Added project/decision_unit_candidate_schema.md.
- Added project/object_redefinition_gate.md.
- Added configs/object_redefinition.json.
- Updated progress.md and artifacts/object_gate/run_state.json so the active branch is Object Redefinition rather than broad family expansion.

Frozen branch decision:
- The old line-level Object branch remains valuable as a bootstrap baseline and as family-selective diagnosis.
- The active object is now decision-bearing state update credit, not arbitrary reasoning-line credit.
- The next admissible execution unit is one-family, one-carrier, decision-versus-control validation, with tower_of_hanoi as the default first family.

Key design consequences:
- line_split_v0 is no longer the default scientific segmentation rule
- future candidate files must label units as decision, execution, bookkeeping, or unclear
- broad family expansion is paused until the new branch passes Unit Validity, Decision Sensitivity, and Proxy Comparison
- countdown and quantum_lock are explicitly deferred for different reasons: multi-solution evaluation mismatch versus solving-reliability failure

Interpretation:
- The project's main bottleneck is now object definition, not more prompt tweaks or more family probes.
- This freeze reduces the risk of over-reading early-line signal as if it were a general process principle.
- The next useful experiment is not another family sweep; it is a controlled test of whether decision-labeled units behave differently from execution/bookkeeping units within the same trace.
