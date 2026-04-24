# CNT Research Workspace

- 你可以使用/cephfs/shared/hf_cache/hub/Qwen3* 系列的模型（开始实验可以使用1.7B或4B的模型），可以暂时不考虑多模型交叉（一定需要的话你可以告知用户，用户方下载）
- 需要的数据可以下载放到data目录下
- 可以使用的conda环境是infer（大部分环境已经装好了，如果还需要一些额外的包或者工具和用户确认）
- 如果你需要api调用来做数据或是别的这里也给你提供（需要给出用量和金额预算）
deepseek-v3.2:
  base_url: https://ark.cn-beijing.volces.com/api/v3
  endpoint: ep-20251213141929-gk2jb
  api_key: 8da5e4ba-59ad-47af-8f87-005fd1d1641b

## Current Reading

- 最新研究状态以 `history/` 为准：
  - [progress.md](/cephfs/luyanzhen/apg/cnt/history/progress.md)
  - [results.md](/cephfs/luyanzhen/apg/cnt/history/results.md)
  - [insights.md](/cephfs/luyanzhen/apg/cnt/history/insights.md)
  - [proposal_update_brief.md](/cephfs/luyanzhen/apg/cnt/history/proposal_update_brief.md)
  - [proposal_update_after_week3.md](/cephfs/luyanzhen/apg/cnt/history/proposal_update_after_week3.md)
- 当前 Week 3 的正式叙事入口：
  - [week3_negative_branch.md](/cephfs/luyanzhen/apg/cnt/history/week3_negative_branch.md)
- 当前 LaTeX 稿件入口：
  - [main.tex](/cephfs/luyanzhen/apg/cnt/paper/neurips/main.tex)
- 当前 accepted reading：
  - Week 1–2 成功，object 已站住
  - Week 3 暂时收束为 clean negative / partial-result branch，而不是 training win
  - Week 4–6 还不能算完成
  - 当前已接受 `A` 路线：默认转写作收束，不继续常规 Week 3 recipe sweep；只有在出现结构上明显不同的新 family 时才重开 Week 3

## Week 1 Status

- 已按 proposal 启动 `Synthetic CounterTrace` Week 1 主线。
- 运行命令：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_week1_synthetic.py --num-instances 48 --sigma 0.35 --output-dir outputs/week1_20260309_run01
```

- 结果文件：
  - `outputs/week1_20260309_run01/synthetic_summary.json`
  - `outputs/week1_20260309_run01/synthetic_rows.jsonl`
- 研究记录：
  - `history/progress.md`
  - `history/results.md`
  - `history/insights.md`

## CounterTrace-mini(math)

- 已启动真实域 `CounterTrace-mini(math)`，当前数据源为 `GSM8K test`。
- 数据下载位置：
  - `data/gsm8k/test.jsonl`
- 运行命令：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_countertrace_mini_math.py --max-examples 16 --target-successes 4 --max-new-tokens 220 --output-dir outputs/countertrace_mini_math_20260309_run01
```

- 结果文件：
  - `outputs/countertrace_mini_math_20260309_run01/math_summary.json`
  - `outputs/countertrace_mini_math_20260309_run01/math_traces.jsonl`
  - `outputs/countertrace_mini_math_20260309_run01/math_success_traces.jsonl`

## Math Stage A Pilot

- 已启动真实域 `N_t` 估计 pilot。
- 运行命令：

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate infer
python scripts/run_math_stage_a.py --max-traces 4 --max-candidates-per-trace 3 --continuation-max-new-tokens 220 --edit-max-new-tokens 48 --output-dir outputs/math_stage_a_20260309_run01
```

- 结果文件：
  - `outputs/math_stage_a_20260309_run01/stage_a_math_summary.json`
  - `outputs/math_stage_a_20260309_run01/stage_a_math_records.jsonl`
