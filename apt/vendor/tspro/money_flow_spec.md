# Net Money Flow — 设计说明（Agent 模式重设计）

## 目标
实现并验证“净资金流 (Net Money Flow)”指标的可重复计算与聚合接口，形成可扩展的代码骨架，便于后续引入更多资金流指标。

## 关键约束（Agent 模式）
- 当前任务仅实现并验证 Net Money Flow。其他指标（MFI、Level-2 等）暂不实现。
- 代码需具备清晰的输入/输出契约、容错处理、可批量运行接口和简单单元测试。
- 避免在模块顶层强制依赖环境库（如 pandas），尽量使用懒加载以便在受限环境中导入模块。

## 接口契约（Contract）
- 函数：`compute_net_money_flow(df, *, code_col=None, date_col='date', min_range=1e-6)`
  - 输入：pandas.DataFrame，必须包含列（高、低、收盘、成交额）；推荐列名：`high, low, close, amount`。若为多只股票，应包含 `code` 列或通过 `code_col` 指定。
  - 输出：DataFrame（原始记录副本或排序副本），额外新增列 `net_money_flow`（数值，float），表示当日净资金流；并保留 `code` 与 `date` 列以便后续聚合。
  - 错误模式：当缺少必需列时抛出 ValueError；当数值异常（NaN）时返回对应行 NaN 或 0（可配置）。
  - 成功条件：输出列 `net_money_flow` 存在，且对已知输入能产生可验证数值。

- 函数：`aggregate_market_flow(df, *, code_col=None, amount_col='amount')`
  - 输入：含 `net_money_flow` 的 DataFrame
  - 输出：聚合结果 dict：`{ 'market_net_flow': float, 'market_total_amount': float, 'flow_strength': float }`

## 数据格式示例
- 单只股票：
  - columns: `['date','open','high','low','close','volume','amount']`
- 多只股票：
  - columns: `['date','code','open','high','low','close','volume','amount']`

## 主要实现细节
1. 对每个 `code` 按 `date` 排序，计算 `prev_close = close.shift(1)`。
2. 计算 `price_range = clip(high - low, min_range)`。
3. 计算 `raw = (close - prev_close) / price_range`。
4. `net_money_flow = raw * amount`。
5. 对 `NaN` 或首日缺失 prev_close 的情况，填充为 0（或可配置为 NaN）。

## 边界与异常情况
- `high - low == 0`：用 `min_range` 替代分母，避免溢出。
- `amount` 为 0 或缺失：结果为 0 或 NaN，视业务偏好。
- 非交易日或缺失 prev_close：首日 net 设为 0。
- 非法数据类型：抛出异常并记录错误行。

## 验证策略（最小）
- 单个样例手算验证（1-3 行）。
- 多股票批量计算（按 code 分组），对比手算或已知值。
- 导入检查（模块懒加载 pandas，保证能在无 pandas 环境下导入模块）。

## 交付物（本次）
- `apt/vendor/tspro/net_money_flow.py`（实现）
- `apt/vendor/tspro/money_flow_spec.md`（本文件）
- `test/test_net_money_flow.py`（简单单元测试）

## 后续（可选）
- 添加参数化填充策略（0 / NaN / 前值）
- 添加 CLI 或小型 runner：输出 CSV 或图像
- 增加 CI 测试与类型检查

---

（设计结束）
