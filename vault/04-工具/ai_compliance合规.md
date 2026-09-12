---
tags:
  - 工具
  - AI合规
  - 2026新规
aliases:
  - ai_compliance
  - AI合规
  - AI声明
category: 工具
related:
  - "[[脚本清单]]"
  - "[[run_all全链流水线]]"
  - "[[去AI味指南]]"
---

# ai_compliance AI 合规模块

> 2026-08-03 组委会《AI工具使用规定（2026试行）》：声明位置移到参考文献前独立「AI工具使用声明」章节。

## 核心要求

- **虚假声明或未审查 AI 核心内容 = 取消评奖资格**
- AILogger：全程记录 AI 交互（阶段/目的/提示词/回复/采纳/人工修改）

## 使用方法

```bash
# Stage 0 初始化
python scripts/ai_compliance.py init

# 每次交互记录
python scripts/ai_compliance.py log --stage "建模" --purpose "公式推导" --prompt "..." --response "..." --adopted true

# Stage 9 生成全部材料
python scripts/ai_compliance.py all
```

## 输出文件

| 文件 | 内容 |
|------|------|
| `output/ai_declaration.tex` | AI 工具使用声明（LaTeX） |
| `output/ai_support_detail.tex` | AI 支撑材料详情 |
| `state/ai_interaction_log.json` | 全程交互日志 |

> **相关笔记**: [[脚本清单]] | [[run_all全链流水线]] | [[去AI味指南]]
