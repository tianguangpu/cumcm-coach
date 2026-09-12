---
name: mathmodel-figure-templates
description: >-
  11 个 Python 高级图表模板库（国赛/期刊进阶图型）。覆盖 SHAP 特征重要性、泰勒图、
  弦图、桑基图、小提琴+蜂群图、山脊图、聚类热图、相关性气泡热图、UpSet 图、冲积图、
  Nature 多面板组合。当用户要画"Nature 图""SHAP""泰勒图"或点名上述任一图型、
  或需要 figure-skill 常规图（折线/柱状/散点/热图/雷达/收敛）覆盖不到的高级图型时调用。
  每个模板配可运行代码骨架 + 合成数据示例，替换数据即可出图。
metadata:
  version: "1.0.0"
  updated: "2026-08-16"
  changelog: "重建缺失 skill：11 模板（SHAP/泰勒/弦图/桑基/小提琴蜂群/山脊/聚类热图/相关气泡/UpSet/冲积/Nature多面板）"
---

# mathmodel-figure-templates — 11 个 Python 高级图表模板

> **核心定位：figure-skill 覆盖不到的进阶图型，用 Python 直接出图。**
> 常规图（折线/柱状/散点/常规热图/雷达/收敛）走 `figure-skill`；MATLAB 惊艳图走 `nature-plot-repro`；**本 skill = Python 版高级图模板**。

## 何时使用

- 用户点名 SHAP / 泰勒图 / 弦图 / 桑基图 / 小提琴图 / 山脊图 / 聚类热图 / 相关性气泡热图 / UpSet 图 / 冲积图 / 多面板组合图
- 用户说"Nature 同款"但**要 Python 环境**（无 MATLAB，或项目本身是 Python 栈）
- 需要机器学习可解释性（SHAP）、多模型精度对比（泰勒）、流量/关联/集合关系图

## 与相邻绘图 skill 分工（避免触发冲突）

| Skill | 引擎 | 覆盖 | 触发 |
|---|---|---|---|
| `figure-skill` | Python | 常规图（折线/柱/散点/热图/雷达/收敛/3D曲面） | 国赛常规数据图 |
| `nature-plot-repro` | MATLAB | 惊艳图 26 案例（弦/桑基/泰勒/环形热图等） | 有 MATLAB，要顶刊复刻 |
| **本 skill** | Python | 11 进阶图（弦/桑基/泰勒/SHAP/UpSet 等 Python 版） | 要 Python 高级图 |

**升级路线**：常规 → `figure-skill`；进阶 Python → 本 skill；最惊艳 + 有 MATLAB → `nature-plot-repro`。输出统一 `paper/figures/png/` + `pdf/`。

## 通用前置（复用 figure-skill 约定）

```python
import numpy as np, pandas as pd, matplotlib.pyplot as plt, matplotlib as mpl
# 中文字体 + 双导出，复用 figure-skill 的 setup_style / finish_figure / get_palette
plt.rcParams.update({'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'],
                     'axes.unicode_minus': False, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})
SEED = 42
```

## 依赖清单（按需安装，缺哪个装哪个）

```bash
pip install shap scikit-learn plotly seaborn scipy upsetplot
# 可选：joypy（山脊图另一实现）、matplotlib-chord（弦图备选）
```

## 11 模板速查表

| # | 模板 | 图型 | 核心库 | 适用题型/场景 |
|---|---|---|---|---|
| 1 | SHAP | 特征重要性/汇总/依赖图 | `shap` + sklearn | C/D 数据题特征归因 |
| 2 | 泰勒图 | 多模型精度对比 | matplotlib 自实现 | 预测模型择优 |
| 3 | 弦图 | 节点关联/流向 | matplotlib 自实现 | D 关联关系 |
| 4 | 桑基图 | 流量/能量/物料流 | `plotly` | B 调度/D 网络流量 |
| 5 | 小提琴+蜂群 | 多组分布 + 单点 | `seaborn` | 统计/分组对比 |
| 6 | 山脊图 | 多组分布重叠演化 | seaborn/手动 | 时序分布演化 |
| 7 | 聚类热图 | 聚类结构 + 树状图 | `seaborn` + scipy | 特征/样本聚类 |
| 8 | 相关性气泡热图 | 相关 + 显著性气泡 | matplotlib 自实现 | C 特征筛选 |
| 9 | UpSet 图 | 集合交集 | `upsetplot` | 多集合重叠 |
| 10 | 冲积图 | 多阶段分类流向 | `plotly` | 阶段/分类变化 |
| 11 | Nature 多面板 | 一图多论点组合 | matplotlib + layout | 综述性 Figure 1 |

