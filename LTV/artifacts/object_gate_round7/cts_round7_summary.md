# CTS Round7 Summary

Round7 was a targeted same-family expansion. It did not add new flip families. The goal was to test whether harder manual same rewrites could reduce the current invariance bottleneck without changing the broader Object/Audit framing.

## What changed

- Lean source base expanded from `32` records / `62` steps / `13` negative steps to `40` records / `79` steps / `13` negative steps.
- Added `8` manual curated same-semantics rows, targeting:
  - `reflexivity_style`
  - `projection_style`
  - `other_same_rewrite`
- Built:
  - `data/cts/cts_mini_v0_round7_manual_only.jsonl`
  - `data/cts/cts_mini_v0_auto_panel_round7_seed.jsonl`

## Main results

### Manual-only round7 slice

This slice is intentionally harsh on same-side stability.

- `transition_only`: `IG = 0.7500`, `SS = 0.7867`
- `post_state_only`: `IG = 0.5000`, `SS = 1.0000`
- `concat_all`: `IG = 0.4167`, `SS = 0.7500`

Interpretation:

- The newly added hard same rows did **not** rescue `transition_only`.
- On the manual-only round7 slice, `transition_only` remains highly flip-sensitive, but still behaves poorly as an invariant representation.

### Full auto panel round7

- `transition_only`: `IG = 0.3127`, `SS = 0.7145`
- `concat_all`: `IG = 0.2979`, `SS = 0.6071`
- `post_state_only`: `IG = 0.3813`, `SS = 0.6429`

Compared with round6:

- `transition_only` overall `IG` improved slightly:
  - round6: `0.3426`
  - round7: `0.3127`
- but overall `SS` weakened:
  - round6: `0.8057`
  - round7: `0.7145`

So round7 helps a bit on same-side aggregate, but not enough to change the gate reading.

## Family-level reading

For `transition_only` on the full panel:

- `projection_style` improved:
  - round6: `IG = 0.2500`
  - round7: `IG = 0.0467`
- `other_same_rewrite` improved:
  - round6: `IG = 0.5000`
  - round7: `IG = 0.3439`
- `reflexivity_style` worsened:
  - round6: `IG = 0.8845`
  - round7: `IG = 0.9982`

This is the core round7 result:

- `projection_style` is no longer the main problem.
- `other_same_rewrite` is somewhat better but still unstable.
- `reflexivity_style` remains the clearest hard failure family.

## Current claim boundary

Round7 does **not** support upgrading the claim.

- Supported:
  - `transition_only` still behaves like a useful failure-sensitive representation across several flip families.
- Not supported:
  - `transition_only` as a robust semantic invariant across hard same rewrites.
- Gate reading:
  - `Object gate`: partial support
  - `Audit gate`: still not passed

## Best next step

The next useful move is no longer generic data expansion.

1. Isolate `reflexivity_style` into a dedicated control slice.
2. Separate:
   - token/format shift
   - target-term substitution
   - proof-keyword substitution
3. If `transition_only` still fails there, treat this as evidence of a representation limit rather than a mere coverage gap.
