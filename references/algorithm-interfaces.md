# 算法接口速查表 v2.0 — 内置算法真实接口

> **定位**：SKILL.md §2.2 只写了 `from sa_pso import SA_PSO`，但没说构造参数和返回键。本表补上**实测通过**的真实接口（逐个喂合成数据跑通验证），Agent 调用时**照抄即可，无需读源码试错**。
> **实测结论**：17 个算法接口已逐个跑通；期间**发现并修复** 2 个优化器硬伤——SA-PSO 初值误用 `obj` 致粒子群冻结、GA 紧约束纯惩罚塌缩为不可行。现已将 `repair` 可行域投影置为**约束主通道**，详见下方"约束处理黄金法则"。

---

## 一、优化算法

> 接口对齐：`obj`(目标函数, 最小化) + `dim`(维度) + `bounds`(边界)。**参数名是 `bounds` 不是 `lb/ub`**。

**`bounds` 三种写法**（GA / DE / NSGA2 / PSO 变体均接受，由
`optimization/bounds.py::normalize_bounds` 统一归一化；行数与 `dim` 不匹配
且无法广播时会抛出含修复建议的 `ValueError`）：

```python
bounds = [(-5, 5)]                    # 各变量取值范围相同 → 自动广播到各维
bounds = [[0, 10], [-1, 1], [-5, 5]]  # 各变量量纲不同 → 逐维给出
bounds = (-5, 5)                      # 一维写法亦可
```

| 算法 | 构造 | 关键参数 | `solve()` 返回键 |
|------|------|---------|-----------------|
| **SA_PSO** | `SA_PSO(obj, dim, bounds, constraints=None, repair=None, N=50, T_max=200, ...)` | `N`(粒子数) `T_max`(迭代) `T_0` `alpha` `w` `c1` `c2` | `x_opt` `f_opt` `history` `iterations` `feasible` |
| **GA** | `GA(obj, dim, bounds, constraints=None, repair=None, pop_size=50, max_gen=200, ...)` | `pop_size` `max_gen` `pc` `pm` `elite_ratio` | `x_opt` `f_opt` `history` `iterations` `feasible` |
| **DE** | `DE(obj, dim, bounds, constraints=None, repair=None, pop_size=50, max_gen=200, ...)` | `pop_size` `max_gen` `F` `CR` | `x_opt` `f_opt` `history` `iterations` `feasible` |
| **Clerc-PSO** | `pso_clerc(obj, dim, bounds, iters=500, swarms=40, c1=2.05, c2=2.05, seed=None, repair=None)` | 函数式，无需构造 | `g_best` `g_val` `history` `variant` `chi` ⚠️**键名与上表不同** |
| **TVAC-PSO** | `pso_tvac(obj, dim, bounds, iters=500, swarms=40, seed=None, repair=None, c1_i=2.5, c1_f=0.5, ...)` | 时变加速系数，抗早熟 | `g_best` `g_val` `history` `variant` |
| **AHO** | `AdaptiveHybrid(objective, bounds, pop_size=50, max_iter=200, seed=42)` | PSO/DE/SA 三策略按种群多样性自适应切换 | `f_opt` `x_opt` `n_eval` `history` |
| **NSGA2** | `NSGA2(objs, dim, bounds, constraints=None, repair=None, pop_size=60, max_gen=200, ...)` | `objs` 是**目标函数列表**（多目标） | `f_opt` `x_opt` `pareto_F` `pareto_X` `n_pareto` `hv` `spread` `feasible` |

> ⚠️ **NSGA2 在同进程内连续实例化多个求解器时可能触发段错误**（C 扩展层问题，
> 与本项目代码无关）。建议通过 `scripts/isolated_solve.py` 的子进程隔离方式调用，
> 或单独放在一个进程里运行。`tests/test_algorithms_smoke.py` 已采用该方案。

> ⚠️ **PSO 变体的返回键是 `g_val`/`g_best`，不是 `f_opt`/`x_opt`** —— 混用会
> 在算法对比时静默取到 `None`。写对比表时统一用
> `r.get("f_opt", r.get("g_val"))` 取值。

**组合优化**（内置算法，无需外部求解器）：

| 问题 | 构造 | 求解 |
|------|------|------|
| 车辆路径 VRP | `VRP(distance_matrix, demands, capacity, n_vehicles)` | `solve_ga(...)` → `total_distance` `routes` |
| 车间调度 JobShop | `JobShopScheduler(jobs)`，`jobs=[[(机器,工时),...],...]` | `solve_ga(pop_size, max_gen)` → `makespan` `schedule` |
| 两阶段选址-路径 | `TwoStageSolver(problem_type='facility_routing')` | `solve(customers, demands, n_clusters, capacity, distance_matrix)` → `total_cost` `n_facilities` `stage1` `stage2` |

