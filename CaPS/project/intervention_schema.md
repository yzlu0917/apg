# CaPS Intervention Schema v0

Date: 2026-03-31
Status: draft-ready
Phase: Object gate

## Goal

Turn a small number of trace records into auditable intervention candidates without prematurely running paraphrase/distractor generation at scale.

This schema is for the first clean closed loop:
- choose candidate steps
- record why each step was chosen
- define delete/paraphrase/distractor slots
- freeze the rollout-comparison interface

## Input trace requirements

A trace is eligible for intervention drafting only if:
- `format_ok = true`
- `reasoning_present = true`
- `final_present = true`

Additional preference:
- For high-dependency families, prefer traces where reasoning is a short plan rather than a copy of the final answer format.
- If reasoning substantially duplicates final content, mark the trace as `review_needed` and do not use it in the first clean intervention batch.

## Step segmentation rule

Version: `line_split_v0`

Default segmentation:
- Split `reasoning` on newline.
- Strip whitespace.
- Drop empty lines.
- Keep line order.

Rationale:
- The current prompt protocol explicitly asks for one short step per line.
- The first Object-gate loop needs a deterministic and reviewable segmentation rule.

## Candidate-step selection rule

Version: `first_last_v0`

Select at most 2 candidate steps per trace:
- If only 1 segmented step exists: select that step.
- If 2 or more steps exist: select the first step and the last step.
- If first and last are identical after normalization: keep only one.

Rationale:
- First step usually captures decomposition or setup.
- Last step usually captures final bridging logic or constraint check.
- This gives minimal coverage without exploding intervention count.

## Trace-level readiness heuristic

Version: `reasoning_final_overlap_v0`

Heuristic checks:
- Compute normalized line overlap between reasoning lines and final lines.
- If overlap ratio is high, mark `trace_readiness = review_needed`.
- If reasoning lines look like final-format answer lines, mark `trace_readiness = review_needed`.

Intended effect:
- Local high-dependency traces that paste move sequences into reasoning should be filtered out.
- API-calibrated plan-style traces and shallow arithmetic traces should pass.

## Intervention record

Each candidate step record should include:
- trace provenance:
  - `source_rollout_file`
  - `prompt_id`
  - `family`
  - `difficulty_stratum`
  - `backend`
- segmentation:
  - `segmentation_version`
  - `step_index`
  - `step_text`
  - `num_segmented_steps`
- selection:
  - `candidate_selection_version`
  - `trace_readiness`
  - `selection_reason`
- intervention slots:
  - `delete_variant`
  - `paraphrase_candidates`
  - `distractor_candidates`
- rollout linkage:
  - `remaining_budget_policy`
  - `continuation_count`
  - `status`

## First-batch defaults

- `delete_variant`: always defined deterministically by removing the selected step.
- `paraphrase_candidates`: empty placeholder list at schema stage.
- `distractor_candidates`: empty placeholder list at schema stage.
- `remaining_budget_policy`: `same_max_tokens_as_source_trace`
- `continuation_count`: `2`
- `status`: `drafted`

## What this schema intentionally does not do yet

- No model-generated paraphrases yet
- No model-generated distractors yet
- No continuation rollouts yet
- No credit estimates yet

## First clean source preference

Use these traces first:
- API high-dependency calibration traces with short plan-style reasoning
- Local shallow traces with non-zero verifier score

Avoid in the first batch:
- Local high-dependency traces whose reasoning duplicates final move lists

## Exit condition for this stage

This stage is complete when:
- intervention templates exist on disk
- at least one high-dependency and one shallow trace have drafted candidate steps
- every drafted step can be traced back to a source rollout and a deterministic segmentation rule
