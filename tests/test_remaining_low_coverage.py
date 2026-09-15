"""剩余低覆盖模块的批量测试。

覆盖:
  - mechanistic: de_quickref / ode_solver / fdm_1d / fem_poisson
  - network: graph_algo
  - base: BaseSolver / SolverResult / PopulationBasedSolver / GradientBasedSolver
  - misc: innovation_guide
  - evaluation: ahp_entropy_topsis
  - optimization: sa_pso / de / ga
  - validation: shap_analysis (无 shap 时的分支)
"""
import os
import warnings

import numpy as np
import pandas as pd
import pytest

# ============= mechanistic.de_quickref =============

class TestDeQuickref:
    def test_query_known(self):
        from algorithms.mechanistic.de_quickref import query, DE_QUICKREF
        info = query("parabolic_explicit")
        assert info["type"] == "抛物线 PDE"
        assert "method" in info
        assert info is DE_QUICKREF["parabolic_explicit"]

    def test_query_all_keys(self):
        from algorithms.mechanistic.de_quickref import query, DE_QUICKREF
        for k in DE_QUICKREF:
            info = query(k)
            assert "type" in info
            assert "stability" in info

    def test_query_unknown_raises(self):
        from algorithms.mechanistic.de_quickref import query
        with pytest.raises(ValueError, match="未知方法"):
            query("nonexistent_method")


# ============= mechanistic.ode_solver =============

class TestODESolver:
    def test_euler_scalar(self):
        from algorithms.mechanistic.ode_solver import euler
        t = np.linspace(0, 1, 11)
        ts, y = euler(lambda ti, yy: -yy, 1.0, t)
        assert len(y) == 11
        assert y[0] == pytest.approx(1.0)
        # y(1) 近似 exp(-1) = 0.3679
        assert 0.3 < y[-1] < 0.5

    def test_euler_vector(self):
        from algorithms.mechanistic.ode_solver import euler
        t = np.linspace(0, 1, 11)
        ts, Y = euler(lambda ti, yy: np.array([-yy[0], yy[1]]),
                       np.array([1.0, 0.5]), t)
        assert Y.shape == (11, 2)
        assert Y[0, 0] == pytest.approx(1.0)

    def test_rk4_scalar(self):
        from algorithms.mechanistic.ode_solver import rk4
        t = np.linspace(0, 2, 20)
        ts, y = rk4(lambda ti, yy: -yy, 1.0, t)
        # RK4 精度高, y(2) 接近 exp(-2) = 0.1353
        assert abs(y[-1] - np.exp(-2)) < 1e-4

    def test_rk4_vector(self):
        from algorithms.mechanistic.ode_solver import rk4
        t = np.linspace(0, 1, 11)
        ts, Y = rk4(lambda ti, yy: np.array([yy[1], -yy[0]]),
                     np.array([1.0, 0.0]), t)
        assert Y.shape == (11, 2)

    def test_solve_ivp_wrapper_scalar(self):
        from algorithms.mechanistic.ode_solver import solve_ivp_wrapper
        ts, y = solve_ivp_wrapper(lambda t, yy: -yy, 1.0, (0, 2),
                                   t_eval=np.linspace(0, 2, 11))
        assert len(y) == 11
        assert abs(y[-1] - np.exp(-2)) < 1e-3

    def test_solve_ivp_wrapper_vector(self):
        from algorithms.mechanistic.ode_solver import solve_ivp_wrapper
        ts, Y = solve_ivp_wrapper(lambda t, yy: np.array([yy[1], -yy[0]]),
                                   np.array([1.0, 0.0]), (0, 1))
        # Y shape: (dim, n_t); dim=2
        assert Y.shape[0] == 2
        assert len(Y.shape) == 2

    def test_coerce(self):
        from algorithms.mechanistic.ode_solver import _coerce
        arr, is_scalar = _coerce(1.0)
        assert is_scalar is True
        assert arr.shape == (1,)
        arr2, is_scalar2 = _coerce(np.array([1.0, 2.0]))
        assert is_scalar2 is False
        assert arr2.shape == (2,)


# ============= mechanistic.fdm_1d =============

