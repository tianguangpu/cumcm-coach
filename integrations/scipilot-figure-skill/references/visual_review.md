# 视觉自检闭环：让 AI 看着图自己挑错、自己改
v2.1 的核心新增能力。普通画图工具画完就结束了——**没人回看成图**。

## 为什么必须「渲染成 PNG 再让 AI 看」
- **矢量 PDF/SVG 没法直接"看"像素层面的重叠和遮挡**——必须先栅格化成 PNG
- **程序能查的有限**：缺字、越界、刻度相交这类**确定性**问题程序能抓，但"图例正好压在一簇数据点上"这类**感知性**问题，只有把图当成图像看才发现

## 分工：程序自检 vs AI 读图
| 层 | 工具 | 负责抓 |
|---|---|---|
| 程序自检 | `visual_qa.py :: audit_layout(fig)` | 缺字乱码、文字越界裁切、刻度标签重叠 |
| AI 读图 | 本文件清单 + `Read` 读 PNG | 图例压数据、标注重叠、子图标签对齐、配色/灰度可分 |

## 标准操作流程

### 第 1 步：渲染预览
```python
from visual_qa import render_preview, audit_layout, print_report
preview = render_preview(fig, "figs/_preview.png", dpi=150)
```

### 第 2 步：程序自检
```python
issues = audit_layout(fig)
print_report(issues)
```

### 第 3 步：AI 读图自检（关键）
用 `Read` 工具读 `figs/_preview.png`，然后**逐条**对照下面的清单核对。

#### 读图自检清单
1. **乱码 / 方框**
   - 中文有没有变成 □□□ 方框？
   - 负号、`±`、`×`、`μ`、`Δ`、希腊字母、上下标有没有缺字？
2. **文字被裁切**
   - 标题、x/y 轴标签、图例、数值标注，有没有被画布四边切掉一截？
3. **文字遮盖 / 重叠**
   - **图例有没有压住数据**（点、线、柱）？
   - 显著性标注、数值标签、注释文字之间有没有互相叠？
   - x 轴刻度标签有没有挤成一团、互相穿插？
4. **子图编号对齐**（多面板必查）
   - a/b/c/d 是否**横看一条线、竖看一条线**？
   - 字号、加粗、风格是否一致？
5. **子图间距 / 互相侵入**
   - 子图之间有没有重叠？某个子图的 y 轴标签有没有伸进左边邻居？
   - colorbar 有没有和子图挤在一起或压住数据？
6. **配色与灰度**
   - 各类别颜色能区分吗？有没有用到红绿对比？
   - 灰度下还能分开吗？分不开 → 加线型/marker 冗余编码
7. **数据完整性**
   - 有没有数据点/曲线/误差棒被坐标轴范围切掉？
8. **跨子图一致性**
   - 同一个变量在多个子图里是否**同色、同标记、同量纲**？

### 第 4 步：回改对应表
| 读图发现 | 回改动作 |
|---|---|
| 中文/符号缺字方框 | `setup_style(lang='zh')`；查字体；负号方框确认 `axes.unicode_minus=False` |
| 文字被裁切 | `layout_tools.finalize_figure(fig)`；导出 `bbox_inches='tight'` |
| 图例压住数据 | `ax.legend(loc=..., bbox_to_anchor=(1.02,1), frameon=False)` 移到图外 |
| 标注文字互相叠 | 调整 `xytext` 偏移；减少标注数量 |
| x 轴刻度重叠 | `ax.tick_params(axis='x', rotation=30)`；减少刻度数 |
| 子图标签不对齐 | `add_panel_labels(fig, style='nature')` 统一重打 |
| 配色不可区分/灰度糊 | 换 Okabe-Ito / `colorblind` 调色板 + 加线型/marker |

### 第 5 步：重新渲染，再读图
改完**回到第 1 步**重新 `render_preview` 并再读一次。循环直到通过。

## 循环纪律
- **每改一处就重渲一次**——不要一次改五处然后猜结果
- **最多 3 轮**：3 轮还过不了，多半是图型选错了或数据维度太多
- **留痕**：把每轮发现的问题和改法简要告诉用户

## 完整示例
```python
import matplotlib.pyplot as plt
from setup_style import setup_style
from layout_tools import finalize_figure, add_panel_labels
from visual_qa import render_preview, audit_layout, print_report
from export_figure import export_figure

setup_style(journal='nature', lang='zh')
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))
# ... 在 axes 上作图 ...

finalize_figure(fig)
add_panel_labels(fig, style='nature')
render_preview(fig, 'figs/_preview.png')
print_report(audit_layout(fig))
# 然后：用 Read 读 figs/_preview.png，对照 8 项清单逐条核对
# 有问题 → 按回改表改 → 重渲 → 再读；全过后再导出：
export_figure(fig, 'figs/fig1', formats=['pdf', 'svg'],
              size_inches=(7.2, 5.4), grayscale_preview=True)
```