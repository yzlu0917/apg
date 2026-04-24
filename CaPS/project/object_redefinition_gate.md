# Object Redefinition Gate

Date: 2026-04-07
Status: active
Phase: pre-experiment branch freeze

## Goal

Freeze the next Object branch around the right scientific unit before any further family expansion or method work.

The branch question is now:
- can decision-bearing units be identified, separated from execution and bookkeeping, and shown to align better with counterfactual utility than older text-line proxies?

## Supported carry-over from the old branch

What remains valid from the earlier Object branch:
- matched-counterfactual interventions remain the right broad testing idea
- prefix-based continuation remains a better rollout idea than full-draft conditioning
- family-selective evidence on tower_of_hanoi justifies continuing object work

What is no longer treated as default scientific truth:
- one reasoning line equals one process step
- early-versus-late line position is itself the main object
- mixed-family broadening is the right next move

## New primary claim boundary

Current headline object claim:
- the project is testing whether decision-bearing state updates, not arbitrary reasoning lines, are the right object for process credit

Conditional claim only:
- if such units can be segmented and audited, matched-counterfactual interventions may expose cleaner process signal than text-line proxies

Not currently supported:
- a universal line-level credit story across heterogeneous reasoning families

## Gate structure

### Gate 1: Unit Validity

Question:
- can the branch produce reviewable candidate units that are mostly non-unclear and meaningfully typed as decision, execution, or bookkeeping?

Go if:
- retained-unit non-unclear rate is at least 0.80 on the dev slice
- most usable traces yield at least one decision unit
- most usable traces also yield at least one matched non-decision control

No-go if:
- the carrier cannot be segmented without heavy ad hoc interpretation
- most units end up unclear or trivially answer-formatting

### Gate 2: Decision Sensitivity

Question:
- do interventions on decision units produce stronger and cleaner damage than interventions on execution or bookkeeping units from the same trace?

Go if:
- decision units beat matched non-decision controls on at least one frozen primary effect measure
- the effect is not explained mainly by unit length or unit position

No-go if:
- decision and non-decision units are not distinguishable under the chosen carrier and rollout

### Gate 3: Proxy Comparison

Question:
- does the new unit-level object align better with counterfactual utility than old proxies such as step correctness, raw progress, or line position?

Go if:
- at least one frozen alignment measure favors the new object over the old proxies on the dev slice

No-go if:
- old simple proxies explain the effect equally well or better

### Gate 4: Family Transfer

Question:
- after passing the first three gates in one family, does the object survive in at least one structurally related family with an appropriate carrier?

Go if:
- the same object logic, not necessarily the same raw carrier, reproduces on one second family

No-go if:
- the effect disappears once the family changes and the branch cannot explain why without post-hoc story repair

## Frozen acceptance for this branch

The branch can move from design to small execution only if all of the following are true:
- a segmentation spec exists and is frozen
- a candidate schema exists and is frozen
- a config exists with one chosen family, one carrier type, and one dev slice
- the active objective is unit validity plus decision sensitivity, not broad family coverage

The branch can claim an Object-gate pass only if:
- Unit Validity passes
- Decision Sensitivity passes
- Proxy Comparison passes

Family Transfer is explicitly not required for the first pass of the redefinition branch.

## Default first-family policy

Default recommended family:
- tower_of_hanoi

Reason:
- it already showed the cleanest evidence that some early planning content behaves differently from later bookkeeping-like content
- it is the lowest-risk place to test whether the new unit labels actually explain the old signal

Default deferred families:
- countdown, until equation-state units and search-cost-aware evaluation are specified
- quantum_lock, until solving reliability is high enough to produce usable state-transition traces

## Required artifacts

- project/decision_unit_segmentation_spec.md
- project/decision_unit_candidate_schema.md
- configs/object_redefinition.json
- updated progress.md
- updated results.md

## What is not allowed yet

- no new family sweep
- no CPV training
- no method claim
- no deployment claim
- no rescue-by-metric-switch after results arrive

## Exit condition for this planning stage

This planning stage is complete when:
- the branch files above are on disk
- project tracking names Object Redefinition as the active line
- the next experiment can be described as one-family, one-carrier, decision-versus-control validation rather than another broad sweep
