# Object-Gate Synthesis v1

Date: 2026-04-09

## 1. Executive Summary

This project started from a simple question:

> Does a reasoning model's hidden state contain a meaningful signal about whether a candidate next step is actually making proof progress?

The current answer is:

- **Yes, inside the model's competence regime.**
- **No, not as a single globally shared hard-domain progress geometry.**
- On genuinely hard Putnam states, latent progress structure becomes **local and state-specific**, while an external after-state judge remains much closer to a **cross-state canonical progress signal**.

The most accurate current picture is therefore:

- `after hidden` carries a real **candidate-level local progress / affordance signal**
- `before hidden` carries a weaker **state-level competence / trust signal**
- external judge carries a more stable **hard-domain canonical progress scalar**

This means the original proposal should no longer be framed as:

- "latent supervision is a universal replacement for textual or external judging"

but as:

- **latent supervision is a real object, but it is competence-scoped**
- **its strongest role is local reranking inside the model's operating regime**
- **hard-domain global supervision still requires an external canonical signal**

## 2. Original Question and Why the Project Was Reframed

The original proposal asked whether process supervision is supervising the wrong object.

The initial strong version was:

- a reasoning step should not primarily be judged as text
- it should be judged as a **latent state transition**

However, early work showed that jumping directly to a large latent verifier mixed together too many things:

- label quality
- scorer architecture
- textual artifacts
- same/flip proxy design
- dataset leakage / benchmark artifacts

So the project was deliberately narrowed into a cleaner object question:

> Given the same `before state`, and multiple legal `after states`, is there low-complexity progress information in frozen hidden states?

This reframing was the key decision that made the rest of the work interpretable.

## 3. Why the Early CTS Line Was Not Enough

The first major phase used CTS-style counterfactual step pairs:

- `same`: semantic-preserving rewrites
- `flip`: superficially similar but semantically different variants

That phase was useful, but it eventually hit a limit:

- text-side `same/flip` tags and Lean replay semantics did not align cleanly
- replay revealed many "flip" rows that were either invalid for trivial reasons or still semantically workable
- CTS became a good **audit / stress set**
- but not a clean **progress supervision dataset**

The project therefore moved away from "repairing CTS into the main benchmark" and switched to a new data pipeline.

## 4. The Clean Setting That Replaced CTS

The final object-gate pipeline became:

1. choose a Lean `before state`
2. generate multiple candidate tactics
3. replay each candidate in Lean
4. keep only `replay-ok` candidates for progress comparison
5. assign human progress tiers within the same state
6. test whether frozen hidden states can recover those pairwise progress relations

This `state-first -> Lean legality -> human oracle` pipeline matters because:

- Lean determines legality, not the model
- human annotation determines relative progress, not a textual proxy
- comparison is always **within a shared before-state**
- the object is now candidate progress, not surface plausibility

## 5. Data and Oracle Construction

The final clean object-gate panel was built in stages:

- easy/dev panel
- medium panel
- harder expansion panel
- `17`-state consensus oracle panel

The consensus panel contains:

- `17` states
- `104` annotated replay-ok candidates
- `162` ordered pairs
- `117` equivalent pairs

Candidate tiers are:

- `solved`
- `strong_partial`
- `weak_partial`
- `neutral`

Second-annotator audit was added later:

- candidate-level agreement: `91.35%`
- only `9 / 104` candidate disagreements
- most disagreements were adjacent-tier only

This upgraded the object-gate result from "single-annotator positive" to a modest but real audited oracle.

## 6. Object Gate: What Was Proven on Easy/Medium States

On the `17`-state consensus panel, frozen hidden states support strong low-complexity separability.

Key result:

- hidden states contain **pairwise progress-difference information**
- this is readable with weak probes
- it holds across **DeepSeek** and **Goedel**

Representative audited results:

DeepSeek:

- gap task linear AUROC: `0.9085`
- direction task linear AUROC: `0.9490`

Goedel:

- gap task linear AUROC: `0.8874`
- direction task linear AUROC: `0.9148`

This was the first hard positive result of the project:

> inside the model's competence regime, hidden states do carry usable progress information

At this point, the original object question was answered positively.

## 7. Method Gate: Can the Object Be Turned into a Learned Scorer?

After object-gate success, the next step was to learn an explicit pairwise progress scorer.

