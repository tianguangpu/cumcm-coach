# MCP 集成指南

本文档说明如何在国赛论文生成流程中调用已配置的 MCP 工具。

> **还没配置 MCP？** 先看 [`mcp-setup.md`](mcp-setup.md) —— 那篇讲怎么装。
> 提示：8 个 MCP 全部是**可选增强**，一个都不配也能跑通核心流程。

---

## 一、已配置的 MCP 工具

| MCP 工具 | 用途 | 调用时机 |
|---------|------|---------|
| `tavily` | 文献/行业背景检索（search/extract/research） | §0 资料检索 |
| `fetch` | 网页/数据抓取（html/json/markdown/txt） | §0 数据抓取 |
| `mcp-optimizer` | 优化问题求解（LP/MIP/NLP/背包/指派/VRP/调度/TSP） | §5 优化建模 |
| `gurddy-mcp` | 经典问题一键求解（24点/鸡兔同笼/图着色/数独/博弈/生产规划） | §5 经典问题 |
| `mcp-mathematics` | 符号推导、公式简化、统计 | §5 公式推导 |
| `numpy-mcp` | 张量/矩阵/特征值/逆矩阵 | §5 矩阵运算 |
| `matlab-mcp` | MATLAB 执行与绘图 | §5/§6 图表生成 |
| `image-reader` (GLM-4V-Plus) | 图表质量验证 | §6 自动检验 |

---

### 1.1 零依赖降级路径（MCP 全部未连接时）

所有 MCP 均为**可选增强**,任一未连接都不应阻断流程。降级映射:

| MCP | 降级方案 | 覆盖范围 |
|-----|---------|---------|
| `tavily` | `scripts/search_openalex.py`（OpenAlex 文献检索）或本地 `references/data-sources.md` 数据源 | 文献/背景检索 |
| `fetch` | Agent 直接读取本地附件/数据文件 | 数据抓取 |
| `mcp-optimizer` | `algorithms/optimization/{sa_pso,ga,de}.py` 或 `scripts/solver_router.py` | 连续/整数/非线性优化全覆盖 |
| `gurddy-mcp` | `algorithms/` 内置经典问题模块 + 手推 | 经典问题 |
| `mcp-mathematics` | Agent 用 `sympy` 现推 / 手推符号公式 | 仅影响公式推导环节 |
| `numpy-mcp` | 本地 Python(`import numpy`) | 直接可用 |
| `matlab-mcp` | Python `matplotlib` + `references/figure-specs.md` 10 技法 / `figure-skill` | 常规图与惊艳图(Python 模板)本地可生成 |
| `image-reader` | `paper-layouter check_overlaps.py` 程序化检测 + 人工复核 | 文字重叠/裁切检测,AI 读图降级为人工抽查 |

**判定规则**:调用 MCP 前先探测连接;若超时/未授权,打印 `[WARN] MCP xxx 未连接,启用降级`,切换内置路径,流程不中断。

## 二、mcp-optimizer 使用指南

### 2.1 完整API列表

| API | 功能 | 适用题型 |
|-----|------|----------|
| `solve_linear_program` | 线性规划(LP) | B/C |
| `solve_integer_program` | 整数规划(IP) | B |
| `solve_mixed_integer_program` | 混合整数规划(MIP) | B |
| `solve_knapsack_problem` | 背包问题 | B |
| `solve_transportation_problem` | 运输问题 | B |
| `solve_assignment_problem` | 指派问题 | B |
| `solve_vehicle_routing_problem` | 车辆路径(VRP) | B |
| `solve_job_shop_scheduling` | 车间调度(JSSP) | B |
| `solve_employee_shift_scheduling` | 员工排班 | B |
| `solve_traveling_salesman_problem` | TSP | B |
| `solve_portfolio_optimization` | 投资组合 | C |
| `solve_production_planning` | 生产规划 | B/C |
| `validate_optimization_input` | 输入验证 | 全部 |

### 2.2 调用示例

