"""示例 6：B 题多目标优化 —— NSGA-II（帕累托前沿）

B 题（优化类）常涉及多个互相冲突的目标（如成本 vs 质量）。
本示例用 NSGA-II 求解 ZDT1 双目标测试问题，输出帕累托前沿。

运行::

    python examples/06_nsga2_multiobjective.py

输出:
    examples/output/06_pareto_front.png
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.optimization.nsga2 import NSGA2  # noqa: E402


def zdt1(x):
    """ZDT1 双目标测试函数（30 维），目标 1 与目标 2 互相冲突。"""
    n = len(x)
    f1 = float(x[0])
    g = 1.0 + 9.0 * sum(x[1:]) / (n - 1)
    f2 = float(g * (1.0 - np.sqrt(f1 / g)))
    return f1, f2


DIM = 30
BOUNDS = [(0.0, 1.0)] * DIM


def main():
    print("=" * 60)
    print("  B 题多目标优化：NSGA-II 求 ZDT1 帕累托前沿")
    print("=" * 60)

    ns = NSGA2(
        [lambda x: zdt1(x)[0], lambda x: zdt1(x)[1]],
        dim=DIM,
        bounds=BOUNDS,
        pop_size=100,
        max_gen=100,
    )
    r = ns.solve()

    pareto_X = np.asarray(r["pareto_X"])
    pareto_F = np.asarray(r["pareto_F"])
    print(f"  帕累托前沿点数: {r['n_pareto']}")
    print(f"  超体积 (HV, 越大越好): {r.get('hv', 0):.4f}")
    print(f"  前沿散布 (spread, 越均匀越好): {r.get('spread', 0):.4f}")
    if pareto_F.size:
        print(f"  目标 1 范围: [{pareto_F[:, 0].min():.4f}, {pareto_F[:, 0].max():.4f}]")
        print(f"  目标 2 范围: [{pareto_F[:, 1].min():.4f}, {pareto_F[:, 1].max():.4f}]")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(pareto_F[:, 0], pareto_F[:, 1], s=14, c="#2166AC", alpha=0.7)
        ax.set_xlabel("目标 1（越小越好）")
        ax.set_ylabel("目标 2（越小越好）")
        ax.set_title(f"NSGA-II 帕累托前沿（{r['n_pareto']} 个非支配解）")
        ax.grid(alpha=0.3)

        out = Path(__file__).resolve().parent / "output" / "06_pareto_front.png"
        out.parent.mkdir(exist_ok=True)
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"\n  帕累托前沿图已保存: {out}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print("\n提示：把 zdt1 换成你的两个真实目标函数（如成本/效率），")
    print("      即可得到可取舍的帕累托最优方案集，供评委看权衡。")


if __name__ == "__main__":
    main()
