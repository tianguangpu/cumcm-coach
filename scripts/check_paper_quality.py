#!/usr/bin/env python3
"""
论文质量自检脚本 v1.0
=====================
基于国一论文特征，自动检查论文是否符合国一标准。

使用方式：
    python scripts/check_paper_quality.py --paper paper/main.tex
    python scripts/check_paper_quality.py --paper paper/main.tex --strict
"""

import argparse
import os
import re
from pathlib import Path


class PaperQualityChecker:
    """论文质量检查器（支持 LaTeX + Typst 双引擎）"""

    def __init__(self, paper_path: str, strict: bool = False):
        self.paper_path = paper_path
        self.strict = strict
        self.content = ""
        self.results = {}
        self.issues = []
        self.engine = self._detect_engine()

        with open(paper_path, encoding='utf-8') as f:
            self.content = f.read()

    def _detect_engine(self) -> str:
        """检测排版引擎：LaTeX 或 Typst"""
        if self.paper_path.endswith('.typ'):
            return 'typst'
        return 'latex'

    def check_all(self) -> dict:
        """执行所有检查"""
        print("=" * 60)
        print(f"论文质量自检（国一标准）— {self.engine.upper()} 引擎")
        print("=" * 60)

        self.results['abstract'] = self.check_abstract()
        self.results['model_structure'] = self.check_model_structure()
        self.results['formulas'] = self.check_formulas()
        self.results['figures'] = self.check_figures()
        self.results['verification'] = self.check_verification()
        self.results['references'] = self.check_references()

        # 计算总分
        total_score = sum(r['score'] for r in self.results.values())
        max_score = sum(r['max_score'] for r in self.results.values())

        self.results['total'] = {
            'score': total_score,
            'max_score': max_score,
            'percentage': total_score / max_score * 100 if max_score > 0 else 0,
            'grade': self._calculate_grade(total_score / max_score * 100)
        }

        return self.results

    def _calculate_grade(self, percentage: float) -> str:
        if percentage >= 90:
            return 'A（国一水平）'
        elif percentage >= 80:
            return 'B（国二水平）'
        elif percentage >= 70:
            return 'C（省一水平）'
        else:
            return 'D（需改进）'

    def check_abstract(self) -> dict:
        """检查摘要质量（支持 LaTeX + Typst）"""
        print("\n[1/6] 检查摘要质量...")

        score = 0
        max_score = 20
        issues = []

        # 提取摘要内容（按引擎分叉）
        abstract = ""
        if self.engine == 'typst':
            # Typst: = 摘要 或 = Abstract 之后的段落
            abstract_match = re.search(
                r'^=\s*(?:摘要|Abstract)\s*\n(.*?)(?=\n=\s|\n#bibliography|$)',
                self.content, re.DOTALL | re.MULTILINE
            )
            if abstract_match:
                abstract = abstract_match.group(1).strip()
        else:
            # LaTeX: \begin{abstract}...\end{abstract}
            abstract_match = re.search(
                r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
                self.content, re.DOTALL
            )
            if abstract_match:
                abstract = abstract_match.group(1)

        if not abstract:
            issues.append("[FAIL] 未找到摘要环境")
            return {'score': 0, 'max_score': max_score, 'issues': issues}

        # 检查1：是否有量化结果
        numbers = re.findall(r'\d+\.?\d*', abstract)
        if len(numbers) >= 3:
            score += 5
            print("  [OK] 摘要包含量化结果")
        else:
            issues.append("[WARN] 摘要缺少量化结果（建议包含R²/误差/改进幅度）")

        # 检查2：是否有方法名称
        method_keywords = ['模型', '算法', '方法', '分析', '优化', '预测']
        has_method = any(kw in abstract for kw in method_keywords)
        if has_method:
            score += 5
            print("  [OK] 摘要包含方法名称")
        else:
            issues.append("[WARN] 摘要缺少方法名称")

        # 检查3：是否有关键词
        if self.engine == 'typst':
            keywords_match = re.search(
                r'关键词[：:](.*?)(?:\n|$)|#keywords\[(.*?)\]',
                self.content
            )
        else:
            keywords_match = re.search(
                r'\\keyword\{(.*?)\}|关键词[：:](.*?)(?:\n|$)',
                self.content
            )
        if keywords_match:
            keywords = keywords_match.group(1) or keywords_match.group(2)
            kw_count = len(re.findall(r'[，,；;]', keywords)) + 1
            if 3 <= kw_count <= 5:
                score += 5
                print(f"  [OK] 关键词数量合适（{kw_count}个）")
            else:
                issues.append(f"[WARN] 关键词数量不合适（{kw_count}个，建议3-5个）")
        else:
            issues.append("[FAIL] 未找到关键词")

        # 检查4：摘要长度
        abstract_len = len(abstract)
        if 300 <= abstract_len <= 600:
            score += 5
            print(f"  [OK] 摘要长度合适（{abstract_len}字）")
        else:
            issues.append(f"[WARN] 摘要长度不合适（{abstract_len}字，建议300-600字）")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def check_model_structure(self) -> dict:
        """检查模型结构"""
        print("\n[2/6] 检查模型结构...")

        score = 0
        max_score = 20
        issues = []

        # 检查1：是否有递进链路
        progression_keywords = [
            ('基础', '基础模型'),
            ('缺陷', '缺陷分析'),
            ('改进', '改进创新'),
            ('创新', '创新点')
        ]

        found_progression = []
        for kw, name in progression_keywords:
            if kw in self.content:
                found_progression.append(name)

        if len(found_progression) >= 3:
            score += 10
            print(f"  [OK] 递进链路完整（{', '.join(found_progression)}）")
        else:
            issues.append(f"[WARN] 递进链路不完整（仅找到：{', '.join(found_progression)}）")

        # 检查2：是否有问题分析
        analysis_keywords = ['问题分析', '问题重述', '问题背景']
        has_analysis = any(kw in self.content for kw in analysis_keywords)
        if has_analysis:
            score += 5
            print("  [OK] 包含问题分析")
        else:
            issues.append("[WARN] 缺少问题分析章节")

        # 检查3：是否有假设说明
        assumption_keywords = ['模型假设', '基本假设', '假设条件']
        has_assumption = any(kw in self.content for kw in assumption_keywords)
        if has_assumption:
            score += 5
            print("  [OK] 包含假设说明")
        else:
            issues.append("[WARN] 缺少假设说明")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def check_formulas(self) -> dict:
        """检查公式规范（支持 LaTeX + Typst）"""
        print("\n[3/6] 检查公式规范...")

        score = 0
        max_score = 15
        issues = []

        if self.engine == 'typst':
            # Typst: 统计 display math $ ... $（独占一行的公式）
            equations = re.findall(r'^\s*\$\s*[^$].*?\$\s*(?:<eq_\w+>)?\s*$', self.content, re.MULTILINE)
            labels = re.findall(r'<(eq_\w+)>', self.content)
            refs = re.findall(r'@eq_\w+', self.content)
        else:
            # LaTeX
            equations = re.findall(r'\\begin\{equation\}|\\begin\{align\}|\\begin\{eqnarray\}', self.content)
            labels = re.findall(r'\\label\{eq:.*?\}', self.content)
            refs = re.findall(r'\\ref\{eq:.*?\}|\\eqref\{eq:.*?\}', self.content)

        if len(equations) >= 5:
            score += 5
            print(f"  [OK] 公式数量充足（{len(equations)}个独立公式）")
        else:
            issues.append(f"[WARN] 公式数量不足（{len(equations)}个，建议≥5个）")

        if len(labels) >= 3:
            score += 5
            print(f"  [OK] 公式编号规范（{len(labels)}个标签）")
        else:
            issues.append("[WARN] 公式编号不规范（Typst用<eq_xxx>，LaTeX用\\label{eq:xxx}）")

        if len(refs) >= 2:
            score += 5
            print(f"  [OK] 公式有引用（{len(refs)}处引用）")
        else:
            issues.append("[WARN] 公式缺少引用（建议在正文中引用公式）")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def check_figures(self) -> dict:
        """检查图表规范（支持 LaTeX + Typst）"""
        print("\n[4/6] 检查图表规范...")

        score = 0
        max_score = 15
        issues = []

        if self.engine == 'typst':
            # Typst: #figure(...) 和 #table(...)
            figures = re.findall(r'#figure\(', self.content)
            tables = re.findall(r'#table\(', self.content)
            captions = re.findall(r'caption:\s*\[(.*?)\]', self.content)
            fig_refs = re.findall(r'@fig_\w+|@tbl_\w+|图\d+|表\d+', self.content)
        else:
            # LaTeX
            figures = re.findall(r'\\begin\{figure\}', self.content)
            tables = re.findall(r'\\begin\{table\}', self.content)
            captions = re.findall(r'\\caption\{(.*?)\}', self.content)
            fig_refs = re.findall(r'\\ref\{fig:.*?\}|图\d+|表\d+', self.content)

        total_figures = len(figures) + len(tables)

        if total_figures >= 8:
            score += 5
            print(f"  [OK] 图表数量充足（{len(figures)}图 + {len(tables)}表）")
        else:
            issues.append(f"[WARN] 图表数量不足（{total_figures}个，建议≥8个）")

        if len(captions) >= 5:
            score += 5
            print(f"  [OK] 图表有标题（{len(captions)}个）")
        else:
            issues.append("[WARN] 图表缺少标题")

        if len(fig_refs) >= 5:
            score += 5
            print(f"  [OK] 图表有引用（{len(fig_refs)}处）")
        else:
            issues.append("[WARN] 图表缺少引用")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def check_verification(self) -> dict:
        """检查四重检验"""
        print("\n[5/6] 检查四重检验...")

        score = 0
        max_score = 20
        issues = []

        # 检查1：拟合精度
        fit_keywords = ['R²', 'R2', 'MAE', 'RMSE', 'MAPE', '拟合精度', '误差分析']
        has_fit = any(kw in self.content for kw in fit_keywords)
        if has_fit:
            score += 5
            print("  [OK] 包含拟合精度检验")
        else:
            issues.append("[FAIL] 缺少拟合精度检验（R²/MAE/RMSE）")

        # 检查2：灵敏度分析
        sensitivity_keywords = ['灵敏度', '敏感性', 'Sobol', 'OAT', '参数影响']
        has_sensitivity = any(kw in self.content for kw in sensitivity_keywords)
        if has_sensitivity:
            score += 5
            print("  [OK] 包含灵敏度分析")
        else:
            issues.append("[FAIL] 缺少灵敏度分析")

        # 检查3：蒙特卡洛
        mc_keywords = ['蒙特卡洛', 'Monte Carlo', '随机模拟', 'Bootstrap']
        has_mc = any(kw in self.content for kw in mc_keywords)
        if has_mc:
            score += 5
            print("  [OK] 包含蒙特卡洛验证")
        else:
            issues.append("[FAIL] 缺少蒙特卡洛验证")

        # 检查4：假设误差
        assumption_keywords = ['假设误差', '假设检验', '假设合理性', '误差来源']
        has_assumption_error = any(kw in self.content for kw in assumption_keywords)
        if has_assumption_error:
            score += 5
            print("  [OK] 包含假设误差分析")
        else:
            issues.append("[FAIL] 缺少假设误差分析")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def check_references(self) -> dict:
        """检查参考文献（支持 LaTeX + Typst）"""
        print("\n[6/6] 检查参考文献...")

        score = 0
        max_score = 10
        issues = []

        refs = []
        if self.engine == 'typst':
            # Typst: #bibliography("refs.yml") — 无法直接解析 .yml 内容
            # 检查是否使用 bibliography 函数
            has_bib = bool(re.search(r'#bibliography\(', self.content))
            if has_bib:
                # 尝试从同目录 .yml/.bib 文件读取
                import yaml
                bib_dir = Path(self.paper_path).parent
                for bib_file in bib_dir.glob("*.yml"):
                    try:
                        with open(bib_file, encoding='utf-8') as f:
                            bib_data = yaml.safe_load(f)
                        if isinstance(bib_data, dict):
                            refs = list(bib_data.values())
                    except Exception:
                        pass
                for bib_file in bib_dir.glob("*.bib"):
                    try:
                        with open(bib_file, encoding='utf-8') as f:
                            bib_content = f.read()
                        refs = re.findall(r'@\w+\{(.*?)(?=@\w+|\Z)', bib_content, re.DOTALL)
                    except Exception:
                        pass
        else:
            # LaTeX: thebibliography 或 .bib 文件
            bib_match = re.search(
                r'\\begin\{thebibliography\}(.*?)\\end\{thebibliography\}',
                self.content, re.DOTALL
            )
            if bib_match:
                bib_content = bib_match.group(1)
                refs = re.findall(r'\\bibitem\{.*?\}(.*?)(?=\\bibitem|$)', bib_content, re.DOTALL)

        ref_count = len(refs) if refs else 0

        # 检查1：参考文献数量
        if ref_count >= 10:
            score += 3
            print(f"  [OK] 参考文献数量充足（{ref_count}篇）")
        else:
            issues.append(f"[WARN] 参考文献数量不足（{ref_count}篇，建议≥10篇）")

        # 检查2：近5年文献
        recent_refs = [r for r in refs if any(str(y) in r for y in ['2024', '2023', '2022', '2021', '2020'])]
        if len(recent_refs) >= ref_count * 0.5:
            score += 4
            print(f"  [OK] 近5年文献比例合适（{len(recent_refs)}/{ref_count}）")
        else:
            issues.append(f"[WARN] 近5年文献比例不足（{len(recent_refs)}/{ref_count}）")

        # 检查3：外文文献
        english_refs = [r for r in refs if re.search(r'[A-Za-z]{5,}', r)]
        if len(english_refs) >= ref_count * 0.3:
            score += 3
            print(f"  [OK] 外文文献比例合适（{len(english_refs)}/{ref_count}）")
        else:
            issues.append(f"[WARN] 外文文献比例不足（{len(english_refs)}/{ref_count}）")

        return {'score': score, 'max_score': max_score, 'issues': issues}

    def generate_report(self, output_path: str = None) -> str:
        """生成检查报告"""
        report = []
        report.append("# 论文质量自检报告（国一标准）\n")
        report.append(f"> 论文：{self.paper_path}")
        report.append(f"> 总分：{self.results['total']['score']}/{self.results['total']['max_score']}")
        report.append(f"> 等级：{self.results['total']['grade']}\n")

        # 各维度得分
        report.append("## 各维度得分\n")
        report.append("| 维度 | 得分 | 满分 | 状态 |")
        report.append("|------|------|------|------|")

        for name, result in self.results.items():
            if name == 'total':
                continue

            status = "[OK]" if result['score'] >= result['max_score'] * 0.8 else "[WARN]"
            report.append(f"| {name} | {result['score']} | {result['max_score']} | {status} |")

        # 问题清单
        report.append("\n## 问题清单\n")
        for name, result in self.results.items():
            if name == 'total':
                continue
            if result.get('issues'):
                report.append(f"### {name}")
                for issue in result['issues']:
                    report.append(f"- {issue}")
                report.append("")

        report_text = "\n".join(report)

        # 保存报告
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n[REPORT] 报告已保存: {output_path}")

        return report_text


def main():
    parser = argparse.ArgumentParser(
        description='论文质量自检（国一标准）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--paper', required=True, help='论文文件路径（.tex 或 .typ）')
    parser.add_argument('--strict', action='store_true', help='严格模式')
    parser.add_argument('--output', default='reports/paper_quality.md', help='输出报告路径')

    args = parser.parse_args()

    # 创建检查器
    checker = PaperQualityChecker(args.paper, strict=args.strict)

    # 执行检查
    results = checker.check_all()

    # 打印结果
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    for name, result in results.items():
        if name == 'total':
            continue
        status = "[OK]" if result['score'] >= result['max_score'] * 0.8 else "[WARN]"
        print(f"{status} {name}: {result['score']}/{result['max_score']}")

    print("\n" + "=" * 60)
    print(f"总分: {results['total']['score']}/{results['total']['max_score']}")
    print(f"等级: {results['total']['grade']}")
    print("=" * 60)

    # 生成报告
    checker.generate_report(args.output)

    # 返回退出码
    if results['total']['percentage'] >= 80:
        return 0
    elif results['total']['percentage'] >= 60:
        return 1
    else:
        return 2


if __name__ == '__main__':
    main()
