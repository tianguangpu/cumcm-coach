"""示例 2：综合评价（C 题场景）

演示「AHP 主观赋权 + 熵权法客观赋权 + TOPSIS 排序」的标准评价流程。
这是 C 题（评价决策类）最常见的组合方法。

运行::

    python examples/02_evaluation.py

输出:
    examples/output/02_ranking.png
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation  # noqa: E402

# 4 个方案 × 3 个指标（均为效益型指标：数值越大越好）
SCHEMES = ["方案 A", "方案 B", "方案 C", "方案 D"]
CRITERIA = ["经济性", "技术性", "环保性"]
DATA = [
    [7, 9, 9],
    [8, 6, 8],
    [9, 4, 7],
    [6, 8, 6],
]


def main():
    print("=" * 62)
    print("  综合评价 — AHP + 熵权法 + TOPSIS")
    print("=" * 62)
    print(f"  方案数: {len(SCHEMES)}   指标数: {len(CRITERIA)}（均为效益型）")
    print()

    ev = ComprehensiveEvaluation(DATA, benefit_cols=[0, 1, 2], cost_cols=[])

    # --- 1) 熵权法：由数据自身离散程度决定权重（客观）---
    w_entropy = np.asarray(ev.run_entropy(), dtype=float)
    print("  [客观赋权] 熵权法权重")
    for name, w in zip(CRITERIA, w_entropy):
        print(f"    {name}: {w:.4f}")

    # --- 2) AHP：由成对比较矩阵导出权重（主观）---
    # 判断矩阵元素 a[i][j] 表示"指标 i 相对指标 j 的重要程度"
    pairwise = np.array([
        [1.0, 2.0, 3.0],
        [1 / 2, 1.0, 2.0],
        [1 / 3, 1 / 2, 1.0],
    ])
    w_ahp = np.asarray(ev.run_ahp(pairwise), dtype=float)
    print()
    print("  [主观赋权] AHP 权重（判断矩阵：经济性 > 技术性 > 环保性）")
    for name, w in zip(CRITERIA, w_ahp):
        print(f"    {name}: {w:.4f}")

    # --- 3) 组合赋权：主客观权重按 alpha 融合 ---
    w_combined = np.asarray(ev.combine_weights(alpha=0.5), dtype=float)
    print()
    print("  [组合赋权] alpha=0.5（主观与客观各占一半）")
    for name, w in zip(CRITERIA, w_combined):
        print(f"    {name}: {w:.4f}")

    # --- 4) TOPSIS：按与理想解的贴近度排序 ---
    scores = np.asarray(ev.topsis(), dtype=float)
    ranking = sorted(zip(SCHEMES, scores), key=lambda t: -t[1])

    print()
    print("  [TOPSIS 排序结果]")
    print(f"    {'名次':<6}{'方案':<10}{'贴近度':>10}")
    print("    " + "-" * 28)
    for rank, (name, score) in enumerate(ranking, start=1):
        print(f"    第{rank}名  {name:<10}{score:>10.4f}")

    print()
    print(f"  最优方案: {ranking[0][0]}（贴近度 {ranking[0][1]:.4f}）")

    # --- 可视化 ---
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        # 左：权重对比
        x = np.arange(len(CRITERIA))
        width = 0.38
        ax1.bar(x - width / 2, w_entropy, width, label="熵权法（客观）", color="#2166AC")
        ax1.bar(x + width / 2, w_ahp, width, label="AHP（主观）", color="#D6604D")
        ax1.set_xticks(x)
        ax1.set_xticklabels(CRITERIA)
        ax1.set_ylabel("权重")
        ax1.set_title("两种赋权方法对比")
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # 右：TOPSIS 贴近度
        names = [t[0] for t in ranking]
        vals = [t[1] for t in ranking]
        colors = ["#4DAF4A" if i == 0 else "#BDBDBD" for i in range(len(names))]
        ax2.barh(names[::-1], vals[::-1], color=colors[::-1])
        ax2.set_xlabel("TOPSIS 贴近度")
        ax2.set_title("方案排序（绿色为最优）")
        ax2.grid(axis="x", alpha=0.3)

        out_dir = Path(__file__).resolve().parent / "output"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "02_ranking.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print(f"  评价结果图已保存: {out_path}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print()
    print("提示：benefit_cols 填效益型指标列号，cost_cols 填成本型指标列号。")
    print("     若指标量纲差异大，本类内部会做归一化，无需手动标准化。")


if __name__ == "__main__":
    main()
