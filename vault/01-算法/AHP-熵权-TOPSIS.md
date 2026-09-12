---
tags:
  - 算法/评价
  - 综合评价
  - v7内置
aliases:
  - AHP熵权TOPSIS
  - 综合评价
  - TOPSIS
category: 算法
related:
  - "[[VIKOR方法]]"
  - "[[灰色关联GRA]]"
  - "[[HMML分层索引]]"
---

# AHP+熵权+TOPSIS 综合评价

> 主客观结合的经典综合评价方法：AHP 确定主观权重，熵权法确定客观权重，TOPSIS 进行排序。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 综合评价 |
| 适用题型 | [[C题-综合评价\|C 评价]] |
| 代码路径 | `algorithms/evaluation/ahp_entropy_topsis.py` |
| 接口 | `ComprehensiveEvaluation(data, benefit_cols, cost_cols)` |
| 适用条件 | 多指标综合评价，指标需独立 |

## 算法流程

```
数据矩阵
  ↓
AHP（主观权重） + 熵权法（客观权重）
  ↓
组合权重（加权平均/乘法归一化）
  ↓
TOPSIS 排序（正负理想解距离）
  ↓
综合得分 + 排名
```

## 使用示例

```python
from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

# data: 评价矩阵, benefit_cols: 效益型指标列, cost_cols: 成本型指标列
ce = ComprehensiveEvaluation(data, benefit_cols=[0,1,2], cost_cols=[3,4])

# AHP 主观权重
ce.run_ahp(pairwise_matrix)

# 熵权法客观权重
ce.run_entropy()

# 组合权重
weights = ce.combine_weights()

# TOPSIS 排序
result = ce.topsis()
print(f"综合得分: {result['scores']}")
print(f"排名: {result['ranking']}")
```

## 消融对照

与 [[VIKOR方法]]、[[灰色关联GRA]] 对比：

| 方法 | 优势 | 劣势 |
|------|------|------|
| AHP+熵权+TOPSIS | 主客观结合，最经典 | 指标需独立 |
| VIKOR | 允许补偿，输出折中解 | 参数选择主观 |
| GRA | 小样本适用，计算简单 | 分辨率取值影响大 |

> **相关笔记**: [[VIKOR方法]] | [[灰色关联GRA]] | [[算法速查卡]] | [[HMML分层索引]]
