---

name: "math-modeling-diagram-master"
description: "【Claudecode 自动选型版】数学建模论文图表智能选型+生成大师。为CUMCM/小美赛题目按题型匹配最优40类图表模板，强制流程图/验证图，消除AI假数据硬编码、图文重叠、流程图错位。接到建模题第一步先输出选型清单，再生成代码。"
metadata:
  version: "1.1.0"
  updated: "2026-08-05"
  changelog: "绘图分工路由（Python 走 figure-skill、出版级走 scipilot-figure-skill）"
---

# 数学建模论文图表智能选型与生成大师（Claudecode 选型执行版）

> **对 Claudecode 的执行指令：**
> 1. 接到数学建模题目 / 用户要求出图时，**第一步必须调用本 Skill**，不得先写模型代码或论文正文。
> 2. 先执行 **§三 选型决策树**，扫题干关键词 → 确定题型 A/B/C/D/E → 生成 **图表选型清单（fig_plan 表格）** 输出给用户确认。
> 3. 用户确认清单后，再调用 **§五 标准工作流 Step 3~7** 生成绘图代码并嵌入论文。
> 4. 任何图不得省略、不得编造假数据，不得跳过自检清单。

本 Skill 接管"题目 → 图表选型 → 绘图代码生成 → 论文 LaTeX / Word 嵌入"的完整链路。
**设计目标：消灭 AI 味（硬编码假数、拍脑袋 ε、标签压数据、流程图瞎摆），确保论文里真的能看到每一张关键图。**

---

## 一、什么时候触发调用（**Claudecode 强制触发，不遵守视为错误**）

出现以下任一情况 **必须** 先调用本 Skill：
1. 用户提到任何数学建模类关键词：国赛 / CUMCM / 美赛 / MCM / ICM / 小美赛 / 研究生建模赛 / 题目分析 / 建模思路 / 论文排版；
2. 用户要求出图、画图、生成图表、流程图、技术路线、甘特图、饼图、柱状图、雷达图、桑基图、热图、曲面图等；
3. 生成了数据/模型结果（尤其是优化目标、预测、评估）但尚未生成对应可视化；
4. 正在组装 LaTeX / Word 论文或报告正文。

**默认约束（Claudecode 不得违反）：没有图表的模型结论 = 没有结论。**
任何 ≥2 页的论文输出必须包含 ≥6 张图，且下限结构为：
> **fig1 流程图（必出） + fig2~3 结果图 + fig4~5 验证图（灵敏度龙卷风+MC组图） + fig6 专题分析图（≥6 张）**

**绘图分工边界（与相邻绘图 Skill，三者触发不冲突）**：
- **本 Skill = 选型决策**（题型→fig_plan 清单）+ MATLAB `academic_plotlib` 模板分发
- **Python 绘图执行 → 调 `figure-skill`**（国赛级 matplotlib 规范：SimHei 中文/5 套学术调色板/finish_figure 双导出）
- **出版级/期刊投稿图 → 调 `scipilot-figure-skill`**（EDA 剖析→选图顾问→期刊规范→视觉自检闭环）
- 执行顺序：本 Skill 选型 → 按技术栈路由执行规范；国赛论文默认 MATLAB 模板库或 figure-skill，scipilot 仅在用户要求期刊投稿级质量时启用

---

## 二、40 类高频图模板总览（与 MATLAB 模板库一一对应）

