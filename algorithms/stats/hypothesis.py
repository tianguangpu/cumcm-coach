# -*- coding: utf-8 -*-
"""
cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 统计检验

本文档属于 cumcm-coach-skill-v7 算法库的《统计》子模块。

提供常用统计检验的封装，统一返回 dict{statistic, p_value, conclusion}。
conclusion 表示“在 0.05 显著性水平下是否显著(是否拒绝原假设)”：
  conclusion = True  -> 有显著差异 / 拒绝原假设
  conclusion = False -> 无充分证据

函数：
  - ks_test(x, y=None, dist="norm")   Kolmogorov-Smirnov 检验(单样本/两样本)
  - anova_oneway(groups)               单因素方差分析(one-way ANOVA)
  - chisq_test(observed, expected=None) 卡方拟合优度检验
  - mann_whitney_u(x, y)               Mann-Whitney U(两独立样本秩和检验)
  - paired_t(x, y)                     配对样本 t 检验

依赖：numpy, scipy.stats。
"""
import numpy as np
from scipy import stats


def _summary(statistic, p_value):
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "conclusion": bool(p_value < 0.05),
        "alpha": 0.05,
    }


def _frozen_dist(dist, x):
    """由样本估计参数并返回 scipy 冻结分布(便于 kstest 用其 cdf)。"""
    if dist == "norm":
        return stats.norm(loc=x.mean(), scale=x.std(ddof=1))
    if dist == "uniform":
        return stats.uniform(loc=x.min(), scale=x.max() - x.min())
    if dist == "expon":
        return stats.expon(scale=x.mean())
    # 兜底: 其余字符串直接取 scipy.stats 中的分布(无参数)
    return getattr(stats, dist)()


def ks_test(x, y=None, dist="norm"):
    """
    Kolmogorov-Smirnov 检验。
      - 若提供 y：两样本 KS 检验(检验两个分布是否相同)。
      - 若未提供 y：单样本 KS 检验(检验 x 是否服从给定分布 dist，默认正态)，
        并自动用样本矩估计分布参数。
    返回 dict{statistic, p_value, conclusion}。
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    if y is not None:
        y = np.asarray(y, dtype=float).reshape(-1)
        statistic, p = stats.ks_2samp(x, y)
    else:
        cdf = _frozen_dist(dist, x).cdf
        statistic, p = stats.kstest(x, cdf)
    return _summary(statistic, p)


def anova_oneway(groups):
    """
    单因素方差分析(one-way ANOVA)。groups 为若干个样本序列(list of array)。
    零假设：各组的总体均值相等。
    返回 dict{statistic(F), p_value, conclusion}。
    """
    groups = [np.asarray(g, dtype=float).reshape(-1) for g in groups]
    statistic, p = stats.f_oneway(*groups)
    return _summary(statistic, p)


def chisq_test(observed, expected=None):
    """
    卡方拟合优度检验。
      - expected 缺省时为“均匀”期望(各分类期望 = 总数/类别数)。
      - 也可提供期望频数做拟合优度检验。
    返回 dict{statistic, p_value, conclusion}。
    """
    observed = np.asarray(observed, dtype=float).reshape(-1)
    f_exp = None if expected is None else np.asarray(expected, dtype=float).reshape(-1)
    statistic, p = stats.chisquare(f_obs=observed, f_exp=f_exp)
    return _summary(statistic, p)


def mann_whitney_u(x, y):
    """
    Mann-Whitney U 检验(两独立样本的非参数秩和检验)。
    零假设：两总体分布相同。返回 dict{statistic(U), p_value, conclusion}。
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    statistic, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    return _summary(statistic, p)


def paired_t(x, y):
    """
    配对样本 t 检验(考察配对样本的均值差异)。
    零假设：配对差值的总体均值为 0。返回 dict{statistic(t), p_value, conclusion}。
    """
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    statistic, p = stats.ttest_rel(x, y)
    return _summary(statistic, p)


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    print("KS 正态自检:", ks_test(rng.normal(size=500)))
    print("KS 两样本:", ks_test(rng.normal(size=100), rng.normal(0.5, 1, 100)))
    print("ANOVA:", anova_oneway([rng.normal(1, 1, 60), rng.normal(2, 1, 60)]))
    print("chisq:", chisq_test([40, 60, 50, 50]))
    print("MannWhitney:", mann_whitney_u(rng.normal(size=80), rng.normal(0.8, 1, 80)))
    print("Paired-t:", paired_t(rng.normal(size=90), rng.normal(0.3, 1, 90)))
