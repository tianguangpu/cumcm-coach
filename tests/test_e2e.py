"""
v7 端到端验证脚本

用 2025 年 C 题（蔬菜定价补货）模拟完整流程。
验证：建模→求解→图表→论文→评审 全链路。

运行: py tests/test_e2e.py
"""

import json
import os
import shutil
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_full_workflow() -> bool:
    """执行完整工作流程，返回是否成功。

    供命令行调用（``python tests/test_e2e.py``）使用。
    pytest 入口见文件末尾的 :func:`test_full_workflow`。
    """
    print("=" * 60)
    print("v7 端到端验证 — 2025 C 题蔬菜定价补货")
    print("=" * 60)

    # 创建临时工作目录
    work_dir = tempfile.mkdtemp(prefix="v7_e2e_")
    print(f"\n工作目录: {work_dir}")

    try:
        # Step 1: 初始化项目
        print("\n[Step 1] 初始化项目...")
        from scripts.init_project import init_project
        init_project(
            project_dir=work_dir,
            team_id="202500001",
            members="测试A,测试B,测试C",
            problem_type="C"
        )
        assert os.path.exists(os.path.join(work_dir, "plan.md")), "plan.md 未生成"
        assert os.path.exists(os.path.join(work_dir, "todo.md")), "todo.md 未生成"
        assert os.path.exists(os.path.join(work_dir, "state", "decision_log.json")), "decision_log.json 未生成"
        print("✅ 项目初始化成功")

        # Step 2: 问题分析
        print("\n[Step 2] 问题分析...")
        from algorithms.misc.problem_analyzer import analyze_problem
        problem_text = """
        某蔬菜商店需要制定每日的蔬菜补货和定价策略。
        已知历史销售数据、进货成本、库存容量等信息。
        问题1: 建立蔬菜需求预测模型
        问题2: 建立最优定价模型
        问题3: 建立补货策略优化模型
        """
        analysis = analyze_problem(problem_text, outdir=os.path.join(work_dir, "results"))
        assert "background" in analysis, "问题分析缺少 background"
        assert "ambiguity" in analysis, "问题分析缺少 ambiguity"
        print(f"✅ 问题分析完成: 背景={analysis.get('background', [])}, 歧义={len(analysis.get('ambiguity', []))}条")

        # Step 3: 算法求解
        print("\n[Step 3] 算法求解...")
        import numpy as np

        from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation
        from algorithms.prediction.arima import ARIMA_Forecast

        # 模拟需求预测
        np.random.seed(42)
        sales_data = np.random.poisson(100, 30).astype(float)  # 30天销售数据
        arima = ARIMA_Forecast(sales_data, order=(1, 1, 1))
        arima.fit()  # 必须先拟合
        forecast_result = arima.forecast(steps=7)
        forecast = forecast_result[0] if isinstance(forecast_result, tuple) else forecast_result
        assert len(forecast) == 7, f"预测长度错误: {len(forecast)}"
        print(f"✅ 需求预测完成: 7天预测均值={np.mean(forecast):.1f}")

        # 模拟评价问题
        data = np.array([
            [0.8, 0.6, 0.9, 0.7],
            [0.6, 0.8, 0.7, 0.9],
            [0.9, 0.5, 0.8, 0.6],
            [0.7, 0.7, 0.6, 0.8],
        ])
        benefit_cols = [0, 1, 2, 3]
        cost_cols = []
        ce = ComprehensiveEvaluation(data, benefit_cols, cost_cols)
        # AHP 判断矩阵
        pairwise = np.array([
            [1, 2, 3, 4],
            [1/2, 1, 2, 3],
            [1/3, 1/2, 1, 2],
            [1/4, 1/3, 1/2, 1],
        ])
        ce.run_ahp(pairwise)
        ce.run_entropy()
        ce.combine_weights(alpha=0.5)
        topsis_result = ce.topsis()
        assert len(topsis_result) == 4, f"TOPSIS 结果长度错误: {len(topsis_result)}"
        print(f"✅ 综合评价完成: 排序={np.argsort(-topsis_result).tolist()}")

        # Step 4: 灵敏度分析
        print("\n[Step 4] 灵敏度分析...")
        from algorithms.validation.sobol import sobol_total_and_first
        def model_func(x):
            return x[0] * 0.4 + x[1] * 0.3 + x[2] * 0.3
        bounds = [(0, 1), (0, 1), (0, 1)]
        sobol_result = sobol_total_and_first(model_func, bounds, N=128)
        assert "S1" in sobol_result, "Sobol 缺少 S1"
        assert "ST" in sobol_result, "Sobol 缺少 ST"
        print(f"✅ Sobol 灵敏度完成: S1={[round(v, 3) for v in sobol_result['S1']]}")

        # Step 5: 蒙特卡洛验证
        print("\n[Step 5] 蒙特卡洛验证...")
        from algorithms.validation.monte_carlo import MonteCarlo
        def mc_model(params):
            return params['x'] * params['y']
        dist_params = {
            'x': {'dist': 'uniform', 'low': 0.8, 'high': 1.2},  # 需求波动 ±20%
            'y': {'dist': 'uniform', 'low': 0.9, 'high': 1.1},  # 价格波动 ±10%
        }
        mc = MonteCarlo(mc_model, dist_params)
        mc.run(n=200, seed=42)
        mc_result = mc.statistics()
        assert "mean" in mc_result, "MC 缺少 mean"
        assert "std" in mc_result, "MC 缺少 std"
        print(f"✅ 蒙特卡洛完成: 均值={mc_result['mean']:.3f}, 标准差={mc_result['std']:.3f}")

        # Step 6: 求解器验证
        print("\n[Step 6] 求解器验证...")
        from scripts.solver_router import solve_lp
        lp_result = solve_lp(
            objective={"x": 10, "y": 8},
            constraints=[
                {"coeffs": {"x": 1, "y": 1}, "sense": "<=", "rhs": 100},
                {"coeffs": {"x": 1, "y": 0}, "sense": ">=", "rhs": 20},
                {"coeffs": {"x": 0, "y": 1}, "sense": ">=", "rhs": 10},
            ],
            variables={
                "x": {"lowBound": 20, "upBound": 80},
                "y": {"lowBound": 10, "upBound": 70},
            },
            sense="maximize"
        )
        assert lp_result["status"] == "optimal", f"LP 求解失败: {lp_result['status']}"
        print(f"✅ LP 求解完成: 最优值={lp_result['objective_value']:.1f}")

        # Step 7: 结果汇总
        print("\n[Step 7] 结果汇总...")
        summary = {
            "problem_type": "C",
            "forecast": forecast.tolist(),
            "topsis_rank": np.argsort(-topsis_result).tolist(),
            "sobol_S1": sobol_result["S1"],
            "mc_mean": mc_result["mean"],
            "lp_optimal": lp_result["objective_value"],
        }
        summary_path = os.path.join(work_dir, "results", "summary.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"✅ 结果已保存: {summary_path}")

        print("\n" + "=" * 60)
        print("✅ 端到端验证通过！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 端到端验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(work_dir)
            print(f"\n已清理临时目录: {work_dir}")
        except OSError:
            pass


def test_full_workflow():
    """pytest 入口：端到端流程必须成功，否则测试失败。

    注意：不能直接在断言里调用返回 bool 的辅助函数——断言失败会被
    内层 ``except Exception`` 捕获并转成 ``return False``，导致测试假绿。
    """
    assert run_full_workflow(), "端到端流程未通过（详见上方输出）"


if __name__ == "__main__":
    sys.exit(0 if run_full_workflow() else 1)
