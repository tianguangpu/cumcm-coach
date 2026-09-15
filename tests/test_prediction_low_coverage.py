"""algorithms/prediction/ 低覆盖模块补测 —— gm11/arima/mlp/tam。"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.prediction.gm11 import GM11
from algorithms.prediction.arima import ARIMA_Forecast


# ============================================================
# GM11 (gm11.py) —— 覆盖 68% → 目标 90%+
# ============================================================

class TestGM11:
    def test_basic_fit_predict(self):
        x = [100, 120, 150, 180, 220]
        fit, pred, info = GM11(x, predict_steps=2)
        assert len(fit) == 5
        assert len(pred) == 2
        assert all(p > 0 for p in pred)

    def test_info_keys(self):
        x = [10, 12, 15, 18]
        _, _, info = GM11(x, predict_steps=1)
        assert {"a", "b", "C", "P", "grade"} <= set(info.keys())
        assert info["grade"] in ("优", "合格", "勉强", "不合格")

    def test_exponential_growth(self):
        t = np.arange(1, 8)
        x = 100 * np.exp(0.3 * (t - 1))
        fit, pred, info = GM11(x, predict_steps=3)
        # 指数增长拟合应该较好
        assert info["C"] < 0.5
        assert len(pred) == 3

    def test_negative_raises(self):
        with pytest.raises(AssertionError, match="全部为正"):
            GM11([1, -2, 3])

    def test_smooth(self):
        x = [10, 15, 12, 18, 14, 20, 16]
        fit, pred, _ = GM11(x, predict_steps=1, smooth=3)
        assert len(fit) == len(x) - 2  # smooth=3 减少 2 个点

    def test_predict_steps(self):
        x = [100, 110, 121, 133]
        _, pred, _ = GM11(x, predict_steps=5)
        assert len(pred) == 5

    def test_grade_levels(self):
        # 高质量数据
        x = np.array([100, 110, 121, 133.1, 146.41])
        _, _, info = GM11(x, predict_steps=1)
        assert info["grade"] in ("优", "合格", "勉强")


# ============================================================
# ARIMA_Forecast (arima.py) —— 覆盖 66% → 目标 85%+
# ============================================================

class TestARIMA:
    @pytest.fixture
    def ts(self):
        rng = np.random.default_rng(42)
        t = np.arange(50)
        return 10 + 0.5 * t + rng.normal(0, 1, 50)

    def test_init(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 1))
        assert m.p == 1 and m.d == 1 and m.q == 1
        assert not m.fitted

    def test_init_2d_raises(self):
        with pytest.raises(ValueError, match="一维"):
            ARIMA_Forecast(np.zeros((5, 2)), order=(1, 0, 0))

    def test_difference(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        d = m._difference(np.array([1, 3, 6, 10]), 1)
        assert np.allclose(d, [2, 3, 4])

    def test_difference_d2(self):
        m = ARIMA_Forecast([1, 2, 4, 7], order=(1, 2, 0))
        d = m._difference(np.array([1, 3, 6, 10]), 2)
        assert len(d) == 2

    def test_fit(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        m.fit()
        assert m.fitted
        assert m.params is not None
        assert m.aic is not None

    def test_fit_ar_only(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 0, 0))
        m.fit()
        assert m.fitted

    def test_fit_ma_only(self, ts):
        m = ARIMA_Forecast(ts, order=(0, 0, 1))
        m.fit()
        assert m.fitted

    def test_fit_pq_zero_raises(self, ts):
        m = ARIMA_Forecast(ts, order=(0, 0, 0))
        with pytest.raises(ValueError, match="不能同时为 0"):
            m.fit()

    def test_fit_insufficient_data(self):
        m = ARIMA_Forecast([1, 2], order=(2, 0, 2))
        with pytest.raises(ValueError, match="样本量不足"):
            m.fit()

    def test_predict_not_fitted_raises(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        with pytest.raises(ValueError, match="请先调用 fit"):
            m.predict(steps=3)

    def test_predict(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        m.fit()
        pred = m.predict(steps=5)
        assert len(pred) == 5
        assert all(np.isfinite(pred))

    def test_predict_d0(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 0, 0))
        m.fit()
        pred = m.predict(steps=3)
        assert len(pred) == 3

    def test_arma_residuals(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 0, 1))
        y = m._difference(ts, 0)
        e = m._arma_residuals(y, np.array([0.0, 0.5, 0.3]))
        assert len(e) == len(y)

    def test_cls_objective(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 0, 0))
        y = m._difference(ts, 0)
        obj = m._cls_objective(np.array([0.0, 0.5]), y)
        assert obj > 0

    def test_inverse_difference(self, ts):
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        preds_diff = np.array([1.0, 2.0, 3.0])
        orig = m._inverse_difference(preds_diff)
        assert len(orig) == 3

    def test_plot(self, ts, monkeypatch):
        import matplotlib.pyplot as plt
        monkeypatch.setattr(plt, "show", lambda *a, **k: None)
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        m.fit()
        m.plot()
        plt.close("all")

    def test_plot_save(self, ts, tmp_path, monkeypatch):
        import matplotlib.pyplot as plt
        monkeypatch.setattr(plt, "show", lambda *a, **k: None)
        m = ARIMA_Forecast(ts, order=(1, 1, 0))
        m.fit()
        p = tmp_path / "arima.png"
        m.plot(str(p))
        assert p.exists()
        plt.close("all")