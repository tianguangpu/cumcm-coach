---
name: cumcm-coach
description: >-
  全国大学生数学建模竞赛(CUMCM)建模与论文辅助工具 v7.12.0。
  核心价值:题型识别(A机理/B优化/C评价/D数据)路由到对应模板与算法 + 交卷前 L1 自动化检查(页数/AI声明/数值溯源)。
  预置算法模板库与评审脚本为可选增强。支持 LaTeX/Typst 双引擎。
  触发词:数学建模、国赛、CUMCM、优化、预测、评价、机理建模。
metadata:
  version: 7.12.0
  created: 2026-07-31
  updated: 2026-09-13
  author: tianguangpu
  license: MIT
  repository: https://github.com/tianguangpu/cumcm-coach
  supersedes: cumcm-coach-skill (v6.0.0, 已删除)
  changelog:
    - v7.12.0 (2026-09-13): **首个开源版本** — MIT 许可 + pyproject.toml 可安装包 + GitHub Actions CI(3 作业 / 3 版本矩阵) + README 英文版 + 扩展测试 41 个(覆盖率 32.9%→46.5%) + ruff 清零(626→0) + 修复 9 处缺陷(含 3 处运行时崩溃、2 处假绿色测试)
    - v7.11.0 (2026-09-01): **最新国赛要求更新 + 绘图skill全量集成** — AIGC检测自保指南 + AIGC风险自检 + 页数合规检查 + AI声明位置检查 + 五轮自审框架 + 去AI味AIGC专项 + 金标准AIGC分级 + figure-routing v2.0(6绘图skill+2排版skill完整集成+题型→图型→skill三维映射+scipilot出版级审查)
    - v7.10.0 (2026-08-28): **工程质量优化** — 烟雾测试覆盖 18→34模块(+89%) + check_paper_quality Typst支持 + baseline_compare数据加载 + solver_router内置路由(VRP/JobShop/TSP) + requirements.txt标注 + run_all集成参考文献审查
    - v7.9.0 (2026-08-27): **GitHub调研优化** — 新增基线比较/结果溯源/VRP/JobShop/TwoStage/NSGA2 + 3套Typst模板 + gen_code_manifest增强
    - v7.8.3 (2026-08-25): **最终优化** — 清理 __pycache__ + 删除模板PDF(-490KB) + 合并 solver_router;总大小 1.5MB→971KB(-35%)
    - v7.8.2 (2026-08-25): **原创算法+端到端验证** — 新增 AHO 自适应混合优化器(PSO/DE/SA融合);新增 tests/test_e2e.py
    - v7.8.1 (2026-08-25): **工程化完善** — 新增 requirements.txt + QUICKSTART.md + tests/test_algorithms.py
    - v7.8.0 (2026-08-25): **大幅精简** — SKILL.md 1210→767行(-37%);详细内容外移至references/
    - v7.7 (2026-08-24): **P0 主流程闭环** — problem_analyzer/innovation_guide/sobol/assumption_error/pso_variants/gen_lit_review 全接入
    - v7.5 (2026-08-19): **国一差距修复** — polish_abstract/check_innovation/boundary_scan/reproducibility/check_ethics
    - v7.3 (2026-08-18): **全面优化** — L1-L4四级评审+TAM+多求解器+HMML+语义锚点+双Agent
    - v7.0 (2026-07-31): **初始版本** — 题型自适应+MCP集成+算法库+自动检验
---

# cumcm-coach v7.12.0 — CUMCM 建模辅助工具

> **核心定位**:CUMCM 国赛辅助工具。真正立住的价值是两件事——①**题型识别 → 模板/算法路由**(帮新手选对方法);②**L1 自动化检查**(交卷前查页数/AI声明/数值溯源,防硬伤)。算法模板库与 L2-L4 评审为可选增强,不作"保证获奖"承诺。
> **渐进式加载**:本文档是主入口。别一次性加载全部 references(20 篇)——按当前阶段参照 [`references/README.md`](references/README.md) 的「何时加载」表按需取用。
> **v7.12.0 开源版本**:MIT 许可 + pyproject.toml 可安装包 + GitHub Actions CI(代码风格 / 测试矩阵 / wheel 构建)+ README 英文版;新增扩展测试 41 个(覆盖率 32.9%→46.5%),ruff 检查清零(626→0),修复 9 处缺陷(含 3 处运行时崩溃与 2 处"假绿色"测试)。
> **不做的**:MCM/华为/华中/APMCM 等其他赛事(交给 MathModelAgent 5writing);非国赛模板。

---

## 一、系统架构

```
赛题输入 → 询问偏好 → problem_analyzer(歧义/隐含约束确认) → 题型识别 → innovation_guide(创新方向+强基线)
              ↓                                                    ↓              ↓
        Typst/LaTeX                                            A/B/C/D      用户选择2-3方向
        Python/MATLAB                                              ↓              ↓
              ↓                                              plan/todo ← ───── 写入plan.md
              ↓                                                ↓
        阶段化执行(建模→图表→论文→L1-L4评审) → 交卷
              ↓                    ↓
        金标准内核+Sobol+       auto_check.py
        assumption_error        +PDF视觉逐页
              ↓                                                          ↓
        ai_compliance.py ←── 全程记录AI交互 ──→ 自动生成合规材料(声明+支撑PDF)
```

### 1.1 题型自动识别(关键特征)

| 题型 | 关键词特征 | 核心任务 | 推荐算法 | 模板 |
|------|-----------|---------|---------|------|
| **A 机理** | 物理、几何、轨迹、能量、扩散、传播 | 建立机理方程求解 | 数值解、拟合 | `templates/template-a.md` |
| **B 优化** | 最优、规划、调度、配置、分配 | 目标函数+约束求解 | SA-PSO、GA、DE | `templates/template-b.md` |
| **C 评价** | 评价、决策、排序、选择、指标 | 综合评价体系 | AHP+熵权+TOPSIS | `templates/template-c.md` |
| **D 数据** | 统计、预测、趋势、相关性、回归 | 数据分析预测 | TAM(首选)、ARIMA、MLP、GM(1,1) | `templates/template-d.md` |

**识别规则**:1. 扫描题目关键词(权重 0.6) 2. 看问题要求关键词(权重 0.4) 3. 得分最高题型激活对应模板。

### 1.1b 题型细分类(12 类,算法选型用)

A/B/C/D 四大类决定**论文模板**,12 细类决定**算法选型**。先定大类路由模板,再定细类选算法。

> **算法选型详细事实源**:各细类的首选方法/对照方法/消融方案以 `algorithms/hmml_index.md`(第二层)为准,本表仅作路由速览,避免多处维护不一致。