---

## 模板 1：SHAP 特征重要性

**用途**：机器学习模型（RF/XGB）特征归因，评委看"模型为什么这么判"。
**依赖**：`shap`, `scikit-learn`。

```python
import shap
from sklearn.ensemble import RandomForestRegressor

# 训练模型
rng = np.random.default_rng(SEED)
X = pd.DataFrame(rng.normal(0, 1, (500, 6)), columns=[f'x{i}' for i in range(1, 7)])
y = 3*X['x1'] - 2*X['x2'] + 0.5*X['x3'] + rng.normal(0, 0.3, 500)
rf = RandomForestRegressor(n_estimators=200, random_state=SEED).fit(X, y)

# SHAP 汇总图（蜂群散点：每个样本每个特征一个点，颜色=特征取值高低）
explainer = shap.TreeExplainer(rf)
shap_values = explainer.shap_values(X.sample(200, random_state=SEED))
fig = plt.figure(figsize=(9, 6))
shap.summary_plot(shap_values, X.sample(200, random_state=SEED), show=False, max_display=12)
plt.title('图N SHAP 特征重要性：x1 正向贡献最大', fontsize=13, fontweight='bold')
finish_figure(fig, 'fig_shap_summary', 'figures')
```

**无 shap 时降级 PFI**（复用 D2019 项目的处理）：
```python
try:
    import shap; HAS_SHAP = True
except ImportError:
    HAS_SHAP = False  # 用 permutation_importance 替代
    from sklearn.inspection import permutation_importance
```

---

## 模板 2：泰勒图（多模型精度对比）

**用途**：一张图同时看相关系数（角度）+ 标准差（半径）+ RMSE（离参考点距离），多模型精度对比首选。
**依赖**：matplotlib + numpy（自实现，无需额外库）。

```python
def taylor_diagram(std_ref, stats, labels, colors, title=''):
    """stats: list of {corr, std, rmse}；std_ref: 观测标准差"""
    fig = plt.figure(figsize=(7.5, 7.5))
    ax = fig.add_subplot(111, projection='polar')
    ax.set_theta_direction(-1); ax.set_theta_zero_location('N')
    # 相关系数弧线（角度 = arccos(r)）
    for r in [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.99]:
        th = np.arccos(r)
        ax.plot([th]*200, np.linspace(0, 2*std_ref, 200), color='0.75', lw=0.6, zorder=1)
        ax.text(th, 2*std_ref*1.04, f'{r}', ha='center', fontsize=8, color='0.5')
    # 标准差网格 + 参考点
    ax.set_rmax(2*std_ref); ax.set_rticks([0.5*std_ref, std_ref, 1.5*std_ref, 2*std_ref])
    ax.scatter(0, std_ref, marker='*', s=260, color='k', zorder=6, label='观测(参考)')
    # 各模型点：角度=arccos(corr)，半径=std
    for s, lab, c in zip(stats, labels, colors):
        ax.scatter(np.arccos(np.clip(s['corr'], -1, 1)), s['std'], s=90, color=c,
                   zorder=7, edgecolors='white', linewidths=1, label=lab)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.15), frameon=False)
    ax.set_title(title, pad=25, fontsize=13, fontweight='bold')
    return fig

# 用法示例
fig = taylor_diagram(std_ref=1.0,
    stats=[{'corr': 0.92, 'std': 0.95, 'rmse': 0.38},
           {'corr': 0.85, 'std': 1.10, 'rmse': 0.52},
           {'corr': 0.78, 'std': 0.70, 'rmse': 0.61}],
    labels=['模型A', '模型B', '模型C'],
    colors=['#4C72B0', '#DD8452', '#55A868'],
    title='图N 泰勒图：模型A精度最优（r=0.92，离参考最近）')
finish_figure(fig, 'fig_taylor', 'figures')
```

