# -*- coding: utf-8 -*-
"""
reproducibility.py — 一键复现 + 哈希绑定
==========================================
国一标准：求解步骤须可复现，代码版本 vs 结果文件哈希绑定。

用法:
    python reproducibility.py --init                  # 初始化复现清单
    python reproducibility.py --verify                # 验证复现性
    python reproducibility.py --hash                  # 生成哈希绑定
    python reproducibility.py --makefile              # 生成Makefile
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def file_hash(path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希。"""
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def scan_project(project_dir: str = ".") -> dict:
    """扫描项目关键文件，生成哈希清单。"""
    root = Path(project_dir)
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "seed": 42,
        "files": {},
        "results": {},
        "scripts": {},
    }

    # 扫描代码文件
    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in str(py_file) or ".pyc" in str(py_file):
            continue
        rel = str(py_file.relative_to(root))
        manifest["scripts"][rel] = file_hash(str(py_file))

    # 扫描结果文件
    results_dir = root / "results"
    if results_dir.exists():
        for f in sorted(results_dir.glob("*")):
            if f.is_file():
                rel = str(f.relative_to(root))
                manifest["results"][rel] = {
                    "hash": file_hash(str(f)),
                    "size": f.stat().st_size,
                }

    # 扫描论文文件
    paper_dir = root / "paper"
    if paper_dir.exists():
        for f in sorted(paper_dir.rglob("*.tex")):
            rel = str(f.relative_to(root))
            manifest["files"][rel] = file_hash(str(f))

    return manifest


def generate_makefile(project_dir: str = ".") -> str:
    """生成Makefile一键复现。"""
    makefile = """# 国赛论文一键复现 Makefile
# 用法: make all (全链) / make verify (验证) / make clean (清理)

PYTHON = python
SEED = 42

.PHONY: all solve plot paper verify clean

all: solve plot paper verify
\t@echo "=== 全链完成 ==="

solve:
\t@echo "[1/4] 建模与求解..."
\t$(PYTHON) code/run_all.py --seed $(SEED)

plot:
\t@echo "[2/4] 图表生成..."
\t$(PYTHON) scripts/gen_figure_manifest.py figures state/figure_manifest.json

paper:
\t@echo "[3/4] 论文编译..."
\txelatex paper/main.tex
\txelatex paper/main.tex

verify:
\t@echo "[4/4] 复现验证..."
\t$(PYTHON) scripts/reproducibility.py --verify

clean:
\trm -f paper/*.aux paper/*.log paper/*.out paper/*.toc
\trm -rf __pycache__

hash:
\t$(PYTHON) scripts/reproducibility.py --hash
"""
    makefile_path = Path(project_dir) / "Makefile"
    makefile_path.write_text(makefile, encoding="utf-8")
    print(f"[复现] Makefile已生成: {makefile_path}")
    return str(makefile_path)


def generate_requirements(project_dir: str = ".") -> str:
    """生成requirements.txt。"""
    reqs = """# 国赛论文复现依赖
numpy>=1.21.0
scipy>=1.7.0
pandas>=1.3.0
matplotlib>=3.4.0
"""
    req_path = Path(project_dir) / "requirements.txt"
    req_path.write_text(reqs, encoding="utf-8")
    print(f"[复现] requirements.txt已生成: {req_path}")
    return str(req_path)


def verify_reproducibility(project_dir: str = ".") -> dict:
    """验证复现性：检查关键文件是否存在且哈希一致。"""
    root = Path(project_dir)
    manifest_path = root / "state" / "reproducibility_manifest.json"

    if not manifest_path.exists():
        return {"status": "no_manifest", "issues": ["复现清单不存在，运行 --init 初始化"]}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    issues = []

    # 验证结果文件
    for rel, info in manifest.get("results", {}).items():
        fpath = root / rel
        if not fpath.exists():
            issues.append(f"结果文件缺失: {rel}")
        else:
            current_hash = file_hash(str(fpath))
            if current_hash != info.get("hash"):
                issues.append(f"结果文件已修改: {rel} (期望={info['hash']}, 实际={current_hash})")

    # 验证代码文件
    for rel, expected_hash in manifest.get("scripts", {}).items():
        fpath = root / rel
        if not fpath.exists():
            issues.append(f"代码文件缺失: {rel}")
        else:
            current_hash = file_hash(str(fpath))
            if current_hash != expected_hash:
                issues.append(f"代码已修改: {rel} (需重新运行solve)")

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "total_files": len(manifest.get("results", {})) + len(manifest.get("scripts", {})),
    }


def main():
    p = argparse.ArgumentParser(description="一键复现+哈希绑定")
    p.add_argument("--init", action="store_true", help="初始化复现清单")
    p.add_argument("--verify", action="store_true", help="验证复现性")
    p.add_argument("--hash", action="store_true", help="生成哈希清单")
    p.add_argument("--makefile", action="store_true", help="生成Makefile")
    p.add_argument("--dir", default=".", help="项目目录")
    a = p.parse_args()

    if a.init:
        # 初始化全套
        generate_requirements(a.dir)
        generate_makefile(a.dir)
        manifest = scan_project(a.dir)
        manifest_path = Path(a.dir) / "state" / "reproducibility_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[复现] 复现清单已生成: {manifest_path}")
        print(f"[复现] 共扫描 {len(manifest['scripts'])} 个脚本, {len(manifest['results'])} 个结果文件")
    elif a.verify:
        result = verify_reproducibility(a.dir)
        print(f"状态: {result['status']}")
        print(f"检查文件: {result['total_files']}个")
        if result["issues"]:
            print(f"问题:")
            for issue in result["issues"]:
                print(f"  - {issue}")
    elif a.hash:
        manifest = scan_project(a.dir)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    elif a.makefile:
        generate_makefile(a.dir)
    else:
        p.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
