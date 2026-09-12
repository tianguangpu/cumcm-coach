"""
scipilot-figure-skill :: visual_qa.py
=====================================
出图后的「程序自检」+「渲染预览」——自检闭环的机器那一层。
Usage
-----
    from visual_qa import render_preview, audit_layout, print_report
    fig, ax = plt.subplots()
    png = render_preview(fig, "figs/_preview.png", dpi=150)
    issues = audit_layout(fig)
    print_report(issues)
"""
from __future__ import annotations
import argparse
import io
import logging
import os
import sys
import warnings
import matplotlib.pyplot as plt
import matplotlib.text as mtext
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
SEVERITY = {"INFO": 0, "WARN": 1, "FAIL": 2}
_GLYPH_MARKERS = ("missing from", "Glyph", "findfont")
def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
class _GlyphLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages: list[str] = []
    def emit(self, record):
        msg = record.getMessage()
        if any(m in msg for m in _GLYPH_MARKERS):
            self.messages.append(msg)
def _draw_and_collect_glyph_warnings(fig) -> list[str]:
    handler = _GlyphLogHandler()
    mpl_logger = logging.getLogger("matplotlib")
    prev_level = mpl_logger.level
    mpl_logger.setLevel(logging.WARNING)
    mpl_logger.addHandler(handler)
    collected: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100)
            buf.close()
        for w in wlist:
            s = str(w.message)
            if any(m in s for m in _GLYPH_MARKERS):
                collected.append(s)
    finally:
        mpl_logger.removeHandler(handler)
        mpl_logger.setLevel(prev_level)
    collected.extend(handler.messages)
    seen, uniq = set(), []
    for m in collected:
        if m not in seen:
            seen.add(m)
            uniq.append(m)
    return uniq
def _visible_texts(fig) -> list:
    out = []
    for t in fig.findobj(mtext.Text):
        try:
            if t.get_visible() and t.get_text().strip():
                out.append(t)
        except Exception:
            continue
    return out
def audit_layout(fig, clip_tol_px: float = 2.0, overlap_tol_px: float = 1.0
                 ) -> list[tuple[str, str]]:
    """对一张 matplotlib Figure 做版面自检。"""
    issues: list[tuple[str, str]] = []
    glyph_msgs = _draw_and_collect_glyph_warnings(fig)
    if glyph_msgs:
        sample = " | ".join(glyph_msgs[:3])
        issues.append((
            "FAIL",
            f"检测到缺字，成图会出现方框/乱码：{sample[:240]}。"
            "中文图请先 setup_style(lang='zh') 配置 CJK 字体；"
            "若是负号方框，确认 axes.unicode_minus=False。"
        ))
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    W = float(fig.bbox.width)
    H = float(fig.bbox.height)
    tick_ids = set()
    for ax in fig.axes:
        for tl in (*ax.get_xticklabels(), *ax.get_xticklabels(minor=True),
                   *ax.get_yticklabels(), *ax.get_yticklabels(minor=True)):
            tick_ids.add(id(tl))
    clipped: list[str] = []
    for t in _visible_texts(fig):
        if id(t) in tick_ids:
            continue
        try:
            bb = t.get_window_extent(renderer)
        except Exception:
            continue
        if (bb.x0 < -clip_tol_px or bb.y0 < -clip_tol_px
                or bb.x1 > W + clip_tol_px or bb.y1 > H + clip_tol_px):
            txt = t.get_text().strip().replace("\n", " ")
            if txt:
                clipped.append(txt[:24])
    if clipped:
        uniq = list(dict.fromkeys(clipped))[:6]
        issues.append((
            "WARN",
            f"以下文字可能超出画布被裁切：{uniq}。"
            "跑 finalize_figure(fig) 或导出时 bbox_inches='tight' 兜底。"
        ))
    overlap_axes = 0
    for ax in fig.axes:
        if ax.get_subplotspec() is None:
            continue
        if _ticklabels_overlap(ax.get_xticklabels(), renderer,
                               axis="x", tol=overlap_tol_px):
            overlap_axes += 1
            continue
        if _ticklabels_overlap(ax.get_yticklabels(), renderer,
                               axis="y", tol=overlap_tol_px):
            overlap_axes += 1
    if overlap_axes:
        issues.append((
            "WARN",
            f"{overlap_axes} 个子图存在刻度标签重叠。"
            "x 轴：ax.tick_params(axis='x', rotation=30) 或减少刻度；"
            "y 轴：增大子图高度或减少刻度数。"
        ))
    return issues