class TestFDM1D:
    def test_basic_heat(self):
        from algorithms.mechanistic.fdm_1d import heat_1d_explicit
        x, t, U = heat_1d_explicit(0.1, 1.0, 0.5, nx=20, nt=200,
                                    u0=lambda x: np.sin(np.pi * x))
        assert len(x) == 21
        assert len(t) == 201
        assert U.shape == (201, 21)
        # t=0 应是 sin(pi*x)
        assert abs(U[0].max() - 1.0) < 1e-3

    def test_with_source(self):
        from algorithms.mechanistic.fdm_1d import heat_1d_explicit
        x, t, U = heat_1d_explicit(0.05, 1.0, 0.1, nx=20, nt=200,
                                    f=lambda x, tt: 1.0)
        assert U.shape == (201, 21)

    def test_unstable_raises(self):
        from algorithms.mechanistic.fdm_1d import heat_1d_explicit
        # r = D*dt/dx^2 > 0.5
        with pytest.raises(ValueError, match="不稳定"):
            heat_1d_explicit(1.0, 1.0, 0.5, nx=10, nt=1)

    def test_with_bc(self):
        from algorithms.mechanistic.fdm_1d import heat_1d_explicit
        x, t, U = heat_1d_explicit(0.05, 1.0, 0.1, nx=10, nt=50,
                                    u0=lambda x: np.ones_like(x),
                                    bc=(0.0, 0.0))
        # 边界条件保持
        assert U[-1, 0] == 0.0
        assert U[-1, -1] == 0.0


# ============= mechanistic.fem_poisson =============

class TestFEMPoisson:
    def test_rect_tri_mesh(self):
        from algorithms.mechanistic.fem_poisson import rect_tri_mesh
        nodes, elements = rect_tri_mesh(2, 2)
        assert nodes.shape == (9, 2)
        assert len(elements) == 8  # 2*nx*ny = 2*2*2

    def test_shape_data(self):
        from algorithms.mechanistic.fem_poisson import _shape_data
        # 单位三角形
        p = np.array([[0, 0], [1, 0], [0, 1]], float)
        area, grads = _shape_data(p)
        assert abs(area - 0.5) < 1e-10
        assert grads.shape == (3, 2)

    def test_coerce_mesh_tuple(self):
        from algorithms.mechanistic.fem_poisson import _coerce_mesh
        nodes = np.array([[0, 0], [1, 0], [0, 1]], float)
        elements = [[0, 1, 2]]
        n, e = _coerce_mesh((nodes, elements))
        assert np.array_equal(n, nodes)
        assert e == elements

    def test_coerce_mesh_list(self):
        from algorithms.mechanistic.fem_poisson import _coerce_mesh
        mesh = [[[0, 0], [1, 0], [0, 1]]]
        n, e = _coerce_mesh(mesh)
        assert n.shape == (3, 2)
        assert e == [[0, 1, 2]]

    def test_assemble_and_solve_basic(self):
        from algorithms.mechanistic.fem_poisson import assemble_and_solve, rect_tri_mesh
        nodes, elements = rect_tri_mesh(3, 3)
        u, n, e = assemble_and_solve((nodes, elements),
                                      f_func=lambda x, y: 1.0,
                                      k_func=1.0,
                                      dirichlet={0: 0.0})
        assert len(u) == len(nodes)
        assert u[0] == 0.0

    def test_assemble_with_k_function(self):
        from algorithms.mechanistic.fem_poisson import assemble_and_solve, rect_tri_mesh
        nodes, elements = rect_tri_mesh(2, 2)
        u, _, _ = assemble_and_solve((nodes, elements),
                                      f_func=lambda x, y: 1.0,
                                      k_func=lambda x, y: 2.0)
        assert len(u) == len(nodes)


# ============= network.graph_algo =============

