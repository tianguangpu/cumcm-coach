"""
v7_styles.py — v7 统一图表样式模块
====================================
封装 SciencePlots + tueplots + 5 套学术调色板，一行代码切换期刊风格。

用法：
    from v7_styles import apply_journal_style, get_palette, setup_chinese, quick_export

    # 切换到 Nature 风格
    apply_journal_style('nature')

    # 获取 IEEE 调色板（前 6 色）
    colors = get_palette('ieee', 6)

    # 中文字体配置
    setup_chinese()

    # 快速导出
    quick_export(fig, 'fig1_result', outdir='figures')
"""
from __future__ import annotations

import os
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np

# ── 检查可选依赖 ──────────────────────────────────────────────
_HAS_SCIENCEPLOTS = False
_HAS_TUEPLOTS = False

try:
    import scienceplots  # noqa: F401
    _HAS_SCIENCEPLOTS = True
except ImportError:
    pass

try:
    from tueplots import bundles, figsizes, fontsizes  # noqa: F401
    _HAS_TUEPLOTS = True
except ImportError:
    pass


# ── 5 套学术调色板（RGB 0-1）──────────────────────────────────
PALETTES: dict[str, np.ndarray] = {
    "nature": np.array([
        [0, 114, 178], [230, 75, 53], [91, 158, 213], [245, 160, 0],
        [90, 158, 75], [184, 84, 80], [76, 114, 176], [204, 184, 116],
    ]) / 255,
    "science": np.array([
        [255, 0, 0], [0, 0, 255], [0, 170, 0], [255, 127, 0],
        [140, 0, 140], [0, 139, 139], [220, 20, 60], [30, 144, 255],
    ]) / 255,
    "qualitative": np.array([
        [102, 194, 165], [252, 141, 98], [141, 179, 211], [231, 138, 194],
        [166, 216, 84], [255, 217, 47], [229, 196, 148], [179, 179, 179],
        [255, 255, 179], [128, 177, 211], [179, 222, 105], [255, 251, 174],
    ]) / 255,
    "diverging": np.array([
        [33, 102, 172], [67, 147, 195], [146, 197, 222], [222, 235, 247],
        [247, 247, 247], [253, 235, 213], [252, 141, 89], [215, 48, 39],
        [165, 0, 38],
    ]) / 255,
    "ieee": np.array([
        [0, 68, 136], [204, 102, 119], [68, 170, 153], [221, 204, 119],
        [102, 204, 238], [170, 136, 187], [238, 102, 85], [0, 136, 187],
    ]) / 255,
}

# SciencePlots 内置风格到期刊的映射
_JOURNAL_TO_SCIENCEPLOTS: dict[str, list[str]] = {
    "nature":   ["science", "nature", "no-latex"],
    "science":  ["science", "high-vis", "no-latex"],
    "ieee":     ["science", "ieee", "no-latex"],
    "aaas":     ["science", "bright", "no-latex"],
    "aps":      ["science", "no-latex"],
    "default":  ["science", "no-latex"],
}

# tueplots 期刊配置
_JOURNAL_TO_TUEPLOTS: dict[str, str] = {
    "nature":   "neurips2024",   # Nature 无专属，NeurIPS 尺寸接近
    "science":  "icml2024",
    "ieee":     "ieee2024",
    "aaas":     "icml2024",
    "aps":      "icml2024",
    "default":  "icml2024",
}


def get_palette(name: str = "nature", n: int | None = None) -> np.ndarray:
    """获取调色板。

    Args:
        name: 调色板名 (nature/science/qualitative/diverging/ieee)
        n: 取前 n 色；None 返回全部

    Returns:
        (n, 3) RGB 数组，值域 [0, 1]
    """
    name = name.lower()
    if name not in PALETTES:
        raise ValueError(f"未知调色板 '{name}'，可选: {list(PALETTES.keys())}")
    pal = PALETTES[name]
    if n is not None:
        pal = pal[:n]
    return pal


def setup_chinese(font_size: int = 9) -> None:
    """配置中文字体（SimHei）+ 关闭负号乱码。"""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["SimHei", "Microsoft YaHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": font_size,
    })


