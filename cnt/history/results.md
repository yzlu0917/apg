# Results

## 2026-03-09 Week 1 Synthetic CounterTrace

Status: completed

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_week1_synthetic.py --num-instances 48 --sigma 0.35 --output-dir outputs/week1_20260309_run01
```

Expected outputs:
- `outputs/week1_20260309_run01/synthetic_summary.json`
- `outputs/week1_20260309_run01/synthetic_rows.jsonl`

Observed summary:

- `cnt_vs_gt_corr = 0.9902`
- `observational_vs_gt_corr = -0.0488`
- `entropy_vs_gt_corr = -0.6187`
- `future_success_vs_gt_corr = -0.2928`
- `ctf_proxy(cnt / obs / entropy / future / random) = 1.00 / 0.50 / 0.00 / 0.50 / 0.4375`
- `deletion_paraphrase_asymmetry = 0.2316`
- `mstl_ratio = 0.8462`

Detectability audit:

- `drop`: shallow `0.5875`, length-only `0.6000`, corr with CNT `-0.4085`
- `swap_local`: shallow `0.7375`, length-only `0.5458`, corr with CNT `-0.1221`
- `swap_decoy`: shallow `0.7625`, length-only `0.5417`, corr with CNT `-0.1220`
- `paraphrase`: shallow `0.4833`, length-only `0.5167`, corr with CNT `0.5183`
- mean detectability correlation: `-0.0336`

Interpretation against proposal Week 1 Go / No-Go:

- PASS: synthetic necessity recovery is clearly stronger for CNT than for observational / entropy / future-success baselines.
- PASS: mean detectability correlation is near zero, so the current CNT signal is not being driven by shallow edit detection.
- PASS: deletion hurts materially more than paraphrase in the synthetic suite.
- PARTIAL: `swap_*` edit families are still somewhat shallow-detectable, so they should be kept inside synthetic object-identification for now, then tightened before promotion into real-domain training data.

Failure notes:

- The first implementation accidentally gave every candidate step enough recovery slack, which collapsed ground-truth necessity to zero. Fix: tighten the continuation budget to 13 and place late core candidates where replaying the omitted step is no longer free.
- Paraphrases were initially too easy to classify because they changed the whole template family. Fix: paraphrase now stays inside the same template family and only flips the local phrasing variant.

Next-step decision:

- Proceed to `CounterTrace-mini(math)` data construction.
- Keep `scripts/run_week1_synthetic.py` as a regression gate before any editor-family or metric change.

Output locations from the successful run:

- `outputs/week1_20260309_run01/synthetic_summary.json`
- `outputs/week1_20260309_run01/synthetic_rows.jsonl`

Key code paths:

- `src/cnt_research/synthetic/benchmark.py`
- `scripts/run_week1_synthetic.py`

## 2026-03-09 CounterTrace-mini(math) Pilot

Status: completed for the first real-domain collection pass

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_countertrace_mini_math.py --max-examples 16 --target-successes 4 --max-new-tokens 220 --output-dir outputs/countertrace_mini_math_20260309_run01
```

Outputs:
- `data/gsm8k/test.jsonl`
- `outputs/countertrace_mini_math_20260309_run01/math_summary.json`
- `outputs/countertrace_mini_math_20260309_run01/math_traces.jsonl`
- `outputs/countertrace_mini_math_20260309_run01/math_success_traces.jsonl`

Observed summary:

- `num_questions_considered = 16`
- `num_attempts = 9`
- `num_verified_traces = 4`
- `verified_trace_rate_over_attempts = 0.4444`
- `verified_trace_rate_over_questions = 0.25`
- `mean_step_count_verified = 6.5`
- `mean_candidate_steps_verified = 4.5`

Successful example ids:

- `gsm8k-00007`
- `gsm8k-00045`
- `gsm8k-00327`
- `gsm8k-00579`

Interpretation against the proposal:

- PASS: `CounterTrace-mini(math)` has been started in a real verifiable domain, not just as a placeholder download step.
- PASS: local-model successful traces can now be collected, verified, and serialized with candidate step metadata.
- PASS: the pipeline now has the minimum pieces needed for Stage A on math: `problem -> trace -> verifier -> successful prefix candidates`.
- NOT DONE: real-domain `drop / swap / paraphrase` editors and continuator-based `N_t` estimation are not implemented yet.
- NOT DONE: cross-editor / held-out-continuator stability audits remain ahead.

Current interpretation:

- This does align with the proposal's next phase: we have moved from Layer 1 synthetic object validation into Layer 2 math data construction.
- The current bottleneck is no longer “can we get verifiable successful math traces?” but “can we build natural real-domain editors and continuations on top of them?”

Key code paths:

- `src/cnt_research/math/countertrace_mini.py`
- `scripts/run_countertrace_mini_math.py`

## 2026-03-09 Math Stage A Necessity Pilot

Status: completed as a real-domain pilot, not yet training-ready

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --max-traces 4 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run01
```

Inputs:

- `outputs/countertrace_mini_math_20260309_run01/math_success_traces.jsonl`

Outputs:

- `outputs/math_stage_a_20260309_run01/stage_a_math_summary.json`
- `outputs/math_stage_a_20260309_run01/stage_a_math_records.jsonl`

Observed summary:

- `num_records = 12`
- `mean_original_solve = 0.7778`
- `mean_drop_solve = 0.7778`
- `mean_paraphrase_solve = 0.8056`
- `mean_swap_solve = 0.6667`
- `mean_n_t = 0.0741`
- `mean_n_t_weighted = 0.00047`
- `mean_stability = 0.6157`
- `mean_paraphrase_gap = 0.0833`
- `positive_n_fraction = 0.25`

Interpretation against the proposal:

- PASS: real-domain Stage A is no longer hypothetical. The repo now supports `success trace -> edited prefix -> continuator continuation -> verifier -> per-step necessity estimate`.
- PASS: the pilot surfaces the exact proposal risk we needed to test next, namely continuator-dependent fragility versus actual necessity.
- FAIL for training use: the unweighted signal is only weakly positive and collapses after stability weighting, so this is not a clean `N_t` estimate yet.
- FAIL for editor audit: current `swap_*` edits are pilot-grade only. Some swaps are ignored or repaired by the continuator; some early prefixes are unsolved even in the original condition.

What this means:

- The research is still aligned with the proposal.
- But the current math Stage A result is a warning, not a win: with this local continuator family and these first editor families, `N_t` is too noisy to promote into training.
- This is still useful progress because the bottleneck is now explicit and reproducible.

Concrete failure pattern from the pilot:

- Early prefixes can already fail under the original trace, so any necessity estimate there is dominated by base continuator weakness.
- Late prefixes are often fully repaired by the continuator even when the target step is swapped or dropped, which drives `N_t` toward zero.
- Stability weighting correctly suppresses these noisy positives, which is why `mean_n_t_weighted` is effectively zero.

Next-step decision:

- Do not start training from this math `N_t` signal yet.
- First improve the real-domain continuator/editor stack:
  - strengthen continuator prompts or model family
  - make `swap_*` edits more locally consequential and natural
  - enlarge the success-trace pool before rerunning Stage A

Key code paths:

- `src/cnt_research/math/stage_a.py`
- `scripts/run_math_stage_a.py`

### 2026-03-09 Prompt / Editor Refinement Smoke

Status: directional improvement confirmed, not a new main result

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --max-traces 1 --max-candidates-per-trace 2 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_smoke04
```

Outputs:

- `outputs/math_stage_a_20260309_smoke04/stage_a_math_summary.json`
- `outputs/math_stage_a_20260309_smoke04/stage_a_math_records.jsonl`

Observed summary:

- `mean_original_solve = 0.6667`
- `mean_drop_solve = 0.6667`
- `mean_paraphrase_solve = 0.5000`
- `mean_swap_solve = 0.0000`
- `mean_n_t = 0.4444`
- `mean_n_t_weighted = 0.0165`
- `positive_n_fraction = 1.0`

What changed:

- continuator prompts now explicitly lock earlier steps instead of inviting repairs
- `swap_quantity` and `swap_operation` now use deterministic arithmetic mistakes instead of weak model-generated rewrites

Interpretation:

- The direction is correct: once the continuator is forced to honor the edited prefix and the edits become locally consequential, wrong late-step edits do depress solve probability as the proposal expects.
- Stability is still low, so this smoke run is evidence for the refinement direction, not a replacement for the larger Stage A pilot.
- A larger rerun with the new prompt/editor family was started but intentionally stopped in this turn because batch runtime was too high to finish cleanly.

## 2026-03-09 Math Stage A Formal Rerun (`run02`)

Status: completed as the first batch-scale rerun with locked-prefix continuators and heuristic arithmetic swaps

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --gpu cuda:0 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run02_shard0
python scripts/run_math_stage_a.py --gpu cuda:1 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run02_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260309_run02_shard0 outputs/math_stage_a_20260309_run02_shard1 --output-dir outputs/math_stage_a_20260309_run02
```

Outputs:

- `outputs/math_stage_a_20260309_run02/stage_a_math_summary.json`
- `outputs/math_stage_a_20260309_run02/stage_a_math_records.jsonl`

Observed summary:

- `num_records = 12`
- `mean_original_solve = 0.8611`
- `mean_drop_solve = 0.7500`
- `mean_paraphrase_solve = 0.7500`
- `mean_swap_solve = 0.0000`
- `mean_n_t = 0.6111`
- `mean_n_t_weighted = 0.0203`
- `mean_stability = 0.0343`
- `mean_paraphrase_gap = 0.1111`
- `positive_n_fraction = 1.0`

Relative to `run01`:

- `mean_n_t`: `0.0741 -> 0.6111`
- `mean_n_t_weighted`: `0.00047 -> 0.0203`
- `mean_swap_solve`: `0.6667 -> 0.0000`
- `positive_n_fraction`: `0.25 -> 1.0`

Cross-editor reading:

- Wrong arithmetic swaps now consistently collapse solve probability on average.
- Deletion is weaker than swap but still hurts on average: `0.8611 -> 0.7500`.
- Paraphrase is no longer catastrophic on average, but it is still not neutral enough to count as a finished invariance audit.

Interpretation against proposal Week 2:

- PASS: the locked-prefix + arithmetic-swap refinement is not a smoke-only artifact; it survives a 12-record rerun.
- PASS: the main failure mode is no longer “swap edits are too soft to matter.”
- PARTIAL: stability remains low, so this is a stronger Stage A signal, not yet a clean held-out-stable training signal.
- NOT DONE: held-out continuator audit is still missing.

Current interpretation:

- This rerun materially improves alignment with the proposal's Week 2 gate. The object is visible in real-domain math now.
- The remaining bottleneck is specifically cross-continuator robustness, not whether local arithmetic swaps can produce consequential counterfactuals.

### 2026-03-09 Stage A Resume / Checkpoint Smoke

Status: completed as infrastructure validation for long held-out audits

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --gpu cuda:4 --max-traces 1 --trace-offset 0 --max-candidates-per-trace 1 --continuation-max-new-tokens 180 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_resume_smoke01
time python scripts/run_math_stage_a.py --resume --gpu cuda:4 --max-traces 1 --trace-offset 0 --max-candidates-per-trace 1 --continuation-max-new-tokens 180 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_resume_smoke01
```

Outputs:

- `outputs/math_stage_a_20260309_resume_smoke01/stage_a_math_summary.json`
- `outputs/math_stage_a_20260309_resume_smoke01/stage_a_math_records.jsonl`

Observed summary:

- `num_records = 1`
- `mean_n_t = 0.3333`
- `mean_n_t_weighted = 0.0095`
- `wc -l stage_a_math_records.jsonl = 1`
- rerunning with `--resume` returned in about `4.2s` and did not duplicate records

Why this matters:

- Attempted `Qwen3-4B` held-out audits were much slower than the 1.7B train-side continuator.
- Stage A now writes records and summary after each completed candidate-step evaluation and can resume from partial output, so long held-out audits no longer need all-or-nothing completion in one uninterrupted run.

Key code paths:

- `src/cnt_research/math/stage_a.py`
- `scripts/run_math_stage_a.py`

## 2026-03-09 Held-Out Continuator Audit (`run03_qwen3_4b`)

Status: completed as the first formal held-out continuator rerun

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:2 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run03_qwen3_4b_shard0
python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:3 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run03_qwen3_4b_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260309_run03_qwen3_4b_shard0 outputs/math_stage_a_20260309_run03_qwen3_4b_shard1 --output-dir outputs/math_stage_a_20260309_run03_qwen3_4b
```

Outputs:

- `outputs/math_stage_a_20260309_run03_qwen3_4b/stage_a_math_summary.json`
- `outputs/math_stage_a_20260309_run03_qwen3_4b/stage_a_math_records.jsonl`

Observed summary:

- `num_records = 12`
- `mean_original_solve = 0.8611`
- `mean_drop_solve = 0.8889`
- `mean_paraphrase_solve = 0.9722`
- `mean_swap_solve = 0.1111`
- `mean_n_t = 0.4907`
- `mean_n_t_weighted = 0.0111`
- `mean_stability = 0.0416`
- `mean_paraphrase_gap = 0.1111`
- `positive_n_fraction = 0.9167`

Relative to `run02`:

- `mean_n_t`: `0.6111 -> 0.4907`
- `mean_n_t_weighted`: `0.0203 -> 0.0111`
- `mean_swap_solve`: `0.0000 -> 0.1111`
- `mean_drop_solve`: `0.7500 -> 0.8889`
- `mean_paraphrase_solve`: `0.7500 -> 0.9722`

Interpretation against proposal Week 2:

- PASS: the real-domain signal survives a held-out continuator; `N_t` stays positive on average.
- PASS: arithmetic swaps are still consequential under held-out continuation, though less cleanly than in `run02`.
- FAIL for a finished Go: deletion and paraphrase are repaired too often by the stronger held-out continuator, so the current editor/continuator family is not yet stable enough for training claims.

Concrete failure pattern:

- The main degradation is concentrated in `gsm8k-00007`, where several candidate prefixes become easier for the held-out model after `drop` or `paraphrase`.
- This is not a general collapse: the other three verified problems stay largely positive under held-out continuation.
- So the current issue is not “`N_t` disappears under held-out,” but “a subset of prefixes are still too repairable and should be filtered or edited more tightly.”

## 2026-03-09 Cross-Continuator Audit / Keep-Set (`audit01`)

Status: completed as the first conservative keep-set construction from train-side + held-out Stage A

Reproducible command:

```bash
python scripts/audit_math_stage_a.py --output-dir outputs/math_stage_a_20260309_audit01
```

Outputs:

- `outputs/math_stage_a_20260309_audit01/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260309_audit01/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260309_audit01/stage_a_audit_kept.jsonl`

Audit thresholds:

- `min_weighted_n > 0`
- `min_original_solve >= 2/3`
- `max_paraphrase_gap <= 1/3`
- `max_swap_solve <= 1/3`

Observed summary:

- `num_pairs = 12`
- `num_kept = 8`
- `keep_fraction = 0.6667`
- `mean_train_n_t_weighted_all = 0.0203`
- `mean_heldout_n_t_weighted_all = 0.0111`
- `mean_train_n_t_weighted_kept = 0.0228`
- `mean_heldout_n_t_weighted_kept = 0.0164`

Main drop reasons:

- `heldout_paraphrase_gap = 2`
- `train_original_solve = 2`
- `heldout_original_solve = 1`
- `heldout_weighted_n = 1`
- `heldout_swap_solve = 1`

Interpretation:

- Even with a conservative cross-continuator filter, two-thirds of current candidate steps remain usable.
- The kept subset is cleaner than the full pool under both train-side and held-out metrics.
- The main remaining weak point is paraphrase invariance on a small subset of prefixes, not a full held-out collapse.

Key code paths:

- `src/cnt_research/math/stage_a_audit.py`
- `scripts/audit_math_stage_a.py`

## 2026-03-10 Conservative Paraphrase Rerun (`run04` / `run05`)

Status: completed, then superseded by `run06` / `run07` after a second paraphrase-template fix

Code change:

- `paraphrase` is now deterministic and conservative. It no longer uses free-form model rewrites; it only applies small surface rewrites and leaves risky line shapes unchanged.

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --resume --gpu cuda:2 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run04_para_fix_shard0
python scripts/run_math_stage_a.py --resume --gpu cuda:3 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run04_para_fix_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260310_run04_para_fix_shard0 outputs/math_stage_a_20260310_run04_para_fix_shard1 --output-dir outputs/math_stage_a_20260310_run04_para_fix

python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:4 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix_shard0
python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:5 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix_shard0 outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix_shard1 --output-dir outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix
```

Outputs:

- `outputs/math_stage_a_20260310_run04_para_fix/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run04_para_fix/stage_a_math_records.jsonl`
- `outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix/stage_a_math_records.jsonl`

Observed summary for `run04` (train-side 1.7B):

- `mean_paraphrase_solve = 0.7222`
- `mean_paraphrase_gap = 0.1389`
- `mean_n_t = 0.6111`
- `mean_n_t_weighted = 0.0203`

Observed summary for `run05` (held-out 4B):

- `mean_paraphrase_solve = 0.8889`
- `mean_paraphrase_gap = 0.0278`
- `mean_n_t = 0.4907`
- `mean_n_t_weighted = 0.0111`

Relative to the previous held-out run (`run03_qwen3_4b`):

