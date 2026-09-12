# -*- coding: utf-8 -*-
"""
init_project.py — 国赛项目初始化
=================================
一键创建标准目录结构 + state/decision_log.json + plan.md + todo.md。

用法:
    python init_project.py --team "202600001" --members "张三,李四,王五"
    python init_project.py --team "202600001" --type B --engine latex --lang python
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEED = 42


def init_project(
    project_dir: str = ".",
    team_id: str = "",
    members: str = "",
    problem_type: str = "",
    engine: str = "latex",
    lang: str = "python",
    external_dir: str = "",
) -> dict:
    """初始化国赛项目目录结构和状态文件。"""
    root = Path(project_dir)

    # 1. 创建目录结构
    dirs = [
        "code",
        "data",
        "results",
        "figures/png",
        "figures/pdf",
        "paper/sections",
        "paper/references",
        "state",
        "reports",
        "output",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)
    print(f"[初始化] 目录结构已创建: {len(dirs)} 个目录")

    # 2. 创建 decision_log.json
    decision_log = {
        "schema_version": "7.4.0",
        "competition": f"CUMCM-{datetime.now().year}",
        "team": {
            "id": team_id,
            "members": [m.strip() for m in members.split(",") if m.strip()],
        },
        "problem_type": problem_type,
        "engine": engine,
        "lang": lang,
        "created_at": datetime.now().isoformat(),
        "current_stage": 0,
        "anchors": {
            "core_constraints": [],
            "key_assumptions": [],
            "symbol_conventions": {},
            "forbidden_variables": [],
        },
        "per_qi": {},
        "change_log": [],
        "propagation_map": {
            "model_change": ["abstract", "section_5", "section_6", "results_report"],
            "algorithm_change": ["abstract", "section_5_5", "algorithm_table", "ablation"],
            "assumption_change": ["section_3", "section_6_4", "verify_report"],
            "data_change": ["all_results", "all_figures", "abstract"],
        },
        "gate_results": {},
        "model_candidates": {},
    }
    log_path = root / "state" / "decision_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(decision_log, f, ensure_ascii=False, indent=2)
    print(f"[初始化] decision_log.json 已创建: {log_path}")

    # 3. 创建 ai_interaction_log.json (AI合规)
    ai_log = {
        "session_started": None,
        "tools": [],
        "interactions": [],
        "summary": {},
    }
    ai_log_path = root / "state" / "ai_interaction_log.json"
    with open(ai_log_path, "w", encoding="utf-8") as f:
        json.dump(ai_log, f, ensure_ascii=False, indent=2)
    print(f"[初始化] ai_interaction_log.json 已创建")

    # 4. 创建 plan.md
    plan_content = f"""# 方案

## 用户偏好
- 排版引擎: {engine}
- 代码语言: {lang}
- 题型: {problem_type or '（待识别）'}

## 团队信息
- 队伍编号: {team_id}
- 队员: {members}

## Workflow

| 步骤 | 产物 | 状态 |
|------|------|------|
| 1. 建模与求解 | code/ + results/ + ANALYSIS_MODELING_REPORT.md | ⬜ |
| 2. 图表生成 | figures/png/ + figures/pdf/ + RESULTS_REPORT.md | ⬜ |
| 3. 论文撰写 | paper/main.{engine} + sections/ | ⬜ |
| 4. L1-L4 四级评审 | VERIFY_REPORT.md | ⬜ |
| 5. AI合规材料 | output/ai_declaration.tex + AI工具使用详情.pdf | ⬜ |
| 6. 答辩PPT | output/ppt_outline.md | ⬜ |

## 国赛金标准内核（每问强制）
- 六段子结构(5.X.1~5.X.6)
- 公式三段式(前置+本体+后置)
- 四重检验(拟合精度+灵敏度+MC+假设误差)
- 算法对比表(3算法⋆评级)
- 创新点量化(强制百分比)

## 全局约束
- SEED = {SEED}
- 数据来源 URL 必须写入论文
- 所有数值来自 results/，不得编造
- 参考文献 ≥10，近5年 ≥40%，外文 ≥30%
"""
    plan_path = root / "plan.md"
    plan_path.write_text(plan_content, encoding="utf-8")
    print(f"[初始化] plan.md 已创建")

    # 5. 创建 todo.md
    todo_content = """# 待办事项

- [ ] 1. 建模与求解（含 MCP 调用）
- [ ] 2. 图表生成（数据图 + 概念图分工）
- [ ] 3. 论文撰写（套用模板 + 金标准内核）
- [ ] 4. L1-L4 四级评审
- [ ] 5. AI合规材料生成
- [ ] 6. 答辩PPT大纲生成
"""
    todo_path = root / "todo.md"
    todo_path.write_text(todo_content, encoding="utf-8")
    print(f"[初始化] todo.md 已创建")

    # 6. 创建 .gitignore
    gitignore_content = """# Python
__pycache__/
*.pyc
*.pyo

# LaTeX
*.aux
*.log
*.out
*.toc
*.bbl
*.blg
*.synctex.gz

# 数据（大文件不提交）
data/*.xlsx
data/*.csv
data/*.mat

# 输出（可重新生成）
output/

# IDE
.vscode/
.idea/
"""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        print(f"[初始化] .gitignore 已创建")

    # 7. 记录外部算法库路径(解耦硬编码 D:\) 
    if external_dir:
        env_path = root / ".env"
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"CUMCM_EXTERNAL_DIR={external_dir}\n")
        decision_log.setdefault("config", {})["external_dir"] = external_dir
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(decision_log, f, ensure_ascii=False, indent=2)
        print(f"[初始化] 外部算法库路径已写入 .env: {external_dir}")

    print(f"\n[初始化] 完成！项目目录: {root.resolve()}")
    return decision_log


def main():
    p = argparse.ArgumentParser(description="国赛项目初始化")
    p.add_argument("--dir", default=".", help="项目目录")
    p.add_argument("--team", default="", help="队伍编号")
    p.add_argument("--members", default="", help="队员姓名，逗号分隔")
    p.add_argument("--type", default="", choices=["A", "B", "C", "D", ""], help="题型")
    p.add_argument("--engine", default="latex", choices=["latex", "typst"], help="排版引擎")
    p.add_argument("--lang", default="python", choices=["python", "matlab", "both"], help="代码语言")
    p.add_argument("--external-dir", default="", help="外部算法库根目录(写入 .env 的 CUMCM_EXTERNAL_DIR,解耦硬编码路径)")
    a = p.parse_args()

    init_project(a.dir, a.team, a.members, a.type, a.engine, a.lang, a.external_dir)


if __name__ == "__main__":
    main()
