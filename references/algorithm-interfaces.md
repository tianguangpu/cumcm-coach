# 算法接口速查表 v1.0 — 17 个内置算法真实接口

> **定位**：SKILL.md §2.2 只写了 `from sa_pso import SA_PSO`，但没说构造参数和返回键。本表补上**实测通过**的真实接口（逐个喂合成数据跑通验证），Agent 调用时**照抄即可，无需读源码试错**。
> **实测结论**：17 个算法接口已逐个跑通；期间**发现并修复** 2 个优化器硬伤——SA-PSO 初值误用 `obj` 致粒子群冻结、GA 紧约束纯惩罚塌缩为不可行。现已将 `repair` 可行域投影置为**约束主通道**，详见下方"约束处理黄金法则"。

---

## 一、优化算法（3 个）

> 三算法接口对齐：`obj`(目标函数) + `dim`(维度) + `bounds`(边界列表)。**注意参数名是 `bounds` 不是 `lb/ub`**。

| 算法 | 构造 | 关键参数 | `solve()` 返回键 |
|------|------|---------|-----------------|
| **SA_PSO** | `SA_PSO(obj, dim, bounds, constraints=None, repair=None, N=50, T_max=200, ...)` | `N`(粒子数) `T_max`(迭代) `T_0` `alpha` `w` `c1` `c2` | `x_opt` `f_opt` `history` `iterations` `feasible` |
| **GA** | `GA(obj, dim, bounds, constraints=None, repair=None, pop_size=50, max_gen=200, ...)` | `pop_size` `max_gen` `pc` `pm` `elite_ratio` | `x_opt` `f_opt` `history` `iterations` `feasible` |
| **DE** | `DE(obj, dim, bounds, constraints=None, repair=None, pop_size=50, max_gen=200, ...)` | `pop_size` `max_gen` `F` `CR` | `x_opt` `f_opt` `history` `iterations` `feasible` |

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

**AHP+熵权+TOPSIS 完整调用链**（`topsis()` 依赖先 `combine_weights()`，否则报 `float * None`）：
```python
from evaluation.ahp_entropy_topsis import ComprehensiveEvaluation
ce = ComprehensiveEvaluation(data, benefit_cols=[0,1,2,3], cost_cols=[])  # 指定效益/成本列索引
ce.run_ahp(pairwise_matrix)   # AHP 判断矩阵(方阵)
ce.run_entropy()              # 熵权
ce.combine_weights(alpha=0.5) # 组合权重(必须,否则 topsis 报错)
scores = ce.topsis()          # 综合得分向量
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

```python
# MonteCarlo 正确 dist 格式(踩坑: 是 'normal'/'mean'/'std' 不是 'norm'/'loc'/'scale')
from validation.monte_carlo import MonteCarlo
def sim(p): return p['mu'] + np.random.randn()
mc = MonteCarlo(sim, {'mu': {'dist': 'normal', 'mean': 0, 'std': 1}})
mc.run(n=200, seed=42); st = mc.statistics()   # st['mean'], st['std'], st['cv'], st['ci_95']
```

---

## 七、实测踩坑速查（7 个高频错误）

| 我猜错 | 正确 | 涉及 |
|--------|------|------|
| `lb`/`ub` | `bounds=[(-5,5)]*dim` | 优化 3 个 |
| `hidden`/`epochs` | `hidden_layer_sizes`/`max_iter` | MLP |
| `benefit=[True]*4` | `benefit_cols=[...]`+`cost_cols=[...]` | AHP |
| `base`/`ranges` | `base_params`/`perturbations` | Sensitivity |
| `norm`/`loc`/`scale` | `normal`/`mean`/`std` | MonteCarlo |
| `best_value` | `f_opt` | 优化 solve 返回 |
| `max_flow(...) > 0` | `total, flow = max_flow(...)` | 图论 |

---

## 八、进阶：模型深度升级路径（国一冲刺）

单周期确定性模型只是基线。要冲刺国一，按 `references/model-upgrade.md` 的阶梯升级：
**单周期凹规划 → 多周期动态规划 → 随机/鲁棒优化（MonteCarlo 场景树）→ 多目标帕累托（DE/NSGA-II）→ 机理-数据融合**。
优化器约束一律走 `repair` 可行域投影（见上文黄金法则），勿依赖纯惩罚。