模板库路径：`C:\Users\Lenovo\matlab_scripts\academic_plotlib\`
配套调色板 / 样式：`get_nature_palette.m`、`set_academic_defaults.m`
主入口分发：`academic_plot.m`（Switch case 按图名路由到具体子函数）

| 大类 | 图类型（9 + 7 + 4 + 3 + 2 + 4 + 4 + 4 = 37） | 对应 MATLAB 模板标识 |
|---|---|---|
| ① 基础统计（9） | 折线图、三维折线图、三维填充折线图、阶梯图、面积图、山脊图、雷达图、针状图 | `line_2d / line_3d / line_3d_fill / stairs / area / ridgeline / radar / stem` |
| ② 柱状堆叠（7） | 普通柱状图、横向多色柱状图、三维赋色柱状图、堆叠柱状图、横向堆叠、三维堆叠柱状图、正负柱状图 | `bar / barh_multi / bar3c / bar_stack / barh_stack / bar3_stack / bar_posneg` |
| ③ 散点（4） | 极坐标散点图、三维散点图、分组散点图、带线+阴影标记散点图 | `scatter_polar / scatter3 / scatter_grouped / scatter_band` |
| ④ 分布+热图（3） | 箱线图、热图、相关性气泡热图 | `box / heatmap / heatmap_bubble` |
| ⑤ 饼图（2） | 二维饼图、三维饼图 | `pie_2d / pie_3d` |
| ⑥ 三维曲面（4） | 伪彩图、曲面图、网格曲面图、带等高线的曲面图 | `pcolor / surf / mesh / surf_contour` |
| ⑦ 特色图（4） | 局部放大图、进阶词云图、桑基图、有向图 | `zoom_inset / wordcloud / sankey / digraph` |
| ⑧ 论文必出（2，强制） | 建模流程图 / 技术路线、MC / 灵敏度 验证组图 | `flowchart / validation_panel` |

> 注：若用户原始清单中含"三维饼图"等与"饼图类：二维/三维"等重复分类已合并。MATLAB 模板库实际覆盖全部 40 项。

---

## 三、核心：**按国赛题目类型 → 图表选型决策树（强制性）**

拿到题目后，**先用本节判定题目类型**，再按下方映射列出图表清单。
如果题目混合多种类型（如 A 题含物理模型+数据分析），则**并集**各自的推荐图表，且总数不得少于 6 张。

### 3.1 题型识别关键字

| 题型代号 | 判定触发词 | 典型例子 |
|---|---|---|
| **A 机理建模型**（物理/光学/热工/流体/机械） | 光学效率、截断、反射、温度场、热传导、应力、辐射、太阳、定日镜、流动、压力、力学方程、PDE、有限元、耦合、几何、结构、流体、光束、功率 | 2023A 定日镜场；2022A 抛物面搜索；2019A 高压油管 |
| **B 调度/分配/组合优化型** | 排班、分批、调度、运输、装箱、分配、栏舍、车间、批次、路径、TSP、VRP、库存、生产计划、资源约束 | 2023D 湖羊养殖；2021B C2 灌装线；2024A 车速优化 |
| **C 数据驱动/评估/预测型** | 附件.xlsx、回归、指标、评价、预测、特征、相关性、聚类、分类、主成分、ARIMA、LSTM、机器学习 | 2023C 碳排放；2022D 无人机定位；2020C 信贷风险 |
| **D 网络/选址/拓扑/图论型** | 基站、选址、线路、网络、拓扑、最短路径、图论、中心地、布局、有向、无向、节点、边、覆盖 | 2023B 海域测地线；2024B 基站覆盖；2022B 无人机组网 |
| **E 生态/环境/资源型** | 生态、捕捞、污染物、扩散、种群、传染病、Logistic、SIR、灰水足迹、资源量 | 2021E 水质；2020D 炉心；2019D 无线覆盖 |

### 3.2 选型强制映射（≥下限）

**通用强制必出图（所有题型必出，缺一张视为不合格）：**
1. **图 1 — 建模流程图 / 技术路线图**：三问或三模块递进，网格化定位（见 §4.1）。
2. **灵敏度龙卷风图**（`bar_posneg` 横向正负柱，也可直接用龙卷风样式）：ε = Δln(目标)/Δln(参数) **必须用真实模型运行后计算，严禁手写 0.50/0.27**。
3. **蒙特卡洛 / 验证组图**（至少 1 张）：残差直方、MC 分布、拟合残差—灵敏度—MC 三张联动；

**各题型额外推荐图（≥数量下限）：**

| 题型 | 必出下限 | 推荐图表模板标识 | 典型用途 |
|---|---|---|---|
| **A 机理** | ≥4 张额外 | `surf / surf_contour / heatmap / scatter_polar / scatter3 / line_2d / bar / validation_panel` | 截断效率等高线、温度场曲面、效率分布极坐标散点、各月效率折线、分问题结果柱状对比、MC 验证组图 |
| **B 调度** | ≥4 张额外 | `barh_multi / bar_stack / area / stairs / radar / digraph / sankey / pie_2d + wordcloud` | 甘特图用 area/stairs 组合；各阶段栏舍分配饼图；分批方案横向对比柱；多方案评价雷达；物料/任务流向桑基 |
| **C 数据** | ≥4 张额外 | `scatter_grouped / box / heatmap_bubble / ridge / stem + pcolor` | 分组散点+趋势置信带；箱线分布对比；特征相关系数气泡热图；变量分布山脊图；残差针状图 |
| **D 网络/选址** | ≥3 张额外 | `digraph / sankey / scatter_polar + zoom_inset + pcolor` | 网络拓扑有向图；流量分配桑基；方位极坐标散点；高密区局部放大图 |
| **E 生态/环境** | ≥3 张额外 | `mesh / line_3d_fill / area + radar + surf_contour` | 种群三维填充折线（SIR）；资源量面积图；指标雷达；污染物扩散带等高线曲面 |

> **Claudecode 选型判定流程（必须严格执行，不得简化）：**
> ```
> Step 1. 关键词扫描（按顺序匹配，全部匹配，多标签）：
>   ↳ 命中以下任一词 → 加标签 A：光学、截断、反射、温度、热传导、应力、辐射、太阳、定日镜、
>                          流动、压力、力学、PDE、有限元、耦合、结构、流体、光束、功率、方程
>   ↳ 命中以下任一词 → 加标签 B：排班、分批、调度、运输、装箱、分配、栏舍、车间、批次、
>                          路径、TSP、VRP、库存、生产、资源、约束、计划
>   ↳ 命中以下任一词 → 加标签 C：附件、.xlsx、.csv、回归、指标、评价、预测、特征、相关性、
>                          聚类、分类、主成分、ARIMA、LSTM、机器学习、数据
>   ↳ 命中以下任一词 → 加标签 D：基站、选址、线路、网络、拓扑、最短路径、图论、中心地、
>                          布局、有向、无向、节点、边、覆盖、覆盖度
>   ↳ 命中以下任一词 → 加标签 E：生态、捕捞、污染物、扩散、种群、传染病、Logistic、SIR、
>                          灰水、资源、水质、环境
>   ↳ 若关键词不足 3 个 → 保守策略：同时加 B + C（调度+数据双标签）
>
> Step 2. 初始化必出三件套：
>   fig_plan = [
>     {fig1, 'flowchart',       '建模技术路线',           '题干三问/三模块结构'},
>     {figX, 'bar_posneg',      '灵敏度龙卷风',          '模型±10%~30%扰动输出的 ε=Δln/Δln 真实计算'},
>     {figY, 'validation_panel','MC+残差三重验证组图',   '模型求解真实结果数组'}
>   ];
>
> Step 3. 对每个题型标签追加推荐图（去重）：
>   标签 A → 追加 [surf / surf_contour / heatmap / line_2d / scatter_polar / scatter3]
>   标签 B → 追加 [barh_multi / bar_stack / area / stairs / radar / sankey / pie_2d / wordcloud]
>   标签 C → 追加 [scatter_grouped / scatter_band / box / heatmap_bubble / ridgeline / stem / pcolor]
>   标签 D → 追加 [digraph / sankey / scatter_polar / zoom_inset / pcolor]
>   标签 E → 追加 [mesh / line_3d_fill / area / radar / surf_contour]
>
> Step 4. 若 |fig_plan| < 6 → 按主标签补齐：
>   主A→heatmap；主B→barh_multi；主C→box；主D→digraph；主E→mesh
>
> Step 5. 为每张图补齐元数据：{图号, 模板ID, 用途说明, 数据来源, 在第几节引用}
>
> Step 6. **输出给用户的选型清单格式（必须严格按下面表格输出，不得改格式）：**
> ```
>
> ### 📊 图表选型计划清单（请确认）
>
> | 图号 | 模板ID | 图名 / 用途 | 数据来源 | 论文引用位置 |
> |---|---|---|---|---|
> | fig1 | flowchart | 建模技术路线三问递进 | 题干三问结构 | §1 技术路线 |
> | fig2 | xxx | xxxxx | 模型结果数组 yyy | §3.1 |
> | ... | ... | ... | ... | ... |
>
> **合计 N 张图（≥6），其中：流程图1张 + 结果图M张 + 验证图2张（强制）**
>
> 请您确认或调整后，我将生成全部绘图代码并执行 PNG+PDF 双输出。
> ```
>
> Step 7. **用户确认后** → 按 §五 标准工作流 Step 3~7 执行代码生成、运行、自检、嵌入论文。
> **严禁在用户未确认选型清单前直接生成绘图代码！**

