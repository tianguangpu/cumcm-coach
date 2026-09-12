"""优化器边界参数归一化。

统一 GA / DE / NSGA2 / PSO 变体对 ``bounds`` 的接受形式，避免各算法
约定不一致造成的误用。

**为什么需要它**：国赛 B 题通常要求做算法对比（PSO vs GA vs DE），
若各算法对 ``bounds`` 的形式要求不同，用户切换算法时就会踩坑——
例如 ``pso_clerc`` 接受统一边界 ``[(-5, 5)]``，而 ``GA`` 按维度索引
``bounds[j]``，同一份参数传给 GA 会直接抛 IndexError。
"""

import numpy as np


def normalize_bounds(bounds, dim: int) -> np.ndarray:
    """把 ``bounds`` 归一化为 ``(dim, 2)`` 的 float 数组。

    接受三种写法::

        [(lo1, hi1), (lo2, hi2), ...]   逐维边界（行数须等于 dim）
        [(lo, hi)]                      统一边界，广播到各维
        (lo, hi) / [lo, hi]             统一边界的一维写法

    Args:
        bounds: 边界描述，见上。
        dim: 决策变量维度。

    Returns:
        形状 ``(dim, 2)`` 的数组，第 i 行为第 i 个变量的 ``[下界, 上界]``。

    Raises:
        ValueError: 行数与 ``dim`` 不匹配且无法广播为统一边界时。
    """
    b = np.asarray(bounds, dtype=float)

    if b.ndim == 1:
        if b.size != 2:
            raise ValueError(
                f"一维形式的 bounds 应为 (lo, hi)，实际收到 {b.size} 个值"
            )
        b = np.tile(b.reshape(1, 2), (dim, 1))
    elif b.shape[0] == 1 and dim > 1:
        # 形如 [(lo, hi)]：视为统一边界，广播到各维
        b = np.tile(b, (dim, 1))

    if b.shape[0] != dim:
        raise ValueError(
            f"bounds 需要 {dim} 行（每个变量一行），实际收到 {b.shape[0]} 行；"
            f"若所有变量取值范围相同，可简写为 bounds=[(lo, hi)]"
        )
    return b
