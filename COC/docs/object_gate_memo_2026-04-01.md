# Object Gate Memo 2026-04-01

## Decision

**结论：`GO`, narrow but now materially stronger than the 2026-03-31 readout.**

当前可以继续推进 Object gate 主线，而且当前主 slice 已从 `v3` 升级到 `v5`：

- domains: `math`, `code`
- active families: `style_flip`, `substance_flip`
- deferred family: `reasoning_fluff`
- current best matched slice: `clean_merged_slice_v5`

这仍然不是“Object gate 已完全通关”，但已经不只是“值得继续”的弱状态。更准确地说：

- 对象存在，且在更大的 fully matched slice 上仍成立；
- object signal 不能被 generic easier slice 解释；
- headline 仍应停在 object claim，不上升到 method / deployment claim。

## What Is Already Supported

### 1. 当前 headline slice 是 clean and matched

`v5` 现在满足：

- audited merged slice
- order-balanced protocol
- fully matched cross-cap panel

具体规模：

- total rows: `18`
- `substance_flip = 14`
- `style_flip = 4`

### 2. capacity split 在更大 slice 上依然成立

`v5` balanced fullpanel:

- `Qwen3-0.6B base`: directional `0.389`, pair-strict `0.0`
- `Qwen3-0.6B critic`: directional `0.389`, pair-strict `0.0`
- `Qwen3-4B base`: directional `0.917`, pair-strict `0.833`
- `Qwen3-4B critic`: directional `0.972`, pair-strict `0.944`

最关键的事实不是某一条 4B 数字，而是：

- 两条 `0.6B` 在 `v3` 和 `v5` 上都停在 `pair-strict=0.0`
- `4B` 在 `v5` 上保持高位，且 `critic` 继续上升

因此当前最稳的 object-gate 读法是：

- low-capacity judges 仍被 order-sensitive collapse 主导
- high-capacity judges 能稳定利用 audited object signal

### 3. `v5` 比 `v3` 更适合做主结果

`v3` 的作用是：

- 首次证明 targeted substance repair 带来的是 capacity-sensitive gain

`v5` 的作用是：

- 在更大 slice 上保留了同样的 cross-cap separation
- 因而更适合作为当前 paper-facing 主 slice

换句话说：

- `v3` 是 first clean breakthrough
- `v5` 是 current best matched reference

## What Is Not Yet Supported

### 1. ranking inversion 仍不能当 headline

当前 strongest supported claim 仍然不是：

> accuracy ranking is already stably inverted

因为我们还没有把“overall accuracy 接近但 family-wise object metric 明显反转”的 judge pair 做成主要结果。

当前更诚实的写法仍是：

> balanced, audit-controlled object slices reveal stable family-sensitive separation that plain aggregate accuracy misses.

### 2. method claim 仍未通过 conversion gate

我们现在支持的是对象与测量层，而不是实用方法层：

- 还没有 utility gain
- 还没有 routing / selection decision gain
- 还没有 conversion-level deployment evidence

### 3. 审计并未完全结束

虽然 `v5` 是 current best slice，但这不等于 Audit gate 全过。
当前更准确的状态是：

- 对象存在且经过了更强控制
- headline slice 已经够干净用于 object claim
- 但若要升级 method/deployment story，仍需更多 audit / conversion evidence

## Gate Reading

### Object Gate

**状态：pass**

当前已满足：

- clean audited object slice
- larger fully matched panel
- stable cross-cap separation
- generic easier-slice 解释被显著削弱

因此 Object gate 不再只是 `partial pass`，而是可以记为：

- `pass for narrow object claim`

### Audit Gate

**状态：in progress, not passed globally**

当前 headline slice 已足够干净支撑 narrow object claim，但 Audit gate 仍未全局通过，因为：

- style 信号仍只来自 audited subset，而非更广 recipe
- `reasoning_fluff` 仍 deferred
- broader deployment-style artifact 排查尚未展开

### Conversion Gate

**状态：not started**

当前没有 conversion 证据，因此 method claim 继续保持 conditional。

## Recommended Story

当前推荐对外叙事是：

1. 先讲 object：我们识别出一个比 aggregate accuracy 更敏感的 judge weakness object。
2. 再讲 audit：这个 object 在 order-balanced、audit-controlled slice 上仍成立。
3. 最后把 method/deployment 明确写成后续问题，而不是当前贡献。

## Immediate Next Move

1. 用 `v2/v3/v4/v5` 写 paper-facing comparison table。
2. 用 `v5` 作为 current best matched slice，整理 object-gate 主表和简短解读。
3. 只在确有 coverage 缺口时，继续扩 `substance_flip_targeted_v1`。

## Bottom Line

当前最诚实的表述是：

**Object gate 已经以窄版本通过；`clean_merged_slice_v5` 是当前 best fully matched reference slice。项目下一步应进入 paper-facing synthesis，而不是继续局部 sweep。**

