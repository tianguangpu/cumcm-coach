"""algorithms/validation/ 低覆盖模块补测 II —— shap_analysis/sobol/sobol_enhanced。

目标：
  shap_analysis 16% → 80%+（覆盖构造/检测类型/未fit报错/降级路径）
  sobol.py       0% → 85%+（覆盖核心估计器 + 自举 CI + 边界）
  sobol_enhanced 0% → 85%+（覆盖 auto/salib/numpy 三分支 + 降级）
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP, HAS_MPL
from algorithms.validation.sobol import sobol_total_and_first
from algorithms.validation.sobol_enhanced import sobol_analysis, _sobol_numpy, HAS_SALIB


# ============================================================
# SHAPAnalyzer (shap_analysis.py) —— 覆盖 16% → 目标 80%+
# ============================================================

class TestSHAPAnalyzer:
    @pytest.fixture
    def rf_model_and_data(self):
        from sklearn.ensemble import RandomForestRegressor
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (100, 4))
        y = 2 * X[:, 0] - X[:, 1] + rng.normal(0, 0.1, 100)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model, X

    def test_init_default_feature_names(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        assert a.feature_names == ["X0", "X1", "X2", "X3"]
        assert a.X_test is not None and len(a.X_test) <= 100

    def test_init_custom_feature_names(self, rf_model_and_data):
        model, X = rf_model_and_data
        names = ["温度", "压力", "流量", "浓度"]
        a = SHAPAnalyzer(model, X[:80], feature_names=names)
        assert a.feature_names == names

    def test_init_custom_X_test(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], X_test=X[80:])
        assert a.X_test.shape[0] == 20

    def test_init_model_type_explicit(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], model_type="tree")
        assert a.model_type == "tree"

    def test_detect_model_type_tree(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], model_type="auto")
        assert a._detect_model_type() == "tree"  # RandomForest -> tree

    def test_detect_model_type_linear(self):
        from sklearn.linear_model import Ridge
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (30, 3))
        y = X[:, 0] + rng.normal(0, 0.1, 30)
        m = Ridge().fit(X, y)
        a = SHAPAnalyzer(m, X, model_type="auto")
        assert a._detect_model_type() == "linear"

    def test_detect_model_type_kernel_fallback(self):
        class DummyModel:
            def predict(self, X):
                return np.zeros(len(X))
        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (20, 2))
        a = SHAPAnalyzer(DummyModel(), X, model_type="auto")
        assert a._detect_model_type() == "kernel"

    def test_fit_raises_without_shap(self, monkeypatch, rf_model_and_data):
        model, X = rf_model_and_data
        # 强制 HAS_SHAP=False 测降级报错
        import algorithms.validation.shap_analysis as mod
        monkeypatch.setattr(mod, "HAS_SHAP", False)
        a = SHAPAnalyzer(model, X[:80])
        with pytest.raises(RuntimeError, match="请安装 shap"):
            a.fit()

    def test_fit_with_shap_tree(self, rf_model_and_data):
        if not HAS_SHAP:
            pytest.skip("shap 未安装")
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], X_test=X[80:95], model_type="tree")
        a.fit()
        assert a.fitted is True
        assert a.shap_values is not None

    def test_get_feature_importance_not_fitted_raises(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            a.get_feature_importance()

    def test_get_feature_importance_fitted(self, rf_model_and_data):
        if not HAS_SHAP:
            pytest.skip("shap 未安装")
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], X_test=X[80:95], model_type="tree")
        a.fit()
        df = a.get_feature_importance()
        assert set(df.columns) >= {"feature", "importance"}
        assert len(df) == 4

    def test_plot_summary_not_fitted(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        a.plot_summary()  # not fitted -> 静默返回

    def test_plot_waterfall_not_fitted(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        a.plot_waterfall()  # not fitted -> 静默返回

    def test_plot_bar_not_fitted(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        a.plot_bar()  # not fitted -> 静默返回

    def test_plot_dependence_not_fitted(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        a.plot_dependence("X0")  # not fitted -> 静默返回

    def test_plot_top_features_not_fitted(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        a.plot_top_features()  # not fitted -> 静默返回

    def test_generate_report_not_fitted_raises(self, rf_model_and_data):
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80])
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            a.generate_report()

    def test_generate_report_fitted(self, rf_model_and_data):
        if not HAS_SHAP:
            pytest.skip("shap 未安装")
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], X_test=X[80:95], model_type="tree",
                         feature_names=["A", "B", "C", "D"])
        a.fit()
        report = a.generate_report()
        assert "SHAP 可解释性分析报告" in report
        assert "模型类型: tree" in report

    def test_plot_top_features_fitted(self, rf_model_and_data, tmp_path, monkeypatch):
        if not HAS_SHAP:
            pytest.skip("shap 未安装")
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        model, X = rf_model_and_data
        a = SHAPAnalyzer(model, X[:80], X_test=X[80:95], model_type="tree")
        a.fit()
        p = tmp_path / "top.png"
        a.plot_top_features(str(p))
        assert p.exists()


# ============================================================
# sobol.py (sobol_total_and_first) —— 覆盖 0% → 目标 85%+
# ============================================================

class TestSobol:
    def test_additive_model(self):
        """f = x1 + 2*x2, S1 应接近 [0.2, 0.8]"""
        def f(x):
            return x[0] + 2.0 * x[1]
        r = sobol_total_and_first(f, [(0, 1), (0, 1)], N=512, seed=42, n_boot=100)
        assert len(r["S1"]) == 2
        assert r["S1"][0] == pytest.approx(0.2, abs=0.1)
        assert r["S1"][1] == pytest.approx(0.8, abs=0.1)
        assert r["ST"][0] == pytest.approx(r["S1"][0], abs=0.15)

    def test_return_keys(self):
        def f(x):
            return x[0] + x[1]
        r = sobol_total_and_first(f, [(0, 1), (0, 1)], N=64, seed=1, n_boot=20)
        assert {"S1", "ST", "S1_conf", "ST_conf", "n_eval"} <= set(r.keys())

    def test_n_eval(self):
        def f(x):
            return x[0]
        r = sobol_total_and_first(f, [(0, 1), (0, 1), (0, 1)], N=32, seed=1, n_boot=10)
        # N * (D + 2) = 32 * 5 = 160
        assert r["n_eval"] == 160

    def test_reproducible(self):
        def f(x):
            return x[0] + x[1]
        r1 = sobol_total_and_first(f, [(0, 1), (0, 1)], N=64, seed=42, n_boot=20)
        r2 = sobol_total_and_first(f, [(0, 1), (0, 1)], N=64, seed=42, n_boot=20)
        assert r1["S1"] == r2["S1"]

    def test_conf_nonnegative(self):
        def f(x):
            return x[0] + x[1]
        r = sobol_total_and_first(f, [(0, 1), (0, 1)], N=64, seed=42, n_boot=30)
        assert all(c >= 0 for c in r["S1_conf"])
        assert all(c >= 0 for c in r["ST_conf"])

    def test_single_dim_raises(self):
        def f(x):
            return x[0]
        with pytest.raises(ValueError, match="至少需要 2 个参数"):
            sobol_total_and_first(f, [(0, 1)], N=32)

    def test_constant_model(self):
        """模型恒定（VarY≈0）走除零保护"""
        def f(x):
            return 5.0
        r = sobol_total_and_first(f, [(0, 1), (0, 1)], N=32, seed=1, n_boot=10)
        assert all(s == 0.0 for s in r["S1"])  # clip 到 [0, ST]

    def test_three_params(self):
        def f(x):
            return x[0] + 2 * x[1] + 3 * x[2]
        r = sobol_total_and_first(f, [(0, 1), (0, 1), (0, 1)], N=128, seed=42, n_boot=50)
        assert len(r["S1"]) == 3
        # 方差贡献: 1, 4, 9 -> 总 14, S1 ≈ [0.07, 0.29, 0.64]
        assert r["S1"][2] > r["S1"][1] > r["S1"][0]


# ============================================================
# sobol_enhanced.py —— 覆盖 0% → 目标 85%+
# ============================================================

class TestSobolEnhanced:
    def test_auto_method(self):
        def f(x):
            return x[0] + 2.0 * x[1]
        r = sobol_analysis(f, [(0, 1), (0, 1)], N=64, seed=42, n_boot=20, method="auto")
        assert r["method"] in ("salib", "numpy")
        assert "S1" in r and len(r["S1"]) == 2

    def test_numpy_method_explicit(self):
        def f(x):
            return x[0] + x[1]
        r = sobol_analysis(f, [(0, 1), (0, 1)], N=32, seed=1, n_boot=10, method="numpy")
        assert r["method"] == "numpy"
        assert r["n_eval"] == 32 * 4

    def test_salib_method_uninstalled_raises(self):
        if HAS_SALIB:
            pytest.skip("SALib 已安装，跳过降级测试")
        def f(x):
            return x[0]
        with pytest.raises(ImportError, match="SALib 未安装"):
            sobol_analysis(f, [(0, 1), (0, 1)], N=32, method="salib")

    def test_salib_method_installed(self):
        if not HAS_SALIB:
            pytest.skip("SALib 未安装")
        def f(x):
            return x[0] + 2.0 * x[1]
        r = sobol_analysis(f, [(0, 1), (0, 1)], N=64, seed=42, n_boot=20, method="salib")
        assert r["method"] == "salib"
        assert r["S1"][0] == pytest.approx(0.2, abs=0.15)

    def test_unknown_method_raises(self):
        def f(x):
            return x[0]
        with pytest.raises(ValueError, match="未知方法"):
            sobol_analysis(f, [(0, 1), (0, 1)], N=32, method="xxx")

    def test_single_dim_raises(self):
        def f(x):
            return x[0]
        with pytest.raises(ValueError, match="至少需要 2 个参数"):
            sobol_analysis(f, [(0, 1)], N=32, method="numpy")

    def test_numpy_additive_model(self):
        def f(x):
            return x[0] + 2.0 * x[1]
        r = sobol_analysis(f, [(0, 1), (0, 1)], N=256, seed=42, n_boot=50, method="numpy")
        assert r["S1"][0] == pytest.approx(0.2, abs=0.1)
        assert r["S1"][1] == pytest.approx(0.8, abs=0.1)

    def test_backward_compat_alias(self):
        """sobol_total_and_first 应是 sobol_analysis 的别名"""
        from algorithms.validation.sobol_enhanced import sobol_total_and_first as alias
        assert alias is sobol_analysis

    def test_auto_warns_without_salib(self, monkeypatch):
        import algorithms.validation.sobol_enhanced as mod
        monkeypatch.setattr(mod, "HAS_SALIB", False)
        def f(x):
            return x[0] + x[1]
        with pytest.warns(UserWarning, match="SALib 未安装"):
            r = sobol_analysis(f, [(0, 1), (0, 1)], N=32, seed=1, n_boot=10, method="auto")
        assert r["method"] == "numpy"
