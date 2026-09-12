# D 题数据类模板 — 统计分析 + 预测建模

> **适用场景**：数据分析、趋势预测、相关性研究、统计建模
> **核心任务**：数据探索、模型选择、预测验证、误差分析

---

## 一、章节结构（12-14 张图）

```
一、问题重述
二、问题分析（附图1：数据特征分析）
三、模型假设（含统计假设）
四、符号说明（变量三线表）
五、模型建立与求解
  5.1 数据探索性分析
  5.2 数据预处理
  5.3 基础统计模型
  5.4 改进预测模型
  5.5 参数估计与检验
  5.6 预测结果与可视化
六、模型检验（拟合精度+预测验证）
七、模型优缺点与改进
八、参考文献
附录（统计检验+代码）
```

---

## 二、核心图表清单（数据类特有）

| 图号 | 内容 | 类型 | 对应章节 |
|------|------|------|---------|
| 图1 | 数据分布概览 | 直方图+箱线组合 | §5.1 |
| 图2 | 时序趋势图 | 折线+滑动平均 | §5.1 |
| 图3 | 相关性热力图 | 矩阵+数值 | §5.1 |
| 图4 | 散点矩阵图 | pairplot | §5.1 |
| 图5 | 残差分布图 | 直方图+正态拟合 | §5.5 |
| 图6 | Q-Q 正态检验 | 散点+参考线 | §5.5 |
| 图7 | 预测值 vs 实际值 | 散点+回归线 | §5.6 |
| 图8 | 预测置信带 | 时序+CI阴影 | §5.6 |
| 图9 | 残差时序图 | 折线+0线 | §6.1 |
| 图10 | MC仿真分布 | 直方图+CDF | §6.3 |
| 图11 | 预测误差分解 | 堆叠柱状 | §6.4 |
| 图12 | 多模型对比 | 柱状+误差棒 | §6.1 |
| 图13 | 特征重要性 | 柱状排序 | §5.4 |
| 图14 | 超参数敏感性 | 曲线+最优点 | §5.5 |

---

## 三、数据探索规范

### 3.1 描述统计表

| 变量 | 均值 | 标准差 | 最小值 | 最大值 | 偏度 | 峰度 |
|------|------|-------|-------|-------|------|------|
| $x_1$ | 45.2 | 12.3 | 18.5 | 89.6 | 0.32 | 2.85 |
| $x_2$ | 128.7 | 35.6 | 62.1 | 215.3 | -0.15 | 3.12 |

### 3.2 正态性检验

```latex
Shapiro-Wilk 检验：
\begin{equation}
W = \frac{\left(\sum_{i=1}^{n} a_i x_{(i)}\right)^2}{\sum_{i=1}^{n}(x_i - \bar{x})^2}
\label{eq:shapiro}
\end{equation}

当 $p > 0.05$ 时，接受正态性假设。
```

### 3.3 相关性分析

```latex
Pearson 相关系数：
\begin{equation}
r_{xy} = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2 \sum_{i=1}^{n}(y_i - \bar{y})^2}}
\label{eq:pearson}
\end{equation}

显著性检验：$t = r\sqrt{\frac{n-2}{1-r^2}}$，服从 $t(n-2)$ 分布。
```

---

## 四、预测模型规范

### 4.1 回归模型

```latex
多元线性回归：
\begin{equation}
y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \cdots + \beta_p x_p + \varepsilon
\label{eq:mlr}
\end{equation}

参数估计（最小二乘）：
\begin{equation}
\hat{\boldsymbol{\beta}} = (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{X}^T \mathbf{y}
\label{eq:ols}
\end{equation}
```

### 4.2 时间序列模型

```latex
ARIMA(p,d,q) 模型：
\begin{equation}
\phi(B) \nabla^d y_t = \theta(B) \varepsilon_t
\label{eq:arima}
\end{equation}

其中：
\begin{align}
\phi(B) &= 1 - \phi_1 B - \cdots - \phi_p B^p \label{eq:ar}\\
\theta(B) &= 1 + \theta_1 B + \cdots + \theta_q B^q \label{eq:ma}
\end{align}
```

### 4.3 机器学习模型

```markdown
LSTM 网络结构：

输入层：n_features 维特征
LSTM 层：64 个单元，return_sequences=True
Dropout：0.2
LSTM 层：32 个单元
Dense 层：1 维输出

优化器：Adam (lr=0.001)
损失函数：MSE
```

---

## 五、模型检验规范

### 5.1 拟合精度指标

