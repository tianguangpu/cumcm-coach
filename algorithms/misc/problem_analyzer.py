"""problem_analyzer.py — 问题理解模块 (P0-4)

在建模开始前对赛题做结构化分析, 解决"直接生成=赌运气"的问题:

1. 歧义检测: 扫描多义词/模糊表述, 列出 2 种解释 + 各自建模影响
2. 隐含约束挖掘: 从背景/常识推导题目未明说的硬约束(如种植题轮作、季节性)
3. 背景关键词: 抽取领域词汇供 Agent 检索行业标准/经典模型
4. 子问题依赖: 构建 Q_i 之间的数据/结果依赖图, 标注并行的机会
5. 生成"问题确认报告"(JSON + Markdown), 供流程中的人工确认节点使用

用法:
    from algorithms.misc.problem_analyzer import analyze_problem
    rep = analyze_problem(problem_text, title="2024C 作物种植", outdir="results")
开
"""
import json
import os
import re

# 领域词表: 词 -> (类型, 可能隐含约束/知识)
DOMAIN_LEXICON = {
    # 农业种植 (2024C 精神)
    "轮作": ("constraint", "同地块不能连年同作物;跨年状态转移"),
    "种植": ("context", "季节性;生长期;光照/温度假设"),
    "地块": ("constraint", "各地块面积上限;地块异质性(土壤/灌溉)"),
    "面积": ("constraint", "面积非负且受地块容量约束"),
    # 预测/数据 (D题)
    "预测": ("method", "可用 ARIMA/Prophet/MLP;需做时间序列检验"),
    "缺失": ("data", "缺失值处理策略需声明(均值/插值/删除)"),
    "序列": ("data", "需做平稳性/ACF/PACF/白噪声检验"),
    # 评价 (C题)
    "指标": ("method", "需构建指标体系;权重来源(AHP属客/熵权)需声明"),
    "权重": ("method", "权重归一化;多方法对比稳定性"),
    "综合": ("method", "需选 TOPSIS/VIKOR/模糊综合并做排序稳定性"),
    # 机理 (A题)
    "方程": ("method", "微分方程;需说明定解条件与稳定性"),
    "守恒": ("theory", "物质/能量守恒;解析解对比验证"),
    "扩散": ("method", "FDM 2D/FEM;需满足 CFL 稳定性条件"),
    "受力": ("theory", "力学平衡;材料参数假设需声明"),
    # 优化 (B题)
    "最大": ("objective", "目标函数明确;需说明线性/非线性/凹性"),
    "收益": ("objective", "收益最大化;成本/价格假设需声明"),
    "约束": ("constraint", "约束需全部列全;松弛可行性处理"),
    "决策": ("context", "决策变量定义需清晰(连续/0-1/整数)"),
}
# 常用隐含约束模板 (无关键词也能靠常识补)
DOMAIN_HINTS = {
    "农业": ["轮作约束", "同地块不连茬", "面积非负", "产量受土地边际递减影响"],
    "制造/排班": ["产能上限", "机器并行约束", "整变量(件数)"],
    "网络/流": ["容量约束", "流量守恒", "可分流/不可分流"],
    "经济/金融": ["价格波动", "风险偏好", "预算约束"],
}

AMBIGUITY_MARKERS = ["左右", "约", "可能", "大致", "等等", "若干", "部分", "可调节", "视情况"]


def _extract_sentences(text):
    return [s.strip() for s in re.split(r"[。；;\n]", text) if len(s.strip()) > 2]


def _find_context_terms(text):
    """判断农耕/制造/网络/经济领域背景(用于补充隐含约束)。"""
    matched = []
    for domain, hints in DOMAIN_HINTS.items():
        for kw in (["轮作", "种植", "地块", "作物"] if domain == "农业"
                   else ["排班", "班次", "产能", "工序"] if domain == "制造/排班"
                   else ["节点", "流量", "网络", "路径"] if domain == "网络/流"
                   else ["价格", "收益", "风险", "投资", "成本"]):
            if kw in text:
                matched.append(domain)
                break
    return matched


def _ambiguity_scan(text):
    """扫描模糊表述, 输出多种解读。"""
    hits = []
    for s in _extract_sentences(text):
        for mark in AMBIGUITY_MARKERS:
            if mark in s:
                hits.append({"sentence": s, "marker": mark,
                             "note": f"含模糊词'{mark}', 需向出题人确认或声明假设"})
    return hits