- `mean_paraphrase_solve`: `0.9722 -> 0.8889`
- `mean_paraphrase_gap`: `0.1111 -> 0.0278`
- `mean_n_t` and `mean_n_t_weighted` are effectively unchanged

Interpretation:

- The paraphrase fix worked where it mattered most for held-out robustness. The previous high-gap late-step Carla case is now neutral under held-out continuation.
- The overall held-out object did not weaken; the gain is specifically cleaner paraphrase invariance.
- The train-side run did not improve in the same way. A new local failure appeared on one `, so` template (`gsm8k-00045`, candidate step 1), so the bottleneck shifted rather than disappeared.

## 2026-03-10 Cross-Continuator Audit / Keep-Set (`audit02`)

Status: completed, then superseded by `audit03`

Reproducible command:

```bash
python scripts/audit_math_stage_a.py --train-records outputs/math_stage_a_20260310_run04_para_fix/stage_a_math_records.jsonl --heldout-records outputs/math_stage_a_20260310_run05_qwen3_4b_para_fix/stage_a_math_records.jsonl --output-dir outputs/math_stage_a_20260310_audit02
```

Outputs:

- `outputs/math_stage_a_20260310_audit02/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260310_audit02/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260310_audit02/stage_a_audit_kept.jsonl`

Observed summary:

- `num_pairs = 12`
- `num_kept = 8`
- `keep_fraction = 0.6667`
- `mean_train_n_t_weighted_kept = 0.0190`
- `mean_heldout_n_t_weighted_kept = 0.0154`
- `mean_train_paraphrase_gap_kept = 0.0`
- `mean_heldout_paraphrase_gap_kept = 0.0`

Comparison against `audit01`:

- keep-set size is unchanged: `8 / 12`
- but the kept subset is cleaner on held-out paraphrase invariance
- the composition changed: `gsm8k-00007`, candidate step `7` is now retained, while `gsm8k-00045`, candidate step `1` becomes the new weak point

Interpretation:

- The cross-continuator keep-set did not expand yet, so this is not a final Week 2 win.
- But the failure mode is now narrower and more interpretable: one local `, so` paraphrase pattern is the main remaining editor issue.
- This is still progress because the bottleneck has moved from “held-out paraphrase is broadly unsafe” to “one specific paraphrase template still breaks train-side invariance.”

## 2026-03-10 Second Template-Fix Rerun (`run06` / `run07`)

Status: completed as the second paraphrase-template refinement pass

Code change:

- `X, so Y` now paraphrases as `X, giving Y` instead of splitting into a new sentence.
- colon-style factual lines such as `Normal download speed: ...` now rewrite without inserting an extra article.

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --resume --gpu cuda:2 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run06_para_fix2_shard0
python scripts/run_math_stage_a.py --resume --gpu cuda:3 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run06_para_fix2_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260310_run06_para_fix2_shard0 outputs/math_stage_a_20260310_run06_para_fix2_shard1 --output-dir outputs/math_stage_a_20260310_run06_para_fix2

python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:4 --max-traces 2 --trace-offset 0 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2_shard0
python scripts/run_math_stage_a.py --resume --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:5 --max-traces 2 --trace-offset 2 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2_shard1
python scripts/merge_math_stage_a.py outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2_shard0 outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2_shard1 --output-dir outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2
```

Outputs:

- `outputs/math_stage_a_20260310_run06_para_fix2/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2/stage_a_math_summary.json`

Observed summary for `run06` (train-side 1.7B):

- `mean_paraphrase_solve = 0.8056`
- `mean_paraphrase_gap = 0.0556`
- `mean_n_t = 0.6111`
- `mean_n_t_weighted = 0.0203`

Observed summary for `run07` (held-out 4B):

- `mean_paraphrase_solve = 0.8889`
- `mean_paraphrase_gap = 0.0278`
- `mean_n_t = 0.4907`
- `mean_n_t_weighted = 0.0111`

Relative to `run04` / `run05`:

- train-side `mean_paraphrase_gap`: `0.1389 -> 0.0556`
- held-out `mean_paraphrase_gap`: stays low at `0.0278`
- main `N_t` levels are preserved on both sides

Interpretation:

- The second template fix solved the train-side `, so` paraphrase regression without sacrificing the held-out gain from the first paraphrase pass.
- At this point paraphrase invariance is no longer the dominant global blocker.

## 2026-03-10 Cross-Continuator Audit / Keep-Set (`audit03`)

Status: completed as the current best joint audit

Reproducible command:

```bash
python scripts/audit_math_stage_a.py --train-records outputs/math_stage_a_20260310_run06_para_fix2/stage_a_math_records.jsonl --heldout-records outputs/math_stage_a_20260310_run07_qwen3_4b_para_fix2/stage_a_math_records.jsonl --output-dir outputs/math_stage_a_20260310_audit03
```

Outputs:

- `outputs/math_stage_a_20260310_audit03/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260310_audit03/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260310_audit03/stage_a_audit_kept.jsonl`

Observed summary:

- `num_pairs = 12`
- `num_kept = 9`
- `keep_fraction = 0.75`
- `mean_train_n_t_weighted_kept = 0.0224`
- `mean_heldout_n_t_weighted_kept = 0.0158`
- `mean_train_paraphrase_gap_kept = 0.0`
- `mean_heldout_paraphrase_gap_kept = 0.0`

Relative to `audit02`:

- keep-set grows from `8 / 12` to `9 / 12`
- `train_paraphrase_gap` is no longer a drop reason
- the remaining dropped Meredith early-step is now blocked by `heldout_swap_solve`, not paraphrase drift

Interpretation:

- This is the first audit where the keep-set meaningfully expands after editor tuning.
- The research object is now much cleaner: remaining drops come from low original solvability or held-out swap repair, not from broad paraphrase instability.
- This is a stronger Week 2 result than `audit01` or `audit02`, though still not a final training claim.

## 2026-03-10 Expanded CounterTrace-mini(math) Pool (`merged01`)

Status: completed as the first non-toy success-trace pool expansion

Code change:

- Added `merge_countertrace_mini_runs(...)` to `src/cnt_research/math/countertrace_mini.py`.
- Added `scripts/merge_countertrace_mini_math.py` to merge multiple trace-collection runs into one canonical pool.

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_countertrace_mini_math.py --gpu cuda:0 --max-examples 48 --target-successes 6 --seed 17 --max-new-tokens 220 --output-dir outputs/countertrace_mini_math_20260310_seed17_run02
python scripts/run_countertrace_mini_math.py --gpu cuda:1 --max-examples 48 --target-successes 6 --seed 23 --max-new-tokens 220 --output-dir outputs/countertrace_mini_math_20260310_seed23_run03
python scripts/merge_countertrace_mini_math.py \
  outputs/countertrace_mini_math_20260309_run01 \
  outputs/countertrace_mini_math_20260310_seed17_run02 \
  outputs/countertrace_mini_math_20260310_seed23_run03 \
  --output-dir outputs/countertrace_mini_math_20260310_merged01
```

Outputs:

- `outputs/countertrace_mini_math_20260310_seed17_run02/math_summary.json`
- `outputs/countertrace_mini_math_20260310_seed23_run03/math_summary.json`
- `outputs/countertrace_mini_math_20260310_merged01/math_summary.json`
- `outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl`

Observed summary:

- seed `17` run adds `6` verified traces
- seed `23` run adds `6` verified traces
- merged pool contains `16` unique verified traces
- merged example ids:
  - `gsm8k-00007`, `gsm8k-00045`, `gsm8k-00076`, `gsm8k-00096`
  - `gsm8k-00110`, `gsm8k-00135`, `gsm8k-00141`, `gsm8k-00145`
  - `gsm8k-00151`, `gsm8k-00164`, `gsm8k-00168`, `gsm8k-00220`
  - `gsm8k-00245`, `gsm8k-00312`, `gsm8k-00327`, `gsm8k-00579`

Interpretation:

- The math pipeline is no longer bottlenecked on a 4-trace toy pool.
- The next held-out audit can now test whether the apparent stability from `audit03` survives on a materially broader prefix distribution.

## 2026-03-10 Larger-Scale Stage A (`run08` / `run09`)

Status: completed as the first 16-trace joint Stage A rerun

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:0 --max-traces 4 --trace-offset 0  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run08_merged16_shard0
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:1 --max-traces 4 --trace-offset 4  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run08_merged16_shard1
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:2 --max-traces 4 --trace-offset 8  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run08_merged16_shard2
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:3 --max-traces 4 --trace-offset 12 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run08_merged16_shard3
python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run08_merged16_shard0 \
  outputs/math_stage_a_20260310_run08_merged16_shard1 \
  outputs/math_stage_a_20260310_run08_merged16_shard2 \
  outputs/math_stage_a_20260310_run08_merged16_shard3 \
  --output-dir outputs/math_stage_a_20260310_run08_merged16

python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:4 --max-traces 4 --trace-offset 0  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard0
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:5 --max-traces 4 --trace-offset 4  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard1
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:6 --max-traces 4 --trace-offset 8  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard2
python scripts/run_math_stage_a.py --resume --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:7 --max-traces 4 --trace-offset 12 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard3
python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard0 \
  outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard1 \
  outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard2 \
  outputs/math_stage_a_20260310_run09_qwen3_4b_merged16_shard3 \
  --output-dir outputs/math_stage_a_20260310_run09_qwen3_4b_merged16
```

Outputs:

- `outputs/math_stage_a_20260310_run08_merged16/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run08_merged16/stage_a_math_records.jsonl`
- `outputs/math_stage_a_20260310_run09_qwen3_4b_merged16/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run09_qwen3_4b_merged16/stage_a_math_records.jsonl`

Observed summary for `run08` (train-side 1.7B):

- `num_records = 48`
- `mean_original_solve = 0.8958`
- `mean_drop_solve = 0.8611`
- `mean_paraphrase_solve = 0.8611`
- `mean_swap_solve = 0.0729`
- `mean_n_t = 0.5602`
- `mean_n_t_weighted = 0.0172`
- `mean_stability = 0.1112`
- `mean_paraphrase_gap = 0.0347`
- `positive_n_fraction = 0.9167`

Observed summary for `run09` (held-out 4B):

- `num_records = 48`
- `mean_original_solve = 0.9444`
- `mean_drop_solve = 0.9236`
- `mean_paraphrase_solve = 0.9514`
- `mean_swap_solve = 0.2049`
- `mean_n_t = 0.5000`
- `mean_n_t_weighted = 0.0164`
- `mean_stability = 0.0999`
- `mean_paraphrase_gap = 0.0069`
- `positive_n_fraction = 0.8958`

Relative to the toy-scale `run06` / `run07`:

- held-out `mean_paraphrase_gap` improves further: `0.0278 -> 0.0069`
- held-out `mean_n_t_weighted` increases: `0.0111 -> 0.0164`
- train-side `mean_n_t_weighted` softens slightly: `0.0203 -> 0.0172`
- held-out `mean_swap_solve` remains the main pressure point: `0.1111 -> 0.2049`

Interpretation:

- The larger pool confirms that broad paraphrase instability is mostly solved.
- The object still survives on both continuators at 48-record scale.
- The dominant remaining failure mode is held-out swap repair, not paraphrase drift.

## 2026-03-10 Larger-Scale Cross-Continuator Audit (`audit04`)

Status: completed as the first larger-scale joint filter over the 16-trace pool

Reproducible command:

```bash
python scripts/audit_math_stage_a.py --train-records outputs/math_stage_a_20260310_run08_merged16/stage_a_math_records.jsonl --heldout-records outputs/math_stage_a_20260310_run09_qwen3_4b_merged16/stage_a_math_records.jsonl --output-dir outputs/math_stage_a_20260310_audit04
```

Outputs:

- `outputs/math_stage_a_20260310_audit04/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260310_audit04/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260310_audit04/stage_a_audit_kept.jsonl`

Observed summary:

- `num_pairs = 48`
- `num_kept = 26`
- `keep_fraction = 0.5417`
- `mean_train_n_t_weighted_all = 0.0172`
- `mean_heldout_n_t_weighted_all = 0.0164`
- `mean_train_n_t_weighted_kept = 0.0213`
- `mean_heldout_n_t_weighted_kept = 0.0242`
- `mean_train_paraphrase_gap_kept = 0.0`
- `mean_heldout_paraphrase_gap_kept = 0.0`

Observed drop reasons:

- `heldout_swap_solve = 15`
- `train_swap_solve = 6`
- `heldout_weighted_n = 5`
- `train_weighted_n = 4`
- `train_original_solve = 5`
- `heldout_original_solve = 2`
- `train_paraphrase_gap = 1`
- `heldout_paraphrase_gap = 1`

Relative to `audit03`:

- keep-set ratio drops from `0.75` to `0.5417`
- kept-sample paraphrase gaps stay perfect at `0.0 / 0.0`
- held-out weighted signal on the kept subset improves: `0.0158 -> 0.0242`
- the regression comes from more repairable swap cases entering the pool, not from paraphrase widening again

Failure concentration:

- fully dropped example families: `gsm8k-00076`, `gsm8k-00096`
- partially dropped but still salvageable families include `gsm8k-00007`, `gsm8k-00045`, `gsm8k-00135`, `gsm8k-00141`, `gsm8k-00145`, `gsm8k-00151`, `gsm8k-00164`, `gsm8k-00220`, `gsm8k-00245`

Interpretation:

- `audit03` was directionally real, but optimistic because it under-sampled swap-fragile traces.
- The scaled audit does not show object collapse: both all-pair weighted means remain positive, and the kept subset becomes stronger on held-out.
- The scaled audit does show that Week 2 is still not complete. The main blocker has shifted from paraphrase instability to held-out swap repair on a broader trace pool.

## 2026-03-10 Swap-Operation Repair: Targeted Smoke

Status: completed as a focused editor-fix validation pass

Code change:

- Tightened `fallback_swap_operation(...)` in `src/cnt_research/math/stage_a.py`.
- Arithmetic operator swaps are now bounded by plausibility checks instead of always flipping to the most extreme opposite operator.
- When an operator change would create an implausible or conspicuously repairable step, the operation family now falls back to a stronger local quantity perturbation instead of emitting an absurd equation.

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:0 --max-traces 3 --trace-offset 1 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_swapfix_smoke_train01

python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:4 --max-traces 3 --trace-offset 1 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_swapfix_smoke_heldout01
```

Outputs:

- `outputs/math_stage_a_20260310_swapfix_smoke_train01/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_swapfix_smoke_heldout01/stage_a_math_summary.json`

Observed summary for the held-out smoke subset (`gsm8k-00045`, `gsm8k-00076`, `gsm8k-00096`):

- old subset from `run09`: `mean_swap_solve = 0.4444`, `mean_n_t = 0.3210`, `mean_n_t_weighted = 0.0074`
- new subset after swap fix: `mean_swap_solve = 0.2037`, `mean_n_t = 0.4815`, `mean_n_t_weighted = 0.0111`

Representative per-record changes:

- `gsm8k-00045`, step `1`: held-out `swap_operation` solve falls from `1.0` to `0.3333`
- `gsm8k-00045`, step `6`: held-out `swap_operation` solve falls from `0.6667` to `0.0`
- `gsm8k-00076`, step `5`: held-out `swap_operation` solve falls from `1.0` to `0.0`
- `gsm8k-00096`, steps `1` and `2`: held-out `swap_operation` solve falls from `1.0` to `0.0`

Interpretation:

- The dominant larger-scale failure mode was in fact concentrated in the old operation family.
- This fix improves the exact subset that previously made `audit04` look fragile, without disturbing paraphrase behavior.

## 2026-03-10 Larger-Scale Rerun After Swap Fix (`run10` / `run11`)

Status: completed as the first full 48-pair rerun after tightening the operation editor

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:1 --max-traces 5 --trace-offset 0  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run10_swapfix_merged16_shard0
python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:2 --max-traces 5 --trace-offset 5  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run10_swapfix_merged16_shard1
python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --gpu cuda:3 --max-traces 6 --trace-offset 10 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run10_swapfix_merged16_shard2
python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run10_swapfix_merged16_shard0 \
  outputs/math_stage_a_20260310_run10_swapfix_merged16_shard1 \
  outputs/math_stage_a_20260310_run10_swapfix_merged16_shard2 \
  --output-dir outputs/math_stage_a_20260310_run10_swapfix_merged16

python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:5 --max-traces 5 --trace-offset 0  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard0
python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:6 --max-traces 5 --trace-offset 5  --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard1
python scripts/run_math_stage_a.py --success-trace-path outputs/countertrace_mini_math_20260310_merged01/math_success_traces.jsonl --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a --gpu cuda:7 --max-traces 6 --trace-offset 10 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard2
python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard0 \
  outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard1 \
  outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16_shard2 \
  --output-dir outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16
