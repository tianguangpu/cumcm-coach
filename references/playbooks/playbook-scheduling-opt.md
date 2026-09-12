# 调度/排队优化 Playbook

> 来源：Lupynow/math-modeling-skills (196★)，已获 MIT 授权。
> 题型：B 题（运筹优化/工程管理类）
> 更新：2026-08-26 新增VRP/MTVRP/车间调度/两阶段求解

## 匹配条件

- 特征词：动态调度、RGV、CNC、排队论、作业调度、物料加工、0-1 规划、启发式算法、工序分配、故障概率、蒙特卡洛模拟、等待时间、最短作业优先、FIFO、就近原则、HRRN、系统效率、班次、上下料、清洗作业、传送带、刀具分配、成料产量、**路径规划、车辆调度、中转站选址、车间调度**
- 数学本质：组合优化 + 0-1 整数规划 + NP-hard 启发式求解 + 随机模拟验证

## 典型题目索引

- 2018 国赛 B 题：智能 RGV 动态调度策略（经典调度类，含 0-1 规划 + 启发式算法 + 概率故障）
- 2022 国赛 B 题：无人机遂行编队飞行中的纯方位无源定位
- 2019 美赛 B 题：Send in the Drones（无人机救灾调度）
- **2024 电工杯 B 题**：城市垃圾分类运输的路径优化与调度（VRP + 两阶段求解）
- **2024 国赛 B 题**：生产决策优化（多目标 + 调度）

## v7.9 新增算法模块

### 1. VRP/MTVRP 求解器 (`algorithms/optimization/vrp.py`)

**适用场景**：路径规划、车辆调度、物流配送

```python
from algorithms.optimization.vrp import VRP, MTVRP

# CVRP（容量约束VRP）
vrp = VRP(distance_matrix, demands, capacity=5, n_vehicles=3)
result = vrp.solve_ga(pop_size=100, max_gen=500)
print(result['routes'], result['total_distance'])

# MTVRP（多车型VRP）
mtvrp = MTVRP(distance_matrix, demands, vehicle_types=[
    {'capacity': 5, 'cost_per_km': 2, 'count': 3},
    {'capacity': 10, 'cost_per_km': 3, 'count': 2},
])
result = mtvrp.solve_greedy()
```

**支持算法**：
- `solve_greedy_2opt()` — 贪心构造 + 2-opt改进（快速）
- `solve_ga()` — 遗传算法（精确）
- `solve_pso()` — 粒子群算法（精确）

### 2. 车间调度求解器 (`algorithms/optimization/job_shop.py`)

**适用场景**：作业车间调度、柔性车间调度、多目标调度

```python
from algorithms.optimization.job_shop import JobShopScheduler

# JSSP（作业车间调度）
jobs = [
    [(0, 3), (1, 2), (2, 2)],  # Job 0: M0-3, M1-2, M2-2
    [(1, 2), (2, 1), (0, 4)],  # Job 1: M1-2, M2-1, M0-4
]
scheduler = JobShopScheduler(jobs, due_dates=[10, 12])
result = scheduler.solve_ga(pop_size=100, max_gen=500)
print(result['makespan'], result['schedule'])

# NSGA-II 多目标优化
result = scheduler.solve_nsga2(pop_size=100, max_gen=500)
print(result['pareto_front'])  # Pareto前沿
```

**支持算法**：
- `solve_spt()` — 最短加工时间优先
- `solve_edd()` — 最早交货期优先
- `solve_ga()` — 遗传算法
- `solve_nsga2()` — NSGA-II多目标优化

### 3. 两阶段求解框架 (`algorithms/optimization/two_stage.py`)

**适用场景**：中转站选址+路径优化、设施选址+资源分配

```python
from algorithms.optimization.two_stage import TwoStageSolver

solver = TwoStageSolver(problem_type='facility_routing')
result = solver.solve(
    customers=customer_coords,
    demands=demands,
    n_clusters=5,
    capacity=20,
    verbose=True
)
print(result['stage1']['clusters'])  # 聚类结果
print(result['stage2']['routes'])    # 路径规划
print(result['total_cost'])          # 总成本
```

