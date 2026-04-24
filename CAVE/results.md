# Results

This file records reproducible commands and outcomes. Large experiments are
intentionally deferred until the Object gate is ready.

## 2026-03-31 - Phase 0 bootstrap

Purpose:
Validate the bootstrap Object gate seed before any model runs.

Command:

```bash
python scripts/validate_object_gate_seed.py data/object_gate_seed/cave_object_seed.jsonl
```

Status:
Passed.

Observed output:

```text
validation ok
records: 6
pairs: 3
domains: {'code': 2, 'plan': 2, 'sym': 2}
actions: {'keep': 3, 'revise': 3}
pair_ids: ['code_pair_001', 'plan_pair_001', 'sym_pair_001']
```

Artifact:

- `artifacts/object_gate/seed_validation.txt`

Notes:

- No training, prompting, or API-based experiments have been run yet.
- This is deliberate. The current stage is object-definition bootstrap.

## 2026-03-31 - Hybrid API bootstrap for Object gate candidates

Purpose:
Verify that model-generated paired interventions can flow through the Object
gate pipeline without turning the project into hardcode-only construction.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym code plan \
  --pairs-per-domain 1 \
  --output artifacts/object_gate/generated_candidates.jsonl \
  --meta-output artifacts/object_gate/generated_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/generated_candidates.jsonl
python scripts/build_object_gate_review_queue.py \
  artifacts/object_gate/generated_candidates.jsonl \
  --output-md artifacts/object_gate/review_queue.md \
  --output-jsonl artifacts/object_gate/review_queue.jsonl
```

Status:
Passed for the minimal bootstrap pass.

Observed outcome:

```text
wrote 6 records to artifacts/object_gate/generated_candidates.jsonl
validation ok
records: 6
pairs: 3
domains: {'code': 2, 'plan': 2, 'sym': 2}
actions: {'keep': 3, 'revise': 3}
wrote review markdown to artifacts/object_gate/review_queue.md
wrote review jsonl to artifacts/object_gate/review_queue.jsonl
```

Artifacts:

- `artifacts/object_gate/generated_candidates.jsonl`
- `artifacts/object_gate/generated_candidates_meta.json`
- `artifacts/object_gate/review_queue.md`
- `artifacts/object_gate/review_queue.jsonl`

Usage:

- API backend: `ep-20251213141929-gk2jb`
- Total tokens across three requests: `2552`

Notes:

- This pass proves that the Object gate can start from model-generated
  candidates while keeping deterministic schema checks.
- Review is still required before any candidate enters a frozen dev panel.

## 2026-03-31 - Batch 01 exploratory review

Purpose:
Use a slightly larger generated batch to find prompt and schema failure modes
before freezing the acceptance rule.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym code plan \
  --pairs-per-domain 2 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch01_candidates.jsonl \
  --meta-output artifacts/object_gate/batch01_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch01_candidates.jsonl
python scripts/build_object_gate_review_queue.py \
  artifacts/object_gate/batch01_candidates.jsonl \
  --output-md artifacts/object_gate/batch01_review_queue.md \
  --output-jsonl artifacts/object_gate/batch01_review_queue.jsonl
```

Status:
Exploratory pass completed.

Observed outcome:

```text
validation ok
records: 12
pairs: 6
domains: {'code': 4, 'plan': 4, 'sym': 4}
actions: {'keep': 6, 'revise': 6}
```

Review outcome:

- accepted pairs: 4
- rejected pairs: 2
- acceptance rate: 66.7 percent

Artifacts:

- `artifacts/object_gate/batch01_candidates.jsonl`
- `artifacts/object_gate/batch01_candidates_meta.json`
- `artifacts/object_gate/batch01_review_queue.md`
- `artifacts/object_gate/batch01_review_queue.jsonl`
- `artifacts/object_gate/batch01_review_summary.md`

Usage:

- total API tokens across six requests: `5130`

Notes:

- This batch was used to tighten prompts and artifact checks.
- It does not count as the frozen review set because the acceptance rule was
  not yet frozen.

## 2026-03-31 - Frozen review set for Object gate bootstrap

Purpose:
Evaluate whether post-tightening generated pairs are good enough to freeze a
bootstrap dev panel and declare an Object gate `GO`.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym code plan \
  --pairs-per-domain 1 \
  --seed 101 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch02_candidates.jsonl \
  --meta-output artifacts/object_gate/batch02_candidates_meta.json
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains plan \
  --pairs-per-domain 1 \
  --seed 301 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch04_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch04_plan_candidates_meta.json
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym \
  --pairs-per-domain 1 \
  --seed 401 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch05_sym_candidates.jsonl \
  --meta-output artifacts/object_gate/batch05_sym_candidates_meta.json