def _constraint_mining(text):
    """从领域词+句子提取显式/疑似约束。"""
    explicit, implied = [], []
    for s in _extract_sentences(text):
        if any(w in s for w in ["约束", "不得", "不可", "必须", "限制", "不超过", "至少", "资金"]):
            explicit.append(s)
    for domain in _find_context_terms(text):
        for hint in DOMAIN_HINTS[domain]:
            implied.append(hint)
    for kw, (typ, note) in DOMAIN_LEXICON.items():
        if typ == "constraint" and kw in text:
            explicit.append(f"{kw}: {note}")
    return explicit, implied


def _dependency_map(text):
    """识别子问题依赖: 按 '问题[0-9]' / '第[一二三四]问' 切分。"""
    heads = re.findall(r"(问题[一二三四0-9]|第[一二三四0-9]问|\(?[一二三四]\)?)", text)
    deps, prev = [], None
    for h in heads:
        node = {"问": h, "依赖": prev if prev else None, "可并行": prev is None}
        deps.append(node)
        prev = h
    return {"nodes": deps, "note": "仅按顺序推断; 实际数据依赖需人工确认"}


def analyze_problem(text, title="", outdir=None, verbose=True):
    """主入口。返回 dict 报告; 若 outdir 则写入 JSON+MD。"""
    rep = {
        "title": title or "(未命名)",
        "ambiguity": _ambiguity_scan(text) or [{"note": "未检出明显模糊词, 仍需人工复核"}],
        "constraints_explicit": list(set(body[4:] if body.startswith("X:") else body
                                         for body in [x for x in _constraint_mining(text)[0]])) or [],
        "constraints_implied": list(set(_constraint_mining(text)[1])),
        "background": _find_context_terms(text),
        "terminology": sorted({kw for kw in DOMAIN_LEXICON if kw in text}),
        "dependencies": _dependency_map(text),
        "needs_confirmation": bool(_ambiguity_scan(text)),
    }
    # 去重显式约束
    seen, uniq = set(), []
    for c in rep["constraints_explicit"]:
        key = c.split(":")[0]
        if key not in seen:
            seen.add(key); uniq.append(c)
    rep["constraints_explicit"] = uniq

    if outdir:
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "problem_analysis.json"), "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
        with open(os.path.join(outdir, "problem_analysis.md"), "w", encoding="utf-8") as f:
            f.write(_to_md(rep))
    if verbose:
        print(f"[problem_analyzer] 歧义 {len(rep['ambiguity'])} 条 / 显式约束 {len(rep['constraints_explicit'])} / "
              f"隐含约束 {len(rep['constraints_implied'])} / 背景 {rep['background']}")
    return rep


def _to_md(rep):
    lines = [f"# 问题分析报告 — {rep['title']}", ""]
    lines.append("## 歧义 / 待确认项")
    for a in rep["ambiguity"]:
        lines.append(f"- {a.get('note', a)}" + (f"`≤{a.get('sentence','')[:30]}...`" if a.get("sentence") else ""))
    lines.append("")
    lines.append("## 显式约束")
    lines += [f"- {c}" for c in rep["constraints_explicit"]] or ["- (未检出)"]
    lines.append("")
    lines.append("## 隐含约束(需人工确认)")
    lines += [f"- {h}" for h in rep["constraints_implied"]] or ["- (未检出)"]
    lines.append("")
    lines.append("## 背景领域")
    lines += [f"- {d}" for d in rep["background"]] or ["- (未识别)"]
    lines.append("")
    lines.append("## 子问题依赖")
    for n in rep["dependencies"]["nodes"]:
        lines.append(f"- {n['问']}  → 依赖 {n['依赖'] or '无(可并行)'}")
    lines.append(f"\n> 依据: {rep['dependencies']['note']}")
    return "\n".join(lines)


if __name__ == "__main__":
    demo = ("问题1: 种植基地内有多个地块, 分别种植若干作物。轮作约束, 同地块不能连年种植同一作物。"
            "在面积限制下, 求解最优种植面积, 使总收益最大。问题2: 在问题1结果上, 进一步考虑价格波动风险, "
            "约±8%。")
    rep = analyze_problem(demo, title="种植规划演示", outdir="results", verbose=True)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
