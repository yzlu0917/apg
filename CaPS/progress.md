# Progress

Current goal:
- Freeze the Object Redefinition branch around decision-bearing units and prepare the next Object gate on the right scientific unit rather than on line-level steps.

Milestones:
- DONE: Read governing `AGENTS.md`, `README.md`, and `proposal.md`.
- DONE: Freeze claim hierarchy, fallback framing, and four-gate progression.
- DONE: Create minimal project skeleton and Object-gate bootstrap files.
- DONE: Connect the `infer` environment to the primary task source.
- DONE: Freeze exact task families and generate the first prompt manifests.
- DONE: Validate live trace collection against the frozen prompt wrapper.
- DONE: Start and inspect the first mixed dev trace batch with the calibrated interface.
- DONE: Tighten high-dependency prompt behavior so reasoning stops duplicating final-format content.
- DONE: Use API as a small calibration branch for high-dependency traces while keeping local models on the main line.
- DONE: Build the first tiny intervention schema on top of the frozen manifests.
- DONE: Turn drafted candidates into the first delete/paraphrase/distractor population pass.
- DONE: Review candidate quality and prepare the first intervention micro-batch manifest.
- DONE: Prepare and run the first continuation-rollout smoke execution on top of the packaged micro-batch.
- DONE: Tighten rollout definition from full-draft conditioning to prefix-based continuation so variants can separate.
- DONE: Expand the prefix-based rollout from the 6-variant smoke batch to the full current ready-only micro-batch.
- DONE: Improve step selection and distractor strength for sources that still show no separation or saturated ties.
- DONE: Build the first explicit proxy-control comparison against step correctness and raw-progress surrogates on top of the cleaner second-pass batch.
- DONE: Rewrite the immediate Object-gate story around family-selective early-planning credit rather than a broad high-dependency claim.
- DONE: Formalize the object-redefinition memo into a segmentation spec, candidate schema, branch gate, and frozen config.
- DOING: Prepare the next Object gate as one-family, one-carrier, decision-versus-control validation.
- DONE: Add one more control slice to test whether the early-planning restriction is stable across another high-dependency family.
- DONE: Probe an additional structured-planning-style family (`quantum_lock`) to decide whether broadening is still viable under the current wrapper.
- BLOCKED: none at phase-0 infrastructure level.