python scripts/validate_object_gate_seed.py artifacts/object_gate/batch02_candidates.jsonl
python scripts/validate_object_gate_seed.py artifacts/object_gate/batch04_plan_candidates.jsonl
python scripts/validate_object_gate_seed.py artifacts/object_gate/batch05_sym_candidates.jsonl
```

Status:
Bootstrap Object gate `GO`.

Observed review outcome:

```text
Frozen review set:
- reviewed pairs: 5
- accepted pairs: 4
- acceptance rate: 80.0 percent
- viable domains: 3
```

Accepted pairs:

- `sym_0`
- `code_pair_0`
- `plan_pair_0_301`
- `sym_pair_0`

Rejected pair:

- `plan_pair_0`

Artifacts:

- `artifacts/object_gate/frozen_reviewed_panel_v0.2.jsonl`
- `artifacts/object_gate/frozen_reviewed_panel_v0.2_summary.md`
- `docs/object_gate_acceptance.md`
- `docs/object_gate_artifact_checklist.md`

Usage:

- batch02 tokens: `2842`
- batch04 tokens: `1195`
- batch05 tokens: `891`
- total frozen-set generation tokens: `4928`

Notes:

- This is a bootstrap-level pass for the Object gate only.
- It is not evidence for ICVT or for downstream deployment claims.
- The next step is Audit gate preparation on the frozen panel.

## 2026-03-31 - Contrastive locality family bootstrap diagnostics

Purpose:
Test a genuinely different family after `audit_final_v1` failed to show a
final-slice `gold_signal > matched_shuffle` gap, and harden the generator
against invalid revise records while doing so.

Commands:

```bash
python -m py_compile scripts/generate_object_gate_candidates.py
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch13_contrastive_locality_code_candidates.jsonl
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains code plan \
  --pairs-per-domain 1 \
  --family contrastive_locality \
  --profile harder \
  --seed 1501 \
  --temperature 0.35 \
  --max-attempts 4 \
  --output artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  --meta-output artifacts/object_gate/batch14_contrastive_locality_candidates_meta.json \
  --max-output-tokens 1100
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains code plan \
  --pairs-per-domain 1 \
  --family contrastive_locality \
  --profile harder \
  --seed 1601 \
  --temperature 0.35 \
  --max-attempts 4 \
  --output artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --meta-output artifacts/object_gate/batch15_contrastive_locality_candidates_meta.json \
  --max-output-tokens 1100
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl
```

Status:
Completed, but the family is still not bootstrap-ready.

Observed outcomes:

```text
batch12 validation ok
batch13 validation failed: revise example requires non-empty repair suffix
batch14 validation ok
batch15 validation ok
```

Review outcomes:

- `batch11`: accepted `2 / 4`
- `batch12`: accepted `0 / 2`
- `batch13`: invalid before review `1 / 1`
- `batch14`: accepted `0 / 2`
- `batch15`: accepted `0 / 2`

Artifacts:

- `artifacts/object_gate/batch12_contrastive_locality_review_summary.md`
- `artifacts/object_gate/batch13_contrastive_locality_review_summary.md`
- `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- `artifacts/object_gate/batch14_contrastive_locality_candidates_meta.json`
- `artifacts/object_gate/batch14_contrastive_locality_review_summary.md`
- `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- `artifacts/object_gate/batch15_contrastive_locality_candidates_meta.json`
- `artifacts/object_gate/batch15_contrastive_locality_review_summary.md`
- `artifacts/object_gate/contrastive_locality_bootstrap_summary.md`

Usage:

- batch14 API total tokens: `3246`
- batch15 API total tokens: `3633`

Notes:

- `generate_object_gate_candidates.py` now validates normalized records before
  writing output, so invalid revise cases like empty repair suffixes are caught
  during generation rather than later in review.
- The main bottleneck has moved from schema validity to semantic drift:
  checker/spec disagreement, underconstrained tests, and plan traces that do
  not actually instantiate the intended contrastive-locality geometry.
- Current aggregate for the new family is `2 accepted / 10 valid reviewed`
  pairs, which is not enough to declare a fresh Object bootstrap.

## 2026-03-31 - Contrastive locality blind judge bootstrap

Purpose:
Test whether a blind model-judge can act as a useful pre-screen for
`contrastive_locality`, instead of continuing pure prompt patching.

Commands:

```bash
python -m py_compile scripts/judge_contrastive_locality_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v1.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v1_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v1_summary.md
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v2.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v2_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v2_summary.md
```

Status:
Completed.

Observed outcomes:

```text
judge_v1 verdicts: {'accept': 10}
judge_v2 verdicts: {'accept': 2, 'reject': 8}
judge_v2 checker_disambiguates_repairs: {'fail': 8, 'pass': 2}
```

Artifacts:

- `scripts/judge_contrastive_locality_candidates.py`
- `docs/contrastive_locality_acceptance.md`
- `artifacts/object_gate/contrastive_locality_judge_v1.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v1_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v1_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v2.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v2_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v2_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v2_assessment.md`

Notes:

- `judge_v1` was too exposed to candidate framing and accepted every reviewed
  pair, so it is not suitable as a pre-screen.
- `judge_v2` removed candidate notes and tightened rejection rules. It now
  filters the obviously bad later batches, but still disagrees with human review
  on several earlier borderline pairs.
- Current recommendation is to keep `judge_v2` as a pre-screen only, not a
  final acceptance oracle.

## 2026-03-31 - Execution-backed contrastive locality judge v3.1

Purpose:
Reduce `judge_v2`'s textual hallucinations by adding execution-backed code
checks and structured plan checks before model judging.

Commands:

```bash
python -m py_compile scripts/judge_contrastive_locality_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v3.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v3_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v3_summary.md
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v3_1.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v3_1_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v3_1_summary.md
```

Status:
Completed.

Observed outcomes:

```text
judge_v3 verdicts: {'accept': 1, 'reject': 9}
judge_v3_1 verdicts: {'accept': 1, 'reject': 9}
judge_v3_1 judging modes: {'auto_reject': 4, 'model_with_program_findings': 6}
```

Artifacts:

- `artifacts/object_gate/contrastive_locality_judge_v3.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v3_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v3_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v3_1.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v3_1_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v3_1_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v3_1_assessment.md`

Notes:

- `judge_v3.1` is more useful than `judge_v2` as a veto mechanism because it
  can directly reject code pairs whose keep/revise traces contradict the written
  tests and plan pairs whose revise trace already satisfies the written
  precedence constraints.
- The main remaining limitation is asymmetry: `judge_v3.1` is much better at
  rejecting bad pairs than at confidently surfacing good ones.
- Current recommendation is to keep `judge_v3.1` as a veto-only pre-screen and
  continue to require human review for every accepted pair.

## 2026-03-31 - Schedule-style plan semantics in judge v3.2

Purpose:
Add a minimal schedule semantics checker so plan pairs with durations and
start-time prose can be screened with program evidence rather than pure text
judgment.

Commands:

```bash
python -m py_compile scripts/judge_contrastive_locality_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v3_2.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v3_2_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v3_2_summary.md
```

Status:
Completed.

Observed outcomes:

```text
judge_v3_2 verdicts: {'accept': 2, 'reject': 8}
judge_v3_2 modes: {'auto_reject': 4, 'model_with_program_findings': 6}
```

Artifacts:

- `artifacts/object_gate/contrastive_locality_judge_v3_2.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v3_2_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v3_2_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v3_2_assessment.md`

Notes:

- `judge_v3.2` now infers schedule start times, precedence edges, and minimal
  makespan for the current schedule-style plan pairs.
- This is enough to recover `batch11`'s schedule-style accepted plan pair and
  to reject `batch12`'s buffered schedule case with explicit program evidence.
- The remaining main weakness is now on the code side, where acceptance still
  diverges from prior human review.

## 2026-03-31 - Execution-backed code semantics in judge v4

Purpose:
Close the remaining code-side gap in the `contrastive_locality` pre-screen by
testing keep/revise and nearby repairs against synthesized reference behavior
on mutated probe inputs.

Commands:

```bash
python -m py_compile scripts/judge_contrastive_locality_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl \
  artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_v4_summary.md
