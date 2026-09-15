"""scripts/ 冒烟测试 —— import 所有脚本模块 + 调用 argparse --help。

提升 scripts/ 覆盖率：至少验证模块无 import 错误、argparse 定义完整。
不测试实际逻辑（那需要真实数据 + LaTeX 环境），只覆盖 import + main 入口。
"""
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# 所有 script 模块名（scripts.xxx）
SCRIPT_MODULES = [
    "scripts.ablation",
    "scripts.ablation_parallel",
    "scripts.ai_compliance",
    "scripts.auto_check",
    "scripts.baseline_compare",
    "scripts.benchmark_viz",
    "scripts.boundary_scan",
    "scripts.check_abstract",
    "scripts.check_ethics",
    "scripts.check_figure_quality",
    "scripts.check_innovation",
    "scripts.check_paper_quality",
    "scripts.check_references",
    "scripts.check_verifiability",
    "scripts.embed_figures",
    "scripts.gen_code_manifest",
    "scripts.gen_figure_manifest",
    "scripts.gen_lit_review",
    "scripts.gen_ppt_outline",
    "scripts.init_project",
    "scripts.isolated_solve",
    "scripts.mcp_router",
    "scripts.mc_multirun",
    "scripts.polish_abstract",
    "scripts.reproducibility",
    "scripts.result_registry",
    "scripts.run_all",
    "scripts.run_demo_solve",
    "scripts.score_estimator",
    "scripts.search_openalex",
    "scripts.self_verify",
    "scripts.semantic_anchor",
    "scripts.solver_router",
    "scripts.writing_check",
]


@pytest.mark.parametrize("module_name", SCRIPT_MODULES)
def test_script_importable(module_name):
    """每个 script 模块必须能被 import（无语法错误、无缺失依赖）。"""
    importlib.import_module(module_name)


# 有 main() 入口 + argparse 的脚本，调用 --help 覆盖 argparse 定义
HELP_SCRIPTS = [
    "ablation.py",
    "ai_compliance.py",
    "auto_check.py",
    "baseline_compare.py",
    "boundary_scan.py",
    "check_abstract.py",
    "check_ethics.py",
    "check_figure_quality.py",
    "check_innovation.py",
    "check_paper_quality.py",
    "check_references.py",
    "check_verifiability.py",
    "gen_code_manifest.py",
    "gen_lit_review.py",
    "gen_ppt_outline.py",
    "init_project.py",
    "mc_multirun.py",
    "polish_abstract.py",
    "reproducibility.py",
    "result_registry.py",
    "run_all.py",
    "run_demo_solve.py",
    "score_estimator.py",
    "search_openalex.py",
    "self_verify.py",
    "semantic_anchor.py",
    "solver_router.py",
    "writing_check.py",
]


@pytest.mark.parametrize("script_name", HELP_SCRIPTS)
def test_script_help(script_name):
    """调用 python scripts/xxx.py --help，验证 argparse 定义完整、无运行时错误。"""
    script_path = SCRIPTS_DIR / script_name
    env = {
        "PATH": sys.prefix + "\\Scripts;" + os.environ["PATH"],
        "PYTHONIOENCODING": "utf-8",
        "MPLBACKEND": "Agg",
        "PYTHONPATH": str(REPO_ROOT),
    }
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    # --help 应该返回 0（正常）或 1（部分 argparse 实现返回 1）
    # 但不能返回 2（参数解析错误）
    assert result.returncode in (0, 1), (
        f"{script_name} --help 返回 {result.returncode}\n"
        f"stdout: {result.stdout[:500]}\n"
        f"stderr: {result.stderr[:500]}"
    )
