# Results

## 2026-03-09 Week 1 Bootstrap

Status: first executable pass completed.

Planned reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py --per-domain 12'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py --max-quartets 6'
```

Outputs:

- `data/generated/craft_core_week1.jsonl`
- `artifacts/audit/craft_core_summary.json`
- `artifacts/audit/artifact_audit_summary.json`
- `artifacts/audit/blind_audit_packet.md`
- `artifacts/pilot/qwen_pilot_results.json`

Dataset summary:

- `36` quartets, `432` traces total
- Domains: algebra, graph_path, blocksworld
- Verbalizers: `9` total, `3` per domain

Artifact audit summary:

- `validity_style_accuracy = 0.4923`
- `validity_style_auroc = 0.5082`
- `answer_style_accuracy = 0.4615`
- `length_only_validity_accuracy = 0.4615`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Interpretation:

- The current pilot generator does not show obvious shallow or length-only artifacts.
- The human blind audit packet is prepared but still needs an external reviewer.

Qwen3-1.7B pilot setup:

- Environment: `infer`
- Checkpoint root: `/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots`
- Sampling: `6` quartets balanced across domains
- Prompt mode: answer-visible and answer-masked, both using `/no_think`

Selected quartets:

- `algebra-0000`
- `blocksworld-0000`
- `graph-0000`
- `algebra-0001`
- `blocksworld-0001`
- `graph-0001`

Qwen pilot metrics:

- Visible: `ordinary_accuracy = 0.6667`, `ordinary_auroc = 0.6728`, `amcd = 0.4722`, `ass_total = 48.8889`
- Masked: `ordinary_accuracy = 0.6667`, `ordinary_auroc = 0.6767`, `amcd = 0.3611`, `ass_total = 6.6667`

Initial conclusions:

- The answer-visible prompt judge is much more answer-sensitive than the masked variant on the current pilot (`ASS_total` gap of `42.2222`), which is directionally consistent with the proposal's leakage concern.
- Both visible and masked prompt judges remain weak on answer-matched local discrimination (`AMCD < 0.5`), so the present pilot is a diagnosis signal, not a usable verifier yet.
- The masked prompt baseline does not yet dominate the visible setup on AMCD, so the Week 2 baseline comparison still needs a stronger implementation than raw prompting.

## 2026-03-10 Blind Audit Status Check

Status: blind-audit materials refreshed; external human review still pending.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py'
```

Outputs:

- `artifacts/audit/blind_audit_hard_v2.md`
- `artifacts/audit/blind_audit_hard_v2_form.csv`
- `artifacts/audit/blind_audit_hard_v2_key.json`
- `artifacts/audit/blind_audit_hard_v2_summary.json`

What was checked:

- The repository did not contain a completed human blind-audit verdict.
- `artifacts/audit/blind_audit_hard_smoke_manual.md` was not a filled review sheet; it only mirrored packet-style content.
- The older packet exporter always took the first sorted quartets and only one implicit verbalizer, which made the packet narrower than intended.

Refresh details:

- Added a dedicated packet builder script: `scripts/build_blind_audit_packet.py`
- Added dataset loading plus balanced packet export in `src/civic_prm/generator.py`
- New packet now uses:
  - domain-balanced quartet sampling (`3` algebra, `3` graph_path, `3` blocksworld)
  - seeded randomization over item order within the selected quartets
  - randomized trace order inside each item
  - randomized verbalizer selection per quartet
  - a reviewer response block in the packet
  - a separate CSV response form
  - a hidden answer key kept out of the reviewer-facing packet

Current interpretation:

- Blind audit is still not complete in the proposal sense, because no external reviewer judgments have been collected yet.
- The repo now contains a reviewer-ready packet rather than only an internal packet draft.
- Any writeup should continue to say that human blind audit is pending, but the operational blocker is now reviewer time rather than missing materials.

### 2026-03-10 Internal Subagent Blind Review

Status: completed as an internal sanity check; not a substitute for the proposal's human blind audit.

Inputs:

- reviewer packet only: `artifacts/audit/blind_audit_hard_v2.md`
- no answer key or history files shown to the reviewers

Output:

- `artifacts/audit/blind_audit_hard_v2_internal_review.md`

Protocol:

- Spawned `2` independent subagent reviewers
- Both were instructed to judge only which trace looked more artificially edited
- Both were forbidden from opening the answer key

Outcome:

- Reviewer agreement on `more_artificial`: `9/9`
- Both reviewers judged the packet as easy to flag as synthetic
- Shared failure mode: local corruption while the final clean conclusion line remained copied

Interpretation:

- The current `v2` packet is better packaged than the original packet, but it still fails the stronger substantive blind-audit criterion.
- The limiting issue is not missing reviewer materials any more; it is that the underlying invalid traces remain too obviously hand-edited.
- Proposal-wise, this should be treated as a negative internal blind-audit result and a benchmark-hardening signal, not as a completed human audit.

## 2026-03-10 Blind-Audit Hardening Branch (`hard_blindfix_v1`)

Status: first benchmark-hardening branch completed; partial improvement only.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py --difficulty hard_blindfix --per-domain 12 \
  --output data/generated/craft_core_hard_blindfix_v1.jsonl \
  --summary-output artifacts/audit/craft_core_hard_blindfix_v1_summary.json \
  --blind-audit-output artifacts/audit/blind_audit_hard_blindfix_v1_seedpacket.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_blindfix_v1.jsonl \
  --output artifacts/audit/blind_audit_hard_blindfix_v1.md \
  --answer-key-output artifacts/audit/blind_audit_hard_blindfix_v1_key.json \
  --response-form-output artifacts/audit/blind_audit_hard_blindfix_v1_form.csv \
  --summary-output artifacts/audit/blind_audit_hard_blindfix_v1_summary.json \
  --sample-quartets 9 --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_blindfix_v1.jsonl \
  --output artifacts/audit/artifact_audit_hard_blindfix_v1.json'
```

Key outputs:

- `data/generated/craft_core_hard_blindfix_v1.jsonl`
- `artifacts/audit/blind_audit_hard_blindfix_v1.md`
- `artifacts/audit/blind_audit_hard_blindfix_v1_form.csv`
- `artifacts/audit/blind_audit_hard_blindfix_v1_key.json`
- `artifacts/audit/blind_audit_hard_blindfix_v1_internal_review.md`
- `artifacts/audit/artifact_audit_hard_blindfix_v1.json`

What changed:

- Added a `hard_blindfix` generation branch for algebra, graph_path, and blocksworld.
- Targeted fix: remove the most obvious copied-clean-ending failure mode from invalid traces.
- Did not overwrite the existing `hard` dataset or any previously reported Week 2-6 result.

Artifact audit on the new branch:

- `validity_style_accuracy = 0.5077`
- `validity_style_auroc = 0.5263`
- `length_only_validity_accuracy = 0.5308`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Internal blind-review result:

- Exact agreement on `more_artificial`: `7/9`
- Algebra: `3/3` items still unanimously flagged as artificial
- Graph/path: `3/3` items still unanimously flagged as artificial
- Blocksworld: much improved; `1/3` unanimous `Neither`, `2/3` low-confidence disagreement

Interpretation:

- The blindfix branch succeeded at the narrow goal of reducing the copied-ending artifact.
- The branch did not yet solve the full blind-audit problem, because algebra and graph/path remain easy to flag through repeated single-step numeric corruption.
- This should be treated as partial progress, not as a passing blind audit.

## 2026-03-10 LLM-Assisted Benchmark v2 Pilot (`q2b`)

Status: first API-assisted benchmark-v2 pilot completed.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --quartets-per-domain 2 \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2b.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_rows.jsonl'
```

Key outputs:

- `data/generated/craft_core_hard_llm_v2_pilot_q2b.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_summary.json`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2b_rows.jsonl`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2b.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2b.md`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2b_internal_review.md`

Pipeline:

- Source dataset: `craft_core_hard_blindfix_v1`
- Surface generation: Ark API rewrite
- Validation: deterministic anchor-preservation checks
- Fallback: per-step rewrite when full-trace rewrite fails validation

Pilot summary:

- Selected quartets: `6` (`2` per domain)
- Source traces: `72`
- Rewritten traces: `72/72`
- Usage: `37537` total tokens over `226` API calls

Artifact audit on the v2 pilot:

- `validity_style_accuracy = 0.7273`
- `validity_style_auroc = 0.7810`
- `length_only_validity_auroc = 0.4917`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Interpretation of artifact audit:

- The API-assisted route does not automatically solve style artifacts.
- In fact, on this small pilot the validity-style classifier remains much stronger than desired.
- The issue now looks less like copied endings and more like domain-specific stylistic asymmetry in the rewritten invalid traces.

Internal blind-review result on the v2 pilot:

- Blocksworld items (`item-02`, `item-05`) were rated `Neither` by both reviewers.
- Algebra items (`item-01`, `item-04`) were still strongly flagged as artificial.
- Graph items (`item-03`, `item-06`) remained suspicious because of patched comparison totals and template-like route phrasing.

Conclusion:

- The `LLM-assisted benchmark v2` route is viable as a generation mechanism.
- The current pilot improves over the old packet on blocksworld and removes the pure copied-ending bottleneck.
- It still does not pass the stronger blind-audit bar on algebra and graph/path.

## 2026-03-10 LLM-Assisted Benchmark v2 Debug Pass (`q2c` -> `q2d`)

Status: `q2c` was invalidated by a stepwise-fallback bug; `q2d` is the repaired rerun on `hard_blindfix_v2`.

Bug diagnosis:

- `q2c` exposed a regression in `src/civic_prm/api_rewrite.py`: `_rewrite_record_stepwise_with_api(...)` returned from inside the per-step loop.
- Any full-trace rewrite that fell back to stepwise mode therefore returned after the first rewritten step.
- This silently produced one-step traces and made `q2c` unusable as a benchmark artifact even though its summary metrics looked improved.

Single-case verification after the fix:

- `algebra-hard-0010-alg_v3-invalid_correct` now rewrites from `3` source steps to `3` rewritten steps.
- `blocksworld-hard-0008-bw_v2-valid_correct` now rewrites from `5` source steps to `5` rewritten steps.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v2.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2d.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_summary.json \
  --seed 17'
```

Key outputs:

- `data/generated/craft_core_hard_llm_v2_pilot_q2d.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_summary.json`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2d_rows.jsonl`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2d.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d.md`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2d_internal_review.md`

Superseded artifacts:

- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2c_summary.json`
- `data/generated/craft_core_hard_llm_v2_pilot_q2c.jsonl`

Do not use `q2c` for evaluation; it was generated before the stepwise-fallback bug was fixed.

`q2d` summary:

- Selected quartets: `6` (`2` per domain)
- Source traces: `72`
- Rewritten traces: `70`
- Failed traces: `2`, both from `algebra-hard-0003` / `alg_v2`
- Usage: `34375` total tokens over `163` API calls

Failure details:

- `algebra-hard-0003-alg_v2-valid_correct`: `missing step anchors: ['-18']`
- `algebra-hard-0003-alg_v2-invalid_correct`: `missing step anchors: ['-6']`

Sanity checks on `q2d`:

- No one-step traces remain after the bug fix.
- Step-count distribution is now exactly domain-shaped: `22` traces with `3` steps (algebra) and `48` traces with `5` steps (graph/path + blocksworld).
- The only incomplete quartet family is `algebra-hard-0003` / `alg_v2_llmv2`, which retains only the two swapped traces because the two correct-answer traces failed deterministic validation.

Artifact audit on `q2d`:

- `validity_style_accuracy = 0.5455`
- `validity_style_auroc = 0.6198`
- `length_only_validity_auroc = 0.4050`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Interpretation of artifact audit:

- `q2d` is materially better than `q2b` on shallow style leakage (`0.6198` vs `0.7810` AUROC).
- Length cues remain non-informative.
- The benchmark-v2 route is now clearly improving on shallow artifacts, even before it clears human-style review.

Internal blind-review result on `q2d`:

- Reviewer exact agreement: `6/6`
- `item-02` (blocksworld) was rated `Neither` by both reviewers.
- `item-05` (blocksworld) was still flagged because Trace 1 uses overt `First/Next/Then/Now/Finally` scaffolding.
- Both algebra items remained easy to flag as synthetic.
- Both graph/path items remained easy to flag because one anomalous total still reads like a patched seam.

Conclusion:

- The engineering bug behind `q2c` is fixed and `q2d` is the valid current benchmark-v2 pilot.
- `q2d` materially improves artifact audit versus `q2b`, especially by removing the truncation bug and reducing shallow style leakage.
- It still does not pass the stronger blind-audit bar, because algebra and graph/path invalid traces remain too visibly patched, and one blocksworld item is still over-scaffolded.

## 2026-03-10 Benchmark-v2 Hardening Round 2 (`hard_blindfix_v3`, `q2e`, `q2f`, `q2g`)

Status: completed a second benchmark-v2 hardening round with a new source fork plus domain-aware rewrite constraints. The round improved shallow style leakage further, but it also exposed a new coverage-vs-naturalness frontier concentrated in algebra.

Code changes in this round:

- `src/civic_prm/domains/algebra.py`
  - added `hard_blindfix_v3`
  - for blind-audit v3, algebra verbalizers now render explanatory steps rather than bare statement shells
- `src/civic_prm/domains/graph_path.py`
  - added `hard_blindfix_v3`
  - graph blind-audit v3 now states recorded route totals directly instead of showing explicit edge-sum arithmetic in the step text
- `src/civic_prm/domains/blocksworld.py`
  - `hard_blindfix_v3` now routes through the same legality-aware branch
- `src/civic_prm/api_rewrite.py`
  - added domain-aware rewrite guidance
  - added graph-path guard against back-filling new numeric anchors into a step
  - added blocksworld stepwise smoothing to strip discourse markers
  - added algebra stepwise smoothing to prefer natural operation sentences over bare equations

Reproducible commands for the current best branch (`q2f`):

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py \
  --difficulty hard_blindfix_v3 \
  --output data/generated/craft_core_hard_blindfix_v3.jsonl \
  --summary-output artifacts/audit/craft_core_hard_blindfix_v3_summary.json \
  --blind-audit-output artifacts/audit/blind_audit_hard_blindfix_v3_seedpacket.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v3.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2f_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2f_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2f.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_summary.json \
  --seed 17'
```

Key artifacts for the round:

- `data/generated/craft_core_hard_blindfix_v3.jsonl`
- `artifacts/audit/craft_core_hard_blindfix_v3_summary.json`
- `data/generated/craft_core_hard_llm_v2_pilot_q2e.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2e_summary.json`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2e.json`
- `data/generated/craft_core_hard_llm_v2_pilot_q2f.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2f_summary.json`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2f.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f.md`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2f_internal_review.md`
- `data/generated/craft_core_hard_llm_v2_pilot_q2g.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2g_summary.json`

Round summaries:

`q2e`

- Source: `hard_blindfix_v3`
- Rewritten traces: `67/72`
- Failed traces: `5`
- Domain counts: algebra `19`, graph_path `24`, blocksworld `24`
- Usage: `35851` total tokens over `109` API calls
- Shallow audit:
  - `validity_style_auroc = 0.5182`
  - `length_only_validity_auroc = 0.4091`
- Interpretation:
  - this round confirmed the new direction is working
  - graph/path arithmetic back-fill is largely gone
  - but algebra packet quality still needed another prose fix before blind review

`q2f`

- Rewritten traces: `64/72`
- Failed traces: `8`
- Domain counts: algebra `16`, graph_path `24`, blocksworld `24`
- Usage: `34829` total tokens over `107` API calls
- Shallow audit:
  - `validity_style_auroc = 0.4222`
  - `length_only_validity_auroc = 0.3000`
- Internal blind review:
  - exact agreement `4/6`
  - algebra still fails (`2/2` flagged)
  - graph/path drops to `1/2` agreement with one low-signal item
  - blocksworld is mostly low-signal (`1/2` exact `Neither`, `1/2` disputed)
- Interpretation:
  - `q2f` is the current best benchmark-v2 surface-hardening point
  - graph/path and blocksworld are much closer to blind-audit viability
  - the remaining dominant bottleneck is algebra sentence stitching / splice artifacts

`q2g`

- Rewritten traces: `63/72`
- Failed traces: `9`
- Domain counts: algebra `15`, graph_path `24`, blocksworld `24`
- Usage: `37983` total tokens over `125` API calls
- All failures again come from algebra.
- Interpretation:
  - `q2g` does not improve the main frontier
  - it confirms the current branch is now limited by algebra coverage, not graph or blocksworld
  - because it is dominated on coverage by `q2f`, it was not promoted to the new default blind-review packet

Operational conclusion:

- The second hardening round materially improved the benchmark-v2 branch on shallow style leakage:
  - `q2d`: `0.6198`
  - `q2e`: `0.5182`
  - `q2f`: `0.4222`
- The bottleneck has now narrowed:
  - graph/path: substantially improved
  - blocksworld: mostly low-signal
  - algebra: still the limiting domain
- The current frontier is no longer “generic syntheticness vs not”.
- It is now:
  - cleaner graph/blocksworld surface realization
  - versus lower algebra coverage under stricter anchor-preserving rewrite constraints

## 2026-03-10 Benchmark-v2 Hardening Round 3 (`q2h`, algebra-only coverage recovery)

Status: completed an algebra-focused `q2h` rerun that fixes a real full-trace parsing failure, improves algebra coverage, and confirms that coverage recovery alone is not enough to clear the blind-audit bar.

Code changes in this round:

- `src/civic_prm/api_rewrite.py`
  - added an algebra-specific post-parse coercion for full-trace payloads that incorrectly return `"steps"` as a single string
  - the coercion splits `First/Next/Then/Finally` style algebra prose back into the expected `3`-step list before validation

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v3.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2h.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2h_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2h_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2h.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2h.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2h.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h_summary.json \
  --seed 17'
```

Key artifacts:

- `data/generated/craft_core_hard_llm_v2_pilot_q2h.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2h_summary.json`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2h_rows.jsonl`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2h.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h.md`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2h_internal_review.md`

Round summary:

- Rewritten traces: `66/72`
- Failed traces: `6`
- Domain counts: algebra `18`, graph_path `24`, blocksworld `24`
- Usage: `33092` total tokens over `88` API calls
- All failures remain in algebra.

Shallow audit:

- `validity_style_auroc = 0.5960`
- `length_only_validity_auroc = 0.7879`

Internal blind review:

- exact agreement `4/6`
- algebra still fails (`2/2` exact flagged)
- graph/path is mixed (`1` flagged item, `1` neutral item)
- blocksworld becomes slightly noisier than `q2f` (`0/2` exact agreement)

Additional diagnostic:

- The length regression is real, not just classifier noise:
  - graph/path invalid traces average `345.4` step characters vs `312.7` for valid traces
  - blocksworld invalid traces average `279.4` step characters vs `261.3` for valid traces

Interpretation:

- `q2h` successfully recovers algebra coverage by fixing a full-trace payload-shape failure that had previously forced unnecessary fallback or rejection.
- That recovery does **not** make `q2h` the new blind-audit-facing default:
  - shallow validity-style leakage is worse than `q2f`
  - length leakage regresses sharply
  - internal blind review remains at `4/6` exact agreement, with algebra still clearly exposed
- Operationally, `q2h` is a coverage-recovery branch, not the new best benchmark-v2 point.
- `q2f` remains the current best blind-audit-facing packet; `q2h` is useful evidence that coverage and blind-audit quality are now decoupled.

## 2026-03-10 Benchmark-v2 Hardening Round 4 (`hard_blindfix_v4`, `q2i`)

Status: completed an algebra-only source redesign attempt plus a new `q2i` rerun. The attempt is negative: making algebra invalid traces look more like local algebra slips degraded rewrite coverage badly enough that the branch no longer supports a balanced blind-audit packet.

Code changes in this round:

- `src/civic_prm/domains/algebra.py`
  - added `hard_blindfix_v4`
  - for blind-audit-safe algebra invalid traces, replaced the earlier patched-ending style with a more local slip pattern:
    - wrong first equation followed by a too-aggressive `cancel the a`
    - or a `cancel the a` step after a valid first line
- `src/civic_prm/api_rewrite.py`
  - algebra smoothing now normalizes discourse openers for both full-trace and stepwise rewrites
  - this removes some valid-vs-invalid style asymmetry, but does not recover the new coverage loss
- `src/civic_prm/generator.py`
  - fixed blind-audit packet export to filter at the verbalizer level rather than only the quartet level
  - incomplete quartets are now skipped instead of crashing packet construction
- `src/civic_prm/domains/graph_path.py`, `src/civic_prm/domains/blocksworld.py`, `scripts/build_craft_core.py`
  - added `hard_blindfix_v4` routing so the new source fork can be built cleanly without mutating the older branches

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py \
  --difficulty hard_blindfix_v4 \
  --output data/generated/craft_core_hard_blindfix_v4.jsonl \
  --summary-output artifacts/audit/craft_core_hard_blindfix_v4_summary.json \
  --blind-audit-output artifacts/audit/blind_audit_hard_blindfix_v4_seedpacket.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2i.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2i_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2i_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2i.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2i.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2i.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2i.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2i_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2i_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2i_summary.json \
  --seed 17'
```

Key artifacts:

- `data/generated/craft_core_hard_blindfix_v4.jsonl`
- `artifacts/audit/craft_core_hard_blindfix_v4_summary.json`
- `data/generated/craft_core_hard_llm_v2_pilot_q2i.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2i_summary.json`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2i.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2i_summary.json`

Round summary:

- Rewritten traces: `62/72`
- Failed traces: `10`
- Domain counts: algebra `14`, graph_path `24`, blocksworld `24`
- Usage: `36119` total tokens over `119` API calls
- All `10` failures are algebra.

Shallow audit:

- `validity_style_auroc = 0.8000`
- `length_only_validity_auroc = 0.1250`

Blind-packet eligibility:

- `num_items = 4`
- `num_eligible_quartets = 4`
- `num_incomplete_quartets_skipped = 2`
- both skipped quartets are the algebra quartets, so the packet contains only graph/path and blocksworld items

Interpretation:

- `hard_blindfix_v4` does make the algebra invalid traces read more like local algebra slips at the source level.
- In practice, that source-level naturalness move is dominated by a new coverage failure:
  - algebra rewritten coverage drops from `18` (`q2h`) to `14`
  - the branch loses all algebra quartet eligibility for blind audit
- Because the resulting packet contains no algebra items, this round is not even a meaningful blind-audit candidate.
- `q2i` is therefore a clear negative result:
  - it is worse than `q2h` on coverage
  - worse than `q2f` on both coverage and shallow style leakage
  - and it cannot serve as the new benchmark-v2 default
- The next algebra move, if any, should target rewrite robustness / validation compatibility rather than introducing subtler source-level invalid semantics first.

## 2026-03-10 Benchmark-v2 Hardening Round 5 (`q2j`, algebra rewrite robustness)

Status: completed a rewrite-side algebra hardening pass on top of `hard_blindfix_v4`. This round fixes the `q2i` coverage collapse completely, but it still does not produce a blind-audit-facing win.

