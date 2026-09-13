"""
cumcm-coach 机理求解模块 — PDE 数值解法速查表

    纯数据 dict + 查询函数, 不含求解逻辑, 零依赖。
    用法:
        from de_quickref import query, DE_QUICKREF
        info = query("parabolic_explicit")   # 返回该行的 dict
"""
DE_QUICKREF = {
    # ---------- 抛物线 PDE (扩散 / 热传导) ----------
    "parabolic_explicit": {
        "type": "抛物线 PDE",
        "method": "FDM 显式 (中心差分+前向欧拉)",
        "example": "fdm_1d.heat_1d_explicit / fdm_2d.fdm_2d_explicit",
        "cfl": "1D r=D*dt/dx^2<=0.5; 2D r=Dx*dt/dx^2+Dy*dt/dy^2<=0.5 (均匀网格单方向 r<0.25)",
        "stability": "条件稳定",
        "note": "实现简单; 时间不长时需很多步, 网格加密代价高",
    },
    "parabolic_implicit": {
        "type": "抛物线 PDE",
        "method": "FDM 隐式 (Crank-Nicolson)/后向欧拉 + 三对角求解",
        "example": "可用 ode_solver 或手写 Thomas 求解",
        "cfl": "无条件稳定 (CN 对步长无限制)",
        "stability": "无条件稳定",
        "note": "每步解线性方程组; CN 二阶时间精度, 适合长时间演化",
    },
    # ---------- 椭圆 PDE (Poisson / Laplace) ----------
    "elliptic_fem": {
        "type": "椭圆 PDE",
        "method": "有限元 FEM (线性三角元)",
        "example": "fem_poisson.assemble_and_solve",
        "cfl": "无 (静态问题)",
        "stability": "无条件稳定",
        "note": "收敛阶 O(h^2); 易处理任意边界形状与变系数 k",
    },
    "elliptic_5point": {
        "type": "椭圆 PDE",
        "method": "五点差分 (中心)",
        "example": "手写离散 + 迭代 (Jacobi/Gauss-Seidel)",
        "cfl": "无 (静态问题)",
        "stability": "无条件稳定",
        "note": "收敛阶 O(h^2); 规则网格下实现最简单",
    },
    # ---------- 双曲 PDE (对流 / 波动) ----------
    "hyperbolic_upwind": {
        "type": "双曲 PDE",
        "method": "迎风差分 (upwind) 或 Lax-Wendroff",
        "example": "手写有限体积 / 差分",
        "cfl": "CFL: c*dt/dx <= 1",
        "stability": "条件稳定",
        "note": "迎风防振荡但有数值耗散; 精度低耗散大, 高阶格式冲激波附近需限制器",
    },
    "hyperbolic_wave": {
        "type": "双曲 PDE",
        "method": "波动方程 二阶中心差",
        "example": "手写蛙跳格式 (leapfrog)",
        "cfl": "CFL: c*dt/dx <= 1",
        "stability": "条件稳定",
        "note": "蛙跳格式守恒能量, CFL=1 时无数值耗散",
    },
    # ---------- 刚性 / 耦合 ODE 系统 ----------
    "stiff_implicit": {
        "type": "刚性/耦合 ODE",
        "method": "隐式 / 自适应步长求解器",
        "example": "ode_solver.solve_ivp_wrapper(method='Radau'/'BDF')",
        "cfl": "无 (自适应步长)",
        "stability": "无条件/L-稳定(隐式)",
        "note": "刚性系统用显式欧拉/RK4 步长过小; 显式用 solve_ivp(RK45), 刚性用 Radau/BDF",
    },
}


def query(method_name):
    """按方法名返回速查行 dict; 未找到抛 ValueError。

    参数: method_name — DE_QUICKREF 的键, 如 'parabolic_explicit'
    返回: dict, 含键 type/method/example/cfl/stability/note
    """
    if method_name in DE_QUICKREF:
        return DE_QUICKREF[method_name]
    raise ValueError(
        f"未知方法: {method_name!r}。可选: {list(DE_QUICKREF.keys())}")


if __name__ == "__main__":
    info = query("elliptic_fem")
    print("方法:", info["method"], "| 收敛:", info["note"])
    print("de_quickref 自测: 通过")
