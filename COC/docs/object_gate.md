# Object Gate v0

## Goal

在最小成本下判断：`COC` 是否对应一个真实、可测、且不同于 mean accuracy 的监督对象。

## Frozen Scope

- domains: `math`, `code`
- active families: `substance_flip`, `style_flip`
- deferred family: `reasoning_fluff`
- source tasks: 仅限 objective / semi-objective；family 构造和语义审查默认由模型完成
- judge pool: 最少 `4` 个 judge variants，优先使用本地 Qwen3 小模型和 prompt variants

## Minimal Closed Loop

1. 从每个 domain 先选一小批有 verifier 的 seed tasks。
2. 用 generator model 为每个 seed task 构造当前激活 family 的反事实 pair。
3. 用 reviewer model 做语义审查与 family 归因，再用 verifier 检查 correctness guardrail，并做少量人工审查确认 family fidelity。
4. 运行最小 judge pool，得到 per-example verdict。
5. 计算 `overall accuracy`、`COC`、`worst-family miss`、`miss overlap`。
6. 判断是否存在 object signal。

## Required Outputs

- 一个 `object-dev-v0` manifest
- 一份 family construction note
- 一份人工审查样本与结论
- 一张 `accuracy vs COC` 对照表或散点
- 一份 Object gate go/no-go 记录

## Minimal Acceptance Rule

Object gate 默认通过至少需要满足以下两条：

1. 保留下来的 family 在人工审查中是干净的，不是明显 artifact。
2. 至少出现一组 judge 在 overall accuracy 上接近，但在 `COC` 或 `worst-family miss` 上明显分离。

## Failure Handling

- 如果 family fidelity 不够：先修 generator/reviewer protocol 或删 family，不扩 judge。
- 如果 judge 差异太弱：先增 prompt / aggregation heterogeneity，再考虑引入更强 judge。
- 如果 `COC` 与 accuracy 基本等价：停止往 method / scale 推进，转入 evaluation-principle fallback。

## Bootstrap Status

- `style_flip`: 当前在 math/code 上都最干净，已进入 bootstrap 主线。
- `substance_flip`: 当前可用，但 code slice 仍需继续压 reviewer/generator 边界。
- `reasoning_fluff`: 当前跨多个 seed 持续过不了 verifier-backed Object gate，已转为 deferred family。