| 细类 | 信号词 | 首选算法(v7 预置) | 备选/消融对照 |
|------|-------|------------------|--------------|
| OPT 优化 | 最小成本、资源分配、选址、排班 | SA-PSO / GA / DE | 三算法互相对照 |
| EVA 评价 | 方案排序、综合效益、等级评估、指标 | AHP+熵权+TOPSIS | VIKOR / GRA |
| PRE 预测 | 时序、回归、分类、异常检测 | ARIMA / MLP / GM(1,1) | 三算法交叉验证 |
| GRA 图论 | 网络、路径、覆盖、中心性 | Dijkstra / Kruskal | 最大流 |
| PDE 机理 | 热传导、扩散、动力学、光学 | FDM 有限差分 | 现写 + mcp-mathematics |
| STA 统计 | 概率、置信、抽样、排队、蒙特卡洛 | Monte Carlo | Bootstrap |
| CLU 聚类 | 聚类、分组、降维、画像、特征 | K-Means / 层次 | GMM |
| GAM 博弈 | 博弈、策略、纳什、均衡、竞争 | Nash / 演化博弈 | Stackelberg |
| ECO 生态 | 种群、SIR、扩散、感染 | Lotka-Volterra / SEIR | 现写 |
| PHY 物理 | 几何、弹道、光学、机理 | 解析解 + FDM 验证 | 现写 |
| NLP 文本 | 文本、摘要、相似、主题 | TF-IDF + 余弦 | 现写 |
| COM 组合 | TSP、背包、调度 | DP / GA / PSO | 分支定界 |

> 其中 OPT/EVA/PRE/GRA/PDE 五类已由 `algorithms/` 预置脚本覆盖;STA 用 `validation/monte_carlo.py` + `stats/hypothesis.py`;CLU 现写;GAM 用 `game/nash.py`;ECO 用 `ecology/population.py`(LV/SIR/SEIR);PHY 用 `mechanistic/fdm_2d.py` + `ode_solver.py`;NLP/COM 依赖具体问题由 Agent 现写(调用 `mcp-mathematics` 推导)。

### 1.2 工具集成点（MCP + Skills 全量接线）

**A. MCP 集成（8 个全部接线，可选增强 + 零依赖降级）**

| 环节 | 调用 MCP | 核心API | 用途 |
|------|---------|---------|------|
| §0 资料检索 | `tavily` | search/extract/research/crawl/map | 文献/行业背景/近5年顶刊深度研究 |
| §0 数据抓取 | `fetch` | fetch_html/json/markdown/txt | 网页/数据/JSON 抓取 |
| §5 建模 | `mcp-optimizer` | solve_linear_program/integer_program/mixed_integer_program | LP/MIP/连续优化（OR-Tools/CBC） |
| §5 组合优化 | `mcp-optimizer` | solve_knapsack/assignment/transportation/vrp/job_shop/tsp | 背包/指派/运输/VRP/调度/TSP |
| §5 生产规划 | `gurddy-mcp` | solve_production_planning/graph_coloring/minimax_game | 生产规划/图着色/博弈论一键求解 |
| §5 设施选址 | `gurddy-mcp` | solve_scipy_facility_location/portfolio_optimization | 设施选址/投资组合（SciPy） |
| §5 公式推导 | `mcp-mathematics` | calculate_expression/statistics/matrix_operation/convert_units | 表达式/统计/矩阵/单位换算 |
| §5 数论分析 | `mcp-mathematics` | analyze_number_theory | 质因数/欧拉函数/素数判定 |
| §5 矩阵运算 | `numpy-mcp` | create_matrix/inverse/determinant/eigen/transpose/rank | 矩阵创建/求逆/特征值/秩 |
| §6 图表生成 | `matlab` | generate_matlab_script/execute_matlab_script | MATLAB 绘图（finish_figure 双导出） |
| §6 自检 | `image-reader` | read_image/describe_image/extract_text_image | 图表质量/文字/数值 AI 读图验证 |

> **零依赖降级**：8 个 MCP 均为可选增强，任一未连接时自动降级到内置算法/脚本（映射见 `references/mcp-integration.md` §1.1），流程不中断。
>
> **MCP路由决策**：详见 `references/mcp-integration.md` §十一 决策树。核心原则：LP/MIP/背包/指派/VRP/调度 → `mcp-optimizer`；生产规划/图着色/博弈 → `gurddy-mcp`；连续优化(SA-PSO/GA/DE) → 内置算法。

**B. Skill 集成（6 绘图 + 2 排版，全量接线）**

| 环节 | 调用 Skill | 触发词 | 核心能力 | 输出 |
|------|-----------|--------|---------|------|
| §0 出图选型 | `math-modeling-diagram-master` | "选图表"/"出图"/"流程图" | 题型→40类图型清单（fig_plan） | `fig_plan.md` |
| §3 常规数据图 | `figure-skill` | Python 出图/折线/柱状/散点/热图 | SimHei/双导出/5调色板/finish_figure | `figures/png/` + `figures/pdf/` |
| §3 惊艳高级图 | `nature-plot-repro` | "Nature同款"/弦图/桑基/雷达/泰勒/环形热图 | MATLAB 26案例复刻（只换数据不改配色） | 300dpi PNG + 矢量 PDF |
| §3 高级图兜底 | `mathmodel-figure-templates` | SHAP/山脊图/蜂群图/小提琴/UpSet | Python 11模板（替换数据出图） | `figures/png/` + `figures/pdf/` |
| §3 流程图 | `diagram-design` | "技术路线"/"架构图"/"算法流程" | 编辑级 HTML+SVG，27图型，灰度无彩色 | SVG/PNG |
| §3 出版级审查 | `scipilot-figure-skill` | "期刊投稿级"/"EDA分析"/"配图审查" | EDA剖析→选图顾问→视觉自检闭环 | 质量报告 |
| §4 排版门禁 | `math-modeling-paper-layouter` | "排版检查"/"重叠修复" | 5层门禁（重叠/编译/一致性/文献/编号） | 排版报告 |
| §4 摘要文献 | `math-modeling-abstract-polisher` | "摘要审查"/"降AI味"/"参考文献" | 4维审查（摘要/文献/AI味/进度） | 审查报告 |

**C. 调用顺序（迭代式）**：
```
diagram-master 选型 → figure-skill/nature-plot-repro 出图 → scipilot 出版级审查
                           ↓
              paper-layouter 排版门禁 ← abstract-polisher 内容审查
                           ↓
              paper-layouter 终编译（总报告）
```
- 常规图走 `figure-skill`，惊艳图走 `nature-plot-repro`，流程图走 `diagram-design`
- **数据图分工**：常规图走 figure-skill（Python），惊艳图走 nature-plot-repro（MATLAB 复刻库）
- **流程图分工**：一律走 diagram-design（编辑级 HTML+SVG，27 图型，反 AI 一坨；中文需加微软雅黑回退）
- **冲突处理**：普通→figure-skill，惊艳→nature-plot-repro 升级路线，输出统一进 `paper/figures/`

**v7.3 多求解器自动路由**(借鉴 OptimAI + OR-Tools):

