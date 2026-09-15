"""JobShopScheduler / FlexibleJobShopScheduler 深层覆盖测试。"""
import random
from collections import Counter

import numpy as np
import pytest

from algorithms.optimization.job_shop import JobShopScheduler, FlexibleJobShopScheduler


@pytest.fixture(autouse=True)
def _seed():
    random.seed(42)
    np.random.seed(42)


JOBS = [
    [(0, 3), (1, 2), (2, 2)],
    [(1, 2), (2, 1), (0, 4)],
    [(2, 3), (0, 1), (1, 3)],
]
DUE_DATES = [10, 12, 15]


class TestJobShopDecode:
    def test_decode_basic(self):
        s = JobShopScheduler(JOBS)
        chrom = [0, 1, 2, 0, 1, 2, 0, 1, 2]
        r = s._decode_chromosome(chrom)
        assert r["makespan"] > 0
        assert len(r["schedule"]) == s.n_operations
        assert "machine_available" in r
        assert "job_available" in r

    def test_decode_skip_extra_genes(self):
        s = JobShopScheduler(JOBS)
        # 包含多余的工序编号,触发 op_idx >= len 跳过分支
        chrom = [0, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2]
        r = s._decode_chromosome(chrom)
        assert r["makespan"] > 0

    def test_decode_empty_schedule(self):
        # 空染色体应返回 makespan=0
        s = JobShopScheduler(JOBS)
        r = s._decode_chromosome([])
        assert r["makespan"] == 0
        assert r["schedule"] == []

    def test_calculate_fitness(self):
        s = JobShopScheduler(JOBS)
        f = s._calculate_fitness([0, 1, 2, 0, 1, 2, 0, 1, 2])
        assert f > 0

    def test_generate_chromosome(self):
        s = JobShopScheduler(JOBS)
        c = s._generate_chromosome()
        assert len(c) == s.n_operations
        # 包含每个作业的工序数
        from collections import Counter
        cnt = Counter(c)
        for j, job in enumerate(JOBS):
            assert cnt[j] == len(job)


class TestJobShopHeuristics:
    def test_solve_spt(self):
        s = JobShopScheduler(JOBS)
        r = s.solve_spt()
        assert r["method"].startswith("SPT")
        assert r["makespan"] > 0

    def test_solve_edd_with_due_dates(self):
        s = JobShopScheduler(JOBS, due_dates=DUE_DATES)
        r = s.solve_edd()
        assert r["method"].startswith("EDD")
        assert r["makespan"] > 0

    def test_solve_edd_fallback_to_spt(self):
        # 无 due_dates -> 回退 SPT
        s = JobShopScheduler(JOBS)
        r = s.solve_edd()
        assert "SPT" in r["method"]


class TestJobShopGA:
    def test_solve_ga_small(self):
        random.seed(42); np.random.seed(42)
        s = JobShopScheduler(JOBS)
        r = s.solve_ga(pop_size=6, max_gen=3, pc=0.9, pm=0.5, verbose=False)
        assert r["method"] == "遗传算法"
        assert r["makespan"] > 0
        assert r["iterations"] == 3

    def test_solve_ga_verbose(self):
        random.seed(42); np.random.seed(42)
        s = JobShopScheduler(JOBS)
        r = s.solve_ga(pop_size=4, max_gen=60, verbose=True)
        assert r["makespan"] > 0

    def test_pox_crossover(self):
        random.seed(42)
        s = JobShopScheduler(JOBS)
        p1 = s._generate_chromosome()
        p2 = s._generate_chromosome()
        child = s._pox_crossover(p1, p2)
        assert len(child) == len(p1)
        from collections import Counter
        assert Counter(child) == Counter(p1)  # 元素相同

    def test_swap_mutation(self):
        random.seed(42)
        s = JobShopScheduler(JOBS)
        c = s._generate_chromosome()
        m = s._swap_mutation(c)
        assert len(m) == len(c)
        assert Counter(m) == Counter(c)


