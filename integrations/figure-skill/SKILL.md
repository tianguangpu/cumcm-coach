---
name: "figure-skill"
description: "Python/Matplotlib国赛级图表绘图规范。当需要用Python画高质量学术图表、热力图、3D曲面、雷达图、收敛曲线时自动调用。"
metadata:
  version: "1.1.0"
  updated: "2026-08-05"
  changelog: "绘图分工边界（选型走 diagram-master、出版级走 scipilot-figure-skill）"
---

# Figure Skill — 国赛级 Python 绘图规范

> **核心目标：用 matplotlib/seaborn 画出评委3秒看懂的国赛级图表。**

## 触发条件
当用户要求用 Python 画图、生成学术图表、绘制国赛论文配图时自动激活。

## 分工边界（与相邻绘图 Skill，三者触发不冲突）
- **选什么图**（题型→fig_plan 选型清单）→ 先调 `math-modeling-diagram-master`（选型决策 + MATLAB 模板分发）
- **国赛 Python 绘图规范**（怎么画：SimHei/5 套调色板/finish_figure 双导出/图题含结论）→ **本 Skill**
- **出版级/期刊投稿图**（EDA 剖析、期刊规范、视觉自检闭环）→ `scipilot-figure-skill`
- 执行顺序：diagram-master 选型 → 本 Skill 出图（国赛）→ scipilot 仅期刊投稿级质量时启用

## 第一步：初始化绘图环境

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# 全局样式配置（必须最先调用）
# 字号按「论文最终尺寸」设定：figsize 用 6.3×3.5 英寸（16cm×9cm），
# 插入论文时 1:1 铺满，不再二次缩放，因此这里的 pt 就是读者看到的 pt。
def setup_style():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'],
        'axes.unicode_minus': False,
        # —— 字号体系（最小 8pt 为 A4 印刷可读红线）——
        'font.size': 9,
        'axes.titlesize': 10,      # 轴标题
        'axes.labelsize': 10,
        'xtick.labelsize': 9,      # 刻度数字
        'ytick.labelsize': 9,
        'legend.fontsize': 9,      # 图例
        # —— 线宽（最终尺寸下的绝对线宽）——
        'lines.linewidth': 2.0,    # 主数据
        'axes.linewidth': 0.8,     # 坐标轴框
        # —— 网格：浅、细，只做辅助，不抢数据 ——
        'axes.grid': True,
        'grid.alpha': 0.15,
        'grid.color': '#CCCCCC',
        'grid.linewidth': 0.5,
        'figure.dpi': 100,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.facecolor': 'white',
    })
setup_style()
```

## 第二步：获取调色板/Colormap

```python
# 5套学术调色板（详见 references/palettes.md）
# 离散色（线/散点/填充）
pal = get_palette('Nature', n=4)          # 取前4色
pal = get_palette('Science', n=3)         # 高饱和对比

# 连续色（曲面/热力图）
cmap = get_colormap('Diverging')          # 发散色，0居中白
cmap = get_colormap('Qualitative')        # 定性分类