| 问题类型 | 自动选择求解器 | 理由 |
|---------|--------------|------|
| 线性规划(LP) | **HiGHS** (首选) / PuLP + CBC | HiGHS 性能接近商业求解器，PuLP 作为兜底 |
| 混合整数规划(MIP) | OR-Tools CP-SAT | Google 工业级,调度/排班/背包天然适配 |
| 非线性规划(NLP) | SciPy `minimize` | 支持 SLSQP/L-BFGS-B 等多种方法 |
| 多目标优化 | PuLP + 加权法 或 NSGA-II | 视帕累托前沿需求选择 |
| 约束满足(CSP) | OR-Tools CP-SAT | 排课/数独/调度类问题 |

**路由逻辑**(`scripts/solver_router.py`):
```python
def select_solver(problem_type, has_integer_vars=False, is_nonlinear=False):
    if problem_type == "CSP" or has_integer_vars and not is_nonlinear:
        return "ortools"  # CP-SAT
    elif is_nonlinear:
        return "scipy"    # minimize
    else:
        return "pulp"     # CBC (默认)
```

---

## 二、执行流程(收到赛题后)

### 第 0 步:询问用户偏好 + 问题分析确认(新增)

**只问 2 个关键问题,不闲聊**:

1. **排版引擎**:Typst 还是 LaTeX?
   - Typst:编译快(<3s),语法简洁,适合迭代
   - LaTeX:xelatex 跑两遍,生态成熟,评委更熟悉
   - **默认 LaTeX**(评委机器普遍装的是 LaTeX)
2. **代码语言**:Python 还是 MATLAB?
   - Python:`algorithms/optimization/sa_pso.py` 等脚本直接可用
   - MATLAB:`figure-specs.md` 的 10 技法 + 5 色板完整可用
   - **默认 Python + MATLAB 双轨**(算法用 Python,绘图用 MATLAB)

记录到 `plan.md` 的"偏好"小节。

**0.2 调用 problem_analyzer.py 生成问题分析报告**(v7.7.11 新增):
```bash
python algorithms/misc/problem_analyzer.py --problem "粘贴赛题文本"
```
产出 `state/problem_analysis.json` + `reports/problem_analysis.md`,含:
- 歧义项检测(左右/约/可能等模糊词)
- 隐含约束挖掘(4领域:农业/制造/网络/经济)
- 子问题依赖图
- `needs_confirmation` 标志

**0.3 向用户展示歧义项+隐含约束+子问题依赖,等待确认**(v7.7.11 新增):
若 `needs_confirmation=True`,必须向用户展示以下关键歧义并等待回复:
- 语义模糊词汇及建议解释
- 隐性约束待确认(如"农业题是否考虑轮作硬约束?")
- 子问题拆分建议

**0.4 确认后进入第 1 步**。`problem_analysis.json` 写入 plan.md 的"问题分析"小节。

### 第 1 步:题型识别 + 生成 plan.md / todo.md

**1.1 自动识别题型**(无需用户确认,关键词加权评分)

**1.2 生成 `plan.md`**(当前工作目录):

```markdown
# 方案

用户偏好:
- 排版引擎:<Typst / LaTeX>
- 代码语言:<Python / MATLAB / 双轨>
- 题型:<A机理 / B优化 / C评价 / D数据>

workflow:
  step      产物
1. 建模与求解   - code/ + results/ + ANALYSIS_MODELING_REPORT.md
2. 图表生成     - figures/png/ + figures/pdf/ + RESULTS_REPORT.md
3. 论文撰写     - paper/main.typ 或 main.tex + sections/
4. L1-L4 四级评审  - VERIFY_REPORT.md

国赛金标准内核(每问强制):
- 六段子结构(5.X.1~5.X.6)
- 公式三段式(前置+本体+后置)
- 四重检验(拟合精度+灵敏度+MC+假设误差)
- 算法对比表(3算法⋆评级)
- 创新点分类证据(不再强制单一百分比;按模型结构/算法改进/问题分解/约束处理/验证方法分5类,每类对应证据要求+强基线对比,见 algorithms/misc/innovation_guide.py — 反作弊自检防乐观偏差/编造百分比)
```

**1.3 生成 `todo.md`**:

```markdown
# 待办事项

- [ ] 1. 建模与求解(含 MCP 调用)
- [ ] 2. 图表生成(数据图 + 概念图分工)
- [ ] 3. 论文撰写(套用模板 + 金标准内核)
- [ ] 4. L1-L4 四级评审
```

每完成一阶段更新对应 checkbox。

**1.4 调用 innovation_guide.py 生成创新方向+强基线建议**(v7.7.11 新增):
```bash
python algorithms/misc/innovation_guide.py --type <A/B/C/D>
```
产出 JSON,含:
- 5类创新点证据要求(CATEGORIES)
- 题型-specific 创新方向(DIRECTIONS,每类 5条带依据链)
- 强基线选择建议(pick_strong_baseline,替代弱贪心)
- anti_cheat_check 防编造清单

**1.5 用户从推荐方向中选择 2-3 个创新方向,写入 plan.md**:
格式:`innovations_selected: [方向 1, 方向 2, 方向 3]`,每个标注类别(模型结构/算法改进/问题分解/约束处理/验证方法)。

### 第 2 步:建模与求解(阶段 1)

**产物**:`code/`、`results/`、`reports/ANALYSIS_MODELING_REPORT.md`

**执行流程**:
1. **数据获取**:赛题附件 > 政府官网 > 专业数据库 > GitHub/Kaggle(详见 `references/data-sources.md`)
2. **建模报告**:子问题拆解→假设预检→数据理解→各子问题模型→代码任务清单→风险记录
3. **算法调用**:按 HMML 分层检索(详见 `algorithms/hmml_index.md` + `references/algorithm-interfaces.md`)
4. **求解器路由**:LP/MIP→HiGHS/PuLP, NLP→SciPy, CSP→OR-Tools(详见 `scripts/solver_router.py`)
5. **结果自证**:每个求解结果必须通过 `scripts/self_verify.py` 自证才能被论文引用
6. **四重检验**:Sobol全局灵敏度 + 假设误差(≥3项) + 蒙特卡洛(≥200次) + 拟合精度

**边界约束**:
- 不画论文用图(交给阶段 2)
- 不写论文正文(交给阶段 3)
- 所有数值结果存入 `results/`,供论文溯源

### 第 3 步:图表生成(阶段 2)

**产物**:`figures/png/`、`figures/pdf/`、`reports/RESULTS_REPORT.md`

**3.1 图型三轨分工**(吸收 MathModelAgent + v7.6 图型路由):

> **图型→工具完整路由见 [`references/figure-routing.md`](references/figure-routing.md)（单一事实源）**。此处只列大类分工;执行时按 `figure-routing.md` 决策树分流,禁止凭直觉选工具。

