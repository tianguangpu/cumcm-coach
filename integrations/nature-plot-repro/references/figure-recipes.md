# 图型详细配方（26 案例）

每个案例：数据格式 → 核心 API → 配色/细节要点 → 常见改动点。
路径均相对于 `assets/cases/`。案例代码保留原作者 slandarer 署名（GPL-2）。

---

## 1. 分组柱状图（复刻一）
- **数据**：`YData` 为 `组数×柱数` 矩阵；`CData` 为 `柱数×3` 颜色
- **画法**：`bar(...,'FaceColor','flat')` + `CData` 逐柱着色
- **要点**：柱面高光用渐变 patch 叠加；误差棒 `errorbar` 后置
- **改动点**：换 `YData` 与 `CData` 即可

## 2. 多面板组合图（复刻二）
- **数据**：`2022.1.15.CSV`（列：treat/day/value），或 `Data.mat`
- **元素**：折线+误差棒阴影、柱状、散点抖动（`randn` 加横坐标抖动）、灰色背景区、外部图片叠加
- **要点**：灰色背景用 `patch` 半透明；抖动散点 `scatter(x+randn.*w,y)`
- **改动点**：替换 readtable 文件名

## 3. 分层聚类热图（复刻三）
- **数据**：数值矩阵 `X`（行=样本，列=变量）→ `Data=corr(X,Y)`
- **画法**：`linkage`+`dendrogram` 左侧树；热图 `imagesc`；行/列名 `text`
- **要点**：行列按 `order` 重排；色带 `slanCM`；树与热图轴对齐
- **改动点**：`X`、`rowName`、`colName`

## 4. 弦图（复刻四）
- **数据**：`dataMat` 为 `行×列` 数值矩阵（行=下方弧块，列=上方弧块）
- **核心 API**：
  ```matlab
  CC = chordChart(dataMat, 'rowName', rowName, 'colName', colName, 'Sep', 1/80);
  CC = CC.draw();
  CC.tickState('on');                       % 刻度
  CC.setFont('FontSize',17,'FontName','Cambria');
  CC.setChordColorByMap(flipud(gray(100))); % 弦按灰度着色
  CC.setChordMN(2,4,'FaceColor',[1,0,0]);   % 指定单根弦颜色
  ```
- **标签旋转**：`findobj(gca,'Type','Text')` 后按角度规则旋转（demo3 有完整逻辑）
- **改动点**：dataMat / rowName / colName / 颜色

## 5. 环形热图+环内树状图（复刻五）
- **数据**：`Data=corr(X,Y)`；`XName`/`YName`
- **画法**：极坐标 `fill` 分段环形；树状图线画在环内圈；`CMap=slanCM(136)`
- **要点**：环分内外两圈（行/列各一圈）；树的分支延伸到对应扇区
- **改动点**：Data、Name、CLim

## 6. 分组环形热图（复刻六）
- **数据**：`Data{1..k}` 元胞，每个是子环矩阵
- **要点**：多环同心排列，环间留白；组名弧形排列
- **改动点**：Data 元胞内容

## 7. 热图+差异气泡图（复刻七）
- **数据**：`test.csv`（gene 列 + 6 样本列 + pvalue + log2fc）
- **画法**：左热图 `imagesc`，右侧差异气泡（`-log10(p)` 为 y，`log2fc` 为 x，气泡大小=显著性）
- **要点**：`negLog10pValue=-log(p)./log(10)`；气泡圆 `scatter` 大小映射
- **改动点**：CSV 结构保持一致

## 8. 水平堆叠柱+哑铃图（复刻八）
- **数据**：`ta_results_revisions_data.csv`
- **画法**：左 `barh(stacked)`；右哑铃图（`plot` 线段+两端散点）
- **要点**：左右共享 y 轴标签；哑铃端点颜色区分前后对比
- **改动点**：csv 各列语义

## 9. 泰勒图（复刻九）
- **数据**：`testData.mat` 的 `Data` 矩阵（首列=参考序列）
- **核心 API**：
  ```matlab
  STATS = SStats(参考列, 对比列);   % 得 [STD,RMSD,COR]
  TD = STaylorDiag(STATS);
  TD.set('STickValues',[0 40 80 120 170]);
  TD.SPlot(std,rmsd,cor,'Marker','o','MarkerSize',15,'Color',colorList(i,:));
  ```
