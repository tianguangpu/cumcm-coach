---
tags:
  - 工具
  - 求解器
  - 路由
aliases:
  - solver_router
  - 求解器路由
  - 多求解器
category: 工具
related:
  - "[[MCP集成指南]]"
  - "[[SA-PSO混合优化]]"
  - "[[遗传算法GA]]"
  - "[[差分进化DE]]"
  - "[[B题-优化决策]]"
---

# solver_router 求解器路由

> 多求解器自动路由：LP→HiGHS/PuLP，NLP→SciPy，CSP→OR-Tools，VRP/JobShop/TSP→内置算法。

## 路由逻辑

```
问题输入
  ↓
问题类型识别
  ├─ LP（线性规划）→ HiGHS / PuLP
  ├─ IP/MIP（整数规划）→ PuLP + CBC
  ├─ NLP（非线性规划）→ SciPy
  ├─ CSP（约束满足）→ OR-Tools
  ├─ VRP → 内置 vrp.py
  ├─ JobShop → 内置 job_shop.py
  └─ TSP → 内置 tsp_ga
```

## 内置路由（v7.10 新增）

| 问题类型 | 求解器 | 代码 |
|---------|--------|------|
| VRP | 遗传算法 | `algorithms/optimization/vrp.py` |
| JobShop | NSGA-II | `algorithms/optimization/job_shop.py` |
| TSP | 遗传算法 | 内置 `solve_tsp_ga` |

## 使用示例

```python
from scripts.solver_router import solve_lp, solve_mip, solve_nlp, select_solver_auto

# 线性规划
result = solve_lp(objective, constraints, variables, sense="minimize")

# 自动选择求解器
result = select_solver_auto(problem_type, objective, constraints, variables)
```

## MCP 降级

当 mcp-optimizer 未连接时，自动降级到内置算法。

> **相关笔记**: [[MCP集成指南]] | [[SA-PSO混合优化]] | [[B题-优化决策]] | [[脚本清单]]
