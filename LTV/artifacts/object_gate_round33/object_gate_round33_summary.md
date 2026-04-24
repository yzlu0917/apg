# Round33: General-Method Reframe

## Why reframe now

The case-analysis branch has done its job.
It established three things:

1. hidden-state signal is real;
2. local-rescue / family-by-family patching is not a method;
3. simple scorer changes do not naturally become a general principle.

So the right move is no longer to rescue more corner cases, but to restore the original proposal-level question:

> what general principle should define a correct latent transition?

## What the proposal already implies

The current project should go back to the original proposal framing:

- object: `latent state transition`, not textual step
- method: `task-conditioned latent transition verifier`
- training principle: combine
  - local correctness
  - same-semantics consistency
  - semantic-flip separation
  - calibration
- evaluation: not just nominal step accuracy, but `IG / SS / matched-budget utility`

The key correction is:

- previous rounds over-indexed on `finding a better scorer`
- the general method should instead learn a `conditioned transition principle`

## New mainline object

The new mainline object is:

**conditioned transition compatibility**

Instead of learning a scalar `step score` directly, learn whether a transition is compatible with a correct local move under the current task / goal context.

Minimal conceptual form:

- inputs:
  - `h^-`
  - `h^+`
  - `Δh`
  - `task embedding`
  - `goal/header context`
  - optional `meta` such as step position / trace length bucket
- output:
  - compatibility / energy of this transition as a locally correct move

## New mainline method hypothesis

The next serious method should be:

**Task-Conditioned Transition Energy Model (TC-TEM)**

High-level idea:

- use an encoder on `(h^-, h^+, Δh)`
- condition it on task / goal context
- learn an energy or compatibility function rather than a single universal truth direction
- train directly with the constraints we actually care about:
  - same pairs should stay close / low-energy together
  - flip pairs should separate with margin
  - calibration should be enforced in-context, not added as a late patch

## What this is not

This is not:

- another small scorer swap
- another family-targeted patch
- another local neighborhood trick
- another attempt to make one global scalar head explain everything

## Why this is the right general direction

This direction is the smallest one that is still aligned with both:

1. the original proposal
2. what the diagnostics already taught us

Specifically:

- task-conditioning is likely necessary
- same/flip must be first-class training signals, not just audits
- calibration must live inside the objective, not only in post-hoc scoring
- universal fixed geometry is too strong an assumption

## Borrowed general ideas that should be treated as first-class

The general line should explicitly borrow from the already-proven families of work behind the proposal:

- hidden-state verification / behavior prediction
- goal-conditioned latent reward modeling
- contrastive learning with hard negatives
- task-specific truth geometry rather than universal truth direction

## What to stop doing

Stop treating the following as mainline work:

- local rescue of singleton cases
- family-by-family story-saving
- simple nonparametric neighborhood scorer branches
- generic scorer sweeps

These can remain diagnostics, but not the method path.

## Round33 decision

Freeze the new mainline as:

**Task-Conditioned Transition Energy Model**

and use the next round to instantiate the smallest executable version of that idea, rather than continuing the old pairwise patch line.

## Minimal next executable step

The next experiment should do exactly three things:

1. add explicit task / goal conditioning to the transition representation;
2. train with one unified objective that includes
   - local correctness,
   - same consistency,
   - flip separation,
   - calibration;
3. evaluate first on the frozen round7 CTS full panel before any scale-up.

## Success condition for the next round

A worthwhile next-round result is not "best single metric".
It is:

- preserves most of round20 same-side cleanliness,
- improves `transition` flip sensitivity over round20 or round32,
- and does so without reopening case-by-case rescue.
