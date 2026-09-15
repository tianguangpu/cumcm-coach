"""algorithms/validation/ 低覆盖模块补测 —— metrics/sensitivity/monte_carlo/auto_tune。

目标：把这 4 个模块的覆盖率从 38%/53%/54%/18% 拉到 80%+。
覆盖核心静态方法 + 类方法 + 边界条件 + 降级路径。
"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

# 确保能 import algorithms.*
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.validation.metrics import FitMetrics
from algorithms.validation.sensitivity import SensitivityAnalyzer
from algorithms.validation.monte_carlo import MonteCarlo


# ============================================================
# FitMetrics (metrics.py) —— 覆盖 38% → 目标 85%+
# ============================================================

class TestFitMetrics:
    def test_r2_perfect(self):
        y = np.array([1.0, 2, 3, 4, 5])
        assert FitMetrics.r2(y, y) == pytest.approx(1.0)

    def test_r2_mean_prediction(self):
        y = np.array([1.0, 2, 3, 4, 5])
        yhat = np.full_like(y, y.mean())
        assert FitMetrics.r2(y, yhat) == pytest.approx(0.0)

    def test_r2_constant_true(self):
        y = np.array([3.0, 3, 3, 3])
        yhat = np.array([3.0, 3, 3, 3])
        assert FitMetrics.r2(y, yhat) == 0.0  # ss_tot=0 分支

    def test_mae_zero(self):
        y = np.array([1.0, 2, 3])
        assert FitMetrics.mae(y, y) == 0.0

    def test_mae_value(self):
        y = np.array([1.0, 2, 3])
        yhat = np.array([2.0, 2, 2])
        assert FitMetrics.mae(y, yhat) == pytest.approx(2 / 3)

    def test_rmse_zero(self):
        y = np.array([1.0, 2, 3])
        assert FitMetrics.rmse(y, y) == 0.0

    def test_rmse_value(self):
        y = np.array([1.0, 2, 3])
        yhat = np.array([1.0, 2, 5])
        assert FitMetrics.rmse(y, yhat) == pytest.approx(np.sqrt(4 / 3))

    def test_mape_normal(self):
        y = np.array([100.0, 200, 400])
        yhat = np.array([110.0, 190, 420])
        # |10/100| + |10/200| + |20/400| / 3 * 100
        assert FitMetrics.mape(y, yhat) == pytest.approx((10 + 5 + 5) / 3)

    def test_mape_all_zero(self):
        y = np.zeros(5)
        yhat = np.zeros(5)
        assert np.isnan(FitMetrics.mape(y, yhat))

    def test_mape_some_zero(self):
        y = np.array([0.0, 100.0])
        yhat = np.array([1.0, 110.0])
        # 只算非零项: |10/100|*100 = 10
        assert FitMetrics.mape(y, yhat) == pytest.approx(10.0)

    def test_evaluate_keys(self):
        y = np.array([1.0, 2, 3])
        m = FitMetrics.evaluate(y, y + 0.1)
        assert set(m.keys()) == {"R2", "MAE", "RMSE", "MAPE"}

    def test_residual_normality_scipy_or_fallback(self):
        rng = np.random.default_rng(42)
        res = rng.normal(0, 1, 100)
        stat, p = FitMetrics.residual_normality(res)
        assert isinstance(stat, float) and isinstance(p, float)

    def test_residual_normality_zero_std(self):
        res = np.array([5.0, 5, 5, 5])
        stat, p = FitMetrics.residual_normality(res)
        assert np.isnan(stat) or stat == 0.0  # shapiro 对常量返回 NaN

    def test_plot_residuals_no_save(self, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        rng = np.random.default_rng(0)
        res = rng.normal(0, 1, 50)
        FitMetrics.plot_residuals(res)  # 不应抛异常
        import matplotlib.pyplot as plt
        plt.close("all")

    def test_plot_residuals_save(self, tmp_path, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        rng = np.random.default_rng(1)
        res = rng.normal(0, 1, 50)
        p = tmp_path / "res.png"
        FitMetrics.plot_residuals(res, str(p))
        assert p.exists()
        import matplotlib.pyplot as plt
        plt.close("all")

    def test_normal_quantile_invalid(self):
        assert np.isnan(FitMetrics._normal_quantile(0.0))
        assert np.isnan(FitMetrics._normal_quantile(1.0))

    def test_normal_quantile_valid(self):
        # p=0.5 应该接近 0
        q = FitMetrics._normal_quantile(0.5)
        assert abs(q) < 0.5


# ============================================================
# SensitivityAnalyzer (sensitivity.py) —— 覆盖 53% → 目标 85%+
# ============================================================

class TestSensitivityAnalyzer:
    @pytest.fixture
    def linear_model(self):
        def f(p):
            return p["a"] * 3.0 + p["b"] * 4.0 ** 2 + p["c"]
        return f

    @pytest.fixture
    def base_params(self):
        return {"a": 2.0, "b": 0.5, "c": 1.0}

    def test_analyze_returns_dict(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        r = sa.analyze()
        assert isinstance(r, dict)
        assert len(r) == 3 * 2  # 3 参数 × 2 扰动档

    def test_analyze_keys(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        assert ("a", 0.1) in sa.results and ("a", 0.2) in sa.results

    def test_analyze_result_fields(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        info = sa.results[("a", 0.1)]
        assert {"y_up", "y_down", "elasticity", "change_up", "change_down"} <= set(info.keys())

    def test_analyze_base_output_set(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        assert sa.base_output is not None

    def test_elasticity_summary_keys(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        s = sa.elasticity_summary()
        assert set(s.keys()) == set(base_params.keys())

    def test_elasticity_summary_grades(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        s = sa.elasticity_summary()
        for name, info in s.items():
            assert info["grade"] in ("高", "中", "低")
            assert "elasticity" in info

    def test_linear_model_elasticity_value(self, linear_model, base_params):
        # y = a*3 + b*16 + c, 对 a 的弹性 = (dY/Y)/(dX/X) ≈ (3*Δa / Y) / (Δa/a) = 3a/Y
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        s = sa.elasticity_summary()
        y_base = 2 * 3 + 0.5 * 16 + 1  # = 15
        expected_eps_a = 3 * 2 / y_base  # = 0.4
        assert s["a"]["elasticity"] == pytest.approx(expected_eps_a, abs=0.05)

    def test_custom_perturbations(self, linear_model, base_params):
        sa = SensitivityAnalyzer(linear_model, base_params, perturbations=(0.05, 0.15, 0.25))
        sa.analyze()
        assert len(sa.results) == 3 * 3

    def test_zero_base_output(self):
        # base_output=0 时走 y0=1.0 分支
        def f(p):
            return p["x"] - p["x"]  # 恒为 0
        sa = SensitivityAnalyzer(f, {"x": 10.0})
        sa.analyze()
        assert sa.base_output == 0.0
        assert sa.results[("x", 0.1)]["elasticity"] == 0.0

    def test_plot_tornado(self, linear_model, base_params, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        sa.plot_tornado()
        import matplotlib.pyplot as plt
        plt.close("all")

    def test_plot_tornado_save(self, linear_model, base_params, tmp_path, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        sa = SensitivityAnalyzer(linear_model, base_params)
        sa.analyze()
        p = tmp_path / "tornado.png"
        sa.plot_tornado(str(p))
        assert p.exists()
        import matplotlib.pyplot as plt
        plt.close("all")


# ============================================================
# MonteCarlo (monte_carlo.py) —— 覆盖 54% → 目标 85%+
# ============================================================

class TestMonteCarlo:
    @pytest.fixture
    def sim_linear(self):
        def f(p):
            return 2.0 * p["x1"] + p["x2"] ** 2
        return f

    @pytest.fixture
    def dist_normal_uniform(self):
        return {
            "x1": {"dist": "normal", "mean": 10, "std": 1},
            "x2": {"dist": "uniform", "low": 0, "high": 3},
        }

    def test_run_returns_array(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        s = mc.run(n=50, seed=42)
        assert isinstance(s, np.ndarray) and len(s) == 50

    def test_run_reproducible(self, sim_linear, dist_normal_uniform):
        mc1 = MonteCarlo(sim_linear, dist_normal_uniform)
        s1 = mc1.run(n=50, seed=42)
        mc2 = MonteCarlo(sim_linear, dist_normal_uniform)
        s2 = mc2.run(n=50, seed=42)
        assert np.allclose(s1, s2)

    def test_quantiles_default(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=50, seed=42)
        q = mc.quantiles()
        assert set(q.keys()) == {"q5", "q50", "q95"}

    def test_quantiles_custom(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=50, seed=42)
        q = mc.quantiles([0.1, 0.9])
        assert set(q.keys()) == {"q10", "q90"}

    def test_quantiles_no_run_raises(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        with pytest.raises(ValueError):
            mc.quantiles()

    def test_statistics_fields(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=50, seed=42)
        st = mc.statistics()
        assert {"mean", "std", "cv", "ci_95", "n", "quantiles", "convergence", "dist_spec", "dist_statement"} <= set(st.keys())
        assert st["n"] == 50
        assert len(st["ci_95"]) == 2

    def test_statistics_no_run_raises(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        with pytest.raises(ValueError):
            mc.statistics()

    def test_convergence_diag(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=100, seed=42)
        c = mc.convergence_diag()
        assert {"cum_mean_end", "cum_se_end", "final_se", "stable_ratio", "n", "tail_len", "converged"} <= set(c.keys())
        assert c["n"] == 100

    def test_convergence_no_run_raises(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        with pytest.raises(ValueError):
            mc.convergence_diag()

    def test_dist_statement_normal_uniform(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        s = mc._dist_statement()
        assert "x1~N(" in s and "x2~U[" in s

    def test_lognormal_dist(self):
        def f(p):
            return p["x"]
        mc = MonteCarlo(f, {"x": {"dist": "lognormal", "mean": 1.0, "std": 0.3, "base": 10}})
        s = mc.run(n=30, seed=42)
        assert len(s) == 30
        assert "x~LogN" in mc._dist_statement()

    def test_triangle_dist(self):
        def f(p):
            return p["x"]
        mc = MonteCarlo(f, {"x": {"dist": "triangle", "low": 0, "mode": 0.5, "high": 1}})
        s = mc.run(n=30, seed=42)
        assert len(s) == 30
        assert "x~Tri(" in mc._dist_statement()

    def test_default_normal_dist(self):
        # 缺省 dist 字段走 normal 分支
        def f(p):
            return p["x"]
        mc = MonteCarlo(f, {"x": {"mean": 5, "std": 1}})
        s = mc.run(n=20, seed=42)
        assert len(s) == 20

    def test_plot_distribution(self, sim_linear, dist_normal_uniform, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=50, seed=42)
        mc.plot_distribution()
        import matplotlib.pyplot as plt
        plt.close("all")

    def test_plot_distribution_save(self, sim_linear, dist_normal_uniform, tmp_path, monkeypatch):
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        mc.run(n=50, seed=42)
        p = tmp_path / "mc.png"
        mc.plot_distribution(str(p))
        assert p.exists()
        import matplotlib.pyplot as plt
        plt.close("all")

    def test_plot_no_run_raises(self, sim_linear, dist_normal_uniform):
        mc = MonteCarlo(sim_linear, dist_normal_uniform)
        with pytest.raises(ValueError):
            mc.plot_distribution()


# ============================================================
# AutoTuner (auto_tune.py) —— 覆盖 18% → 目标 80%+
# 跳过 optuna（可能未装）和 plot（matplotlib 可选）的深度测试
# ============================================================

class TestAutoTuner:
    @pytest.fixture
    def regression_data(self):
        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (60, 3))
        y = 2 * X[:, 0] - X[:, 1] + 0.5 * X[:, 2] + rng.normal(0, 0.1, 60)
        return X, y

    def test_param_grids_dict(self):
        from algorithms.validation.auto_tune import PARAM_GRIDS
        assert {"rf", "xgb", "lgbm", "svr", "ridge", "lasso", "knn", "mlp"} <= set(PARAM_GRIDS.keys())

    def test_quick_cv(self, regression_data):
        from algorithms.validation.auto_tune import quick_cv
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        r = quick_cv(RandomForestRegressor(n_estimators=10, random_state=42), X, y, cv=3)
        assert {"mean", "std", "scores", "report_str"} <= set(r.keys())
        assert len(r["scores"]) == 3

    def test_quick_cv_time_series(self, regression_data):
        from algorithms.validation.auto_tune import quick_cv
        from sklearn.linear_model import Ridge
        X, y = regression_data
        r = quick_cv(Ridge(), X, y, cv=3, is_time_series=True)
        assert r["mean"] is not None

    def test_fit_grid(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner, PARAM_GRIDS
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        tuner = AutoTuner(
            RandomForestRegressor,
            {"n_estimators": [10, 20], "max_depth": [3, 5]},
            method="grid",
        )
        best_model, best_params, cv_results = tuner.fit(X, y, cv=3)
        assert best_model is not None
        assert "n_estimators" in best_params
        assert len(cv_results) > 0

    def test_fit_random(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        tuner = AutoTuner(
            RandomForestRegressor,
            {"n_estimators": [10, 20], "max_depth": [3, 5]},
            method="random",
            n_iter=3,
        )
        best_model, best_params, cv_results = tuner.fit(X, y, cv=3)
        assert best_model is not None
        assert "n_estimators" in best_params

    def test_fit_time_series(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.linear_model import Ridge
        X, y = regression_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]}, method="grid")
        best_model, best_params, _ = tuner.fit(X, y, cv=3, is_time_series=True)
        assert best_model is not None
        assert "alpha" in best_params

    def test_cross_validate(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        tuner = AutoTuner(RandomForestRegressor, {"n_estimators": [10]}, method="grid")
        tuner.fit(X, y, cv=3)
        r = tuner.cross_validate(X, y, cv=3)
        assert {"r2_mean", "r2_std", "mse_mean", "mae_mean"} <= set(r.keys())

    def test_cross_validate_no_fit_raises(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        tuner = AutoTuner(RandomForestRegressor, {})
        with pytest.raises(RuntimeError):
            tuner.cross_validate(X, y)

    def test_summary(self, regression_data):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        X, y = regression_data
        tuner = AutoTuner(RandomForestRegressor, {"n_estimators": [10]}, method="grid")
        tuner.fit(X, y, cv=3)
        s = tuner.summary()
        assert {"method", "best_params", "best_score", "search_time", "n_trials"} <= set(s.keys())
        assert s["method"] == "grid"

    def test_summary_no_fit(self):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        tuner = AutoTuner(RandomForestRegressor, {})
        s = tuner.summary()
        assert s["best_params"] is None and s["n_trials"] == 0

    def test_plot_convergence_no_results(self):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        tuner = AutoTuner(RandomForestRegressor, {})
        # cv_results=None 时 plot_convergence 应静默返回
        tuner.plot_convergence()  # 不应抛异常

    def test_plot_cv_results_no_model(self):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        tuner = AutoTuner(RandomForestRegressor, {})
        tuner.plot_cv_results()  # best_model=None 时应静默返回

    def test_plot_convergence_with_results(self, regression_data, tmp_path, monkeypatch):
        from algorithms.validation.auto_tune import AutoTuner
        from sklearn.ensemble import RandomForestRegressor
        monkeypatch.setattr("matplotlib.pyplot.show", lambda *a, **k: None)
        X, y = regression_data
        tuner = AutoTuner(RandomForestRegressor, {"n_estimators": [10, 20]}, method="grid")
        tuner.fit(X, y, cv=3)
        p = tmp_path / "conv.png"
        tuner.plot_convergence(str(p))
        assert p.exists()
        import matplotlib.pyplot as plt
        plt.close("all")