```

Status:
Completed.

Observed outcomes:

```text
judge_v4 verdicts: {'accept': 2, 'reject': 8}
judge_v4 modes: {'auto_reject': 5, 'model_with_program_findings': 5}
```

Artifacts:

- `artifacts/object_gate/contrastive_locality_judge_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_v4_summary.md`
- `artifacts/object_gate/contrastive_locality_judge_v4_assessment.md`

Notes:

- `judge_v4` adds synthesized-reference code probes on top of the existing
  execution-backed test checks and plan semantics.
- This fixes the main remaining disagreement with human review: `code_1501_0`
  is now rejected because the keep trace disagrees with the synthesized
  reference on mixed-sign odd probes that the written tests missed.
- Current accepted set now matches the human review ledger exactly:
  `code_contrastive_locality_0` and `plan_contrastive_locality_0`.
- Operationally, `judge_v4` is now the default veto pre-screen for new
  `contrastive_locality` batches, but accepted pairs still require human
  review.

## 2026-03-31 - Batch16 contrastive_locality under judge v4 workflow

Purpose:
Test whether the new `judge_v4` workflow can surface additional acceptable
`contrastive_locality` pairs, and determine whether the bottleneck has moved
from screening to generation.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains code plan \
  --pairs-per-domain 2 \
  --family contrastive_locality \
  --profile harder \
  --seed 1701 \
  --temperature 0.35 \
  --max-attempts 5 \
  --request-timeout 60 \
  --max-output-tokens 1100 \
  --output artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl \
  --meta-output artifacts/object_gate/batch16_contrastive_locality_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch16_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch16_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch16_v4_summary.md
```

Status:
Completed.

Observed outcomes:

```text
validation ok
records: 8
pairs: 4
judge_batch16_v4 verdicts: {'accept': 1, 'reject': 3}
```

Review outcomes:

- accepted `1 / 4`
- rejected `3 / 4`

Artifacts:

- `artifacts/object_gate/batch16_contrastive_locality_candidates.jsonl`
- `artifacts/object_gate/batch16_contrastive_locality_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch16_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch16_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch16_v4_summary.md`
- `artifacts/object_gate/batch16_contrastive_locality_review_summary.md`

Usage:

- batch16 generation total tokens: `7736`

Notes:

- `judge_v4` pre-screen aligned with human review on this batch: it accepted
  only `code_1701_harder_0`, which is also the only pair kept after review.
- `code_1702_1` was correctly auto-rejected because the claimed revise trace
  already passes the written tests.
- both plan pairs were still rejected in human review, confirming that the main
  remaining instability is on plan generation rather than judge behavior.
- family aggregate is now `3 accepted / 14 valid reviewed`, so this branch is
  still not Object-bootstrap ready.

## 2026-03-31 - Plan-only prompt override test for contrastive_locality

Purpose:
Test whether a plan-specific prompt override can reduce false violations and
checker ambiguity enough to make plan-side `contrastive_locality` generation
usable.

Commands:

```bash
python -m py_compile scripts/generate_object_gate_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains plan \
  --pairs-per-domain 3 \
  --family contrastive_locality \
  --profile harder \
  --seed 1801 \
  --temperature 0.35 \
  --max-attempts 5 \
  --request-timeout 60 \
  --max-output-tokens 1100 \
  --output artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch17_contrastive_locality_plan_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch17_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch17_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch17_v4_summary.md
```

Status:
Completed.

Observed outcomes:

```text
validation ok
records: 6
pairs: 3
judge_batch17_v4 verdicts: {'reject': 3}
```

Review outcomes:

- accepted `0 / 3`
- rejected `3 / 3`

Artifacts:

- `artifacts/object_gate/batch17_contrastive_locality_plan_candidates.jsonl`
- `artifacts/object_gate/batch17_contrastive_locality_plan_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch17_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch17_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch17_v4_summary.md`
- `artifacts/object_gate/batch17_contrastive_locality_plan_review_summary.md`

Usage:

- batch17 generation total tokens: `5846`

Notes:

- the plan-specific prompt override did improve surface quality: this batch no
  longer relied on obviously false revise claims like the earlier pasta case
- however, all three pairs still failed on checker ambiguity or undercoverage,
  not on schema validity
- this means the remaining plan bottleneck is now object/checker design rather
  than simple prompt wording
- family aggregate is now `3 accepted / 17 valid reviewed`, which is worse than
  before and still far from a fresh Object bootstrap

## 2026-03-31 - Structured plan object bootstrap for contrastive_locality

Purpose:
Replace prose plan constraints with a structured checker that defines an exact
one-adjacent-swap local repair object, then test whether the current generator
can satisfy that geometry.

Commands:

```bash
python -m py_compile scripts/generate_object_gate_candidates.py \
  scripts/judge_contrastive_locality_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains plan \
  --pairs-per-domain 3 \
  --family contrastive_locality \
  --profile harder \
  --seed 1901 \
  --temperature 0.35 \
  --max-attempts 5 \
  --request-timeout 60 \
  --max-output-tokens 1100 \
  --output artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch18_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch18_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch18_v4_summary.md
```

Status:
Completed, but rejected.

Observed outcomes:

```text
validation ok
records: 6
pairs: 3
judge_batch18_v4 verdicts: {'reject': 3}
```

Review outcomes:

- accepted `0 / 3`
- rejected `3 / 3`

Artifacts:

- `docs/contrastive_locality_structured_plan.md`
- `artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates.jsonl`
- `artifacts/object_gate/batch18_contrastive_locality_structured_plan_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch18_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch18_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch18_v4_summary.md`
- `artifacts/object_gate/batch18_contrastive_locality_structured_plan_review_summary.md`

Usage:

- batch18 generation total tokens: `5800`

Notes:

- the structured checker makes the plan failure mode much cleaner than the old
  prose checker path
- however, the API generator still tends to produce revise orders that are
  actually valid under the structured edges
- this justified moving the same family-semantic rule into generation-time
  validation

## 2026-03-31 - Generator-side semantic validation for structured plan

Purpose:
Reject bad structured-plan candidates during generation rather than after
judging, so the generator only accepts pairs that already satisfy the
contrastive-locality geometry.

Commands:

```bash
python -m py_compile scripts/generate_object_gate_candidates.py
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains plan \
  --pairs-per-domain 2 \
  --family contrastive_locality \
  --profile harder \
  --seed 2001 \
  --temperature 0.35 \
  --max-attempts 6 \
  --request-timeout 60 \
  --max-output-tokens 1100 \
  --output artifacts/object_gate/batch19_contrastive_locality_structured_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch19_contrastive_locality_structured_plan_candidates_meta.json
```

Status:
Failed before first pair.

Observed failure:

```text
RuntimeError: failed to generate valid pair for domain=plan index=0:
attempt 1: structured plan revise order already satisfies precedence edges;
attempt 2: structured plan revise order already satisfies precedence edges;
attempt 3: structured plan revise order already satisfies precedence edges;
attempt 4: structured plan revise order already satisfies precedence edges;
attempt 5: structured plan revise order already satisfies precedence edges;
attempt 6: structured plan revise order already satisfies precedence edges
```

Notes:

- this is a cleaner and more informative failure than the earlier prompt-only
  route because the family-semantic criterion is now explicit
- it shows the current API generator cannot satisfy the structured plan object
  reliably enough even to start a new batch
- at this point, continuing this family would require either hand-constructed
  structured plan seeds or a search-based generation loop, not just direct
  free generation

