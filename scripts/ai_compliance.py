"""
ai_compliance.py — 国赛 AI 工具使用合规模块 (v2.0)
====================================================
适配《全国大学生数学建模竞赛人工智能工具使用规定》。

功能:
  1. AILogger  — 全程记录 AI 交互日志（提示词/回复/采纳情况）
  2. generate_declaration()  — 生成论文中的「AI工具使用声明」章节
  3. generate_support_pdf()  — 生成支撑材料「AI工具使用详情.pdf」
  4. generate_compliance_package() — 一键打包全部合规材料
  5. check_aigc_risk()  — AIGC 检测风险自检（基于文本特征分析）
  6. estimate_ai_ratio()  — 估算论文 AI 内容比例

用法:
  # 1. 赛前初始化（在 Stage 0 调用）
  from ai_compliance import AILogger
  logger = AILogger(project_dir=".")
  logger.start_session(tools=["Claude Code", "DeepSeek-R1"])

  # 2. 每次 AI 交互后记录
  logger.log_interaction(
      stage="Stage 2 问题拆解",
      purpose="子问题分解与变量定义",
      prompt="请将本题拆解为3个子问题...",
      response="子问题1: ...\n子问题2: ...\n子问题3: ...",
      adopted=True,
      human_changes="调整了子问题2的约束条件表述"
  )

  # 3. 赛后生成合规材料
  logger.generate_declaration()        # → output/ai_declaration.tex
  logger.generate_support_pdf()        # → output/AI工具使用详情.pdf
  logger.generate_compliance_package() # → output/ 全部合规文件

  # 4. AIGC 风险自检
  logger.check_aigc_risk("paper/main.tex")  # → AIGC 风险报告

命令行:
  python ai_compliance.py --init --tools "Claude Code,DeepSeek-R1"
  python ai_compliance.py --log --stage "S2" --purpose "建模" --prompt "..." --response "..."
  python ai_compliance.py --declare
  python ai_compliance.py --support
  python ai_compliance.py --all
  python ai_compliance.py --aigc-check --paper paper/main.tex  # AIGC 风险自检
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── 常量 ──────────────────────────────────────────────────────────────
LOG_FILE = "state/ai_interaction_log.json"
DECLARATION_TEX = "output/ai_declaration.tex"
SUPPORT_TEX = "output/ai_support_detail.tex"
SUPPORT_PDF = "output/AI工具使用详情.pdf"
COMPLIANCE_CHECKLIST = "output/compliance_checklist.json"

# 2026 新规要求的声明模板
DECL_TEMPLATE_NO_AI = (
    "本参赛队在竞赛过程中未使用任何AI工具。"
)
DECL_TEMPLATE_USED = (
    "本参赛队在竞赛过程中使用了AI工具，"
    "主要用于{purposes}，详细使用情况见支撑材料。"
)


# ── AILogger 类 ───────────────────────────────────────────────────────
class AILogger:
    """AI 交互日志记录器，全程追踪 AI 工具使用情况。"""

    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.log_path = self.project_dir / LOG_FILE
        self._ensure_dirs()
        self._log = self._load_log()

    def _ensure_dirs(self):
        (self.project_dir / "state").mkdir(parents=True, exist_ok=True)
        (self.project_dir / "output").mkdir(parents=True, exist_ok=True)

    def _load_log(self) -> dict:
        if self.log_path.exists():
            with open(self.log_path, encoding="utf-8") as f:
                return json.load(f)
        return {
            "session_started": None,
            "tools": [],
            "interactions": [],
            "summary": {},
        }

    def _save(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self._log, f, ensure_ascii=False, indent=2)

    # ── 会话管理 ──

    def start_session(self, tools: list[str]):
        """赛前初始化，记录使用的 AI 工具列表。"""
        self._log["session_started"] = datetime.now().isoformat()
        self._log["tools"] = tools
        self._save()
        print(f"[AI合规] 会话已启动，工具: {', '.join(tools)}")

    def log_interaction(
        self,
        stage: str,
        purpose: str,
        prompt: str,
        response: str,
        adopted: bool = True,
        human_changes: str = "",
        tool: str = "",
    ):
        """记录一次 AI 交互。"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "purpose": purpose,
            "tool": tool or (self._log["tools"][0] if self._log["tools"] else "AI"),
            "prompt_summary": prompt[:500] + ("..." if len(prompt) > 500 else ""),
            "response_summary": response[:500] + ("..." if len(response) > 500 else ""),
            "adopted": adopted,
            "human_changes": human_changes,
        }
        self._log["interactions"].append(entry)
        self._save()
        print(f"[AI合规] 已记录: {stage} / {purpose} (采纳={adopted})")

    def get_summary(self) -> dict:
        """统计 AI 使用概况。"""
        interactions = self._log["interactions"]
        stages = set()
        purposes = []
        adopted_count = 0
        modified_count = 0
        for it in interactions:
            stages.add(it["stage"])
            purposes.append(it["purpose"])
            if it["adopted"]:
                adopted_count += 1
            if it.get("human_changes"):
                modified_count += 1
        summary = {
            "total_interactions": len(interactions),
            "stages_covered": sorted(stages),
            "purposes": list(dict.fromkeys(purposes)),  # 去重保序
            "adopted_count": adopted_count,
            "modified_count": modified_count,
            "tools_used": self._log["tools"],
        }
        self._log["summary"] = summary
        self._save()
        return summary

    # ── 生成论文声明 ──

    def generate_declaration(self, used_ai: bool = True) -> str:
        """
        生成论文中的「AI工具使用声明」LaTeX 章节。
        放置位置: 参考文献之前。
        """
        if not used_ai:
            text = DECL_TEMPLATE_NO_AI
        else:
            purposes = self._log["summary"].get("purposes", [])
            if not purposes:
                purposes = ["代码调试", "语言润色", "文献检索辅助"]
            purpose_str = "、".join(purposes[:5])
            text = DECL_TEMPLATE_USED.format(purposes=purpose_str)

        # 生成 LaTeX 片段
        latex = []
        latex.append("% ── AI 工具使用声明（2026 新规要求） ──")
        latex.append("% 放置位置: \\section*{参考文献} 之前")
        latex.append("\\subsection*{AI工具使用声明}")
        latex.append("")
        latex.append(text)
        latex.append("")

        out_path = self.project_dir / DECLARATION_TEX
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(latex))
        print(f"[AI合规] 声明已生成: {out_path}")
        return "\n".join(latex)

    # ── 生成支撑材料 ──

    def generate_support_pdf(self) -> str:
        """
        生成支撑材料「AI工具使用详情.pdf」的 LaTeX 源文件。
        编译方式: xelatex ai_support_detail.tex
        """
        summary = self.get_summary()
        interactions = self._log["interactions"]

        # 构建交互记录表
        rows = []
        for i, it in enumerate(interactions, 1):
            rows.append(
                f"\\textbf{{{i}.}} & {self._tex_escape(it['stage'])} & "
                f"{self._tex_escape(it['purpose'])} & "
                f"{self._tex_escape(it['tool'])} & "
                f"{'是' if it['adopted'] else '否'} & "
                f"{self._tex_escape(it.get('human_changes', '无需修改'))} \\\\"
            )

        interaction_table = "\n".join(rows) if rows else "（本次竞赛未记录到AI交互）"

        # 构建典型交互示例（取前5条）
        examples = []
        for i, it in enumerate(interactions[:5], 1):
            examples.append(f"""
\\subsubsection*{{示例 {i}: {self._tex_escape(it['purpose'])}}}
\\begin{{itemize}}
  \\item \\textbf{{使用阶段:}} {self._tex_escape(it['stage'])}
  \\item \\textbf{{AI工具:}} {self._tex_escape(it['tool'])}
  \\item \\textbf{{主要提示:}} \\texttt{{{self._tex_escape(it['prompt_summary'][:200])}}}
  \\item \\textbf{{AI回复摘要:}} {self._tex_escape(it['response_summary'][:200])}
  \\item \\textbf{{采纳情况:}} {'已采纳' if it['adopted'] else '未采纳'}
  \\item \\textbf{{人工修改:}} {self._tex_escape(it.get('human_changes', '无需修改'))}
\\end{{itemize}}
""")
        examples_str = "\n".join(examples) if examples else "（无典型交互示例）"

        latex = r"""\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage[margin=2.5cm]{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead[C]{AI工具使用详情 — 支撑材料}
\title{AI工具使用详情说明}
\author{（参赛队编号：\underline{\hspace{3cm}}）}
\date{竞赛日期：\underline{\hspace{4cm}}}
\begin{document}
\maketitle
\tableofcontents
\newpage

\section{所用AI工具名称、版本或型号}
""" + "\n".join(
    f"\\begin{{itemize}}\n  \\item {self._tex_escape(t)}\n\\end{{itemize}}"
    for t in summary["tools_used"]
) + r"""

\section{具体使用目的和环节}
本次竞赛中，AI工具主要用于以下环节：
\begin{enumerate}[label=\arabic*.]
""" + "\n".join(
    f"  \\item {self._tex_escape(p)}" for p in summary["purposes"]
) + r"""
\end{enumerate}

\section{主要提示方式与使用过程说明}
\subsection{使用概况}
\begin{itemize}
  \item 总交互次数：""" + str(summary["total_interactions"]) + r"""
  \item 覆盖阶段数：""" + str(len(summary["stages_covered"])) + r"""
  \item 采纳次数：""" + str(summary["adopted_count"]) + r"""
  \item 经人工修改次数：""" + str(summary["modified_count"]) + r"""
\end{itemize}

\subsection{各阶段交互记录}
\begin{longtable}{p{0.5cm}p{2.5cm}p{3cm}p{2cm}p{1cm}p{3.5cm}}
\toprule
序号 & 使用阶段 & 使用目的 & AI工具 & 采纳 & 人工修改情况 \\
\midrule
\endhead
""" + interaction_table + r"""
\bottomrule
\end{longtable}

\subsection{典型交互示例}
""" + examples_str + r"""

\section{对AI输出的采纳、人工修改和核验情况}
\subsection{总体策略}
本参赛队对AI输出遵循以下原则：
\begin{enumerate}[label=\arabic*.]
  \item \textbf{核心建模独立完成}：模型假设、数学推导、核心算法设计均由参赛队独立完成，AI仅辅助实现和验证。
  \item \textbf{逐项审查核实}：所有AI生成内容均经人工审查，数值结果经独立代码验证，确保准确无误。
  \item \textbf{修改记录留痕}：对AI输出的修改均记录在交互日志中，可追溯。
\end{enumerate}

\subsection{各环节核验详情}
\begin{itemize}
""" + "\n".join(
    f"  \\item \\textbf{{{self._tex_escape(it['stage'])}}}（{self._tex_escape(it['purpose'])}）："
    f"{'已采纳' if it['adopted'] else '未采纳'}，"
    f"{self._tex_escape(it.get('human_changes', '经人工审查无误'))}"
    for it in interactions
) + r"""
\end{itemize}

\end{document}
"""
        out_path = self.project_dir / SUPPORT_TEX
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(latex)
        print(f"[AI合规] 支撑材料 LaTeX 已生成: {out_path}")
        print(f"[AI合规] 编译命令: xelatex {out_path}")
        return str(out_path)

    # ── 一键打包 ──

    def generate_compliance_package(self, used_ai: bool = True) -> dict:
        """一键生成全部合规材料，返回清单。"""
        self.get_summary()
        declaration = self.generate_declaration(used_ai=used_ai)
        support_tex = self.generate_support_pdf()

        # 真实检测: AI 声明是否已插入论文、支撑 PDF 是否已编译
        paper_candidates = [
            self.project_dir / "latex" / "paper.tex",
            self.project_dir / "paper" / "main.tex",
            self.project_dir / "paper.tex",
        ]
        paper_path = next((p for p in paper_candidates if p.exists()), None)
        decl_in_paper = False
        if paper_path:
            ptxt = paper_path.read_text(encoding="utf-8", errors="ignore")
            decl_in_paper = ("AI工具使用声明" in ptxt) or ("AI 工具使用声明" in ptxt)
        support_pdf_compiled = (
            (self.project_dir / SUPPORT_PDF).exists()
            or (self.project_dir / "output" / SUPPORT_PDF).exists()
        )

        checklist = {
            "generated_at": datetime.now().isoformat(),
            "used_ai": used_ai,
            "files": {
                "declaration_tex": DECLARATION_TEX,
                "support_tex": support_tex,
                "support_pdf": SUPPORT_PDF,
                "interaction_log": LOG_FILE,
                "paper_source": str(paper_path) if paper_path else None,
            },
            "checklist": {
                "ai_declaration_in_paper": decl_in_paper,
                "support_pdf_compiled": support_pdf_compiled,
                "prompt_log_complete": len(self._log["interactions"]) > 0,
                "tools_listed": len(self._log["tools"]) > 0,
                "human_review_documented": any(
                    it.get("human_changes") for it in self._log["interactions"]
                ),
            },
            "next_steps": [] if (decl_in_paper and support_pdf_compiled) else [
                "1. 将 output/ai_declaration.tex 内容插入论文参考文献之前",
                "2. 运行 'xelatex output/ai_support_detail.tex' 生成 PDF",
                "3. 将 PDF 放入支撑材料目录，命名为 'AI工具使用详情.pdf'",
                "4. 确认论文中 AI 声明位置正确（参考文献前，独立小节）",
            ],
        }
        checklist_path = self.project_dir / COMPLIANCE_CHECKLIST
        with open(checklist_path, "w", encoding="utf-8") as f:
            json.dump(checklist, f, ensure_ascii=False, indent=2)
        print(f"[AI合规] 合规清单已生成: {checklist_path}")
        return checklist

    # ── 工具函数 ──

    @staticmethod
    def _tex_escape(text: str) -> str:
        """转义 LaTeX 特殊字符。"""
        replacements = {
            "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircrum{}",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    # ── AIGC 风险自检 ──

    # AI 高频词/短语（困惑度低的标志）
    AI_PHRASES = [
        "标志着", "关键作用", "重要贡献", "奠定了坚实基础",
        "发挥了重要作用", "具有重要意义", "突破性的", "令人震撼的",
        "完美的", "极致的", "著名的", "不仅.*而且",
        "在.*方面表现出色", "为.*提供了.*依据", "取得了.*进展",
        "展现了.*潜力", "具有.*优势", "呈现出.*趋势",
    ]

    # AI 典型句式（突发性低的标志）
    AI_SENTENCE_PATTERNS = [
        r"[。，]从而[^。，]{10,30}[。，]",  # "从而...从而" 连锁
        r"通过[^。，]{5,15}，(?:有效|显著|大幅)",  # "通过...有效/显著"
        r"基于[^。，]{5,15}，(?:实现|达到|获得)",  # "基于...实现/达到"
        r"本文(?:提出|设计|构建)了[^。，]{10,40}，(?:能够|可以|有效)",  # "本文提出...能够"
    ]

    def check_aigc_risk(self, paper_path: str) -> dict:
        """
        AIGC 检测风险自检（基于文本特征分析）。
        分析论文的困惑度指标、AI 高频词、句式模式等。
        返回风险评估报告。
        """
        paper = Path(paper_path)
        if not paper.exists():
            return {"error": f"论文文件不存在: {paper_path}"}

        try:
            text = paper.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = paper.read_text(encoding="utf-8", errors="ignore")

        # 读取 sections/ 下所有文件
        sections_dir = paper.parent / "sections"
        if sections_dir.exists():
            for f in sorted(sections_dir.glob("*.tex")):
                try:
                    text += "\n" + f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    pass

        # 去掉 LaTeX 命令和注释
        clean_text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        clean_text = re.sub(r'\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})*', '', clean_text)
        clean_text = re.sub(r'\$[^$]+\$', '', clean_text)  # 去掉行内公式
        clean_text = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # 提取中文句子
        cn_sentences = re.findall(r'[\u4e00-\u9fff][^。！？\n]*[。！？]', clean_text)

        if not cn_sentences:
            return {
                "status": "SKIP",
                "reason": "未检测到中文句子（可能全为公式/代码）",
                "aigc_risk": "LOW",
            }

        # ── 指标 1: AI 高频词检测 ──
        ai_phrase_hits = []
        for phrase in self.AI_PHRASES:
            matches = re.findall(phrase, clean_text)
            if matches:
                ai_phrase_hits.extend(matches)

        # ── 指标 2: AI 句式检测 ──
        ai_pattern_hits = []
        for pattern in self.AI_SENTENCE_PATTERNS:
            matches = re.findall(pattern, clean_text)
            if matches:
                ai_pattern_hits.extend(matches)

        # ── 指标 3: 句子长度均匀度（突发性指标）──
        sent_lengths = [len(s) for s in cn_sentences]
        if len(sent_lengths) > 5:
            import statistics
            mean_len = statistics.mean(sent_lengths)
            stdev_len = statistics.stdev(sent_lengths)
            cv = stdev_len / mean_len if mean_len > 0 else 0
            # CV < 0.3 表示句子长度过于均匀（AI 特征）
            burstiness_score = min(cv / 0.5, 1.0)  # 归一化到 0-1
        else:
            burstiness_score = 0.5  # 样本不足，给中性分

        # ── 指标 4: 首尾句重复模式 ──
        first_sentences = []
        for s in cn_sentences[:20]:
            first_sentences.append(s[:10])
        # 检查是否有大量相同开头
        from collections import Counter
        opening_counter = Counter(first_sentences)
        repetition_ratio = max(opening_counter.values()) / len(first_sentences) if first_sentences else 0

        # ── 综合风险评估 ──
        total_cn_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
        ai_phrase_density = len(ai_phrase_hits) / max(total_cn_chars / 100, 1)
        ai_pattern_density = len(ai_pattern_hits) / max(len(cn_sentences), 1)

        # 风险分数（0-100，越高越危险）
        risk_score = 0
        risk_score += min(ai_phrase_density * 5, 30)  # AI 高频词贡献最多 30 分
        risk_score += min(ai_pattern_density * 40, 25)  # AI 句式贡献最多 25 分
        risk_score += max(0, (0.4 - burstiness_score)) * 40  # 突发性低扣分
        risk_score += max(0, (repetition_ratio - 0.2)) * 50  # 重复开头扣分
        risk_score = min(risk_score, 100)

        # 风险等级
        if risk_score < 20:
            risk_level = "LOW"
            risk_label = "🟢 低风险"
        elif risk_score < 40:
            risk_level = "MEDIUM"
            risk_label = "🟡 中风险"
        elif risk_score < 60:
            risk_level = "HIGH"
            risk_label = "🟠 高风险"
        else:
            risk_level = "CRITICAL"
            risk_label = "🔴 极高风险"

        report = {
            "status": "OK",
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "risk_label": risk_label,
            "metrics": {
                "total_cn_chars": total_cn_chars,
                "total_sentences": len(cn_sentences),
                "ai_phrase_count": len(ai_phrase_hits),
                "ai_phrase_density": round(ai_phrase_density, 3),
                "ai_pattern_count": len(ai_pattern_hits),
                "ai_pattern_density": round(ai_pattern_density, 3),
                "burstiness_score": round(burstiness_score, 3),
                "opening_repetition_ratio": round(repetition_ratio, 3),
            },
            "ai_phrases_found": list(set(ai_phrase_hits))[:10],
            "ai_patterns_found": list({str(p) for p in ai_pattern_hits})[:5],
            "recommendations": [],
        }

        # 生成建议
        if ai_phrase_density > 0.5:
            report["recommendations"].append("AI 高频词过多，建议逐一替换（详见 references/de-ai-writing.md）")
        if ai_pattern_density > 0.1:
            report["recommendations"].append("AI 句式模式过多，建议打乱句子结构")
        if burstiness_score < 0.3:
            report["recommendations"].append("句子长度过于均匀，建议故意制造长短交替")
        if repetition_ratio > 0.3:
            report["recommendations"].append("段落开头重复率高，建议多样化开头句式")
        if risk_score >= 40:
            report["recommendations"].append("整体风险较高，建议参考 references/aigc-awareness.md 逐段改写")

        return report

    def print_aigc_report(self, report: dict):
        """打印 AIGC 风险自检报告。"""
        if report.get("status") == "SKIP":
            print(f"[AIGC自检] {report['reason']}")
            return

        print("\n" + "=" * 60)
        print("  AIGC 检测风险自检报告")
        print("=" * 60)
        print(f"\n  风险等级: {report['risk_label']}  (分数: {report['risk_score']}/100)")
        print("\n  ── 核心指标 ──")
        m = report["metrics"]
        print(f"  中文字符总数: {m['total_cn_chars']}")
        print(f"  中文句子总数: {m['total_sentences']}")
        print(f"  AI 高频词命中: {m['ai_phrase_count']} 个 (密度: {m['ai_phrase_density']})")
        print(f"  AI 句式模式命中: {m['ai_pattern_count']} 个 (密度: {m['ai_pattern_density']})")
        print(f"  句子突发性得分: {m['burstiness_score']} (≥0.3 为安全)")
        print(f"  段首重复率: {m['opening_repetition_ratio']} (≤0.2 为安全)")

        if report.get("ai_phrases_found"):
            print("\n  ── 命中的 AI 高频词 ──")
            for phrase in report["ai_phrases_found"]:
                print(f"    · {phrase}")

        if report.get("recommendations"):
            print("\n  ── 改进建议 ──")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 60)


