---
name: nature-plot-repro
description: Nature 同款论文图 MATLAB 复刻引擎。基于 slandarer PLTreprint 系列 26 个已验证案例（GPL-2），覆盖环形柱状图/核密度面积图/桑基图/弦图/冲积图/雷达图/三角热图/扇形热图/小提琴图/UpSet图/泰勒图/聚类热图/环形热图/哑铃图等 40+ 期刊级图型。当用户要画"Nature 同款""顶刊风格""期刊配图"、给出期刊论文图片要复刻、或点名上述任一图型时自动调用。执行链路：图型识别→案例匹配→数据替换→MATLAB 运行→300dpi PNG+矢量 PDF 导出→视觉自检。
---

# Nature 同款绘图复刻（MATLAB）

**核心定位**：把 Nature / Nature Communications / Science 论文里的精美图表用 MATLAB 复刻出来，供数学建模论文与期刊投稿直接使用。

**素材库**：`assets/cases/` 内 26 个案例（源自 slandarer 的 PLTreprint 开源仓库，GPL-2 协议，使用须保留作者署名注释）。
每个案例目录含：完整可运行的 `.m` 代码 + 必需示例数据 + 核心绘图类/函数。

## 一、图型速查表

用户描述图型时，按下表匹配案例目录（`assets/cases/` 下同名文件夹）：

| # | 案例目录 | 图型 | 入口脚本 | 依赖 |
|---|---|---|---|---|
| 1 | 复刻一：分组柱状图 | 分组柱状图（渐变/纹理配色） | `groupBarDemo.m` | 无 |
| 2 | 复刻二：折线图+误差棒+… | 多面板组合（折线/柱状/散点抖动/图片叠加） | `plotBarDemo.m` | Data.mat |
| 3 | 复刻三：分层聚类分析图 | 聚类热图+树状图 | `treeHeatmapDemo.m` | 无 |
| 4 | 复刻四：和弦图+颜色修改+标签旋转 | 弦图 | `chordChart.m`+`chordDemo.m` | 无 |
| 5 | 复刻五：带树状图的环形热图 | 环形热图+环内树状图 | `toroidalTreeHeatmapDemo.m` | slanCM |
| 6 | 复刻六：分组环形热图 | 多环分组热图 | `multiRingHeatmapDemo.m` | slanCM |
| 7 | 复刻七：热图+差异气泡图 | 热图+差异气泡（火山图元素） | `heatMapBubbleDemo.m` | test.csv, slanCM |
| 8 | 复刻八：堆叠柱状图+哑铃图 | 水平堆叠柱+哑铃图 | `stackedBarhBarDumbbellBemo.m` | csv 数据 |
| 9 | 复刻九：组合泰勒图 | 泰勒图（多模型对比） | `demo0~4.m`+`STaylorDiag.m` | testData.mat |
| 10 | 复刻十：旋转相关系数热图 | 45° 旋转三角相关热图 | `demoR45Heatmap.m` | 无 |
| 11 | 复刻十一：截断含误差棒分组柱状图 | 截断轴柱状图 | `truncAxis.m`+`truncBarChartDemo.m` | 无 |
| 12 | 复刻十二：桑基图+气泡图 | 桑基图+气泡组合 | `SSankey.m`+`sankeyBubble.m` | 无 |
| 13 | 复刻十三：含NaN图例地图绘制 | 地理图（NaN 灰色图例） | `NaN_Map_demo2.m` | Mapping Toolbox，需自备 tif |
| 14 | 复刻十四：右侧对齐桑基图 | 右对齐桑基图 | `SSankey.m`+`natureSankeyDemo1.m` | natureRandData.mat |
| 15 | 复刻十五：环形聚类树状图 | 环形聚类树 | `clusterTreeDemo.m` | slanCL |
| 16 | 复刻十六 弦末端弧形块单独上色弦图 | 弦图（弧块单独配色） | `chordChart.m`+`demo8.m` | 无 |
| 17 | 复刻十七：半小提琴图 | 半小提琴图（成对分布） | `halfViolinPlot.m` | 无 |
| 18 | 复刻十八：分组热图 | K-means 分组相关热图 | `groupedHeatmapDemo.m` | 无 |
| 19 | 复刻十九：弦图+桑基图 | 弦图+桑基图组合 | `demo_biogeographic_patterns.m` | Fig.4d.csv |
| 20 | 复刻二十：冲积图 | 冲积图（堆叠柱+流向带） | `FIG1bPerMANOVA.m` | Fig.1b.xlsx |
| 21 | 复刻二十一：扇形热图+小提琴图 | 扇形热图+小提琴图 | `fanHeatmap.m` | 无 |
| 22 | 复刻二十二：各类带树状图倒三角热图 | 三角热图+树状图（SMatrix/STree 类） | `demo0~4.m` | 无 |
| 23 | 复刻二十三：雷达图 | 雷达图（radarChart 类） | `demo1~3.m`+`demoNature.m` | 无 |
| 24 | 复刻二十四：桑基图+堆叠柱状图 | 桑基图+堆叠柱组合 | `demoSankey.m`+`demoNatureCom.m` | xlsx 数据 |
| 25 | 复刻二十五：环形柱状图+面积图 | 环形柱状图+核密度面积图 | `demoAreaBar.m` | 无 |
| 26 | 复刻二十六：UpSet图+弦图 | UpSet 图+弦图组合 | `demoUpSetPlot.m`+`demoChordChart.m` | gene.csv |

