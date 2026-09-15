"""algorithms/optimization/ 低覆盖模块补测 II —— vrp/job_shop。"""
import os
import random
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.optimization.vrp import VRP
from algorithms.optimization.job_shop import JobShopScheduler


class TestVRP:
    @pytest.fixture
    def small_vrp(self):
        rng = np.random.default_rng(42)
        n = 6
        dm = rng.uniform(5, 50, (n, n))
        dm = (dm + dm.T) / 2
        np.fill_diagonal(dm, 0)
        demands = [0, 3, 4, 2, 5, 3]
        return VRP(dm, demands, capacity=8, n_vehicles=2)

    def test_init(self, small_vrp):
        assert small_vrp.n_nodes == 6
        assert small_vrp.depot == 0
        assert 5 in small_vrp.customers

    def test_init_with_time_windows(self):
        dm = np.zeros((4, 4))
        vrp = VRP(dm, [0, 1, 2, 3], capacity=5, n_vehicles=1,
                  time_windows=[(0, 10)] * 4, service_times=[1, 2, 3, 4])
        assert vrp.time_windows is not None
        assert vrp.service_times == [1, 2, 3, 4]

    def test_calculate_route_distance_empty(self, small_vrp):
        assert small_vrp._calculate_route_distance([]) == 0

    def test_calculate_route_distance(self, small_vrp):
        assert small_vrp._calculate_route_distance([1, 2, 3]) > 0

    def test_calculate_route_load(self, small_vrp):
        assert small_vrp._calculate_route_load([1, 3, 5]) == 8

    def test_is_route_feasible(self, small_vrp):
        assert small_vrp._is_route_feasible([1, 3])
        assert not small_vrp._is_route_feasible([2, 4, 5])

    def test_split_routes(self, small_vrp):
        routes = small_vrp._split_routes([1, 2, 3, 4, 5])
        all_customers = [c for r in routes for c in r]
        assert sorted(all_customers) == [1, 2, 3, 4, 5]

    def test_split_routes_n_vehicles_limit(self, small_vrp):
        routes = small_vrp._split_routes([1, 2, 3, 4, 5])
        assert len(routes) <= small_vrp.n_vehicles

    def test_total_distance(self, small_vrp):
        d = small_vrp._total_distance([[1, 2], [3, 4, 5]])
        assert d > 0

    def test_solve_greedy_2opt(self, small_vrp):
        r = small_vrp.solve_greedy_2opt()
        assert r["method"] == "贪心+2-opt"
        assert r["total_distance"] > 0

    def test_solve_ga(self, small_vrp):
        random.seed(42)
        r = small_vrp.solve_ga(pop_size=20, max_gen=20)
        assert r["method"] == "遗传算法"
        assert r["total_distance"] > 0


class TestJobShopScheduler:
    @pytest.fixture
    def small_jssp(self):
        jobs = [[(0, 3), (1, 2), (2, 2)], [(1, 2), (2, 1), (0, 4)]]
        return JobShopScheduler(jobs)

    def test_init(self, small_jssp):
        assert small_jssp.n_jobs == 2
        assert small_jssp.n_machines == 3
        assert small_jssp.n_operations == 6

    def test_init_custom_n_machines(self):
        s = JobShopScheduler([[(0, 1)], [(2, 1)]], n_machines=5)
        assert s.n_machines == 5

    def test_init_with_due_dates(self):
        s = JobShopScheduler([[(0, 1)], [(0, 2)]], due_dates=[10, 20])
        assert s.due_dates == [10, 20]

    def test_decode_chromosome(self, small_jssp):
        r = small_jssp._decode_chromosome([0, 1, 0, 1, 0, 1])
        assert r["makespan"] > 0
        assert len(r["schedule"]) == 6

    def test_calculate_fitness(self, small_jssp):
        assert small_jssp._calculate_fitness([0, 1, 0, 1, 0, 1]) > 0

    def test_generate_chromosome(self, small_jssp):
        c = small_jssp._generate_chromosome()
        assert len(c) == 6
        assert c.count(0) == 3 and c.count(1) == 3

    def test_solve_spt(self, small_jssp):
        r = small_jssp.solve_spt()
        assert r["method"] == "SPT（最短加工时间）"
        assert r["makespan"] > 0

    def test_solve_edd_no_due_dates(self, small_jssp):
        r = small_jssp.solve_edd()
        assert r["method"] == "SPT（最短加工时间）"

    def test_solve_edd_with_due_dates(self):
        s = JobShopScheduler([[(0, 3), (1, 2)], [(1, 4), (0, 1)]], due_dates=[10, 5])
        r = s.solve_edd()
        assert r["method"] == "EDD（最早交货期）"
        assert r["makespan"] > 0

    def test_solve_ga(self, small_jssp):
        random.seed(42)
        r = small_jssp.solve_ga(pop_size=10, max_gen=10)
        assert r["method"] == "遗传算法"
        assert r["makespan"] > 0

    def test_decode_schedule_structure(self, small_jssp):
        r = small_jssp._decode_chromosome([0, 0, 0, 1, 1, 1])
        for entry in r["schedule"]:
            assert len(entry) == 5
            job, op, machine, start, end = entry
            assert end > start