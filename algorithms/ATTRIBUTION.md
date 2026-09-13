# 算法来源说明（Attribution）

诚实说明本算法库的实现来源，避免「看起来自研、实为包装」的误解。

**一句话结论：算法是经典算法（非原创），但实现是自研的（纯 numpy 手写，非包装现成算法库）。**

## 实现方式分类（实测扫描全部 37 个模块）

### ① 纯 numpy / pandas 自研（34 个模块）

无 scipy / pulp / sklearn / mealpy / deap / statsmodels 等算法库依赖，算法逻辑手写：

| 方向 | 模块 |
|------|------|
| 优化 | `ga.py` `de.py` `nsga2.py` `sa_pso.py` `pso_variants.py` `adaptive_hybrid.py` `vrp.py` `job_shop.py` |
| 评价 | `ahp_entropy_topsis.py` `vikor.py` `gra.py` |
| 预测 | `arima.py` `gm11.py` `mlp.py` `tam.py`（降级版）|
| 机理 | `fdm_1d.py` `fdm_2d.py` `fem_poisson.py` `ode_solver.py` |
| 验证 | `sobol.py` `sobol_enhanced.py`（降级版）`monte_carlo.py` `sensitivity.py` `assumption_error.py` `metrics.py` `shap_analysis.py` `auto_tune.py` |
| 其他 | `graph_algo.py`（Dijkstra/Kruskal/最大流）`nash.py` `bounds.py` `base.py` `problem_analyzer.py` `innovation_guide.py` |

### ② 使用 scipy 做基础科学计算（3 个模块）

scipy 是科学计算基础库，用它做 ODE 积分 / 优化 / 统计检验，**不是「包装算法」**：

- `ecology/population.py` — `scipy.integrate` 求解 Lotka-Volterra / SIR / SEIR ODE
- `optimization/two_stage.py` — `scipy.optimize` 做两阶段优化
- `stats/hypothesis.py` — `scipy.stats` 做 t / ANOVA / 卡方 / Mann-Whitney 检验

### ③ 调用外部求解器（仅 LP/MIP）

`scripts/solver_router.py` — LP/MIP 是成熟问题，调用 PuLP / HiGHS / OR-Tools 求解器（业界标准做法）。

### ④ 可选外部库增强（缺失自动降级为自研简化版）

- `tam.py` — 可选 `tam` 库；未装降级为「线性趋势 + 固定周期季节」简化分解
- `sobol_enhanced.py` — 可选 `SALib`；未装降级为纯 numpy Saltelli 实现

## 关于「原创性」的诚实边界

| 维度 | 事实 |
|------|------|
| **算法本身** | 经典算法（GA / DE / NSGA-II / AHP / TOPSIS / ARIMA / Sobol…），**非原创** |
| **实现** | 纯 numpy 手写，**自研**，非包装 mealpy / deap / statsmodels 等现成库 |
| **价值** | 统一接口 + 题型路由 + 与评审检查链路集成，而非「新算法」|

> 若你期望的是「原创算法」，本库不是；若你期望「可读、可改、可复现的算法实现 + 竞赛流程自动化」，本库是。