# 调色板速查（按图型选）
# 热力图/相关性 → Diverging
# 雷达图/多方案 → Nature 或 Qualitative
# 收敛曲线/多算法 → Nature
# 3D曲面 → Diverging 或 Science
```

## 第三步：统一收尾（必须调用）

```python
def finish_figure(fig, name, outdir):
    import os
    png_dir = os.path.join(outdir, 'png')
    pdf_dir = os.path.join(outdir, 'pdf')
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    fig.savefig(os.path.join(png_dir, f'{name}.png'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(pdf_dir, f'{name}.pdf'), dpi=600, bbox_inches='tight')
    plt.close(fig)

# 用法
finish_figure(fig, 'fig3_monthly_eff', 'cumcm_2026/figures')
```

## 图表铁律（强制遵守）

1. **视觉3层级**：主数据 linewidth≥2.5 > 辅助 1.5 > 框架 0.4
2. **双编码**：颜色 + marker 形状（o/s/^/d）双重区分
3. **中文字体 SimHei**：所有标题/标签/图例用 SimHei
4. **字号按最终尺寸定**：见下方「尺寸与字号」——**不是**先画大图再缩小
5. **导出双格式**：300dpi PNG（嵌论文）+ 600dpi PDF（存档）
6. **图题含结论**：禁"示意图"，格式 `图N [对象][趋势]（[数值]）`
7. **标注不遮挡**：放稀疏区 + 白底黑框 + 箭头引出
8. **禁止裸图**：每图叠加≥1个创新技法

---

## 尺寸与字号（决定"看起来舒不舒服"）

> **这是最容易翻车的一点**。很多人习惯 `figsize=(14, 7)` 画大图，插进论文后
> 被缩放到 0.4 倍——**字号 12pt 实际只剩 5pt**，评委看着费劲，图就"废"了。

### 铁律：figsize 直接等于论文中的最终尺寸

论文里图片的实际宽度（A4 正文，左右页边距 2.5cm）：

| 版式 | 最终宽度 | 对应 figsize（英寸） |
|------|---------|---------------------|
| 单栏窄图 | 8 cm | `figsize=(3.15, 2.4)` |
| **常规整幅图** | **16 cm** | **`figsize=(6.30, 3.54)`** ← 最常用 |
| 整幅方图（热力图/雷达） | 14 cm | `figsize=(5.51, 4.72)` |
| 横向宽图（多子图） | 16 cm | `figsize=(6.30, 3.15)` |

**换算**：1 英寸 = 2.54 cm。**LaTeX 侧同步设置**
`\includegraphics[width=\linewidth]{...}`，让图片按自然尺寸铺满，不再二次缩放。

### 字号体系（按最终尺寸，印刷可读下限）

| 元素 | 字号 | 字重 |
|------|------|------|
| 子图编号 (a)(b)(c) | 11pt | 加粗，左上角 |
| 轴标题（物理量 + 单位） | 10pt | 常规 |
| 刻度数字 | 9pt | 常规 |
| 图例文字 | 9pt | 常规 |
| 图内标注/数值 | 9pt | 加粗 |
| **最小任何元素** | **≥8pt** | A4 印刷可读红线 |

> ⚠️ **校验口诀**：`最终字号 = 设定字号 × (论文插入宽度 / figsize宽度)`。
> 该值必须 ≥8pt。若你的 figsize 宽度超过 7 英寸，几乎必然不达标。

### 标注布局（不遮挡数据）

1. **放稀疏区**：标注放数据未覆盖的角落（左上/右下留白处）
2. **箭头引出**：文字框距数据点 5–10% 画布距离，用 `arrowprops` 引向目标
3. **白底半透明**：`bbox=dict(boxstyle='round', fc='white', ec='gray', alpha=0.85)`
4. **错开不叠**：多个标注横向/纵向错开 ≥1 行高
5. **峰值偏移**：最值标注在点正上方/侧方 +0.5 字高，不压点

### 布局体检（出图后自查）

- [ ] 子图间距不拥挤：`fig.tight_layout()` 或 `constrained_layout=True`
- [ ] 刻度不重叠：长标签用 `rotation=30, ha='right'`
- [ ] 图例不压数据：优先放数据稀疏区，或置于图外 `bbox_to_anchor`
- [ ] 无文字超出画布被裁切（`bbox_inches='tight'` 只救得回一点，根因是字号/尺寸失衡）
- [ ] 留白不过量：主体占画布 70% 以上，避免"图很小、白边很大"

## 快速示例

### 示例1：多条曲线（收敛对比）
```python
# figsize 直接取论文最终尺寸：16cm × 9cm = 6.30 × 3.54 英寸
fig, ax = plt.subplots(figsize=(6.30, 3.54))
x = np.linspace(0, 200, 200)
pal = get_palette('Nature', 2)
ax.plot(x, 10*np.exp(-x/40)+0.5, '-', color=pal[0], linewidth=2.0, label='基础PSO')
ax.plot(x, 10*np.exp(-x/20)+0.3, '--', color=pal[1], linewidth=2.0, label='改进SA-PSO')
ax.set_xlabel('迭代次数 (次)')
ax.set_ylabel('目标函数值')
ax.legend(loc='upper right', frameon=False)
fig.tight_layout()
finish_figure(fig, 'fig5_convergence', 'figures')
# 图题在 LaTeX 侧用 \caption{...} 出（字号由模板统一控制），
# 若坚持画在图内，用 ax.set_title(..., fontsize=10, fontweight='bold')
```

### 示例2：热力图（相关性）
```python
fig, ax = plt.subplots(figsize=(5.51, 4.72))   # 14cm × 12cm
data = np.random.randn(100, 6)
data[:,3] = data[:,0]*0.8 + np.random.randn(100)*0.3
C = np.corrcoef(data)
cmap = get_colormap('Diverging')
im = ax.imshow(C, cmap=cmap, vmin=-1, vmax=1)
# 标注数值（字号 ≥8pt）
for i in range(6):
    for j in range(6):
        star = '*' if abs(C[i,j])>0.5 and i!=j else ''
        color = 'white' if abs(C[i,j])>0.7 else 'black'
        ax.text(j, i, f'{C[i,j]:.2f}{star}', ha='center', va='center',
                fontsize=9, fontweight='bold', color=color)
ax.set_xticks(range(6)); ax.set_yticks(range(6))
ax.set_xticklabels(['x1','x2','x3','x4','x5','x6'])
ax.set_yticklabels(['x1','x2','x3','x4','x5','x6'])
plt.colorbar(im, label='Pearson r')
fig.tight_layout()
finish_figure(fig, 'fig3_heatmap', 'figures')
```

### 示例3：雷达图（多方案对比）
```python
fig, ax = plt.subplots(figsize=(5.51, 5.12), subplot_kw=dict(projection='polar'))  # 14cm 方图
dims = ['精度','效率','稳定性','可解释性','成本','迁移']
vals = [[0.92,0.78,0.85,0.70,0.65,0.80],
        [0.85,0.90,0.75,0.82,0.55,0.88],
        [0.70,0.95,0.90,0.60,0.72,0.75]]
pal = get_palette('Nature', 3)
angles = np.linspace(0, 2*np.pi, len(dims), endpoint=False).tolist()
angles += angles[:1]
for v, color, ls, mk in zip(vals, pal, ['-','--','-.'], ['o','s','^']):
    v_plot = v + v[:1]
    ax.plot(angles, v_plot, ls, color=color, linewidth=2.0, marker=mk, markersize=5)
    ax.fill(angles, v_plot, color=color, alpha=0.15)
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims, fontsize=9, fontweight='bold')
ax.set_title('方案 B 综合最优', fontsize=10, fontweight='bold', pad=18)
ax.legend(['方案A','方案B','方案C'], loc='lower center',
          bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)
fig.tight_layout()
finish_figure(fig, 'fig2_radar', 'figures')
```

## 参考文件
- `references/palettes.md` — 5套调色板详细说明
- `references/advanced-techniques.md` — 10种高级绘图技法
