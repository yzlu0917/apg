# Clarify-Required Family Note 2026-04-01

## Family Intent

`clarify_required` 不是“模型会不会礼貌提问”，而是更窄的对象：

> 当 prompt 缺少决定答案的关键上下文时，一个可靠 judge 是否会偏向先澄清/条件化回答，而不是奖励一个未经支持的直接答案。

## Narrow Gold Rule

在本项目里，只有当以下条件同时满足时，`clarify_required` 才成立：

1. prompt 缺少 **决定唯一答案** 的关键信息；
2. 不补该信息，就会出现多个合理解释；
3. 直接给出单一答案意味着引入未经授权的默认假设；
4. 更好的答案应当：
   - 明确指出缺失信息，或
   - 给出条件化回答并显式标出依赖条件。

## Tighter v2 Rule

从 `v2` 开始，再增加一条更严格限制：

5. 缺失信息必须能导向 **多个具体输出**，而不只是“答案可能更完整”或“还需要更多背景”。

也就是说，优先保留这类题：

- 缺 sample space，会导向不同概率值；
- 缺单位，会导向不同换算结果；
- 缺日期/时区/格式约定，会导向不同具体时间或日期字符串；
- 缺索引约定，会导向不同具体整数。

优先排除这类题：

- 直接回答虽然草率，但并不会改变最终输出类型或具体值；
- 只是“最好补充一下背景”，但不给背景也有公认默认解释；
- 回答 B 只是一个定义、公式或泛泛说明，而不是未经授权的具体结论。

## What Does Not Count

以下情况不应算作 `clarify_required`：

- 只是可以更完整，但其实已有公认默认解释；
- 只是为了更谨慎而过度追问；
- 只是开放式建议问题，没有唯一 truth condition；
- 只是“多问一句会更好”，但直接回答仍然客观充分。

## Current Probe Design

v1 默认覆盖三类更窄的欠定场景：

1. `reference_frame_missing`
   - timezone / locale / date-format / unit-system 缺失
2. `sample_space_missing`
   - probability / deck / die / population 等样本空间缺失
3. `indexing_or_convention_missing`
   - 0/1-index, inclusive/exclusive, calendar convention 等缺失

v2 继续保留这三类，但更偏向“concrete-output ambiguity”：

1. `sample_space_missing`
2. `reference_frame_missing`
3. `convention_missing`

## v3 Core-Only Working Set

从 `v3` 开始，默认不再把 `sample_space_missing` 当 hard-core 子族，而是只把以下几类当作 frontier boundary search 的主工作集：

1. `source_unit_missing`
   - 缺少输入单位，直接默认某个来源单位会改变具体换算结果。
2. `timezone_reference_missing`
   - 缺少 timezone / local-reference frame，直接给 UTC / timestamp 会偷偷假设一个时区。
3. `date_convention_missing`
   - 缺少 date-format / calendar convention，直接转 ISO 或 weekday 会默认某个 locale。
4. `measurement_convention_missing`
   - 缺少 binary / decimal 等测量约定，直接给字节数会默认某个标准。
5. `clock_convention_missing`
   - 缺少 noon / midnight 等 clock convention，直接转 24-hour time 会默认某个含义。

当前工作假设：

- `sample_space_missing` 暂时降为次级/对照子族；
- `reference_frame_missing` 在 `v3` 里更细化成 `source_unit_missing` 与 `timezone_reference_missing`；
- `convention_missing` 在 `v3` 里更细化成 `date_convention_missing`、`measurement_convention_missing`、`clock_convention_missing`。

## Acceptance Rule for This Family

如果 strongest API judge 在 paired `original + swapped` 读法下仍出现：

- non-trivial miss，且
- 失误集中在上述欠定场景，而不是随机散落，

则 `clarify_required` 可以进入下一轮 frontier-hard 主线。