---

## 四、去 AI 味 + 防重叠排版规范（**强制性约束，任何图违反即返工**）

### 4.1 流程图 / 技术路线（必出，零容忍）
- **网格化定位**：不得手写模糊的 `[0.02 0.18 0.18 0.64]` 类 magic number。必须显式定义列中心 `cx = [20, 50, 80]`、行 y 中心 `y_in, y_q, y_m, y_r, y_out` 等，所有子框通过 `(cx[i] ± bw/2, y[j] ± bh/2)` 计算坐标。
- 画布尺寸 16cm×10cm（A4 版心），框宽高比 `aspect=0.5`（高度/宽度=1:2）。
- 列与列之间至少留 6cm 通道，箭头水平居中、不跨框。
- 图例与输出框 y 坐标需检查不相交（输出框 y 范围±图例 y 范围无交集）。
- 三问/三模块的颜色用 Nature 蓝/青/橙 定性色，不得花里胡哨。

### 4.2 柱状图（bar/barh/bar_stack）
- 数值标签：柱高**上方 + 1.2~1.5 × 字体高度**间距（柱状），或左侧/右侧（横向柱），**禁止写在柱内部**。
- 图例：放在图外（`bestoutside` 或 `southoutside`），绝不盖数据。
- 正负柱（`bar_posneg`）：0 基准线加粗 1.4pt，正值深蓝、负值深红，每柱数值标签置于外侧。