| 图类 | 内容 | 工具 | 数量下限 |
|------|------|------|---------|
| **常规数据图** | 折线/柱状/散点/热图/雷达/收敛/3D曲面等 | Python `figure-skill` 或 MATLAB `figure-specs.md` 10 技法 | A:12-14 / B:14-16 / C:10-12 / D:12-14 |
| **惊艳高级图** | 弦图/桑基图/泰勒图/环形热图/小提琴/UpSet/SHAP/山脊/冲积等 | **`nature-plot-repro`(MATLAB 首选) / `mathmodel-figure-templates`(Python 兜底)** | 每篇 ≥2 张(关键结论处) |
| **概念图** | 总体流程图(全局技术路线图) | **diagram-design(唯一工具,编辑级 HTML+SVG)** | **仅 1 张**(总体流程图,不额外画子流程图) |

**惊艳高级图调用要点**(详见 `figure-routing.md` §三 映射表):
- 弦图/桑基/泰勒/环形热图/小提琴/UpSet/冲积等 → 首选 `nature-plot-repro`(MATLAB 26 案例,已跑通);复制案例到 `matlab/` → 只换数据不改配色 → MATLAB MCP 运行 → 300dpi PNG+矢量 PDF
- SHAP/山脊图/蜂群图(Python 独有)或纯 Python 项目 → `mathmodel-figure-templates`(11 模板)
- 无真实关联/流转数据时**禁止硬画**弦图/桑基图凑数,反而扣分

**3.2 数据图强制规范**(继承 v6 + figure-specs.md):
- 格式:矢量 PDF 600dpi + PNG 300dpi 双导出
- 配色:5 套学术色板(Nature/Science/Qualitative/Diverging/IEEE)按图型选择
- 字号:任何元素 ≥8pt,子图编号 11pt 加粗
- 创新技法:每图从 `figure-specs.md` 10 技法中选 ≥1 个叠加,禁止裸 plot/bar
- 图题自解释:含结论+关键数值,禁"示意图"(公式:图N [对象][趋势]([关键数值]))
- 收尾:每图末尾调用 `finish_figure()`(见 `references/figure-specs.md` §九)
- 题型→技法映射:A→1+3+9, B→4+5+10, C→7+8+2, D→8+9+10

**3.3 概念图/流程图强制规范**(v7.8 简化:仅1张总体流程图,黑白灰度):

> **完整规范见 [`references/flowchart-specs.md`](references/flowchart-specs.md)** —— 灰度无彩色、标准符号。

- **数量铁律**:全文**仅 1 张总体流程图**(全局技术路线图),不额外画子流程图/算法流程/数据流水线/四重检验图
- **工具唯一**:`diagram-design`(编辑级 HTML+SVG,27图型),不用 Mermaid/draw.io/TikZ/LogicFlow
- **铁律黑白灰度无彩色**:纯白底 + 纯黑线条 + 浅灰辅助线;核心节点 #404040 白字、一般节点 #F5F5F5,**禁止任何彩色流程图**
- **符号**:圆角矩形(起止/总目标)、矩形(计算)、菱形(判断,须标是/否)、平行四边形(数据输入输出),不自创形状
- **布局**:自上而下单向、直角拐弯、无交叉;分「数据层/建模层/求解层/检验层」四分区
- **字体**:中文内容在字体栈加 `'Microsoft YaHei'` 回退,否则缺字
- **选型**:只用模板1技术路线(总体流程图),其余模板2/3/4 不再单独出图

**3.4 图表质量自动验证**(v7.7 升级为视觉自检闭环,调用 `scipilot-figure-skill` + `paper-layouter`):
1. **画图错误拦截**(scipilot §主动拦截):出图前先对图型做拦截检查,禁止——双Y轴、饼图、Y轴不当截断、小样本(n<10)画均值柱、rainbow/jet色图、把分类点连成折线。命中即按替代方案改图(均值柱→箱线+stripplot,饼图→横向柱状,rainbow→viridis/RdBu_r)
2. **机器审计**:调用 `integrations/scipilot-figure-skill/scripts/check_figure.py --strict`(程序自检缺字/裁切/刻度重叠/字号<8pt)
3. **AI 读图复核**:调用 `image-reader` (GLM-4V-Plus) 复核遮盖/子图对齐
4. **文字重叠修复**:调用 `math-modeling-paper-layouter` 的 `code/check_overlaps.py --fix --marked`(repel_text 仿 ggrepel 排斥 + shrink_overlapping 缩字号≥8pt),补齐 v7 原"只检测不修复"短板
5. **回改重渲**:任一层 FAIL → 回改 → 重渲,直到通过,记录到 `RESULTS_REPORT.md`

**3.5 RESULTS_REPORT.md 强制结构**:

```markdown
# 结果报告

## 1. 运行环境
(Python/MATLAB 版本,关键依赖)

## 2. 数据预处理
(字段说明 + 异常处理)

## 3. 各子问题结果
### 3.X 问题X
- 求解方法
- 关键数值(表格)
- 对应图表清单(figX_XXX.pdf)

## 4. 四重检验结果
- 拟合精度:R²/MAE/RMSE/MAPE
- 灵敏度:3参数±10%/±20% + 弹性系数分级
- 蒙特卡洛:≥200次 + 均值/标准差/CV/95%CI
- 假设误差量化:逐项假设偏差

## 5. 约束校验
(优化类必填:所有约束条件验证)

## 6. 复现方式
(pip install / matlab 版本 → 运行命令)
```

**3.6 自动生成 figure_manifest.json**(图表清单,供论文自动嵌入):逻辑已提取到独立脚本 `scripts/gen_figure_manifest.py`(50 行,源码头注释完整),此处不再内联。调用方式见下方「调用时机」。

**调用时机**:阶段 2 结束时自动调用:
```bash
python scripts/gen_figure_manifest.py figures state/figure_manifest.json
```

**3.7 论文自动嵌入图表**(读取 manifest,按章节插入):逻辑已提取到独立脚本 `scripts/embed_figures.py`(76 行,源码头注释完整),此处不再内联。调用方式见 §4.1b。

**3.8 阶段 2 收尾清单**(必须完成后再进入阶段 3):
- [ ] 所有图表已生成到 `figures/png/` 和 `figures/pdf/`
- [ ] 已调用 `python scripts/gen_figure_manifest.py figures state/figure_manifest.json`
- [ ] 已填写 `state/figure_manifest.json` 中每张图的 `caption` 和 `chapter`
- [ ] 已生成 `reports/RESULTS_REPORT.md`

### 第 4 步:论文撰写(阶段 3)

**产物**:`paper/main.typ` 或 `paper/main.tex` + `paper/sections/` + `paper/references`

**4.1b 生成研究现状章节**(v7.7.11 新增):
```bash
python scripts/gen_lit_review.py --type <A/B/C/D> --out reports/lit_review.tex
```
产出: `reports/lit_review.tex`(可 \input 的 LaTeX 片段)+`reports/lit_review.md`
- 复用论文既有 `\cite{refN}` 键,避免重排参考文献
- 可选 `--openalex` 增量检索(网络不可用自动回退内置模板)
- 产出直接嵌入论文 §研究现状(用 `\input{reports/lit_review.tex}` 或 `#include "reports/lit_review.typ"`) 

