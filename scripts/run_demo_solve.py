"""run_demo_solve.py — L0 基线演示：单周期确定性凹规划

**定位**

本脚本是 [`references/model-upgrade.md`](../references/model-upgrade.md)
所述「模型深度升级阶梯」的**起点（L0）**。国一论文通常不止于此，需按该
文档逐级升级::

    L0  单周期确定性凹规划   ← 本脚本
    L1  多周期动态规划
    L2  随机 / 鲁棒优化
    L3  多目标帕累托
    L4  机理-数据融合

**模型**

.. code-block:: text

    max  Σ_i [ p_i·x_i − c_i·x_i² ]      凹收益（边际收益递减）
    s.t. Σ_i a_ij·x_i ≤ b_j              资源约束
         0 ≤ x_i ≤ u_i                   产能/面积上限

**为何用「凹」而非线性**

线性模型会把资源全押在单位收益最高的选项上，得到角点解；这与实际
「规模扩大后边际收益递减」不符。凹项正是刻画这一点 —— 它也是
国一论文区别于「套公式」的常见起点。

**约束处理**

按 [`references/algorithm-interfaces.md`](../references/algorithm-interfaces.md)
的「黄金法则」，用 ``repair`` 做**可行域投影**（而非纯惩罚项），
确保返回解必然可行。

**用法**::

    python scripts/run_demo_solve.py                    # 默认算例
    python scripts/run_demo_solve.py --compare          # 与线性基线对比
    python scripts/run_demo_solve.py --json results/l0_baseline.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.optimization.ga import GA  # noqa: E402

# ---------------- 默认算例：3 个决策变量 × 2 类资源 ----------------
# 可替换为你的赛题数据
P = np.array([8.0, 6.5, 5.0])        # 单位收益
C = np.array([0.14, 0.12, 0.10])     # 凹项系数（越大则边际递减越快）
A = np.array([                        # 资源消耗矩阵 a[资源][变量]
    [1.0, 1.2, 0.8],                  # 资源 1
    [0.5, 0.4, 0.9],                  # 资源 2
])
B = np.array([30.0, 18.0])            # 资源上限（设计为绑定约束，使权衡可见）
U = np.array([80.0, 70.0, 90.0])      # 各变量上限


def objective(x):
    """凹收益目标的**负值**（GA 求最小化）。"""
    x = np.asarray(x, dtype=float)
    return -float(np.sum(P * x - C * x**2))


def make_repair():
    """构造可行域投影函数（黄金法则：约束走 repair 而非纯惩罚）。

    策略：先把负值截断、再按比例缩放，使每条资源约束都满足，
    最后逐项 clip 到上限。
    """

    def repair(x):
        x = np.maximum(np.asarray(x, dtype=float), 0.0)
        x = np.minimum(x, U)
        for j in range(len(B)):
            used = float(np.dot(A[j], x))
            if used > B[j]:
                x = x * (B[j] / used)
        return np.minimum(x, U)

    return repair


def linear_baseline():
    """线性基线：忽略凹项，求 ``max Σp_i·x_i`` 的线性规划（必然落在角点）。

    与凹规划使用**同一套约束**，仅目标函数不同（去掉凹项）。这样两者的
    差异纯粹来自「是否刻画边际收益递减」，消融对比才公平。
    """
    try:
        from scipy.optimize import linprog

        r = linprog(
            c=-P, A_ub=A, b_ub=B,
            bounds=[(0.0, float(u)) for u in U],
            method="highs",
        )
        if r.success:
            return np.asarray(r.x, dtype=float)
    except ImportError:
        pass

    # scipy 不可用时的贪心兜底：按「单位资源收益」降序填充至约束用尽
    x = np.zeros(len(P))
    remaining = B.copy()
    density = P / np.maximum(A.sum(axis=0), 1e-9)   # 每单位资源收益
    for i in np.argsort(-density):
        caps = [U[i]]
        for j in range(len(B)):
            if A[j, i] > 0:
                caps.append(remaining[j] / A[j, i])
        take = max(0.0, min(caps))
        x[i] = take
        remaining = remaining - A[:, i] * take
    return x


def evaluate(x):
    """返回 (收益, 各资源占用, 是否可行)。"""
    x = np.asarray(x, dtype=float)
    profit = float(np.sum(P * x - C * x**2))
    usage = A @ x
    feasible = bool(np.all(usage <= B + 1e-6) and np.all(x >= -1e-9))
    return profit, usage, feasible


def main() -> int:
    p = argparse.ArgumentParser(description="L0 基线：单周期确定性凹规划")
    p.add_argument("--compare", action="store_true",
                   help="同时求解线性基线并对比")
    p.add_argument("--json", help="把结果写入指定 JSON 路径")
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    repair = make_repair()
    bounds = [(0.0, float(u)) for u in U]

    ga = GA(objective, dim=len(P), bounds=bounds, repair=repair,
            pop_size=60, max_gen=250, seed=a.seed)
    res = ga.solve(verbose=False)

    x_opt = np.asarray(res["x_opt"], dtype=float)
    profit, usage, feasible = evaluate(x_opt)

    print("=" * 62)
    print("  L0 基线模型 — 单周期确定性凹规划")
    print("=" * 62)
    print(f"  决策变量数: {len(P)}   资源约束数: {len(B)}")
    print()
    print(f"  {'变量':<8}{'取值':>10}{'上限':>10}")
    print("  " + "-" * 28)
    for i, (xi, ui) in enumerate(zip(x_opt, U)):
        print(f"  x{i+1:<7}{xi:>10.3f}{ui:>10.1f}")

    print()
    print(f"  目标收益: {profit:.3f}")
    print(f"  可行性  : {'✅ 满足全部约束' if feasible else '❌ 存在越界'}")
    for j, (u_j, b_j) in enumerate(zip(usage, B)):
        ratio = u_j / b_j * 100 if b_j else 0
        print(f"    资源{j+1}: {u_j:8.3f} / {b_j:<8.1f} （占用 {ratio:5.1f}%）")

    baseline = None
    if a.compare:
        x_lin = linear_baseline()
        lin_profit, lin_usage, lin_feasible = evaluate(x_lin)
        baseline = {
            "x": x_lin.tolist(),
            "profit": lin_profit,
            "feasible": lin_feasible,
        }
        gain = profit - lin_profit
        pct = gain / abs(lin_profit) * 100 if lin_profit else 0.0

        print()
        print("  ── 与线性基线对比（消融）──")
        print(f"    {'方案':<16}{'收益':>12}{'可行性':>10}")
        print("    " + "-" * 38)
        print(f"    {'线性（角点解）':<16}{lin_profit:>12.3f}{'✅' if lin_feasible else '❌':>10}")
        print(f"    {'凹规划（本模型）':<16}{profit:>12.3f}{'✅' if feasible else '❌':>10}")
        print(f"    → 凹规划改进: {gain:+.3f}（{pct:+.1f}%）")
        print()
        print("    说明: 线性模型把资源全押在单位收益最高者上，得到角点解；")
        print("          凹项刻画边际收益递减，因而给出更均衡、更接近实际的分配。")

    if a.json:
        out = Path(a.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "level": "L0",
            "model": "单周期确定性凹规划",
            "x_opt": x_opt.tolist(),
            "profit": profit,
            "usage": usage.tolist(),
            "capacity": B.tolist(),
            "feasible": feasible,
            "n_eval": res.get("n_eval"),
            "baseline": baseline,
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print(f"  结果已写入: {out}")

    print()
    print("  下一步: 按 references/model-upgrade.md 逐级升级")
    print("          L1 多周期动态规划 → L2 随机/鲁棒 → L3 多目标 → L4 机理-数据融合")
    return 0 if feasible else 1


if __name__ == "__main__":
    sys.exit(main())