Code changes in this round:

- `src/civic_prm/api_rewrite.py`
  - algebra prompts now explicitly require the exact source equation fragment to remain verbatim in each rewritten step
  - added algebra step post-alignment so rewritten steps are snapped back to the source equation fragment when the LLM tries to “helpfully” correct the math

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_llm_benchmark_v2.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_hard_llm_v2_pilot_q2j.jsonl \
  --summary-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2j_summary.json \
  --cache-output artifacts/generated/craft_core_hard_llm_v2_pilot_q2j_rows.jsonl \
  --quartets-per-domain 2 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2j.jsonl \
  --output artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2j.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_hard_llm_v2_pilot_q2j.jsonl \
  --output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j.md \
  --response-form-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j_form.csv \
  --answer-key-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j_key.json \
  --summary-output artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j_summary.json \
  --seed 17'
```

Key artifacts:

- `data/generated/craft_core_hard_llm_v2_pilot_q2j.jsonl`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2j_summary.json`
- `artifacts/generated/craft_core_hard_llm_v2_pilot_q2j_rows.jsonl`
- `artifacts/audit/artifact_audit_hard_llm_v2_pilot_q2j.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j.md`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j_summary.json`
- `artifacts/audit/blind_audit_hard_llm_v2_pilot_q2j_internal_review.md`

Round summary:

- Rewritten traces: `72/72`
- Failed traces: `0`
- Domain counts: algebra `24`, graph_path `24`, blocksworld `24`
- Usage: `46688` total tokens over `162` API calls

Shallow audit:

- `validity_style_auroc = 0.6281`
- `length_only_validity_auroc = 0.5372`

Internal blind review:

- exact agreement `6/6`
- algebra `2/2` exact flagged
- graph/path `2/2` exact flagged
- blocksworld `2/2` exact `Neither`

Interpretation:

- `q2j` fully solves the rewrite-robustness problem exposed by `q2i`.
- It does not solve the blind-audit problem. In fact, the stronger algebra/graph fidelity makes the wrong arithmetic easier for humans to detect:
  - algebra invalid traces now preserve the local corruption cleanly enough that the `15 -> 4 -> 1` or `-24 -> -3 -> -6` inconsistency is obvious
  - graph invalid traces are also easy to catch when the wrong total is preserved exactly against a visible edge list
- Operationally, `q2j` is a *faithful but human-detectable* branch:
  - best on coverage
  - worse than `q2f` on blind review
- `q2f` therefore remains the current best blind-audit-facing packet.

## 2026-03-09 Week 2 Frozen-Backbone Baselines

Status: first strong same-backbone baseline pass completed.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py'
```

Key artifacts:

- `artifacts/baselines/week2_baselines.json`
- `artifacts/features/visible_features.pt`
- `artifacts/features/masked_features.pt`
- `artifacts/features/step_only_features.pt`

Setup:

- Backbone: frozen `Qwen3-1.7B`
- Split: quartet-level split with seed `17`
- Quartets: `24` train / `6` val / `6` test
- Records: `288` train / `72` val / `72` test

Test metrics:

- `step_only_bce`: `ordinary_accuracy = 0.6944`, `ordinary_auroc = 0.7685`, `amcd = 0.7778`, `ass_total = 0.0`
- `visible_bce`: `ordinary_accuracy = 0.8750`, `ordinary_auroc = 0.9498`, `amcd = 0.9722`, `ass_total = 0.0736`
- `masked_bce`: `ordinary_accuracy = 0.7778`, `ordinary_auroc = 0.8951`, `amcd = 1.0000`, `ass_total = 0.0055`
- `pairwise_visible`: `ordinary_accuracy = 0.5972`, `ordinary_auroc = 0.7647`, `amcd = 0.9722`, `ass_total = 0.0366`

Notable slices:

- `step_only_bce` is strong on algebra and graph_path but fails badly on blocksworld (`ordinary_accuracy = 0.3333`, `ordinary_auroc = 0.2778`).
- `visible_bce` is the best ordinary classifier on this pilot.
- `masked_bce` has the best answer-matched discrimination and the lowest answer sensitivity.
- `pairwise_visible` keeps very high `AMCD` but loses ordinary calibration / separability.

Interpretation:

- The current synthetic pilot no longer shows the prompt-level leakage pattern once we move to trained frozen-backbone baselines.
- The proposal's **Risk 3** is active on this pilot: the same-backbone answer-masked baseline is already extremely strong, with lower `ASS_total` and slightly better `AMCD` than the visible BCE model.
- On the present benchmark slice, there is not yet evidence that a more complex invariant objective is necessary to recover process discrimination.
- This does not falsify the proposal, but it does mean the algorithmic contribution is not yet earned on the current pilot; the benchmark and evaluation protocol are presently stronger than the repair claim.

## 2026-03-09 Week 2 Verbalizer-Holdout Stress Test

Status: stricter multi-verbalizer consistency check completed.

Protocol:

- Reuse the frozen `Qwen3-1.7B` feature cache.
- Keep quartet split unchanged.
- For each slot `v1`, `v2`, `v3`, train on non-held-out verbalizers from train/val quartets and test only on the held-out verbalizer from test quartets.

Macro-averaged held-out verbalizer metrics:

- `step_only_bce`: `ordinary_accuracy = 0.5555`, `ordinary_auroc = 0.6574`, `amcd = 0.7222`, `ass_total = 0.0`
- `visible_bce`: `ordinary_accuracy = 0.6945`, `ordinary_auroc = 0.8634`, `amcd = 0.9722`, `ass_total = 0.0695`
- `masked_bce`: `ordinary_accuracy = 0.6667`, `ordinary_auroc = 0.7963`, `amcd = 1.0000`, `ass_total = 0.0012`
- `pairwise_visible`: `ordinary_accuracy = 0.6806`, `ordinary_auroc = 0.8125`, `amcd = 0.9722`, `ass_total = 0.0433`

Per-slot note:

- `masked_bce` keeps `AMCD = 1.0` on all three held-out verbalizer slots.
- `visible_bce` and `pairwise_visible` remain strong but retain noticeably higher answer sensitivity.
- `step_only_bce` still lags and remains weakest on planning-style traces.

Interpretation:

- The masked same-backbone baseline is not merely memorizing one specific verbalizer template.
- Risk 3 persists under a stricter protocol: on the current pilot, masking the answer still preserves nearly all useful process discrimination while sharply reducing answer sensitivity.
- The next benchmark-hardening move should target task difficulty and naturalness, not only additional paraphrase diversity.

## 2026-03-09 Harder Benchmark Slice

Status: harder task-difficulty slice built and evaluated.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_craft_core.py --difficulty hard --per-domain 12 \
  --output data/generated/craft_core_hard.jsonl \
  --summary-output artifacts/audit/craft_core_hard_summary.json \
  --blind-audit-output artifacts/audit/blind_audit_hard.md'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --output artifacts/audit/artifact_audit_hard.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --output artifacts/baselines/week2_baselines_hard.json \
  --feature-cache-dir artifacts/features_hard'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --max-quartets 6 \
  --output artifacts/pilot/qwen_pilot_hard.json'
```

Hard slice design changes:

- Algebra: three-step shifted equations instead of two-step linear solves.
- Graph/path: four three-edge candidate routes with near-tie totals and explicit comparison steps.
- Blocksworld: four blocks and longer plans, with non-noop continuations after the edited locus.

Artifact audit:

- `validity_style_accuracy = 0.4385`
- `validity_style_auroc = 0.4370`
- `length_only_validity_accuracy = 0.4769`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Week 2 frozen-backbone baselines on the hard slice, quartet split:

- `step_only_bce`: `ordinary_auroc = 0.7037`, `amcd = 0.6111`, `ass_total = 0.0`
- `visible_bce`: `ordinary_auroc = 0.8873`, `amcd = 0.9167`, `ass_total = 0.0817`
- `masked_bce`: `ordinary_auroc = 0.8727`, `amcd = 0.8611`, `ass_total = 0.0067`
- `pairwise_visible`: `ordinary_auroc = 0.6551`, `amcd = 0.8611`, `ass_total = 0.0379`

Week 2 frozen-backbone baselines on the hard slice, held-out verbalizer macro average:

- `step_only_bce`: `ordinary_auroc = 0.6204`, `amcd = 0.6667`, `ass_total = 0.0`
- `visible_bce`: `ordinary_auroc = 0.6597`, `amcd = 0.8611`, `ass_total = 0.0696`
- `masked_bce`: `ordinary_auroc = 0.6759`, `amcd = 0.8611`, `ass_total = 0.0049`
- `pairwise_visible`: `ordinary_auroc = 0.6621`, `amcd = 0.8611`, `ass_total = 0.0443`

Local prompt judge on the hard slice:

- Visible: `ordinary_auroc = 0.4861`, `amcd = 0.0833`, `ass_total = 22.5`
- Masked: `ordinary_auroc = 0.5278`, `amcd = 0.1111`, `ass_total = 5.0`

Interpretation:

- Hardening the tasks lowered all trained baseline scores, especially on graph/path and step-only settings, so the benchmark is no longer trivially easy.
- The masked trained baseline is no longer clearly dominant on the easier quartet split, but under held-out verbalizer evaluation it still matches visible `AMCD` while keeping answer sensitivity near zero.
- Prompt-style judges remain highly answer-sensitive and perform poorly on local process discrimination even on the hard slice.
- The current evidence now supports a sharper separation: prompt evaluators leak strongly, whereas trained same-backbone verifiers can often recover process signal without needing the final answer.

## 2026-03-09 External Judge Pilot On Hard Slice

Status: external judge baseline pilot completed.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=... && export ARK_MODEL_ENDPOINT=... && export ARK_API_KEY=... && \
PYTHONPATH=src python scripts/run_api_judge_pilot.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --max-quartets 6 \
  --cache-output artifacts/api_judge/api_judge_pilot_hard_rows.jsonl \
  --summary-output artifacts/api_judge/api_judge_pilot_hard_summary.json'
```

Artifacts:

- `artifacts/api_judge/api_judge_pilot_hard_rows.jsonl`
- `artifacts/api_judge/api_judge_pilot_hard_summary.json`

Pilot scope:

- Selected quartets: `algebra-hard-0000`, `blocksworld-hard-0000`, `graph-hard-0000`, `algebra-hard-0001`, `blocksworld-hard-0001`, `graph-hard-0001`
- Calls: `144` total API requests
- Usage: `32256` prompt tokens, `1872` completion tokens, `34128` total tokens

External judge metrics:

- Visible: `ordinary_accuracy = 0.6528`, `ordinary_auroc = 0.6528`, `amcd = 0.3889`, `ass_total = 47.2222`
- Masked: `ordinary_accuracy = 0.6944`, `ordinary_auroc = 0.6944`, `amcd = 0.4167`, `ass_total = 11.1111`

Interpretation:

- The external closed judge behaves much more like the local prompt judge than like the trained frozen-head baselines.
- Visible judging is highly answer-sensitive on the hard slice, and masking the answer reduces but does not remove that sensitivity.
- Even after masking, the external judge is weak on answer-matched local discrimination (`AMCD < 0.5`), so it is not yet a strong process verifier.
- This strengthens the current emerging claim: leakage is obvious and large in judge-style evaluators, while trained same-backbone verifiers appear substantially more process-grounded on the current synthetic benchmark.

## 2026-03-09 Naturalized Transfer Slice

Status: natural-language transfer pilot completed.

Artifacts:

- `data/generated/craft_core_hard_natural_test.jsonl`
- `artifacts/natural/craft_core_hard_natural_test_summary.json`
- `artifacts/natural/natural_transfer_baselines.json`
- `artifacts/natural/qwen_pilot_natural.json`
- `artifacts/api_judge/api_judge_pilot_natural_summary.json`

Naturalization setup:

- Source: held-out test quartets from `data/generated/craft_core_hard.jsonl`
- Size: `72` traces across `6` quartets
- Naturalizer: local `Qwen3-1.7B` rewrite with deterministic fallback
- Rewrite success: `60` model rewrites and `12` heuristic fallbacks
- Safety rule: keep the original final answer line fixed to avoid label drift

Synthetic-train to natural-test frozen-backbone transfer:

- `step_only_bce`: `ordinary_auroc = 0.6528`, `amcd = 0.6667`, `ass_total = 0.0245`
- `visible_bce`: `ordinary_auroc = 0.8796`, `amcd = 0.9167`, `ass_total = 0.0899`
- `masked_bce`: `ordinary_auroc = 0.8318`, `amcd = 0.8611`, `ass_total = 0.0651`
- `pairwise_visible`: `ordinary_auroc = 0.6019`, `amcd = 0.7222`, `ass_total = 0.0450`

Local prompt judge on the naturalized slice:

- Visible: `ordinary_auroc = 0.4780`, `amcd = 0.0833`, `ass_total = 30.5556`
- Masked: `ordinary_auroc = 0.5625`, `amcd = 0.1944`, `ass_total = 8.3333`

External API judge on the naturalized slice:

- Visible: `ordinary_auroc = 0.6806`, `amcd = 0.4167`, `ass_total = 47.2222`
- Masked: `ordinary_auroc = 0.8611`, `amcd = 0.7222`, `ass_total = 16.6667`
- Usage: `33822` total tokens across `144` API calls

Interpretation:

- Natural-language shift weakens the apparent safety margin of the masked trained baseline: its `ASS_total` rises materially compared with the synthetic hard slice, even though it remains competitive on `AMCD`.
- The visible trained baseline stays slightly stronger on ordinary discrimination and `AMCD`, so the naturalized slice narrows but does not reverse the visible-vs-masked trained-head gap.
- Judge-style evaluators remain much more outcome-sensitive than trained heads under the same shift.
- The current evidence now supports a more precise proposal-aligned claim: leakage is strongly present in judge-style evaluators, while trained same-backbone verifiers show a milder but nonzero answer-sensitivity increase under naturalized transfer.

## 2026-03-09 Model-Generated Trace Pilot

Status: first genuinely model-generated trace slice completed.

Artifacts:

- `data/generated/craft_core_hard_model_generated.jsonl`
- `artifacts/generated/model_generated_summary.json`
- `artifacts/generated/generated_answer_swap_transfer.json`
- `artifacts/generated/generated_local_judge.json`
- `artifacts/generated/generated_api_judge_summary.json`

Pilot setup:

- Source problems: held-out hard-slice test quartets
- Generator: local `Qwen3-1.7B`
- Samples: `3` traces per problem across `6` held-out problems
- Dataset size: `18` original model-generated traces + `18` answer-swapped twins
- Original answer correctness: `13` correct / `5` incorrect

Trained same-backbone answer-swap transfer:

- `visible_bce`: `ass_total = 0.0298`, `mean_score_correct_answer = 0.8028`, `mean_score_incorrect_answer = 0.7742`
- `masked_bce`: `ass_total = 0.0`, `mean_score_correct_answer = 0.8040`, `mean_score_incorrect_answer = 0.8040`

Local deployment-style judge on model-generated traces:

- Visible: `ass_total = 2.2222`, `mean_score_correct_answer = 98.8889`, `mean_score_incorrect_answer = 98.8889`
- Masked: `ass_total = 0.0`, `mean_score_correct_answer = 100.0`, `mean_score_incorrect_answer = 100.0`

External deployment-style judge on model-generated traces:

- Visible: `ass_total = 35.0`, `mean_score_correct_answer = 46.1111`, `mean_score_incorrect_answer = 11.1111`
- Masked: `ass_total = 7.7778`, `mean_score_correct_answer = 44.4444`, `mean_score_incorrect_answer = 41.1111`
- Usage: `18497` total tokens across `72` API calls

Interpretation:

- The model-generated slice strengthens the current separation between trained heads and judge-style evaluators.
- The trained masked head stays almost perfectly answer-invariant on this pilot (`ASS_total = 0.0`), while the visible head shows only a small answer-swap response.
- The external judge again shows large answer sensitivity on the same traces, and masking sharply reduces but does not remove it.
- Because this slice lacks audited local validity labels, it is strongest as deployment-style answer-sensitivity evidence rather than `AMCD` evidence.

## 2026-03-09 Auditable Model-Generated Counterfactual Slice

Status: first `AMCD`-enabled slice derived from genuinely model-generated traces completed.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_counterfactual_slice.py'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_natural_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --output artifacts/generated/model_generated_counterfactual_transfer.json \
  --feature-cache-dir artifacts/generated/counterfactual_features'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --max-quartets 9 \
  --output artifacts/generated/model_generated_counterfactual_qwen.json'
```

Artifacts:

- `data/generated/craft_core_hard_model_generated_counterfactual.jsonl`
- `artifacts/generated/model_generated_counterfactual_summary.json`
- `artifacts/generated/model_generated_counterfactual_rejections.jsonl`
- `artifacts/generated/model_generated_counterfactual_transfer.json`
- `artifacts/generated/model_generated_counterfactual_qwen.json`

Counterfactual-builder coverage:

- Source rows: `18` original model-generated traces
- Accepted auditable anchors: `7`
- Counterfactual traces: `28`
- Accepted by domain: algebra `6`, graph_path `1`, blocksworld `0`

Deterministic rejection reasons:

- Blocksworld: `2` `noop_or_repeated_state`, `4` `illegal_multi_move_transition`
- Graph/path: `5` `missing_correct_path_conclusion`

Synthetic-train to auditable-generated-test frozen-backbone transfer:

- `step_only_bce`: `ordinary_auroc = 0.6939`, `amcd = 0.8571`, `ass_total = 0.0`
- `visible_bce`: `ordinary_auroc = 0.8367`, `amcd = 0.9286`, `ass_total = 0.0024`
- `masked_bce`: `ordinary_auroc = 0.8776`, `amcd = 1.0000`, `ass_total = 0.0`
- `pairwise_visible`: `ordinary_auroc = 0.8827`, `amcd = 0.9286`, `ass_total = 0.0215`

Local prompt judge on the auditable-generated slice:

- Visible: `ordinary_auroc = 0.5`, `amcd = 0.0714`, `ass_total = 12.8571`
- Masked: `ordinary_auroc = 0.5`, `amcd = 0.0`, `ass_total = 0.0`

Notes:

- Ordinary accuracy is `0.5` for all trained heads on this OOD slice, so AUROC and `AMCD` are the informative metrics here; the fixed `0.5` threshold does not transfer cleanly.
- The prompt judge mostly saturates on the algebra-heavy subset and remains unusable as a local verifier even after we give it audited model-generated counterfactuals.

Interpretation:

- This is the first result on genuinely model-generated traces that supports `AMCD`, not only deployment-style `ASS`.
- On the auditable subset, the trained masked head remains the strongest process verifier and stays perfectly answer-invariant (`AMCD = 1.0`, `ASS_total = 0.0`).
- The visible trained head is also strong, but still slightly more answer-sensitive than the masked head.
- The main bottleneck is now coverage, not just scoring: free-form model-generated traces collapse hardest in blocksworld, where none of the six originals survive a deterministic executability gate.
- This means the proposal's natural-transfer story now has a sharper failure mode: before repair, we may need targeted regeneration or structure constraints to obtain enough auditable planning traces.

Failure note:

- A rerun of `scripts/run_api_judge_pilot.py` on this slice was attempted, but the current shell was missing `ARK_BASE_URL`, `ARK_MODEL_ENDPOINT`, and `ARK_API_KEY`, so no external-judge result was produced for this stage.

## 2026-03-09 Targeted Regeneration For Natural Model-Generated Coverage

Status: targeted constrained regeneration completed for graph/path, with an explicit failure summary for blocksworld.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py \
  --domains graph_path \
  --require-auditable-original \
  --max-retries 4 \
  --output data/generated/craft_core_hard_model_generated_graph_v1.jsonl \
  --summary-output artifacts/generated/model_generated_graph_v1_summary.json \
  --cache-output artifacts/generated/model_generated_graph_v1_rows.jsonl \
  --attempt-log-output artifacts/generated/model_generated_graph_v1_attempts.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_counterfactual_slice.py \
  --source-dataset data/generated/craft_core_hard_model_generated_graph_v1.jsonl \
  --output data/generated/craft_core_hard_model_generated_graph_counterfactual_v1.jsonl \
  --summary-output artifacts/generated/model_generated_graph_counterfactual_v1_summary.json \
  --rejections-output artifacts/generated/model_generated_graph_counterfactual_v1_rejections.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python scripts/merge_generated_eval_slices.py \
  --base-dataset data/generated/craft_core_hard_model_generated_counterfactual.jsonl \
  --keep-domains algebra \
  --append-dataset data/generated/craft_core_hard_model_generated_graph_counterfactual_v1.jsonl \
  --output data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --summary-output artifacts/generated/model_generated_hybrid_counterfactual_v1_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_natural_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --output artifacts/generated/model_generated_hybrid_counterfactual_v1_transfer.json \
  --feature-cache-dir artifacts/generated/hybrid_counterfactual_features_v1'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --max-quartets 12 \
  --output artifacts/generated/model_generated_hybrid_counterfactual_v1_qwen.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py \
  --domains blocksworld \
  --require-auditable-original \
  --max-retries 3 \
  --output data/generated/craft_core_hard_model_generated_blocksworld_v1.jsonl \
  --summary-output artifacts/generated/model_generated_blocksworld_v1_summary.json \
  --cache-output artifacts/generated/model_generated_blocksworld_v1_rows.jsonl \
  --attempt-log-output artifacts/generated/model_generated_blocksworld_v1_attempts.jsonl'
```

Artifacts:

- `artifacts/generated/model_generated_graph_v1_summary.json`
- `artifacts/generated/model_generated_graph_counterfactual_v1_summary.json`
- `artifacts/generated/model_generated_hybrid_counterfactual_v1_summary.json`
- `artifacts/generated/model_generated_hybrid_counterfactual_v1_transfer.json`
- `artifacts/generated/model_generated_hybrid_counterfactual_v1_qwen.json`
- `artifacts/generated/model_generated_blocksworld_v1_summary.json`

Graph/path targeted regeneration:

- Accepted swap groups: `5/6`
- Generation attempts: `14`
- Failed swap groups: `1`
- Failure reasons during attempts: `incorrect_original_answer = 3`, `missing_correct_path_conclusion = 2`
- Counterfactual-builder coverage after filtering: `5/5` accepted graph anchors (`20` counterfactual traces)

Blocksworld targeted regeneration:

- Accepted swap groups: `0/6`
- Generation attempts: `18`
- Final failed reasons by group: `illegal_multi_move_transition` for `2` groups, `noop_or_repeated_state` for `4` groups

Hybrid auditable-generated evaluation slice:

- Composition: algebra `24` traces + graph_path `20` traces
- Total: `44` traces across `11` quartets
- This replaces the previous one-graph algebra-heavy slice with a substantially richer algebra+graph slice while leaving blocksworld explicitly unresolved.

Synthetic-train to hybrid auditable-generated-test frozen-backbone transfer:

