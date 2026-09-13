# 示例（题型 × 算法矩阵）

八个可直接运行的示例，覆盖 A/B/C/D 四类题型 × 高频算法。**装好之后不知道干嘛？从这里开始。**

## 运行

无需安装即可运行（示例内部已处理 `sys.path`）：

```bash
python examples/01_optimization.py      # B 题：算法对比
python examples/02_evaluation.py        # C 题：综合评价
python examples/03_prediction.py        # D 题：时序预测
python examples/04_verification.py      # 通用：四重检验
python examples/05_mechanism_fdm.py     # A 题：机理 FDM
python examples/06_nsga2_multiobjective.py  # B 题：多目标
python examples/07_sobol_sensitivity.py # 通用：Sobol 灵敏度
python examples/08_tam_forecast.py      # D 题：TAM 分解
```

生成的图片输出到 `examples/output/`（该目录已加入 `.gitignore`）。

## 题型 × 算法矩阵

| 题型 | 示例 | 算法 | 什么时候用 |
|------|------|------|-----------|
| **A 机理** | [`05_mechanism_fdm.py`](05_mechanism_fdm.py) | FDM 有限差分 | 物理方程（热传导/扩散/波动）数值解 |
| **B 优化** | [`01_optimization.py`](01_optimization.py) | GA / DE / Clerc-PSO | 单目标连续优化 + 算法对比 |
| **B 优化** | [`06_nsga2_multiobjective.py`](06_nsga2_multiobjective.py) | NSGA-II | 多目标（成本 vs 质量）帕累托前沿 |
| **C 评价** | [`02_evaluation.py`](02_evaluation.py) | 熵权 + AHP + TOPSIS | 综合评价排序、指标赋权 |
| **D 数据** | [`03_prediction.py`](03_prediction.py) | TAM / ARIMA / MLP | 时序预测（多算法交叉）|
| **D 数据** | [`08_tam_forecast.py`](08_tam_forecast.py) | TAM 趋势 + 季节分解 | 可解释的时序分解预测 |
| **通用** | [`04_verification.py`](04_verification.py) | 灵敏度 + 假设误差 | 四重检验（国赛硬性要求）|
| **通用** | [`07_sobol_sensitivity.py`](07_sobol_sensitivity.py) | Sobol 全局灵敏度 | 参数重要性 + 交互效应 |

## 关于 bounds 写法

优化器（GA / DE / NSGA2 / PSO 变体）接受**同一种** `bounds` 写法，
由 `algorithms/optimization/bounds.py` 统一归一化：

```python
bounds = [(-5, 5)]                    # 各变量范围相同 → 自动广播到各维
bounds = [[0, 10], [-1, 1], [-5, 5]]  # 各变量量纲不同 → 逐维给出
bounds = (-5, 5)                      # 一维写法亦可
```

行数与 `dim` 不匹配且无法广播时，会给出含修复建议的 `ValueError`。

## 关于可选依赖

以下依赖缺失时程序会自动降级，但**论文中必须如实说明**实际使用的实现：

| 依赖 | 缺失时的行为 |
|------|-------------|
| `SALib` | Sobol 分析降级为纯 numpy 实现 |
| `tam` | TAM 模型降级为「线性趋势 + 固定周期季节」简化分解 |
| `matplotlib` | 跳过绘图，仅输出数值结果 |

安装全部可选依赖：

```bash
pip install -e ".[full]"
```

## 从示例到实际赛题

把示例中的目标函数、数据矩阵或时间序列替换成你的赛题数据即可。例如示例 1：

```python
# 把 rastrigin 换成你的目标函数
def my_objective(x):
    return x[0] ** 2 + 3 * x[1] ** 2 + x[0] * x[1]

# 各变量量纲不同时逐维给出边界
BOUNDS = [[0, 100], [0, 10]]
```

完整的赛题工作流（题型识别 → 建模求解 → 图表 → 论文 → 评审）见
[`../SKILL.md`](../SKILL.md) 与 [`../docs/00_新手最小路径.md`](../docs/00_新手最小路径.md)。
