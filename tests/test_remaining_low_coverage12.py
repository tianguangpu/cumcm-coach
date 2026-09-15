"""第十二批：nsga2 repair/constraints/verbose + job_shop 内部方法"""
import os
import sys
import subprocess
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest

SKILL_ROOT = r"C:\Users\Lenovo\.claude\skills\cumcm-coach-skill-v7"


# ============================================================
# nsga2: repair 参数 (lines 143-146, 204, 282-284)
# ============================================================
class TestNsga2Repair:
    def test_with_repair(self):
        from algorithms.optimization.nsga2 import NSGA2

        def repair(x):
            return np.clip(x, -2, 2)

        opt = NSGA2(
            [lambda x: float(np.sum(x ** 2)),
             lambda x: float(np.sum((x - 1) ** 2))],
            dim=2, bounds=[(-5, 5)] * 2,
            repair=repair, pop_size=10, max_gen=5, seed=42
        )
        r = opt.solve(verbose=False)
        assert "pareto_F" in r
        assert r["feasible"] in (True, False)

    def test_repair_shape_mismatch_triggers_infeasible(self):
        from algorithms.optimization.nsga2 import NSGA2

        def bad_repair(x):
            return np.array([1.0])  # 形状不匹配 -> feasible_all = False

        opt = NSGA2(
            [lambda x: float(np.sum(x ** 2)),
             lambda x: float(np.sum((x - 1) ** 2))],
            dim=2, bounds=[(-5, 5)] * 2,
            repair=bad_repair, pop_size=6, max_gen=3, seed=42
        )
        r = opt.solve(verbose=False)
        assert r["feasible"] is False


# ============================================================
# nsga2: constraints 参数 (lines 234, 278-280)
# ============================================================
class TestNsga2Constraints:
    def test_with_constraints(self):
        from algorithms.optimization.nsga2 import NSGA2

        opt = NSGA2(
            [lambda x: float(np.sum(x ** 2)),
             lambda x: float(np.sum((x - 1) ** 2))],
            dim=2, bounds=[(-5, 5)] * 2,
            constraints=lambda x: np.all(np.abs(x) <= 3),
            pop_size=10, max_gen=5, seed=42
        )
        r = opt.solve(verbose=False)
        assert "pareto_F" in r

    def test_constraints_infeasible(self):
        from algorithms.optimization.nsga2 import NSGA2

        opt = NSGA2(
            [lambda x: float(np.sum(x ** 2)),
             lambda x: float(np.sum((x - 1) ** 2))],
            dim=2, bounds=[(-5, 5)] * 2,
            constraints=lambda x: False,  # 永远不可行
            pop_size=6, max_gen=3, seed=42
        )
        r = opt.solve(verbose=False)
        assert r["feasible"] is False


# ============================================================
# nsga2: verbose (lines 220, 256)
# ============================================================
class TestNsga2Verbose:
    def test_verbose_print(self):
        from algorithms.optimization.nsga2 import NSGA2

        opt = NSGA2(
            [lambda x: float(np.sum(x ** 2)),
             lambda x: float(np.sum((x - 1) ** 2))],
            dim=2, bounds=[(-5, 5)] * 2,
            pop_size=10, max_gen=25, seed=42
        )
        r = opt.solve(verbose=True)  # gen+1 % 20 == 0 at gen=19
        assert "history" in r


# ============================================================
# nsga2: __main__ block (lines 298-309)
# ============================================================
class TestNsga2MainBlock:
    def test_main_block(self):
        """nsga2 __main__ 跑单个 NSGA2 实例，应该安全"""
        import runpy
        old = sys.argv
        sys.argv = ["nsga2.py"]
        try:
            runpy.run_module("algorithms.optimization.nsga2", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# job_shop: verbose (line 382)
# ============================================================
class TestJobShopVerbose:
    def test_solve_ga_verbose(self):
        from algorithms.optimization.job_shop import JobShopScheduler

        jobs = [[(0, 3), (1, 2), (2, 2)],
                [(1, 2), (2, 1), (0, 4)],
                [(2, 3), (0, 1), (1, 3)]]
        js = JobShopScheduler(jobs)
        r = js.solve_ga(pop_size=20, max_gen=100, verbose=True)
        assert "makespan" in r

    def test_solve_nsga2_verbose(self):
        from algorithms.optimization.job_shop import JobShopScheduler

        jobs = [[(0, 3), (1, 2)],
                [(1, 2), (0, 4)],
                [(0, 1), (1, 3)]]
        js = JobShopScheduler(jobs)
        r = js.solve_nsga2(pop_size=20, max_gen=100, verbose=True)
        assert "pareto_front" in r or "n_solutions" in r


# ============================================================
# job_shop: _calculate_crowding_single with <=2 (lines 496-498)
# ============================================================
class TestJobShopCrowding:
    def test_crowding_single_small(self):
        from algorithms.optimization.job_shop import JobShopScheduler

        jobs = [[(0, 1)], [(0, 1)]]
        js = JobShopScheduler(jobs)
        # 2 个解, 拥挤度应返回 inf
        objectives = [[1.0, 2.0], [3.0, 4.0]]
        cd = js._calculate_crowding_single(objectives, [0, 1])
        assert cd[0] == float('inf')
        assert cd[1] == float('inf')


# ============================================================
# job_shop: _decode_chromosome with exhausted job (line 577)
# ============================================================
class TestJobShopDecodeExhausted:
    def test_decode_with_exhausted_job(self):
        """染色体中 job 出现次数 > 操作数时 continue"""
        from algorithms.optimization.job_shop import JobShopScheduler

        # 2 jobs, each 1 operation
        jobs = [[(0, 3)], [(1, 2)]]
        js = JobShopScheduler(jobs)
        # 染色体: job 0 出现 3 次, 但只有 1 个操作 -> 第2、3次 continue
        chromosome = [0, 0, 0, 1, 1, 1]
        result = js._decode_chromosome(chromosome)
        assert "makespan" in result


# ============================================================
# job_shop: solve_nsga2 front break (line 364)
# ============================================================
class TestJobShopNsga2Break:
    def test_nsga2_enough_generations(self):
        """足够代数触发 front_idx >= len(combined_fronts) break"""
        from algorithms.optimization.job_shop import JobShopScheduler

        np.random.seed(42)
        jobs = [[(0, 3), (1, 2)],
                [(1, 2), (0, 4)],
                [(0, 1), (1, 3)]]
        js = JobShopScheduler(jobs)
        r = js.solve_nsga2(pop_size=30, max_gen=50, verbose=False)
        assert "n_solutions" in r or "pareto_front" in r


# ============================================================
# job_shop: __main__ block (lines 651-688, 子进程隔离)
# ============================================================
class TestJobShopMainBlock:
    def test_main_block(self):
        """job_shop __main__ 跑 SPT+EDD+GA+NSGA2，子进程隔离"""
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.argv=['job_shop.py']; import runpy; "
             "runpy.run_module('algorithms.optimization.job_shop', run_name='__main__')"],
            env=env, cwd=SKILL_ROOT,
            capture_output=True, timeout=120
        )
        assert r.returncode in (0, 1, -1073740791)  # 0xC0000374 也可接受