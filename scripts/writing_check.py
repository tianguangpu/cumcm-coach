# -*- coding: utf-8 -*-
"""
writing_check.py — 论文写作质量检查（Windows兼容版）
=====================================================
替代 writing_check.sh，纯Python实现，跨平台兼容。

用法:
    python writing_check.py --paper paper/ --engine latex
    python writing_check.py --paper paper/ --results reports/RESULTS_REPORT.md
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def check_paper(paper_dir: str, engine: str = "latex", results_file: str = None) -> int:
    """检查论文质量，返回退出码(0=通过)。"""
    exit_code = 0
    paper = Path(paper_dir)
    root = paper.parent if paper.name == "paper" else paper

    def fail(msg):
        nonlocal exit_code
        print(f"FAIL: {msg}")
        exit_code = 1

    def warn(msg):
        print(f"WARN: {msg}")

    def info(msg):
        print(f"INFO: {msg}")

    # 检测主文件
    if engine == "latex":
        main = paper / "main.tex"
        section_ext = "*.tex"
        heading_re = re.compile(r"\\section\{([^}]*)\}")
        image_re = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
        cite_re = re.compile(r"\\cite\w*\{[^}]+\}")
        figure_blocks_re = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.S)
        caption_re = re.compile(r"\\caption\{([^}]*)\}")
        include_re = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
        list_re = re.compile(r"\\begin\{(?:itemize|enumerate)\}")
    else:
        main = paper / "main.typ"
        section_ext = "*.typ"
        heading_re = re.compile(r"(?m)^=\s+(.+)")
        image_re = re.compile(r'image\(\s*"([^"]+)"')
        cite_re = re.compile(r"@\w[\w:-]*|#cite\(")
        figure_blocks_re = None
        caption_re = re.compile(r"caption:\s*\[(.*?)\]", re.S)
        include_re = re.compile(r'#include\(\s*"([^"]+\.typ)"\s*\)')
        list_re = re.compile(r"#(?:enum|list)\s*\(")

    if not main.exists():
        fail(f"主文件不存在: {main}")
        return exit_code

    info(f"论文目录: {paper}")
    info(f"主文件: {main}")
    info(f"引擎: {engine}")

    main_text = read(main)

    # 检查includes
    includes = include_re.findall(main_text)
    if engine == "latex":
        includes = [inc if inc.endswith(".tex") else inc + ".tex" for inc in includes]

    info(f"include数量: {len(includes)}")

    # 检查章节文件
    sections_dir = paper / "sections"
    if sections_dir.exists():
        section_files = sorted(sections_dir.glob(section_ext))
    else:
        section_files = sorted(p for p in paper.glob(section_ext) if p != main)
    info(f"章节数: {len(section_files)}")

    # 占位符检查
    placeholder_re = re.compile(r"PLACEHOLDER|TODO|TBD|XXX|待补充|待续写|这里补|示例数据|待完善")
    for sf in section_files:
        text = read(sf)
        if placeholder_re.search(text):
            fail(f"占位符未清除: {rel(sf, root)}")

    # 章节标题检查
    section_titles = []
    for sf in section_files:
        text = read(sf)
        headings = heading_re.findall(text)
        if not headings and not sf.name.startswith("A_"):
            warn(f"章节无标题: {sf.name}")
        for title in headings:
            section_titles.append((sf.name, title))

    if section_titles:
        info("章节顺序:")
        for i, (name, title) in enumerate(section_titles, 1):
            info(f"  {i}. {name} → {title}")

    # 图片引用检查
    for sf in section_files:
        text = read(sf)
        for ref in image_re.findall(text):
            target = (sf.parent / ref).resolve()
            if not target.exists():
                fail(f"图片不存在: {rel(sf, root)} → {ref}")

    # 图表数量检查
    figures_dir = root / "figures" / "png"
    if figures_dir.exists():
        fig_count = len(list(figures_dir.glob("*.png")))
        info(f"图表数量: {fig_count}")
        if fig_count < 10:
            warn(f"图表数量偏少: {fig_count}张(建议≥12)")

    # 引用检查
    if re.search(cite_re, main_text):
        info("检测到引用标记")
    else:
        warn("未检测到引用标记(\\cite或@引用)")

    # 参考文献检查
    refs_file = paper / "references.bib" if engine == "latex" else paper / "references.yml"
    if refs_file.exists():
        refs_text = read(refs_file)
        if len(refs_text.strip()) < 80:
            warn(f"参考文献文件过短: {refs_file.name}")
    else:
        refs_tex = paper / "references.tex"
        if refs_tex.exists():
            bibitems = re.findall(r"\\bibitem", read(refs_tex))
            info(f"参考文献条目: {len(bibitems)}")
            if len(bibitems) < 10:
                warn(f"参考文献偏少: {len(bibitems)}条(要求≥10)")
        else:
            warn("未找到参考文献文件")

    # 结果文件数值一致性检查
    if results_file:
        rf = Path(results_file)
        if rf.exists():
            results_text = read(rf)
            metric_re = re.compile(
                r"(?i)\b(?:rmse|mae|mape|r2|score|objective|accuracy|precision|recall|f1|"
                r"权重|目标值|误差|得分)\b"
            )
            metrics = metric_re.findall(results_text)
            if metrics:
                paper_text = main_text + "\n".join(read(sf) for sf in section_files)
                found = any(m.lower() in paper_text.lower() for m in metrics[:20])
                if found:
                    info("结果指标在论文中找到")
                else:
                    warn("结果文件中的指标在论文中未找到")

    if exit_code == 0:
        print("\nPASS: 论文写作质量检查通过")
    else:
        print("\nFAIL: 论文写作质量检查未通过")

    return exit_code


def main():
    p = argparse.ArgumentParser(description="论文写作质量检查")
    p.add_argument("--paper", default="paper/", help="论文目录")
    p.add_argument("--engine", default="latex", choices=["latex", "typst"])
    p.add_argument("--results", default=None, help="结果报告文件")
    a = p.parse_args()

    sys.exit(check_paper(a.paper, a.engine, a.results))


if __name__ == "__main__":
    main()
