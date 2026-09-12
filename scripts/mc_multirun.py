# -*- coding: utf-8 -*-
"""mc_multirun.py — 蒙特卡洛多轮满核并行评估(子进程隔离)

对指定求解器在某 benchmark 问题做 N 次不同随机种子的隔离子进程求解,
用 os.cpu_count() 全核并行, 统计目标函数分布(均值/std/最优/分位数/成功率)。
每个 MC 样本经 subprocess 独立子进程求解, 规避同进程连跑多个优化器的偶发崩溃。

用法:
    py -3 mc_multirun.py                            # 默认 SA_PSO / sphere 300 次
    py -3 mc_multirun.py -s GA -p rastrigin -n 300
    from mc_multirun import run_mc_sim             # 供代码复用

输出: {skill}/results/mc_multirun.csv
"""
import argparse
import csv
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
from isolated_solve import run_isolated  # noqa: E402

TRUE_OPT = {"sphere": 0.0, "rastrigin": 0.0, "box": 0.0}


def run_mc_sim(solver="SA_PSO", problem="sphere", n=300, dim=10,
               base_seed=1, tol=1e-3, out=None):
    """满核并行蒙特卡洛评估。返回统计字典, 并写入 out CSV。"""
    out_path = Path(out) if out else SKILL / "results" / "mc_multirun.csv"
    workers = max(1, os.cpu_count() or 4)

    def one_run(seed):
        t0 = time.time()
        res = run_isolated(solver, problem=problem, seed=seed, dim=dim, retries=3)
        return {"f_opt": float(res["f_opt"]),
                "feasible": bool(res.get("feasible", True)),
                "elapsed_s": time.time() - t0}

    sys.stdout.write(f"[MC] {solver}/{problem}(dim{dim}) x {n} 次, 并行度 {min(workers, n)}\n")
    sys.stdout.flush()
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=min(workers, n)) as ex:
        futs = {ex.submit(one_run, base_seed + i): base_seed + i for i in range(n)}
        done = 0
        for fut in as_completed(futs):
            done += 1
            results.append(fut.result())
            if done % 100 == 0:
                sys.stdout.write(f"  ... {done}/{n}\n"); sys.stdout.flush()
    total = time.time() - t0

    vals = [r["f_opt"] for r in results]
    opts = TRUE_OPT.get(problem, 0.0)
    vals_sorted = sorted(vals)
    def q(p):
        return vals_sorted[min(len(vals_sorted) - 1, int(p * len(vals_sorted)))]
    mean = statistics.fmean(vals)
    stats = {
        "solver": solver, "problem": problem, "dim": dim, "n": n,
        "mean": round(mean, 6), "std": round(statistics.pstdev(vals), 6),
        "min": round(min(vals), 6), "median": round(q(0.5), 6),
        "p95": round(q(0.95), 6), "p99": round(q(0.99), 6),
        "success_rate": round(sum(1 for v in vals if abs(v - opts) <= tol) / n, 3),
        "elapsed_total_s": round(total, 2),
        "mean_per_run_s": round(statistics.fmean(r["elapsed_s"] for r in results), 4),
        "feasible_ratio": round(sum(1 for r in results if r["feasible"]) / n, 3),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(stats.keys()))
        w.writeheader(); w.writerow(stats)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--solver", default="SA_PSO")
    ap.add_argument("-p", "--problem", default="sphere")
    ap.add_argument("-n", "--n", type=int, default=300)
    ap.add_argument("-d", "--dim", type=int, default=10)
    ap.add_argument("-b", "--base-seed", type=int, default=1)
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    st = run_mc_sim(a.solver, a.problem, a.n, a.dim, a.base_seed, a.tol, a.out)

    print(f"\n== 结果已写入: {Path(a.out) if a.out else SKILL/'results'/'mc_multirun.csv'}")
    print(f"{st['solver']} / {st['problem']}(dim={st['dim']})  共 {st['n']} 次 MC, "
          f"总耗时 {st['elapsed_total_s']}s (并行 {os.cpu_count()} 核, 场均 {st['mean_per_run_s']}s)")
    print(f"  均值={st['mean']:.6f}  std={st['std']:.6f}  min={st['min']:.6f}  "
          f"中位={st['median']:.6f}  p95={st['p95']:.6f}  p99={st['p99']:.6f}")
    print(f"  成功率(≤{a.tol}): {st['success_rate']*100:.1f}%")


if __name__ == "__main__":
    main()