### 4.3 饼图 / 环形图
- **标签外置 + 引导线**，禁止直接写在扇形内部（小于 5% 的扇区尤其要外置）。
- 环形（donut）中心文字：只放总数值，不得塞文字。

### 4.4 折线图 / 面积图 / 山脊图
- 图例数量 ≥4 条时必须外放到 `southoutside`，并列多列。
- 数据标签只标注关键点（峰值/谷值/拐点），不能每条线每一个点都写数字。
- 带阴影置信带（`scatter_band`）：`fill_between(x, y±σ, alpha=0.12)` 置于线条下层（zorder）。

### 4.5 热图 / 气泡热图
- 数值 **≤10×10** 的小热图必须写单元格数字。
- 气泡热图的气泡尺寸图例必须放在右侧外侧。
- 色条（colorbar）始终放在图外右侧或顶部，不占用主绘图区。

### 4.6 三维曲面 / 网格
- 视角默认 `view(30, 25)`（Nature 风格 30° 方位 25° 俯仰）。
- 必须有 z 轴标签，色条必须显示物理量名称。
- 带等高线的曲面（`surf_contour`）：底部投影等高线，主图半透明。

### 4.7 弹性系数 ε、均值 μ、标准差 σ 等统计数字
- **绝对禁止手写假数据**（如 `ε = 0.50` 这类与实际模型输出不一致的数）。
- 正确写法：运行模型得到 high/low 两组输出，按
  ```
  ε = ln(y_high / y_low) / ln(p_high / p_low)
  ```
  **真实计算**并在图生成代码里自动格式化字符串。
- 置信区间上下限、MC 的 P(≥1500)、R² 等任何"评估数值"一律从实际计算的数组中取，不得编造。

### 4.8 论文嵌入规范
- 每张图同时导出 **PNG (300/600 dpi) + PDF (矢量 painter)** 双格式。
- LaTeX：`\includegraphics[width=0.85\textwidth]{fig1_flowchart.png}` 配套 `\caption{}` + `\label{fig:xxx}`，文字描述必须与图中数值一致。
- Word：高分辨率 PNG 嵌入，保持纵横比；论文正文中出现的数字必须先在图/表中出现。

---

## 五、标准工作流 Step-by-Step

在用户描述完一道建模题并要求出图/写论文时，**严格按以下 7 步执行**：

