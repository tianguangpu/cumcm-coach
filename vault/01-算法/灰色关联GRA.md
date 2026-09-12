---
tags:
  - 算法/评价
  - 灰色系统
  - v7内置
aliases:
  - GRA
  - 灰色关联分析
category: 算法
related:
  - "[[AHP-熵权-TOPSIS]]"
  - "[[VIKOR方法]]"
  - "[[GM11灰色预测]]"
---

# 灰色关联分析（GRA）

> 通过计算参考序列与比较序列的关联度，评估因素间的相似程度。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 综合评价 |
| 适用题型 | [[C题-综合评价\|C 评价]] |
| 代码路径 | `algorithms/evaluation/gra.py` |
| 接口 | `grey_relational(reference, comparison, rho=0.5)` |
| 适用条件 | 小样本，计算简单 |

## 算法原理

1. 数据标准化（初值化/均值化）
2. 计算差序列：Δᵢ(k) = |x₀(k) - xᵢ(k)|
3. 计算关联系数：γᵢ(k) = (Δmin + ρΔmax) / (Δᵢ(k) + ρΔmax)
4. 计算关联度：rᵢ = Σγᵢ(k) / n

## 使用示例

```python
from algorithms.evaluation.gra import grey_relational

reference = [100, 200, 300, 400]  # 参考序列
comparison = [[95, 210, 290, 420], [90, 190, 310, 380]]  # 比较序列
result = grey_relational(reference, comparison, rho=0.5)
print(f"关联度: {result}")
```

> **相关笔记**: [[AHP-熵权-TOPSIS]] | [[VIKOR方法]] | [[GM11灰色预测]] | [[算法速查卡]]
