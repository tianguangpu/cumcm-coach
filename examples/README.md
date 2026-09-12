# 示例

四个可直接运行的示例，对应国赛四类题型的典型分析流程。

## 运行

无需安装即可运行（示例内部已处理 `sys.path`）：

```bash
python examples/01_optimization.py
python examples/02_evaluation.py
python examples/03_prediction.py
python examples/04_verification.py
```

生成的图片输出到 `examples/output/`（该目录已加入 `.gitignore`）。

## 示例一览

| 示例 | 对应题型 | 演示内容 | 核心接口 |
|------|---------|---------|---------|
| [`01_optimization.py`](01_optimization.py) | **B 优化** | 同一问题跑 GA / DE / Clerc-PSO，输出对比表与收敛曲线 | `GA` `DE` `pso_clerc` |
| [`02_evaluation.py`](02_evaluation.py) | **C 评价** | 熵权法 + AHP + 组合赋权 + TOPSIS 排序 | `ComprehensiveEvaluation` |
| [`03_prediction.py`](03_prediction.py) | **D 数据** | TAM 加法分解预测，含置信区间与成分分解图 | `TAM_Forecast` |
| [`04_verification.py`](04_verification.py) | **通用验证** | 局部灵敏度 + Sobol 全局灵敏度 + 假设误差量化 | `SensitivityAnalyzer` `sobol_analysis` `AssumptionChecker` |

## 关于 bounds 写法

四个优化器（GA / DE / NSGA2 / PSO 变体）接受**同一种** `bounds` 写法，
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

完整的赛题工作流（题型识别 → 建模求解 → 图表 → 论文 → 四级评审）见
[`../SKILL.md`](../SKILL.md) 与 [`../QUICKSTART.md`](../QUICKSTART.md)。