def apply_journal_style(
    journal: str = "nature",
    *,
    setup_chinese_font: bool = True,
    dpi: int = 600,
    font_size: int = 9,
) -> None:
    """一行切换期刊风格。

    优先用 SciencePlots 样式，fallback 到 tueplots + 手动配置。

    Args:
        journal: 期刊名 (nature/science/ieee/aaas/aps/default)
        setup_chinese_font: 是否同时配置中文字体
        dpi: 输出分辨率
        font_size: 基础字号
    """
    journal = journal.lower()

    # 1) SciencePlots 样式（核心）
    #    必须先禁用 usetex，否则 SciencePlots 会尝试 LaTeX 渲染
    plt.rcParams["text.usetex"] = False
    if _HAS_SCIENCEPLOTS:
        styles = _JOURNAL_TO_SCIENCEPLOTS.get(journal, ["science", "no-latex"])
        try:
            plt.style.use(styles)
        except Exception:
            # SciencePlots 版本差异，fallback 到基础
            plt.style.use(["science", "no-latex"])
        # 强制关闭 usetex（SciencePlots 某些风格会开启）
        plt.rcParams["text.usetex"] = False

    # 2) tueplots 期刊尺寸/字号
    if _HAS_TUEPLOTS:
        try:
            bundle_name = _JOURNAL_TO_TUEPLOTS.get(journal, "icml2024")
            if hasattr(bundles, bundle_name):
                plt.rcParams.update(getattr(bundles, bundle_name)())
            # 通用字号
            plt.rcParams.update(fontsizes.icml2024())
        except Exception:
            pass

    # 3) 基础配置（覆盖/补充）
    #    确保关闭 LaTeX 渲染（中文环境通常没有完整 LaTeX 链）
    plt.rcParams["text.usetex"] = False
    plt.rcParams.update({
        "figure.dpi": dpi,
        "savefig.dpi": dpi,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,        # TrueType 嵌入，期刊不拒
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "font.size": font_size,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.4,
        "legend.frameon": False,
        "legend.fontsize": font_size - 1,
    })

    # 4) 中文字体
    if setup_chinese_font:
        setup_chinese(font_size)


def quick_export(
    fig,
    name: str,
    outdir: str = "figures",
    formats: Sequence[str] = ("png", "pdf"),
    dpi: int = 600,
) -> list[str]:
    """快速导出图表。

    Args:
        fig: matplotlib Figure
        name: 文件名（不含扩展名）
        outdir: 输出目录
        formats: 导出格式列表
        dpi: 分辨率

    Returns:
        导出文件路径列表
    """
    saved = []
    for fmt in formats:
        fmt = fmt.lower().lstrip(".")
        subdir = os.path.join(outdir, fmt)
        os.makedirs(subdir, exist_ok=True)
        path = os.path.join(subdir, f"{name}.{fmt}")
        kwargs: dict = {"bbox_inches": "tight", "pad_inches": 0.05}
        if fmt in ("png", "tiff", "tif", "jpg", "jpeg"):
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
        saved.append(path)
        print(f"[v7] saved {path}")
    return saved


def demo_styles(outdir: str = "v7_style_demo") -> None:
    """生成 6 张演示图（6 种期刊风格），用于快速验证。"""
    os.makedirs(outdir, exist_ok=True)
    x = np.linspace(0, 10, 50)
    rng = np.random.default_rng(42)

    for journal in ("nature", "science", "ieee", "aaas", "aps", "default"):
        # 重置 rcParams
        plt.rcdefaults()
        try:
            apply_journal_style(journal, setup_chinese_font=False)
        except Exception as e:
            print(f"[v7] WARNING: style '{journal}' failed: {e}")
            continue

        fig, ax = plt.subplots(figsize=(3.5, 2.625))
        # aaas/aps 无专属调色板，fallback 到 science
        pal_name = journal if journal in PALETTES else "science"
        pal = get_palette(pal_name, 4)
        for i, (label, ls) in enumerate(zip(
            ["sin", "cos", "sin+noise", "cos+noise"],
            ["-", "--", "-.", ":"]
        )):
            y = np.sin(x + i * 0.5) + rng.normal(0, 0.15, x.size)
            ax.plot(x, y, label=label, color=pal[i % len(pal)],
                    linestyle=ls, linewidth=1.2, marker="o", markersize=2,
                    markevery=5)
        ax.set_xlabel("x (a.u.)")
        ax.set_ylabel("y (a.u.)")
        ax.legend()
        ax.set_title(f"Style: {journal}", fontsize=10, fontweight="bold")

        path = os.path.join(outdir, f"demo_{journal}")
        quick_export(fig, path, formats=["png", "pdf"])
        plt.close(fig)

    print(f"\n[v7] Demo 完成！{outdir}/ 下有 6 张图，对比检查字号/配色/网格。")


# ── CLI ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        out = sys.argv[2] if len(sys.argv) > 2 else "v7_style_demo"
        demo_styles(out)
    else:
        print("用法: python v7_styles.py demo [输出目录]")
        print(f"SciencePlots: {'✓' if _HAS_SCIENCEPLOTS else '✗'}")
        print(f"tueplots:     {'✓' if _HAS_TUEPLOTS else '✗'}")
        print(f"调色板:       {list(PALETTES.keys())}")