```

Outputs:

- `outputs/math_stage_a_20260310_run10_swapfix_merged16/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16/stage_a_math_summary.json`

Observed summary for `run10` (train-side 1.7B):

- `num_records = 48`
- `mean_swap_solve = 0.0208`
- `mean_n_t = 0.5949`
- `mean_n_t_weighted = 0.0182`
- `mean_paraphrase_gap = 0.0347`

Observed summary for `run11` (held-out 4B):

- `num_records = 48`
- `mean_swap_solve = 0.1146`
- `mean_n_t = 0.5602`
- `mean_n_t_weighted = 0.0180`
- `mean_paraphrase_gap = 0.0069`

Relative to `run08` / `run09`:

- train-side `mean_swap_solve`: `0.0729 -> 0.0208`
- held-out `mean_swap_solve`: `0.2049 -> 0.1146`
- train-side `mean_n_t_weighted`: `0.0172 -> 0.0182`
- held-out `mean_n_t_weighted`: `0.0164 -> 0.0180`
- paraphrase behavior is unchanged on both sides

Interpretation:

- The swap fix improves the actual bottleneck without buying that gain by worsening paraphrase or original solvability.
- The held-out signal is now not only surviving; it is quantitatively stronger than the pre-fix 48-pair baseline.

## 2026-03-10 Larger-Scale Audit After Swap Fix (`audit05`)

Status: completed as the current best larger-scale joint audit

Reproducible command:

```bash
python scripts/audit_math_stage_a.py --train-records outputs/math_stage_a_20260310_run10_swapfix_merged16/stage_a_math_records.jsonl --heldout-records outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16/stage_a_math_records.jsonl --output-dir outputs/math_stage_a_20260310_audit05
```

Outputs:

- `outputs/math_stage_a_20260310_audit05/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260310_audit05/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260310_audit05/stage_a_audit_kept.jsonl`

Observed summary:

- `num_pairs = 48`
- `num_kept = 35`
- `keep_fraction = 0.7292`
- `mean_train_n_t_weighted_all = 0.0182`
- `mean_heldout_n_t_weighted_all = 0.0180`
- `mean_train_n_t_weighted_kept = 0.0205`
- `mean_heldout_n_t_weighted_kept = 0.0230`
- `mean_train_paraphrase_gap_kept = 0.0190`
- `mean_heldout_paraphrase_gap_kept = 0.0`

Observed drop reasons:

- `heldout_swap_solve = 7`
- `heldout_weighted_n = 5`
- `train_original_solve = 5`
- `train_weighted_n = 4`
- `heldout_original_solve = 2`
- `heldout_paraphrase_gap = 1`
- `train_paraphrase_gap = 1`
- `train_swap_solve = 1`

Relative to `audit04`:

- keep-set grows from `26 / 48` to `35 / 48`
- `keep_fraction`: `0.5417 -> 0.7292`
- `heldout_swap_solve` drop count: `15 -> 7`
- `train_swap_solve` drop count: `6 -> 1`
- all-pair held-out weighted signal rises: `0.0164 -> 0.0180`

Composition change:

- `gsm8k-00045` now keeps all `3` audited steps instead of `2`
- `gsm8k-00220` now keeps all `3` audited steps instead of `2`
- `gsm8k-00096`, `gsm8k-00141`, `gsm8k-00145`, `gsm8k-00151`, and `gsm8k-00164` all gain one additional kept candidate relative to `audit04`
- the main remaining weak families are `gsm8k-00007`, `gsm8k-00076`, `gsm8k-00135`, and `gsm8k-00245`

Interpretation:

- This is the first larger-scale audit that nearly recovers the small-sample `audit03` keep rate while holding the full 48-pair pool fixed.
- The Week 2 bottleneck was indeed concentrated in the old operation family; after fixing it, the remaining failures are mostly low-original-solve or low-weighted-`N_t` prefixes rather than widespread held-out swap repair.
- This is a materially stronger pre-training state than `audit04`.

## 2026-03-10 Conservative Train-Side Filter (`filter01`)

Status: completed as the final conservative pre-training filter pass

Code change:

- Added train-side filtering support to `src/cnt_research/math/stage_a_audit.py`.
- Added `scripts/filter_math_stage_a_records.py` to produce aligned filtered train / held-out record files before a final audit.

Filter rule used:

- `train original solve == 1.0`
- `train paraphrase gap == 0.0`

Reproducible command:

```bash
python scripts/filter_math_stage_a_records.py \
  --train-records outputs/math_stage_a_20260310_run10_swapfix_merged16/stage_a_math_records.jsonl \
  --heldout-records outputs/math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16/stage_a_math_records.jsonl \
  --train-min-original-solve 1.0 \
  --train-max-paraphrase-gap 0.0 \
  --output-dir outputs/math_stage_a_20260310_filter01_conservative
```

Outputs:

- `outputs/math_stage_a_20260310_filter01_conservative/filter_summary.json`
- `outputs/math_stage_a_20260310_filter01_conservative/filtered_train_records.jsonl`
- `outputs/math_stage_a_20260310_filter01_conservative/filtered_heldout_records.jsonl`
- `outputs/math_stage_a_20260310_filter01_conservative/filtered_manifest.jsonl`

Observed summary:

- candidate universe shrinks from `48` to `40`
- removed candidates are concentrated in:
  - low train original solve (`gsm8k-00007`, `gsm8k-00135`, `gsm8k-00245`)
  - train-side paraphrase-instability edge cases (`gsm8k-00045`, `gsm8k-00151`)
- filter counts:
  - `train_prefilter_original_solve = 7`
  - `train_prefilter_paraphrase_gap = 4`

Interpretation:

- This is a true conservative filter, not a held-out-informed pruning pass.
- It removes the small number of surviving edge cases that were still only barely acceptable on the train-side invariance checks.

## 2026-03-10 Final Conservative Audit (`audit06`)

Status: completed as the strictest current pre-training audit

Reproducible command:

```bash
python scripts/audit_math_stage_a.py \
  --train-records outputs/math_stage_a_20260310_filter01_conservative/filtered_train_records.jsonl \
  --heldout-records outputs/math_stage_a_20260310_filter01_conservative/filtered_heldout_records.jsonl \
  --output-dir outputs/math_stage_a_20260310_audit06_conservative
```

Outputs:

- `outputs/math_stage_a_20260310_audit06_conservative/stage_a_audit_summary.json`
- `outputs/math_stage_a_20260310_audit06_conservative/stage_a_audit_records.jsonl`
- `outputs/math_stage_a_20260310_audit06_conservative/stage_a_audit_kept.jsonl`

Observed summary:

- `num_pairs = 40`
- `num_kept = 33`
- `keep_fraction = 0.8250`
- `mean_train_n_t_weighted_all = 0.0201`
- `mean_heldout_n_t_weighted_all = 0.0200`
- `mean_train_n_t_weighted_kept = 0.0209`
- `mean_heldout_n_t_weighted_kept = 0.0235`
- `mean_train_paraphrase_gap_kept = 0.0`
- `mean_heldout_paraphrase_gap_kept = 0.0`

Observed drop reasons:

- `heldout_swap_solve = 6`
- `heldout_weighted_n = 3`
- `heldout_original_solve = 1`
- `train_swap_solve = 1`
- `train_weighted_n = 1`

Relative to `audit05`:

- candidate pool shrinks: `48 -> 40`
- kept count shrinks mildly: `35 -> 33`
- within-pool keep fraction improves: `0.7292 -> 0.8250`
- all-pair weighted means rise on both sides:
  - train: `0.0182 -> 0.0201`
  - held-out: `0.0180 -> 0.0200`
- kept-set paraphrase gaps become perfectly clean: `0.0 / 0.0`

Interpretation:

- `audit05` was already good enough to train on; `audit06` is the stricter, cleaner version of that same keep-set.
- The cost of going conservative is small (`35 -> 33` kept), while the training pool gets materially cleaner and easier to interpret.
- This is the strongest current evidence chain for entering matched training without carrying avoidable Stage A noise.

## 2026-03-10 Stage B Matched Training Pilot

Status: completed as the first end-to-end matched training pilot sequence

Code added:

- `src/cnt_research/math/stage_b.py`
- `scripts/build_math_stage_b_data.py`
- `scripts/run_math_stage_b_training.py`
- `scripts/eval_math_stage_b_rollout.py`

### Dataset build + trainer

What landed:

- within-prefix Stage B dataset builder for `sft / necessity pair / paraphrase consistency pair`
- question-held-out split support
- minimal `torch + transformers` trainer for
  - `L_sft`
  - `lambda_N * L_pref`
  - `lambda_inv * L_equiv`
- rollout-style evaluation that reuses Stage A prefixes and reports object-level solve metrics after training

Primary dataset outputs:

- `outputs/math_stage_b_20260310_dataset01/train_rows.jsonl`
- `outputs/math_stage_b_20260310_dataset01/eval_rows.jsonl`
- `outputs/math_stage_b_20260310_dataset01/stage_b_dataset_summary.json`

Key dataset summary:

- `33` conservative kept pairs expand to `68` train rows and `30` eval rows
- split is question-held-out over `16` unique GSM8K problems
- eval example ids:
  - `gsm8k-00141`
  - `gsm8k-00164`
  - `gsm8k-00168`
  - `gsm8k-00327`

### Step-only local training (`smoke01`)

Reproducible commands:

```bash
python scripts/build_math_stage_b_data.py \
  --output-dir outputs/math_stage_b_20260310_dataset01

python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset01 \
  --gpu cuda:0 \
  --epochs 1 \
  --output-dir outputs/math_stage_b_20260310_smoke01

python scripts/eval_math_stage_b_rollout.py \
  --model-dir /cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e \
  --gpu cuda:1 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_base_lc120

python scripts/eval_math_stage_b_rollout.py \
  --model-dir outputs/math_stage_b_20260310_smoke01/model \
  --gpu cuda:2 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke01_lc120
```

Outputs:

- `outputs/math_stage_b_20260310_smoke01/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_base_lc120/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_smoke01_lc120/stage_b_rollout_summary.json`

Observed result:

- local offline metrics improved a little:
  - eval `sft_nll_mean`: `1.3823 -> 1.3304`
- but object-level rollout metrics moved the wrong way:
  - `mean_drop_solve`: `0.7000 -> 0.8000`
  - `mean_n_t`: `0.6667 -> 0.6333`
  - `mean_n_t_weighted`: `0.2133 -> 0.1152`

Interpretation:

- local next-step preference is too easy and already saturated at base-model level
- as a research metric it is not sufficient; it can improve while the actual necessity object weakens under full continuation

### Rollout-suffix training with continuator-generated positives (`smoke02`, `smoke03`)

Reproducible commands:

```bash
python scripts/build_math_stage_b_data.py \
  --completion-mode rollout \
  --rollout-style locked_careful \
  --output-dir outputs/math_stage_b_20260310_dataset02_rollout

python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset02_rollout \
  --gpu cuda:0 \
  --epochs 1 \
  --max-length 1536 \
  --output-dir outputs/math_stage_b_20260310_smoke02_rollout

python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset02_rollout \
  --gpu cuda:0 \
  --epochs 1 \
  --learning-rate 2e-7 \
  --max-length 1536 \
  --output-dir outputs/math_stage_b_20260310_smoke03_rollout_lr2e7
```

Outputs:

- `outputs/math_stage_b_20260310_dataset02_rollout/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260310_smoke02_rollout/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_smoke03_rollout_lr2e7/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_smoke02_rollout_lc120/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_smoke03_rollout_lr2e7_lc120/stage_b_rollout_summary.json`

Observed result:

- both rollout versions still hurt held-out object metrics
- for both `smoke02` and `smoke03`:
  - `mean_original_solve = 0.8000`
  - `mean_drop_solve = 0.7000`
  - `mean_n_t = 0.5667`
  - `mean_n_t_weighted = 0.2105`
- the main failure concentrates on `gsm8k-00164`, where the tuned model flips the original-prefix continuation from correct to incorrect

Diagnosis:

- the chosen rollout suffix was taken from Stage A continuator completions
- some of those completions are verifier-correct but locally dirty, e.g. for `gsm8k-00164` the suffix says
  - step content implies `90`
  - final answer is `15`
- training on these dirty positives can poison the policy even when the verifier says the suffix is correct

### Clean-positive rollout training (`smoke04`)

Reproducible commands:

```bash
python scripts/build_math_stage_b_data.py \
  --completion-mode rollout \
  --chosen-source success_trace \
  --rollout-style locked_careful \
  --output-dir outputs/math_stage_b_20260310_dataset03_cleanchosen

python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset03_cleanchosen \
  --gpu cuda:0 \
  --epochs 1 \
  --learning-rate 1e-6 \
  --max-length 1536 \
  --output-dir outputs/math_stage_b_20260310_smoke04_cleanchosen

python scripts/eval_math_stage_b_rollout.py \
  --dataset-summary outputs/math_stage_b_20260310_dataset03_cleanchosen/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260310_smoke04_cleanchosen/model \
  --gpu cuda:2 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120
```

Outputs:

- `outputs/math_stage_b_20260310_dataset03_cleanchosen/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260310_smoke04_cleanchosen/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120/stage_b_rollout_summary.json`

Observed result:

- clean-positive chosen suffixes fix the `gsm8k-00164` collapse
- held-out rollout metrics return to the base-model level:
  - base:
    - `mean_original_solve = 0.9000`
    - `mean_drop_solve = 0.7000`
    - `mean_n_t = 0.6667`
    - `mean_n_t_weighted = 0.2133`
  - `smoke04_cleanchosen`:
    - `mean_original_solve = 0.9000`
    - `mean_drop_solve = 0.7000`
    - `mean_n_t = 0.6667`
    - `mean_n_t_weighted = 0.2133`
- offline eval remains slightly better on the clean-positive run:
  - eval `sft_nll_mean`: `0.4302 -> 0.4196`
  - eval `equiv_abs_gap_mean`: `0.3578 -> 0.3544`

Interpretation:

- the first clean-positive rollout pilot is the first Stage B version that is not actively harmful on the held-out object-level gate
- it is still a no-gain result on the current held-out rollout metric, not yet a positive Week 3 win
- the research bottleneck has narrowed:
  - not `N_t` object failure
  - not editor failure
  - not keep-set impurity
  - but positive-suffix purity and how aggressively offline training moves the policy from a strong base model

### Matched SFT Control (`control01`)

Reproducible commands:

```bash
python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset03_cleanchosen \
  --gpu cuda:0 \
  --epochs 1 \
  --learning-rate 1e-6 \
  --max-length 1536 \
  --lambda-n 0.0 \
  --lambda-inv 0.0 \
  --output-dir outputs/math_stage_b_20260310_control01_sftonly

python scripts/eval_math_stage_b_rollout.py \
  --dataset-summary outputs/math_stage_b_20260310_dataset03_cleanchosen/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260310_control01_sftonly/model \
  --gpu cuda:2 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_control01_sftonly_lc120
```

Outputs:

- `outputs/math_stage_b_20260310_control01_sftonly/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_control01_sftonly_lc120/stage_b_rollout_summary.json`

Observed result:

- the matched SFT-only control is also no-harm on the held-out rollout gate
- rollout metrics are identical to base and `smoke04_cleanchosen`:
  - `mean_original_solve = 0.9000`
  - `mean_drop_solve = 0.7000`
  - `mean_n_t = 0.6667`
  - `mean_n_t_weighted = 0.2133`
- offline eval is slightly better than `smoke04_cleanchosen` on this small split:
  - control `sft_nll_mean = 0.4141`
  - `smoke04_cleanchosen sft_nll_mean = 0.4196`

Interpretation:

- at the current smoke scale, clean-positive CNT has not yet separated itself from matched SFT-only training
- this is exactly the proposal's matched-data control question, and right now the answer is:
  - `no visible CNT-specific gain yet`

### Stronger Clean-Positive CNT (`smoke05`)

Reproducible commands:

```bash
python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260310_dataset03_cleanchosen \
  --gpu cuda:0 \
  --epochs 2 \
  --learning-rate 5e-7 \
  --max-length 1536 \
  --output-dir outputs/math_stage_b_20260310_smoke05_cleanchosen_e2_lr5e7

python scripts/eval_math_stage_b_rollout.py \
  --dataset-summary outputs/math_stage_b_20260310_dataset03_cleanchosen/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260310_smoke05_cleanchosen_e2_lr5e7/model \
  --gpu cuda:2 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke05_cleanchosen_e2_lr5e7_lc120
