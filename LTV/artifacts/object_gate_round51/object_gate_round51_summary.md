# Round51 Summary

## Goal

Add a second-annotator review pass on the current `17`-state oracle panel, quantify disagreement, build a minimally adjudicated consensus panel, and test whether the object-level separability claim survives this label perturbation.

## Second Annotator / Agreement

- Second annotator panel: [state_first_progress_oracle_panel_v2_second_annotator.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_panel_v2_second_annotator.jsonl)
- Agreement summary: [oracle_agreement_summary.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/oracle_agreement_summary.json)
- Disagreement rows: [oracle_disagreements.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/oracle_disagreements.jsonl)

Agreement statistics:

- `num_states = 17`
- `num_candidates_compared = 104`
- `candidate_agreement = 0.9135`
- `agreement_count = 95`
- `disagreement_count = 9`

Disagreement structure:

- `95` exact matches
- `8` one-tier disagreements
- `1` two-tier disagreement

The disagreement is concentrated in a small number of states:

- `lean_and_comm_pos__step1`
- `lean_imp_trans_pos__step3`
- `lean_and_imp_elim_pos__step1`
- `lean_and_to_imp_apply_pos__step1`
- `lean_double_neg_intro_pos__step2`

These are all boundary cases about whether exposing an exact next-step premise counts as `weak_partial` or `strong_partial`, plus one case about whether duplicating an existing hypothesis counts as progress.

## Consensus Panel

- Adjudication overrides: [oracle_adjudication_overrides.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/oracle_adjudication_overrides.json)
- Consensus panel: [state_first_progress_oracle_panel_v2_consensus.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_panel_v2_consensus.jsonl)

Adjudication policy:

- exposing the exact immediate premise for the next obvious implication step is treated as `strong_partial`
- duplicating an already available hypothesis without changing the state is treated as `neutral`

## Separability on Consensus Panel

- DeepSeek: [deepseek_state_first_panel_v2_consensus_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/deepseek_state_first_panel_v2_consensus_sep.json)
- Goedel: [goedel_state_first_panel_v2_consensus_sep.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round51/goedel_state_first_panel_v2_consensus_sep.json)

DeepSeek:

- gap task:
  - `linear AUROC = 0.9085`
  - `centroid AUROC = 0.8874`
- direction task:
  - `linear AUROC = 0.9490`
  - `centroid AUROC = 0.9755`

Goedel:

- gap task:
  - `linear AUROC = 0.8874`
  - `centroid AUROC = 0.8426`
- direction task:
  - `linear AUROC = 0.9148`
  - `centroid AUROC = 0.9748`

## Readout

The second-annotator pass does not overturn the object-level result. The numeric tradeoff shifts slightly relative to round50, but the main conclusion remains:

> pairwise progress-difference information is still clearly separable in frozen hidden states under weak readouts, even after second-annotator review and minimal consensus adjudication.

This makes the current object gate substantially harder to dismiss as a single-annotator artifact.
