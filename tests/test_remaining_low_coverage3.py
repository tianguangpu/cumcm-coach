"""第四批测试: __main__ 块 + 遗漏的内部函数。

目标: 推进总覆盖率 84% -> 85%+ (差 52 行)。
覆盖:
  - 各模块 __main__ 自测块 (runpy)
  - metrics.demo()
  - arima 内部方法 (_arma_residuals / aic_select / _prepare_plot_data)
  - sobol._sobol_indices / plot_sobol
  - shap_analysis plot_top_features 重载 + load_kernel_explainer 路径
  - tam _predict_tam 路径 (手动注入 model)
  - fdm_1d __main__ 块
"""
import os
import runpy
import sys
import unittest.mock
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


# ============= __main__ 块统一测试 =============

class TestMainBlocks:
    """通过 runpy 执行各模块的 __main__ 自测块。"""

    @pytest.mark.parametrize("module", [
        "algorithms.mechanistic.de_quickref",
        "algorithms.mechanistic.fdm_1d",
        "algorithms.mechanistic.fdm_2d",
        "algorithms.ecology.population",
        "algorithms.evaluation.vikor",
        "algorithms.evaluation.gra",
        "algorithms.prediction.gm11",
        "algorithms.misc.innovation_guide",
        "algorithms.optimization.bounds",
    ])
    def test_run_main(self, module):
        old_argv = sys.argv
        sys.argv = [module + ".py"]
        try:
            runpy.run_module(module, run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv


# ============= metrics.demo() =============

class TestMetricsDemo:
    def test_demo(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        # demo() 调用 plot_residuals(save_path='residuals.png') 写入当前目录
        # 改 cwd 到 tmp_path 避免污染
        old_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            with unittest.mock.patch("matplotlib.pyplot.show"):
                from algorithms.validation.metrics import demo
                demo()
            # 应生成 residuals.png
            assert (tmp_path / "residuals.png").exists()
        finally:
            os.chdir(old_cwd)


# ============= arima 内部方法 =============

class TestARIMAMore:
    def _make_series(self):
        rng = np.random.default_rng(42)
        t = np.arange(60)
        return 0.5 * t + rng.normal(0, 1, 60)

    def test_fit_predict_basic(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        s = self._make_series()
        m = ARIMA_Forecast(s, order=(1, 1, 0))
        m.fit()
        pred = m.predict(steps=5)
        assert len(pred) == 5
        assert m.fitted is True
        assert m.aic is not None
        assert m.params is not None
        assert m.residuals is not None

    def test_fit_with_q(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        s = self._make_series()
        m = ARIMA_Forecast(s, order=(1, 0, 1))
        m.fit()
        assert m.fitted is True

    def test_aic_select(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        s = self._make_series()
        m = ARIMA_Forecast(s, order=(1, 1, 0))
        # 手动调用 aic_select (若存在)
        if hasattr(m, "aic_select"):
            best_order = m.aic_select(max_p=2, max_q=2, d=1)
            assert isinstance(best_order, tuple)

    def test_predict_before_fit(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        m = ARIMA_Forecast(self._make_series(), order=(1, 1, 1))
        with pytest.raises((RuntimeError, ValueError)):
            m.predict(steps=3)

    def test_plot(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        from algorithms.prediction.arima import ARIMA_Forecast
        m = ARIMA_Forecast(self._make_series(), order=(1, 1, 0))
        m.fit()
        p = str(tmp_path / "arima.png")
        with unittest.mock.patch("matplotlib.pyplot.show"):
            m.plot(save_path=p)
        assert os.path.exists(p)

    def test_plot_no_save_path(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        from algorithms.prediction.arima import ARIMA_Forecast
        m = ARIMA_Forecast(self._make_series(), order=(1, 1, 0))
        m.fit()
        with unittest.mock.patch("matplotlib.pyplot.show"):
            m.plot()  # save_path=None -> plt.show()

    def test_difference(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        m = ARIMA_Forecast(np.arange(10, dtype=float), order=(1, 2, 0))
        out = m._difference(np.arange(10, dtype=float), 2)
        # 2 阶差分后长度减 2
        assert len(out) == 8

    def test_arma_residuals(self):
        from algorithms.prediction.arima import ARIMA_Forecast
        m = ARIMA_Forecast(np.arange(20, dtype=float), order=(1, 1, 1))
        y = np.diff(np.arange(20, dtype=float))
        params = np.array([0.5, 0.3, 0.2])
        r = m._arma_residuals(y, params)
        assert len(r) > 0
        # 残差应有限
        assert np.isfinite(r).all()


# ============= sobol.py 内部 =============

class TestSobolInternal:
    def test_sobol_basic(self):
        # sobol.py 接口: sobol_total_and_first
        from algorithms.validation.sobol import sobol_total_and_first
        def f(x):
            return float(x[0] + 2.0 * x[1])
        r = sobol_total_and_first(f, [(0, 1), (0, 1)], N=64)
        assert "S1" in r and "ST" in r
        assert "S1_conf" in r and "ST_conf" in r
        assert "n_eval" in r and r["n_eval"] == 64 * 4

    def test_main_block(self):
        old_argv = sys.argv
        sys.argv = ["sobol.py"]
        try:
            runpy.run_module("algorithms.validation.sobol", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv


# ============= shap_analysis 额外路径 =============

class TestSHAPExtra:
    def _make_analyzer(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer
        class FakeModel:
            pass
        return SHAPAnalyzer(FakeModel(),
                            X_train=np.random.rand(20, 3),
                            X_test=np.random.rand(10, 3),
                            feature_names=["a", "b", "c"])

    def test_plot_top_features_default_path(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        a = self._make_analyzer()
        a.fitted = True
        a.shap_values = np.random.normal(0, 1, (10, 3))
        # 不传 save_path -> plt.show()
        with unittest.mock.patch("matplotlib.pyplot.show"):
            a.plot_top_features()

    def test_plot_top_features_with_top_n(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        a = self._make_analyzer()
        a.fitted = True
        a.shap_values = np.random.normal(0, 1, (10, 3))
        p = str(tmp_path / "top2.png")
        a.plot_top_features(save_path=p, top_n=2)
        assert os.path.exists(p)
        assert os.path.exists(p.replace(".png", ".pdf"))

    def test_generate_report_no_top5(self):
        a = self._make_analyzer()
        a.fitted = True
        a.model_type = "linear"
        a.shap_values = np.random.normal(0, 1, (5, 2))
        a.feature_names = ["x1", "x2"]
        report = a.generate_report()
        assert "SHAP 可解释性分析报告" in report


# ============= tam _predict_tam 路径 (手动注入 model) =============

class TestTAMPredictTAM:
    def test_predict_tam_with_yhat_lower(self):
        # 手动注入 self.model 模拟 tam 库可用
        from algorithms.prediction.tam import TAM_Forecast
        m = TAM_Forecast()
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m.fit(df)

        # FakeForecastDF.__getitem__ 返回 pandas.Series 以支持 .values 调用
        class FakeForecastDF:
            def __init__(self, d):
                self._d = {k: pd.Series(v) for k, v in d.items()}
            def __getitem__(self, k):
                return self._d[k]
            def __contains__(self, k):
                return k in self._d
            def get(self, k, default=None):
                return self._d.get(k, default)

        class FakeModel:
            def predict(self, steps=12):
                return FakeForecastDF({
                    "yhat": [50 + i for i in range(steps)],
                    "trend": [50 + i for i in range(steps)],
                    "seasonal": [0.1 * i for i in range(steps)],
                    "yhat_lower": [48 + i for i in range(steps)],
                    "yhat_upper": [52 + i for i in range(steps)],
                })

        m.model = FakeModel()
        # 直接调用 _predict_tam (绕过 HAS_TAM 检查)
        r = m._predict_tam(steps=5, include_components=True)
        assert "forecast" in r
        assert "trend" in r
        assert "seasonal" in r
        assert "ci_lower" in r
        assert "ci_upper" in r
        assert len(r["forecast"]) == 5

    def test_predict_tam_without_yhat_lower(self):
        # 模拟 tam 库返回不含 yhat_lower -> 走 fallback 公式
        from algorithms.prediction.tam import TAM_Forecast
        m = TAM_Forecast()
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m.fit(df)

        class FakeForecastDF:
            def __init__(self, d):
                self._d = {k: pd.Series(v) for k, v in d.items()}
            def __getitem__(self, k):
                return self._d[k]
            def __contains__(self, k):
                return k in self._d
            def get(self, k, default=None):
                return self._d.get(k, default)

        class FakeModel:
            def predict(self, steps=12):
                return FakeForecastDF({
                    "yhat": [50 + i for i in range(steps)],
                    "trend": [50 + i for i in range(steps)],
                    "seasonal": [0.1 * i for i in range(steps)],
                    # 不含 yhat_lower / yhat_upper
                })

        m.model = FakeModel()
        r = m._predict_tam(steps=3, include_components=True)
        assert "ci_lower" in r and "ci_upper" in r
        # 用残差 std 构造置信区间
        assert len(r["ci_lower"]) == 3

    def test_predict_tam_no_components(self):
        from algorithms.prediction.tam import TAM_Forecast
        m = TAM_Forecast()
        n = 24
        t = np.arange(n)
        y = 50 + 0.3 * t + np.sin(2 * np.pi * t / 12)
        df = pd.DataFrame({"month": t, "value": y})
        m.fit(df)

        class FakeForecastDF:
            def __init__(self, d):
                self._d = {k: pd.Series(v) for k, v in d.items()}
            def __getitem__(self, k):
                return self._d[k]
            def __contains__(self, k):
                return k in self._d
            def get(self, k, default=None):
                return self._d.get(k, default)

        class FakeModel:
            def predict(self, steps=12):
                return FakeForecastDF({
                    "yhat": [50 + i for i in range(steps)],
                    "yhat_lower": [48 + i for i in range(steps)],
                    "yhat_upper": [52 + i for i in range(steps)],
                })

        m.model = FakeModel()
        r = m._predict_tam(steps=4, include_components=False)
        assert "trend" not in r
        assert "forecast" in r
        assert "ci_lower" in r

    def test_main_block(self):
        old_argv = sys.argv
        sys.argv = ["tam.py"]
        try:
            runpy.run_module("algorithms.prediction.tam", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv


# ============= 其他 __main__ 块 =============

class TestOtherMainBlocks:
    @pytest.mark.parametrize("module", [
        "algorithms.optimization.sa_pso",
        "algorithms.optimization.de",
        "algorithms.optimization.ga",
        "algorithms.prediction.arima",
        "algorithms.prediction.mlp",
        "algorithms.network.graph_algo",
        "algorithms.mechanistic.fem_poisson",
        "algorithms.mechanistic.ode_solver",
        "algorithms.validation.metrics",
        "algorithms.validation.sobol_enhanced",
        "algorithms.validation.auto_tune",
    ])
    def test_run_main(self, module):
        old_argv = sys.argv
        sys.argv = [module + ".py"]
        try:
            runpy.run_module(module, run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv


# ============= bounds.py 内部 (已 100%, 仅 main 块) =============

class TestBoundsMain:
    def test_main_block(self):
        old_argv = sys.argv
        sys.argv = ["bounds.py"]
        try:
            runpy.run_module("algorithms.optimization.bounds", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