- **要点**：`STaylorDiag` 是 classdef；多模型散点+图例
- **改动点**：Data 各列替换为模型输出序列

## 10. 45° 旋转三角相关热图（复刻十）
- **数据**：`Data=corr(X)`；`NameList`
- **画法**：`fill(sqX+(i-1)+(j-1), sqY-(i-1)+(j-1), Data(i,j))` 菱形格拼三角
- **要点**：`demoR45HeatmapTree.m` 版带树状图重排
- **改动点**：Data、NameList

## 11. 截断轴柱状图（复刻十一）
- **数据**：`DataA`/`DataB`（`样本×重复` 矩阵）
- **核心 API**：`truncAxis(ax,'Y',[断点范围])` 画斜切符号；柱+误差棒常规绘制
- **要点**：断点上下比例由数据范围决定；`truncAxis` 函数先于导出调用
- **改动点**：DataA/DataB/NameList

## 12. 桑基图+气泡图（复刻十二）
- **数据**：`links` 元胞 `{源, 目标, 数值}` 三元组
- **核心 API**：`SSankey(Source,Target,Value)` + `SK.draw()`；气泡 `scatter` 叠加
- **要点**：`RenderingMethod='left'/'up'` 控制流向着色
- **改动点**：links 三元组

## 13. NaN 图例地图（复刻十三）
- **数据**：GeoTIFF（案例用 southboulder.tif，未打包，自备或从原仓库取）
- **要点**：NaN 区赋 `min-(max-min)/10` 并给 colormap 前置灰色段；`nclCM(15,100)` 配色
- **依赖**：Mapping Toolbox（`readgeoraster`/`usamap`/`geoshow`）
- **改动点**：tif 路径与 NaN 阈值 `Z(Z<2100)=nan`

## 14. 右对齐桑基图（复刻十四）
- **数据**：`natureRandData.mat`
- **核心 API**：`SK=SSankey(S,T,V); SK.LayerOrder='reverse';` 实现右对齐
- **要点**：`Sep` 逐层可调 `SK.Sep=[.2,.06,...]`
- **改动点**：S/T/V 三列

## 15. 环形聚类树状图（复刻十五）
- **数据**：`Data=rand(75,3)`（样本×特征）
- **要点**：`linkage`+手工极坐标画树；`slanCL(251,1:N)` 离散配色；RSet 控制四圈半径
- **改动点**：Data、sampleName、分类数 N

## 16. 弧块单独配色弦图（复刻十六）
- **数据**：`dataMat=randi([1,15],[7,22])`（行=组织，列=基因）
- **核心 API**：`chordChart` 系列 + `setSquareF_N(i,'FaceColor',...)` 逐弧块配色
- **要点**：稀疏矩阵（<11 置 0）是弦图常见数据形态
- **改动点**：dataMat/rowName/colName

## 17. 半小提琴图（复刻十七）
- **数据**：`DataL`/`DataR`（左/右两组，`样本×类别`）
- **要点**：`ksdensity` 得密度曲线→`patch` 半边填充；显著性标注 `Condition={'ns','*','**'}`
- **改动点**：DataL/DataR/Name/Condition

## 18. K-means 分组相关热图（复刻十八）
- **数据**：`Data`（`样本×变量` 矩阵）
- **要点**：`[Class,Ind]=sort(kmeans(Data,K))` → `corr(Data(Ind,:).')`；组间白色分隔线；组名标签
- **改动点**：Data、K

## 19. 弦图+桑基图组合（复刻十九）
- **数据**：`Fig.4d.csv`（Region 列 + 数值列）或 `41467_2025_60327_MOESM6_ESM.xlsx`
- **核心 API**：`chordChart` + `biChordChart`（有向弦图）+ `SSankey` 组合布局
- **要点**：子图 Position 手工排布；三图共享配色 CList
- **改动点**：csv 列名与数值

## 20. 冲积图（复刻二十）
- **数据**：`Fig.1b.xlsx`（行=类别，列=阶段，值=占比）
- **画法**：堆叠柱状图 + 柱间流向带（`patch` 用柱的 YEndPoints 插值画贝塞尔过渡）
- **要点**：`Include_neg.m` 支持负值段；`barHdl.YEndPoints` 是流向带关键数据
- **改动点**：xlsx 内容

## 21. 扇形热图+小提琴图（复刻二十一）
- **数据**：`Data`（`年×月` 矩阵）；`VData` 小提琴数据（`样本×列`）
- **要点**：`fanHeatmap.m` 把月份展开成扇形；`createData.m` 演示季节数据构造
- **改动点**：Data、VData、年/月标签

