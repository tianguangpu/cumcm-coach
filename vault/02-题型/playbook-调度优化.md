---
tags:
  - 题型
  - playbook
  - 调度优化
  - B题
aliases:
  - 调度优化playbook
  - 生产调度
category: playbook
related:
  - "[[B题-优化决策]]"
  - "[[JobShop调度]]"
  - "[[SA-PSO混合优化]]"
---

# 调度优化 Playbook

> 题型：B 题（生产调度/排班/资源配置）

## 匹配条件

- 特征词：调度、排班、排程、车间、生产线、资源分配、工时
- 数学本质：约束优化 + 调度理论

## 常用算法

| 算法 | 适用场景 | 代码 |
|------|---------|------|
| [[JobShop调度]] | 车间调度 | `optimization/job_shop.py` |
| OR-Tools CP-SAT | 整数/调度/排班 | `scripts/solver_router.py` |
| [[SA-PSO混合优化]] | 通用调度 | `optimization/sa_pso.py` |
| [[遗传算法GA]] | 复杂调度 | `optimization/ga.py` |

## 解题路径

1. **问题建模**：机器/工件/工序/时间窗
2. **约束建模**：工序约束、资源约束、时间窗约束
3. **目标函数**：最小化完工时间/成本/延迟
4. **求解**：GA/SA-PSO/OR-Tools
5. **验证**：Gantt 图可视化 + 灵敏度分析

> **相关笔记**: [[B题-优化决策]] | [[JobShop调度]] | [[VRP车辆路径]]
