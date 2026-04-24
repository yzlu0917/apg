# Progress

## Current objective

Phase 0 bootstrap for the VSI project:

- freeze claim hierarchy
- define fallback framing and go/no-go gates
- stand up a minimal project scaffold
- complete the smallest Object-gate closure

## Gate status

- `Object`: bootstrap `GO`, full gate still DOING
- `Audit`: DOING
- `Conversion`: shallow inference-time path `NO_GO`; training-based path shows first positive subset signal
- `Scale`: TODO

## Milestones

### DONE

- read `AGENTS.md`, `README.md`, and `proposal.md`
- convert proposal into phase-0 claim hierarchy and fallback framing
- freeze gate definitions and bootstrap acceptance rule
- create project scaffold: `docs/`, `history/`, `configs/`, `scripts/`, `artifacts/`
- implement and run the `Object gate` microbench bootstrap
- write the first reproducible artifact to `artifacts/object_gate/bootstrap_summary.json`
- implement and run a hybrid local-model smoke test with `Qwen3-4B`
- write the hybrid artifact to `artifacts/object_gate/hybrid_smoke.json`
- add an OpenAI-compatible API provider to the hybrid runner
- run and log an API-backed smoke test to `artifacts/object_gate/hybrid_api_smoke.json`
- add and run an API-backed mini-family runner to `artifacts/object_gate/hybrid_api_family.json`
- add and run `rewrite_audit.py` for prompt-style and verifier-sensitivity checks
- add and run `exploit_code_tasks.py` to establish a non-toy exploitability signal
- add a non-arithmetic string ambiguity family
- add verifier-swap measurements to exploitability code tasks
- add generators for larger-sample ambiguity and exploit families
- freeze a first dev/final split and summarize it
- run first minimal conversion protocols on the frozen split
- run a second round of exploit-focused conversion alternatives
- run learned risk-model and agreement-filter conversion baselines
- run a tiny trained verifier baseline on exploit attempts
- run a tiny numeric training-based conversion prototype on the frozen exploit subset

### DOING

- upgrade the toy bootstrap into controlled instance generators
- pivot to a hybrid object study: model-generated rewrites / weak judging plus programmatic strong checks
- prepare the first Audit-gate checks on rewrite robustness and verifier swap
- strengthen the exploit-search task so `E` is tested in a model-in-the-loop setting instead of a hand-written toy
- use the API path selectively for stronger rewrite/exploit proposals while keeping objective strong verification local
- diversify beyond arithmetic-style problems before claiming any family-level generality
- split `A` into surface-form and semantic components if audit keeps showing canonicalization sensitivity

### TODO

- expand the microbench into actual generators instead of fixed toy instances
- add rewrite-robustness and verifier-swap checks for Audit gate
- define frozen dev slice and final slice for controlled synthetic families
- prepare the smallest equal-budget conversion protocol

### BLOCKED

- none at phase 0 bootstrap

## Latest updates

### 2026-03-31

