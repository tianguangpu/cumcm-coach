---
tags:
  - 算法/优化
  - 智能优化
  - v7内置
aliases:
  - SA-PSO
  - 模拟退火粒子群
category: 算法
related:
  - "[[遗传算法GA]]"
  - "[[差分进化DE]]"
  - "[[HMML分层索引]]"
---

# SA-PSO 混合优化算法

> 模拟退火（SA）与粒子群优化（PSO）的混合算法，兼具全局搜索能力和快速收敛性。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 智能优化（混合） |
| 适用题型 | [[B题-优化决策\|B 优化]] |
| 代码路径 | `algorithms/optimization/sa_pso.py` |
| 接口 | `SA_PSO(obj, dim, bounds, N=50, T_max=200)` → `r['x_opt'], r['f_opt']` |
| 适用条件 | 连续、多峰、中等规模 |

## 算法原理

1. **PSO 阶段**：粒子群在搜索空间中飞行，通过个体最优和全局最优引导搜索方向
2. **SA 阶段**：对 PSO 找到的最优解进行模拟退火扰动，跳出局部最优
3. **混合策略**：PSO 快速定位最优区域 → SA 精细搜索 + 跳出局部最优

## 使用示例

```python
from algorithms.optimization.sa_pso import SA_PSO

def objective(x):
    return sum(xi**2 for xi in x)  # 测试函数

bounds = [(-10, 10)] * 5  # 5维问题
result = SA_PSO(objective, dim=5, bounds=bounds, N=50, T_max=200)

print(f"最优解: {result['x_opt']}")
print(f"最优值: {result['f_opt']}")
print(f"收敛代数: {result['convergence_iter']}")
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `obj` | - | 目标函数 |
| `dim` | - | 问题维度 |
| `bounds` | - | 搜索边界 `[(low, high), ...]` |
| `N` | 50 | 粒子数量 |
| `T_max` | 200 | 最大迭代次数 |

## 消融对照

与 [[遗传算法GA]]、[[差分进化DE]] 三算法对比，生成对比表用于论文 §5.X.5：

| 算法 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| SA-PSO | 全局搜索强，收敛快 | 参数敏感 | 连续多峰优化 |
| GA | 鲁棒性好，并行友好 | 收敛慢 | 连续/离散混合 |
| DE | 简单高效，少参数 | 离散问题弱 | 实数优化 |

> **相关笔记**: [[遗传算法GA]] | [[差分进化DE]] | [[VRP车辆路径]] | [[JobShop调度]] | [[HMML分层索引]]
