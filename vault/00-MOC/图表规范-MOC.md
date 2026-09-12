---
tags:
  - MOC
  - 图表
aliases:
  - 图表规范MOC
  - 图表索引页
category: MOC
related:
  - "[[图表路由规范]]"
  - "[[图表技术规范]]"
---

# 图表规范 MOC

> 图表生成的路由、技术和规范。

## 🗺️ 路由体系

| 笔记 | 说明 |
|------|------|
| [[图表路由规范]] | 三级路由总览（常规→惊艳→流程） |
| [[图表技术规范]] | 10 种标准技法 |
| [[流程图规范]] | 灰度流程图规范 |

## 🎨 图型分类

### 常规数据图（figure-skill / figure-specs）
- 折线图、柱状图、散点图
- 热力图、雷达图、箱线图
- 3D曲面、双编码散点、收敛渐变、inset放大

### 惊艳高级图（nature-plot-repro）
- 弦图、桑基图、泰勒图
- 环形热图、小提琴图、UpSet图
- SHAP、山脊图、蜂群图

### 流程图（diagram-design）
- 技术路线图
- 模型结构图
- 算法流程图

## 🔧 工具选择

```
出图前选型
  ├─ 概念图/流程图 → diagram-design（灰度）
  ├─ 常规数据图 → figure-skill（Python）
  └─ 惊艳高级图 → nature-plot-repro（MATLAB）
```

## 📏 配色方案

| 色板 | 来源 | 用途 |
|------|------|------|
| Nature | Nature 期刊 | 学术首选 |
| Science | Science 期刊 | 学术备选 |
| Qualitative | 定性色板 | 分类数据 |
| Diverging | 发散色板 | 正负对比 |
| IEEE | IEEE 期刊 | 工程类 |
