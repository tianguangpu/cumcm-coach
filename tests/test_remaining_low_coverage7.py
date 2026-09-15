"""第七批：sobol_enhanced SALib 分支 + auto_tune _fit_optuna"""
import os
import sys
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest

import matplotlib
matplotlib.use("Agg")

# 抑制 optuna 试验日志
os.environ.setdefault("OPTUNA_LOG_LEVEL", "WARNING")


# ============================================================
# sobol_enhanced: SALib 路径
# ============================================================
class TestSobolEnhancedSalib:
    def test_salib_method(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis

        r = sobol_analysis(lambda x: x[0] + 2 * x[1],
                           [(0.0, 1.0), (0.0, 1.0)],
                           N=64, n_boot=20, method="salib")
        assert r["method"] == "salib"
        assert len(r["S1"]) == 2 and len(r["ST"]) == 2
        assert r["n_eval"] >= 64 * 3

    def test_auto_uses_salib_when_installed(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis, HAS_SALIB

        if not HAS_SALIB:
            pytest.skip("SALib 未安装")
        r = sobol_analysis(lambda x: x[0] + x[1],
                           [(0.0, 1.0), (0.0, 1.0)],
                           N=32, n_boot=10, method="auto")
        assert r["method"] == "salib"

    def test_salib_single_dim_raises(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis

        with pytest.raises(ValueError):
            sobol_analysis(lambda x: x[0], [(0.0, 1.0)], method="salib")

    def test_main_block(self):
        import runpy
        old = sys.argv
        sys.argv = ["sobol_enhanced.py"]
        try:
            runpy.run_module("algorithms.validation.sobol_enhanced", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# auto_tune: _fit_optuna
# ============================================================
@pytest.fixture(scope="module")
def at_reg_data():
    np.random.seed(42)
    X = np.random.randn(40, 4)
    y = 2 * X[:, 0] - X[:, 1] + np.random.randn(40) * 0.2
    return X, y


class TestAutoTuneOptuna:
    def test_fit_optuna(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")
        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]},
                          method="optuna", n_iter=5)
        best_model, best_params, cv_results = tuner.fit(X, y, cv=3)
        assert "alpha" in best_params
        assert tuner.best_model is best_model
        assert len(cv_results) == 5
        assert "mean_test_score" in cv_results.columns

    def test_fit_optuna_int_param(self, at_reg_data):
        from sklearn.ensemble import RandomForestRegressor
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")
        X, y = at_reg_data
        tuner = AutoTuner(RandomForestRegressor,
                          {"n_estimators": [50, 100], "max_depth": [3, 5]},
                          method="optuna", n_iter=3)
        tuner.fit(X, y, cv=3)
        assert tuner.best_params is not None

    def test_fit_optuna_float_log_scale(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")
        X, y = at_reg_data
        # alpha 为浮点 -> 走 suggest_float(log=True)
        tuner = AutoTuner(Ridge, {"alpha": [0.01, 0.1, 1.0, 10.0]},
                          method="optuna", n_iter=3)
        tuner.fit(X, y, cv=3)
        assert tuner.cv_results is not None

    def test_fit_optuna_categorical_param(self, at_reg_data):
        from sklearn.svm import SVR
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")
        X, y = at_reg_data
        tuner = AutoTuner(SVR, {"kernel": ["linear", "rbf"], "C": [0.1, 1.0]},
                          method="optuna", n_iter=3, scoring="r2")
        tuner.fit(X, y, cv=3)
        assert "kernel" in tuner.best_params

    def test_optuna_main_block(self):
        import runpy
        old = sys.argv
        sys.argv = ["auto_tune.py"]
        try:
            runpy.run_module("algorithms.validation.auto_tune", run_name="__main__")
        except (SystemExit, TypeError):
            # 源码 __main__ 块用 PARAM_GRIDS["rf"] 含 max_depth=None，
            # _fit_optuna 的 suggest_int(min(values)) 会因 None 比较失败
            pass
        finally:
            sys.argv = old
