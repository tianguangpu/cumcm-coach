---
tags:
  - 工具
  - 溯源
  - 注册表
aliases:
  - result_registry
  - 结果溯源
  - 数值验证
category: 工具
related:
  - "[[baseline_compare基线比较]]"
  - "[[self_verify自证门禁]]"
  - "[[金标准内核]]"
---

# result_registry 数值结果溯源注册表

> **核心原则**：论文中不得出现任何未经验证的数值。

## 使用方法

```bash
# 初始化
python scripts/result_registry.py init --project .

# 注册结果
python scripts/result_registry.py add --id result_001 --desc "最优解" --value 123.456 --script code/problem1.py --status PASS

# 验证
python scripts/result_registry.py verify --project .

# 生成报告
python scripts/result_registry.py report --project .
```

## 铁则

`verification_status = PASS` 且 `approved_for_paper = true` 才能写入论文。

## 数据结构

```json
{
  "id": "result_001",
  "description": "问题1最优解",
  "value": 123.456,
  "script": "code/problem1.py",
  "verification_status": "PASS",
  "approved_for_paper": true,
  "timestamp": "2026-08-28T10:00:00"
}
```

> **相关笔记**: [[baseline_compare基线比较]] | [[self_verify自证门禁]] | [[脚本清单]]
