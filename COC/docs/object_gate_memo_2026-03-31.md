# Object Gate Memo 2026-03-31

## Decision

**结论：`GO`, but narrow.**

当前可以继续推进 Object gate 主线，但主线范围应暂时限定为：

- domains: `math`, `code`
- active families: `style_flip`, `substance_flip`
- deferred family: `reasoning_fluff`

这不是“Object gate 已经完全通关”，而是：

- 已经有足够证据说明当前 object 不是空的，值得继续推进；
- 但还没有足够证据把强 headline 升级成“accuracy ranking inversion 已被稳定证明”。

## What Is Already Supported

### 1. 当前 object slice 是干净的

- active slice `v3` 大小为 `12`
- 其中：
  - `style_flip = 9`
  - `substance_flip = 3`
- 这些样本都经过：
  - generator construction
  - API reviewer audit
  - verifier consistency check

### 2. order-balanced 后 object signal 仍然存在

在 unbalanced 读法里：

- `Qwen3-0.6B base`: overall `0.25`, COC `0.5`
- `Qwen3-0.6B critic`: overall `0.25`, COC `0.5`
- `Qwen3-4B base`: overall `0.833`, COC `0.889`
- `Qwen3-4B critic`: overall `0.667`, COC `0.778`

最关键的不是 overall accuracy 本身，而是：

- 所有 judge 在 `substance_flip` 上目前都是 `1.0` accuracy
- 区分度几乎全部集中在 `style_flip`
- `Qwen3-0.6B` 两个版本对 `style_flip` 的 miss 都是 `1.0`
- `Qwen3-4B base` 在 `style_flip` 上 miss 是 `0.222`
- `Qwen3-4B critic` 在 `style_flip` 上 miss 是 `0.444`

但在 `original + swapped` 的 order-balanced 读法里：

- `Qwen3-0.6B base`: balanced directional `0.125`, pair-strict `0.0`
- `Qwen3-0.6B critic`: balanced directional `0.125`, pair-strict `0.0`
- `Qwen3-4B base`: balanced directional `0.667`, pair-strict `0.417`
- `Qwen3-4B critic`: balanced directional `0.583`, pair-strict `0.417`

这说明：

- 当前 object 不只是顺序幻觉，因为 `4B` 在 balanced 读法下仍显著高于 `0.6B`
- 但 object 的有效宽度比 unbalanced 读法窄得多
- 未来 gate 读数必须优先看 balanced protocol，而不能继续单看单边 accuracy

### 3. `style_flip` 仍是当前最难、也最主要的 active family

在 balanced pair-strict 读法下：

- `substance_flip = 0.667`
- `style_flip = 0.333`

这说明：

- `style_flip` 仍然是 object signal 的主要来源
- 但它的严格通过率只有 `1/3`
- `substance_flip` 没有塌，但样本仍过少，不能单独撑起 coverage story

## What Is Not Yet Supported

### 1. 还没有达到强版本的 ranking inversion 证据

当前我们还没有找到一对 judge 满足：

- overall accuracy 非常接近
- 但 COC / worst-family miss 明显不同

所以目前还不能把 headline 直接写成：

> accuracy is insufficient because we already observe stable rank inversion

更准确的说法是：

> current evidence shows meaningful family-wise differentiation, and part of it survives order balancing, but stable ranking inversion still needs a larger and cleaner slice.

### 2. prompt-style effect 目前不够稳，不能当强证据

在 unbalanced 读法里，`Qwen3-4B base` 明显优于 `Qwen3-4B critic`。

但在 balanced pair-strict 读法里，两者都为 `0.417`。

这意味着：

- prompt-style 确实可能影响 judge 行为
- 但目前它还没有稳定到可以写成 headline-level 证据
- 当前更稳的 separation 还是 capacity gap，而不是 prompt gap

### 3. 当前 object 仍偏窄

- active object 仍主要由 `style_flip` 驱动
- `substance_flip` 当前只占 `3/12` pair
- `reasoning_fluff` 仍然 deferred

## Gate Reading

### Object gate

**状态：partial pass / continue**

已满足：

- 有干净 active slice
- 有 family-wise differentiation
- 在 order-balanced 读法下，`4B` 和 `0.6B` 仍可分离

未满足：

- 强版本的 inversion / matched-accuracy spread
- 更宽的 family coverage
- 对 prompt-style effect 的稳定支持

因此当前决策是：

- 继续扩大 active slice
- headline 仍停在窄版本 object claim
- 不进入 method/deployment claim

### Audit gate

**状态：started, not passed**

目前已经补做了第一轮 answer-order control，结论是：

- `Qwen3-0.6B` 两个 judge 几乎是严重的 A-position bias
- `Qwen3-4B` 两个 judge 虽然明显更好，但在 `style_flip` 的 tie cases 上仍有明显 order sensitivity

在 balanced readout 下，情况仍然不够好：

- `Qwen3-4B` 的 `style_flip` pair-strict 只有 `0.333`
- `Qwen3-0.6B` 在 pair-strict 下直接为 `0.0`
- style-specific length audit 显示：
  - `0.6B` 主问题是 position bias
  - `4B` 在非 tie 时更常偏向更短答案，而不是更长答案

因此当前还不能说 `style_flip` 已经完全通过审计。更准确的说法是：

- object signal 存在
- 但该 object signal 仍部分混有 order artifact 与 briefness / prompt-fit bias
- 所以下一步必须用 order-balanced 协议继续推进，而不是直接写强结论

## Immediate Next Move

1. 将 future eval 默认切到 order-balanced paired protocol。
2. 继续扩 active families 的样本量，优先补 `substance_flip`。
3. 在更大的 balanced slice 上再次检查：
   - pair-strict accuracy
   - balanced COC
   - worst-family pair-strict miss
   - 是否出现 closer-overall / wider-COC pairs
4. 对 `style_flip` 做受控 recipe，区分真正 style signal 与 `brief explanation` 指令诱导出的 shorter-answer bias。

## Bottom Line

当前最诚实的表述是：

**这个项目已经证明“object 方向值得继续”，而且部分信号经 order balancing 后仍然存在；但 headline 仍必须保持窄版本，Audit gate 目前依然未过。**
