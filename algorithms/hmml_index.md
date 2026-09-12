# HMML 分层建模知识库 (Hierarchical Mathematical Modeling Library)

> 借鉴 MM-Agent (NeurIPS 2025) 的 HMML 架构,将扁平算法列表重构为三层索引:
> **问题类型 → 建模方法 → 代码实现**
> 每层都有决策逻辑,Agent 按层检索而非遍历整个算法库。

---

## 第一层:问题类型识别

```
赛题输入
  ↓
关键词扫描(权重 0.6) + 问题要求(权重 0.4)
  ↓
大类判定: A机理 / B优化 / C评价 / D数据
  ↓
细类判定: 12 类信号词匹配
  ↓
进入第二层:建模方法选择
```

| 大类 | 细类 | 信号词 | 频率 |
|------|------|--------|------|
| A | PDE 机理 | 热传导、扩散、动力学、光学 | 高 |
| A | PHY 物理 | 几何、弹道、光学、机理 | 中 |
| B | OPT 优化 | 最小成本、资源分配、选址、排班 | 最高 |
| B | COM 组合 | TSP、背包、调度 | 高 |
| B | GRA 图论 | 网络、路径、覆盖、中心性 | 中 |
| C | EVA 评价 | 方案排序、综合效益、等级评估 | 高 |
| C | GAM 博弈 | 博弈、策略、纳什、均衡 | 低 |
| D | PRE 预测 | 时序、回归、分类、异常检测 | 最高 |
| D | STA 统计 | 概率、置信、抽样、排队 | 中 |
| D | CLU 聚类 | 聚类、分组、降维、画像 | 中 |
| D | NLP 文本 | 文本、摘要、相似、主题 | 低 |
| A/B/C/D | ECO 生态 | 种群、SIR、扩散、感染 | 低 |

---

## 第二层:建模方法选择

按细类检索,每个细类有 **首选方法 + 对照方法 + 消融方案**。

### OPT 优化

| 方法 | 适用条件 | 优势 | 劣势 | 代码 |
|------|---------|------|------|------|
| **SA-PSO** | 连续、多峰、中等规模 | 全局搜索强,收敛快 | 参数敏感 | `optimization/sa_pso.py` |
| **GA** | 连续/离散混合 | 鲁棒性好,并行友好 | 收敛慢 | `optimization/ga.py` |
| **DE** | 实数优化 | 简单高效,少参数 | 离散问题弱 | `optimization/de.py` |
| **OR-Tools CP-SAT** | 整数/调度/排班 | 工业级,超大规模 | 仅离散 | `scripts/solver_router.py` |
| **PuLP + CBC** | 线性规划 | 快速可靠 | 仅线性 | `scripts/solver_router.py` |

**消融方案**: SA-PSO vs GA vs DE → 三算法对比表

### PRE 预测

| 方法 | 适用条件 | 优势 | 劣势 | 代码 |
|------|---------|------|------|------|
| **TAM** | 时序、可解释优先 | 加法分解,物理约束 | 需 `pip install tam` 获完整版;未装则降级为简化加法分解(论文须如实说明) | `prediction/tam.py` |
| **ARIMA** | 线性时序 | 经典,统计理论完备 | 非线性弱 | `prediction/arima.py` |
| **MLP** | 非线性关系 | 灵活,可捕捉复杂模式 | 黑箱,过拟合 | `prediction/mlp.py` |
| **GM(1,1)** | 小样本(<20) | 数据需求极低 | 仅单调趋势 | `prediction/gm11.py` |

**消融方案**: TAM vs ARIMA vs MLP → 四重检验(拟合精度+灵敏度+MC+假设误差)

### EVA 评价

| 方法 | 适用条件 | 优势 | 劣势 | 代码 |
|------|---------|------|------|------|
| **AHP+熵权+TOPSIS** | 多指标综合评价 | 主客观结合,最经典 | 指标需独立 | `evaluation/ahp_entropy_topsis.py` |
| **VIKOR** | 多准则折中 | 允许补偿,输出折中解 | 参数选择主观 | `evaluation/vikor.py` |
| **GRA** | 关联度分析 | 小样本适用,计算简单 | 分辨率取值影响大 | `evaluation/gra.py` |