**4.1 排版引擎路由**(按用户偏好):

| 引擎 | 入口 | 章节 | 编译命令 | 模板源 |
|------|------|------|---------|--------|
| **LaTeX**(默认) | `paper/main.tex` | `paper/sections/*.tex` | `xelatex main.tex`(跑两遍) | `templates/template-a/b/c/d.md` + `references/figure-specs.md` LaTeX 模板 |
| **Typst** | `paper/main.typ` | `paper/sections/*.typ` | `typst compile main.typ` | 把 LaTeX 模板转译为 Typst(见 §4.4) |

**4.1b 自动嵌入图表**(阶段 3 开始时):
```bash
# 读取 manifest,自动在对应章节文件中插入图表引用
python scripts/embed_figures.py paper/sections state/figure_manifest.json <engine>
# <engine> 为 latex 或 typst,按用户偏好
```
- 脚本会自动在对应章节 `.tex` 文件末尾插入 `\begin{figure}...\end{figure}` 代码块
- 如需调整图表位置,可手动移动代码块到合适位置

**4.2 章节结构**(按题型,继承 v6):

| 题型 | 章节数 | 章节重点差异 |
|------|-------|------------|
| A 机理 | 8 章 + 附录 | §5 物理方程推导 / §5.5 数值求解方法 / §6 误差量化 |
| B 优化 | 8 章 + 附录 | §5.2 目标函数+约束 / §5.5 多算法对比 / §6 灵敏度 |
| C 评价 | 8 章 + 附录 | §5.3 评价模型构建 / §5.5 权重计算 / §6 一致性检验 |
| D 数据 | 8 章 + 附录 | §5.2 统计模型选择 / §5.5 参数优化 / §6 拟合精度+MC |

**4.3 国赛金标准内核**:详见 [`references/gold-standard.md`](references/gold-standard.md)。核心要点:
- **六段子结构**:参数配置→基础模型→缺陷剖析→创新改进→算法对比→数值结果
- **公式三段式**:前置说明+公式本体+后置拆解
- **四重检验**:拟合精度/灵敏度(Sobol)/蒙特卡洛/假设误差(≥3项)
- **算法对比表**:B题必含 pso_variants 高级部件
- **消融对比**:每问「基础方案 vs 创新方案」双方案对照
- **决策日志**:`state/decision_log.json` 全程记录变更

**4.4 Typst 引擎转译规则**:详见 [`references/typst-guide.md`](references/typst-guide.md)。核心要点:
- Typst 单次编译(非 xelatex 两遍)
- 数学语法: `$ a = b $ <eq_x>` 替代 `\begin{equation}\label{eq:x}`
- 图表: `#image("x.pdf", width: 85%)` 替代 `\includegraphics`
- 引用: `@fig_x` 替代 `\ref{fig:x}`

**4.5 图表自动嵌入论文**:读取 `state/figure_manifest.json`,调用 `scripts/embed_figures.py` 自动插入。

**4.6 边界约束**:
- 所有数值必须来自 `RESULTS_REPORT.md` 或 `results/`,**不得编造/估算**
- 不混用 Typst/LaTeX 语法
- 正文避免出现工作流内部名称(`reports/`、`figures/`、`plan.md`、`todo.md`)
- 参考文献必须真实存在,数量 ≥10,近5年 ≥40%,外文 ≥30%
- **参考文献推荐用 `thebibliography`(GB/T 7714 格式, 编译最可靠)**, 也可用 `.bib`+biber(LaTeX, 需 gb7714-2015 包)或 `.yml`+`#bibliography`(Typst); 手写或 `search_openalex.py` 生成, 模板默认 `\bibitem` 直写, auto_check 自动校验数量/近5年/外文占比

### 第 5 步:四级反馈评审(阶段 4)

**产物**:`reports/VERIFY_REPORT.md`

> **设计理念**:L1-L4 分级反馈,高层评审仅在低层全部通过后触发。
> **自审框架**:L3 前建议先执行 `references/self-review-framework.md` 五轮自审（含 AIGC 合规审查）。

```bash
python scripts/auto_check.py --paper paper/main.tex --figures figures/png/ --engine <latex|typst> --level <1|2|3|4|all>
```

