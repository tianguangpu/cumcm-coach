---
tags:
  - MOC
  - 工具
aliases:
  - 脚本工具MOC
  - 工具索引页
category: MCP
related:
  - "[[脚本清单]]"
  - "[[MCP集成指南]]"
---

# 脚本工具 MOC

> MCP 工具、脚本清单和流水线的完整索引。

## 🔌 MCP 工具

| 笔记 | 说明 |
|------|------|
| [[MCP集成指南]] | 8 个 MCP 工具 + 零依赖降级路径 |

### MCP 速查

| MCP | 用途 | 降级方案 |
|-----|------|---------|
| tavily | 文献检索 | search_openalex.py |
| fetch | 数据抓取 | 本地文件 |
| mcp-optimizer | 优化求解 | 内置算法 |
| gurddy-mcp | 经典问题 | 内置模块 |
| mcp-mathematics | 符号推导 | sympy |
| numpy-mcp | 矩阵运算 | numpy |
| matlab-mcp | MATLAB | matplotlib |
| image-reader | 图质验证 | check_overlaps.py |

## 📜 脚本清单

| 笔记 | 说明 |
|------|------|
| [[脚本清单]] | 28 主脚本 + 3 测试完整清单 |
| [[run_all全链流水线]] | 13 步全链流水线 |
| [[ai_compliance合规]] | 2026 新规 AI 合规 |

## 🔧 求解工具

| 笔记 | 说明 |
|------|------|
| [[solver_router求解器路由]] | 多求解器自动路由 |
| [[baseline_compare基线比较]] | 基线比较机制 |
| [[result_registry结果溯源]] | 数值结果溯源注册表 |

## 🔄 流水线

```
init → problem_analyzer → innovation_guide → 建模 → 求解
  → 图表 → 论文 → L1-L4评审 → AI合规 → 参考文献
  → 摘要精修 → 排版 → 交卷
```
