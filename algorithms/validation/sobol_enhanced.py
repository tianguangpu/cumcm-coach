"""
Sobol 全局灵敏度分析 — 增强版（SALib 优先 + 纯 numpy 降级）

本模块优先使用 SALib (1k★) 库，不可用时自动降级到纯 numpy 实现。
零配置：`pip install salib` 即可获得完整功能；不装也能用。

入口：
  sobol_analysis(model_func, bounds, N=256, seed=42, n_boot=200, method="auto")

返回 dict：
  {
     "S1": [...],       一阶灵敏度指数
     "ST": [...],       总阶灵敏度指数
     "S1_conf": [...],  一阶指数 95% 置信区间
     "ST_conf": [...],  总阶指数 95% 置信区间
     "method": "salib" | "numpy",  实际使用的方法
     "n_eval": int,     模型求值次数
  }

方法选择：
  - "auto": 优先 SALib，不可用时降级
  - "salib": 强制使用 SALib（未安装则报错）
  - "numpy": 强制使用纯 numpy 实现
"""

import warnings

import numpy as np

# 尝试导入 SALib
try:
    from SALib.analyze import sobol as salib_sobol
    from SALib.sample import saltelli as salib_saltelli
    HAS_SALIB = True
except ImportError:
    HAS_SALIB = False


def _sobol_numpy(model_func, bounds, N=256, seed=42, n_boot=200):
    """纯 numpy 实现（降级方案）"""
    D = len(bounds)
    if D < 2:
        raise ValueError("Sobol 分析至少需要 2 个参数维度。")
    lo = np.asarray([b[0] for b in bounds], dtype=float)
    hi = np.asarray([b[1] for b in bounds], dtype=float)
    rng = np.random.default_rng(seed)

    def to_x(U):
        return lo + (hi - lo) * U

    # 基矩阵 A、B 与替换矩阵 AB^i
    A = rng.random((N, D))
    B = rng.random((N, D))
    YA = np.empty(N)
    YB = np.empty(N)
    for j in range(N):
        YA[j] = model_func(to_x(A[j]))
        YB[j] = model_func(to_x(B[j]))

    AB = np.empty((D, N))
    for i in range(D):
        U = A.copy()
        U[:, i] = B[:, i]
        for j in range(N):
            AB[i, j] = model_func(to_x(U[j]))

    # 总方差
    VarY = YA.var(ddof=1)
    if VarY < 1e-14:
        VarY = 1e-14

    # Saltelli 2010 一阶 + Jansen 1999 总阶
    d = AB - YA[None, :]
    S1_raw = (YB[None, :] * d).mean(axis=1) / VarY
    ST = (0.5 * (YA[None, :] - AB) ** 2).mean(axis=1) / VarY
    S1 = np.clip(S1_raw, 0.0, ST)

    # 自举置信区间
    idx = rng.integers(0, N, size=(n_boot, N))
    YA_b = YA[idx]
    YB_b = YB[idx]
    AB_b = AB[:, idx]
    S1b_raw = (YB_b[None, :, :] * (AB_b - YA_b[None, :, :])).mean(axis=-1) / VarY
    STb = (0.5 * (YA_b[None, :, :] - AB_b) ** 2).mean(axis=-1) / VarY
    S1b = np.clip(S1b_raw, 0.0, STb)
    S1_conf = S1b.std(axis=1)
    ST_conf = STb.std(axis=1)

    return {
        "S1": S1.tolist(),
        "ST": ST.tolist(),
        "S1_conf": S1_conf.tolist(),
        "ST_conf": ST_conf.tolist(),
        "method": "numpy",
        "n_eval": N * (D + 2),
    }


def _sobol_salib(model_func, bounds, N=256, seed=42, n_boot=200):
    """SALib 实现（推荐）"""
    D = len(bounds)
    if D < 2:
        raise ValueError("Sobol 分析至少需要 2 个参数维度。")

    # 构造 SALib problem 格式
    problem = {
        "num_vars": D,
        "names": [f"x{i+1}" for i in range(D)],
        "bounds": [list(b) for b in bounds],
    }

    # Saltelli 采样
    X = salib_saltelli.sample(problem, N, seed=seed)

    # 模型求值
    Y = np.array([model_func(x) for x in X])

    # Sobol 分析
    Si = salib_sobol.analyze(problem, Y, calc_second_order=False, n_resamples=n_boot)

    return {
        "S1": Si["S1"].tolist(),
        "ST": Si["ST"].tolist(),
        "S1_conf": Si["S1_conf"].tolist(),
        "ST_conf": Si["ST_conf"].tolist(),
        "method": "salib",
        "n_eval": len(X),
    }


def sobol_analysis(model_func, bounds, N=256, seed=42, n_boot=200, method="auto"):
    """
    Sobol 全局灵敏度分析（自动选择最优实现）

    参数
    ----
    model_func : callable(x:np.ndarray)->float   模型函数
    bounds     : list[(l,u), ...]                每个参数区间
    N          : int                             样本数（默认 256）
    seed       : int                             随机种子
    n_boot     : int                             自举重抽样次数
    method     : str                             "auto"/"salib"/"numpy"

    返回
    ----
    dict : {S1, ST, S1_conf, ST_conf, method, n_eval}
    """
    if method == "auto":
        if HAS_SALIB:
            return _sobol_salib(model_func, bounds, N, seed, n_boot)
        else:
            warnings.warn("SALib 未安装，降级到纯 numpy 实现。建议 `pip install salib` 获得更稳定的结果。")
            return _sobol_numpy(model_func, bounds, N, seed, n_boot)
    elif method == "salib":
        if not HAS_SALIB:
            raise ImportError("SALib 未安装。请运行 `pip install salib`。")
        return _sobol_salib(model_func, bounds, N, seed, n_boot)
    elif method == "numpy":
        return _sobol_numpy(model_func, bounds, N, seed, n_boot)
    else:
        raise ValueError(f"未知方法: {method}，可选 'auto'/'salib'/'numpy'")


# 向后兼容：保留旧接口
sobol_total_and_first = sobol_analysis


if __name__ == "__main__":
    def f(xx):
        return xx[0] + 2.0 * xx[1]

    bounds = [(0.0, 1.0), (0.0, 1.0)]

    print("=" * 50)
    print("测试 Sobol 灵敏度分析")
    print("=" * 50)

    # 测试自动选择
    r = sobol_analysis(f, bounds, N=512, n_boot=200, method="auto")
    print(f"\n方法: {r['method']}")
    print(f"S1 = {[round(v, 3) for v in r['S1']]}  sum = {round(sum(r['S1']), 3)}")
    print(f"ST = {[round(v, 3) for v in r['ST']]}")
    print(f"S1_conf = {[round(v, 4) for v in r['S1_conf']]}")
    print(f"ST_conf = {[round(v, 4) for v in r['ST_conf']]}")
    print(f"总求值次数 = {r['n_eval']}")

    # 验证：可加模型 f = x1 + 2*x2，方差贡献正比于 a_i^2/12
    # Var(x1) = 1/12, Var(x2) = 4/12, 总方差 = 5/12
    # S1(x1) ≈ (1/12)/(5/12) = 0.2, S1(x2) ≈ (4/12)/(5/12) = 0.8
    print("\n期望: S1 ≈ [0.2, 0.8]")
    print(f"实际: S1 = {[round(v, 3) for v in r['S1']]}")
    print(f"误差: {[round(abs(v - e), 3) for v, e in zip(r['S1'], [0.2, 0.8])]}")
