# -*- coding: utf-8 -*-
"""
一维有限差分法(FDM)求解扩散/热传导方程 — 机理题(国赛 A 题)数值求解模板
方程: ∂u/∂t = D ∂²u/∂x² + f(x,t),  显式差分格式
纯 numpy 无额外依赖。接口: from fdm_1d import heat_1d_explicit
"""
import numpy as np


def heat_1d_explicit(D, L, T, nx=100, nt=5000, f=None, u0=None, bc=None):
    """
    一维热传导/扩散方程显式差分。
    参数:
        D: 扩散系数(标量或函数 D(x))
        L: 空间域 [0, L]
        T: 总时间
        nx / nt: 空间 / 时间网格数
        f: 源项函数 f(x, t), 默认 0
        u0: 初值函数 u0(x), 默认 0
        bc: 边界条件 (u_left, u_right), 默认 Dirichlet 0
    返回:
        x: 空间网格 (nx+1,)
        t: 时间网格 (nt+1,)
        U: 解矩阵 (nt+1, nx+1)
    """
    x = np.linspace(0, L, nx + 1)
    t = np.linspace(0, T, nt + 1)
    dx = L / nx
    dt = T / nt
    r = D * dt / dx ** 2
    if r > 0.5:
        raise ValueError(f"显式格式不稳定: r={r:.3f} > 0.5, 请增大 nt 或减小 nx")

    U = np.zeros((nt + 1, nx + 1))
    if u0 is not None:
        U[0, :] = u0(x)
    if bc is not None:
        U[:, 0], U[:, -1] = bc[0], bc[1]

    for k in range(nt):
        U[k + 1, 1:-1] = U[k, 1:-1] + r * (U[k, 2:] - 2 * U[k, 1:-1] + U[k, :-2])
        if f is not None:
            U[k + 1, 1:-1] += dt * f(x[1:-1], t[k])
        if bc is not None:
            U[k + 1, 0], U[k + 1, -1] = bc[0], bc[1]
    return x, t, U


if __name__ == "__main__":
    # 自测:热传导,初值 sin(πx/L),应指数衰减且守恒
    D, L, T = 0.1, 1.0, 0.5
    x, t, U = heat_1d_explicit(D, L, T, nx=50, nt=5000,
                               u0=lambda x: np.sin(np.pi * x / L),
                               bc=(0.0, 0.0))
    print("t=0   峰值:", round(U[0].max(), 4))
    print("t=T   峰值:", round(U[-1].max(), 4), "(应 < 1, 衰减)")
    print("数值稳定性: 通过")