## 22. 三角热图+树状图（复刻二十二）
- **数据**：`Data=corr(X)`（对称方阵）
- **核心 API**（classdef 类）：
  ```matlab
  Z1 = linkage(Data,'average');
  ST = STree(Z1,'MaxClust',3); ST.draw();        % 先算聚类/排序
  SM = SMatrix(Data);
  SM.RowOrder = ST.order;  SM.RowClass = ST.class;
  SM.TopLabel = 'on';  SM.TopLabelFont = {'FontSize',15,'FontName','Times New Roman'};
  ```
- **要点**：上/下三角分别放矩阵与分类条；STree 提供 order/class
- **改动点**：Data、NameList、MaxClust

## 23. 雷达图（复刻二十三）
- **数据**：`X` 为 `方案×指标` 矩阵
- **核心 API**（radarChart 类）：
  ```matlab
  RC = radarChart(X);
  RC.RLim = [-5,10];  RC.RTick = [-5,2,8,10];
  RC.PropName = {...};  RC.ClassName = {...};
  RC.CList = [r,g,b]./255;
  RC = RC.draw();  RC.legend();
  RC.setType('Patch');        % Line/Patch/Both
  ```
- **Nature 版要点**（demoNature.m）：`RC.RRange=[.1,1]` 背景区间、`RC.Rotation=pi/2`、`RC.ThetaDir='reverse'`
- **改动点**：X、PropName、ClassName、RLim/RTick

## 24. 桑基图+堆叠柱（复刻二十四）
- **数据**：`natureCommunications1.xlsx`（源/目标/数值三列）
- **核心 API**：`SK=SSankey(Data(:,1),Data(:,2),Data(:,3)); SK.LabelLocation='left'; SK.draw(); SK.setLabelLocation(3,'right');`
- **要点**：`demoNatureCom.m` 是桑基+堆叠柱组合版
- **改动点**：xlsx 三列

## 25. 环形柱状图+核密度面积图（复刻二十五）
- **数据**：`Name`（基因名）、`Value`（富集数）、`Class`（分类）、`Num`（密度图数据）
- **环形柱要点**：极坐标手工画网格（NaN 断开）+ 柱子 `patch`（内外半径 R±r，角度∝Value）；顶部数字 `text`
- **密度图要点**：`ksdensity` 按 Class 分色 + `area`/`fill` 填充；`CList=[235,173,189;123,166,211]./255`（粉蓝配色）
- **改动点**：Name/Value/Class/Num；柱子长度可独立于标注数值（长度=显著性，数字=数量）

## 26. UpSet 图+弦图（复刻二十六）
- **数据**：`gene.csv`（0/1 集合矩阵）；`adjMat.csv`（弦图邻接矩阵）
- **核心 API**：
  ```matlab
  USP = UpSetPlot(fig, setMat, 'SetName', setName);
  USP.BarColorI = [0,0,0];  USP.BarColorS = [0,0,0];
  CC = chordChart(adjMat, 'RowName',rowName, 'ColName',colName);
  CC.SRadius = [1.025,1.15];  CC.draw();
  CC.setSquareColorF([...]./255);  CC.setChordColorBySquareF();
  ```
- **要点**：`demoCombin.m` 是 Nature 论文组合版（Mayassi et al. Nature 636, 2024）
- **改动点**：gene.csv 列（集合）、adjMat.csv

---

## 配色函数速查

| 函数 | 数据文件 | 用法 | 典型值 |
|---|---|---|---|
| `slanCM(type,num)` | slanCM_Data.mat | 连续色带 | `slanCM(136)` 紫绿发散；`slanCM('viridis')` 按名 |
| `slanCL(type,num)` | slanCL_Data.mat | 离散色板 | `slanCL(251,1:N)` |
| `nclCM(type,num)` | nclCM_Data.mat | NCL 科学色 | `nclCM(15,100)` 地形蓝绿棕 |

调用前确保 `.mat` 与 `.m` 在同一目录。

## 快速改造模板

```matlab
% ==== 用户数据入口（只改这里）====
% Data = readtable('用户数据.csv');   % 或直接赋值矩阵
% ================================
% 以下沿用案例原布局/配色代码
```

数据列数不匹配时优先保持矩阵形状一致，其次调 demo 中 `N`/`M` 参数。