| 步骤 | 动作 | 产出物 |
|---|---|---|
| ① 题型识别 | 扫题干关键词 → 类型 A/B/C/D/E（可混合） | 题型标签集合 |
| ② 图表清单（本 Skill 决策） | 通用必出(3) + 题型推荐(≥3~4) → 清单≥6 张，命名 fig1~figN | `fig_plan[]` 数组（图号/模板名/用途/数据来源） |
| ③ 模型结果数据抽取 | 从求解脚本取真实数组 / Excel 输出，**绝对不写死假数** | 数据数组 X, Y, Z, labels 等 |
| ④ 绘图代码生成 | 调 `C:\Users\Lenovo\matlab_scripts\academic_plotlib\academic_plot('模板标识', 数据, opts)` 或对应 Python 模式 | `plot_fig1.m`、`plot_fig2.m` …… |
| ⑤ 执行+双导出 | 运行绘图代码；检查每张图 PNG+PDF 均已输出 + 无报错 | `d_figures/png/`、`d_figures/pdf/` 下文件 |
| ⑥ 图文一致性审查 | 对照 §4 各条约束，重点查：(a) ε 等数值是否来自真代码；(b) 标签是否压数据；(c) 流程图网格定位+无错位；(d) 图例位置合理 | 审查通过清单（不合格返工） |
| ⑦ 嵌入论文正文 | 在 LaTeX/Word 中插入图 → 写 caption → 引用 label → 正文文字与图内数值逐句核对 | 含图的完整论文章节 |

---

## 六、40 类图的最小示例模板速查（直接粘贴到绘图脚本）

位置：`C:\Users\Lenovo\matlab_scripts\academic_plotlib\academic_plot.m`
接口规范：
```
[fig_h, ax_h] = academic_plot('line_2d',        x, Y,            struct('xlabel','x','ylabel','y','title','...'));
[fig_h, ax_h] = academic_plot('bar_stack',      X, groups,       struct('colors','nature_qual','legend',{...}));
[fig_h, ax_h] = academic_plot('flowchart',      plan_struct,     struct('title','建模技术路线'));
[fig_h, ax_h] = academic_plot('sankey',         nodes, edges,    struct('value_field','flow_kgs'));
```
所有图的第 4 个参数是 options 结构体，可覆盖：`xlabel / ylabel / zlabel / title / fontsize / palette / colors / legend_labels / xticks / yticks / ylim / filename / dpi`。

**Python 等价模式**（若当前用户在使用 Python 环境）：
- **调用 `figure-skill` 执行**（国赛 Python 绘图规范：SimHei 中文字体、5 套学术调色板、finish_figure 双导出）
- 参考 `C:\Users\Lenovo\OneDrive\Desktop\2023D\d_plot_figures.py` 中的 7 张图实现。
- 必须统一：`rcParams['font.sans-serif']` 中文字体 + savefig bbox_inches tight + 双 PNG/PDF 导出。

---

## 七、质量自检清单（生成完所有图后必须逐项划勾）

```
[ ] 1. fig1 流程图存在，且三模块列 cx、行 y 采用显式网格变量定位（非 magic number）
[ ] 2. 流程图底部图例与输出框 y 坐标区间不相交
[ ] 3. 灵敏度图中 ε 数值由实际运行结果 `Δln/Δln` 自动计算打印（不是手写）
[ ] 4. 所有柱状图/饼图/环形图的数值/类别标签全外置，不压数据/扇区
[ ] 5. 所有折线图例 ≥4 条时置于图外（southoutside / eastoutside）
[ ] 6. 每张图同时输出 .png 与 .pdf 两份，文件名一致
[ ] 7. 论文 `\includegraphics` 引用的文件在文件系统中实际存在
[ ] 8. 论文正文引用的数值（如年出栏 2358 只）与图中标签一致
[ ] 9. 总张数 ≥ 6（含流程图、灵敏度、MC 验证三件套）
[ ] 10. 色/字体/线宽符合 Nature/Science/IEEE 学术风格（无亮粉/霓虹/默认彩虹 colormap）
```

---

## 八、失败兜底（如果 MATLAB 模板运行报错）

1. 缺工具箱（如 `wordcloud` / `sankey` / `digraph` 的 Bioinformatics / Graph Theory Toolbox 未激活）→ **自动降级到 matplotlib Python 实现**，调用相同调色板函数，输出同样 PNG+PDF。
2. 中文字体报 `SimHei/Microsoft YaHei 不存在` → 自动回退到 `SimSun` + `Times New Roman` 组合。
3. 某张图运行失败时：**不得删掉该图**，而是在论文对应位置保留占位符 `[TODO: figX - 原因]` 并在对话中立即请求用户修复，绝不让论文缺图。

---

**Skill 输出承诺：**
> 调用本 Skill 后，我会先给你一份 `图表选型计划清单（fig1~figN，含模板ID/用途/数据来源）` → 你确认后生成所有绘图代码 → 执行 → 自检 → 嵌入论文正文。
> 若任何阶段发现 AI 假数据硬编码/标签压数据/流程图错位，自动返工并标红原因。
