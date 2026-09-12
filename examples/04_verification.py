"""示例 4：四重检验（国赛金标准）

国赛要求对模型做多重验证。本示例演示其中三项：

1. 局部灵敏度 —— 逐参数扰动，给出弹性系数与敏感度分级
2. 全局灵敏度 —— Sobol 一阶指数 S1 与总效应指数 ST，可捕捉交互作用
3. 假设误差量化 —— 逐条放松假设，量化对结论的影响并分级

（第四项「拟合精度」依赖具体模型，可用 ``algorithms/validation/metrics.py``
中的 ``FitMetrics`` 计算 R²/MAE/RMSE。）

运行::

    python examples/04_verification.py

输出:
    examples/output/04_sensitivity.png
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.validation.assumption_error import AssumptionChecker  # noqa: E402
from algorithms.validation.sensitivity import SensitivityAnalyzer  # noqa: E402
from algorithms.validation.sobol_enhanced import sobol_analysis  # noqa: E402

# 一个简化的生产利润模型：利润 = 单价×产量×良率 - 单位成本×产量
BASE_PARAMS = {"price": 12.0, "cost": 7.0, "yield_rate": 0.90}
PRODUCTION = 1000.0


def profit_model(p):
    """参数化利润模型（支持 dict 与数组两种输入）。"""
    if isinstance(p, dict):
        return p["price"] * PRODUCTION * p["yield_rate"] - p["cost"] * PRODUCTION
    return p[0] * PRODUCTION * p[2] - p[1] * PRODUCTION


def main():
    print("=" * 62)
    print("  四重检验 — 灵敏度与假设误差量化")
    print("=" * 62)

    base_value = profit_model(BASE_PARAMS)
    print(f"  基准参数: {BASE_PARAMS}")
    print(f"  基准利润: {base_value:.2f}")
    print()

    # ---------------- 1) 局部灵敏度 ----------------
    print("  [1] 局部灵敏度（弹性系数 = 输出相对变化 / 输入相对变化）")
    sa = SensitivityAnalyzer(profit_model, BASE_PARAMS, perturbations=(0.1, 0.2))
    sa.analyze()
    summary = sa.elasticity_summary()

    print(f"    {'参数':<14}{'弹性系数':>12}{'分级':>10}")
    print("    " + "-" * 36)
    for name, info in summary.items():
        elast = info.get("elasticity", info) if isinstance(info, dict) else info
        grade = info.get("grade", "-") if isinstance(info, dict) else "-"
        print(f"    {name:<14}{float(elast):>12.4f}{str(grade):>10}")

    # ---------------- 2) 全局灵敏度 ----------------
    print()
    print("  [2] 全局灵敏度（Sobol 指数，N=256 采样）")
    bounds = [[8.0, 16.0], [5.0, 9.0], [0.75, 0.99]]
    names = ["price", "cost", "yield_rate"]

    sobol = sobol_analysis(profit_model, bounds=bounds, N=256, seed=42, n_boot=50)
    print(f"    实现方式: {sobol.get('method')}   评估次数: {sobol.get('n_eval')}")
    print(f"    {'参数':<14}{'S1 (一阶)':>14}{'ST (总效应)':>14}")
    print("    " + "-" * 42)
    for i, name in enumerate(names):
        print(f"    {name:<14}{sobol['S1'][i]:>14.4f}{sobol['ST'][i]:>14.4f}")

    gap = max(abs(np.asarray(sobol["ST"]) - np.asarray(sobol["S1"])))
    print(f"    ST 与 S1 最大差值: {gap:.4f}（差值大说明存在参数交互作用）")

    # ---------------- 3) 假设误差量化 ----------------
    print()
    print("  [3] 假设误差量化（逐条放松假设，观察结论变化）")
    checker = AssumptionChecker(
        base_output=base_value,
        assumptions=[
            {
                "name": "良率视为常数",
                "relax_func": lambda: profit_model(
                    {**BASE_PARAMS, "yield_rate": 0.85}
                ),
                "relaxed_name": "良率随批次波动降至 0.85",
            },
            {
                "name": "单价固定",
                "delta": 0.08,
                "relaxed_name": "市场价格下浮 8%",
            },
            {
                "name": "忽略固定成本",
                "delta": 0.02,
                "relaxed_name": "计入固定成本摊销",
            },
        ],
    )
    report = checker.analyze()

    print(f"    {'假设':<18}{'影响占比':>10}{'等级':>8}")
    print("    " + "-" * 38)
    for detail in report["details"]:
        print(f"    {detail['name']:<18}{detail['impact_pct']:>9.2f}%{detail['grade']:>8}")

    print(f"    致命影响: {report['n_fatal']} 项   显著影响: {report['n_significant']} 项")

    # ---------------- 可视化 ----------------
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))

        # 左：Sobol 指数
        x = np.arange(len(names))
        width = 0.38
        ax1.bar(x - width / 2, sobol["S1"], width, label="S1（一阶）", color="#2166AC")
        ax1.bar(x + width / 2, sobol["ST"], width, label="ST（总效应）", color="#D6604D")
        ax1.set_xticks(x)
        ax1.set_xticklabels(names)
        ax1.set_ylabel("灵敏度指数")
        ax1.set_title("Sobol 全局灵敏度")
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # 右：假设影响占比
        a_names = [d["name"] for d in report["details"]]
        a_vals = [d["impact_pct"] for d in report["details"]]
        colors = ["#D6604D" if d["grade"] in ("致命", "显著") else "#92C5DE"
                  for d in report["details"]]
        ax2.barh(a_names[::-1], a_vals[::-1], color=colors[::-1])
        ax2.set_xlabel("影响占比 (%)")
        ax2.set_title("假设放松对结论的影响")
        ax2.grid(axis="x", alpha=0.3)

        out_dir = Path(__file__).resolve().parent / "output"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "04_sensitivity.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print()
        print(f"  灵敏度分析图已保存: {out_path}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print()
    print("提示：Sobol 需要 SALib 才启用增强实现，未安装时自动降级为纯 numpy；")
    print("     两条路径接口一致，但论文中应说明实际使用的实现。")


if __name__ == "__main__":
    main()