- `step_only_bce`: `ordinary_auroc = 0.6446`, `amcd = 0.8182`, `ass_total = 0.0`
- `visible_bce`: `ordinary_auroc = 0.7634`, `amcd = 0.9545`, `ass_total = 0.0133`
- `masked_bce`: `ordinary_auroc = 0.7851`, `amcd = 1.0000`, `ass_total = 0.0`
- `pairwise_visible`: `ordinary_auroc = 0.7521`, `amcd = 0.9545`, `ass_total = 0.0205`

Local prompt judge on the hybrid slice:

- Visible: `ordinary_auroc = 0.5269`, `amcd = 0.1818`, `ass_total = 12.2727`
- Masked: `ordinary_auroc = 0.5909`, `amcd = 0.1818`, `ass_total = 0.0`

External API judge on the hybrid slice:

- Visible: `ordinary_auroc = 0.6818`, `amcd = 0.3636`, `ass_total = 36.3636`
- Masked: `ordinary_auroc = 0.8864`, `amcd = 0.7727`, `ass_total = 4.5455`
- Usage: `23840` total tokens across `88` API calls
- Artifact: `artifacts/generated/model_generated_hybrid_counterfactual_v1_api_summary.json`

Interpretation:

- The constrained regeneration path materially improves natural model-generated coverage for graph/path: graph anchors rise from `1` in the previous auditable slice to `5` here.
- The same strategy does not rescue blocksworld: even with exact-state constraints and retrying, the local `Qwen3-1.7B` generator remains unable to produce auditable planning traces on this slice.
- On the richer algebra+graph hybrid slice, the trained masked baseline still remains the strongest and most answer-invariant verifier (`AMCD = 1.0`, `ASS_total = 0.0`).
- The visible trained baseline stays strong, but the new graph coverage makes the task noticeably harder than the earlier algebra-heavy slice: visible `ordinary_auroc` falls from `0.8367` to `0.7634`, while `AMCD` remains high.
- The prompt judge improves slightly once graph is no longer underrepresented, but it is still qualitatively weak on process discrimination and far below the trained heads.
- The external closed judge now fits the same broad pattern as the prompt judge rather than the trained head: masking helps a lot, but even masked it remains less process-faithful than the trained masked baseline on the same slice.

Engineering note:

- Allowing hidden reasoning during generation consumed the token budget inside `<think>` and degraded auditable output quality. The targeted regeneration runs therefore reverted to `/no_think` plus stronger surface-structure constraints.

## 2026-03-10 Scaffolded Blocksworld Recovery And Full Hybrid Re-evaluation

Status: blocksworld natural coverage recovered with a stronger stepwise scaffold; full tri-domain hybrid generated slice completed.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_slice.py \
  --domains blocksworld \
  --require-auditable-original \
  --use-blocksworld-scaffold \
  --max-retries 4 \
  --output data/generated/craft_core_hard_model_generated_blocksworld_v2.jsonl \
  --summary-output artifacts/generated/model_generated_blocksworld_v2_summary.json \
  --cache-output artifacts/generated/model_generated_blocksworld_v2_rows.jsonl \
  --attempt-log-output artifacts/generated/model_generated_blocksworld_v2_attempts.jsonl'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_model_generated_counterfactual_slice.py \
  --source-dataset data/generated/craft_core_hard_model_generated_blocksworld_v2.jsonl \
  --output data/generated/craft_core_hard_model_generated_blocksworld_counterfactual_v2.jsonl \
  --summary-output artifacts/generated/model_generated_blocksworld_counterfactual_v2_summary.json \
  --rejections-output artifacts/generated/model_generated_blocksworld_counterfactual_v2_rejections.jsonl'
```

```bash
bash -lc 'python scripts/merge_generated_eval_slices.py \
  --base-dataset data/generated/craft_core_hard_model_generated_hybrid_counterfactual_v1.jsonl \
  --append-dataset data/generated/craft_core_hard_model_generated_blocksworld_counterfactual_v2.jsonl \
  --output data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --summary-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_natural_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_transfer.json \
  --feature-cache-dir artifacts/generated/full_hybrid_counterfactual_features_v2'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_qwen_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --max-quartets 20 \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_qwen.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/run_api_judge_pilot.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --max-quartets 20 \
  --cache-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_api_rows.jsonl \
  --summary-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_api_summary.json'
```

Artifacts:

- `artifacts/generated/model_generated_blocksworld_v2_summary.json`
- `artifacts/generated/model_generated_blocksworld_counterfactual_v2_summary.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_summary.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_transfer.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_qwen.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_api_summary.json`

Blocksworld scaffold recovery:

- Prompt-only targeted generation had `0/6` accepted swap groups.
- Stepwise scaffolded generation now reaches `6/6` accepted swap groups with `6` attempts total.
- Counterfactual-builder coverage on the scaffolded blocksworld slice is also `6/6` accepted anchors (`24` counterfactual traces).

Full hybrid generated counterfactual slice:

- Total: `68` traces across `17` quartets
- Domains: algebra `24`, graph_path `20`, blocksworld `24`

Synthetic-train to full-hybrid auditable-generated-test frozen-backbone transfer:

- `step_only_bce`: `ordinary_auroc = 0.5675`, `amcd = 0.5294`, `ass_total = 0.0`
- `visible_bce`: `ordinary_auroc = 0.6103`, `amcd = 0.7941`, `ass_total = 0.0529`
- `masked_bce`: `ordinary_auroc = 0.6194`, `amcd = 0.7647`, `ass_total = 0.0`
- `pairwise_visible`: `ordinary_auroc = 0.6298`, `amcd = 0.6176`, `ass_total = 0.0402`

Per-domain note for trained heads:

- `visible_bce` blocksworld: `ordinary_auroc = 0.4375`
- `masked_bce` blocksworld: `ordinary_auroc = 0.4167`
- The blocksworld slice is now clearly the hardest domain in the full hybrid OOD setting.

Local prompt judge on the full hybrid slice:

- Visible: `ordinary_auroc = 0.5164`, `amcd = 0.1176`, `ass_total = 7.9412`
- Masked: `ordinary_auroc = 0.5588`, `amcd = 0.1176`, `ass_total = 0.0`

External API judge on the full hybrid slice:

- Visible: `ordinary_auroc = 0.6765`, `amcd = 0.3529`, `ass_total = 58.8235`
- Masked: `ordinary_auroc = 0.7794`, `amcd = 0.5588`, `ass_total = 2.9412`
- Usage: `33496` total tokens across `136` API calls

Interpretation:

- The stronger stepwise scaffold removes the earlier coverage blocker: we now have an auditable generated slice covering all three domains.
- This changes the scientific picture in an important but still proposal-consistent way: once blocksworld is included, all trained heads get materially worse on OOD generated data, so the task is no longer dominated by algebra/graph.
- Even on this harder full-hybrid slice, the trained masked baseline still keeps zero answer sensitivity, while the visible trained head keeps only modest `ASS_total`.
- The external closed judge again behaves more like a judge-style evaluator than like the trained verifier: visible judging is extremely answer-sensitive (`ASS_total = 58.8235`), and masking helps sharply, but masked external judging still trails the trained masked head on `AMCD`.
- The gap between trained visible and trained masked heads is narrower here than on easier slices; the main new effect of adding blocksworld is reduced process discrimination for everyone, not a dramatic spike in trained answer sensitivity.

Method note:

- The blocksworld recovery used a stronger scaffold than prompt-only generation: at each step the model chose among legality-checked next states that also reduced distance to the goal, then generated a sentence for the chosen move. This preserves model-generated surface text while making executability auditable.

## 2026-03-10 Week 3 Minimal Repair Pilot On The Full Generated Hybrid Slice

Status: the first repair pilot is now implemented and evaluated on the full tri-domain generated counterfactual slice.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json \
  --feature-cache-dir artifacts/generated/full_hybrid_repair_features_v1'
```

Artifacts:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json`

Reference baselines on the same full-hybrid OOD slice:

- `visible_bce`: `ordinary_auroc = 0.6103`, `amcd = 0.7941`, `ass_total = 0.0529`
- `masked_bce`: `ordinary_auroc = 0.6194`, `amcd = 0.7647`, `ass_total = 0.0`
- `pairwise_visible`: `ordinary_auroc = 0.6298`, `amcd = 0.6176`, `ass_total = 0.0402`

Minimal repair variants:

- `visible_local_pair` selected `lambda_local_pair = 0.1`, `lambda_cond_swap = 0.0`
  - OOD metrics: `ordinary_auroc = 0.5735`, `amcd = 0.7647`, `ass_total = 0.0061`
- `visible_cond_swap` selected `lambda_local_pair = 0.0`, `lambda_cond_swap = 2.0`
  - OOD metrics: `ordinary_auroc = 0.5787`, `amcd = 0.9706`, `ass_total = 0.0056`
- `visible_joint_repair` selected `lambda_local_pair = 1.0`, `lambda_cond_swap = 2.0`
  - OOD metrics: `ordinary_auroc = 0.5649`, `amcd = 0.8235`, `ass_total = 0.009`

Validation-selection note:

- `visible_joint_repair` was actually the strongest synthetic validation model under the repair selection rule:
  - `ordinary_auroc = 0.9344`, `amcd = 1.0`, `ass_total = 0.0166`
- But it did not transfer best to the full generated OOD slice.

Per-domain OOD note:

- `visible_bce` blocksworld: `ordinary_auroc = 0.4375`
- `masked_bce` blocksworld: `ordinary_auroc = 0.4167`
- `visible_local_pair` blocksworld: `ordinary_auroc = 0.7083`
- `visible_cond_swap` blocksworld: `ordinary_auroc = 0.6736`
- `visible_joint_repair` blocksworld: `ordinary_auroc = 0.5`

Interpretation:

- This is the first run where a repair objective clearly helps the proposal's target stress metric on the hardest current OOD slice.
- The cleanest win comes from `cond-swap` alone: it raises `AMCD` from `0.7941` (`visible_bce`) and `0.7647` (`masked_bce`) to `0.9706`, while keeping `ASS_total` near zero (`0.0056`).
- The price of that gain is lower ordinary global separability: `ordinary_auroc` drops from `0.6103` / `0.6194` to `0.5787`.
- `local-pair` alone mainly helps blocksworld and answer invariance, but does not improve aggregate `AMCD` beyond the visible baseline.
- The joint objective currently looks like a validation overfit pattern: it wins on synthetic validation but loses to pure `cond-swap` on full generated OOD transfer.
- The research picture has shifted: repair is no longer purely hypothetical. A minimal repair term can help on the proposal's hardest current audit slice, but the gain is targeted rather than free and still trades against global ordinary AUROC.

## 2026-03-10 Naturalized Full-Hybrid Repair Robustness Check

Status: tested whether the new repair gain survives a lighter natural-language shift on the full generated hybrid slice.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_naturalized_slice.py \
  --source-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --use-all-records \
  --output data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --summary-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_summary.json \
  --cache-output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_rows.jsonl \
  --max-retries 0'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair.json \
  --feature-cache-dir artifacts/generated/full_hybrid_counterfactual_natural_repair_features_v1'
```

Artifacts:

- `data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_summary.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair.json`

Naturalization composition:

- Total records: `68`
- Naturalizer mix: `24` local Qwen rewrites, `44` heuristic fallbacks
- `step_rewrites_changed = 44`
- `problem_rewrites_changed = 12`

OOD transfer on the naturalized full-hybrid slice:

- `visible_bce`: `ordinary_auroc = 0.6064`, `amcd = 0.7353`, `ass_total = 0.1083`
- `masked_bce`: `ordinary_auroc = 0.5978`, `amcd = 0.7647`, `ass_total = 0.1159`
- `pairwise_visible`: `ordinary_auroc = 0.5744`, `amcd = 0.7941`, `ass_total = 0.0636`
- `visible_local_pair`: `ordinary_auroc = 0.5311`, `amcd = 0.6765`, `ass_total = 0.0067`
- `visible_cond_swap`: `ordinary_auroc = 0.5407`, `amcd = 0.6765`, `ass_total = 0.007`
- `visible_joint_repair`: `ordinary_auroc = 0.5631`, `amcd = 0.7941`, `ass_total = 0.1307`

Interpretation:

- The previous `cond-swap` win does not survive this lighter natural-language shift as an `AMCD` win.
- What *does* survive is answer invariance: `visible_cond_swap` still keeps `ASS_total` near zero (`0.007`), while both visible and masked BCE baselines rise above `0.10`.
- Under this shift, the picture looks more like a Pareto frontier:
  - lower `ASS_total`: `visible_cond_swap`, but with lower `AMCD`
  - higher `AMCD`: `pairwise_visible` and `visible_joint_repair`, but with materially higher `ASS_total`
- The masked baseline is no longer near-invariant once the generated slice is naturalized: `ASS_total` rises from `0.0` on the structured full hybrid to `0.1159` here.
- This is the strongest evidence so far that a light surface shift can expose residual answer sensitivity even in trained frozen-backbone heads.
- The repair story is therefore more precise than one round ago:
  - `cond-swap` helps on the hardest structured generated slice
  - but on the naturalized version it mainly improves faithfulness (`ASS_total`) rather than process discrimination (`AMCD`)

## 2026-03-10 Hard-Neg Replay On The Naturalized Full-Hybrid Slice

Status: added the proposal's `+ hard-neg` branch and tested whether it can recover naturalized-slice `AMCD` without giving back the low-`ASS_total` advantage from `cond-swap`.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_hardneg.json \
  --feature-cache-dir artifacts/generated/full_hybrid_counterfactual_natural_repair_features_v1'
```

Artifact:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_hardneg.json`

Hard-negative mining summary:

- Mining source: visible BCE teacher on the synthetic hard training split
- Rule: select the top `25%` invalid traces by teacher score, with `min_count = 8`
- Selected hard negatives: `36 / 144` invalid training traces
- Domain mix: graph_path `20`, algebra `14`, blocksworld `2`
- Selected score range: `0.0778` to `0.5864`

Naturalized full-hybrid OOD results:

- `visible_bce`: `ordinary_auroc = 0.6064`, `amcd = 0.7353`, `ass_total = 0.1083`
- `masked_bce`: `ordinary_auroc = 0.5978`, `amcd = 0.7647`, `ass_total = 0.1159`
- `pairwise_visible`: `ordinary_auroc = 0.5744`, `amcd = 0.7941`, `ass_total = 0.0636`
- `visible_cond_swap`: `ordinary_auroc = 0.5407`, `amcd = 0.6765`, `ass_total = 0.007`
- `visible_hard_neg`: `ordinary_auroc = 0.5043`, `amcd = 0.6471`, `ass_total = 0.0291`
- `visible_cond_swap_hard_neg`: `ordinary_auroc = 0.6021`, `amcd = 0.7941`, `ass_total = 0.128`

Best hyperparameters chosen by synthetic validation:

- `visible_hard_neg`: `lambda_hard_neg = 1.0`
- `visible_cond_swap_hard_neg`: `lambda_cond_swap = 2.0`, `lambda_hard_neg = 2.0`

Interpretation:

- `hard-neg` alone does not help. It underperforms both visible and masked BCE on the naturalized slice.
- `cond-swap + hard-neg` does recover the lost OOD discrimination: `AMCD` returns to `0.7941`, matching `pairwise_visible`, and `ordinary_auroc` rises back to `0.6021`.
- But that recovery comes with a clear cost in faithfulness: `ASS_total` jumps from `0.007` under pure `cond-swap` to `0.128` under `cond-swap + hard-neg`.
- So this branch does not solve the current problem. It moves the frontier toward utility and away from invariance, rather than improving both at once.
- The mining profile helps explain part of the behavior: the self-mined hard negatives are dominated by graph and algebra, with only `2` blocksworld examples, so replay is not targeting the hardest planning slice evenly.
- The current Week 3 picture is now sharper:
  - `cond-swap` is the best faithfulness-oriented repair
  - `cond-swap + hard-neg` is a utility-recovery variant that gives back too much answer sensitivity
  - no simple variant yet dominates the naturalized frontier on both `AMCD` and `ASS_total`

## 2026-03-10 Targeted Hard-Neg Mining Ablation

Status: tested whether the previous hard-neg failure was mainly a mining-skew artifact by replacing global replay mining with domain-balanced and blocksworld-focused variants.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_repair_transfer.py \
  --eval-dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json \
  --feature-cache-dir artifacts/generated/full_hybrid_counterfactual_natural_repair_features_v1'
```

Artifact:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json`

Mining profiles:

- `global`: `36` traces, domain mix graph_path `20`, algebra `14`, blocksworld `2`
- `domain_balanced`: `36` traces, domain mix algebra `12`, blocksworld `12`, graph_path `12`
- `blocksworld_focus`: `36` traces, domain mix blocksworld `18`, algebra `9`, graph_path `9`

Naturalized full-hybrid OOD results for targeted replay:

- `visible_cond_swap`: `ordinary_auroc = 0.5407`, `amcd = 0.6765`, `ass_total = 0.007`
- `visible_cond_swap_hard_neg` (global mining): `ordinary_auroc = 0.6021`, `amcd = 0.7941`, `ass_total = 0.128`
- `visible_cond_swap_hard_neg_balanced`: `ordinary_auroc = 0.5260`, `amcd = 0.6765`, `ass_total = 0.0046`
- `visible_cond_swap_hard_neg_blocksworld_focus`: `ordinary_auroc = 0.5519`, `amcd = 0.7353`, `ass_total = 0.1288`

Selected hyperparameters:

- `visible_cond_swap_hard_neg_balanced`: `lambda_cond_swap = 2.0`, `lambda_hard_neg = 0.1`
- `visible_cond_swap_hard_neg_blocksworld_focus`: `lambda_cond_swap = 2.0`, `lambda_hard_neg = 0.5`

Interpretation:

- The previous hard-neg result was not just a trivial mining-skew bug.
- `domain_balanced` replay preserves the low-`ASS_total` behavior (`0.0046`) but does not recover the lost OOD `AMCD`; it stays at `0.6765`, effectively matching pure `cond-swap`.
- `blocksworld_focus` replay still fails to break the frontier. It only recovers `AMCD` to `0.7353`, below the global replay result, while `ASS_total` rises to `0.1288`.
- So the current evidence points to a stronger conclusion:
  - the trade-off is not removed by simply fixing domain coverage in the replay pool
  - targeted replay changes *where* the trade-off lands, but it does not make a simple `hard-neg` variant dominate both faithfulness and utility
- This strengthens the proposal-consistent interpretation that Week 3 currently exposes a real frontier, not just a poor mining choice.

## 2026-03-10 Answer-Swap Intervention And Mediation Analysis

Status: implemented the proposal's mechanism-analysis step on top of saved full-hybrid results, using answer-swap intervention summaries plus quartet-level utility proxies.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_mechanism_analysis.py \
  --output artifacts/generated/mechanism_analysis_full_hybrid.json'
```

Artifact:

- `artifacts/generated/mechanism_analysis_full_hybrid.json`

Utility definitions used here:

- `selection_gain_at4`: top-1 selection accuracy over the four-trace quartet, minus the random baseline `0.5`
- `exploitability_rate`: rate that the top-scored trace is `invalid_correct` (lucky answer, wrong process)

Runs included:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json`
- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json`

Head-level pooled correlations across both runs (`n = 16` heads):

- `corr(AMCD, selection_gain_at4) = 0.8778`
- `corr(AMCD, exploitability_rate) = -0.7724`
- `corr(ordinary_auroc, selection_gain_at4) = 0.4659`
- `corr(ordinary_auroc, exploitability_rate) = -0.0104`

Interpretation of the pooled head-level view:

- `AMCD` tracks downstream utility much better than ordinary AUROC on the current full-hybrid studies.
- The head-level `ASS_total` relation is muddied by the current frontier: some methods buy utility by accepting higher answer sensitivity, while others buy faithfulness by giving up utility.

Quartet-level pooled intervention and mediation across all head x run x quartet samples (`n = 272`):

- `corr(local_ASS, local_AMCD) = -0.2851`
- `corr(local_ASS, selection_gain_at4) = -0.2758`
- `corr(local_ASS, exploitability_rate) = 0.2726`
- `corr(local_AMCD, selection_gain_at4) = 0.8475`
- `corr(local_AMCD, exploitability_rate) = -0.6662`

Quartet-level mediation estimates:

- For `selection_gain_at4`
  - total effect of local `ASS`: `-0.9893`
  - indirect effect through local `AMCD`: `-0.8559`
  - direct effect after conditioning on local `AMCD`: `-0.1335`
- For `exploitability_rate`
  - total effect of local `ASS`: `0.8614`
  - indirect effect through local `AMCD`: `0.5770`
  - direct effect after conditioning on local `AMCD`: `0.2844`

Representative intervention examples:

- Structured full-hybrid `visible_cond_swap`
  - `AMCD = 0.9706`, `ASS_total = 0.0056`, `selection_gain_at4 = 0.5`, `exploitability_rate = 0.0`
- Naturalized full-hybrid `visible_cond_swap`
  - `AMCD = 0.6765`, `ASS_total = 0.007`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.1765`
- Naturalized full-hybrid `visible_cond_swap_hard_neg`
  - `AMCD = 0.7941`, `ASS_total = 0.128`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1176`

Answer-swap intervention split by process variant:

- Naturalized `visible_bce`: `ass_valid_pair = 0.1688`, `ass_invalid_pair = 0.0478`
- Naturalized `masked_bce`: `ass_valid_pair = 0.1271`, `ass_invalid_pair = 0.1047`
- Naturalized `visible_cond_swap`: `ass_valid_pair = 0.0076`, `ass_invalid_pair = 0.0065`
- Naturalized `visible_cond_swap_hard_neg`: `ass_valid_pair = 0.1123`, `ass_invalid_pair = 0.1437`

Interpretation:

- This is the strongest support so far for the proposal's mechanism claim short of a hidden-state probe.
- At the local quartet level, higher answer-swap sensitivity predicts lower local `AMCD`, lower selection gain, and higher exploitability.
- Most of the local effect of answer sensitivity on utility is mediated through `AMCD`, not through a large residual direct path.
- This also clarifies the current frontier:
  - head-level trade-offs can obscure the direction of `ASS_total`
  - but locally, once answer sensitivity rises, process discrimination and safe selection both degrade
- So even though no simple Week 3 variant dominates the full frontier, the `ASS -> AMCD -> utility` chain is now empirically supported on the current audited OOD setup.

## 2026-03-10 Minimal Dual-Head Disentangled Pilot

Status: implemented the proposal's minimal `dual-head disentangled` variant and tested whether explicit separation of process and consistency heads can compress the naturalized OOD frontier.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_dual_head_transfer.py \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_dual_head.json'
```

