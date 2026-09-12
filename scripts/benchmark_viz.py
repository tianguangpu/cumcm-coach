#!/usr/bin/env python3
"""
算法基准测试可视化

生成算法性能对比雷达图和柱状图。

Usage:
    python scripts/benchmark_viz.py --output reports/benchmark.png
    python scripts/benchmark_viz.py --algorithms ga,de,sa_pso --output reports/benchmark.png
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# 默认配色方案（学术风格）
COLORS = {
    "primary": "#2166AC",
    "secondary": "#D6604D",
    "tertiary": "#4DAF4A",
    "quaternary": "#7570B3",
    "quinary": "#E6AB02",
}


def generate_benchmark_data() -> Dict[str, Dict[str, float]]:
    """
    生成基准测试数据（示例数据，实际应从测试结果读取）。

    Returns:
        Dict: 算法性能数据
    """
    return {
        "GA": {"accuracy": 0.92, "speed": 0.75, "robustness": 0.88, "convergence": 0.85, "scalability": 0.80},
        "DE": {"accuracy": 0.95, "speed": 0.70, "robustness": 0.92, "convergence": 0.90, "scalability": 0.85},
        "SA-PSO": {"accuracy": 0.97, "speed": 0.65, "robustness": 0.95, "convergence": 0.93, "scalability": 0.88},
        "NSGA-II": {"accuracy": 0.90, "speed": 0.60, "robustness": 0.85, "convergence": 0.82, "scalability": 0.92},
        "VRP-GA": {"accuracy": 0.88, "speed": 0.80, "robustness": 0.82, "convergence": 0.80, "scalability": 0.75},
    }


def plot_radar_chart(
    data: Dict[str, Dict[str, float]],
    output: str = "reports/benchmark_radar.png",
    figsize: tuple = (10, 8),
) -> None:
    """
    绘制雷达图。

    Args:
        data: 算法性能数据
        output: 输出文件路径
        figsize: 图片尺寸
    """
    algorithms = list(data.keys())
    metrics = list(data[algorithms[0]].keys())
    n_metrics = len(metrics)

    # 计算角度
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # 绘制每个算法
    color_list = list(COLORS.values())
    for idx, algo in enumerate(algorithms):
        values = [data[algo][m] for m in metrics]
        values += values[:1]  # 闭合

        color = color_list[idx % len(color_list)]
        ax.plot(angles, values, "o-", linewidth=2, label=algo, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    # 设置标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.7)

    ax.set_title("算法性能对比雷达图", fontsize=14, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)

    plt.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"雷达图已保存: {output}")


def plot_bar_chart(
    data: Dict[str, Dict[str, float]],
    output: str = "reports/benchmark_bar.png",
    figsize: tuple = (12, 6),
) -> None:
    """
    绘制柱状图。

    Args:
        data: 算法性能数据
        output: 输出文件路径
        figsize: 图片尺寸
    """
    algorithms = list(data.keys())
    metrics = list(data[algorithms[0]].keys())
    n_algos = len(algorithms)
    n_metrics = len(metrics)

    fig, ax = plt.subplots(figsize=figsize)

    x = np.arange(n_metrics)
    width = 0.15

    color_list = list(COLORS.values())
    for idx, algo in enumerate(algorithms):
        values = [data[algo][m] for m in metrics]
        offset = (idx - n_algos / 2 + 0.5) * width
        color = color_list[idx % len(color_list)]
        bars = ax.bar(x + offset, values, width, label=algo, color=color, edgecolor="white", linewidth=0.5)

        # 添加数值标签
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_xlabel("性能指标", fontsize=12)
    ax.set_ylabel("得分", fontsize=12)
    ax.set_title("算法性能对比柱状图", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    plt.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"柱状图已保存: {output}")


def plot_summary_table(
    data: Dict[str, Dict[str, float]],
    output: str = "reports/benchmark_table.md",
) -> None:
    """
    生成 Markdown 格式的基准测试汇总表。

    Args:
        data: 算法性能数据
        output: 输出文件路径
    """
    algorithms = list(data.keys())
    metrics = list(data[algorithms[0]].keys())

    lines = ["# 算法基准测试报告", "", "## 性能对比表", "", "| 算法 | " + " | ".join(metrics) + " | 综合得分 |", "|"]
    lines[0] = "# 算法基准测试报告"
    lines.append("| --- | " + " | ".join(["---"] * len(metrics)) + " | --- |")

    for algo in algorithms:
        values = [data[algo][m] for m in metrics]
        avg_score = sum(values) / len(values)
        row = f"| {algo} | " + " | ".join([f"{v:.3f}" for v in values]) + f" | {avg_score:.3f} |"
        lines.append(row)

    lines.extend(
        [
            "",
            "## 指标说明",
            "",
            "- **accuracy**: 求解精度（与已知最优解的接近程度）",
            "- **speed**: 求解速度（归一化处理）",
            "- **robustness**: 鲁棒性（多次运行的稳定性）",
            "- **convergence**: 收敛性（收敛速度和稳定性）",
            "- **scalability**: 可扩展性（高维问题的表现）",
            "",
            "## 推荐算法",
            "",
        ]
    )

    # 推荐算法
    best_algo = max(algorithms, key=lambda a: sum(data[a].values()) / len(data[a]))
    lines.append(f"综合性能最优：**{best_algo}**")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"汇总表已保存: {output}")


def main():
    parser = argparse.ArgumentParser(description="算法基准测试可视化")
    parser.add_argument("--output", "-o", default="reports/benchmark.png", help="输出文件路径")
    parser.add_argument("--algorithms", "-a", default=None, help="算法列表，逗号分隔")
    parser.add_argument("--format", "-f", choices=["png", "pdf", "svg"], default="png", help="输出格式")

    args = parser.parse_args()

    # 生成基准数据（实际应从测试结果读取）
    data = generate_benchmark_data()

    # 筛选算法
    if args.algorithms:
        algo_list = [a.strip() for a in args.algorithms.split(",")]
        data = {k: v for k, v in data.items() if k in algo_list}

    # 生成可视化
    output_base = Path(args.output).stem
    output_dir = Path(args.output).parent

    plot_radar_chart(data, str(output_dir / f"{output_base}_radar.{args.format}"))
    plot_bar_chart(data, str(output_dir / f"{output_base}_bar.{args.format}"))
    plot_summary_table(data, str(output_dir / f"{output_base}_table.md"))

    print(f"\n基准测试完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()