```latex
决定系数：
\begin{equation}
R^2 = 1 - \frac{\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{n}(y_i - \bar{y})^2}
\label{eq:r2}
\end{equation}

均方根误差：
\begin{equation}
RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}
\label{eq:rmse}
\end{equation}

平均绝对百分比误差：
\begin{equation}
MAPE = \frac{100}{n}\sum_{i=1}^{n}\left|\frac{y_i - \hat{y}_i}{y_i}\right|
\label{eq:mape}
\end{equation}
```

### 5.2 残差检验

```markdown
残差正态性：Shapiro-Wilk p > 0.05
残差独立性：Durbin-Watson ≈ 2
残差同方差：Breusch-Pagan p > 0.05
```

### 5.3 交叉验证

```python
# K折交叉验证
from sklearn.model_selection import KFold

kf = KFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X, y, cv=kf, scoring='r2')

# 输出
平均 R² = 0.912 (±0.023)
```

---

## 六、预测结果规范

### 6.1 置信区间

```latex
预测值的 $(1-\alpha)$ 置信区间：
\begin{equation}
\hat{y} \pm t_{\alpha/2, n-p} \cdot SE(\hat{y})
\label{eq:ci}
\end{equation}

其中 $SE(\hat{y}) = \hat{\sigma}\sqrt{\mathbf{x}_0^T (\mathbf{X}^T \mathbf{X})^{-1} \mathbf{x}_0}$。
```

### 6.2 预测对比表

| 时间 | 实际值 | 预测值 | 误差 | 95% CI |
|------|-------|-------|------|--------|
| t+1 | 52.3 | 51.8 | -0.5 | [49.2, 54.4] |
| t+2 | 54.1 | 55.2 | +1.1 | [51.8, 58.6] |
| t+3 | 56.8 | 57.5 | +0.7 | [53.2, 61.8] |

---

## 七、可视化规范

### 7.1 时序预测图（技法10）

```matlab
% 预测值 + 置信带
t = linspace(0, 12, 200);
mu = 20*sqrt(t);
lo = mu - 3*sqrt(t);
hi = mu + 3*sqrt(t);

% 渐变填充
for k=1:20
  alpha = 0.04 + 0.25*(1-k/20);
  fill([t fliplr(t)], [mu+(hi-mu)*k/20 fliplr(mu+(hi-mu)*(k-1)/20)], ...
       'FaceAlpha', alpha, 'EdgeColor', 'none');
end

plot(t, mu, '-', 'LineWidth', 2);
```

### 7.2 残差诊断图

```python
import matplotlib.pyplot as plt
from statsmodels.graphics.gofplots import qqplot

fig, axes = plt.subplots(2, 2)

# 残差时序图
axes[0,0].plot(residuals)
axes[0,0].axhline(0, color='r', linestyle='--')

# 残差直方图
axes[0,1].hist(residuals, bins=20, density=True)

# Q-Q 图
qqplot(residuals, line='s', ax=axes[1,0])

# 残差 vs 拟合值
axes[1,1].scatter(y_pred, residuals)
axes[1,1].axhline(0, color='r', linestyle='--')
```

---

## 八、MCP 调用示例

```markdown
**§5.4 预测模型构建**

调用 `numpy-mcp` 执行数据预处理：
- 标准化：z = (x - μ) / σ
- 滑动窗口：window_size = 12

调用 `mcp-optimizer` 执行超参数优化：
- 目标：min RMSE
- 参数：learning_rate, n_estimators, max_depth
- 方法：GridSearchCV

验证：调用 `mcp-mathematics` 计算置信区间
```

---

## 九、创新点提炼模板

### 9.1 预测方法创新

```
创新点1：提出 ARIMA-LSTM 混合预测模型，
线性趋势由 ARIMA 捕捉，非线性残差由 LSTM 学习，
预测精度较单一模型提升 18.5%。

创新点2：引入自适应滑动窗口特征工程，
动态调整窗口大小，模型泛化能力提升 23%。

创新点3：设计多模型集成框架，
结合 Bootstrap 和模型平均，预测稳定性提高 31%。
```

---

## 十、自检清单（数据类）

- [ ] 描述统计表存在
- [ ] 正态性检验结果存在
- [ ] 相关性热力图存在
- [ ] 回归方程三段式完整
- [ ] 拟合精度指标齐全（R²/RMSE/MAPE）
- [ ] 残差检验完整（≥3 项）
- [ ] 交叉验证结果存在
- [ ] 预测置信区间存在
- [ ] 残差诊断图（2×2）存在
- [ ] 图表数量 ≥12 张