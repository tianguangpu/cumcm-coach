---
tags:
  - 算法/机理
  - 数值方法
  - v7内置
aliases:
  - FDM
  - 有限差分
category: 算法
related:
  - "[[A题-机理建模]]"
  - "[[HMML分层索引]]"
---

# FDM 有限差分法

> A 型机理题的核心数值方法，用于求解偏微分方程（PDE）。

## 基本信息

| 属性 | 值 |
|------|-----|
| 类型 | 数值方法 |
| 适用题型 | [[A题-机理建模\|A 机理]] |
| 代码路径 | `algorithms/mechanistic/fdm_1d.py` |
| 接口 | `heat_1d_explicit(D, L, T, nx, nt)` → `(u, x, t)` |
| 适用条件 | 一维扩散/热传导方程 |

## 算法原理

将连续 PDE 离散化为差分方程：

$$\frac{\partial u}{\partial t} = D \frac{\partial^2 u}{\partial x^2}$$

离散化：
$$u_i^{n+1} = u_i^n + \frac{D \Delta t}{\Delta x^2}(u_{i+1}^n - 2u_i^n + u_{i-1}^n)$$

## 使用示例

```python
from algorithms.mechanistic.fdm_1d import heat_1d_explicit

D = 0.01   # 扩散系数
L = 1.0    # 长度
T = 1.0    # 总时间
nx = 100   # 空间步数
nt = 1000  # 时间步数

u, x, t = heat_1d_explicit(D, L, T, nx, nt)
```

## 扩展

- 二维 FDM：`algorithms/mechanistic/fdm_2d.py`
- ODE 求解器：`algorithms/mechanistic/ode_solver.py`
- 复杂几何：现写 FEM/FVM

> **相关笔记**: [[A题-机理建模]] | [[算法速查卡]] | [[HMML分层索引]]