**示例1：线性规划**
```python
# 求解：max 3x1 + 5x2, s.t. x1≤4, x2≤8, x1+x2≤8
result = solve_linear_program(
    objective={"sense": "maximize", "coefficients": {"x1": 3, "x2": 5}},
    variables={"x1": {"type": "continuous", "lower": 0}, 
               "x2": {"type": "continuous", "lower": 0}},
    constraints=[
        {"expression": {"x1": 1}, "operator": "<=", "rhs": 4},
        {"expression": {"x2": 1}, "operator": "<=", "rhs": 8},
        {"expression": {"x1": 1, "x2": 1}, "operator": "<=", "rhs": 8}
    ]
)
# 返回：{"status": "optimal", "objective_value": 36, "variables": {"x1": 2, "x2": 6}}
```

**示例2：背包问题**
```python
result = solve_knapsack_problem(
    items=[
        {"name": "item1", "value": 10, "weight": 5},
        {"name": "item2", "value": 15, "weight": 8},
        {"name": "item3", "value": 8, "weight": 3}
    ],
    capacity=15
)
# 返回：{"total_value": 25, "selected_items": [...]}
```

**示例3：生产规划**
```python
result = solve_production_planning(
    profits={"A": 10, "B": 15},
    consumption={"A": {"machine": 2, "labor": 3}, "B": {"machine": 4, "labor": 2}},
    capacities={"machine": 100, "labor": 80}
)
# 返回：{"objective": 410.0, "values": {"A": 14, "B": 18}}
```

### 2.3 与内置算法对比

| 场景 | mcp-optimizer | 内置算法 | 推荐 |
|------|---------------|----------|------|
| 线性规划 | CBC/OR-Tools | PuLP+CBC | mcp-optimizer |
| 背包/指派 | OR-Tools | 动态规划 | mcp-optimizer |
| 连续优化 | 无 | SA-PSO/GA/DE | 内置 |
| 车间调度 | OR-Tools | JobShopScheduler | mcp-optimizer |

---

## 三、mcp-mathematics 使用指南

### 3.1 完整API列表

| API | 功能 | 示例 |
|-----|------|------|
| `calculate_expression` | 表达式计算 | `2^10 + sqrt(144)` |
| `calculate_statistics` | 统计计算 | mean/median/stdev/variance |
| `matrix_operation` | 矩阵运算 | multiply/determinant/inverse |
| `analyze_number_theory` | 数论分析 | is_prime/prime_factors/totient |
| `convert_units` | 单位换算 | 100 km/h → m/s |
| `batch_calculate` | 批量计算 | 多表达式一次求解 |
| `session_calculate` | 会话计算 | 带变量的连续计算 |
| `list_functions` | 函数目录 | 查看所有可用函数 |

### 3.2 调用示例

**示例1：统计计算**
```python
result = calculate_statistics(
    data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    operation="mean"
)
# 返回：{"result": 5.5}
```

**示例2：矩阵乘法**
```python
result = matrix_operation(
    matrices=[[[1, 2], [3, 4]], [[5, 6], [7, 8]]],
    operation="multiply"
)
# 返回：{"result": [[19, 22], [43, 50]]}
```

**示例3：数论分析**
```python
result = analyze_number_theory(number=17, operation="is_prime")
# 返回：{"is_prime": true}
```

**示例4：单位换算**
```python
result = convert_units(value=100, from_unit="km/h", to_unit="m/s", unit_type="speed")
# 返回：{"result": 27.78}
```

### 3.3 支持的函数库

| 类别 | 函数 |
|------|------|
| 基础 | cos, sin, tan, exp, log, sqrt, pow, factorial |
| 统计 | mean, median, mode, stdev, variance, quantiles |
| 复数 | ccos, csin, cexp, clog, csqrt |
| 常量 | pi, e, tau, phi(黄金比), euler |

---

## 四、matlab-mcp 使用指南

### 4.1 调用示例

```markdown
**场景**：绘制收敛曲线对比图

**调用**：
```
使用 matlab-mcp 执行绘图脚本：

% MATLAB 代码
figure('Color','w');
plot(iter, conv_sa_pso, 'b-', 'LineWidth', 2);
plot(iter, conv_ga, 'r--', 'LineWidth', 2);
xlabel('迭代次数');
ylabel('目标函数值');
legend('SA-PSO', 'GA');
print('-dpng', '-r300', 'convergence.png');
```

**输出**：
- figures/png/convergence.png (300dpi)
- figures/pdf/convergence.pdf (600dpi)
```

### 4.2 MATLAB 路径配置

