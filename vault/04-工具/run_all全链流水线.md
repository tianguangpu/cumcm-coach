---
tags:
  - 工具
  - 流水线
  - 全链
aliases:
  - run_all
  - 全链流水线
  - 13步
category: 工具
related:
  - "[[脚本清单]]"
  - "[[MCP集成指南]]"
  - "[[ai_compliance合规]]"
  - "[[金标准内核]]"
---

# run_all 全链流水线（13 步）

> 国赛全链流水线，支持断点续跑。

## 使用方法

```bash
# 预览（不执行）
python scripts/run_all.py --dry

# 从第7步开始
python scripts/run_all.py --from 07

# 快速模式
python scripts/run_all.py --fast
```

## 13 步流程

| 步骤 | 脚本 | 功能 |
|------|------|------|
| 01 | init_project.py | 项目初始化 |
| 02 | problem_analyzer | 问题分析确认 |
| 03 | innovation_guide | 创新方向确定 |
| 04 | - | 建模（人工介入） |
| 05 | solver_router.py | 求解 |
| 06 | - | 图表生成（人工介入） |
| 07 | - | 论文写作（人工介入） |
| 08 | auto_check.py | L1-L4 评审 |
| 09 | ai_compliance.py | AI 合规材料 |
| 10 | check_references.py | 参考文献审查 |
| 11 | polish_abstract.py | 摘要精修 |
| 12 | - | 最终排版（人工介入） |
| 13 | - | 交卷（人工介入） |

## 断点续跑

使用 `--from N` 从第 N 步开始，跳过已完成步骤。

> **相关笔记**: [[脚本清单]] | [[ai_compliance合规]] | [[金标准内核]] | [[论文自审框架]]
