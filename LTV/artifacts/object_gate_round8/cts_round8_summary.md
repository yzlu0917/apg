# CTS Round8 Summary

Round8 isolates `reflexivity_style` into a dedicated control slice. The goal is to determine whether the remaining same-side failure is mainly caused by:

- pure format change
- proof-keyword substitution
- target-term binding

This round reuses the round7 feature store and does not expand the main Lean source base.

## Control design

- total rows: `13`
- same pairs: `9`
- flip pairs: `4`

Same-side rows are balanced across three subfamilies:

- `reflexivity_pure_format = 3`
- `reflexivity_proof_keyword = 3`
- `reflexivity_target_term = 3`

Flip-side rows are all `wrong_target_term`.

## Main result

Overall on this dedicated control:

- `transition_only`: `IG = 0.9943`, `SS = 1.0000`
- `post_state_only`: `IG = 0.5556`, `SS = 0.9456`
- `concat_all`: `IG = 0.5556`, `SS = 1.0000`
- `text_only`: `IG = 0.6682`, `SS = 0.9981`

This is a strong negative result for same-side invariance.

## Subfamily reading

For `transition_only`:

- `reflexivity_pure_format`: `IG = 0.9830`
- `reflexivity_proof_keyword`: `IG = 1.0000`
- `reflexivity_target_term`: `IG = 1.0000`

Interpretation:

- The failure is **not** limited to explicit target-term binding.
- Even pure format-only wrapping such as `rfl -> exact rfl` is enough to break transition stability.
- So the remaining issue is better explained as a representation-level instability around reflexivity-style steps, not merely a missing rewrite family.

## Claim impact

Round8 materially sharpens the claim boundary.

- Supported:
  - `transition_only` remains highly sensitive to `wrong_target_term` flips.
- Not supported:
  - `transition_only` as a stable semantic invariant for reflexivity-style same rewrites.

This means the current same-side bottleneck is no longer best framed as a simple coverage gap.

## Gate reading

- `Object gate`: partial support only
- `Audit gate`: still not passed

## Best next move

The strongest next step is not more generic expansion.

1. Treat `reflexivity_style` as a hard negative / diagnosis branch.
2. Narrow the object claim to the families where transition evidence is stable.
3. Only reopen this branch if there is a thesis-level new representation idea, rather than another round of rewrite accumulation.
