---
tags:
  - 算法/评价
  - 综合评价
  - v7内置
aliases:
  - VIKOR
  - 折中排序
category: 算法
related:
  - "[[AHP-熵权-TOPSIS]]"
  - "[[灰色关联GRA]]"
---

# VIKOR 方法

> 多准则折中排序方法，允许指标间补偿，输出折中解。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 综合评价 |
| 适用题型 | [[C题-综合评价\|C 评价]] |
| 代码路径 | `algorithms/evaluation/vikor.py` |
| 接口 | `VIKOR(decision_matrix, weights, benefit, v=0.5)` |

## 算法原理

1. 确定正理想解和负理想解
2. 计算群体效益 S 和个体遗憾 R
3. 计算 VIKOR 值 Q = v(S-S*)/(S**-S*) + (1-v)(R-R*)/(R**-R*)
4. 按 Q 值排序，输出折中解

## 消融对照

与 [[AHP-熵权-TOPSIS]]、[[灰色关联GRA]] 对比。

> **相关笔记**: [[AHP-熵权-TOPSIS]] | [[灰色关联GRA]] | [[算法速查卡]]
