# CUMCM Coach Skill v7

<div align="center">

![Version](https://img.shields.io/badge/version-7.11.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.13+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-34%20modules-brightgreen.svg)
![CUMCM](https://img.shields.io/badge/CUMCM-国一冲刺-gold.svg)

**全国大学生数学建模竞赛（CUMCM）国一冲刺级论文生成系统**

[快速开始](#快速开始) · [功能特性](#功能特性) · [架构设计](#架构设计) · [使用指南](#使用指南) · [贡献指南](CONTRIBUTING.md)

</div>

---

## 快速开始

### 环境要求

- Python 3.13+
- MATLAB R2024a+（可选，用于绘图）
- LaTeX（XeLaTeX）或 Typst（可选，用于论文编译）

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd cumcm-coach-skill-v7

# 安装依赖
pip install -r requirements.txt

# 或使用 Makefile
make install
```

### 5分钟快速使用

```bash
# 1. 初始化项目
python scripts/init_project.py --team "202600001" --members "张三,李四,王五" --type B

# 2. 运行全链流水线（干跑模式）
python scripts/run_all.py --dry

# 3. 运行单元测试
make test

# 4. 生成基准测试报告
make benchmark
```

---

## 功能特性

### 核心能力

| 模块 | 功能 | 脚本 |
|------|------|------|
| **项目初始化** | 目录结构+状态文件 | `init_project.py` |
| **全链流水线** | 13步断点续跑 | `run_all.py` |
| **算法库** | 34个模块全PASS | `algorithms/` |
| **求解器路由** | 多求解器自动选择 | `solver_router.py` |
| **基线比较** | 防止"自证循环" | `baseline_compare.py` |
| **结果溯源** | 数值验证注册表 | `result_registry.py` |
| **四重检验** | L1-L4分级评审 | `auto_check.py` |
| **AI合规** | 2026新规全链路 | `ai_compliance.py` |
| **文献检索** | OpenAlex自动检索 | `search_openalex.py` |
| **摘要优化** | 5+3检查+8稿迭代 | `polish_abstract.py` |

### 算法库（34模块）

```
algorithms/
├── optimization/      # 优化算法（6个）
│   ├── ga.py         # 遗传算法
│   ├── de.py         # 差分进化
│   ├── sa_pso.py     # 模拟退火+粒子群混合
│   ├── vrp.py        # 车辆路径问题
│   ├── job_shop.py   # 车间调度
│   └── two_stage.py  # 两阶段优化
├── prediction/        # 预测算法（4个）
│   ├── arima.py      # ARIMA时序预测
│   ├── gm11.py       # 灰色预测
│   ├── mlp.py        # 神经网络预测
│   └── tam.py        # 技术采纳模型
├── evaluation/        # 评价算法（3个）
│   ├── ahp_entropy_topsis.py  # 综合评价
│   ├── vikor.py      # VIKOR评价
│   └── gra.py        # 灰色关联
├── mechanistic/       # 机理模型（5个）
│   ├── fdm_1d.py     # 一维有限差分
│   ├── fdm_2d.py     # 二维有限差分
│   ├── fem_poisson.py # 有限元
│   └── ode_solver.py # ODE求解器
├── network/           # 图论算法（1个）
│   └── graph_algo.py # Dijkstra/Kruskal/最大流
├── validation/        # 验证工具（3个）
│   ├── metrics.py    # 拟合指标
│   ├── sensitivity.py # 灵敏度分析
│   └── monte_carlo.py # 蒙特卡洛仿真
└── misc/              # 辅助工具（2个）
    ├── problem_analyzer.py  # 问题分析
    └── innovation_guide.py  # 创新指导
```

### 题型支持

| 题型 | 代码 | 基线模型 | 典型算法 |
|------|------|----------|----------|
| A 机理分析 | `--type A` | 离散队列模型 | FDM/FEM/ODE |
| B 优化决策 | `--type B` | 贪心分配 | GA/DE/SA-PSO |
| C 综合评价 | `--type C` | 等权赋权 | TOPSIS/VIKOR/GRA |
| D 数据分析 | `--type D` | 移动平均 | ARIMA/GM11/MLP |

---

## 架构设计

```
cumcm-coach-skill-v7/
├── SKILL.md              # 主文档（Claude Code skill定义）
├── QUICKSTART.md         # 快速开始
├── README.md             # 本文件
├── CHANGELOG.md          # 版本历史
├── CONTRIBUTING.md       # 贡献指南
├── Makefile              # 自动化命令
├── Dockerfile            # Docker容器化
├── docker-compose.yml    # Docker编排
├── requirements.txt      # Python依赖
├── .pre-commit-config.yaml # Git hooks配置
│
├── scripts/              # 工具脚本（28个）
│   ├── run_all.py        # 全链流水线
│   ├── init_project.py   # 项目初始化
│   ├── solver_router.py  # 求解器路由
│   ├── auto_check.py     # 四重检验
│   └── ...               # 其他脚本
│
├── algorithms/           # 算法库（34模块）
│   ├── base.py           # 基类定义
│   ├── optimization/     # 优化算法
│   ├── prediction/       # 预测算法
│   ├── evaluation/       # 评价算法
│   ├── mechanistic/      # 机理模型
│   └── ...               # 其他类别
│
├── templates/            # 论文模板
│   ├── template-a.tex    # A题LaTeX模板
│   ├── template-b.tex    # B题LaTeX模板
│   └── ...               # 其他模板
│
├── references/           # 参考文档
│   ├── de-ai-writing.md  # 去AI味指南
│   ├── figure-routing.md # 图表路由
│   └── ...               # 其他参考
│
├── tests/                # 测试套件
│   ├── conftest.py       # pytest配置
│   ├── test_algorithms.py # 算法单元测试
│   └── test_e2e.py       # 端到端测试
│
├── vault/                # Obsidian知识库
│   ├── 00-MOC/           # 内容地图
│   ├── 01-算法/          # 算法笔记
│   └── ...               # 其他笔记
│
├── state/                # 运行状态
│   └── project_state.json
│
├── output/               # 输出目录
│   ├── ai_declaration.tex
│   └── ...
│
└── utils/                # 工具模块
    └── logger.py         # 统一日志
```

---

## 使用指南

### 场景1：完整论文生成

```bash
# 初始化
python scripts/init_project.py --team "202600001" --members "张三,李四,王五" --type B

# 全链运行（带断点续跑）
python scripts/run_all.py

# 从第7步继续
python scripts/run_all.py --from 07
```

### 场景2：单问题求解

```python
from algorithms.optimization.ga import GA
from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

# 遗传算法求解
def objective(x):
    return sum(xi**2 for xi in x)

result = GA(objective, dim=3, bounds=[(-5,5)]*3, pop_size=50, max_gen=200)
print(f"最优解: {result['x_opt']}, 最优值: {result['f_opt']}")

# TOPSIS综合评价
data = [[7, 9, 9], [8, 6, 8], [9, 4, 7]]
ev = ComprehensiveEvaluation(data, benefit_cols=[0,1,2], cost_cols=[])
weights = ev.run_entropy()
topsis_result = ev.topsis()
```

### 场景3：求解器自动路由

```python
from scripts.solver_router import SolverRouter

router = SolverRouter()

# 自动选择求解器
result = router.solve({
    'type': 'vrp',
    'dist': distance_matrix,
    'demands': demands,
    'capacity': 100,
    'n_vehicles': 5
})
```

### 场景4：基线比较

```bash
# 运行基线比较
python scripts/baseline_compare.py \
    --type B \
    --advanced results/model.json \
    --output reports/baseline.md

# 查看报告
cat reports/baseline.md
```

### 场景5：运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
pytest tests/test_algorithms.py -v

# 生成覆盖率报告
pytest --cov=algorithms --cov-report=html
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CUMCM_MATLAB_PATH` | MATLAB路径 | `/d/MatLab/bin/matlab.exe` |
| `CUMCM_TEAM_ID` | 队伍编号 | `202600001` |
| `CUMCM_PROBLEM_TYPE` | 题型 | `B` |
| `CUMCM_SEED` | 随机种子 | `42` |

### 配置文件

- `requirements.txt` - Python依赖
- `state/project_state.json` - 项目状态
- `vault/` - Obsidian知识库配置

---

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细指南。

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 致谢

- [latexstudio/CUMCMThesis](https://github.com/latexstudio/CUMCMThesis) - LaTeX模板参考
- [PuLP](https://github.com/coin-or/pulp) - 优化求解器
- [OR-Tools](https://github.com/google/or-tools) - 运筹优化工具
- [scikit-learn](https://github.com/scikit-learn/scikit-learn) - API设计参考

---

<div align="center">

**[⬆ 回到顶部](#cumcm-coach-skill-v7)**

</div>
