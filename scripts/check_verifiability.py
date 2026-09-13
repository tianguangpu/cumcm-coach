# -*- coding: utf-8 -*-
"""
check_verifiability.py — 图表真实性溯源检测(反假图, 题目无关通用版)
====================================================================
核对论文中每一张图是否「由真实脚本 + 真实数据生成」, 而非 AI 编造/手绘/复制。
不硬编码任何具体题目细节(脚本名/数据文件名/图名), 全部从工作链自动发现:

  工作链:  main.tex 引用图 → figures/png 磁盘图 → code/*.py 绘图脚本 → 数据文件(results/ + 原始 xlsx/csv)

五层检测:
  L1 溯源链:   论文引用图 ↔ 脚本生成图 ↔ 磁盘文件 三方比对, 揪「孤儿图」(引用但无脚本生成)
  L2 数据来源: 脚本引用的数据文件是否在位 + 硬编码长数据数组检测
  L3 时序一致: 图文件 mtime 是否晚于其依赖的数据文件(旧图=未随数据重生成)
  L4 可复现性: 绘图脚本语法是否有效
  L5 端到端:   实际运行绘图脚本, 检查输出文件是否真实生成(成功+10, 失败-20)

分级: FAIL=致命(孤儿图/幽灵图/语法错/端到端失败), WARN=提示(引用缺失/硬编码/时序旧图)

用法:
  py check_verifiability.py              # 五层全检
  py check_verifiability.py --quick      # 仅 L1 溯源链
  py check_verifiability.py --no-e2e     # 跳过 L5(慢)
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):  # Win GBK console emoji fix
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import os
import re
import argparse

# v7 移植版：项目根默认取当前工作目录（run_all.py 在用户项目目录下调用本脚本）。
# 脚本位于 v7/scripts/，用户项目结构为 BASE/{code,paper,figures,results}。
BASE = os.getcwd()
CODE_DIR = os.path.join(BASE, 'code')
SRC = BASE
TEX = os.path.join(BASE, 'paper', 'main.tex')
FIG_PNG = os.path.join(BASE, 'figures', 'png')
RESULTS = os.path.join(BASE, 'results')

FIG_NAME_RE = r'fig\d+[a-z0-9_]*'            # 图名规范: fig1_workflow / fig10_11_subcluster

# 纯工具脚本(不含业务数据读取/成图, 不参与扫描)
PURE_TOOLS = {'pipeline.py', 'run_all.py', 'dashboard.py', 'build_paper.py'}
# 被 import 的公共模块(定义 finish_figure/load_data 但本身不成图, 绘图脚本发现时排除)
LIB_MODULES = {'plot_style.py', 'common.py'}


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def read_optional(path):
    return read(path) if os.path.exists(path) else ''


# ==================== 工作链自动发现(题目无关) ====================
def list_scripts():
    """所有业务脚本 = code/*.py 排除纯工具与 check_*(含公共模块, 供数据引用扫描)。"""
    return [f for f in sorted(os.listdir(CODE_DIR))
            if f.endswith('.py') and f not in PURE_TOOLS and not f.startswith('check_')]


def discover_plot_scripts():
    """自动发现绘图脚本 = 排除公共模块后, 实际调用 finish_figure / savefig→figures 的脚本。"""
    out = []
    for f in list_scripts():
        if f in LIB_MODULES:
            continue
        src = read_optional(os.path.join(CODE_DIR, f))
        if re.search(r'finish_figure\s*\(', src) or ('.savefig(' in src and 'figures' in src):
            out.append(f)
    return out


def discover_data_basenames():
    """已知数据文件 basename = results/ 全部 + 项目根及 data/ 子目录下原始 xlsx/csv。"""
    names = set()
    if os.path.isdir(RESULTS):
        names |= set(os.listdir(RESULTS))
    # v7 用户项目数据常在 data/raw、data/clean，须一并扫描，否则误判脚本「未读数据」
    scan_dirs = [BASE]
    for sub in ('data', 'data/raw', 'data/clean', 'raw', 'clean'):
        d = os.path.join(BASE, sub)
        if os.path.isdir(d):
            scan_dirs.append(d)
    for d in scan_dirs:
        for f in os.listdir(d):
            if f.lower().endswith(('.xlsx', '.xls', '.csv')):
                names.add(f)
    return names


def collect_fig_names(scripts):
    """扫描绘图脚本里所有 fig* 字面量 → 图名集合。"""
    names = set()
    for s in scripts:
        src = read_optional(os.path.join(CODE_DIR, s))
        names |= set(re.findall(r"['\"](" + FIG_NAME_RE + r")['\"]", src))
    return names


def collect_data_refs():
    """扫描业务脚本(含 common.py)里引用的数据文件名 → basename 集合。"""
    refs = set()
    for s in list_scripts():
        src = read_optional(os.path.join(CODE_DIR, s))
        for m in re.findall(r"['\"]([a-zA-Z0-9_./-]+\.(?:npy|npz|json|csv|xlsx|xls))['\"]", src):
            refs.add(os.path.basename(m))
    return refs


def collect_save_targets():
    """扫描脚本保存的数据文件 → {脚本: 保存的文件名集合}(反凭空生成)。"""
    saves = {}
    for s in list_scripts():
        src = read_optional(os.path.join(CODE_DIR, s))
        names = set()
        for m in re.findall(r"(?:np\.save|json\.dump|to_excel|to_csv)\([^)]*?['\"]([a-zA-Z0-9_./-]+\.(?:npy|npz|json|xlsx|csv))['\"]", src):
            names.add(os.path.basename(m))
        if names:
            saves[s] = names
    return saves


def reads_any_input(s):
    """脚本是否读取原始数据(load_data/read_excel/read_csv)或上游结果(np.load/json.load)。"""
    src = read_optional(os.path.join(CODE_DIR, s))
    has_raw = re.search(r'load_data\s*\(|read_excel\s*\(|read_csv\s*\(|ExcelFile\s*\(|\.parse\s*\(|\.read_table\s*\(|\.read_fwf\s*\(', src) is not None
    has_upstream = re.search(r'np\.load\s*\(|json\.load\s*\(\s*open', src) is not None
    return has_raw or has_upstream


# ==================== L1 溯源链完整性 ====================
def check_trace():
    print('=' * 70)
    print('L1 溯源链: 论文引用图 ↔ 脚本生成图 ↔ 磁盘文件')
    print('=' * 70)

    tex = read_optional(TEX)
    tex_figs = set()
    for r in re.findall(r'\\includegraphics[^{]*\{([^}]+)\}', tex):
        m = re.search(r'(' + FIG_NAME_RE + r')\.(?:pdf|png)$', r)
        if m:
            tex_figs.add(m.group(1))

    plot_scripts = discover_plot_scripts()
    code_figs = collect_fig_names(plot_scripts)

    disk_figs = set()
    if os.path.isdir(FIG_PNG):
        for f in os.listdir(FIG_PNG):
            m = re.match(r'(' + FIG_NAME_RE + r')\.png$', f)
            if m:
                disk_figs.add(m.group(1))

    # 概念图（技术路线图/流程图）用 TikZ/diagram-design 生成，非数据脚本，豁免溯源链
    concept = {f for f in tex_figs if re.search(
        r'roadmap|flowchart|techroute|architecture|framework|model_arch|data_pipe|algorithm_flow|workflow',
        f, re.I)}
    orphan = sorted((tex_figs - code_figs) - concept)  # 论文引用但无脚本生成 → 假图高危
    ghost = sorted(code_figs - disk_figs)          # 脚本声明但磁盘无文件 → 图未生成
    redundant = sorted(code_figs - tex_figs)       # 脚本生成但论文未引用(提示)
    unknown = sorted(disk_figs - code_figs)        # 磁盘有图但无脚本声明(提示)

    print(f'  绘图脚本: {", ".join(plot_scripts) or "无"}')
    print(f'  论文引用: {len(tex_figs)} 张 | 脚本声明: {len(code_figs)} 张 | 磁盘实存: {len(disk_figs)} 张')
    for label, lst in [('孤儿图(论文引用但无脚本生成, 假图高危)', orphan),
                       ('幽灵图(脚本声明但磁盘无文件, 图未生成)', ghost)]:
        if lst:
            for x in lst:
                print(f'  ✗ [FAIL] {x}')
        else:
            print(f'  ✓ 无{label.split("(")[0]}')
    for label, lst in [('冗余图(脚本生成但论文未引用)', redundant),
                       ('未登记图(磁盘有但无脚本声明)', unknown)]:
        if lst:
            for x in lst:
                print(f'  ⚠ [WARN] {label}: {x}')
    if not (orphan or ghost):
        print(f'  ✓ L1 通过: 论文引用的每张图都能溯源到脚本与磁盘文件')
    return len(orphan) + len(ghost)


# ==================== L2 数据来源真实性 ====================
def check_data_source():
    print('\n' + '=' * 70)
    print('L2 数据来源: 引用在位 + 硬编码 + 凭空生成检测')
    print('=' * 70)

    # (a) 脚本引用的数据文件名 vs 已知数据文件 basename
    refs = collect_data_refs()
    known = discover_data_basenames()
    missing = sorted(refs - known)
    if missing:
        for m in missing:
            print(f'  ⚠ [WARN] 脚本引用但磁盘未找到: {m}')
        print(f'  ⚠ [WARN] 共 {len(missing)} 个, 可能是中间结果未生成或路径写法差异, 请人工确认')
    else:
        print(f'  ✓ 脚本引用的 {len(refs)} 个数据文件全部在位')

    # (b) 硬编码数据检测(连续≥6个数字的数组字面量 = 疑似手写数据而非从文件读)
    hardcode = []
    for s in list_scripts():
        src = read_optional(os.path.join(CODE_DIR, s))
        for i, line in enumerate(src.splitlines(), 1):
            if re.search(r"\[\s*[\d.+-]+(?:\s*,\s*[\d.+-]+){5,}\s*\]", line):
                hardcode.append((s, i, line.strip()[:70]))
    if hardcode:
        for s, i, txt in hardcode:
            print(f'  ⚠ [WARN] {s}:{i} 疑似硬编码数据数组(≥6数字): {txt}...')
        print(f'  ⚠ [WARN] 共 {len(hardcode)} 处, 请人工确认是否为真实计算值或仅为布局坐标')
    else:
        print(f'  ✓ 未发现硬编码长数据数组(数据均从文件读取)')

    # (c) 数据溯源: 保存结果文件的脚本必须读取原始数据或上游结果, 否则是凭空生成假数据
    phantom = []
    for s, names in collect_save_targets().items():
        if not reads_any_input(s):
            phantom.append((s, sorted(names)))
    if phantom:
        for s, names in phantom:
            print(f'  ✗ [FAIL] {s} 保存了 {", ".join(names)} 但未读取原始数据/上游结果(凭空生成假数据)')
    else:
        print(f'  ✓ 每个结果文件均由读取了数据的脚本生成(数据可溯源)')
    return len(phantom)


# ==================== L3 时序一致性 ====================
def check_timestamps():
    print('\n' + '=' * 70)
    print('L3 时序一致: 图文件 mtime 是否晚于其依赖的数据文件')
    print('=' * 70)
    if not os.path.isdir(FIG_PNG):
        print('  ✗ figures/png 目录不存在'); return 1

    data_files = []
    if os.path.isdir(RESULTS):
        data_files += [os.path.join(RESULTS, f) for f in os.listdir(RESULTS)]
    for d in (BASE, SRC):
        if os.path.isdir(d):
            data_files += [os.path.join(d, f) for f in os.listdir(d)
                           if f.lower().endswith(('.xlsx', '.xls', '.csv'))]
    data_mtime = max((os.path.getmtime(f) for f in data_files if os.path.exists(f)), default=0)

    stale = [f for f in sorted(os.listdir(FIG_PNG))
             if f.endswith('.png') and os.path.getmtime(os.path.join(FIG_PNG, f)) < data_mtime]
    if stale:
        for f in stale:
            print(f'  ⚠ [WARN] {f} 早于最新数据文件(可能是旧图, 未随数据重生成)')
        print(f'  ⚠ [WARN] 共 {len(stale)} 张, 建议重跑绘图(注: OneDrive 同步可能干扰 mtime, 需人工复核)')
    else:
        print(f'  ✓ 所有图均晚于数据文件(时序正常)')
    return 0  # 时序仅提示, 不计 FAIL


# ==================== L4 可复现性 ====================
def check_compile():
    print('\n' + '=' * 70)
    print('L4 可复现性: 绘图脚本语法是否有效')
    print('=' * 70)
    scripts = discover_plot_scripts()
    if not scripts:
        print('  ⚠ [WARN] 未自动发现绘图脚本, 请检查是否用了 finish_figure/savefig 命名')
        return 0
    fail = 0
    for s in scripts:
        try:
            compile(read(os.path.join(CODE_DIR, s)), s, 'exec')
            print(f'  ✓ {s} 语法有效')
        except SyntaxError as e:
            print(f'  ✗ [FAIL] {s} 语法错误: {e}'); fail += 1
    return fail


# ==================== L5 端到端验证 ====================
def check_e2e():
    """L5 端到端验证: 实际运行绘图脚本, 检查输出是否生成。
    选择 1~2 个绘图脚本, 在安全环境运行, 验证输出文件。
    成功 +10 分, 失败 -20 分(容错: 仅选 1 个脚本, 避免环境依赖问题)。
    """
    import subprocess
    import tempfile
    import shutil

    print('\n' + '=' * 70)
    print('L5 端到端验证: 实际运行绘图脚本, 检查输出是否真实生成')
    print('=' * 70)

    scripts = discover_plot_scripts()
    if not scripts:
        print('  ⚠ [WARN] 未发现绘图脚本, 跳过端到端验证')
        return 0

    # 优先选择: 调用 finish_figure 的脚本(最可能是关键图表)
    candidates = []
    for s in scripts:
        src = read_optional(os.path.join(CODE_DIR, s))
        if 'finish_figure' in src:
            candidates.insert(0, s)  # 优先
        else:
            candidates.append(s)

    # 仅取前 1 个脚本(减少环境依赖风险)
    test_scripts = candidates[:1]
    success = 0
    fail = 0

    for script in test_scripts:
        script_path = os.path.join(CODE_DIR, script)
        print(f'\n  运行: {script}')

        # 检查依赖数据文件是否存在
        src = read_optional(script_path)
        data_deps = re.findall(r"['\"]([a-zA-Z0-9_./-]+\.(?:npy|npz|json|csv|xlsx))['\"]", src)
        missing_deps = [d for d in data_deps
                        if not os.path.exists(os.path.join(BASE, d))
                        and not os.path.exists(os.path.join(RESULTS, os.path.basename(d)))
                        and not os.path.exists(os.path.join(CODE_DIR, d))]
        if missing_deps:
            print(f'  ⚠ [WARN] 缺少数据依赖: {", ".join(missing_deps)}, 跳过此脚本')
            continue

        # 在临时目录运行, 复现项目结构 (BASE/code, BASE/results, BASE/figures)
        tmp_base = tempfile.mkdtemp(prefix='verif_e2e_')
        tmp_code = os.path.join(tmp_base, 'code')
        tmp_results = os.path.join(tmp_base, 'results')
        tmp_figures = os.path.join(tmp_base, 'figures')
        for d in (tmp_code, tmp_results, tmp_figures):
            os.makedirs(d, exist_ok=True)
        tmp_script = os.path.join(tmp_code, script)
        try:
            # 复制脚本 + 库模块到 code/
            shutil.copy2(script_path, tmp_script)
            for mod in LIB_MODULES:
                mod_path = os.path.join(CODE_DIR, mod)
                if os.path.exists(mod_path):
                    shutil.copy2(mod_path, os.path.join(tmp_code, mod))

            # 复制结果到 results/
            if os.path.isdir(RESULTS):
                for f in os.listdir(RESULTS):
                    src_f = os.path.join(RESULTS, f)
                    if os.path.isfile(src_f):
                        shutil.copy2(src_f, os.path.join(tmp_results, f))

            # 复制原始数据到 BASE/(cwd 回退可找到)
            raw = os.path.join(os.path.dirname(BASE), '附件.xlsx')
            if os.path.exists(raw):
                shutil.copy2(raw, os.path.join(tmp_base, '附件.xlsx'))

            # 运行脚本 (timeout=60s, 强制 Agg 无头后端避免 GUI 段错误)
            env = dict(os.environ)
            env['MPLBACKEND'] = 'Agg'
            r = subprocess.run(
                [sys.executable, '-X', 'utf8', tmp_script],
                cwd=tmp_base,
                capture_output=True,
                timeout=60,
                env=env,
            )

            if r.returncode == 0:
                # 检查 figures/ 下新生成的图(递归, 含 png/pdf 子目录)
                outputs = []
                for root, _dirs, files in os.walk(tmp_base):
                    for f in files:
                        fp = os.path.join(root, f)
                        if f.endswith(('.png', '.pdf', '.jpg', '.svg')) \
                           and os.path.getmtime(fp) > os.path.getmtime(tmp_script):
                            outputs.append(os.path.relpath(fp, tmp_base))
                if outputs:
                    # 检查文件大小 > 1KB
                    valid = [f for f in outputs
                             if os.path.getsize(os.path.join(tmp_base, f)) > 1024]
                    if valid:
                        print(f'  ✓ {script} 运行成功, 生成 {len(valid)} 个有效输出: {", ".join(valid)}')
                        success += 1
                    else:
                        print(f'  ✗ [FAIL] {script} 输出文件过小(<1KB), 可能是空图')
                        fail += 1
                else:
                    print(f'  ✗ [FAIL] {script} 运行成功但未生成新图文件')
                    fail += 1
            else:
                stderr = (r.stderr or b'').decode('utf-8', errors='ignore')[-300:]
                print(f'  ✗ [FAIL] {script} 运行失败 (rc={r.returncode})')
                if stderr:
                    print(f'    stderr: {stderr[:200]}')
                fail += 1

        except subprocess.TimeoutExpired:
            print(f'  ✗ [FAIL] {script} 运行超时(>60s)')
            fail += 1
        except Exception as e:
            print(f'  ✗ [FAIL] {script} 运行异常: {e}')
            fail += 1
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(tmp_base, ignore_errors=True)
            except Exception:
                pass

    return fail  # 每个失败 -1 (汇总时 *20 扣分)


def main():
    ap = argparse.ArgumentParser(description='图表真实性溯源检测(反假图, 通用版)')
    ap.add_argument('--dir', default=None, help='项目根目录(默认当前工作目录)')
    ap.add_argument('--quick', action='store_true', help='仅 L1 溯源链')
    ap.add_argument('--no-e2e', action='store_true', help='跳过 L5 端到端验证(慢)')
    args = ap.parse_args()

    # --dir 覆盖项目根（v7 移植版：脚本不在项目 code/ 内）
    if args.dir:
        global BASE, CODE_DIR, SRC, TEX, FIG_PNG, RESULTS
        BASE = os.path.abspath(args.dir)
        CODE_DIR = os.path.join(BASE, 'code')
        SRC = BASE
        TEX = os.path.join(BASE, 'paper', 'main.tex')
        FIG_PNG = os.path.join(BASE, 'figures', 'png')
        RESULTS = os.path.join(BASE, 'results')

    fail = check_trace()
    if not args.quick:
        fail += check_data_source()
        fail += check_timestamps()
        fail += check_compile()
        if not args.no_e2e:
            fail += check_e2e()

    print('\n' + '=' * 70)
    print('总结')
    print('=' * 70)
    if fail == 0:
        print('✓ 图表可溯源: 论文引用的每张图均能回溯到真实脚本 + 真实数据, 无假图。')
    else:
        print(f'  ✗ 发现 {fail} 处 FAIL(孤儿图/幽灵图/语法错误/端到端失败), 需处理')
    _score = max(50, 100 - fail * 20)
    print(f'SCORE:{_score}/100')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