# ── 命令行入口 ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="2026国赛 AI合规工具")
    sub = parser.add_subparsers(dest="cmd")

    # init
    p_init = sub.add_parser("init", help="初始化AI交互日志")
    p_init.add_argument("--tools", required=True, help="AI工具列表，逗号分隔")
    p_init.add_argument("--dir", default=".", help="项目目录")

    # log
    p_log = sub.add_parser("log", help="记录一次AI交互")
    p_log.add_argument("--stage", required=True, help="使用阶段")
    p_log.add_argument("--purpose", required=True, help="使用目的")
    p_log.add_argument("--prompt", required=True, help="提示词摘要")
    p_log.add_argument("--response", required=True, help="回复摘要")
    p_log.add_argument("--no-adopt", action="store_true", help="未采纳")
    p_log.add_argument("--changes", default="", help="人工修改说明")
    p_log.add_argument("--tool", default="", help="使用的AI工具")
    p_log.add_argument("--dir", default=".", help="项目目录")

    # declare
    p_dec = sub.add_parser("declare", help="生成论文AI声明")
    p_dec.add_argument("--no-ai", action="store_true", help="未使用AI")
    p_dec.add_argument("--dir", default=".", help="项目目录")

    # support
    p_sup = sub.add_parser("support", help="生成支撑材料LaTeX")
    p_sup.add_argument("--dir", default=".", help="项目目录")

    # all
    p_all = sub.add_parser("all", help="一键生成全部合规材料")
    p_all.add_argument("--no-ai", action="store_true", help="未使用AI")
    p_all.add_argument("--dir", default=".", help="项目目录")

    # status
    p_stat = sub.add_parser("status", help="查看当前合规状态")
    p_stat.add_argument("--dir", default=".", help="项目目录")

    # aigc-check
    p_aigc = sub.add_parser("aigc-check", help="AIGC 检测风险自检")
    p_aigc.add_argument("--paper", required=True, help="论文主文件路径")
    p_aigc.add_argument("--dir", default=".", help="项目目录")
    p_aigc.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    if args.cmd == "init":
        logger = AILogger(args.dir)
        tools = [t.strip() for t in args.tools.split(",")]
        logger.start_session(tools)
    elif args.cmd == "log":
        logger = AILogger(args.dir)
        logger.log_interaction(
            stage=args.stage,
            purpose=args.purpose,
            prompt=args.prompt,
            response=args.response,
            adopted=not args.no_adopt,
            human_changes=args.changes,
            tool=args.tool,
        )
    elif args.cmd == "declare":
        logger = AILogger(args.dir)
        logger.get_summary()
        logger.generate_declaration(used_ai=not args.no_ai)
    elif args.cmd == "support":
        logger = AILogger(args.dir)
        logger.get_summary()
        logger.generate_support_pdf()
    elif args.cmd == "all":
        logger = AILogger(args.dir)
        logger.generate_compliance_package(used_ai=not args.no_ai)
    elif args.cmd == "status":
        logger = AILogger(args.dir)
        summary = logger.get_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif args.cmd == "aigc-check":
        logger = AILogger(args.dir)
        report = logger.check_aigc_risk(args.paper)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            logger.print_aigc_report(report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
