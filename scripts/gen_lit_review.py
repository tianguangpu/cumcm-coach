"""
gen_lit_review.py — 文献综述模块
================================
按题目题型生成结构化『研究现状/文献综述』章节段落(LaTeX 片段 + Markdown),
复用论文已有 \\cite{refN} 引用键,避免重排参考文献;可选 OpenAlex 增量检索
(沿用 search_openalex.py 的 retrieval 逻辑,网络不可用时自动回退内置模板)。

用法:
    python gen_lit_review.py --type B --topic "多作物种植规划" --out reports/lit_review.tex
    python gen_lit_review.py --type C --out reports/lit_review.tex --openalex

产出:
    lit_review.tex   可 \\input 的 LaTeX 章节片段(核心交付)
    lit_review.md    Markdown 版综述(供论文撰写/答辩复用)
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# 各题型的『研究现状』结构化内容模板: 按 3 层组织 —— 国内/国外方法演进 + 不足 + 本文切入点
# refN 一律取自论文 thebibliography 既有键, 保证 \cite 可解析。
# ---------------------------------------------------------------------------
TYPE_TEMPLATES = {
    "B": {  # B类 优化/规划
        "label": "优化建模与智能寻优研究现状",
        "background": (
            "种植/生产规划类优化问题广泛存在于农业与供应链决策中。传统建模多以线性规划刻画"
            "收益对投入的线性响应，但现实生产过程普遍存在边际收益递减，线性假设易导致面积/产能虚高。"
            "\\cite{ref2}"
        ),
        "method_evolution": (
            "在求解层面，以粒子群\\cite{ref2}、模拟退火\\cite{ref7}、遗传算法及其多目标扩展"
            "NSGA-II\\cite{ref6}为代表的智能优化算法，为处理非凸、带复杂约束(如轮作/容量/预算)的"
            "种植规划提供了可行框架；近年来学者进一步引入多周期滚动规划与跨年状态转移，"
            "以刻画产量与价格的时序关联\\cite{ref5}。"
        ),
        "verification": (
            "模型可靠性方面，灵敏度分析与全局灵敏度方法(如 Saltelli 的 Sobol 分解\\cite{ref9}、"
            "基于 Sobol 的种植参数不确定性量化\\cite{ref8})被用于定位关键决策参数，"
            "外文文献则在风险约束下的稳健种植决策上多有拓展。"
        ),
        "gap": (
            "综上，现有工作或停留在线性/单周期假设，或对非线性非凸的凹收益与轮作跨年耦合刻画不足，"
            "较少在统一框架下同时覆盖模型改进、智能寻优与四重检验闭环。"
        ),
        "entry": (
            "本文针对多作物、多地块种植规划，构建``线性基准$\\to$凹规划改进$\\to$智能寻优$\\to$四重检验''"
            "的完整链路，在收益边际递减与轮作约束下追求净收益最大化\\cite{ref3,ref10}，"
            "为涉农供应链多阶决策提供可复现范例。"
        ),
    },
    "A": {  # A类 机理/物理
        "label": "机理建模研究现状",
        "background": (
            "该类问题需从物理/力学/热学等基本定律出发建立控制方程，传统依赖解析解与有限差分差分近似。"
            "近年来有限元与数值求解器被广泛用于刻画复杂边界与源项。\\cite{ref10}"
        ),
        "method_evolution": (
            "数值方法层面，一/二维有限差分\\cite{ref7}与有限元\\cite{ref6}已在传热、流场等场景成熟应用；"
            "对含强非线性或随机扰动的系统，智能优化用于参数标定与反演\\cite{ref2}。"
        ),
        "verification": "模型验证强调网格无关性检验与守恒律核对，并借助灵敏度分析定位主导参数\\cite{ref8,ref9}。",
        "gap": "现有工作多在简化几何/定常假设下求解，对多物理场耦合与参数不确定性刻画不足。",
        "entry": "本文从守恒方程出发建立机理模型，引入数值离散+智能标定，并以灵敏度与误差量化校验稳健性。",
    },
    "C": {  # C类 评价/决策
        "label": "综合评价研究现状",
        "background": (
            "综合评价问题需在多属性下排序或分级。层次分析法、熵权、TOPSIS 等经典方法被广泛用于构造指标体系"
            "与权重聚合。\\cite{ref10}"
        ),
        "method_evolution": (
            "为降低主观性，AHP 与熵权结合形成组合赋权\\cite{ref2}，并衍生灰度关联与 VIKOR 等稳健排序；"
            "机器学习方法(如梯度提升)用于非线性指标关系拟合\\cite{ref5}。"
        ),
        "verification": "评价结果的稳健性常以灵敏度(权重扰动)与稳定性分析检验\\cite{ref8,ref9}。",
        "gap": "单一赋权或单一排序法对指标相关性、等级边界刻画不足，且密度差异常被忽略。",
        "entry": "本文采用主客观组合赋权与多准则排序融合，并以权重扰动与置信度分析增强结论稳健性。",
    },
    "D": {  # D类 数据/预测
        "label": "数据驱动与预测研究现状",
        "background": (
            "数据类问题聚焦时序预测与关系挖掘。传统统计模型(ARIMA/GM)对线性平稳序列有效，但对非线性、"
            "多变量耦合的强局限。\\cite{ref10}"
        ),
        "method_evolution": (
            "机器学习与集成方法(GBDT/XGBoost)及神经网络在非线性拟合与特征交互上表现更优\\cite{ref5}；"
            "模型可解释性则借助特征重要性与 SHAP 等手段\\cite{ref8}。"
        ),
        "verification": "预测可靠性以多折交叉验证、误差归因与残差检验衡量\\cite{ref9}。",
        "gap": "短期拟合强的模型常欠可解释性与外推稳健性，对分布漂移敏感。",
        "entry": "本文在经典时序基础上集成机器学习增强，辅以交叉验证与误差归因，兼顾精度与可解释性。",
    },
}


def render_latex(t: dict) -> str:
    """生成 LaTeX 章节片段(可直接 \\input)。"""
    return "\n".join([
        r"\section{" + t["label"] + r"}",
        "",
        r"\paragraph{研究背景}" + t["background"],
        "",
        r"\paragraph{方法演进}" + t["method_evolution"],
        "",
        r"\paragraph{现有不足}" + t["gap"],
        "",
        r"\paragraph{本文切入点}" + t["entry"],
        "",
    ])


def render_markdown(t: dict, topic: str, now: str) -> str:
    md = []
    md.append(f"# 文献综述({t['label']})")
    md.append(f"> 题目类型: {topic} | 生成时间: {now}")
    md.append("")
    md.append("## 研究背景\n\n" + t["background"])
    md.append("\n## 方法演进\n\n" + t["method_evolution"])
    md.append("\n## 现有不足\n\n" + t["gap"])
    md.append("\n## 本文切入点\n\n" + t["entry"])
    md.append("")
    return "\n".join(md)


def try_openalex(topic: str, limit: int = 6) -> list:
    """可选: 用 OpenAlex 增量检索近5年文献(网络不可用/无结果则回退空列表)。"""
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from search_openalex import format_bibtex_entry, search_openalex
    except Exception:
        return []
    works = search_openalex(topic, years=5, limit=limit)
    if not works:
        return []
    out = []
    for i, w in enumerate(works, 1):
        try:
            out.append(format_bibtex_entry(w, i))
        except Exception:
            continue
    return out


def main():
    p = argparse.ArgumentParser(description="文献综述模块")
    p.add_argument("--type", required=True, choices=["A", "B", "C", "D"], help="题目题型")
    p.add_argument("--topic", default="农场多作物种植规划", help="题目主题(用于OpenAlex检索与文档)")
    p.add_argument("--out", default=None, help="输出tex路径(默认 reports/lit_review.tex)")
    p.add_argument("--dir", default=None, help="输出目录(默认 skill根/reports)")
    p.add_argument("--openalex", action="store_true", help="尝试OpenAlex增量检索")
    a = p.parse_args()

    t = TYPE_TEMPLATES[a.type]
    base = Path(a.dir) if a.dir else Path(__file__).parent.parent / "reports"
    base.mkdir(parents=True, exist_ok=True)
    out_tex = Path(a.out) if a.out else base / "lit_review.tex"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 可选增量
    extra = ""
    if a.openalex:
        fetched = try_openalex(a.topic)
        if fetched:
            extra = "\n\n".join(fetched)
            print(f"[lit_review] OpenAlex 增量 {len(fetched)} 条(见 lit_review_openalex.bib)")

    tex = render_latex(t)
    if extra:
        tex += "\n% --- OpenAlex 增量检索备选文献(需自行 ${renewcommand}? 建议并入 thebibliography) ---\n"

    out_tex.write_text(tex, encoding="utf-8")
    print(f"[lit_review] LaTeX 综述已生成: {out_tex}")

    (base / "lit_review.md").write_text(render_markdown(t, a.topic, now), encoding="utf-8")
    print(f"[lit_review] Markdown 综述已生成: {base / 'lit_review.md'}")

    if extra:
        bib_path = base / "lit_review_openalex.bib"
        bib_path.write_text(extra, encoding="utf-8")
        print(f"[lit_review] OpenAlex BibTeX 已保存: {bib_path}")


if __name__ == "__main__":
    main()
