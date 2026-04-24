# ToolShift Reviewer Concern Bullets

## Purpose

This note is a concise reviewer-facing map of the strongest predictable attacks on the current \toolshift{} paper and the concrete evidence now available in the repository to answer them.

## 1. ``The benchmark is too small and family-sensitive.''

- True boundary:
  - blind panel is still small: `24 cases / 48 views / 6 family tags`
  - paper should not be framed as a large-$N$ leaderboard
- Current evidence:
  - family bootstrap and vendor bootstrap are now reported
  - leave-one-family-out analysis shows blind pressure is not only `slack_auth`
  - scaffold blind `NOS=0.727`, family bootstrap CI `[0.444, 0.917]`
  - removing `slack_auth` raises scaffold `NOS` only to `0.800`
- Where to point:
  - `artifacts/real_evolution_blind_stability_v1/summary.json`
  - [appendix.tex](/cephfs/luyanzhen/apg/toolshift/paper/sections/appendix.tex)

## 2. ``Your protocol hides subjectivity inside canonical labels.''

- True boundary:
  - we still do not claim full inter-annotator agreement
  - this remains a real remaining weakness
- Current evidence:
  - deterministic evaluator is now complemented by protocol reliability analysis
  - dev/blind panels report single-action vs multi-action views, dual-control negatives, and source-support structure
  - blind split sensitivity explicitly shows why single-action negatives would trivialize `NOS`
- Where to point:
  - `artifacts/real_evolution_protocol_reliability_dev_v1/summary.json`
  - `artifacts/real_evolution_protocol_reliability_blind_v1/summary.json`

## 3. ``This is only hard for your own methods.''

- Current evidence:
  - external bridges now include API-Bank, BFCL, ToolEVO
  - public-model snapshots now include:
    - `Qwen3-8B`
    - `Qwen3-4B`
    - `Llama-3.2-3B-Instruct`
  - a retrieval+rerrank document baseline is also included
  - public baselines drop on the same blind negative families
- Where to point:
  - `artifacts/real_evolution_blind_qwen3_8b_v1/summary.json`
  - `artifacts/real_evolution_blind_qwen_prompt_4b_v1/summary.json`
  - `artifacts/real_evolution_blind_llama32_3b_v1/summary.json`
  - `artifacts/real_evolution_blind_doc_retrieval_v1/summary.json`
  - [appendix.tex](/cephfs/luyanzhen/apg/toolshift/paper/sections/appendix.tex)

## 4. ``Your scaffold baseline just exploits textual cues.''

- Correct response:
  - yes, the current strongest story is explicitly about `schema-visible textual/contract cue grounding`
  - we should not claim hidden-shift robustness
- Current evidence:
  - name masking barely hurts
  - description / contract masking sharply hurts
  - impossible-shadow boundary tests fail completely for the strongest scaffold baseline
- Where to point:
  - `artifacts/real_evolution_masking_sensitivity_v1/summary.json`
  - `artifacts/real_evolution_boundary_evidence_v1/summary.json`

## 5. ``Why should I believe your SCC story if it failed?''

- Correct response:
  - the paper is no longer a method-win paper
  - SCC is retained only as a decisive negative result
- Current evidence:
  - final teacher-distilled bottleneck run improves dev `NOS` only from `0.606` to `0.636`
  - `CAA+` and `POC` remain `0.000`
  - go/no-go bar was not met, so the method story was intentionally demoted
- Where to point:
  - `artifacts/real_evolution_family_holdout_teacher_distilled_v1/summary.json`
  - [05_results.tex](/cephfs/luyanzhen/apg/toolshift/paper/sections/05_results.tex)

## 6. ``What is the safest final framing?''

- Recommended one-line framing:
  - `ToolShift is a benchmark and evaluation protocol for canonical semantic actions under real API evolution, with a strong scaffold baseline and a clear negative result for SCC-style learned routes.`
- Strongest empirical claim:
  - `schema-visible capability-gap inhibition is a distinct and measurable challenge`
- Claims to avoid:
  - universal tool robustness
  - hidden backend shift robustness
  - learned invariance success