**消融方案**: AHP+熵权+TOPSIS vs VIKOR vs GRA

### PDE 机理

| 方法 | 适用条件 | 优势 | 劣势 | 代码 |
|------|---------|------|------|------|
| **FDM 有限差分** | 一维扩散/热传导 | 简单直观,精度可控 | 仅一维,边界处理 | `mechanistic/fdm_1d.py` |
| **mcp-mathematics** | 符号推导 | 解析解,精确 | 仅限可解析问题 | MCP 调用 |
| **现写 FEM/FVM** | 复杂几何 | 通用性最强 | 实现复杂 | Agent 现写 |

**消融方案**: FDM 数值解 vs 解析解(如有) → 精度对比

### GRA 图论

| 方法 | 适用条件 | 代码 |
|------|---------|------|
| **Dijkstra** | 最短路 | `network/graph_algo.py` |
| **Kruskal** | 最小生成树 | `network/graph_algo.py` |
| **Edmonds-Karp** | 最大流 | `network/graph_algo.py` |

### STA 统计 / CLU 聚类 / 其他

| 细类 | 首选 | 备选 | 代码来源 |
|------|------|------|---------|
| STA 统计 | Monte Carlo | Bootstrap | `validation/monte_carlo.py` |
| CLU 聚类 | K-Means | 层次聚类 / GMM | 外部库 / 现写 |
| GAM 博弈 | Nash 均衡 | 演化博弈 | 现写 + mcp-mathematics |
| ECO 生态 | Lotka-Volterra | SEIR | 现写 + mcp-mathematics |
| NLP 文本 | TF-IDF + 余弦 | LDA 主题 | 现写 |
| COM 组合 | DP / GA / PSO | 分支定界 | `optimization/` + 现写 |

---

## 第三层:代码实现

每个算法的入口函数签名统一,方便 Agent 直接调用。

### 统一接口约定

```python
# 优化类
from sa_pso import SA_PSO
result = SA_PSO(objective_func, bounds, constraints, **params)
# 返回: {"best_x", "best_f", "history", "convergence_iter"}

# 预测类
from tam import TAM_Forecast
model = TAM_Forecast(formula="y ~ trend(year) + seasonal(month, period=12)")
model.fit(df)
forecast = model.predict(steps=12)
# 返回: {"forecast", "trend", "seasonal", "ci_lower", "ci_upper"}

# 评价类
from ahp_entropy_topsis import ComprehensiveEvaluation
result = ComprehensiveEvaluation(data_matrix, weights_method="entropy+ahp")
# 返回: {"scores", "ranking", "weights", "consistency_ratio"}

# 求解器路由
from solver_router import solve_lp, solve_mip, solve_nlp, solve_csp
result = solve_lp(objective, constraints, variables, sense="minimize")
# 返回: {"status", "objective_value", "variables", "solver_used"}
```

### 外部算法库索引

> 位置: 由环境变量 `CUMCM_EXTERNAL_DIR` 指定（默认 `D:\BaiduNetdiskDownload\...\50多种常用算法源代码！（Matlab+Python）`）；未设置时用默认路径。
> 详见: `algorithms/external_index.md`
> 使用: 当内置算法不够时,从外部库按类别检索

| 类别 | 数量 | 使用频率 |
|------|------|---------|
| 优化 | 10 | 最高 |
| 预测 | 10 | 高 |
| 评价 | 8 | 高 |
| 分类 | 5 | 中 |
| 聚类 | 2 | 中 |
| 降维 | 3 | 低 |
| 图论 | 2 | 中 |
| 统计 | 6 | 中 |

---

## Agent 检索流程

```
收到赛题
  ↓
第一层:关键词 → 大类(A/B/C/D) + 细类(OPT/PRE/EVA/...)
  ↓
第二层:按细类查 HMML → 首选方法 + 对照方法 + 消融方案
  ↓
第三层:查代码实现 → 统一接口调用
  ↓
消融实验 → 对比表 → 写入 ablation.csv
  ↓
论文 §5.X.5 算法对比表直接引用 ablation.csv
```
