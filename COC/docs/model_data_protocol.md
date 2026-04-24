# Model-Driven Data Protocol

## Goal

为 `Object gate v0` 提供最小可执行的数据生产协议，明确哪些工作由模型做，哪些工作只作为 guardrail。

## Roles

### Generator Model

职责：

- 接收 seed task、seed answer、目标 family
- 生成满足 `F1/F2/F3` 的反事实 pair
- 输出简短自检说明：它试图保持什么、不改变什么

默认候选：

- `Qwen3 4B Instruct`
- `Qwen3 1.7B Instruct`

### Reviewer Model

职责：

- 判断 family 是否真的成立
- 判断是否混入 confounds
- 给出 `pass / fail / needs_revision`
- 标记风险类型：`style_leakage`、`semantic_drift`、`reasoning_fix`、`source_cue`

默认候选：

- `Qwen3 4B Instruct`
- 可选 stronger reviewer：项目提供的 OpenAI-compatible API endpoint

### Verifier

职责：

- 只检查 correctness guardrail
- 不负责裁定 family target 是否成立

例子：

- math: symbolic / numeric check
- code: execution / unit test / reference output

## Pipeline

1. 选 seed task 与 reference answer。
2. generator model 为指定 family 生成候选 pair。
3. reviewer model 审查 family fidelity。
4. verifier 检查 correctness 是否与目标标签一致。
5. reviewer/verifier 冲突样本进入人工复核。
6. 通过样本写入 `object_dev_v0` manifest。

## Acceptance Policy

- generator 自检通过不代表样本可用。
- reviewer `pass` 且 verifier 不冲突，才可进入 `object_dev_v0`。
- reviewer `needs_revision` 的样本可以回流给 generator 重写一次。
- 同一 seed task 最多重写两轮；超过两轮仍不干净则弃用。

## Why This Protocol

- family 构造本质上是语义编辑问题，模型比规则更适合。
- reviewer 把“构造”和“审查”拆开，降低 generator 自说自话。
- verifier 只做 correctness guardrail，避免把 easy rule 误当作 family definition。
- 当本地 reviewer 协议不稳时，可以用 stronger API reviewer 做 Object-gate 审查，但仍需走一致性审计。