---

## 模板 3：弦图（关联/流向）

**用途**：多节点间两两关联强度/流量。**核心原理**：圆周按总流量分配弧段，节点间画贝塞尔弦（控制点在圆心）。
**依赖**：matplotlib + numpy（自实现）。完整精确版可参考 `nature-plot-repro` 的 `chordChart.m` 思路。

```python
def chord_diagram(M, names, colors, title=''):
    """M: n×n 流量矩阵，M[i,j] = i→j 的流量"""
    n = len(names); R = 1.0
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect='equal'))
    out = M.sum(axis=1); tot = out.sum()
    # 每个源在圆周上的弧段起止角
    starts, a = [], 0.0
    for i in range(n):
        starts.append(a); a += out[i]/tot*2*np.pi
    # 弦（三次贝塞尔，两端在弧段内按流量比例分布，控制点指向圆心）
    cum = np.cumsum(M, axis=1)
    for i in range(n):
        for j in range(n):
            if M[i, j] <= 0: continue
            a0 = starts[i] + (cum[i, j]-M[i, j])/out[i]*2*np.pi
            a1 = starts[i] + cum[i, j]/out[i]*2*np.pi
            b0 = starts[j] + (cum[j, i]-M[j, i])/out[j]*2*np.pi
            b1 = starts[j] + cum[j, i]/out[j]*2*np.pi
            # 简化：用弧段中点连弦（精确版按比例细分）
            t = np.linspace(0, 1, 80)
            p0 = np.array([np.cos(a0), np.sin(a0)]); p3 = np.array([np.cos(b0), np.sin(b0)])
            ctrl = p0*0.0  # 控制点取圆心 → 弦向内弯曲
            bez = ((1-t)**3)[:, None]*p0 + (3*(1-t)**2*t)[:, None]*ctrl + \
                  (3*(1-t)*t**2)[:, None]*ctrl + (t**3)[:, None]*p3
            ax.plot(bez[:, 0], bez[:, 1], color=colors[i], alpha=0.35, lw=M[i, j]/M.max()*8)
    # 外环弧段 + 标签
    for i in range(n):
        th = np.linspace(starts[i], starts[i]+out[i]/tot*2*np.pi, 100)
        ax.plot(np.cos(th), np.sin(th), lw=14, color=colors[i], solid_capstyle='round')
        mid = starts[i] + out[i]/tot*np.pi
        ax.text(np.cos(mid)*1.18, np.sin(mid)*1.18, names[i], ha='center', va='center', fontsize=11, fontweight='bold')
    ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4); ax.axis('off'); ax.set_title(title, pad=15, fontsize=13, fontweight='bold')
    return fig
```

---

## 模板 4：桑基图（流量/能量/物料流）

**用途**：多级流量分配、能量转换、物料平衡。**依赖**：`plotly`（几行即出）。

```python
import plotly.graph_objects as go

def sankey(nodes, links, title=''):
    """nodes: list[str]；links: list of {source, target, value}（下标索引）"""
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=15, thickness=20,
                  color=['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B3']),
        link=dict(source=[l['source'] for l in links],
                  target=[l['target'] for l in links],
                  value=[l['value'] for l in links],
                  color='rgba(76,114,176,0.3)')))
    fig.update_layout(title_text=title, font_size=12)
    fig.write_image('figures/fig_sankey.png', width=1200, height=700, scale=3)
    return fig
```

---

## 模板 5：小提琴 + 蜂群图

**用途**：多组分布形态 + 每个样本点，比均值柱更可信（呼应 scipilot 的 P1 拦截）。
**依赖**：`seaborn`。

```python
import seaborn as sns
rng = np.random.default_rng(SEED)
df = pd.DataFrame({'group': np.repeat(['A', 'B', 'C'], 30),
                   'value': np.concatenate([rng.normal(1, 1, 30), rng.normal(2, 1.5, 30), rng.normal(3, 0.8, 30)])})
fig, ax = plt.subplots(figsize=(7, 5))
sns.violinplot(data=df, x='group', y='value', inner=None, palette='colorblind', linewidth=1, ax=ax)
sns.stripplot(data=df, x='group', y='value', color='black', size=3, alpha=0.5, ax=ax)
ax.set_xlabel(''); ax.set_ylabel('指标值')
ax.set_title('图N 三组分布对比：C 组集中且偏高', fontsize=13, fontweight='bold')
finish_figure(fig, 'fig_violin_swarm', 'figures')
```

