# Object Redefinition Memo

Date: 2026-04-03
Status: active
Phase: object clarification before further experimentation

## 1. Why this memo exists

The current Object-gate loop was designed to answer a small question:

- can matched-counterfactual interventions expose a measurable process object on objective-verifier tasks?

That loop succeeded only partially. It produced signal on `tower_of_hanoi`, but it also exposed a deeper problem:

- the project has been using "one reasoning line" as a stand-in for "one process step"
- in many families, that stand-in is wrong

This memo therefore pauses further family expansion and redefines the object that the project should be trying to measure.

## 2. The core mistake in the current branch

The current branch mostly assumes:

- text line ~= reasoning step ~= unit of causal work

That assumption is attractive because it is easy to segment and easy to audit. But it fails whenever:

- one real decision is unpacked across several lines
- one line is only bookkeeping or formatting
- a later line merely externalizes a commitment made earlier
- the task admits many alternative continuations, so deleting one text line does not erase the underlying strategy

This means that the current branch is not yet measuring "what really worked." It is often measuring "what happened to be said on this line."

## 3. What should count as "work"

The project should use a stricter notion of process work.

### Proposed definition

A unit of reasoning works if it satisfies all three conditions:

1. It performs a decision-bearing state update.
2. That update shrinks the future search space toward successful continuations.
3. The update is not mechanically recoverable from earlier accepted state without comparable extra search.

In plain language:

- a process unit works when it commits the solver to information that the later success actually depends on
- and that commitment is not just a stylistic restatement or a trivial bookkeeping move

## 4. The right unit is not the text line

The project should distinguish at least four levels.

### 4.1 Text line

- The literal surface span in `<reasoning>`.
- Useful for logging and debugging.
- Not reliable as the scientific unit.

### 4.2 Surface step

- A locally coherent chunk of text that looks step-like.
- Better than a raw line, but still may be only rhetorical packaging.

### 4.3 Decision-bearing unit

- A unit that commits to a meaningful choice:
  - decomposition choice
  - intermediate target choice
  - search branch pruning
  - algorithm or schema selection
  - state transition that changes future reachable solutions

This is the proposed default object for credit assignment.

### 4.4 Execution or bookkeeping unit

- Expands or verifies an earlier decision without adding a new branch-resolving commitment.
- Examples:
  - writing out already-determined moves
  - checking legality after the plan is fixed
  - formatting the final expression
  - repeating that all numbers were used

These units may still matter for complete execution, but they should not be treated as the main causal object by default.

## 5. Three-way process taxonomy

The next branch should classify candidate units into:

### A. Decision units

- Introduce new constraint-satisfying commitments
- Change the latent solver state in a non-trivial way
- Are the primary target for Object-gate credit

### B. Execution units

- Realize a decision that is already fixed
- May have local necessity, but usually derive their value from an earlier decision
- Should be analyzed separately from decision units

### C. Bookkeeping units

- Validate, restate, or format
- Often useful for robustness or audit
- Should not be expected to carry primary process credit

## 6. Counterfactual meaning under the new object

Under the redefined object, a good counterfactual test is not:

- "if this sentence disappears, does the answer change?"

Instead, the test should be closer to:

- "if this decision-bearing update is removed or replaced, does the solver lose the branch-resolving information that later success depends on?"

This creates two important consequences.

### 6.1 Delete must be interpreted carefully

Deleting a text line is only a valid intervention if that line is a faithful carrier of a decision-bearing update.

If a later line merely restates an already-fixed plan, deletion should not be expected to cause a large drop. That is not evidence against the object. It is evidence that the selected unit was not the right causal unit.

### 6.2 Multiple-solution tasks dilute naive deletion effects

In tasks with many alternative valid continuations, deleting one textual step may not reveal whether that step worked. The model can route around the local deletion by finding another valid path.

So the correct question becomes:

- does the intervention increase required search or push the policy into worse branches?

not merely:

- does the final answer flip immediately?

## 7. Reinterpreting current results

The current results are more coherent under the new object.

### 7.1 `tower_of_hanoi`

- Early planning lines often behave like decision units.
- Late legality-check lines often behave like bookkeeping.
- So early signal and late saturation is not necessarily a bug. It is what we should expect if only early lines carry branch-resolving decisions.

### 7.2 `countdown`

- The task admits many alternative valid constructions.
- A line-level intervention can leave enough room for the model to recover via another path.
- So weak deletion sensitivity does not imply that nothing worked. It implies that line-level textual units are too fine and too local for this family.

### 7.3 `quantum_lock`

- The family naturally lives in an explicit transition system.
- Free-form reasoning lines are a poor trace carrier.
- The state-search protocol was directionally correct because it moved the unit from text to transition, but the branch still failed because the model could not reliably solve the task itself.

## 8. What the next Object gate should actually test

The next Object-gate branch should no longer ask:

- can arbitrary reasoning lines be assigned causal credit?

It should ask:

- can decision-bearing units be identified, separated from execution and bookkeeping, and shown to align better with counterfactual utility than old proxies?

That reframing changes the acceptance logic.

### New primary checks

1. Unit validity
   - Does the segmentation identify decision-bearing units rather than arbitrary text lines?
2. Decision sensitivity
   - Do interventions on decision units produce stronger and cleaner effects than interventions on execution or bookkeeping units?
3. Proxy comparison
   - Does the new unit-level credit align better with deletion effect, search cost, or continuation utility than step correctness and raw progress?
4. Family-appropriate carrier
   - Is the trace carrier matched to the task family?
   - Examples:
     - planning text for structured planning
     - state transitions for search tasks
     - equation-state snapshots for constructive arithmetic search

## 9. Protocol implications

The next branch should change protocol in three ways.

### 9.1 Replace `line_split_v0`

`line_split_v0` should be treated as a temporary bootstrap heuristic, not the default scientific segmentation rule.

Next segmentation options:

- decision-span segmentation for natural-language plans
- simulator transition segmentation for explicit-state tasks
- macro-step grouping that merges mechanical follow-through under one earlier commitment

### 9.2 Add unit labels

Each candidate unit should carry a provisional type:

- `decision`
- `execution`
- `bookkeeping`
- `unclear`

The first non-trivial Object question then becomes whether these types show different intervention signatures.

### 9.3 Add search-cost-aware evaluation

For multi-solution tasks, the main effect should not rely only on final correctness drop. It should also consider:

- extra search required after intervention
- continuation instability
- divergence into weaker branches
- delayed rather than immediate failure

## 10. Consequences for paper framing

This memo implies a narrower but cleaner story.

Supported direction:

- matched-counterfactual process auditing can reveal useful structure when the object is defined at the level of decision-bearing updates and the trace carrier matches the family

Not yet supported:

- a universal line-level process credit principle over mixed high-dependency reasoning families

This pushes the project closer to:

- protocol plus object-definition paper
- family-selective diagnosis
- eventual method work only after the object unit is corrected

## 11. Immediate next research questions

Before expanding experiments again, answer these:

1. What operational rule defines a decision-bearing unit in each family?
2. Which families offer a trace carrier that faithfully exposes those units?
3. Which evaluation signals capture delayed search damage rather than only immediate final-answer drop?
4. How should multi-solution tasks be scored so local work is not washed out by easy rerouting?

## 12. Recommended next branch

The next branch should be an Object Redefinition branch, not a family sweep.

Concretely:

1. Choose one family where decision units are likely cleanly identifiable.
2. Build a segmentation and labeling scheme for `decision / execution / bookkeeping`.
3. Re-run interventions on those units, not on arbitrary text lines.
4. Only then decide whether the object generalizes or whether the project should freeze as protocol plus diagnosis.