> **约束处理黄金法则（务必遵守）**：对"各分量之和≤某容量""矩阵/网络可行性"等**紧约束**，**不要只传 `constraints` 回调 + 依赖惩罚项**——惩罚在紧约束下会把搜索推到不可行角（GA 实测塌缩、SA-PSO 曾因初值冻结）。正确做法：①能用 `bounds` 表达的硬约束（如轮作禁种=上界 0）一律写进 `bounds`；②其余紧约束传入 `repair(x)` 做**可行域投影**（返回后仍满足约束的解）；③`repair` 存在时 `fitness` 只算 `obj`，惩罚项仅作辅助；④求解后用返回 `feasible` 标志断言可行性，杜绝静默输出不可行解。

```python
from optimization.sa_pso import SA_PSO
def sphere(x): return float(np.sum(np.array(x)**2))
# 紧约束示例: 两变量之和 <= 1, 用 repair 投影保证可行
def repair(x):
    x = np.array(x, float)
    return x * (1.0 / x.sum()) if x.sum() > 1.0 else x
s = SA_PSO(sphere, dim=3, bounds=[(-5,5)]*3, repair=repair, N=50, T_max=200)
r = s.solve(verbose=False)          # r['f_opt'] = 最优值, r['x_opt'] = 最优解, r['feasible'] = 是否可行
# 注意: SA_PSO 用 N/T_max, GA/DE 用 pop_size/max_gen —— 不要混用
```

---

## 二、预测算法（4 个）

| 算法 | 构造 | 关键方法 | 说明 |
|------|------|---------|------|
| **TAM**(D 型首选) | `TAM_Forecast()` | `fit(df, time_col, value_col)` → `predict(steps)` | 需 `pip install tam`，未装则降级简化加法分解(有警告) |
| **ARIMA** | `ARIMA_Forecast(series, order=(1,1,1))` | `fit()` → `predict(steps)` / `forecast(steps, alpha)` | 纯 numpy 自实现，无 statsmodels 依赖 |
| **MLP** | `MLP_Forecast(series, window=5, hidden_layer_sizes=(50,), max_iter=1000)` | `fit()` → `predict(steps)` | **参数是 `hidden_layer_sizes` 不是 `hidden`** |
| **GM(1,1)** | `GM11(x0, predict_steps=1, smooth=0)` | 直接返回预测值 | 纯函数，小样本(<20)用 |

```python
from prediction.tam import TAM_Forecast
import pandas as pd
df = pd.DataFrame({'ds': pd.date_range('2023-01-01', periods=60, freq='D'), 'y': ...})
m = TAM_Forecast(); m.fit(df, time_col='ds', value_col='y'); m.predict(steps=5)
```

---

## 三、评价算法（3 个）

| 算法 | 接口 | 调用顺序 |
|------|------|---------|
| **AHP+熵权+TOPSIS** | `ComprehensiveEvaluation(data, benefit_cols, cost_cols)` | **注意是 `benefit_cols`/`cost_cols` 两个列表**，不是 `benefit` 布尔列表 |
| **VIKOR** | `VIKOR(decision_matrix, weights, benefit, v=0.5)` | 纯函数，直接返回 |
| **灰色关联 GRA** | `grey_relational(reference, comparison, rho=0.5, normalize="init")` | 纯函数，直接返回 |

**AHP+熵权+TOPSIS 调用链**（`topsis()` 已自带权重回退，组合赋权为可选项）：
```python
from evaluation.ahp_entropy_topsis import ComprehensiveEvaluation
ce = ComprehensiveEvaluation(data, benefit_cols=[0,1,2,3], cost_cols=[])  # 指定效益/成本列索引
ce.run_ahp(pairwise_matrix)   # AHP 判断矩阵(方阵)           —— 可选
ce.run_entropy()              # 熵权（客观赋权）
ce.combine_weights(alpha=0.5) # 组合权重（主客观加权融合）    —— 可选
scores = ce.topsis()          # 综合得分向量

# 权重选取顺序：显式传入 → 组合权重 → 熵权 → AHP → 自动计算熵权。
# 只调 run_entropy() 后直接 topsis() 可用（回退到熵权并打印提示），
# 不会因未调用 combine_weights() 而报 float * None。
```

---

## 四、图论/网络（1 个文件，3 个函数）

| 函数 | 输入 | 返回 | 注意 |
|------|------|------|------|
| `dijkstra(adj, start)` | 邻接矩阵(n×n，无边填 -1 或 inf) | `(dist, prev)` **tuple** | 不是邻接表! |
| `kruskal(n, edges)` | `edges=[(u,v,w),...]` 边列表 | `(mst, total)` tuple | |
| `max_flow(capacity, source, sink)` | 容量邻接矩阵(无边填 0) | `(total, flow)` **tuple** | 需解包: `total, flow = max_flow(...)` |

---

## 五、机理（1 个）