class TestJobShopNSGA2:
    def test_calculate_objectives_no_due_dates(self):
        s = JobShopScheduler(JOBS)
        obj = s._calculate_objectives([0, 1, 2, 0, 1, 2, 0, 1, 2])
        assert obj[0] > 0
        assert obj[1] == 0  # 无交货期

    def test_calculate_objectives_with_due_dates(self):
        s = JobShopScheduler(JOBS, due_dates=[1, 1, 1])  # 极短交货期触发 tardiness
        obj = s._calculate_objectives([0, 1, 2, 0, 1, 2, 0, 1, 2])
        assert obj[0] > 0
        assert obj[1] > 0

    def test_dominates(self):
        s = JobShopScheduler(JOBS)
        assert s._dominates([1, 1], [2, 2]) is True   # obj1 全优于 obj2
        assert s._dominates([2, 2], [1, 1]) is False
        assert s._dominates([1, 2], [2, 1]) is False  # 互有优劣,不支配
        assert s._dominates([1, 1], [1, 1]) is False  # 相同不支配

    def test_non_dominated_sort(self):
        s = JobShopScheduler(JOBS)
        objs = [[1, 1], [2, 2], [1, 2], [2, 1]]
        fronts = s._non_dominated_sort(objs)
        assert len(fronts) >= 1
        # 第一前沿应包含非支配解
        assert 0 in fronts[0]

    def test_calculate_crowding_small_front(self):
        s = JobShopScheduler(JOBS)
        fronts = [[0, 1]]
        crowding = s._calculate_crowding([[1, 1], [2, 2]], fronts)
        # len(front) <= 2 -> inf
        assert crowding[0] == float("inf")
        assert crowding[1] == float("inf")

    def test_calculate_crowding_large_front(self):
        s = JobShopScheduler(JOBS)
        objs = [[1, 5], [2, 4], [3, 3], [4, 2], [5, 1]]
        fronts = [list(range(5))]
        crowding = s._calculate_crowding(objs, fronts)
        # 边界为 inf
        assert crowding[0] == float("inf")
        assert crowding[4] == float("inf")

    def test_calculate_crowding_single(self):
        s = JobShopScheduler(JOBS)
        indices = [0, 1, 2, 3]
        objs = [[1, 4], [2, 3], [3, 2], [4, 1]]
        c = s._calculate_crowding_single(objs, indices)
        assert c[0] == float("inf")
        assert c[3] == float("inf")

    def test_calculate_crowding_single_zero_range(self):
        s = JobShopScheduler(JOBS)
        indices = [0, 1, 2]
        objs = [[5, 5], [5, 5], [5, 5]]  # obj_range = 0 触发 continue
        c = s._calculate_crowding_single(objs, indices)
        assert c[0] == float("inf")

    def test_tournament_select(self):
        random.seed(42)
        s = JobShopScheduler(JOBS, due_dates=DUE_DATES)
        pop = [s._generate_chromosome() for _ in range(8)]
        objs = [s._calculate_objectives(c) for c in pop]
        fronts = s._non_dominated_sort(objs)
        crowding = s._calculate_crowding(objs, fronts)
        selected = s._tournament_select(pop, objs, fronts, crowding)
        assert len(selected) == len(pop[0])

    def test_solve_nsga2_small(self):
        random.seed(42); np.random.seed(42)
        s = JobShopScheduler(JOBS, due_dates=DUE_DATES)
        r = s.solve_nsga2(pop_size=6, max_gen=2, verbose=False)
        assert r["method"] == "NSGA-II"
        assert r["n_solutions"] >= 1
        assert r["iterations"] == 2
        assert isinstance(r["pareto_front"], list)


class TestFlexibleJobShop:
    def test_flexible_init(self):
        jobs = [
            [[(0, 3), (1, 4)], [(1, 2), (2, 3)]],
            [[(0, 2)], [(2, 2)]],
        ]
        s = FlexibleJobShopScheduler(jobs)
        assert s.n_jobs == 2
        assert s.n_machines == 3

    def test_flexible_solve_ga(self):
        random.seed(42); np.random.seed(42)
        jobs = [
            [[(0, 3), (1, 4)], [(1, 2), (2, 3)]],
            [[(0, 2)], [(2, 2)]],
        ]
        s = FlexibleJobShopScheduler(jobs)
        r = s.solve_ga(pop_size=6, max_gen=3, verbose=False)
        assert r["method"] == "GA（柔性车间调度）"
        assert r["makespan"] > 0
        assert isinstance(r["schedule"], list)

    def test_flexible_solve_ga_verbose(self):
        random.seed(42); np.random.seed(42)
        jobs = [[[(0, 3)]], [[(1, 2)]]]
        s = FlexibleJobShopScheduler(jobs)
        r = s.solve_ga(pop_size=4, max_gen=55, verbose=True)
        assert r["makespan"] > 0
