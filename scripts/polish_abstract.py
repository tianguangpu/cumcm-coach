"""
polish_abstract.py — 摘要"5+3"结构检查 + 8稿迭代追踪
======================================================
国一标准：摘要至少修改8稿，嵌入≥3个量化结果值。

用法:
    python polish_abstract.py --tex paper/main.tex
    python polish_abstract.py --tex paper/main.tex --check-5plus3
    python polish_abstract.py --tex paper/main.tex --draft-num 3
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


# ── 5+3 结构定义 ──────────────────────────────────────────────────────

STRUCTURE_5 = [
    ("问题导入", r"(针对|基于|为解决|围绕|本文研究|本文针对|面对)"),
    ("建模思路", r"(建立|构建|提出|采用|引入|设计).*(模型|方法|框架|算法)"),
    ("方法创新", r"(改进|优化|创新|融合|结合|提出).*(策略|机制|权重|结构)"),
    ("关键结论", r"(结果表明|实验显示|分析发现|计算得到|求解得出)"),
    ("实际价值", r"(应用|推广|迁移|参考|指导|意义|价值)"),
]

QUANT_PATTERNS = [
    r"\d+\.?\d*\s*%",                    # 12.3%
    r"\d+\.?\d*\s*(万元|元|美元)",         # 123.45万元
    r"R[²2]\s*[=≈]\s*\d+\.?\d*",        # R²=0.994
    r"RMSE\s*[=≈]\s*\d+\.?\d*",         # RMSE=0.023
    r"MAE\s*[=≈]\s*\d+\.?\d*",          # MAE=0.015
    r"精度(提升|提高|达到)\s*\d+\.?\d*",  # 精度提升12.3%
    r"收敛(速度|快|慢)\s*\d+\.?\d*",     # 收敛速度快2.3倍
    r"(优于|超越|超过)\s*\d+\.?\d*",      # 优于基线12.3%
    r"\d+\.?\d*\s*(倍|次|秒|分钟|小时)",   # 2.3倍
    r"[=≈]\s*\d+\.?\d+",                # =0.994
]


def extract_abstract(tex_path: str) -> str:
    """从LaTeX提取摘要内容。"""
    txt = open(tex_path, encoding="utf-8", errors="ignore").read()
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", txt, re.S)
    if m:
        return m.group(1).strip()
    return ""


def check_5plus3(abstract: str) -> dict:
    """检查摘要是否满足5+3结构。"""
    result = {
        "abstract_length": len(abstract),
        "word_count_cn": len(re.findall(r"[\u4e00-\u9fff]", abstract)),
        "structure_5": {},
        "quant_count": 0,
        "quant_values": [],
        "score": 0,
        "issues": [],
    }

    # 检查5要素
    found_count = 0
    for name, pattern in STRUCTURE_5:
        match = re.search(pattern, abstract)
        result["structure_5"][name] = bool(match)
        if match:
            found_count += 1
        else:
            result["issues"].append(f"缺少要素: {name}")

    # 检查量化值
    for pat in QUANT_PATTERNS:
        matches = re.findall(pat, abstract)
        result["quant_values"].extend(matches)
    result["quant_count"] = len(result["quant_values"])

    if result["quant_count"] < 3:
        result["issues"].append(f"量化值不足: {result['quant_count']}/3")

    # 评分
    score = 0
    score += found_count * 12  # 5要素×12=60分
    score += min(20, result["quant_count"] * 7)  # 量化值×7, 最高20分
    # 长度检查
    if 300 <= result["word_count_cn"] <= 1000:
        score += 10
    elif result["word_count_cn"] < 300:
        score += 5
        result["issues"].append(f"摘要过短: {result['word_count_cn']}字(建议300-1000)")
    else:
        score += 5
        result["issues"].append(f"摘要过长: {result['word_count_cn']}字(建议300-1000)")
    # 关键词检查
    if re.search(r"\\关键词|关键词", abstract):
        score += 10
    else:
        result["issues"].append("缺少关键词")

    result["score"] = min(100, score)
    return result


def track_draft(project_dir: str, abstract: str, draft_num: int = None) -> dict:
    """追踪摘要迭代版本。"""
    state_dir = Path(project_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    history_path = state_dir / "abstract_history.json"

    # 加载历史
    history = []
    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))

    # 确定稿号
    if draft_num is None:
        draft_num = len(history) + 1

    # 记录当前版本
    entry = {
        "draft": draft_num,
        "timestamp": datetime.now().isoformat(),
        "length": len(abstract),
        "word_count": len(re.findall(r"[\u4e00-\u9fff]", abstract)),
        "check": check_5plus3(abstract),
    }
    history.append(entry)

    # 保存
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "draft_num": draft_num,
        "total_drafts": len(history),
        "target_drafts": 8,
        "reached_target": len(history) >= 8,
        "history_path": str(history_path),
    }


def render_report(check_result: dict, draft_info: dict = None) -> str:
    """生成摘要质量报告。"""
    L = []
    L.append("=" * 55)
    L.append("  摘要 '5+3' 结构检查报告")
    L.append("=" * 55)

    # 基础信息
    L.append("\n【基础信息】")
    L.append(f"  字数: {check_result['word_count_cn']} (建议300-1000)")
    L.append(f"  综合得分: {check_result['score']}/100")

    # 5要素
    L.append("\n【5要素结构】")
    for name, found in check_result["structure_5"].items():
        icon = "✓" if found else "✗"
        L.append(f"  {icon} {name}")
    found_count = sum(check_result["structure_5"].values())
    L.append(f"  → {found_count}/5 要素齐全")

    # 量化值
    L.append("\n【量化结果值】")
    L.append(f"  数量: {check_result['quant_count']} (要求≥3)")
    if check_result["quant_values"]:
        L.append(f"  示例: {', '.join(str(v) for v in check_result['quant_values'][:5])}")

    # 迭代追踪
    if draft_info:
        L.append("\n【迭代追踪】")
        L.append(f"  当前: 第{draft_info['draft_num']}稿")
        L.append(f"  目标: {draft_info['target_drafts']}稿")
        L.append(f"  已完成: {draft_info['total_drafts']}/{draft_info['target_drafts']}")
        if draft_info["reached_target"]:
            L.append("  ✓ 已达到8稿迭代要求")
        else:
            L.append(f"  ⚠ 还需{draft_info['target_drafts'] - draft_info['total_drafts']}稿")

    # 问题
    if check_result["issues"]:
        L.append("\n【待修复问题】")
        for i, issue in enumerate(check_result["issues"], 1):
            L.append(f"  {i}. {issue}")

    # 达标判断
    L.append(f"\n{'='*55}")
    if check_result["score"] >= 80:
        L.append(f"  ✓ 摘要质量达标 ({check_result['score']}分)")
    else:
        L.append(f"  ✗ 摘要质量不达标 ({check_result['score']}分), 需优化")

    return "\n".join(L)


def main():
    p = argparse.ArgumentParser(description="摘要5+3结构检查+8稿迭代追踪")
    p.add_argument("--tex", default="paper/main.tex", help="论文LaTeX文件")
    p.add_argument("--check-5plus3", action="store_true", help="仅检查5+3结构")
    p.add_argument("--draft-num", type=int, default=None, help="指定当前稿号")
    p.add_argument("--dir", default=".", help="项目目录")
    a = p.parse_args()

    if not os.path.isfile(a.tex):
        print(f"[err] 未找到 {a.tex}")
        return 1

    abstract = extract_abstract(a.tex)
    if not abstract:
        print("[err] 未找到摘要(\\begin{abstract}...\\end{abstract})")
        return 1

    check = check_5plus3(abstract)

    if a.check_5plus3:
        print(f"5要素: {sum(check['structure_5'].values())}/5")
        print(f"量化值: {check['quant_count']}/3")
        print(f"得分: {check['score']}")
        return 0

    draft = track_draft(a.dir, abstract, a.draft_num)
    print(render_report(check, draft))
    return 0


if __name__ == "__main__":
    sys.exit(main())