---

## 模板 6：山脊图（多组分布重叠）

**用途**：多组/多时段分布演化（如逐年指标分布漂移）。
**依赖**：seaborn（0.12+ FacetGrid）或手动画 offset KDE。

```python
import seaborn as sns
rng = np.random.default_rng(SEED)
groups = [f'{y}年' for y in range(2018, 2024)]
data = []
for i, g in enumerate(groups):
    data.extend([(g, v) for v in rng.normal(i, 1 + 0.2*i, 200)])
df = pd.DataFrame(data, columns=['group', 'value'])

# seaborn 手动 offset 山脊
fig, ax = plt.subplots(figsize=(8, 6))
for i, g in enumerate(groups):
    sub = df[df.group == g]['value']
    sns.kdeplot(sub, y=g, fill=True, alpha=0.5, linewidth=1.2, ax=ax)
ax.set_ylabel(''); ax.set_xlabel('指标值')
ax.set_title('图N 2018–2023 指标分布逐年右移', fontsize=13, fontweight='bold')
finish_figure(fig, 'fig_ridgeline', 'figures')
```

---

## 模板 7：聚类热图（聚类结构 + 树状图）

**用途**：特征/样本聚类，行列自动重排 + 树状图，一眼看出分组结构。
**依赖**：`seaborn` + `scipy`。

```python
import seaborn as sns
from scipy.cluster.hierarchy import linkage
rng = np.random.default_rng(SEED)
X = pd.DataFrame(rng.normal(0, 1, (40, 8)), columns=[f'f{i}' for i in range(1, 9)])
# 人为制造两组相关结构
X['f5'] = X['f1']*0.8 + rng.normal(0, 0.3, 40)
X['f6'] = X['f2']*0.7 + rng.normal(0, 0.3, 40)
g = sns.clustermap(X.corr(), cmap='RdBu_r', vmin=-1, vmax=1, center=0,
                   annot=True, fmt='.2f', figsize=(8, 7), method='average')
g.ax_heatmap.set_title('图N 特征聚类热图：f1/f5、f2/f6 聚为一组', pad=60)
g.savefig('figures/fig_clustermap.png', dpi=300, bbox_inches='tight')
```

---

## 模板 8：相关性气泡热图

**用途**：相关系数矩阵，气泡大小=|r|、颜色=正负、显著性用空心/实心，信息密度高于普通热图。
**依赖**：matplotlib + pandas + numpy（自实现）。

```python
def corr_bubble(df, title=''):
    C = df.corr()
    n = len(C.columns)
    fig, ax = plt.subplots(figsize=(8, 7))
    for i in range(n):
        for j in range(n):
            r = C.iloc[i, j]
            color = '#C44E52' if r > 0 else '#4C72B0'
            ax.scatter(j, i, s=abs(r)*800, color=color, alpha=0.75, zorder=3)
            if i == j: r = 1.0
            ax.text(j, i, f'{r:.2f}', ha='center', va='center', fontsize=9,
                    color='white' if abs(r) > 0.6 else 'black', zorder=4, fontweight='bold')
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(C.columns); ax.set_yticklabels(C.columns)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    ax.grid(False); ax.set_aspect('equal')
    return fig
```

---

## 模板 9：UpSet 图（集合交集）

**用途**：多集合（多分类标签）重叠关系，替代维恩图（集合 > 5 时维恩图不可读）。
**依赖**：`upsetplot`（`pip install upsetplot`）。

```python
from upsetplot import UpSet, from_indicators
# 布尔 DataFrame：每列一个集合，每行一个元素，True=属于该集合
rng = np.random.default_rng(SEED)
ind = pd.DataFrame({c: rng.random(300) < p for c, p in
                    zip(['集合A', '集合B', '集合C', '集合D'], [0.5, 0.4, 0.35, 0.3])})
upset = UpSet(from_indicators(ind.columns, data=ind), subset_size='count',
              show_counts='%d', sort_by='cardinality')
upset.plot()
plt.suptitle('图N 四集合交集分布', fontsize=13, fontweight='bold')
plt.savefig('figures/fig_upset.png', dpi=300, bbox_inches='tight')
```

