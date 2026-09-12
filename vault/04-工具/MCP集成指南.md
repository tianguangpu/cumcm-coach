---
tags:
  - 工具
  - MCP
  - 集成
aliases:
  - MCP集成
  - MCP工具
  - 8个MCP
category: 工具
related:
  - "[[solver_router求解器路由]]"
  - "[[脚本清单]]"
  - "[[run_all全链流水线]]"
---

# MCP 集成指南

> v7 集成的 8 个 MCP 工具及降级方案。

## 已配置的 MCP 工具

| MCP 工具 | 用途 | 调用时机 |
|---------|------|---------|
| `tavily` | 文献/行业背景检索 | §0 资料检索 |
| `fetch` | 网页/数据抓取 | §0 数据抓取 |
| `mcp-optimizer` | 优化问题求解 | §5 优化建模 |
| `gurddy-mcp` | 经典问题一键求解 | §5 经典问题 |
| `mcp-mathematics` | 符号推导、公式简化 | §5 公式推导 |
| `numpy-mcp` | 张量/矩阵/特征值 | §5 矩阵运算 |
| `matlab-mcp` | MATLAB 执行与绘图 | §5/§6 图表生成 |
| `image-reader` | 图表质量验证 | §6 自动检验 |

## 零依赖降级路径

所有 MCP 均为**可选增强**，任一未连接都不应阻断流程。

| MCP | 降级方案 |
|-----|---------|
| `tavily` | `scripts/search_openalex.py` 或本地 `data-sources.md` |
| `fetch` | Agent 直接读取本地文件 |
| `mcp-optimizer` | 内置 `sa_pso.py`/`ga.py`/`de.py` 或 `solver_router.py` |
| `gurddy-mcp` | 内置算法模块 + 手推 |
| `mcp-mathematics` | sympy 现推 / 手推 |
| `numpy-mcp` | 本地 `import numpy` |
| `matlab-mcp` | Python matplotlib + figure-specs.md |
| `image-reader` | `check_overlaps.py` + 人工复核 |

## mcp-optimizer API 列表

| API | 功能 | 适用题型 |
|-----|------|---------|
| `solve_linear_program` | 线性规划(LP) | B/C |
| `solve_integer_program` | 整数规划(IP) | B |
| `solve_mixed_integer_program` | 混合整数规划(MIP) | B |
| `solve_knapsack_problem` | 背包问题 | B |
| `solve_transportation_problem` | 运输问题 | B |
| `solve_assignment_problem` | 指派问题 | B |
| `solve_vehicle_routing_problem` | VRP | B |
| `solve_job_shop_scheduling` | 车间调度 | B |
| `solve_traveling_salesman_problem` | TSP | B |
| `solve_production_planning` | 生产规划 | B/C |

> **相关笔记**: [[solver_router求解器路由]] | [[脚本清单]] | [[run_all全链流水线]]