## 2026-03-31 - Search-constructed structured plan path

Purpose:
Test whether the structured-plan object becomes viable if pair construction is
done by explicit search over precedence graphs and adjacent-swap neighborhoods
instead of direct model generation.

Commands:

```bash
python -m py_compile scripts/build_structured_plan_locality_pairs.py
python scripts/build_structured_plan_locality_pairs.py \
  --limit 3 \
  --seed 2101 \
  --output artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl \
  --meta-output artifacts/object_gate/batch20_structured_plan_search_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch20_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch20_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch20_v4_summary.md
```

Status:
Completed and accepted.

Observed outcomes:

```text
validation ok
records: 6
pairs: 3
judge_batch20_v4 verdicts: {'accept': 3}
```

Review outcomes:

- accepted `3 / 3`
- rejected `0 / 3`

Artifacts:

- `scripts/build_structured_plan_locality_pairs.py`
- `artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl`
- `artifacts/object_gate/batch20_structured_plan_search_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch20_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch20_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch20_v4_summary.md`
- `artifacts/object_gate/batch20_structured_plan_search_review_summary.md`

Notes:

- this is the first plan path in `contrastive_locality` that is stable under
  validator, judge, and human review at the same time
- the positive signal is specific to the search-constructed structured-plan
  sub-object, not to direct API generation
- family aggregate moves to `6 accepted / 23 valid reviewed`, which still does
  not clear the frozen bootstrap bar for the whole family

## 2026-03-31 - Diversified structured-plan search expansion

Purpose:
Check whether the positive `batch20` result was a one-off or whether the
search-constructed structured-plan path can sustain a larger reviewed batch
with better diversity.

Commands:

```bash
python -m py_compile scripts/build_structured_plan_locality_pairs.py
python scripts/build_structured_plan_locality_pairs.py \
  --limit 5 \
  --seed 2201 \
  --output artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl \
  --meta-output artifacts/object_gate/batch21_structured_plan_search_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch21_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch21_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch21_v4_summary.md
cat artifacts/object_gate/batch20_structured_plan_search_candidates.jsonl \
  artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl \
  > artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl
```

Status:
Completed and accepted.

Observed outcomes:

```text
validation ok
records: 10
pairs: 5
judge_batch21_v4 verdicts: {'accept': 5}

validation ok
records: 16
pairs: 8
```

Review outcomes:

- accepted `5 / 5`
- rejected `0 / 5`

Artifacts:

- `artifacts/object_gate/batch21_structured_plan_search_candidates.jsonl`
- `artifacts/object_gate/batch21_structured_plan_search_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch21_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch21_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch21_v4_summary.md`
- `artifacts/object_gate/batch21_structured_plan_search_review_summary.md`
- `artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl`
- `artifacts/object_gate/frozen_structured_plan_subpanel_v0_summary.md`

Notes:

- the diversified search path remains stable under validator, judge, and human
  review
- this is enough to freeze a first structured-plan reviewed subpanel with `8`
  accepted pairs
- the positive result still belongs to the structured-plan sub-object, not yet
  to the whole `contrastive_locality` family
- family aggregate moves to `11 accepted / 28 valid reviewed`

## 2026-03-31 - Failed plan replacement before normalization fix

Purpose:
Record a generation failure that exposed a remaining schema weakness in the
plan-domain path.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains plan \
  --pairs-per-domain 2 \
  --seed 201 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch03_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch03_plan_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch03_plan_candidates.jsonl
```

Status:
Failed validation.

Observed failure:

```text
validation failed: line 3: utility_delta missing key 'abstain'
```

Artifacts:

- `artifacts/object_gate/batch03_plan_candidates.jsonl`
- `artifacts/object_gate/batch03_plan_candidates_meta.json`

Notes:

- One generated pair omitted `utility_delta.abstain`.
- This failure led to a normalization fix in
  `scripts/generate_object_gate_candidates.py` that now fills missing utility
  keys with defaults.

## 2026-03-31 - Audit gate bootstrap assets

Purpose:
Freeze the first audit dev slice and generate bootstrap control/probe assets
before any baseline comparison.

Command:

```bash
cp artifacts/object_gate/frozen_reviewed_panel_v0.2.jsonl artifacts/audit/audit_dev_v0.jsonl
python scripts/validate_object_gate_seed.py artifacts/audit/audit_dev_v0.jsonl
python scripts/build_audit_controls.py \
  artifacts/audit/audit_dev_v0.jsonl \
  --output-jsonl artifacts/audit/audit_dev_v0_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_dev_v0_matched_shuffle_summary.json
python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_dev_v0.jsonl \
  --output-md artifacts/audit/audit_dev_v0_artifact_report.md \
  --output-json artifacts/audit/audit_dev_v0_artifact_report.json
```

Status:
Audit gate entry `GO`; full Audit pass not yet.

Observed outcome:

```text
validation ok
records: 8
pairs: 4
domains: {'code': 2, 'plan': 2, 'sym': 4}
actions: {'keep': 4, 'revise': 4}
wrote 4 controls to artifacts/audit/audit_dev_v0_matched_shuffle.jsonl
wrote markdown report to artifacts/audit/audit_dev_v0_artifact_report.md
```

Artifacts:

- `artifacts/audit/audit_dev_v0.jsonl`
- `artifacts/audit/audit_dev_v0_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v0_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v0_artifact_report.md`
- `artifacts/audit/audit_dev_v0_artifact_report.json`
- `artifacts/audit/audit_bootstrap_summary.md`
- `docs/audit/audit_gate_bootstrap.md`
- `docs/audit/audit_logging_contract.md`
- `docs/audit/audit_dev_slice_contract.md`

Notes:

- This established the first audit-ready protocol layer, but panel coverage was
  still incomplete for same-domain shuffle in `code` and `plan`.

## 2026-03-31 - Panel expansion for baseline-ready Audit protocol

Purpose:
Extend the frozen panel until every active domain supports same-domain matched
shuffle controls.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains code plan \
  --pairs-per-domain 2 \
  --seed 501 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch06_code_plan_candidates.jsonl \
  --meta-output artifacts/object_gate/batch06_code_plan_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch06_code_plan_candidates.jsonl
```

Status:
Completed and accepted into frozen panel `v0.3` after review.

Observed outcome:

```text
validation ok
records: 8
pairs: 4
domains: {'code': 4, 'plan': 4}
actions: {'keep': 4, 'revise': 4}
```

Review outcome:

- accepted pairs: `code_pair_0_501`, `code_pair_1`, `plan_pair_1`
- rejected pair: `plan_pair_0`

Artifacts:

- `artifacts/object_gate/batch06_code_plan_candidates.jsonl`
- `artifacts/object_gate/batch06_code_plan_candidates_meta.json`
- `artifacts/object_gate/batch06_review_summary.md`
- `artifacts/object_gate/frozen_reviewed_panel_v0.3.jsonl`
- `artifacts/object_gate/frozen_reviewed_panel_v0.3_summary.md`

Usage:

- total API tokens across four requests: `4375`

Notes:

- `plan_pair_0` was rejected because the written checker did not force the
  claimed violation.

## 2026-03-31 - Audit protocol upgraded to baseline-ready

Purpose:
Rebuild audit assets on the expanded frozen panel.

Command:

```bash
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/frozen_reviewed_panel_v0.3.jsonl
cp artifacts/object_gate/frozen_reviewed_panel_v0.3.jsonl \
  artifacts/audit/audit_dev_v1.jsonl
python scripts/build_audit_controls.py \
  artifacts/audit/audit_dev_v1.jsonl \
  --output-jsonl artifacts/audit/audit_dev_v1_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_dev_v1_matched_shuffle_summary.json
python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_dev_v1.jsonl \
  --output-md artifacts/audit/audit_dev_v1_artifact_report.md \
  --output-json artifacts/audit/audit_dev_v1_artifact_report.json
```

Status:
Audit protocol baseline-ready.

Observed outcome:

```text
validation ok
records: 14
pairs: 7
domains: {'code': 6, 'plan': 4, 'sym': 4}
actions: {'keep': 7, 'revise': 7}
same_domain_controls: 7
cross_domain_controls: 0
```

Artifacts:

- `artifacts/audit/audit_dev_v1.jsonl`
- `artifacts/audit/audit_dev_v1_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v1_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v1_artifact_report.md`
- `artifacts/audit/audit_dev_v1_artifact_report.json`
- `artifacts/audit/audit_bootstrap_summary.md`

Residual risk:

- `audit_dev_v1` has one flagged artifact risk: `code_pair_0_501` has a compact
  repair suffix (`tiny_repair_suffix`), so this pair should be monitored in the
  first empirical audit pass.

Notes:

- The remaining blocker is empirical: no baseline has yet been run against the
  audit controls.

## 2026-03-31 - First empirical audit baseline pass

Purpose:
Run the smallest executable baseline against the frozen audit dev slice and
measure whether `gold_signal` separates from `matched_shuffle`.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/run_audit_baseline.py \
  --slice artifacts/audit/audit_dev_v1.jsonl \
  --controls artifacts/audit/audit_dev_v1_matched_shuffle.jsonl \
  --run-id audit_baseline_v1_api \
  --output-log artifacts/audit/audit_baseline_v1_api_log.jsonl \
  --output-summary artifacts/audit/audit_baseline_v1_api_summary.json
```

Status:
Completed; informative but not sufficient for Audit gate pass.

Observed summary:

```text
direct: action_match=0.857, checker_pass=1.000
procedure_retry: action_match=0.857, checker_pass=1.000
gold_signal: action_match=1.000, checker_pass=1.000
matched_shuffle: action_match=0.857, checker_pass=0.857
```

Artifacts:

- `artifacts/audit/audit_baseline_v1_api_log.jsonl`
- `artifacts/audit/audit_baseline_v1_api_summary.json`
- `artifacts/audit/audit_baseline_v1_api_summary.md`
- `scripts/run_audit_baseline.py`

Usage:

- total rows: `28`
- total tokens: `10452`

Notes:

- The clearest shuffle failure is `plan_pair_0_301`, which passes under
  `gold_signal` but fails under `matched_shuffle`.
- The first pass still shows strong procedure effect: `direct` and
  `procedure_retry` are already very strong.
- Current interpretation: the audit story is now empirical, but not yet strong
  enough to claim robust verifier-content dependence.

## 2026-03-31 - Harder slice expansion and stronger shuffle matching

Purpose:
Expand the audit dev slice with harder revise samples and rebuild matched
shuffle controls with better same-domain matching.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym code plan \
  --pairs-per-domain 2 \
  --profile harder \
  --seed 601 \
  --request-timeout 60 \
  --output artifacts/object_gate/batch07_harder_candidates.jsonl \
  --meta-output artifacts/object_gate/batch07_harder_candidates_meta.json
python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/frozen_reviewed_panel_v0.4.jsonl
python scripts/build_audit_controls.py \
  artifacts/audit/audit_dev_v2.jsonl \
  --output-jsonl artifacts/audit/audit_dev_v2_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_dev_v2_matched_shuffle_summary.json
python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_dev_v2.jsonl \
  --output-md artifacts/audit/audit_dev_v2_artifact_report.md \
  --output-json artifacts/audit/audit_dev_v2_artifact_report.json
```

Status:
Completed.

Accepted harder pairs:

- `sym_601_harder`
- `sym_harder_602_1`
- `code_0_601`
- `plan_pair_1_harder_602`

Rejected harder pairs:

- `code_pair_602_harder`
- reason: empty repair suffix
- `plan_pair_0_harder`
- reason: lower-value step-extension artifact relative to stronger accepted plan samples

Artifacts:

- `artifacts/object_gate/batch07_harder_candidates.jsonl`
- `artifacts/object_gate/batch07_harder_candidates_meta.json`
- `artifacts/object_gate/frozen_reviewed_panel_v0.4.jsonl`
- `artifacts/audit/audit_dev_v2.jsonl`
- `artifacts/audit/audit_dev_v2_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v2_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v2_artifact_report.md`
- `artifacts/audit/audit_dev_v2_artifact_report.json`

Notes:

- `audit_dev_v2` has 11 pairs and 11 same-domain matched shuffles.
- Artifact report now flags one `tiny_repair_suffix` case and one
  `large_trace_length_gap` case.

## 2026-03-31 - Second empirical audit baseline pass on harder slice

Purpose:
Re-run the empirical audit on a larger and harder dev slice to test whether the
shuffle penalty becomes clearer.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
CAVE_API_KEY=... python scripts/run_audit_baseline.py \
  --slice artifacts/audit/audit_dev_v2.jsonl \
  --controls artifacts/audit/audit_dev_v2_matched_shuffle.jsonl \
  --run-id audit_baseline_v2_api \
  --output-log artifacts/audit/audit_baseline_v2_api_log.jsonl \
  --output-summary artifacts/audit/audit_baseline_v2_api_summary.json
