---
tags:
  - 算法/优化
  - 智能优化
  - v7内置
aliases:
  - DE
  - 差分进化
category: 算法
related:
  - "[[SA-PSO混合优化]]"
  - "[[遗传算法GA]]"
  - "[[HMML分层索引]]"
---

# 差分进化算法（DE）

> 基于种群差异的进化算法，通过差分变异和交叉操作搜索最优解。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 智能优化（进化算法） |
| 适用题型 | [[B题-优化决策\|B 优化]] |
| 代码路径 | `algorithms/optimization/de.py` |
| 接口 | `DE(obj, dim, bounds, pop_size=50, max_gen=200)` → `r['x_opt'], r['f_opt']` |
| 适用条件 | 实数优化，参数少 |

## 算法原理

1. **变异**：选择两个个体，计算差分向量，加到第三个个体上
2. **交叉**：变异向量与目标向量交叉，生成试验向量
3. **选择**：试验向量与目标向量竞争，保留更优者

## 使用示例

```python
from algorithms.optimization.de import DE

def objective(x):
    return sum(xi**2 for xi in x)

bounds = [(-10, 10)] * 5
result = DE(objective, dim=5, bounds=bounds, pop_size=50, max_gen=200)
print(f"最优解: {result['x_opt']}, 最优值: {result['f_opt']}")
```

> **相关笔记**: [[SA-PSO混合优化]] | [[遗传算法GA]] | [[HMML分层索引]] | [[算法速查卡]]
