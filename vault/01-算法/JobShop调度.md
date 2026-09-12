---
tags:
  - 算法/优化
  - 调度优化
  - v7内置
aliases:
  - JobShop
  - 车间调度
category: 算法
related:
  - "[[VRP车辆路径]]"
  - "[[SA-PSO混合优化]]"
  - "[[B题-优化决策]]"
---

# JobShop 车间调度

> 车间调度问题的 NSGA-II 多目标优化求解器。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 组合优化 |
| 适用题型 | [[B题-优化决策\|B 优化]] |
| 代码路径 | `algorithms/optimization/job_shop.py` |
| 接口 | `JobShopScheduler(jobs).solve_nsga2()` → `pareto_front, makespan` |
| 适用条件 | 生产调度、资源分配 |

## 使用示例

```python
from algorithms.optimization.job_shop import JobShopScheduler

scheduler = JobShopScheduler(jobs=job_list)
pareto_front, makespan = scheduler.solve_nsga2()
print(f"Pareto 前沿: {pareto_front}")
print(f"最短完工时间: {makespan}")
```

> **相关笔记**: [[VRP车辆路径]] | [[SA-PSO混合优化]] | [[B题-优化决策]] | [[算法速查卡]]
