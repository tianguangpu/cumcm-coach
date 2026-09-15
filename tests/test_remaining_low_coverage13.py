"""第十三批：ga/sa_pso repair+constraints / two_stage 异常路径 / arima 降级 / auto_tune tuple 分支"""
import os
import sys
import warnings

os.environ["MPLBACKEND"] = "Agg"

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest


# ============================================================
# GA: repair offspring 路径 + constraints 不可行警告
# ============================================================
class TestGARepairAndConstraints:
    def test_ga_repair_path_covers_lines_174_178(self):
        """传 repair 触发每代修复 offspring 的循环"""
        from algorithms.optimization.ga import GA

        def sphere(x):
            return float(np.sum(x ** 2))

        def identity_repair(x):
            return np.clip(x, -5.0, 5.0)

        solver = GA(
            obj=sphere,
            dim=3,
            bounds=[(-5.0, 5.0)] * 3,
            repair=identity_repair,
            pop_size=8,
            max_gen=10,
            seed=42,
        )
        result = solver.solve(verbose=False)
        assert result["x_opt"] is not None
        assert result["feasible"] is True
        assert len(result["history"]) == 10

    def test_ga_constraints_infeasible_warning_lines_193_195(self):
        """constraints 永远返回 False（且无 repair）触发不可行警告"""
        from algorithms.optimization.ga import GA

        def sphere(x):
            return float(np.sum(x ** 2))

        def always_infeasible(x):
            return False

        solver = GA(
            obj=sphere,
            dim=3,
            bounds=[(-5.0, 5.0)] * 3,
            constraints=always_infeasible,
            pop_size=8,
            max_gen=5,
            seed=42,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = solver.solve(verbose=False)
            assert any("constraints" in str(wi.message) for wi in w)
        assert result["feasible"] is False


# ============================================================
# SA_PSO: repair particles 路径 + constraints 不可行警告
# ============================================================
class TestSAPSORepairAndConstraints:
    def test_sa_pso_repair_path_covers_lines_192_196(self):
        """传 repair 触发每代修复粒子的循环"""
        from algorithms.optimization.sa_pso import SA_PSO

        def sphere(x):
            return float(np.sum(x ** 2))

        def identity_repair(x):
            return np.clip(x, -5.0, 5.0)

        solver = SA_PSO(
            obj=sphere,
            dim=3,
            bounds=[(-5.0, 5.0)] * 3,
            repair=identity_repair,
            N=8,
            T_max=10,
            T_0=50.0,
            alpha=0.9,
            seed=42,
        )
        result = solver.solve(verbose=False)
        assert result["x_opt"] is not None
        assert result["feasible"] is True
        assert len(result["history"]) == 10

    def test_sa_pso_constraints_infeasible_warning_lines_229_231(self):
        """constraints 永远返回 False（且无 repair）触发不可行警告"""
        from algorithms.optimization.sa_pso import SA_PSO

        def sphere(x):
            return float(np.sum(x ** 2))

        def always_infeasible(x):
            return False

        solver = SA_PSO(
            obj=sphere,
            dim=3,
            bounds=[(-5.0, 5.0)] * 3,
            constraints=always_infeasible,
            N=8,
            T_max=5,
            T_0=50.0,
            alpha=0.9,
            seed=42,
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = solver.solve(verbose=False)
            assert any("constraints" in str(wi.message) for wi in w)
        assert result["feasible"] is False


# ============================================================
# two_stage: 空聚类 continue / 异常降级路径 / remaining 空 break
# ============================================================
class TestTwoStageEdgePaths:
    def test_empty_cluster_continue_line_264_265(self):
        """partition_assignment 模式 n_clusters > n_customers 产生空聚类"""
        from algorithms.optimization.two_stage import TwoStageSolver

        customers = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
        demands = [1.0, 2.0, 1.5]
        # 贪心选址 5 个设施但只有 3 个客户 -> 至少 2 个聚类为空
        solver = TwoStageSolver(problem_type="partition_assignment")
        result = solver.solve(customers, demands, n_clusters=5, capacity=10,
                              verbose=False)
        assert "routes" in result["stage2"]
        # 空聚类被 continue 跳过，只有非空聚类产出路径
        assert result["stage2"]["n_routes"] >= 1

    def test_vrp_exception_fallback_lines_337_348(self):
        """capacity 为非数值字符串触发 VRP 内层 TypeError 降级"""
        from algorithms.optimization.two_stage import TwoStageSolver

        customers = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0],
                              [3.0, 3.0], [4.0, 4.0]])
        demands = [1.0, 2.0, 1.5, 1.0, 0.5]
        # capacity="invalid" -> (capacity or 100)="invalid" ->
        # load + sub_demands[node] <= "invalid" raises TypeError inside try block
        solver = TwoStageSolver(problem_type="facility_routing")
        result = solver.solve(customers, demands, n_clusters=2, capacity="invalid",
                              verbose=False)
        assert "routes" in result["stage2"]
        assert result["stage2"]["n_routes"] >= 1

    def test_facility_remaining_empty_break_line_405_406(self):
        """max_facilities > n_facilities remaining 空 break"""
        from algorithms.optimization.two_stage import FacilityLocationSolver

        customers = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
        demands = [1.0, 2.0, 1.5]
        facilities = np.array([[0.5, 0.5], [1.5, 1.5]])
        fixed_costs = [10.0, 12.0]
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        result = solver.solve_greedy(max_facilities=5)
        assert result["n_facilities"] == 2


