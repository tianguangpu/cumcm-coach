"""
cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 种群动态 / 传染病模型

本文档属于 cumcm-coach-skill-v7 算法库的《生态》子模块。

提供可独立调用的常微分方程(ODE)模型，互不耦连、各可单独运行：
  - lotka_volterra(alpha, beta, delta, gamma, x0, y0, t) -> (t, x, y)
        捕食-被捕食(Lotka-Volterra)模型
  - SIR(beta, gamma, S0, I0, R0, t)                       -> (t, S, I, R)
        基础传染病模型(易感-感染-康复)
  - SEIR(beta, sigma, gamma, S0, E0, I0, R0, t)           -> (t, S, E, I, R)
        带潜伏期的传染病模型(易感-暴露-感染-康复)

所有模型均用 scipy.integrate.solve_ivp(RK45) 数值积分。t 可传入时间点数组，
也可传入单个数值 T(此时自动生成 t = linspace(0, T, 200))。

依赖：numpy, scipy.integrate。
"""
import numpy as np
from scipy.integrate import solve_ivp


def _as_time(t):
    """将 t 规范化为时间点数组。"""
    t = np.asarray(t, dtype=float)
    if t.ndim == 0:
        return np.linspace(0.0, float(t), 200)
    return t.reshape(-1)


def lotka_volterra(alpha, beta, delta, gamma, x0, y0, t):
    """
    Lotka-Volterra 捕食-被捕食模型。

    状态：x=被捕食者数量(猎物)，y=捕食者数量。
      dx/dt = alpha*x - beta*x*y
      dy/dt = delta*x*y - gamma*y

    参数
    ----
    alpha, beta : 猎物增长率、捕食率
    delta, gamma: 捕食效率、捕食者死亡率
    x0, y0      : 初始猎物、捕食者数量
    t           : 时间点数组(或终点时间 T)

    返回
    ----
    (t, x, y)：t 为时间数组，x/y 为对应数量的时间序列。
    """
    t = _as_time(t)

    def rhs(s, z):
        x, y = z
        dx = alpha * x - beta * x * y
        dy = delta * x * y - gamma * y
        return [dx, dy]

    sol = solve_ivp(rhs, (t[0], t[-1]), [x0, y0], t_eval=t,
                    method='RK45', rtol=1e-8, atol=1e-10)
    if not sol.success:
        raise RuntimeError("Lotka-Volterra 积分失败: " + sol.message)
    return t, sol.y[0], sol.y[1]


def SIR(beta, gamma, S0, I0, R0, t):
    """
    基础 SIR 传染病模型(易感-感染-康复)。

      dS/dt = -beta*S*I
      dI/dt =  beta*S*I - gamma*I
      dR/dt =  gamma*I

    参数
    ----
    beta      : 有效接触传染率
    gamma     : 恢复率
    S0, I0, R0: 初始易感、感染、康复人数(三者常满足和 = 总人口)
    t         : 时间点数组(或终点时间 T)

    返回
    ----
    (t, S, I, R)
    """
    t = _as_time(t)

    def rhs(s, z):
        S, I, R = z
        dS = -beta * S * I
        dI = beta * S * I - gamma * I
        dR = gamma * I
        return [dS, dI, dR]

    n = int(np.sum([S0, I0, R0]))
    if n == 0:
        n = 1
    sol = solve_ivp(rhs, (t[0], t[-1]), [S0, I0, R0], t_eval=t,
                    method='RK45', rtol=1e-8, atol=1e-10,
                    max_step=1.0)
    if not sol.success:
        raise RuntimeError("SIR 积分失败: " + sol.message)
    return t, sol.y[0], sol.y[1], sol.y[2]


def SEIR(beta, sigma, gamma, S0, E0, I0, R0, t):
    """
    带潜伏期的 SEIR 传染病模型(易感-暴露-感染-康复)。

      dS/dt = -beta*S*I
      dE/dt =  beta*S*I - sigma*E
      dI/dt =  sigma*E - gamma*I
      dR/dt =  gamma*I

    参数
    ----
    beta            : 有效接触传染率
    sigma           : 潜伏期末发病速率(1/潜伏期)
    gamma           : 恢复率
    S0, E0, I0, R0  : 初始易感、暴露、感染、康复人数
    t               : 时间点数组(或终点时间 T)

    返回
    ----
    (t, S, E, I, R)
    """
    t = _as_time(t)

    def rhs(s, z):
        S, E, I, R = z
        dS = -beta * S * I
        dE = beta * S * I - sigma * E
        dI = sigma * E - gamma * I
        dR = gamma * I
        return [dS, dE, dI, dR]

    sol = solve_ivp(rhs, (t[0], t[-1]), [S0, E0, I0, R0], t_eval=t,
                    method='RK45', rtol=1e-8, atol=1e-10, max_step=1.0)
    if not sol.success:
        raise RuntimeError("SEIR 积分失败: " + sol.message)
    return t, sol.y[0], sol.y[1], sol.y[2], sol.y[3]


if __name__ == "__main__":
    tv, x, y = lotka_volterra(0.7, 0.5, 0.3, 0.2, 10, 5, np.linspace(0, 50, 200))
    print(f"Lotka-Volterra OK, len(t)={len(tv)}, x_end={x[-1]:.3f}, y_end={y[-1]:.3f}")
    ts, S, I, R = SIR(0.3, 0.1, 990, 10, 0, np.linspace(0, 100, 200))
    print(f"SIR OK, I_peak={I.max():.1f}, R_end={R[-1]:.1f}")
    te, Ss, E, Ie, Rr = SEIR(0.3, 0.2, 0.1, 980, 10, 10, 0, np.linspace(0, 120, 240))
    print(f"SEIR OK, E_peak={E.max():.1f}, I_peak={Ie.max():.1f}, total={Ss[-1] + E[-1] + Ie[-1] + Rr[-1]:.1f}")