```

Outputs:

- `outputs/math_stage_b_20260310_smoke05_cleanchosen_e2_lr5e7/stage_b_training_summary.json`
- `outputs/math_stage_b_20260310_rollout_eval_smoke05_cleanchosen_e2_lr5e7_lc120/stage_b_rollout_summary.json`

Observed result:

- the stronger clean-positive CNT schedule remains no-harm
- held-out rollout metrics are still identical to base / control / `smoke04`:
  - `mean_original_solve = 0.9000`
  - `mean_drop_solve = 0.7000`
  - `mean_n_t = 0.6667`
  - `mean_n_t_weighted = 0.2133`
- offline eval moves only slightly:
  - `sft_nll_mean = 0.4233`
  - `pref_margin_mean = 0.2910`

Interpretation:

- the current Stage B state is now well identified:
  - harmful variants have been removed
  - a stable no-harm training path exists
  - but neither clean-positive CNT nor a slightly stronger CNT schedule beats matched SFT-only control on the current held-out rollout gate
- so the next Week 3 bottleneck is no longer data cleanliness; it is finding a training/eval regime where CNT-specific signal can actually separate from matched SFT

### Multi-Split Matched-Control Comparison (`split_compare`)

Reproducible commands:

```bash
python scripts/run_math_stage_b_split_compare.py --split-seed 5  --train-gpu cuda:4 --eval-gpu cuda:5 --epochs 1 --learning-rate 1e-6 --output-root outputs/math_stage_b_20260310_split_compare
python scripts/run_math_stage_b_split_compare.py --split-seed 23 --train-gpu cuda:0 --eval-gpu cuda:1 --epochs 1 --learning-rate 1e-6 --output-root outputs/math_stage_b_20260310_split_compare
python scripts/run_math_stage_b_split_compare.py --split-seed 41 --train-gpu cuda:2 --eval-gpu cuda:3 --epochs 1 --learning-rate 1e-6 --output-root outputs/math_stage_b_20260310_split_compare
python scripts/run_math_stage_b_split_compare.py --split-seed 77 --train-gpu cuda:6 --eval-gpu cuda:7 --epochs 1 --learning-rate 1e-6 --output-root outputs/math_stage_b_20260310_split_compare
```

Verification:

```bash
python -m py_compile scripts/run_math_stage_b_split_compare.py
```

Outputs:

- `outputs/math_stage_b_20260310_split_compare/seed05/comparison_summary.json`
- `outputs/math_stage_b_20260310_split_compare/seed23/comparison_summary.json`
- `outputs/math_stage_b_20260310_split_compare/seed41/comparison_summary.json`
- `outputs/math_stage_b_20260310_split_compare/seed77/comparison_summary.json`
- `outputs/math_stage_b_20260310_split_compare/multisplit_summary.json`

Observed result:

- the clean-positive Stage B comparison is no longer based on one split only; there are now four new split-specific base/control/CNT comparisons plus the earlier split-17 baseline
- at `continuation_max_new_tokens = 120`, three of the four new splits (`05`, `41`, `77`) are exact ties between matched SFT-only control and CNT on the held-out rollout gate
- only `seed23` shows a non-zero rollout delta:
  - `delta mean_drop_solve = -0.1250`
  - `delta mean_n_t = +0.0417`
  - `delta mean_n_t_weighted = +0.1226`
- aggregating the five available lc120 splits (`05`, `17`, `23`, `41`, `77`) gives:
  - `nonzero_delta_seeds_lc120 = [23]`
  - `mean_delta_n_t_weighted_lc120 = 0.0245`
  - `mean_delta_n_t_lc120 = 0.0083`
  - `mean_delta_drop_solve_lc120 = -0.0250`

Interpretation:

- the current Week 3 picture is still "mostly tied", not a robust CNT win
- the one apparent positive split is isolated and must be stress-tested before being counted as evidence

### Seed23 Continuation-Budget Recheck (`lc160`)

Reproducible commands:

```bash
python scripts/eval_math_stage_b_rollout.py \
  --train-records outputs/math_stage_a_20260310_filter01_conservative/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit06_conservative/stage_a_audit_kept.jsonl \
  --dataset-summary outputs/math_stage_b_20260310_split_compare/seed23/dataset/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260310_split_compare/seed23/control_sftonly/model \
  --gpu cuda:0 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 160 \
  --output-dir outputs/math_stage_b_20260310_split_compare/seed23/control_rollout_lc160

python scripts/eval_math_stage_b_rollout.py \
  --train-records outputs/math_stage_a_20260310_filter01_conservative/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit06_conservative/stage_a_audit_kept.jsonl \
  --dataset-summary outputs/math_stage_b_20260310_split_compare/seed23/dataset/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260310_split_compare/seed23/cnt/model \
  --gpu cuda:1 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 160 \
  --output-dir outputs/math_stage_b_20260310_split_compare/seed23/cnt_rollout_lc160
```

Outputs:

- `outputs/math_stage_b_20260310_split_compare/seed23/control_rollout_lc160/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260310_split_compare/seed23/cnt_rollout_lc160/stage_b_rollout_summary.json`

Observed result:

- the only apparent lc120 gain disappears at `continuation_max_new_tokens = 160`
- on the recheck, control and CNT are again identical:
  - `mean_original_solve = 1.0000`
  - `mean_drop_solve = 1.0000`
  - `mean_n_t = 0.6667`
  - `mean_n_t_weighted = 0.0190`
- the lc120 delta came entirely from one record, `gsm8k-00145 @ step 0`
- on that record, the control model had already reconstructed the correct dropped-step reasoning but left `Final answer:` blank under the tighter 120-token budget

Interpretation:

- the seed23 offset is a rollout-budget / answer-formatting artifact, not yet a robust CNT-specific gain
- after the budget recheck, the strongest current Stage B claim remains:
  - clean-positive CNT is no-harm
  - but it still does not beat matched SFT-only control under a budget-robust held-out rollout gate

### Robust Rollout Gate Hardening And Deterministic Rescore

Code changes:

- added `extract_verifiable_answer(...)` in `src/cnt_research/math/countertrace_mini.py`
- updated `src/cnt_research/math/stage_a.py` and `src/cnt_research/math/stage_b.py` to use the new verdict logic
- added `scripts/rescore_math_stage_b_rollout.py`
- added `scripts/summarize_math_stage_b_multisplit.py`

Reproducible commands:

```bash
python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_base_lc120_v2/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_base_lc120_v2_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_control01_sftonly_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_control01_sftonly_lc120_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_smoke01_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke01_lc120_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_smoke02_rollout_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke02_rollout_lc120_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_smoke03_rollout_lr2e7_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke03_rollout_lr2e7_lc120_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_rollout_eval_smoke05_cleanchosen_e2_lr5e7_lc120/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_rollout_eval_smoke05_cleanchosen_e2_lr5e7_lc120_robust

for seed in 05 23 41 77; do
  python scripts/rescore_math_stage_b_rollout.py \
    --records-path outputs/math_stage_b_20260310_split_compare/seed${seed}/base_rollout/stage_b_rollout_records.jsonl \
    --output-dir outputs/math_stage_b_20260310_split_compare/seed${seed}/base_rollout_robust
  python scripts/rescore_math_stage_b_rollout.py \
    --records-path outputs/math_stage_b_20260310_split_compare/seed${seed}/control_rollout/stage_b_rollout_records.jsonl \
    --output-dir outputs/math_stage_b_20260310_split_compare/seed${seed}/control_rollout_robust
  python scripts/rescore_math_stage_b_rollout.py \
    --records-path outputs/math_stage_b_20260310_split_compare/seed${seed}/cnt_rollout/stage_b_rollout_records.jsonl \
    --output-dir outputs/math_stage_b_20260310_split_compare/seed${seed}/cnt_rollout_robust
done

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_split_compare/seed23/control_rollout_lc160/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_split_compare/seed23/control_rollout_lc160_robust

python scripts/rescore_math_stage_b_rollout.py \
  --records-path outputs/math_stage_b_20260310_split_compare/seed23/cnt_rollout_lc160/stage_b_rollout_records.jsonl \
  --output-dir outputs/math_stage_b_20260310_split_compare/seed23/cnt_rollout_lc160_robust

python scripts/summarize_math_stage_b_multisplit.py
```

Verification:

```bash
python -m py_compile \
  src/cnt_research/math/countertrace_mini.py \
  src/cnt_research/math/stage_a.py \
  src/cnt_research/math/stage_b.py \
  scripts/rescore_math_stage_b_rollout.py \
  scripts/summarize_math_stage_b_multisplit.py
```

Outputs:

- `outputs/math_stage_b_20260310_rollout_eval_base_lc120_v2_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_control01_sftonly_lc120_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_smoke01_lc120_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_smoke02_rollout_lc120_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_smoke03_rollout_lr2e7_lc120_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_smoke04_cleanchosen_lc120_robust/`
- `outputs/math_stage_b_20260310_rollout_eval_smoke05_cleanchosen_e2_lr5e7_lc120_robust/`
- `outputs/math_stage_b_20260310_split_compare/multisplit_summary_robust.json`

Observed result:

- the rollout verdict is now robust to two concrete formatting failures:
  - blank `Final answer:` stubs
  - currency/percent-marked final answers like `Final answer: $15`
- under the hardened gate, the clean Stage B variants are still exact ties:
  - base / matched SFT-only / `smoke04_cleanchosen` / `smoke05_cleanchosen`
  - `mean_original_solve = 0.9000`
  - `mean_drop_solve = 0.8000`
  - `mean_n_t = 0.6333`
  - `mean_n_t_weighted = 0.1152`
- the 5-split robust matched-control aggregate in `multisplit_summary_robust.json` is now completely flat:
  - `nonzero_delta_seeds_lc120 = []`
  - `mean_delta_n_t_weighted_lc120 = 0.0000`
  - `mean_delta_n_t_lc120 = 0.0000`
  - `mean_delta_drop_solve_lc120 = 0.0000`
- the old `seed23` positive split is gone even before the lc160 recheck; the lc160 robust recheck remains exactly zero
- the earlier `smoke01` harm claim does not survive the hardened gate:
  - `smoke01` now ties the base model on the robust rollout summary
- the dirty rollout-positive variants are still not acceptable:
  - `smoke02` / `smoke03` keep `mean_drop_solve = 0.7000`, but lower `mean_original_solve` to `0.8000`

Interpretation:

- several Stage B deltas at smoke scale were gate artifacts rather than stable training effects
- after hardening the gate, the strongest clean result is stricter than before:
  - clean-positive CNT is still no-harm
  - matched SFT-only is still tied with it
  - there is still no robust CNT-specific gain
- the dirty rollout-positive diagnosis still holds, but it should now be stated in utility terms:
  - they hurt original solvability
  - not as a clean "weighted-necessity collapse" story under the hardened gate
- this supersedes the earlier provisional reading that `seed23` showed a positive split and that `smoke01` was clearly harmful

### Disjoint 4-Fold Stage B Comparison

Code changes:

- extended `build_stage_b_dataset(...)` in `src/cnt_research/math/stage_b.py` to accept explicit eval ids
- added `scripts/run_math_stage_b_fold_compare.py`
- added `scripts/summarize_math_stage_b_fold_compare.py`

Reproducible commands:

```bash
python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 0 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --output-root outputs/math_stage_b_20260310_fold_compare

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 1 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --output-root outputs/math_stage_b_20260310_fold_compare

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 2 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:4 --eval-gpu cuda:5 \
  --epochs 1 --learning-rate 1e-6 \
  --output-root outputs/math_stage_b_20260310_fold_compare

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 3 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:6 --eval-gpu cuda:7 \
  --epochs 1 --learning-rate 1e-6 \
  --output-root outputs/math_stage_b_20260310_fold_compare

python scripts/summarize_math_stage_b_fold_compare.py
```

Verification:

```bash
python -m py_compile \
  src/cnt_research/math/stage_b.py \
  scripts/run_math_stage_b_fold_compare.py \
  scripts/summarize_math_stage_b_fold_compare.py
```

Outputs:

- `outputs/math_stage_b_20260310_fold_compare/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare/fold_compare_summary.json`

Observed result:

- this is not another random-seed smoke; the four folds are disjoint and jointly cover all `16` unique eval examples in the conservative Stage B pool
- every fold is an exact rollout tie between matched SFT-only control and CNT:
  - `nonzero_delta_folds = []`
  - `mean_delta_n_t_weighted = 0.0000`
  - `mean_delta_n_t = 0.0000`
  - `mean_delta_drop_solve = 0.0000`
- the aggregated summary reports:
  - `num_unique_eval_examples = 16`
  - `all_eval_ids_disjoint = true`
- fold structure is now explicit rather than sampled:
  - fold00 is the hard slice (`gsm8k-00141 / 00164 / 00168 / 00327`) with `mean_n_t_weighted = 0.1152`
  - fold01 / fold02 / fold03 are all easy slices with exact control/CNT ties
- offline deltas remain small and mixed-sign across folds, and none translate into rollout separation

Interpretation:

- the Week 3 null result is now much stronger than before
- after hardening the gate and replacing random split sampling with full-coverage disjoint folds, the clean-positive CNT recipe still does not separate from matched SFT-only control
- therefore split noise is no longer a plausible main explanation
- the bottleneck has moved to the training signal itself, not to the evaluation split

### Stage B Signal-Shape Iteration: Original-Prefix Anchor And Rollout Pairing

Code changes:

- extended `build_stage_b_dataset(...)` in `src/cnt_research/math/stage_b.py` with:
  - `anchor_mode`
  - `_build_success_trace_suffix(...)`
  - `original-prefix` rollout-anchor SFT rows
- added `--anchor-mode` to `scripts/build_math_stage_b_data.py`
- added `--anchor-mode` to `scripts/run_math_stage_b_fold_compare.py`

Reproducible commands:

```bash
python -m py_compile \
  src/cnt_research/math/stage_b.py \
  scripts/build_math_stage_b_data.py \
  scripts/run_math_stage_b_fold_compare.py

python scripts/build_math_stage_b_data.py \
  --completion-mode rollout \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --weight-source heldout \
  --chosen-source success_trace \
  --eval-examples 4 \
  --split-seed 17 \
  --output-dir outputs/math_stage_b_20260310_dataset04_anchor_smoke

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 0 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal02_anchor

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 0 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 1 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 2 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:4 --eval-gpu cuda:5 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair

python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 3 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:6 --eval-gpu cuda:7 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair \
  --output-path outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260310_dataset04_anchor_smoke/`
- `outputs/math_stage_b_20260310_fold_compare_signal02_anchor/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair/fold_compare_summary.json`

Observed result:

- the new anchor dataset adds one extra `original-prefix` rollout SFT row per kept pair:
  - on the hard fold00 split, train rows grow from `68` to `91`
  - `sft` rows grow from `23` to `46`
- anchor alone is not enough:
  - `signal02` (`anchor + step pair`) is still an exact control/CNT tie on hard fold00
  - it preserves the old failure: `base 0.9 / 0.8 -> control = cnt 0.8 / 0.7` for `mean_original_solve / mean_drop_solve`
- pairing must align to rollout to produce any separation:
  - in hard fold00, `signal03` (`anchor + rollout pair`) moves `cnt` back to the base-model rollout while control still drops
  - fold00:
    - base: `mean_original_solve = 0.9000`, `mean_drop_solve = 0.8000`, `mean_n_t = 0.6333`, `mean_n_t_weighted = 0.1152`
    - control: `0.8000`, `0.7000`, `0.5667`, `0.2105`
    - cnt: `0.9000`, `0.8000`, `0.6333`, `0.1152`
    - delta(cnt - control): `mean_original_solve = +0.1000`, `mean_drop_solve = +0.1000`, `mean_n_t = +0.0667`, `mean_n_t_weighted = -0.0952`
- expanding `signal03` to the full disjoint 4-fold comparison gives:
  - `nonzero_delta_folds = [0]`
  - `mean_delta_drop_solve = +0.0250`
  - `mean_delta_n_t = +0.0167`
  - `mean_delta_n_t_weighted = -0.0238`
  - fold01 / fold02 / fold03 stay exact ties, so the current gain is concentrated on the hardest slice rather than spread across the easy folds

Interpretation:

- `original-prefix` anchoring by itself does not solve the Week 3 control/CNT tie
- the first signal shape that actually separates CNT from matched SFT-only under the hardened gate is:
  - clean chosen rollout suffixes from success traces
  - `original-prefix` rollout anchors
  - rollout-aligned pair losses
- the separation is not yet broad enough to call a robust Week 3 win:
  - only fold00 moves
  - fold01 / fold02 / fold03 remain ties
- the negative aggregate `mean_delta_n_t_weighted` should not be read as "CNT got worse" by itself:
  - in fold00, matched SFT-only lowers both original and drop solvability in a more uniform way, which raises the stability term and can inflate weighted `N_t` despite worse utility
  - for Stage B, `mean_original_solve` and `mean_drop_solve` now need to be read alongside weighted `N_t`, not after it
- this supersedes the previous flat-null reading in one important way:
  - the best current training-signal recipe is no longer "nothing separates"
  - it is now "rollout-paired CNT repairs the hard slice while matched SFT-only still harms it"

### Signal03 Budget Stress Test At `lc160`

Reproducible command:

```bash
python scripts/run_math_stage_b_fold_compare.py \
  --fold-index 0 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 160 \
  --output-root outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair_lc160
```

Output:

- `outputs/math_stage_b_20260310_fold_compare_signal03_anchor_rolloutpair_lc160/fold00/comparison_summary.json`

Observed result:

- widening the continuation budget from `120` to `160` removes the hard-fold repair:
  - base: `mean_original_solve = 1.0000`, `mean_drop_solve = 1.0000`, `mean_n_t = 0.6667`, `mean_n_t_weighted = 0.0190`
  - control: `0.9000`, `0.9000`, `0.6000`, `0.1143`
  - cnt: `0.9000`, `0.9000`, `0.6000`, `0.1143`
  - delta(cnt - control): all rollout metrics return to `0.0`
- because the decisive hard slice already collapsed back to a tie, the wider-budget stress test was not expanded to fold01 / fold02 / fold03

Interpretation:

- `signal03` is more promising than the earlier flat-null recipes, but it is not yet budget-robust
- the fold00 repair at `lc120` is therefore not strong enough to promote `signal03` to the new Week 3 default
- the correct reading is now:
  - `anchor + rollout pair` can create a hard-slice separation under the hardened `lc120` gate
  - that separation disappears under `lc160`
  - so the current recipe still has not crossed the proposal-quality bar for a stable Week 3 win

### GSM8K-Hard Stage B Slice

Code changes:

- extended `scripts/run_math_stage_b_fold_compare.py` to support explicit eval-id slices via:
  - `--eval-example-ids-path`
  - `--run-name`
- added `scripts/select_math_stage_b_hard_slice.py`

Reproducible commands:

```bash
python -m py_compile \
  scripts/run_math_stage_b_fold_compare.py \
  scripts/select_math_stage_b_hard_slice.py

