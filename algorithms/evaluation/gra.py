"""
灰色关联分析(GRA) — 评价题/相关性题常用,可与 VIKOR/TOPSIS 做消融对照
纯 numpy 无额外依赖。接口: from gra import grey_relational
"""
import numpy as np


def grey_relational(reference, comparison, rho=0.5, normalize="init"):
    """
    灰色关联度。
    参数:
        reference: 参考序列(1D array), 如理想解/目标
        comparison: 比较序列矩阵 (m × n), 每一行是一个待评序列
        rho: 分辨系数(默认 0.5)
        normalize: 无量纲化方式 "init"(初值化) / "mean"(均值化)
    返回:
        gamma: 各比较序列与参考序列的关联度 (m,), 越大越优
    """
    ref = np.asarray(reference, dtype=float).ravel()
    comp = np.asarray(comparison, dtype=float)
    if comp.ndim == 1:
        comp = comp.reshape(1, -1)
    if normalize == "init":
        ref = ref / ref[0]
        comp = comp / comp[:, 0:1]
    else:  # mean
        ref = ref / ref.mean()
        comp = comp / comp.mean(axis=1, keepdims=True)

    diff = np.abs(comp - ref)
    mmax, mmin = diff.max(), diff.min()
    xi = (mmin + rho * mmax) / (diff + rho * mmax)   # 关联系数
    return xi.mean(axis=1)                            # 关联度


if __name__ == "__main__":
    # 自测:参考序列为理想效益,3 个方案与之的关联度
    ref = np.array([9, 8, 7, 9])
    schemes = np.array([[7, 6, 5, 8],
                        [9, 8, 7, 9],
                        [5, 4, 6, 7]])
    gamma = grey_relational(ref, schemes)
    print("关联度:", np.round(gamma, 4))
