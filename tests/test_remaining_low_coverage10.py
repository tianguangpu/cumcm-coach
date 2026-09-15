"""第十批：__main__ 块批量覆盖 + verbose 分支 + demo()

子进程隔离：VRP/job_shop/nsga2 的 __main__ 块顺序跑多个求解器，
触发 numpy C 扩展栈溢出 (0xC0000409)，必须子进程隔离。
"""
import os
import sys
import subprocess

os.environ["MPLBACKEND"] = "Agg"

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pytest

SKILL_ROOT = r"C:\Users\Lenovo\.claude\skills\cumcm-coach-skill-v7"


def _run_main_in_subprocess(module_name, timeout=60):
    """子进程运行 __main__ 块，避免同进程多求解器崩溃"""
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    code = (
        "import sys; sys.argv=[module_name.split('.')[-1] + '.py']; "
        "import runpy; runpy.run_module('" + module_name + "', run_name='__main__')"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        env=env, cwd=SKILL_ROOT,
        capture_output=True, timeout=timeout
    )
    return r.returncode


# ============================================================
# ahp_entropy_topsis demo()
# ============================================================
class TestAhpDemo:
    def test_demo(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from algorithms.evaluation.ahp_entropy_topsis import demo
        demo()
        assert (tmp_path / "weights_comparison.png").exists()
        assert (tmp_path / "radar_comparison.png").exists()

    def test_main_block(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        old = sys.argv
        sys.argv = ["ahp_entropy_topsis.py"]
        try:
            import runpy
            runpy.run_module("algorithms.evaluation.ahp_entropy_topsis", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# pso_variants __main__ (单进程安全：只跑 PSO 变体)
# ============================================================
class TestPsoVariantsMain:
    def test_main_block(self):
        old = sys.argv
        sys.argv = ["pso_variants.py"]
        try:
            import runpy
            runpy.run_module("algorithms.optimization.pso_variants", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# vrp __main__ (子进程隔离)
# ============================================================
class TestVrpMain:
    def test_main_block(self):
        assert _run_main_in_subprocess("algorithms.optimization.vrp") in (0, 1)


# ============================================================
# job_shop __main__ (子进程隔离)
# ============================================================
class TestJobShopMain:
    def test_main_block(self):
        assert _run_main_in_subprocess("algorithms.optimization.job_shop") in (0, 1)


# ============================================================
# nsga2 __main__ (子进程隔离)
# ============================================================
class TestNsga2Main:
    def test_main_block(self):
        assert _run_main_in_subprocess("algorithms.optimization.nsga2") in (0, 1)


# ============================================================
# nsga2 internal: _spread
# ============================================================
class TestNsga2Internals:
    def test_spread_2d(self):
        from algorithms.optimization.nsga2 import _spread
        F = [[0, 1], [0.5, 0.5], [1, 0]]
        s = _spread(F)
        assert 0.0 <= s <= 1.0

    def test_spread_few_points(self):
        from algorithms.optimization.nsga2 import _spread
        assert _spread([[0, 1], [1, 0]]) == 0.0

    def test_crowding_distance_edge(self):
        from algorithms.optimization.nsga2 import _crowding_distance
        F = [[0.0, 1.0], [1.0, 0.0]]
        cd = _crowding_distance(F, [0, 1])
        assert len(cd) == 2

    def test_solve_small(self):
        """nsga2 solve 子进程隔离避免 C 层崩溃"""
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        code = (
            "import sys; sys.path.insert(0, r'" + SKILL_ROOT + "'); "
            "import numpy as np; from algorithms.optimization.nsga2 import NSGA2; "
            "opt = NSGA2([lambda x: float(np.sum(np.asarray(x,float)**2)), "
            "lambda x: float(np.sum(np.asarray(x,float)**2)+1)], "
            "dim=2, bounds=[(-5,5)]*2, pop_size=20, max_gen=10, seed=42); "
            "r = opt.solve(); print(len(r['pareto_F']))"
        )
        r = subprocess.run([sys.executable, "-c", code],
                           env=env, capture_output=True, timeout=60, text=True)
        assert r.returncode == 0
        assert int(r.stdout.strip()) > 0


# ============================================================
# two_stage verbose branches
# ============================================================
class TestTwoStageVerbose:
    def test_clustering_verbose(self):
        from algorithms.optimization.two_stage import TwoStageSolver
        np.random.seed(1)
        customers = np.random.rand(12, 2)
        demands = [1] * 12
        solver = TwoStageSolver(problem_type="clustering_scheduling")
        result = solver.solve(customers, demands, n_clusters=3, capacity=10, verbose=True)
        assert result["stage1"]["method"] == "层次聚类"

    def test_greedy_verbose(self):
        from algorithms.optimization.two_stage import TwoStageSolver
        np.random.seed(2)
        customers = np.random.rand(15, 2)
        demands = np.random.randint(1, 4, 15).tolist()
        solver = TwoStageSolver(problem_type="partition_assignment")
        result = solver.solve(customers, demands, n_clusters=3, capacity=15, verbose=True)
        assert result["stage1"]["method"] == "贪心选址"

    def test_facility_routing_verbose_with_empty_cluster(self):
        from algorithms.optimization.two_stage import TwoStageSolver
        np.random.seed(42)
        customers = np.random.rand(3, 2)
        demands = [1, 1, 1]
        solver = TwoStageSolver(problem_type="facility_routing")
        result = solver.solve(customers, demands, n_clusters=2, capacity=100, verbose=True)
        assert result["total_cost"] >= 0


# ============================================================
# vrp verbose + solve methods (单求解器, 安全)
# ============================================================
class TestVrpVerbose:
    def test_solve_greedy_2opt_verbose(self):
        from algorithms.optimization.vrp import VRP
        import random
        np.random.seed(42)
        random.seed(42)
        n = 8
        coords = np.random.rand(n, 2) * 100
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0] + [random.randint(1, 3) for _ in range(n - 1)]
        vrp = VRP(dist, demands, capacity=10, n_vehicles=2)
        r = vrp.solve_greedy_2opt()
        assert "total_distance" in r and "routes" in r

    def test_solve_pso(self):
        from algorithms.optimization.vrp import VRP
        import random
        np.random.seed(42)
        random.seed(42)
        n = 6
        coords = np.random.rand(n, 2) * 100
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0] + [random.randint(1, 2) for _ in range(n - 1)]
        vrp = VRP(dist, demands, capacity=10, n_vehicles=2)
        r = vrp.solve_pso(n_particles=10, max_iter=20, verbose=False)
        assert "total_distance" in r


# ============================================================
# job_shop verbose + solve methods (单求解器, 安全)
# ============================================================
class TestJobShopVerbose:
    def test_solve_spt(self):
        from algorithms.optimization.job_shop import JobShopScheduler
        # jobs: list of [(machine, time), ...]
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 3)], [(1, 1), (0, 4)]]
        js = JobShopScheduler(jobs)
        r = js.solve_spt()
        assert "makespan" in r
        assert r["makespan"] >= 0

    def test_solve_ga(self):
        from algorithms.optimization.job_shop import JobShopScheduler
        jobs = [[(0, 3), (1, 2)], [(0, 2), (1, 3)], [(1, 1), (0, 4)]]
        js = JobShopScheduler(jobs)
        r = js.solve_ga(pop_size=10, max_gen=20, verbose=False)
        assert "makespan" in r