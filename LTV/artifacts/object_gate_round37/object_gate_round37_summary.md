# Round37: stronger pairwise progress label spec

## Goal

Turn the next step after rounds 35/36 into a concrete artifact:

- define a stronger pairwise progress label schema,
- make explicit which fields are missing from the current Lean data,
- and scaffold the existing CTS panel into that schema without pretending the labels are already final.

## What Exists Now

Current Lean raw rows contain only:

- `theorem_id`
- `header`
- `steps`
- `local_sound`
- `notes`

They do **not** contain proof-state fields such as:

- before / after goal counts
- main-goal solved flag
- spawned subgoal counts
- before / after pretty-printed goals
- before / after goal-complexity measures
- parser / replay status for variants

So the current round35/36 pairwise results remain proxy-based object evidence, not final pairwise progress labels.

## New Spec

Created:

- [pairwise_progress_label_v0.yaml](/cephfs/luyanzhen/apg/LTV/configs/object_gate/pairwise_progress_label_v0.yaml)

This spec defines:

### Candidate-level progress classes

- `solved` = closes the main goal
- `reduced` = locally sound and reduces goals / obligation complexity
- `equivalent` = locally sound and proof-state-equivalent rewrite
- `ambiguous` = locally sound but progress direction unclear
- `regressed` = locally sound but worsens goal structure
- `unsound` = invalid local step

### Pair-level labels

- `no_progress_difference`
- `source_better_weak`
- `source_better_strong`
- `variant_better_weak`
- `variant_better_strong`
- `incomparable`

### Label status

- `final_usable`
- `proxy_only`
- `needs_proof_state_extraction`
- `ambiguous_holdout`

## Scaffold

Created:

- [scaffold_pairwise_progress_panel.py](/cephfs/luyanzhen/apg/LTV/scripts/scaffold_pairwise_progress_panel.py)
- [cts_pairwise_progress_round37_scaffold.jsonl](/cephfs/luyanzhen/apg/LTV/data/cts/cts_pairwise_progress_round37_scaffold.jsonl)

This scaffold maps the current round7 CTS panel into the new schema while keeping the status honest.

Current scaffold counts:

- `num_pairs = 58`
- `proxy_only_pairs = 58`
- `needs_proof_state_extraction_pairs = 58`
- `same_pairs = 30`
- `source_better_strong_pairs = 28`

So the current panel is now schema-aligned, but none of its rows yet satisfy the stronger final label requirements.

## Interpretation

Round37 does not create a new experimental result.
It does something more important for the next stage:

- it freezes what a stronger pairwise progress label should mean,
- it separates current proxy evidence from future structural labels,
- and it prevents the project from quietly reusing `same/flip` as if that were already the final object.

The practical next step is now explicit:

- add a proof-state extraction pass,
- replay both source and variant steps,
- fill the missing before/after state fields,
- then derive `final_usable` pairwise progress labels under the new schema.
