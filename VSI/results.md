# Results

## 2026-03-31

### Object gate bootstrap

Status:

- `GO` on the toy bootstrap slice

Command:

```bash
python scripts/object_gate_bootstrap.py \
  --config configs/object_gate_microbench.json \
  --out artifacts/object_gate/bootstrap_summary.json
```

Outputs:

- `artifacts/object_gate/bootstrap_summary.json`

Key observations:

- matched difficulty proxy across all four families: `trajectory_length=6`, `branching_factor=2`, `search_space_proxy=64`
- horizon separation: `early_cert=0.167` vs `delayed_cert=1.000`, gap `0.833`
- ambiguity separation: `rewrite_ambiguity=0.750`, gap `0.750`
- exploitability separation: `partial_test_exploit=1.000`, gap `1.000`
- bootstrap decision: `GO`

Interpretation:

- the measurement object is separable from the matched coarse-difficulty proxy on the current toy slice
- this is enough to proceed with controlled generator construction and Audit-gate probes

Caveats:

- this bootstrap uses fixed toy families, not real generators
- no training, routing, or transfer claim has been tested
- the result only supports continuing the Object gate; it does not close Audit, Conversion, or Scale

### Hybrid object smoke test

Status:

- `PASS` as a model-in-the-loop smoke test

Command:

```bash
conda run -n infer python scripts/hybrid_object_gate.py \
  --config configs/hybrid_object_gate.json \
  --out artifacts/object_gate/hybrid_smoke.json
```

Outputs:

- `artifacts/object_gate/hybrid_smoke.json`

Key observations:

- local `Qwen3-4B` loaded successfully in non-thinking mode
- model generated three correct but non-canonical reasoning traces for the same arithmetic problem
- canonical weak verifier rejected all three correct rewrites, yielding `ambiguity_score=1.0`
- model weak judge accepted all three correct rewrites, so current `judge_disagreement=0.0`
- exploit search did not yet find a wrong-but-high-scoring trajectory, so current `exploitability_score=0.0`

Interpretation:

- the hybrid path is viable: the model can now serve as rewrite generator and weak judge while strong verification remains objective
- ambiguity is already a live signal in a model-generated setting, so the project has moved beyond a purely hand-written toy bootstrap
- exploitability is not established yet; the next step is to strengthen the exploit search task rather than claim this axis works

Caveats:

- this is a single-problem smoke test, not a benchmark result
- the ambiguity signal currently depends on a canonical weak verifier; it still needs verifier-swap and rewrite-robustness audit
- exploitability remains unresolved on this first prompt/task pair

### Hybrid API smoke test

Status:

- `PASS` as an API-backed model-in-the-loop smoke test

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/hybrid_object_gate.py \
  --config configs/hybrid_object_gate_api.json \
  --out artifacts/object_gate/hybrid_api_smoke.json
```

Outputs:

- `artifacts/object_gate/hybrid_api_smoke.json`

Key observations:

- OpenAI-compatible API path worked against the provided endpoint
- the API run reproduced the same qualitative result as the local run: `ambiguity_score=1.0`, `judge_disagreement=0.0`, `exploitability_score=0.0`
- total API usage for this smoke test was `2041` tokens across `10` calls
- the API judge remained permissive on correct non-canonical rewrites, but exploit search still failed to produce a wrong high-scoring candidate

Interpretation:

- the project now has both local and API-backed hybrid paths
- ambiguity remains the first live object signal under both providers
- exploitability still needs a better task construction; the current arithmetic prompt is too clean and too easy for the exploit objective

Caveats:

- this still measures only a single problem, not a generated family
- no pricing claim is recorded here; only token usage is logged
- API strength helps generation quality, but does not by itself validate the `E` axis

### Hybrid API family smoke test

Status:

- `PASS` on a 3-problem mini-family

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/hybrid_object_family.py \
  --config configs/hybrid_object_family_api.json \
  --out artifacts/object_gate/hybrid_api_family.json
```

Outputs:

- `artifacts/object_gate/hybrid_api_family.json`

Key observations:

- mini-family size: `3` problems
- `avg_surface_ambiguity=1.0`
- `avg_semantic_ambiguity=0.778`
- `avg_judge_disagreement=0.0`
- `max_exploitability=0.0`
- `object_signal_alive_rate=1.0`
- total API usage: `6172` tokens across `30` calls

Interpretation:

- the surface-form ambiguity signal is now stable across a small API-backed family, not just one prompt
- the current weak judge consistently accepts correct non-canonical rewrites, while the canonical verifier rejects them; this makes `A` a live and repeatable object signal
- the bottleneck has shifted: the immediate next risk is not whether `A` exists, but whether `E` can be elicited in a non-toy setting and whether `A` survives audit probes