class TestGraphAlgo:
    def test_dijkstra_simple(self):
        from algorithms.network.graph_algo import dijkstra
        adj = [[0, 2, -1, 5], [2, 0, 1, 4], [-1, 1, 0, 1], [5, 4, 1, 0]]
        dist, prev = dijkstra(adj, 0)
        assert dist[0] == 0
        assert dist[1] == 2
        assert dist[2] == 3
        assert dist[3] == 4

    def test_dijkstra_disconnected(self):
        from algorithms.network.graph_algo import dijkstra
        # 不连通
        adj = [[0, -1], [-1, 0]]
        dist, prev = dijkstra(adj, 0)
        assert dist[1] == float("inf")

    def test_kruskal_basic(self):
        from algorithms.network.graph_algo import kruskal
        edges = [(0, 1, 2), (0, 3, 5), (1, 2, 1), (1, 3, 4), (2, 3, 1)]
        mst, total = kruskal(4, edges)
        # MST: (1,2,1), (2,3,1), (0,1,2) 总权 4
        assert total == 4
        assert len(mst) == 3

    def test_kruskal_empty(self):
        from algorithms.network.graph_algo import kruskal
        mst, total = kruskal(0, [])
        assert mst == []
        assert total == 0

    def test_max_flow_basic(self):
        from algorithms.network.graph_algo import max_flow
        cap = [[0, 16, 13, 0, 0, 0], [0, 0, 0, 12, 0, 0], [0, 4, 0, 0, 14, 0],
               [0, 0, 9, 0, 0, 20], [0, 0, 0, 7, 0, 4], [0, 0, 0, 0, 0, 0]]
        total, flow = max_flow(cap, 0, 5)
        assert total == 23  # 经典示例最大流=23

    def test_max_flow_no_path(self):
        from algorithms.network.graph_algo import max_flow
        cap = [[0, 0], [0, 0]]
        total, _ = max_flow(cap, 0, 1)
        assert total == 0


# ============= base =============

class TestSolverResult:
    def test_default(self):
        from algorithms.base import SolverResult
        r = SolverResult()
        assert r.f_opt == float("inf")
        assert r.metadata == {}  # post_init
        assert r.history is None

    def test_to_dict(self):
        from algorithms.base import SolverResult
        r = SolverResult(x_opt=np.array([1.0, 2.0]), f_opt=0.5,
                          iterations=100, convergence=True)
        d = r.to_dict()
        assert d["x_opt"] == [1.0, 2.0]  # ndarray -> list
        assert d["f_opt"] == 0.5
        assert d["iterations"] == 100

    def test_to_dict_scalar_x(self):
        from algorithms.base import SolverResult
        r = SolverResult(x_opt=[1.0, 2.0, 3.0])
        d = r.to_dict()
        assert d["x_opt"] == [1.0, 2.0, 3.0]

    def test_summary_short_x(self):
        from algorithms.base import SolverResult
        r = SolverResult(x_opt=[1.0], f_opt=0.5, iterations=100,
                          convergence=True, solve_time=0.5, solver_name="Test")
        s = r.summary()
        assert "Test" in s
        assert "0.500000" in s

    def test_summary_long_x(self):
        from algorithms.base import SolverResult
        # 长解触发截断分支
        long_x = list(range(100))
        r = SolverResult(x_opt=long_x)
        s = r.summary()
        assert "..." in s

    def test_summary_no_x(self):
        from algorithms.base import SolverResult
        r = SolverResult()
        s = r.summary()
        assert "Solver" in s