在 `.claude.json` 中已配置：
```json
{
  "matlab": {
    "executable": "D:\\MatLab\\bin\\matlab.exe"
  }
}
> **路径解耦**:`executable` 通过环境变量 `MATLAB_BIN` 注入,换机请改为本机 MATLAB 实际路径,或 `set MATLAB_BIN=<path>` 后由启动脚本读取。
```

---

## 五、image-reader (GLM-4V-Plus) 使用指南

### 5.1 调用示例

```markdown
**场景**：验证图表质量

**调用**：
```
使用 image-reader (model=glm-4v-plus) 分析图表：
- 输入：figures/png/fig1.png
- 检查项：
  1. 是否有缺字乱码
  2. 文字是否被裁切
  3. 图例是否遮挡数据
  4. 配色是否清晰可辨
```

**输出**：
若发现问题，返回具体问题描述，需重新绘制。
```

### 5.2 模型选择

| 模型 | 优点 | 缺点 | 推荐场景 |
|------|------|------|---------|
| glm-4v-plus | 数值提取准确 | 收费 | 图表质量验证（推荐） |
| glm-4v-flash | 免费 | 可能捏造数值 | 仅预览查看 |

---

## 六、集成流程示例

### 6.1 优化类题目完整流程

```
1. 收到赛题 → 题型识别为 B 优化
2. §5.2 建立目标函数 → 调用 mcp-mathematics 推导
3. §5.2 设定约束条件 → 手动编写约束方程
4. §5.5 算法求解 → 调用 mcp-optimizer 执行 SA-PSO
5. §5.6 结果绘图 → 调用 matlab-mcp 生成图表
6. §6 自动检验 → 调用 image-reader 验证图表质量
7. 整合所有内容 → 输出完整 .tex 论文
```

### 6.2 MCP 调用决策树

```
需要符号推导？
  是 → mcp-mathematics
  否 ↓

需要优化求解？
  是 → mcp-optimizer
  否 ↓

需要数值计算？
  是 → numpy-mcp
  否 ↓

需要绘图？
  是 → matlab-mcp (Python 可用 figure-skill)
  否 ↓

需要验证图表？
  是 → image-reader (glm-4v-plus)
  否 → 完成
```

---

## 七、注意事项

1. **MCP 调用顺序**：
   - 先调用 `mcp-mathematics` 完成公式推导
   - 再调用 `mcp-optimizer` 进行数值求解
   - 最后调用 `matlab-mcp` 绘图

2. **错误处理**：
   - 若 MCP 调用失败，回退到手动计算
   - 记录失败原因，后续优化

3. **资源管理**：
   - 优化问题复杂时，设置合理的迭代次数上限
   - 图表验证使用 glm-4v-plus 需计费，控制调用次数

4. **与 Skill 协同**：
   - `mcp-optimizer` 配合 `algorithms/optimization/sa_pso.py` 使用
   - `matlab-mcp` 配合 `references/figure-specs.md` 中的绘图规范

---

## 八、gurddy-mcp 使用指南

### 8.1 完整API列表

| API | 功能 | 适用场景 |
|-----|------|----------|
| `solve_production_planning` | 生产规划 | B/C题资源分配 |
| `solve_graph_coloring` | 图着色 | 组合优化/调度 |
| `solve_map_coloring` | 地图着色 | 区域分配问题 |
| `solve_n_queens` | N皇后 | 约束满足问题 |
| `solve_sudoku` | 数独 | 逻辑推理 |
| `solve_minimax_game` | 博弈论 | C题决策问题 |
| `solve_minimax_decision` | 鲁棒决策 | 不确定环境决策 |
| `solve_24_point_game` | 24点游戏 | 趣味数学 |
| `solve_chicken_rabbit_problem` | 鸡兔同笼 | 经典方程组 |
| `solve_scipy_portfolio_optimization` | 投资组合 | C题金融优化 |
| `solve_scipy_facility_location` | 设施选址 | B题选址问题 |

### 8.2 调用示例

**示例1：生产规划**
```python
result = solve_production_planning(
    profits={"A": 10, "B": 15},
    consumption={"A": {"machine": 2, "labor": 3}, "B": {"machine": 4, "labor": 2}},
    capacities={"machine": 100, "labor": 80}
)
# 返回：{"objective": 410.0, "values": {"A": 14, "B": 18}}
```