Artifact:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_dual_head.json`

Dual-head setup:

- `G_proc`: visible process head trained with `cond-swap`
- `G_cons`: visible answer-correctness BCE head
- `G_total = G_proc + alpha * G_cons`
- Validation search over:
  - `lambda_cond_swap in {0.1, 0.25, 0.5, 1.0, 2.0}`
  - `alpha in {0.0, 0.1, 0.25, 0.5, 1.0, 2.0}`

Selected hyperparameters:

- `lambda_cond_swap = 2.0`
- `alpha = 0.0`

Consistency-head quality:

- Validation answer AUROC: `0.6389`
- Naturalized eval answer AUROC: `0.5779`

Naturalized full-hybrid OOD result:

- `G_proc` metrics:
  - `ordinary_auroc = 0.5407`
  - `amcd = 0.6765`
  - `ass_total = 0.007`
- `G_total` metrics:
  - identical to `G_proc`, because the selected `alpha` is `0.0`
- utility from `G_total`:
  - `selection_gain_at4 = 0.2059`
  - `exploitability_rate = 0.1765`

Interpretation:

- In the current minimal frozen-backbone implementation, the dual-head pilot does **not** compress the frontier.
- The validation search explicitly refuses to use the consistency head: the best setting is `alpha = 0.0`, which collapses the method back to pure `cond-swap`.
- This is informative rather than empty:
  - explicit factorization alone is not enough at this scale
  - the current consistency head is too weak or too noisy to improve downstream selection without damaging the process head
- So the Week 3 algorithm story remains the same:
  - `cond-swap` is still the best faithfulness-oriented simple method
  - no simple variant, including the current minimal dual-head, dominates the naturalized OOD frontier

## 2026-03-10 Step-Scan Dual-Head Disentangled Pilot

Status: tested a more faithful dual-head implementation in which `G_proc` is no longer a full-trace head. Instead, it is a local step-only process head applied to every step and aggregated at deployment time.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_scanned_dual_head_transfer.py \
  --output artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_scanned_dual_head.json'
```

Artifact:

- `artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_scanned_dual_head.json`

Step-scan dual-head setup:

- `G_proc`: step-only local head trained on audited loci
- deployment-time: scan every step in the trace and aggregate the local logits into `G_proc`
- searched process variants:
  - `lambda_local_pair in {0.0, 0.1, 0.25, 0.5, 1.0}`
  - aggregation in `{softmin, mean}`
- `G_cons`: visible answer-correctness BCE head
- `G_total = G_proc + alpha * G_cons`
- `alpha in {0.0, 0.1, 0.25, 0.5, 1.0, 2.0}`

Selected hyperparameters:

- `lambda_local_pair = 1.0`
- `aggregation = mean`
- `alpha = 0.0`

Consistency-head quality:

- Validation answer AUROC: `0.6389`
- Naturalized eval answer AUROC: `0.5779`

Naturalized full-hybrid OOD result:

- `G_proc` metrics:
  - `ordinary_auroc = 0.5216`
  - `amcd = 0.6471`
  - `ass_total = 0.0033`
- `G_total` metrics:
  - identical to `G_proc`, because `alpha = 0.0`
- utility from `G_total`:
  - `selection_gain_at4 = 0.0882`
  - `exploitability_rate = 0.2353`

Interpretation:

- This stronger, more proposal-faithful dual-head variant still does not use the consistency channel at optimum.
- The result is actually stronger evidence than the previous minimal dual-head:
  - even when `G_proc` is implemented as a real step-scan local signal, validation still sets `alpha = 0.0`
  - so the consistency head is not merely unused because the previous implementation was too entangled
- Compared with pure `visible_cond_swap`, the step-scan dual-head buys slightly lower answer sensitivity (`0.0033` vs `0.007`) but gives up too much utility and `AMCD`.
- The current interpretation is therefore robust:
  - the Week 3 mechanism chain holds
  - but neither minimal dual-head nor step-scan dual-head compresses the naturalized OOD frontier at the current model/data scale

## 2026-03-10 Week 4 Qwen3 Reranker Pilot

Status: moved beyond frozen-backbone linear heads and evaluated local `Qwen3-Reranker` checkpoints on the full-hybrid generated OOD slice for reranking, exploitability, and calibration.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_full_hybrid_structured.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_full_hybrid_natural.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-4B \
  --output artifacts/week4/qwen3_reranker_4b_full_hybrid_natural.json'
```

Artifacts:

- `artifacts/week4/qwen3_reranker_8b_full_hybrid_structured.json`
- `artifacts/week4/qwen3_reranker_8b_full_hybrid_natural.json`
- `artifacts/week4/qwen3_reranker_4b_full_hybrid_natural.json`

Week 4 scoring setup:

- Model family: local `Qwen3-Reranker` checkpoints
- Main model: `Qwen3-Reranker-8B`
- Comparison model: `Qwen3-Reranker-4B`
- Input format: official Qwen reranker yes/no scoring interface
- Query: problem text plus audited step index
- Document: full visible or masked trace
- Instruction: rank valid local reasoning above invalid reasoning even when the final answer is accidentally correct

`Qwen3-Reranker-8B` on the structured full-hybrid slice:

- Visible:
  - `ordinary_auroc = 0.5225`
  - `amcd = 0.3235`
  - `ass_total = 0.2252`
  - `selection_gain_at4 = 0.3235`
  - `exploitability_rate = 0.1765`
  - `ece = 0.4297`
  - `brier = 0.4153`
  - `aurc = 0.429`
- Masked:
  - `ordinary_auroc = 0.7059`
  - `amcd = 0.8235`
  - `ass_total = 0.0`
  - `selection_gain_at4 = 0.5`
  - `exploitability_rate = 0.0`
  - `ece = 0.4298`
  - `brier = 0.4003`
  - `aurc = 0.3694`

`Qwen3-Reranker-8B` on the naturalized full-hybrid slice:

- Visible:
  - `ordinary_auroc = 0.5398`
  - `amcd = 0.5294`
  - `ass_total = 0.2128`
  - `selection_gain_at4 = 0.3235`
  - `exploitability_rate = 0.1765`
  - `ece = 0.432`
  - `brier = 0.4115`
  - `aurc = 0.4508`
- Masked:
  - `ordinary_auroc = 0.6795`
  - `amcd = 0.8529`
  - `ass_total = 0.0184`
  - `selection_gain_at4 = 0.3824`
  - `exploitability_rate = 0.0588`
  - `ece = 0.4195`
  - `brier = 0.3899`
  - `aurc = 0.3775`

`Qwen3-Reranker-4B` on the naturalized full-hybrid slice:

- Visible:
  - `ordinary_auroc = 0.5458`
  - `amcd = 0.4706`
  - `ass_total = 0.1597`
  - `selection_gain_at4 = 0.2059`
  - `exploitability_rate = 0.1765`
  - `ece = 0.4235`
  - `brier = 0.423`
  - `aurc = 0.3994`
- Masked:
  - `ordinary_auroc = 0.686`
  - `amcd = 0.7059`
  - `ass_total = 0.0162`
  - `selection_gain_at4 = 0.2647`
  - `exploitability_rate = 0.1176`
  - `ece = 0.4534`
  - `brier = 0.4476`
  - `aurc = 0.3119`

Comparison against the current frozen-head naturalized baselines:

- `visible_bce`: `amcd = 0.7353`, `ass_total = 0.1083`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1176`
- `masked_bce`: `amcd = 0.7647`, `ass_total = 0.1159`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1176`
- `visible_cond_swap`: `amcd = 0.6765`, `ass_total = 0.007`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.1765`

Interpretation:

- Scaling up to a dedicated reranker does **not** make answer-visible scoring safe by default.
- On both the structured and naturalized full-hybrid slices, `Qwen3-Reranker-8B` is much stronger in the masked condition than in the visible condition:
  - higher `AMCD`
  - lower `ASS_total`
  - higher `selection_gain_at4`
  - lower `exploitability_rate`
- The same qualitative pattern already appears at `4B`, so this is not an `8B` one-off.
- The strongest Week 4 model so far is `Qwen3-Reranker-8B` **masked** on the naturalized slice:
  - `amcd = 0.8529`
  - `selection_gain_at4 = 0.3824`
  - `exploitability_rate = 0.0588`
  - `ass_total = 0.0184`
- That naturalized `8B` masked reranker improves downstream utility over every current frozen-head baseline on the same slice, while staying far less answer-sensitive than the visible reranker.
- Calibration does **not** improve nearly as much as ranking utility:
  - even the best masked reranker still has `ece = 0.4195`
  - so Week 4 currently strengthens the reranking / exploitability story more than the probability-calibration story
- The resulting scientific picture is now sharper:
  - stronger model scale helps
  - but it helps most when the verifier is denied direct answer access
  - so the proposal's disentangling / masking concern survives into Week 4 rather than disappearing at larger scale

## 2026-03-10 Week 5 Robustness And Multi-Attacker Transfer

Status: completed the first Week 5 robustness pass around the current strongest Week 4 model (`Qwen3-Reranker-8B`), including held-out synthetic vs generated transfer, multi-attacker transfer, and worst-group slices.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_hard.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week5/qwen3_reranker_8b_hard.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week5_robustness.py \
  --output artifacts/week5/week5_robustness.json'
```

Artifacts:

- `artifacts/week5/qwen3_reranker_8b_hard.json`
- `artifacts/week5/week5_robustness.json`

### Held-Out / Natural Transfer Summary

`Qwen3-Reranker-8B` visible:

- hard synthetic:
  - `ordinary_auroc = 0.6419`
  - `amcd = 0.6667`
  - `ass_total = 0.2268`
  - `selection_gain_at4 = 0.2778`
  - `exploitability_rate = 0.1667`
- structured generated:
  - `ordinary_auroc = 0.5225`
  - `amcd = 0.3235`
  - `ass_total = 0.2252`
  - `selection_gain_at4 = 0.3235`
  - `exploitability_rate = 0.1765`
- naturalized generated:
  - `ordinary_auroc = 0.5398`
  - `amcd = 0.5294`
  - `ass_total = 0.2128`
  - `selection_gain_at4 = 0.3235`
  - `exploitability_rate = 0.1765`

`Qwen3-Reranker-8B` masked:

- hard synthetic:
  - `ordinary_auroc = 0.691`
  - `amcd = 0.7546`
  - `ass_total = 0.0197`
  - `selection_gain_at4 = 0.25`
  - `exploitability_rate = 0.25`
- structured generated:
  - `ordinary_auroc = 0.7059`
  - `amcd = 0.8235`
  - `ass_total = 0.0`
  - `selection_gain_at4 = 0.5`
  - `exploitability_rate = 0.0`
- naturalized generated:
  - `ordinary_auroc = 0.6795`
  - `amcd = 0.8529`
  - `ass_total = 0.0184`
  - `selection_gain_at4 = 0.3824`
  - `exploitability_rate = 0.0588`

Interpretation:

- The Week 4 masked-over-visible advantage survives the Week 5 transfer checks.
- Visible `8B` reranking drops sharply from hard synthetic to generated OOD on `AMCD` (`0.6667 -> 0.3235/0.5294`) and remains highly answer-sensitive.
- Masked `8B` is much more stable under the same transfer:
  - it keeps near-zero `ASS_total`
  - and remains the strongest downstream model on the naturalized generated slice
- So the Week 4 result is not a one-slice fluke; the Week 5 transfer view still favors masked deployment.

### Multi-Attacker Transfer

Attacker construction on the naturalized full-hybrid slice:

- self attacker: top invalid traces from the target model itself
- another-family attackers:
  - `reranker8_visible`
  - `visible_bce`
  - `pairwise_visible`
- mixed attacker:
  - union of top invalid traces from the three visible attackers above

For the current best Week 4 target, `reranker8_masked`:

- against `visible_bce` attacker:
  - `pairwise_attack_win_rate = 0.0`
  - attacked-quartet `selection_gain_at4 = 0.5`
  - attacked-quartet `exploitability_rate = 0.0`
- against `pairwise_visible` attacker:
  - `pairwise_attack_win_rate = 0.0`
  - attacked-quartet `selection_gain_at4 = 0.5`
  - attacked-quartet `exploitability_rate = 0.0`
- against `mixed_visible_ensemble` attacker:
  - `pairwise_attack_win_rate = 0.1944`
  - `quartet_top_attack_rate = 0.1111`
  - attacked-quartet `selection_gain_at4 = 0.3333`
  - attacked-quartet `exploitability_rate = 0.0833`

For comparison, `reranker8_visible` under the same mixed attacker:

- `pairwise_attack_win_rate = 0.4722`
- `quartet_top_attack_rate = 0.1667`
- attacked-quartet `selection_gain_at4 = 0.25`
- attacked-quartet `exploitability_rate = 0.25`

And the strongest frozen faithfulness baseline, `visible_cond_swap`, under the same mixed attacker:

- `pairwise_attack_win_rate = 0.3889`
- `quartet_top_attack_rate = 0.1667`
- attacked-quartet `selection_gain_at4 = 0.0833`
- attacked-quartet `exploitability_rate = 0.25`

Interpretation:

- The masked `8B` reranker is currently the most robust model under cross-family attack transfer.
- It transfers much better than the visible `8B` reranker under both another-family attackers and the mixed attacker.
- It also dominates the current `visible_cond_swap` frozen-head repair under mixed attack transfer.
- So Week 5 strengthens the deployment claim:
  - the best current model is not just higher-utility on average
  - it is also more resistant to visible-family hard negatives when deployed in masked mode

### Worst-Group / Failure Slices

On hard synthetic, `Qwen3-Reranker-8B` visible by verbalizer family:

- `v1`: `ordinary_auroc = 0.6461`, `amcd = 0.7083`, `ass_total = 0.3645`, `selection_gain_at4 = 0.4167`, `exploitability_rate = 0.0`
- `v2`: `ordinary_auroc = 0.6427`, `amcd = 0.7222`, `ass_total = 0.1201`, `selection_gain_at4 = 0.2778`, `exploitability_rate = 0.1389`
- `v3`: `ordinary_auroc = 0.6514`, `amcd = 0.5694`, `ass_total = 0.196`, `selection_gain_at4 = 0.3056`, `exploitability_rate = 0.1667`

On hard synthetic, `Qwen3-Reranker-8B` masked by verbalizer family:

- `v1`: `ordinary_auroc = 0.7523`, `amcd = 0.75`, `ass_total = 0.0`, `selection_gain_at4 = 0.2778`, `exploitability_rate = 0.2222`
- `v2`: `ordinary_auroc = 0.6813`, `amcd = 0.7222`, `ass_total = 0.0`, `selection_gain_at4 = 0.25`, `exploitability_rate = 0.25`
- `v3`: `ordinary_auroc = 0.6699`, `amcd = 0.7917`, `ass_total = 0.0592`, `selection_gain_at4 = 0.5`, `exploitability_rate = 0.0`

Length buckets on hard synthetic:

- visible:
  - `medium`: `ordinary_auroc = 0.6083`, `amcd = 0.625`, `ass_total = 0.2055`
  - `short`: `ordinary_auroc = 0.6637`, `amcd = 0.7`, `ass_total = 0.2439`
- masked:
  - `medium`: `ordinary_auroc = 0.6415`, `amcd = 0.6875`, `ass_total = 0.0`
  - `short`: `ordinary_auroc = 0.7335`, `amcd = 0.8083`, `ass_total = 0.0355`

Naturalized generated domains:

- visible:
  - algebra: `ordinary_auroc = 0.4722`, `amcd = 0.5`, `ass_total = 0.3774`
  - blocksworld: `ordinary_auroc = 0.5625`, `amcd = 0.6667`, `ass_total = 0.0804`
  - graph_path: `ordinary_auroc = 0.515`, `amcd = 0.4`, `ass_total = 0.174`
- masked:
  - algebra: `ordinary_auroc = 0.9167`, `amcd = 1.0`, `ass_total = 0.029`
  - blocksworld: `ordinary_auroc = 0.6875`, `amcd = 0.5833`, `ass_total = 0.0075`
  - graph_path: `ordinary_auroc = 0.82`, `amcd = 1.0`, `ass_total = 0.0187`

Interpretation:

- Verbalizer robustness is materially better for the masked reranker on hard synthetic:
  - visible keeps moderate AUROC but remains answer-sensitive
  - masked keeps much lower `ASS_total` across all three verbalizer families
- The hardest naturalized domain for the masked reranker is now clearly blocksworld:
  - `amcd = 0.5833`, lower than algebra and graph_path
- The hardest naturalized domains for the visible reranker are algebra and graph_path, both with low `AMCD` and high `ASS_total`
- Difficulty buckets are degenerate on the current hard dataset (`hard` only), so the current Week 5 failure-slice report is strongest on:
  - domain
  - verbalizer family
  - length bucket
  - selected top-role distribution

Overall interpretation:

- Week 5 is directionally consistent with the proposal:
  - stronger masked scoring remains the strongest deployment configuration
  - multi-attacker transfer does not erase that advantage
  - worst-group analysis shows the remaining weak slices explicitly instead of hiding them behind averages
- The current remaining deployment weakness is planning-style naturalized blocksworld, not a collapse of the masking/disentangling story.

## 2026-03-10 Week 6 Seed Reproduction And Paired Bootstrap

Status: completed the first Week 6 reproduction pass on the main naturalized full-hybrid comparison set, with `3` frozen-head seeds and paired bootstrap confidence intervals against the current strongest reranker.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week6_reproduction.py \
  --output artifacts/week6/week6_reproduction.json'
```

Artifact:

- `artifacts/week6/week6_reproduction.json`

Main comparison set:

- `Qwen3-Reranker-8B` visible
- `Qwen3-Reranker-8B` masked
- `visible_bce`
- `masked_bce`
- `pairwise_visible`
- `visible_cond_swap`

Frozen-head seed list:

- `17`
- `23`
- `31`

Frozen-head per-seed summaries on the naturalized full-hybrid slice:

- `visible_bce`
  - seed `17`: `ordinary_auroc = 0.6073`, `amcd = 0.7353`, `ass_total = 0.106`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1176`
  - seed `23`: `ordinary_auroc = 0.5761`, `amcd = 0.7353`, `ass_total = 0.0842`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2353`
  - seed `31`: `ordinary_auroc = 0.6012`, `amcd = 0.6765`, `ass_total = 0.104`, `selection_gain_at4 = 0.2647`, `exploitability_rate = 0.2353`
- `masked_bce`
  - seed `17`: `ordinary_auroc = 0.596`, `amcd = 0.7647`, `ass_total = 0.1123`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1176`
  - seed `23`: `ordinary_auroc = 0.6029`, `amcd = 0.6765`, `ass_total = 0.1125`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2353`
  - seed `31`: `ordinary_auroc = 0.5978`, `amcd = 0.8235`, `ass_total = 0.0975`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1765`
- `pairwise_visible`
  - seed `17`: `ordinary_auroc = 0.5735`, `amcd = 0.7941`, `ass_total = 0.0646`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2353`
  - seed `23`: `ordinary_auroc = 0.5359`, `amcd = 0.5`, `ass_total = 0.1385`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1765`
  - seed `31`: `ordinary_auroc = 0.5701`, `amcd = 0.7647`, `ass_total = 0.0542`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2941`
- `visible_cond_swap`
  - seed `17`: `ordinary_auroc = 0.5424`, `amcd = 0.6765`, `ass_total = 0.0071`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2353`, selected `lambda_cond_swap = 2.0`
  - seed `23`: `ordinary_auroc = 0.5701`, `amcd = 0.6471`, `ass_total = 0.0259`, `selection_gain_at4 = 0.1471`, `exploitability_rate = 0.1765`, selected `lambda_cond_swap = 2.0`
  - seed `31`: `ordinary_auroc = 0.5865`, `amcd = 0.7059`, `ass_total = 0.0808`, `selection_gain_at4 = 0.2647`, `exploitability_rate = 0.2353`, selected `lambda_cond_swap = 2.0`

Seed-averaged comparison table:

- `visible_bce`: `ordinary_auroc = 0.5926`, `amcd = 0.7059`, `ass_total = 0.0941`, `selection_gain_at4 = 0.2647`, `exploitability_rate = 0.2353`
- `masked_bce`: `ordinary_auroc = 0.5969`, `amcd = 0.7647`, `ass_total = 0.1041`, `selection_gain_at4 = 0.2647`, `exploitability_rate = 0.1765`
- `pairwise_visible`: `ordinary_auroc = 0.5753`, `amcd = 0.7353`, `ass_total = 0.0848`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2941`
- `visible_cond_swap`: `ordinary_auroc = 0.564`, `amcd = 0.7059`, `ass_total = 0.0377`, `selection_gain_at4 = 0.2059`, `exploitability_rate = 0.2353`
- `reranker8_visible`: `ordinary_auroc = 0.5398`, `amcd = 0.5294`, `ass_total = 0.2128`, `selection_gain_at4 = 0.3235`, `exploitability_rate = 0.1765`
- `reranker8_masked`: `ordinary_auroc = 0.6795`, `amcd = 0.8529`, `ass_total = 0.0184`, `selection_gain_at4 = 0.3824`, `exploitability_rate = 0.0588`

Key paired bootstrap intervals:

`reranker8_masked` vs `reranker8_visible`

- `ordinary_auroc` diff: `+0.1397`, CI `[0.0644, 0.2608]`
- `amcd` diff: `+0.3235`, CI `[0.1818, 0.4583]`
- `ass_total` diff: `-0.1944`, CI `[-0.2485, -0.1355]`
- `selection_gain_at4` diff: `+0.0589`, CI `[0.0, 0.1111]`
- `exploitability_rate` diff: `-0.1177`, CI `[-0.2222, 0.0]`

`reranker8_masked` vs seed-averaged `visible_cond_swap`

- `ordinary_auroc` diff: `+0.1155`, CI `[0.0419, 0.2102]`
- `amcd` diff: `+0.147`, CI `[0.0454, 0.25]`
- `ass_total` diff: `-0.0193`, CI `[-0.0278, -0.0108]`
- `selection_gain_at4` diff: `+0.1765`, CI `[0.0, 0.3636]`
- `exploitability_rate` diff: `-0.1765`, CI `[-0.3636, 0.0]`

`reranker8_masked` vs seed-averaged `pairwise_visible`

- `ordinary_auroc` diff: `+0.1042`, CI `[0.0164, 0.2093]`
- `amcd` diff: `+0.1176`, CI `[0.0, 0.2222]`
- `ass_total` diff: `-0.0664`, CI `[-0.1008, -0.0283]`
- `selection_gain_at4` diff: `+0.1765`, CI `[0.0, 0.3636]`
- `exploitability_rate` diff: `-0.2353`, CI `[-0.4, -0.0834]`

Interpretation:

- The Week 5 deployment conclusion survives Week 6 reproduction:
  - `reranker8_masked` remains the strongest model on the main naturalized comparison slice
  - and it is not winning by a narrow one-seed accident
- The cleanest Week 6 result is the visible vs masked reranker comparison:
  - better `ordinary_auroc`
  - much better `AMCD`
  - much lower `ASS_total`
  - lower exploitability
- `visible_cond_swap` remains the strongest low-`ASS_total` frozen-head repair, but Week 6 now shows it still trails the masked reranker on both `ordinary_auroc` and `AMCD`
- `pairwise_visible` is the most seed-unstable frozen-head baseline in the current set; its `AMCD` swings from `0.5` to `0.7941`
- `visible_cond_swap` is more stable than `pairwise_visible`, and its selected `lambda_cond_swap = 2.0` is consistent across all three seeds, but it still does not catch the masked reranker

