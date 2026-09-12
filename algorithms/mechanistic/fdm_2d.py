"""
cumcm-coach 机理求解模块 — 二维有限差分法(FDM)求解扩散/热传导方程

    方程:   du/dt = Dx·d2u/dx2 + Dy·d2u/dy2 + f(x,y,t)
    离散:   5 点显式差分模板 (二维中心差分 stencil)
    依赖:   仅 numpy, 零外部依赖
    接口:   from fdm_2d import fdm_2d_explicit

本函数为纯局部对象风格: 每次调用独立构造数值网格, 不持有任何跨调用的
全局求解器状态, 可在同一进程内安全多次调用。

CFL 稳定条件(二维显式扩散):
    r = Dx*dt/dx^2 + Dy*dt/dy^2 < 1/2
均匀网格且 Dx=Dy=D 时, 等价于单方向 r = D*dt/dx^2 < 1/4 (即记作 nr<0.25)。
违反即抛 ValueError, 提示需增大 nt 或减小 nx/ny。
"""
import numpy as np


def fdm_2d_explicit(D, Lx, Ly, T, nx, ny, nt, f=None, u0=None, bc=0.0,
                    return_all=False):
    """
    二维热传导/扩散方程 5 点显式差分求解。

    参数:
        D: 扩散系数。标量(各向同性)或 [Dx, Dy](各向异性)
        Lx / Ly: x / y 方向空间域长度
        T: 总时间
        nx / ny / nt: x / y 空间网格格点数、时间层数
        f: 源项函数 f(x, y, t), 默认 0
        u0: 初值函数 u0(x, y), 默认 0
        bc: Dirichlet 边界值。
            标量 -> 四条边界同为该值;
            四元组 (上, 下, 左, 右) -> (y=Ly, y=0, x=0, x=Lx) 分别取值。
        return_all: True 返回全程 (U_list, x, y, t); False 只返回末层 (U, x, y)

    返回:
        return_all=False: U(nx+1, ny+1), x(nx+1,), y(ny+1,)
        return_all=True:  U_list(nt+1, nx+1, ny+1), x, y, t(nt+1,)

    稳定条件: r = Dx*dt/dx^2 + Dy*dt/dy^2 < 0.5 (均匀网格单方向 r<0.25)。
    """
    if np.isscalar(D):
        Dx = Dy = float(D)
    else:
        Dx, Dy = float(D[0]), float(D[1])

    x = np.linspace(0.0, Lx, nx + 1)
    y = np.linspace(0.0, Ly, ny + 1)
    t = np.linspace(0.0, T, nt + 1)
    dx, dy, dt = Lx / nx, Ly / ny, T / nt
    rx, ry = Dx * dt / dx ** 2, Dy * dt / dy ** 2
    r = rx + ry
    if r >= 0.5:
        raise ValueError(
            "显式格式不稳定: r = Dx*dt/dx^2 + Dy*dt/dy^2 = %.4f >= 0.5 "
            "(均匀网格需单方向 r<0.25)。请增大 nt 或减小 nx/ny。" % r)

    X, Y = np.meshgrid(x, y, indexing='ij')  # 形状 (nx+1, ny+1)

    def _set_bc(U):
        if np.isscalar(bc):
            U[:, 0] = U[:, -1] = U[0, :] = U[-1, :] = bc
        else:
            top, bottom, left, right = bc
            U[:, -1] = top     # y=Ly (上)
            U[:, 0] = bottom   # y=0  (下)
            U[0, :] = left     # x=0  (左)
            U[-1, :] = right   # x=Lx (右)
        return U

    U = np.zeros((nx + 1, ny + 1))
    if u0 is not None:
        U = np.asarray(u0(X, Y), float)
    U = _set_bc(U)

    U_list = [U.copy()] if return_all else None
    for k in range(nt):
        interior = U[1:-1, 1:-1]
        lap_x = U[2:, 1:-1] - 2 * interior + U[:-2, 1:-1]
        lap_y = U[1:-1, 2:] - 2 * interior + U[1:-1, :-2]
        rhs = rx * lap_x + ry * lap_y
        if f is not None:
            rhs = rhs + dt * np.asarray(f(X[1:-1, 1:-1], Y[1:-1, 1:-1], t[k]), float)
        U[1:-1, 1:-1] = interior + rhs
        U = _set_bc(U)
        if return_all:
            U_list.append(U.copy())

    if return_all:
        return U_list, x, y, t
    return U, x, y


if __name__ == "__main__":
    # 自测: 各向同性扩散, 初值为矩形中央单位热斑, 应随时间平滑扩散并衰减
    u_final, x, y = fdm_2d_explicit(
        D=0.1, Lx=1.0, Ly=1.0, T=0.05, nx=40, ny=40, nt=200,
        u0=lambda X, Y: np.exp(-80 * ((X - 0.5) ** 2 + (Y - 0.5) ** 2)),
        bc=0.0)
    print("末层峰值:", round(float(u_final.max()), 4), "(应 < 1, 平滑衰减)")
    print("末层均值:", round(float(u_final.mean()), 5))
    print("fdm_2d CFL 稳定性: 通过")
