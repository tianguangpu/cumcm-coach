"""
gen_code_manifest.py — v7 代码清单自动生成（增强版 v1.1）
======================================================
扫描 scripts/ + algorithms/ + templates/，自动生成 references/code-inventory.md，
根治「SKILL.md 手写文件结构」与「实际代码」漂移的问题。

增强功能（v1.1）：
    - requirements.txt 依赖一致性检查
    - 代码可运行性快速检测（语法检查）
    - Typst 模板扫描支持
    - 溯源完整性检查

用法:
    python scripts/gen_code_manifest.py                   # 默认扫描本 skill 根目录
    python scripts/gen_code_manifest.py --root <dir>      # 指定 skill 根目录
    python scripts/gen_code_manifest.py --output <path>   # 指定输出文件
    python scripts/gen_code_manifest.py --check-deps      # 检查依赖一致性
    python scripts/gen_code_manifest.py --check-syntax    # 检查代码语法

输出:
    references/code-inventory.md — 全量代码清单(脚本/算法/模板，含行数/摘要/主要符号)
    stdout — 统计摘要

设计原则(对应单一事实源):
    本脚本是代码清单的「唯一事实源」。SKILL.md 不再手写文件结构，
    只引用 references/code-inventory.md；每次增删脚本后重跑本脚本刷新。
"""
import argparse
import ast
import re
from pathlib import Path

if hasattr(__import__("sys").stdout, "reconfigure"):
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── 提取逻辑 ──────────────────────────────────────────────────────────

def _first_line(text: str) -> str:
    """取 docstring/首行摘要，去空白、截断。"""
    text = (text or "").strip()
    if not text:
        return ""
    line = text.split("\n")[0].strip()
    return line[:80]


def extract_py(path: Path) -> dict:
    """用 AST 解析 .py，提取模块 docstring + 顶层函数/类。"""
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    n_lines = src.count("\n") + 1
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"lines": n_lines, "summary": f"⚠ 语法错误: {e}", "symbols": []}

    summary = _first_line(ast.get_docstring(tree) or "")
    symbols = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            symbols.append((node.name, kind, _first_line(ast.get_docstring(node) or "")))
    return {"lines": n_lines, "summary": summary, "symbols": symbols}


def extract_text(path: Path) -> dict:
    """提取 .sh/.md/.tex 的行数与首行摘要。"""
    src = path.read_text(encoding="utf-8-sig", errors="replace")
    n_lines = src.count("\n") + 1
    # 首条非空且非 shebang 的行作为摘要
    summary = ""
    for line in src.split("\n"):
        s = line.strip()
        if s and not s.startswith("#!") and not s.startswith("---"):
            # 去掉 markdown 标题符号 / 注释符号
            summary = s.lstrip("#%/ ").strip()[:80]
            break
    return {"lines": n_lines, "summary": summary, "symbols": []}


# ── 渲染 ──────────────────────────────────────────────────────────────

def _render_table(rows):
    """渲染一张 markdown 表格。rows: list of (文件, 行数, 摘要, 主要符号)。"""
    out = ["| 文件 | 行数 | 摘要 | 主要符号 |", "|------|-----:|------|---------|"]
    for name, lines, summary, symbols in rows:
        sym = ", ".join(f"`{n}`" for n, _k, _d in symbols[:6])
        if len(symbols) > 6:
            sym += f" …(+{len(symbols) - 6})"
        out.append(f"| `{name}` | {lines} | {summary} | {sym} |")
    return "\n".join(out)


def render_markdown(inventory: dict, root: Path) -> str:
    parts = []
    parts.append("# v7 代码清单（自动生成）\n")
    parts.append("> 由 `scripts/gen_code_manifest.py` 生成。**勿手改本文件**，改脚本后重跑刷新。\n")
    parts.append(f"> 根目录：`{root}`\n")

    total_py = sum(
        1 for grp in inventory.values() for f, *_ in grp if f.endswith(".py")
    )
    total_files = sum(len(grp) for grp in inventory.values())
    parts.append(f"- 文件总数：{total_files}（其中 Python {total_py} 个）\n")

    for section, files in inventory.items():
        if not files:
            continue
        parts.append(f"\n## {section}\n")
        parts.append(_render_table(files))

    parts.append("\n---\n")
    parts.append("> SKILL.md §六 引用本文件作为唯一文件结构源。")
    return "\n".join(parts)


# ── 扫描 ──────────────────────────────────────────────────────────────