Caveats:

- this is still a mini-family, not a frozen benchmark slice
- all three problems are arithmetic-style and structurally similar
- exploitability remains unresolved, so the `E` axis is still not supported by the hybrid study

### Rewrite Audit

Status:

- `PARTIAL PASS` for `A`: survives audit, but is sensitive to weak-verifier choice and rewrite style

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/rewrite_audit.py \
  --config configs/rewrite_audit_api.json \
  --out artifacts/object_gate/rewrite_audit_api.json
```

Outputs:

- `artifacts/object_gate/rewrite_audit_api.json`

Key observations:

- `narrative` rewrites: `avg_surface_ambiguity=1.0`, `avg_semantic_ambiguity=0.778`, `avg_judge_disagreement=0.111`
- `equation` rewrites: `avg_surface_ambiguity=0.667`, `avg_semantic_ambiguity=0.444`, `avg_judge_disagreement=0.0`
- total API usage: `3972 + 3638 = 7610` tokens across `36` calls

Interpretation:

- the current ambiguity signal does not disappear under prompt variation, so `A_surface` is not purely a one-prompt artifact
- however, the drop from `A_surface` to `A_semantic` shows that a meaningful portion of the current signal is caused by canonicalization choice
- this confirms the split into `surface-form ambiguity` and `semantic ambiguity` rather than treating ambiguity as a single scalar

Caveats:

- this audit still uses arithmetic-style problems only
- the model weak judge stayed permissive across all variants, so verifier-swap evidence is still one-sided
- this is enough to block naive overclaiming, not enough to close Audit

### Exploitability Code Tasks

Status:

- `PASS` for first non-toy `E` signal

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_api.json \
  --out artifacts/object_gate/exploit_code_tasks_api.json
```

Outputs:

- `artifacts/object_gate/exploit_code_tasks_api.json`

Key observations:

- aggregate: `max_exploit_gap=1.0`, `avg_best_exploit_gap=0.8`, `tasks_with_exploit=4/5`
- verifier-swap aggregate: `max_judge_gap=1.0`, `avg_best_judge_gap=0.6`, `tasks_with_judge_gap=3/5`
- total API usage: `7351` tokens across `40` calls
- on `poly_rule`, one candidate explicitly overfit visible tests with lookup code:
  `def solve(x): return [2,5,10][x-1]`
- that candidate achieved `visible_score=1.0` and `hidden_score=0.0`, giving `exploit_gap=1.0`

Interpretation:

- the `E` axis now has a clean model-in-the-loop family with objective weak/strong verification
- this is much closer to the intended weak-verifier exploit story than the earlier arithmetic prompt
- the exploitability branch has moved past a single anecdote and now behaves like a real small family
- verifier swap matters: some tasks are exploitable under visible-test weak verification but not under the model judge, so `E` is weak-verifier dependent rather than a single scalar property of the task alone

Caveats:

- the task family is still small and intentionally favorable to overfitting
- this supports existence of `E`, not yet a calibrated estimate of how common it is

### String Ambiguity Family

Status:

- `PASS` for a first non-arithmetic ambiguity family

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/string_ambiguity_family.py \
  --config configs/string_ambiguity_family_api.json \
  --out artifacts/object_gate/string_ambiguity_family_api.json
```

Outputs:

- `artifacts/object_gate/string_ambiguity_family_api.json`

Key observations:

- aggregate: `avg_surface_ambiguity=1.0`, `avg_semantic_ambiguity=0.667`
- `tasks_with_surface_ambiguity=3/3`
- `tasks_with_semantic_ambiguity=2/3`
- total API usage: `971` tokens across `3` calls

Interpretation:

- `A` no longer depends only on arithmetic-style traces; a non-arithmetic string-transformation family also exhibits strong surface ambiguity
- semantic ambiguity is lower than surface ambiguity but still present on part of the family, which supports keeping the `A_surface / A_semantic` split
- this reduces the risk that the current object is merely an artifact of arithmetic phrasing

Caveats:

- the family is still small and uses short deterministic transformations
- semantic ambiguity here is sensitive to step-format compliance, so this remains an audit-oriented family rather than a final benchmark slice

### Large String Ambiguity Family

Status:

- `PASS` on a 12-task generated family

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/string_ambiguity_family.py \
  --config configs/string_ambiguity_family_large_api.json \
  --out artifacts/object_gate/string_ambiguity_family_large_api.json
```

Outputs:

- `artifacts/object_gate/string_ambiguity_family_large_api.json`

Key observations:

- sample size: `12` tasks
- `avg_surface_ambiguity=1.0`
- `avg_semantic_ambiguity=0.833`
- `tasks_with_surface_ambiguity=12/12`
- `tasks_with_semantic_ambiguity=10/12`
- total API usage: `4030` tokens across `12` calls

Interpretation:

- the non-arithmetic ambiguity signal survives when the family is expanded from `3` to `12` tasks
- semantic ambiguity remains lower than surface ambiguity, but the gap does not collapse with larger sample size
- this is the first point where the ambiguity side has a meaningful sample count rather than a pure smoke-test scale

Caveats:

- the family is still generator-based and structurally simple
- one API call per task means this is breadth-first evidence, not robustness under heavy resampling

### Large Exploitability Code Family

Status:

- `PASS` on a 12-task generated family

Command:

```bash
VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/exploit_code_tasks_large_api.json
```

Outputs:

- `artifacts/object_gate/exploit_code_tasks_large_api.json`

Key observations:

- sample size: `12` tasks
- objective weak verifier: `tasks_with_exploit=10/12`, `avg_best_exploit_gap=0.75`
- model-judge weak verifier: `tasks_with_judge_gap=5/12`, `avg_best_judge_gap=0.417`
- total API usage: `12692` tokens across `72` calls

Interpretation:

- exploitability remains strong at a larger sample size instead of collapsing after a few hand-picked tasks
- verifier swap still changes the picture materially, which strengthens the claim that `E` is a task-and-verifier interaction rather than a single scalar
- this is now large enough to justify reporting exploitability as a family-level phenomenon in phase 0

Caveats:

- the generator still favors low-entropy hidden rules that are easy to overfit
- this is still an audit family, not yet a publication-ready benchmark

### Frozen Slice Summary

Status:

- frozen dev/final split recorded and summarized

Command:

```bash
python scripts/summarize_frozen_slices.py \
  --slices configs/frozen_slices_phase0.json \
  --string-artifact artifacts/object_gate/string_ambiguity_family_large_api.json \
  --exploit-artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/frozen_slices_summary.json
```

Outputs:

- `configs/frozen_slices_phase0.json`
- `artifacts/object_gate/frozen_slices_summary.json`

Key observations:

- string ambiguity dev/final:
  `dev A_surface=1.0, A_semantic=1.0`
  `final A_surface=1.0, A_semantic=0.667`
- exploit family dev/final:
  `dev avg_exploit_gap=0.722, avg_judge_gap=0.333`
  `final avg_exploit_gap=0.778, avg_judge_gap=0.5`

Interpretation:

- the final slice is not collapsing relative to the dev slice, which is the main thing needed at phase 0
- the split is now frozen enough to support a first minimal conversion protocol without silently changing evaluation boundaries later

Caveats:

- this is still the first frozen split and may need revision if family definitions change materially

### Conversion: String Ambiguity Routing

Status:

- `NO_GO` for now

Command:

```bash
python scripts/conversion_string_ambiguity.py \
  --config configs/conversion_string_ambiguity.json \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/string_ambiguity_family_large_api.json \
  --out artifacts/object_gate/conversion_string_ambiguity.json
```

Outputs:

- `artifacts/object_gate/conversion_string_ambiguity.json`

Key observations:

- dev-learned routing chose `surface` for all three templates because dev semantic acceptance did not beat surface
- final results:
  `always_surface accepted_correct=0/6, utility_per_cost=0.0`
  `always_semantic accepted_correct=2/6, utility_per_cost=0.167`
  `routed accepted_correct=0/6, utility_per_cost=0.0`

Interpretation:

- the current ambiguity object is real, but the present routing rule does not convert it into decision gain on the frozen split
- this is a clean negative for the first conversion attempt, not a reason to reopen the object claim
- the likely issue is that the current semantic acceptance criterion is still too brittle to support template-level routing

Caveats:

- this protocol is intentionally minimal and uses only one handcrafted routing rule
- a negative result here does not rule out conversion entirely; it rules out this first routing recipe

### Conversion: Exploit Routing

Status:

- `NO_GO` for now

Command:

```bash
python scripts/conversion_exploit_routing.py \
  --config configs/conversion_exploit_routing.json \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_routing.json
```

Outputs:

- `artifacts/object_gate/conversion_exploit_routing.json`

Key observations:

- selected threshold from dev: `1.0`
- final results:
  `always_visible avg_hidden_score=0.667, utility_per_cost=0.667`
  `always_judge avg_hidden_score=0.667, utility_per_cost=0.333`
  `routed avg_hidden_score=0.667, utility_per_cost=0.333`

Interpretation:

