"""示例 8：D 题时序预测 —— TAM（趋势 + 季节分解）

D 题（数据类）常要求时序预测。本示例用 TAM_Forecast 对一段
「趋势 + 季节 + 噪声」合成序列做分解与预测。

注：完整 TAM 需 `pip install tam`；未装时自动降级为简化加法分解，
本示例无需额外依赖即可运行。

运行::

    python examples/08_tam_forecast.py

输出:
    examples/output/08_tam_forecast.png
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.prediction.tam import TAM_Forecast  # noqa: E402


def make_series(n=120):
    """合成月度序列：线性趋势 + 年季节（12 个月）+ 噪声。"""
    t = np.arange(n)
    trend = 0.5 * t
    season = 15 * np.sin(2 * np.pi * t / 12)
    noise = np.random.default_rng(42).normal(0, 2, n)
    y = 100 + trend + season + noise
    dates = pd.date_range("2020-01-01", periods=n, freq="ME")
    return pd.DataFrame({"date": dates, "value": y})


def main():
    print("=" * 60)
    print("  D 题时序预测：TAM 趋势 + 季节分解")
    print("=" * 60)

    df = make_series(n=120)
    train, test = df.iloc[:-12], df.iloc[-12:]

    model = TAM_Forecast()
    model.fit(train, time_col="date", value_col="value")
    pred = model.predict(steps=12, include_components=True)

    y_pred = pred["forecast"] if isinstance(pred, dict) else pred
    if isinstance(y_pred, pd.Series):
        y_pred = y_pred.values
    actual = test["value"].values
    mae = float(np.mean(np.abs(actual - np.asarray(y_pred).ravel())))
    print(f"  训练 {len(train)} 点，预测 {len(test)} 点")
    print(f"  预测 MAE: {mae:.2f}")
    if isinstance(pred, dict):
        print(f"  返回字段: {list(pred.keys())}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(train["date"], train["value"], label="历史", color="#2166AC")
        ax.plot(test["date"], test["value"], label="真实", color="#4DAF4A")
        ax.plot(test["date"], np.asarray(y_pred).ravel(), label="预测",
                color="#D6604D", linestyle="--")
        ax.set_xlabel("日期")
        ax.set_ylabel("值")
        ax.set_title("TAM 时序预测（趋势 + 季节 + 噪声）")
        ax.legend()
        ax.grid(alpha=0.3)

        out = Path(__file__).resolve().parent / "output" / "08_tam_forecast.png"
        out.parent.mkdir(exist_ok=True)
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"\n  预测图已保存: {out}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print("\n提示：把 make_series 换成你的真实数据（date/value 两列），")
    print("      即可做时序分解与预测。ARIMA/MLP/GM(1,1) 见同目录 03_prediction.py。")


if __name__ == "__main__":
    main()
