# 七类图配方
每一节给一份**可直接运行的 Python 代码**——直接复制改数据就能出图。

## 目录
- [通用前置](#通用前置)
- [1. 折线图（含误差阴影）](#1-折线图含误差阴影)
- [2. 柱状图（分组 + 误差棒）](#2-柱状图分组--误差棒)
- [3. 散点图（多语义映射 + 回归线）](#3-散点图多语义映射--回归线)
- [4. 箱线图 / 小提琴图（叠 stripplot）](#4-箱线图--小提琴图叠-stripplot)
- [5. 热力图（感知均匀色图）](#5-热力图感知均匀色图)
- [6. 误差棒图](#6-误差棒图)
- [7. 分布图（直方图 / KDE）](#7-分布图直方图--kde)
- [8. 相关性矩阵 / 散点矩阵](#8-相关性矩阵--散点矩阵)
- [9. 多面板组合图](#9-多面板组合图)

---

## 通用前置
```python
import sys, os
sys.path.insert(0, '../scripts')
from setup_style import setup_style
from export_figure import export_figure
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
setup_style(journal='nature', lang='en')
OKABE = ['#000000', '#E69F00', '#56B4E9', '#009E73',
         '#F0E442', '#0072B2', '#D55E00', '#CC79A7']
PAL = sns.color_palette('colorblind')
```

---

## 1. 折线图（含误差阴影）
```python
def lineplot_with_band(ax, x, y_mean, y_err, label, color, ls='-'):
    ax.plot(x, y_mean, color=color, linewidth=1.0, linestyle=ls, label=label)
    ax.fill_between(x, y_mean - y_err, y_mean + y_err,
                    color=color, alpha=0.2, linewidth=0)

rng = np.random.default_rng(42)
x = np.linspace(0, 10, 100)
n = 12
y1_samples = np.sin(x)[:, None] + rng.normal(0, 0.3, (100, n))
y2_samples = np.cos(x)[:, None] + rng.normal(0, 0.3, (100, n))
y1_mean, y1_sem = y1_samples.mean(1), y1_samples.std(1, ddof=1) / np.sqrt(n)
y2_mean, y2_sem = y2_samples.mean(1), y2_samples.std(1, ddof=1) / np.sqrt(n)
fig, ax = plt.subplots(figsize=(3.5, 2.625))
lineplot_with_band(ax, x, y1_mean, y1_sem, 'Condition A', color=OKABE[2], ls='-')
lineplot_with_band(ax, x, y2_mean, y2_sem, 'Condition B', color=OKABE[6], ls='--')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Response (a.u.)')
ax.legend(frameon=False, loc='lower right')
export_figure(fig, 'figs/01_line', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 2.625), dpi=300, grayscale_preview=True)
```

## 2. 柱状图（分组 + 误差棒）
```python
rng = np.random.default_rng(0)
groups = ['Control', 'Drug A', 'Drug B']
conditions = ['Before', 'After']
data = pd.DataFrame({
    'group': np.repeat(groups, 2 * 10),
    'condition': np.tile(np.repeat(conditions, 10), 3),
    'value': np.concatenate([rng.normal(loc, 1.0, 10) for loc in [1, 2, 3, 4, 2, 3]]),
})
fig, ax = plt.subplots(figsize=(3.5, 2.625))
sns.barplot(data=data, x='group', y='value', hue='condition',
            palette=[OKABE[2], OKABE[6]], errorbar='se', capsize=0.15,
            err_kws={'linewidth': 0.8}, ax=ax)
sns.stripplot(data=data, x='group', y='value', hue='condition',
              palette=[OKABE[2], OKABE[6]], dodge=True, size=2, alpha=0.6,
              edgecolor='black', linewidth=0.3, ax=ax, legend=False)
ax.set_xlabel(''); ax.set_ylabel('Score (a.u.)')
ax.legend(title='', frameon=False, loc='upper left')
export_figure(fig, 'figs/02_bar', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 2.625), dpi=300)
```

## 3. 散点图（多语义映射 + 回归线）
```python
rng = np.random.default_rng(1)
N = 80
df = pd.DataFrame({
    'x': rng.normal(0, 1, N),
    'group': rng.choice(['A', 'B'], N),
})
df['y'] = 0.6 * df['x'] + np.where(df['group']=='B', 0.5, 0) + rng.normal(0, 0.5, N)
fig, ax = plt.subplots(figsize=(3.5, 3.0))
sns.scatterplot(data=df, x='x', y='y', hue='group', style='group',
                palette=[OKABE[2], OKABE[6]], s=25, alpha=0.85,
                edgecolor='black', linewidth=0.3, ax=ax)
sns.regplot(data=df[df.group=='A'], x='x', y='y',
            scatter=False, color=OKABE[2], line_kws={'lw': 1.0}, ax=ax)
sns.regplot(data=df[df.group=='B'], x='x', y='y',
            scatter=False, color=OKABE[6], line_kws={'lw': 1.0}, ax=ax)
from scipy.stats import pearsonr
for g, c in zip(['A', 'B'], [OKABE[2], OKABE[6]]):
    sub = df[df.group == g]
    r, p = pearsonr(sub.x, sub.y)
    ax.text(0.05, 0.95 if g=='A' else 0.88,
            f'{g}: r={r:.2f}, p={p:.1e}',
            transform=ax.transAxes, fontsize=6, color=c, va='top')
ax.set_xlabel('Predictor x'); ax.set_ylabel('Response y')
ax.legend(title='Group', frameon=False, loc='lower right')
export_figure(fig, 'figs/03_scatter', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 3.0), dpi=300)
```

## 4. 箱线图 / 小提琴图（叠 stripplot）
```python
fig, ax = plt.subplots(figsize=(3.5, 2.625))
sns.boxplot(data=data, x='group', y='value', hue='condition',
            palette=[OKABE[2], OKABE[6]], showfliers=False, width=0.6,
            linewidth=0.8, ax=ax)
sns.stripplot(data=data, x='group', y='value', hue='condition',
              palette=[OKABE[2], OKABE[6]], dodge=True, size=2.5, alpha=0.6,
              edgecolor='black', linewidth=0.3, ax=ax, legend=False)
ax.set_xlabel(''); ax.set_ylabel('Score (a.u.)')
ax.legend(title='', frameon=False)
export_figure(fig, 'figs/04_box', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 2.625), dpi=300)
```

## 5. 热力图（感知均匀色图）
```python
rng = np.random.default_rng(2)
mat = rng.uniform(-1, 1, (8, 8))
mat = (mat + mat.T) / 2
np.fill_diagonal(mat, 1.0)
labels = [f'f{i+1}' for i in range(8)]
fig, ax = plt.subplots(figsize=(3.5, 3.0))
hm = sns.heatmap(mat, ax=ax, cmap='RdBu_r', vmin=-1, vmax=1, center=0,
                 annot=True, fmt='.2f', annot_kws={'fontsize': 5},
                 cbar_kws={'label': "Pearson's r", 'shrink': 0.8},
                 linewidths=0.5, linecolor='white',
                 xticklabels=labels, yticklabels=labels, square=True)
ax.tick_params(labelsize=6)
export_figure(fig, 'figs/05_heatmap', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 3.0), dpi=300)
```

## 6. 误差棒图
```python
doses = np.array([0, 1, 3, 10, 30, 100])
n = 8
rng = np.random.default_rng(3)
responses = (np.log10(doses + 1) * 2 + rng.normal(0, 0.5, (n, doses.size)))
mean = responses.mean(0)
sem = responses.std(0, ddof=1) / np.sqrt(n)
fig, ax = plt.subplots(figsize=(3.5, 2.625))
ax.errorbar(doses, mean, yerr=sem, fmt='o', color=OKABE[2], ecolor=OKABE[2],
            elinewidth=0.8, capsize=2, capthick=0.8, markersize=5,
            markeredgecolor='black', markeredgewidth=0.4, label='Compound X')
ax.set_xscale('symlog', linthresh=1)
ax.set_xlabel('Dose (μM)')
ax.set_ylabel('Response (a.u.)')
ax.legend(frameon=False, loc='lower right')
export_figure(fig, 'figs/06_errbar', formats=['pdf', 'svg', 'png'],
              size_inches=(3.5, 2.625), dpi=300)
```

## 7. 分布图（直方图 / KDE）
```python
rng = np.random.default_rng(7)
data1 = np.concatenate([rng.normal(0, 1, 200), rng.normal(4, 1, 200)])
data2 = rng.lognormal(0, 0.5, 400)
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), constrained_layout=True)
ax = axes[0]
ax.hist(data1, bins=30, density=True, alpha=0.55, color=OKABE[2],
        edgecolor='black', linewidth=0.4, label='Histogram')
sns.kdeplot(data1, ax=ax, color=OKABE[6], linewidth=1.2, label='KDE')
sns.rugplot(data1, ax=ax, color='black', height=0.04, alpha=0.4)
ax.set_xlabel('Value'); ax.set_ylabel('Density')
ax.set_title('Bimodal distribution')
ax.legend(frameon=False, fontsize=6)
ax = axes[1]
ax.hist(data2, bins=30, density=True, alpha=0.55, color=OKABE[3],
        edgecolor='black', linewidth=0.4)
sns.kdeplot(data2, ax=ax, color=OKABE[6], linewidth=1.2)
ax.axvline(data2.mean(), color='red', linestyle='--', linewidth=0.8,
           label=f'mean={data2.mean():.2f}')
ax.axvline(np.median(data2), color='black', linestyle=':', linewidth=0.8,
           label=f'median={np.median(data2):.2f}')
ax.set_xlabel('Value (log-normal)'); ax.set_ylabel('Density')
ax.set_title('Right-skewed: mean vs median')
ax.legend(frameon=False, fontsize=6)
export_figure(fig, 'figs/07_distribution', formats=['pdf', 'svg', 'png'],
              size_inches=(7.0, 2.8), dpi=300)
```

## 8. 相关性矩阵 / 散点矩阵
```python
rng = np.random.default_rng(8)
n = 200
base = rng.normal(0, 1, n)
df = pd.DataFrame({
    'feature_A': base + rng.normal(0, 0.5, n),
    'feature_B': base + rng.normal(0, 0.3, n),
    'feature_C': -base + rng.normal(0, 0.4, n),
    'feature_D': rng.normal(0, 1, n),
    'feature_E': rng.normal(0, 1, n),
    'feature_F': base * 0.5 + rng.normal(0, 0.6, n),
})
corr = df.corr(method='pearson')
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
fig, ax = plt.subplots(figsize=(4.0, 3.5))
sns.heatmap(corr, mask=mask, cmap='RdBu_r', vmin=-1, vmax=1, center=0,
            annot=True, fmt='.2f', annot_kws={'fontsize': 6},
            cbar_kws={'label': "Pearson's r", 'shrink': 0.7},
            linewidths=0.5, linecolor='white', square=True, ax=ax)
ax.tick_params(labelsize=6)
ax.set_title('Feature correlations', fontsize=8)
export_figure(fig, 'figs/08a_corr_heatmap', formats=['pdf', 'svg', 'png'],
              size_inches=(4.0, 3.5), dpi=300)
```

## 9. 多面板组合图
```python
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4), constrained_layout=True)
# 子图 a：折线
ax = axes[0, 0]
x = np.linspace(0, 10, 50)
ax.plot(x, np.sin(x), color=OKABE[2], label='A')
ax.plot(x, np.cos(x), color=OKABE[6], linestyle='--', label='B')
ax.set_xlabel('Time (s)'); ax.set_ylabel('Signal')
ax.legend(frameon=False, fontsize=6)
# 子图 b：散点
ax = axes[0, 1]
ax.scatter(rng.normal(0,1,50), rng.normal(0,1,50),
           c=OKABE[3], s=12, edgecolor='black', linewidth=0.3)
ax.set_xlabel('PC1'); ax.set_ylabel('PC2')
# 子图 c：柱状
ax = axes[1, 0]
vals = [3.2, 4.5, 2.8]; errs = [0.3, 0.2, 0.4]
ax.bar(['G1','G2','G3'], vals, yerr=errs, capsize=2,
       color=[OKABE[2], OKABE[6], OKABE[3]], edgecolor='black', linewidth=0.5)
ax.set_ylabel('Score')
# 子图 d：箱线
ax = axes[1, 1]
data_box = [rng.normal(loc, 1, 30) for loc in [0, 0.7, 1.4]]
ax.boxplot(data_box, tick_labels=['G1','G2','G3'], patch_artist=True, widths=0.5,
           boxprops=dict(facecolor=OKABE[2], alpha=0.6, linewidth=0.6),
           medianprops=dict(color='black', linewidth=1.0),
           flierprops=dict(marker='o', markersize=2))
ax.set_ylabel('Value')
# 子图标签
from layout_tools import finalize_figure, add_panel_labels
finalize_figure(fig)
add_panel_labels(fig, style='nature')
export_figure(fig, 'figs/09_multipanel', formats=['pdf', 'svg', 'png'],
              size_inches=(7.2, 5.4), dpi=300, grayscale_preview=True)
```