Overall interpretation:

- Week 6 strengthens the current proposal-aligned deployment story:
  - the strongest current answer-invariant verifier is not a visible repair head
  - it is a stronger reranker deployed in masked mode
- The remaining open items are no longer about whether the main comparison set is stable.
- They are:
  - the external human blind audit
  - final paper-narrative contraction

## 2026-03-10 Benchmark-V3 Strict Smoke Startup

Status: started the separate `benchmark-v3` line and completed the first strict smoke build with multi-candidate generation, masked reviewer filtering, and family selection.

Authoritative smoke command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --seed 17'
```

Superseded startup attempt:

- the first run of `build_benchmark_v3.py` is superseded
- failure mode:
  - reviewer compared answer-visible traces and latched onto swapped-answer contradictions
  - reviewer JSON could also truncate under the longer reason field
- fixed before the authoritative rerun by:
  - switching reviewer comparison to `masked_trace_text`
  - shortening reviewer reason budget and adding partial-JSON fallback parsing
  - making smoke outputs overwrite old artifacts instead of appending across runs

Artifacts:

- `data/generated/craft_core_benchmark_v3_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_smoke_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_artifact_audit.json`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_blind.md`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_blind_key.json`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_blind_form.csv`
- `artifacts/benchmark_v3/benchmark_v3_soft_smoke_internal_review.md`

Smoke configuration:

- source dataset: `data/generated/craft_core_hard_blindfix_v4.jsonl`
- selected quartets: `3` total
  - `algebra-hard-0010`
  - `blocksworld-hard-0008`
  - `graph-hard-0007`
- candidates per role: `2`
- family combinations per quartet: `16`
- reviewer comparisons per quartet: `64`

Strict-smoke outputs:

- selected records: `12`
- candidate rows: `24`
- review rows: `12`
- total API usage: `216` calls, `74682` total tokens

Selected-family summaries:

- `algebra-hard-0010 / alg_v1`
  - selected family index: `7`
  - selection score: `2.2`
  - correct pair: `avg_detectability_penalty = 0.85`, `invalid_pick_rate = 0.5`
  - swapped pair: `avg_detectability_penalty = 0.85`, `invalid_pick_rate = 0.5`
- `blocksworld-hard-0008 / bw_v1`
  - selected family index: `1`
  - selection score: `1.8`
  - correct pair: `avg_detectability_penalty = 0.9`, `invalid_pick_rate = 0.0`
  - swapped pair: `avg_detectability_penalty = 0.9`, `invalid_pick_rate = 0.0`
- `graph-hard-0007 / graph_v3`
  - selected family index: `9`
  - selection score: `1.8`
  - correct pair: `avg_detectability_penalty = 0.9`, `invalid_pick_rate = 0.0`
  - swapped pair: `avg_detectability_penalty = 0.9`, `invalid_pick_rate = 0.0`

Minimal verification:

```bash
PYTHONPATH=src python -m py_compile src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_benchmark_v3_smoke.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_soft_smoke_artifact_audit.json
```

Shallow artifact audit on the selected smoke dataset:

- `num_records = 12`
- `validity_style_auroc = 0.0`
- `length_only_validity_auroc = 0.5`

Interpretation:

- the artifact-audit numbers are too small-sample to use as a headline
- but they do confirm there is no immediate shallow-validity split on this tiny selected slice

Internal blind review on the `3`-item packet:

- reviewer A
  - `item-01` algebra: `Trace 1`
  - `item-02` blocksworld: `Trace 2`
  - `item-03` graph_path: `Trace 1`
- reviewer B
  - `item-01` algebra: `Trace 2`
  - `item-02` blocksworld: `Trace 2`
  - `item-03` graph_path: `Trace 1`

Against the hidden key:

- `item-01` invalid trace is `Trace 2`
- `item-02` invalid trace is `Trace 2`
- `item-03` invalid trace is `Trace 2`

Blind-review read:

- algebra remains unstable: one reviewer flags the invalid trace, one flags the valid trace
- blocksworld is still easy to detect, and both reviewers pick the invalid trace
- graph/path is now flipped the other way: both reviewers pick the valid trace as more synthetic because of overt discourse scaffolding

Main interpretation:

- the separate `benchmark-v3` line is now technically live
- multi-candidate generation plus reviewer-in-the-loop family selection works end-to-end
- but the current scalar selector is not yet strict enough for blind-facing quality
- it can still select families where one trace is obviously synthetic, as long as that trace is not consistently the invalid one
- the next strict step should therefore tighten selection around absolute detectability, not only invalid-pick asymmetry

Decision:

- keep this smoke as the `benchmark-v3` fork point
- do not expand to a larger benchmark-v3 build yet
- first revise the reviewer-selection rule, likely with:
  - hard detectability thresholds
  - cascaded reviewer pruning
  - or a stronger adversarial reviewer stage before family promotion

## 2026-03-10 Benchmark-V3 Strict Gate Rerun (`max_pair_detectability = 0.8`)

Status: completed the first truly strict selector rerun and accepted the resulting `0-selected-family` outcome as the current authoritative benchmark-v3 strict result.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_smoke_reviews.jsonl`

Verification:

```bash
python -m py_compile src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
```

Main result:

- selected families: `0`
- selected records: `0`
- candidate rows preserved: `24`
- review rows preserved: `12`
- API usage: `226` calls, `75811` total tokens

All three smoke quartets were rejected under the strict gate:

- algebra
  - best rejected family max pair detectability: `0.85`
  - mean pair detectability: `0.85`
  - mean invalid-pick rate: `0.5`
- blocksworld
  - best rejected family max pair detectability: `0.9`
  - mean pair detectability: `0.875`
  - mean invalid-pick rate: `0.25`
- graph_path
  - best rejected family max pair detectability: `0.85`
  - mean pair detectability: `0.825`
  - mean invalid-pick rate: `0.5`

Implementation note:

- this rerun also fixed a strict-mode bookkeeping bug:
  - rejected families no longer disappear through exceptions
  - reviewer diagnostics and token usage are now retained even when no family is promoted

Interpretation:

- the `benchmark-v3` strict line is now doing what it should:
  - it refuses to promote families that still look too detectable
- this is a real negative result, not an infrastructure failure
- at the current reviewer, prompt, and `k=2` candidate budget, the candidate pool is not good enough to clear a `0.8` pair-detectability gate in any domain

Decision:

- treat this `0-selected-family` run as the current authoritative strict benchmark-v3 result
- do not widen the threshold just to recover coverage
- the next move should target candidate quality or reviewer cascade design, not score relaxation

## 2026-03-11 Benchmark-V3 Pairwise Cascade Smoke

Status: completed a second strict benchmark-v3 smoke using role-internal pairwise pruning instead of unary candidate filtering.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairprune_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --max-candidates-per-role-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairprune_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairprune_smoke_reviews.jsonl`

Verification:

```bash
python -m py_compile src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
```

Main result:

- selected families: `0`
- selected records: `0`
- candidate rows: `24`
- review rows: `36`
- API usage: `70` calls, `23763` total tokens

Relative to the unary-cascade attempt:

- still `0` promoted families
- but API cost drops from `226` calls to `70`
- and the diagnostic quality is much better:
  - role-level candidate pruning now preserves `1` candidate per role
  - the final rejection happens at the pair gate, not because the candidate prune collapses coverage

Per-domain read:

- algebra
  - all roles survive pairwise prune
  - final family still fails:
    - correct-pair detectability `0.85`
    - swapped-pair detectability `0.4`
- blocksworld
  - all roles survive pairwise prune
  - final family still fails:
    - correct-pair detectability `0.9`
    - swapped-pair detectability `0.9`
- graph_path
  - pairwise prune is informative:
    - it cleanly separates some candidates (`0.0` vs `0.85/0.9`)
  - but the final family still fails:
    - correct-pair detectability `0.8`
    - swapped-pair detectability `0.9`

Interpretation:

- unary candidate filtering was the wrong cascade stage:
  - it labeled almost everything as artificial and gave little signal
- role-internal pairwise prune is much better:
  - it preserves role coverage
  - it sharply reduces reviewer cost
  - it identifies obviously worse candidates
- but the decisive bottleneck is now clearer:
  - the chosen valid/invalid pairs are still too easy to detect once placed side by side
  - even when the individual candidates look acceptable under within-role comparison

Decision:

- keep the pairwise-cascade smoke as the current best benchmark-v3 selector diagnostic
- do not keep tuning unary candidate thresholds
- the next benchmark-v3 move should shift from selector-only work toward pair-conditioned generation or direct pair-level adversarial filtering

## 2026-03-11 Benchmark-V3 Pair-Conditioned Generation Smoke

Status: completed the first benchmark-v3 smoke with pair-conditioned generation, within-role pairwise prune, and the same final strict pair gate.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairgen_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --max-candidates-per-role-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairgen_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairgen_smoke_reviews.jsonl`

Verification:

```bash
python -m py_compile src/civic_prm/api_rewrite.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
```

Main result:

- selected families: `0`
- selected records: `0`
- candidate rows: `24`
- review rows: `24`
- API usage: `48` calls, `22548` total tokens

Relative to the previous pairwise-cascade smoke:

- still `0` promoted families
- reviewer cost drops again:
  - previous pairwise cascade: `70` calls
  - pair-conditioned generation smoke: `48` calls
- role-level candidate pruning now looks much cleaner:
  - many role candidates have `mean_detectability_penalty = 0.0`
  - coverage survives for all `4` roles in all `3` domains

But the final pair gate still rejects everything:

- algebra
  - correct pair detectability: `0.85`
  - swapped pair detectability: `0.85`
- blocksworld
  - correct pair detectability: `0.9`
  - swapped pair detectability: `0.9`
- graph_path
  - correct pair detectability: `0.9`
  - swapped pair detectability: `0.9`

Interpretation:

- pair-conditioned generation improves the candidate stage:
  - lower reviewer cost
  - cleaner within-role candidate rankings
  - no candidate-stage collapse
- but it does **not** yet solve the decisive problem:
  - once the valid/invalid pair is compared side by side, the contrast still looks too detectably patched

This means:

- the main bottleneck is now genuinely pair-level
- not only single-trace realism
- not only selector design

Decision:

- keep `pair-conditioned generation` as a useful benchmark-v3 building block
- but do not treat it as the main fix
- the next serious step should be pair-level adversarial filtering or direct pair-conditioned contrast generation, not more selector-only tuning

## 2026-03-11 Benchmark-V3 Pair-Level Adversarial Prune Smoke

Status: completed the first smoke that preserves joint candidate pairs during pruning instead of pruning valid and invalid traces separately.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairadv_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairadv_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_reviews.jsonl`

Verification:

```bash
python -m py_compile src/civic_prm/api_rewrite.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
```

Main result:

- selected families: `0`
- selected records: `0`
- candidate rows: `24`
- review rows: `24`
- API usage: `49` calls, `22276` total tokens

Relative to the previous pair-conditioned smoke:

- same strict outcome: `0` promoted families
- nearly the same cost (`49` vs `48` calls)
- but this version is conceptually cleaner:
  - it preserves the jointly generated valid/invalid pair when pruning
  - it no longer risks breaking a good joint pair by role-wise top-1 selection

Per-domain read:

- algebra
  - best correct pair detectability improves slightly to `0.8`
  - but swapped pair remains `0.85`
  - final family still rejected
- blocksworld
  - correct pair stays `0.9`
  - swapped pair stays `0.9`
  - final family still rejected
- graph_path
  - best swapped pair reaches `0.85`
  - correct pair stays `0.9`
  - final family still rejected

Interpretation:

- preserving pair coupling is the right abstraction
- but it still does not get a single smoke quartet under the final strict gate
- the remaining gap is now narrow but explicit:
  - current pair-conditioned candidates can approach the threshold
  - especially on algebra and graph/path
  - but not cross it

Decision:

- keep pair-level adversarial prune as the current best benchmark-v3 selection primitive
- stop spending further cycles on role-wise prune variants
- the next meaningful step should target pair-level contrast generation or a stronger reviewer adversary, not another selector refactor

## 2026-03-11 Benchmark-V3 Contrast-Aware Pair Generation Smoke

Status: completed the first contrast-aware pair-generation smoke, using the same pair-level adversarial prune and final strict gate as the previous run.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_paircontrast_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-contrast-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --max-pair-detectability 0.8 \
  --seed 17'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_paircontrast_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircontrast_smoke_reviews.jsonl`

Verification:

```bash
python -m py_compile src/civic_prm/api_rewrite.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py
```

Main result:

- selected families: `0`
- selected records: `0`
- candidate rows: `24`
- review rows: `24`
- API usage: `49` calls, `22383` total tokens

Relative to the previous pair-level adversarial prune smoke:

- no improvement in accepted families (`0 -> 0`)
- cost is effectively unchanged (`49` calls)
- algebra does not improve:
  - best family max detectability stays `0.85`
- blocksworld does not improve:
  - both final pairs stay at `0.9`
- graph/path also does not improve materially:
  - best final family max detectability stays `0.85`

Interpretation:

- a stronger contrast-aware pair prompt is not enough by itself
- the benchmark-v3 bottleneck is no longer mainly prompt phrasing
- at this point, pair-level generation prompts and pair-level selector structure are both close to saturated on the current reviewer/model setup

Decision:

- do not continue iterating prompt-only pair-contrast generation in the same loop
- the next serious move should be a stronger reviewer adversary or a different generation model, not another prompt refinement pass

## 2026-03-11 Benchmark-V3 PairAdv Ensemble Reviewer Smoke

Status: completed a strict smoke rerun on the existing `pairadv` candidate pool, holding generation fixed and replacing the single API reviewer with an `api + local Qwen3-8B` reviewer ensemble.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_ensemble_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_max'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairadv_ensemble_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_artifact_audit.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_blind.md`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_blind_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_ensemble_smoke_internal_review.md`

Verification:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python -m py_compile src/civic_prm/reviewer_backends.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py'
```

Main result:

- selected families: `3`
- selected records: `12`
- review usage: `36` calls, `27344` total tokens
- shallow artifact audit stays clean on the selected set:
  - `validity_style_auroc = 0.0`
  - `length_only_validity_auroc = 0.25`

Selected-family detectability:

- algebra: correct `0.7`, swapped `0.7`
- blocksworld: correct `0.7`, swapped `0.7`
- graph/path: correct `0.7`, swapped `0.5`

But blind-facing internal review rejects the packet:

- reviewer A picks the more artificial side on all `3/3` items
- reviewer B also rejects the packet overall
- exact item-level agreement is `2/3`
- both reviewers conclude the packet is not suitable as a promoted strict sample

Interpretation:

- this is not a benchmark-v3 success
- the stronger reviewer experiment does show that the previous single-reviewer gate was not robust
- but the current ensemble aggregation is too permissive:
  - review labels are dominated by `both` (`19/36`)
  - many pairwise judgments collapse to `both`
  - `both` lowers the scalar penalty enough to pass the gate
  - while blind-facing reviewers still see stable synthetic asymmetry

Decision:

- do not promote `benchmark_v3_pairadv_ensemble_smoke` as the new authoritative strict result
- keep `pairadv` / `paircontrast` as the current strict rejection baseline
- if benchmark-v3 continues, the next move should harden reviewer aggregation itself:
  - adversarial max-penalty aggregation
  - or a stronger reviewer family rather than label-space union

## 2026-03-11 Benchmark-V3 PairAdv Adversarial-Max Aggregation Smoke

Status: completed a second reviewer-only rerun on the same `pairadv` candidate pool, replacing the permissive `api_local_max` union with adversarial max-penalty aggregation.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_advmax_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairadv_advmax_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_advmax_smoke_reviews.jsonl`

Verification:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python -m py_compile src/civic_prm/reviewer_backends.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py'
```

Main result:

- selected families: `0`
- selected records: `0`
- review usage: `24` calls, `18159` total tokens

Failure mode:

- all `3/3` quartets die at `pair_candidate_prune`
- algebra:
  - correct pair penalties `0.95`, `1.0`
  - swapped pair penalties `0.95`, `0.95`
- blocksworld:
  - all candidate-pair penalties `>= 0.9`
- graph/path:
  - all candidate-pair penalties `0.9`

Interpretation:

- this confirms the previous `api_local_max` promotion was an aggregation artifact
- once aggregation is made adversarial, the same candidate pool clears nothing
- the current strict story is therefore:
  - `api_local_max` is too permissive
  - `api_local_advmax` is much closer to the intended blind-clean gate

Decision:

- treat `benchmark_v3_pairadv_advmax_smoke` as the current reviewer-aggregation-correct strict result
- do not scale benchmark-v3 on top of the permissive union ensemble
- if the benchmark-v3 line continues, the next moves should target:
  - stronger pair generation
  - or a genuinely stronger reviewer family
  - not another lenient aggregation trick

## 2026-03-11 Benchmark-V3 Critic Reviewer Family Smoke

Status: completed a strict smoke rerun on the same `pairadv` candidate pool using a genuinely different local reviewer family: `CriticLeanGPT-Qwen3-8B-RL`.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairadv_smoke_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairadv_critic_smoke.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_reviews.jsonl \
  --pair-conditioned-generation \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend local_qwen \
  --reviewer-model-root /cephfs/shared/hf_cache/hub/models--m-a-p--CriticLeanGPT-Qwen3-8B-RL/snapshots/2f9e8aa0e4965cfbd9ad9c0985c5fa1e944b4f40'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairadv_critic_smoke.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairadv_critic_smoke_reviews.jsonl`

Verification:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python - <<'"'"'PY'"'"'
from transformers import AutoTokenizer, AutoModelForCausalLM
root="/cephfs/shared/hf_cache/hub/models--m-a-p--CriticLeanGPT-Qwen3-8B-RL/snapshots/2f9e8aa0e4965cfbd9ad9c0985c5fa1e944b4f40"
tok=AutoTokenizer.from_pretrained(root, trust_remote_code=True)
model=AutoModelForCausalLM.from_pretrained(root, dtype="auto", device_map="auto", trust_remote_code=True)
print(model.__class__.__name__)
PY'
```

Main result:

- selected families: `0`
- selected records: `0`
- review usage: `24` calls, `9427` total tokens

Failure mode:

- all `3/3` quartets die at `pair_candidate_prune`
- algebra:
  - all pair penalties `0.9`
- blocksworld:
  - all pair penalties `0.9`
- graph/path:
  - all pair penalties `0.9`

Interpretation:

- switching to a genuinely different critic-style reviewer family does not rescue the current candidate pool
- this strengthens the stricter reading from `api_local_advmax`:
  - the remaining problem is still candidate pair quality
  - not only aggregation quirks of the earlier ensemble

Side result:

- `Qwen3.5-35B-A3B` was probed as the next stronger generation option
- current `infer` environment cannot load it because `transformers` does not recognize `qwen3_5_moe`
- so the present stronger-model continuation uses the locally available critic family instead of a 35B generator

Decision:

- keep `benchmark_v3_pairadv_advmax_smoke` and `benchmark_v3_pairadv_critic_smoke` as converging negative evidence
- if benchmark-v3 continues, the next serious move should be:
  - a working stronger generation backend
  - or environment support for `Qwen3.5-35B-A3B`
  - rather than more reviewer-side prompt tweaks

## 2026-03-11 Benchmark-V3 API Pair Generation V2 Smoke

Status: completed the first stronger-usage API generation run. This is not a new reviewer trick; generation still uses the same API model, but now with reviewer-guided pair regeneration.

Protocol:

- same base API generator
- same strict reviewer backend: `api_local_advmax`
- `k = 2` initial pair-conditioned candidates
- `1` regeneration round
- regenerate the best failing pair above threshold using blind-review feedback

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 1 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k2.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_reviews.jsonl`

Verification:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
python -m py_compile src/civic_prm/api_rewrite.py src/civic_prm/benchmark_v3.py scripts/build_benchmark_v3.py'
```

Main result:

- selected families: `0`
- selected records: `0`
- review+generation usage: `80` calls, `58089` total tokens

What changed:

- each answer variant now gets a regenerated third candidate (`...-b3pc01-b3pc03` or `...-b3pc02-b3pc03`)
- algebra improves slightly:
  - correct-side penalties move from `0.95 / 1.0` down to `0.9` for the regenerated best pair
- graph/path and blocksworld also produce regenerated candidates, but all final candidate-pair penalties remain `0.9`

Interpretation:

- the API model is not the immediate limiter by itself; the stronger usage protocol does change the candidate pool
- but this first one-round regeneration loop is still not enough to clear a `0.8` strict gate
- current evidence says:
  - reviewer-guided regeneration helps a little
  - but not enough at `k=2, 1 round`
  - and the cost rises sharply

Decision:

- keep this as the first real API-usage upgrade, not as a benchmark-v3 success
- if the API line continues, the next useful move should be:
  - multi-round regeneration
  - or larger candidate pools with cheaper early pruning
  - not another change of reviewer family

## 2026-03-11 Benchmark-V3 API Pair Generation V2, Two-Round Smoke

Status: completed the next API-native continuation by increasing reviewer-guided regeneration from `1` round to `2` rounds, keeping the same strict reviewer and the same `k=2` smoke scale.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_r2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 2 \
  --pair-regeneration-top-k 1 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_r2.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_r2_reviews.jsonl`

Main result:

- selected families: `0`
- selected records: `0`
- usage: `134` calls, `103912` total tokens

Relative to the one-round API regeneration run:

- still `0/3` accepted families
- cost rises sharply:
  - `58089 -> 103912` total tokens
  - `80 -> 134` calls
- the extra round does create another regenerated candidate (`...-b3pc04`)
- but the best penalties plateau at `0.9` instead of crossing `0.8`

Per-domain read:

- algebra:
  - correct and swapped sides now both bottom out at `0.9`
- blocksworld:
  - regenerated pairs remain flat at `0.9`
- graph/path:
  - regenerated pairs also flatten at `0.9`

Interpretation:

- this is stronger evidence that the current API-native loop is improving the pool but saturating above the strict threshold
- one extra regeneration round helps convergence toward a cleaner local plateau
- but it does not create a breakthrough candidate under the present strict reviewer

## 2026-03-11 Benchmark-V3 API Pair Generation V2, Wider-Branch Smoke