- Reframed the project so that the paper headline is strictly the object claim; method and deployment claims remain conditional.
- Wrote the fallback ladder: predictive-law paper, benchmark/diagnosis paper, or clean negative-result paper.
- Defined `Object`, `Audit`, `Conversion`, and `Scale` gates with explicit go/no-go criteria.
- Ran a deterministic `Object gate` microbench and obtained a bootstrap `GO`: `H/A/E` are separable from a matched coarse-difficulty proxy on the toy slice.
- Shifted the next step from rule-first generation to a hybrid setup: local Qwen3 for rewrite / weak-verifier / exploit search, objective checking for strong validation.
- Confirmed that local `Qwen3-4B` can run a non-thinking JSON-only pipeline for object work; the first smoke test produced live ambiguity signal but not yet exploitability.
- Added an OpenAI-compatible provider and confirmed that the provided API endpoint works for the same hybrid workflow with low token usage and the same qualitative ambiguity signal.
- Ran a 3-problem API-backed mini-family; `A` is stable across the family, while `E` is still absent and therefore the main unresolved object axis.
- Split ambiguity into `A_surface` and `A_semantic`; rewrite audit shows both survive, but `A_semantic` is materially smaller, confirming that the old ambiguity scalar mixed canonicalization with true semantic variation.
- Expanded exploitability code tasks to a 5-task family; `E` is now alive beyond a single anecdote, with `tasks_with_exploit=4/5` and `max_exploit_gap=1.0`.
- Added verifier-swap on the exploit family: `tasks_with_judge_gap=3/5`, so exploitability depends on which weak verifier is used.
- Added a non-arithmetic string ambiguity family; `A_surface` and `A_semantic` both remain live outside arithmetic traces.
- Expanded the string ambiguity family to `12` tasks and the exploit code family to `12` tasks; both signals remain alive at larger sample size.
- Froze the first phase-0 dev/final split and verified that final-slice aggregates do not collapse relative to dev.
- Ran first minimal conversion protocols on the frozen split; both current routing recipes failed to beat simple baselines, so conversion is presently a clean negative.
- Tried a second conversion round with attempt-level reranking and abstention on the exploit family; reranking still failed and abstention collapsed on final, so conversion remains negative.
- Tried a tiny learned risk model and an agreement-based filter on the exploit family; both also failed on the frozen final slice, so repeated conversion negatives now span multiple intervention styles.
- Trained a tiny char-gram exploit verifier on the dev attempts; it matched but did not beat the cheap visible baseline, so conversion remains negative but the failure mode is now better localized.
- Trained a tiny numeric rule solver on synthetic visible-to-hidden tasks and evaluated it on the frozen numeric exploit subset; this reached `exact_hidden_match_rate=0.917` versus `0.583` for the same-subset visible baseline, giving the first positive training-based conversion signal.
- Ran a transfer probe on the numeric training path: when training covers all exploit-rule families, frozen final reaches `1.0`; when training only covers dev-like `affine/quadratic` families, frozen final drops to `0.5`, equal to the visible baseline. The current method signal is therefore real but not family-shift robust.
- Added a structurally different held-out `piecewise_jump` family. Training on legacy families alone gets `0.0` on that family; adding piecewise family coverage raises held-out performance to `1.0`, while quadratic and lookup baselines both stay at `0.0`. This makes the current boundary sharper: training helps under family coverage, but not under true family shift.
- Added a small API-backed OOD exploit family with `cubic` and `piecewise_jump` tasks. Exploitability stays extremely strong on this new family (`6/6` visible-test exploits), and the same training boundary repeats: legacy-only training gets `0.0`, while coverage-aware training gets `1.0`, with the visible-attempt baseline also at `0.0`.
- Added a first non-numeric API-backed exploit family with `mirror_join` and `vowel_mask`. Exploitability is weaker here (`2/6` visible-test exploits), and the current classifier-style training recipe stays below the API baseline (`0.167` vs `0.667`). So the bounded positive method story still does not extend to this semantic family.
- Re-designed the semantic family into a more exploit-prone `odd_even_join/half_swap` v2 family. This time exploitability is strong (`5/6` visible-test exploits), and coverage-aware training reaches `0.333` versus a `0.167` visible baseline. This is the first bounded positive semantic conversion signal, though still much weaker than the numeric line.
- Added a structured semantic-v2 decoder probe. Under legacy-only coverage it stays at `0.0`; with v2 family coverage it reaches `1.0`, with no ambiguous matches. So semantic-v2 is not blocked by missing signal; it is currently blocked by learner strength.
- Replaced the weak semantic-v2 learner with a char-level neural decoder. Under legacy-only coverage it stays at `0.0`; with v2 family coverage it reaches `1.0`, matching the structured upper bound and far exceeding the `0.167` visible baseline. So semantic-v2 is now a real positive method result under coverage, not just an upper-bound thought experiment.
- Ran a true no-coverage semantic transfer probe. `v1 -> v2` transfer is `0.0`, and even `odd_even -> half_swap` / `half_swap -> odd_even` are both `0.0`, while full coverage remains `1.0`. So the semantic result is genuinely coverage-bound rather than transfer-capable.
- Tried a new intervention class: a char-level seq2seq / LM-style prototype. Under the current budget it failed to learn even coverage on semantic-v2 (`0.0`), so it does not currently rescue semantic transfer.
- Tried a heavier decoder-only transformer LM on GPU. It also stayed at `0.0`, including on a stronger coverage-only run, so the current positive semantic-v2 result still appears specific to the finite-label decoder family rather than replicated by an open generative model.