Latest updates:
- 2026-03-31: Initialized `project/`, `configs/`, `scripts/`, `history/`, `data/`, and `artifacts/`.
- 2026-03-31: Wrote the phase-0 claim and gate documents.
- 2026-03-31: Added `configs/object_gate.json` and `scripts/bootstrap_object_gate.py`.
- 2026-03-31: Ran the bootstrap script and created `artifacts/object_gate/run_state.json` plus `artifacts/object_gate/manifest.template.json`.
- 2026-03-31: Installed `reasoning-gym==0.1.25` into `infer` and confirmed a 106-dataset registry.
- 2026-03-31: Froze the first four Object-gate families and wrote the prompt protocol.
- 2026-03-31: Generated `artifacts/object_gate/samples/dev_manifest.jsonl` with 48 prompts and `final_manifest.jsonl` with 96 prompts.
- 2026-03-31: Verified sample prompt rows for the thin-wrapper format and family split.
- 2026-03-31: Added `scripts/collect_object_gate_traces.py` and confirmed `vllm` is blocked by a local `flash_attn` / `GLIBC_2.32` mismatch.
- 2026-03-31: Switched trace collection to `transformers` fallback and calibrated Qwen3 with assistant prefill from `<reasoning>`.
- 2026-03-31: Verified one shallow sample with `format_ok=1` and `score=1.0`; verified one high-dependency sample with `format_ok=1` but incorrect final answer.
- 2026-03-31: Ran a 4-prompt mixed smoke batch with `format_ok=4/4`; shallow samples scored `1/2`, high-dependency samples scored `0/2`.
- 2026-03-31: Added `scripts/collect_api_calibration_traces.py` and confirmed the provided API works with OpenAI-compatible `chat/completions`.
- 2026-03-31: API high-dependency calibration improved from `format_ok=1/2` to `2/2` after enforcing very short reasoning.
- 2026-03-31: Added `project/intervention_schema.md` and `scripts/build_intervention_templates.py`.
- 2026-03-31: Drafted 9 intervention candidates: 7 `ready`, 2 `review_needed`.
- 2026-03-31: Added `scripts/generate_intervention_candidates.py` and generated paraphrase/distractor candidates for all 7 ready steps.
- 2026-03-31: Added `scripts/package_intervention_batch.py` and packaged 21 intervention variants into `micro_batch_v0.jsonl`.
- 2026-03-31: Added `scripts/run_intervention_smoke_rollout.py` and ran a 6-variant smoke rollout across one high-dependency and one shallow source.
- 2026-03-31: Added `scripts/run_intervention_prefix_rollout.py` and reran the same 6 variants under prefix-based continuation.
- 2026-03-31: Fixed `intervention_id` collisions by adding source provenance to packaged ids.
- 2026-03-31: Ran the full 21-variant ready-only prefix rollout batch.
- 2026-03-31: Added `scripts/refine_intervention_candidates.py` validation retries so second-pass distractors are rejected if they are equivalent or lack a concrete error commitment.
- 2026-03-31: Regenerated `generated_candidates_v1.jsonl`, repackaged `micro_batch_v1.jsonl`, and ran `intervention_prefix_rollout_batch_v1_000.jsonl`.
- 2026-03-31: Added `scripts/analyze_intervention_rollout.py` and confirmed the cleaner batch reaches weak ordering on `3/4` source groups but strict ordering on `0/4`.
- 2026-03-31: The main second-pass gain is concentrated on high-dependency early planning: one `tower_of_hanoi` distractor dropped from `1.0` to `0.0`, while shallow arithmetic still shows one distractor tying the paraphrase.
- 2026-03-31: Parameterized `scripts/refine_intervention_candidates.py` with selection-reason and family filters so it can build dedicated control batches.
- 2026-03-31: Built a matched-role high-dependency paired-step control batch: `generated_candidates_proxy_v0.jsonl` -> `micro_batch_proxy_v0.jsonl`.
- 2026-03-31: Ran `intervention_prefix_rollout_proxy_v0_000.jsonl` and confirmed the current signal is early-step-specific: first steps show weak ordering on `2/2`, while last-step legality checks either saturate at one common score or collapse to all zero.
- 2026-03-31: Added rollout-selectable drafting in `scripts/build_intervention_templates.py`, carved out a `countdown` manifest slice, and ran `api_countdown_calibration_001.jsonl`.
- 2026-03-31: Built `countdown` paired-step batches through `generated_candidates_countdown_v1.jsonl` and `micro_batch_countdown_v1.jsonl`.
- 2026-03-31: Ran `intervention_prefix_rollout_countdown_v1_000.jsonl`; `countdown` did not replicate the `tower_of_hanoi` pattern. Three of four step groups saturated at full score across variants, and the remaining group only separated because the distractor continuation truncated.
- 2026-03-31: Built a 4-prompt exploratory `quantum_lock` slice and ran `api_quantum_lock_calibration_000.jsonl`.
- 2026-03-31: `quantum_lock` failed at the formatting layer under the current wrapper: `format_ok = 0/4`, `nonzero_score_count = 0`, with all 4 samples exhausting the reasoning budget before closing tags.
- 2026-03-31: Added a family-specific `quantum_lock_shortplan` mode to `scripts/collect_api_calibration_traces.py` and reran the same 4-prompt slice.
- 2026-03-31: The rescue branch improved formatting only marginally (`format_ok = 1/4`) and still produced `nonzero_score_count = 0`; the broad-object branch remains closed under the current protocol family.
- 2026-03-31: Opened a separate `quantum_lock` state-search protocol branch with [project/quantum_lock_protocol.md](/cephfs/luyanzhen/apg/CaPS/project/quantum_lock_protocol.md).
- 2026-03-31: Added [collect_quantum_lock_answer_only.py](/cephfs/luyanzhen/apg/CaPS/scripts/collect_quantum_lock_answer_only.py) and [derive_quantum_lock_transition_traces.py](/cephfs/luyanzhen/apg/CaPS/scripts/derive_quantum_lock_transition_traces.py).
- 2026-03-31: The new branch solved format but not correctness: `api_quantum_lock_answer_only_000.jsonl` achieved `final_present = 4/4`, `nonzero_score_count = 0`, so the derived transition-trace file kept `0` usable samples.

Blockers and default decisions:
- Default: procedural generation remains limited to frozen task instances and benchmark slices.
- Default: semantic generation remains model-first, but no broad execution is allowed until the redefinition branch leaves design freeze.
- Environment note: use transformers for now; vllm is not the critical path until the system library mismatch is resolved.
- Default: tower_of_hanoi is the first-family choice for the redefinition branch; countdown and quantum_lock stay deferred for object-definition reasons, not because they are forgotten.

Resume point:
- Treat the old line-level branch as a documented bootstrap baseline, not as the active scientific object.
- Build candidate units under macro_decision_v0 with explicit decision/execution/bookkeeping labels and same-trace non-decision controls.
- Keep the next execution scoped to one family, one carrier, and Unit Validity plus Decision Sensitivity.
- Reopen broad family expansion only after the redefinition branch passes Proxy Comparison on the chosen family.