# ============================================================
# ARIMA: Yule-Walker 降级 + auto_order 异常 continue
# ============================================================
class TestARIMAFallbackPaths:
    def test_yule_walker_singular_except_lines_105_106(self):
        """常数序列 d=1 差分后全 0 R 奇异 except 0.1 初值"""
        from algorithms.prediction.arima import ARIMA_Forecast

        series = np.array([5.0] * 20)
        model = ARIMA_Forecast(series, order=(1, 1, 0))
        model.fit()
        assert model.fitted is True
        assert model.params is not None
        pred = model.predict(steps=3)
        assert len(pred) == 3

    def test_auto_order_except_continue_lines_226_227(self):
        """d=1 差分后长度不足 p+q+2 -> ValueError -> except continue (226-227)"""
        from algorithms.prediction.arima import ARIMA_Forecast

        # 5 个点 d=1 后 y 长度 4，p=3 时 4 < 3+0+2=5 -> ValueError -> except
        series = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        best = ARIMA_Forecast.auto_order(series, max_p=3, max_d=1, max_q=0)
        assert best is not None
        assert best[0] >= 1


# ============================================================
# auto_tune: optuna else 分支（tuple 类型参数值）
# ============================================================
class TestAutoTuneOptunaElseBranch:
    def test_fit_optuna_tuple_param_line_219(self):
        """param_grid 含 tuple 值走 else: suggest_categorical 分支"""
        from sklearn.neural_network import MLPRegressor
        from algorithms.validation.auto_tune import AutoTuner, HAS_OPTUNA

        if not HAS_OPTUNA:
            pytest.skip("optuna 未安装")

        np.random.seed(42)
        X = np.random.randn(30, 3)
        y = X[:, 0] * 2 + np.random.randn(30) * 0.1

        tuner = AutoTuner(
            MLPRegressor,
            {"hidden_layer_sizes": [(16,), (8, 4)],
             "max_iter": [50, 100]},
            method="optuna",
            n_iter=3,
        )
        tuner.fit(X, y, cv=3)
        assert "hidden_layer_sizes" in tuner.best_params
        assert tuner.cv_results is not None


# ============================================================
# base.py 抽象方法 pass 行
# ============================================================
class TestBaseSolverAbstractPass:
    def test_abstract_solve_pass_line_141(self):
        """通过子类 super() 触发 BaseSolver.solve() 的 pass"""
        from algorithms.base import BaseSolver, SolverResult

        class ConcreteSolver(BaseSolver):
            def solve(self, objective, bounds, **kwargs):
                super().solve(objective, bounds, **kwargs)
                return SolverResult(x_opt=np.array([0.0]), f_opt=0.0)

            def validate_params(self):
                super().validate_params()
                return True

        solver = ConcreteSolver()
        result = solver.solve(lambda x: 0.0, [(0, 1)])
        assert result is not None
        assert result.f_opt == 0.0

    def test_abstract_validate_params_pass_line_154(self):
        """通过子类 super() 触发 BaseSolver.validate_params() 的 pass"""
        from algorithms.base import BaseSolver

        class MinimalSolver(BaseSolver):
            def solve(self, objective, bounds, **kwargs):
                return None

            def validate_params(self):
                super().validate_params()
                return True

        solver = MinimalSolver()
        result = solver.validate_params()
        assert result is True
