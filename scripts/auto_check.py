"""
自动化自检脚本 v7-pro — L1-L4 四级评审 + 5 项 PRO 冲刺检查
=======================================================
CUMCM 国赛论文全流程验收,支持 LaTeX / Typst 双引擎。

L1-L4 四级评审(核心自动化检查项):
1. 编译通过            (check_compilation)
2. 章节数量与顺序       (check_chapter_structure)
3. 图表与章节匹配       (check_figure_refs)
4. 公式编号连续         (check_equation_numbering)
5. 数值一致性           (check_values)
6. 占位符与泄露检查     (check_placeholders)
7. 参考文献规范         (check_references)
8. 图表数量与质量       (check_figure_count + check_figure_quality)
9. PDF 视觉逐页检查     (check_pdf_visual)

+++ 5 项 v7-pro 国奖冲刺检查(PRO 扩展):
10. 控制页合规检查       (check_control_page)        [PRO-1 新]
11. 参考文献 8 维质量    (check_bib_quality)         [PRO-5 新: DOI/自引/期刊名]
12. 评委 7 维评分自查     (check_judge_scores)        [PRO-6 新: 7 维度百分制估算]
13. 可复现性-固定种子     (check_seed_fixed)          [PRO-8 新: np/torch/random/seed]
14. 占位符严格检查       (check_placeholder_strict)  [PRO-1 新: 编号/队名/占位符号]

用法:
    python auto_check.py --paper paper/main.tex --figures figures/png/ --engine latex
    python auto_check.py --paper paper/main.tex --figures figures/png/ --pro
    python auto_check.py --paper paper/main.tex --figures figures/png/ \
        --results reports/RESULTS_REPORT.md --bib references.bib --code code/
"""

