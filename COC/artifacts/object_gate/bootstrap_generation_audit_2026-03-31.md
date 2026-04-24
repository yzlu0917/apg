# Bootstrap Generation Audit 2026-03-31

## Run Scope

- seeds used: `math_001`, `math_002`
- families: `substance_flip`, `style_flip`, `reasoning_fluff`
- generator: `Qwen3-4B`
- reviewer: `Qwen3-4B`

## What Worked

- `style_flip` 在两个 math seed 上都生成了可用样本。
- `substance_flip` 至少生成出一条符合目标的样本：`math_001__substance_flip`。
- 整条 generator -> reviewer -> manifest 写入链路已经跑通。

## What Failed

- `reasoning_fluff` 在两个 math seed 上都塌成“更啰嗦但仍然正确”的样本，不是真正的 wrong-but-persuasive family。
- `math_002__substance_flip` 生成器没有按要求制造 objective error，结果更接近 style change。
- reviewer 存在自洽性问题：
  - 有时 `review_family_valid = true`，但 `reviewer_decision = fail`
  - 有时会接受明显不满足 family hard constraint 的样本

## Interpretation

这说明：

1. model-driven construction 是可行的，但不能把单个 reviewer model 当成充分审查器；
2. `style_flip` 比 `reasoning_fluff` 更容易在 phase 0 早期形成干净对象；
3. `reasoning_fluff` 需要更强 prompt、更强 reviewer，或更难的 domain/task 才可能成立；
4. 当前还不能据此扩到大样本，否则会把 family noise 放大。

## Immediate Next Fixes

- 把 reviewer 从 generator 解耦，优先尝试更强 reviewer。
- 对 `reasoning_fluff` 加硬约束：
  - wrong answer must remain wrong under verifier
  - verbose answer alone is insufficient
- 从 math 扩到 code seed，看 `reasoning_fluff` 是否在 code 上更容易成立。

## Additional Reviewer Check

后续又补做了一个小对照：

- generator: `Qwen3-4B`
- reviewer: `Qwen3-8B`
- scope: `math_001` 上的三个 family

结果：

- 8B reviewer 没有解决核心问题。
- 三条样本都出现了 `review_family_valid = true` 但 `reviewer_decision = fail` 的结构化矛盾。

结论：

- 当前 reviewer 不是单纯“能力不足”，而是**协议不稳定**。
- 后续所有模型审查结果都必须经过一致性审计脚本过滤，不能直接把 reviewer 字段当真标签。

## API Reviewer Outcome

在补充 API reviewer 并收紧 `style_flip` 指令后：

- `math_001` 上得到的结果更符合预期：
  - `substance_flip`: pass
  - `style_flip`: pass
  - `reasoning_fluff`: fail
- 一致性审计结果：`flagged=0`

这说明 API reviewer 明显优于当前本地 reviewer，至少在 bootstrap 阶段更适合作为主审查器。

## Code Slice Outcome

对 `code_001` 和 `code_002` 的 API reviewer 结果：

- `style_flip`: `2/2 pass`
- `reasoning_fluff`: `2/2 fail`
- `substance_flip`: `1/2 pass`

解释：

- `style_flip` 是当前最稳定、最容易形成干净 family 的对象。
- `reasoning_fluff` 目前在 math 和 code 上都没有成功生成出 clean object，问题主要在 generator，不在 reviewer。
- `substance_flip` 基本可做，但在某些 code case 上 reviewer 仍会过度解释 family 边界，说明 protocol 还需继续压实。
