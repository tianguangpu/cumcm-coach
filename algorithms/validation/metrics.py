"""
Metrics: 拟合精度指标 + 残差分析
=======================================
用于四重检验 §6.1 拟合精度: R²/MAE/RMSE/MAPE + 残差正态性。

特点：
- 指标计算纯 numpy，无依赖
- 残差正态性检验优先 scipy(shapiro)，降级到偏度/峰度
- 残差直方图 + Q-Q 图

参数说明：
- y_true: 真实值（一维 array）
- y_pred: 预测值（一维 array）

用法：
    from metrics import FitMetrics
    m = FitMetrics.evaluate(y_true, y_pred)   # {'R2':.., 'MAE':.., 'RMSE':.., 'MAPE':..}
    FitMetrics.plot_residuals(y_true - y_pred, 'residuals.png')
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional


class FitMetrics:
    """拟合精度指标与残差分析"""

    @staticmethod
    def r2(y_true, y_pred) -> float:
        """决定系数 R²"""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1.0 - ss_res / ss_tot if ss_tot > 1e-15 else 0.0

    @staticmethod
    def mae(y_true, y_pred) -> float:
        """平均绝对误差"""
        return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))

    @staticmethod
    def rmse(y_true, y_pred) -> float:
        """均方根误差"""
        return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))

    @staticmethod
    def mape(y_true, y_pred) -> float:
        """平均绝对百分比误差(%)，规避除零"""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        mask = np.abs(y_true) > 1e-10
        if not np.any(mask):
            return float('nan')
        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    @staticmethod
    def evaluate(y_true, y_pred) -> dict:
        """一次性返回全部精度指标"""
        y_true = np.asarray(y_true, dtype=float)
        y_pred = np.asarray(y_pred, dtype=float)
        return {
            'R2': FitMetrics.r2(y_true, y_pred),
            'MAE': FitMetrics.mae(y_true, y_pred),
            'RMSE': FitMetrics.rmse(y_true, y_pred),
            'MAPE': FitMetrics.mape(y_true, y_pred),
        }

    @staticmethod
    def residual_normality(residuals):
        """残差正态性检验，返回 (统计量, p值)；scipy 不可用时降级为 (偏度, 峰度)"""
        residuals = np.asarray(residuals, dtype=float)
        try:
            from scipy.stats import shapiro
            W, p = shapiro(residuals)
            return W, p
        except Exception:
            m = np.mean(residuals)
            s = np.std(residuals, ddof=1)
            if s < 1e-15:
                return 0.0, 0.0
            skew = float(np.mean(((residuals - m) / s) ** 3))
            kurt = float(np.mean(((residuals - m) / s) ** 4))
            return skew, kurt

    @staticmethod
    def plot_residuals(residuals, save_path: str = None):
        """残差直方图 + Q-Q 图"""
        residuals = np.asarray(residuals, dtype=float)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.hist(residuals, bins=30, edgecolor='k', alpha=0.7, color='#2166AC')
        ax1.axvline(0, color='r', linestyle='--', linewidth=1.5)
        ax1.set_xlabel('残差', fontsize=12)
        ax1.set_ylabel('频数', fontsize=12)
        ax1.set_title('残差直方图', fontsize=14)
        ax1.grid(True, alpha=0.3)

        try:
            from scipy import stats
            stats.probplot(residuals, dist="norm", plot=ax2)
            ax2.set_title('残差 Q-Q 图', fontsize=14)
        except Exception:
            n = len(residuals)
            sorted_res = np.sort(residuals)
            theo = np.array([FitMetrics._normal_quantile((i + 0.5) / n) for i in range(n)])
            ax2.scatter(theo, sorted_res, s=12, alpha=0.7)
            ax2.set_xlabel('理论分位', fontsize=12)
            ax2.set_ylabel('样本分位', fontsize=12)
            ax2.set_title('残差 Q-Q 图(近似)', fontsize=14)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()

    @staticmethod
    def _normal_quantile(p: float) -> float:
        """标准正态分位数的近似(Abramowitz-Stegun 公式)"""
        if p <= 0 or p >= 1:
            return float('nan')
        z = np.sqrt(-2.0 * np.log(1.0 - p if p > 0.5 else p))
        sign = 1.0 if p > 0.5 else -1.0
        q = z - 2.30753 + 0.27061 * z
        q = q / (1.0 + 0.99229 * z + 0.04481 * z * z)
        return sign * q


def demo():
    """示例：合成正弦数据拟合"""
    np.random.seed(42)
    t = np.linspace(0, 10, 100)
    y_true = 2.0 * np.sin(t) + 1.0
    y_pred = y_true + np.random.normal(0, 0.3, 100)

    m = FitMetrics.evaluate(y_true, y_pred)
    print("拟合精度指标:")
    for k, v in m.items():
        print(f"  {k}: {v:.4f}")

    residuals = y_true - y_pred
    W, p = FitMetrics.residual_normality(residuals)
    print(f"残差正态性: 统计量={W:.4f}, p={p:.4f}")

    FitMetrics.plot_residuals(residuals, 'residuals.png')


if __name__ == '__main__':
    demo()
