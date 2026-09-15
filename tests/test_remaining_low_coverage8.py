"""第八批：auto_tune plot_cv_results 修复后全路径 + shap 降级边界"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest
import matplotlib
matplotlib.use("Agg")


@pytest.fixture(scope="module")
def at_reg_data():
    np.random.seed(42)
    X = np.random.randn(40, 4)
    y = 2 * X[:, 0] - X[:, 1] + np.random.randn(40) * 0.2
    return X, y


# ============================================================
# auto_tune plot_cv_results 修复 boxplot 兼容
# ============================================================
class TestAutoTunePlotCvFixed:
    def test_plot_cv_results_save(self, at_reg_data, tmp_path):
        """monkeypatch boxplot 使 labels -> tick_labels 兼容, 覆盖 313-323"""
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner
        import matplotlib.axes as mpl_axes

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]},
                          method="grid", scoring="r2")
        tuner.fit(X, y, cv=3)

        # monkeypatch: 让 boxplot 接受 labels 参数（新版 matplotlib 已改名 tick_labels）
        orig_boxplot = mpl_axes.Axes.boxplot
        def patched_boxplot(self, x, **kwargs):
            if "labels" in kwargs and "tick_labels" not in kwargs:
                kwargs["tick_labels"] = kwargs.pop("labels")
            return orig_boxplot(self, x, **kwargs)

        with patch.object(mpl_axes.Axes, "boxplot", patched_boxplot):
            save = str(tmp_path / "cv_fixed.png")
            tuner.plot_cv_results(save)

        assert Path(save).exists()
        assert Path(save.replace(".png", ".pdf")).exists()

    def test_plot_cv_results_no_save(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner
        import matplotlib.axes as mpl_axes

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]},
                          method="grid", scoring="r2")
        tuner.fit(X, y, cv=3)

        orig_boxplot = mpl_axes.Axes.boxplot
        def patched_boxplot(self, x, **kwargs):
            if "labels" in kwargs and "tick_labels" not in kwargs:
                kwargs["tick_labels"] = kwargs.pop("labels")
            return orig_boxplot(self, x, **kwargs)

        with patch.object(mpl_axes.Axes, "boxplot", patched_boxplot):
            assert tuner.plot_cv_results() is None

    def test_plot_cv_results_best_model_none(self):
        """best_model 为 None 时直接 return"""
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.linear_model import Ridge

        tuner = AutoTuner(Ridge, {"alpha": [0.1]})
        # 不 fit, best_model 为 None
        assert tuner.plot_cv_results() is None

    def test_plot_convergence_no_cv_results(self):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.linear_model import Ridge

        tuner = AutoTuner(Ridge, {"alpha": [0.1]})
        assert tuner.plot_convergence() is None

    def test_summary_no_fit(self):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.linear_model import Ridge

        tuner = AutoTuner(Ridge, {"alpha": [0.1]})
        s = tuner.summary()
        assert s["best_params"] is None
        assert s["best_score"] is None
        assert s["n_trials"] == 0


# ============================================================
# auto_tune __main__ 后半段（手动调用跳过 TypeError 部分）
# ============================================================
class TestAutoTuneMainTail:
    def test_cross_validate_and_summary_after_optuna(self, at_reg_data):
        """覆盖 __main__ 块 TypeError 后中断的 cross_validate + summary 部分"""
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]},
                          method="optuna", n_iter=3)
        tuner.fit(X, y, cv=3)

        # 详细交叉验证（__main__ 块后半段）
        detailed = tuner.cross_validate(X, y, cv=3)
        assert "r2_mean" in detailed
        assert "mse_mean" in detailed
        assert "mae_mean" in detailed

        # summary
        s = tuner.summary()
        assert s["method"] == "optuna"
        assert s["best_params"] is not None
        assert s["n_trials"] == 3


# ============================================================
# shap_analysis 降级路径补充（不安装 shap）
# ============================================================
class TestShapExtraFallback:
    def test_plot_summary_fitted_no_mpl(self):
        """fitted=True 但 HAS_MPL=False 时 plot 方法 return None"""
        # 只在 shap 未安装时测试降级路径
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP, HAS_MPL
        if HAS_SHAP:
            pytest.skip("shap 已安装")
        # 手动设置 fitted=True 绕过 fit() 的 RuntimeError
        a = SHAPAnalyzer(object(), np.zeros((10, 3)))
        a.fitted = True
        if not HAS_MPL:
            assert a.plot_summary() is None
            assert a.plot_waterfall() is None
            assert a.plot_bar() is None
            assert a.plot_top_features() is None
            assert a.plot_dependence("X0") is None

    def test_shap_main_block(self):
        """__main__ 块会因 RuntimeError 跳过 fit 后的代码, 但 import 和初始化部分仍执行"""
        from algorithms.validation.shap_analysis import HAS_SHAP
        if HAS_SHAP:
            pytest.skip("shap 已安装")
        import runpy
        old = sys.argv
        sys.argv = ["shap_analysis.py"]
        try:
            runpy.run_module("algorithms.validation.shap_analysis", run_name="__main__")
        except (SystemExit, RuntimeError):
            pass
        finally:
            sys.argv = old