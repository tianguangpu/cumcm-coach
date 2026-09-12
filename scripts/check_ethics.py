"""
check_ethics.py — 伦理维度检查（2025年新增）
=============================================
国一标准：政策类题目需评估不同收入群体的成本分摊公平性。

用法:
    python check_ethics.py --tex paper/main.tex
    python check_ethics.py --tex paper/main.tex --type policy
    python check_ethics.py --tex paper/main.tex --fix-suggest
"""
import argparse
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── 伦理关键词库 ──────────────────────────────────────────────────────

ETHICS_KEYWORDS = {
    "公平性": [
        "公平", "公正", "平等", "等价", "均等", "公平性", "公正性",
        "收入分配", "成本分摊", "利益分配", "资源分配",
    ],
    "可持续性": [
        "可持续", "绿色发展", "低碳", "环保", "生态", "环境友好",
        "代际公平", "长期影响", "可持续发展",
    ],
    "社会影响": [
        "社会影响", "社会效益", "社会成本", "公众利益", "民生",
        "弱势群体", "低收入", "贫困人口", "社会公平",
    ],
    "风险伦理": [
        "风险评估", "安全边界", "容错", "失效模式", "最坏情况",
        "极端场景", "边界条件", "安全裕度",
    ],
    "数据伦理": [
        "隐私", "数据安全", "个人信息", "脱敏", "匿名化",
        "数据合规", "知情同意",
    ],
}


def check_ethics_content(tex_path: str, problem_type: str = "") -> dict:
    """检查论文中的伦理维度内容。"""
    txt = open(tex_path, encoding="utf-8", errors="ignore").read()
    # 去注释
    txt = re.sub(r"(?m)^[ \t]*%.*$", "", txt)
    txt = re.sub(r"(?m)%.*$", "", txt)

    result = {
        "categories": {},
        "total_hits": 0,
        "coverage": 0,
        "score": 0,
        "issues": [],
        "suggestions": [],
    }

    # 检查每个类别
    for category, keywords in ETHICS_KEYWORDS.items():
        hits = []
        for kw in keywords:
            count = txt.count(kw)
            if count > 0:
                hits.append({"keyword": kw, "count": count})
        result["categories"][category] = {
            "found": len(hits) > 0,
            "hits": hits,
            "total": sum(h["count"] for h in hits),
        }
        result["total_hits"] += sum(h["count"] for h in hits)

    # 覆盖率
    found_categories = sum(1 for c in result["categories"].values() if c["found"])
    result["coverage"] = found_categories / len(ETHICS_KEYWORDS)

    # 评分
    score = 0
    # 每个类别覆盖+20分
    score += found_categories * 20
    # 总命中数加分
    score += min(20, result["total_hits"] * 2)
    # 政策类题目额外要求
    if problem_type in ("C", "policy"):
        if not result["categories"]["公平性"]["found"]:
            score -= 20
            result["issues"].append("政策类题目必须包含公平性分析")
        if not result["categories"]["社会影响"]["found"]:
            score -= 10
            result["issues"].append("政策类题目必须包含社会影响评估")

    result["score"] = max(0, min(100, score))

    # 生成建议
    if not result["categories"]["公平性"]["found"]:
        result["suggestions"].append("添加公平性分析: '不同收入群体的成本分摊比例为...'")
    if not result["categories"]["可持续性"]["found"]:
        result["suggestions"].append("添加可持续性分析: '长期来看，该方案的环境影响为...'")
    if not result["categories"]["风险伦理"]["found"]:
        result["suggestions"].append("添加风险伦理: '在最坏情况下，模型失效条件为...'")
    if not result["categories"]["社会影响"]["found"]:
        result["suggestions"].append("添加社会影响评估: '该方案对弱势群体的影响为...'")

    return result


def render_report(result: dict) -> str:
    """生成伦理维度检查报告。"""
    L = []
    L.append("=" * 55)
    L.append("  伦理维度检查报告 (2025年新增)")
    L.append("=" * 55)

    L.append(f"\n【综合得分】 {result['score']}/100")
    L.append(f"【覆盖率】 {result['coverage']*100:.0f}% ({sum(1 for c in result['categories'].values() if c['found'])}/{len(ETHICS_KEYWORDS)} 类)")

    L.append("\n【各类别检测】")
    for category, data in result["categories"].items():
        icon = "✓" if data["found"] else "✗"
        L.append(f"  {icon} {category}: {data['total']}次命中")
        if data["hits"]:
            for h in data["hits"][:3]:
                L.append(f"      '{h['keyword']}' x{h['count']}")

    if result["issues"]:
        L.append("\n【问题】")
        for i, issue in enumerate(result["issues"], 1):
            L.append(f"  {i}. {issue}")

    if result["suggestions"]:
        L.append("\n【建议】")
        for i, s in enumerate(result["suggestions"], 1):
            L.append(f"  {i}. {s}")

    L.append(f"\n{'='*55}")
    if result["score"] >= 60:
        L.append(f"  ✓ 伦理维度达标 ({result['score']}分)")
    else:
        L.append(f"  ✗ 伦理维度不达标 ({result['score']}分), 需补充")

    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="伦理维度检查")
    p.add_argument("--tex", default="paper/main.tex")
    p.add_argument("--type", default="", choices=["A", "B", "C", "D", "policy", ""], help="题目类型")
    p.add_argument("--fix-suggest", action="store_true")
    a = p.parse_args()

    if not os.path.isfile(a.tex):
        print(f"[err] 未找到 {a.tex}")
        return 1

    result = check_ethics_content(a.tex, a.type)

    if a.fix_suggest:
        for s in result["suggestions"]:
            print(f"建议: {s}")
        return 0

    print(render_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