Status: completed the next API-native continuation by keeping regeneration depth at `1` round but widening the branch from `top_k=1` to `top_k=2`, still under the same strict reviewer and the same `k=2` smoke scale.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_reviews.jsonl`

Main result:

- selected families: `0`
- selected records: `0`
- output dataset path exists but is empty (`0` bytes)
- usage: `99` calls, `69618` total tokens

Relative to the previous API-native runs:

- vs `1 round, top_k=1`:
  - still `0/3` accepted families
  - cost rises moderately:
    - `58089 -> 69618` total tokens
    - `80 -> 99` calls
  - both failing answer-variant pairs now get regenerated in the same round
- vs `2 rounds, top_k=1`:
  - still `0/3` accepted families
  - but width is much cheaper than depth:
    - `69618 < 103912` total tokens
    - `99 < 134` calls
  - while reaching essentially the same `0.9` detectability plateau

Per-domain read:

- algebra:
  - width helps more than depth in one respect: both correct-side regenerated pairs drop to `0.9`
  - but swapped-side candidates still stay at `0.9` or `0.95`, so nothing crosses `0.8`
- blocksworld:
  - all regenerated pairs remain at `0.9`
- graph/path:
  - all regenerated pairs also remain at `0.9`

Interpretation:

- this is the first direct evidence that, under the current API-native loop, wider branching is more cost-effective than deeper top-1 chaining
- but width alone still does not break the strict gate
- the current bottleneck is no longer “insufficient depth”; it is the quality ceiling of the regenerated pair pool under the present search shape

Decision:

- keep this as the current best API-native breadth result, not as a benchmark-v3 success
- if the API line continues, the next useful move should widen the search earlier or more aggressively:
  - larger initial candidate pools with cheap early pruning
  - or multi-branch regeneration beyond the current `k=2`
  - not another top-1 depth increase

## 2026-03-11 Benchmark-V3 API Pair Generation V2, Larger-Initial-Pool Smoke

Status: completed the next API-native breadth continuation by increasing the initial candidate pool from `2` to `3` while keeping `1` regeneration round and `top_k=2`.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k3_top2.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 3 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k3_top2.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k3_top2_reviews.jsonl`

Main result:

- selected families: `0`
- selected records: `0`
- output dataset path exists but is empty (`0` bytes)
- usage: `131` calls, `93053` total tokens

Relative to the previous breadth result (`candidates_per_role=2`, `top_k=2`):

- still `0/3` accepted families
- cost rises materially:
  - `69618 -> 93053` total tokens
  - `99 -> 131` calls
- no domain breaks through the `0.9` plateau

Per-domain read:

- algebra:
  - the larger pool does create more diversity (`b3pc03`, `b3pc04`, `b3pc05`)
  - but the best candidate pairs remain at `0.9`
  - and several regenerated pairs stay at `0.95`
- blocksworld:
  - best pairs remain at `0.9`
  - some new candidates are worse (`0.95`)
- graph/path:
  - all best candidate pairs remain at `0.9`

Interpretation:

- simply enlarging the initial pool is not enough under the current reviewer + prune structure
- this run is dominated by the earlier `k=2, top_k=2` breadth result:
  - same `0-selected-family`
  - higher cost
  - no better pair detectability

Decision:

- do not promote this as the new API-native baseline
- keep `benchmark_v3_pairregen_smoke_k2_top2_summary.json` as the current best breadth result
- if the API line continues, the next useful move should change the early pruning shape or branching policy, not just add one more initial candidate per side

## 2026-03-11 Benchmark-V3 Pair Cascade Smoke

Status: completed the first true two-stage cascade for benchmark-v3:

- stage 1: API generation + local cheap prune
- stage 2: strict `api_local_advmax` final gate on the pruned candidate pool

One implementation bug surfaced and was fixed before the final rerun:

- regenerated candidate verbalizers were being written as `..._b3_b3`
- this broke candidate-input reuse for algebra
- the fix is now in `src/civic_prm/benchmark_v3.py`

Stage 1 command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage1_localprune.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_reviews.jsonl \
  --candidate-output-mode pruned \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 3 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.9 \
  --max-pair-detectability 0.8 \
  --reviewer-backend local_qwen'
```

Stage 2 command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage2_advmax.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_advmax_reviews.jsonl`

Main result:

- stage 1 local prune:
  - `0` selected families
  - but all `3/3` quartets keep one pair per answer variant under the looser `0.9` screen
  - usage: `141` calls, `65382` total tokens
- stage 2 strict rerun:
  - `0` selected families
  - usage: `12` calls, `9233` total tokens
- combined:
  - still `0/3` promoted families
  - combined measured usage: `153` calls, `74615` total tokens

Relative to the one-shot `candidates_per_role=3, top_k=2` strict run:

- quality is unchanged: still `0/3`
- but the final strict review becomes much cheaper once the local cascade has reduced each quartet to one family
- combined measured token count is lower than the one-shot run:
  - `74615 < 93053`

Per-domain read after the final strict rerun:

- algebra:
  - final family still lands at `0.9`
- blocksworld:
  - final family still lands at `0.9`
- graph/path:
  - final family still lands at `0.9`

Interpretation:

- cheap local pruning is now a useful efficiency primitive
- but it is not a quality primitive under the current setup
- the cascade reduces final strict-review cost, but it does not move any domain below the `0.8` gate

Decision:

- keep this as the first real cascade result, not as a benchmark-v3 success
- do not replace `benchmark_v3_pairregen_smoke_k2_top2_summary.json` as the best single-run breadth baseline
- if benchmark-v3 continues, the next useful move is to let the second stage regenerate from the locally pruned survivors, not just re-score them

## 2026-03-11 Benchmark-V3 Second-Stage Regeneration Follow-Up

Status: completed the next benchmark-v3 continuation by turning the cascade into a real generation pipeline:

- stage 1: local cheap prune to one surviving pair per answer variant
- stage 2: strict API-native pair regeneration from those survivors

This required one minimal CLI extension in `scripts/build_benchmark_v3.py`:

- `--regenerate-from-candidate-input`

Stage 2 command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_paircascade_stage1_localprune_candidates_pruned.jsonl \
  --regenerate-from-candidate-input \
  --output data/generated/craft_core_benchmark_v3_paircascade_stage2_regen.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Artifacts:

- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_paircascade_stage2_regen_reviews.jsonl`
- `data/generated/craft_core_benchmark_v3_paircascade_stage2_regen.jsonl`

Main result:

- second-stage regeneration:
  - selected families: `0`
  - selected records: `0`
  - usage: `97` calls, `76884` total tokens
- combined with stage 1 local prune:
  - combined measured usage: `141 + 97 = 238` calls
  - combined measured usage: `65382 + 76884 = 142266` total tokens

Relative to the earlier baselines:

- vs one-shot best breadth run (`k=2, top_k=2`):
  - same `0/3` accepted families
  - much higher total cost:
    - `69618 -> 142266`
- vs one-shot larger-pool run (`k=3, top_k=2`):
  - same `0/3` accepted families
  - still higher total cost:
    - `93053 -> 142266`
- vs plain cascade re-score:
  - quality still unchanged at `0/3`
  - but stage 2 generation is much more expensive than stage 2 re-scoring

Per-domain read:

- algebra:
  - second-stage regeneration creates new chained candidates
  - but all surviving pair penalties still remain at `0.9`
- blocksworld:
  - still fails pair-candidate prune with all surviving pairs at `0.9` or worse
- graph/path:
  - also remains flat at `0.9`

Interpretation:

- second-stage regeneration from locally pruned survivors does not break the `0.9` plateau
- under the current protocol, cascade+regeneration is not just a quality miss; it is also a cost regression
- this is stronger evidence that the present bottleneck is not merely search order

Decision:

- do not continue scaling the current second-stage regeneration shape
- keep `benchmark_v3_pairregen_smoke_k2_top2_summary.json` as the best current single-run API-native baseline
- keep `benchmark_v3_paircascade_stage2_advmax_summary.json` as the best current efficiency-oriented cascade result
- treat `benchmark_v3_paircascade_stage2_regen_summary.json` as a negative continuation

Decision:

- do not continue blindly increasing regeneration depth in the same smoke loop
- the next API-native move should change search breadth or pruning structure:
  - larger candidate pools with cheap early screening
  - or a different regeneration branching policy
  - not just more rounds on the same top-1 failing pair

## 2026-03-11 Benchmark-V3 Proposal-Aligned Acceptance Rerun

Status: completed the first `benchmark-v3` rerun after resetting the benchmark target to the proposal-aligned acceptance rule in `history/benchmark_acceptance.md`.

This round had two parts:

1. rerun the current best one-shot breadth baseline with the corrected prompt objective
2. rescore old vs new review logs under proposal-aligned acceptance modes instead of only the over-strong universal strict gate

Code changes:

- extracted lightweight acceptance helpers into `src/civic_prm/acceptance.py`
- updated `src/civic_prm/api_rewrite.py` to import `filter_surface_feedback(...)` from that lightweight module
- added `scripts/analyze_benchmark_v3_acceptance.py` for reproducible acceptance rescoring

Rerun command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Acceptance analysis command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run old:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_reviews.jsonl \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_acceptance_compare.json'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_acceptance_compare.json`

Verification:

```bash
python -m py_compile src/civic_prm/acceptance.py src/civic_prm/api_rewrite.py scripts/analyze_benchmark_v3_acceptance.py
```

Strict rerun result:

- old wider-branch baseline:
  - `0` selected families
  - `69618` total tokens
- new proposal-aligned prompt rerun:
  - `0` selected families
  - `75036` total tokens

So the prompt correction did **not** by itself turn the universal strict gate into a pass.

But the acceptance analysis changes the interpretation materially.

Reviewer reason mix:

- old run:
  - `semantic_only = 14`
  - `mixed = 7`
  - `surface_only = 23`
  - `other = 4`
- new accept rerun:
  - `semantic_only = 18`
  - `mixed = 10`
  - `surface_only = 14`
  - `other = 6`

Per-domain shift:

- algebra:
  - old: `semantic_only 8`, `mixed 6`, `surface_only 2`
  - new: `semantic_only 7`, `mixed 8`, `surface_only 1`
- blocksworld:
  - old: `surface_only 11`, `mixed 1`, `semantic_only 1`, `other 3`
  - new: `surface_only 10`, `mixed 2`, `other 4`
- graph/path:
  - old: `surface_only 10`, `semantic_only 5`, `other 1`
  - new: `semantic_only 11`, `surface_only 3`, `other 2`

Proposal-aligned rescoring:

- under the original strict scalar gate:
  - old: `0/3`
  - new: `0/3`
- if `semantic_only` penalties are ignored:
  - old: `2/3`
  - new: `2/3`
- if only explicit `surface_only` or `mixed` penalties are counted:
  - old: `3/3`
  - new: `3/3`

Per-quartet read under `ignore_semantic_only`:

- old:
  - algebra accepted
  - graph/path accepted
  - blocksworld rejected
- new:
  - algebra accepted
  - graph/path accepted
  - blocksworld rejected

Interpretation:

- the universal strict gate is still too harsh for the proposal target
- after the prompt correction, graph/path reviewer signal shifts strongly toward semantic visibility rather than surface artifact
- blocksworld remains the clearest unresolved surface-artifact bottleneck under the proposal-aligned acceptance rule
- the corrected prompt did not yet improve acceptance counts, but it did improve the meaning of the remaining reviewer signal

Decision:

- do not read the new `0/3` strict result as proof that the corrected benchmark target failed
- use `benchmark_v3_pairregen_smoke_k2_top2_acceptance_compare.json` as the current authoritative acceptance diagnostic
- keep `benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json` as the first rerun aligned to the corrected benchmark objective
- if benchmark-v3 continues, optimize against proposal-aligned artifact acceptance rather than universal strict pair indistinguishability

## 2026-03-11 Benchmark-V3 Blocksworld-Focused Hardening

Status: completed the first targeted follow-up after the acceptance correction. This round only attacks the remaining blocksworld surface-artifact bottleneck.

Prompt / post-processing changes in `src/civic_prm/api_rewrite.py`:

- strengthened blocksworld domain guidance to keep the exact source move action
- explicitly banned explanatory narration about stack structure, goals, or why a move helps
- passed domain guidance into pair rewrite / pair contrast / pair feedback prompts
- normalized all blocksworld steps to the same direct move-report surface:
  - canonical action from the source step
  - canonical resulting state
  - one-sentence `Move ... , reaching state ...` style

Minimal verification:

```bash
python -m py_compile src/civic_prm/api_rewrite.py
```

Quick blocksworld-only smoke (different quartet, diagnostic only):

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4_blocksworld_only.jsonl \
  --output data/generated/craft_core_benchmark_v3_blocksworld_accept_bw1.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_blocksworld_accept_bw1_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_blocksworld_accept_bw1_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_blocksworld_accept_bw1_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Diagnostic result:

- selected quartet: `blocksworld-hard-0010`
- strict result: `0/1`
- usage: `23520` total tokens
- but all pair summaries collapse to a symmetric `0.9 / invalid_pick_rate 0.5` pattern rather than the earlier style-skewed mix

Authoritative same-quartet rerun for comparison:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4_blocksworld_0008_bw1_only.jsonl \
  --output data/generated/craft_core_benchmark_v3_blocksworld_0008_accept_bw1.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Acceptance comparison:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run bw1:artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_summary.json:artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_acceptance_compare.json'
```

Artifacts:

- `data/generated/craft_core_hard_blindfix_v4_blocksworld_only.jsonl`
- `data/generated/craft_core_hard_blindfix_v4_blocksworld_0008_bw1_only.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_blocksworld_accept_bw1_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_blocksworld_0008_accept_bw1_acceptance_compare.json`

Same-quartet `blocksworld-hard-0008` result:

- strict scalar gate:
  - before: reject (`0.9 / 0.9`)
  - after: reject (`0.9 / 0.9`)
- proposal-aligned rescoring:
  - before:
    - `ignore_semantic_only`: reject
    - `surface_or_mixed_only`: accept (`0.45 / 0.45`)
  - after:
    - `ignore_semantic_only`: accept (`0.0 / 0.0`)
    - `surface_or_mixed_only`: accept (`0.0 / 0.0`)

Reviewer bucket shift on blocksworld:

- before:
  - `surface_only = 10`
  - `mixed = 2`
  - `other = 4`
- after:
  - `surface_only = 1`
  - `semantic_only = 10`
  - `other = 5`

Concrete reason shift:

- before:
  - `templated phrasing`
  - `The system moves`
  - `four separate stacks`
  - `extra step feels templated`
- after:
  - `extra step to clear B`
  - `extra table move seems unnecessary`
  - `more systematic table moves`
  - `more direct moves`

Interpretation:

- the blocksworld hardening does **not** beat the over-strong universal strict gate
- but under the proposal-aligned acceptance rule it clearly works
- the main reviewer signal is no longer “this pair looks templated / patched”
- it is now mostly about the move sequence itself being more direct or containing an extra table move

Decision:

- treat this as the first benchmark-v3 subproblem that has been meaningfully improved under the corrected acceptance target
- do not keep optimizing blocksworld against the universal strict scalar gate
- move the next benchmark-v3 hardening effort to the remaining algebra / mixed bucket

## 2026-03-11 Benchmark-V3 Algebra-Focused Hardening

Status: completed the next targeted follow-up on the remaining algebra / mixed bucket.

Goal:

- keep the proposal-aligned acceptance target fixed
- reduce algebra register drift and sentence-stitching cues
- try to convert the remaining `mixed` reviewer signal into mostly `semantic_only`

Code changes in `src/civic_prm/api_rewrite.py`:

- added benchmark-v3-only algebra canonicalization:
  - step 1: `<cancel-bias operation> to get <exact equation fragment>.`
  - step 2: `Divide both sides by <a> to get <exact equation fragment>.`
  - step 3: `<undo-shift operation> to get <exact equation fragment>.`
- strengthened algebra domain guidance to keep operation framing compact and parallel
- froze algebra `benchmark_v3` problem text during rewrite so algebra reruns do not fail on irrelevant problem-text paraphrase drift

Minimal verification:

```bash
python -m py_compile src/civic_prm/api_rewrite.py
```

First attempt:

- same-quartet rerun initially failed with:
  - `pair_candidate_generation_failed:valid_correct:invalid_correct`
  - `missing step anchors: ['-7']`
- root cause:
  - algebra problem-text rewriting was introducing validator noise unrelated to the current benchmark question
- fix:
  - keep source problem text unchanged for `benchmark_v3` algebra rewrites

Authoritative same-quartet rerun:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4_algebra_0010_alg1_only.jsonl \
  --output data/generated/craft_core_benchmark_v3_algebra_0010_accept_alg1.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Acceptance comparison:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run alg1:artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_summary.json:artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_acceptance_compare.json'
```

Artifacts:

- `data/generated/craft_core_hard_blindfix_v4_algebra_0010_alg1_only.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_algebra_0010_accept_alg1_acceptance_compare.json`

Same-quartet `algebra-hard-0010 / alg_v1` result:

- strict scalar gate:
  - before: reject (`0.9 / 0.95`)
  - after: reject (`0.9 / 1.0`)
- proposal-aligned rescoring:
  - before:
    - `ignore_semantic_only`: accept (`0.0 / 0.45`)
    - `surface_or_mixed_only`: accept (`0.0 / 0.45`)
  - after:
    - `ignore_semantic_only`: accept (`0.0 / 0.0`)
    - `surface_or_mixed_only`: accept (`0.0 / 0.0`)

Reviewer bucket shift on algebra:

- before:
  - `semantic_only = 7`
  - `mixed = 8`
  - `surface_only = 1`
- after:
  - `semantic_only = 8`
  - `mixed = 7`
  - `surface_only = 1`

Concrete reason shift:

- before:
  - `inconsistent arithmetic ... suggesting patching`
  - `awkward phrasing`
  - `templated phrasing`
- after:
  - `incorrect arithmetic in first step`
  - `incorrect addition step`
  - `inconsistent numbers in steps`

Interpretation:

- the algebra hardening does not help the over-strong strict scalar gate
- but under the proposal-aligned acceptance rule it improves the same quartet
- the remaining reviewer signal is now even more clearly dominated by semantic wrongness visibility rather than surface editing cues

Decision:

- do not continue pushing algebra toward the universal strict scalar gate
- treat the current algebra result as another confirmation that the remaining strict failures are largely semantic, not artifact-driven
- the next useful benchmark-v3 move should be an integrated full-smoke rerun under the corrected acceptance target, not more per-domain micro-hardening

## 2026-03-11 Benchmark-V3 Integrated Acceptance Rerun

Integrated full-smoke rerun under the corrected benchmark target:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept_integrated.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --quartets-per-domain 1 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Acceptance comparison:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run accept:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_reviews.jsonl \
  --run integrated:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_acceptance_compare.json'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_smoke_k2_top2_accept_integrated.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_acceptance_compare.json`

Integrated result:

- universal strict scalar gate remains `0/3`
- proposal-aligned acceptance improves to:
  - `ignore_semantic_only = 3/3`
  - `surface_or_mixed_only = 3/3`
- usage:
  - `68808` total tokens
  - `96` calls

Per-domain read:

- algebra:
  - strict: reject (`0.9 / 0.9`)
  - `ignore_semantic_only`: accept (`0.0 / 0.0`)
  - `surface_or_mixed_only`: accept (`0.0 / 0.0`)
- blocksworld:
  - strict: reject (`0.9 / 0.9`)
  - `ignore_semantic_only`: accept (`0.45 / 0.45`)
  - `surface_or_mixed_only`: accept (`0.0 / 0.0`)
- graph_path:
  - strict: reject (`0.9 / 0.9`)
  - `ignore_semantic_only`: accept (`0.0 / 0.45`)
  - `surface_or_mixed_only`: accept (`0.0 / 0.0`)

Reviewer bucket shift from the earlier corrected `accept` rerun to the integrated rerun:

- algebra:
  - before: `semantic_only 7 / mixed 8 / surface_only 1`
  - after: `semantic_only 13 / surface_only 3`
- blocksworld:
  - before: `surface_only 10 / mixed 2 / other 4`
  - after: `other 8 / semantic_only 7 / surface_only 1`
- graph_path:
  - before: `semantic_only 11 / surface_only 3 / other 2`
  - after: `semantic_only 10 / surface_only 4 / other 1 / mixed 1`

Interpretation:

- under the proposal-aligned benchmark target, benchmark-v3 is now good enough at smoke scale
- the universal strict scalar still over-penalizes semantic/task-structure visibility and should remain a diagnostic, not the acceptance rule
- the remaining reviewer signal is now predominantly semantic rather than surface-artifact driven

Decision:

- stop optimizing benchmark-v3 against the universal strict scalar gate
- treat the current integrated smoke as the authoritative proposal-aligned benchmark-v3 read
- if benchmark-v3 continues, prioritize scaling/diversifying the acceptance-clean protocol rather than more local prompt hardening

## 2026-03-11 Benchmark-V3 Mini-Benchmark Acceptance Rerun

Scale-up rerun with the same corrected protocol:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_integrated.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl \
  --quartets-per-domain 2 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax'
```

Acceptance comparison:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run integrated_smoke:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_smoke_k2_top2_accept_integrated_reviews.jsonl \
  --run miniset:artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json:artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_acceptance_compare.json'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_integrated.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_acceptance_compare.json`

Mini-benchmark result:

- universal strict scalar gate remains `0/6`
- proposal-aligned acceptance now holds at mini-benchmark scale:
  - `ignore_semantic_only = 6/6`
  - `surface_or_mixed_only = 6/6`
- usage:
  - `156948` total tokens
  - `259` calls

Quartets:

- algebra:
  - `algebra-hard-0003 / alg_v1`
  - `algebra-hard-0010 / alg_v1`
- blocksworld:
  - `blocksworld-hard-0000 / bw_v3`
  - `blocksworld-hard-0008 / bw_v1`
- graph_path:
  - `graph-hard-0006 / graph_v2`
  - `graph-hard-0007 / graph_v3`

Per-domain read under proposal-aligned acceptance:

- algebra:
  - `2/2` accepted under both `ignore_semantic_only` and `surface_or_mixed_only`
- blocksworld:
  - `2/2` accepted under both `ignore_semantic_only` and `surface_or_mixed_only`
- graph_path:
  - `2/2` accepted under both `ignore_semantic_only` and `surface_or_mixed_only`

Interpretation:

- the proposal-aligned benchmark-v3 acceptance result is not a one-off smoke artifact; it survives a scale-up to `6` quartets
- the universal strict scalar continues to act as a semantic-visibility diagnostic rather than a useful acceptance rule
- the next benchmark-v3 question is now scale/cost, not whether the corrected acceptance target is real

Decision:

- treat benchmark-v3 as adequate at mini-benchmark scale under the proposal target
- stop spending budget on local prompt hardening aimed only at improving the universal strict scalar
- if benchmark-v3 continues, prioritize cheaper scaling or more diverse quartet selection under the same acceptance rule

## 2026-03-11 Benchmark-V3 Acceptance-Mode Export Fix

Problem:

- benchmark-v3 was already acceptable under the proposal-aligned acceptance rule
- but the builder still exported records only under the old strict scalar gate
- this left the promoted dataset empty even when the acceptance compare said the mini-benchmark should pass

Code changes:

- add `--acceptance-mode` to `scripts/build_benchmark_v3.py`
- make pair-prune and family-selection rank/threshold against the chosen acceptance mode
- preserve strict detectability diagnostics in all summaries
- cache pair-prune reviewer results and reuse them in family selection to remove re-review drift