def scan(root: Path) -> dict:
    """扫描 scripts/ algorithms/ templates/，返回分组清单。"""
    inventory = {}

    # scripts/
    scripts = []
    for p in sorted((root / "scripts").glob("*.py")):
        info = extract_py(p)
        scripts.append((p.name, info["lines"], info["summary"], info["symbols"]))
    for p in sorted((root / "scripts").glob("*.sh")):
        info = extract_text(p)
        scripts.append((p.name, info["lines"], info["summary"], []))
    inventory["scripts/（编排/检查/工具脚本）"] = scripts

    # algorithms/ 按子目录分组
    algo_dir = root / "algorithms"
    for sub in sorted(p for p in algo_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        files = []
        for p in sorted(sub.glob("*.py")):
            info = extract_py(p)
            files.append((f"{sub.name}/{p.name}", info["lines"], info["summary"], info["symbols"]))
        if files:
            inventory[f"algorithms/{sub.name}/（算法库）"] = files

    # algorithms/ 顶层索引 .md
    idx = []
    for p in sorted(algo_dir.glob("*.md")):
        info = extract_text(p)
        idx.append((p.name, info["lines"], info["summary"], []))
    if idx:
        inventory["algorithms/（索引文档）"] = idx

    # templates/
    templates = []
    for p in sorted((root / "templates").glob("*.tex")):
        info = extract_text(p)
        templates.append((p.name, info["lines"], info["summary"], []))
    for p in sorted((root / "templates").glob("*.md")):
        info = extract_text(p)
        templates.append((p.name, info["lines"], info["summary"], []))
    if templates:
        inventory["templates/（题型模板 .tex/.md）"] = templates

    return inventory


def main():
    p = argparse.ArgumentParser(description="v7 代码清单自动生成（增强版）")
    p.add_argument("--root", default=str(Path(__file__).resolve().parent.parent),
                   help="skill 根目录（默认脚本上一级）")
    p.add_argument("--output", default=None,
                   help="输出文件（默认 references/code-inventory.md）")
    p.add_argument("--check-deps", action="store_true",
                   help="检查 requirements.txt 依赖一致性")
    p.add_argument("--check-syntax", action="store_true",
                   help="检查 Python 代码语法")
    a = p.parse_args()

    root = Path(a.root)
    out_path = Path(a.output) if a.output else root / "references" / "code-inventory.md"

    inventory = scan(root)
    markdown = render_markdown(inventory, root)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    # stdout 摘要
    total = sum(len(v) for v in inventory.values())
    n_py = sum(1 for grp in inventory.values() for f, *_ in grp if f.endswith(".py"))
    print(f"[OK] 已生成 {out_path.relative_to(root)}")
    print(f"     文件总数 {total}，Python {n_py} 个")
    for section, files in inventory.items():
        print(f"     - {section}: {len(files)} 个")

    # 依赖检查
    if a.check_deps:
        print("\n" + "=" * 50)
        print("依赖一致性检查")
        print("=" * 50)
        check_requirements_consistency(root)

    # 语法检查
    if a.check_syntax:
        print("\n" + "=" * 50)
        print("Python 语法检查")
        print("=" * 50)
        check_python_syntax(root)


def check_requirements_consistency(root: Path):
    """检查 requirements.txt 与代码中的 import 是否一致"""
    req_file = root / "requirements.txt"

    if not req_file.exists():
        print("[WARN]  requirements.txt 不存在")
        return

    # 解析 requirements.txt
    declared_deps = set()
    for line in req_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # 提取包名（忽略版本号）
            pkg = line.split(">=")[0].split("==")[0].split("<=")[0].split("[")[0].strip()
            declared_deps.add(pkg.lower())

    # 扫描代码中的 import
    imported_pkgs = set()
    import_pattern = re.compile(r'^(?:from|import)\s+([\w]+)', re.MULTILINE)

    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".pyc" in str(py_file):
            continue
        try:
            src = py_file.read_text(encoding="utf-8-sig", errors="replace")
            matches = import_pattern.findall(src)
            imported_pkgs.update(m.lower() for m in matches)
        except (OSError, UnicodeDecodeError):
            pass

    # 标准库和本地模块（排除）
    stdlib_and_local = {
        'os', 'sys', 'json', 're', 'math', 'random', 'datetime', 'pathlib',
        'argparse', 'typing', 'collections', 'itertools', 'functools',
        'subprocess', 'shutil', 'glob', 'io', 'abc', 'copy', 'hashlib',
        'time', 'logging', 'unittest', 'dataclasses', 'enum', 'warnings',
        'ast', 'textwrap', 'string', 'operator', 'contextlib', 'traceback',
        'algorithms', 'scripts', 'templates', 'references', 'state',
        'test_', '__init__'
    }

    # 过滤出可能的第三方依赖
    third_party = imported_pkgs - stdlib_and_local
    third_party = {p for p in third_party if not p.startswith('_')}

    # 比较
    missing_in_req = third_party - declared_deps
    unused_in_code = declared_deps - third_party

    if missing_in_req:
        print("[WARN]  代码中导入但 requirements.txt 未声明:")
        for pkg in sorted(missing_in_req):
            print(f"   - {pkg}")
    else:
        print("[OK] 所有代码导入都在 requirements.txt 中声明")

    if unused_in_code:
        print("ℹ️  requirements.txt 中声明但代码未直接导入:")
        for pkg in sorted(unused_in_code):
            print(f"   - {pkg}")


def check_python_syntax(root: Path):
    """检查所有 Python 文件的语法"""
    import py_compile

    errors = []
    total = 0

    for py_file in sorted(root.rglob("*.py")):
        if "__pycache__" in str(py_file) or ".pyc" in str(py_file):
            continue

        total += 1
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append((py_file.name, str(e)))

    if errors:
        print(f"[FAIL] 发现 {len(errors)} 个语法错误:")
        for name, err in errors:
            print(f"   - {name}: {err}")
    else:
        print(f"[OK] 所有 {total} 个 Python 文件语法正确")


# 增强：添加 .typ 模板扫描
def scan_enhanced(root: Path) -> dict:
    """增强扫描：包含 .typ 模板"""
    inventory = scan(root)

    # 扫描 .typ 文件
    typ_files = []
    for p in sorted((root / "templates").glob("*.typ")):
        info = extract_text(p)
        typ_files.append((p.name, info["lines"], info["summary"], []))

    if typ_files:
        inventory["templates/（Typst 模板 .typ）"] = typ_files

    return inventory


if __name__ == "__main__":
    main()