```

Status:
Completed; empirical signal strengthened on dev slice.

Observed summary:

```text
direct: action_match=0.909, checker_pass=0.909
procedure_retry: action_match=0.909, checker_pass=0.909
gold_signal: action_match=1.000, checker_pass=1.000
matched_shuffle: action_match=0.818, checker_pass=0.727
```

Artifacts:

- `artifacts/audit/audit_baseline_v2_api_log.jsonl`
- `artifacts/audit/audit_baseline_v2_api_summary.json`
- `artifacts/audit/audit_baseline_v2_api_summary.md`

Usage:

- total rows: `44`
- total tokens: `17331`

Notes:

- Compared with v1, `matched_shuffle` checker pass dropped from `0.857` to
  `0.727`.
- `gold_signal` remained perfect on this dev slice.
- Strong procedure effect remains, so this is stronger dev evidence rather than
  a full Audit gate close.

## 2026-03-31 - Local backend support and source-bank shuffle controls

Purpose:
Make audit replication less dependent on one execution environment by adding a
separate-source control path and local model support for generation and audit
runner scripts.

Verification:

```bash
python -m py_compile \
  scripts/build_audit_controls.py \
  scripts/generate_object_gate_candidates.py \
  scripts/run_audit_baseline.py
```

Status:
Completed.

Changes:

- `scripts/build_audit_controls.py`
  - fixed the `--source-jsonl` path to reuse the same JSONL loader as the main
    input
- `scripts/generate_object_gate_candidates.py`
  - added cached local-model loading
  - added robust JSON extraction for non-pure outputs
  - disabled Qwen3 thinking mode for local generation
  - normalized keep examples to empty fail span / repair suffix
  - tightened generation prompt constraints after local failure review
- `scripts/run_audit_baseline.py`
  - added cached local-model execution
  - added robust JSON extraction for local/API outputs
  - disabled Qwen3 thinking mode for local baseline runs

## 2026-03-31 - Local harder generation attempts for held-out audit subset

Purpose:
Test whether local `Qwen3-8B` is already good enough to generate a reviewable
held-out harder subset for final-slice Audit work.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/generate_object_gate_candidates.py \
  --provider local \
  --model /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --domains sym code plan \
  --pairs-per-domain 2 \
  --profile harder \
  --temperature 0.2 \
  --seed 701 \
  --output artifacts/object_gate/batch08_local_harder_candidates.jsonl \
  --meta-output artifacts/object_gate/batch08_local_harder_candidates_meta.json \
  --max-output-tokens 700

python scripts/generate_object_gate_candidates.py \
  --provider local \
  --model /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --domains sym code plan \
  --pairs-per-domain 1 \
  --profile harder \
  --temperature 0.05 \
  --seed 901 \
  --output artifacts/object_gate/batch09_local_harder_candidates.jsonl \
  --meta-output artifacts/object_gate/batch09_local_harder_candidates_meta.json \
  --max-output-tokens 700
```

Status:
Completed; no held-out subset frozen from local generation.

Observed outcome:

```text
batch08: validator failed; 0 accepted pairs
batch09: validator passed; reviewed pairs=3; accepted pairs=0
```

Artifacts:

- `artifacts/object_gate/batch08_local_harder_candidates.jsonl`
- `artifacts/object_gate/batch08_local_harder_candidates_meta.json`
- `artifacts/object_gate/batch09_local_harder_candidates.jsonl`
- `artifacts/object_gate/batch09_local_harder_candidates_meta.json`
- `artifacts/object_gate/local_generation_attempts_summary.md`

Notes:

- Batch 08 failed mostly on schema and semantic-drift issues.
- Batch 09 passed deterministic validation but still failed review because the
  candidate pairs did not preserve one shared intended answer plus a true local
  error.
- Current local `Qwen3-8B` generation is not reliable enough to freeze a
  final-like audit subset.

## 2026-03-31 - Cross-backend dev-slice audit replication on local Qwen3-8B

Purpose:
Replicate the `audit_dev_v2` empirical audit on a second backend while the
held-out final slice is still missing.

Command:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_audit_baseline.py \
  --provider local \
  --model /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --slice artifacts/audit/audit_dev_v2.jsonl \
  --controls artifacts/audit/audit_dev_v2_matched_shuffle.jsonl \
  --run-id audit_baseline_v2_local_qwen3_8b \
  --output-log artifacts/audit/audit_baseline_v2_local_qwen3_8b_log.jsonl \
  --output-summary artifacts/audit/audit_baseline_v2_local_qwen3_8b_summary.json \
  --sample-filter revise_only \
  --max-output-tokens 250
```

Status:
Completed; cross-backend dev-slice replication is positive in checker terms.

Observed summary:

```text
direct: action_match=0.727, checker_pass=0.545
procedure_retry: action_match=0.727, checker_pass=0.727
gold_signal: action_match=1.000, checker_pass=1.000
matched_shuffle: action_match=1.000, checker_pass=0.545
```

Artifacts:

- `artifacts/audit/audit_baseline_v2_local_qwen3_8b_log.jsonl`
- `artifacts/audit/audit_baseline_v2_local_qwen3_8b_summary.json`
- `artifacts/audit/audit_baseline_v2_local_qwen3_8b_summary.md`

Notes:

- The local backend preserves the same core checker-level pattern:
  `gold_signal` stays perfect while `matched_shuffle` degrades.
- The local model is much weaker overall than the API baseline in `direct` and
  only partially recovers under `procedure_retry`.
- Under shuffle, the local model almost always chooses `revise`, so the useful
  signal is checker outcome rather than action choice.

## 2026-03-31 - Restored API generation for the held-out final audit slice

Purpose:
Recover a reviewable held-out harder batch using API generation after local
generation proved too brittle.

Commands:

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym \
  --pairs-per-domain 1 \
  --profile harder \
  --seed 1001 \
  --output artifacts/object_gate/api_smoke_candidates.jsonl \
  --meta-output artifacts/object_gate/api_smoke_candidates_meta.json \
  --max-output-tokens 900

python scripts/generate_object_gate_candidates.py \
  --provider api \
  --domains sym code plan \
  --pairs-per-domain 2 \
  --profile harder \
  --seed 1101 \
  --temperature 0.4 \
  --max-attempts 4 \
  --output artifacts/object_gate/batch10_api_harder_candidates.jsonl \
  --meta-output artifacts/object_gate/batch10_api_harder_candidates_meta.json \
  --max-output-tokens 1100
```

Status:
Completed; held-out batch accepted and frozen.

Observed outcome:

```text
smoke batch: validator passed, 1/1 pair reviewable
batch10: validator passed, 6/6 pairs accepted on review
```

Artifacts:

- `artifacts/object_gate/api_smoke_candidates.jsonl`
- `artifacts/object_gate/api_smoke_candidates_meta.json`
- `artifacts/object_gate/batch10_api_harder_candidates.jsonl`
- `artifacts/object_gate/batch10_api_harder_candidates_meta.json`
- `artifacts/object_gate/batch10_api_review_summary.md`
- `artifacts/audit/audit_final_v0.jsonl`
- `docs/audit/audit_final_slice_contract.md`

Notes:

- One API response in the first full-batch attempt returned malformed top-level
  JSON. This led to a generator upgrade with per-pair retries and failure logs.