class TestBaseSolver:
    def test_concrete_subclass(self):
        from algorithms.base import BaseSolver, SolverResult
        class MySolver(BaseSolver):
            name = "MySolver"
            def solve(self, objective, bounds, **kwargs):
                self._record(0.5)
                return SolverResult(x_opt=[0.0], f_opt=0.5,
                                     iterations=1, convergence=True)
            def validate_params(self):
                return True

        s = MySolver(param1=1, param2=2)
        assert s.params == {"param1": 1, "param2": 2}
        assert s.name == "MySolver"
        assert "MySolver" in repr(s)
        assert s.get_history() == []

        result = s.solve(None, None)
        assert result.f_opt == 0.5
        assert s.get_history() == [0.5]

        s.clear_history()
        assert s.get_history() == []

    def test_population_based_solver(self):
        from algorithms.base import PopulationBasedSolver
        class MyPopSolver(PopulationBasedSolver):
            name = "MyPopSolver"
            def solve(self, objective, bounds, **kwargs):
                pop = self._init_population(bounds)
                return pop
            def validate_params(self):
                return super().validate_params()

        s = MyPopSolver(pop_size=10, max_iter=50)
        assert s.pop_size == 10
        assert s.max_iter == 50
        assert s.validate_params() is True

        # _init_population
        bounds = [(-1.0, 1.0), (0.0, 2.0)]
        pop = s.solve(None, bounds)
        assert pop.shape == (10, 2)
        assert s.dim == 2

        # _clip_bounds
        x = np.array([1.5, -0.5])
        clipped = s._clip_bounds(x, bounds)
        assert clipped[0] == 1.0
        assert clipped[1] == 0.0

    def test_population_invalid_params(self):
        from algorithms.base import PopulationBasedSolver
        class MyPop(PopulationBasedSolver):
            def solve(self, *a, **k): pass
        # pop_size<=0 在 validate_params 中抛错
        s_bad = MyPop(pop_size=0, max_iter=10)
        with pytest.raises(ValueError, match="pop_size"):
            s_bad.validate_params()
        s_bad2 = MyPop(pop_size=10, max_iter=0)
        with pytest.raises(ValueError, match="max_iter"):
            s_bad2.validate_params()

    def test_gradient_solver(self):
        from algorithms.base import GradientBasedSolver
        class MyGrad(GradientBasedSolver):
            name = "MyGrad"
            def solve(self, *a, **k):
                return self._numerical_gradient(lambda x: float(np.sum(x**2)),
                                                 np.array([1.0, 2.0]))
            def validate_params(self):
                return super().validate_params()

        s = MyGrad(learning_rate=0.01, tolerance=1e-6)
        assert s.learning_rate == 0.01
        assert s.validate_params() is True

        grad = s.solve(None, None)
        assert grad.shape == (2,)
        # d/dx (x^2+y^2) at (1,2) = (2,4)
        assert abs(grad[0] - 2.0) < 1e-4
        assert abs(grad[1] - 4.0) < 1e-4

    def test_gradient_invalid_params(self):
        from algorithms.base import GradientBasedSolver
        class MyGrad(GradientBasedSolver):
            def solve(self, *a, **k): pass
        # 参数校验在 validate_params, 不在 __init__
        s_bad = MyGrad(learning_rate=0, tolerance=1e-6)
        with pytest.raises(ValueError, match="learning_rate"):
            s_bad.validate_params()
        s_bad2 = MyGrad(learning_rate=0.01, tolerance=0)
        with pytest.raises(ValueError, match="tolerance"):
            s_bad2.validate_params()


# ============= misc.innovation_guide =============

class TestInnovationGuide:
    def test_suggest_innovations_b(self):
        from algorithms.misc.innovation_guide import suggest_innovations
        plan = suggest_innovations(problem_type="B")
        assert "categories" in plan
        assert len(plan["categories"]) == 5
        assert "concrete_directions" in plan
        assert len(plan["concrete_directions"]) <= 5
        assert "strong_baselines" in plan
        assert isinstance(plan["anti_cheat_check"], list)

    def test_suggest_innovations_all_types(self):
        from algorithms.misc.innovation_guide import suggest_innovations
        for pt in ["A", "B", "C", "D"]:
            plan = suggest_innovations(problem_type=pt)
            assert len(plan["concrete_directions"]) >= 1

    def test_suggest_innovations_unknown_type_falls_back(self):
        from algorithms.misc.innovation_guide import suggest_innovations
        plan = suggest_innovations(problem_type="Z")  # 未知, 回退到 B
        assert len(plan["concrete_directions"]) >= 1

    def test_suggest_innovations_with_text(self):
        from algorithms.misc.innovation_guide import suggest_innovations
        plan = suggest_innovations(problem_type="A", problem_text="PDE diffusive")
        assert "source" in plan
        assert "matched=True" in plan["source"]

    def test_eval_direction_valid(self):
        from algorithms.misc.innovation_guide import eval_direction
        d = {"dir": "x", "why": "y", "evidence": "e"}
        r = eval_direction(d, category="algorithm")
        assert r["valid"] is True

    def test_eval_direction_invalid_missing_key(self):
        from algorithms.misc.innovation_guide import eval_direction
        d = {"dir": "x", "why": "y"}  # 缺 evidence
        r = eval_direction(d)
        assert r["valid"] is False
        assert "hint" in r

    def test_eval_direction_unknown_category(self):
        from algorithms.misc.innovation_guide import eval_direction
        d = {"dir": "x", "why": "y", "evidence": "e"}
        r = eval_direction(d, category="unknown_cat")
        assert r["evidence_benchmark"] == "证据链"


# ============= evaluation.ahp_entropy_topsis =============