- the current exploit object is measurable and audit-relevant, but this first threshold-routing recipe does not outperform the cheap visible verifier baseline
- this is the right point to stop and record a clean negative rather than force a story
- the conversion bottleneck is not lack of object signal; it is that the current routing policy fails to monetize that signal

Caveats:

- the current route uses one coarse threshold over weak-signal disagreement; richer routing could still work
- this is a minimal decision protocol, not a training-based conversion study

### Conversion: Exploit Alternatives

Status:

- `NO_GO` again

Command:

```bash
python scripts/conversion_exploit_alternatives.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_alternatives.json
```

Outputs:

- `artifacts/object_gate/conversion_exploit_alternatives.json`

Key observations:

- dev-selected `rerank` penalty: `alpha=0.0`
- dev-selected `abstain` threshold: `0.0`
- final rerank:
  `avg_hidden_score=0.667`, `utility_per_cost=0.333`
- final abstain:
  `coverage=0.0`, `avg_hidden_score_over_all=0.0`, `utility_per_cost=0.0`

Interpretation:

- attempt-level reranking still does not beat the cheap visible baseline
- abstention looked superficially promising on the dev slice, but it does not transfer at all to the frozen final slice
- this is now a second clean negative for conversion, which makes it hard to justify continued local recipe tweaking without a real redesign

Caveats:

- these are still lightweight decision rules, not training-based interventions
- the negative here does not refute the object; it refutes these specific conversion recipes

### Conversion: Exploit Learned Risk Model

Status:

- `NO_GO` again

Command:

```bash
python scripts/conversion_exploit_learned.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_learned.json
```

Outputs:

- `artifacts/object_gate/conversion_exploit_learned.json`

Key observations:

- learned weights put strong positive weight on `judge_score` and strong negative weight on `disagreement`
- dev:
  `avg_hidden_score=0.667`, `utility_per_cost=0.333`
- final:
  `avg_hidden_score=0.333`, `utility_per_cost=0.167`

Interpretation:

- a tiny learned risk model still fails to convert the object signal into a useful frozen-slice policy
- the drop from dev to final suggests the current feature set overfits the dev slice structure instead of capturing a stable transfer signal
- this is now evidence against the idea that a simple learned risk model is enough

Caveats:

- this is deliberately minimal and uses only a few handcrafted features
- it is still not a training-based policy over model behavior, only over verifier signals

### Conversion: Exploit Agreement Filter

Status:

- `NO_GO` again

Command:

```bash
python scripts/conversion_exploit_agreement.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_agreement.json
```

Outputs:

- `artifacts/object_gate/conversion_exploit_agreement.json`

Key observations:

- selected agreement threshold from dev: `0.5`
- dev:
  `coverage=0.667`, `avg_hidden_score_over_all=0.667`
- final:
  `coverage=0.667`, `avg_hidden_score_over_all=0.333`, `avg_hidden_score_over_accepted=0.5`

Interpretation:

- even when visible and judge weak verifiers agree, that agreement is not strong enough to guarantee good hidden performance on the final slice
- this weakens the hope that a simple agreement-based filter can rescue the method story
- the conversion bottleneck now looks structural rather than just a poor threshold choice

Caveats:

- this is still an inference-time filter, not a learned verifier or post-training intervention

### Conversion: Trained Exploit Verifier

Status:

- `NO_GO` for conversion, but more stable than prior heuristics

Command:

```bash
conda run -n infer python scripts/conversion_exploit_trained_verifier.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/conversion_exploit_trained_verifier.json
```

Outputs:

- `artifacts/object_gate/conversion_exploit_trained_verifier.json`

Key observations:

- trained on `18` dev attempts with `100` char-gram features
- final learned weights still put positive mass on `visible_score` and `judge_score`, negative mass on `disagreement`
- dev:
  `avg_hidden_score=0.667`, `utility_per_cost=0.333`
- final:
  `avg_hidden_score=0.667`, `utility_per_cost=0.333`

Interpretation:

- a trained lightweight verifier is more stable than the earlier heuristic and learned-risk baselines in the sense that it does not collapse on final
- however, it still does not beat the cheap visible baseline on cost-adjusted utility
- this keeps conversion in `NO_GO`, but narrows the failure diagnosis: richer training may help, while shallow hand-built rules likely will not

Caveats:

- this is still a tiny linear verifier over code text and weak signals, not a fine-tuned language model
- the result is best read as “small trained verifier is insufficient”, not “training can never help”

### Conversion: Tiny Numeric Rule Solver

Status:

- `POSITIVE SIGNAL` on the frozen numeric exploit subset

Command:

```bash
conda run -n infer python scripts/train_numeric_rule_solver.py \
  --slices configs/frozen_slices_phase0.json \
  --out artifacts/object_gate/train_numeric_rule_solver.json
```

Outputs:

- `artifacts/object_gate/train_numeric_rule_solver.json`

Key observations:

- synthetic training set: `768` tasks
- validation set: `192` tasks
- final train loss: `0.001235`
- synthetic validation: `exact_hidden_match_rate=1.0`
- frozen numeric exploit subset: `exact_hidden_match_rate=0.917` over `12` tasks
- same-subset visible-test baseline: `exact_hidden_match_rate=0.583`

Interpretation:

- this is the first conversion result that improves the frozen-slice outcome rather than merely matching it
- unlike the earlier shallow routing and filtering policies, a materially different intervention class, direct training to infer hidden rules from visible evidence, shows real gain on the numeric exploit subset
- this does not close `Conversion` overall, but it re-opens the method line in a narrower form: training-based conversion may work where inference-time routing did not

Caveats:

- this result excludes the non-numeric `string_wrap` task and should be read as numeric-subset evidence only
- the training distribution is synthetic and structurally close to the evaluation family
- this is evidence for a promising intervention class, not yet a general training or deployment claim

### Conversion: Numeric Rule Transfer Probe

Status:

- `PARTIAL PASS` for in-family transfer, `NO_GO` for family-shift transfer

Command:

```bash
conda run -n infer python scripts/train_numeric_rule_transfer.py \
  --slices configs/frozen_slices_phase0.json \
  --artifact artifacts/object_gate/exploit_code_tasks_large_api.json \
  --out artifacts/object_gate/train_numeric_rule_transfer.json
```

Outputs:

- `artifacts/object_gate/train_numeric_rule_transfer.json`

Key observations:

- `all_family_train`:
  `frozen_dev exact_hidden_match_rate=1.0`, `frozen_final exact_hidden_match_rate=1.0`
- `dev_family_only_train`:
  `frozen_dev exact_hidden_match_rate=1.0`, `frozen_final exact_hidden_match_rate=0.5`
- same-split visible baseline:
  `dev=0.667`, `final=0.5`

Interpretation:

- training remains genuinely useful when the training distribution covers the target rule families
- the current positive conversion signal is therefore not a fluke, but it is not yet strong family-shift generalization either
- once the target families move from `affine/quadratic` to `triangular/alternating`, the smaller train regime falls back to baseline-level performance

Caveats:

- this probe still uses synthetic supervised training rather than language-model fine-tuning
- the exploit family remains narrow and numeric
- the right current claim is “training with family coverage helps,” not “training has solved conversion in general”

### Conversion: OOD Piecewise Family Probe

Status:

- `PARTIAL PASS` with coverage, `NO_GO` without coverage

Command:

```bash
conda run -n infer python scripts/train_numeric_rule_ood_family.py \
  --out artifacts/object_gate/train_numeric_rule_ood_family.json
```

Outputs:

- `artifacts/object_gate/train_numeric_rule_ood_family.json`

Key observations:

- held-out `piecewise_jump` eval set size: `6`
- `legacy_only_train` on old families:
  `heldout_piecewise exact_hidden_match_rate=0.0`
- `legacy_plus_piecewise_train` with family coverage:
  `heldout_piecewise exact_hidden_match_rate=1.0`
- non-trained baselines on the same held-out family:
  `quadratic_extrapolation=0.0`, `visible_lookup=0.0`

Interpretation:

- the training line now has a clean result on a structurally different family: without family coverage it fails completely, and with family coverage it succeeds completely
- this strengthens the current method diagnosis: training-based conversion is a real intervention class, but its current success is coverage-dependent rather than broad family-shift generalization
- the result is stronger than the earlier within-family split because the held-out task family is structurally different from the original four numeric families

Caveats:

- this remains a synthetic probe rather than an API-backed exploit family
- the positive result is still conditional on family coverage
- this should still be framed as a bounded method result, not a general conversion win

### OOD API Exploit Family

Status:

- `PASS` for exploitability on a new API-backed family

Command:

```bash
python scripts/generate_exploit_code_tasks_ood.py \
  --out configs/exploit_code_tasks_ood_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_code_tasks_ood_api.json \
  --out artifacts/object_gate/exploit_code_tasks_ood_api.json
```

Outputs:

- `configs/exploit_code_tasks_ood_api.json`
- `artifacts/object_gate/exploit_code_tasks_ood_api.json`

Key observations:

- family size: `6` tasks across `cubic` and `piecewise_jump`
- objective weak verifier: `tasks_with_exploit=6/6`, `avg_best_exploit_gap=1.0`, `max_exploit_gap=1.0`
- model-judge weak verifier: `tasks_with_judge_gap=3/6`, `avg_best_judge_gap=0.5`, `max_judge_gap=1.0`
- API usage: `6527` total tokens across `36` calls

Interpretation:

- the exploitability signal is not confined to the original four numeric families
- a new API-backed OOD family still shows clean visible-test exploits on every task
- verifier dependence remains present, but the objective exploit signal is now extremely strong on this family

Caveats:

- this remains a small family and should be read as a probe, not a frequency estimate
- pricing is not logged here; only token usage is recorded

### Conversion: Training on API-backed OOD Family

Status:

- `PARTIAL PASS` with family coverage, `NO_GO` without coverage

Command:

```bash
conda run -n infer python scripts/train_numeric_rule_api_ood.py \
  --artifact artifacts/object_gate/exploit_code_tasks_ood_api.json \
  --out artifacts/object_gate/train_numeric_rule_api_ood.json
```

Outputs:

- `artifacts/object_gate/train_numeric_rule_api_ood.json`

Key observations:

- `legacy_only_train`:
  `api_ood_eval exact_hidden_match_rate=0.0`
- `legacy_plus_ood_train`:
  `api_ood_eval exact_hidden_match_rate=1.0`
- visible-attempt baseline on the same OOD API family:
  `exact_hidden_match_rate=0.0`

Interpretation:

- the earlier coverage-vs-shift diagnosis now survives contact with a small API-backed exploit family
- training on legacy families alone does not transfer to the new `cubic/piecewise_jump` family
- once the new families are covered during training, the training intervention beats the exploit baseline cleanly

Caveats:

- the training data is still synthetic even though evaluation uses an API-generated exploit artifact
- this remains a bounded method result under family coverage, not a broad generalization claim

### OOD String Exploit Family

Status:

- `PARTIAL PASS` for object-level exploitability; weaker than the numeric OOD family

Command:

```bash
python scripts/generate_exploit_string_tasks_ood.py \
  --out configs/exploit_string_tasks_ood_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_string_tasks_ood_api.json \
  --out artifacts/object_gate/exploit_string_tasks_ood_api.json
```

Outputs:

- `configs/exploit_string_tasks_ood_api.json`
- `artifacts/object_gate/exploit_string_tasks_ood_api.json`

Key observations:

- family size: `6` tasks across `mirror_join` and `vowel_mask`
- objective weak verifier: `tasks_with_exploit=2/6`, `avg_best_exploit_gap=0.333`, `max_exploit_gap=1.0`
- model-judge weak verifier: `tasks_with_judge_gap=0/6`
- API usage: `6875` total tokens across `36` calls

Interpretation:

- a non-numeric exploit signal exists, but it is materially weaker than the numeric OOD exploit family
- the model often generalized correctly on `mirror_join`, so visible-test overfitting is not the dominant behavior on every semantic family
- this is useful audit information: object signals do not transfer uniformly across task types

Caveats:

- this family is small and may not be the strongest semantic exploit construction
- the zero judge-gap result means the model judge added no additional exploit evidence here

### Conversion: Training on API-backed OOD String Family

Status:

- `NO_GO`

Command:

```bash
conda run -n infer python scripts/train_string_rule_api_ood.py \
  --artifact artifacts/object_gate/exploit_string_tasks_ood_api.json \
  --out artifacts/object_gate/train_string_rule_api_ood.json
```

Outputs:

- `artifacts/object_gate/train_string_rule_api_ood.json`

Key observations:

- `legacy_only_train`:
  `api_ood_eval exact_hidden_match_rate=0.0`
- `legacy_plus_ood_train`:
  `api_ood_eval exact_hidden_match_rate=0.167`
- visible-attempt baseline on the same OOD string family:
  `exact_hidden_match_rate=0.667`

Interpretation:

- the bounded positive method story does not yet extend to this first non-numeric family
- coverage-aware training improved over pure shift failure, but it remained far below the actual API baseline
- this suggests that the current string training formulation is too weak and that semantic families are not yet in the same regime as the numeric rule families

Caveats:

- this used a small classifier-style training prototype rather than a sequence model or language-model fine-tune
- the family itself was only moderately exploit-prone, which makes conversion harder to demonstrate cleanly

### OOD String Exploit Family V2

Status:

- `PASS` for a stronger semantic exploit family

Command:

```bash
python scripts/generate_exploit_string_tasks_v2.py \
  --out configs/exploit_string_tasks_v2_api.json

VSI_API_KEY=... conda run -n infer python scripts/exploit_code_tasks.py \
  --config configs/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/exploit_string_tasks_v2_api.json
```

