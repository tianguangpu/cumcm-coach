"""
check_innovation.py — 创新百分比强制检查
=========================================
国一标准：每个创新点必须附带量化百分比，不能只说"显著提高"。

用法:
    python check_innovation.py --tex paper/main.tex
    python check_innovation.py --tex paper/main.tex --ablation results/ablation.csv
    python check_innovation.py --tex paper/main.tex --fix-suggest
"""
import argparse
import csv
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── 模糊表述检测 ──────────────────────────────────────────────────────

VAGUE_TERMS = [
    "显著提高", "大幅提升", "明显改善", "有效提升", "显著优于",
    "明显优于", "大幅改善", "显著降低", "明显降低", "有效降低",
    "效果显著", "性能优越", "表现优异", "结果良好", "效果良好",
    "显著提升", "明显提升", "有效改善", "大幅降低", "显著改善",
]

PRECISE_PATTERNS = [
    r"(?:精度|准确率|R²|RMSE|MAE|MAPE|误差|收敛速度|效率).*(?:提升|提高|降低|减少|改善)\s*\d+\.?\d*\s*%",
    r"(?:优于|超越|超过|胜过).*(?:基线|传统|经典|原有|对照)\s*\d+\.?\d*\s*%",
    r"\d+\.?\d*\s*%\s*(?:的\s*)?(?:提升|改善|降低|减少)",
    r"(?:快|慢|高|低)\s*\d+\.?\d*\s*(?:倍|%)",
    r"[↑↓]\s*\d+\.?\d*\s*%",
]


def extract_innovations(tex_path: str) -> dict:
    """提取论文中的创新点和量化百分比。"""
    txt = open(tex_path, encoding="utf-8", errors="ignore").read()
    # 去注释
    txt = re.sub(r"(?m)^[ \t]*%.*$", "", txt)
    txt = re.sub(r"(?m)%.*$", "", txt)
    # 取正文
    m = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", txt, re.S)
    if m:
        txt = m.group(1)

    result = {
        "vague_terms": [],
        "precise_values": [],
        "innovation_sections": [],
        "ablation_refs": [],
        "score": 0,
        "issues": [],
    }

    # 检测模糊表述
    for term in VAGUE_TERMS:
        count = txt.count(term)
        if count > 0:
            result["vague_terms"].append({"term": term, "count": count})

    # 检测精确量化
    for pat in PRECISE_PATTERNS:
        matches = re.findall(pat, txt)
        result["precise_values"].extend(matches)

    # 检测创新点段落（通常在5.X.4或5.X.5）
    innovation_patterns = [
        r"(?:改进|创新|优化|融合|提出).{0,50}(?:模型|方法|策略|算法|机制)",
        r"(?:本文|本研究|本方法).{0,30}(?:改进|创新|优化|提出)",
    ]
    for pat in innovation_patterns:
        matches = re.findall(pat, txt)
        result["innovation_sections"].extend(matches[:3])

    # 检测ablation引用
    if "ablation" in txt.lower() or "消融" in txt or "对照实验" in txt:
        result["ablation_refs"].append("检测到消融对比引用")

    # 评分
    score = 0
    # 精确量化值数量
    score += min(40, len(result["precise_values"]) * 10)
    # 创新点段落
    score += min(20, len(result["innovation_sections"]) * 5)
    # 消融对比
    if result["ablation_refs"]:
        score += 20
    # 模糊表述扣分
    vague_penalty = min(30, sum(v["count"] for v in result["vague_terms"]) * 3)
    score = max(0, score - vague_penalty)
    # 无模糊表述加分
    if not result["vague_terms"]:
        score += 20

    result["score"] = min(100, score)

    # 生成问题列表
    if result["vague_terms"]:
        result["issues"].append(
            f"发现{len(result['vague_terms'])}种模糊表述(共{sum(v['count'] for v in result['vague_terms'])}次)"
        )
    if len(result["precise_values"]) < 3:
        result["issues"].append(f"精确量化值不足: {len(result['precise_values'])}/3")
    if not result["ablation_refs"]:
        result["issues"].append("未检测到消融对比实验")

    return result


