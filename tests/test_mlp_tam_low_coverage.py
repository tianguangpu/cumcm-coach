"""MLP / TAM 预测模块覆盖测试。"""
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from algorithms.prediction.mlp import MLP_Forecast
from algorithms.prediction.tam import TAM_Forecast, HAS_TAM


# ============= MLP =============

class TestMLPInit:
    def test_init_basic(self):
        series = np.arange(20, dtype=float)
        m = MLP_Forecast(series, window=5)
        assert m.window == 5
        assert m.fitted is False

    def test_init_2d_raises(self):
        with pytest.raises(ValueError, match="一维"):
            MLP_Forecast(np.zeros((5, 2)), window=2)


class TestMLPFit:
    def test_fit_with_sklearn(self):
        np.random.seed(42)
        t = np.arange(30)
        series = 0.5 * t + np.random.normal(0, 1, 30)
        m = MLP_Forecast(series, window=5, max_iter=200)
        m.fit()
        assert m.fitted is True
        assert m.model is not None
        assert m.train_loss is not None
        assert m.train_r2 is not None

    def test_fit_insufficient_samples(self):
        # window 太大导致样本不足
        m = MLP_Forecast(np.arange(6, dtype=float), window=5)
        with pytest.raises(ValueError, match="样本量不足"):
            m.fit()

    def test_fit_linear_fallback(self, monkeypatch):
        # 模拟 sklearn 未安装
        import sys
        sklearn_backup = sys.modules.get("sklearn")
        sklearn_nn_backup = sys.modules.get("sklearn.neural_network")
        # 强制 import 失败
        import builtins
        orig_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name.startswith("sklearn"):
                raise ImportError("simulated")
            return orig_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        # 重新 import 模块,触发 except 分支
        # 注: MLP_Forecast 已经 import 过,实际触发降级路径需要重新加载
        # 改为直接调用 _fit_linear 测分支
        m = MLP_Forecast(np.arange(20, dtype=float), window=5)
        X = np.array([[i, i+1, i+2, i+3, i+4] for i in range(15)])
        y = np.arange(5, 20, dtype=float)
        m._fit_linear(X, y)
        assert m.train_r2 is not None
        assert hasattr(m, "_w")
        assert hasattr(m, "_linear")


class TestMLPPredict:
    def test_predict_before_fit_raises(self):
        m = MLP_Forecast(np.arange(20, dtype=float), window=5)
        with pytest.raises(ValueError, match="请先调用 fit"):
            m.predict(steps=3)

    def test_predict_sklearn_path(self):
        np.random.seed(42)
        t = np.arange(30)
        series = 0.5 * t + np.random.normal(0, 1, 30)
        m = MLP_Forecast(series, window=5, max_iter=200)
        m.fit()
        pred = m.predict(steps=5)
        assert pred.shape == (5,)
        assert np.isfinite(pred).all()

    def test_predict_linear_path(self):
        # 直接走 _fit_linear -> predict 的 linear 分支
        m = MLP_Forecast(np.arange(20, dtype=float), window=5)
        X = np.array([[i, i+1, i+2, i+3, i+4] for i in range(15)])
        y = np.arange(5, 20, dtype=float)
        m._fit_linear(X, y)
        m.fitted = True  # 强制绕过
        m.series = np.arange(20, dtype=float)  # 用于取 window 末尾
        pred = m.predict(steps=3)
        assert pred.shape == (3,)


class TestMLPPlot:
    def test_plot_save(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        np.random.seed(42)
        t = np.arange(30)
        series = 0.5 * t + np.random.normal(0, 1, 30)
        m = MLP_Forecast(series, window=5, max_iter=100)
        m.fit()
        save = str(tmp_path / "mlp_test.png")
        m.plot(save_path=save, steps=3)
        assert os.path.exists(save)


# ============= TAM =============

class TestTAMInit:
    def test_init_default(self):
        m = TAM_Forecast()
        assert m.fitted is False
        assert m.using_tam == HAS_TAM
        assert m.n_changepoints == 10


class TestTAMFit:
    def test_fit_simple(self):
        # HAS_TAM 在导入时确定;若 False 走简化路径
        n = 60
        t = np.arange(n)
        y = 50 + 0.5 * t + 10 * np.sin(2 * np.pi * t / 12) + np.random.normal(0, 1, n)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        assert m.fitted is True
        assert "trend" in m.components
        assert "seasonal" in m.components
        assert "residual" in m.components

    def test_fit_explicit_cols(self):
        n = 30
        t = np.arange(n)
        y = 10 + 0.3 * t + np.random.normal(0, 1, n)
        df = pd.DataFrame({"date": t, "val": y})
        m = TAM_Forecast()
        m.fit(df, time_col="date", value_col="val")
        assert m.time_col == "date"
        assert m.value_col == "val"
        assert m.fitted is True

    def test_fit_short_series(self):
        # 短序列触发 period<2 分支
        n = 3
        t = np.arange(n)
        y = np.array([1.0, 2.0, 3.0])
        df = pd.DataFrame({"date": t, "val": y})
        m = TAM_Forecast()
        m.fit(df)
        # period = min(12, n//2) = 1 -> seasonal = zeros
        assert m.period == 1
        assert np.all(m.components["seasonal"] == 0)


class TestTAMPredict:
    def test_predict_before_fit_raises(self):
        m = TAM_Forecast()
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            m.predict(steps=3)

    def test_predict_simple(self):
        n = 36
        t = np.arange(n)
        y = 50 + 0.5 * t + 10 * np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        r = m.predict(steps=6)
        assert "forecast" in r
        assert "ci_lower" in r
        assert "ci_upper" in r
        assert len(r["forecast"]) == 6

    def test_predict_with_components(self):
        n = 36
        t = np.arange(n)
        y = 50 + 0.5 * t + 10 * np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        r = m.predict(steps=3, include_components=True)
        assert "trend" in r
        assert "seasonal" in r

    def test_predict_without_components(self):
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        r = m.predict(steps=3, include_components=False)
        assert "trend" not in r
        assert "forecast" in r


class TestTAMSummary:
    def test_summary_before_fit(self):
        m = TAM_Forecast()
        s = m.summary()
        assert s == "模型未拟合"

    def test_summary_after_fit(self):
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        info = m.summary()
        assert info["algorithm"] == "TAM (Time Series Additive Model)"
        assert "train_size" in info
        assert "components" in info


class TestTAMDecomposition:
    def test_get_decomposition_before_fit_raises(self):
        m = TAM_Forecast()
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            m.get_decomposition()

    def test_get_decomposition_after_fit(self):
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m = TAM_Forecast()
        m.fit(df)
        df_decomp = m.get_decomposition()
        assert "trend" in df_decomp.columns
        assert "seasonal" in df_decomp.columns
        assert "residual" in df_decomp.columns
        assert len(df_decomp) == n