class TestComprehensiveEvaluation:
    @pytest.fixture
    def ce_basic(self):
        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation
        data = np.array([
            [85, 90, 78, 92, 88],
            [90, 85, 82, 88, 90],
            [78, 92, 85, 90, 85],
            [88, 88, 80, 85, 92],
        ])
        return ComprehensiveEvaluation(data, benefit_cols=[0, 1, 2, 3, 4],
                                        cost_cols=[], col_names=["A", "B", "C", "D", "E"])

    def test_init(self, ce_basic):
        assert ce_basic.n_samples == 4
        assert ce_basic.n_features == 5
        assert ce_basic.weights_ahp is None

    def test_normalize(self, ce_basic):
        n = ce_basic.normalize()
        assert n.shape == (4, 5)
        # 效益型: 标准化后 [0,1]
        assert 0 <= n.min() and n.max() <= 1.0 + 1e-9

    def test_normalize_cost_cols(self):
        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation
        data = np.array([[1.0, 10.0], [5.0, 5.0], [10.0, 1.0]])
        ce = ComprehensiveEvaluation(data, benefit_cols=[0], cost_cols=[1])
        n = ce.normalize()
        # 成本型: 值越小 -> 标准化值越大
        # col 1: [10, 5, 1] -> normalized: [0, 0.555, 1]
        assert n[2, 1] > n[0, 1]
        assert n[2, 1] == pytest.approx(1.0, abs=1e-6)

    def test_run_ahp(self, ce_basic):
        # 一致判断矩阵
        A = np.array([
            [1, 1, 3, 1, 1/3],
            [1, 1, 3, 1, 1/3],
            [1/3, 1/3, 1, 1/3, 1/5],
            [1, 1, 3, 1, 1/3],
            [3, 3, 5, 3, 1],
        ])
        w = ce_basic.run_ahp(A)
        assert w.shape == (5,)
        assert abs(w.sum() - 1.0) < 1e-6
        assert ce_basic.cr is not None

    def test_run_entropy(self, ce_basic):
        w = ce_basic.run_entropy()
        assert w.shape == (5,)
        assert abs(w.sum() - 1.0) < 1e-6

    def test_combine_weights_before_run_raises(self, ce_basic):
        with pytest.raises(ValueError, match="请先运行"):
            ce_basic.combine_weights()

    def test_combine_weights(self, ce_basic):
        ce_basic.run_entropy()
        # 直接给 AHP 权重(不走 run_ahp 路径)
        ce_basic.weights_ahp = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        w = ce_basic.combine_weights(alpha=0.5)
        assert w.shape == (5,)
        assert abs(w.sum() - 1.0) < 1e-6

    def test_topsis_no_weights_auto_entropy(self, ce_basic):
        scores = ce_basic.topsis()
        assert scores.shape == (4,)
        assert np.all((scores >= 0) & (scores <= 1))

    def test_topsis_with_explicit_weights(self, ce_basic):
        w = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        scores = ce_basic.topsis(weights=w)
        assert scores.shape == (4,)

    def test_topsis_with_combined(self, ce_basic):
        ce_basic.run_entropy()
        ce_basic.weights_ahp = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        ce_basic.combine_weights(alpha=0.5)
        scores = ce_basic.topsis()
        assert scores.shape == (4,)

    def test_topsis_with_ahp_only(self, ce_basic):
        ce_basic.weights_ahp = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        scores = ce_basic.topsis()
        assert scores.shape == (4,)

    def test_topsis_with_entropy_only(self, ce_basic):
        ce_basic.run_entropy()
        scores = ce_basic.topsis()
        assert scores.shape == (4,)

    def test_plot_weights(self, ce_basic, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        ce_basic.run_entropy()
        ce_basic.weights_ahp = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        ce_basic.combine_weights(alpha=0.5)
        p = str(tmp_path / "w.png")
        ce_basic.plot_weights(save_path=p)
        assert os.path.exists(p)

    def test_plot_radar(self, ce_basic, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        scores = ce_basic.topsis()
        p = str(tmp_path / "r.png")
        ce_basic.plot_radar(scores, save_path=p)
        assert os.path.exists(p)


# ============= optimization.sa_pso =============

class TestSAPSO:
    def test_init_basic(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=10, T_max=10, seed=42)
        assert s.N == 10
        assert s.X.shape == (10, 2)
        assert s.gbest.shape == (2,)

    def test_init_with_repair(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        def repair(x): return np.clip(x, -3, 3)
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=5, T_max=2,
                    repair=repair, seed=42)
        assert s.X.shape == (5, 2)
        assert np.all(s.X >= -3) and np.all(s.X <= 3)

    def test_is_feasible(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return 0.0
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=4, seed=42)
        assert bool(s.is_feasible(np.array([0.0, 0.0]))) is True
        assert bool(s.is_feasible(np.array([10.0, 0.0]))) is False

    def test_is_feasible_with_constraints(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return 0.0
        def constr(x): return x[0] + x[1] <= 5
        s = SA_PSO(obj, dim=2, bounds=[(-10, 10)] * 2, N=4,
                    constraints=constr, seed=42)
        assert bool(s.is_feasible(np.array([2.0, 2.0]))) is True
        assert bool(s.is_feasible(np.array([4.0, 4.0]))) is False

    def test_penalty(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return 0.0
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=4, seed=42)
        assert s.penalty(np.array([0.0, 0.0])) == 0.0
        assert s.penalty(np.array([10.0, 0.0])) > 0

    def test_fitness_with_repair(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        def repair(x): return np.clip(x, -3, 3)
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=4, repair=repair, seed=42)
        # 有 repair -> 直接返回 obj
        v = s.fitness(np.array([2.0, 2.0]))
        assert v == 8.0

    def test_metropolis_accept_better(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return 0.0
        s = SA_PSO(obj, dim=1, bounds=[(-5, 5)], N=2, seed=42)
        # new < old -> True
        assert s.metropolis_accept(10.0, 5.0, 100.0) is True

    def test_metropolis_accept_worse_with_high_temp(self):
        np.random.seed(0)
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return 0.0
        s = SA_PSO(obj, dim=1, bounds=[(-5, 5)], N=2, seed=42)
        # 高温下接受劣解的概率高, 多次至少有一次接受
        accepts = [bool(s.metropolis_accept(0.0, 0.001, 1000.0)) for _ in range(20)]
        assert any(accepts)  # 至少一次接受

    def test_solve_small(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=8, T_max=5, seed=42)
        r = s.solve(verbose=False)
        assert r["iterations"] == 5
        assert r["f_opt"] >= 0
        assert r["x_opt"].shape == (2,)
        assert len(r["history"]) == 5

    def test_solve_with_constraint_warns(self):
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        def constr(x): return x[0] + x[1] <= 0.1
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=5, T_max=3,
                    constraints=constr, seed=42)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            r = s.solve(verbose=False)
        assert "x_opt" in r

    def test_plot_convergence(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        from algorithms.optimization.sa_pso import SA_PSO
        def obj(x): return float(np.sum(x**2))
        s = SA_PSO(obj, dim=2, bounds=[(-5, 5)] * 2, N=4, T_max=3, seed=42)
        s.solve(verbose=False)
        p = str(tmp_path / "sa.png")
        s.plot_convergence(save_path=p)
        assert os.path.exists(p)


# ============= optimization.de =============

class TestDE:
    def test_init_basic(self):
        from algorithms.optimization.de import DE
        def obj(x): return float(np.sum(x**2))
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=10, seed=42)
        assert d.pop_size == 10
        assert d.pop.shape == (10, 2)

    def test_init_too_small_pop(self):
        from algorithms.optimization.de import DE
        def obj(x): return 0.0
        with pytest.raises(ValueError, match="至少为 4"):
            DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=3)

    def test_is_feasible_penalty(self):
        from algorithms.optimization.de import DE
        def obj(x): return 0.0
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, seed=42)
        assert bool(d.is_feasible(np.array([0.0, 0.0]))) is True
        assert bool(d.is_feasible(np.array([10.0, 0.0]))) is False
        assert d.penalty(np.array([0.0, 0.0])) == 0.0
        assert d.penalty(np.array([10.0, 0.0])) > 0

    def test_fitness(self):
        from algorithms.optimization.de import DE
        def obj(x): return float(np.sum(x**2))
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, seed=42)
        # 可行解 -> fitness = obj
        assert d.fitness(np.array([2.0, 2.0])) == 8.0
        # 不可行 -> obj + penalty
        assert d.fitness(np.array([10.0, 0.0])) > 0

    def test_mutate(self):
        from algorithms.optimization.de import DE
        def obj(x): return 0.0
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=5, seed=42)
        mutant = d._mutate(0)
        assert mutant.shape == (2,)

    def test_crossover(self):
        from algorithms.optimization.de import DE
        def obj(x): return 0.0
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, CR=0.5, seed=42)
        target = np.array([1.0, 1.0])
        mutant = np.array([2.0, 3.0])
        child = d._crossover(target, mutant)
        assert child.shape == (2,)

    def test_bound(self):
        from algorithms.optimization.de import DE
        def obj(x): return 0.0
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, seed=42)
        out = d._bound(np.array([10.0, -10.0]))
        assert out[0] <= 5
        assert out[1] >= -5

    def test_solve_small(self):
        from algorithms.optimization.de import DE
        def obj(x): return float(np.sum(x**2))
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=8, max_gen=5, seed=42)
        r = d.solve(verbose=False)
        assert r["iterations"] == 5
        assert r["f_opt"] >= 0
        assert len(r["history"]) == 5

    def test_plot_convergence(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        from algorithms.optimization.de import DE
        def obj(x): return float(np.sum(x**2))
        d = DE(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, max_gen=3, seed=42)
        d.solve(verbose=False)
        p = str(tmp_path / "de.png")
        d.plot_convergence(save_path=p)
        assert os.path.exists(p)


# ============= optimization.ga =============

class TestGA:
    def test_init_basic(self):
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=10, seed=42)
        assert g.pop_size == 10
        assert g.pop.shape == (10, 2)

    def test_is_feasible_penalty_fitness(self):
        from algorithms.optimization.ga import GA
        def obj(x): return 0.0
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, seed=42)
        assert bool(g.is_feasible(np.array([0.0, 0.0]))) is True
        assert bool(g.is_feasible(np.array([10.0, 0.0]))) is False
        assert g.penalty(np.array([0.0, 0.0])) == 0.0

    def test_fitness_with_repair(self):
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        def repair(x): return np.clip(x, -3, 3)
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, repair=repair, seed=42)
        # repair 模式下 fitness = obj
        assert g.fitness(np.array([2.0, 2.0])) == 8.0

    def test_tournament_select(self):
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=10, seed=42)
        sel = g._tournament_select()
        assert sel.shape == (2,)

    def test_crossover(self):
        from algorithms.optimization.ga import GA
        def obj(x): return 0.0
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, pc=0.8, seed=42)
        p1 = np.array([1.0, 2.0]); p2 = np.array([3.0, 4.0])
        c1, c2 = g._crossover(p1, p2)
        assert c1.shape == (2,)
        assert c2.shape == (2,)

    def test_crossover_no_crossover(self):
        from algorithms.optimization.ga import GA
        def obj(x): return 0.0
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, pc=0.0, seed=42)
        p1 = np.array([1.0, 2.0]); p2 = np.array([3.0, 4.0])
        c1, c2 = g._crossover(p1, p2)
        # pc=0 -> 直接复制父代
        assert np.allclose(c1, p1)
        assert np.allclose(c2, p2)

    def test_mutate(self):
        from algorithms.optimization.ga import GA
        def obj(x): return 0.0
        g = GA(obj, dim=3, bounds=[(-5, 5)] * 3, pop_size=4, pm=1.0, seed=42)
        x = np.array([1.0, 1.0, 1.0])
        m = g._mutate(x.copy())
        assert m.shape == (3,)
        # pm=1 -> 至少有一个变异
        assert not np.allclose(m, np.array([1.0, 1.0, 1.0]))

    def test_bound(self):
        from algorithms.optimization.ga import GA
        def obj(x): return 0.0
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, seed=42)
        out = g._bound(np.array([10.0, -10.0]))
        assert out[0] <= 5
        assert out[1] >= -5

    def test_solve_small(self):
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=8, max_gen=5, seed=42)
        r = g.solve(verbose=False)
        assert r["iterations"] == 5
        assert r["f_opt"] >= 0
        assert len(r["history"]) == 5

    def test_solve_with_repair_constraint_warns(self):
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        def constr(x): return x[0] + x[1] <= 0.1
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=5, max_gen=3,
                constraints=constr, seed=42)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            r = g.solve(verbose=False)
        assert "x_opt" in r

    def test_plot_convergence(self, tmp_path):
        import matplotlib
        matplotlib.use("Agg")
        from algorithms.optimization.ga import GA
        def obj(x): return float(np.sum(x**2))
        g = GA(obj, dim=2, bounds=[(-5, 5)] * 2, pop_size=4, max_gen=3, seed=42)
        g.solve(verbose=False)
        p = str(tmp_path / "ga.png")
        g.plot_convergence(save_path=p)
        assert os.path.exists(p)


