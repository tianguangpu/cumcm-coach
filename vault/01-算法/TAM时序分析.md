---
tags:
  - 算法/预测
  - 时序分析
  - v7内置
  - D型首选
aliases:
  - TAM
  - 时序加法分解
category: 算法
related:
  - "[[ARIMA预测]]"
  - "[[GM11灰色预测]]"
  - "[[HMML分层索引]]"
---

# TAM 时序分析

> D 型数据题的首选预测算法。加法分解 + 物理约束，可解释性强。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 预测 |
| 适用题型 | [[D题-数据分析\|D 数据]] |
| 代码路径 | `algorithms/prediction/tam.py` |
| 接口 | `TAM_Forecast()` → `.fit(df, time_col, value_col)` → `.predict(steps)` |
| 适用条件 | 时序数据，可解释优先 |
| 依赖 | 需 `pip install tam`（未装则降级为简化加法分解） |

## 算法原理

TAM（Time series Additive Model）将时序分解为：

$$y(t) = \text{trend}(t) + \text{seasonal}(t) + \text{residual}(t)$$

- **趋势项**：多项式/样条拟合长期趋势
- **季节项**：周期性成分（月/季度/年）
- **残差项**：随机波动

## 使用示例

```python
from algorithms.prediction.tam import TAM_Forecast

model = TAM_Forecast(formula="y ~ trend(year) + seasonal(month, period=12)")
model.fit(df)
forecast = model.predict(steps=12)
# 返回: {"forecast", "trend", "seasonal", "ci_lower", "ci_upper"}
```

## 消融对照

与 [[ARIMA预测]]、MLP、[[GM11灰色预测]] 四算法对比：

| 算法 | 优势 | 劣势 |
|------|------|------|
| TAM | 可解释性强，物理约束 | 需安装 tam 库 |
| ARIMA | 统计理论完备 | 非线性弱 |
| MLP | 灵活，捕捉复杂模式 | 黑箱，过拟合 |
| GM(1,1) | 小样本适用 | 仅单调趋势 |

> **相关笔记**: [[ARIMA预测]] | [[GM11灰色预测]] | [[算法速查卡]] | [[D题-数据分析]]
