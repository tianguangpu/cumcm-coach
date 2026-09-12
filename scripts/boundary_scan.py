"""
boundary_scan.py — 边界检验 + 鲁棒性分析
==========================================
国一标准：必须回答"模型在什么条件下失效"。

用法:
    python boundary_scan.py --model my_model --params "x=0,10" "y=0,5"
    python boundary_scan.py --model my_model --sensitivity --monte-carlo 500
    python boundary_scan.py --tex paper/main.tex --check-robustness
"""
import argparse
import sys
from pathlib import Path
from typing import Callable

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def sensitivity_scan(
    model_fn: Callable,
    base_params: dict[str, float],
    param_ranges: dict[str, tuple[float, float]],
    n_points: int = 20,
) -> dict[str, list]:
    """
    自动扫描参数灵敏度，生成龙卷风图数据。

    Args:
        model_fn: 模型函数，接受参数字典，返回标量结果
        base_params: 基准参数
        param_ranges: 每个参数的扫描范围 {name: (min, max)}
        n_points: 每个参数的扫描点数

    Returns:
        灵敏度分析结果
    """
    base_result = model_fn(base_params)
    results = {"base_value": base_result, "params": {}}

    for param_name, (p_min, p_max) in param_ranges.items():
        if param_name not in base_params:
            continue

        # ±5%, ±10%, ±20% 三档
        base_val = base_params[param_name]
        perturbations = [0.05, 0.10, 0.20]
        param_results = {"base": base_val, "sensitivity": {}}

        for pct in perturbations:
            low_val = base_val * (1 - pct)
            high_val = base_val * (1 + pct)

            # 限制在范围内
            low_val = max(p_min, low_val)
            high_val = min(p_max, high_val)

            # 运行模型
            params_low = {**base_params, param_name: low_val}
            params_high = {**base_params, param_name: high_val}

            try:
                result_low = model_fn(params_low)
                result_high = model_fn(params_high)

                # 弹性系数
                if base_result != 0 and base_val != 0:
                    elasticity = abs((result_high - result_low) / base_result) / (2 * pct)
                else:
                    elasticity = 0

                param_results["sensitivity"][f"±{int(pct*100)}%"] = {
                    "low": round(float(result_low), 6),
                    "high": round(float(result_high), 6),
                    "range": round(float(result_high - result_low), 6),
                    "elasticity": round(float(elasticity), 4),
                    "grade": _grade_elasticity(elasticity),
                }
            except Exception as e:
                param_results["sensitivity"][f"±{int(pct*100)}%"] = {"error": str(e)}

        results["params"][param_name] = param_results

    return results


def _grade_elasticity(e: float) -> str:
    """弹性系数分级。"""
    if e >= 1.0:
        return "高敏感"
    elif e >= 0.3:
        return "中敏感"
    else:
        return "低敏感"


def monte_carlo_boundary(
    model_fn: Callable,
    base_params: dict[str, float],
    noise_levels: list[float] = [0.01, 0.05, 0.10, 0.20],
    n_runs: int = 500,
    seed: int = 42,
) -> dict[str, dict]:
    """
    蒙特卡洛边界检验：在不同噪声水平下测试模型鲁棒性。

    Args:
        model_fn: 模型函数
        base_params: 基准参数
        noise_levels: 噪声水平列表（相对标准差）
        n_runs: 每个噪声水平的运行次数
        seed: 随机种子

    Returns:
        各噪声水平下的模型表现
    """
    np.random.seed(seed)
    base_result = model_fn(base_params)
    results = {"base_value": base_result, "noise_levels": {}}

    for noise in noise_levels:
        run_results = []
        failures = 0

        for _ in range(n_runs):
            # 添加噪声
            noisy_params = {}
            for k, v in base_params.items():
                if isinstance(v, (int, float)):
                    noisy_params[k] = v * (1 + np.random.normal(0, noise))
                else:
                    noisy_params[k] = v

            try:
                result = model_fn(noisy_params)
                if np.isfinite(result):
                    run_results.append(float(result))
                else:
                    failures += 1
            except Exception:
                failures += 1

        if run_results:
            arr = np.array(run_results)
            results["noise_levels"][f"{int(noise*100)}%"] = {
                "mean": round(float(np.mean(arr)), 6),
                "std": round(float(np.std(arr)), 6),
                "cv": round(float(np.std(arr) / abs(np.mean(arr))) if np.mean(arr) != 0 else 0, 4),
                "min": round(float(np.min(arr)), 6),
                "max": round(float(np.max(arr)), 6),
                "q5": round(float(np.percentile(arr, 5)), 6),
                "q95": round(float(np.percentile(arr, 95)), 6),
                "failure_rate": round(failures / n_runs, 4),
                "n_success": len(run_results),
            }

    return results


