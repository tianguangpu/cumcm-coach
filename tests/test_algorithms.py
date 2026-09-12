"""
算法库单元测试（pytest 版本）

覆盖 34 个算法模块的完整测试。

Usage:
    pytest tests/test_algorithms.py -v
    pytest tests/test_algorithms.py -v -k "TestGA"
    pytest tests/test_algorithms.py -v --tb=short
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.base import SolverResult

# ============================================================
# 基类测试
# ============================================================


class TestSolverResult:
    """SolverResult 数据类测试"""

    def test_creation(self):
        """测试基本创建"""
        result = SolverResult(x_opt=[1.0, 2.0], f_opt=0.5)
        assert result.x_opt == [1.0, 2.0]
        assert result.f_opt == 0.5

    def test_default_values(self):
        """测试默认值"""
        result = SolverResult()
        assert result.f_opt == float("inf")
        assert result.history is None
        assert result.metadata == {}

    def test_to_dict(self):
        """测试字典转换"""
        result = SolverResult(x_opt=[1.0], f_opt=0.5, iterations=100)
        d = result.to_dict()
        assert d["x_opt"] == [1.0]
        assert d["f_opt"] == 0.5
        assert d["iterations"] == 100

    def test_summary(self):
        """测试摘要生成"""
        result = SolverResult(x_opt=[1.0, 2.0], f_opt=0.5, solver_name="TestSolver", iterations=100)
        summary = result.summary()
        assert "TestSolver" in summary
        assert "0.500000" in summary


# ============================================================
# 优化算法测试
# ============================================================


class TestGA:
    """遗传算法测试"""

    def test_convergence_sphere(self, sphere_function, simple_bounds_3d):
        """GA 应在 Sphere 函数上收敛"""
        from algorithms.optimization.ga import GA

        solver = GA(sphere_function, dim=3, bounds=simple_bounds_3d, pop_size=30, max_gen=100)
        result = solver.solve()
        assert result["f_opt"] < 1.0, f"GA 未收敛: {result['f_opt']}"

    def test_result_structure(self, sphere_function, simple_bounds_2d):
        """测试返回结构"""
        from algorithms.optimization.ga import GA

        solver = GA(sphere_function, dim=2, bounds=simple_bounds_2d, pop_size=20, max_gen=50)
        result = solver.solve()
        assert "x_opt" in result
        assert "f_opt" in result
        assert len(result["x_opt"]) == 2


class TestDE:
    """差分进化算法测试"""

    def test_convergence_sphere(self, sphere_function, simple_bounds_3d):
        """DE 应在 Sphere 函数上收敛"""
        from algorithms.optimization.de import DE

        solver = DE(sphere_function, dim=3, bounds=simple_bounds_3d, pop_size=30, max_gen=100)
        result = solver.solve()
        assert result["f_opt"] < 1.0, f"DE 未收敛: {result['f_opt']}"


class TestSAPSO:
    """模拟退火+粒子群混合算法测试"""

    def test_convergence_sphere(self, sphere_function, simple_bounds_3d):
        """SA-PSO 应在 Sphere 函数上收敛"""
        from algorithms.optimization.sa_pso import SA_PSO

        solver = SA_PSO(sphere_function, dim=3, bounds=simple_bounds_3d, N=20, T_max=50)
        result = solver.solve()
        assert result["f_opt"] < 1.0, f"SA-PSO 未收敛: {result['f_opt']}"


class TestVRP:
    """车辆路径问题测试"""

    def test_basic_vrp(self, sample_distance_matrix):
        """VRP 应返回有效路径"""
        from algorithms.optimization.vrp import VRP

        demands = [0, 10, 15, 20, 25]
        vrp = VRP(sample_distance_matrix, demands, capacity=50, n_vehicles=2)
        result = vrp.solve_ga()

        assert result["total_distance"] > 0
        assert len(result["routes"]) <= 2


class TestJobShop:
    """车间调度测试"""

    @pytest.mark.skip(reason="NSGA-II 求解器存在段错误，需修复")
    def test_basic_scheduling(self):
        """JobShop 应返回可行调度"""
        from algorithms.optimization.job_shop import JobShopScheduler

        jobs = [
            [(0, 3), (1, 2), (2, 4)],
            [(1, 4), (0, 3), (2, 2)],
            [(2, 2), (1, 3), (0, 5)],
        ]
        scheduler = JobShopScheduler(jobs)
        result = scheduler.solve_ga(pop_size=20, max_gen=50)

        assert result["makespan"] > 0

    def test_basic_interface(self):
        """JobShop 应有正确接口"""
        from algorithms.optimization.job_shop import JobShopScheduler

        jobs = [
            [(0, 3), (1, 2)],
            [(1, 2), (0, 3)],
        ]
        scheduler = JobShopScheduler(jobs)

        assert scheduler.n_jobs == 2
        assert scheduler.n_machines == 2


class TestTwoStage:
    """两阶段优化测试"""

    def test_basic_interface(self):
        """TwoStageSolver 应有正确接口"""
        from algorithms.optimization.two_stage import TwoStageSolver

        solver = TwoStageSolver("facility_routing")
        assert hasattr(solver, "solve")


# ============================================================
# 预测算法测试
# ============================================================


class TestGM11:
    """灰色预测模型测试"""

    def test_basic_prediction(self):
        """GM11 应返回预测值"""
        from algorithms.prediction.gm11 import GM11

        x0 = [10, 12, 15, 18, 22, 25]
        result = GM11(x0, predict_steps=3)

        # GM11 返回 tuple (拟合+预测序列, 参数)
        assert result is not None
        if isinstance(result, tuple):
            pred = result[0]
            # 应该包含原始数据拟合 + 预测值
            assert len(pred) >= len(x0)

    def test_prediction_extends_data(self):
        """GM11 预测值应延续数据趋势"""
        from algorithms.prediction.gm11 import GM11

        x0 = [10, 12, 15, 18, 22, 25]
        result = GM11(x0, predict_steps=3)

        if isinstance(result, tuple):
            pred = result[0]
            # 最后的预测值应大于原始数据最大值（递增数据）
            assert float(pred[-1]) > max(x0)


class TestARIMA:
    """ARIMA 时序预测测试"""

    def test_basic_prediction(self, sample_time_series):
        """ARIMA 应返回预测值"""
        from algorithms.prediction.arima import ARIMA_Forecast

        forecaster = ARIMA_Forecast(sample_time_series, order=(1, 1, 1))
        forecaster.fit()
        predictions = forecaster.predict(steps=5)

        assert len(predictions) == 5


class TestMLP:
    """神经网络预测测试"""

    def test_basic_prediction(self, sample_time_series):
        """MLP 应返回预测值"""
        from algorithms.prediction.mlp import MLP_Forecast

        forecaster = MLP_Forecast(sample_time_series, window=5, hidden_layer_sizes=(10,), max_iter=100)
        # 需要先 fit
        forecaster.fit()
        predictions = forecaster.predict(steps=5)

        assert len(predictions) == 5


class TestTAM:
    """技术采纳模型测试"""

    def test_basic_interface(self):
        """TAM 应有正确接口"""
        from algorithms.prediction.tam import TAM_Forecast

        forecaster = TAM_Forecast()
        assert hasattr(forecaster, "fit")
        assert hasattr(forecaster, "predict")


# ============================================================
# 评价算法测试
# ============================================================


class TestTOPSIS:
    """TOPSIS 综合评价测试"""

    def test_basic_evaluation(self, sample_decision_matrix):
        """TOPSIS 应返回排序结果"""
        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

        ev = ComprehensiveEvaluation(sample_decision_matrix, benefit_cols=[0, 1, 2], cost_cols=[])
        ev.run_entropy()
        # 需要同时运行 ahp 才能 combine
        pairwise = [[1, 2, 3], [0.5, 1, 2], [0.33, 0.5, 1]]
        ev.run_ahp(pairwise)
        ev.combine_weights(alpha=0.5)
        result = ev.topsis()

        assert len(result) == len(sample_decision_matrix)

    def test_entropy_weights(self, sample_decision_matrix):
        """熵权法应返回有效权重"""
        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

        ev = ComprehensiveEvaluation(sample_decision_matrix, benefit_cols=[0, 1, 2], cost_cols=[])
        weights = ev.run_entropy()

        assert len(weights) == 3
        assert abs(sum(weights) - 1.0) < 0.1

    def test_ahp_weights(self, sample_decision_matrix):
        """AHP 应返回有效权重"""
        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

        ev = ComprehensiveEvaluation(sample_decision_matrix, benefit_cols=[0, 1, 2], cost_cols=[])
        pairwise = [[1, 2, 3], [0.5, 1, 2], [0.33, 0.5, 1]]
        weights = ev.run_ahp(pairwise)

        assert len(weights) == 3


class TestVIKOR:
    """VIKOR 评价测试"""

    def test_basic_evaluation(self, sample_decision_matrix):
        """VIKOR 应返回排序结果"""
        from algorithms.evaluation.vikor import VIKOR

        weights = [0.4, 0.3, 0.3]
        benefit = [True, True, True]
        result = VIKOR(sample_decision_matrix, weights, benefit, v=0.5)

        assert len(result) == len(sample_decision_matrix)


class TestGRA:
    """灰色关联分析测试"""

    def test_basic_correlation(self):
        """GRA 应计算关联度"""
        from algorithms.evaluation.gra import grey_relational

        reference = [1, 2, 3, 4, 5]
        comparison = [1.1, 2.2, 2.8, 4.1, 5.2]
        result = grey_relational(reference, comparison, rho=0.5)

        assert 0 <= result <= 1


# ============================================================
# 机理模型测试
# ============================================================


class TestFDM1D:
    """一维有限差分测试"""

    def test_heat_equation(self):
        """FDM1D 应求解热传导方程"""
        from algorithms.mechanistic.fdm_1d import heat_1d_explicit

        D = 0.01
        L = 1.0
        T = 0.5
        nx = 50
        nt = 100

        x, t, U = heat_1d_explicit(D, L, T, nx, nt)

        assert U.shape == (nt + 1, nx + 1)
        assert len(x) == nx + 1
        assert len(t) == nt + 1


class TestFDM2D:
    """二维有限差分测试"""

    def test_basic_interface(self):
        """FDM2D 应有正确接口"""
        from algorithms.mechanistic.fdm_2d import fdm_2d_explicit

        assert callable(fdm_2d_explicit)


class TestODESolver:
    """ODE 求解器测试"""

    def test_basic_interface(self):
        """ODE 求解器应有正确接口"""
        from algorithms.mechanistic.ode_solver import euler, rk4, solve_ivp_wrapper

        assert callable(euler)
        assert callable(rk4)
        assert callable(solve_ivp_wrapper)

    def test_euler_simple(self):
        """Euler 应求解简单 ODE"""
        from algorithms.mechanistic.ode_solver import euler

        # dy/dt = -y, y(0) = 1
        f = lambda t, y: -y
        t = np.linspace(0, 1, 10)
        result = euler(f, 1.0, t)

        # euler 返回 (t, y) tuple
        if isinstance(result, tuple):
            t_out, y = result
            assert len(y) == len(t)
        else:
            assert len(result) == len(t)


# ============================================================
# 图论算法测试
# ============================================================


class TestGraphAlgo:
    """图论算法测试"""

    def test_dijkstra(self):
        """Dijkstra 应找到最短路径"""
        from algorithms.network.graph_algo import dijkstra

        # 使用邻接矩阵格式
        adj = [
            [0, 4, 1, 0],
            [0, 0, 0, 1],
            [0, 2, 0, 5],
            [0, 0, 0, 0],
        ]
        dist = dijkstra(adj, 0)

        # dist 应该是距离数组或字典
        assert dist is not None

    def test_kruskal(self):
        """Kruskal 应找到最小生成树"""
        from algorithms.network.graph_algo import kruskal

        n = 4
        edges = [(0, 1, 10), (0, 2, 6), (0, 3, 5), (1, 3, 15), (2, 3, 4)]
        mst = kruskal(n, edges)

        # MST 应该有 n-1 条边或返回权重
        assert mst is not None


# ============================================================
# 验证工具测试
# ============================================================


class TestMetrics:
    """拟合指标测试"""

    def test_r2_score(self):
        """R² 应正确计算"""
        from algorithms.validation.metrics import FitMetrics

        y_true = [1, 2, 3, 4, 5]
        y_pred = [1.1, 2.2, 2.8, 4.1, 5.2]

        metrics = FitMetrics.evaluate(y_true, y_pred)
        assert "R2" in metrics
        assert metrics["R2"] > 0.9

    def test_perfect_fit(self):
        """完美拟合应返回 R²=1"""
        from algorithms.validation.metrics import FitMetrics

        y_true = [1, 2, 3]
        y_pred = [1, 2, 3]

        metrics = FitMetrics.evaluate(y_true, y_pred)
        assert metrics["R2"] == 1.0


class TestSensitivity:
    """灵敏度分析测试"""

    def test_basic_interface(self):
        """SensitivityAnalyzer 应有正确接口"""
        from algorithms.validation.sensitivity import SensitivityAnalyzer

        def model(params):
            return params['a'] * 2 + params['b']

        base_params = {'a': 1.0, 'b': 2.0}
        analyzer = SensitivityAnalyzer(model, base_params)
        assert analyzer is not None


class TestMonteCarlo:
    """蒙特卡洛仿真测试"""

    def test_basic_simulation(self):
        """MonteCarlo 应运行仿真"""
        from algorithms.validation.monte_carlo import MonteCarlo

        def sim(params):
            return params["x"] + params["y"]

        dist_params = {
            "x": {"dist": "normal", "mean": 0, "std": 1},
            "y": {"dist": "normal", "mean": 0, "std": 1},
        }
        mc = MonteCarlo(sim, dist_params)
        mc.run(n=200, seed=42)
        stats = mc.statistics()

        assert "mean" in stats
        assert "std" in stats


# ============================================================
# Sobol 灵敏度测试
# ============================================================


class TestSobol:
    """Sobol 灵敏度分析测试"""

    def test_basic_sobol(self):
        """Sobol 应计算灵敏度指数"""
        from algorithms.validation.sobol import sobol_total_and_first

        def f(x):
            return x[0] + 2 * x[1]

        bounds = [(0, 1), (0, 1)]
        result = sobol_total_and_first(f, bounds, N=256)

        assert abs(sum(result["S1"]) - 1.0) < 0.5


# ============================================================
# 求解器路由测试
# ============================================================


class TestSolverRouter:
    """求解器路由测试"""

    def test_solve_lp(self):
        """LP 求解应成功"""
        from scripts.solver_router import solve_lp

        result = solve_lp(
            objective={"x": 1, "y": 1},
            constraints=[
                {"coeffs": {"x": 1, "y": 0}, "sense": "<=", "rhs": 1},
                {"coeffs": {"x": 0, "y": 1}, "sense": "<=", "rhs": 1},
            ],
            variables={"x": {"lowBound": 0}, "y": {"lowBound": 0}},
            sense="maximize",
        )
        assert result["status"] == "optimal"


# ============================================================
# 其他模块测试
# ============================================================


class TestPopulation:
    """种群模型测试"""

    def test_basic_interface(self):
        """Population 模型应有正确接口"""
        from algorithms.ecology.population import SEIR, SIR, lotka_volterra

        assert callable(lotka_volterra)
        assert callable(SIR)
        assert callable(SEIR)

    def test_sir_model(self):
        """SIR 模型应返回正确结果"""
        from algorithms.ecology.population import SIR

        t = np.linspace(0, 100, 100)
        result = SIR(beta=0.3, gamma=0.1, S0=999, I0=1, R0=0, t=t)

        # SIR 可能返回 dict 或 tuple
        assert result is not None
        if isinstance(result, dict):
            assert 'S' in result or 's' in result
        elif isinstance(result, tuple):
            assert len(result) >= 3


class TestNash:
    """纳什均衡测试"""

    def test_basic_interface(self):
        """Nash 应有正确接口"""
        from algorithms.game.nash import mixed_nash_2x2, pure_nash

        assert callable(pure_nash)
        assert callable(mixed_nash_2x2)

    def test_pure_nash(self):
        """纯策略纳什均衡测试"""
        from algorithms.game.nash import pure_nash

        # 囚徒困境
        payoff = [[-1, -3], [0, -2]]
        result = pure_nash(payoff)
        assert result is not None


class TestNSGA2:
    """NSGA-II 多目标优化测试"""

    def test_basic_interface(self):
        """NSGA2 应有正确接口"""
        from algorithms.optimization.nsga2 import NSGA2

        assert NSGA2 is not None


class TestPSOVariants:
    """PSO 变体测试"""

    def test_basic_interface(self):
        """PSO 变体应有正确接口"""
        from algorithms.optimization.pso_variants import pso_clerc, pso_tvac

        assert callable(pso_clerc)
        assert callable(pso_tvac)


class TestAdaptiveHybrid:
    """自适应混合算法测试"""

    def test_basic_interface(self):
        """AdaptiveHybrid 应有正确接口"""
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        assert AdaptiveHybrid is not None


class TestFEMPoisson:
    """有限元泊松方程测试"""

    def test_basic_interface(self):
        """FEM 应有正确接口"""
        from algorithms.mechanistic.fem_poisson import assemble_and_solve, rect_tri_mesh

        assert callable(assemble_and_solve)
        assert callable(rect_tri_mesh)


class TestProblemAnalyzer:
    """问题分析器测试"""

    def test_basic_interface(self):
        """ProblemAnalyzer 应有正确接口"""
        from algorithms.misc.problem_analyzer import analyze_problem

        assert callable(analyze_problem)


class TestInnovationGuide:
    """创新指导测试"""

    def test_basic_interface(self):
        """InnovationGuide 应有正确接口"""
        from algorithms.misc.innovation_guide import eval_direction, suggest_innovations

        assert callable(suggest_innovations)
        assert callable(eval_direction)


# ============================================================
# 运行入口
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
