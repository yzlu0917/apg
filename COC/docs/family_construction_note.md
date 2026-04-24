# Family Construction Note

本文件用于 `Object gate v0` 的最小 family 构造约束，避免后续把 artifact 当对象。

## Construction Policy

默认采用 **model-driven construction**：

- `generator model` 负责把 seed answer 改写成指定 family 的反事实样本
- `reviewer model` 负责判断是否真的满足 family target、是否混入 confounds
- `verifier` 只负责 correctness guardrail，不负责决定 family 是否成立

如果 reviewer 和 verifier 冲突，默认进入人工审查，而不是靠规则硬裁。

## F1. Substance Flip

### Target

保持答案风格基本不变，只引入可验证的内容错误或关键推理错误。

### Allowed Edits

- 替换一个关键数值、边界条件或代码语句
- 删除导致 correctness 失效的关键一步
- 在不改变整体写作风格的前提下制造 semantic error

### Forbidden Confounds

- 同时显著改变长度、语气或格式
- 把明显低质写法和内容错误绑在一起
- 引入无法客观验证的主观争议

### Audit Questions

1. 两个答案在风格上是否近似？
2. 标签差异是否主要来自内容 correctness，而不是表面质量？
3. verifier 是否能明确指出错误位置？

### Targeted Repair Note

如果 `substance_flip` 在 swap-balanced 审计里反复暴露出：

- wrong answer 基本复制了正确推理
- 只改了最后一个数字或返回值

则应切到 `substance_flip_targeted_v1`：

- 要求错误进入中间 reasoning step、operator 或 condition 本身
- 对 math，避免“全对推理 + 最后一位数字改掉”
- 对 code，优先 prompt-opposite logic，而不是微妙运行时 artifact

当前经验是：一旦错误位置从“最后输出 token”移到“中间语义步骤”，高容量 judge 的 swap-stability 会明显改善。

到当前为止，`substance_flip_targeted_v1` 已在两轮 fresh-seed 扩张里都实现了 `3/4` 的 reviewer+verifier 净增长。
因此在 bootstrap 现阶段，它应被视为默认的 substance growth protocol，而不是只在修旧 pair 时启用的例外 recipe。

## F2. Style Flip

### Target

保持内容等价，只改变答案风格，使其更 polished、更长、或更像“高级答案”。

### Allowed Edits

- 增加礼貌套话、结构化标题、解释性连接语
- 改写措辞，使其更流畅或更像推理答案
- 保持最终 correctness 与关键信息完全不变

### Forbidden Confounds

- 借风格改写偷偷修正或引入内容错误
- 加入新的 reasoning steps 导致事实含义变化
- 使用 judge 已知来源标记或显式模型自报家门

### Audit Questions

1. 两个答案是否在语义上等价？
2. 偏好差异是否只可能来自 style，而不该来自 correctness？
3. 是否出现长度、格式之外的隐性内容变化？

### Controlled Recipe Note

`style_flip` 在 bootstrap 当前阶段默认采用 `controlled_v1` 审计方向：

- 尽量避免把 pair 做成“明显更短、更像 brief prompt”对“明显更长、更完整”的对比。
- 优先使用措辞、节奏、变量命名、轻格式差异，而不是大长度差。
- 对 code 任务，优先做语义等价代码的轻格式/注释/命名差异，不优先做解释段落的堆砌。

若一个 `style_flip` pair 的主要对比来自：

- 大幅 verbosity gap
- 一边明显更贴合 `briefly / brief explanation`
- 一边在 substance 上更完整

则应视为 audit risk，而不是 clean style pair。

如果 `controlled_v1` 仍频繁保留：

- math 上的大长度差
- `brief explanation` 一侧明显更占优
- code 上的解释段落堆砌

则应升级到 `controlled_v2`：

- math: 两边都限制为短句、短答案
- code: 只允许轻格式 / 命名 / 注释差异，不允许 explanation-vs-code-only
- reviewer 对超出长度阈值的 pair 更严格

如果 `controlled_v2` 出现“长度差下降但 reviewer 0 pass”的情况，则应尝试 `controlled_v2.1`：

- 保持 brevity symmetry
- 允许更明确但仍表面的 style marker：
  - `Answer:` / `Final answer:`
  - `is` / `equals`
  - 轻量句式差异
- 目标不是把 pair 压成纯同义改写，而是在不引入额外 reasoning 的前提下保留可审的 style contrast

对 code 侧，不应直接复用 math-side `controlled_v2.1`。默认应改用 code-specific recipe：

- 允许的 style marker 优先级：
  - compact one-liner vs expanded multi-line layout
  - neutral variable naming contrast
  - mirrored harmless comments on both sides
- 禁止的退化形态：
  - comment-vs-no-comment
  - 一边明显更完整、更文档化
  - explanation paragraph vs code-only

当前 code-side 最佳起点是 `controlled_code_v1`：

- 鼓励：
  - generator expression / comprehension vs explicit loop
  - neutral variable naming contrast
  - 结构等价的 compact vs expanded layout
- 不鼓励：
  - 单边加注释
  - 只做极弱重命名且没有结构差

若 `controlled_code_v1` 在 swap-balanced 审计里暴露出“长结构答案在 swapped 后掉成 shorter choice”，则应收紧到 `controlled_code_v1_1`：

- 优先同结构布局差异
- 控制长度差更小
- 对大幅 loop-vs-comprehension 重写更严格

当前 code-side 的实践约定是：

- `controlled_code_v1`：默认高产 recipe，用于扩 code 候选池
- `controlled_code_v1_1`：默认干净子集 recipe，用于 audit-sensitive eval

也就是说，`v1.1` 不是简单“比 `v1` 更好”，而是显式用更低 pass rate 换更干净的 balanced subset。

## F3. Reasoning-Fluff

### Target

给错误答案加上“看起来更会推理”的包装，但不改变其真实 correctness。

### Allowed Edits

- 添加 chain-of-thought 风格的前缀或解释性过渡
- 加入看似系统化但实际不修复错误的 reasoning scaffold
- 强化答案的自信表达，但不新增真实有效证据

### Forbidden Confounds

- 通过额外 reasoning 实际把答案修对
- 让错误变得更明显而失去迷惑性
- 使用明显 prompt injection 或过强攻击 token

### Audit Questions

1. reasoning 包装是否没有改变真实 correctness？
2. 包装是否足以让 judge 误以为答案更可靠？
3. verifier 是否仍能指向原始错误，而 reviewer 仍判断其只是 reasoning-fluff？

## Shared Audit Rule

如果一个样本同时违反两项以上 forbidden confounds，则默认 `needs_revision`，不得进入 `object_dev_v0`。

## Minimal Review Flow

1. generator model 按 family 指令生成候选 pair。
2. reviewer model 给出：
   - family 是否成立
   - 是否混入 style/content confound
   - 是否建议 `pass / fail / needs_revision`
3. verifier 只检查 correctness 是否与目标标签一致。
4. 对 reviewer 高不确定或 reviewer/verifier 冲突样本做人工复核。