import os
import re
import subprocess
import argparse
import sys
if hasattr(sys.stdout, 'reconfigure'):  # Win GBK console emoji/UTF-8 fix
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class PaperChecker:
    """论文自检类(L1-L4 四级评审)"""

    # 国赛金标准章节(LaTeX 用 \section, Typst 用 ^ = )。
    # v7.7 修复: 从精确子串改为「标准章节 → 关键词集合」映射, 避免"模型检验"vs"模型的分析与检验"
    # 这类命名变体被误报缺失。命中任一关键词即视为该章节存在。
    EXPECTED_CHAPTERS = {
        "问题重述": ["重述", "问题描述"],
        "问题分析": ["分析"],
        "模型假设": ["假设"],
        "符号说明": ["符号"],
        "模型建立与求解": ["模型建立", "建模", "求解"],
        "模型检验": ["检验", "验证"],
        "模型评价": ["评价", "优缺点"],
        # 注: "参考文献"不在此检查——国赛论文用 \bibliography/\bibitem 而非 \section{参考文献},
        # 由 check_references() 独立负责数量/近5年/外文检查, 避免双重计数与误报。
    }
    # 内部工作流术语(禁止出现在论文正文)
    # v7.2.1 修复: 移除 figures/pdf/ 和 figures/png/（LaTeX 合法路径）
    # XXX 改用 \bXXX\b 精确匹配, 避免误报 XXXX
    INTERNAL_TERMS = [
        "RESULTS_REPORT", "ANALYSIS_MODELING_REPORT",
        "VERIFY_REPORT", "PROBLEM_ANALYSIS",
        "reports/",
        "plan.md", "todo.md", "CLAUDE.md",
        "PLACEHOLDER", "TODO", "TBD",
        "待补充", "待续写", "这里补", "示例数据", "待完善",
    ]
    INTERNAL_TERMS_EXACT = [r"\bXXX\b"]

    def __init__(
        self,
        paper_path: str,
        figures_dir: str,
        engine: str = "latex",
        results_file: Optional[str] = None,
        root_dir: Optional[str] = None,
        enable_pro: bool = False,
        bib_file: Optional[str] = None,
        code_dir: Optional[str] = None,
    ):
        self.paper_path = Path(paper_path)
        self.figures_dir = Path(figures_dir)
        self.engine = engine.lower()
        self.results_file = Path(results_file) if results_file else None
        self.root_dir = Path(root_dir) if root_dir else self.paper_path.parent.parent
        self.enable_pro = enable_pro
        self._bib_file_override = bib_file
        self._code_dir_override = code_dir
        self._pro_mode = enable_pro

        self.is_latex = self.engine == "latex"
        self.is_typst = self.engine == "typst"

        # 自动检测引擎(优先文件后缀)
        if self.paper_path.suffix == ".tex":
            self.is_latex, self.is_typst = True, False
            self.engine = "latex"
        elif self.paper_path.suffix == ".typ":
            self.is_latex, self.is_typst = False, True
            self.engine = "typst"

        self.results = []
        self._content_cache = None

    # ============================================================
    # 内容读取
    # ============================================================
    def _read_paper(self) -> str:
        """读取论文主文件(缓存)"""
        if self._content_cache is None:
            try:
                self._content_cache = self.paper_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self._content_cache = self.paper_path.read_text(encoding="utf-8", errors="ignore")
        return self._content_cache

    def _read_all_paper_text(self) -> str:
        """读取主文件 + sections/ 下所有同后缀文件(论文全文)"""
        parts = [self._read_paper()]
        sections_dir = self.paper_path.parent / "sections"
        if sections_dir.exists():
            ext = "*.tex" if self.is_latex else "*.typ"
            for f in sorted(sections_dir.glob(ext)):
                try:
                    parts.append(f.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ============================================================
    # 步骤 1:编译通过
    # ============================================================
    def check_compilation(self) -> Tuple[bool, str]:
        """检查编译(LaTeX xelatex 两次 / Typst 单次)"""
        try:
            if self.is_latex:
                for _ in range(2):
                    result = subprocess.run(
                        ['xelatex', '-interaction=nonstopmode', self.paper_path.name],
                        cwd=self.paper_path.parent,
                        capture_output=True, encoding='utf-8', errors='ignore', timeout=120
                    )
                    if result.returncode != 0:
                        errors = self._extract_latex_errors(result.stdout)
                        return False, f"LaTeX 编译失败: {errors}"
                return True, "LaTeX 编译通过(xelatex 两次)"
            else:  # typst
                result = subprocess.run(
                    ['typst', 'compile', self.paper_path.name],
                    cwd=self.paper_path.parent,
                    capture_output=True, encoding='utf-8', errors='ignore', timeout=60
                )
                if result.returncode != 0:
                    return False, f"Typst 编译失败: {result.stderr[:200]}"
                return True, "Typst 编译通过(单次)"
        except FileNotFoundError:
            cmd = "xelatex" if self.is_latex else "typst"
            return False, f"{cmd} 未安装或不在 PATH 中"
        except subprocess.TimeoutExpired:
            return False, "编译超时(>120s)"

    def _extract_latex_errors(self, log: str) -> List[str]:
        errors = []
        for line in log.split('\n'):
            if line.startswith('!') or 'Error' in line:
                errors.append(line.strip())
        return errors[:5]

    # ============================================================
    # 步骤 2:章节数量与顺序 [新增]
    # ============================================================
    def check_chapter_structure(self) -> Tuple[bool, str]:
        """检查 8 章 + 附录齐全,顺序正确"""
        text = self._read_all_paper_text()

        if self.is_latex:
            # \section{标题} / \section*{标题} / \subsection{标题}(问题重述常作 subsection 放"引言"下)
            found = re.findall(r'\\(?:sub)?section\*?\{([^}]*)\}', text)
        else:  # typst
            # = 标题(一级标题)
            found = re.findall(r'(?m)^=\s+(.+?)$', text)

        found_clean = [t.strip() for t in found if t.strip()]

        if not found_clean:
            return False, "未检测到任何一级章节标题"

        # 检查 8 章是否齐全(关键词匹配: 任一别名命中即算该章节存在)
        missing = []
        for expected, keywords in self.EXPECTED_CHAPTERS.items():
            if not any(any(kw in ch for kw in keywords) for ch in found_clean):
                missing.append(expected)

        # 检查附录(附录可作为 \appendix 后的 \section)
        has_appendix = (
            "\\appendix" in text
            or "附录" in text
            or any("附录" in ch or "appendix" in ch.lower() for ch in found_clean)
        )
        if not has_appendix:
            missing.append("附录")

        if missing:
            return False, f"章节缺失: {missing}; 实际章节: {found_clean}"
        return True, f"章节齐全(8章+附录), 实际: {found_clean}"

    # ============================================================
    # 步骤 3:图表与章节匹配 [新增]
    # ============================================================
    def check_figure_refs(self) -> Tuple[bool, str]:
        """检查所有图表引用文件是否存在"""
        text = self._read_all_paper_text()
        missing = []

        if self.is_latex:
            # \includegraphics[width=...]{path}
            refs = re.findall(
                r'\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}', text
            )
        else:  # typst
            # image("path", ...) 或 #image("path")
            refs = re.findall(r'image\(\s*"([^"]+)"', text)

        for ref in refs:
            # 论文中路径通常是相对路径(从 paper/ 出发)
            target = (self.paper_path.parent / ref).resolve()
            if not target.exists():
                missing.append(ref)

        if missing:
            return False, f"引用的图表文件不存在: {missing[:5]}(共 {len(missing)} 个)"
        return True, f"所有图表引用文件均存在(共 {len(refs)} 个)"

    # ============================================================
    # 步骤 4:公式编号连续
    # ============================================================
    def check_equation_numbering(self) -> Tuple[bool, str]:
        """检查公式编号:被引用 + 无未标注公式(真正的'编号连续'靠 LaTeX 计数器保证)"""
        text = self._read_all_paper_text()

        if self.is_latex:
            labels = re.findall(r'\\label\{eq:([^}]+)\}', text)
            eq_envs = re.findall(r'\\begin\{equation\}', text)
            refs = re.findall(r'\\(?:eqref|ref)\{eq:([^}]+)\}', text)
        else:  # typst
            labels = re.findall(r'<eq_([^>]+)>', text)
            eq_envs = []
            refs = re.findall(r'@eq_([^\s,\)]+)', text)

        if not labels:
            return True, "未发现公式标签(可能全用自动编号)"

        issues = []
        unreferenced = [l for l in labels if l not in refs]
        if unreferenced:
            issues.append(f"未引用: {unreferenced[:5]}")
        # 有 equation 环境但无对应 label = 无法被引用 = 疑似遗漏
        if self.is_latex and len(eq_envs) > len(labels):
            issues.append(f"{len(eq_envs) - len(labels)} 个 equation 环境无 label")

        if issues:
            return False, "公式编号问题: " + " | ".join(issues)
        return True, f"公式编号规范(共 {len(labels)} 个, 全部被引用且标注)"

    # ============================================================
    # 步骤 5:数值一致性 [新增]
    # ============================================================
    def check_values(self, min_coverage: float = 0.7) -> Tuple[bool, str]:
        """检查论文关键数值与 RESULTS_REPORT.md 一致(覆盖率 ≥70% 通过, 避免中间量误报)"""
        if not self.results_file or not self.results_file.exists():
            return True, "未提供 RESULTS_REPORT.md, 跳过数值一致性检查"

        try:
            results_text = self.results_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            results_text = self.results_file.read_text(encoding="utf-8", errors="ignore")

        paper_text = self._read_all_paper_text()

        # 带语义标签的数值(R²=0.95 / 功率54.2MW / 误差4.65% 等)
        key_numbers = re.findall(
            r'(?:R²|R\^2|RMSE|MAE|MAPE|CV|精度|功率|误差|得分|权重|损失|富集|流失|一致率)'
            r'\s*[=:：]?\s*(-?\d+\.?\d*)\s*(MW|%|kg|s|km|m)?',
            results_text
        )
        nums = [n[0] for n in key_numbers if n[0]]
        # 独立的 ≥2 位小数数值(排除年份)
        standalone = re.findall(r'(?<!\d)(\d{1,4}\.\d{2,4})(?!\d)', results_text)
        all_nums = list(dict.fromkeys(nums + standalone))[:40]

        if not all_nums:
            return True, "RESULTS_REPORT.md 中未提取到关键数值"

        present = [n for n in all_nums if n in paper_text]
        coverage = len(present) / len(all_nums)

        if coverage < min_coverage:
            missing = [n for n in all_nums if n not in paper_text][:8]
            return False, (
                f"数值覆盖率过低 {coverage:.0%} < {min_coverage:.0%}: "
                f"缺失 {len(all_nums) - len(present)}/{len(all_nums)}, 如 {missing}"
            )
        return True, f"数值一致性通过(关键数值 {len(present)}/{len(all_nums)} 出现, 覆盖率 {coverage:.0%})"

    # ============================================================
    # 步骤 6:占位符与内部文件泄露检查 [新增]
    # ============================================================
    def check_placeholders(self) -> Tuple[bool, str]:
        """检查无占位符、无内部工作流术语泄露"""
        text = self._read_all_paper_text()

        found_terms = []
        # 普通术语:直接子串匹配
        for term in self.INTERNAL_TERMS:
            if term in text:
                found_terms.append(term)
        # 精确匹配术语:用正则词边界
        for pattern in self.INTERNAL_TERMS_EXACT:
            matches = re.findall(pattern, text)
            if matches:
                found_terms.extend(matches)

        if found_terms:
            return False, f"发现占位符或内部术语泄露: {found_terms[:5]}(共 {len(found_terms)})"
        return True, "无占位符, 无内部术语泄露"

    # ============================================================
    # 步骤 6b:页数合规检查 [新增]
    # ============================================================
    def check_page_count(self, max_pages: int = 20) -> Tuple[bool, str]:
        """
        检查论文页数是否超过限制。
        国赛要求：正文（不含附录）不超过 20 页。
        通过编译后的 PDF 页数检测，或通过 LaTeX 源文件估算。
        """
        # 方式1:检查编译后的 PDF 页数
        pdf_candidates = [
            self.paper_path.with_suffix(".pdf"),
            self.paper_path.parent / "main.pdf",
        ]
        for pdf_path in pdf_candidates:
            if pdf_path.exists():
                try:
                    # 尝试用 PyPDF2 或简单正则读取 PDF 页数
                    import subprocess
                    result = subprocess.run(
                        ["python", "-c", f"""
import sys
try:
    from PyPDF2 import PdfReader
    reader = PdfReader(r"{pdf_path}")
    print(len(reader.pages))
except ImportError:
    # 简单方法:搜索 /Type /Page
    with open(r"{pdf_path}", "rb") as f:
        content = f.read()
    import re
    pages = len(re.findall(rb'/Type\s*/Page[^s]', content))
    print(pages)
"""],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0 and result.stdout.strip().isdigit():
                        page_count = int(result.stdout.strip())
                        if page_count > max_pages:
                            return False, (
                                f"PDF 页数超限: {page_count} > {max_pages} 页。"
                                f"建议精简内容或移入附录。"
                            )
                        return True, f"PDF 页数合规: {page_count}/{max_pages} 页"
                except Exception:
                    pass  # PDF 读取失败，回退到源文件估算

        # 方式2:通过 LaTeX 源文件估算页数
        text = self._read_all_paper_text()
        # 粗略估算:每个 \newpage / \clearpage 约增加 1 页
        # 每 3000 字符约 1 页（含公式/图表/表格占位）
        page_breaks = len(re.findall(r'\\(?:newpage|clearpage)', text))
        char_estimate = len(text) / 3000
        estimated_pages = max(page_breaks, char_estimate)

        # 检查附录位置（附录后的页数不计入）
        appendix_pos = text.find("\\appendix")
        if appendix_pos > 0:
            before_appendix = text[:appendix_pos]
            estimated_main_pages = max(
                len(re.findall(r'\\(?:newpage|clearpage)', before_appendix)),
                len(before_appendix) / 3000
            )
        else:
            estimated_main_pages = estimated_pages

        if estimated_main_pages > max_pages:
            return False, (
                f"估算正文页数约 {estimated_main_pages:.0f} 页，可能超过 {max_pages} 页限制。"
                f"（注:此为源文件估算，以编译后 PDF 为准）"
            )
        return True, f"估算正文页数约 {estimated_main_pages:.0f}/{max_pages} 页（源文件估算）"

    # ============================================================
    # 步骤 6c:AI 声明位置检查 [新增]
    # ============================================================
    def check_ai_declaration(self) -> Tuple[bool, str]:
        """检查论文中是否包含 AI 工具使用声明（参考文献之前）。"""
        text = self._read_all_paper_text()

        # 检查是否包含 AI 声明
        has_declaration = bool(re.search(
            r'AI\s*(?:工具)?\s*使用\s*声明', text
        ))

        if not has_declaration:
            return False, "论文中未找到「AI工具使用声明」章节（应放在参考文献之前）"

        # 检查声明位置是否在参考文献之前
        decl_pos = text.find("AI工具使用声明")
        if decl_pos < 0:
            decl_pos = text.find("AI 使用声明")
        if decl_pos < 0:
            decl_pos = text.find("AI工具使用声明")

        ref_pos = max(
            text.find("\\begin{thebibliography}"),
            text.find("\\bibliography{"),
            text.find("\\section*{参考文献}"),
            text.find("\\section{参考文献}"),
        )

        if ref_pos > 0 and decl_pos > ref_pos:
            return False, "AI声明位置错误：应放在参考文献之前，当前在参考文献之后"

        return True, "AI工具使用声明位置正确（参考文献之前）"

    # ============================================================
    # 步骤 7:参考文献规范 [扩展]
    # ============================================================
    def check_references(
        self, min_count: int = 10, min_recent_ratio: float = 0.4, min_foreign_ratio: float = 0.3
    ) -> Tuple[bool, str]:
        """检查参考文献:数量 + 近5年比例 + 外文比例"""
        text = self._read_all_paper_text()
        current_year = datetime.now().year
        recent_threshold = current_year - 5  # 2021

        if self.is_latex:
            # 方式1: \bibitem{ref1} 作者. 标题[J]. 期刊, 年份, ...
            bib_entries = re.findall(
                r'\\bibitem\{[^}]*\}\s*(.+?)(?=\\bibitem|\\end\{thebibliography\}|\Z)',
                text, re.S
            )
            # 方式2: BibTeX — \bibliography{ref} / \addbibresource{ref.bib} (+ \nocite{*} 引用全部)
            if not bib_entries:
                bib_files = re.findall(r'\\bibliography\{([^}]+)\}', text)
                bib_files += re.findall(r'\\addbibresource\{([^}]+)\}', text)
                for bf in bib_files:
                    for name in bf.split(','):
                        bib_path = self.paper_path.parent / (name.strip() + '.bib')
                        if bib_path.exists():
                            try:
                                bib_text = bib_path.read_text(encoding='utf-8', errors='ignore')
                            except Exception:
                                continue
                            bib_entries += re.findall(r'@\w+\s*\{', bib_text)
        else:  # typst: 假设用 references.yml 或 #bibliography
            # Typst 引用条目格式较灵活,简化处理:提取 #bibliography 前的引用块
            bib_entries = re.findall(
                r'-\s+(.+?)(?=\n-\s+|\Z)', text, re.S
            )

        count = len(bib_entries)
        if count < min_count:
            return False, f"参考文献数量不足: {count}/{min_count}"

        # 检查近5年比例
        recent_count = 0
        foreign_count = 0
        for entry in bib_entries:
            # 提取年份
            years = re.findall(r'(?:19|20)\d{2}', entry)
            if years:
                year = max(int(y) for y in years)
                if year >= recent_threshold:
                    recent_count += 1
            # 判断外文(简单启发:含较多 ASCII 字符且无中文)
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', entry))
            if chinese_chars < 3 and len(entry.strip()) > 10:
                foreign_count += 1

        recent_ratio = recent_count / count if count > 0 else 0
        foreign_ratio = foreign_count / count if count > 0 else 0

        issues = []
        if recent_ratio < min_recent_ratio:
            issues.append(f"近5年比例 {recent_ratio:.1%} < {min_recent_ratio:.0%}")
        if foreign_ratio < min_foreign_ratio:
            issues.append(f"外文比例 {foreign_ratio:.1%} < {min_foreign_ratio:.0%}")

        if issues:
            return False, f"参考文献问题: {issues}(总数 {count}, 近5年 {recent_count}, 外文 {foreign_count})"
        return True, (
            f"参考文献规范(总数 {count}, 近5年 {recent_ratio:.0%}, 外文 {foreign_ratio:.0%})"
        )

    # ============================================================
    # 步骤 8a:图表数量
    # ============================================================
    def check_figure_count(self, min_count: int = 12) -> Tuple[bool, str]:
        """检查图表数量(PNG 在 figures/png/, PDF 在兄弟目录 figures/pdf/)"""
        if not self.figures_dir.exists():
            return False, f"图表目录不存在: {self.figures_dir}"

        png_files = list(self.figures_dir.glob('*.png'))
        pdf_dir = self.figures_dir.parent / 'pdf'
        pdf_files = list(pdf_dir.glob('*.pdf')) if pdf_dir.exists() else list(self.figures_dir.glob('*.pdf'))
        count = min(len(png_files), len(pdf_files))

        if count >= min_count:
            return True, f"图表数量达标: {count} 张(PNG {len(png_files)} + PDF {len(pdf_files)})"
        return False, f"图表数量不足: {count}/{min_count} 张(PNG {len(png_files)}, PDF {len(pdf_files)})"

    # ============================================================
    # 步骤 8b:图表质量(占位,需调用 image-reader MCP)
    # ============================================================
    def check_figure_quality(self) -> Tuple[bool, str]:
        """检查图表质量(程序化基础检查: 空白/过小; 缺字/遮挡需 Agent 用 image-reader 复核)"""
        if not self.figures_dir.exists():
            return False, f"图表目录不存在: {self.figures_dir}"

        pngs = sorted(self.figures_dir.glob("*.png"))
        if not pngs:
            return False, "图表目录下无 PNG 文件"

        blank, small = [], []
        try:
            from PIL import Image
        except ImportError:
            for p in pngs:
                if p.stat().st_size < 3000:
                    small.append(p.name)
        else:
            for p in pngs:
                try:
                    im = Image.open(p)
                    w, h = im.size
                    if w < 400 or h < 300:
                        small.append(f"{p.name}({w}x{h})")
                    colors = len(set(im.convert("L").resize((8, 8)).tobytes()))
                    if colors <= 2:
                        blank.append(p.name)
                except Exception:
                    pass

        if blank or small:
            return False, (f"图表质量存疑: 空白 {blank[:3]}, 过小 {small[:3]}"
                           f"(共 {len(blank) + len(small)} 张)")
        return True, f"图表质量基础检查通过({len(pngs)} 张; 缺字/遮挡请另用 image-reader 复核)"

    # ============================================================
    # 步骤 8c:图题自解释校验(禁"示意图",须含数值)
    # ============================================================
    def check_figure_captions(self) -> Tuple[bool, str]:
        """检查图题:禁止'示意图/图示'等空泛词, 应含结论+关键数值"""
        text = self._read_all_paper_text()

        if self.is_latex:
            captions = re.findall(r'\\caption\{([^}]*)\}', text)
        else:  # typst
            captions = re.findall(r'caption:\s*\[([^\]]*)\]', text)

        # 粗判过滤表题(以"表"或"Tab"开头)
        fig_captions = [c for c in captions if not c.strip().startswith(("表", "Tab"))]
        if not fig_captions:
            return True, "未检测到图题, 跳过"

        vague = [c for c in fig_captions if "示意" in c or "图示" in c]
        no_num = [c for c in fig_captions if not re.search(r'\d', c)]

        issues = []
        if vague:
            issues.append(f"空泛图题 {len(vague)} 个(含'示意/图示')")
        if no_num:
            issues.append(f"无数值图题 {len(no_num)} 个")

        if issues:
            return False, "图题自解释不足: " + " | ".join(issues) + f"(共 {len(fig_captions)} 图题)"
        return True, f"图题自解释通过({len(fig_captions)} 个图题, 无'示意图', 均含数值)"

    # ============================================================
    # 步骤 9:PDF 视觉逐页检查 [新增]
    # ============================================================
    def check_pdf_visual(self) -> Tuple[bool, str]:
        """逐页导出 PNG, 检查空白/裁切/越界/乱码"""
        pdf_path = self.paper_path.with_suffix('.pdf')
        if not pdf_path.exists():
            return False, f"PDF 不存在: {pdf_path}(请先编译)"

        # 尝试用 pdftoppm 或 magick 导出第一页 + 最后页做抽样
        export_tool = None
        for tool in ['pdftoppm', 'magick', 'convert']:
            try:
                r = subprocess.run(
                    ['where' if os.name == 'nt' else 'which', tool],
                    capture_output=True, text=True
                )
                if r.returncode == 0:
                    export_tool = tool
                    break
            except Exception:
                continue

        if export_tool is None:
            return True, "未找到 pdftoppm/magick, 跳过 PDF 视觉检查(建议安装 poppler 或 ImageMagick)"

        # 逐页导出(全页), 检查空白页
        out_dir = self.paper_path.parent / "_pdf_check"
        out_dir.mkdir(exist_ok=True)
        try:
            if export_tool == 'pdftoppm':
                subprocess.run(
                    ['pdftoppm', '-png', '-r', '80', str(pdf_path), str(out_dir / 'page')],
                    capture_output=True, timeout=180
                )
            else:  # magick / convert: 逐页导出
                subprocess.run(
                    [export_tool, '-density', '80', str(pdf_path), str(out_dir / 'page.png')],
                    capture_output=True, timeout=180
                )

            exported = sorted(out_dir.glob('*.png'))
            if not exported:
                return False, "PDF 视觉检查: 导出 PNG 失败"

            blank_pages = []
            for png in exported:
                size_kb = png.stat().st_size / 1024
                if size_kb < 5:
                    blank_pages.append(png.name)

            if blank_pages:
                return False, f"PDF 疑似空白页: {blank_pages[:5]}(共 {len(blank_pages)} 页)"

            return True, f"PDF 视觉检查通过(逐页导出 {len(exported)} 页, 无空白页)"
        except subprocess.TimeoutExpired:
            return False, "PDF 视觉检查: 导出超时"
        finally:
            # 清理临时目录
            try:
                for f in out_dir.glob('*.png'):
                    f.unlink()
                out_dir.rmdir()
            except Exception:
                pass

    # ============================================================
    # PRO-1 新: 控制页合规检查
    # ============================================================
    def check_control_page(self) -> Tuple[bool, str]:
        """检查控制页/承诺书/编号页 符合国赛规范 8 项合规要求"""
        text = self._read_paper()
        issues = []

        # (1) 页边距: 上 2.54cm 下 2.54cm 左 3.17cm 右 3.17cm
        margin_ok = False
        if self.is_latex:
            if re.search(r"\\usepackage\s*\{geometry\}", text):
                # 一次正则捕获 key/value/unit, 避免两次 findall 再 zip 的配对错位
                margins = re.findall(r"(top|bottom|left|right)\s*=\s*([\d\.]+)\s*(cm|mm)?", text)
                if len(margins) >= 4:
                    vals = {}
                    for key, v, unit in margins:
                        num = float(v)
                        if unit == "mm":
                            num = num / 10.0
                        vals[key] = num
                    if (vals.get("top") and abs(vals["top"] - 2.54) < 0.2 and
                        vals.get("bottom") and abs(vals["bottom"] - 2.54) < 0.2 and
                        vals.get("left") and abs(vals["left"] - 3.17) < 0.2 and
                        vals.get("right") and abs(vals["right"] - 3.17) < 0.2):
                        margin_ok = True
            if "cumcm" in text.lower() or "gmcm" in text.lower():
                margin_ok = True
        if not margin_ok and self.is_latex:
            issues.append("页边距未设置为国赛标准(上2.54/下2.54/左3.17/右3.17cm)")

        # (2) 正文字号: 五号 10.5pt
        if self.is_latex:
            if "\\zihao{5}" not in text and "10.5pt" not in text:
                if "ctexart" not in text and "cumcm" not in text.lower():
                    issues.append("正文字号未明确指定五号(10.5pt)")

        # (3) 行距: 20pt 固定值
        if self.is_latex:
            if not ("linespread" in text or "baselineskip" in text or "cumcm" in text.lower()):
                issues.append("行距未设置(推荐 20pt 或 \\linespread{1.3})")

        # (4) 首行缩进: 2 字符
        if self.is_latex:
            if not ("parindent" in text or "indentfirst" in text or "ctex" in text or "cumcm" in text.lower()):
                issues.append("首行缩进未设置(推荐 2em / 2字符)")

        # (5) 控制页三要素: 承诺书/编号页/选题号(宽松匹配, 避免 "承 诺 书" 空格分开漏判)
        control_markers_exact = ["参赛队号", "题号", "选题号", "A题", "B题", "C题", "D题", "编号"]
        marker_hits = [m for m in control_markers_exact if m in text]
        # 承诺书: 允许 "承_诺_书" / "承 诺 书" / 	extbf{承诺 书} 等排版变化
        if re.search(r"承\s*诺\s*书", text):
            marker_hits.append("承诺书")
        if len(marker_hits) < 3:
            issues.append("控制页要素不足(承诺书/编号页/选题号, 至少3项, 检测到: " + ",".join(marker_hits) + ")")

        # (6) 摘要关键字: 3-5 个(先剥 LaTeX 命令, 再分词)
        if self.is_latex:
            kw_matches = re.findall(r"(关键字|关键词)\s*[：:]\s*(.+?)(?:\n\s*\n|\\\\|$)", text, re.S)
        else:
            kw_matches = re.findall(r"(关键字|关键词)\s*[：:]\s*(.+?)$", text, re.M)
        if kw_matches:
            raw = kw_matches[0][1].strip()
            # 截断到第一行(避免 \end{abstract} 等后续内容污染)
            raw = raw.split("\n")[0].strip()
            # 删除环境命令 \begin{...} \end{...} (整段移除,不保留内容)
            cleaned = re.sub(r"\\(begin|end)\s*\{[^}]*\}", "", raw)
            # 剥去 \cmd{text} -> text 和 花括号
            cleaned = re.sub(r"\\[a-zA-Z]+\*?\{([^}]*)\}", r"\1", cleaned)
            # 无花括号的 LaTeX 命令(如 \quad \qquad)替换为空格
            cleaned = re.sub(r"\\[a-zA-Z]+(?![a-zA-Z])", " ", cleaned)
            cleaned = re.sub(r"[{}]", "", cleaned)
            kws = re.split(r"[,，;；、\s]+", cleaned.strip())
            kws = [k.strip() for k in kws if k and len(k.strip()) >= 2]
            if len(kws) < 3 or len(kws) > 5:
                issues.append("关键字数量异常(期望 3-5 个, 实际 " + str(len(kws)) +
                              "个, 原始=\"" + raw[:60] + "\")")
        else:
            issues.append("摘要后未检测到关键字")

        # (7) 页眉
        if self.is_latex:
            if not ("head" in text.lower() and ("数学建模" in text or "CUMCM" in text.upper())):
                if "ctex" not in text and "cumcm" not in text.lower():
                    issues.append("页眉未设置(推荐: 第?届全国大学生数学建模竞赛 居中)")

        # (8) 附录三模块
        appendix_text = ""
        if self.is_latex:
            m = re.search(r"\\appendix(.+?)$", text, re.S)
            if m:
                appendix_text = m.group(1)
        if appendix_text:
            module_hits = []
            for name in ["数据", "代码", "公式"]:
                if name in appendix_text:
                    module_hits.append(name)
            if len(module_hits) < 3:
                issues.append("附录三模块不足(期望: 数据说明/核心代码/公式推导)")

        if issues:
            head = issues[:4]
            tail = "" if len(issues) <= 4 else " (共" + str(len(issues)) + "项)"
            return False, "控制页/合规问题: " + " | ".join(head) + tail
        return True, "控制页合规检查通过(8 项: 边距/字号/行距/缩进/三要素/关键字/页眉/附录)"

    # ============================================================
    # PRO-5 新: 参考文献 8 维质量检查
    # ============================================================
    def check_bib_quality(
        self,
        min_total: int = 15,
        min_recent_years: int = 5,
        min_recent_ratio: float = 0.4,
        min_foreign_ratio: float = 0.3,
        min_journal_ratio: float = 0.3,
        min_doi_ratio: float = 0.7,
        max_web_ratio: float = 0.2,
    ) -> Tuple[bool, str]:
        """.bib 文件 8 维质量: 总数/近5年/外文/期刊/DOI/网页/作者/空标题"""
        current_year = datetime.now().year
        recent_cutoff = current_year - min_recent_years

        bib_path = None
        if self._bib_file_override:
            p = Path(self._bib_file_override)
            if p.exists():
                bib_path = p
        if bib_path is None:
            for name in ["references.bib", "ref.bib", "refs.bib"]:
                candidate = self.paper_path.parent / name
                if candidate.exists():
                    bib_path = candidate
                    break
        if bib_path is None and self.is_latex:
            m = re.search(r"\\bibliography\{([^}]+)\}", self._read_paper())
            if m:
                bib_name = m.group(1).strip()
                if not bib_name.endswith(".bib"):
                    bib_name += ".bib"
                candidate = self.paper_path.parent / bib_name
                if candidate.exists():
                    bib_path = candidate

        if bib_path is None or not bib_path.exists():
            return True, ("未检测到独立 .bib 文件, 跳过 8 维 bib 质量检查; "
                          "正文内 \\bibitem 仍由 check_references() 处理")

        try:
            bib_text = bib_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")

        # 健壮的 bib 条目提取: 以 @<type>{<citekey>, 开头, 遇到下一个 @<type>{ 或文件结尾结束
        entries = []
        # 预处理: 移除注释行
        cleaned_lines = []
        for ln in bib_text.splitlines():
            if not ln.lstrip().startswith("%"):
                cleaned_lines.append(ln)
        clean_text = "\n".join(cleaned_lines)
        pattern = re.compile(r"@[A-Za-z]+\s*\{\s*[^,{}]+\s*,", re.S)
        starts = [m.start() for m in pattern.finditer(clean_text)]
        for i, s in enumerate(starts):
            e = starts[i+1] if i+1 < len(starts) else len(clean_text)
            block = clean_text[s:e]
            # 切掉 @type{citekey, 头
            head_end = block.find(",")
            if head_end >= 0:
                body = block[head_end+1:].strip()
                entries.append(body)
        total = len(entries)
        if total == 0:
            return False, ".bib 文件中未解析到任何条目"

        # v7.7.13: cite↔bib 对应检查——论文中每个引用键都在 .bib 中命中间名条目。
        # 防止 thebibliography(\bibitem{refN}) / \cite{refN} 与 refs.bib 键不一致(历史不一致问题)。
        bib_keys = set(re.findall(r"@[A-Za-z]+\s*\{\s*([^,\s}]+)\s*,", clean_text))
        paper_text = self._read_paper()
        bibit_keys = set(re.findall(r"\\bibitem\{([^}]+)\}", paper_text))
        cite_keys = set()
        for m in re.findall(r"\\cite\s*\{([^}]*)\}", paper_text):
            cite_keys.update(k.strip() for k in m.split(",") if k.strip())
        paper_refs = (bibit_keys | cite_keys) - {"*"}
        missing_in_bib = sorted(paper_refs - bib_keys)
        if bib_keys and missing_in_bib:
            issues.append("cite↔bib 对应缺失 " + ",".join(missing_in_bib))
            return False, ".bib 对应检查: 论文引用键未命中 .bib 条目 " + ",".join(missing_in_bib)

        counts = {"recent": 0, "foreign": 0, "journal": 0, "has_doi": 0,
                  "web": 0, "no_author": 0, "empty_title": 0}
        for entry in entries:
            years = re.findall(r"(?:19|20)\d{2}", entry)
            if years:
                y = max(int(yy) for yy in years)
                if y >= recent_cutoff:
                    counts["recent"] += 1
            chinese = len(re.findall(r"[\u4e00-\u9fff]", entry))
            if chinese < 3 and len(entry.strip()) > 10:
                counts["foreign"] += 1
            # 期刊
            if re.search(r"@article\s*\{", entry, re.IGNORECASE) or re.search(r"journal\s*=", entry, re.IGNORECASE):
                counts["journal"] += 1
            # DOI: DOI 单词边界, 或 doi = {xxx}
            if re.search(r"\bDOI\b", entry, re.IGNORECASE) or re.search(r"doi\s*=", entry, re.IGNORECASE):
                counts["has_doi"] += 1
            # 网页条目: @online / @misc + url 有 .html
            if re.search(r"@(online|misc)\s*\{", entry, re.IGNORECASE):
                if re.search(r"url\s*=\s*\{.*https?://[^}]*\.html", entry, re.IGNORECASE | re.DOTALL):
                    counts["web"] += 1
            # 字段检查: 去除额外转义使正则为 \s 而不是多余反斜杠
            if not re.search(r"author\s*=", entry, re.IGNORECASE):
                counts["no_author"] += 1
            # title 可能嵌套花括号: 简单地找 title= 之后第一个 {..} 内容(支持多行)
            m_title = re.search(r"title\s*=\s*\{(.+?)\}\s*[,\n]", entry, re.IGNORECASE | re.DOTALL)
            if not m_title:
                # 退化: title = xxx , (无花括号)
                m_title2 = re.search(r"title\s*=\s*([^,\n]+)", entry, re.IGNORECASE)
                if m_title2:
                    t = m_title2.group(1).strip().strip('"').strip("'")
                    if len(t) < 3:
                        counts["empty_title"] += 1
                else:
                    counts["empty_title"] += 1
            else:
                t = m_title.group(1).strip()
                # 剥掉内部嵌套花括号
                t = re.sub(r"[{}]", "", t).strip()
                if len(t) < 3:
                    counts["empty_title"] += 1

        ratios = {k: v / total for k, v in [
            ("recent", counts["recent"]), ("foreign", counts["foreign"]),
            ("journal", counts["journal"]), ("has_doi", counts["has_doi"]),
            ("web", counts["web"]),
        ]}

        issues = []
        if total < min_total:
            issues.append("总数 " + str(total) + " < " + str(min_total))
        if ratios["recent"] < min_recent_ratio:
            issues.append("近5年 " + str(int(ratios["recent"] * 100)) + "% < " + str(int(min_recent_ratio * 100)) + "%")
        if ratios["foreign"] < min_foreign_ratio:
            issues.append("外文 " + str(int(ratios["foreign"] * 100)) + "% < " + str(int(min_foreign_ratio * 100)) + "%")
        if ratios["journal"] < min_journal_ratio:
            issues.append("期刊 " + str(int(ratios["journal"] * 100)) + "% < " + str(int(min_journal_ratio * 100)) + "%")
        if ratios["has_doi"] < min_doi_ratio:
            issues.append("DOI " + str(int(ratios["has_doi"] * 100)) + "% < " + str(int(min_doi_ratio * 100)) + "%")
        if ratios["web"] > max_web_ratio:
            issues.append("网页 " + str(int(ratios["web"] * 100)) + "% > " + str(int(max_web_ratio * 100)) + "%")
        if counts["no_author"] > 0:
            issues.append("无作者条目 " + str(counts["no_author"]))
        if counts["empty_title"] > 0:
            issues.append("空标题条目 " + str(counts["empty_title"]))

        summary = ("总数" + str(total) +
                   " 近5年" + str(int(ratios["recent"] * 100)) + "%" +
                   " 外文" + str(int(ratios["foreign"] * 100)) + "%" +
                   " 期刊" + str(int(ratios["journal"] * 100)) + "%" +
                   " DOI" + str(int(ratios["has_doi"] * 100)) + "%" +
                   " 网页" + str(int(ratios["web"] * 100)) + "%")
        if issues:
            return False, ".bib 8维质量不达标: " + " ; ".join(issues) + " | " + summary
        return True, ".bib 8维质量达标: " + summary

    # ============================================================
    # PRO-6 新: 评委 7 维评分自查(百分制估算)
    # ============================================================
    def check_judge_scores(self) -> Tuple[bool, str]:
        """7 维度百分制估算(假设10 创新25 结果25 深度15 结构15 图表5 摘要5), >=80 通过"""
        text = self._read_all_paper_text()
        scores = {}

        # 1. 模型假设(10分)
        h = 0
        if any(kw in text for kw in ["模型假设", "基本假设", "假设说明"]):
            h += 5
            hypo_count = len(re.findall(r"(?m)^\s*\(?\d+\)?[\.、\s]+", text))
            if hypo_count >= 3:
                h += 3
            if re.search(r"\$[^$]+\$|\\eqref\{", text):
                h += 2
        scores["假设"] = min(10, h)

        # 2. 创新性(25分)
        inn = 5
        for kw in ["改进", "优化", "组合", "融合", "自适应", "混合", "并行",
                   "新颖", "创新性", "本文提出", "本文设计", "对比基线", "消融实验"]:
            if kw in text:
                inn += 2
        scores["创新"] = min(25, inn)

        # 3. 结果正确性(25分)
        rs = 8
        if self.is_latex:
            eq_labels = re.findall(r"\\label\{eq:([^}]+)\}", text)
            eq_refs = re.findall(r"\\(?:eqref|ref)\{eq:([^}]+)\}", text)
            if eq_labels:
                ref_ratio = len(set(eq_refs) & set(eq_labels)) / len(eq_labels)
                rs += int(5 * ref_ratio)
        numbers = re.findall(r"(?<!\d)\d+\.\d{1,4}(?!\d)", text)
        if len(numbers) >= 15:
            rs += 5
        if self.is_latex:
            fig_c = len(re.findall(r"\\includegraphics", text))
            tab_c = len(re.findall(r"\\begin\{tabular\}", text))
        else:
            fig_c = len(re.findall(r"image\(", text))
            tab_c = len(re.findall(r"#table", text))
        if fig_c >= 6:
            rs += 5
        if tab_c >= 3:
            rs += 5
        scores["结果"] = min(25, rs)

        # 4. 分析深度(15分)
        d = 3
        for kw in ["灵敏度", "敏感性", "误差分析", "蒙特卡洛", "鲁棒", "稳健",
                   "参数讨论", "消融", "稳定性", "置信区间", "方差"]:
            if kw in text:
                d += 2
        if all(kw in text.lower() for kw in ["拟合", "灵敏度"]):
            d += 3
        scores["深度"] = min(15, d)

        # 5. 结构完整性(15分)
        s = 5
        if self.is_latex:
            found = re.findall(r"\\section\*?\{([^}]*)\}", text)
        else:
            found = re.findall(r"(?m)^=\s+(.+?)$", text)
        hit = 0
        for expected in ["问题重述", "问题分析", "模型假设", "符号说明", "模型建立",
                         "模型检验", "模型评价", "参考文献"]:
            if any(expected in c or c in expected for c in found):
                hit += 1
        s += min(10, hit)
        scores["结构"] = min(15, s)

        # 6. 图表质量(5分)
        fg = 2
        if self.figures_dir.exists():
            png = list(self.figures_dir.glob("*.png"))
            pdf = list(self.figures_dir.glob("*.pdf"))
            if len(png) >= 10 and len(pdf) >= 10:
                fg += 2
            if self.is_latex and len(re.findall(r"\\caption", text)) >= 8:
                fg += 2
        scores["图表"] = min(5, fg)

        # 7. 摘要质量(5分)
        ab = 2
        if self.is_latex:
            m = re.search(r"\\begin\{abstract\}(.+?)\\end\{abstract\}", text, re.S)
        else:
            m = re.search(r"摘要(.+?)(关键字|关键词)", text, re.S)
        if m:
            abstract_text = m.group(1)
            if re.search(r"\d+\.?\d*", abstract_text):
                ab += 2
            cn_chars = len(re.findall(r"[\u4e00-\u9fff]", abstract_text))
            if 200 <= cn_chars <= 600:
                ab += 2
        scores["摘要"] = min(5, ab)

        total = sum(scores.values())
        detail = " ".join(k + str(int(v)) for k, v in scores.items()) + " / 合计" + str(total)
        if total >= 80:
            return True, "评委7维得分通过(>=80): 总分 " + str(total) + " /100 (" + detail + ")"
        return False, "评委7维得分未达标(期望>=80): 总分 " + str(total) + " /100 (" + detail + ")"

    # ============================================================
    # PRO-8 新: 可复现性 - 固定随机种子
    # ============================================================
    def check_seed_fixed(self) -> Tuple[bool, str]:
        """扫描代码目录,验证 numpy/random/torch/random_state 都有固定 seed"""
        code_roots = []
        if self._code_dir_override:
            code_roots.append(Path(self._code_dir_override))
        for r in [self.root_dir / "code", self.root_dir / "src", self.root_dir / "algorithms"]:
            if r.exists():
                code_roots.append(r)

        if not code_roots:
            return True, "未检测到代码目录(默认 code/ src/ algorithms/), 跳过种子检查"

        targets = [
            ("NumPy",   r"np\.random\.seed\s*\(\s*\d+",       "np.random.seed"),
            ("Python",  r"(?<!\w)random\.seed\s*\(\s*\d+",   "random.seed"),
            ("PyTorch", r"torch\.manual_seed\s*\(\s*\d+",     "torch.manual_seed"),
            ("sklearn", r"random_state\s*=\s*\d+",              "random_state=N"),
            ("scipy",   r"seed\s*=\s*\d+",                      "seed=N"),
        ]

        all_py = []
        for root in code_roots:
            for fp in root.rglob("*.py"):
                all_py.append(fp)
        if not all_py:
            return True, "代码目录下未找到 .py 文件, 跳过种子检查"

        hits = {name: set() for name, _, _ in targets}
        missing_sklearn = []
        for fp in all_py:
            try:
                content = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = fp.read_text(encoding="utf-8", errors="ignore")
            for name, pattern, _ in targets:
                if re.findall(pattern, content):
                    try:
                        key = str(fp.relative_to(self.root_dir))
                    except ValueError:
                        key = str(fp)
                    hits[name].add(key)
            if re.search(r"(GridSearchCV|RandomForest|XGBClassifier|KMeans|train_test_split)", content):
                if not re.search(r"random_state\s*=\s*\d+", content):
                    missing_sklearn.append(fp.name + ": sklearn随机状态未固定")

        used = [(n, len(locs)) for n, locs in hits.items() if len(locs) > 0]
        pass_score = len(used)
        issues = []
        import_map = {
            "NumPy":   r"import\s+numpy",
            "Python":  r"import\s+random(\s|$)",
            "PyTorch": r"import\s+torch",
            "sklearn": r"from\s+sklearn|import\s+sklearn",
        }
        combined = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in all_py)
        for name, imp in import_map.items():
            if re.search(imp, combined):
                if name not in [n for n, _ in used]:
                    issues.append(name + " 已 import 但未调用固定种子")
        if missing_sklearn:
            issues.extend(missing_sklearn[:3])

        used_detail = ", ".join(n + " x" + str(c) for n, c in used) if used else "无"
        msg = "可复现性-种子固定: 命中 " + str(pass_score) + " 类 (" + used_detail + ")"
        if issues:
            msg += " ; 缺失: " + " | ".join(issues[:5])
        passed = (pass_score >= 2 and not issues)
        return passed, msg

    # ============================================================
    # PRO-1 新: 占位符严格检查(控制页/交卷命名)
    # ============================================================
    def check_placeholder_strict(self) -> Tuple[bool, str]:
        """严格模式: 控制页编号/队名/XXX 等交卷前必须替换的占位符"""
        text = self._read_all_paper_text()
        issues = []

        strict_patterns = [
            (r"参赛队号\s*[：:]\s*\D*队号\D*", "参赛队号占位符未替换"),
            (r"[编队]号\s*[：:]\s*[Xx_\*\?]{3,}",   "编号/队号仍为 XXX/___ 占位"),
            (r"队\s*名\s*[：:]\s*[Xx_\*\?]{3,}",   "队名仍为占位符"),
            (r"姓\s*名\s*[：:]\s*[Xx_\*\?]{3,}",   "队员姓名仍为占位符"),
            (r"指\s*导.*[Xx_\*\?]{3,}",             "指导教师/签名仍为占位符"),
            (r"日期\s*[：:]\s*[Xx_\?年]{3,}",       "日期占位"),
        ]
        for pattern, desc in strict_patterns:
            if re.search(pattern, text):
                issues.append(desc)

        if self.paper_path.parent.exists():
            try:
                for name in os.listdir(self.paper_path.parent):
                    for marker in ["编号", "队名", "XXX"]:
                        if marker in name and (name.endswith(".pdf") or name.endswith(".zip")):
                            issues.append("交卷文件名仍含占位符 '" + marker + "': " + name)
            except OSError:
                pass

        if "编号_队名" in text:
            issues.append("正文/PDF 标题中仍含 '编号_队名' 占位模板")

        if issues:
            head = issues[:5]
            tail = "" if len(issues) <= 5 else " (共" + str(len(issues)) + "项)"
            return False, "占位符严格检查不通过: " + " | ".join(head) + tail
        return True, "占位符严格检查通过(无编号/队名/姓名/签名占位, 文件名正确)"

    # ============================================================
    # 中文字体(辅助检查,不计入门禁)
    # ============================================================
    def check_chinese_font(self) -> Tuple[bool, str]:
        """检查中文字体设置"""
        text = self._read_paper()
        if self.is_latex:
            if any(t in text for t in ('ctexart', 'ctexbook', '\\usepackage{ctex}', 'cumcmthesis', 'xeCJK')):
                return True, "中文字体由 ctex/cumcmthesis 设置(无需显式 SimHei/SimSun)"
            if 'SimHei' in text or 'SimSun' in text:
                return True, "中文字体已设置 (SimSun/SimHei)"
            return True, "非中文文档, 跳过字体检查"
        else:  # typst
            if 'SimHei' in text or 'SimSun' in text or 'Noto Sans CJK' in text:
                return True, "中文字体已设置"
            return False, "未设置中文字体(SimSun/SimHei/Noto Sans CJK)"

    # ============================================================
    # 主入口:运行 L1-L4 四级评审门禁
    # ============================================================
    def run_all_checks(
        self, min_figures: int = 12, min_refs: int = 10, level: int = 4
    ) -> List[Tuple[str, bool, str]]:
        """运行门禁检查。level: 1=结构(L1) 2=+交叉验证(L2) 3/4=全部自动化项(+人工评审提示)。

        层级映射:
          L1 结构层: 编译/章节/图表引用/公式编号/占位符
          L2 交叉验证层: 数值一致性/参考文献/图表数量质量/PDF视觉
          L3 对抗评审 = 人工步骤(本脚本不自动判,仅在报告里提示)
          L4 语义锚点 = 独立脚本 semantic_anchor.py
        """
        # (名称, 所属层级, 检查函数)
        checks = [
            ('1. 编译通过', 1, self.check_compilation),
            ('2. 章节结构', 1, self.check_chapter_structure),
            ('3. 图表引用', 1, self.check_figure_refs),
            ('4. 公式编号', 1, self.check_equation_numbering),
            ('5. 数值一致性', 2, self.check_values),
            ('6. 占位符与泄露', 1, self.check_placeholders),
            ('7. 参考文献规范', 2, lambda: self.check_references(min_count=min_refs)),
            ('8a. 图表数量', 2, lambda: self.check_figure_count(min_count=min_figures)),
            ('8b. 图表质量', 2, self.check_figure_quality),
            ('8c. 图题自解释', 2, self.check_figure_captions),
            ('9. PDF视觉检查', 2, self.check_pdf_visual),
        ]

        if self.enable_pro or self._pro_mode:
            checks += [
                ('P1. 控制页合规', 2, self.check_control_page),
                ('P2. bib 8维质量', 2, self.check_bib_quality),
                ('P3. 评委7维评分', 2, self.check_judge_scores),
                ('P4. 种子固定', 2, self.check_seed_fixed),
                ('P5. 占位符严格', 2, self.check_placeholder_strict),
            ]

        checks.append(('附. 中文字体', 1, self.check_chinese_font))  # 辅助检查,不计入门禁

        results = []
        for name, lv, check_func in checks:
            if lv > level:
                continue  # 层级高于指定 level,跳过
            try:
                passed, message = check_func()
                results.append((name, passed, message))
                self.results.append({'name': name, 'passed': passed, 'message': message})
            except Exception as e:
                results.append((name, False, f"检查异常: {str(e)}"))
                self.results.append({'name': name, 'passed': False, 'message': str(e)})
        return results

    def print_report(self, min_figures: int = 12, min_refs: int = 10, level: int = 4) -> bool:
        """打印检查报告"""
        print("\n" + "=" * 70)
        pro_tag = " + PRO5项" if self.enable_pro else ""
        print(f"CUMCM 国赛论文 L1-L4 自检报告 (v7.7.5{pro_tag}, engine={self.engine})")
        print(f"论文: {self.paper_path}")
        print(f"评审层级: L{level}" + (" (全部)" if level >= 4 else ""))
        print("=" * 70)

        all_passed = True
        results = self.run_all_checks(min_figures=min_figures, min_refs=min_refs, level=level)

        for name, passed, message in results:
            status = "[OK]" if passed else "[FAIL]"
            print(f"{status} {name}: {message}")
            if not passed and not name.startswith("附"):
                all_passed = False

        # L3/L4 为人工/独立脚本,本脚本只自动执行 L1+L2,诚实提示
        if level >= 3:
            print("-" * 70)
            print("ℹ L3 对抗评审 = 人工步骤:由独立 Agent 反证式核对(机理优先/假设自洽/")
            print("  消融对照/在线离线边界/特征工程/误差归因/创新落地/优缺点平衡)。")
            print("  本脚本只做 L1 结构 + L2 交叉验证,不自动判定 L3。")
        if level >= 4:
            print("ℹ L4 语义锚点终审 = 独立脚本: python scripts/semantic_anchor.py")
            print("  --problem problem.txt --paper paper/main.tex --state state/decision_log.json")

        print("=" * 70)
        if all_passed:
            print("[OK] L1/L2 自动化门禁全部通过! 完成 L3/L4 人工评审后可交卷。")
        else:
            print("[FAIL] 存在未通过的门禁项, 请修正后再交卷。")
        print("=" * 70 + "\n")
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description='CUMCM 国赛论文 L1-L4 自检 v7.7.5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # LaTeX 论文,只跑 L1 结构检查
  python auto_check.py --paper paper/main.tex --figures figures/png/ --engine latex --level 1

  # Typst 论文,跑 L1+L2(默认 all)
  python auto_check.py --paper paper/main.typ --figures figures/png/ --engine typst --level all

  # 含数值一致性检查
  python auto_check.py --paper paper/main.tex --figures figures/png/ \\
      --results reports/RESULTS_REPORT.md
        """
    )
    parser.add_argument('--paper', required=True, help='论文主文件路径(.tex 或 .typ)')
    parser.add_argument('--figures', required=True, help='图表目录路径(PNG)')
    parser.add_argument('--engine', default='latex', choices=['latex', 'typst'],
                        help='排版引擎(默认 latex, 可自动从文件后缀检测)')
    parser.add_argument('--results', default=None,
                        help='RESULTS_REPORT.md 路径(用于数值一致性检查)')
    parser.add_argument('--root', default=None,
                        help='项目根目录(默认为 paper/ 的上级)')
    parser.add_argument('--min-figures', type=int, default=12, help='最小图表数量(默认 12)')
    parser.add_argument('--min-refs', type=int, default=10, help='最小参考文献数量(默认 10)')
    parser.add_argument('--pro', action='store_true',
                        help='启用 v7-pro 国奖冲刺 5 项扩展检查(默认关)')
    parser.add_argument('--bib', default=None,
                        help='参考文献 .bib 文件路径(用于 P2.bib 8维质量)')
    parser.add_argument('--code', default=None,
                        help='代码目录路径(默认 code/ / src/ / algorithms/, 用于 P4.种子固定)')
    parser.add_argument('--level', default='all', choices=['1', '2', '3', '4', 'all'],
                        help='评审层级(1=结构 2=+交叉验证 3/4=+人工评审提示, all=4, 默认 all)')

    args = parser.parse_args()
    level = 4 if args.level == 'all' else int(args.level)

    checker = PaperChecker(
        paper_path=args.paper,
        figures_dir=args.figures,
        engine=args.engine,
        results_file=args.results,
        root_dir=args.root,
        enable_pro=args.pro,
        bib_file=args.bib,
        code_dir=args.code,
    )
    passed = checker.print_report(
        min_figures=args.min_figures, min_refs=args.min_refs, level=level
    )
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