```python
from mechanistic.fdm_1d import heat_1d_explicit
u = heat_1d_explicit(D=0.1, L=1.0, T=0.5, nx=100, nt=5000)  # 扩散系数/长度/时间/网格
```

---

## 六、检验（5 个）

| 类/函数 | 接口 | 返回键 | 注意 |
|---------|------|--------|------|
| `FitMetrics.evaluate(y_true, y_pred)` | 静态方法 | `'R2' 'MAE' 'RMSE' 'MAPE'` (**大写**) | 不是 'r2'/'rmse' |
| `SensitivityAnalyzer(model_func, base_params, perturbations=(0.1,0.2))` | `analyze()` → `elasticity_summary()` | — | **参数是 `base_params` 不是 `base`** |
| `MonteCarlo(sim_func, dist_params)` | `run(n, seed)` → `statistics()` | `'mean' 'std' 'cv' 'ci_95' 'n'` | dist 格式: `{'mu': {'dist':'normal','mean':0,'std':1}}` (**'mean'/'std' 不是 'loc'/'scale'**) |
| `AutoTuner` / `quick_cv(model, X, y, cv=5)` | `quick_cv` 最简 | — | 需 sklearn 模型 |
| `SHAPAnalyzer(model, X_train, X_test)` | **先 `fit()` 再 `get_feature_importance()`** | — | 需 `pip install shap`；不先 fit 会报 "先调 fit()" |
| `sobol_analysis(model_func, bounds, N=256, seed=42, n_boot=200, method="auto")` | 函数式 | `'S1' 'ST' 'S1_conf' 'ST_conf' 'method' 'n_eval'` | 有 SALib 走 SALib，否则降级纯 numpy；**论文须说明实际实现** |
| `AssumptionChecker(base_output, assumptions)` | `analyze()` → `paper_text()` | `'details' 'n_fatal' 'n_significant' 'max_impact_pct'` | 每条假设给 `delta` 或 `relax_func` 之一 |

```python
# MonteCarlo 正确 dist 格式(踩坑: 是 'normal'/'mean'/'std' 不是 'norm'/'loc'/'scale')
from validation.monte_carlo import MonteCarlo
def sim(p): return p['mu'] + np.random.randn()
mc = MonteCarlo(sim, {'mu': {'dist': 'normal', 'mean': 0, 'std': 1}})
mc.run(n=200, seed=42); st = mc.statistics()   # st['mean'], st['std'], st['cv'], st['ci_95']
```

---

## 七、博弈与生态

| 函数 | 接口 | 返回 | 注意 |
|------|------|------|------|
| `pure_nash(payoff_matrix)` | 2×2 收益矩阵 | `list[dict]`；**空列表表示无纯策略均衡** | 按零和博弈处理，列玩家收益取负（匹配硬币即返回 `[]`） |
| `mixed_nash_2x2(payoffA, payoffB=None)` | 2×2 收益矩阵 | `list[dict]`，`type` 为 `"pure"` / `"mixed"` | 缺省 `payoffB` 按零和；匹配硬币返回 50-50 混合 |
| `lotka_volterra / SIR / SEIR` | 见 `ecology/population.py` | 时间序列 | 纯 numpy ODE 积分，无外部依赖 |

---

## 八、实测踩坑速查（高频错误）

| 我猜错 | 正确 | 涉及 |
|--------|------|------|
| `lb`/`ub` | `bounds`：统一 `[(-5,5)]` 或逐维 `[[0,10],[-1,1]]` 均可 | 全部优化器 |
| `hidden`/`epochs` | `hidden_layer_sizes`/`max_iter` | MLP |
| `benefit=[True]*4` | `benefit_cols=[...]`+`cost_cols=[...]` | AHP |
| `base`/`ranges` | `base_params`/`perturbations` | Sensitivity |
| `norm`/`loc`/`scale` | `normal`/`mean`/`std` | MonteCarlo |
| `best_value` | `f_opt` | GA/DE/SA-PSO/AHO solve 返回 |
| 用 `f_opt` 取 PSO 变体结果 | PSO 变体是 `g_val`/`g_best` | pso_clerc/pso_tvac |
| 必须 `combine_weights()` 才能 `topsis()` | 现已自带权重回退，可不调 | AHP+TOPSIS |
| `max_flow(...) > 0` | `total, flow = max_flow(...)` | 图论 |

---

## 九、进阶：模型深度升级路径（国一冲刺）

单周期确定性模型只是基线。要冲刺国一，按 `references/model-upgrade.md` 的阶梯升级：
**单周期凹规划 → 多周期动态规划 → 随机/鲁棒优化（MonteCarlo 场景树）→ 多目标帕累托（DE/NSGA-II）→ 机理-数据融合**。
优化器约束一律走 `repair` 可行域投影（见上文黄金法则），勿依赖纯惩罚。
