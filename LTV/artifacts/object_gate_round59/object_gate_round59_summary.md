## Round59: Putnam hard locality comes from state-specific affordance geometry, while the external judge behaves more like a cross-state canonical scalar

### Goal

Push beyond the round58 locality result and ask two mechanism questions on the same Putnam v1 hard panel:

1. What state structure lets `within-state` latent ordering survive?
2. Why does that local ordering fail to align across hard states, while the external after-state judge remains stable?

### Inputs

- Oracle panel: [data/annotations/state_first_progress_oracle_putnam_v1.jsonl](/cephfs/luyanzhen/apg/LTV/data/annotations/state_first_progress_oracle_putnam_v1.jsonl)
- Replayed candidates: [artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round55/state_first_putnam_candidates_v1_replayed.jsonl)
- Judge rows: [artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round56/putnam_v1_judge_rows.jsonl)
- Locality audit: [artifacts/object_gate_round58/deepseek_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/deepseek_putnam_locality.json), [artifacts/object_gate_round58/goedel_putnam_locality.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round58/goedel_putnam_locality.json)

### Method

For each Putnam hard state:

- build simple interpretable structure features:
  - before-goal length
  - candidate count
  - tier spread
  - tactic-family counts/entropy
  - replayed after-goal statistics
- compute a **state-local latent prototype**:
  - average `h_plus(better) - h_plus(worse)` over all ordered pairs in that state
- measure:
  - `within_mean_cos`: cosine of each ordered pair with its own state prototype
  - `global_mean_cos`: cosine of each ordered pair with the leave-one-state-out global prototype
  - `prototype_offdiag_mean_cos`: pairwise cosine between different states’ prototypes
- compare this to the external judge’s pairwise correctness and calibration across the same states

Outputs:

- [artifacts/object_gate_round59/deepseek_putnam_mechanism.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round59/deepseek_putnam_mechanism.json)
- [artifacts/object_gate_round59/goedel_putnam_mechanism.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round59/goedel_putnam_mechanism.json)

### Key results

#### 1. Cross-state latent prototypes are almost unaligned

DeepSeek:
- prototype off-diagonal mean cosine = `-0.0097`
- min/max off-diagonal cosine = `-0.3562 / 0.1236`

Goedel:
- prototype off-diagonal mean cosine = `-0.0161`
- min/max off-diagonal cosine = `-0.3791 / 0.2750`

Interpretation:
- hard-state latent ordering directions do **not** form a shared global axis
- the failure in round55/58 is not just low margin; the state-level ordering directions themselves are nearly orthogonal on average and sometimes anti-aligned

#### 2. Every state still has a real local affordance direction

For every state in both models:
- `prototype_within_mean_cos` stays clearly positive
- `prototype_global_mean_cos` is near `0` or negative

Representative DeepSeek examples:
- `putnam_1993_a4__sorry0`
  - within mean cosine = `0.9642`
  - global mean cosine = `-0.0226`
- `putnam_2013_b4__sorry2`
  - within = `0.8695`
  - global = `0.0021`
- `finite_diff_identity__sorry1`
  - within = `0.6113`
  - global = `-0.1210`

Representative Goedel examples:
- `putnam_1993_a4__sorry0`
  - within = `0.9545`
  - global = `-0.0186`
- `putnam_2013_b4__sorry3`
  - within = `0.9627`
  - global = `-0.1103`
- `putnam_1976_b5__sorry2`
  - within = `0.5547`
  - global = `-0.0770`

Interpretation:
- the hard-state latent object survives as a **state-local direction**
- what disappears is the ability to align these local directions into a transferable cross-state geometry

#### 3. Surface tactic diversity alone does not explain locality

Important counterexample:
- `coeff_X_sub_C_pow__sorry0`
  - `5` tactic families: `by_cases / rw / apply / have / simp`
  - still strong local latent ordering:
    - DeepSeek direction within AUROC = `1.0`
    - Goedel direction within AUROC = `1.0`

This matters because it rules out a shallow explanation like:
- “local latent only works when all tactics are surface-similar”

Instead, the stronger explanation is:
- local geometry survives when candidates all engage the **same local proof bottleneck**
- even if their surface forms differ

In `coeff_X_sub_C_pow__sorry0`, the local bottleneck is the conditional split around `m ≤ n`; diverse tactics still point toward the same local obstacle.

#### 4. Weaker local latent states are the ones mixing multiple incomparable local moves

States with weaker local latent ordering:
- `putnam_1976_b5__sorry3`
  - DeepSeek direction within AUROC = `0.8`
  - Goedel direction within AUROC = `0.44`
- `finite_diff_identity__sorry1`
  - local direction still separable, but prototype alignment is much weaker than simpler local-setup states

These states mix:
- structural rewrites
- algebra normalization
- auxiliary setup steps

Interpretation:
- when candidate moves do **not** orbit a single bottleneck, the local latent direction becomes less sharp
- so the right explanatory unit is not tactic family count alone, but whether the state induces a **single dominant affordance axis**

#### 5. The external judge behaves much more like a cross-state canonical scalar

Judge global behavior on the same Putnam panel:
- mean direction correct probability = `0.8115`
- mean gap correct probability = `0.7550`
- mean equivalent probability on true-equivalent pairs = `0.1611`

Judge direction correct probability rises monotonically with oracle tier gap:
- tier gap `1` -> `0.7985`
- tier gap `2` -> `0.8584`
- tier gap `3` -> `0.9000`

Statewise judge direction correct probability remains relatively stable:
- roughly `0.7345` to `0.8944`

Interpretation:
- judge outputs appear to live on a much more state-invariant scale
- unlike latent local prototypes, judge confidence tracks oracle tier distance across states instead of collapsing into state-specific directions

### Mechanism conclusion

The best current picture is:

1. Latent hard-state progress is **not absent**.
2. It survives as a **local, state-specific affordance geometry**.
3. Cross-state failure happens because these local directions do not align into a shared canonical coordinate system.
4. The external judge is stronger on hard states because it behaves more like a **cross-state canonical scalar**, with confidence that tracks oracle tier gaps across different states.

So the deeper contrast is:

- latent: `state-specific affordance geometry`
- judge: `cross-state canonical progress scale`

This is more precise than “latent works on easy states and fails on hard states.” The harder-domain failure is specifically a **geometry alignment failure**.
