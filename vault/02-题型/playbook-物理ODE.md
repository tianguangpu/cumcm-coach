---
tags:
  - 题型
  - playbook
  - 物理机理
  - A题
aliases:
  - 物理ODE playbook
  - 机理建模playbook
category: playbook
related:
  - "[[A题-机理建模]]"
  - "[[FDM有限差分]]"
---

# 物理 ODE/PDE Playbook

> 题型：A 题（物理/化学/生物机理）

## 匹配条件

- 特征词：热传导、扩散、动力学、轨迹、能量、微分方程
- 数学本质：ODE/PDE 建模 + 数值求解

## 常用方法

| 方法 | 适用场景 | 代码 |
|------|---------|------|
| [[FDM有限差分]] | 一维扩散/热传导 | `mechanistic/fdm_1d.py` |
| ODE 求解器 | 常微分方程 | `mechanistic/ode_solver.py` |
| mcp-mathematics | 符号推导/解析解 | MCP 调用 |
| 现写 FEM/FVM | 复杂几何 | Agent 现写 |

## 解题路径

1. **物理建模**：守恒定律/平衡方程
2. **数学建模**：ODE/PDE + 边界条件 + 初始条件
3. **数值求解**：FDM/FEM/FVM
4. **验证**：解析解对比（如有）+ 网格收敛性

> **相关笔记**: [[A题-机理建模]] | [[FDM有限差分]] | [[金标准内核]]
