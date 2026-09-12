---
tags:
  - 算法/预测
  - 时序分析
  - v7内置
aliases:
  - ARIMA
  - ARMA
  - 时间序列预测
category: 算法
related:
  - "[[TAM时序分析]]"
  - "[[GM11灰色预测]]"
---

# ARIMA 预测

> 经典的时间序列预测方法，统计理论完备。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 预测 |
| 适用题型 | [[D题-数据分析\|D 数据]] |
| 代码路径 | `algorithms/prediction/arima.py` |
| 接口 | `ARIMA_Forecast(series, order=(1,1,1))` → `.fit()` → `.predict(steps)` |
| 适用条件 | 线性时序，平稳或差分后平稳 |

## 算法原理

ARIMA(p,d,q) 模型：
- **AR(p)**：自回归项，当前值与过去 p 个值相关
- **I(d)**：差分次数，使序列平稳
- **MA(q)**：移动平均项，当前值与过去 q 个误差相关

## 使用示例

```python
from algorithms.prediction.arima import ARIMA_Forecast

model = ARIMA_Forecast(series, order=(1,1,1))
model.fit()
forecast = model.predict(steps=10)
```

## 消融对照

作为 [[TAM时序分析]] 的对照算法，用于 D 型数据题的四重检验。

> **相关笔记**: [[TAM时序分析]] | [[GM11灰色预测]] | [[算法速查卡]]
