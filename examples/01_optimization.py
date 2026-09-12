"""示例 1：优化算法对比（B 题场景）

国赛 B 题通常要求做算法对比。本示例用同一份问题配置跑
遗传算法（GA）/ 差分进化（DE）/ Clerc 收敛系数 PSO，
输出对比表并绘制收敛曲线。

运行::

    python examples/01_optimization.py

输出:
    examples/output/01_convergence.png
"""

import sys
from pathlib import Path

import numpy as np

# 使示例无需 pip install 即可运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.optimization.de import DE  # noqa: E402
from algorithms.optimization.ga import GA  # noqa: E402
from algorithms.optimization.pso_variants import pso_clerc  # noqa: E402

SEED = 42


def rastrigin(x):
    """Rastrigin 函数：多峰，易陷入局部最优，常用于检验全局搜索能力。"""
    n = len(x)
    return float(10 * n + sum(v**2 - 10 * np.cos(2 * np.pi * v) for v in x))


def sphere(x):
    """球函数：单峰，用于检验收敛速度。"""
    return float(sum(v**2 for v in x))


# 问题配置：三维，各分量取值范围相同
DIM = 3
BOUNDS = [(-5.12, 5.12)]
ITERS = 200


def main():
    print("=" * 62)
    print("  优化算法对比 — Rastrigin 函数（3 维，多峰）")
    print("=" * 62)
    print(f"  变量维度: {DIM}   取值范围: {BOUNDS[0]}   迭代: {ITERS}")
    print()

    results = {}

    # --- 遗传算法 ---
    ga = GA(rastrigin, dim=DIM, bounds=BOUNDS, pop_size=50, max_gen=ITERS, seed=SEED)
    r_ga = ga.solve(verbose=False)
    results["GA"] = r_ga

    # --- 差分进化 ---
    de = DE(rastrigin, dim=DIM, bounds=BOUNDS, pop_size=50, max_gen=ITERS, seed=SEED)
    r_de = de.solve(verbose=False)
    results["DE"] = r_de

    # --- Clerc 系数 PSO ---
    r_pso = pso_clerc(rastrigin, dim=DIM, bounds=BOUNDS, iters=ITERS, swarms=50, seed=SEED)
    results["PSO(Clerc)"] = r_pso

    # --- 对比表 ---
    print(f"  {'算法':<12}{'最优值':>14}{'最优解':>34}")
    print("  " + "-" * 58)
    for name, r in results.items():
        f_opt = r.get("f_opt", r.get("g_val"))
        x_opt = r.get("x_opt", r.get("g_best"))
        x_str = "[" + ", ".join(f"{v:6.3f}" for v in np.asarray(x_opt).ravel()) + "]"
        print(f"  {name:<12}{f_opt:>14.6f}{x_str:>34}")

    # --- 收敛曲线 ---
    try:
        import matplotlib

        matplotlib.use("Agg")  # 无图形界面环境下也能保存图片

        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(8, 5))

        if r_ga.get("history"):
            ax.plot(r_ga["history"], label="GA", linewidth=1.8)
        if r_de.get("history"):
            ax.plot(r_de["history"], label="DE", linewidth=1.8)
        if r_pso.get("history"):
            ax.plot(r_pso["history"], label="PSO (Clerc)", linewidth=1.8)

        ax.set_yscale("log")
        ax.set_xlabel("迭代代数")
        ax.set_ylabel("当前最优值（对数刻度）")
        ax.set_title(f"三种算法在 Rastrigin 函数上的收敛对比（{DIM} 维）")
        ax.legend()
        ax.grid(alpha=0.3)

        out_dir = Path(__file__).resolve().parent / "output"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "01_convergence.png"
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print()
        print(f"  收敛曲线已保存: {out_path}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print()
    print("提示：把 rastrigin 换成你自己的目标函数、调整 BOUNDS 即可用于实际赛题。")
    print("     若各变量量纲不同，逐维给出边界，例如 BOUNDS=[[0,10],[-1,1],[-5,5]]")


if __name__ == "__main__":
    main()
