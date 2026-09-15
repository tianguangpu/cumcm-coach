"""VRP / MTVRP 深层覆盖测试。"""
import random
import numpy as np
import pytest

from algorithms.optimization.vrp import VRP, MTVRP


@pytest.fixture(autouse=True)
def _seed():
    random.seed(42)
    np.random.seed(42)


def make_dist(n=8, seed=42):
    rng = np.random.default_rng(seed)
    c = rng.random((n, 2)) * 100
    d = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            d[i, j] = float(np.sqrt(((c[i] - c[j]) ** 2).sum()))
    return d


class TestVRPInternal:
    def test_route_distance_empty(self):
        v = VRP(make_dist(5), [0, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        assert v._calculate_route_distance([]) == 0

    def test_route_distance_normal(self):
        d = make_dist(5)
        v = VRP(d, [0, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        dist = v._calculate_route_distance([1, 2, 3])
        expected = d[0, 1] + d[1, 2] + d[2, 3] + d[3, 0]
        assert abs(dist - expected) < 1e-6

    def test_route_load(self):
        v = VRP(make_dist(5), [0, 2, 3, 1, 4], capacity=10, n_vehicles=2)
        assert v._calculate_route_load([1, 2]) == 5

    def test_is_route_feasible(self):
        # 需求 6+6=12 超过 capacity=10 -> False
        v = VRP(make_dist(5), [0, 6, 6, 1, 1], capacity=10, n_vehicles=2)
        assert bool(v._is_route_feasible([1, 2])) is False
        # 需求 1+1=2 <= capacity=10 -> True
        v_ok = VRP(make_dist(5), [0, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        assert bool(v_ok._is_route_feasible([1, 2])) is True

    def test_split_routes_normal(self):
        v = VRP(make_dist(6), [0, 2, 3, 2, 3, 2], capacity=5, n_vehicles=3)
        chrom = [1, 2, 3, 4, 5]
        routes = v._split_routes(chrom)
        assert isinstance(routes, list)
        # 所有客户都被服务
        flat = sorted(c for r in routes for c in r)
        assert flat == [1, 2, 3, 4, 5]

    def test_split_routes_merge_for_n_vehicles(self):
        # 总载重迫使合并
        v = VRP(make_dist(6), [0, 1, 1, 1, 1, 1], capacity=10, n_vehicles=1)
        chrom = [1, 2, 3, 4, 5]
        routes = v._split_routes(chrom)
        assert len(routes) <= 1

    def test_total_distance(self):
        v = VRP(make_dist(5), [0, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        routes = [[1, 2], [3, 4]]
        d = v._total_distance(routes)
        assert d > 0


class TestVRPGreedy2opt:
    def test_solve_greedy_2opt_basic(self):
        random.seed(42)
        v = VRP(make_dist(8), [0, 2, 2, 2, 2, 2, 2, 2], capacity=6, n_vehicles=3)
        r = v.solve_greedy_2opt()
        assert r["method"] == "贪心+2-opt"
        assert r["total_distance"] > 0
        assert r["n_vehicles_used"] >= 1

    def test_2opt_improve_short_route(self):
        v = VRP(make_dist(5), [0, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        # len < 3 路径直接返回
        out = v._2opt_improve([[1]])
        assert out == [[1]]

    def test_2opt_improve_long_route(self):
        v = VRP(make_dist(8), [0, 1, 1, 1, 1, 1, 1, 1], capacity=20, n_vehicles=2)
        out = v._2opt_improve([[1, 2, 3, 4, 5, 6, 7]])
        assert len(out[0]) == 7


class TestVRPGA:
    def test_solve_ga_small(self):
        random.seed(42); np.random.seed(42)
        v = VRP(make_dist(6), [0, 1, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        r = v.solve_ga(pop_size=6, max_gen=3, pc=0.9, pm=0.5, verbose=False)
        assert r["method"] == "遗传算法"
        assert r["total_distance"] > 0
        assert r["n_vehicles_used"] >= 1
        assert r["iterations"] == 3

    def test_order_crossover(self):
        random.seed(42)
        v = VRP(make_dist(6), [0, 1, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        p1 = [1, 2, 3, 4, 5]
        p2 = [5, 4, 3, 2, 1]
        child = v._order_crossover(p1, p2)
        assert sorted(child) == sorted(p1)

    def test_swap_mutation(self):
        random.seed(42)
        v = VRP(make_dist(6), [0, 1, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        c = [1, 2, 3, 4, 5]
        m = v._swap_mutation(c)
        assert sorted(m) == sorted(c)


class TestVRPPSO:
    def test_solve_pso_small(self):
        random.seed(42); np.random.seed(42)
        v = VRP(make_dist(6), [0, 1, 1, 1, 1, 1], capacity=10, n_vehicles=2)
        r = v.solve_pso(n_particles=5, max_iter=3, verbose=False)
        assert r["method"] == "粒子群算法"
        assert r["total_distance"] > 0
        assert r["n_vehicles_used"] >= 1


class TestMTVRP:
    def test_mtvrp_init(self):
        v = MTVRP(make_dist(6), [0, 1, 1, 1, 1, 1],
                  vehicle_types=[{"capacity": 5, "cost_per_km": 2, "count": 2}])
        assert v.n_nodes == 6
        assert len(v.customers) == 5

    def test_mtvrp_solve_greedy(self):
        random.seed(42)
        v = MTVRP(make_dist(6), [0, 1, 1, 1, 1, 1],
                  vehicle_types=[{"capacity": 5, "cost_per_km": 2, "count": 2}])
        r = v.solve_greedy()
        assert r["method"] == "贪心（多车型）"
        assert r["total_cost"] >= 0
        assert r["total_distance"] >= 0
        assert isinstance(r["vehicle_assignments"], list)

    def test_mtvrp_route_distance_empty(self):
        v = MTVRP(make_dist(5), [0, 1, 1, 1, 1],
                 vehicle_types=[{"capacity": 5, "cost_per_km": 2, "count": 1}])
        assert v._calculate_route_distance([]) == 0
