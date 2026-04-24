# Decision-Unit Segmentation Spec v0

Date: 2026-04-07
Status: frozen draft for the Object Redefinition branch
Phase: object clarification before further experimentation

## Goal

Replace line_split_v0 with a segmentation rule that targets candidate units of causal work rather than arbitrary text lines.

This spec does not yet claim to solve segmentation for every family. It defines:
- the scientific unit the project now wants
- the minimum labeling interface
- the first deterministic reviewable procedure for building candidate units

## Scientific target

The default target is not a text line.

The default target is a decision-bearing state update:
- a unit that commits the solver to a meaningful new choice
- changes the reachable continuation set in a non-trivial way
- is not merely a restatement, formatting step, or mechanical unfold of an earlier commitment

## Unit taxonomy

Every segmented unit must receive one provisional type label:
- decision
- execution
- bookkeeping
- unclear

Interpretation:
- decision: introduces a branch-resolving commitment
- execution: carries out an already-fixed commitment
- bookkeeping: checks, restates, formats, or records without adding a new commitment
- unclear: insufficient evidence to label cleanly

## Segmentation principles

### 1. Preserve causal coherence

A unit should correspond to one local update in solver state, not one rhetorical sentence.

If multiple adjacent lines only unpack the same commitment, they should be merged into one candidate unit.

### 2. Prefer macro-steps over micro-lines

When in doubt, over-merge mechanical follow-through rather than over-splitting it.

Reason:
- over-splitting turns one real decision into many fake low-credit steps
- that creates the misleading pattern where only the earliest line seems to matter

### 3. Split when the solver commits to a new branch

Create a new candidate unit when the trace introduces a new choice such as:
- decomposition choice
- intermediate-goal choice
- algorithm or schema selection
- irreversible branch pruning
- explicit transition to a new search state

### 4. Do not promote presentation moves into scientific units

These are not primary candidate units by default:
- repeating the task constraint after it is already accepted
- restating the current plan in different wording
- formatting or copying the final answer
- post-hoc legality checks after the plan is already fixed

## Family-specific carrier rule

Segmentation must follow the task's natural trace carrier.

### Structured planning text

Default carrier:
- short planning spans in natural language

Examples:
- tower_of_hanoi

Candidate pattern:
- one macro-unit per strategy commitment or subgoal commitment
- legality reminders usually label as bookkeeping unless they actually prune a branch

### Explicit state-transition tasks

Default carrier:
- simulator transitions or state snapshots, not free-form text lines

Examples:
- quantum_lock

Candidate pattern:
- one unit per state-changing transition or compact transition block
- natural-language commentary is auxiliary only

### Constructive arithmetic or search tasks

Default carrier:
- equation-state updates or branch commitments, not generic prose

Examples:
- countdown

Candidate pattern:
- one unit per intermediate-target commitment, subexpression commitment, or admissibility constraint update
- algebraic mechanical simplification is usually execution

## First operational procedure

Version: macro_decision_v0

For each trace:
1. Extract the family-appropriate carrier.
2. Build the smallest contiguous spans that preserve one local commitment per span.
3. Label each span with one provisional type.
4. Mark the evidence used for the label.
5. Keep at most 3 candidate units per trace for the first branch.

Priority order for retained candidates:
1. first clear decision
2. second clear decision, if it reflects a different commitment type
3. one matched non-decision control from execution or bookkeeping

If no clear decision exists:
- keep the trace for audit only
- do not use it for the main decision-unit intervention batch

## Labeling cues

### Decision cues

Positive cues:
- chooses a subgoal, representation, or algorithm
- rules out a branch or class of branches
- commits to a state update that changes what success paths remain
- introduces information that later steps rely on rather than merely repeat

### Execution cues

Positive cues:
- carries out a previously chosen plan
- performs already-implied arithmetic or move expansion
- fills in deterministic consequences of an earlier decision

### Bookkeeping cues

Positive cues:
- checks legality or completeness after the main plan is already fixed
- repeats constraints without changing the plan
- formats or copies the final output

### Unclear cues

Use unclear when:
- the span mixes decision and execution inseparably
- the trace is too compressed to isolate the commitment
- the family carrier is mismatched and the text cannot be trusted as a faithful state description

## Anti-patterns

Reject these segmentation patterns:
- one raw newline equals one scientific unit by default
- selecting only earliest and latest lines without asking whether they carry distinct commitments
- using answer-format lines as process units
- treating verbosity as evidence of decision content

## Review fields required at segmentation time

Each retained unit must record:
- unit_id
- family
- carrier_type
- segmentation_version
- unit_type
- unit_text_or_state
- span_start
- span_end
- label_evidence
- upstream_commitment_id, if this unit depends on an earlier decision
- review_status

## Acceptance rule for segmentation stage

A segmentation method is acceptable for the next Object branch only if:
- at least 80 percent of retained units can be labeled as non-unclear
- at least one clear decision and one non-decision control can be extracted from most usable traces in the dev slice
- review notes suggest that candidate units correspond to actual commitments rather than rhetorical formatting

## What this spec intentionally does not claim yet

- It does not claim that one segmentation rule will cover all families.
- It does not claim that all decision units will have large immediate final-answer effects.
- It does not claim that free-form reasoning text is always the right carrier.

## Exit condition for this stage

This stage is complete when:
- a candidate-unit file can be built under macro_decision_v0
- every candidate unit has a provisional type label and evidence field
- at least one chosen family yields a clean dev slice with both decision units and non-decision controls