Outputs:

- `configs/exploit_string_tasks_v2_api.json`
- `artifacts/object_gate/exploit_string_tasks_v2_api.json`

Key observations:

- family size: `6` tasks across `odd_even_join` and `half_swap`
- objective weak verifier: `tasks_with_exploit=5/6`, `avg_best_exploit_gap=0.667`, `max_exploit_gap=1.0`
- model-judge weak verifier: `tasks_with_judge_gap=4/6`, `avg_best_judge_gap=0.5`, `max_judge_gap=1.0`
- API usage: `7283` total tokens across `36` calls

Interpretation:

- redesigning the semantic family mattered: this v2 family is much more exploit-prone than the earlier `mirror_join/vowel_mask` family
- object-level exploitability is now clearly live on a non-numeric semantic family rather than just barely present
- this makes the semantic conversion question meaningful again, whereas the earlier family was too weak and too baseline-friendly

Caveats:

- this is still a small family and should be read as a targeted probe
- semantic exploitability remains family-design dependent

### Conversion: Training on API-backed OOD String Family V2

Status:

- `PARTIAL PASS`

Command:

```bash
conda run -n infer python scripts/train_string_rule_api_v2.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/train_string_rule_api_v2.json
```

Outputs:

- `artifacts/object_gate/train_string_rule_api_v2.json`

Key observations:

- `legacy_only_train`:
  `api_v2_eval exact_hidden_match_rate=0.0`
- `legacy_plus_v2_train`:
  `api_v2_eval exact_hidden_match_rate=0.333`
- visible-attempt baseline on the same semantic-v2 family:
  `exact_hidden_match_rate=0.167`

Interpretation:

- this is the first semantic-family result where coverage-aware training actually beats the API baseline
- however, the gain is still small and the absolute score remains modest, so this is not yet a strong semantic conversion success
- the semantic method story therefore becomes conditional rather than purely negative: family design matters, and some semantic families can be moved by training under coverage

Caveats:

- this still uses a small classifier-style training probe rather than a generative or fine-tuned language model
- absolute performance remains far below the clean numeric-family results
- the right claim is “first positive semantic signal,” not “semantic conversion solved”

### Conversion: Structured Decoder on API-backed OOD String Family V2

Status:

- `PASS` as a bounded upper-bound probe

Command:

```bash
python scripts/train_string_rule_api_v2_library.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --out artifacts/object_gate/train_string_rule_api_v2_library.json
```

Outputs:

- `artifacts/object_gate/train_string_rule_api_v2_library.json`

Key observations:

- `legacy_only_library`:
  `exact_hidden_match_rate=0.0`, `tasks_with_no_match=6`
- `legacy_plus_v2_library`:
  `exact_hidden_match_rate=1.0`, `tasks_with_no_match=0`, `tasks_with_multiple_matches=0`
- visible-attempt baseline:
  `exact_hidden_match_rate=0.167`

Interpretation:

- semantic-v2 is not intrinsically unsalvageable; with a stronger structured decoder and family coverage, the task can be solved cleanly
- the bottleneck on semantic-v2 is therefore not the absence of usable signal, but the weakness of the current learned decoder
- this materially changes the semantic diagnosis: the earlier `0.333` result was a lower bound from a weak learner, not a clear ceiling

Caveats:

- this is not a generic learned model; it is a bounded rule-library probe on a finite synthetic family
- the result should be read as an upper-bound style diagnostic, not as a deployment-ready method claim

### Conversion: Neural Decoder on API-backed OOD String Family V2

Status:

- `PASS`

Command:

```bash
conda run -n infer python scripts/train_string_rule_api_v2_neural.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --repeats 24 \
  --epochs 180 \
  --out artifacts/object_gate/train_string_rule_api_v2_neural.json
```

Outputs:

- `artifacts/object_gate/train_string_rule_api_v2_neural.json`

Key observations:

- `legacy_only_neural`:
  `api_v2_eval exact_hidden_match_rate=0.0`
- `legacy_plus_v2_neural`:
  `api_v2_eval exact_hidden_match_rate=1.0`
- validation under family coverage:
  `exact_hidden_match_rate=1.0`
- visible-attempt baseline:
  `exact_hidden_match_rate=0.167`

Interpretation:

- a stronger learned decoder is enough to close the gap on semantic-v2
- unlike the earlier weak classifier (`0.333`), the char-level neural decoder now matches the structured upper-bound result on this family
- this means the semantic-v2 bottleneck was indeed decoder weakness rather than lack of usable conversion signal

Caveats:

- this is still a bounded family-level result rather than a broad semantic generalization claim
- the decoder is trained with family coverage and evaluated on a very small family

### Conversion: Semantic Transfer on String Family V2

Status:

- `NO_GO` for no-coverage transfer

Command:

```bash
conda run -n infer python scripts/train_string_rule_semantic_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --repeats 24 \
  --epochs 180 \
  --out artifacts/object_gate/train_string_rule_semantic_transfer.json
```

Outputs:

- `artifacts/object_gate/train_string_rule_semantic_transfer.json`

Key observations:

- full coverage reference:
  `eval exact_hidden_match_rate=1.0`
- `v1_to_v2_transfer`:
  `eval exact_hidden_match_rate=0.0`
- `odd_to_half_transfer`:
  `eval exact_hidden_match_rate=0.0`
- `half_to_odd_transfer`:
  `eval exact_hidden_match_rate=0.0`
- visible baselines:
  `full=0.167`, `odd=0.0`, `half=0.333`

Interpretation:

- the positive semantic-v2 result is real, but it is coverage-bound
- neither transfer from the earlier semantic family nor transfer between the two v2 subfamilies survives without target-family coverage
- this sharply separates two claims:
  `semantic conversion under coverage` is supported;
  `semantic transfer without coverage` is currently unsupported

Caveats:

- this is still a small-family transfer probe
- zero transfer here does not rule out broader semantic methods, but it does rule out claiming transfer from the current setup

### Conversion: Seq2Seq Transfer Prototype on String Family V2

Status:

- `NO_GO` for the current minimal seq2seq intervention

Commands:

```bash
conda run -n infer python scripts/train_string_seq2seq_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference,v1_to_v2_transfer \
  --repeats 6 \
  --epochs 40 \
  --out artifacts/object_gate/train_string_seq2seq_transfer_small.json

conda run -n infer python scripts/train_string_seq2seq_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference \
  --repeats 12 \
  --epochs 120 \
  --out artifacts/object_gate/train_string_seq2seq_coverage_only.json
```

Outputs:

- `artifacts/object_gate/train_string_seq2seq_transfer_small.json`
- `artifacts/object_gate/train_string_seq2seq_coverage_only.json`

Key observations:

- small two-regime run:
  both `full_coverage_reference` and `v1_to_v2_transfer` stayed at `0.0`
- stronger coverage-only run:
  `full_coverage_reference exact_hidden_match_rate=0.0`
- visible baseline on the same family:
  `exact_hidden_match_rate=0.167`

Interpretation:

- this first seq2seq / LM-style prototype does not currently help
- unlike the finite-label neural decoder, the minimal generative transfer model failed to learn even the covered family under the current training budget
- so the current evidence does not support saying that “switching to a more open sequence model” rescues transfer

Caveats:

- this is a small, CPU-budgeted char-level prototype rather than a serious sequence-model training run
- the negative result is about the current prototype, not about all possible LM-style interventions

### Conversion: Decoder-only Transformer LM on String Family V2

Status:

- `NO_GO` for the current heavier LM-style intervention

Commands:

```bash
conda run -n infer python scripts/train_string_transformer_lm_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference,v1_to_v2_transfer \
  --repeats 12 \
  --epochs 20 \
  --batch_size 64 \
  --out artifacts/object_gate/train_string_transformer_lm_transfer.json

conda run -n infer python scripts/train_string_transformer_lm_transfer.py \
  --artifact artifacts/object_gate/exploit_string_tasks_v2_api.json \
  --modes full_coverage_reference \
  --repeats 24 \
  --epochs 80 \
  --batch_size 64 \
  --out artifacts/object_gate/train_string_transformer_lm_coverage_only.json
```

Outputs:

- `artifacts/object_gate/train_string_transformer_lm_transfer.json`
- `artifacts/object_gate/train_string_transformer_lm_coverage_only.json`

Key observations:

- two-regime run:
  `full_coverage_reference exact_hidden_match_rate=0.0`
  `v1_to_v2_transfer exact_hidden_match_rate=0.0`
- stronger coverage-only run:
  `full_coverage_reference exact_hidden_match_rate=0.0`
- visible baseline on the same family:
  `exact_hidden_match_rate=0.167`

Interpretation:

- a materially heavier decoder-only transformer LM does not currently rescue semantic transfer
- more importantly, it does not even solve the covered family under the present training setup
- this means the positive semantic-v2 result is currently specific to the finite-label decoder family, not something we have yet reproduced with an open generative LM-style model

Caveats:

- this is still a small custom transformer rather than a pretrained language model fine-tune
- the negative result is about the current LM-style prototype and training setup, not about every possible pretrained LM intervention
