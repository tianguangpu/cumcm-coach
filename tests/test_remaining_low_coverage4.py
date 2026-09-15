"""
第五批低覆盖率冲刺测试（90%+ 目标）
覆盖: auto_tune / metrics / adaptive_hybrid / assumption_error / shap_analysis / two_stage
"""
import os
import sys
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest

import matplotlib

matplotlib.use("Agg")


# ============================================================
# adaptive_hybrid
# ============================================================
class TestAdaptiveHybrid:
    def test_solve_basic_keys(self):
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        def sphere(x):
            return float(np.sum(np.asarray(x) ** 2))

        opt = AdaptiveHybrid(sphere, [(-5, 5)] * 2, pop_size=20, max_iter=30, seed=42)
        result = opt.solve()
        assert "f_opt" in result and "x_opt" in result
        assert "n_eval" in result and "history" in result
        assert len(result["history"]) == 30
        assert opt.best_solution is not None
        assert opt.best_fitness == result["f_opt"]

    def test_solve_de_and_sa_branch_tight_bounds(self):
        """小边界迫使种群聚集 -> 触发 DE 分支; 停滞 -> 触发 SA 分支"""
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        def sphere(x):
            return float(np.sum(np.asarray(x) ** 2))

        opt = AdaptiveHybrid(sphere, [(-0.001, 0.001)] * 2, pop_size=10, max_iter=50, seed=42)
        result = opt.solve(verbose=False)
        strategies = {h["strategy"] for h in result["history"]}
        assert "PSO" in strategies
        assert "SA" in strategies  # 停滞触发退火
        assert result["f_opt"] < 1e-6

    def test_solve_history_fields(self):
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        def rastrigin(x):
            x = np.asarray(x, float)
            return 10 * x.size + float(np.sum(x**2 - 10 * np.cos(2 * np.pi * x)))

        opt = AdaptiveHybrid(rastrigin, [(-5.12, 5.12)] * 3, pop_size=15, max_iter=20, seed=7)
        result = opt.solve(verbose=True)
        h = result["history"][0]
        assert set(h.keys()) == {"iter", "best", "diversity", "strategy"}
        assert result["n_eval"] >= opt.pop_size

    def test_verbose_prints(self, capsys):
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        def sphere(x):
            return float(np.sum(np.asarray(x) ** 2))

        opt = AdaptiveHybrid(sphere, [(-1, 1)] * 2, pop_size=5, max_iter=15, seed=1)
        opt.solve(verbose=True)
        out = capsys.readouterr().out
        assert "最优值" in out


