---
tags:
  - 题型
  - playbook
  - 路径规划
  - B题
aliases:
  - 路径规划playbook
  - 物流优化
category: playbook
related:
  - "[[B题-优化决策]]"
  - "[[VRP车辆路径]]"
  - "[[SA-PSO混合优化]]"
---

# 路径规划 Playbook

> 题型：B 题（路径/物流/网络优化）

## 匹配条件

- 特征词：路径、物流、配送、TSP、VRP、最短路、网络流、选址
- 数学本质：图论 + 组合优化

## 常用算法

| 算法 | 适用场景 | 代码 |
|------|---------|------|
| Dijkstra | 最短路 | `network/graph_algo.py` |
| Kruskal | 最小生成树 | `network/graph_algo.py` |
| [[VRP车辆路径]] | 物流配送 | `optimization/vrp.py` |
| 蚁群算法 | TSP/VRP | 外部库 |

## 解题路径

1. **建图**：节点=位置，边=距离/成本
2. **选算法**：最短路→Dijkstra，多车→VRP，巡回→TSP
3. **求解**：内置算法 或 mcp-optimizer
4. **验证**：灵敏度分析 + 蒙特卡洛

> **相关笔记**: [[B题-优化决策]] | [[VRP车辆路径]] | [[SA-PSO混合优化]]
