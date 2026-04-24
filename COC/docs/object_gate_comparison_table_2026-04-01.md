# Object Gate Comparison Table 2026-04-01

## Purpose

把当前 `v2/v3/v4/v5` 的 object-gate 主结果压缩成 paper-facing 比较表，并明确哪一版适合作为当前 headline slice。

## Comparison Table

| Slice | Rows | Family Mix | Panel Type | 0.6B base pair-strict | 0.6B critic pair-strict | 4B base pair-strict | 4B critic pair-strict | Current Read |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| `v2` | `12` | `8 substance + 4 style` | fully matched | `0.0` | `0.0` | `0.583` | `0.667` | first clean merged slice after audited style control |
| `v3` | `12` | `8 substance + 4 style` | fully matched | `0.0` | `0.0` | `0.833` | `0.917` | first slice showing strong capacity-sensitive gain after targeted substance repair |
| `v4` | `15` | `11 substance + 4 style` | 4B only | n/a | n/a | `0.867` | `0.933` | larger high-cap readout; useful growth evidence but not yet matched |
| `v5` | `18` | `14 substance + 4 style` | fully matched | `0.0` | `0.0` | `0.833` | `0.944` | current best fully matched audit-controlled slice |

## Selection Rule

当前主 slice 选择规则不是“谁的单个 4B 数最高”，而是：

1. 必须是 audited merged slice。
2. 尽量是 fully matched cross-cap panel。
3. 必须保留清晰的 capacity split，而不是 generic easier slice。
4. 在满足以上条件时，优先更大的 slice。

按这个规则：

- `v2` 太早，说明对象存在，但 high-cap signal 还不够强。
- `v3` 首次达成可信的 fully matched capacity split。
- `v4` 在 high-cap 上更大更强，但缺少 matched `0.6B`，所以不能做主 headline slice。
- `v5` 同时满足更大 + fully matched + capacity split preserved，因此优先于 `v3`。

## Why `v5` Wins

### 1. 它比 `v3` 更大，但没有把 slice 做容易

- `v3 -> v5`：
  - `0.6B base`: `0.0 -> 0.0`
  - `0.6B critic`: `0.0 -> 0.0`
  - `4B base`: `0.833 -> 0.833`
  - `4B critic`: `0.917 -> 0.944`

如果 `v5` 只是变成 generic easier slice，`0.6B` 也应该同步改善；但它没有。

### 2. 它保留了 clean claim boundary

- `v5` 仍然只基于 audited `style_flip + substance_flip`。
- `reasoning_fluff` 仍然 deferred，没有被重新塞回 headline。
- `style_flip` 沿用 audited subset，而不是重新放大到未审计 recipe。

### 3. 它最适合当前 headline

当前最稳的 headline 不是 “ranking inversion 已被证明”，而是：

> 在一个 order-balanced、audit-controlled 的 object slice 上，高容量 judge 与低容量 judge 出现稳定的 family-sensitive separation，而这一 separation 不能由 generic easier slice 解释。

`v5` 是当前最适合承载这句话的 slice。

## Claim Status

### Supported Now

- `object claim`: supported
  - clean object exists
  - balanced protocol 下 capacity split 仍在
  - larger matched slice `v5` 复现并扩展了 `v3` 的主结论

### Conditional Only

- `method claim`: conditional
  - 还没进入 conversion-gate 级别的 utility / decision gain 证明
- `deployment claim`: not supported
  - 当前只在 `math + code` 的 audited bootstrap slice 上成立

## Recommended Paper Use

- 主文 object-gate 表格默认引用 `v5`。
- `v3` 作为“first matched breakthrough”放进叙事或 appendix。
- `v4` 作为 “intermediate larger high-cap step” 使用，不单独承担主 claim。

