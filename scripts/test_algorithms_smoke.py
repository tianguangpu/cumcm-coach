# -*- coding: utf-8 -*-
"""
test_algorithms_smoke.py — 算法回归冒烟测试
============================================
确保各算法模块可导入且关键符号存在,算法修改后快速回归。

用法:
    python scripts/test_algorithms_smoke.py
    python scripts/test_algorithms_smoke.py --verbose

退出码: 0 = 全部通过; 1 = 有模块导入失败或关键符号缺失。
(环境缺失依赖导致的导入失败记为 [ENV],不计入致命失败。)
"""
import argparse
import importlib
import sys
import traceback
from pathlib import Path

import numpy as np

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT / "algorithms") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "algorithms"))

# 模块 -> 必须存在的符号
MODULES = {
    # 优化算法（核心）
    "optimization.sa_pso": ["SA_PSO"],
    "optimization.ga": ["GA"],
    "optimization.de": ["DE"],
    "optimization.nsga2": ["NSGA2"],
    "optimization.adaptive_hybrid": ["AdaptiveHybrid"],
    "optimization.pso_variants": ["pso_clerc", "clerc_constriction"],
    # 优化算法（组合问题）
    "optimization.vrp": ["VRP", "MTVRP"],
    "optimization.job_shop": ["JobShopScheduler", "FlexibleJobShopScheduler"],
    "optimization.two_stage": ["TwoStageSolver", "FacilityLocationSolver"],
    # 评价算法
    "evaluation.ahp_entropy_topsis": ["ComprehensiveEvaluation"],
    "evaluation.vikor": ["VIKOR"],
    "evaluation.gra": ["grey_relational"],
    # 机理算法
    "mechanistic.fdm_1d": ["heat_1d_explicit"],
    "mechanistic.fdm_2d": ["fdm_2d_explicit"],
    "mechanistic.fem_poisson": ["assemble_and_solve", "rect_tri_mesh"],
    "mechanistic.ode_solver": ["euler", "rk4", "solve_ivp_wrapper"],
    # 图论
    "network.graph_algo": ["dijkstra", "kruskal", "max_flow"],
    # 预测算法
    "prediction.arima": ["ARIMA_Forecast"],
    "prediction.gm11": ["GM11"],
    "prediction.mlp": ["MLP_Forecast"],
    "prediction.tam": ["TAM_Forecast"],
    # 验证算法
    "validation.metrics": ["FitMetrics"],
    "validation.monte_carlo": ["MonteCarlo"],
    "validation.sensitivity": ["SensitivityAnalyzer"],
    "validation.auto_tune": ["AutoTuner"],
    "validation.shap_analysis": ["SHAPAnalyzer"],
    "validation.sobol": ["sobol_total_and_first"],
    "validation.sobol_enhanced": ["sobol_analysis"],
    "validation.assumption_error": ["AssumptionChecker"],
    # 博弈/生态/统计
    "game.nash": ["pure_nash", "mixed_nash_2x2"],
    "ecology.population": ["lotka_volterra", "SIR", "SEIR"],
    "stats.hypothesis": ["paired_t", "chisq_test", "mann_whitney_u"],
    # 辅助模块
    "misc.problem_analyzer": ["analyze_problem"],
    "misc.innovation_guide": ["suggest_innovations"],
}

ENV_HINTS = ("No module named", "ImportError", "ModuleNotFoundError")


def check(verbose: bool = False) -> int:
    passed = failed = env_fail = 0
    for mod_name, symbols in MODULES.items():
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            if any(h in msg for h in ENV_HINTS):
                print(f"[ENV ] {mod_name}: 依赖缺失 -> {msg.splitlines()[0]}")
                env_fail += 1
            else:
                print(f"[FAIL] {mod_name}: 导入异常 -> {msg.splitlines()[0]}")
                if verbose:
                    traceback.print_exc()
                failed += 1
            continue

        missing = [s for s in symbols if not hasattr(mod, s)]
        if missing:
            print(f"[FAIL] {mod_name}: 缺失符号 {missing}")
            failed += 1
        else:
            print(f"[PASS] {mod_name}")
            passed += 1

    print(f"\n冒烟测试: {passed} 通过 / {failed} 致命失败 / {env_fail} 环境依赖缺失")
    return 1 if failed else 0


def test_optimizers_feasibility(verbose: bool = False) -> int:
    """回归测试: 隔离子进程跑求解器, 验证内置 repair 在紧约束下返回可行解。

    采用 isolated_solve.run_isolated 将每个求解器放入独立子进程执行, 规避
    本机 numpy/matplotlib C 扩展在同进程连续实例化多个求解器时的偶发崩溃。
    """
    try:
        from isolated_solve import run_isolated
    except Exception as e:  # noqa: BLE001
        print(f"[ENV ] 优化器可行性测试跳过: 依赖缺失 -> {e}")
        return 0

    fails = 0
    for name in ("SA_PSO", "GA", "NSGA2"):
        try:
            res = run_isolated(name)  # 非零退出码自动重试
            if name == "NSGA2":
                ok = res.get("feasible", False) and res.get("n_pareto", 0) >= 1
                if ok:
                    print(f"[PASS] NSGA-II: 多目标返回可行 Pareto 前沿 "
                          f"(n={res['n_pareto']}, feasible=True)")
                else:
                    print(f"[FAIL] NSGA-II: 返回不可行/空前沿 ({res})")
                    fails += 1
            else:
                ok = res.get("feasible", False)
                if ok:
                    print(f"[PASS] {name}: 紧约束下返回可行解 (feasible=True)")
                else:
                    print(f"[FAIL] {name}: 紧约束下返回不可行解 ({res})")
                    fails += 1
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {name}: 求解异常 -> {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            fails += 1
    return fails


def main() -> int:
    p = argparse.ArgumentParser(description="算法回归冒烟测试")
    p.add_argument("--verbose", action="store_true", help="打印导入异常完整堆栈")
    a = p.parse_args()
    code = check(a.verbose)
    code = code or test_optimizers_feasibility(a.verbose)
    return code


if __name__ == "__main__":
    sys.exit(main())
