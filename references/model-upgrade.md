# 模型深度升级路径（国一冲刺）

> **定位**：本 skill 的 `run_demo_solve.py` 演示的是「单周期确定性凹规划」基线模型。国一论文通常不止于此。本文给出**逐级升级阶梯**，每级均指向 skill 内**已有**算法，避免另起炉灶。
> **约束铁律**：所有升级中，优化器一律走 `repair` 可行域投影（`references/algorithm-interfaces.md` 黄金法则），勿依赖纯惩罚项。

---

## 阶梯总览

| 层级 | 模型形态 | skill 内可用工具 | 升级收益 |
|------|---------|----------------|---------|
| L0 | 单周期确定性凹规划（基线） | `sa_pso.py` / `ga.py` + `repair` | 已可达国一框架 |
| L1 | 多周期动态规划 | 现写 DP / 滚动时域；`validation/monte_carlo.py` 做情景评估 | 刻画"今年种什么影响明年" |
| L2 | 随机/鲁棒优化 | `validation/monte_carlo.py` 场景树 + `validation/monte_carlo.py` 的 `dist_params`；`boundary_scan.py` 做鲁棒边界 | 价格/产量不确定下的稳健决策 |
| L3 | 多目标帕累托 | `optimization/de.py`（或 NSGA-II）求帕累托前沿；`solver_router.py` 多目标路由 | 净收益 vs 风险 vs 生态多目标权衡 |
| L4 | 机理-数据融合 | `mechanistic/fdm_1d.py`（机理）+ `prediction/tam.py`（数据）联合 | 物理规律与数据双驱动 |

---

## L1 多周期动态规划（最易上手）

- 把决策变量从「单年面积」扩展为「多年面积矩阵」`x[i][j][t]`（作物 i / 地块 j / 年份 t）。
- 阶段收益仍用凹二次，但**引入状态转移**：本年种植面积影响地力/轮作状态，下年约束随之变化。
- 用滚动时域（receding horizon）在 `sa_pso` / `ga` 内逐期寻优；每期用 `MonteCarlo` 抽样未来价格做期望评估。
- 论文写法：§5.4 改为「多周期凹规划」，§6.2 灵敏度改为「跨期弹性」。

## L2 随机/鲁棒优化（国一常见）

- 将单位净收益 `p_i` 建模为随机向量，用 `MonteCarlo(dist_params={'p_i': {'dist':'normal','mean':..,'std':..}})` 生成 N 个场景。
- **期望max**：目标改为 `E[Z]`，直接把 `MonteCarlo` 内循环包进 `obj`（即对场景集求平均）。
- **鲁棒max-min**：目标改为 `min_{场景} Z`，用 `boundary_scan.py` 找最差可行边界。
- 关键：`repair` 须对每个场景都可行（投影保持容量约束），否则 MonteCarlo 会吸入不可行解。

## L3 多目标帕累托（体现"权衡"深度）

- 同时优化 `Z(净收益)` 与 `R(风险=收益方差)` 或 `E(生态指标)`。
- 用 `DE`（或 NSGA-II）输出帕累托前沿，论文 §5.5 给 3-5 个代表解 + 权衡曲线。
- `solver_router.py` 的 `solve_nlp`/`solve_mip` 可接管线性化后的多目标加权。

## L4 机理-数据融合（顶配）

- 机理侧：`mechanistic/fdm_1d.py` 解作物生长偏微分方程，给出理论产量上界。
- 数据侧：`prediction/tam.py` 用历史数据标定 `p_i`、`gamma_i` 参数。
- 二者经 `validation/shap_analysis.py` 做特征重要性互验，避免数据过拟合。

---

## 落地检查清单（升级后必做）

- [ ] 每级均用 `repair` 投影，且 `res['feasible']==True` 断言通过（`test_algorithms_smoke.py` 已回归）
- [ ] 四重检验随模型层级同步加厚（多周期→跨期拟合；随机→场景覆盖度）
- [ ] 消融对比包含「少一级 vs 多一级」的量化增益（呼应 §5.6）
- [ ] 图表 ≥ 8 张，覆盖：收敛、分配、灵敏度、蒙特卡洛、帕累托前沿、跨期轨迹
