# Hybrid Object Gate Workflow

Date: 2026-03-31

## Principle

The Object gate should not be hardcode-first and should not be model-only.

Use:

- models for semantic generation and semantic audit,
- deterministic validators for schema checks and exact-checkable boundaries,
- spot review to prevent circular labeling.

## Workflow

1. Generate candidate pairs with an API or local model.
2. Normalize into the CAVE seed schema.
3. Run deterministic validation.
4. Build a review queue for labelability, locality, and artifact checks.
5. Freeze a reviewed dev panel before running baselines.

## Scripts

- `scripts/generate_object_gate_candidates.py`
- `scripts/validate_object_gate_seed.py`
- `scripts/build_object_gate_review_queue.py`

## Minimal API example

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
export CAVE_API_KEY=...
python scripts/generate_object_gate_candidates.py \
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

## Acceptance rule draft

The first reviewed dev panel should only be accepted if:

- pair consistency is 100 percent,
- at least 80 percent of reviewed pairs are labeled `label_clear`,
  `localizable`, and `repair_plausible`,
- at least two domains remain viable after review,
- no dominant formatting or metadata artifact explains the gold action.

Until this rule is passed, the project headline remains the object claim only.
