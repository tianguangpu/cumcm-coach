"""algorithms/optimization/ 低覆盖模块补测 —— two_stage/job_shop/vrp/pso_variants。"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.optimization.two_stage import TwoStageSolver, FacilityLocationSolver


class TestTwoStageSolver:
    @pytest.fixture
    def small_problem(self):
        rng = np.random.default_rng(42)
        customers = rng.uniform(0, 100, (15, 2))
        demands = [1, 2, 1, 3, 2, 1, 2, 1, 3, 2, 1, 2, 1, 2, 1]
        return customers, demands

    def test_init_default(self):
        s = TwoStageSolver()
        assert s.problem_type == "facility_routing"

    def test_solve_facility_routing(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver(problem_type="facility_routing")
        r = s.solve(customers, demands, n_clusters=3, capacity=10)
        assert r["problem_type"] == "facility_routing"
        assert r["n_facilities"] == 3
        assert r["stage1"]["method"] == "K-Means聚类"

    def test_solve_clustering_scheduling(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver(problem_type="clustering_scheduling")
        r = s.solve(customers, demands, n_clusters=3)
        assert r["stage1"]["method"] == "层次聚类"

    def test_solve_partition_assignment(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver(problem_type="partition_assignment")
        r = s.solve(customers, demands, n_clusters=2)
        assert r["stage1"]["method"] == "贪心选址"

    def test_solve_with_distance_matrix(self, small_problem):
        from scipy.spatial.distance import cdist
        customers, demands = small_problem
        dm = cdist(customers, customers, metric="euclidean")
        s = TwoStageSolver()
        r = s.solve(customers, demands, n_clusters=2, distance_matrix=dm)
        assert r["n_facilities"] == 2

    def test_solve_verbose(self, small_problem, capsys):
        customers, demands = small_problem
        s = TwoStageSolver()
        s.solve(customers, demands, n_clusters=2, verbose=True)
        out = capsys.readouterr().out
        assert "第一阶段" in out

    def test_solve_no_capacity(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver()
        r = s.solve(customers, demands, n_clusters=2, capacity=None)
        assert "routes" in r["stage2"]

    def test_solve_total_cost(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver()
        r = s.solve(customers, demands, n_clusters=3, capacity=20)
        assert r["total_cost"] >= 0

    def test_kmeans_clustering_result(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver(problem_type="facility_routing")
        s.solve(customers, demands, n_clusters=4, capacity=20)
        assert len(s.stage1_result["clusters"]) == 4

    def test_greedy_facility_indices(self, small_problem):
        customers, demands = small_problem
        s = TwoStageSolver(problem_type="partition_assignment")
        r = s.solve(customers, demands, n_clusters=3)
        assert len(r["stage1"]["facility_indices"]) == 3


class TestFacilityLocationSolver:
    @pytest.fixture
    def setup(self):
        rng = np.random.default_rng(42)
        customers = rng.uniform(0, 100, (10, 2))
        demands = [1, 2, 1, 3, 2, 1, 2, 1, 3, 2]
        facilities = rng.uniform(0, 100, (5, 2))
        fixed_costs = [50, 80, 60, 100, 70]
        return customers, demands, facilities, fixed_costs

    def test_init_auto_transport(self, setup):
        customers, demands, facilities, fixed_costs = setup
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        assert solver.transport_costs.shape == (10, 5)

    def test_init_custom_transport(self, setup):
        customers, demands, facilities, fixed_costs = setup
        tc = np.ones((10, 5)) * 10
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs, tc)
        assert np.all(solver.transport_costs == 10)

    def test_solve_greedy_default(self, setup):
        customers, demands, facilities, fixed_costs = setup
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        r = solver.solve_greedy()
        assert r["method"] == "贪心选址"
        assert len(r["selected_facilities"]) <= 5

    def test_solve_greedy_max_facilities(self, setup):
        customers, demands, facilities, fixed_costs = setup
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        r = solver.solve_greedy(max_facilities=2)
        assert r["n_facilities"] <= 2

    def test_solve_p_median_small(self, setup):
        customers, demands, facilities, fixed_costs = setup
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        r = solver.solve_p_median(p=2)
        assert r["n_facilities"] == 2

    def test_solve_p_median_large_falls_back(self):
        rng = np.random.default_rng(0)
        customers = rng.uniform(0, 100, (8, 2))
        demands = [1] * 8
        facilities = rng.uniform(0, 100, (20, 2))
        fixed_costs = list(range(20, 40))
        solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
        r = solver.solve_p_median(p=3)
        assert r["method"] == "贪心选址"


class TestPSOVariants:
    def test_clerc_constriction(self):
        from algorithms.optimization.pso_variants import clerc_constriction
        chi, c1, c2 = clerc_constriction(2.05, 2.05)
        assert chi == pytest.approx(0.7298, abs=0.01)

    def test_clerc_constriction_raises(self):
        from algorithms.optimization.pso_variants import clerc_constriction
        with pytest.raises(ValueError, match="Clerc 要求"):
            clerc_constriction(1.0, 1.0)

    def test_pso_clerc_sphere(self):
        from algorithms.optimization.pso_variants import pso_clerc
        def sphere(x):
            return float(np.sum(x ** 2))
        r = pso_clerc(sphere, dim=3, bounds=[(-5, 5)] * 3, iters=50, swarms=20, seed=42)
        assert r["g_val"] < 1.0

    def test_pso_clerc_repair(self):
        from algorithms.optimization.pso_variants import pso_clerc
        def sphere(x):
            return float(np.sum(x ** 2))
        def repair(x):
            return np.clip(x, -2, 2)
        r = pso_clerc(sphere, dim=2, bounds=[(-5, 5)] * 2, iters=30, swarms=10, seed=42, repair=repair)
        assert r["g_val"] < 5.0

    def test_pso_clerc_return_keys(self):
        from algorithms.optimization.pso_variants import pso_clerc
        def sphere(x):
            return float(np.sum(x ** 2))
        r = pso_clerc(sphere, dim=2, bounds=[(-5, 5)] * 2, iters=10, swarms=5, seed=42)
        assert {"g_best", "g_val", "history", "variant", "chi"} <= set(r.keys())
        assert r["variant"] == "clerc"
        assert len(r["history"]) == 10
