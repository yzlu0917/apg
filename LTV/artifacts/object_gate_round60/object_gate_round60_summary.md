## Round60: Goal-aligned relational features partially recover hard cross-state geometry, but only at the coarse gap level

### Goal

Test whether a more local, proof-state-aligned representation works better on Putnam hard states than the current `h_plus` candidate representation.

Instead of using the hidden state at the end of the full proof prompt, build candidate features directly from the textual proof states:

- `goal_after_mean`
- `goal_delta_mean = mean(after_goals) - mean(before_goals)`
- `goal_concat_rel = [before_goal_mean ; after_goal_mean ; delta]`

All goal texts are encoded by mean-pooling hidden states over the standalone goal text.

### Files

- [scripts/evaluate_putnam_goal_features.py](/cephfs/luyanzhen/apg/LTV/scripts/evaluate_putnam_goal_features.py)
- [artifacts/object_gate_round60/deepseek_putnam_goal_features.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round60/deepseek_putnam_goal_features.json)
- [artifacts/object_gate_round60/goedel_putnam_goal_features.json](/cephfs/luyanzhen/apg/LTV/artifacts/object_gate_round60/goedel_putnam_goal_features.json)

### Results

Baseline from round55 / round58:

DeepSeek hard Putnam:
- `h_plus` gap cross linear AUROC = `0.3405`
- `h_plus` direction cross linear AUROC = `0.3502`

Goedel hard Putnam:
- `h_plus` gap cross linear AUROC = `0.3728`
- `h_plus` direction cross linear AUROC = `0.3007`

#### DeepSeek goal-aligned features

`goal_after_mean`
- gap cross linear AUROC = `0.6362`
- direction cross linear AUROC = `0.2425`
- gap within linear AUROC = `0.6774`
- direction within linear AUROC = `0.9807`

`goal_delta_mean`
- identical to `goal_after_mean` on this fixed-before protocol

`goal_concat_rel`
- gap cross linear AUROC = `0.6362`
- direction cross linear AUROC = `0.4527`
- gap within linear AUROC = `0.6882`
- direction within linear AUROC = `0.9355`

#### Goedel goal-aligned features

`goal_after_mean`
- gap cross linear AUROC = `0.6487`
- direction cross linear AUROC = `0.2950`
- gap within linear AUROC = `0.7348`
- direction within linear AUROC = `0.9584`

`goal_delta_mean`
- identical to `goal_after_mean` on this fixed-before protocol

`goal_concat_rel`
- gap cross linear AUROC = `0.6452`
- direction cross linear AUROC = `0.3970`
- gap within linear AUROC = `0.7115`
- direction within linear AUROC = `0.9667`

### Interpretation

This is a meaningful change in the mechanism picture.

#### 1. Goal-aligned features recover **coarse cross-state geometry**

On both DeepSeek and Goedel, the gap task jumps from:
- roughly `0.34 / 0.37`
to
- roughly `0.64 / 0.65`

So once the representation is anchored to proof-state text directly, a substantial cross-state signal reappears for:
- `ordered` vs `equivalent`

This suggests that some of the missing global structure was not entirely absent; it was obscured by using a feature that was too tied to the full proof prompt trajectory.

#### 2. But they still do **not** recover a cross-state canonical direction

Direction remains poor:
- DeepSeek: `0.24` to `0.45`
- Goedel: `0.29` to `0.40`

So these features recover:
- a cross-state notion of “does this candidate change the proof state in a meaningful way?”

but not:
- a stable global direction of “which candidate is better?”

That means the hard-domain failure is not just about choosing the wrong feature family; even proof-state-aligned features still fail to produce a fully transferable ranking geometry.

#### 3. This sharpens the latent vs judge contrast

Current best reading:
- latent `h_plus`: very local, state-specific affordance geometry
- goal-aligned relational features: recover a **coarse cross-state progress boundary**
- external judge: still the only signal that stays strong on the full cross-state **direction** task

So the emerging hierarchy is:

1. local latent geometry
2. proof-state-aligned coarse cross-state geometry
3. judge-like canonical cross-state ranking geometry

### Conclusion

Goal-aligned relational features **do help** on hard Putnam states, but only partially.

They show that the cross-state collapse was not absolute:
- there is recoverable coarse structure at the proof-state text level

But they do **not** rescue the full hard-state ranking problem:
- the fine-grained cross-state direction signal still does not become stable

So the deeper conclusion becomes:

**hard Putnam does not destroy all shared structure; it destroys the strongest, ranking-level shared geometry first.**
