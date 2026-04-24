## Round58 Summary

### Goal

Test a more fundamental mechanism hypothesis on the Putnam hard slice:

> Does latent progress signal disappear entirely on hard states, or does it remain locally within a state while losing cross-state geometry?

### Protocol

Use the same Putnam v1 panel as round55:
- `7` states
- `27` replay-ok candidates
- `40` gap pairs
- `62` direction examples

Then compare two evaluation modes on the same features:

1. **cross-state**
   - leave-one-state-out
   - asks whether a shared geometry transfers across hard states

2. **within-state**
   - leave-one-pair-out inside each state
   - for direction, both orientations of the same candidate pair are held out together to avoid leakage
   - asks whether a local state-specific ranking signal still exists

Implementation:
- [analyze_state_first_locality.py](/cephfs/luyanzhen/apg/LTV/scripts/analyze_state_first_locality.py)

Outputs:
- [deepseek_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/deepseek_putnam_locality.json)
- [goedel_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/goedel_putnam_locality.json)

### Results

#### DeepSeek

Gap:
- cross linear AUROC = `0.3405`
- within linear AUROC = `0.7796`
- cross centroid AUROC = `0.1989`
- within centroid AUROC = `0.7455`

Direction:
- cross linear AUROC = `0.3502`
- within linear AUROC = `0.9355`
- cross centroid AUROC = `0.4984`
- within centroid AUROC = `0.9865`

#### Goedel

Gap:
- cross linear AUROC = `0.3728`
- within linear AUROC = `0.7186`
- cross centroid AUROC = `0.2330`
- within centroid AUROC = `0.6918`

Direction:
- cross linear AUROC = `0.3007`
- within linear AUROC = `0.8824`
- cross centroid AUROC = `0.5463`
- within centroid AUROC = `0.9740`

### Interpretation

This is the strongest mechanism result so far on the hard slice.

The Putnam failure is **not**:
- "latent has no progress object at all on hard states"

It is much closer to:
- "latent still carries a strong **local, within-state** progress ordering signal"
- "but that signal no longer organizes into a stable **cross-state** geometry"

So the hard-domain boundary is more precise than in round55:

- round55 said: hard Putnam breaks cross-state separability
- round58 adds: the object is still present locally; what fails is transfer / shared geometry

### Claim Update

Current best object-level reading:

1. easy-to-medium states:
   - latent progress signal is present and transferable
2. hard Putnam states:
   - latent progress signal is still locally readable
   - but cross-state generalization collapses

This favors a stronger conceptual distinction:

- **local internal affordance / local progress geometry**
- versus
- **shared transferable progress geometry**

The former survives farther into the hard regime than the latter.

### Why This Matters

This is more fundamental than a routing story.

It suggests the hard failure is not simply “the model knows nothing”:
- the model still organizes candidates meaningfully inside a given state
- but those local orderings do not align into one reusable global latent axis across harder states

### Next Step

Most useful next moves are now:
- analyze what state-specific structure those local orderings depend on, or
- test whether external judge agreement is closer to within-state latent than to cross-state latent

Do **not** jump straight to recipe sweep; the more interesting question is now geometric locality.
