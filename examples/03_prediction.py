"""示例 3：时序预测（D 题场景）

演示 TAM（Time series Additive Model）加法分解预测：
趋势 + 季节 + 残差，输出预测值及其置信区间，并给出成分分解图。

运行::

    python examples/03_prediction.py

输出:
    examples/output/03_forecast.png

说明:
    未安装 ``tam`` 库时会自动降级为「线性趋势 + 固定周期季节」的简化
    加法分解，并在日志中明确告知。此时论文中不得声称使用了 TAM 的
    物理约束或 PyTorch 后端。
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.prediction.tam import TAM_Forecast  # noqa: E402

HISTORY = 60   # 历史期数
STEPS = 12     # 预测步长


def make_series(n=HISTORY):
    """构造带趋势与年周期的合成序列（周期 12）。"""
    t = np.arange(n)
    y = 50.0 + 0.8 * t + 6.0 * np.sin(2 * np.pi * t / 12) + 2.0 * np.cos(2 * np.pi * t / 12)
    return pd.DataFrame({"t": t, "y": y})


def main():
    print("=" * 62)
    print("  时序预测 — TAM 加法分解模型")
    print("=" * 62)

    df = make_series()
    print(f"  历史期数: {len(df)}   预测步长: {STEPS}")
    print()

    tam = TAM_Forecast()
    tam.fit(df, time_col="t", value_col="y")

    info = tam.summary()
    print("  模型摘要")
    for key in ("algorithm", "train_size", "has_tam_lib", "components"):
        if key in info:
            print(f"    {key}: {info[key]}")
    if info.get("note"):
        print(f"    注: {info['note']}")

    # --- 预测 ---
    pred = tam.predict(steps=STEPS)
    forecast = np.asarray(pred["forecast"], dtype=float)
    ci_lower = np.asarray(pred.get("ci_lower", forecast), dtype=float)
    ci_upper = np.asarray(pred.get("ci_upper", forecast), dtype=float)

    print()
    print("  预测结果（含 95% 置信区间）")
    print(f"    {'期数':<8}{'预测值':>12}{'下界':>12}{'上界':>12}")
    print("    " + "-" * 44)
    for i in range(STEPS):
        period = len(df) + i
        print(f"    {period:<8}{forecast[i]:>12.3f}{ci_lower[i]:>12.3f}{ci_upper[i]:>12.3f}")

    # --- 可视化 ---
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), height_ratios=[2, 1])

        # 上：历史 + 预测 + 置信带
        t_hist = df["t"].to_numpy()
        t_pred = np.arange(len(df), len(df) + STEPS)

        ax1.plot(t_hist, df["y"], label="历史数据", color="#2166AC", linewidth=1.8)
        ax1.plot(t_pred, forecast, label="预测值", color="#D6604D", linewidth=2.2, linestyle="--")
        ax1.fill_between(t_pred, ci_lower, ci_upper, color="#D6604D", alpha=0.18,
                         label="95% 置信区间")
        ax1.axvline(len(df) - 0.5, color="gray", linestyle=":", linewidth=1.2)
        ax1.set_xlabel("期数")
        ax1.set_ylabel("观测值")
        ax1.set_title(f"TAM 预测结果（历史 {HISTORY} 期，预测 {STEPS} 期）")
        ax1.legend()
        ax1.grid(alpha=0.3)

        # 下：成分分解
        trend = np.asarray(pred.get("trend", np.zeros(STEPS)), dtype=float)
        seasonal = np.asarray(pred.get("seasonal", np.zeros(STEPS)), dtype=float)
        ax2.plot(t_pred, trend, label="趋势项", color="#4DAF4A", linewidth=1.8)
        ax2.plot(t_pred, seasonal, label="季节项", color="#984EA3", linewidth=1.8)
        ax2.set_xlabel("期数")
        ax2.set_ylabel("成分值")
        ax2.set_title("预测期成分分解")
        ax2.legend()
        ax2.grid(alpha=0.3)

        out_dir = Path(__file__).resolve().parent / "output"
        out_dir.mkdir(exist_ok=True)
        out_path = out_dir / "03_forecast.png"
        fig.tight_layout()
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        print()
        print(f"  预测图已保存: {out_path}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print()
    print("提示：把 df 换成你的实际数据（需包含时间列与数值列）即可。")


if __name__ == "__main__":
    main()
