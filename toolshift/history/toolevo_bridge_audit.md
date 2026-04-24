# ToolEVO Bridge Audit

- Benchmark: `toolevo_bridge_benchmark`
- Cases: `8`
- Views: `32`
- Split: all cases are `unambiguous_core` with explicit clean / positive version v1 / positive version v2 / negative legacy-deprecate views.
- Provenance: bridge microcases are derived from ToolEVO public API variation definitions and few-shot usage trajectories rather than imported end-to-end ToolQA answers.

## Sources

- `toolevo_paper`: paper | https://arxiv.org/abs/2410.06617
  - ToolEVO paper introducing the ToolQA-D benchmark and API-kernel evolution settings Pc, Ps_in, and Ps_OOD.
- `toolevo_readme`: repository | https://github.com/Chen-GX/ToolEVO
  - Official ToolEVO repository README describing ToolQA-D, public code/data release, and the api_kernel_version controls.
- `toolevo_api_vary`: code | https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/api_vary.py
  - Official ToolEVO API variation file mapping legacy ToolQA tool names and argument schemas to Ps_in and Ps_OOD variants.
- `toolevo_prompts`: code | https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/prompts.py
  - Official ToolEVO prompt file containing UpdateTool examples that document legacy-to-current tool migration behavior.
- `toolevo_few_shot_airbnb`: code | https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/few_shots/toolqa_easy/airbnb-easy.py
  - ToolEVO few-shot trajectories showing LoadDB, FilterDB, and GetValue usage on ToolQA-D airbnb tasks.
- `toolevo_few_shot_dblp`: code | https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/few_shots/toolqa_easy/dblp-easy.py
  - ToolEVO few-shot trajectories showing LoadGraph and NodeCheck usage on ToolQA-D dblp tasks.

## Case Families

- `toolevo_bridge`: legacy-to-current tool migrations imported from ToolEVO `api_vary.py` for retrieval, database, graph, SQL, and Python tools.

## Negative Policy

- `negative_legacy_deprecate` views intentionally expose only the legacy deprecated tool and unrelated distractors.
- Admissible actions are `ask_clarification` or `abstain`, because ToolEVO's actual recovery path depends on discovering a replacement tool through an interactive warning loop that is outside the one-step TOOLSHIFT protocol.