On the `17`-state consensus panel:

- a simple linear scorer already worked well
- more complex MLPs were not necessary to get a first positive result

Representative results:

DeepSeek linear:

- ordered pair accuracy: `0.9576`
- top1 max-tier hit rate: `1.0000`
- mean NDCG: `0.9974`

Goedel linear:

- ordered pair accuracy: `0.9488`
- top1 max-tier hit rate: `1.0000`
- mean NDCG: `0.9947`

The remaining weakness was not ordered-pair recovery, but calibration on equivalent candidates:

- same-tier candidates were often spread too far apart

Still, this phase established a clean minimum method claim:

> the object signal is not only probe-readable; it can also be turned into a learned pairwise scorer

## 8. The Hard-Domain Boundary: Putnam Changes the Picture

The next question was whether the same claim survives on truly hard states.

Earlier "hard" slices were not enough; they were still too close to the model's comfort zone.
So the project moved to a Putnam-based formal slice.

This changed the result qualitatively.

### 8.1 Cross-state latent separability collapses

On Putnam hard states:

- frozen hidden separability across states becomes unstable
- both coarse and fine cross-state ranking degrade sharply

This showed that the earlier positive object claim does **not** extrapolate unchanged into the genuinely hard regime.

### 8.2 But the latent object does not disappear

The next mechanism question was:

> Is the hard-domain latent object gone, or merely no longer globally aligned?

This was answered by splitting evaluation into:

- `cross-state`
- `within-state`

The result was the deepest finding of the project.

On Putnam:

- `within-state` latent ranking remains strong
- `cross-state` latent geometry collapses

So the right reading is:

- hard-domain latent signal is **not absent**
- it becomes **local and state-specific**
- what disappears is the **shared transferable geometry**

This is much stronger than simply saying "hard is harder".

## 9. What the Hard-Domain Latent Signal Seems to Be

At this stage the project stopped being mainly about raw metrics and became a mechanism study.

The current best interpretation is:

- on easy/medium states, latent geometry behaves like a shared progress geometry
- on hard states, latent geometry behaves more like **model-internal local affordance**

That means:

- the model still internally distinguishes better/worse local continuations within a given hard state
- but these local orderings do not line up into a global cross-state coordinate system

This distinction matters because it separates two different objects:

1. **external progress**
2. **model-relative local affordance**

The current evidence suggests that hard-domain latent structure is much closer to the second than the first.

## 10. Before Hidden vs After Hidden

Another key mechanism distinction is between:

- `before hidden`
- `after hidden`

Current picture:

- `after hidden` carries the strong **candidate-level local progress signal**
- `before hidden` carries a weaker but real **state-level competence / trust signal**

This means the model seems to encode two related but distinct objects:

1. local candidate preference after proposing a move
2. whether the current state is inside or outside the latent scorer's reliable regime

This second object became important later for gating.

## 11. Why External Judge Behaves Differently

On the same hard Putnam panel, an external after-state judge remained much more stable than frozen hidden states.

This was important for two reasons:

1. it showed the hard oracle was not inherently unjudgeable
2. it showed the latent failure was specifically a latent-geometry issue, not a panel-quality issue

Current reading:

- latent behaves like a **local, model-internal affordance geometry**
- judge behaves more like a **canonical cross-state progress scalar**

This is one of the project's most useful conceptual distinctions.

## 12. Trust Gating and Hybrid Use

Once the project established that:

- hard latent ranking fails globally
- `before hidden` partly predicts that failure

the next natural test was a hybrid:

- use latent local scoring when the state looks trustworthy
- fall back to judge when the state looks unreliable

This hybrid is scientifically secondary but still informative.

It showed:

- trust gating is real
- latent failure is partially predictable
- hybrid is better than latent-only
- but hard-side performance comes mainly from judge fallback, not from latent recovering hard ranking

So this line does **not** prove latent is a hard-domain substitute.
It only supports a system role where latent handles the easy/local part and trust decides when to escalate.

## 13. Feature Deepening on Hard States

One remaining question was whether the hard failure was mainly caused by poor feature choice.

The strongest tested variant used more goal-aligned features:

- proof-state aligned hidden means over `before_goals / after_goals`

This recovered part of the hard-domain picture:

