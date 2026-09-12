"""
ARIMA: 差分整合移动平均自回归模型
=======================================
用于时间序列预测（D 数据题）。

特点：
- 纯 numpy + scipy 实现，无 statsmodels 依赖，开箱即用
- 条件最小二乘（CLS）估计 ARMA 参数
- 支持 AIC 网格自动定阶 + 近似置信区间

参数说明：
- series: 时间序列（一维 array）
- order: (p, d, q) = (自回归阶数, 差分阶数, 移动平均阶数)

用法：
    from arima import ARIMA_Forecast

    model = ARIMA_Forecast(series, order=(1, 1, 1))
    model.fit()
    pred = model.predict(steps=10)
    model.plot('arima_forecast.png')

依赖：
- numpy（必选）
- scipy.optimize.minimize（参数估计）
- matplotlib（绘图，仅 plot() 需要）
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple


class ARIMA_Forecast:
    """ARIMA(p, d, q) 时间序列预测模型"""

    def __init__(self, series, order: Tuple[int, int, int] = (1, 1, 1)):
        """
        初始化

        Args:
            series: 时间序列（一维 array）
            order: (p, d, q) 自回归阶数 / 差分阶数 / 移动平均阶数
        """
        self.series = np.asarray(series, dtype=float)
        if self.series.ndim != 1:
            raise ValueError("series 必须是一维时间序列")
        self.p, self.d, self.q = order
        self.fitted = False
        self.params = None       # [c, phi_1..phi_p, theta_1..theta_q]
        self.residuals = None
        self.aic = None

    def _difference(self, x: np.ndarray, d: int) -> np.ndarray:
        """d 阶差分"""
        for _ in range(d):
            x = np.diff(x)
        return x

    def _arma_residuals(self, y: np.ndarray, params: np.ndarray) -> np.ndarray:
        """计算条件残差 e_t（初值取 0）"""
        c = params[0]
        phi = params[1:1 + self.p]
        theta = params[1 + self.p:1 + self.p + self.q]
        n = len(y)
        e = np.zeros(n)
        for t in range(n):
            mu = c
            for i in range(self.p):
                if t - i - 1 >= 0:
                    mu += phi[i] * y[t - i - 1]
            for j in range(self.q):
                if t - j - 1 >= 0:
                    mu += theta[j] * e[t - j - 1]
            e[t] = y[t] - mu
        return e

    def _cls_objective(self, params: np.ndarray, y: np.ndarray) -> float:
        """条件最小二乘目标：残差平方和"""
        e = self._arma_residuals(y, params)
        return np.sum(e ** 2)

    def fit(self) -> "ARIMA_Forecast":
        """条件最小二乘估计参数，返回 self"""
        from scipy.optimize import minimize

        if self.p == 0 and self.q == 0:
            raise ValueError("p 和 q 不能同时为 0，请指定至少一个非零阶数")

        y = self._difference(self.series, self.d)
        if len(y) < self.p + self.q + 2:
            raise ValueError("样本量不足以估计该阶数的 ARIMA 模型")

        n_params = 1 + self.p + self.q
        init = np.zeros(n_params)
        init[0] = np.mean(y)

        # AR 初值：Yule-Walker 方程（提升收敛速度与稳定性）
        if self.p > 0:
            try:
                gamma = [np.dot(y[:-k], y[k:]) / len(y) for k in range(self.p + 1)]
                R = np.array([[gamma[abs(i - j)] for j in range(self.p)]
                              for i in range(self.p)])
                init[1:1 + self.p] = np.linalg.solve(R, gamma[1:])
            except Exception:
                init[1:1 + self.p] = 0.1 * np.ones(self.p)

        result = minimize(self._cls_objective, init, args=(y,), method='BFGS',
                          options={'maxiter': 2000})

        # BFGS 失败时用 Nelder-Mead 兜底（无梯度，对 ARMA 参数更鲁棒）
        if not result.success:
            result = minimize(self._cls_objective, result.x, args=(y,),
                              method='Nelder-Mead',
                              options={'maxiter': 10000, 'xatol': 1e-6, 'fatol': 1e-6})

        if not result.success:
            print(f"[WARN] 参数估计未完全收敛: {result.message}")

        self.params = result.x
        self.residuals = self._arma_residuals(y, self.params)

        # AIC（高斯似然近似）
        n = len(y)
        sigma2 = np.sum(self.residuals ** 2) / n
        ll = -0.5 * n * (np.log(2 * np.pi * sigma2) + 1)
        self.aic = 2 * n_params - 2 * ll
        self.fitted = True

        print(f"ARIMA{(self.p, self.d, self.q)} 拟合完成: AIC = {self.aic:.2f}")
        return self

    def _inverse_difference(self, preds_diff: np.ndarray) -> np.ndarray:
        """将差分域预测还原到原始尺度"""
        levels = []
        cur = self.series.copy()
        for _ in range(self.d):
            levels.append(cur[-1])
            cur = np.diff(cur)
        integrated = np.asarray(preds_diff, dtype=float)
        for lv in reversed(levels):
            integrated = np.cumsum(integrated) + lv
        return integrated

    def predict(self, steps: int) -> np.ndarray:
        """未来 steps 步预测（返回原始尺度）"""
        if not self.fitted:
            raise ValueError("请先调用 fit()")

        c = self.params[0]
        phi = self.params[1:1 + self.p]
        theta = self.params[1 + self.p:]

        y = self._difference(self.series, self.d)
        e = self.residuals

        preds_diff = []
        for s in range(steps):
            mu = c
            # AR 项：用最近的 y 与已预测的未来 y
            for i in range(self.p):
                offset = len(y) + s - i - 1
                if offset >= len(y):
                    mu += phi[i] * preds_diff[offset - len(y)]
                elif offset >= 0:
                    mu += phi[i] * y[offset]
            # MA 项：未来误差取 0（条件期望）
            for j in range(self.q):
                offset = len(e) + s - j - 1
                if 0 <= offset < len(e):
                    mu += theta[j] * e[offset]
            preds_diff.append(mu)

        return self._inverse_difference(np.array(preds_diff))

    def forecast(self, steps: int, alpha: float = 0.05):
        """预测 + 近似置信区间（正态近似，不随步长扩展）"""
        pred = self.predict(steps)
        sigma = np.std(self.residuals) if self.residuals is not None else 0.0
        z = 1.96  # 95% 近似
        return pred, pred - z * sigma, pred + z * sigma

    def plot(self, save_path: str = None, steps: int = 10):
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
        ax.set_title(f'ARIMA{(self.p, self.d, self.q)} 预测', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()

    @staticmethod
    def auto_order(series, max_p: int = 5, max_d: int = 2, max_q: int = 2):
        """AIC 网格自动定阶，返回 (p, d, q)"""
        best = None
        best_aic = np.inf
        for d in range(max_d + 1):
            for p in range(max_p + 1):
                for q in range(max_q + 1):
                    if p == 0 and q == 0:
                        continue
                    try:
                        m = ARIMA_Forecast(series, order=(p, d, q))
                        m.fit()
                        if m.aic < best_aic:
                            best_aic = m.aic
                            best = (p, d, q)
                    except Exception:
                        continue
        print(f"最优阶数 (p,d,q) = {best}, AIC = {best_aic:.2f}")
        return best


def demo():
    """示例：带趋势 + 周期 + 噪声的序列"""
    t = np.arange(100)
    np.random.seed(42)
    series = 0.5 * t + 10 * np.sin(t / 5.0) + np.random.normal(0, 1.5, 100)

    model = ARIMA_Forecast(series, order=(2, 1, 1))
    model.fit()
    pred, lo, hi = model.forecast(steps=20)

    print(f"\n未来 5 步预测: {pred[:5]}")
    print(f"95% 置信区间下界: {lo[:5]}")
    print(f"95% 置信区间上界: {hi[:5]}")

    model.plot('arima_forecast.png', steps=20)


if __name__ == '__main__':
    demo()