---

## 模板 10：冲积图（多阶段分类流向）

**用途**：多个离散阶段的分类变化（如不同时期类别迁移、分层下钻）。
**依赖**：`plotly`（用 Sankey 的 alluvial 语义）。

```python
import plotly.graph_objects as go
# 阶段1→阶段2→阶段3，每个阶段一个分类集
nodes = ['A1', 'A2', 'B1', 'B2', 'B3', 'C1', 'C2']
links = [
    {'source': 0, 'target': 2, 'value': 40},
    {'source': 0, 'target': 3, 'value': 30},
    {'source': 1, 'target': 3, 'value': 20},
    {'source': 1, 'target': 4, 'value': 10},
    {'source': 2, 'target': 5, 'value': 35},
    {'source': 3, 'target': 5, 'value': 20},
    {'source': 3, 'target': 6, 'value': 30},
    {'source': 4, 'target': 6, 'value': 15},
]
fig = go.Figure(go.Sankey(
    node=dict(label=nodes, pad=15, thickness=20, x=[0, 0, 0.5, 0.5, 0.5, 1, 1]),
    link=dict(source=[l['source'] for l in links], target=[l['target'] for l in links],
              value=[l['value'] for l in links], color='rgba(76,114,176,0.25)')))
fig.update_layout(title_text='图N 三阶段分类流向', font_size=12)
fig.write_image('figures/fig_alluvial.png', width=1000, height=600, scale=3)
```

---

## 模板 11：Nature 多面板组合图

**用途**：一图多论点的综述性 Figure 1（PCA / loss / 混淆矩阵 / 分布等），统一字号配色 + 面板编号 a/b/c。
**依赖**：matplotlib + scipilot 的 `layout_tools`（可选）。

```python
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), constrained_layout=True)
rng = np.random.default_rng(SEED)
# (a) 折线
x = np.linspace(0, 10, 50); axes[0, 0].plot(x, np.sin(x), color='#4C72B0', label='A')
axes[0, 0].plot(x, np.cos(x), '--', color='#DD8452', label='B')
axes[0, 0].set_ylabel('信号'); axes[0, 0].legend(frameon=False, fontsize=6)
# (b) 散点
axes[0, 1].scatter(rng.normal(0, 1, 60), rng.normal(0, 1, 60), s=12, c='#55A868', alpha=0.7)
# (c) 柱状
axes[1, 0].bar(['G1', 'G2', 'G3'], [3.2, 4.5, 2.8], yerr=[0.3, 0.2, 0.4], capsize=2,
               color=['#4C72B0', '#DD8452', '#55A868'])
# (d) 箱线
axes[1, 1].boxplot([rng.normal(l, 1, 40) for l in [0, 0.7, 1.4]], tick_labels=['G1', 'G2', 'G3'],
                   patch_artist=True)
# 面板编号（复用 scipilot 的 add_panel_labels，或手动统一位置）
for ax, lab in zip(axes.flat, ['(a)', '(b)', '(c)', '(d)']):
    ax.text(-0.1, 1.08, lab, transform=ax.transAxes, fontsize=11, fontweight='bold', va='top')
fig.suptitle('图1 多角度结果总览', fontsize=14, fontweight='bold')
finish_figure(fig, 'fig1_multipanel', 'figures')
```

---

## 通用铁律（与 figure-skill 一致）

1. **双导出**：`finish_figure` → 300dpi PNG（嵌论文）+ 600dpi PDF（存档）
2. **图题含结论**：`图N [对象][趋势/关系]（[关键数值]）`，禁止"示意图"
3. **色盲安全 + 双编码**：颜色 + 线型/marker 双重区分
4. **数值不可手写**：所有 r / RMSE / 重要性值从真实计算取
5. **交互图导出**：plotly 用 `write_image`（需 `kaleido`）或导出 HTML 后截图，PNG 仍要 300dpi
