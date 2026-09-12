"""
摘要质量自动评分 — 检查结构/数值密度/创新量化/关键词/AI味

用法:
    python scripts/check_abstract.py --tex paper/sections/1_restatement.tex --output reports/abstract_report.md
    python scripts/check_abstract.py --text "摘要文本内容" --output reports/abstract_report.md
"""

import re
import sys
from pathlib import Path

# AI 味高频词(检测用)
AI_PATTERNS = {
    "filler_words": [
        "标志着", "重要的是", "关键作用", "具有重要意义", "取得了显著",
        "令人振奋", "突破性的", "创新性的", "开创性的", "具有深远影响",
        "不仅.*而且", "值得注意的是", "显而易见", "毫无疑问",
    ],
    "vague_attribution": [
        "专家认为", "研究表明", "广泛认为", "众所周知",
        "独立报道", "多方证实",
    ],
    "structure_patterns": [
        r"不仅.{0,20}而且",
        r"通过.{0,10}方法.{0,10}实现了",
        r"基于.{0,10}提出了",
    ],
}


def extract_abstract_from_tex(tex_path):
    """从 .tex 文件提取摘要"""
    content = Path(tex_path).read_text(encoding="utf-8")

    # 尝试多种摘要格式
    patterns = [
        r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
        r'\\abstract\{(.*?)\}',
        r'摘\s*要[：:]\s*(.*?)(?=\n\s*\\|\n\s*关|\n\s* key)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def check_abstract_structure(text):
    """检查摘要三段式结构"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    paragraphs = [l for l in lines if len(l) > 20]

    issues = []

    # 检查段落数
    if len(paragraphs) < 2:
        issues.append(f"段落数过少({len(paragraphs)}),建议三段式结构")

    # 检查第一段:背景+研究对象
    first_para = paragraphs[0] if paragraphs else ""
    bg_keywords = ["背景", "问题", "研究", "针对", "本文", "面对"]
    has_bg = any(kw in first_para for kw in bg_keywords)
    if not has_bg:
        issues.append("第一段缺少背景/研究对象描述")

    # 检查第二段:模型+算法+数值
    second_para = paragraphs[1] if len(paragraphs) > 1 else ""
    model_keywords = ["模型", "算法", "方法", "求解", "建立"]
    has_model = any(kw in second_para for kw in model_keywords)
    if not has_model:
        issues.append("第二段缺少模型/算法描述")

    # 检查第三段:创新+检验
    third_para = paragraphs[2] if len(paragraphs) > 2 else ""
    innovation_keywords = ["创新", "改进", "提升", "优化", "检验", "灵敏度", "蒙特卡洛"]
    has_innovation = any(kw in third_para for kw in innovation_keywords)
    if len(paragraphs) >= 3 and not has_innovation:
        issues.append("第三段缺少创新点/检验结果")

    return {
        "paragraph_count": len(paragraphs),
        "has_background": has_bg,
        "has_model": has_model,
        "has_innovation": has_innovation,
        "issues": issues,
        "score": max(0, 100 - len(issues) * 15),
    }


def check_numerical_density(text):
    """检查数值密度(关键数值是否充足)"""
    # 匹配数字(含百分比、小数)
    numbers = re.findall(r'\d+\.?\d*%?', text)
    total_chars = len(text)

    density = len(numbers) / (total_chars / 100) if total_chars > 0 else 0

    issues = []
    if density < 2:
        issues.append(f"数值密度偏低({density:.1f}个/百字),摘要应包含关键数值结果")
    if density > 10:
        issues.append(f"数值密度过高({density:.1f}个/百字),可能过于冗余")

    return {
        "number_count": len(numbers),
        "density": density,
        "issues": issues,
        "score": min(100, max(0, 100 - abs(density - 5) * 10)),
    }


def check_innovation_quantification(text):
    """检查创新点是否量化"""
    # 检查百分比/提升幅度
    quant_patterns = [
        r'提升\s*\d+\.?\d*%',
        r'提高\s*\d+\.?\d*%',
        r'降低\s*\d+\.?\d*%',
        r'减少\s*\d+\.?\d*%',
        r'精度.*?\d+\.?\d*%',
        r'准确率.*?\d+\.?\d*%',
        r'R².*?=\s*\d+\.?\d*',
        r'RMSE.*?=\s*\d+\.?\d*',
    ]

    quantified = []
    for pattern in quant_patterns:
        matches = re.findall(pattern, text)
        quantified.extend(matches)

    issues = []
    if len(quantified) == 0:
        issues.append("未找到量化创新点(提升X%/精度Y%),国赛要求创新必须量化")

    return {
        "quantified_count": len(quantified),
        "quantified_items": quantified[:5],
        "issues": issues,
        "score": min(100, len(quantified) * 25),
    }


def check_keywords(text):
    """检查关键词"""
    # 提取关键词
    kw_match = re.search(r'关键词[：:]\s*(.*?)(?:\n|$)', text)
    if not kw_match:
        return {"count": 0, "issues": ["未找到关键词"], "score": 0}

    keywords = [kw.strip() for kw in re.split(r'[,，;；\s]+', kw_match.group(1)) if kw.strip()]

    issues = []
    if len(keywords) < 3:
        issues.append(f"关键词过少({len(keywords)}个),建议5个")
    if len(keywords) > 8:
        issues.append(f"关键词过多({len(keywords)}个),建议5个")

    return {
        "count": len(keywords),
        "keywords": keywords,
        "issues": issues,
        "score": min(100, len(keywords) * 20),
    }


def check_ai_flavor(text):
    """检查 AI 味"""
    issues = []
    ai_score = 0

    # 检查填充词
    for word in AI_PATTERNS["filler_words"]:
        if re.search(word, text):
            issues.append(f"AI 味填充词: '{word}'")
            ai_score += 5

    # 检查模糊归因
    for word in AI_PATTERNS["vague_attribution"]:
        if word in text:
            issues.append(f"模糊归因: '{word}'")
            ai_score += 3

    # 检查结构模式
    for pattern in AI_PATTERNS["structure_patterns"]:
        matches = re.findall(pattern, text)
        if matches:
            issues.append(f"AI 味结构: '{matches[0][:30]}...'")
            ai_score += 5

    # 计算得分(越低越好,转换为0-100)
    score = max(0, 100 - ai_score)

    return {
        "ai_score": ai_score,
        "issues": issues,
        "score": score,
        "grade": "优秀" if score >= 90 else "良好" if score >= 75 else "需改进" if score >= 60 else "严重",
    }


def score_abstract(text):
    """
    综合评分摘要质量。

    Returns
    -------
    dict: {
        "total_score", "structure", "numerical", "innovation", "keywords", "ai_flavor",
        "grade", "issues"
    }
    """
    structure = check_abstract_structure(text)
    numerical = check_numerical_density(text)
    innovation = check_innovation_quantification(text)
    keywords = check_keywords(text)
    ai_flavor = check_ai_flavor(text)

    # 加权总分
    weights = {"structure": 0.25, "numerical": 0.20, "innovation": 0.25, "keywords": 0.10, "ai_flavor": 0.20}
    total_score = (
        structure["score"] * weights["structure"] +
        numerical["score"] * weights["numerical"] +
        innovation["score"] * weights["innovation"] +
        keywords["score"] * weights["keywords"] +
        ai_flavor["score"] * weights["ai_flavor"]
    )

    all_issues = []
    for section in [structure, numerical, innovation, keywords, ai_flavor]:
        all_issues.extend(section.get("issues", []))

    grade = "国一" if total_score >= 85 else "国二" if total_score >= 70 else "省一" if total_score >= 55 else "需改进"

    return {
        "total_score": round(total_score, 1),
        "structure": structure,
        "numerical": numerical,
        "innovation": innovation,
        "keywords": keywords,
        "ai_flavor": ai_flavor,
        "grade": grade,
        "issues": all_issues,
    }


def generate_report(result, output_path=None):
    """生成摘要质量报告"""
    lines = [
        "# 摘要质量评分报告",
        "",
        f"## 总分: {result['total_score']}/100 ({result['grade']})",
        "",
        "## 各维度评分",
        "",
        "| 维度 | 得分 | 权重 | 加权分 |",
        "|------|------|------|--------|",
        f"| 结构(三段式) | {result['structure']['score']} | 25% | {result['structure']['score']*0.25:.1f} |",
        f"| 数值密度 | {result['numerical']['score']} | 20% | {result['numerical']['score']*0.20:.1f} |",
        f"| 创新量化 | {result['innovation']['score']} | 25% | {result['innovation']['score']*0.25:.1f} |",
        f"| 关键词 | {result['keywords']['score']} | 10% | {result['keywords']['score']*0.10:.1f} |",
        f"| AI味(越低越好) | {result['ai_flavor']['score']} | 20% | {result['ai_flavor']['score']*0.20:.1f} |",
    ]

    if result["issues"]:
        lines.extend([
            "",
            "## 问题清单",
            "",
        ])
        for issue in result["issues"]:
            lines.append(f"- {issue}")

    if result["innovation"].get("quantified_items"):
        lines.extend([
            "",
            "## 已量化创新点",
            "",
        ])
        for item in result["innovation"]["quantified_items"]:
            lines.append(f"- {item}")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] 摘要质量报告已生成: {output_path}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="摘要质量自动评分")
    parser.add_argument("--tex", help=".tex 文件路径")
    parser.add_argument("--text", help="直接输入摘要文本")
    parser.add_argument("--output", default="reports/abstract_report.md", help="报告输出路径")
    args = parser.parse_args()

    if args.tex:
        abstract = extract_abstract_from_tex(args.tex)
        if not abstract:
            print("[ERROR] 未能从 .tex 文件中提取摘要")
            sys.exit(1)
    elif args.text:
        abstract = args.text
    else:
        print("请指定 --tex 或 --text")
        sys.exit(1)

    result = score_abstract(abstract)
    generate_report(result, args.output)
    print(f"[SCORE] 摘要总分: {result['total_score']}/100 ({result['grade']})")