**L1 自动化检查(秒级)**:编译通过/章节完整/图表路径/公式编号/占位符/参考文献/**页数合规**/**AI声明位置**
**L2 交叉验证(分钟级)**:数值一致性/图表数量/图表质量/PDF逐页/决策日志同步
**L3 对抗评审(语义级)**:机理优先/假设自洽/消融对照/在线离线边界/特征工程/误差归因/创新落地/优缺点平衡
**L4 Red-Team 终审**:语义锚点对齐/摘要正文一致性/符号一致性/跨问引用/创新量化/**AIGC风险自检**

**AIGC 合规检查(阶段 4 必做)**:
```bash
python scripts/ai_compliance.py --aigc-check --paper paper/main.tex
```
- AIGC 风险分数 < 40 → PASS
- AIGC 风险分数 ≥ 40 → 需人工改写高风险段落（详见 `references/aigc-awareness.md`）

> 任一 FAIL → 回相应阶段修复,全部 PASS → 交卷。

### 第 6 步:输出物

```text
cumcm_2026/
├── plan.md                          # 流程方案 + 用户偏好
├── todo.md                          # 待办 checklist
├── reports/                         # 阶段报告(可审计)
│   ├── ANALYSIS_MODELING_REPORT.md  # 建模分析报告
│   ├── RESULTS_REPORT.md            # 结果报告(四重检验)
│   └── VERIFY_REPORT.md             # L1-L4 四级评审验收报告
├── code/
│   ├── python/                      # Python 算法代码
│   │   ├── problem1.py
│   │   ├── problem2.py
│   │   ├── problem3.py
│   │   └── utils.py
│   └── matlab/                      # MATLAB 绘图脚本
│       ├── fig1_xxx.m
│       └── figN_xxx.m
├── figures/
│   ├── png/                         # 300dpi PNG(预览+GLM-4V验证)
│   └── pdf/                         # 600dpi 矢量 PDF(论文嵌入)
├── results/
│   ├── result1.xlsx                 # 问题一结果
│   ├── result2.xlsx
│   └── result3.xlsx
└── paper/
    ├── main.tex 或 main.typ         # 入口(按引擎)
    ├── sections/                    # 分章节
    │   ├── 1_restatement.tex/.typ
    │   ├── 2_analysis.tex/.typ
    │   ├── ...
    │   └── A_appendix.tex/.typ
    └── refs.bib                      # 参考文献(GB/T 7714 格式,biber 编译)
```

---

## 三、题型模板差异

### 3.1 图表数量与类型

| 题型 | 推荐图表数 | 核心图表类型 | 配色建议 |
|------|-----------|-------------|---------|
| A 机理 | 12-14 张 | 3D曲面、剖面图、轨迹图、等高线 | Nature/Science |
| B 优化 | 14-16 张 | 收敛曲线、可行域、布局图、对比表 | IEEE/Qualitative |
| C 评价 | 10-12 张 | 雷达图、流程图、热力图、灵敏度图 | Diverging |
| D 数据 | 12-14 张 | 时序图、分布图、相关性热力图、预测图 | Nature |

### 3.2 章节重点差异

| 章节 | A 机理 | B 优化 | C 评价 | D 数据 |
|------|-------|-------|-------|-------|
| §2 问题分析 | 机理拆解 | 优化目标识别 | 指标体系梳理 | 数据特征分析 |
| §5.2 模型建立 | **物理方程推导** | 目标函数+约束 | 评价模型构建 | 统计模型选择 |
| §5.5 算法设计 | 数值求解方法 | **多算法对比** | 权重计算方法 | 参数优化方法 |
| §6 检验 | 误差量化 | 灵敏度分析 | 一致性检验 | 拟合精度+MC |

### 3.3 模板文件位置

| 题型 | 模板文件 | 用途 |
|------|---------|------|
| A 机理 | `templates/template-a.md` | 物理建模论文骨架 |
| B 优化 | `templates/template-b.md` | 优化问题论文骨架 |
| C 评价 | `templates/template-c.md` | 评价决策论文骨架 |
| D 数据 | `templates/template-d.md` | 数据分析论文骨架 |

### 3.4 Playbook 匹配

| 题型 | 推荐 Playbook | 典型题目 |
|------|--------------|---------|
| A 机理 | `playbook-physics-ode.md` / `playbook-path-planning.md` | 2023A 定日镜 / 2024A 板凳龙 |
| B 优化 | `playbook-scheduling-opt.md` / `playbook-path-planning.md` | 2018B RGV / 2022B 无人机 |
| C 评价 | `playbook-evaluation-decision.md` / `playbook-data-insight.md` | 2020C 信贷 / 2024C 种植 |
| D 数据 | `playbook-data-insight.md` | 2023C 蔬菜定价 |

---

## 四、算法模板库(预置)

> **v7.3 新增 HMML 分层索引**:详见 `algorithms/hmml_index.md`
> 三层检索:问题类型→建模方法→代码实现,替代扁平列表遍历。

### 4.1 优化算法

| 算法 | 适用场景 | 脚本路径 |
|------|---------|---------|
| **AHO** | 多峰优化/易陷入局部最优 | `algorithms/optimization/adaptive_hybrid.py` |
| SA-PSO | 连续优化、多峰 | `algorithms/optimization/sa_pso.py` |
| GA | 连续优化(实数编码) | `algorithms/optimization/ga.py` |
| DE | 实数优化 | `algorithms/optimization/de.py` |
| Clerc 系数 PSO | 需收敛性保证 | `algorithms/optimization/pso_variants.py` |
| TVAC-PSO | 时变加速系数抗早熟 | `algorithms/optimization/pso_variants.py` |
| 可行性规则 / ε-约束 | 高级约束处理 | `algorithms/optimization/pso_variants.py` |
| PSO+局部搜索 / GA+SA | 混合算法框架 | `algorithms/optimization/pso_variants.py` |

### 4.2 预测算法

| 算法 | 适用场景 | 脚本路径 | 说明 |
|------|---------|---------|------|
| **TAM** | 时序预测(可解释,物理约束) | `algorithms/prediction/tam.py` | **D 型首选**。加法分解(趋势+季节+残差),R-style 公式,支持物理约束先验。**需 `pip install tam` 获得完整版;未装则降级为简化加法分解,论文须如实说明** |
| ARIMA | 时序预测(统计经典) | `algorithms/prediction/arima.py` | TAM 的对照算法,用于消融实验 |
| MLP | 神经网络预测(机器学习) | `algorithms/prediction/mlp.py` | 非线性关系捕捉 |
| GM(1,1) | 灰色预测(小样本) | `algorithms/prediction/gm11.py` | 数据量 <20 时使用 |

**D 数据型算法选型策略**(v7.3 更新):
1. 默认首选 **TAM**(可解释+物理约束+论文展示效果最佳)
2. 用 ARIMA + MLP + GM(1,1) 做对照消融
3. 四算法交叉验证,结果写入 `results/ablation.csv`

### 4.3 评价算法

| 算法 | 适用场景 | 脚本路径 |
|------|---------|---------|
| AHP+熵权+TOPSIS | 主客观权重+排序 | `algorithms/evaluation/ahp_entropy_topsis.py` |
| VIKOR | 多准则折中排序 | `algorithms/evaluation/vikor.py` |
| 灰色关联 GRA | 关联度分析 | `algorithms/evaluation/gra.py` |

### 4.4 图论/网络算法

| 算法 | 适用场景 | 脚本路径 |
|------|---------|---------|
| Dijkstra | 最短路/路径规划 | `algorithms/network/graph_algo.py` |
| Kruskal | 最小生成树 | `algorithms/network/graph_algo.py` |
| Edmonds-Karp | 最大流 | `algorithms/network/graph_algo.py` |

### 4.5 机理算法

| 算法 | 适用场景 | 脚本路径 |
|------|---------|---------|
| 有限差分 FDM 1D | 1D 扩散/热传导 PDE(A 题) | `algorithms/mechanistic/fdm_1d.py` |
| FDM 2D(5点) | 2D 扩散/热传导,各向异性+源项 | `algorithms/mechanistic/fdm_2d.py` |
| FEM(Poisson) | 三角形网格线性基函数 | `algorithms/mechanistic/fem_poisson.py` |
| ODE 求解器 | Euler/RK4/solve_ivp 封装 | `algorithms/mechanistic/ode_solver.py` |
| PDE 数值解法速查表 | 选法+稳定性条件 | `algorithms/mechanistic/de_quickref.py` |

> **注**:以上预置算法脚本均已实现可直接 import;6.4 假设误差量化由 `algorithms/validation/assumption_error.py` 提供 (覆盖每假设含 delta/relax_func,自动分级+生成论文段落)。

### 4.6 优化算法(高级 PSO 变体 - v7.7.11 新增)

| 算法 | 适用场景 | 脚本路径 | 强制要求 |
|------|---------|---------|---------|
| Clerc 系数 PSO | 需收敛性保证 | `algorithms/optimization/pso_variants.py` | **B 优化题必做**!至少选一个做算法对比 |
| TVAC-PSO | 时变加速系数抗早熟 | `algorithms/optimization/pso_variants.py` | 同上 |
| 可行性规则 / ε-约束 | 高级约束处理 | `algorithms/optimization/pso_variants.py` | 同上 |
| PSO+局部搜索 / GA+SA | 混合算法框架 | `algorithms/optimization/pso_variants.py` | 可选增强 |

### 4.7 博弈 / 生态 / 统计 / 全局灵敏度(2026 新增)

| 算法 | 适用场景 | 脚本路径 |
|------|---------|---------|
| 纳什均衡(纯/混合) | 2x2 博弈题 | `algorithms/game/nash.py` |
| Lotka-Volterra / SIR / SEIR | 生态/传染病 ODE | `algorithms/ecology/population.py` |
| 统计检验 | t/ANOVA/卡方/Mann-Whitney/KS | `algorithms/stats/hypothesis.py` |
| Sobol 全局灵敏度 | 参数交互+全局敏感度 | `algorithms/validation/sobol.py`(纯numpy) / `sobol_enhanced.py`(SALib优先+降级) |
| 假设误差量化 | 逐项假设影响分级 | `algorithms/validation/assumption_error.py` |

### 4.9 问题理解 / 创新引导(2026 新增)

| 模块 | 场景 | 脚本路径 |
|------|---------|---------|
| 问题分析 | 歧义/隐含约束/子问题依赖 | `algorithms/misc/problem_analyzer.py` |
| 创新引导 | 分类创新+证据+强基线 | `algorithms/misc/innovation_guide.py` |

### 4.8 外部算法库（50+ 算法）

> 详见 `algorithms/external_index.md`。由环境变量 `CUMCM_EXTERNAL_DIR` 指定路径。

---

## 五、关键约束(继承 v6.0 + v7.2 新增)

### 5.1 排版约束
- LaTeX: XeLaTeX 编译(两次);Typst: 单次编译
- 12 色学术调色板(见 `references/figure-specs.md`)
- 中文 SimHei / 英文 Times New Roman
- 公式 `\begin{equation}` 三段式(Typst 用 `$ ... $ <eq_x>`)
- 页边距:上下 2.5cm,左右 2.5cm
- 行距:1.5 倍(国赛) / 单倍(美赛)

### 5.2 内容约束(国赛金标准)
- 六段子结构完整(详见 `references/gold-standard.md`)
- 四重检验齐全(缺一降档)
- 算法对比表(B/D 题必做)
- 创新点按 5 类框架(模型结构/算法改进/问题分解/约束处理/验证方法)
- 图题含结论(非"示意图")
- 禁止裸 plot/bar(每图 ≥1 创新技法)
- 摘要三段式(背景+结果+创新,半页内)
- 参考文献 ≥10 条,近 5 年 ≥40%,外文 ≥30%

### 5.3 流程约束(v7.2 新增)
- 每阶段产出强制报告文件(ANALYSIS_MODELING/RESULTS/VERIFY)
- 数值必须从 `results/` 溯源,不得编造
- 数据图与概念图分工,不重复
- L1-L4 四级评审任何一层 FAIL 不得交卷
- 决策日志 `state/decision_log.json` 全程记录

### 5.4 AI 合规约束(2024年起国赛新规)
- 论文参考文献前必须有「AI工具使用声明」
- 支撑材料必须包含:工具名称版本、使用目的、提示方式、采纳修改情况
- 虚假声明或未审查的AI核心内容 = 取消评奖资格
- **AIGC 检测合规**:论文必须通过 AIGC 检测(AIGC 比例 < 15% 为安全)
- **AIGC 风险自检**:提交前运行 `python ai_compliance.py --aigc-check --paper paper/main.tex`
- 详见 `scripts/ai_compliance.py` + `references/aigc-awareness.md`

### 5.5 去AI味约束(新增)
- 论文初稿完成后必须对照 `references/de-ai-writing.md` 逐条自查
- 禁用「标志着/重要的/关键作用」等过度强调词
- 禁用「不仅...而且...」平行结构
- 每句话至少包含:具体数字 / 具体对比 / 因果解释
- **AIGC 检测专项**:对照 `references/de-ai-writing.md` 第六节 AIGC 检测专项
- 详见 `references/de-ai-writing.md` + `references/self-review-framework.md`

---

## 六、文件结构

> 完整代码清单见 [`references/code-inventory.md`](references/code-inventory.md) —— 由 `scripts/gen_code_manifest.py` 自动生成。**勿手改清单文件**，增删脚本/算法后重跑 `py scripts/gen_code_manifest.py` 刷新。

### 6.1 目录概览

```
cumcm-coach/ (971KB, 106个文件)
├── SKILL.md                    # 主入口(768行)
├── QUICKSTART.md               # 快速启动指南
├── requirements.txt            # 依赖清单
├── algorithms/                 # 算法库(41个文件)
├── templates/                  # 4题型模板(.tex/.md)
├── scripts/                    # 工具脚本(27个)
├── references/                 # 参考文档(22个)
│   ├── gold-standard.md        # 金标准详细规范
│   ├── typst-guide.md          # Typst转译指南
│   ├── de-ai-writing.md        # 去AI味指南
│   ├── self-review-framework.md # 四轮自审框架
│   └── playbooks/              # 5本解题手册
├── tests/                      # 单元测试(2个)
└── state/                      # 状态文件
```

### 6.2 文件统计

| 目录 | 文件数 | 大小 | 说明 |
|------|--------|------|------|
| algorithms/ | 40 | 659KB | 算法实现 |
| templates/ | 8 | 576KB | 题型模板 |
| scripts/ | 28 | 318KB | 工具脚本 |
| references/ | 20 | 155KB | 参考文档 |
| state/ | 3 | 12KB | 状态文件 |
| **总计** | **79** | **1.8MB** | |

---

## 七、启动规则(收到赛题后)

### 7.1 启动流程(11步)

1. **询问偏好**(2 个问题:排版引擎 + 代码语言,默认 LaTeX + 双轨)
2. **问题分析确认**(调用 `problem_analyzer.py` 生成歧义/隐含约束/依赖图,向用户展示并等待确认)
3. **自动识别题型**(无需用户确认,关键词加权)
4. **创新方向规划**(调用 `innovation_guide.py` 生成 5 类创新方向+强基线建议,用户选择 2-3 个方向写入 plan.md)
5. **初始化AI合规日志**(Stage 0 自动调用 `ai_compliance.py init`)
6. **生成 plan.md + todo.md**(流水线编排,含问题分析+创新方向)
7. **阶段化执行**(建模 → 图表 → 论文 → 验收,每阶段产出报告;建模阶段强制使用 Sobol+assumption_error+pso_variants)
8. **全程记录AI交互**(每次 AI 辅助后调用 `ai_compliance.py log`)
9. **AIGC 风险自检**(论文完成后运行 `ai_compliance.py --aigc-check`,AIGC 比例 < 15% 为安全)
10. **L1-L4 四级评审**(含页数合规/AI声明位置/AIGC风险自检,任何 FAIL 回阶段修复)
11. **生成合规材料**(Stage 9 自动调用 `ai_compliance.py all`)

### 7.2 快速启动命令

```bash
# 项目初始化
py scripts/init_project.py --team "202600001" --members "张三,李四,王五" --type B

# 全链流水线
py scripts/run_all.py                        # 全链运行
py scripts/run_all.py --from 07              # 从第7步断点续跑
py scripts/run_all.py --fast                 # 快速模式

# 单步执行
py scripts/auto_check.py --paper paper/main.tex --level all  # L1-L4检查
py scripts/check_verifiability.py --dir . --no-e2e   # 反假图五层溯源(图↔脚本↔数据)
py scripts/self_verify.py --type B --results results/  # 求解结果自证(反自证循环)
py scripts/search_openalex.py --query "关键词" --limit 10    # 文献检索
py scripts/ai_compliance.py all              # 生成合规材料
py scripts/ai_compliance.py --aigc-check --paper paper/main.tex  # AIGC风险自检
```

### 7.3 断点续跑

中断/误关后重开会话:
1. 读 `state/decision_log.json: current_stage`
2. 从最近 checkpoint 恢复
3. 继续执行后续阶段

### 7.4 模式切换

| 模式 | 适用场景 | 检查点 |
|------|---------|--------|
| fast | 选题试跑、快速 sanity check | 仅 Stage 0/9 |
| standard | 默认比赛流程(72h) | Stage 0→1→3→5→7→9 |
| championship | 国一冲刺 | 每个阶段结束都问 |

---

## 八、版本历史

> 完整变更记录见 SKILL.md frontmatter `changelog` 字段。以下仅列里程碑版本。

### 8.1 版本里程碑

| 版本 | 日期 | 主要更新 | 文件数 | 大小 |
|------|------|---------|--------|------|
| **v7.10.0** | 2026-08-28 | **工程质量优化** — 测试覆盖+Typst支持+数据加载+内置路由 | ~110 | ~980KB |
| **v7.9.0** | 2026-08-27 | **GitHub调研优化** — 基线比较/结果溯源/VRP/JobShop/NSGA2 + 3套Typst模板 | 191 | **2.0MB** |
| **v7.8.3** | 2026-08-25 | **最终优化** — 清理缓存+删除PDF+合并路由 | 106 | **971KB** |
| **v7.8.2** | 2026-08-25 | **原创算法+端到端验证** — AHO优化器 + E2E测试 | 111 | 1.5MB |
| **v7.7.18** | 2026-08-25 | **HiGHS 求解器** — solver_router.py | 79 |
| **v7.7.17** | 2026-08-25 | **数据驱动 Playbook** — 5本覆盖A/B/C | 78 |
| **v7.7.15** | 2026-08-25 | **SALib 增强** — sobol_enhanced.py | 77 |
| **v7.7.14** | 2026-08-25 | **去AI味+自审框架** — 2个参考文档 | 76 |
| **v7.7.12** | 2026-08-24 | **P0 主流程闭环** — 6个新模块接入 | 75 |
| **v7.7.8** | 2026-08-24 | **LaTeX 直出** — 取代HTML | 70 |
| **v7.7.7** | 2026-08-24 | **算法深度补齐** — 17个新算法文件 | 65 |
| **v7.5** | 2026-08-19 | **国一差距修复** — 5个新脚本 | 55 |
| **v7.3** | 2026-08-18 | **全面优化** — L1-L4/TAM/HMML | 45 |
| **v7.0** | 2026-07-31 | **初始版本** — 题型自适应+MCP | 30 |

---

## 九、与 MathModelAgent 的协作边界

本 skill **专做 CUMCM 国赛**。遇到以下情况建议转交 MathModelAgent:

| 场景 | 用谁 | 理由 |
|------|------|------|
| CUMCM 国赛 | **本 skill(v7.7)** | 题型识别+金标准+HMML知识库+多求解器+四级评审 国奖专精 |
| MCM/ICM/华为杯/华中杯/APMCM 等其他赛事 | MathModelAgent `5writing` | 14 赛事模板覆盖,本 skill 无对应模板 |
| 需要 17 套赛事 Typst/LaTeX 真实模板 | MathModelAgent `5writing` | 本 skill 仅国赛 4 题型 .tex 模板(已落地),无 17 套赛事模板 |
| 摘要 AI 味检测 / 72h 进度看板 | math-modeling-abstract-polisher | §2 已接 `dashboard.py` 节奏管控 |
| 文字重叠自动修复(repel_text) | math-modeling-paper-layouter | §3.4 已接 `check_overlaps.py --fix` |
| 图型→工具完整路由 | **`references/figure-routing.md`** | 三级路由(常规/惊艳/流程图)单一事实源,§3 出图前先读 |
| 出图前选型(题型→40类图型清单) | `math-modeling-diagram-master` | 第一步输出 fig_plan 选型清单,再按路由分发 |
| 常规数据图(Python) | `figure-skill` | SimHei/5调色板/finish_figure双导出 |
| 惊艳高级图(弦图/桑基/泰勒/环形热图/小提琴/UpSet/冲积等) | **`nature-plot-repro`(MATLAB 首选)** | 26 案例已跑通;无 MATLAB 时降级 `mathmodel-figure-templates` |
| SHAP/山脊图/蜂群图(Python 独有) | `mathmodel-figure-templates` | 11 模板,替换数据出图 |
| **概念图/流程图(技术路线/算法流程/四重检验)** | **`diagram-design` skill** | 编辑级 HTML+SVG,27 图型,反 AI 一坨;中文需加微软雅黑回退;需浏览器手工微调时用 `mathmodel-flowchart` |

**协作模式**:用本 skill 跑国赛主流程,关键节点叠加 MathModelAgent 专项 skill 补强。

---

## 十、新增功能概述（v7.9-v7.10）

> 详细使用示例见 [`references/v7-features-guide.md`](references/v7-features-guide.md)

| 功能 | 脚本 | 一行命令 |
|------|------|---------|
| **基线比较** | `baseline_compare.py` | `--type B --data cost.csv --advanced results/model.json` |
| **结果溯源** | `result_registry.py` | `init` → `add --id r1 --value 123 --status PASS` → `verify` |
| **论文自检** | `check_paper_quality.py` | `--paper paper/main.tex`（支持 LaTeX+Typst） |
| **求解器路由** | `solver_router.py` | `select_solver_auto("VRP", dist_matrix=..., demands=..., capacity=10)` |
| **代码清单** | `gen_code_manifest.py` | `--check-deps` / `--check-syntax` |
| **Typst 模板** | `templates/*.typ` | 7 套（国赛4+华数杯+华为杯+MCM） |
| **参考文献审查** | `check_references.py` | `--tex paper/sections/`（已集成 run_all 步骤 10b） |

**B题优化算法库**：`vrp.py`(GA/PSO) / `job_shop.py`(GA/NSGA-II/SPT/EDD) / `two_stage.py`(K-Means+VRP)

**烟雾测试覆盖**：34 个算法模块全部 PASS（v7.10 从 18 扩展到 34）
