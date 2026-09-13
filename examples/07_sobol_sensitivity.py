"""示例 7：全局灵敏度分析 —— Sobol（通用，四重检验之一）

国赛四重检验要求灵敏度分析。本示例用 Sobol 全局灵敏度分析
Ishigami 函数（含参数交互），输出一阶 S1 与总阶 ST 及置信区间。

运行::

    python examples/07_sobol_sensitivity.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.validation.sobol import sobol_total_and_first  # noqa: E402


def ishigami(x):
    """Ishigami 函数：3 参数，x1 与 x3 有交互，是 Sobol 标准测试函数。

    真实灵敏度（理论值）：S1 ≈ [0.314, 0.442, 0]，ST ≈ [0.557, 0.442, 0.244]
    """
    return float(
        np.sin(x[0]) + 7.0 * np.sin(x[1]) ** 2 + 0.1 * x[2] ** 4 * np.sin(x[0])
    )


BOUNDS = [(-np.pi, np.pi)] * 3
NAMES = ["x1", "x2", "x3"]


def main():
    print("=" * 60)
    print("  通用：Sobol 全局灵敏度分析（Ishigami 函数）")
    print("=" * 60)

    r = sobol_total_and_first(ishigami, BOUNDS, N=512, seed=42, n_boot=200)

    print(f"  模型评估次数: {r['n_eval']}")
    print(f"\n  {'参数':<6}{'一阶 S1':>10}{'总阶 ST':>10}{'S1 置信':>12}{'ST 置信':>12}")
    print("  " + "-" * 52)
    for i, name in enumerate(NAMES):
        print(f"  {name:<6}{r['S1'][i]:>10.3f}{r['ST'][i]:>10.3f}"
              f"{r['S1_conf'][i]:>12.3f}{r['ST_conf'][i]:>12.3f}")

    # 解读：ST 明显大于 S1 的参数存在交互效应
    print("\n  解读：")
    for i, name in enumerate(NAMES):
        inter = r["ST"][i] - r["S1"][i]
        if inter > 0.05:
            print(f"    {name}：ST>S1 达 {inter:.3f}，存在参数交互效应")
        elif r["ST"][i] > 0.1:
            print(f"    {name}：主效应为主（S1≈ST≈{r['S1'][i]:.3f}）")
        else:
            print(f"    {name}：灵敏度很低（ST={r['ST'][i]:.3f}），可忽略")

    print("\n提示：把 ishigami 换成你的模型函数（形如 f(x) -> float），")
    print("      BOUNDS 换成各参数的取值范围，即可做真实灵敏度分析。")


if __name__ == "__main__":
    main()