python scripts/select_math_stage_b_hard_slice.py \
  --output-path outputs/math_stage_b_20260310_gsm8k_hard_slice/hard_slice_summary.json

python scripts/run_math_stage_b_fold_compare.py \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice/hard_slice_summary.json \
  --run-name hard_lc120 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03

python scripts/run_math_stage_b_fold_compare.py \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice/hard_slice_summary.json \
  --run-name hard_lc160 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 160 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03
```

Outputs:

- `outputs/math_stage_b_20260310_gsm8k_hard_slice/hard_slice_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03/hard_lc120/comparison_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03/hard_lc160/comparison_summary.json`

Observed result:

- the `GSM8K-hard` slice is defined using only pre-existing artifacts:
  - select examples whose mean Stage B base-rollout original/drop solve at `lc120` is below `1.0`, or whose mean Stage A held-out original/drop solve is below `1.0`
- this rule selects exactly four conservative-core examples:
  - `gsm8k-00007`
  - `gsm8k-00141`
  - `gsm8k-00164`
  - `gsm8k-00327`
- on this harder slice, the base model is no longer trivially saturated at `lc120`:
  - base: `mean_original_solve = 0.8750`, `mean_drop_solve = 0.7500`, `mean_n_t = 0.6250`, `mean_n_t_weighted = 0.1393`
  - control: `0.7500`, `0.6250`, `0.5417`, `0.2583`
  - cnt: `0.8750`, `0.7500`, `0.6250`, `0.1393`
  - delta(cnt - control): `mean_original_solve = +0.1250`, `mean_drop_solve = +0.1250`, `mean_n_t = +0.0833`, `mean_n_t_weighted = -0.1190`
- crucially, unlike the earlier fold00 result, this separation survives the wider budget:
  - at `lc160`:
    - base: `1.0000`, `1.0000`, `0.6667`, `0.0190`
    - control: `0.8750`, `0.8750`, `0.5833`, `0.1381`
    - cnt: `1.0000`, `1.0000`, `0.6667`, `0.0190`
    - delta(cnt - control): again `mean_original_solve = +0.1250`, `mean_drop_solve = +0.1250`, `mean_n_t = +0.0833`, `mean_n_t_weighted = -0.1190`

Interpretation:

- the user's concern was correct: the old Stage B conservative core had too much ceiling pressure from easy GSM8K slices
- once evaluation is restricted to the `GSM8K-hard` subset, the current `signal03` recipe becomes much more informative
- this is the first Stage B result that is both:
  - post-hardening
  - budget-robust across `lc120 -> lc160`
- the positive signal is still small-sample and slice-specific, so it is not yet a full-domain Week 3 win
- but it is strong enough to change the research reading:
  - the null result is no longer "CNT cannot separate on GSM8K"
  - it is now "CNT does not separate on the easy-heavy conservative core, but it does separate on the non-ceiling GSM8K-hard slice"

## 2026-03-10 Expanded 30-Trace Conservative Core (`merged02 -> run12/run13 -> audit07`)

Status: completed as the first Stage A rerun over a `30`-trace verified GSM8K pool

Code changes:

- extended `scripts/select_math_stage_b_hard_slice.py` with `--selection-source`, including an `audit_only` mode for larger conservative pools that do not yet have matching Stage B base-rollout artifacts

Reproducible commands:

```bash
python -m py_compile scripts/select_math_stage_b_hard_slice.py

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 64 \
  --target-successes 8 \
  --seed 31 \
  --gpu cuda:0 \
  --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260310_seed31_run04

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 64 \
  --target-successes 8 \
  --seed 47 \
  --gpu cuda:1 \
  --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260310_seed47_run05

PYTHONPATH=src python scripts/merge_countertrace_mini_math.py \
  outputs/countertrace_mini_math_20260310_merged01 \
  outputs/countertrace_mini_math_20260310_seed31_run04 \
  outputs/countertrace_mini_math_20260310_seed47_run05 \
  --output-dir outputs/countertrace_mini_math_20260310_merged02

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --gpu cuda:0 \
  --max-traces 10 --trace-offset 0 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run12_merged30_shard0

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --gpu cuda:1 \
  --max-traces 10 --trace-offset 10 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run12_merged30_shard1

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --gpu cuda:2 \
  --max-traces 10 --trace-offset 20 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run12_merged30_shard2

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a \
  --gpu cuda:4 \
  --max-traces 10 --trace-offset 0 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard0

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a \
  --gpu cuda:5 \
  --max-traces 10 --trace-offset 10 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard1

PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a \
  --gpu cuda:6 \
  --max-traces 10 --trace-offset 20 \
  --max-candidates-per-trace 3 \
  --continuation-max-new-tokens 220 \
  --edit-max-new-tokens 48 \
  --output-dir outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard2

PYTHONPATH=src python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run12_merged30_shard0 \
  outputs/math_stage_a_20260310_run12_merged30_shard1 \
  outputs/math_stage_a_20260310_run12_merged30_shard2 \
  --output-dir outputs/math_stage_a_20260310_run12_merged30

PYTHONPATH=src python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard0 \
  outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard1 \
  outputs/math_stage_a_20260310_run13_qwen3_4b_merged30_shard2 \
  --output-dir outputs/math_stage_a_20260310_run13_qwen3_4b_merged30

PYTHONPATH=src python scripts/filter_math_stage_a_records.py \
  --train-records outputs/math_stage_a_20260310_run12_merged30/stage_a_math_records.jsonl \
  --heldout-records outputs/math_stage_a_20260310_run13_qwen3_4b_merged30/stage_a_math_records.jsonl \
  --train-min-original-solve 1.0 \
  --train-max-paraphrase-gap 0.0 \
  --output-dir outputs/math_stage_a_20260310_filter02_conservative_merged30

PYTHONPATH=src python scripts/audit_math_stage_a.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --heldout-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_heldout_records.jsonl \
  --output-dir outputs/math_stage_a_20260310_audit07_conservative_merged30

python scripts/select_math_stage_b_hard_slice.py \
  --selection-source audit_only \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --output-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30/hard_slice_summary.json

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30/hard_slice_summary.json \
  --run-name hard_audit07_lc120 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30/hard_slice_summary.json \
  --run-name hard_audit07_lc160 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 160 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30
```

Outputs:

- `outputs/countertrace_mini_math_20260310_seed31_run04/math_summary.json`
- `outputs/countertrace_mini_math_20260310_seed47_run05/math_summary.json`
- `outputs/countertrace_mini_math_20260310_merged02/math_summary.json`
- `outputs/math_stage_a_20260310_run12_merged30/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_run13_qwen3_4b_merged30/stage_a_math_summary.json`
- `outputs/math_stage_a_20260310_filter02_conservative_merged30/filter_summary.json`
- `outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30/hard_slice_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30/hard_audit07_lc120/comparison_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30/hard_audit07_lc160/comparison_summary.json`

Observed result:

- the verified GSM8K success-trace pool expands from `16` to `30` unique traces in `merged02`
- Stage A rerun over that larger pool stays positive on both sides:
  - train `run12`: `num_records = 89`, `mean_n_t_weighted = 0.0338`, `mean_paraphrase_gap = 0.0187`
  - held-out `run13`: `num_records = 89`, `mean_n_t_weighted = 0.0153`, `mean_paraphrase_gap = 0.0037`
- the stricter train-side-only conservative filter remains cheap:
  - `filter02`: `79 / 89` kept, `keep_fraction = 0.8876`
- the larger conservative joint audit still preserves a strong usable core:
  - `audit07`: `62 / 79` kept, `keep_fraction = 0.7848`
  - `mean_train_n_t_weighted_kept = 0.0248`
  - `mean_heldout_n_t_weighted_kept = 0.0193`
  - `mean_train_paraphrase_gap_kept = 0.0`
  - `mean_heldout_paraphrase_gap_kept = 0.0`
- the dominant larger-pool failure remains held-out swap repair, not paraphrase drift:
  - `heldout_swap_solve = 14`
  - `heldout_weighted_n = 9`
  - `heldout_original_solve = 3`
- a new `audit_only` hard-slice read on the expanded conservative core selects exactly two true held-out-hard examples:
  - `gsm8k-00007`
  - `gsm8k-00132`
- but that 2-example hard core is not a useful Week 3 discriminator:
  - at `lc120`, `base = control = cnt = 1.0 / 1.0 / 0.6667 / 0.0190`
  - at `lc160`, `base = control = cnt = 1.0 / 1.0 / 0.6667 / 0.0190`
  - in both cases, `delta(cnt - control)` is exactly zero on all rollout metrics

Interpretation:

- expanding the verified GSM8K pool materially improves Week 2 coverage without collapsing the object; the conservative exit grows from the earlier `33 / 40` regime to a new `62 / 79` regime
- however, "hard under Stage A held-out audit" is not the same as "discriminative under Stage B rollout comparison"
- the new 2-example `audit_only` hard slice is genuinely Stage-A-hard, but too saturated at Stage B to separate `base`, matched SFT-only, and CNT
- the old mixed-source `GSM8K-hard` gate remains the better Week 3 discriminator for now
- the next correct move is not to abandon GSM8K, but to compute a broader non-ceiling Week 3 gate over the expanded 30-example conservative core using Stage B base-rollout information, not held-out audit alone

## 2026-03-10 Mixed-Source Hard Gate Rebuilt Over `audit07`

Status: completed as the first Week 3 gate rebuild over the expanded `30`-trace conservative core

Code changes:

- added `scripts/run_math_stage_b_base_rollout_folds.py` to generate disjoint Stage B base-rollout artifacts without wasting compute on control/CNT training

Reproducible commands:

```bash
python -m py_compile \
  scripts/run_math_stage_b_base_rollout_folds.py \
  scripts/select_math_stage_b_hard_slice.py

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_base_rollout_folds.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --gpu cuda:0 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260310_base_rollout_folds_merged30_lc120

python scripts/select_math_stage_b_hard_slice.py \
  --selection-source base_and_audit \
  --base-fold-root outputs/math_stage_b_20260310_base_rollout_folds_merged30_lc120 \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --output-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30_mixed/hard_slice_summary.json

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30_mixed/hard_slice_summary.json \
  --run-name hard_mixed07_lc120 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30_mixed/hard_slice_summary.json \
  --run-name hard_mixed07_lc160 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 160 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed
```

Outputs:

- `outputs/math_stage_b_20260310_base_rollout_folds_merged30_lc120/base_rollout_folds_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30_mixed/hard_slice_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed/hard_mixed07_lc120/comparison_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed/hard_mixed07_lc160/comparison_summary.json`

Observed result:

- the new base-only fold root covers all `30` unique examples in `audit07`, with disjoint eval ids:
  - `num_unique_eval_examples = 30`
  - `all_eval_ids_disjoint = true`
- unlike the earlier `audit_only` hard slice, the rebuilt mixed-source gate expands to `7` examples:
  - `gsm8k-00007`
  - `gsm8k-00019`
  - `gsm8k-00132`
  - `gsm8k-00134`
  - `gsm8k-00141`
  - `gsm8k-00144`
  - `gsm8k-00327`
- the new gate is genuinely non-ceiling before training:
  - at `lc120`, base is `mean_original_solve = 0.8571`, `mean_drop_solve = 0.6429`, `mean_n_t_weighted = 0.2265`
  - at `lc160`, base is `1.0000`, `0.7857`, `0.2292`
- unlike the 2-example `audit_only` slice, the new gate does separate model variants:
  - at `lc120`:
    - control: `0.8571`, `0.7143`, `0.1565`
    - cnt: `0.8571`, `0.6429`, `0.2265`
    - delta(cnt - control): `mean_drop_solve = -0.0714`, `mean_n_t_weighted = +0.0701`
  - at `lc160`:
    - control: `1.0000`, `0.8571`, `0.1592`
    - cnt: `1.0000`, `1.0000`, `0.0190`
    - delta(cnt - control): `mean_drop_solve = +0.1429`, `mean_n_t_weighted = -0.1401`

Interpretation:

- the gate-rebuild strategy works: adding Stage B base-rollout information is enough to recover a broader discriminative hard slice from the expanded `audit07` core
- the 7-example mixed gate is therefore a better Week 3 stress gate than the 2-example `audit_only` slice
- but it is not yet a clean replacement for the old 4-example `GSM8K-hard` gate:
  - the new gate is informative, but utility and weighted-`N_t` move in opposite directions across `lc120` and `lc160`
  - this means the gate is now broad enough to expose a real recipe tradeoff, not just a clean win/loss
- current reading:
  - old 4-example `GSM8K-hard`: cleaner regression probe for stable utility repair
  - new 7-example mixed gate: broader stress test that exposes metric conflict

## 2026-03-10 Structural Probe: Remove Drop-Prefix SFT (`anchor_only`)

Status: completed as a targeted falsification test on the rebuilt `7`-example mixed gate

Code changes:

- extended `build_stage_b_dataset(...)` in `src/cnt_research/math/stage_b.py` with `include_drop_sft`
- added `--include-drop-sft / --no-include-drop-sft` to:
  - `scripts/build_math_stage_b_data.py`
  - `scripts/run_math_stage_b_fold_compare.py`

Reproducible commands:

```bash
python -m py_compile \
  src/cnt_research/math/stage_b.py \
  scripts/build_math_stage_b_data.py \
  scripts/run_math_stage_b_fold_compare.py

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260310_filter02_conservative_merged30/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260310_audit07_conservative_merged30/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260310_merged02/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260310_gsm8k_hard_slice_merged30_mixed/hard_slice_summary.json \
  --run-name hard_mixed07_lc160_anchoronly \
  --train-gpu cuda:4 --eval-gpu cuda:5 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --no-include-drop-sft \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 160 \
  --output-root outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed_anchoronly
```

Outputs:

- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed_anchoronly/hard_mixed07_lc160_anchoronly/dataset/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260310_gsm8k_hard_compare_signal03_merged30_mixed_anchoronly/hard_mixed07_lc160_anchoronly/comparison_summary.json`

Observed result:

- the new dataset is structurally different as intended:
  - `include_drop_sft = false`
  - train rows shrink from `159` to `135`
  - eval rows shrink from `54` to `40`
- but the hoped-for faithfulness recovery does not happen:
  - base stays `mean_drop_solve = 0.7857`, `mean_n_t_weighted = 0.2292`
  - control moves to `0.9286`, `0.0891`
  - cnt is identical on the main rollout metrics: `0.9286`, `0.0891`
- `delta(cnt - control)` is exactly zero on the core tension metrics:
  - `mean_drop_solve = 0.0`
  - `mean_n_t_weighted = 0.0`
- the only visible difference is paraphrase cleanup:
  - control `mean_paraphrase_solve = 0.9286`
  - cnt `mean_paraphrase_solve = 1.0`
  - `delta mean_paraphrase_gap = -0.0714`

Interpretation:

- the structural hypothesis was too simple
- removing `drop-prefix` SFT does **not** fix the over-repair behavior on the broader mixed gate
- worse, it collapses the useful `cnt vs control` distinction on the main rollout metrics
- current diagnosis:
  - the lc160 conflict is not driven mainly by the presence of explicit drop-prefix SFT positives
  - the remaining tension is deeper in the anchor + rollout-pair recipe itself, or in how the broader gate scores utility vs weighted necessity

## 2026-03-11 GSM8K Trace-Pool Expansion: `30 -> 112` Unique Verified Traces

Status: completed

Goal:

- move the GSM8K math line off the small `30`-trace collection baseline and onto a `100+` verified success-trace pool
- keep the same `CounterTrace-mini(math)` collection recipe and numeric verifier
- verify whether collection scale is still the main bottleneck before doing more Week 3 gate work

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 59 \
  --gpu cuda:0 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed59_run06

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 71 \
  --gpu cuda:1 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed71_run07

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 83 \
  --gpu cuda:2 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed83_run08

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 97 \
  --gpu cuda:3 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed97_run09

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 109 \
  --gpu cuda:4 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed109_run10

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 131 \
  --gpu cuda:5 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed131_run11

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 149 \
  --gpu cuda:6 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed149_run12

PYTHONPATH=src python scripts/run_countertrace_mini_math.py \
  --max-examples 128 --target-successes 16 --seed 173 \
  --gpu cuda:7 --max-new-tokens 220 \
  --output-dir outputs/countertrace_mini_math_20260311_seed173_run13

PYTHONPATH=src python scripts/merge_countertrace_mini_math.py \
  outputs/countertrace_mini_math_20260310_merged02 \
  outputs/countertrace_mini_math_20260311_seed59_run06 \
  outputs/countertrace_mini_math_20260311_seed71_run07 \
  outputs/countertrace_mini_math_20260311_seed83_run08 \
  outputs/countertrace_mini_math_20260311_seed97_run09 \
  outputs/countertrace_mini_math_20260311_seed109_run10 \
  outputs/countertrace_mini_math_20260311_seed131_run11 \
  outputs/countertrace_mini_math_20260311_seed149_run12 \
  outputs/countertrace_mini_math_20260311_seed173_run13 \
  --output-dir outputs/countertrace_mini_math_20260311_merged03
