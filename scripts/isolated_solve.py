"""isolated_solve.py — 子进程隔离求解执行器 (v1.1)

背景
----
本机环境(Python 3.13 + Windows)下, numpy/matplotlib 的 C 扩展在**同一进程内
连续实例化多个求解器**时, 会偶发 C 层崩溃(访问冲突 0xC0000005 / 栈溢出 0xC0000409),
表现为进程被直接终止且无 Python 堆栈。实测: 单进程连跑三个优化器崩溃率约 50%,
而**每个求解器放到独立子进程执行则 0 崩溃**。

本脚本把"构造求解器 + solve"放到独立子进程(`--solver` worker 模式)执行,
父进程通过 `run_isolated()` 发起并校验退出码, 非 0 自动重试。既规避同进程连跑
崩溃, 又保证可复现。结果以单行 JSON 打印, 供父进程解析。

v1.1 (2026-08-22): 新增 --seed / --problem / --dim, 接入 DE, 支持多目标 benchmark,
使消融(SA_PSO vs GA vs DE)与 MC 多轮能以每轮不同 seed 隔离运行。

用法(worker, 由 run_isolated 内部调用):
    python isolated_solve.py --solver SA_PSO [--problem box] [--seed 1] [--dim 10]
    python isolated_solve.py --solver DE --problem rastrigin --seed 2 --dim 10

Python 层调用:
    from isolated_solve import run_isolated
    res = run_isolated("DE", problem="rastrigin", seed=2, dim=10, retries=3)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKILL_ROOT = Path(__file__).resolve().parent.parent
ALGO_DIR = SKILL_ROOT / "algorithms"

PROBLEMS = ("box", "sphere", "rastrigin")
SOLVERS = ("SA_PSO", "GA", "DE", "NSGA2")


# ---------- 目标函数 / 修复器 ----------
def _box_repair(x):
    import numpy as np
    x = np.array(x, float)
    s = x.sum()
    return x * (0.5 / s) if s > 0.5 else x


def _box_obj(x):
    import numpy as np
    return -float(np.sum(x))


def _make_bench(name: str, dim: int):
    """无约束 benchmark (最小化)。返回 (obj, bound) 或 None。"""
    import numpy as np
    if name == "sphere":
        return (lambda x: float(np.sum(np.asarray(x, dtype=float) ** 2)),
                [(-5.0, 5.0)] * dim)
    if name == "rastrigin":
        A = 10.0
        def rastr(x):
            x = np.asarray(x, dtype=float)
            return float(A * dim + np.sum(x ** 2 - A * np.cos(2 * np.pi * x)))
        return (rastr, [(-5.12, 5.12)] * dim)
    return None


def _worker(solver: str, problem: str, seed: int, dim: int) -> None:
    """在子进程内构造并求解, 结果以单行 JSON 打印到 stdout。"""
    sys.path.insert(0, str(ALGO_DIR))
    import numpy as np

    if problem == "box":
        obj, repair, bounds = _box_obj, _box_repair, [(0.0, 1.0)] * 2
    else:
        made = _make_bench(problem, dim)
        if made is None:
            raise ValueError(f"未知问题: {problem}")
        obj, bounds = made
        repair = None  # 无约束 benchmark

    if solver in ("SA_PSO", "GA"):
        if solver == "SA_PSO":
            from optimization.sa_pso import SA_PSO
            s = SA_PSO(obj, len(bounds), bounds, None, repair=repair,
                       N=30, T_max=80, seed=seed)
        else:
            from optimization.ga import GA
            s = GA(obj, len(bounds), bounds, None, repair=repair,
                   pop_size=30, max_gen=80, seed=seed)
        r = s.solve(verbose=False)
        out = {"solver": solver, "problem": problem, "seed": seed,
               "feasible": bool(r.get("feasible", True)),
               "f_opt": float(r["f_opt"]),
               "x_opt": [float(v) for v in r["x_opt"]],
               "history_len": int(len(r["history"]))}
    elif solver == "DE":
        from optimization.de import DE
        s = DE(obj, len(bounds), bounds, constraints=None,
               pop_size=30, max_gen=80, seed=seed)
        r = s.solve(verbose=False)
        out = {"solver": solver, "problem": problem, "seed": seed,
               "feasible": bool(r.get("feasible", True)),
               "f_opt": float(r["f_opt"]),
               "x_opt": [float(v) for v in r["x_opt"]],
               "history_len": int(len(r["history"]))}
    elif solver == "NSGA2":
        if problem != "box":
            raise ValueError("NSGA2 仅为 box 多目标问题设计")
        from optimization.nsga2 import NSGA2
        obj2 = lambda x: float(np.sum((np.array(x) - 0.5) ** 2))  # noqa: E731
        s = NSGA2([obj, obj2], 2, bounds, repair=repair,
                  pop_size=30, max_gen=60, seed=seed)
        r = s.solve(verbose=False)
        out = {"solver": solver, "problem": problem, "seed": seed,
               "feasible": bool(r["feasible"]),
               "n_pareto": int(r["n_pareto"]),
               "hv": float(r["hv"]), "spread": float(r["spread"])}
    else:
        raise ValueError(f"未知求解器: {solver}")

    print(json.dumps(out, ensure_ascii=False))


# ---------- 父进程侧: 发起子进程 + 失败重试 ----------
def run_isolated(solver: str, problem: str = "box", seed: int = 1,
                 dim: int = 10, retries: int = 3):
    """以独立子进程执行求解, 非零退出码(含 C 层崩溃)自动重试。

    Returns:
        dict: worker 输出的 JSON(解析后)

    Raises:
        RuntimeError: 重试耗尽仍失败
    """
    cmd = [sys.executable, str(Path(__file__).resolve()),
           "--solver", solver, "--problem", problem, "--seed", str(seed),
           "--dim", str(dim)]
    last = None
    for attempt in range(1, retries + 1):
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 0:
            lines = [ln for ln in p.stdout.splitlines()
                     if ln.strip() and ln.startswith("{")]
            if not lines:  # 无 JSON 输出
                last = RuntimeError(f"{solver}: 子进程无有效输出 (stdout={p.stdout!r})")
                continue
            return json.loads(lines[-1])
        last = RuntimeError(
            f"{solver}/{problem}: 子进程退出码 {p.returncode} (尝试 {attempt}/{retries})")
    raise last


def _main() -> None:
    ap = argparse.ArgumentParser(description="子进程隔离求解执行器")
    ap.add_argument("--solver", required=True, choices=SOLVERS)
    ap.add_argument("--problem", default="box", choices=PROBLEMS)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dim", type=int, default=10)
    a = ap.parse_args()
    _worker(a.solver, a.problem, a.seed, a.dim)


if __name__ == "__main__":
    _main()
