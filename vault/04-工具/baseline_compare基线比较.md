---
tags:
  - 工具
  - 基线
  - 比较
aliases:
  - baseline_compare
  - 基线比较
  - corrective比sophistication
category: 工具
related:
  - "[[result_registry结果溯源]]"
  - "[[self_verify自证门禁]]"
  - "[[金标准内核]]"
---

# baseline_compare 基线比较机制

> **核心原则**：correctness beats sophistication。每个高级模型必须先跑简单基线，对比验证通过才能写入论文。

## 使用方法

```bash
python scripts/baseline_compare.py --type B --advanced results/model.json --output reports/baseline.md
```

## 题型→基线映射

| 题型 | 基线模型 | 比较指标 | 方向 |
|------|---------|---------|------|
| A 机理 | 离散队列模型 | avg_wait | 越低越好 |
| B 优化 | 贪心分配 | total_cost | 越低越好 |
| C 评价 | 等权赋权 | score | 越高越好 |
| D 预测 | 移动平均 | mape | 越低越好 |

## 工作流程

1. 先跑基线模型，得到基准数值
2. 跑高级模型，得到改进数值
3. 对比：高级必须优于基线
4. 通过 → 写入论文；不通过 → 检查模型

> **相关笔记**: [[result_registry结果溯源]] | [[self_verify自证门禁]] | [[金标准内核]]
