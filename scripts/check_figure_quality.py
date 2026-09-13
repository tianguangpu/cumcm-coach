"""check_figure_quality.py — 图表视觉质量检查（"看得舒服"）

检查绘图脚本的「画布尺寸 ↔ 字号」是否匹配论文插入尺寸。

**原理**

    最终字号 = 设定字号 × (论文插入宽度 / figsize 宽度)

论文中图片被缩放到插入宽度（A4 正文整幅约 16cm）后，字号会同比缩小。
若用 ``figsize=(14, 7)`` 画图再缩到 16cm，缩放系数仅 0.45 ——
设定 12pt 的标签实际只剩 5.4pt，低于 A4 印刷可读下限 8pt，读者看着费劲。

**用法**::

    python scripts/check_figure_quality.py figures/            # 检查目录下所有绘图脚本
    python scripts/check_figure_quality.py --script fig1.py    # 检查单个文件
    python scripts/check_figure_quality.py --width-cm 8        # 单栏窄图

退出码: 0 = 全部达标; 1 = 存在不达标项。
"""

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# A4 印刷可读下限：任何元素字号不得低于此值
MIN_PRINTABLE_PT = 8.0

# figsize 正则：figsize=(6.3, 3.5) / figsize=(6.3,3.5) / figsize = (6.3, 3.5)
RE_FIGSIZE = re.compile(
    r"""figsize\s*=\s*\(\s*([\d.]+)\s*,\s*([\d.]+)\s*\)""", re.VERBOSE
)
# 字号设置：fontsize=9 / font.size': 9 / 'font.size': 9
RE_FONTSIZE_KW = re.compile(r"""fontsize\s*=\s*([\d.]+)""")
# 兼容两种写法：字典 'font.size': 9；赋值 rcParams['font.size'] = 9（引号后还有 ]）
RE_RCPARAM_SIZE = re.compile(
    r"""font\.size['"]?\s*\]?\s*(?::|=)\s*([\d.]+)""")
RE_RCPARAM_LABEL = re.compile(
    r"""(?:axes\.labelsize|xtick\.labelsize|ytick\.labelsize|legend\.fontsize)['"]?\s*\]?\s*(?::|=)\s*([\d.]+)"""
)

# 若脚本未显式设定字号，matplotlib 默认值（会被缩放）
MPL_DEFAULT_SIZE = 10.0


def _collect_font_sizes(src: str) -> list[tuple[str, float]]:
    """抽取脚本中出现的所有字号设置，返回 (来源描述, pt) 列表。"""
    found: list[tuple[str, float]] = []

    for m in RE_FONTSIZE_KW.finditer(src):
        found.append(("fontsize=", float(m.group(1))))
    for m in RE_RCPARAM_SIZE.finditer(src):
        found.append(("rcParams['font.size']", float(m.group(1))))
    for m in RE_RCPARAM_LABEL.finditer(src):
        found.append(("rcParams[刻度/图例/轴标题]", float(m.group(1))))

    return found


def check_script(path: Path, target_width_cm: float) -> list[dict]:
    """检查单个脚本，返回问题列表（空列表表示达标）。"""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [{"file": str(path), "level": "ERR", "msg": f"无法读取: {e}"}]

    # 只检查真正绘图的脚本：不含 matplotlib 调用的脚本（如纯数据预处理）
    # 没有画布尺寸与字号可言，报「未设定字号」属误报
    if not re.search(r"\bmatplotlib\b|\bplt\.|\bsns\.|\bseaborn\b", src):
        return []

    issues: list[dict] = []

    figsizes = [(float(w), float(h)) for w, h in RE_FIGSIZE.findall(src)]
    if not figsizes:
        # 没有显式 figsize：matplotlib 默认 6.4×4.8 英寸，通常尚可
        widths = [6.4]
    else:
        widths = [w for w, _ in figsizes]

    # 逐 figsize 检查（取最宽的那张作为判据：越宽缩放越狠）
    max_width_in = max(widths)
    max_width_cm = max_width_in * 2.54
    scale = target_width_cm / max_width_cm if max_width_cm > 0 else 1.0

    if scale < 0.99:
        issues.append({
            "file": str(path),
            "level": "WARN",
            "msg": (
                f"画布宽 {max_width_cm:.1f}cm 超过论文插入宽 {target_width_cm:.1f}cm，"
                f"将被缩至 {scale:.2f} 倍；建议 figsize 宽 ≤ {target_width_cm / 2.54:.2f} 英寸"
            ),
        })

    # 字号检查
    sizes = _collect_font_sizes(src)
    if not sizes:
        sizes = [("matplotlib 默认", MPL_DEFAULT_SIZE)]
        issues.append({
            "file": str(path),
            "level": "INFO",
            "msg": "未显式设定字号，按 matplotlib 默认 10pt 估算；建议用 setup_style() 统一设定",
        })

    for label, pt in sizes:
        effective = pt * scale
        if effective < MIN_PRINTABLE_PT - 0.01:
            issues.append({
                "file": str(path),
                "level": "FAIL",
                "msg": (
                    f"{label}{pt:g}pt × {scale:.2f} 缩放 = 实际 {effective:.1f}pt "
                    f"< {MIN_PRINTABLE_PT:g}pt 印刷红线"
                ),
            })

    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="图表视觉质量检查（尺寸-字号匹配）")
    p.add_argument("path", nargs="?", default="figures",
                   help="绘图脚本目录或文件（默认 figures/）")
    p.add_argument("--script", help="指定单个脚本文件")
    p.add_argument("--width-cm", type=float, default=16.0,
                   help="论文中图片插入宽度（cm）。整幅 16、单栏窄图 8、方图 14")
    a = p.parse_args()

    targets: list[Path] = []
    if a.script:
        targets = [Path(a.script)]
    else:
        root = Path(a.path)
        if root.is_file():
            targets = [root]
        elif root.is_dir():
            targets = sorted(root.rglob("*.py"))
        else:
            print(f"[err] 路径不存在: {root}")
            return 1

    if not targets:
        print(f"[warn] 未找到 Python 绘图脚本（{a.path}）")
        return 0

    print("=" * 66)
    print("  图表视觉质量检查 — 尺寸与字号匹配")
    print(f"  论文插入宽度: {a.width_cm:g}cm   印刷可读下限: {MIN_PRINTABLE_PT:g}pt")
    print("=" * 66)

    all_issues: list[dict] = []
    for t in targets:
        all_issues.extend(check_script(t, a.width_cm))

    if not all_issues:
        print(f"\n  [OK] 已检查 {len(targets)} 个脚本，全部达标。")
        return 0

    fails = [i for i in all_issues if i["level"] == "FAIL"]
    warns = [i for i in all_issues if i["level"] == "WARN"]
    infos = [i for i in all_issues if i["level"] == "INFO"]

    for group, title in ((fails, "不达标（字号低于印刷红线）"),
                         (warns, "警告（画布过宽会被缩放）"),
                         (infos, "提示")):
        if not group:
            continue
        print(f"\n  【{title}】")
        for it in group:
            print(f"    {it['level']:<5} {Path(it['file']).name}")
            print(f"          {it['msg']}")

    print()
    print(f"  汇总: {len(fails)} 项不达标 / {len(warns)} 项警告 / 共 {len(targets)} 个脚本")
    if fails:
        print("  建议: 把 figsize 设为论文最终尺寸（整幅 6.30×3.54 英寸），字号即可 1:1 呈现。")
        print("        详见 integrations/figure-skill/SKILL.md 「尺寸与字号」一节。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
