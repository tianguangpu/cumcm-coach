# -*- coding: utf-8 -*-
"""
cumcm-coach 机理求解模块 — 常微分方程(ODE)直接数值求解器封装

    提供:  euler (前向欧拉, 一阶), rk4 (经典四阶龙格库塔),
           solve_ivp_wrapper (scipy 自适应步长 RK45 封装)
    依赖:  numpy (euler/rk4); scipy (仅 solve_ivp_wrapper 需 scipy)
    接口统一: 每个函数返回 (t_array, y_array)
    - y_array 维度: 初值 y0 为标量 -> y 一维 (n,);
                     y0 为数组   -> y 二维 (n, d)
"""
import numpy as np


def _coerce(y0):
    """统一初值为一维数组, 并返回是否是标量。"""
    y0a = np.atleast_1d(np.asarray(y0, float))
    return y0a, (np.ndim(y0) == 0)


def euler(f, y0, t):
    """前向欧拉法 (一阶精度, 条件稳定)。

    参数: f(t, y) 右端项; y0 初值(标量或数组); t 时间网格(单调数组)
    返回: (t, y)
    """
    ts = np.asarray(t, float)
    y0a, scalar = _coerce(y0)
    n = len(ts)
    Y = np.empty((n, y0a.size))
    Y[0] = y0a
    for i in range(n - 1):
        h = ts[i + 1] - ts[i]
        Y[i + 1] = Y[i] + h * np.asarray(f(ts[i], Y[i]), float)
    return ts, (Y[:, 0] if scalar else Y)


def rk4(f, y0, t):
    """经典四阶龙格-库塔法 (RK4, 四阶精度)。

    参数: f(t, y) 右端项; y0 初值; t 时间网格(单调数组)
    返回: (t, y)
    """
    ts = np.asarray(t, float)
    y0a, scalar = _coerce(y0)
    n = len(ts)
    Y = np.empty((n, y0a.size))
    Y[0] = y0a
    for i in range(n - 1):
        h = ts[i + 1] - ts[i]
        k1 = np.asarray(f(ts[i], Y[i]), float)
        k2 = np.asarray(f(ts[i] + h / 2, Y[i] + h / 2 * k1), float)
        k3 = np.asarray(f(ts[i] + h / 2, Y[i] + h / 2 * k2), float)
        k4 = np.asarray(f(ts[i] + h, Y[i] + h * k3), float)
        Y[i + 1] = Y[i] + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return ts, (Y[:, 0] if scalar else Y)


def solve_ivp_wrapper(f, y0, t_span, t_eval=None, method='RK45', rtol=1e-6,
                      atol=1e-9, **kwargs):
    """scipy.integrate.solve_ivp 封装 (自适应步长)。

    参数: f(t, y) 右端项; y0 初值; t_span=(t0, t1);
          t_eval 输出时间点(可选), method/rtol/atol 与 solve_ivp 一致
    返回: (t, y); 失败时抛 RuntimeError
    依赖: 需已安装 scipy
    """
    from scipy.integrate import solve_ivp
    y0a, scalar = _coerce(y0)
    res = solve_ivp(f, tuple(t_span), y0a, t_eval=t_eval,
                    method=method, rtol=rtol, atol=atol, **kwargs)
    if not res.success:
        raise RuntimeError("solve_ivp 求解失败: %s" % res.message)
    y = res.y[0] if scalar else res.y
    return res.t, y


if __name__ == "__main__":
    # 自测: y' = -y, y(0)=1, 解析解 exp(-t)。RK4 应逼近, 欧拉在粗网格略偏高。
    import math
    t = np.linspace(0, 2, 20)
    t_r, yr = rk4(lambda ti, yy: -yy, 1.0, t)
    t_e, ye = euler(lambda ti, yy: -yy, 1.0, t)
    print("RK4  y(2)=", round(float(yr[-1]), 6), "  解析 =", round(math.exp(-2), 6))
    print("Euler y(2)=", round(float(ye[-1]), 6))
    print("ode_solver 自测: 通过")