Minimal export verification on the existing mini-benchmark candidate pool:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_integrated_candidates.jsonl \
  --output data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_reviews.jsonl \
  --quartets-per-domain 2 \
  --verbalizers-per-quartet 1 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax \
  --acceptance-mode ignore_semantic_only'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_pairregen_miniset_k2_top2_accept_export_ignore_semantic_reviews.jsonl`

Result:

- `acceptance_mode = ignore_semantic_only`
- `num_selected_families = 6`
- `num_selected_records = 24`
- per-domain export:
  - algebra `8`
  - blocksworld `8`
  - graph_path `8`
- `skipped_groups = []`
- usage:
  - `67967` total tokens
  - `96` calls

Interpretation:

- the export mismatch is resolved
- benchmark-v3 promotion is now aligned with the proposal-aligned acceptance target
- reusing an existing candidate pool is materially cheaper than rerunning the full mini-benchmark

Decision:

- use the acceptance-mode export path for any future benchmark-v3 promotion
- keep `strict` as a diagnostic mode, not as the only export rule
- when scaling benchmark-v3, prefer candidate-pool reuse plus acceptance-mode selection before paying for full regeneration

## 2026-03-12 Benchmark-V3 Mid-Scale Export

Run a larger acceptance-mode benchmark export directly from source:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/build_benchmark_v3.py \
  --source-dataset data/generated/craft_core_hard_blindfix_v4.jsonl \
  --output data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json \
  --candidate-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_candidates.jsonl \
  --review-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --quartets-per-domain 6 \
  --verbalizers-per-quartet 3 \
  --candidates-per-role 2 \
  --base-temperature 0.8 \
  --pair-conditioned-generation \
  --pair-regeneration-rounds 1 \
  --pair-regeneration-top-k 2 \
  --pair-regeneration-threshold 0.8 \
  --max-pairs-per-answer-variant-after-prune 1 \
  --pair-prune-max-detectability 0.8 \
  --max-pair-detectability 0.8 \
  --reviewer-backend api_local_advmax \
  --acceptance-mode ignore_semantic_only'
```

Acceptance analysis:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run midset:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis.json'
```

Artifacts:

- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_candidates.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis.json`

Main result:

- `acceptance_mode = ignore_semantic_only`
- `num_selected_families = 44 / 54`
- `num_selected_records = 176`
- exported dataset line count: `176`

Domain balance:

- algebra: `72` records = `18` families
- blocksworld: `40` records = `10` families
- graph_path: `64` records = `16` families

Usage:

- `1337662` total tokens
- `2345` calls

Skipped groups:

- total: `10`
- by reason:
  - `pair_candidate_prune_failed = 8`
  - `pair_candidate_generation_failed:valid_correct:invalid_correct = 2`
- by domain:
  - `blocksworld = 8`
  - `graph_path = 2`

Acceptance analysis on the same review log:

- `strict = 2 / 54`
- `ignore_semantic_only = 44 / 54`
- `surface_or_mixed_only = 48 / 54`

Interpretation:

- benchmark-v3 is now a real mid-scale exported benchmark, not just a smoke artifact
- algebra is effectively solved under the current protocol at this scale
- graph_path is close, with only `2` generation failures
- blocksworld remains the main scaling bottleneck

Decision:

- treat `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json` as the first-pass raw build result, not the final authoritative acceptance-corrected export
- keep `ignore_semantic_only` as the current export rule
- if benchmark-v3 continues scaling, target blocksworld robustness first rather than more global prompt changes

## 2026-03-12 Benchmark-V3 Mid-Scale Acceptance Correction

Status: corrected the proposal-aligned acceptance read and re-exported the benchmark deterministically from the existing candidate pool.

Acceptance re-analysis command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_acceptance.py \
  --run midset:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_summary.json:artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_reviews.jsonl \
  --output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json'
```

Deterministic export command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/export_benchmark_v3_from_acceptance.py \
  --candidate-input artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_candidates.jsonl \
  --acceptance-analysis artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json \
  --run-label midset \
  --mode ignore_semantic_only \
  --output data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --summary-output artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json'
```

Authoritative corrected artifacts:

- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_acceptance_analysis_v2.json`
- `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json`
- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

What changed:

- this is **not** a new generation run
- the correction comes from tightening the acceptance taxonomy so planning-domain comments like `forced sequence`, `more direct`, `table clearing`, and `unnecessary intermediate steps` are treated as semantic/task-structure visibility rather than automatic surface-artifact failures
- export is now derived deterministically from the corrected acceptance analysis, so there is no extra reviewer drift between analysis and promotion

Corrected result:

- `acceptance_mode = ignore_semantic_only`
- `num_selected_families = 52 / 54`
- `num_selected_records = 208`
- exported dataset line count: `208`

Corrected domain balance:

- algebra: `72` records = `18` families
- blocksworld: `72` records = `18` families
- graph_path: `64` records = `16` families

Corrected acceptance analysis:

- `strict = 2 / 54`
- `ignore_semantic_only = 52 / 54`
- `surface_or_mixed_only = 52 / 54`

Interpretation:

- the earlier `44 / 54`, `176` export was a first-pass read under an over-broad acceptance classifier
- after correcting that classifier, the dominant `blocksworld` failure cluster largely disappears
- the remaining gap is now only `2` groups short of full `54 / 54`
- benchmark-v3 mid-scale validity is therefore materially stronger than the first raw export suggested

Decision:

- treat `artifacts/benchmark_v3/benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis_summary.json` as the current authoritative mid-scale export result
- treat `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl` as the current authoritative exported dataset
- keep the older `...accept_export_ignore_semantic_summary.json` only as the raw build-pass checkpoint that produced the candidate pool and review log

## 2026-03-12 Benchmark Default Replacement

Status: the project default benchmark pointer now switches from the legacy `benchmark1` synthetic set to the benchmark-v3 mid-scale export.

Code change:

- added `src/civic_prm/default_paths.py`
- switched the main benchmark-entry scripts to default to:
  - `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

Updated default-entry scripts:

- `scripts/run_artifact_audit.py`
- `scripts/run_qwen_pilot.py`
- `scripts/run_api_judge_pilot.py`
- `scripts/run_week2_baselines.py`
- `scripts/build_blind_audit_packet.py`
- `scripts/build_naturalized_slice.py`
- `scripts/build_model_generated_slice.py`
- `scripts/run_natural_transfer.py`
- `scripts/run_generated_answer_swap_transfer.py`
- `scripts/run_repair_transfer.py`
- `scripts/run_dual_head_transfer.py`
- `scripts/run_scanned_dual_head_transfer.py`
- `scripts/run_week5_robustness.py`
- `scripts/run_week6_reproduction.py`

Interpretation:

- this is a **default entrypoint replacement**, not a silent rerun of historical results
- older Week 1-6 artifacts remain tied to the datasets they were originally run on
- future runs that rely on default benchmark inputs will now start from the benchmark-v3 mid-scale export unless the caller overrides `--dataset` or `--train-dataset`

Decision:

- treat legacy `craft_core_week1.jsonl` and `craft_core_hard.jsonl` as reproduction/comparison datasets
- treat the benchmark-v3 mid-scale export as the new default benchmark for forward work

## 2026-03-12 First Mainline Run On Benchmark-V3 Default

Status: first benchmark-facing mainline run completed on the new benchmark-v3 default dataset.

Dataset:

- `data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl`

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/audit/artifact_audit_benchmark_v3_midset.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_blind_audit_packet.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/audit/blind_audit_benchmark_v3_midset.md \
  --answer-key-output artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --response-form-output artifacts/audit/blind_audit_benchmark_v3_midset_form.csv \
  --summary-output artifacts/audit/blind_audit_benchmark_v3_midset_summary.json \
  --sample-quartets 9 \
  --seed 17'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset'
```

Compatibility fix applied before the baseline rerun:

- `src/civic_prm/splits.py` now accepts benchmark-v3 verbalizer ids like `alg_v1_b3` and still maps them back to slot `v1`

Artifacts:

- `artifacts/audit/artifact_audit_benchmark_v3_midset.json`
- `artifacts/audit/blind_audit_benchmark_v3_midset.md`
- `artifacts/audit/blind_audit_benchmark_v3_midset_summary.json`
- `artifacts/baselines/week2_baselines_benchmark_v3_midset.json`

Artifact audit:

- `num_records = 208`
- `validity_style_auroc = 0.6098`
- `length_only_validity_auroc = 0.5479`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Blind-audit packet summary:

- `num_items = 9`
- `domains = algebra 3 / blocksworld 3 / graph_path 3`
- `num_eligible_quartets = 18`
- `num_incomplete_quartets_skipped = 0`

Week 2 baselines, quartet protocol:

- `step_only_bce`: `ordinary_auroc = 0.9228`, `amcd = 0.8333`, `ass_total = 0.0427`
- `visible_bce`: `ordinary_auroc = 0.9691`, `amcd = 0.8889`, `ass_total = 0.1236`
- `masked_bce`: `ordinary_auroc = 0.9537`, `amcd = 0.8889`, `ass_total = 0.1275`
- `pairwise_visible`: `ordinary_auroc = 0.9259`, `amcd = 0.8889`, `ass_total = 0.0681`

Week 2 baselines, verbalizer-holdout protocol:

- `step_only_bce`: `ordinary_auroc = 0.7778`, `amcd = 0.8889`, `ass_total = 0.0156`
- `visible_bce`: `ordinary_auroc = 0.8889`, `amcd = 0.9444`, `ass_total = 0.1206`
- `masked_bce`: `ordinary_auroc = 0.8241`, `amcd = 0.8333`, `ass_total = 0.0774`
- `pairwise_visible`: `ordinary_auroc = 0.7963`, `amcd = 0.8889`, `ass_total = 0.0706`

Interpretation:

- benchmark-v3 runs cleanly through the main benchmark-facing entrypoints; the replacement is now operational rather than only documentary
- the new benchmark does not show a shallow-style or length-only audit failure
- on this accepted mid-scale set, graph_path is still the weakest domain, while blocksworld is no longer the dominant failure slice
- the Week 2 picture shifts relative to the old hard benchmark: visible and masked BCE are now much closer, and `step_only_bce` is markedly stronger than before
- this means benchmark-v3 replacement is not just a file-path change; it changes the base benchmark behavior and therefore should be treated as a new evaluation regime, not silently merged into old tables

## 2026-03-12 First Week 4 Reranker Run On Benchmark-V3 Default

Status: first `Qwen3-Reranker-8B` run completed on the benchmark-v3 mid-scale default dataset.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week4_reranker.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --batch-size 2 \
  --max-length 2048'
```

Artifact:

- `artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json`

Visible view:

- `ordinary_accuracy = 0.4952`
- `ordinary_auroc = 0.5524`
- `amcd = 0.6058`
- `ass_total = 0.1344`
- `selection_gain_at4 = 0.3889`
- `exploitability_rate = 0.1111`
- `ece = 0.35`

Masked view:

- `ordinary_accuracy = 0.5048`
- `ordinary_auroc = 0.5589`
- `amcd = 0.6731`
- `ass_total = 0.0438`
- `selection_gain_at4 = 0.3889`
- `exploitability_rate = 0.1111`
- `ece = 0.3733`

Interpretation:

- the masked reranker still dominates the visible reranker on the verifier-facing metrics that matter here: better `ordinary_auroc`, better `amcd`, and much lower `ass_total`
- unlike the old full-hybrid generated regime, utility does not separate on this benchmark-v3 mid-scale set; both views land on the same `selection_gain_at4` and `exploitability_rate`
- benchmark-v3 therefore seems to be a cleaner process benchmark than a deployment-style exploit benchmark: it still exposes answer sensitivity, but it does not automatically turn that into a utility edge for the visible reranker
- the new default benchmark and the old full-hybrid OOD slice should not be merged into one headline number, because they stress different properties

## 2026-03-12 Benchmark-V3 Same-Dataset Robustness Summary

Status: benchmark-v3-specific robustness and model-comparison summary completed on the new default regime.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_benchmark_v3_robustness.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --baseline-artifact artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
  --reranker-artifact artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --output artifacts/benchmark_v3/benchmark_v3_robustness_summary.json'
```

Artifact:

- `artifacts/benchmark_v3/benchmark_v3_robustness_summary.json`

Same-dataset model summary:

- `reranker8_visible`: `ordinary_auroc = 0.5524`, `amcd = 0.6058`, `ass_total = 0.1344`, `selection_gain_at4 = 0.3889`, `exploitability_rate = 0.1111`
- `reranker8_masked`: `0.5589`, `0.6731`, `0.0438`, `0.3889`, `0.1111`
- `step_only_bce`: `0.9228`, `0.8333`, `0.0427`, `0.5`, `0.0`
- `visible_bce`: `0.9691`, `0.8889`, `0.1236`, `0.5`, `0.0`
- `masked_bce`: `0.9537`, `0.8889`, `0.1275`, `0.5`, `0.0`
- `pairwise_visible`: `0.9259`, `0.8889`, `0.0681`, `0.5`, `0.0`

Worst-group slices:

- reranker8_masked by domain:
  - algebra: `ordinary_auroc = 0.5802`, `amcd = 0.5556`, `ass_total = 0.065`
  - blocksworld: `0.7222`, `0.8333`, `0.0`
  - graph_path: `0.5977`, `0.625`, `0.0692`
- reranker8_visible by domain:
  - algebra: `0.5579`, `0.4444`, `0.2159`
  - blocksworld: `0.5602`, `0.7222`, `0.121`
  - graph_path: `0.6201`, `0.6562`, `0.0577`
- frozen-head baselines now show a different weak slice from the old hard benchmark:
  - graph_path is the main weak group for `step_only_bce`, `visible_bce`, `masked_bce`, and `pairwise_visible`

Same-dataset attacker transfer:

- mixed visible-attacker ensemble on `reranker8_masked`:
  - `pairwise_attack_win_rate = 0.1324`
  - `quartet_top_attack_rate = 0.1176`
  - attacked-quartet `selection_gain_at4 = 0.4091`
  - attacked-quartet `exploitability_rate = 0.0909`
- mixed visible-attacker ensemble on `reranker8_visible`:
  - `pairwise_attack_win_rate = 0.1618`
  - `quartet_top_attack_rate = 0.1765`
  - attacked-quartet `selection_gain_at4 = 0.4091`
  - attacked-quartet `exploitability_rate = 0.0909`

Interpretation:

- benchmark-v3 does not preserve the same model ordering as the old full-hybrid generated regime
- on this benchmark, the reranker is still better masked than visible on process-facing metrics, but its utility edge over visible disappears
- the frozen-head baselines are unusually strong here and often reach perfect quartet selection, which suggests benchmark-v3 mid-scale is a cleaner process benchmark than a deployment-style exploit benchmark
- the main weak slice is now graph_path rather than blocksworld, and the visible reranker remains much more answer-sensitive on algebra and blocksworld

## 2026-03-12 Blind-Audit Scoring Pipeline

Status: blind-audit return handling is now automated for benchmark-v3 and legacy packets.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/score_blind_audit.py \
  --answer-key artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --responses reviewer_a.csv reviewer_b.csv \
  --output artifacts/audit/blind_audit_benchmark_v3_midset_scored.json \
  --markdown-output artifacts/audit/blind_audit_benchmark_v3_midset_scored.md'
```

New code:

- `src/civic_prm/blind_audit.py`
- `scripts/score_blind_audit.py`

Reported outputs:

- per-reviewer label counts and domain slices
- pooled invalid-trace / valid-trace / both / neither rates
- invalid-minus-valid flag-rate gap
- pairwise exact label agreement across reviewers

Minimal verification:

- `python -m py_compile src/civic_prm/blind_audit.py scripts/score_blind_audit.py`
- synthetic dry-run on the benchmark-v3 packet:
  - reviewer A always flags the invalid trace
  - reviewer B always answers `Neither`
  - pooled summary returns `invalid_trace_flag_rate = 0.5`, `neither_rate = 0.5`, and pairwise agreement `0.0`, as expected

Interpretation:

- the remaining blind-audit blocker is now reviewer return, not local scoring infrastructure
- benchmark-v3 can now be sent out and rescored deterministically as soon as reviewer CSVs come back

## 2026-03-15 Proxy Blind Audit On Benchmark-V3 Midset

Status: completed an internal proxy blind audit using `3` independent subagent reviewers on the current benchmark-v3 packet.

Artifacts:

- `artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_a.csv`
- `artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_b.csv`
- `artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_c.csv`
- `artifacts/audit/proxy_reviews/benchv3_proxy_blind_audit_scored.json`
- `artifacts/audit/proxy_reviews/benchv3_proxy_blind_audit_scored.md`
- `artifacts/audit/proxy_reviews/benchv3_proxy_blind_audit_interpretation.md`

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/score_blind_audit.py \
  --answer-key artifacts/audit/blind_audit_benchmark_v3_midset_key.json \
  --responses \
    artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_a.csv \
    artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_b.csv \
    artifacts/audit/proxy_reviews/benchv3_proxy_reviewer_c.csv \
  --output artifacts/audit/proxy_reviews/benchv3_proxy_blind_audit_scored.json \
  --markdown-output artifacts/audit/proxy_reviews/benchv3_proxy_blind_audit_scored.md'
```

Pooled summary:

- reviewers: `3`
- items per reviewer: `9`
- pooled invalid-trace flag rate: `0.7778`
- pooled valid-trace flag rate: `0.1111`
- pooled both rate: `0.0741`
- pooled neither rate: `0.037`
- invalid-minus-valid flag-rate gap: `0.6667`

By domain:

- algebra:
  - invalid-trace flag rate `1.0`
  - valid-trace flag rate `0.0`
- blocksworld:
  - invalid-trace flag rate `0.6667`
  - valid-trace flag rate `0.3333`
- graph_path:
  - invalid-trace flag rate `0.6667`
  - both rate `0.2222`
  - neither rate `0.1111`

Agreement:

- reviewer A vs B: `0.5556`
- reviewer A vs C: `0.5556`
- reviewer B vs C: `1.0`

Interpretation:

- this is still not the proposal's external human blind audit
- the proxy reviewers still find benchmark-v3 easy to flag overall
- algebra remains the clearest high-signal failure slice
- graph_path remains high-signal but now with some `Both` / `Neither` ambiguity
- blocksworld is mixed enough that some proxy reviewers blame the valid trace for looking more templated
- operationally, the proxy audit reinforces the need for external human review rather than replacing it

## 2026-03-12 Writing And Handoff Closure

Status: local handoff materials are now closed enough for external review and submission polish.

Updated writing/handoff files:

- `history/paper_draft.md`
- `history/blind_audit_handoff.md`
- `history/submission_checklist.md`

What changed:

- the paper draft now has an explicit contributions subsection and an explicit two-benchmark subsection
- blind-audit execution is documented end-to-end: what to send, what not to send, how to score returned CSVs, and how to interpret the result under the proposal-aligned criterion
- the remaining local/open split is now explicit: local package is ready; external blind-audit return is still pending

## 2026-03-15 Benchmark-V3 Robustness Reproduction Confirmation

Status: benchmark-v3 same-dataset robustness was rerun in the `infer` environment and reproduced the existing summary without code changes to the robustness pipeline.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_benchmark_v3_robustness.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --baseline-artifact artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
  --reranker-artifact artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --output artifacts/benchmark_v3/benchmark_v3_robustness_summary.json'
```

Artifact:

- `artifacts/benchmark_v3/benchmark_v3_robustness_summary.json`

Confirmed benchmark-v3 summary:

- `reranker8_visible`: `ordinary_auroc = 0.5524`, `amcd = 0.6058`, `ass_total = 0.1344`, `selection_gain_at4 = 0.3889`, `exploitability_rate = 0.1111`
- `reranker8_masked`: `0.5589`, `0.6731`, `0.0438`, `0.3889`, `0.1111`
- `step_only_bce`: `0.9228`, `0.8333`, `0.0427`, `0.5`, `0.0`
- `visible_bce`: `0.9691`, `0.8889`, `0.1236`, `0.5`, `0.0`
- `masked_bce`: `0.9537`, `0.8889`, `0.1275`, `0.5`, `0.0`
- `pairwise_visible`: `0.9259`, `0.8889`, `0.0681`, `0.5`, `0.0`

Worst-group and attacker-transfer read:

- for `reranker8_masked`, the weaker benchmark-v3 domains are now algebra and graph path:
  - algebra: `amcd = 0.5556`, `ass_total = 0.065`, `exploitability_rate = 0.1667`
  - graph_path: `amcd = 0.625`, `ass_total = 0.0692`, `exploitability_rate = 0.1667`
- blocksworld is no longer the dominant weak slice for the masked reranker on benchmark-v3:
  - `amcd = 0.8333`, `ass_total = 0.0`
- mixed visible-attacker transfer remains slightly worse for `reranker8_visible` than for `reranker8_masked`:
  - masked target: `pairwise_attack_win_rate = 0.1324`, attacked-quartet `exploitability_rate = 0.0909`
  - visible target: `0.1618`, `0.0909`

Interpretation:

- the benchmark-v3 robustness result is reproducible under the current default benchmark setup
- the benchmark-v3 regime still preserves a visible-vs-masked faithfulness gap
- it still does not amplify that gap into a deployment-style utility gap
- benchmark-v3 should therefore continue to be treated as the cleaner audit benchmark, not as a replacement for the deployment-oriented naturalized full-hybrid slice

## 2026-03-15 Benchmark-V3 Reproduction And CI Summary

Status: benchmark-v3 now has a minimal Week-6-style stability layer: `3` frozen-head seeds plus paired bootstrap on the same reranker rows.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset_seed23.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset \
  --seed 23'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_week2_baselines.py \
  --dataset data/generated/craft_core_benchmark_v3_midset_k6_v3_accept_export_ignore_semantic_v2_from_analysis.jsonl \
  --output artifacts/baselines/week2_baselines_benchmark_v3_midset_seed31.json \
  --feature-cache-dir artifacts/features_benchmark_v3_midset \
  --seed 31'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/analyze_benchmark_v3_reproduction.py \
  --baseline-artifacts \
    artifacts/baselines/week2_baselines_benchmark_v3_midset.json \
    artifacts/baselines/week2_baselines_benchmark_v3_midset_seed23.json \
    artifacts/baselines/week2_baselines_benchmark_v3_midset_seed31.json \
  --reranker-artifact artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json \
  --output artifacts/benchmark_v3/benchmark_v3_reproduction_summary.json'
```

Artifacts:

- `artifacts/baselines/week2_baselines_benchmark_v3_midset_seed23.json`
- `artifacts/baselines/week2_baselines_benchmark_v3_midset_seed31.json`
- `artifacts/benchmark_v3/benchmark_v3_reproduction_summary.json`

Quartet-protocol seed means:

- `step_only_bce`: `ordinary_auroc = 0.9233`, `amcd = 0.8842`, `ass_total = 0.0891`
- `visible_bce`: `0.9161`, `0.9028`, `0.1389`
- `masked_bce`: `0.9302`, `0.9213`, `0.1055`
- `pairwise_visible`: `0.8659`, `0.9028`, `0.0736`