## Decisions and defaults

- Default object-first strategy: do not spend training budget before the object survives bootstrap audit.
- Default synthetic-first strategy: start from controlled families before touching Lean / MathArena / LiveBench anchors.
- Default acceptance rule: narrow bootstrap thresholds only; do not over-interpret the first toy result as full validation.
- Default hybrid rule: use models for semantic generation and weak audit, but keep strong verification objective and reproducible.
- Default API usage rule: use API selectively for stronger semantic generation or exploit search, not for replacing objective scoring.
- Current priority rule: stop trying to re-prove `A` on near-duplicate arithmetic items and move effort to exploitability design plus audit.
- Current audit rule: treat `A_surface` and `A_semantic` as separate reported quantities rather than collapsing them back into one ambiguity number.
- Current exploit rule: report `E` together with the weak verifier used; do not collapse visible-test exploitability and model-judge exploitability into one number.
- Current sampling rule: prefer broader family coverage before increasing per-task resampling depth.
- Current conversion rule: do not promote to `Conversion GO` unless a routed policy beats a fixed baseline on the frozen split.
- Current conversion rule: stop local recipe tweaking after repeated frozen-slice negatives unless the intervention class changes materially.
- Current conversion rule: shallow inference-time routing/filtering is no longer the right search region for this project.
- Current training rule: lightweight verifier-side training is insufficient, but direct task-family training now shows promise on the numeric exploit subset.
- Current claim rule: do not collapse the new training result into a general conversion win; it currently supports only a narrow subset-level method claim.
- Current transfer rule: distinguish `family-covered training` from `family-shift generalization`; only the former is currently positive.
- Current OOD rule: new-family evaluation is now mandatory before upgrading any training result beyond a bounded method claim.
- Current method rule: the bounded positive method claim now extends to a small API-backed OOD exploit family, but still only under family coverage.
- Current semantic rule: do not assume the numeric-family training story transfers to non-numeric families; the first string-family probe is a clean negative for conversion.
- Current semantic rule: semantic conversion is family-design dependent. The first string family was negative, while the stronger v2 family gives a small positive under coverage.
- Current decoder rule: for semantic-v2, bounded structured decoding is already strong; the open problem is learning a decoder that approaches this upper bound without hardcoded family libraries.
- Current decoder rule: for semantic-v2, the learned decoder can now match the structured upper bound under coverage; the remaining open problem is broader semantic transfer, not decoder adequacy on this family.
- Current transfer rule: semantic transfer without target-family coverage is currently unsupported, even within the semantic-v2 superfamily.
- Current intervention rule: the finite-label neural decoder works under coverage; the first small seq2seq prototype is a clean negative and should not be used as evidence that open generative transfer helps.
- Current LM rule: the first heavier decoder-only transformer LM is also a clean negative; we do not currently have evidence that LM-style open generation reproduces the semantic-v2 win.

## Resume point

Freeze the method claim as “numeric positive; semantic-v2 positive under coverage via finite-label decoders; semantic transfer without coverage negative in current probes; first LM-style generative prototypes negative,” unless you want a real pretrained-LM fine-tuning experiment.
