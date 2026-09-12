---
tags:
  - 规范
  - Typst
  - 排版
aliases:
  - Typst指南
  - Typst排版
category: 规范
related:
  - "[[排版规范]]"
  - "[[公式三段式规范]]"
---

# Typst 排版指南

> Typst 是 LaTeX 的现代替代方案，v7 支持 Typst + LaTeX 双引擎。

## Typst vs LaTeX 对比

| 特性 | Typst | LaTeX |
|------|-------|-------|
| 编译速度 | 毫秒级 | 秒级 |
| 语法 | 简洁直观 | 复杂 |
| 错误提示 | 精确行号 | 模糊 |
| 中文支持 | 原生 | 需 XeLaTeX |
| 数学公式 | `$...$` | `$...$` |

## Typst 模板列表

| 模板 | 文件 | 赛事 |
|------|------|------|
| 国赛A题 | `template-a.md` | CUMCM A 机理 |
| 国赛B题 | `template-b.md` | CUMCM B 优化 |
| 国赛C题 | `template-c.md` | CUMCM C 评价 |
| 国赛D题 | `template-d.md` | CUMCM D 数据 |
| 华数杯 | `template-huashu.typ` | 华数杯 |
| 华为杯 | `template-huawei.typ` | 华为杯 |
| MCM/ICM | `template-mcm.typ` | 美赛 |

## 常用语法

```typst
// 标题
= 一级标题
== 二级标题

// 公式
$ F = m a $

// 引用
@eq:example

// 图
#figure(image("fig.png"), caption: [图表标题])
```

> **相关笔记**: [[排版规范]] | [[公式三段式规范]] | [[金标准内核]]
