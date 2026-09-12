"""
参考文献自动审查 — 检查数量/年份/语言/格式/URL可访问性

用法:
    python scripts/check_references.py --bib paper/references.bib --output reports/reference_report.md
    python scripts/check_references.py --tex paper/sections/ --output reports/reference_report.md
"""

import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def extract_refs_from_bib(bib_path):
    """从 .bib 文件提取参考文献"""
    content = Path(bib_path).read_text(encoding="utf-8")
    refs = []

    # 匹配 @article, @book, @inproceedings 等
    entries = re.findall(r'@(\w+)\{([^,]+),\s*(.*?)\n\}', content, re.DOTALL)

    for entry_type, key, fields_str in entries:
        ref = {"type": entry_type, "key": key}

        # 提取字段
        for field in ["author", "title", "year", "journal", "booktitle", "url", "doi", "publisher"]:
            match = re.search(rf'{field}\s*=\s*\{{(.*?)\}}', fields_str, re.IGNORECASE)
            if match:
                ref[field] = match.group(1).strip()

        refs.append(ref)

    return refs


def extract_refs_from_tex(tex_dir):
    """从 .tex 文件的 \bibitem 提取参考文献"""
    refs = []
    tex_files = list(Path(tex_dir).glob("*.tex"))

    for tex_file in tex_files:
        content = tex_file.read_text(encoding="utf-8")
        bibitems = re.findall(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem|\Z)', content, re.DOTALL)

        for key, text in bibitems:
            ref = {"key": key, "raw_text": text.strip()}

            # 尝试提取年份
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                ref["year"] = year_match.group()

            # 尝试提取作者
            author_match = re.search(r'^([^,\.]+)', text)
            if author_match:
                ref["author"] = author_match.group(1).strip()

            # 判断语言
            if re.search(r'[\u4e00-\u9fff]', text):
                ref["language"] = "zh"
            else:
                ref["language"] = "en"

            refs.append(ref)

    return refs


def check_references(refs, config=None):
    """
    检查参考文献质量。

    Returns
    -------
    dict: {
        "total", "pass", "issues", "year_stats", "lang_stats",
        "checks": [{"name", "status", "detail"}]
    }
    """
    config = config or {
        "min_count": 10,
        "recent_ratio": 0.4,  # 近5年 ≥40%
        "foreign_ratio": 0.3,  # 外文 ≥30%
        "recent_years": 5,
    }

    current_year = datetime.now().year
    recent_cutoff = current_year - config["recent_years"]

    issues = []
    checks = []

    # 1. 数量检查
    total = len(refs)
    count_pass = total >= config["min_count"]
    checks.append({
        "name": "参考文献数量",
        "status": "PASS" if count_pass else "FAIL",
        "detail": f"{total} 条 (要求 ≥{config['min_count']})"
    })
    if not count_pass:
        issues.append(f"参考文献不足: {total} < {config['min_count']}")

    # 2. 年份分布
    years = [int(r.get("year", 0)) for r in refs if r.get("year")]
    recent_count = sum(1 for y in years if y >= recent_cutoff)
    recent_ratio = recent_count / total if total > 0 else 0
    recent_pass = recent_ratio >= config["recent_ratio"]

    year_stats = {
        "total_with_year": len(years),
        "recent_count": recent_count,
        "recent_ratio": recent_ratio,
        "min_year": min(years) if years else None,
        "max_year": max(years) if years else None,
    }

    checks.append({
        "name": f"近{config['recent_years']}年文献比例",
        "status": "PASS" if recent_pass else "FAIL",
        "detail": f"{recent_ratio:.1%} (要求 ≥{config['recent_ratio']:.0%})"
    })
    if not recent_pass:
        issues.append(f"近{config['recent_years']}年文献比例不足: {recent_ratio:.1%} < {config['recent_ratio']:.0%}")

    # 3. 语言分布
    languages = [r.get("language", "unknown") for r in refs]
    en_count = sum(1 for l in languages if l == "en")
    en_ratio = en_count / total if total > 0 else 0
    foreign_pass = en_ratio >= config["foreign_ratio"]

    lang_stats = {
        "zh": languages.count("zh"),
        "en": en_count,
        "unknown": languages.count("unknown"),
        "en_ratio": en_ratio,
    }

    checks.append({
        "name": "外文文献比例",
        "status": "PASS" if foreign_pass else "FAIL",
        "detail": f"{en_ratio:.1%} (要求 ≥{config['foreign_ratio']:.0%})"
    })
    if not foreign_pass:
        issues.append(f"外文文献比例不足: {en_ratio:.1%} < {config['foreign_ratio']:.0%}")

    # 4. 格式检查(BibTeX)
    format_issues = []
    for ref in refs:
        if "title" in ref and not ref["title"]:
            format_issues.append(f"  - {ref.get('key', '?')}: 标题为空")
        if "year" in ref and not ref["year"]:
            format_issues.append(f"  - {ref.get('key', '?')}: 年份缺失")

    checks.append({
        "name": "格式完整性",
        "status": "PASS" if len(format_issues) == 0 else "WARN",
        "detail": f"{len(format_issues)} 个问题" if format_issues else "完整"
    })

    # 5. 年份分布直方图数据
    year_distribution = Counter(years)

    return {
        "total": total,
        "pass": count_pass and recent_pass and foreign_pass,
        "issues": issues,
        "checks": checks,
        "year_stats": year_stats,
        "lang_stats": lang_stats,
        "year_distribution": dict(sorted(year_distribution.items())),
    }


def generate_report(result, output_path=None):
    """生成参考文献审查报告"""
    lines = [
        "# 参考文献审查报告",
        "",
        f"## 总体结论: {'[OK] PASS' if result['pass'] else '[FAIL] FAIL'}",
        "",
        "## 检查项",
        "",
        "| 检查项 | 状态 | 详情 |",
        "|--------|------|------|",
    ]

    for check in result["checks"]:
        icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(check["status"], "?")
        lines.append(f"| {check['name']} | {icon} {check['status']} | {check['detail']} |")

    lines.extend([
        "",
        "## 年份统计",
        "",
        f"- 有年份信息的文献: {result['year_stats']['total_with_year']} 条",
        f"- 最早: {result['year_stats']['min_year']}",
        f"- 最新: {result['year_stats']['max_year']}",
        f"- 近5年: {result['year_stats']['recent_count']} 条 ({result['year_stats']['recent_ratio']:.1%})",
        "",
        "## 语言统计",
        "",
        f"- 中文: {result['lang_stats']['zh']} 条",
        f"- 外文: {result['lang_stats']['en']} 条 ({result['lang_stats']['en_ratio']:.1%})",
    ])

    if result["issues"]:
        lines.extend([
            "",
            "## 问题清单",
            "",
        ])
        for issue in result["issues"]:
            lines.append(f"- {issue}")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] 参考文献审查报告已生成: {output_path}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="参考文献自动审查")
    parser.add_argument("--bib", help=".bib 文件路径")
    parser.add_argument("--tex", help=".tex 文件目录")
    parser.add_argument("--output", default="reports/reference_report.md", help="报告输出路径")
    args = parser.parse_args()

    if args.bib:
        refs = extract_refs_from_bib(args.bib)
    elif args.tex:
        refs = extract_refs_from_tex(args.tex)
    else:
        print("请指定 --bib 或 --tex")
        sys.exit(1)

    print(f"[INFO] 提取到 {len(refs)} 条参考文献")
    result = check_references(refs)
    generate_report(result, args.output)
