## Round64: A minimal bottleneck taxonomy does not restore shared hard-state latent geometry

### Goal

Test the strongest remaining mechanism hypothesis from rounds 58–60:

> On hard Putnam states, maybe latent progress geometry is not completely unshareable; maybe it aligns again once states are grouped by proof bottleneck type.

This round asks whether a small manual taxonomy can recover any meaningful **type-conditioned shared geometry**.

### Bottleneck Taxonomy

Typing file:
- [putnam_bottleneck_types_v0.json](/cephfs/luyanzhen/apg/LTV/configs/object_gate/putnam_bottleneck_types_v0.json)

Types:
- `structural_reduction`
  - `coeff_X_sub_C_pow__sorry0`
  - `putnam_1976_b5__sorry3`
  - `putnam_2013_b4__sorry2`
- `algebraic_normalization`
  - `finite_diff_identity__sorry1`
  - `putnam_1976_b5__sorry2`
  - `putnam_2013_b4__sorry3`
- `setup_extraction`
  - `putnam_1993_a4__sorry0`

The singleton `setup_extraction` type is retained for completeness, but no type-level alignment claim is based on it.

### Method

Implementation:
- [analyze_putnam_bottleneck_types.py](/cephfs/luyanzhen/apg/LTV/scripts/analyze_putnam_bottleneck_types.py)

Outputs:
- [deepseek_putnam_bottleneck_types.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round64/deepseek_putnam_bottleneck_types.json)
- [goedel_putnam_bottleneck_types.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round64/goedel_putnam_bottleneck_types.json)

For each state:
1. build its latent `better-minus-worse` prototype from `h_plus`
2. compare its ordered-pair diffs against:
   - the mean prototype of same-type peers
   - the mean prototype of all other states
   - the mean prototype of only other-type states
3. report:
   - type-conditioned direction AUROC
   - global direction AUROC
   - type-conditioned cosine alignment
   - global cosine alignment

This is a direct test of whether bottleneck conditioning restores cross-state latent directionality.

### Results

#### Prototype alignment overview

DeepSeek:
- within-type off-diagonal prototype cosine = `-0.0414`
- cross-type off-diagonal prototype cosine = `0.0030`

Goedel:
- within-type off-diagonal prototype cosine = `-0.0502`
- cross-type off-diagonal prototype cosine = `-0.0024`

So type-conditioned prototypes do **not** become more aligned than the global pool.

#### DeepSeek type summaries

`algebraic_normalization`:
- mean same-type direction AUROC = `0.2170`
- mean global direction AUROC = `0.4022`
- mean same-vs-global AUC gain = `-0.1852`
- mean same-type cosine = `-0.1218`
- mean global cosine = `-0.0459`

`structural_reduction`:
- mean same-type direction AUROC = `0.5056`
- mean global direction AUROC = `0.7885`
- mean same-vs-global AUC gain = `-0.2829`
- mean same-type cosine = `0.0240`
- mean global cosine = `0.0187`

#### Goedel type summaries

`algebraic_normalization`:
- mean same-type direction AUROC = `0.1141`
- mean global direction AUROC = `0.2044`
- mean same-vs-global AUC gain = `-0.0904`
- mean same-type cosine = `-0.1782`
- mean global cosine = `-0.0914`

`structural_reduction`:
- mean same-type direction AUROC = `0.6022`
- mean global direction AUROC = `0.7918`
- mean same-vs-global AUC gain = `-0.1896`
- mean same-type cosine = `0.0528`
- mean global cosine = `0.0436`

#### Per-state pattern

There are isolated states where same-type conditioning helps:

DeepSeek:
- `coeff_X_sub_C_pow__sorry0`: same-type AUC `0.8367` vs global `0.7755`
- `putnam_1976_b5__sorry2`: same-type AUC `0.6111` vs global `0.4167`

Goedel:
- `coeff_X_sub_C_pow__sorry0`: same-type AUC `0.8367` vs global `0.7755`
- `putnam_1976_b5__sorry3`: same-type AUC `0.7200` vs global `0.6000`

But these gains do not persist at the type level:
- some same-type peers help
- others actively anti-align

#### Judge by type

External judge remains relatively stable across types:

- `algebraic_normalization`: mean direction correct prob = `0.7641`
- `setup_extraction`: `0.7778`
- `structural_reduction`: `0.8650`

So the judge does not show the same kind of type-conditioned collapse.

### Interpretation

This round is a negative mechanism result, but a useful one.

#### 1. Hard-state locality is finer than this bottleneck taxonomy

The main hypothesis was:
- hard states might fail globally
- but re-align once grouped by bottleneck type

That is **not** what we see.

The smallest useful reading is:
- some states have compatible peers
- but the shared latent geometry does not stabilize even at this type granularity

#### 2. The local object is more specific than “proof bottleneck type”

By round59 we already knew that hard latent geometry was local.
Round64 sharpens this:

It is not merely:
- `state-type local`

It is closer to:
- **state-specific** or **micro-structure-specific**

In other words, the hard latent object seems to depend on a finer configuration than this coarse bottleneck grouping can capture.

#### 3. Judge remains more canonical even after typing

The external judge continues to behave like a cross-state scalar across all these groups.

So round64 strengthens the asymmetry:
- latent = local affordance geometry
- judge = more canonical progress geometry

### Conclusion

Round64 does **not** rescue hard-state shared latent geometry through a minimal bottleneck taxonomy.

So the current strongest reading becomes:

**hard Putnam latent geometry is not just globally misaligned; it remains too local even after a coarse bottleneck grouping.**

This pushes the picture one step further:
- easy/medium: shared latent progress geometry
- hard: local affordance geometry
- hard typed by coarse bottleneck: still not enough to recover shared latent ranking geometry
