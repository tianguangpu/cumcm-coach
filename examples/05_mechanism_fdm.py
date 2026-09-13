"""示例 5：A 题机理建模 —— 一维热传导有限差分（FDM）

A 题（机理类）通常要求建立物理方程并数值求解。本示例演示
一维热传导（扩散）方程的显式有限差分离散与求解。

方程：∂u/∂t = D · ∂²u/∂x²

运行::

    python examples/05_mechanism_fdm.py

输出:
    examples/output/05_heat_fdm.png
"""

import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from algorithms.mechanistic.fdm_1d import heat_1d_explicit  # noqa: E402


def main():
    D = 0.1       # 扩散系数
    L = 1.0       # 杆长
    T = 0.5       # 总时间
    nx, nt = 50, 5000

    def u0(x):
        """初始温度分布：中间高、两端低（高斯脉冲）"""
        return np.exp(-((x - L / 2) ** 2) / 0.01)

    # heat_1d_explicit 返回 (x, t, U)，U 形状 (nt+1, nx+1)，U[i,:] 为 t[i] 时刻空间分布
    x, t, U = heat_1d_explicit(D, L, T, nx=nx, nt=nt, u0=u0, bc=(0.0, 0.0))

    print("=" * 60)
    print("  A 题机理：一维热传导方程显式 FDM 求解")
    print("=" * 60)
    print(f"  扩散系数 D={D}  杆长 L={L}  总时间 T={T}")
    print(f"  网格 {nx} 点 × {nt} 步，解的形状 {U.shape}")
    print(f"  末端 (x=L) 最终温度: {U[-1, -1]:.4f}")
    print(f"  数值稳定性条件 dt/dx² = {(T/nt)/((L/nx)**2):.4f}（< 0.5 才稳定）")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(7, 4))
        for i in [0, nt // 10, nt // 4, nt // 2, nt - 1]:
            ax.plot(x, U[i, :], label=f"t={t[i]:.2f}", linewidth=1.6)
        ax.set_xlabel("位置 x")
        ax.set_ylabel("温度 u")
        ax.set_title("一维热传导的温度演化（显式 FDM）")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

        out = Path(__file__).resolve().parent / "output" / "05_heat_fdm.png"
        out.parent.mkdir(exist_ok=True)
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"\n  温度演化图已保存: {out}")
    except ImportError:
        print("\n  [跳过绘图] matplotlib 未安装")

    print("\n提示：把热传导方程换成你的机理方程（对流/反应扩散/波动），")
    print("      调整 D、边界条件即可用于实际 A 题。")


if __name__ == "__main__":
    main()
