# Object Gate Minimal Closed Loop

Date: 2026-03-31
Status: family-selective early-planning signal; broad Object branch closed in the current wrapper

## Goal

Show that matched-counterfactual step credit is a measurable object and that it behaves better than old process proxies on a tiny frozen slice, before any CPV training or large rollout spend.

Current evidence boundary:
- Supported: structured-planning families can show early-step-sensitive intervention signal.
- Supported most clearly on `tower_of_hanoi`.
- Not supported in the current branch: a generic step-credit story across mixed high-dependency families.

## Current defaults

- Environment: `conda run -n infer`
- Default model tier: Qwen3 1.7B
- Fallback model tier: Qwen3 4B if 1.7B cannot produce stable multi-step traces
- Primary task source: Reasoning Gym
- External tasks: disabled for the minimal loop
- API usage: enabled for tiny calibration and later semantic intervention generation, but not as the main evidence path

## Minimal loop

1. Freeze the slice definition and output locations.
2. Collect a tiny prompt batch and 2 traces per prompt.
3. Segment only 1-2 candidate steps per trace.
4. Create three matched interventions per candidate:
   - delete
   - paraphrase
   - distractor
5. Under the same remaining budget, run a tiny number of continuations for each intervention.
6. Compare the induced effect against:
   - step correctness
   - raw progress
   - simple artifacts such as step position and length
7. Decide `go` or `no-go` for widening the object slice.

## Frozen pilot protocol

- Dev slice size:
  - high-dependency prompts: 24
  - shallow prompts: 24
- Final slice size:
  - high-dependency prompts: 48
  - shallow prompts: 48
- Seeds:
  - dev: `1729`
  - final: `314159`
- Trace budget:
  - traces per prompt `K=2`
  - candidate steps per trace `L<=2`
  - paraphrase variants `P=1`
  - distractor variants `D=1`
  - continuation rollouts per intervention `M=2`

These numbers are intentionally small. They are for object existence and protocol debugging only, not for a paper claim.

## Object-gate acceptance

Primary checks:
- Signal existence: at least one candidate step in at least 60 percent of evaluated prompts shows a meaningful non-zero intervention effect under the frozen rollout budget.
- Proxy comparison: matched-counterfactual credit beats step correctness and raw progress on at least one primary alignment measure on the dev slice.
- Invariance pattern: paraphrase perturbations are materially smaller than distractor/delete perturbations.

Go:
- Pass at least 2 of the 3 primary checks, and one of the passes must be the proxy comparison.

No-go:
- Proxy comparison fails cleanly, or the signal is dominated by trivial artifacts.

## Artifact checks that start immediately

- Position control: early versus late step credit cannot be explained only by index.
- Length control: raw token count cannot explain most of the measured effect.
- Style control: phrases like "therefore" or "let us" should not behave like high-credit content by default.
- Shallow-task control: shallow tasks should not exhibit the same strength of credit signal as genuinely high-dependency tasks.

## Required artifacts

- `artifacts/object_gate/run_state.json`
- `artifacts/object_gate/manifest.template.json`
- `artifacts/object_gate/samples/`
- `artifacts/object_gate/interventions/`
- `artifacts/object_gate/rollouts/`
- `artifacts/object_gate/analysis/`

Current drafted artifact:
- `artifacts/object_gate/interventions/draft_candidates_v0.jsonl`
- `artifacts/object_gate/interventions/generated_candidates_v0.jsonl`
- `artifacts/object_gate/interventions/micro_batch_v0.jsonl`

## What is allowed before the package is installed

- Initialize the artifact tree and run-state files.
- Freeze the config, seeds, and gate criteria.
- Add family names once the task source is connected.

## What is not allowed yet

- Large prompt generation
- Baseline sweeps
- CPV training
- Any method or deployment claim

## First command

```bash
conda run -n infer python scripts/bootstrap_object_gate.py
```

## Day-1 completion criterion

Day 1 is complete when the following are true:
- `configs/object_gate.json` contains the frozen protocol fields.
- `artifacts/object_gate/` exists with run-state and manifest template files.
- `results.md` records the environment state and the next unblocker.