```

Outputs:

- merged pool:
  - `outputs/countertrace_mini_math_20260311_merged03/math_summary.json`
  - `outputs/countertrace_mini_math_20260311_merged03/math_traces.jsonl`
  - `outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl`
- child runs:
  - `outputs/countertrace_mini_math_20260311_seed59_run06/`
  - `outputs/countertrace_mini_math_20260311_seed71_run07/`
  - `outputs/countertrace_mini_math_20260311_seed83_run08/`
  - `outputs/countertrace_mini_math_20260311_seed97_run09/`
  - `outputs/countertrace_mini_math_20260311_seed109_run10/`
  - `outputs/countertrace_mini_math_20260311_seed131_run11/`
  - `outputs/countertrace_mini_math_20260311_seed149_run12/`
  - `outputs/countertrace_mini_math_20260311_seed173_run13/`

Observed result:

- each of the 8 new runs reached its `target_successes = 16`
- merged totals:
  - previous baseline: `30` unique verified traces in `outputs/countertrace_mini_math_20260310_merged02/`
  - new baseline: `112` unique verified traces in `outputs/countertrace_mini_math_20260311_merged03/`
  - absolute gain: `+82`
  - merged `num_trace_rows_total = 283`
- per-run attempts stayed operationally reasonable:
  - seed59: `16 / 28`
  - seed71: `16 / 29`
  - seed83: `16 / 29`
  - seed97: `16 / 34`
  - seed109: `16 / 28`
  - seed131: `16 / 24`
  - seed149: `16 / 30`
  - seed173: `16 / 23`

Interpretation:

- this batch alone is enough to move the project off the old `30`-trace collection regime
- verified-trace collection scale is no longer the immediate blocker on GSM8K math
- the next correct move is not another small hard-slice tweak; it is to rerun Stage A / conservative filtering on top of `outputs/countertrace_mini_math_20260311_merged03/`
- until that rerun exists, all Week 3 gates derived from the older `30`-trace pool should be treated as diagnostic stress probes rather than the main evidence base

## 2026-03-11 Larger Week 2 Exit Over the `112`-Trace Pool (`merged03 -> run14/run15 -> audit08`)

Status: completed

Goal:

- rebuild the conservative Week 2 exit on top of the new `112`-trace GSM8K success-trace pool
- keep the same Stage A / held-out audit / conservative filter logic as `run12/run13 -> filter02 -> audit07`
- determine whether the larger pool scales without collapsing the object

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

for i in 0 1 2 3 4 5 6 7; do
  offset=$((14 * i))
  gpu="cuda:${i}"
  PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
    --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
    --gpu "${gpu}" \
    --max-traces 14 --trace-offset "${offset}" \
    --max-candidates-per-trace 3 \
    --continuation-max-new-tokens 220 \
    --edit-max-new-tokens 48 \
    --output-dir "outputs/math_stage_a_20260311_run14_merged112_shard${i}" &
done
wait

for i in 0 1 2 3 4 5 6 7; do
  offset=$((14 * i))
  gpu="cuda:${i}"
  PYTHONPATH=src python scripts/run_math_stage_a.py --resume \
    --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
    --model-dir /cephfs/luyanzhen/test/model/models--Qwen--Qwen3-4B/snapshots/531c80e289d6cff3a7cd8c0db8110231d23a6f7a \
    --gpu "${gpu}" \
    --max-traces 14 --trace-offset "${offset}" \
    --max-candidates-per-trace 3 \
    --continuation-max-new-tokens 220 \
    --edit-max-new-tokens 48 \
    --output-dir "outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard${i}" &
done
wait

PYTHONPATH=src python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260311_run14_merged112_shard0 \
  outputs/math_stage_a_20260311_run14_merged112_shard1 \
  outputs/math_stage_a_20260311_run14_merged112_shard2 \
  outputs/math_stage_a_20260311_run14_merged112_shard3 \
  outputs/math_stage_a_20260311_run14_merged112_shard4 \
  outputs/math_stage_a_20260311_run14_merged112_shard5 \
  outputs/math_stage_a_20260311_run14_merged112_shard6 \
  outputs/math_stage_a_20260311_run14_merged112_shard7 \
  --output-dir outputs/math_stage_a_20260311_run14_merged112

PYTHONPATH=src python scripts/merge_math_stage_a.py \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard0 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard1 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard2 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard3 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard4 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard5 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard6 \
  outputs/math_stage_a_20260311_run15_qwen3_4b_merged112_shard7 \
  --output-dir outputs/math_stage_a_20260311_run15_qwen3_4b_merged112

PYTHONPATH=src python scripts/filter_math_stage_a_records.py \
  --train-records outputs/math_stage_a_20260311_run14_merged112/stage_a_math_records.jsonl \
  --heldout-records outputs/math_stage_a_20260311_run15_qwen3_4b_merged112/stage_a_math_records.jsonl \
  --train-min-original-solve 1.0 \
  --train-max-paraphrase-gap 0.0 \
  --output-dir outputs/math_stage_a_20260311_filter03_conservative_merged112

PYTHONPATH=src python scripts/audit_math_stage_a.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --heldout-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_heldout_records.jsonl \
  --output-dir outputs/math_stage_a_20260311_audit08_conservative_merged112
```

Outputs:

- `outputs/math_stage_a_20260311_run14_merged112/stage_a_math_summary.json`
- `outputs/math_stage_a_20260311_run15_qwen3_4b_merged112/stage_a_math_summary.json`
- `outputs/math_stage_a_20260311_filter03_conservative_merged112/filter_summary.json`
- `outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_summary.json`

Observed result:

- both sides scale to the full larger pool with aligned record counts:
  - train `run14`: `num_records = 331`
  - held-out `run15`: `num_records = 331`
- the object remains positive on both sides at the larger scale:
  - train `mean_n_t_weighted = 0.0429643698`
  - held-out `mean_n_t_weighted = 0.0285377423`
  - held-out `mean_paraphrase_gap = 0.0040281974`
- the conservative train-side filter remains cheap:
  - `filter03`: `298 / 331` kept, `keep_fraction = 0.9003`
- the larger conservative joint audit still preserves a strong Week 2 exit:
  - `audit08`: `230 / 298` kept, `keep_fraction = 0.7718`
  - `mean_train_n_t_weighted_kept = 0.0510597661`
  - `mean_heldout_n_t_weighted_kept = 0.0332479157`
  - `mean_train_paraphrase_gap_kept = 0.0`
  - `mean_heldout_paraphrase_gap_kept = 0.0`
- the main broader-pool failure mode is still swap robustness, not paraphrase drift:
  - `heldout_swap_solve = 56`
  - `heldout_weighted_n = 33`
  - `train_swap_solve = 28`
  - `train_weighted_n = 18`

Interpretation:

- the Week 2 object scales cleanly from the old `30`-trace regime to the new `112`-trace regime
- the larger pool does not wash out the signal; if anything, the conservative kept subset gets stronger:
  - `audit07` kept held-out weighted `N_t = 0.0193`
  - `audit08` kept held-out weighted `N_t = 0.0332`
- the bottleneck remains the same family as before, just at larger scale:
  - held-out swap repair dominates the dropped pairs
  - paraphrase invariance stays essentially solved on the kept subset
- operational note:
  - Stage A shard summaries are incremental and should not be used as a completion signal
  - an earlier partial merge of `run14` at `146` records was superseded by the final rerun/merge at `331` records

## 2026-03-11 Week 3 Gate Rebuild Over `audit08` (`base_rollout_folds -> strict mixed gate`)

Status: completed for gate construction

Goal:

- replace the old `4` / `7` example Week 3 probes with a larger main gate derived from the new `audit08` conservative exit
- keep the old selection rule unchanged while testing how far the larger-pool artifacts scale
- use fresh Stage B base-rollout artifacts plus `audit08` held-out scores to rebuild the eval slice

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_base_rollout_folds.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --gpu cuda:0 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260311_base_rollout_folds_merged112_lc120

python scripts/select_math_stage_b_hard_slice.py \
  --selection-source audit_only \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --output-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_auditonly/hard_slice_summary.json

python scripts/select_math_stage_b_hard_slice.py \
  --selection-source base_and_audit \
  --base-fold-root outputs/math_stage_b_20260311_base_rollout_folds_merged112_lc120 \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --output-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json
```

Outputs:

- `outputs/math_stage_b_20260311_base_rollout_folds_merged112_lc120/base_rollout_folds_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_auditonly/hard_slice_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json`

Observed result:

- the rebuilt base-only fold root covers the full larger-pool evidence set:
  - `num_unique_eval_examples = 110`
  - `all_eval_ids_disjoint = true`
  - fold sizes: `28 / 28 / 27 / 27`
- under the unchanged strict `base_and_audit` rule, the new mixed Week 3 gate expands from the old tiny probes to `29` examples:
  - `num_selected_examples = 29`
- this is materially larger than the `audit_only` gate on the same `audit08` pool:
  - `audit_only`: `10` examples
  - `base_and_audit`: `29` examples
- the larger-pool base rollout is clearly non-ceiling on average:
  - mean fold `base_original_solve = 0.9787`
  - mean fold `base_drop_solve = 0.9008`
  - mean fold `base_n_t_weighted = 0.0950`

Interpretation:

- the Week 3 gate-rebuild logic still works at the `audit08` scale
- adding fresh base-rollout artifacts is again the difference between an undersized `audit_only` gate (`10`) and a much more useful mixed gate (`29`)
- but the strict old selection rule does **not** naturally reach the user's desired `30+` threshold; it stops one example short at `29`
- this is important methodologically:
  - the project now has a substantially larger Week 3 main gate under the old rule
  - moving from `29` to `30+` would require an explicit change in gate definition, not just more bookkeeping under the current rule

## 2026-03-11 First Matched Compare On the Strict `audit08` Mixed Gate (`29` examples, `lc120`)

Status: completed

Goal:

- run the first Week 3 matched compare on the newly rebuilt strict `audit08` mixed gate
- keep the current Stage B recipe unchanged and test whether the larger-pool gate preserves or weakens the earlier small-gate picture
- compare `base`, matched `SFT-only` control, and current CNT under the same `lc120` rollout gate

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112
```

Outputs:

- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/comparison_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/control_rollout/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/cnt_rollout/stage_b_rollout_summary.json`

Observed result:

- eval gate size: `29` examples
- rollout summaries:
  - base: `mean_original_solve = 0.9194`, `mean_drop_solve = 0.6290`, `mean_n_t_weighted = 0.3023`
  - control: `0.9194`, `0.6452`, `0.2865`
  - cnt: `0.9032`, `0.6452`, `0.2860`
- CNT minus control:
  - `mean_original_solve = -0.0161`
  - `mean_drop_solve = 0.0`
  - `mean_n_t = -0.0161`
  - `mean_n_t_weighted = -0.00046`
  - `mean_paraphrase_gap = 0.0`
- offline metrics remain almost tied:
  - `delta pref_margin_mean = +0.00184`
  - `delta sft_nll_mean = +0.00243`

Interpretation:

- on the new strict `29`-example main gate, the current CNT recipe does **not** beat matched SFT-only control
- the result is slightly worse than a flat tie:
  - control matches base on `mean_original_solve` and improves `mean_drop_solve`
  - CNT matches control on `mean_drop_solve` but loses `mean_original_solve`
- this is a stronger null than the earlier small-gate ambiguity:
  - the gate is much larger than the old `4/7`-example probes
  - under this larger strict gate, current `signal03` does not survive as a broad win
- current reading:
  - the `audit08` object and larger Week 2 exit are fine
  - the blocker has moved back to the Stage B recipe itself
  - if we keep the strict gate definition unchanged, the next recipe iteration has to beat control on this `29`-example set, not just on tiny probes

## 2026-03-11 Stage B Recipe Sweep On the Strict `audit08` Mixed Gate (`29` examples, fixed gate)

Status: completed

Goal:

- keep the strict `29`-example `audit08` mixed gate fixed
- test whether the current Stage B failure is better explained by `weight_source` or by `pair_completion_mode`
- compare three recipe variants against the already completed heldout-weight rollout-pair baseline

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_minw \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source min \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_weightsrc_sweep

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_trainw \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source train \
  --weight-field weight_normalized \
  --pair-completion-mode rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_weightsrc_sweep

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_step_pair \
  --train-gpu cuda:4 --eval-gpu cuda:5 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260311_gsm8k_hard_compare_signal04_step_pair
```

Outputs:

- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_weightsrc_sweep/hard_audit08_mixed_lc120_minw/comparison_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_weightsrc_sweep/hard_audit08_mixed_lc120_trainw/comparison_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal04_step_pair/hard_audit08_mixed_lc120_step_pair/comparison_summary.json`

Observed result:

- baseline (`heldout`, `rollout-pair`) stays slightly negative:
  - `delta(cnt-control)`: `mean_original_solve = -0.0161`, `mean_drop_solve = 0.0`, `mean_n_t_weighted = -0.00046`
  - only one differing row: `gsm8k-00155 @ step 2`
- `weight_source=min`:
  - control: `mean_original_solve = 0.9194`, `mean_drop_solve = 0.6774`, `mean_n_t_weighted = 0.2548`
  - cnt: `0.9194`, `0.6452`, `0.2865`
  - `delta(cnt-control)`: `mean_original_solve = 0.0`, `mean_drop_solve = -0.0323`, `mean_n_t_weighted = +0.0316`
  - differing rows: `gsm8k-00134 @ step 1`, `gsm8k-00198 @ step 1`
- `weight_source=train`:
  - control: `0.9194`, `0.6613`, `0.2707`
  - cnt: `0.9194`, `0.6452`, `0.2865`
  - `delta(cnt-control)`: `mean_original_solve = 0.0`, `mean_drop_solve = -0.0161`, `mean_n_t_weighted = +0.0158`
  - differing row: `gsm8k-00118 @ step 2`
- `step-pair` (`heldout` + `pair_completion_mode=step`):
  - control: `0.9194`, `0.6613`, `0.2707`
  - cnt: `0.9194`, `0.6774`, `0.2548`
  - `delta(cnt-control)`: `mean_original_solve = 0.0`, `mean_drop_solve = +0.0161`, `mean_n_t_weighted = -0.0158`
  - differing row: `gsm8k-00134 @ step 1`

Example-level diagnosis:

- the original-prefix regression at `gsm8k-00155 @ step 2` disappears in all three new variants
- the sweep does **not** produce a broad win; instead it creates a sparse frontier:
  - `min` / `train` weighting improve weighted `N_t` relative to control, but lose one or two drop repairs that control gets
  - `step-pair` flips one of those repairs the other way, improving `drop_solve` over control but lowering weighted `N_t`
- representative failure / repair patterns:
  - `gsm8k-00134 @ step 1`:
    - under `minw`, CNT answers `60` instead of `720`, so control wins on utility
    - under `step-pair`, control answers `60` while CNT restores `720`, so CNT wins on utility
  - `gsm8k-00198 @ step 1` (`minw`): CNT truncates before the final total and loses the drop case
  - `gsm8k-00118 @ step 2` (`trainw`): CNT stops at `20` instead of finishing `20 / 5 = 4`

Interpretation:

- the first strict-gate negative result was **not** just a `gsm8k-00155` one-off
- changing `weight_source` is not useless, but it is not the main unlock:
  - it removes the old original-prefix regression
  - it does not create a clean CNT-over-control utility win
- `step-pair` is the first variant to win `mean_drop_solve` over control on the fixed strict gate, but only by sacrificing weighted `N_t`
- current Stage B diagnosis is now sharper:
  - the fixed `29`-example gate exposes a sparse utility-vs-weighted-`N_t` frontier
  - next recipe iterations should target this tradeoff directly rather than keep sweeping only `weight_source`

Operational note:

- `scripts/run_math_stage_b_fold_compare.py` now supports `--reuse-base-rollout-from`, so future same-gate recipe sweeps can skip re-running identical base-rollout evaluation

## 2026-03-12 Stage B Structural Follow-up: `step-pair + pref_margin_target = 1.0` On the Strict `audit08` Mixed Gate

Status: completed

Goal:

- keep the strict `29`-example `audit08` mixed gate fixed
- start moving from small-parameter sweeps to a structural Stage B recipe change
- test whether a hard-negative-only pref objective can preserve the utility gain of `step-pair` while recovering weighted `N_t`

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_step_pair_prefmargin1p0 \
  --train-gpu cuda:6 --eval-gpu cuda:7 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --pref-margin-target 1.0 \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout \
  --output-root outputs/math_stage_b_20260311_gsm8k_hard_compare_signal05_step_pair_prefmargin
```

Outputs:

- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal05_step_pair_prefmargin/hard_audit08_mixed_lc120_step_pair_prefmargin1p0/comparison_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal05_step_pair_prefmargin/hard_audit08_mixed_lc120_step_pair_prefmargin1p0/cnt/stage_b_training_summary.json`
- `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal05_step_pair_prefmargin/hard_audit08_mixed_lc120_step_pair_prefmargin1p0/control_sftonly/stage_b_training_summary.json`

Observed result:

- control:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6613`
  - `mean_n_t = 0.6989`
  - `mean_n_t_weighted = 0.2707`
- CNT (`step-pair + pref_margin_target = 1.0`):
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- `delta(cnt-control)`:
  - `mean_original_solve = 0.0`
  - `mean_drop_solve = -0.0161`
  - `mean_n_t = +0.0054`
  - `mean_n_t_weighted = +0.0158`

Comparison to the preceding `step-pair` run:

- plain `step-pair` had:
  - `mean_drop_solve = +0.0161`
  - `mean_n_t_weighted = -0.0158`
