"""
cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 纳什均衡

本文档属于 cumcm-coach-skill-v7 算法库的《博弈》子模块。

功能：
  1. pure_nash(payoff_matrix)          2x2 二人矩阵博弈的纯策略纳什均衡
  2. mixed_nash_2x2(payoffA, payoffB)  2x2 一般二人博弈的混合策略纳什均衡

约定：
  - payoffA 为“行玩家”(玩家1) 的 2x2 收益矩阵；
  - payoffB 为“列玩家”(玩家2) 的 2x2 收益矩阵；
  - 若只传入一个矩阵给 pure_nash，则按“二人零和博弈”处理(玩家2 收益 = -payoff)。
  - 均衡以概率向量给出：strategy_row=[p0,p1], strategy_col=[q0,q1]。

依赖：仅 numpy，无任何第三方依赖。
"""
import numpy as np


def _profile_is_nash(A, B, pr, qc):
    """判断混合策略 (pr, qc) 是否为纳什均衡。pr 行玩家，qc 列玩家。"""
    er = A @ qc      # 行玩家每个纯策略的期望收益
    ec = pr @ B      # 列玩家每个纯策略的期望收益
    maxr, maxc = er.max(), ec.max()
    if not np.all(pr[er < maxr - 1e-12] == 0):
        return False
    return np.all(qc[ec < maxc - 1e-12] == 0)


def pure_nash(payoff_matrix):
    """
    求 2x2 二人矩阵博弈的纯策略纳什均衡 (按零和博弈处理)。

    参数
    ----
    payoff_matrix : array_like, shape=(2,2)
        行玩家收益矩阵；列玩家收益取其负号(零和)。

    返回
    ----
    list[dict]：每个元素表示一个纯策略纳什均衡，含字段
        row, col                  : 均衡所在行/列
        strategy_row, strategy_col: 退化后的概率向量(单点)
        payoff_row, payoff_col    : 双方收益
        is_pure                   : True
    """
    A = np.asarray(payoff_matrix, dtype=float)
    res = []
    for i in range(2):
        for j in range(2):
            if A[i, j] < A[1 - i, j] - 1e-12:   # 行 i 须是列 j 中最大值
                continue
            if A[i, j] > A[i, 1 - j] + 1e-12:   # 列 j 须是行 i 中最小值(列玩家最小化)
                continue
            pr = np.zeros(2); pr[i] = 1.0
            qc = np.zeros(2); qc[j] = 1.0
            res.append({
                "row": i, "col": j,
                "strategy_row": pr.tolist(),
                "strategy_col": qc.tolist(),
                "payoff_row": float(A[i, j]),
                "payoff_col": float(-A[i, j]),
                "is_pure": True, "type": "pure",
            })
    return res


def mixed_nash_2x2(payoffA, payoffB=None):
    """
    求 2x2 一般二人博弈的混合策略纳什均衡。

    参数
    ----
    payoffA : array_like,(2,2)   玩家1 收益
    payoffB : array_like,(2,2),可选  玩家2 收益；缺省按零和(-payoffA)

    返回
    ----
    list[dict]：纳什均衡列表(可能同时含纯策略与混合策略)，元素含
        strategy_row / strategy_col : 混合概率向量
        payoff_row / payoff_col     : 均衡收益
        is_pure                     : 是否纯策略
        type                        : "pure" 或 "mixed"

    说明
    ----
    纯策略通过逐格最优反应判定；混合策略通过“无差异条件”构造：
    行玩家以 (p,1-p) 使列玩家两列无差异，列玩家以 (q,1-q) 使行玩家两行无差异。
    退化/边界情形交由纯策略覆盖。
    """
    A = np.asarray(payoffA, dtype=float)
    B = np.asarray(payoffB, dtype=float) if payoffB is not None else -A

    eqs = []
    for i in range(2):
        for j in range(2):
            if A[i, j] < A[1 - i, j] - 1e-12:
                continue
            if B[i, j] < B[i, 1 - j] - 1e-12:
                continue
            pr = np.zeros(2); pr[i] = 1.0
            qc = np.zeros(2); qc[j] = 1.0
            eqs.append({
                "strategy_row": pr.tolist(), "strategy_col": qc.tolist(),
                "payoff_row": float(A[i, j]), "payoff_col": float(B[i, j]),
                "is_pure": True, "type": "pure",
            })

    den_p = (A[0, 0] + A[1, 1]) - (A[0, 1] + A[1, 0])
    den_q = (B[0, 0] + B[1, 1]) - (B[0, 1] + B[1, 0])
    p = (B[1, 1] - B[1, 0]) / den_q if abs(den_q) > 1e-12 else None
    q = (A[1, 1] - A[0, 1]) / den_p if abs(den_p) > 1e-12 else None
    if p is not None and q is not None and (0.0 < p < 1.0) and (0.0 < q < 1.0):
        pr = np.array([p, 1 - p], dtype=float)
        qc = np.array([q, 1 - q], dtype=float)
        if _profile_is_nash(A, B, pr, qc):
            eqs.append({
                "strategy_row": pr.tolist(), "strategy_col": qc.tolist(),
                "payoff_row": float(pr @ A @ qc), "payoff_col": float(pr @ B @ qc),
                "is_pure": False, "type": "mixed",
            })

    seen = set()
    unique = []
    for e in eqs:
        key = (tuple(np.round(e["strategy_row"], 6)), tuple(np.round(e["strategy_col"], 6)))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


if __name__ == "__main__":
    print("猜硬币(零和)纯策略均衡:", pure_nash([[1, -1], [-1, 1]]))
    print("猜硬币(零和)混合均衡:", mixed_nash_2x2([[1, -1], [-1, 1]]))
