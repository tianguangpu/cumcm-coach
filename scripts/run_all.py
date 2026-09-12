"""
run_all.py — 国赛全链流水线
============================
一键执行完整建模流程，支持断点续跑。

用法:
    python run_all.py                           # 全链运行
    python run_all.py --from 07                 # 从第7步断点续跑
    python run_all.py --to 03                   # 只跑到第3步
    python run_all.py --fast                    # 快速模式（跳过耗时步骤）
    python run_all.py --dry                     # 干跑（只打印步骤，不执行）

步骤:
    01. 初始化项目目录
    02. AI合规日志初始化
    02a. 问题分析确认(歧义/隐含约束/依赖图 — problem_analyzer.py)
    03. 数据预处理
    03b. 创新方向+强基线规划(innovation_guide.py → 用户选择写入 plan.md)
    04. 建模与求解(含 Sobol 全局灵敏度 + assumption_error 假设误差 + pso_variants 高级算法)
    05. 消融对比实验
    06. 图表生成
    07. 图表质量验证
    08. 结果报告生成
    08c. 文献综述生成(按 --type 题型)
    08b. 真实LaTeX论文直出(读 summary.json + figures/png → latex/paper.tex, 一键编译脚本；自动嵌入 08c 综述)
    09. 论文组装
    10. L1-L4 四级评审
    11. AI合规材料生成
    12. 答辩PPT大纲
    13. 终检打包
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── 步骤定义 ──────────────────────────────────────────────────────────

STEPS = [
    {
        "id": "01",
        "name": "初始化项目目录",
        "cmd": "{py} scripts/init_project.py --team {team} --members {members}",
        "skip_if": "plan.md",
        "fast_skip": False,
    },
    {
        "id": "02",
        "name": "AI合规日志初始化",
        "cmd": "{py} scripts/ai_compliance.py init --tools \"Claude Code\"",
        "skip_if": "state/ai_interaction_log.json",
        "fast_skip": False,
    },
    {
        "id": "02a",
        "name": "问题分析确认(歧义/隐含约束/依赖)",
        "cmd": "{py} algorithms/misc/problem_analyzer.py",
        "skip_if": "results/problem_analysis.md",
        "fast_skip": True,
    },
    {
        "id": "03",
        "name": "数据预处理",
        "cmd": None,  # 手动步骤
        "skip_if": "data/",
        "fast_skip": True,
        "manual": "检查 data/ 目录是否有清洗后的数据文件",
    },
    {
        "id": "03b",
        "name": "创新方向+强基线规划",
        "cmd": "{py} algorithms/misc/innovation_guide.py {ptype} reports/innovation_plan.json",
        "skip_if": "reports/innovation_plan.json",
        "fast_skip": True,
    },
    {
        "id": "04",
        "name": "建模与求解",
        "cmd": None,  # Agent执行
        "skip_if": "results/",
        "fast_skip": True,
        "manual": "执行 code/ 下的求解脚本，生成 results/*.json",
    },
    {
        "id": "04b",
        "name": "高级检验数据生成(Sobol+假设误差+Clerc-PSO)",
        "cmd": "{py} gen_validation_results.py --only validation",
        "skip_if": "results/validation_results.json",
        "fast_skip": True,
    },
    {
        "id": "05",
        "name": "消融对比实验",
        "cmd": "{py} scripts/ablation.py validate --path results/ablation.csv",
        "skip_if": "results/ablation.csv",
        "fast_skip": True,
    },
    {
        "id": "06",
        "name": "图表生成",
        "cmd": None,
        "skip_if": "figures/png/",
        "fast_skip": True,
        "manual": "运行绘图脚本，生成 figures/png/ 和 figures/pdf/",
    },
    {
        "id": "07",
        "name": "图表质量验证",
        "cmd": "{py} scripts/check_figure_quality.py figures/ --width-cm 16",
        "skip_if": None,
        "fast_skip": True,
        "manual": (
            "已自动执行「尺寸-字号」检查（缩放后实际字号 <8pt 即拦截）。"
            "完整视觉自检闭环另见 §3.4：check_figure.py --strict 机器审计"
            "（DPI/画布尺寸）+ check_overlaps.py --fix 重叠修复 + "
            "image-reader 读图复核 + 回改重渲"
        ),
    },
    {
        "id": "08",
        "name": "结果报告生成",
        "cmd": "{py} scripts/gen_figure_manifest.py figures state/figure_manifest.json",
        "skip_if": "state/figure_manifest.json",
        "fast_skip": False,
    },
    {
        "id": "08c",
        "name": "文献综述生成",
        "cmd": "{py} scripts/gen_lit_review.py --type {ptype} --out reports/lit_review.tex",
        "skip_if": "reports/lit_review.tex",
        "fast_skip": True,
    },
    {
        "id": "08b",
        "name": "论文模板准备",
        "cmd": "echo 论文模板已就绪: 使用 templates/ 下的 LaTeX/Typst 模板手动组装论文",
        "skip_if": "paper/main.tex",
        "fast_skip": True,
    },
    {
        "id": "09",
        "name": "论文组装",
        "cmd": "{py} scripts/embed_figures.py paper/sections state/figure_manifest.json {engine}",
        "skip_if": "paper/main.tex",
        "fast_skip": True,
    },
    {
        "id": "10",
        "name": "L1-L4 四级评审",
        "cmd": "{py} scripts/auto_check.py --paper latex/paper.tex --figures figures/png/ --engine {engine} --level all --pro --bib latex/refs.bib",
        "skip_if": None,
        "fast_skip": True,
    },
    {
        "id": "10b",
        "name": "参考文献审查",
        "cmd": "{py} scripts/check_references.py --tex paper/sections/ --output reports/reference_report.md",
        "skip_if": "reports/reference_report.md",
        "fast_skip": True,
    },
    {
        "id": "11",
        "name": "AI合规材料生成",
        "cmd": "{py} scripts/ai_compliance.py all",
        "skip_if": "output/ai_declaration.tex",
        "fast_skip": False,
    },
    {
        "id": "12",
        "name": "答辩PPT大纲",
        "cmd": "{py} scripts/gen_ppt_outline.py --tex paper/main.tex --results results/ --output output/ppt_outline.md --type {ptype}",
        "skip_if": "output/ppt_outline.md",
        "fast_skip": False,
    },
    {
        "id": "13",
        "name": "终检打包",
        "cmd": None,
        "skip_if": None,
        "fast_skip": True,
        "manual": "检查 output/ 目录，确认所有材料齐全",
    },
]


def run_step(step: dict, project_dir: str, engine: str, team: str, members: str, ptype: str = "B", dry: bool = False) -> bool:
    """执行单个步骤。返回True表示成功或跳过。"""
    root = Path(project_dir)
    step_id = step["id"]
    step_name = step["name"]

    # 检查是否跳过
    skip_if = step.get("skip_if")
    if skip_if and (root / skip_if).exists():
        print(f"  [{step_id}] {step_name}: ✓ 已存在，跳过")
        return True

    # 命令优先：有 cmd 就执行；manual 仅在没有 cmd 时表示纯手动步骤。
    # 此前 manual 会无条件短路 return，导致「同时带 cmd 与 manual」的步骤
    # 永远不会真正执行（图表质量验证步骤曾因此形同虚设）。
    cmd = step.get("cmd")
    if not cmd:
        if step.get("manual"):
            print(f"  [{step_id}] {step_name}: ⚠ 手动步骤 - {step['manual']}")
        else:
            print(f"  [{step_id}] {step_name}: ⚠ 无自动命令，需手动执行")
        return True

    # 格式化命令(用当前解释器 sys.executable 替代 python,规避别名缺失)
    py = f'"{sys.executable}"'
    cmd = cmd.format(engine=engine, team=team, members=members, ptype=ptype, py=py)

    if dry:
        print(f"  [{step_id}] {step_name}: [DRY] {cmd}")
        return True

    # 执行
    print(f"  [{step_id}] {step_name}: 执行中...")
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=project_dir,
            capture_output=True, text=True, timeout=300,
            encoding="utf-8", errors="replace"
        )
        elapsed = time.time() - t0
        if result.returncode == 0:
            print(f"  [{step_id}] {step_name}: ✓ 完成 ({elapsed:.1f}s)")
            return True
        else:
            print(f"  [{step_id}] {step_name}: ✗ 失败 ({elapsed:.1f}s)")
            if result.stderr:
                print(f"    错误: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  [{step_id}] {step_name}: ✗ 超时(300s)")
        return False
    except Exception as e:
        print(f"  [{step_id}] {step_name}: ✗ 异常: {e}")
        return False


def run_pipeline(
    project_dir: str = ".",
    from_step: str = "01",
    to_step: str = "99",
    fast: bool = False,
    dry: bool = False,
    engine: str = "latex",
    team: str = "",
    members: str = "",
    ptype: str = "B",
):
    """运行全链流水线。"""
    print("=" * 55)
    print("  国赛全链流水线 v7.10.0")
    print("=" * 55)
    print(f"  项目目录: {Path(project_dir).resolve()}")
    print(f"  步骤范围: {from_step} → {to_step}")
    print(f"  快速模式: {'是' if fast else '否'}")
    print(f"  干跑模式: {'是' if dry else '否'}")
    print(f"  排版引擎: {engine}")
    print("=" * 55)
    if not team or not members:
        print("⚠ 未提供 --team / --members,步骤 01 将生成空队伍信息。")
        print("  建议: python run_all.py --team 队伍编号 --members \"张三,李四,王五\"")
    print()

    t0 = time.time()
    passed = 0
    failed = 0
    skipped = 0

    for step in STEPS:
        step_id = step["id"]

        # 范围过滤
        if step_id < from_step:
            continue
        if step_id > to_step:
            break

        # 快速模式跳过
        if fast and step.get("fast_skip"):
            print(f"  [{step_id}] {step['name']:20s} ⏭ 快速模式跳过")
            skipped += 1
            continue

        ok = run_step(step, project_dir, engine, team, members, ptype, dry)
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"\n  ⚠ 步骤 {step_id} 失败，流水线中断")
            break

    elapsed = time.time() - t0
    print()
    print("=" * 55)
    print(f"  完成! 通过={passed} 失败={failed} 跳过={skipped} 耗时={elapsed:.1f}s")
    print("=" * 55)

    # 更新 decision_log
    log_path = Path(project_dir) / "state" / "decision_log.json"
    if log_path.exists() and not dry:
        with open(log_path, encoding="utf-8") as f:
            log = json.load(f)
        log["last_pipeline_run"] = {
            "timestamp": datetime.now().isoformat(),
            "from_step": from_step,
            "to_step": to_step,
            "passed": passed,
            "failed": failed,
            "elapsed_s": round(elapsed, 1),
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    return failed == 0


def main():
    p = argparse.ArgumentParser(description="国赛全链流水线")
    p.add_argument("--from", dest="from_step", default="01", help="从第N步开始(01-13)")
    p.add_argument("--to", default="99", help="到第N步结束(01-13)")
    p.add_argument("--fast", action="store_true", help="快速模式（跳过耗时步骤）")
    p.add_argument("--dry", action="store_true", help="干跑（只打印，不执行）")
    p.add_argument("--dir", default=".", help="项目目录")
    p.add_argument("--engine", default="latex", choices=["latex", "typst"])
    p.add_argument("--team", default="", help="队伍编号")
    p.add_argument("--members", default="", help="队员姓名")
    p.add_argument("--type", dest="ptype", default="B", choices=["A", "B", "C", "D"], help="题目题型(用于文献综述/模板路由)")
    a = p.parse_args()

    ok = run_pipeline(a.dir, a.from_step, a.to, a.fast, a.dry, a.engine, a.team, a.members, a.ptype)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
