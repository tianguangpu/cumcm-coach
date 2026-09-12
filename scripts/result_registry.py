#!/usr/bin/env python3
"""
数值结果溯源注册表 v1.0 — 确保每个写入论文的数值可溯源

核心原则：论文中不得出现任何未经验证的数值
所有数值必须：可溯源到可执行代码 → 通过验证报告 → 批准写入论文

使用方式：
  # 初始化注册表
  python scripts/result_registry.py init --project .

  # 注册新结果
  python scripts/result_registry.py add --id result_001 --desc "问题1最优解" \
    --value 123.456 --script code/problem1.py --status PASS

  # 验证所有结果
  python scripts/result_registry.py verify --project .

  # 生成溯源报告
  python scripts/result_registry.py report --project . --output reports/traceability.md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_FILE = "state/result_registry.json"
REQUIRED_FIELDS = ['description', 'value', 'verification_status', 'source_script']


def init_registry(project_dir: str) -> dict:
    """初始化注册表"""
    registry = {
        "_meta": {
            "version": "1.0",
            "description": "数值结果溯源注册表",
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        },
        "results": {}
    }

    registry_path = os.path.join(project_dir, REGISTRY_FILE)
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f"[OK] 注册表已初始化: {registry_path}")
    return registry


def load_registry(project_dir: str) -> dict:
    """加载注册表"""
    registry_path = os.path.join(project_dir, REGISTRY_FILE)

    if not os.path.exists(registry_path):
        print(f"[WARN] 注册表不存在，正在初始化...")
        return init_registry(project_dir)

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_registry(project_dir: str, registry: dict):
    """保存注册表"""
    registry_path = os.path.join(project_dir, REGISTRY_FILE)
    registry['_meta']['updated'] = datetime.now().isoformat()

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def add_result(project_dir: str, result_id: str, description: str,
               value, unit: str, script: str, function: str,
               status: str, report: str) -> dict:
    """注册新结果"""
    registry = load_registry(project_dir)

    now = datetime.now().isoformat()

    result_entry = {
        "description": description,
        "value": value,
        "unit": unit or "",
        "verification_status": status,
        "approved_for_paper": status == "PASS",
        "source_script": script,
        "source_function": function or "",
        "verification_report": report or "",
        "baseline_comparison": None,
        "created_at": now,
        "updated_at": now
    }

    registry['results'][result_id] = result_entry
    save_registry(project_dir, registry)

    print(f"[OK] 结果已注册: {result_id}")
    print(f"   描述: {description}")
    print(f"   值: {value}")
    print(f"   状态: {status}")
    print(f"   可写入论文: {'是' if result_entry['approved_for_paper'] else '否'}")

    return result_entry


def verify_registry(project_dir: str) -> dict:
    """验证所有结果的状态"""
    registry = load_registry(project_dir)

    total = len(registry['results'])
    passed = 0
    failed = 0
    pending = 0
    issues = []

    for result_id, result in registry['results'].items():
        status = result.get('verification_status', 'PENDING')

        # 检查必填字段
        missing_fields = [f for f in REQUIRED_FIELDS if f not in result]
        if missing_fields:
            issues.append(f"{result_id}: 缺少字段 {missing_fields}")
            failed += 1
            continue

        # 检查源脚本是否存在
        script_path = os.path.join(project_dir, result.get('source_script', ''))
        if not os.path.exists(script_path):
            issues.append(f"{result_id}: 源脚本不存在 {result['source_script']}")
            failed += 1
            continue

        # 检查验证报告是否存在
        if result.get('verification_report'):
            report_path = os.path.join(project_dir, result['verification_report'])
            if not os.path.exists(report_path):
                issues.append(f"{result_id}: 验证报告不存在 {result['verification_report']}")
                pending += 1
                continue

        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        else:
            pending += 1

    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "approved_for_paper": sum(1 for r in registry['results'].values()
                                   if r.get('approved_for_paper', False)),
        "issues": issues
    }

    return report


def generate_report(project_dir: str, output_path: str) -> str:
    """生成溯源报告"""
    registry = load_registry(project_dir)
    verify_result = verify_registry(project_dir)

    report = f"""# 数值结果溯源报告

> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 注册表版本：{registry.get('_meta', {}).get('version', '未知')}

## 一、概览统计

| 指标 | 数量 |
|------|------|
| 总结果数 | {verify_result['total']} |
| 验证通过 | {verify_result['passed']} |
| 验证失败 | {verify_result['failed']} |
| 待验证 | {verify_result['pending']} |
| 可写入论文 | {verify_result['approved_for_paper']} |

## 二、结果清单

| ID | 描述 | 值 | 状态 | 可写入 | 源脚本 |
|----|------|-----|------|--------|--------|
"""

    for result_id, result in registry['results'].items():
        status_emoji = {
            'PASS': '[OK]',
            'FAIL': '[FAIL]',
            'PENDING': '⏳'
        }.get(result.get('verification_status'), '❓')

        approved = '[OK]' if result.get('approved_for_paper') else '[FAIL]'
        value = result.get('value', 'N/A')
        if isinstance(value, float):
            value = f"{value:.6f}"

        report += f"| {result_id} | {result.get('description', '-')} | {value} | {status_emoji} {result.get('verification_status')} | {approved} | {result.get('source_script', '-')} |\n"

    # 问题清单
    if verify_result['issues']:
        report += f"""
## 三、问题清单

"""
        for issue in verify_result['issues']:
            report += f"- [FAIL] {issue}\n"

    # 论文引用规则
    report += """
## 四、论文引用规则

**铁则：论文中不得出现任何未经验证的数值**

所有数值必须满足以下条件才能写入论文：
1. 已在本注册表登记（`result_registry.json`）
2. `verification_status = PASS`
3. `approved_for_paper = true`
4. 源脚本可执行且验证报告存在

违反此规则的数值将被 auto_check.py 的 L3 检查拦截。
"""

    # 保存报告
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"[REPORT] 溯源报告已生成: {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description='数值结果溯源注册表 — 确保每个写入论文的数值可溯源'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化注册表')
    init_parser.add_argument('--project', default='.', help='项目目录')

    # add 命令
    add_parser = subparsers.add_parser('add', help='注册新结果')
    add_parser.add_argument('--project', default='.', help='项目目录')
    add_parser.add_argument('--id', required=True, help='结果ID，如 result_001')
    add_parser.add_argument('--desc', required=True, help='结果描述')
    add_parser.add_argument('--value', required=True, help='数值结果')
    add_parser.add_argument('--unit', default='', help='单位')
    add_parser.add_argument('--script', required=True, help='源脚本路径')
    add_parser.add_argument('--function', default='', help='源函数名')
    add_parser.add_argument('--status', default='PENDING',
                           choices=['PASS', 'FAIL', 'PENDING'], help='验证状态')
    add_parser.add_argument('--report', default='', help='验证报告路径')

    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='验证所有结果')
    verify_parser.add_argument('--project', default='.', help='项目目录')

    # report 命令
    report_parser = subparsers.add_parser('report', help='生成溯源报告')
    report_parser.add_argument('--project', default='.', help='项目目录')
    report_parser.add_argument('--output', default='reports/traceability.md',
                              help='输出路径')

    args = parser.parse_args()

    if args.command == 'init':
        init_registry(args.project)

    elif args.command == 'add':
        # 尝试解析数值
        try:
            value = float(args.value)
            if value == int(value):
                value = int(value)
        except ValueError:
            value = args.value

        add_result(
            project_dir=args.project,
            result_id=args.id,
            description=args.desc,
            value=value,
            unit=args.unit,
            script=args.script,
            function=args.function,
            status=args.status,
            report=args.report
        )

    elif args.command == 'verify':
        result = verify_registry(args.project)
        print(f"\n[STATS] 验证结果:")
        print(f"   总数: {result['total']}")
        print(f"   通过: {result['passed']} [OK]")
        print(f"   失败: {result['failed']} [FAIL]")
        print(f"   待验: {result['pending']} ⏳")
        print(f"   可写入: {result['approved_for_paper']}")

        if result['issues']:
            print(f"\n[WARN] 问题:")
            for issue in result['issues']:
                print(f"   - {issue}")

    elif args.command == 'report':
        generate_report(args.project, args.output)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