def check_ablation_coverage(ablation_path: str, tex_path: str) -> dict:
    """检查消融结果是否正确引用到论文中。"""
    if not os.path.isfile(ablation_path):
        return {"status": "no_ablation_file", "issues": ["ablation.csv不存在"]}

    txt = open(tex_path, encoding="utf-8", errors="ignore").read()

    with open(ablation_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    issues = []
    for r in rows:
        q = r.get("q", "")
        alg = r.get("algorithm", "")
        best = r.get("best_value", "")
        # 检查数值是否在论文中出现
        if best and best not in txt:
            issues.append(f"{q}/{alg}: 最优值{best}未在论文中引用")

    return {
        "total_rows": len(rows),
        "referenced": len(rows) - len(issues),
        "issues": issues,
    }


def generate_fix_suggestions(innovation: dict, ablation_check: dict = None) -> list:
    """生成修复建议。"""
    suggestions = []

    # 模糊表述替换建议
    vague_map = {
        "显著提高": "提高 X%",
        "大幅提升": "提升 X%",
        "明显改善": "改善 X%",
        "显著优于": "优于基线 X%",
        "效果显著": "效果提升 X%",
        "性能优越": "性能优于基线 X%",
    }
    for v in innovation["vague_terms"]:
        term = v["term"]
        if term in vague_map:
            suggestions.append(f"'{term}' → '{vague_map[term]}' (替换{v['count']}次)")

    # 量化值不足
    if len(innovation["precise_values"]) < 3:
        suggestions.append("每个创新点必须附带: '精度提升X%' 或 '优于基线X%'")

    # 消融对比
    if not innovation["ablation_refs"]:
        suggestions.append("在§5.X.6添加: '基础方案vs创新方案对比，创新方案精度提升X%'")

    # ablation引用
    if ablation_check and ablation_check.get("issues"):
        for issue in ablation_check["issues"][:3]:
            suggestions.append(f"消融结果未引用: {issue}")

    return suggestions


def render_report(innovation: dict, ablation_check: dict = None) -> str:
    """生成创新性检查报告。"""
    L = []
    L.append("=" * 55)
    L.append("  创新百分比强制检查报告")
    L.append("=" * 55)

    # 评分
    L.append(f"\n【综合得分】 {innovation['score']}/100")

    # 模糊表述
    L.append(f"\n【模糊表述】 {len(innovation['vague_terms'])}种")
    for v in innovation["vague_terms"]:
        L.append(f"  ✗ '{v['term']}' x{v['count']} → 需替换为精确百分比")

    # 精确量化
    L.append(f"\n【精确量化】 {len(innovation['precise_values'])}个")
    for v in innovation["precise_values"][:5]:
        L.append(f"  ✓ {v}")

    # 创新点
    L.append(f"\n【创新点段落】 {len(innovation['innovation_sections'])}个")
    for s in innovation["innovation_sections"][:3]:
        L.append(f"  • {s[:60]}...")

    # 消融对比
    L.append(f"\n【消融对比】 {'✓ 检测到' if innovation['ablation_refs'] else '✗ 未检测到'}")
    if ablation_check:
        L.append(f"  覆盖: {ablation_check.get('referenced', 0)}/{ablation_check.get('total_rows', 0)} 行")

    # 问题
    if innovation["issues"]:
        L.append("\n【待修复】")
        for i, issue in enumerate(innovation["issues"], 1):
            L.append(f"  {i}. {issue}")

    # 修复建议
    suggestions = generate_fix_suggestions(innovation, ablation_check)
    if suggestions:
        L.append("\n【修复建议】")
        for i, s in enumerate(suggestions, 1):
            L.append(f"  {i}. {s}")

    # 达标判断
    L.append(f"\n{'='*55}")
    if innovation["score"] >= 70:
        L.append(f"  ✓ 创新性达标 ({innovation['score']}分)")
    else:
        L.append(f"  ✗ 创新性不达标 ({innovation['score']}分), 需量化创新百分比")

    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="创新百分比强制检查")
    p.add_argument("--tex", default="paper/main.tex")
    p.add_argument("--ablation", default="results/ablation.csv")
    p.add_argument("--fix-suggest", action="store_true")
    a = p.parse_args()

    if not os.path.isfile(a.tex):
        print(f"[err] 未找到 {a.tex}")
        return 1

    innovation = extract_innovations(a.tex)
    ablation_check = check_ablation_coverage(a.ablation, a.tex) if os.path.isfile(a.ablation) else None

    if a.fix_suggest:
        for s in generate_fix_suggestions(innovation, ablation_check):
            print(f"建议: {s}")
        return 0

    print(render_report(innovation, ablation_check))
    return 0


if __name__ == "__main__":
    sys.exit(main())
