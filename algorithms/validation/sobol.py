"""
cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— Sobol 全局灵敏度分析

本文档属于 cumcm-coach-skill-v7 算法库的《验证/全局灵敏度》子模块。

用纯 numpy 实现 Saltelli 采样 + 一阶(S1) / 总阶(ST) Sobol 指数，
不依赖 SALib，保证零外部新增依赖可用(本模块仅用 numpy)。

约定：
  - model_func(x_array) -> scalar   模型函数(输入参数向量，输出标量响应)
  - bounds = [(l,u),...]            各参数取值区间

入口：
  sobol_total_and_first(model_func, bounds, N=256, problem=None, seed=42, n_boot=200)

返回 dict：
  {
     "S1": [...],       一阶灵敏度指数 Var(E[Y|Xi])/Var(Y)
     "ST": [...],       总阶灵敏度指数 1 - Var(E[Y|X~i])/Var(Y)
     "S1_conf": [...],  一阶指数的自举标准差(近似 95% 置信区间约 ±2*conf)
     "ST_conf": [...],  总阶指数的自举标准差
  }

采样方案
--------
1) 生成两个独立的 N x D 基矩阵 A、B(默认均匀随机，seed 可复现)；
   构造 D 个矩阵 AB^i(A 中第 i 列替换为 B 的第 i 列)，
   总模型求值数 = N*(D+2)。
2) 一阶估计算子：S1_i = E[Y_B * (Y_AB_i - Y_A)] / Var(Y_A)
   总阶估计算子：ST_i = (1/2) * E[(Y_A - Y_AB_i)^2] / Var(Y_A)   (Jansen)
3) 置信区间用自举法对 N 个基样本重抽样得到。

数值验证(内置 __main__)：对可加模型 f = x1 + 2*x2 在 [0,1] 上，
S1 应大致正比于各参数方差贡献、且 S1 之和接近 1，ST 接近 S1。
"""
import numpy as np


def sobol_total_and_first(model_func, bounds, N=256, problem=None, seed=42, n_boot=200):
    """
    计算一阶与总阶 Sobol 全局灵敏度指数(零依赖，纯 numpy)。

    参数
    ----
    model_func : callable(x:np.ndarray)->float   模型函数
    bounds     : list[(l,u), ...]                每个参数区间
    N          : int                             每个基矩阵/替换块的样本数(默认 256)
    problem    : dict,可选                       兼容接口占位(已内建, 无需)
    seed       : int                             随机种子(保证可复现)
    n_boot     : int                             自举重抽样次数(默认 200)

    返回
    ----
    dict : {S1, ST, S1_conf, ST_conf}
    """
    D = len(bounds)
    if D < 2:
        raise ValueError("Sobol 分析至少需要 2 个参数维度。")
    lo = np.asarray([b[0] for b in bounds], dtype=float)
    hi = np.asarray([b[1] for b in bounds], dtype=float)
    rng = np.random.default_rng(seed)

    def to_x(U):
        return lo + (hi - lo) * U

    # ---- 基矩阵 A、B 与替换矩阵 AB^i ----
    A = rng.random((N, D))
    B = rng.random((N, D))
    YA = np.empty(N)
    YB = np.empty(N)
    for j in range(N):
        YA[j] = model_func(to_x(A[j]))
        YB[j] = model_func(to_x(B[j]))

    AB = np.empty((D, N))          # AB[i, j] = model(AB^i_第j个)
    for i in range(D):
        U = A.copy()
        U[:, i] = B[:, i]
        for j in range(N):
            AB[i, j] = model_func(to_x(U[j]))

    # ---- 总方差 ----
    VarY = YA.var(ddof=1)
    if VarY < 1e-14:  # 防除零: 模型几乎恒定
        VarY = 1e-14

    # ---- 基估计 (Saltelli 2010 一阶 + Jansen 总阶) ----
    # 一阶: S1_i = Var(E[Y|Xi]) / Var(Y) 用 Saltelli 2010 估计器
    #   = (1/N) Σ YB_j * (AB^i_j - YA_j) / Var(Y)
    # 总阶: ST_i = 1 - Var(E[Y|X~i]) / Var(Y) 用 Jansen 1999 估计器
    #   = (1/(2N)) Σ (YA_j - AB^i_j)^2 / Var(Y)
    d = AB - YA[None, :]                        # (D, N)
    S1_raw = (YB[None, :] * d).mean(axis=1) / VarY
    ST = (0.5 * (YA[None, :] - AB) ** 2).mean(axis=1) / VarY
    # S1 截断到 [0, ST]：负值是采样方差导致的，不是真实效应
    S1 = np.clip(S1_raw, 0.0, ST)

    # ---- 自举置信区间 ----
    idx = rng.integers(0, N, size=(n_boot, N))   # (n_boot, N)
    YA_b = YA[idx]                               # (n_boot, N)
    YB_b = YB[idx]                               # (n_boot, N)
    AB_b = AB[:, idx]                            # (D, n_boot, N)
    S1b_raw = (YB_b[None, :, :] * (AB_b - YA_b[None, :, :])).mean(axis=-1) / VarY   # (D, n_boot)
    STb = (0.5 * (YA_b[None, :, :] - AB_b) ** 2).mean(axis=-1) / VarY           # (D, n_boot)
    S1b = np.clip(S1b_raw, 0.0, STb)
    S1_conf = S1b.std(axis=1)
    ST_conf = STb.std(axis=1)

    return {
        "S1": S1.tolist(),
        "ST": ST.tolist(),
        "S1_conf": S1_conf.tolist(),
        "ST_conf": ST_conf.tolist(),
        "n_eval": N * (D + 2),
    }


if __name__ == "__main__":
    def f(xx):   # 可加模型: 方差贡献正比于 a_i^2/12
        return xx[0] + 2.0 * xx[1]

    bounds = [(0.0, 1.0), (0.0, 1.0)]
    r = sobol_total_and_first(f, bounds, N=512, n_boot=200)
    print("S1 =", [round(v, 3) for v in r["S1"]], " sum =", round(sum(r["S1"]), 3))
    print("ST =", [round(v, 3) for v in r["ST"]])
    print("S1_conf =", [round(v, 4) for v in r["S1_conf"]])
    print("ST_conf =", [round(v, 4) for v in r["ST_conf"]])
    print("总求值次数 =", r["n_eval"])
