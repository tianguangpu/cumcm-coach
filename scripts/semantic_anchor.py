"""
语义锚点验证 — 借鉴 SAC-Opt 思想
从赛题原始语义提取核心锚点,与生成的模型/论文逐一比对,检查忠实度。

用法:
    python scripts/semantic_anchor.py --problem problem.txt --paper paper/main.tex --state state/decision_log.json
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SemanticAnchor:
    """语义锚点:从赛题中提取的核心约束/目标/变量"""
    anchor_type: str  # "objective" | "constraint" | "variable" | "assumption" | "metric"
    content: str      # 原始语义描述
    keywords: list = field(default_factory=list)
    verified: bool = False
    location: str = ""  # 在论文中的位置
    status: str = "pending"  # "matched" | "partial" | "missing" | "contradicted"


@dataclass
class VerificationResult:
    """验证结果"""
    total_anchors: int = 0
    matched: int = 0
    partial: int = 0
    missing: int = 0
    contradicted: int = 0
    anchors: list = field(default_factory=list)
    score: float = 0.0  # 0-100


def extract_anchors_from_problem(problem_text: str) -> list:
    """
    从赛题文本中提取语义锚点。
    使用规则+关键词匹配,不依赖 LLM。
    """
    anchors = []

    # 目标函数关键词
    objective_patterns = [
        r"(?:最大化|maximize|最大|最高|最优)",
        r"(?:最小化|minimize|最小|最低|最优)",
        r"(?:目标[函数是为]|优化目标|求.*(?:最大|最小))",
    ]

    # 约束条件关键词
    constraint_patterns = [
        r"(?:约束|限制|不超过|至少|不少于|不能|必须|要求)",
        r"(?:s\.t\.|subject to|满足)",
        r"(?:范围|区间|上下限|界限)",
    ]

    # 变量关键词
    variable_patterns = [
        r"(?:决策变量|变量|参数|未知量)",
        r"(?:设|令|定义).*?(?:为|是|=)",
    ]

    # 假设关键词
    assumption_patterns = [
        r"(?:假设|假定|不妨设|忽略|不考虑)",
        r"(?:理想|简化|近似)",
    ]

    # 指标/评价关键词
    metric_patterns = [
        r"(?:评价指标|指标体系|评分|权重|得分)",
        r"(?:R²|RMSE|MAE|MAPE|精度|准确率)",
    ]

    # 分析/比较关键词（评价/数据类题目，如 2012A 葡萄酒评价）
    analysis_patterns = [
        r"(?:分析|比较|差异|显著性|检验|评估|判断)",
    ]
    # 关系/影响关键词
    relation_patterns = [
        r"(?:相关|联系|关系|影响|作用|关联)",
    ]
    # 分级/聚类关键词
    cluster_patterns = [
        r"(?:分级|聚类|分类|排序|分组|等级|档次)",
    ]

    lines = problem_text.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 检测目标
        for pattern in objective_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                anchors.append(SemanticAnchor(
                    anchor_type="objective",
                    content=line,
                    keywords=_extract_keywords(line),
                ))
                break

        # 检测约束
        for pattern in constraint_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                anchors.append(SemanticAnchor(
                    anchor_type="constraint",
                    content=line,
                    keywords=_extract_keywords(line),
                ))
                break

        # 检测假设
        for pattern in assumption_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                anchors.append(SemanticAnchor(
                    anchor_type="assumption",
                    content=line,
                    keywords=_extract_keywords(line),
                ))
                break

        # 检测指标
        for pattern in metric_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                anchors.append(SemanticAnchor(
                    anchor_type="metric",
                    content=line,
                    keywords=_extract_keywords(line),
                ))
                break

        # 检测分析/关系/分级（评价/数据类题目，补优化类题型未覆盖的锚点）
        for anchor_type, patterns in [
            ("analysis", analysis_patterns),
            ("relation", relation_patterns),
            ("cluster", cluster_patterns),
        ]:
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    anchors.append(SemanticAnchor(
                        anchor_type=anchor_type,
                        content=line,
                        keywords=_extract_keywords(line),
                    ))
                    break

    return anchors


def _extract_keywords(text: str) -> list:
    """提取关键词：英文词 + 数学建模术语词典匹配。

    关键修复：不再用 [一-鿿]+ 把整句中文当一个词(导致永远匹配不上论文短词)，
    改为按术语词典提取有意义的短词。
    """
    stop_words = {"的", "了", "是", "在", "有", "和", "与", "对", "将", "把", "被", "从", "到", "为", "以", "用",
                  "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                  "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}

    # 数学建模核心术语（用于中文关键词提取）
    modeling_terms = [
        "分析", "比较", "差异", "显著性", "检验", "评估", "判断",
        "相关", "联系", "关系", "影响", "作用", "关联",
        "分级", "聚类", "分类", "排序", "分组", "等级",
        "目标", "约束", "最大化", "最小化", "最优", "求解",
        "评价", "评分", "权重", "得分", "指标", "综合",
        "灵敏度", "蒙特卡洛", "拟合", "精度", "误差", "鲁棒",
        "模型", "建立", "算法", "回归", "预测", "决策变量", "假设", "参数",
    ]

    keywords = []
    # 英文词
    keywords.extend(re.findall(r"[a-zA-Z]+", text))
    # 中文：术语词典匹配
    for term in modeling_terms:
        if term in text:
            keywords.append(term)
    keywords = [w.lower() for w in keywords if w.lower() not in stop_words and len(w) > 1]
    return list(set(keywords))


def verify_anchors_against_paper(anchors: list, paper_text: str) -> VerificationResult:
    """
    将语义锚点与论文内容比对,检查忠实度。
    """
    result = VerificationResult(total_anchors=len(anchors))

    paper_lower = paper_text.lower()

    for anchor in anchors:
        matched_keywords = 0
        total_keywords = len(anchor.keywords)

        if total_keywords == 0:
            anchor.status = "partial"
            result.partial += 1
            result.anchors.append(anchor)
            continue

        for kw in anchor.keywords:
            if kw in paper_lower:
                matched_keywords += 1

        match_ratio = matched_keywords / total_keywords

        if match_ratio >= 0.7:
            anchor.status = "matched"
            anchor.verified = True
            result.matched += 1
        elif match_ratio >= 0.3:
            anchor.status = "partial"
            result.partial += 1
        else:
            anchor.status = "missing"
            result.missing += 1

        result.anchors.append(anchor)

    # 计算得分
    if result.total_anchors > 0:
        result.score = (result.matched * 100 + result.partial * 50) / result.total_anchors

    return result


def verify_against_decision_log(anchors: list, decision_log_path: str) -> dict:
    """
    与 decision_log.json 交叉验证:
    1. anchors 中的 symbol_conventions 是否被遵守
    2. change_log 中的变更是否已同步到论文
    """
    if not Path(decision_log_path).exists():
        return {"status": "no_log", "issues": ["decision_log.json 不存在"]}

    with open(decision_log_path, encoding="utf-8") as f:
        log = json.load(f)

    issues = []

    # 检查未同步的变更
    for change in log.get("change_log", []):
        if change.get("sync_status") == "pending":
            issues.append(f"未同步变更: {change['type']} - {change['qi']} - {change['old_value']} → {change['new_value']}")

    # 检查符号一致性
    symbol_conventions = log.get("anchors", {}).get("symbol_conventions", {})
    for symbol, meaning in symbol_conventions.items():
        # 这里可以扩展为更详细的符号检查
        pass

    return {
        "status": "checked",
        "issues": issues,
        "pending_changes": len([c for c in log.get("change_log", []) if c.get("sync_status") == "pending"]),
    }


def generate_report(result: VerificationResult, log_check: dict, output_path: Optional[str] = None) -> str:
    """生成语义锚点验证报告"""
    lines = [
        "# 语义锚点验证报告",
        "",
        f"## 总分: {result.score:.1f}/100",
        "",
        "| 类型 | 数量 |",
        "|------|------|",
        f"| 总锚点 | {result.total_anchors} |",
        f"| [OK] 匹配 | {result.matched} |",
        f"| [WARN] 部分匹配 | {result.partial} |",
        f"| [FAIL] 缺失 | {result.missing} |",
        f"| 🚫 矛盾 | {result.contradicted} |",
        "",
        "## 锚点详情",
        "",
        "| 类型 | 内容 | 状态 | 关键词命中 |",
        "|------|------|------|-----------|",
    ]

    for anchor in result.anchors:
        status_icon = {"matched": "[OK]", "partial": "[WARN]", "missing": "[FAIL]", "contradicted": "🚫"}.get(anchor.status, "?")
        lines.append(f"| {anchor.anchor_type} | {anchor.content[:50]}... | {status_icon} {anchor.status} | {len(anchor.keywords)} 个 |")

    if log_check.get("issues"):
        lines.extend([
            "",
            "## 决策日志问题",
            "",
        ])
        for issue in log_check["issues"]:
            lines.append(f"- {issue}")

    report = "\n".join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="语义锚点验证")
    parser.add_argument("--problem", required=True, help="赛题文件路径")
    parser.add_argument("--paper", required=True, help="论文文件路径")
    parser.add_argument("--state", default="state/decision_log.json", help="决策日志路径")
    parser.add_argument("--output", default="reports/semantic_anchor_report.md", help="报告输出路径")
    args = parser.parse_args()

    # 读取文件
    problem_text = Path(args.problem).read_text(encoding="utf-8")
    paper_text = Path(args.paper).read_text(encoding="utf-8")

    # 提取锚点
    anchors = extract_anchors_from_problem(problem_text)
    print(f"[INFO] 提取到 {len(anchors)} 个语义锚点")

    # 验证
    result = verify_anchors_against_paper(anchors, paper_text)
    print(f"[INFO] 匹配: {result.matched}, 部分: {result.partial}, 缺失: {result.missing}")

    # 决策日志交叉验证
    log_check = verify_against_decision_log(anchors, args.state)

    # 生成报告
    report = generate_report(result, log_check, args.output)
    print(f"[OK] 报告已生成: {args.output}")
    print(f"[SCORE] 语义锚点得分: {result.score:.1f}/100")


if __name__ == "__main__":
    main()
