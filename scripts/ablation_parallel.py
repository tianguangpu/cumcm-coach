"""ablation_parallel.py — 多算法消融的满核并行版(子进程隔离)

基于 isolated_solve.run_isolated: 每个 (算法, 问题, seed) 一次独立子进程求解,
规避同一进程连跑多个优化器的偶发崩溃(C层)；用 os.cpu_count() 全核并行摊满 CPU,
输出与 ablation.py 的 HEADER 对齐的 ablation.csv, 可被 validate_ablation 读取。

用法:
    py -3 ablation_parallel.py                     # SA_PSO/GA/DE × sphere/rastrigin
    from ablation_parallel import run_ablation_parallel   # 供代码复用

输出: {skill}/results/ablation_parallel.csv
"""
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL / "scripts"))
from isolated_solve import run_isolated  # noqa: E402

N_RUNS = 30
DIM = 10
BASE_SEED = 1
ALGOS = ["SA_PSO", "GA", "DE"]
PROBLEMS = ["sphere", "rastrigin"]
OUT = SKILL / "results" / "ablation_parallel.csv"

TRUE_OPT = {"sphere": 0.0, "rastrigin": 0.0}

HEADER = ["q", "algorithm", "elapsed_s", "best_value", "success_rate_30run",
          "std", "iter", "converged", "notes"]


def run_ablation_parallel(algorithms=None, problems=None, n_runs=N_RUNS,
                          dim=DIM, base_seed=BASE_SEED, out=None):
    """满核并行消融。返回行列表(供 write 复用), 并写入 out。

    Args:
        algorithms: 算法名列表, 默认 SA_PSO/GA/DE
        problems:   问题名列表, 默认 sphere/rastrigin
        n_runs:     每(算法×问题)运行次数
        dim:        无约束问题维度
        base_seed:  起始随机种子
        out:        CSV 输出路径, 默认 {skill}/results/ablation_parallel.csv
    """
    algorithms = algorithms or ALGOS
    problems = problems or PROBLEMS
    out_path = Path(out) if out else OUT
    workers = max(1, os.cpu_count() or 4)

    def one_run(problem, algo, seed):
        t0 = time.time()
        res = run_isolated(algo, problem=problem, seed=seed, dim=dim, retries=3)
        return {
            "problem": problem, "algorithm": algo, "seed": seed,
            "f_opt": res["f_opt"], "feasible": res["feasible"],
            "history_len": res["history_len"], "elapsed_s": time.time() - t0,
        }

    jobs = [(p, a, base_seed + i)
            for p in problems for a in algorithms for i in range(n_runs)]
    n_workers = min(workers, len(jobs))
    sys.stdout.write(f"[并行] 并行度 {n_workers} → {len(jobs)} 次隔离子进程求解\n")
    sys.stdout.flush()

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        futs = {ex.submit(one_run, p, a, s): (p, a, s) for (p, a, s) in jobs}
        done = 0
        for fut in as_completed(futs):
            done += 1
            try:
                results.append(fut.result())
            except Exception as e:  # noqa: BLE001
                p, a, s = futs[fut]
                print(f"[FAIL] {a}/{p}/seed{s}: {e}", file=sys.stderr)
            if done % 90 == 0:
                sys.stdout.write(f"  ... {done}/{len(jobs)}\n"); sys.stdout.flush()
    sys.stdout.write(f"  ... 共耗时 {time.time()-t0:.1f}s\n"); sys.stdout.flush()

    by = {}
    for r in results:
        by.setdefault((r["problem"], r["algorithm"]), []).append(r)

    rows = []
    for (problem, algo) in sorted(by):
        rs = by[(problem, algo)]
        vals = [r["f_opt"] for r in rs]
        n_ok = sum(1 for v in vals if abs(v - TRUE_OPT[problem]) <= 1e-3)
        means = sum(vals) / len(vals)
        var = sum((v - means) ** 2 for v in vals) / len(vals)
        rows.append({
            "q": problem, "algorithm": algo,
            "elapsed_s": round(sum(r["elapsed_s"] for r in rs) / len(rs), 3),
            "best_value": round(min(vals), 6),
            "success_rate_30run": round(n_ok / len(vals), 3),
            "std": round(var ** 0.5, 6),
            "iter": max(r["history_len"] for r in rs),
            "converged": n_ok == len(vals),
            "notes": f"mean={means:.5f}, median={sorted(vals)[len(vals)//2]:.5f}, "
                     f"feasible_ratio={sum(r['feasible'] for r in rs)/len(rs):.2f}",
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADER})
    return rows


def main() -> None:
    rows = run_ablation_parallel()
    print(f"\n== 消融结果已写入: {OUT}\n")
    print(f"{'问题':<10}{'算法':<10}{'最优':>12}{'均值':>12}{'std':>12}{'成功率':>8}")
    for r in rows:
        note_mean = r["notes"].split("mean=")[1].split(",")[0]
        print(f"{r['q']:<10}{r['algorithm']:<10}{r['best_value']:>12.6f}"
              f"{note_mean:>12}{r['std']:>12}{r['success_rate_30run']:>8.2f}")


if __name__ == "__main__":
    main()