**图型→关键词映射**（快速路由）：
- 流/流向类：桑基图(12/14/19/24)、冲积图(20)
- 关系/网络类：弦图(4/16/19/26)、UpSet 图(26)
- 圆形布局类：环形柱状图(25)、环形热图(5/6)、扇形热图(21)、环形聚类树(15)、雷达图(23)
- 矩阵/热图类：聚类热图(3/7/18)、三角热图(22)、旋转热图(10)
- 分布类：小提琴图(17/21)、核密度面积图(25)、散点抖动(2)
- 对比类：分组柱状图(1/8/11)、哑铃图(8)、泰勒图(9)、误差棒(2/11)
- 地理类：地图(13)

详细 API 用法与每个案例的数据格式见 `references/figure-recipes.md`。

## 二、标准工作流（每次画图执行）

### 第 1 步：图型识别 + 案例匹配
问清用户：数据长什么样（矩阵/表/流记录）→ 对应上表选案例。用户给期刊图片要复刻时，用 `mcp__image-reader__read_image` 看图，提取布局/配色/元素，再匹配最近案例。

### 第 2 步：复制案例到工作目录
```bash
cp -r "/c/Users/Lenovo/.claude/skills/nature-plot-repro/assets/cases/<案例目录>" "<用户工作目录>/matlab/"
cd "<用户工作目录>/matlab"
```
复制完整目录（`.m` + 数据文件都要），类文件（如 `chordChart.m`）必须与 demo 同目录。

### 第 3 步：数据替换
打开 demo 脚本头部数据构造段，换成用户数据：
- 注释掉 `rng(...)` 随机数据段；
- 数值矩阵直接赋值；Excel/CSV 用 `readtable`/`readcell`；
- **保留原脚本的配色、布局、字体设置不动**——这是"Nature 味"的来源。

### 第 4 步：运行（两条路线）
**路线 A：MATLAB MCP**（交互调试首选）
```
mcp__matlab__generate_matlab_script(scriptName="demo_xxx", code="<读取本地 demo 文件后的完整内容>")
mcp__matlab__execute_matlab_script(script_name="demo_xxx")
```
注意：MCP 在临时目录执行，类文件需先写入同一临时目录；不确定时用路线 B。

**路线 B：直接批处理**（最稳）
```bash
cd "<工作目录>/matlab"
"/d/MatLab/bin/matlab.exe" -batch "cd('<工作目录>/matlab'); demoAreaBar; exportgraphics(gcf,'out.png','Resolution',300)"
```
中文路径用 `cd('...')` 引号包裹。

### 第 5 步：导出（按用户全局规范）
```matlab
% 脚本末尾加导出（300dpi PNG + 矢量 PDF）
exportgraphics(gcf, 'fig_xxx.png', 'Resolution', 300);
exportgraphics(gcf, 'fig_xxx.pdf', 'ContentType', 'vector');
```
中文标签需 SimHei 时在绘图前加：
```matlab
set(0,'DefaultAxesFontName','SimHei');  % 全局一次即可
```

### 第 6 步：视觉自检（必做）
用 `mcp__image-reader__read_image` 读导出 PNG，检查：
- 布局是否与目标图一致（左右/上下结构）；
- 配色是否协调（红蓝/冷暖对比、灰度可用）；
- 文字无截断、图例无遮挡、刻度无重叠；
- 不满意则回到第 3 步改参数重跑。

## 三、全局规范（源自案例库 + 用户偏好）

