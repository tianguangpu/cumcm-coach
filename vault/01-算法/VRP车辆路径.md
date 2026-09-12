---
tags:
  - 算法/优化
  - 组合优化
  - v7内置
aliases:
  - VRP
  - 车辆路径问题
category: 算法
related:
  - "[[JobShop调度]]"
  - "[[SA-PSO混合优化]]"
  - "[[B题-优化决策]]"
---

# VRP 车辆路径问题

> 车辆路径规划问题的遗传算法求解器。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 组合优化 |
| 适用题型 | [[B题-优化决策\|B 优化]] |
| 代码路径 | `algorithms/optimization/vrp.py` |
| 接口 | `VRP(dist, demands, capacity, n_vehicles).solve_ga()` → `routes, total_distance` |
| 适用条件 | 物流配送、路径规划 |

## 使用示例

```python
from algorithms.optimization.vrp import VRP

vrp = VRP(
    dist=distance_matrix,      # 距离矩阵
    demands=demand_list,        # 各点需求量
    capacity=vehicle_capacity,  # 车辆容量
    n_vehicles=5                # 车辆数
)
routes, total_distance = vrp.solve_ga()
print(f"路径: {routes}, 总距离: {total_distance}")
```

> **相关笔记**: [[JobShop调度]] | [[SA-PSO混合优化]] | [[B题-优化决策]] | [[算法速查卡]]
