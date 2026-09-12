# -*- coding: utf-8 -*-
"""
VIKOR 多准则折中排序 — 评价/决策题(国赛 C 题)常用,可与 TOPSIS 做消融对照
纯 numpy 无额外依赖。接口: from vikor import VIKOR
"""
import numpy as np


def VIKOR(decision_matrix, weights, benefit, v=0.5):
    """
    VIKOR 折中排序法。
    参数:
        decision_matrix: 决策矩阵 (m 方案 × n 准则), 数值
        weights: 准则权重 (n,), 通常来自 AHP/熵权
        benefit: 布尔数组 (n,), True=效益型(越大越好), False=成本型(越小越好)
        v: 群体效用权重(默认 0.5, 折中解)
    返回:
        Q: 折中指数 (m,), 越小越优
        S: 群体效用 (m,)
        R: 个体遗憾 (m,)
        ranking: 按 Q 升序的方案索引
    """
    X = np.asarray(decision_matrix, dtype=float)
    w = np.asarray(weights, dtype=float)
    benefit = np.asarray(benefit, dtype=bool)

    f_best = np.where(benefit, X.max(axis=0), X.min(axis=0))
    f_worst = np.where(benefit, X.min(axis=0), X.max(axis=0))
    rng = f_best - f_worst
    rng[rng == 0] = 1e-12                      # 防除零(准则全相等)

    d = (f_best - X) / rng                     # 规范化距离(成本型已由 benefit 翻转)
    S = (w * d).sum(axis=1)                    # 群体效用
    R = (w * d).max(axis=1)                    # 个体遗憾

    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()
    Q = v * (S - S_star) / (S_minus - S_star + 1e-12) \
        + (1 - v) * (R - R_star) / (R_minus - R_star + 1e-12)
    ranking = np.argsort(Q)                    # Q 越小越优
    return Q, S, R, ranking


if __name__ == "__main__":
    # 自测:3 方案 × 4 准则(前 2 效益型, 后 2 成本型)
    X = np.array([[80, 90, 600, 5.4],
                  [65, 75, 400, 4.8],
                  [90, 70, 550, 6.0]])
    w = np.array([0.3, 0.2, 0.3, 0.2])
    benefit = [True, True, False, False]
    Q, S, R, rank = VIKOR(X, w, benefit)
    print("Q(越小越优):", np.round(Q, 4))
    print("排序(方案索引):", rank + 1)