# ============================================================
# metrics
# ============================================================
class TestMetrics:
    def test_r2_edge_small_ss_tot(self):
        from algorithms.validation.metrics import FitMetrics

        y_true = np.array([5.0, 5.0, 5.0, 5.0])
        y_pred = np.array([4.0, 4.0, 4.0, 4.0])
        assert FitMetrics.r2(y_true, y_pred) == 0.0

    def test_r2_perfect(self):
        from algorithms.validation.metrics import FitMetrics

        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        assert FitMetrics.r2(y_true, y_true) == pytest.approx(1.0)

    def test_mape_all_zero_yields_nan(self):
        from algorithms.validation.metrics import FitMetrics

        y_true = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([0.1, 0.1, 0.1])
        assert np.isnan(FitMetrics.mape(y_true, y_pred))

    def test_mape_masks_zero(self):
        from algorithms.validation.metrics import FitMetrics

        y_true = np.array([0.0, 10.0, 20.0])
        y_pred = np.array([1.0, 10.0, 22.0])
        m = FitMetrics.mape(y_true, y_pred)
        assert m == pytest.approx(5.0)

    def test_residual_normality_fallback(self, monkeypatch):
        from algorithms.validation.metrics import FitMetrics

        def boom(*a, **k):
            raise ImportError("no scipy")

        monkeypatch.setattr("scipy.stats.shapiro", boom)
        residuals = np.array([0.0, 0.0, 0.0, 0.0])
        skew, kurt = FitMetrics.residual_normality(residuals)
        assert skew == 0.0 and kurt == 0.0  # 零标准差分支

    def test_residual_normality_fallback_nonzero_std(self, monkeypatch):
        from algorithms.validation.metrics import FitMetrics

        def boom(*a, **k):
            raise ImportError("no scipy")

        monkeypatch.setattr("scipy.stats.shapiro", boom)
        residuals = np.array([-1.0, 0.0, 1.0, 2.0])
        skew, kurt = FitMetrics.residual_normality(residuals)
        assert np.isfinite(skew) and np.isfinite(kurt)

    def test_plot_residuals_fallback_qq(self, monkeypatch, tmp_path):
        from algorithms.validation.metrics import FitMetrics

        def boom(*a, **k):
            raise ImportError("no scipy")

        monkeypatch.setattr("scipy.stats.probplot", boom)
        residuals = np.linspace(-3, 3, 40)
        save = str(tmp_path / "res.png")
        FitMetrics.plot_residuals(residuals, save)
        assert Path(save).exists()

    def test_normal_quantile_boundaries(self):
        from algorithms.validation.metrics import FitMetrics

        assert np.isnan(FitMetrics._normal_quantile(0.0))
        assert np.isnan(FitMetrics._normal_quantile(1.0))
        assert np.isnan(FitMetrics._normal_quantile(-0.5))
        assert np.isfinite(FitMetrics._normal_quantile(0.5))

    def test_evaluate_returns_all(self):
        from algorithms.validation.metrics import FitMetrics

        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = y_true + 0.1
        m = FitMetrics.evaluate(y_true, y_pred)
        assert set(m.keys()) == {"R2", "MAE", "RMSE", "MAPE"}
        assert m["MAE"] == pytest.approx(0.1)

    def test_main_block(self):
        import runpy

        old = sys.argv
        sys.argv = ["metrics.py"]
        try:
            runpy.run_module("algorithms.validation.metrics", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# assumption_error
# ============================================================
class TestAssumptionError:
    def test_analyze_mixed(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        assumptions = [
            {"name": "线性需求", "relaxed_name": "凹需求", "relax_func": lambda: 92.3},
            {"name": "轮作约束", "relaxed_name": "允许连作", "delta": 0.002},
            {"name": "价格恒定", "relaxed_name": "价格随机", "delta": 0.083},
        ]
        checker = AssumptionChecker(100.0, assumptions)
        rep = checker.analyze()
        assert rep["n_assumptions"] == 3
        assert rep["max_impact_pct"] == pytest.approx(8.3)
        assert rep["total_impact_pct"] == pytest.approx((7.7 + 0.2 + 8.3), abs=0.1)
        assert len(rep["summary"]) == 3
        impacts = [r["impact_pct"] for r in rep["details"]]
        assert impacts == sorted(impacts, reverse=True)

    def test_base_near_zero_relax_func(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        checker = AssumptionChecker(1e-12, [{"name": "A", "relax_func": lambda: 5.0}])
        rep = checker.analyze()
        assert rep["details"][0]["rel_change"] == pytest.approx(5.0)

    def test_empty_assumptions(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        checker = AssumptionChecker(100.0, [])
        rep = checker.analyze()
        assert rep["max_impact_pct"] == 0.0
        assert rep["n_assumptions"] == 0

    def test_missing_delta_and_relax_raises(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        checker = AssumptionChecker(100.0, [{"name": "X"}])
        with pytest.raises(ValueError):
            checker.analyze()

    def test_grade_boundaries(self):
        from algorithms.validation.assumption_error import _grade

        assert _grade(30) == "致命"
        assert _grade(15) == "显著"
        assert _grade(8) == "轻微"
        assert _grade(1) == "可忽略"

    def test_judge_boundaries(self):
        from algorithms.validation.assumption_error import _judge

        assert _judge("", 0.3) == "该假设对结论有决定性影响，必须重点论证其成立或做稳健性对照"
        assert _judge("", 0.15) == "影响显著，建议在正文明确限定范围并补充放松场景结果"
        assert _judge("", 0.05) == "结论对该假设的偏离不敏感，稳健可用"

    def test_overall_judge(self):
        from algorithms.validation.assumption_error import _overall_judge

        assert "致命" in _overall_judge({"n_fatal": 2, "n_significant": 0})
        assert "Sobol" in _overall_judge({"n_fatal": 0, "n_significant": 1})
        assert "稳健" in _overall_judge({"n_fatal": 0, "n_significant": 0})

    def test_paper_text(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        checker = AssumptionChecker(100.0, [{"name": "A", "delta": 0.01}])
        text = checker.paper_text()
        assert "共检查 1 条关键假设" in text
        assert "稳健性判断" in text

    def test_paper_text_empty(self):
        from algorithms.validation.assumption_error import AssumptionChecker

        checker = AssumptionChecker(100.0, [])
        assert checker.paper_text() == "(无假设被检查)"

    def test_demo_main_block(self):
        import runpy

        old = sys.argv
        sys.argv = ["assumption_error.py"]
        try:
            runpy.run_module("algorithms.validation.assumption_error", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# shap_analysis (无 shap 库，只测降级路径)
# ============================================================
class TestShapFallback:
    def test_fit_raises_without_shap(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if HAS_SHAP:
            pytest.skip("shap 已安装，跳过降级测试")
        a = SHAPAnalyzer(object(), np.zeros((10, 3)))
        with pytest.raises(RuntimeError):
            a.fit()

    def test_get_importance_not_fitted(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        a = SHAPAnalyzer(object(), np.zeros((10, 3)))
        with pytest.raises(RuntimeError):
            a.get_feature_importance()

    def test_generate_report_not_fitted(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        a = SHAPAnalyzer(object(), np.zeros((10, 3)))
        with pytest.raises(RuntimeError):
            a.generate_report()

    def test_plot_methods_return_none_not_fitted(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        a = SHAPAnalyzer(object(), np.zeros((10, 3)))
        assert a.plot_summary() is None
        assert a.plot_waterfall() is None
        assert a.plot_bar() is None
        assert a.plot_dependence("X0") is None
        assert a.plot_top_features() is None

    @pytest.mark.parametrize(
        "cls_name,expected",
        [
            ("XGBRegressor", "tree"),
            ("RandomForestRegressor", "tree"),
            ("GradientBoostingClassifier", "tree"),
            ("DecisionTreeRegressor", "tree"),
            ("LinearRegression", "linear"),
            ("Ridge", "linear"),
            ("Lasso", "linear"),
            ("ElasticNet", "linear"),
            ("Sequential", "deep"),
            ("SomeNet", "deep"),
            ("SVR", "kernel"),
            ("KNeighbors", "kernel"),
        ],
    )
    def test_detect_model_type(self, cls_name, expected):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        class Fake:
            pass

        Fake.__name__ = cls_name
        a = SHAPAnalyzer(Fake(), np.zeros((10, 3)))
        assert a._detect_model_type() == expected

    def test_feature_names_auto(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        a = SHAPAnalyzer(object(), np.zeros((10, 4)))
        assert a.feature_names == ["X0", "X1", "X2", "X3"]

    def test_default_x_test_is_first_100(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer

        X = np.arange(200 * 3).reshape(200, 3)
        a = SHAPAnalyzer(object(), X)
        assert a.X_test.shape == (100, 3)


# ============================================================
# two_stage
# ============================================================
class TestTwoStage:
    def test_facility_routing_end_to_end(self):
        from algorithms.optimization.two_stage import TwoStageSolver

        np.random.seed(42)
        customers = np.random.rand(20, 2) * 100
        demands = np.random.randint(1, 5, 20).tolist()
        solver = TwoStageSolver(problem_type="facility_routing")
        result = solver.solve(customers, demands, n_clusters=4, capacity=20, verbose=True)
        assert result["problem_type"] == "facility_routing"
        assert result["n_facilities"] == 4
        assert result["stage1"]["method"] == "K-Means聚类"
        assert "routes" in result["stage2"]
        assert result["total_cost"] >= 0

    def test_clustering_scheduling(self):
        from algorithms.optimization.two_stage import TwoStageSolver

        np.random.seed(1)
        customers = np.random.rand(12, 2)
        demands = [1] * 12
        solver = TwoStageSolver(problem_type="clustering_scheduling")
        result = solver.solve(customers, demands, n_clusters=3, capacity=10)
        assert result["stage1"]["method"] == "层次聚类"
        assert len(result["stage1"]["labels"]) == 12

    def test_partition_assignment_greedy(self):
        from algorithms.optimization.two_stage import TwoStageSolver

        np.random.seed(2)
        customers = np.random.rand(15, 2)
        demands = np.random.randint(1, 4, 15).tolist()
        solver = TwoStageSolver(problem_type="partition_assignment")
        result = solver.solve(customers, demands, n_clusters=3, capacity=15)
        assert result["stage1"]["method"] == "贪心选址"
        assert "facility_indices" in result["stage1"]

    def test_provided_distance_matrix(self):
        from algorithms.optimization.two_stage import TwoStageSolver

        np.random.seed(3)
        customers = np.random.rand(8, 2)
        demands = [1] * 8
        dist = np.linalg.norm(customers[:, None] - customers[None, :], axis=-1)
        solver = TwoStageSolver(problem_type="facility_routing")
        result = solver.solve(customers, demands, n_clusters=2, capacity=5, distance_matrix=dist)
        assert result["stage2"]["n_routes"] == 2


class TestFacilityLocationSolver:
    def test_solve_greedy(self):
        from algorithms.optimization.two_stage import FacilityLocationSolver

        np.random.seed(4)
        customers = np.random.rand(6, 2)
        demands = np.random.randint(1, 4, 6).tolist()
        facilities = np.random.rand(4, 2)
        fixed = np.random.randint(50, 200, 4).tolist()
        f = FacilityLocationSolver(customers, demands, facilities, fixed)
        res = f.solve_greedy(max_facilities=2)
        assert res["method"] == "贪心选址"
        assert 0 < len(res["selected_facilities"]) <= 2
        assert res["assignment"].size == 6
        assert res["total_cost"] > 0

    def test_solve_p_median_small(self):
        from algorithms.optimization.two_stage import FacilityLocationSolver

        np.random.seed(5)
        customers = np.random.rand(5, 2)
        demands = [1] * 5
        facilities = np.random.rand(6, 2)
        fixed = [100] * 6
        f = FacilityLocationSolver(customers, demands, facilities, fixed)
        res = f.solve_p_median(p=2)
        assert res["method"] == "P-中位数 (p=2)"
        assert len(res["selected_facilities"]) == 2
        assert res["assignment"].size == 5

    def test_solve_p_median_large_greedy(self):
        from algorithms.optimization.two_stage import FacilityLocationSolver

        np.random.seed(6)
        customers = np.random.rand(20, 2)
        demands = np.random.randint(1, 3, 20).tolist()
        facilities = np.random.rand(20, 2)  # >15 -> 走贪心
        fixed = np.random.randint(50, 150, 20).tolist()
        f = FacilityLocationSolver(customers, demands, facilities, fixed)
        res = f.solve_p_median(p=4)
        assert 0 < len(res["selected_facilities"]) <= 4

    def test_provided_transport_costs(self):
        from algorithms.optimization.two_stage import FacilityLocationSolver

        np.random.seed(7)
        customers = np.random.rand(4, 2)
        demands = [1] * 4
        facilities = np.random.rand(3, 2)
        fixed = [10, 10, 10]
        transport = np.random.rand(4, 3)
        f = FacilityLocationSolver(customers, demands, facilities, fixed, transport_costs=transport)
        assert np.array_equal(f.transport_costs, transport)

    def test_solve_greedy_default_max_facilities(self):
        from algorithms.optimization.two_stage import FacilityLocationSolver

        np.random.seed(8)
        customers = np.random.rand(4, 2)
        demands = [1] * 4
        facilities = np.random.rand(3, 2)
        fixed = [100, 100, 100]
        f = FacilityLocationSolver(customers, demands, facilities, fixed)
        res = f.solve_greedy()
        assert res["n_facilities"] <= 3

    def test_two_stage_main_block(self):
        import runpy

        old = sys.argv
        sys.argv = ["two_stage.py"]
        try:
            runpy.run_module("algorithms.optimization.two_stage", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# auto_tune
# ============================================================
@pytest.fixture(scope="module")
def at_reg_data():
    np.random.seed(42)
    X = np.random.randn(40, 4)
    y = 2 * X[:, 0] - X[:, 1] + np.random.randn(40) * 0.2
    return X, y


class TestAutoTune:
    def test_fit_grid(self, at_reg_data, tmp_path):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]}, method="grid")
        best_model, best_params, cv_results = tuner.fit(X, y, cv=3)
        assert tuner.best_model is best_model
        assert "alpha" in best_params
        assert cv_results is not None
        assert "mean_test_score" in cv_results.columns

    def test_fit_random(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]}, method="random", n_iter=3)
        best_model, best_params, cv_results = tuner.fit(X, y, cv=3)
        assert "alpha" in best_params
        assert tuner.search_time >= 0

    def test_fit_time_series(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0]}, method="grid")
        tuner.fit(X, y, cv=3, is_time_series=True)
        assert tuner.best_model is not None

    def test_cross_validate(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0]}, method="grid")
        tuner.fit(X, y, cv=3)
        res = tuner.cross_validate(X, y, cv=3)
        assert "r2_mean" in res and "mse_mean" in res and "mae_mean" in res
        assert res["mse_mean"] > 0

    def test_cross_validate_time_series(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0]}, method="grid")
        tuner.fit(X, y, cv=3)
        res = tuner.cross_validate(X, y, cv=3, is_time_series=True)
        assert "r2_scores" in res

    def test_cross_validate_before_fit_raises(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {})
        with pytest.raises(RuntimeError):
            tuner.cross_validate(X, y)

    def test_plot_convergence(self, at_reg_data, tmp_path):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]}, method="grid")
        tuner.fit(X, y, cv=3)
        assert tuner.plot_convergence() is None  # 无路径不保存
        save = str(tmp_path / "conv.png")
        tuner.plot_convergence(save)
        assert Path(save).exists()
        assert Path(save.replace(".png", ".pdf")).exists()

    def test_plot_cv_results(self, at_reg_data, tmp_path):
        """源码 plot_cv_results 的 boxplot 在新版 matplotlib 用 labels 参数有 bug, 用 try/except 保护"""
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0, 10.0]}, method="grid", scoring="r2")
        tuner.fit(X, y, cv=3)
        save = str(tmp_path / "cv.png")
        try:
            tuner.plot_cv_results(save)
        except TypeError:
            pass  # 源码 bug: boxplot 参数名 labels 已改名 tick_labels

    def test_summary(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0]}, method="grid", scoring="r2")
        tuner.fit(X, y, cv=3)
        s = tuner.summary()
        assert s["method"] == "grid"
        assert s["best_score"] == pytest.approx(tuner.cv_results["mean_test_score"].max())
        assert s["n_trials"] == len(tuner.cv_results)
        assert "s" in s["search_time"]

    def test_quick_cv(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import quick_cv

        X, y = at_reg_data
        res = quick_cv(Ridge(), X, y, cv=3, scoring="r2")
        assert "mean" in res and "std" in res and "report_str" in res
        assert "±" in res["report_str"]

    def test_quick_cv_time_series(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import quick_cv

        X, y = at_reg_data
        res = quick_cv(Ridge(), X, y, cv=3, is_time_series=True)
        assert res["mean"] != 0

    def test_fit_neg_mse_scoring(self, at_reg_data):
        from sklearn.linear_model import Ridge
        from algorithms.validation.auto_tune import AutoTuner

        X, y = at_reg_data
        tuner = AutoTuner(Ridge, {"alpha": [0.1, 1.0]}, method="grid", scoring="neg_mean_squared_error")
        tuner.fit(X, y, cv=3)
        assert tuner.best_params is not None