def _ticklabels_overlap(labels, renderer, axis: str, tol: float) -> bool:
    boxes = []
    for l in labels:
        try:
            if l.get_visible() and l.get_text().strip():
                boxes.append(l.get_window_extent(renderer))
        except Exception:
            continue
    if len(boxes) < 2:
        return False
    if axis == "x":
        boxes.sort(key=lambda b: b.x0)
        return any(a.x1 - b.x0 > tol for a, b in zip(boxes, boxes[1:]))
    else:
        boxes.sort(key=lambda b: b.y0)
        return any(a.y1 - b.y0 > tol for a, b in zip(boxes, boxes[1:]))
def render_preview(fig_or_path, out_png: str = "_preview.png",
                   dpi: int = 150) -> str:
    """渲一张 PNG 预览供 AI 读图。"""
    if hasattr(fig_or_path, "savefig"):
        _ensure_parent(out_png)
        fig_or_path.savefig(out_png, dpi=dpi, bbox_inches="tight")
        return out_png
    path = str(fig_or_path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext in {"png", "tif", "tiff", "jpg", "jpeg", "bmp"}:
        return path
    if ext == "pdf":
        try:
            import fitz
        except ImportError as e:
            raise RuntimeError(
                "把 PDF 渲成预览需要 PyMuPDF（pip install pymupdf）。"
            ) from e
        doc = fitz.open(path)
        pix = doc[0].get_pixmap(dpi=dpi)
        _ensure_parent(out_png)
        pix.save(out_png)
        doc.close()
        return out_png
    raise RuntimeError(f"不支持从 .{ext} 生成预览；请传 Figure 对象或位图。")
def print_report(issues: list[tuple[str, str]]) -> str:
    if not issues:
        print("  [PASS] 程序自检未发现缺字 / 裁切 / 刻度重叠。")
        print("  >>> 仍需 AI 读图复核感知性问题（见 visual_review.md）。")
        return "PASS"
    max_sev = max(SEVERITY[s] for s, _ in issues)
    verdict = {2: "FAIL", 1: "WARN", 0: "INFO"}[max_sev]
    for sev, msg in sorted(issues, key=lambda x: -SEVERITY[x[0]]):
        print(f"  [{sev}] {msg}")
    print(f"  >>> verdict: {verdict}（修完再渲一次 PNG 让 AI 读图复核）")
    return verdict
def _demo() -> int:
    import numpy as np
    rng = np.random.default_rng(1)
    fig, ax = plt.subplots(figsize=(3.0, 2.2))
    cats = [f"very_long_condition_name_{i}" for i in range(12)]
    ax.bar(range(12), rng.random(12))
    ax.set_xticks(range(12))
    ax.set_xticklabels(cats)
    ax.set_title("An intentionally overlong title that runs off the canvas edge")
    ax.set_ylabel("value")
    print("=== visual_qa demo ===")
    issues = audit_layout(fig)
    print_report(issues)
    out = render_preview(fig, "./visual_qa_demo.png", dpi=120)
    print(f"\n预览已写出：{out}")
    return 0
def _cli() -> int:
    p = argparse.ArgumentParser(description="scipilot-figure-skill visual QA")
    p.add_argument("target", nargs="?", help="图片路径；或 'demo'")
    p.add_argument("--preview", metavar="OUT.png", help="把 target 渲成 PNG 预览到此路径")
    p.add_argument("--dpi", type=int, default=150)
    args = p.parse_args()
    if args.target == "demo" or args.target is None:
        return _demo()
    if args.preview:
        out = render_preview(args.target, args.preview, dpi=args.dpi)
        print(f"[visual_qa] 预览：{out}")
    return 0
if __name__ == "__main__":
    sys.exit(_cli())