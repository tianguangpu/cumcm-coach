"""
scipilot-figure-skill :: layout_tools.py
========================================
排版安全网 + 多面板子图编号对齐。
解决两类高频成图问题：
1. **子图 a/b/c 编号乱放、横竖不对齐** —— `add_panel_labels()`
2. **标题/轴标签被裁、图例压数据、子图互相重叠** —— `finalize_figure()`
Usage
-----
    from layout_tools import add_panel_labels, finalize_figure
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))
    finalize_figure(fig)
    add_panel_labels(fig, style="nature")
CLI: ``python layout_tools.py demo --out ./panel_demo``
"""
from __future__ import annotations
import argparse
import string
import sys
import matplotlib.pyplot as plt
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
PANEL_STYLES = {
    "nature": lambda s: s,
    "science": lambda s: s,
    "ieee": lambda s: f"({s})",
    "paren": lambda s: f"({s})",
    "upper": lambda s: s.upper(),
    "upper_paren": lambda s: f"({s.upper()})",
}
def _letter_sequence(n: int) -> list[str]:
    letters = string.ascii_lowercase
    out: list[str] = []
    for i in range(n):
        if i < 26:
            out.append(letters[i])
        else:
            out.append(letters[i // 26 - 1] + letters[i % 26])
    return out
def _data_axes(fig) -> list:
    return [ax for ax in fig.axes if ax.get_subplotspec() is not None]
def add_panel_labels(
    fig,
    axes=None,
    labels=None,
    style: str = "nature",
    fontsize=None,
    fontweight: str = "bold",
    x_offset_pt: float = -20.0,
    y_offset_pt: float = 2.0,
    ha: str = "right",
    va: str = "bottom",
    color: str = "black",
):
    """给多面板图的每个子图打统一对齐的 a/b/c 编号。"""
    if axes is None:
        axes = _data_axes(fig)
        axes = sorted(
            axes,
            key=lambda ax: (-round(ax.get_position().y1, 3),
                            round(ax.get_position().x0, 3)),
        )
    axes = list(axes)
    n = len(axes)
    if n == 0:
        return []
    if labels is None:
        fmt = PANEL_STYLES.get(style)
        if fmt is None:
            raise ValueError(f"Unknown panel style: {style!r}. Choose from {sorted(PANEL_STYLES)}")
        labels = [fmt(s) for s in _letter_sequence(n)]
    elif len(labels) < n:
        raise ValueError(f"提供了 {len(labels)} 个 labels 但有 {n} 个子图需要标注。")
    if fontsize is None:
        fontsize = plt.rcParams.get("axes.labelsize", 9)
    placed = []
    for ax, lab in zip(axes, labels):
        t = ax.annotate(
            lab,
            xy=(0, 1), xycoords="axes fraction",
            xytext=(x_offset_pt, y_offset_pt), textcoords="offset points",
            fontsize=fontsize, fontweight=fontweight, color=color,
            ha=ha, va=va,
            annotation_clip=False,
        )
        placed.append(t)
    return placed
def finalize_figure(fig, prefer: str = "constrained", verbose: bool = False) -> str:
    """出图前兜底理顺版面。"""
    used = "none"
    if prefer == "constrained":
        try:
            fig.set_layout_engine("constrained")
            fig.canvas.draw()
            used = "constrained"
        except Exception:
            used = "none"
    if used == "none":
        try:
            with _suppress_tight_warnings():
                fig.tight_layout()
            used = "tight"
        except Exception:
            used = "none"
    if verbose:
        print(f"[layout_tools] finalize_figure -> {used}")
    return used
class _suppress_tight_warnings:
    def __enter__(self):
        import warnings
        self._cm = warnings.catch_warnings()
        self._cm.__enter__()
        warnings.simplefilter("ignore")
        return self
    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)
def _demo(out_basename: str) -> None:
    import numpy as np
    rng = np.random.default_rng(0)
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))
    axes[0, 0].plot(np.arange(10), rng.normal(0, 1, 10), marker="o")
    axes[0, 0].set_ylabel("score")
    axes[0, 1].plot(np.arange(10), rng.normal(0, 1, 10) * 1e6, marker="s")
    axes[0, 1].set_ylabel("count")
    axes[1, 0].bar(np.arange(5), rng.normal(0, 1, 5))
    axes[1, 0].set_ylabel("Δ expression (a.u.)")
    axes[1, 0].set_xlabel("condition")
    axes[1, 1].scatter(rng.random(20), rng.random(20))
    axes[1, 1].set_ylabel("p")
    axes[1, 1].set_xlabel("x")
    used = finalize_figure(fig, verbose=True)
    labels = add_panel_labels(fig, style="nature")
    png = f"{out_basename}.png"
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print(f"[layout_tools] layout={used}, labels={[t.get_text() for t in labels]}")
def _cli() -> int:
    p = argparse.ArgumentParser(description="scipilot-figure-skill layout tools")
    p.add_argument("cmd", choices=["demo"], help="`demo`: 画一张 2x2 验证子图标签对齐")
    p.add_argument("--out", default="./panel_demo", help="输出 basename")
    args = p.parse_args()
    if args.cmd == "demo":
        _demo(args.out)
    return 0
if __name__ == "__main__":
    sys.exit(_cli())