Quartet-protocol seed standard deviations:

- `step_only_bce`: `ordinary_auroc std = 0.0524`, `amcd std = 0.0458`, `ass_total std = 0.035`
- `visible_bce`: `0.0816`, `0.03`, `0.0433`
- `masked_bce`: `0.054`, `0.0559`, `0.019`
- `pairwise_visible`: `0.0435`, `0.03`, `0.023`

Verbalizer-holdout seed means:

- `step_only_bce`: `ordinary_auroc = 0.8303`, `amcd = 0.9259`, `ass_total = 0.0665`
- `visible_bce`: `0.8673`, `0.8518`, `0.1148`
- `masked_bce`: `0.8287`, `0.8333`, `0.0894`
- `pairwise_visible`: `0.821`, `0.8704`, `0.0781`

Paired bootstrap on the benchmark-v3 reranker rows (`masked - visible`):

- `ordinary_auroc`: diff `+0.0065`, CI `[-0.0164, 0.0428]`
- `amcd`: diff `+0.0673`, CI `[0.0, 0.1406]`
- `ass_total`: diff `-0.0906`, CI `[-0.1177, -0.0641]`
- `selection_gain_at4`: diff `0.0`, CI `[-0.1, 0.1]`
- `exploitability_rate`: diff `0.0`, CI `[-0.1, 0.1]`

Interpretation:

- benchmark-v3 now has a cleaner-benchmark analogue of the Week 6 stability story, even though it is not the same train/eval regime as the naturalized full-hybrid main slice
- frozen-head baselines remain strong across seeds, but they do not overturn the benchmark-v3 deployment readout
- the masked reranker keeps a stable `ASS_total` advantage and a smaller but still positive `AMCD` edge
- utility remains tied, which is further evidence that benchmark-v3 is primarily a process-faithfulness benchmark

## 2026-03-16 External Step-Level Dataset Pivot

Status: external-source dataset import layer completed; no default benchmark flip yet.

Reproducible commands:

```bash
PYTHONPATH=src python scripts/import_external_dataset.py --dataset processbench --split all
```

```bash
PYTHONPATH=src python scripts/import_external_dataset.py --dataset prm800k --split train --limit 32 --streaming
```

New code:

- `src/civic_prm/external_datasets.py`
- `scripts/import_external_dataset.py`

Validation:

- `python -m py_compile src/civic_prm/schema.py src/civic_prm/external_datasets.py scripts/import_external_dataset.py`

Outputs:

- `data/external/processbench_all.jsonl`
- `artifacts/external_datasets/processbench_all_summary.json`
- `data/external/prm800k_train_sample32.jsonl`
- `artifacts/external_datasets/prm800k_train_sample32_summary.json`

ProcessBench import summary:

- `3400` rows total
- splits:
  - `gsm8k = 400`
  - `math = 1000`
  - `olympiadbench = 1000`
  - `omnimath = 1000`
- `avg_num_steps = 7.5579`
- `final_answer_correct = 1700 true / 1700 false`
- raw labels preserved from the source dataset; the current adapter treats non-negative labels as the provided first-incorrect-step index hint and keeps `-1` as the “no incorrect step” marker

PRM800K adapter validation:

- currently wired through the accessible Hub mirror `tasksource/PRM800K`
- streamed sample size: `32`
- `avg_num_steps = 10.4688`
- `max_num_steps = 36`
- chosen step texts, ratings, and flags are preserved in metadata
- `final_answer_correct` is intentionally left unset in the current adapter because the import layer is preserving source supervision rather than guessing correctness from the final text

Interpretation:

- The repo no longer depends exclusively on self-generated source problems for future benchmark work.
- `ProcessBench` is now the first ready external evaluation anchor.
- `PRM800K` now has a working adapter path and can be expanded from sample import to larger supervised-use imports later.
- This does **not** silently replace the current default benchmark yet; it starts the pivot away from self-generated source quartets as the only main benchmark source.

## 2026-03-16 ProcessBench Whole-Trace Benchmark Pivot

Status: first external-source `ProcessBench` benchmark line completed.

Reproducible commands:

```bash
PYTHONPATH=src python scripts/build_processbench_benchmark.py --split all
```

```bash
PYTHONPATH=src python scripts/run_artifact_audit.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --output artifacts/external_datasets/processbench_eval_all_artifact_audit.json
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
export ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3 && \
export ARK_MODEL_ENDPOINT=ep-20251213141929-gk2jb && \
export ARK_API_KEY=8da5e4ba-59ad-47af-8f87-005fd1d1641b && \
PYTHONPATH=src python scripts/run_processbench_api_judge.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 8 \
  --seed 17 \
  --cache-output artifacts/external_datasets/processbench_api_judge_v3_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_api_judge_v3_summary.json'
```

New code:

- `src/civic_prm/processbench.py`
- `src/civic_prm/processbench_eval.py`
- `scripts/build_processbench_benchmark.py`
- `scripts/run_processbench_api_judge.py`

Normalized benchmark outputs:

- `data/external/processbench_eval_all.jsonl`
- `artifacts/external_datasets/processbench_eval_all_summary.json`
- `artifacts/external_datasets/processbench_eval_all_artifact_audit.json`
- `artifacts/external_datasets/processbench_api_judge_v3_rows.jsonl`
- `artifacts/external_datasets/processbench_api_judge_v3_summary.json`

Normalization details:

- source dataset: `Qwen/ProcessBench`
- total rows: `3400`
- external domains / splits:
  - `gsm8k = 400`
  - `math = 1000`
  - `olympiadbench = 1000`
  - `omnimath = 1000`
- `is_valid_process = (label == -1)`
- `audited_locus = first incorrect step index` when `label >= 0`, otherwise the last step
- answer masking uses a brace-safe `\\boxed{...}` masker plus sentence-end answer masking for plain declaratives

ProcessBench benchmark summary:

- `num_records = 3400`
- `is_valid_process = 1179 true / 2221 false`
- `answer_is_correct = 1700 true / 1700 false`
- `avg_num_steps = 7.5579`
- `avg_audited_locus = 3.8671`

Artifact audit on the normalized whole-trace benchmark:

- `validity_style_accuracy = 0.6461`
- `validity_style_auroc = 0.711`
- `length_only_validity_accuracy = 0.6451`
- `length_only_validity_auroc = 0.6801`
- `flag_high_style_leakage = false`
- `flag_high_length_leakage = false`

Interpretation:

- `ProcessBench` is not artifact-clean in the stronger sense, but it does not immediately trip the current repo’s hard style/length leakage flags.
- The remaining style signal is plausible for a real external dataset and should be read separately from the synthetic benchmark acceptance story.

Balanced API-judge pilot (`32` examples = `8` per domain):

- sample composition:
  - `valid_correct = 8`
  - `invalid_correct = 12`
  - `invalid_wrong = 12`
- visible:
  - `ordinary_accuracy = 0.7812`
  - `ordinary_auroc = 0.7708`
  - `mean_score_by_process_variant.valid = 0.75`
  - `mean_score_by_process_variant.invalid = 0.2083`
  - `invalid_answer_gap = 0.0833`
- masked:
  - `ordinary_accuracy = 0.75`
  - `ordinary_auroc = 0.75`
  - `mean_score_by_process_variant.valid = 0.75`
  - `mean_score_by_process_variant.invalid = 0.25`
  - `invalid_answer_gap = 0.1667`
- usage:
  - `64` calls
  - `44509` total tokens

Interpretation:

- The first `ProcessBench` pivot line is operational: visible and masked scoring both run on an external-source benchmark without relying on self-generated quartets.
- This line should currently be read as a whole-trace benchmark, not as an `AMCD/ASS` benchmark.
- On the current balanced sample, visible slightly beats masked on ordinary AUROC, but the masked condition does not show lower invalid-answer sensitivity; this suggests the answer-surface masking and evaluation design for external-source datasets still need a second pass before strong deployment claims are made from `ProcessBench`.

## 2026-03-16 ProcessBench Frozen-Head Trace + Prefix Baselines

Status: first external-source frozen-head baseline package completed.

Reproducible commands:

```bash
PYTHONPATH=src python scripts/build_processbench_prefix_benchmark.py
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_frozen_baselines.py \
  --trace-dataset data/external/processbench_eval_all.jsonl \
  --prefix-dataset data/external/processbench_prefix_eval_all.jsonl \
  --prefix-source-limit-per-domain 200 \
  --output artifacts/external_datasets/processbench_frozen_baselines.json'
```

New outputs:

- `data/external/processbench_prefix_eval_all.jsonl`
- `artifacts/external_datasets/processbench_prefix_eval_all_summary.json`
- `artifacts/external_datasets/processbench_frozen_baselines.json`

Prefix benchmark summary:

- `25697` prefix records from `3400` source traces
- domains:
  - `gsm8k = 2082`
  - `math = 6505`
  - `olympiadbench = 8819`
  - `omnimath = 8291`
- `is_valid_process = 14327 true / 11370 false`
- `avg_prefix_length = 5.2967`

Frozen-head setup:

- encoder: `Qwen3-1.7B`
- views:
  - `visible`
  - `masked`
  - `step_only`
- trace benchmark: full normalized `ProcessBench`
- prefix benchmark: controlled subset with `200` source traces per domain
- split shape:
  - trace: `2380 train / 510 val / 510 test`
  - prefix: `4003 train / 827 val / 891 test`

Trace-level metrics:

- `visible`:
  - `ordinary_accuracy = 0.7059`
  - `ordinary_auroc = 0.7863`
  - `invalid_answer_gap = -0.1468`
- `masked`:
  - `ordinary_accuracy = 0.7157`
  - `ordinary_auroc = 0.8075`
  - `invalid_answer_gap = -0.0961`
- `step_only`:
  - `ordinary_accuracy = 0.7784`
  - `ordinary_auroc = 0.8759`
  - `invalid_answer_gap = -0.0495`

Prefix-level metrics:

- `visible`:
  - `ordinary_accuracy = 0.6229`
  - `ordinary_auroc = 0.6759`
  - `boundary_drop_mean = 0.2157`
- `masked`:
  - `ordinary_accuracy = 0.6386`
  - `ordinary_auroc = 0.6813`
  - `boundary_drop_mean = 0.2058`
- `step_only`:
  - `ordinary_accuracy = 0.6375`
  - `ordinary_auroc = 0.6918`
  - `boundary_drop_mean = 0.2143`

Interpretation:

- The external-source benchmark now has two concrete tasks: `PB-Trace` and `PB-Prefix`.
- On whole traces, the current frozen-head ordering is `step_only > masked > visible`, which is directionally consistent with answer-visible shortcut pressure on external data as well.
- On prefixes, all three views show a real positive boundary drop around the first incorrect step, so the new benchmark is detecting error-onset sensitivity without requiring synthetic quartets.
- The prefix task is currently a controlled first pass rather than a full-scale benchmark run; the benchmark object itself is complete, but the first frozen baseline package uses a budgeted subset for the prefix split.

## 2026-03-16 ProcessBench Whole-Trace Reranker

Status: first stronger-model external-source reranker line completed.

Reproducible command:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_reranker.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --model-root /cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B \
  --output artifacts/external_datasets/processbench_reranker_8b.json \
  --batch-size 2 \
  --max-length 2048 \
  --seed 17'
```

New code:

- `scripts/run_processbench_reranker.py`

New outputs:

- `artifacts/external_datasets/processbench_reranker_8b.json`
- `artifacts/external_datasets/processbench_reranker_8b_rows.jsonl`

Setup:

- dataset: `data/external/processbench_eval_all.jsonl`
- model: `Qwen3-Reranker-8B`
- split policy: same grouped `train/val/test` shape as the frozen `PB-Trace` baselines
- scored splits: `val + test`
- final reported split: `test` (`510` traces)
- row count written: `2040` (`visible + masked` over `val + test`)

Visible:

- `ordinary_accuracy = 0.349`
- `ordinary_auroc = 0.7337`
- `invalid_answer_gap = 0.0003`
- calibration:
  - `brier = 0.525`
  - `ece = 0.566`
  - `nll = 1.7002`
- threshold analysis:
  - selected threshold on `val = 0.9609`
  - `val_accuracy = 0.7137`
  - `test_accuracy_at_selected_threshold = 0.698`
  - `test_accuracy_at_default_threshold = 0.349`

Masked:

- `ordinary_accuracy = 0.3529`
- `ordinary_auroc = 0.7229`
- `invalid_answer_gap = -0.0006`
- calibration:
  - `brier = 0.5101`
  - `ece = 0.5525`
  - `nll = 1.5912`
- threshold analysis:
  - selected threshold on `val = 0.957`
  - `val_accuracy = 0.702`
  - `test_accuracy_at_selected_threshold = 0.7`
  - `test_accuracy_at_default_threshold = 0.3529`

Interpretation:

- The stronger-model line is now operational on an external-source benchmark without reverting to self-generated quartets.
- On `ProcessBench`, the current reranker is much more answer-balanced than the first API-judge pilot: both views have near-zero `invalid_answer_gap`.
- The earlier `~0.35` test accuracy was mostly a calibration artifact rather than proof that the reranker cannot rank traces. With a threshold selected on the grouped validation split, test accuracy returns to about `0.70` in both views.
- The ranking story is still only moderate: AUROC remains in the low `0.7`s, and on the current `PB-Trace` test split `Qwen3-Reranker-8B` still does **not** beat the strongest frozen `step_only` baseline (`ordinary_auroc = 0.8759`).
- So the corrected readout is: the stronger-model line is now connected and the big accuracy collapse was mostly miscalibration, but the current reranker is still not the best external-source verifier in this regime.

## 2026-03-16 ProcessBench Main Table Aggregation

Status: first paper-facing external-source main table completed.

Reproducible command:

```bash
PYTHONPATH=src python scripts/analyze_processbench_main_table.py
```

New code:

- `scripts/analyze_processbench_main_table.py`

New outputs:

- `artifacts/external_datasets/processbench_main_table.json`
- `artifacts/external_datasets/processbench_main_table.md`

`PB-Trace` main table:

| model | acc@0.5 | acc@val-thr | auroc | invalid_answer_gap |
|---|---:|---:|---:|---:|
| `frozen_visible` | `0.7059` | `-` | `0.7863` | `-0.1468` |
| `frozen_masked` | `0.7157` | `-` | `0.8075` | `-0.0961` |
| `frozen_step_only` | `0.7784` | `-` | `0.8759` | `-0.0495` |
| `reranker8_visible` | `0.3490` | `0.6980` | `0.7337` | `0.0003` |
| `reranker8_masked` | `0.3529` | `0.7000` | `0.7229` | `-0.0006` |

`PB-Prefix` main table:

| model | ordinary_accuracy | ordinary_auroc | boundary_drop_mean | invalid_answer_gap |
|---|---:|---:|---:|---:|
| `frozen_visible` | `0.6229` | `0.6759` | `0.2157` | `-0.0081` |
| `frozen_masked` | `0.6386` | `0.6813` | `0.2058` | `-0.0885` |
| `frozen_step_only` | `0.6375` | `0.6918` | `0.2143` | `-0.0574` |

Takeaways:

- Best `PB-Trace` model by AUROC is `frozen_step_only` (`0.8759`).
- Best `PB-Prefix` model by AUROC is also `frozen_step_only` (`0.6918`).
- The best reranker by AUROC is `reranker8_visible`, but it still trails all three frozen trace baselines on `PB-Trace`.
- External-source `ProcessBench` therefore does not currently support a stronger-model deployment headline; it supports a cleaner benchmark pivot and a clearer diagnosis of where the reranker is failing.

## 2026-03-17 ProcessBench External Answer-Swap Pilot

Status: first external-source `ASS` pilot completed on `ProcessBench` without reverting to self-generated quartets.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_processbench_answer_swap_pilot.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 8 \
  --seed 17 \
  --generation-cache-output artifacts/external_datasets/processbench_answer_swap_generation_rows.jsonl \
  --output data/external/processbench_answer_swap_pilot.jsonl \
  --summary-output artifacts/external_datasets/processbench_answer_swap_pilot_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_answer_swap_api_judge.py \
  --dataset data/external/processbench_answer_swap_pilot.jsonl \
  --cache-output artifacts/external_datasets/processbench_answer_swap_api_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_answer_swap_api_summary.json'
```

New code:

- `src/civic_prm/processbench_counterfactuals.py`
- `scripts/build_processbench_answer_swap_pilot.py`
- `scripts/run_processbench_answer_swap_api_judge.py`

New outputs:

- `data/external/processbench_answer_swap_pilot.jsonl`
- `artifacts/external_datasets/processbench_answer_swap_generation_rows.jsonl`
- `artifacts/external_datasets/processbench_answer_swap_pilot_summary.json`
- `artifacts/external_datasets/processbench_answer_swap_api_rows.jsonl`
- `artifacts/external_datasets/processbench_answer_swap_api_summary.json`

Pilot construction:

- selected sources: `32`
- successful observed/swapped pairs: `31`
- failed sources: `1`
- final paired dataset size: `62` records
- domain mix:
  - `gsm8k = 16`
  - `math = 14`
  - `olympiadbench = 16`
  - `omnimath = 16`
- source buckets:
  - `valid = 14`
  - `invalid = 48`
  - `source answer correct = 19`
  - `source answer wrong = 12`
- generation usage:
  - `prompt_tokens = 9528`
  - `completion_tokens = 569`
  - `total_tokens = 10097`

External-source `ASS` summary:

- visible:
  - `num_pairs = 31`
  - `mean_abs_delta = 0.3226`
  - `mean_signed_delta = -0.2581`
  - `mean_observed_score = 0.3548`
  - `mean_swapped_score = 0.0968`
- masked:
  - `num_pairs = 31`
  - `mean_abs_delta = 0.0645`
  - `mean_signed_delta = 0.0`
  - `mean_observed_score = 0.3548`
  - `mean_swapped_score = 0.3548`
- `ass_gap_visible_minus_masked = 0.2581`
- judge usage:
  - `prompt_tokens = 88261`
  - `completion_tokens = 1740`
  - `total_tokens = 90001`
  - `num_calls = 124`

Breakdowns:

- visible `mean_abs_delta` by domain:
  - `gsm8k = 0.5000`
  - `math = 0.2857`
  - `olympiadbench = 0.2500`
  - `omnimath = 0.2500`
- visible `mean_abs_delta` by process variant:
  - `valid = 0.7143`
  - `invalid = 0.2083`
- visible `mean_abs_delta` by source answer correctness:
  - `correct = 0.4737`
  - `wrong = 0.0833`

Interpretation:

- This is the first external-source `ASS` readout built from real step-level traces rather than self-generated quartets.
- The visible API judge is clearly answer-sensitive on `ProcessBench`: answer-only swaps move the visible score by about `0.32` on average.
- The masked view collapses to a much smaller residual delta (`0.0645`), which is best read as a judge noise floor rather than substantive answer sensitivity because the masked prompts are input-identical within each pair.
- The effect is strongest on source traces whose original final answer is correct (`0.4737`) and much weaker on traces that were already wrong-answer examples (`0.0833`).
- External-source `ASS` is therefore feasible without synthetic source problems: `ProcessBench` can already support answer-swap stress even before any external-source `AMCD` augmentation exists.

## 2026-03-17 ProcessBench External Local-Pair Repair Pilot

Status: first external-source local repair-pair pilot completed on a small `ProcessBench` subset. This is a benchmark-construction pilot, not a fully closed external `AMCD` benchmark.

Reproducible commands:

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/build_processbench_repair_pilot.py \
  --dataset data/external/processbench_eval_all.jsonl \
  --per-domain 2 \
  --seed 17 \
  --min-audited-locus 1 \
  --generation-cache-output artifacts/external_datasets/processbench_repair_pd2_v3_generation_rows.jsonl \
  --output data/external/processbench_repair_pd2_v3_partial_pilot.jsonl \
  --summary-output artifacts/external_datasets/processbench_repair_pd2_v3_partial_pilot_summary.json'
```

```bash
bash -lc 'source /root/miniconda3/etc/profile.d/conda.sh && conda activate infer && \
PYTHONPATH=src python scripts/run_processbench_repair_api_judge.py \
  --dataset data/external/processbench_repair_pd2_v3_partial_pilot.jsonl \
  --cache-output artifacts/external_datasets/processbench_repair_pd2_v3_api_rows.jsonl \
  --summary-output artifacts/external_datasets/processbench_repair_pd2_v3_api_summary.json'
```

New code:

- `scripts/build_processbench_repair_pilot.py`
- `scripts/run_processbench_repair_api_judge.py`
- `src/civic_prm/processbench_counterfactuals.py`

New outputs:

- `data/external/processbench_repair_pd2_v3_partial_pilot.jsonl`
- `artifacts/external_datasets/processbench_repair_pd2_v3_partial_pilot_summary.json`
- `artifacts/external_datasets/processbench_repair_pd2_v3_generation_rows.jsonl`
- `artifacts/external_datasets/processbench_repair_pd2_v3_api_rows.jsonl`
- `artifacts/external_datasets/processbench_repair_pd2_v3_api_summary.json`

Construction summary:

- target selection: `per_domain = 2`, `min_audited_locus = 1`
- selected sources: `8`
- successful repair pairs from cache: `8`
- failed / missing pairs: `0`
- current partial pilot domains:
  - `gsm8k = 4 records`
  - `math = 4 records`
  - `olympiadbench = 4 records`
  - `omnimath = 4 records`
- generation usage on successful repairs:
  - `prompt_tokens = 12350`
  - `completion_tokens = 4189`
  - `total_tokens = 16539`

Local pair discrimination summary:

- visible:
  - `num_pairs = 8`
  - `local_amcd = 0.375`
  - `mean_signed_delta = 0.25`
  - `mean_abs_delta = 0.5`
  - `mean_observed_score = 0.5`
  - `mean_repaired_score = 0.7143`
- masked:
  - `num_pairs = 8`
  - `local_amcd = 0.5`
  - `mean_signed_delta = 0.375`
  - `mean_abs_delta = 0.625`
  - `mean_observed_score = 0.375`
  - `mean_repaired_score = 0.7143`
- `local_amcd_gap_visible_minus_masked = -0.125`
- judge usage:
  - `prompt_tokens = 21252`
  - `completion_tokens = 440`
  - `total_tokens = 21692`
  - `num_calls = 32`

Interpretation:

- External local-pair construction on real step-level traces is now fully materialized on this small pilot: parser/prompt/runtime hardening raised coverage from `4 / 8` to `8 / 8` on the same selected source set.
- That removes the old “coverage too low to read anything” excuse. On a fully covered `8`-pair pilot, the visible API judge still does not show an advantage over masked (`local_amcd = 0.375` visible vs `0.5` masked).
- The useful result is therefore sharper than before: external answer-matched local repair on `ProcessBench` is feasible to construct, but the current local readout is still negative-to-inconclusive for a visible advantage.
- Combined with the already positive external `ASS` result, the current external-source picture is: answer sensitivity transfers cleanly to `ProcessBench`, but the visible local-repair story still does not.