# ============= validation.shap_analysis (无 shap 时的分支) =============

class TestSHAPAnalyzerNoShap:
    """shap 未安装时,fit 会抛 RuntimeError;但仍可测 _detect_model_type
    以及手动注入 fitted/shap_values 后的 plot_top_features / generate_report。"""

    def _make_analyzer(self):
        from algorithms.validation.shap_analysis import SHAPAnalyzer
        # 用一个 fake model
        class FakeModel:
            pass
        return SHAPAnalyzer(FakeModel(),
                            X_train=np.random.rand(20, 3),
                            X_test=np.random.rand(10, 3),
                            feature_names=["a", "b", "c"])

    def test_init(self):
        a = self._make_analyzer()
        assert a.fitted is False
        assert len(a.feature_names) == 3
        assert a.X_train.shape == (20, 3)

    def test_fit_raises_without_shap(self):
        from algorithms.validation.shap_analysis import HAS_SHAP
        a = self._make_analyzer()
        if not HAS_SHAP:
            with pytest.raises(RuntimeError, match="请安装 shap"):
                a.fit()

    def test_detect_model_type_tree(self):
        a = self._make_analyzer()
        class RandomForestRegressor: pass
        a.model = RandomForestRegressor()
        assert a._detect_model_type() == "tree"

    def test_detect_model_type_linear(self):
        a = self._make_analyzer()
        class LinearRegression: pass
        a.model = LinearRegression()
        assert a._detect_model_type() == "linear"

    def test_detect_model_type_deep(self):
        a = self._make_analyzer()
        class Sequential: pass
        a.model = Sequential()
        assert a._detect_model_type() == "deep"

    def test_detect_model_type_kernel(self):
        a = self._make_analyzer()
        class FooBar: pass
        a.model = FooBar()
        assert a._detect_model_type() == "kernel"

    def test_get_feature_importance_before_fit_raises(self):
        a = self._make_analyzer()
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            a.get_feature_importance()

    def test_plot_summary_before_fit_returns_none(self):
        a = self._make_analyzer()
        assert a.plot_summary() is None

    def test_plot_waterfall_before_fit_returns_none(self):
        a = self._make_analyzer()
        assert a.plot_waterfall() is None

    def test_plot_bar_before_fit_returns_none(self):
        a = self._make_analyzer()
        assert a.plot_bar() is None

    def test_plot_dependence_before_fit_returns_none(self):
        a = self._make_analyzer()
        assert a.plot_dependence("a") is None

    def test_generate_report_before_fit_raises(self):
        a = self._make_analyzer()
        with pytest.raises(RuntimeError, match="请先调用 fit"):
            a.generate_report()

    def test_plot_top_features_with_manual_fit(self, tmp_path):
        # 手动注入 fitted + shap_values,跳过 fit 调用
        a = self._make_analyzer()
        a.fitted = True
        a.shap_values = np.random.normal(0, 1, (10, 3))
        p = str(tmp_path / "top.png")
        a.plot_top_features(save_path=p)
        assert os.path.exists(p)
        # pdf 也生成
        assert os.path.exists(p.replace(".png", ".pdf"))

    def test_get_feature_importance_with_manual_fit(self):
        a = self._make_analyzer()
        a.fitted = True
        a.shap_values = np.array([[0.1, 0.5, 0.2], [0.3, 0.1, 0.4]])
        df = a.get_feature_importance()
        assert "feature" in df.columns
        assert "importance" in df.columns
        assert len(df) == 3
        # 应按重要性降序
        assert df["importance"].iloc[0] >= df["importance"].iloc[-1]

    def test_generate_report_with_manual_fit(self):
        a = self._make_analyzer()
        a.fitted = True
        a.model_type = "tree"
        a.shap_values = np.random.normal(0, 1, (10, 3))
        report = a.generate_report()
        assert "SHAP 可解释性分析报告" in report
        assert "Top-5 特征重要性" in report
