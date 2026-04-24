# CTS Round9 Summary

Round9 is a scoring audit on the fixed round8 reflexivity control. It does not change data, features, or model family. It only changes how the same latent representation is mapped to scores.

## Why this round matters

Round8 suggested a very strong negative result on `reflexivity_style`, but that conclusion depended on a single scorer:

- linear probe
- sigmoid probability

Round9 tests whether the failure survives under alternative scoring rules.

## Compared scorers

On both `post-state` and `transition` representations, round9 compares:

- `linear_prob`
- `linear_logit_z`
- `mlp_prob`
- `centroid_cosine`

## Main result

For `transition` on the same fixed round8 control:

- `transition_linear_prob`
  - `IG = 0.7778`
  - `SS = 1.0000`
- `transition_linear_logit_z`
  - `IG = 0.5722`
  - `SS = 2.7894`
- `transition_centroid_cosine`
  - `IG = 0.2896`
  - `SS = 0.5918`
- `transition_mlp_prob`
  - `IG = 0.0444`
  - `SS = 1.0000`

This is the key round9 finding:

- the severe round8 failure does **not** survive a scorer audit.
- scorer choice materially changes the reflexivity conclusion.

## Subfamily reading

For `transition_mlp_prob`:

- `reflexivity_pure_format`
  - `IG = 0.0000`
- `reflexivity_proof_keyword`
  - `IG = 0.1136`
- `reflexivity_target_term`
  - `IG = 0.0196`

Compared with round8 `transition_only`:

- `pure_format`
  - round8: `0.9830`
  - round9 MLP: `0.0000`
- `proof_keyword`
  - round8: `1.0000`
  - round9 MLP: `0.1136`
- `target_term`
  - round8: `1.0000`
  - round9 MLP: `0.0196`

So the dominant failure mode in round8 was not simply “transition representations cannot support reflexivity invariance.” It was strongly entangled with the scorer.

## Interpretation

Round9 does **not** prove that the object claim is now solved.

What it does show is:

- the previous hard-negative reading for `reflexivity_style` was too strong;
- `transition` features can support good reflexivity behavior under a better scorer;
- the mapping layer is a first-order design choice, not a minor implementation detail.

## Updated claim boundary

- Supported:
  - scorer choice can dominate same-side behavior on the fixed reflexivity control
  - `transition` representations remain viable after scorer audit
- Still not supported:
  - a strong claim that current LTV-style object identification has already passed `Audit gate`

## Best next move

1. Re-run the broader same-family panel with `mlp_prob` and one geometry scorer.
2. Check whether the round9 rescue generalizes beyond reflexivity control.
3. Only after that decide whether the project should reopen same-side claims more broadly.
