# Typst 引擎转译指南

> 当用户选 Typst 排版引擎时使用本指南。

## 转译规则

| LaTeX | Typst | 说明 |
|-------|-------|------|
| `\documentclass{ctexart}` | `#import "@preview/...:0.x.x":*` | 用 i-figured / unequivocal-ams 等包 |
| `\begin{equation}\label{eq:x}` | `$ a = b $ <eq_x>` | Typst 数学语法 |
| `\includegraphics[width=0.85\textwidth]{x.pdf}` | `#image("x.pdf", width: 85%)` | — |
| `\caption{...}\label{fig:x}` | `#figure(image(...), caption: [...]) <fig_x>` | — |
| `\ref{fig:x}` | `@fig_x` | 自动交叉引用 |
| `\bibitem` | `#bibliography("refs.bib")` | Typst 原生 Hayagriva |
| `\begin{align}` | `$ a &= b \ b &= c $` | 多行对齐用 `\` 换行 |
| `xelatex` 两次 | `typst compile` 一次 | Typst 单次编译 |

## 国赛模板骨架

```typst
#import "@preview/i-figured:0.2.4":*
#import "@preview/unequivocal-ams:0.1.0":*
#show: amsthm-style

#set text(font: ("Times New Roman", "SimHei"), size: 10pt)
#set par(justify: true, leading: 1em)
#set page(margin: (x: 2.5cm, y: 2.5cm))

#show figure: set text(font: "Times New Roman")

= 问题重述
= 问题分析
= 模型假设
= 符号说明
= 模型建立与求解
== 问题一
=== 参数配置与数据预处理
=== 基础经典模型
$ a + b = c $ <eq_model1>
@eq_model1 中...
=== 传统模型缺陷剖析
=== 创新改进模型
=== 算法设计与求解
=== 数值结果与可视化
= 模型检验
== 拟合精度
== 灵敏度分析
== 蒙特卡洛验证
== 假设误差量化
= 模型优缺点与改进
= 参考文献
#bibliography("references.yml")

= 附录 <appendix>
== 附录1 数据说明
== 附录2 代码
== 附录3 公式推导
```

## 图表嵌入

```typst
#figure(
  image("../figures/pdf/fig1_xxx.pdf", width: 85%),
  caption: [图1 [对象][趋势]([关键数值])]
) <fig_fig1>
在 @fig_fig1 中可以看到...
```