### 配色
- **slanCM(type, num)**：200+ colormap（matplotlib 全家桶 viridis/plasma 等 + 感知均匀色系），热图/曲面首选；
- **slanCL(type, num)**：2000 套离散色板（`slanCL_Data.mat`），分类变量首选；
- **nclCM(type, num)**：NCL 科学配色（地图/气候用）；
- 原图取色法：截图后用 `[r,g,b]./255` 硬编码（如复刻一 `CList=[111,173,72;92,154,215]./255`）；
- 通用原则：≤4 类用离散对比色，连续变量用感知均匀色带，避免彩虹色。

### 排版
- 图窗：`figure('Units','normalized','Position',[.1,.2,.7,.7],'Color','w')`
- 字体：Times New Roman 12-15（英文）；中文 SimHei；字号与图幅匹配，标签 14、标题 16 起步
- 坐标：`Box off` + `TickDir out` + `LineWidth 1.2`；无关轴线 `XColor none` 隐藏
- 刻度标签 45° 旋转防重叠；图例放空白区，必要时 `legend('Location','northeastoutside')`

### 常见坑（案例作者已踩平）
1. **极坐标断线**：NaN 分隔段是 MATLAB 极坐标断开的标准手法（复刻二十五网格线）；
2. **fill 顺序**：环形/扇形要按半径从外到内或逆序 patch，避免遮挡；
3. **类文件版本**：`chordChart.m`/`SSankey.m` 有多个版本（按案例目录取用，勿混用）；
4. **颜色范围**：MATLAB 颜色 0-1，取色值必须 `/255`；
5. **树状图顺序**：`dendrogram` 拿 order 后矩阵行列要同步重排（`Data(order,order)`）；
6. **统计工具箱缺失**：`ksdensity`（案例 25/17 用）需要 Statistics Toolbox；无此工具箱时用纯 MATLAB 高斯 KDE 替代（Silverman 带宽：`h=1.06*std(x)*n^(-1/5)`，已在本机 2026-08-14 验证可行，参考 `plt-demo/matlab/demoAreaBar_local.m`）。

## 四、交付物

每次完成输出：300dpi PNG + 矢量 PDF + 可复现 `.m` 脚本 + 一句"数据替换点"说明（用户数据从哪行开始改）。

## 五、数学建模场景用法（CUMCM 国赛）

### 题型→图型映射

| 题型 | 推荐图型（案例号） | 用途 |
|---|---|---|
| A 机理分析 | 环形柱状图(25)、扇形热图(21)、泰勒图(9)、热图+差异气泡(7)、环形热图(5/6) | 富集/周期/模型精度对比 |
| B 优化规划 | 桑基图(12/14/24)、冲积图(20)、哑铃图(8)、截断轴柱状图(11)、UpSet 图(26) | 流量分配/方案前后对比 |
| C 评价决策 | 雷达图(23)、K-means 分组热图(18)、环形聚类树(15)、半小提琴图(17)、分组柱状图(1) | 多指标画像/分类结构 |
| D 数据挖掘 | 弦图(4/16/19/26)、聚类热图(3/7)、旋转相关热图(10)、散点抖动(2) | 关联关系/相关性 |

### 国赛适配要点（与期刊场景的差异）
1. **字体换 SimHei**：`set(0,'DefaultAxesFontName','SimHei')`，图内中文正常显示（figure-skill 同规范）；
2. **黑白打印可读**：颜色之外加冗余编码（`FaceAlpha` 差异、`LineStyle`、填充纹理），评委可能黑白打印；
3. **中文图题**：导出后配合 LaTeX 图注（图表下方一句结论式说明），数值与正文绑定（v7 三段式）；
4. **字号放大一档**：国赛论文版面 A4 双栏，图中字号 ≥ 正文 80%，标签 14 起步。

### 与现有绘图 skill 分工（避免重复造轮子）
- `math-modeling-diagram-master`：流程图/技术路线/模型结构图（**非数据图**）→ 选型权在其；
- `figure-skill`（Python）：标准图表（折线/柱状/常规热图）国赛规范版 → 常规图用它；
- **本 skill**：需要"惊艳效果"的数据图（环形/弦图/桑基/泰勒等复杂图型）→ 升级路线；
- 规则：数据图选型冲突时按"普通→figure-skill，惊艳→nature-plot-repro"；双引擎输出目录统一 `paper/figures/`。

### 组合用法（创新分套路）
- B 题物流/调度：桑基图（流量）+ 弦图（节点耦合关系）双图联动；
- C 题评价：雷达图（指标画像）+ 半小提琴（样本分布）；
- D 题聚类：K-means 分组热图（类内结构）+ 弦图（类间关联）。
