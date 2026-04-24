# QuantumLock State-Search Protocol

Date: 2026-03-31
Status: exploratory branch

## Motivation

`quantum_lock` failed under the shared reasoning wrapper because the model used
`<reasoning>` as an open-ended search scratchpad and exhausted the token budget
before emitting a final sequence. That failure says more about the trace
protocol than about the task family itself.

This branch therefore treats `quantum_lock` as a state-search task with a
different object representation.

## Redefined object

- Task type: shortest-path state search under explicit simulator dynamics
- Step unit: one executed state transition edge
- Trace source: the final button sequence, not free-form natural-language search
- Rollout unit: continue from a simulator state plus an accepted action prefix

## Protocol

1. Collect answer-only button sequences from the model.
2. Simulate the proposed sequence with the task metadata.
3. Convert the sequence into a transition trace:
   - `State <value>/<color> -> <button> -> <new_value>/<new_color>`
4. Treat each transition line as a candidate step unit.
5. For continuation rollouts, condition on:
   - the original task
   - the current simulator state
   - the accepted action prefix
   - optionally the structured transition prefix

## Why this differs from the default object gate

- The default protocol assumes the model can externalize short causal reasoning
  lines before producing the final answer.
- `quantum_lock` naturally induces many short simulated branches, so that
  assumption fails.
- The state-search protocol instead makes the executed transition sequence the
  primary trace object and uses the simulator to recover step structure.

## Acceptance for this branch

- Minimum viability:
  - at least `2/4` sampled prompts produce a parsable final sequence
  - at least `1/4` sampled prompts reaches non-zero score
  - transition traces can be derived automatically from the final sequence
- If this fails, the branch is not worth expanding without a larger protocol
  redesign.

## Current note

- This branch is exploratory and does not overwrite the main Object-gate
  account unless it produces a cleaner second structured-planning family than
  the shared wrapper did.
