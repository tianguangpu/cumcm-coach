---
tags:
  - 算法/优化
  - 智能优化
  - v7内置
aliases:
  - GA
  - 遗传算法
category: 算法
related:
  - "[[SA-PSO混合优化]]"
  - "[[差分进化DE]]"
  - "[[HMML分层索引]]"
---

# 遗传算法（GA）

> 模拟生物进化过程的全局优化算法，通过选择、交叉、变异操作搜索最优解。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 智能优化（进化算法） |
| 适用题型 | [[B题-优化决策\|B 优化]] |
| 代码路径 | `algorithms/optimization/ga.py` |
| 接口 | `GA(obj, dim, bounds, pop_size=50, max_gen=200)` → `r['x_opt'], r['f_opt']` |
| 适用条件 | 连续/离散混合，鲁棒性要求高 |

## 算法原理

1. **编码**：将解编码为染色体（二进制/实数）
2. **选择**：轮盘赌/锦标赛选择，保留优秀个体
3. **交叉**：单点/多点/均匀交叉，产生后代
4. **变异**：随机扰动，维持种群多样性
5. **迭代**：重复选择→交叉→变异，直到收敛

## 使用示例

```python
from algorithms.optimization.ga import GA

def objective(x):
    return sum(xi**2 for xi in x)

bounds = [(-10, 10)] * 5
result = GA(objective, dim=5, bounds=bounds, pop_size=50, max_gen=200)
print(f"最优解: {result['x_opt']}, 最优值: {result['f_opt']}")
```

## 消融对照

与 [[SA-PSO混合优化]]、[[差分进化DE]] 三算法对比。

> **相关笔记**: [[SA-PSO混合优化]] | [[差分进化DE]] | [[HMML分层索引]] | [[算法速查卡]]