def find_failure_boundary(
    model_fn: Callable,
    base_params: dict[str, float],
    param_name: str,
    direction: str = "up",
    max_factor: float = 5.0,
    n_steps: int = 50,
) -> dict:
    """
    寻找模型失效边界：逐步增大/减小参数直到模型失效。

    Args:
        model_fn: 模型函数
        base_params: 基准参数
        param_name: 要测试的参数
        direction: "up"增大/"down"减小
        max_factor: 最大倍数
        n_steps: 步数

    Returns:
        失效边界信息
    """
    base_val = base_params[param_name]
    factors = np.linspace(1.0, max_factor, n_steps) if direction == "up" else np.linspace(1.0, 1/max_factor, n_steps)

    for factor in factors:
        test_params = {**base_params, param_name: base_val * factor}
        try:
            result = model_fn(test_params)
            if not np.isfinite(result):
                return {
                    "param": param_name,
                    "direction": direction,
                    "failure_factor": round(float(factor), 4),
                    "failure_value": round(float(base_val * factor), 6),
                    "status": "found_boundary",
                }
        except Exception:
            return {
                "param": param_name,
                "direction": direction,
                "failure_factor": round(float(factor), 4),
                "failure_value": round(float(base_val * factor), 6),
                "status": "found_boundary(exception)",
            }

    return {
        "param": param_name,
        "direction": direction,
        "max_factor": max_factor,
        "status": "no_boundary_found(可能模型很鲁棒)",
    }


def render_report(sensitivity: dict, mc_boundary: dict, failure_boundaries: list = None) -> str:
    """生成鲁棒性分析报告。"""
    L = []
    L.append("=" * 55)
    L.append("  边界检验 + 鲁棒性分析报告")
    L.append("=" * 55)

    # 灵敏度
    L.append(f"\n【灵敏度扫描】 基准值={sensitivity.get('base_value', '?')}")
    for param, data in sensitivity.get("params", {}).items():
        L.append(f"\n  参数: {param} (基准={data.get('base', '?')})")
        for level, vals in data.get("sensitivity", {}).items():
            if "error" in vals:
                L.append(f"    {level}: 错误 - {vals['error']}")
            else:
                L.append(f"    {level}: [{vals.get('low', '?')}, {vals.get('high', '?')}] "
                         f"弹性={vals.get('elasticity', '?')} [{vals.get('grade', '?')}]")

    # 蒙特卡洛
    L.append(f"\n【蒙特卡洛边界检验】 基准值={mc_boundary.get('base_value', '?')}")
    for noise, vals in mc_boundary.get("noise_levels", {}).items():
        L.append(f"\n  噪声={noise}:")
        L.append(f"    均值={vals.get('mean', '?')} ± {vals.get('std', '?')}")
        L.append(f"    CV={vals.get('cv', '?')} (越小越鲁棒)")
        L.append(f"    95%CI=[{vals.get('q5', '?')}, {vals.get('q95', '?')}]")
        L.append(f"    失败率={vals.get('failure_rate', '?')}")

    # 失效边界
    if failure_boundaries:
        L.append("\n【失效边界】")
        for fb in failure_boundaries:
            L.append(f"  {fb['param']} ({fb['direction']}): {fb['status']}")
            if "failure_factor" in fb:
                L.append(f"    失效倍数: {fb['failure_factor']}x, 失效值: {fb['failure_value']}")

    # 总结
    L.append(f"\n{'='*55}")
    # 判断鲁棒性
    all_cv = []
    for noise_data in mc_boundary.get("noise_levels", {}).values():
        if "cv" in noise_data:
            all_cv.append(noise_data["cv"])
    avg_cv = np.mean(all_cv) if all_cv else 1.0

    if avg_cv < 0.05:
        L.append(f"  ✓ 模型高度鲁棒 (平均CV={avg_cv:.4f})")
    elif avg_cv < 0.15:
        L.append(f"  ✓ 模型较为鲁棒 (平均CV={avg_cv:.4f})")
    else:
        L.append(f"  ⚠ 模型鲁棒性不足 (平均CV={avg_cv:.4f}), 需加固")

    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="边界检验+鲁棒性分析")
    p.add_argument("--tex", default="paper/main.tex", help="论文LaTeX(检查是否包含鲁棒性分析)")
    p.add_argument("--check-robustness", action="store_true", help="检查论文中的鲁棒性内容")
    a = p.parse_args()

    if a.check_robustness:
        if not Path(a.tex).is_file():
            print(f"[err] 未找到 {a.tex}")
            return 1
        txt = open(a.tex, encoding="utf-8", errors="ignore").read()

        # 检查鲁棒性相关内容
        robustness_terms = [
            "灵敏度分析", "敏感性分析", "鲁棒性", "稳健性",
            "边界检验", "失效边界", "蒙特卡洛", "不确定性",
            "扰动", "噪声", "容错", "抗干扰",
        ]
        found = [t for t in robustness_terms if t in txt]

        print("=" * 50)
        print("  论文鲁棒性内容检查")
        print("=" * 50)
        print(f"  检测词: {len(robustness_terms)}个")
        print(f"  命中: {len(found)}个 → {', '.join(found)}")
        if len(found) < 3:
            print("  ⚠ 鲁棒性内容不足，建议补充:")
            print("    1. 灵敏度分析(龙卷风图)")
            print("    2. 蒙特卡洛边界检验(CV/95%CI)")
            print("    3. 失效边界(模型什么时候不能用)")
        else:
            print("  ✓ 鲁棒性内容充足")
        return 0

    # 如果没有指定模型函数，打印帮助
    print("用法:")
    print("  --check-robustness: 检查论文中的鲁棒性内容")
    print("  作为Python模块调用: from boundary_scan import sensitivity_scan, monte_carlo_boundary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
