# API Judge Probe on v5 Summary 2026-04-01

## Setup

- slice: `object_dev_v0_clean_merged_slice_v5`
- judge backend: project OpenAI-compatible API endpoint `ep-20251213141929-gk2jb`
- judge style: `critic`
- protocol: paired `original + swapped`

## Outcome

- original accuracy: `18/18`
- swapped accuracy: `18/18`
- balanced directional accuracy: `1.0`
- pair-strict accuracy: `1.0`
- family pair-strict:
  - `substance_flip = 1.0`
  - `style_flip = 1.0`

## Read

- the API judge does **not** collapse the object signal
- instead, it cleanly solves the current `v5` slice
- this means the current object is strongly model-sensitive in the expected direction:
  - low-capacity local judges collapse
  - stronger API judge saturates the slice

## Interpretation

- this probe strengthens the current object claim rather than weakening it
- `v5` is not “only hard for tiny local models” in a pathological way; it behaves like a capability-sensitive slice
- however, this also means `v5` is probably too easy to serve as a long-term final benchmark for frontier API judges

## Immediate Consequence

- for the current paper-facing object claim, the API probe is positive evidence
- for any later deployment or stronger-model story, we will likely need a harder final slice than `v5`