- The accepted batch gives a clean held-out final slice with 2 pairs each from
  `sym`, `code`, and `plan`.

## 2026-03-31 - First API audit run on frozen final slice

Purpose:
Run the first empirical Audit decision on a frozen held-out final slice.

Commands:

```bash
python scripts/build_audit_controls.py \
  artifacts/audit/audit_final_v0.jsonl \
  --source-jsonl artifacts/audit/audit_dev_v2.jsonl \
  --output-jsonl artifacts/audit/audit_final_v0_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_final_v0_matched_shuffle_summary.json

python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_final_v0.jsonl \
  --output-md artifacts/audit/audit_final_v0_artifact_report.md \
  --output-json artifacts/audit/audit_final_v0_artifact_report.json

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_audit_baseline.py \
  --slice artifacts/audit/audit_final_v0.jsonl \
  --controls artifacts/audit/audit_final_v0_matched_shuffle.jsonl \
  --run-id audit_final_v0_api \
  --output-log artifacts/audit/audit_final_v0_api_log.jsonl \
  --output-summary artifacts/audit/audit_final_v0_api_summary.json \
  --sample-filter revise_only \
  --max-output-tokens 400
```

Status:
Completed; final slice is frozen and first-run complete, but Audit gate is not
closed.

Observed summary:

```text
direct: action_match=0.833, checker_pass=0.500
procedure_retry: action_match=0.833, checker_pass=0.667
gold_signal: action_match=1.000, checker_pass=0.667
matched_shuffle: action_match=1.000, checker_pass=0.500
```

Artifacts:

- `artifacts/audit/audit_final_v0_matched_shuffle.jsonl`
- `artifacts/audit/audit_final_v0_matched_shuffle_summary.json`
- `artifacts/audit/audit_final_v0_artifact_report.md`
- `artifacts/audit/audit_final_v0_artifact_report.json`
- `artifacts/audit/audit_final_v0_api_log.jsonl`
- `artifacts/audit/audit_final_v0_api_summary.json`
- `artifacts/audit/audit_final_v0_api_summary.md`

Notes:

- This run is more informative than the dev slice because it reveals a new
  blocker on frozen held-out data.
- The dominant new issue is brittle plan canonicalization: both held-out `plan`
  pairs fail even under `gold_signal`, despite semantically correct repaired
  outputs.
- Because the final slice is already frozen, any checker fix now requires a new
  versioned final slice or an explicitly narrowed claim.

## 2026-03-31 - Versioned final-slice checker repair and v1 rerun

Purpose:
Open `audit_final_v1` to reduce the `plan` canonicalization confound exposed by
`audit_final_v0`, without changing any `sym` or `code` sample.

Verification and construction:

```bash
python scripts/validate_object_gate_seed.py artifacts/audit/audit_final_v1.jsonl

python scripts/build_audit_controls.py \
  artifacts/audit/audit_final_v1.jsonl \
  --source-jsonl artifacts/audit/audit_dev_v2.jsonl \
  --output-jsonl artifacts/audit/audit_final_v1_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_final_v1_matched_shuffle_summary.json

python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_final_v1.jsonl \
  --output-md artifacts/audit/audit_final_v1_artifact_report.md \
  --output-json artifacts/audit/audit_final_v1_artifact_report.json

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_audit_baseline.py \
  --slice artifacts/audit/audit_final_v1.jsonl \
  --controls artifacts/audit/audit_final_v1_matched_shuffle.jsonl \
  --run-id audit_final_v1_api \
  --output-log artifacts/audit/audit_final_v1_api_log.jsonl \
  --output-summary artifacts/audit/audit_final_v1_api_summary.json \
  --sample-filter revise_only \
  --max-output-tokens 400
```

Status:
Completed; checker confound reduced, but Audit gate still not closed.

Observed summary:

```text
direct: action_match=0.833, checker_pass=0.833
procedure_retry: action_match=0.833, checker_pass=1.000
gold_signal: action_match=1.000, checker_pass=0.833
matched_shuffle: action_match=1.000, checker_pass=0.833
```

Artifacts:

- `artifacts/audit/audit_final_v1.jsonl`
- `artifacts/audit/audit_final_v1_matched_shuffle.jsonl`
- `artifacts/audit/audit_final_v1_matched_shuffle_summary.json`
- `artifacts/audit/audit_final_v1_artifact_report.md`
- `artifacts/audit/audit_final_v1_artifact_report.json`
- `artifacts/audit/audit_final_v1_api_log.jsonl`
- `artifacts/audit/audit_final_v1_api_summary.json`
- `artifacts/audit/audit_final_v1_api_summary.md`
- `artifacts/audit/audit_final_v1_change_note.md`

Notes:

- `audit_final_v1` only changes `plan` checker metadata. It is a versioned
  repair, not the same metric series as `audit_final_v0`.
- The repaired final slice no longer shows a meaningful checker-level gap
  between `gold_signal` and `matched_shuffle`.
- `procedure_retry` now reaches `1.000`, so the strongest remaining signal is
  still procedural rather than verifier-content-specific.
- This shifts the current Audit reading from “checker confound” to a cleaner
  negative/partial-result branch on the frozen final slice.

## 2026-04-01 - Structured code path for contrastive locality

Purpose:
Build a matching structured-code path for the `contrastive_locality` family so
code no longer depends only on free-form generation and heuristic nearby-repair
mining.

Commands:

```bash
python -m py_compile scripts/build_structured_code_locality_pairs.py \
  scripts/judge_contrastive_locality_candidates.py

python scripts/build_structured_code_locality_pairs.py \
  --limit 3 \
  --seed 3101 \
  --output artifacts/object_gate/batch22_structured_code_search_candidates.jsonl \
  --meta-output artifacts/object_gate/batch22_structured_code_search_candidates_meta.json

python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch22_structured_code_search_candidates.jsonl

python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch22_structured_code_search_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch22_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch22_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch22_v4_summary.md

python scripts/build_structured_code_locality_pairs.py \
  --limit 5 \
  --seed 3201 \
  --output artifacts/object_gate/batch23_structured_code_search_candidates.jsonl \
  --meta-output artifacts/object_gate/batch23_structured_code_search_candidates_meta.json

python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/batch23_structured_code_search_candidates.jsonl

python scripts/judge_contrastive_locality_candidates.py \
  artifacts/object_gate/batch23_structured_code_search_candidates.jsonl \
  --output-jsonl artifacts/object_gate/contrastive_locality_judge_batch23_v4.jsonl \
  --output-summary-json artifacts/object_gate/contrastive_locality_judge_batch23_v4_summary.json \
  --output-md artifacts/object_gate/contrastive_locality_judge_batch23_v4_summary.md

cat artifacts/object_gate/batch22_structured_code_search_candidates.jsonl \
  artifacts/object_gate/batch23_structured_code_search_candidates.jsonl \
  > artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl

python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl
```

