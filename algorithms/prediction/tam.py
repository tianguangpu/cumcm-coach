"""
TAM (Time Series Additive Model) — D 数据型首选算法
来源: EDF-Lab/tam (法国电力, JOSS 论文)
特点: 可解释加法分解 + 物理约束先验(依赖 tam 包;未安装则降级为简化加法分解,论文需如实说明)

用法:
    from tam import TAM_Forecast
    model = TAM_Forecast(formula="y ~ trend(year) + seasonal(month, period=12)")
    model.fit(df)
    forecast = model.predict(steps=12)
"""

import warnings

import numpy as np
import pandas as pd

try:
    from tam import TAM
    HAS_TAM = True
except ImportError:
    HAS_TAM = False
    warnings.warn("tam 未安装, 回退到简化加法分解。安装: pip install tam")


class TAM_Forecast:
    """
    TAM 时序预测封装。

    Parameters
    ----------
    formula : str
        R-style 公式, 如 "y ~ trend(year) + seasonal(month, period=12)"
    n_changepoints : int
        趋势变点数量, 默认 10
    seasonality_mode : str
        季节性模式: 'additive' (默认) 或 'multiplicative'
    """

    def __init__(self, formula=None, n_changepoints=10, seasonality_mode="additive"):
        self.formula = formula
        self.n_changepoints = n_changepoints
        self.seasonality_mode = seasonality_mode
        self.model = None
        self.fitted = False
        self.components = {}
        self.using_tam = HAS_TAM  # True=完整 TAM, False=简化降级

    def fit(self, df, time_col=None, value_col=None):
        """
        拟合模型。

        Parameters
        ----------
        df : pd.DataFrame
            包含时间列和目标列的数据
        time_col : str, optional
            时间列名(自动检测)
        value_col : str, optional
            目标列名(自动检测)
        """
        if time_col is None:
            time_col = df.columns[0]
        if value_col is None:
            value_col = df.columns[1]

        self.time_col = time_col
        self.value_col = value_col
        self.train_data = df.copy()

        if HAS_TAM and self.formula:
            self._fit_tam(df)
        else:
            self._fit_simple(df, time_col, value_col)

        self.fitted = True
        return self

    def _fit_tam(self, df):
        """使用 TAM 库拟合"""
        self.model = TAM(formula=self.formula)
        self.model.fit(df)
        self.components = {
            "trend": self.model.trend_,
            "seasonal": self.model.seasonal_,
            "residual": self.model.residual_
        }

    def _fit_simple(self, df, time_col, value_col):
        """简化加法分解(TAM 不可用时的回退方案)"""
        warnings.warn(
            "TAM 未安装, 本模型降级为简化加法分解(线性趋势+固定周期季节), "
            "论文中不得声称使用了 TAM 的物理约束/PyTorch 后端。安装完整版: pip install tam",
            RuntimeWarning,
        )
        y = df[value_col].values
        n = len(y)

        # 趋势: 线性拟合 + 平滑
        x = np.arange(n)
        trend_coef = np.polyfit(x, y, 1)
        trend = np.polyval(trend_coef, x)

        # 季节性: STL 简化版(假设周期=12)
        detrended = y - trend
        period = min(12, n // 2)
        if period >= 2:
            seasonal = np.zeros(n)
            for i in range(period):
                idx = slice(i, n, period)
                seasonal[idx] = np.mean(detrended[idx])
            seasonal -= seasonal.mean()
        else:
            seasonal = np.zeros(n)

        residual = y - trend - seasonal

        self.components = {
            "trend": trend,
            "seasonal": seasonal,
            "residual": residual
        }
        self.trend_coef = trend_coef
        self.period = period
        self.n_train = n

    def predict(self, steps=12, include_components=True):
        """
        预测未来 steps 步。

        Parameters
        ----------
        steps : int
            预测步数
        include_components : bool
            是否返回分量分解

        Returns
        -------
        dict: {"forecast": array, "trend": array, "seasonal": array, "ci_lower": array, "ci_upper": array}
        """
        if not self.fitted:
            raise RuntimeError("请先调用 fit()")

        if HAS_TAM and self.model is not None:
            return self._predict_tam(steps, include_components)
        else:
            return self._predict_simple(steps, include_components)

    def _predict_tam(self, steps, include_components):
        """TAM 库预测"""
        forecast_df = self.model.predict(steps=steps)
        result = {"forecast": forecast_df["yhat"].values}

        if include_components:
            result["trend"] = forecast_df.get("trend", None)
            result["seasonal"] = forecast_df.get("seasonal", None)

        # 置信区间
        if "yhat_lower" in forecast_df:
            result["ci_lower"] = forecast_df["yhat_lower"].values
            result["ci_upper"] = forecast_df["yhat_upper"].values
        else:
            residual_std = np.std(self.components["residual"])
            result["ci_lower"] = result["forecast"] - 1.96 * residual_std
            result["ci_upper"] = result["forecast"] + 1.96 * residual_std

        return result

    def _predict_simple(self, steps, include_components):
        """简化预测"""
        n = self.n_train
        x_future = np.arange(n, n + steps)

        # 趋势外推
        trend_future = np.polyval(self.trend_coef, x_future)

        # 季节性循环
        if self.period >= 2:
            seasonal_pattern = self.components["seasonal"][:self.period]
            seasonal_future = np.array([seasonal_pattern[i % self.period] for i in range(steps)])
        else:
            seasonal_future = np.zeros(steps)

        forecast = trend_future + seasonal_future

        # 95% 置信区间
        residual_std = np.std(self.components["residual"])
        ci_lower = forecast - 1.96 * residual_std
        ci_upper = forecast + 1.96 * residual_std

        result = {
            "forecast": forecast,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        }

        if include_components:
            result["trend"] = trend_future
            result["seasonal"] = seasonal_future

        return result

    def summary(self):
        """输出模型摘要"""
        if not self.fitted:
            return "模型未拟合"

        info = {
            "algorithm": "TAM (Time Series Additive Model)",
            "train_size": self.n_train if hasattr(self, "n_train") else len(self.train_data),
            "has_tam_lib": HAS_TAM,
            "components": list(self.components.keys()),
        }

        if not HAS_TAM:
            info["note"] = "使用简化加法分解(安装 tam 库可获得完整功能)"

        return info

    def get_decomposition(self):
        """返回分解结果 DataFrame"""
        if not self.fitted:
            raise RuntimeError("请先调用 fit()")

        df = self.train_data.copy()
        df["trend"] = self.components["trend"]
        df["seasonal"] = self.components["seasonal"]
        df["residual"] = self.components["residual"]
        return df


if __name__ == "__main__":
    # 示例: 简单时序预测
    np.random.seed(42)
    n = 120
    t = np.arange(n)
    trend = 0.5 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 2, n)
    y = 50 + trend + seasonal + noise

    df = pd.DataFrame({"month": t, "value": y})

    model = TAM_Forecast()
    model.fit(df)
    result = model.predict(steps=24)

    print("=== TAM 预测结果 ===")
    print(f"未来 24 步预测: {result['forecast'][:6].round(2)} ...")
    print(f"95% CI 宽度: {(result['ci_upper'] - result['ci_lower']).mean():.2f}")
    print(f"模型摘要: {model.summary()}")
