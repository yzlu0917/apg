# Benchmark Acceptance Standard

## Purpose

This document fixes the benchmark quality target for this project.

The goal is **proposal-aligned benchmark adequacy**, not the strongest possible human-indistinguishability target.

## Proposal-Aligned Hard Requirements

A benchmark slice is good enough for this project if it satisfies all of the following:

1. **Audited semantics are preserved**
   - quartet structure remains valid
   - the audited locus still marks the intended local process flip
   - answer-matched counterfactuals are still valid inputs for `AMCD`

2. **Executable / verifiable content is preserved**
   - equations, path identities, totals, state strings, and other domain anchors remain exact where required
   - invalid traces remain invalid for the intended local reason

3. **Artifact audit is passed**
   - shallow classifier does not trivially separate counterfactual type
   - length-only baseline does not trivially separate counterfactual type
   - multi-verbalizer consistency is maintained

4. **Blind audit rejects obvious artificial-edit cues**
   - no copied clean ending
   - no one-side-only scaffolding
   - no near-copy plus one local text patch
   - no obvious style-shell with a single injected wrong number
   - no overt discourse-marker asymmetry that reveals the edited trace

## Explicit Non-Requirements

The benchmark does **not** need to satisfy the following stronger target:

- every valid/invalid pair must be visually indistinguishable to a human reviewer
- structured algebra errors must be made as inconspicuous as valid derivations
- semantic wrongness must be hidden if it follows naturally from the domain structure

In particular, for algebra and other highly structured domains:

- a wrong derivation step may remain visibly wrong because of the math itself
- this is acceptable as long as the trace does not also expose non-semantic editing artifacts

## What Blind Review Should Target

Blind review should primarily ask:

> Does this trace or pair look artificially edited, templated, patched, or stylistically asymmetric?

Blind review should **not** be interpreted as requiring:

> The wrong step must look semantically as plausible as the valid one.

## Prompt Objective

Generation prompts should optimize for:

- artifact cleanliness
- independently written surface style
- balanced polish / verbosity across paired traces
- preservation of exact latent content

Generation prompts should explicitly avoid optimizing for:

- hiding wrong arithmetic / wrong state transitions
- making invalid reasoning semantically look valid
- universal pairwise indistinguishability

## Feedback Policy

Reviewer feedback should be split into two kinds:

1. **Surface-artifact feedback**
   - templated
   - patched
   - copied
   - asymmetrical
   - over-scaffolded
   - unnatural phrasing

2. **Semantic-wrongness feedback**
   - incorrect arithmetic
   - inconsistent equation
   - wrong total
   - illegal move
   - invalid path/state update

Only the first kind should be fed back into regeneration prompts.

## Practical Acceptance Rule

For this project, a benchmark slice is acceptable when:

- proposal hard requirements are met
- remaining reviewer signal is dominated by semantic wrongness visibility rather than obvious artificial-edit cues

That is the benchmark target to optimize going forward.