Status:
Completed; structured-code sub-object is now panel-viable.

Observed outcomes:

```text
batch22: validation ok, judge_v4 accept 3/3
batch23: validation ok, judge_v4 accept 5/5
frozen_structured_code_subpanel_v0: validation ok, 8 pairs
```

Artifacts:

- `docs/contrastive_locality_structured_code.md`
- `artifacts/object_gate/batch22_structured_code_search_candidates.jsonl`
- `artifacts/object_gate/batch22_structured_code_search_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch22_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch22_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch22_v4_summary.md`
- `artifacts/object_gate/batch22_structured_code_search_review_summary.md`
- `artifacts/object_gate/batch23_structured_code_search_candidates.jsonl`
- `artifacts/object_gate/batch23_structured_code_search_candidates_meta.json`
- `artifacts/object_gate/contrastive_locality_judge_batch23_v4.jsonl`
- `artifacts/object_gate/contrastive_locality_judge_batch23_v4_summary.json`
- `artifacts/object_gate/contrastive_locality_judge_batch23_v4_summary.md`
- `artifacts/object_gate/batch23_structured_code_search_review_summary.md`
- `artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl`
- `artifacts/object_gate/frozen_structured_code_subpanel_v0_summary.md`

Notes:

- The first `--limit 4` attempt only produced `3` pairs because two earlier
  specs contained behaviorally equivalent wrong candidates. The builder was
  then tightened to use only behaviorally distinct nearby repairs.
- `judge_v4` now has an `auto_accept` path for exact `code_local_repair_v1`
  pairs, so this sub-object no longer depends on API availability for its
  pre-screen step.
- This is a positive object-level result for the structured-code sub-object,
  not whole-family `contrastive_locality` Object `GO`.

## 2026-04-01 - Structured locality spin-out branch

Purpose:
Separate the two exact structured sub-objects into a clean `structured_locality`
branch, instead of continuing to judge them through the mixed
`contrastive_locality` ledger.

Commands:

```bash
cat artifacts/object_gate/frozen_structured_plan_subpanel_v0.jsonl \
  artifacts/object_gate/frozen_structured_code_subpanel_v0.jsonl \
  > artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl

python scripts/validate_object_gate_seed.py \
  artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl
```

Status:
Completed; fresh Object branch frozen and validated.

Observed outcome:

```text
validation ok
records: 32
pairs: 16
domains: {'code': 16, 'plan': 16}
actions: {'keep': 16, 'revise': 16}
```

Artifacts:

- `docs/structured_locality_branch.md`
- `docs/structured_locality_object_gate.md`
- `artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl`
- `artifacts/object_gate/frozen_structured_locality_panel_v0_summary.md`

Notes:

- This spin-out intentionally excludes the old weak free-generation batches.
- The new branch supports an Object-level `GO` for `structured_locality` only.
- This does not change the status of the older mixed `contrastive_locality`
  branch, which remains `Object bootstrap in progress`.

## 2026-04-01 - Structured locality Audit bootstrap on dev slice

Purpose:
Open Audit bootstrap on the clean `structured_locality` branch rather than on
the old mixed-family ledger.

Commands:

```bash
cp artifacts/object_gate/frozen_structured_locality_panel_v0.jsonl \
  artifacts/audit/audit_dev_v3.jsonl

python scripts/build_audit_controls.py \
  artifacts/audit/audit_dev_v3.jsonl \
  --output-jsonl artifacts/audit/audit_dev_v3_matched_shuffle.jsonl \
  --summary-json artifacts/audit/audit_dev_v3_matched_shuffle_summary.json

python scripts/build_audit_artifact_report.py \
  artifacts/audit/audit_dev_v3.jsonl \
  --output-md artifacts/audit/audit_dev_v3_artifact_report.md \
  --output-json artifacts/audit/audit_dev_v3_artifact_report.json

source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_audit_baseline.py \
  --slice artifacts/audit/audit_dev_v3.jsonl \
  --controls artifacts/audit/audit_dev_v3_matched_shuffle.jsonl \
  --provider local \
  --model /cephfs/shared/hf_cache/hub/Qwen3-8B \
  --run-id audit_baseline_v3_local_qwen3_8b \
  --output-log artifacts/audit/audit_baseline_v3_local_qwen3_8b_log.jsonl \
  --output-summary artifacts/audit/audit_baseline_v3_local_qwen3_8b_summary.json \
  --sample-filter revise_only \
  --max-output-tokens 300
```

Status:
Completed; Audit bootstrap opened on the clean branch.

Observed outcome:

```text
control summary: same_domain_controls=16, cross_domain_controls=0
artifact report: risk_counts={}
direct checker pass: 0.875
procedure_retry checker pass: 0.8125
gold_signal checker pass: 1.000
matched_shuffle checker pass: 0.750
```

Artifacts:

- `docs/audit/structured_locality_audit_dev_slice_contract.md`
- `docs/audit/structured_locality_audit_bootstrap.md`
- `artifacts/audit/audit_dev_v3.jsonl`
- `artifacts/audit/audit_dev_v3_matched_shuffle.jsonl`
- `artifacts/audit/audit_dev_v3_matched_shuffle_summary.json`
- `artifacts/audit/audit_dev_v3_artifact_report.md`
- `artifacts/audit/audit_dev_v3_artifact_report.json`
- `artifacts/audit/audit_baseline_v3_local_qwen3_8b_log.jsonl`
- `artifacts/audit/audit_baseline_v3_local_qwen3_8b_summary.json`
- `artifacts/audit/audit_baseline_v3_local_qwen3_8b_summary.md`
- `artifacts/audit/structured_locality_audit_bootstrap_summary.md`

Notes:

- The new branch is empirically inside the Audit gate on dev slice.
- The observed `gold_signal > matched_shuffle` gap is real, but mostly
  concentrated in the structured-plan half.
- Before opening a final slice, the structured-plan matched-shuffle builder
  should be tightened so the control is more topology-matched rather than
  repeatedly steering toward one canonical repair order.

## 2026-04-07 - Two-branch strategy split

Purpose:
Make the next project phase explicit by separating:

- a clean anchor branch (`structured_locality`)
- a weaker-program-dependence exploratory branch (`semantic_locality`)

Status:
Completed as project framing and governance, with no new empirical run.

Artifacts:

- `docs/two_branch_strategy.md`
- `docs/semantic_locality_branch.md`

Notes:

- `structured_locality` remains the only branch with fresh Object `GO`.
- `semantic_locality` is intentionally opened as design-only, with no inherited
  gate credit.
- This split is meant to prevent a false choice between “clean but narrow” and
  “natural but ambiguous” by letting each branch optimize for one goal.
- `apply_patch` was unavailable in this session, so this framing update used a
  shell-write fallback.