**示例2：图着色**
```python
result = solve_graph_coloring(
    num_vertices=5,
    edges=[[0, 1], [0, 2], [1, 2], [1, 3], [2, 4]],
    max_colors=3
)
# 返回：{"solution": [0, 1, 2, 0, 0]}
```

**示例3：博弈论（minimax）**
```python
result = solve_minimax_game(
    payoff_matrix=[[3, -1], [1, 2]],
    player="row"
)
# 返回：{"strategy": [0.2, 0.8], "value": 1.4}
```

### 8.3 与内置算法对比

| 场景 | gurddy-mcp | 内置算法 | 推荐 |
|------|------------|----------|------|
| 生产规划 | 一键求解 | 现写LP | gurddy-mcp |
| 图着色 | OR-Tools | 现写贪心 | gurddy-mcp |
| 博弈论 | minimax | nash.py | 视复杂度 |
| 背包问题 | 无 | mcp-optimizer | mcp-optimizer |

---

## 九、numpy-mcp 使用指南

### 9.1 完整API列表

| API | 功能 | 示例 |
|-----|------|------|
| `create_matrix` | 创建矩阵 | shape=[3,3], values=[1..9] |
| `view_tensor` | 查看矩阵 | name="test_matrix" |
| `matrix_inverse` | 矩阵求逆 | name="A" |
| `determinant` | 行列式 | name="A" |
| `eigen` | 特征值/特征向量 | name="A" |
| `transpose` | 转置 | name="A" |
| `rank` | 矩阵的秩 | name="A" |
| `add_tensors` | 矩阵加法 | name_a="A", name_b="B" |
| `subtract_tensors` | 矩阵减法 | name_a="A", name_b="B" |
| `scale_tensor` | 标量乘法 | name="A", scale_factor=2 |
| `delete_tensor` | 删除矩阵 | name="A" |
| `get_tensors` | 列出所有矩阵 | 无参数 |

### 9.2 调用示例

**示例1：创建矩阵并求逆**
```python
# 创建
create_matrix(shape=[2, 2], values=[1, 2, 3, 4], name="A")

# 求逆
result = matrix_inverse(name="A")
# 返回：[[-2, 1], [1.5, -0.5]]
```

**示例2：特征值分解**
```python
result = eigen(name="A")
# 返回：{"eigenvalues": [...], "eigenvectors": [...]}
```

### 9.3 使用场景

- **§5 线性代数**：矩阵运算、特征值分析
- **§5 数据预处理**：协方差矩阵、相关系数矩阵
- **§5 模型求解**：线性方程组求解

---

## 十、tavily 使用指南

### 10.1 完整API列表

| API | 功能 | 适用场景 |
|-----|------|----------|
| `tavily_search` | 网页搜索 | §0 文献检索 |
| `tavily_extract` | 内容提取 | §0 数据抓取 |
| `tavily_crawl` | 网站爬取 | §0 深度采集 |
| `tavily_map` | 网站地图 | §0 结构分析 |
| `tavily_research` | 深度研究 | §0 综述生成 |

### 10.2 调用示例

**示例1：文献搜索**
```python
result = tavily_search(
    query="2024 mathematical modeling optimization",
    max_results=5,
    search_depth="advanced"
)
# 返回：标题+URL+摘要列表
```

**示例2：深度研究**
```python
result = tavily_research(
    input="近5年数学建模国赛A题常用算法综述",
    model="pro"
)
# 返回：结构化研究报告
```

### 10.3 v7集成点

- **§0 资料检索**：替代 `search_openalex.py`
- **§4.1b 文献综述**：配合 `gen_lit_review.py`
- **行业背景**：配合 `references/data-sources.md`

---

## 十一、MCP 路由决策树（完整版）

```
需要文献/背景检索？
  是 → tavily_search / tavily_research
  否 ↓

需要符号推导/统计/单位换算？
  是 → mcp-mathematics
  否 ↓

需要优化求解？
  ├─ 线性/整数/背包/指派/VRP/调度 → mcp-optimizer
  ├─ 生产规划/图着色/博弈 → gurddy-mcp
  └─ 连续优化(SA-PSO/GA/DE) → 内置算法
  否 ↓

需要矩阵运算？
  是 → numpy-mcp (或本地 numpy)
  否 ↓

需要绘图？
  是 → matlab-mcp / figure-skill / nature-plot-repro
  否 ↓

需要验证图表？
  是 → image-reader (glm-4v-plus)
  否 → 完成
```