- coarse cross-state `ordered vs equivalent` boundary improved substantially
- fine cross-state ranking direction did **not** recover

This result matters because it shows:

- feature choice matters
- but feature choice alone does not restore a canonical hard-domain ranking geometry

So the hard failure is not merely "wrong embedding choice".

## 14. Bottleneck Typing on Hard States

The next hypothesis was:

> maybe hard latent geometry is not globally shared, but can re-align inside coarse proof-bottleneck types

A first manual taxonomy was built over Putnam states:

- `structural_reduction`
- `algebraic_normalization`
- `setup_extraction`

Result:

- same-type prototype alignment did **not** reliably improve
- type-conditioned direction AUROC did **not** beat global prototypes
- same-type prototypes often anti-aligned

So the coarse bottleneck hypothesis failed.

This sharpened the hard-side conclusion again:

- hard latent geometry is not just "not global"
- it is also too local to be recovered by this coarse type grouping

At the current evidence level, the hard latent object looks closer to:

- **state-specific**
- or **micro-structure-specific**

than to any coarse reusable type-conditioned geometry.

## 15. Current Claim Hierarchy

### 15.1 Claims supported

#### Object claim

Within the model's competence regime, hidden states contain real pairwise progress-related information.

#### Audit claim

This signal survives:

- cleaner state-first data
- Lean legality filtering
- human oracle labeling
- second-annotator audit
- cross-model replication

#### Boundary claim

The signal is **competence-scoped**:

- easy/medium: shared latent progress geometry
- hard Putnam: local latent affordance remains, but shared cross-state geometry collapses

#### Secondary systems claim

`before hidden` contains a useful competence / trust signal that can support escalation decisions.

### 15.2 Claims only conditionally supported

#### Method claim

Latent pairwise progress scoring is learnable and useful inside the competence regime.

This is supported on the easy/medium audited panel, but not as a universal hard-domain method.

#### Hybrid systems claim

`latent + trust + judge fallback` can improve over latent-only and can be useful as a layered system design.

This is plausible and supported in mixed settings, but it is not the main scientific result.

### 15.3 Claims not supported

The project does **not** support any of the following strong claims:

- latent supervision is a universal replacement for external judging
- hard-domain latent progress is globally shared across states
- a single hard-domain global latent ranker exists with the current object/feature setup
- coarse proof-bottleneck typing is enough to recover hard shared geometry

## 16. What This Means for the Proposal

The original proposal should be rewritten.

The strongest defensible version is now:

1. process supervision should not be reduced to text-only judging
2. latent states do carry real progress-related structure
3. but that structure is **not universally canonical**
4. instead, it splits into:
   - a shared competence-regime progress geometry
   - a hard-domain local affordance geometry
   - a separate competence / trust signal in `before hidden`
5. external judging remains the more canonical hard-domain progress signal

This is a stronger and more precise proposal than the original universal latent-verifier story, because it has been forced through actual failure boundaries.

## 17. What the Project Should and Should Not Do Next

### 17.1 What should stop

These are no longer good mainline directions:

- more coarse taxonomy slicing
- more generic feature hunt
- more judge-cost-reduction micro-optimizations
- more attempts to rescue a universal hard latent ranker without a new object hypothesis

These now have low marginal value.

### 17.2 What is worth doing

Only two next-step directions now look high-value.

#### A. Proposal rewrite / claim formalization

Turn the current findings into a clean claim hierarchy and paper framing:

- object
- boundary
- mechanism
- system role

This is likely the highest-value next step.

#### B. Reopen experimentation only with a genuinely new object hypothesis

For example:

- token-slot aligned proof-state relations
- micro-structure objects below coarse bottleneck type
- a formalized notion of model-internal affordance

Without a new object hypothesis, more experimentation will mostly repeat the same conclusion.

## 18. Final Bottom Line

The project did **not** discover a universal latent progress judge.

What it discovered is more interesting:

- there is a real latent progress object
- it is strong and transferable inside the model's competence regime
- it localizes and loses global alignment on genuinely hard states
- what remains there is best understood as local affordance geometry, not canonical progress geometry
- `before hidden` separately tracks whether latent ranking should be trusted

The deepest current conclusion is therefore:

> latent process supervision is real, but it is competence-scoped; on hard states it becomes local rather than globally canonical.
