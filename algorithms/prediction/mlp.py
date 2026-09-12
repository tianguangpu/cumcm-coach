"""
MLP: 多层感知机序列预测
=======================================
用于时间序列预测(D 数据题),作为 ARIMA 的机器学习对照算法。

特点：
- 滑动窗口 + sklearn MLPRegressor,无 torch 依赖,开箱即用
- 迭代式多步预测
- 与 arima.py 形成"统计 vs 机器学习"对比

参数说明：
- series: 时间序列(一维 array)
- window: 滑动窗口长度(用前 window 个点预测下一点,推荐 5-15)
- hidden_layer_sizes: 隐层结构,默认 (50,)
- max_iter: 最大迭代次数,默认 1000
- random_state: 随机种子,默认 42

用法：
    from mlp import MLP_Forecast
    model = MLP_Forecast(series, window=5)
    model.fit()
    pred = model.predict(steps=10)
    model.plot('mlp_forecast.png')

依赖：
- numpy（必选）
- scikit-learn（MLPRegressor）
- matplotlib（绘图，仅 plot() 需要）
"""

from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


class MLP_Forecast:
    """多层感知机序列预测(滑动窗口)"""

    def __init__(
        self,
        series,
        window: int = 5,
        hidden_layer_sizes: Tuple[int, ...] = (50,),
        max_iter: int = 1000,
        random_state: int = 42
    ):
        """
        初始化

        Args:
            series: 时间序列（一维 array）
            window: 滑动窗口长度
            hidden_layer_sizes: 隐层结构
            max_iter: 最大迭代次数
            random_state: 随机种子
        """
        self.series = np.asarray(series, dtype=float)
        if self.series.ndim != 1:
            raise ValueError("series 必须是一维时间序列")
        self.window = window
        self.hidden_layer_sizes = hidden_layer_sizes
        self.max_iter = max_iter
        self.random_state = random_state
        self.model = None
        self.fitted = False
        self.train_loss = None
        self.train_r2 = None

    def _make_samples(self, x):
        """滑动窗口构造 (X, y)"""
        X, y = [], []
        for i in range(len(x) - self.window):
            X.append(x[i:i + self.window])
            y.append(x[i + self.window])
        return np.array(X), np.array(y)

    def fit(self) -> "MLP_Forecast":
        """训练 MLP，返回 self"""
        from sklearn.neural_network import MLPRegressor

        X, y = self._make_samples(self.series)
        if len(X) < 5:
            raise ValueError("样本量不足以训练(window 过大或序列太短)")

        self.model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        self.model.fit(X, y)

        self.train_loss = self.model.loss_
        pred_train = self.model.predict(X)
        ss_res = np.sum((y - pred_train) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        self.train_r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 0.0
        self.fitted = True

        print(f"MLP 训练完成: loss={self.train_loss:.6f}, 训练R2={self.train_r2:.4f}")
        return self

    def predict(self, steps: int) -> np.ndarray:
        """迭代式多步预测"""
        if not self.fitted:
            raise ValueError("请先调用 fit()")

        preds = []
        cur = self.series[-self.window:].copy()
        for _ in range(steps):
            nxt = self.model.predict(cur.reshape(1, -1))[0]
            preds.append(nxt)
            cur = np.roll(cur, -1)
            cur[-1] = nxt
        return np.array(preds)

    def plot(self, save_path: Optional[str] = None, steps: int = 10):
        """绘制真实序列与预测序列"""
        pred = self.predict(steps)
        n = len(self.series)
        x_hist = np.arange(n)
        x_pred = np.arange(n, n + steps)

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(x_hist, self.series, 'b-', linewidth=2, label='真实序列')
        ax.plot(x_pred, pred, 'r--o', linewidth=2, markersize=4, label='预测序列')
        ax.plot([n - 1, n], [self.series[-1], pred[0]], 'r--', linewidth=1.5)

        ax.set_xlabel('时间', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.set_title(f'MLP 预测(window={self.window})', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()


def demo():
    """示例：带趋势 + 周期 + 噪声的序列"""
    t = np.arange(100)
    np.random.seed(42)
    series = 0.5 * t + 10 * np.sin(t / 5.0) + np.random.normal(0, 1.5, 100)

    model = MLP_Forecast(series, window=5, hidden_layer_sizes=(50,))
    model.fit()
    pred = model.predict(steps=20)

    print(f"\n未来 5 步预测: {pred[:5]}")

    model.plot('mlp_forecast.png', steps=20)


if __name__ == '__main__':
    demo()
