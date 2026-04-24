# Decision-Unit Candidate Schema v0

Date: 2026-04-07
Status: frozen draft for the Object Redefinition branch
Phase: candidate construction before rollout redesign

## Goal

Define the minimal auditable record for candidate units under the redefined object.

This schema replaces the assumption that one candidate equals one reasoning line. A candidate is now a labeled unit built from the family-appropriate carrier and reviewed as one of:
- decision
- execution
- bookkeeping
- unclear

## Input eligibility

A source trace or state record is eligible only if:
- the carrier is present and parseable
- final answer data is present
- verifier metadata is present
- the trace carrier matches the family's expected unit type well enough to support review

Additional branch preference:
- prefer traces with at least one clear decision unit and one usable non-decision control
- prefer traces where the candidate unit can be localized without reconstructing the whole latent plan from scratch
- keep unclear traces for audit, not for the main intervention batch

## Candidate record fields

Each candidate record should include the following sections.

### Provenance

- candidate_id
- source_rollout_file
- trace_id
- prompt_id
- family
- difficulty_stratum
- backend
- model_family
- protocol_branch

### Carrier metadata

- carrier_type
  - examples: planning_text, state_transition, equation_state
- carrier_version
- carrier_parse_ok
- carrier_location
  - text span, transition index, or state block reference

### Segmentation metadata

- segmentation_version
- unit_id
- unit_index
- num_units_in_trace
- span_start
- span_end
- unit_surface
- unit_state_before, if available
- unit_state_after, if available

### Unit typing

- unit_type
  - decision, execution, bookkeeping, unclear
- unit_type_confidence
  - high, medium, low
- label_evidence
- upstream_commitment_id
- decision_role
  - examples: decomposition, intermediate_target, branch_prune, algorithm_choice, transition_commitment, none

### Selection metadata

- selection_version
- selection_reason
- review_status
  - ready, review_needed, audit_only, rejected
- rejection_reason, if not ready

### Intervention slots

- delete_variant
- paraphrase_candidates
- distractor_candidates
- matched_control_unit_id, if present
- intervention_policy_version

### Rollout linkage

- continuation_policy
- remaining_budget_policy
- continuation_count
- evaluation_policy
- status

## Minimal first-branch defaults

- segmentation_version: macro_decision_v0
- selection_version: decision_control_pair_v0
- intervention_policy_version: matched_counterfactual_v1
- continuation_policy: prefix_or_state_resume
- remaining_budget_policy: same_remaining_budget_as_source
- continuation_count: 2
- status: drafted

## Required pair structure for the first clean branch

The main dev batch should prefer trace-local pairs:
- one clear decision unit
- one matched non-decision control from the same trace

Preferred control order:
1. execution
2. bookkeeping
3. no control, only if the trace otherwise would be lost

Rationale:
- the next Object branch should test whether the unit type itself predicts intervention sensitivity
- same-trace pairing reduces prompt-level confounds

## Variant construction rules

### Delete

- remove the selected unit from the carrier
- preserve all earlier accepted context
- do not silently rewrite surrounding content unless the carrier requires structural repair

### Paraphrase

- preserve the commitment type and operational content
- allow surface rewording only
- for state carriers, paraphrase may be a semantically equivalent alternative encoding rather than language rewriting

### Distractor

- stay locally plausible for the same carrier role
- introduce a different commitment or a wrong branch implication
- do not collapse to a pure formatting or verbosity change
- must be rejected if equivalent to the original decision under local normalization

## Review gates at candidate stage

A candidate is ready only if:
- the carrier parse is trustworthy enough for this family
- the selected unit has a non-unclear type label
- the intervention slots can be defined without changing upstream context
- the selected unit is not just copied final-answer formatting

A candidate is audit_only if:
- it is scientifically informative for failure analysis
- but not trustworthy enough for main-batch intervention

## What this schema intentionally leaves open

- exact search-cost metrics for multi-solution families
- family-specific paraphrase realizations for non-text carriers
- whether later branches should include more than one decision unit per trace

## Exit condition for this stage

This stage is complete when:
- a candidate file exists with the fields above
- most retained records contain one decision unit and one matched non-decision control
- review can recover why each candidate was included and what scientific role it plays
