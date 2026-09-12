# v7 新功能详细使用指南

> 本文档包含 v7.9-v7.10 新增功能的详细使用示例。SKILL.md 中仅列概述。

## 1. 基线比较机制（baseline_compare.py）

**核心原则**：correctness beats sophistication。每个高级模型必须先跑简单基线。

### 使用方式

```bash
# B题：用预设方案比较（随机数据）
python scripts/baseline_compare.py --type B --advanced results/model.json --output reports/baseline.md

# 指定实际数据文件（CSV/JSON/NPY）
python scripts/baseline_compare.py --type B --data data/cost_matrix.csv --advanced results/model.json

# D题：自定义基线类型
python scripts/baseline_compare.py --type D --baseline-type moving_average \
  --data data/sales_series.csv --advanced results/arima.json --metric mape --lower-is-better
```

### 题型→基线映射

| 题型 | 基线模型 | 比较指标 | 方向 | --data 格式 |
|------|----------|----------|------|-------------|
| A机理 | 离散队列模型 | avg_wait | 越低越好 | 到达序列 CSV |
| B优化 | 贪心分配 | total_cost | 越低越好 | N×M 成本矩阵 CSV |
| C评价 | 等权赋权 | score | 越高越好 | N×M 决策矩阵 CSV |
| D预测 | 移动平均 | mape | 越低越好 | 单列时序 CSV |

### 铁则

高级模型必须优于基线才能写入论文。未通过则需重新审视模型选择。

## 2. 数值结果溯源注册表（result_registry.py）

**核心原则**：论文中不得出现任何未经验证的数值。

### 使用方式

```bash
# 初始化注册表
python scripts/result_registry.py init --project .

# 注册结果
python scripts/result_registry.py add --id result_001 --desc "问题1最优解" \
  --value 123.456 --script code/problem1.py --status PASS

# 验证所有结果
python scripts/result_registry.py verify --project .

# 生成溯源报告
python scripts/result_registry.py report --project . --output reports/traceability.md
```

### 注册表结构（state/result_registry.json）

```json
{
  "result_001": {
    "description": "问题1最优解",
    "value": 123.456,
    "verification_status": "PASS",
    "approved_for_paper": true,
    "source_script": "code/problem1.py",
    "verification_report": "reports/verification/problem1_verify.md"
  }
}
```

**铁则**：`verification_status = PASS` 且 `approved_for_paper = true` 才能写入论文。

## 3. 论文质量自检（check_paper_quality.py）

支持 LaTeX + Typst 双引擎，自动检测排版引擎。

### 使用方式

```bash
# LaTeX 论文
python scripts/check_paper_quality.py --paper paper/main.tex --output reports/quality.md

# Typst 论文
python scripts/check_paper_quality.py --paper paper/main.typ --output reports/quality.md
```

### 6维度100分制

| 维度 | 满分 | 检查项 |
|------|------|--------|
| 摘要质量 | 20 | 量化结果、方法名称、关键词、长度 |
| 模型结构 | 20 | 递进链路、问题分析、假设说明 |
| 公式规范 | 15 | 数量、编号、引用 |
| 图表规范 | 15 | 数量、标题、引用 |
| 四重检验 | 20 | 拟合精度、灵敏度、蒙特卡洛、假设误差 |
| 参考文献 | 10 | 数量、近5年、外文 |

### 等级划分

- A（≥90分）：国一水平
- B（≥80分）：国二水平
- C（≥70分）：省一水平
- D（<70分）：需改进

## 4. 求解器自动路由（solver_router.py）

支持 LP/MIP/NLP/VRP/JobShop/TSP 多种问题类型自动路由。

### 使用方式

```python
from scripts.solver_router import solve_lp, solve_vrp, solve_job_shop, select_solver_auto

# LP 求解
result = solve_lp(
    objective={"x": 10, "y": 8},
    constraints=[{"coeffs": {"x": 1, "y": 1}, "sense": "<=", "rhs": 100}],
    variables={"x": {"lowBound": 0}, "y": {"lowBound": 0}},
    sense="maximize"
)

# VRP 求解
result = solve_vrp(dist_matrix, demands, capacity=10, method="ga")

# JobShop 求解
result = solve_job_shop(jobs, method="ga")

# 自动路由
result = select_solver_auto("VRP", dist_matrix=dist, demands=demands, capacity=10)
```

### 路由规则

| 问题类型 | 路由目标 | 优先级 |
|---------|---------|--------|
| LP/MIP | HiGHS → PuLP → SciPy | 外部求解器 |
| VRP | algorithms/optimization/vrp.py | 内置算法 |
| JSSP | algorithms/optimization/job_shop.py | 内置算法 |
| TSP | GA 兜底 / mcp-optimizer（MCP优先） | 混合 |
| NLP | SciPy minimize | 外部求解器 |

## 5. 代码清单增强（gen_code_manifest.py v1.1）

```bash
# 检查依赖一致性
python scripts/gen_code_manifest.py --check-deps

# 检查 Python 语法
python scripts/gen_code_manifest.py --check-syntax
```

## 6. Typst 模板（7 套）

| 模板 | 文件 | 赛事 |
|------|------|------|
| 国赛A题 | templates/template-a.md | CUMCM A机理 |
| 国赛B题 | templates/template-b.md | CUMCM B优化 |
| 国赛C题 | templates/template-c.md | CUMCM C评价 |
| 国赛D题 | templates/template-d.md | CUMCM D数据 |
| 华数杯 | templates/template-huashu.typ | 第七届华数杯 |
| 华为杯 | templates/template-huawei.typ | 华为杯研究生 |
| MCM/ICM | templates/template-mcm.typ | 美国大学生建模 |