**问题类型**：
- `facility_routing` — 设施选址 + 路径优化
- `clustering_scheduling` — 聚类 + 调度
- `partition_assignment` — 分区 + 分配

## 解题示例（一种可行路径）

### Step 1：系统运行机制的精确刻画

调度类问题必须首先理清系统的"物理层"规则：

- **设备拓扑图**：画出系统设备布局，标注所有距离和移动时间
- **作业时间线**：对单个物料列时序 -- 上料 -> 加工 -> 下料 -> 清洗 -> 成料
- **状态机描述**：系统的"状态"有哪些变量？(RGV 位置、各 CNC 剩余加工时间、各 CNC 有无物料、RGV 手中的物料工序状态)
- **唯一性约束**：RGV 一次只能服务一台 CNC，每台 CNC 一次只能加工一个物料

### Step 2：调度规划的数学模型建立

**决策变量**：x_i^(k) -- 第 k 轮是否前往第 i 台 CNC

**目标函数**：
- 单工序：max Z = max_k w(k)
- 双工序：max Z = max_k w_ab(k)

**约束条件（共 7 类）**：
```
(1) RGV 每次只选一台：sum_i x_i^(k) = 1
(2) 总时间不超过 8 小时
(3) 移动连续性：q(k) = p(k+1)
(4) CNC 物料状态转移
(5) 等待时间计算
(6) 成料计数
(7) 双工序额外约束：工序必须匹配
```

### Step 3：启发式调度原则设计

三种经典调度原则：

**原则一：就近原则（时间代价最小）**
适用于各台 CNC 加工时间接近的场景。

**原则二：FIFO 原则（最长等待优先）**
适用于加工时间差异较大的场景。

**原则三：HRRN 原则（最高响应比优先）**
综合"等待时间"和"时间代价"两个因素的折中方案。

### Step 4：概率故障的融合处理

- **等效处理**：将故障排除时间等效为一次超长的加工作业
- **随机变量建模**：是否故障 ~ Bernoulli(0.01)，维修时长 ~ U(600, 1200)
- **多轮蒙特卡洛**：重复仿真 N 次（N >= 100），取产量均值

### Step 5：刀具/工序分配方案的搜索

- **枚举所有方案**：对所有刀具分配方案分别仿真，取产量最高的方案
- **对称性剪枝**：利用系统对称性减少计算量
- **负载均衡原则**：两道工序的加工时间之比决定了最优的 CNC 数量之比

### Step 6：模型评价与交叉验证

- **多原则对比**：比较三种调度原则的结果差异
- **理想上限计算**：将实际结果与理论上限比较
- **蒙特卡洛学习验证**：验证启发式解是否接近全局最优

## 关键陷阱

1. **RGV 移动时间的计算错误**：注意不同位置 CNC 之间的距离差异
2. **上下料时间因位置而异**：奇数号和偶数号 CNC 的上下料时间可能不同
3. **清洗时间只在下料后发生**：系统启动后前几轮不需要清洗
4. **工序匹配的"满载"限制**：RGV 手中携带半熟料时，只能前往对应工序的 CNC
5. **故障的多阶段检查**：在移动、等待、加工过程中都可能发生故障

## 完整例题：2018 B 题 -- 智能 RGV 动态调度

### 结果解读

| 组别 | 单工序产量 | 双工序产量 | 双工序最优刀具分配 | 单工序故障产量 |
|------|-----------|-----------|---------------------|----------------|
| 1 | 382 | 253 | [1,2,1,2,1,2,1,2] | 376 |
| 2 | 359 | 211 | [2,1,2,1,2,1,2,1] | 354 |
| 3 | 392 | 243 | [1,2,1,1,2,1,1,2] | 383 |

### 论文亮点
- 将 RGV 按信息处理能力分为"可预判"和"仅响应"两类模型
- 用"循环遍历法"求最优刀具分配（254 种方案全枚举）
- 同时采用三种调度原则进行对比实验
- 提出"基于蒙特卡洛的学习算法"验证启发式解是否接近全局最优