- adding `pref_margin_target = 1.0` flips the sign:
  - `mean_drop_solve = -0.0161`
  - `mean_n_t_weighted = +0.0158`

Example-level diagnosis:

- plain `step-pair` differed from control only on `gsm8k-00134 @ step 1`, where CNT repaired the drop case and control answered `60` instead of `720`
- `pref_margin_target = 1.0` differs from control only on `gsm8k-00198 @ step 1`, where control finishes correctly but CNT truncates before the final total
- so the new structural variant does **not** dominate the old one; it simply moves the single decisive drop case from one family to another

Offline signal:

- `delta cnt-control (after eval)`:
  - `pref_margin_mean = +0.0200`
  - `sft_nll_mean = +0.0063`
- inside the CNT run itself:
  - `before_metrics.eval.pref_margin_mean = 0.8830`
  - `after_metrics.eval.pref_margin_mean = 0.8996`
- this confirms the mechanism is active, but the rollout effect is still a sparse tradeoff rather than a broad improvement

Interpretation:

- `pref_margin_target = 1.0` is not the fix
- it does not preserve the utility win of `step-pair`
- instead, it pushes the recipe back onto the weighted-`N_t` side of the frontier
- updated diagnosis:
  - the current strict-gate Stage B problem is not just “easy pref margins are being over-optimized”
  - the tradeoff is more structural and remains concentrated in a handful of drop-repairable families

## 2026-03-12 Stage B Structural Follow-up: `step-pair + anchor_pair_mode = original_truncated_pref` On the Strict `audit08` Mixed Gate

Status: completed

Goal:

- keep the strict `29`-example `audit08` mixed gate fixed
- test an original-prefix protection mechanism instead of another small loss sweep
- add anchor-side contrastive rows that prefer the full correct original suffix over a truncated original suffix

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_step_pair_anchortrunc \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --anchor-pair-mode original_truncated_pref \
  --lambda-n 24 --lambda-inv 8 \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout \
  --output-root outputs/math_stage_b_20260312_gsm8k_hard_compare_signal06_step_pair_anchortrunc
```

Outputs:

- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal06_step_pair_anchortrunc/hard_audit08_mixed_lc120_step_pair_anchortrunc/comparison_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal06_step_pair_anchortrunc/hard_audit08_mixed_lc120_step_pair_anchortrunc/dataset/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal06_step_pair_anchortrunc/hard_audit08_mixed_lc120_step_pair_anchortrunc/cnt/stage_b_training_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal06_step_pair_anchortrunc/hard_audit08_mixed_lc120_step_pair_anchortrunc/control_sftonly/stage_b_training_summary.json`

Observed result:

- control:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6613`
  - `mean_n_t = 0.6989`
  - `mean_n_t_weighted = 0.2707`
- CNT (`step-pair + original_truncated_pref`):
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6774`
  - `mean_n_t = 0.6935`
  - `mean_n_t_weighted = 0.2548`
- `delta(cnt-control)`:
  - `mean_original_solve = 0.0`
  - `mean_drop_solve = +0.0161`
  - `mean_n_t = -0.0054`
  - `mean_n_t_weighted = -0.0158`

Comparison to the preceding `step-pair` run:

- the aggregate rollout deltas are exactly the same as plain `step-pair`
  - `mean_drop_solve = +0.0161`
  - `mean_n_t_weighted = -0.0158`
- so this is **not** a broad improvement over the current utility-positive branch

Mechanism check:

- the anchor-side contrastive rows were actually added:
  - plain `step-pair` dataset task counts:
    - train `pref = 232`
    - eval `pref = 78`
  - `original_truncated_pref` task counts:
    - train `pref = 343`
    - eval `pref = 119`
- offline metrics also moved:
  - `delta cnt-control (after eval)`:
    - `pref_margin_mean = +0.0199`
    - `sft_nll_mean = +0.0119`
- this confirms the mechanism is active; the null result is not caused by the rows being absent

Example-level diagnosis:

- unlike plain `step-pair`, the decisive differences are no longer concentrated in one utility-positive family
- metric-relevant flips vs control now occur on three records:
  - `gsm8k-00030 @ step 0`: CNT repairs the drop case that control misses
  - `gsm8k-00118 @ step 2`: CNT loses a drop case that control finishes correctly
  - `gsm8k-00134 @ step 1`: CNT repairs the same drop case that plain `step-pair` repaired
- there is also one non-metric original-prefix answer change:
  - `gsm8k-00129 @ step 0`: control and CNT are both wrong, but with different wrong original answers
- net effect:
  - the new mechanism redistributes the sparse frontier
  - but the positive and negative flips cancel back to the same aggregate as plain `step-pair`

Interpretation:

- `anchor_pair_mode = original_truncated_pref` is not the fix
- it is also not inactive; it changes which families flip under rollout
- the current strict-gate Stage B tradeoff remains structural:
  - original-anchor truncation negatives can move sparse flip locations
  - but they do not yet improve the aggregate utility-vs-weighted-`N_t` frontier

## 2026-03-12 Stage B Diagnostic: Literal Utility Sign-Consistency Is A No-Op On `audit08`, So The Real Lever Is `drop-prefix` SFT

Status: completed diagnostic

Goal:

- test the most literal implementation of the proposed “utility sign-consistent pair eligibility”
- check whether `min(train_delta, heldout_delta) >= 0` would actually change the current `audit08` Stage B dataset

Diagnostic result:

- on `outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl`, the literal sign-consistency rule is already satisfied for every kept candidate:
  - total candidates: `230`
  - `drop_ok = 230`
  - `swap_quantity_ok = 230`
  - `swap_operation_ok = 230`
- so applying `min(train_delta, heldout_delta) >= 0` directly to current `pref` rows would be a no-op

More informative breakdown:

- the real asymmetry is in `drop`, not in `swap`
- `drop` minimum deltas over `(train, heldout)` are:
  - `0.0`: `227 / 230`
  - `0.3333`: `1 / 230`
  - `1.0`: `2 / 230`
- `swap_quantity` and `swap_operation` are already strictly positive for all kept candidates

Interpretation:

- the current Stage B bottleneck is not “wrong-sign swap pairs slipped through audit08”
- it is that most kept candidates still have `drop delta = 0` on at least one side, so full-strength `drop-prefix` SFT mainly teaches generic repair on recoverable cases
- therefore the nearest nontrivial recipe update is to act on `drop-prefix` SFT admission rather than on swap-pair eligibility

## 2026-03-12 Stage B Dataset Smoke: `step-pair + drop_sft_filter = one_side_positive`

Status: completed dataset smoke

Goal:

- implement a utility-aware variant that keeps `pref/equiv` intact
- filter only `drop-prefix` SFT rows to candidates with positive drop utility on at least one side

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/build_math_stage_b_data.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --output-dir outputs/math_stage_b_20260312_dataset04_step_pair_dropfilter_smoke \
  --eval-examples 29 \
  --split-seed 17 \
  --weight-source heldout \
  --completion-mode rollout \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --chosen-source success_trace \
  --drop-sft-filter one_side_positive
```

Outputs:

- `outputs/math_stage_b_20260312_dataset04_step_pair_dropfilter_smoke/stage_b_dataset_summary.json`

Observed result:

- this knob only affects `drop-prefix` SFT rows; `pref/equiv` rows remain intact
- relative to the previous same-family `step-pair` dataset:
  - train `sft`: `336 -> 189`
  - eval `sft`: `124 -> 63`
  - train `pref`: unchanged at `240` on this split
  - eval `pref`: unchanged at `70` on this split
- the explicit filter accounting is:
  - train: `drop_sft_kept = 16`, `drop_sft_filtered = 157`
  - eval: `drop_sft_kept = 6`, `drop_sft_filtered = 51`

Interpretation:

- this is the first Stage B recipe update that directly targets the likely generic-repair supervision source without collapsing the full dataset
- a strict-gate compare with the exact same idea has been launched separately on the frozen `29`-example gate; that run is operational progress, not yet a completed result

## 2026-03-12 Stage B Strict-Gate Compare: `step-pair + drop_sft_filter = one_side_positive`

Status: completed

Goal:

- keep the strict frozen `29`-example `audit08` mixed gate fixed
- test whether filtering `drop-prefix` SFT to positive-drop candidates can preserve the utility side of `step-pair` without paying the same weighted-`N_t` cost

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_step_pair_dropfilter1side \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout \
  --output-root outputs/math_stage_b_20260312_gsm8k_hard_compare_signal07_step_pair_dropfilter
```

Outputs:

- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal07_step_pair_dropfilter/hard_audit08_mixed_lc120_step_pair_dropfilter1side/comparison_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal07_step_pair_dropfilter/hard_audit08_mixed_lc120_step_pair_dropfilter1side/dataset/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal07_step_pair_dropfilter/hard_audit08_mixed_lc120_step_pair_dropfilter1side/control_sftonly/stage_b_training_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal07_step_pair_dropfilter/hard_audit08_mixed_lc120_step_pair_dropfilter1side/cnt/stage_b_training_summary.json`

Observed result:

- control:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- CNT:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- `delta(cnt-control)`:
  - all rollout metrics are exactly `0.0`

Comparison to plain `step-pair`:

- plain `step-pair` had:
  - `mean_drop_solve = +0.0161`
  - `mean_n_t_weighted = -0.0158`
- this new recipe removes that separation entirely:
  - `mean_drop_solve = 0.0`
  - `mean_n_t_weighted = 0.0`

What changed relative to plain `step-pair`:

- the filtered dataset keeps only nonzero-drop `drop-prefix` SFT rows:
  - strict-gate train split: `drop_sft_kept = 4`, `drop_sft_filtered = 164`
  - strict-gate eval split: `drop_sft_kept = 18`, `drop_sft_filtered = 44`
- rollout behavior moves both models toward the same midpoint:
  - control: `drop_solve 0.6613 -> 0.6452`, `weighted N_t 0.2707 -> 0.2865`
  - CNT: `drop_solve 0.6774 -> 0.6452`, `weighted N_t 0.2548 -> 0.2865`

Example-level diagnosis:

- under this recipe, control and CNT differ only on two drop cases:
  - `gsm8k-00134 @ step 1`: control repairs the drop case, CNT does not
  - `gsm8k-00155 @ step 2`: CNT repairs the drop case, control does not
- these two opposing flips cancel exactly, producing an aggregate tie

Interpretation:

- `drop_sft_filter = one_side_positive` is not the missing unlock
- but it is informative:
  - filtering zero-margin `drop-prefix` SFT removes the plain `step-pair` CNT-over-control utility edge
  - at the same time, it raises weighted `N_t` for both models to the same level
- updated diagnosis:
  - the strict-gate frontier is not driven only by generic zero-margin drop repair
  - removing that supervision collapses the separation instead of turning it into a clean CNT win

## 2026-03-12 Stage B Strict-Gate Compare: `step-pair + drop_sft_filter = one_side_positive + anchor_pair_mode = original_truncated_pref`

Status: completed

Goal:

- keep the same strict frozen `29`-example `audit08` mixed gate
- start from the cleaner `drop_sft_filter = one_side_positive` base
- test whether adding original-anchor truncation negatives can create a positive CNT-vs-control separation without reintroducing the old frontier

Reproducible command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_step_pair_dropfilter_anchortrunc \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step \
  --anchor-mode original_rollout \
  --anchor-pair-mode original_truncated_pref \
  --lambda-n 24 --lambda-inv 8 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout \
  --output-root outputs/math_stage_b_20260312_gsm8k_hard_compare_signal08_step_pair_dropfilter_anchortrunc
```

Outputs:

- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal08_step_pair_dropfilter_anchortrunc/hard_audit08_mixed_lc120_step_pair_dropfilter_anchortrunc/comparison_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal08_step_pair_dropfilter_anchortrunc/hard_audit08_mixed_lc120_step_pair_dropfilter_anchortrunc/dataset/stage_b_dataset_summary.json`

Observed result:

- control:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- CNT:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6290`
  - `mean_n_t = 0.7097`
  - `mean_n_t_weighted = 0.3023`
- `delta(cnt-control)`:
  - `mean_original_solve = 0.0`
  - `mean_drop_solve = -0.0161`
  - `mean_n_t = +0.0054`
  - `mean_n_t_weighted = +0.0158`

Comparison to nearby recipes:

- relative to `step-pair + drop_sft_filter = one_side_positive`, this new recipe moves away from the exact tie:
  - `mean_drop_solve: 0.0 -> -0.0161`
  - `mean_n_t_weighted: 0.0 -> +0.0158`
- relative to `step-pair + pref_margin_target = 1.0`, the aggregate direction is the same:
  - utility drops back below control
  - weighted `N_t` rises back above control

What changed:

- `drop_sft_filter` accounting stays unchanged from the cleaner base:
  - train `drop_sft_kept = 4`, `drop_sft_filtered = 164`
  - eval `drop_sft_kept = 18`, `drop_sft_filtered = 44`
- the only added pressure is anchor-side truncation preference:
  - train `pref: 232 -> 343`
  - eval `pref: 78 -> 119`

Example-level diagnosis:

- the new recipe changes several rollout texts, but only one record moves the aggregate in a metric-relevant bad direction:
  - `gsm8k-00198 @ step 1`: control repairs the drop case, CNT does not
- other changed rows are mostly wrong-vs-wrong answer-text changes and do not move the strict-gate metric totals

Interpretation:

- adding original-anchor truncation negatives on top of the filtered-drop base is **not** the missing unlock
- more specifically:
  - `drop_sft_filter` had cleaned the old sparse frontier into a tie
  - anchor-side truncation pressure pushes that cleaned-up recipe back onto the weighted-`N_t` side of the tradeoff
- updated diagnosis:
  - the strict-gate bottleneck is now deeper than zero-margin drop repair alone
  - a new positive signal is needed; stacking more anchor/filter pressure on the cleaned base just recreates the old utility-vs-weighted-`N_t` frontier

## 2026-03-12 Stage B Strict-Gate Compare: `step_and_rollout + drop_sft_filter = one_side_positive`

Status: completed via fasttrack execution on the same frozen strict gate

Goal:

- keep the strict frozen `29`-example `audit08` mixed gate fixed
- start from the cleaner `drop_sft_filter = one_side_positive` base
- combine local `step` pairs with full-suffix `rollout` pairs in one dataset, instead of choosing only one pair modality

Fasttrack execution path:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --eval-example-ids-path outputs/math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed/hard_slice_summary.json \
  --run-name hard_audit08_mixed_lc120_stepandrollout_dropfilter1side \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout \
  --output-root outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter
```

Because the monolithic compare is slow under doubled pair rows, the final completed result was assembled from the same dataset/config with these equivalent fasttrack sub-commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_training.py \
  --dataset-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/dataset \
  --gpu cuda:2 \
  --epochs 1 \
  --learning-rate 1e-6 \
  --weight-field weight_normalized \
  --lambda-n 24 \
  --lambda-inv 8 \
  --output-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/cnt_fasttrack

PYTHONPATH=src python scripts/eval_math_stage_b_rollout.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --dataset-summary outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/dataset/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/control_sftonly/model \
  --gpu cuda:3 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/control_rollout_fasttrack

PYTHONPATH=src python scripts/eval_math_stage_b_rollout.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_a_20260311_audit08_conservative_merged112/stage_a_audit_kept.jsonl \
  --dataset-summary outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/dataset/stage_b_dataset_summary.json \
  --model-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/cnt_fasttrack/model \
  --gpu cuda:4 \
  --split eval \
  --styles locked_careful \
  --continuation-max-new-tokens 120 \
  --output-dir outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/cnt_rollout_fasttrack
```

Outputs:

- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/dataset/stage_b_dataset_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/control_sftonly/stage_b_training_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/control_rollout_fasttrack/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/cnt_fasttrack/stage_b_training_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/cnt_rollout_fasttrack/stage_b_rollout_summary.json`
- `outputs/math_stage_b_20260312_gsm8k_hard_compare_signal09_stepandrollout_dropfilter/hard_audit08_mixed_lc120_stepandrollout_dropfilter1side/comparison_summary.json`

Observed result:

- dataset growth relative to the same strict-gate dropfilter base:
  - train `pref: 232 -> 464`, `equiv: 66 -> 132`, `sft: 172` unchanged
  - eval `pref: 78 -> 156`, `equiv: 22 -> 44`, `sft: 80` unchanged
- control:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- CNT:
  - `mean_original_solve = 0.9194`
  - `mean_drop_solve = 0.6452`
  - `mean_n_t = 0.7043`
  - `mean_n_t_weighted = 0.2865`
- `delta(cnt-control)`:
  - all rollout metrics are exactly `0.0`

Offline side:

- CNT still moves the offline pair metrics:
  - `delta pref_margin_mean = +0.0257`
  - `delta pref_margin_weighted_mean = +0.0216`
- but that stronger offline separation does not translate into any strict-gate rollout gain

Interpretation:

- `step_and_rollout + drop_sft_filter = one_side_positive` is not the missing unlock either
- compared with plain `step-pair + drop_sft_filter`, it does **not** recreate the old utility-vs-weighted-`N_t` frontier; it stays on the same exact tie
- updated diagnosis:
  - combining local and rollout pref rows is safe on the cleaned dropfilter base
  - but it still does not produce any CNT-over-control separation on the strict `29`-example gate
  - the remaining Week 3 bottleneck is therefore deeper than “missing rollout pair modality”

## 2026-03-15 Week 3 Evaluation Hygiene: Freeze The Strict `29`-Example Gate And Split Out A Recipe-Dev Pool

Status: completed

Why:

- the strict `29`-example `audit08` mixed gate had already absorbed a full exploratory same-gate recipe sweep
- continuing to search on the same `29` examples would blur the line between final test and recipe development
- the next step had to be an evaluation-hygiene change, not another silent gate or metric change

Command:

```bash
python -m py_compile scripts/freeze_math_stage_b_gate.py
python scripts/freeze_math_stage_b_gate.py
```

Outputs:

- `outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/strict_gate_manifest.json`
- `outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_slice_summary.json`

Observed result:

- the strict Week 3 gate is now frozen as an explicit final-test manifest:
  - `label = audit08_strict29`
  - `role = final_test`
  - `num_gate_examples = 29`
  - `selection_source = base_and_audit`
  - `selection_rule` unchanged from the prior strict mixed gate
  - `fixed_compare_base_rollout_root` pinned to `outputs/math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112/hard_audit08_mixed_lc120/base_rollout`
- the complementary dev pool is now explicit:
  - `role = recipe_dev`
  - `num_total_audit_examples = 110`
  - `num_gate_examples = 29`
  - `num_dev_examples = 81`
  - `selection_policy = Complement of the frozen final-test gate within the audit08 kept-example pool.`

Interpretation:

- no research claim changes here; this is an evaluation-discipline correction
- the strict `29`-example gate should now be treated as a final-style Week 3 test only
- recipe search should move to the complementary `81`-example dev pool, then return to the frozen strict gate for confirmation
- this keeps the Week 2 object-validity exit (`audit08`) and the Week 3 utility gate explicitly separated instead of letting the same `29` examples absorb both roles

## 2026-03-15 Week 3 Dev-Pool Infrastructure Fix + First Structural Dev Recipe (`equiv_weight_mode = uniform`)

Status: completed

Goal:

- keep the strict `29`-example gate frozen as final test
- move the next Stage B recipe iteration onto the complementary `81`-example dev pool
- test one structural hypothesis, not another small same-gate sweep:
  - make paraphrase consistency a first-class term by assigning uniform weight to `equiv` rows instead of inheriting the same `N_t`-derived row weight as `pref`

Important hygiene correction:

- the first naive attempt was to feed `recipe_dev_slice_summary.json` directly into `--eval-example-ids-path`
- that would have made the strict `29` final-test examples become the training split inside `run_math_stage_b_fold_compare.py`
- this was aborted before any compare result was accepted
- corrected procedure:
  - re-run `scripts/freeze_math_stage_b_gate.py` so it emits `recipe_dev_audit_kept.jsonl`
  - run fold compare inside that dev-only pool, not against the complement of the final gate

Code changes:

- `src/cnt_research/math/stage_b.py`
  - added `equiv_weight_mode` with `match` and `uniform`
- `scripts/build_math_stage_b_data.py`
  - wired `--equiv-weight-mode`
- `scripts/run_math_stage_b_fold_compare.py`
  - wired `--equiv-weight-mode`
  - accepts either `eval_example_ids` or `dev_example_ids`
- `scripts/run_math_stage_b_split_compare.py`
  - wired `--equiv-weight-mode`
- `scripts/freeze_math_stage_b_gate.py`
  - now writes `recipe_dev_audit_kept.jsonl`

Execution path:

```bash
python -m py_compile \
  src/cnt_research/math/stage_b.py \
  scripts/build_math_stage_b_data.py \
  scripts/run_math_stage_b_fold_compare.py \
  scripts/run_math_stage_b_split_compare.py \
  scripts/freeze_math_stage_b_gate.py

python scripts/freeze_math_stage_b_gate.py

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index 0 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:0 --eval-gpu cuda:1 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --equiv-weight-mode uniform \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index 1 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:2 --eval-gpu cuda:3 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --equiv-weight-mode uniform \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index 2 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:4 --eval-gpu cuda:5 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --equiv-weight-mode uniform \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index 3 --num-folds 4 --fold-seed 17 \
  --train-gpu cuda:6 --eval-gpu cuda:7 \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --equiv-weight-mode uniform \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds \
  --num-folds 4 \
  --output-path outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl`
- `outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal10_equivuniform_folds/fold_compare_summary.json`

Observed result:

- the dev-only pool now has `168` candidate-step rows across `81` unique examples
- the 4-fold dev compare is disjoint and exhaustive over the dev universe:
  - `num_unique_eval_examples = 81`
  - `all_eval_ids_disjoint = true`
- CNT vs matched SFT-only control is an exact tie on the rollout side:
  - `mean_delta_drop_solve = 0.0`
  - `mean_delta_n_t = 0.0`
  - `mean_delta_n_t_weighted = 0.0`
  - `nonzero_delta_folds = []`
- aggregate utility/object readout:
  - base:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 1.0000`
    - `mean_n_t_weighted = 0.0190`
  - control:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
  - CNT:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
- offline separation still moves:
  - every fold shows higher `pref_margin_mean` for CNT than control
  - but that larger offline separation does not produce any dev-side rollout gain

Interpretation:

- this is the first properly hygienic dev-side Stage B recipe result after freezing the strict gate
- making `equiv` rows uniformly weighted is still not enough to separate CNT from matched SFT-only control
- the result is cleaner than the old same-gate sweep:
  - no final-test contamination
  - no ambiguous sparse frontier
  - just a flat dev-side null result
- this recipe should therefore **not** be promoted back to the frozen strict `29`-example gate

## 2026-03-15 Week 3 Dev-Pool Structural Recipe 2 (`rollout-pref-only`)

Status: completed

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index <0|1|2|3> --num-folds 4 --fold-seed 17 \
  --train-gpu <gpu> --eval-gpu <gpu> \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --lambda-n 24 --lambda-inv 8 \
  --pref-step-multiplier 0.0 \
  --pref-rollout-multiplier 1.0 \
  --pref-anchor-multiplier 1.0 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds \
  --num-folds 4 \
  --output-path outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold_compare_summary.json`

Observed result:

- the dev-side compare still covers all `81` dev examples with disjoint 4-fold evaluation:
  - `num_unique_eval_examples = 81`
  - `all_eval_ids_disjoint = true`
- CNT vs matched SFT-only control is no longer a flat tie, but the new separation is still a sparse frontier:
  - `mean_delta_drop_solve = +0.0127`
  - `mean_delta_n_t = +0.0017`
  - `mean_delta_n_t_weighted = -0.0123`
  - `nonzero_delta_folds = [0, 2]`
- aggregate rollout readout:
  - base:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 1.0000`
    - `mean_n_t_weighted = 0.0190`
  - control:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9805`
    - `mean_n_t_weighted = 0.0380`
  - CNT:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 0.9932`
    - `mean_n_t_weighted = 0.0257`
- fold structure:
  - fold00: `drop_solve +0.0270`, `weighted N_t -0.0265`
  - fold01: exact tie
  - fold02: `drop_solve +0.0238`, `weighted N_t -0.0227`
  - fold03: exact tie
- offline pair metrics still move in the expected direction:
  - CNT improves `pref_margin_mean` over control in every fold
  - but the rollout gain stays sparse and does not turn into a broad dev-side win

Interpretation:

- turning off `step` preference while keeping `rollout` and `anchor` preference active does change behavior
- however, it recreates the same Week 3 frontier at dev-pool scale:
  - utility moves slightly toward CNT
  - `weighted N_t` moves away from CNT
- this is stronger than the old tiny-gate frontier because it survives on the hygienic `81`-example dev pool
- but it is still **not** enough to promote back to the frozen strict `29`-example final-test gate

Relevant code paths:

- `src/cnt_research/math/stage_b.py`
- `scripts/run_math_stage_b_training.py`
- `scripts/run_math_stage_b_fold_compare.py`
- `scripts/run_math_stage_b_split_compare.py`

## 2026-03-15 Week 3 Dev-Pool Structural Recipe 3 (`original_counterfactual_pref`)

Status: completed

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index <0|1|2|3> --num-folds 4 --fold-seed 17 \
  --train-gpu <gpu> --eval-gpu <gpu> \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --anchor-pair-mode original_counterfactual_pref \
  --lambda-n 24 --lambda-inv 8 \
  --pref-step-multiplier 0.0 \
  --pref-rollout-multiplier 1.0 \
  --pref-anchor-multiplier 1.0 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260315_recipe_dev_signal11_rolloutprefonly_folds/fold<00|01|02|03>/base_rollout \
  --output-root outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds \
  --num-folds 4 \
  --output-path outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold_compare_summary.json`

Observed result:

- this recipe adds semantic original-prefix negatives on top of `signal11`:
  - train `pref_anchor_original_cf = 185`
  - eval `pref_anchor_original_cf = 47`
- the compare still covers all `81` dev examples with disjoint 4-fold evaluation:
  - `num_unique_eval_examples = 81`
  - `all_eval_ids_disjoint = true`
- CNT vs matched SFT-only control returns to an exact rollout tie:
  - `mean_delta_drop_solve = 0.0`
  - `mean_delta_n_t = 0.0`
  - `mean_delta_n_t_weighted = 0.0`
  - `nonzero_delta_folds = []`
- aggregate rollout readout:
  - base:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 1.0000`
    - `mean_n_t_weighted = 0.0190`
  - control:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
  - CNT:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
- unlike `signal11`, even the previously non-zero folds (`fold00`, `fold02`) flatten to tie
- offline separation still grows:
  - each fold shows higher `pref_margin_mean` for CNT than control
  - but none of that extra offline preference separation turns into dev-side rollout gain

Interpretation:

- adding semantic original-prefix counterfactual negatives is strong enough to neutralize the `signal11` sparse frontier
- but it does so by collapsing back to a clean dev-side null, not by producing a broad win
- this means same-prompt plus anchor-side preference shaping is still not enough; the next unlock likely needs a genuinely cross-prompt protection term rather than another anchor-only negative
- this recipe should therefore **not** be promoted back to the frozen strict `29`-example gate

Relevant code paths:

- `src/cnt_research/math/stage_b.py`
- `scripts/build_math_stage_b_data.py`
- `scripts/run_math_stage_b_fold_compare.py`
- `scripts/run_math_stage_b_split_compare.py`

## 2026-03-16 Week 3 Dev-Pool Structural Recipe 4 (`cross-prompt protect`)

Status: completed

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index <0|1|2|3> --num-folds 4 --fold-seed 17 \
  --train-gpu <gpu> --eval-gpu <gpu> \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --anchor-pair-mode none \
  --protect-mode original_over_drop_hinge \
  --lambda-n 24 --lambda-inv 8 --lambda-protect 8 \
  --pref-step-multiplier 0.0 \
  --pref-rollout-multiplier 1.0 \
  --pref-anchor-multiplier 1.0 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260315_recipe_dev_signal12_anchorcf_folds/fold<00|01|02|03>/base_rollout \
  --output-root outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds \
  --num-folds 4 \
  --output-path outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold_compare_summary.json`

Observed result:

- this recipe adds a genuine cross-prompt protection term:
  - compare `original prompt -> gold suffix`
  - against `drop prompt -> repaired gold completion`
- protect rows are active in every fold:
  - fold00 eval `protect = 37`
  - fold01 eval `protect = 44`
  - fold02 eval `protect = 42`
  - fold03 eval `protect = 45`
- the rollout result is still an exact 4-fold tie:
  - `num_unique_eval_examples = 81`
  - `all_eval_ids_disjoint = true`
  - `mean_delta_drop_solve = 0.0`
  - `mean_delta_n_t = 0.0`
  - `mean_delta_n_t_weighted = 0.0`
  - `nonzero_delta_folds = []`
- aggregate rollout readout:
  - base:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 1.0000`
    - `mean_n_t_weighted = 0.0190`
  - control:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
  - CNT:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`
- the new offline protect metrics do not improve:
  - control:
    - `protect_accuracy = 0.2602`
    - `protect_margin_mean = -0.5072`
  - CNT:
    - `protect_accuracy = 0.2544`
    - `protect_margin_mean = -0.5156`

Interpretation:

- this is a stronger falsification than the anchor-only variants:
  - even a genuine cross-prompt protect term does not separate CNT from matched SFT-only control on rollout
  - and the protect metric itself drifts slightly in the wrong direction
- so the current Stage B bottleneck is not just “missing original-prefix protection”
- this recipe should therefore **not** be promoted back to the frozen strict `29`-example gate

Relevant code paths:

- `src/cnt_research/math/stage_b.py`
- `scripts/build_math_stage_b_data.py`
- `scripts/run_math_stage_b_training.py`
- `scripts/run_math_stage_b_fold_compare.py`
- `scripts/run_math_stage_b_split_compare.py`

## 2026-03-16 Week 3 Dev-Pool Structural Recipe 5 (`bundle-level cross-prefix ranking`)

Status: completed

Reproducible commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer

PYTHONPATH=src python scripts/run_math_stage_b_fold_compare.py \
  --train-records outputs/math_stage_a_20260311_filter03_conservative_merged112/filtered_train_records.jsonl \
  --audit-kept outputs/math_stage_b_20260315_gate_bundle_audit08_strict29/recipe_dev_audit_kept.jsonl \
  --success-trace-path outputs/countertrace_mini_math_20260311_merged03/math_success_traces.jsonl \
  --fold-index <0|1|2|3> --num-folds 4 --fold-seed 17 \
  --train-gpu <gpu> --eval-gpu <gpu> \
  --epochs 1 --learning-rate 1e-6 \
  --weight-source heldout \
  --weight-field weight_normalized \
  --pair-completion-mode step_and_rollout \
  --anchor-mode original_rollout \
  --anchor-pair-mode none \
  --protect-mode none \
  --bundle-mode original_drop_paraphrase \
  --lambda-n 0 --lambda-inv 0 --lambda-protect 0 \
  --lambda-bundle-rank 24 --lambda-bundle-equiv 8 \
  --pref-step-multiplier 0.0 \
  --pref-rollout-multiplier 0.0 \
  --pref-anchor-multiplier 0.0 \
  --drop-sft-filter one_side_positive \
  --continuation-max-new-tokens 120 \
  --reuse-base-rollout-from outputs/math_stage_b_20260316_recipe_dev_signal13_protect_folds/fold<00|01|02|03>/base_rollout \
  --output-root outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds

python scripts/summarize_math_stage_b_fold_compare.py \
  --fold-root outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds \
  --num-folds 4 \
  --output-path outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold_compare_summary.json
```

Outputs:

- `outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold00/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold01/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold02/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold03/comparison_summary.json`
- `outputs/math_stage_b_20260316_recipe_dev_signal14_bundle_v2_folds/fold_compare_summary.json`

Observed result:

- this is the first truly different Stage B family after the prior `pref/equiv/protect` line:
  - bundle rows compare `original prompt -> gold suffix`
  - against `drop prompt -> full repaired gold completion`
  - while also penalizing deviation between `original prompt -> gold suffix` and `paraphrase prompt -> same gold suffix`
- the implementation is live, not a dataset-only stub:
  - bundle rows appear in every dev fold
  - bundle-specific offline metrics are present in `stage_b_training_summary.json`
  - zero-weight rows are now short-circuited in training so the dev loop does not waste compute on inactive losses
- aggregate dev-side rollout result:
  - `num_unique_eval_examples = 81`
  - `all_eval_ids_disjoint = true`
  - `mean_delta_drop_solve = -0.0060`
  - `mean_delta_n_t = -0.0040`
  - `mean_delta_n_t_weighted = +0.0057`
  - `nonzero_delta_folds = [2]`
- fold-wise behavior:
  - fold00: exact tie on rollout, but offline bundle metrics improve
  - fold01: exact tie on rollout, but offline bundle metrics improve
  - fold02: sparse frontier
    - `delta mean_original_solve = -0.0238`
    - `delta mean_drop_solve = -0.0238`
    - `delta mean_n_t_weighted = +0.0227`
  - fold03: exact tie on rollout, but offline bundle metrics improve
- aggregate rollout readout:
  - base:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 1.0000`
    - `mean_n_t_weighted = 0.0190`
  - control:
    - `mean_original_solve = 1.0000`
    - `mean_drop_solve = 0.9932`
    - `mean_n_t_weighted = 0.0257`
  - CNT:
    - `mean_original_solve = 0.9940`
    - `mean_drop_solve = 0.9873`
    - `mean_n_t_weighted = 0.0313`

Interpretation:

- this is **not** a broad dev-side win
- the new family is genuinely active offline:
  - `bundle_rank_margin_mean` improves in all four folds
  - `sft_nll_mean` improves in all four folds
- but rollout separation is still not in the right regime:
  - three folds stay exact ties
  - one fold reproduces the familiar utility-vs-weighted-`N_t` frontier, now on a genuinely new family
- so this recipe should **not** be promoted back to the frozen strict `29`-example gate
- after `signal10` through `signal14`, the current Week 3 evidence is now stronger:
  - several structurally different Stage B families can move offline margins
  - but none yet convert that movement into a stable CNT-over-control dev-side rollout gain

Relevant code paths:

- `src/cnt_research/math/stage_b.py`
- `scripts/build_math_stage_b_data.py`
- `scripts/run_math_stage_b_training.py`
- `scripts/run_math_stage_b_fold_compare.py`
- `scripts/run_math_stage_b_split_compare.py`
