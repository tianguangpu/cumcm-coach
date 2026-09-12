"""
gen_ppt_outline.py — 国赛答辩PPT自动生成
==========================================
根据论文内容和建模结果，自动生成12页答辩PPT大纲（Markdown格式）。

用法:
    python gen_ppt_outline.py --tex paper/main.tex --results results/ --output output/ppt_outline.md
    python gen_ppt_outline.py --tex paper/main.tex --results results/ --format pptx --output output/答辩.pptx

依赖: python-pptx (仅 --format pptx 时需要)
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── PPT 12页结构模板（国一奖标配） ──────────────────────────────────
PPT_STRUCTURE = [
    {"page": 1, "title": "封面", "content": "题目+队伍号+学校+日期"},
    {"page": 2, "title": "问题重述与分析", "content": "背景+核心问题+关键约束"},
    {"page": 3, "title": "模型假设与符号说明", "content": "核心假设(3~5条)+关键符号表"},
    {"page": 4, "title": "问题一：模型建立与求解", "content": "方法选择+模型公式+求解结果"},
    {"page": 5, "title": "问题一：结果可视化", "content": "核心图表(1~2张)+关键数值"},
    {"page": 6, "title": "问题二：模型建立与求解", "content": "方法选择+模型公式+求解结果"},
    {"page": 7, "title": "问题二：结果可视化", "content": "核心图表(1~2张)+关键数值"},
    {"page": 8, "title": "问题三：模型建立与求解", "content": "方法选择+模型公式+求解结果"},
    {"page": 9, "title": "问题三：结果可视化", "content": "核心图表(1~2张)+关键数值"},
    {"page": 10, "title": "灵敏度分析与模型检验", "content": "四重检验结果+鲁棒性分析"},
    {"page": 11, "title": "模型评价与改进方向", "content": "3优3缺+未来改进"},
    {"page": 12, "title": "参考文献与致谢", "content": "核心参考文献(5~8篇)"},
]


def extract_paper_info(tex_path: str) -> dict:
    """从LaTeX论文中提取关键信息。"""
    if not os.path.isfile(tex_path):
        return {}
    txt = open(tex_path, encoding="utf-8", errors="ignore").read()

    info = {}

    # 提取标题
    m = re.search(r"\\title\{([^}]+)\}", txt)
    if m:
        info["title"] = m.group(1).strip()

    # 提取摘要
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", txt, re.S)
    if m:
        info["abstract"] = m.group(1).strip()[:300]

    # 提取章节结构
    secs = re.findall(r"\\section\{([^}]+)\}", txt)
    info["sections"] = secs

    # 提取图表数量
    figs = re.findall(r"\\begin\{figure\}", txt)
    info["figure_count"] = len(figs)

    # 提取公式数量
    eqs = re.findall(r"\\begin\{(equation|align|gather)\}", txt)
    info["equation_count"] = len(eqs)

    # 提取参考文献数量
    bibs = re.findall(r"\\bibitem\{", txt)
    bib_file = re.search(r"\\bibliography\{([^}]+)\}", txt)
    info["ref_count"] = len(bibs)

    return info


def extract_results(results_dir: str) -> dict:
    """从results/目录提取关键数值结果。"""
    results = {}
    rdir = Path(results_dir)
    if not rdir.exists():
        return results

    for f in sorted(rdir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8-sig"))
            # 提取数值型结果
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    results[f"{f.stem}_{k}"] = v
                elif isinstance(v, dict):
                    for kk, vv in v.items():
                        if isinstance(vv, (int, float)):
                            results[f"{f.stem}_{k}_{kk}"] = vv
        except Exception:
            pass

    return results


def generate_markdown(info: dict, results: dict, output_path: str, ptype: str = "") -> str:
    """生成Markdown格式的PPT大纲。"""
    title = info.get("title", "数学建模竞赛答辩")
    abstract = info.get("abstract", "")
    sections = info.get("sections", [])
    fig_count = info.get("figure_count", 0)
    eq_count = info.get("equation_count", 0)

    # 提取关键数值
    key_values = []
    for k, v in list(results.items())[:10]:
        if isinstance(v, float):
            key_values.append(f"- {k}: {v:.4f}")
        else:
            key_values.append(f"- {k}: {v}")

    md = []
    md.append(f"# {title}")
    md.append("## 答辩PPT大纲（自动生成）")
    md.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"> 题目类型: {ptype if ptype else '—'}")
    md.append(f"> 论文统计: {len(sections)}节 / {fig_count}图 / {eq_count}公式")
    md.append("")

    for page in PPT_STRUCTURE:
        md.append("---")
        md.append("")
        md.append(f"### 第{page['page']}页：{page['title']}")
        md.append("")

        if page["page"] == 1:
            md.append(f"**{title}**")
            md.append("")
            md.append("- 队伍编号：_______________")
            md.append("- 学校名称：_______________")
            md.append("- 指导教师：_______________")
            md.append(f"- 日期：{datetime.now().strftime('%Y年%m月%d日')}")

        elif page["page"] == 2:
            md.append("**问题背景**：（简述2~3句）")
            md.append("")
            md.append("**核心问题**：")
            for i, s in enumerate(sections[:3], 1):
                md.append(f"  {i}. {s}")
            md.append("")
            md.append("**关键约束**：（列出题目中的硬约束）")

        elif page["page"] == 3:
            md.append("**核心假设**：")
            md.append("  1. （假设1：合理性说明）")
            md.append("  2. （假设2：合理性说明）")
            md.append("  3. （假设3：合理性说明）")
            md.append("")
            md.append("**关键符号**：")
            md.append("| 符号 | 含义 | 单位 |")
            md.append("|------|------|------|")
            md.append("| $x$ | （待填） | （待填） |")

        elif page["page"] in (4, 6, 8):
            q_num = (page["page"] - 4) // 2 + 1
            md.append("**方法选择**：（为何选此方法，有何优势）")
            md.append("")
            md.append("**模型公式**：")
            md.append("$$")
            md.append("\\min_{x} \\quad f(x) = \\cdots")
            md.append("$$")
            md.append("")
            md.append("**求解结果**：")
            if key_values:
                md.append(key_values[q_num - 1] if q_num <= len(key_values) else "- （待填）")
            else:
                md.append("- （待填关键数值）")

        elif page["page"] in (5, 7, 9):
            md.append("**核心图表**：")
            md.append("")
            md.append(f"![图{(page['page']-5)//2+1}](figures/png/fig{(page['page']-5)//2+1}.png)")
            md.append("")
            md.append("**关键发现**：")
            md.append("- （2~3句话总结图表揭示的规律）")

        elif page["page"] == 10:
            md.append("**四重检验结果**：")
            md.append("| 检验项 | 方法 | 结果 |")
            md.append("|--------|------|------|")
            md.append("| 拟合精度 | R²/RMSE | （待填） |")
            md.append("| 灵敏度 | ±10%扰动 | （待填） |")
            md.append("| 蒙特卡洛 | 1000次模拟 | （待填） |")
            md.append("| 交叉验证 | 5折CV | （待填） |")

        elif page["page"] == 11:
            md.append("**模型优点**：")
            md.append("  1. （优点1）")
            md.append("  2. （优点2）")
            md.append("  3. （优点3）")
            md.append("")
            md.append("**模型不足**：")
            md.append("  1. （不足1）")
            md.append("  2. （不足2）")
            md.append("  3. （不足3）")
            md.append("")
            md.append("**改进方向**：（1~2句）")

        elif page["page"] == 12:
            md.append("**核心参考文献**：")
            md.append("  1. [1] 作者. 标题. 期刊, 年份.")
            md.append("  2. [2] 作者. 标题. 期刊, 年份.")
            md.append("  3. ...")
            md.append("")
            md.append("**致谢**：（感谢指导教师、队友等）")

        md.append("")

    content = "\n".join(md)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"[PPT] 大纲已生成: {out}")
    return content


def generate_pptx(info: dict, results: dict, output_path: str):
    """生成PPTX格式（需要python-pptx）。"""
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Inches, Pt
    except ImportError:
        print("[PPT] python-pptx 未安装，请运行: pip install python-pptx")
        print("[PPT] 已降级为Markdown格式输出")
        return

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    title = info.get("title", "数学建模竞赛答辩")

    for page in PPT_STRUCTURE:
        slide = prs.slides.add_slide(prs.slide_layouts[1])  # 标题+内容布局
        tf = slide.shapes.title
        tf.text = f"第{page['page']}页：{page['title']}"
        tf.text_frame.paragraphs[0].font.size = Pt(28)
        tf.text_frame.paragraphs[0].font.bold = True

        body = slide.placeholders[1]
        body.text = page["content"]

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    print(f"[PPT] PPTX已生成: {out}")


def main():
    p = argparse.ArgumentParser(description="国赛答辩PPT自动生成")
    p.add_argument("--tex", default="paper/main.tex", help="论文LaTeX源文件")
    p.add_argument("--results", default="results/", help="结果目录")
    p.add_argument("--output", default="output/ppt_outline.md", help="输出路径")
    p.add_argument("--format", choices=["md", "pptx"], default="md", help="输出格式")
    p.add_argument("--type", default="", help="题目题型(A/B/C/D), 仅标注, 不影响内容结构")
    a = p.parse_args()

    info = extract_paper_info(a.tex)
    results = extract_results(a.results)

    if a.format == "pptx":
        generate_pptx(info, results, a.output)
    else:
        generate_markdown(info, results, a.output, a.type)

    return 0


if __name__ == "__main__":
    sys.exit(main())
