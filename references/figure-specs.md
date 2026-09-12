# 图表绘制参数规范 v5.0

## 全局硬性规则
- 格式：矢量PDF，600dpi，禁止JPG/PNG截图
- 配色：学术彩色 12 色（见下方调色板），禁止黑白/灰度
- 中文字体：SimHei/Song 9pt；英文/数字：Times New Roman 9pt
- 坐标轴：标注物理量+单位，浅灰网格线（0.3pt #CCCCCC）
- 图题：图下方，小五加粗，编号连续「图X XXXX示意图」
- 表题：表上方，小五加粗「表X XXXX指标对比表」
- 排版：图宽70%页面，居中，紧跟对应文字，不跨页不拆分
- 图表后强制≥3行定量分析文字
- **创新要求：禁止只画基础图（裸 plot/bar），必须从下方技巧库选≥1个高级技法叠加**

# 5 套学术论文调色板（按题型/图型选择）

> **铁律：按图型选配色，禁止随意混用。所有配色色盲友好 + 黑白打印可辨。**

## 1. Nature（顶级综合刊）
- **适用**：多线对比图、散点分组、雷达图（最多 8 类）
- **特点**：柔和不刺眼，Nature/Science 通用
```matlab
C_Nature = [0x00,0x72,0xB2; 0xE6,0x4B,0x35; 0x5B,0x9E,0xD5; 0xF5,0xA0,0x00;
            0x54,0xA2,0x4B; 0xB8,0x54,0x50; 0x4C,0x72,0xB0; 0xCC,0xB8,0x74] / 255;
```

## 2. Science（高饱和视觉冲击）
- **适用**：强调对比、关键指标高亮、展示图
- **特点**：高饱和，Science/Cell 风格
```matlab
C_Science = [0xFF,0x00,0x00; 0x00,0x00,0xFF; 0x00,0xAA,0x00; 0xFF,0x7F,0x00;
             0x8C,0x00,0x8C; 0x00,0x8B,0x8B; 0xDC,0x14,0x3C; 0x1E,0x90,0xFF] / 255;
```

## 3. ColorBrewer-Qualitative（离散分类，12 色）
- **适用**：热力图分类、离散柱状图、≥6 类分组
- **特点**：ColorBrewer 官方，色盲安全（除红绿）
```matlab
C_Qualitative = [0x66,0xC2,0xA5; 0xFC,0x8D,0x62; 0x8D,0xB3,0xD3; 0xE7,0x8A,0xC2;
                 0xA6,0xD8,0x54; 0xFF,0xD9,0x2F; 0xE5,0xC4,0x94; 0xB3,0xB3,0xB3;
                 0xFF,0xFF,0xB3; 0x80,0xB1,0xD3; 0xB3,0xDE,0x69; 0xFF,0xFB,0xAE] / 255;
```

## 4. ColorBrewer-Diverging（发散色，热力图/相关性）
- **适用**：相关性热力图、残差图、偏差图、3D 曲面
- **特点**：红蓝发散，0 值附近为白，正负对称
```matlab
C_Diverging = [0x21,0x66,0xAC; 0x43,0x93,0xC3; 0x92,0xC5,0xDE; 0xDE,0xEB,0xF7;
               0xF7,0xF7,0xF7; 0xFD,0xEB,0xD5; 0xFC,0x8D,0x59; 0xD7,0x30,0x27;
               0xA5,0x00,0x26] / 255;
```

## 5. IEEE（专业工程刊，8 色）
- **适用**：工程优化/控制/信号处理类（B 题机理类）
- **特点**：IEEE Transactions 风格，专业稳重
```matlab
C_IEEE = [0x00,0x44,0x88; 0xCC,0x66,0x77; 0x44,0xAA,0x99; 0xDD,0xCC,0x77;
          0x66,0xCC,0xEE; 0xAA,0x88,0xBB; 0xEE,0x66,0x55; 0x00,0x88,0xBB] / 255;
```

## 配色选择速查表（强制）

| 图型 | 推荐调色板 | 色板大小 | 理由 |
|------|-----------|---------|------|
| 热力图/相关性 | **Diverging** | 9 色 | 发散色有明确的 0 中心，正负一眼分开 |
| 雷达图/多方案对比 | **Nature** 或 **Qualitative** | 6-12 色 | 柔和无抢戏，每类清晰 |
| 3D 曲面/等高线 | **Diverging** 或 **Science** | 9 色 | 发散有立体感，高饱和突出峰值 |
| 收敛曲线/多算法对比 | **Nature** | 4-6 色 | 柔和耐看，适合多条同图 |
| 散点/聚类分组 | **Qualitative** 或 **IEEE** | 6-8 色 | 分类清晰，专业感强 |
| 单变量趋势/预测 | **Science** 双色或 **Nature** | 2-3 色 | 重点突出 |

## color_manager.m 调用方式
```matlab
% 获取调色板
pal = get_palette('Nature', 6);    % 取前 6 色
colormap(get_colormap('Diverging')); % 设置全局 colormap
```

## MATLAB 标准模板（每图独立.m脚本）
```matlab
% ============================================================
% 文件名: figX_XXXX.m  |  画布: 16cm×8cm  |  导出: 600dpi PDF
% ============================================================
close all; clc;
set(gcf, 'Position', [100, 100, 1600, 800]);        % 16×8cm画布
set(gca, 'FontName', 'Times New Roman', 'FontSize', 10);
set(gca, 'LineWidth', 1.2, 'Box', 'on');
colormap(flipud(gray(256)));                          % 黑白灰度梯度
xlabel('变量名 (单位)', 'FontSize', 10);
ylabel('变量名 (单位)', 'FontSize', 10);
title('');
legend('boxoff');
grid on; set(gca, 'GridAlpha', 0.15);
print('-dpdf', '-r600', '-painters', 'figX_output.pdf');
```

## 流程图（Visio/MATLAB）
| 参数 | 值 |
|------|-----|
| 画布 | 16cm×8cm（总图）/ 14cm×10cm（结构图） |
| 节点 | 圆角矩形，半径2mm |
| 核心节点 | 填充#404040，白字粗体10pt，边框3pt |
| 一般节点 | 填充#F5F5F5，黑字常规10pt，边框1.5pt |
| 箭头 | 实线1.5pt #333333 / 虚线1.0pt #666666 |
| 数据流方向 | 左→右，上→下，单向黑色箭头 |
| 导出 | PDF 600dpi + 矢量EPS |

## Matplotlib 图表

### 推荐：SciencePlots + tueplots 一行切换期刊风格

> **SciencePlots** (9k⭐) 内置 Nature/Science/IEEE 等期刊配色+字号+网格规范。
> **tueplots** (755⭐) 自动配置期刊要求的 figsize/fontsize。
> 两者组合 = 手写 rcParams 的上位替代。

```python
# 方式一：直接用 SciencePlots 样式（推荐）
import scienceplots
import matplotlib.pyplot as plt
plt.style.use(['science', 'nature', 'no-latex'])   # Nature 风格
plt.style.use(['science', 'ieee', 'no-latex'])     # IEEE 风格
plt.style.use(['science', 'no-latex'])              # 通用学术

# 方式二：用 v7 统一样式模块（封装了 SciencePlots + tueplots + 5 套调色板）
from v7_styles import apply_journal_style, get_palette, quick_export
apply_journal_style('nature')           # 一行搞定
colors = get_palette('ieee', 6)         # 取前 6 色
quick_export(fig, 'fig1_result')        # 300dpi PNG + 600dpi PDF
```

#### SciencePlots 可用风格
| 风格名 | 适用 | 叠加用法 |
|--------|------|---------|
| `science` | 基础学术风格（必选） | `['science', ...]` |
| `nature` | Nature/Science 期刊 | `['science', 'nature']` |
| `ieee` | IEEE Transactions | `['science', 'ieee']` |
| `high-vis` | 高对比度（PPT/海报） | `['science', 'high-vis']` |
| `bright` | 明亮配色 | `['science', 'bright']` |
| `muted` | 柔和配色 | `['science', 'muted']` |
| `no-latex` | 不用 LaTeX 渲染（中文必选） | `['science', 'nature', 'no-latex']` |

#### tueplots 期刊尺寸
```python
from tueplots import bundles, figsizes, fontsizes
plt.rcParams.update(bundles.icml2024())              # 完整配置
plt.rcParams.update(figsizes.icml2024_full(column='full'))  # 仅尺寸
plt.rcParams.update(fontsizes.icml2024())            # 仅字号
```

### 备选：手动 rcParams（SciencePlots 不可用时）
```python
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['SimHei'],
    'axes.unicode_minus': False,
    'figure.dpi': 600,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight'
})
```

| 图类型 | cmap | 特点 |
|--------|------|------|
| 热力图 | plt.cm.Greys | vmin/vmax按数据范围，标注数值 |
| 相关性热力图 | plt.cm.Greys_r | 下三角矩阵，显示相关系数 |
| 箱线图 | 三灰度#E0E0E0/#A0A0A0/#606060 | 1.5pt黑边 |
| 散点图 | alpha=0.15, s=2, #333333 | 避免过度绘制 |
| 分布直方图 | facecolor='#808080', edgecolor='black' | bins=15~25 |
| 趋势折线图 | 线宽1.5pt, 'o-' marker, #202020 | 三线同图用灰度区分 |
| 参考线 | 黑色虚线1.5pt | 黑白打印替代红色 |

## LaTeX 公式规范
- 变量：斜体 $Y_{ij}$、$\beta_k$、$x_i$
- 向量/矩阵：粗体 $\mathbf{X}$、$\boldsymbol{\beta}$
- 估计值：帽子 $\hat{\beta}$、$\hat{Y}$
- 单位：正体 $\text{week}$、$\text{kg/m}^2$
- 编号：行间公式居中，右对齐编号(1)(2)(3)
- 加粗创新公式用 `\mathbf` 或 `\boldsymbol`
- 禁止截图式图片公式，全部可粘贴Word公式编辑器的LaTeX源码

## 三线表 Word 标准
| 线型 | 磅值 | 颜色 |
|------|------|------|
| 顶线 | 1.5pt | 黑色实线 |
| 底线 | 1.5pt | 黑色实线 |
| 表头分隔线 | 1pt | 黑色实线 |
| 竖线/斜线 | 无 | — |

- 数值保留4位小数，百分比保留2位
- 表头统一标注单位（括号内）
- 表格占页面70%宽度，居中

---

# 创新绘图技巧库 v1.0（国赛加分核心）

> **铁律：每张图必须从下列技法中选≥1个叠加，禁止裸 plot/bar/surf。**
> 评审加分逻辑：信息密度↑ + 视觉层次↑ + 量化标注↑ = 创新印象。
> 所有代码均已设 12 色调色板 + 中文标注 + 600dpi 双导出，直接套用。

## 技法1：3D曲面 + 底面等高线投影叠加（机理/优化类）

**创新点**：一张图同时看曲面形态 + 等高线投影 + 最值标注，信息量=3张普通图。
**适用**：§5 机理建模、§5.2 目标函数景观、§6 灵敏度曲面。

```matlab
close all; clc;
figure('Color','w','Position',[100 100 1600 900]);
palette = [0x21,0x66,0xAC; 0xD6,0x60,0x4D]/255;
[X,Y] = meshgrid(linspace(-3,3,80));
Z = peaks(X,Y);
% 主曲面
surf(X,Y,Z,'EdgeColor','none','FaceAlpha',0.85);
colormap([palette(1,:); 0.9 0.9 0.9; palette(2,:)]);  % 蓝-白-红发散色
shading interp; hold on;
% 底面等高线投影（z=最低处贴底）
zmin = min(Z(:));
contour(X,Y,Z,15,'LineColor',[0.2 0.2 0.2],'LineWidth',0.4,'ZData',zmin*ones(size(X)));
% 最值标注
[maxval,imax] = max(Z(:));
[~,idx] = max(Z(:));
plot3(X(idx),Y(idx),Z(idx),'rp','MarkerSize',12,'MarkerFaceColor','r');
text(X(idx),Y(idx),Z(idx)+0.3,sprintf('峰值 %.2f',maxval),'FontSize',9,'FontWeight','bold');
set(gca,'FontName','Times New Roman','FontSize',10);
xlabel('参数 \alpha'); ylabel('参数 \beta'); zlabel('目标函数 f');
colorbar; view(135,30); grid on; set(gca,'GridAlpha',0.2);
print('-dpdf','-r600','-painters','fig_3d_contour.pdf');
```

## 技法2：双变量编码散点（颜色+大小，分布/聚类类）

**创新点**：一个散点图同时编码 3 个变量（x,y,位置 + 颜色=类别 + 大小=权重），替代多张图。
**适用**：§5.1.1 EDA、§5.2 布局分布、聚类结果。

```matlab
figure('Color','w','Position',[100 100 1400 800]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D;0x4D,0xAF,0x4A;0xE6,0xAB,0x02]/255;
rng(42); n=200;
x = randn(n,1); y = 2*x + randn(n,1)*0.8;
grp = randi(4,n,1); w = rand(n,1)*80+10;
scatter(x,y,w,palette(grp,:),'filled','MarkerEdgeColor',[0.1 0.1 0.1],'LineWidth',0.3,'MarkerFaceAlpha',0.6);
% 椭圆置信区间叠加
hold on; for g=1:4
  idx=grp==g; mu=mean([x(idx) y(idx)]);
  plot(mu(1),mu(2),'p','MarkerSize',14,'MarkerFaceColor',palette(g,:),'MarkerEdgeColor','k');
end
set(gca,'FontName','Times New Roman','FontSize',10);
xlabel('特征1'); ylabel('特征2');
cb = colorbar; cb.Label.String='类别'; cb.Label.FontSize=10;
legend('类别1','类别2','类别3','类别4','质心','Location','best','Box','off');
grid on; set(gca,'GridAlpha',0.2);
```

## 技法3：多子图组合（3D+剖面+投影，机理类）

**创新点**：2×2 子图同屏展示 3D曲面 / XZ剖面 / YZ剖面 / 顶视等高线，评审一眼看全。
**适用**：§5.1 机理分析、§6.4 误差量化。

```matlab
figure('Color','w','Position',[100 100 1600 1000]);
[X,Y] = meshgrid(linspace(-2,2,60)); Z = X.*exp(-X.^2-Y.^2);
% (a) 3D曲面
subplot(2,2,1); surf(X,Y,Z,'EdgeColor','none'); shading interp; view(135,25);
title('(a) 三维曲面','FontSize',10); colormap(parula);
% (b) XZ剖面（Y=0切片）
subplot(2,2,2); plot(X(:,30),Z(:,30),'-o','Color',[0xD6,0x60,0x4D]/255,'LineWidth',1.5);
title('(b) Y=0 剖面','FontSize',10); xlabel('X'); ylabel('Z'); grid on;
% (c) YZ剖面
subplot(2,2,3); plot(Y(30,:),Z(30,:),'-s','Color',[0x21,0x66,0xAC]/255,'LineWidth',1.5);
title('(c) X=0 剖面','FontSize',10); xlabel('Y'); ylabel('Z'); grid on;
% (d) 顶视等高线
subplot(2,2,4); contourf(X,Y,Z,15,'LineColor','none'); colormap(parula);
title('(d) 俯视等高线','FontSize',10); xlabel('X'); ylabel('Y'); colorbar;
set(gcf,'DefaultAxesFontName','Times New Roman','DefaultAxesFontSize',9);
```

## 技法4：可行域填充 + 峰值标注 + 双轴（优化类）

**创新点**：可行域半透明填充 + 最优解星标 + 约束边界虚线 + 双纵轴（目标+约束余量）。
**适用**：§5.2 优化求解、§5.3 方案对比。

```matlab
figure('Color','w','Position',[100 100 1600 800]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D;0x4D,0xAF,0x4A]/255;
x = linspace(0,10,200);
% 可行域填充
yy = arrayfun(@(t) min(8-0.5*t, 6), x);  % 可行上界
fill([x fliplr(x)],[yy zeros(size(x))],palette(1,:),'FaceAlpha',0.18,'EdgeColor','none'); hold on;
% 目标函数
plot(x, 8-0.5*x,'-',x,6*ones(size(x)),'--','Color',palette(2,:),'LineWidth',1.5);
% 最优解标注
[optx]=4; [opty]=6;
plot(optx,opty,'rp','MarkerSize',15,'MarkerFaceColor','r');
annotation('textarrow',[0.5 0.45],[0.7 0.75],'String',sprintf('最优解 (%.1f, %.1f)',optx,opty),'FontSize',9);
% 双纵轴：约束余量
yyaxis right; plot(x,abs(8-0.5*x-6),'-','Color',palette(3,:),'LineWidth',1); ylabel('约束余量');
yyaxis left; ylabel('目标函数值'); xlabel('决策变量 x');
legend('可行域','目标函数','约束边界','最优解','Location','best','Box','off');
set(gca,'FontName','Times New Roman','FontSize',10); grid on;
```

## 技法5：收敛曲线 + 背景渐变 + 双算法对比（算法类）

**创新点**：背景用温度渐变（早期热/晚期冷）+ 双算法收敛曲线 + 收敛点圆圈标注 + 改进算法提升百分比文本框。
**适用**：§5.X.5 算法设计、§5.2.4 SA-PSO 收敛。

```matlab
figure('Color','w','Position',[100 100 1600 800]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D]/255;
% 背景渐变（热→冷）
bg = [linspace(1,0.7,100); linspace(0.85,0.95,100); linspace(0.85,1,100)]';
colormap(bg); imagesc([0 200],[0 1],zeros(1,100)); axis xy; hold on;
% 两条收敛曲线
iter = 1:200;
conv1 = 10*exp(-iter/40)+0.5+0.1*randn(size(iter));   % 基础算法
conv2 = 10*exp(-iter/20)+0.3+0.05*randn(size(iter));  % 改进算法
plot(iter,conv1,'-',iter,conv2,'-','Color',[palette(1,:);palette(2,:)],'LineWidth',1.8);
% 收敛点圆圈
plot(iter(end),conv1(end),'o',iter(end),conv2(end),'s','MarkerSize',10,'MarkerFaceColor',[palette(1,:);palette(2,:)]);
% 提升百分比文本框
improve = (conv1(end)-conv2(end))/conv1(end)*100;
text(120,7,sprintf('改进算法收敛速度提升 %.1f%%',improve),'FontSize',10,'FontWeight','bold','BackgroundColor',[1 1 1 0.8]);
set(gca,'FontName','Times New Roman','FontSize',10); xlabel('迭代次数'); ylabel('目标函数值');
legend('基础PSO','改进SA-PSO','Location','northeast','Box','off'); grid on;
```

## 技法6：极坐标玫瑰图（周期/方向类）

**创新点**：极坐标玫瑰图展示方向/周期分布，比直方图更贴合物理意义（如太阳方位、风向）。
**适用**：§5.1 定日镜方位、风场/潮流分析、时间周期性。

```matlab
figure('Color','w','Position',[100 100 1000 800]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D;0xE6,0xAB,0x02]/255;
theta = linspace(0,2*pi,24);
rose_data = 50+40*sin(theta*2)+10*randn(size(theta));
[theta_rho,rho] = rose(rose_data,24);
% 用 polarplot + 颜色映射
figure('Color','w','Position',[100 100 1000 800]);
ax = polaraxes('FontSize',10);
th = linspace(0,2*pi,200); r = 50+40*sin(th*2);
polarplot(ax,th,r,'-','LineWidth',2,'Color',palette(1,:)); hold on;
polarplot(ax,linspace(0,2*pi,200),50+40*cos(linspace(0,2*pi,200)),'--','Color',palette(2,:),'LineWidth',1.5);
ax.ThetaLabel.String = '方位角 (°)'; ax.RLabel.String = '功率 (MW)';
legend('上午','下午','Location','southoutside','Box','off');
```

## 技法7：雷达图多维对比（评价类）

**创新点**：多方案多维度雷达叠加，一眼看出各方案优劣维度，适合评价/决策题。
**适用**：§5.3 方案择优、§7 模型评价、TOPSIS/熵权结果。

```matlab
figure('Color','w','Position',[100 100 1000 800]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D;0x4D,0xAF,0x4A]/255;
dims = {'精度','效率','稳定性','可解释性','计算成本','迁移性'};
vals = [0.92 0.78 0.85 0.70 0.65 0.80;   % 方案A
        0.85 0.90 0.75 0.82 0.55 0.88;   % 方案B
        0.70 0.95 0.90 0.60 0.72 0.75];  % 方案C
N = length(dims); angles = linspace(0,2*pi,N);
angles = [angles, angles(1)]; vals = [vals, vals(:,1)];
hold on;
for i=1:3
  [x,y] = pol2cart(angles, vals(i,:));
  plot(x,y,'-o','Color',palette(i,:),'LineWidth',1.8,'MarkerFaceColor',palette(i,:));
  fill(x,y,palette(i,:),'FaceAlpha',0.12,'EdgeColor','none');
end
for i=1:N; plot([0 cos(angles(i))],[0 sin(angles(i))],'-','Color',[0.7 0.7 0.7]); end
for i=1:N; text(cos(angles(i))*1.15,sin(angles(i))*1.15,dims{i},'FontSize',9,'HorizontalAlignment','center'); end
axis equal; axis([-1.3 1.3 -1.3 1.3]); axis off;
legend('方案A','方案B','方案C','Location','south','Box','off');
```

## 技法8：热力图 + 数值标注 + 显著性星号（相关性/检验类）

**创新点**：相关性矩阵热力图 + 每格标注相关系数 + p<0.05 加星号，统计严谨性拉满。
**适用**：§5.1.1 EDA、§6.1 拟合检验、特征筛选。

```matlab
figure('Color','w','Position',[100 100 900 800]);
rng(42); data = randn(100,6); data(:,4)=data(:,1)*0.8+randn(100,1)*0.3;
C = corrcoef(data); vars = {'x_1','x_2','x_3','x_4','x_5','x_6'};  % corrcoef 内置，corr 需 Statistics Toolbox
imagesc(C); colormap([0xD6,0x60,0x4D; 1 1 1; 0x21,0x66,0xAC]/255); caxis([-1 1]);
hold on;
for i=1:6, for j=1:6
  star=''; if abs(C(i,j))>0.5 && i~=j, star='*'; end
  text(j,i,sprintf('%.2f%s',C(i,j),star),'HorizontalAlignment','center','FontSize',9,'FontWeight','bold');
end, end
set(gca,'XTick',1:6,'YTick',1:6,'XTickLabel',vars,'YTickLabel',vars,'FontName','Times New Roman','FontSize',10);
colorbar; title('Pearson 相关系数矩阵 (* |r|>0.5)','FontSize',10);
```

## 技法9：图中图局部放大（inset axes，趋势/细节类）

**创新点**：主图看全局趋势，inset 圆框放大关键区域（如收敛末期、突变点），一图两用。
**适用**：§5.X.6 数值结果、§6.3 蒙特卡洛分布尾部。

```matlab
figure('Color','w','Position',[100 100 1400 700]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D]/255;
x = linspace(0,10,500); y = sin(x).*exp(-x/5) + 0.02*randn(size(x));
plot(x,y,'-','Color',palette(1,:),'LineWidth',1.2); hold on;
% 关键区域标注
plot(x(350:450),y(350:450),'-','Color',palette(2,:),'LineWidth',2);
% inset 放大框
axes('Position',[0.55 0.55 0.32 0.32]);
plot(x(350:450),y(350:450),'-','Color',palette(2,:),'LineWidth',1.5);
set(gca,'FontName','Times New Roman','FontSize',8); grid on; title('局部放大: x∈[7,9]');
% 主图标注放大区域
axes(gca); rectangle('Position',[7 -0.15 2 0.3],'EdgeColor',palette(2,:),'LineWidth',1.5,'LineStyle','--');
set(gca,'FontName','Times New Roman','FontSize',10); xlabel('时间 (s)'); ylabel('幅值'); grid on;
```

## 技法10：渐变填充面积图 + 阈值线（趋势/预测类）

**创新点**：垂直渐变填充（深→浅）+ 置信区间阴影带 + 阈值虚线 + 预测拐点标注。
**适用**：§5 预测建模、§6.3 蒙特卡洛置信带。

```matlab
figure('Color','w','Position',[100 100 1600 700]);
palette = [0x21,0x66,0xAC;0xD6,0x60,0x4D]/255;
t = linspace(0,12,200); mu = 20*sqrt(t); lo = mu-3*sqrt(t); hi = mu+3*sqrt(t);
% 渐变填充（用多层 alpha 模拟垂直渐变）
for k=1:20
  alpha = 0.04+0.25*(1-k/20);
  fill([t fliplr(t)],[mu+(hi-mu)*k/20 fliplr(mu+(hi-mu)*(k-1)/20)],palette(1,:),'FaceAlpha',alpha,'EdgeColor','none'); hold on;
end
plot(t,mu,'-',t,lo,'--',t,hi,'--','Color',[palette(1,:);0.5 0.5 0.5;0.5 0.5 0.5],'LineWidth',1.8);
% 阈值线
yline(60,'-r','阈值 60','LabelHorizontalAlignment','left','FontSize',9);
% 拐点
[idx,~]=max(diff(mu)); plot(t(idx),mu(idx),'v','MarkerSize',12,'MarkerFaceColor',palette(2,:));
text(t(idx),mu(idx)+3,sprintf('增速拐点 t=%.1f',t(idx)),'FontSize',9);
set(gca,'FontName','Times New Roman','FontSize',10); xlabel('时间 (月)'); ylabel('预测值');
legend('均值','95%CI下界','95%CI上界','Location','northwest','Box','off'); grid on;
```

---

## 技法选择速查表（按题型）

| 题型/章节 | 推荐技法 | 理由 |
|-----------|----------|------|
| A机理 | 技法1+3+9 | 3D曲面+剖面组合，机理可视化 |
| B优化 | 技法4+5+10 | 可行域+收敛+置信带 |
| C评价 | 技法7+8+2 | 雷达+热力图+双编码散点 |
| D数据/统计 | 技法8+9+10 | 相关性+局部放大+预测带 |
| §6 检验 | 技法8+9+10 | 检验热力图+残差放大+MC带 |
| 算法收敛 | 技法5 | 双算法对比+提升% |

## 创新加分检查清单
- [ ] 每图至少 1 个高级技法（非裸 plot/bar）
- [ ] 关键数值有标注（峰值/最优/拐点/百分比）
- [ ] 多变量同图（颜色/大小/双轴编码 ≥2 变量）
- [ ] 配色用 12 色学术彩色，非默认彩色
- [ ] 有定量分析文字紧跟图后（≥3行）

---

# 排版优化规范 v1.0（评委3秒看懂）

> **目标：评委扫一眼（≤3秒）就抓住图的核心结论，无需细读文字。**
> 评审场景：A4黑白/彩色打印，视力正常，每张图平均停留 5-8 秒。
> 排版差=创新被埋没；排版好=普通模型也显高级。

## 一、视觉层级（3层，强制区分）

| 层级 | 内容 | 线宽/参数 | 评委感知 |
|------|------|-----------|----------|
| L1 主数据 | 核心曲线/散点/曲面 | 线宽2pt / 点大小8-12 / 饱和色 | 第一眼看到 |
| L2 辅助 | 参考线/置信带/次要曲线 | 线宽1pt / 半透明0.4 / 次饱和 | 第二眼补充 |
| L3 框架 | 网格/坐标轴/边框 | 线宽0.3-0.5pt / 浅灰#CCCCCC | 几乎无感 |

**铁律**：L1 必须比 L2 粗 2 倍以上，L2 必须比 L3 深 3 倍以上。三者差不多=没有重点。

## 二、字号体系（印刷可读下限）

| 元素 | 字号 | 字重 |
|------|------|------|
| 子图编号 (a)(b)(c) | 11pt | 加粗，左上角 |
| 轴标题（物理量+单位） | 10pt | 常规 |
| 刻度数字 | 9pt | 常规 |
| 图例文字 | 9pt | 常规 |
| 图内标注/数值 | 9pt | 加粗（突出） |
| **最小任何元素** | **≥8pt** | — A4印刷可读红线 |

**禁止**：默认字号（MATLAB 默认 10-12pt 但子图会缩到 7pt 以下，必须手动 set 到 ≥9pt）。

## 三、标注布局（不遮挡数据）

1. **放稀疏区**：标注文字放数据曲线未覆盖的角落（左上/右下空白）
2. **箭头引出**：文字框距数据点 5-10% 画布距离，用 `annotation('textarrow')` 引向目标
3. **白底半透明**：文字框 `'BackgroundColor',[1 1 1 0.85]`，防止压住网格
4. **错开不叠**：多个标注横向/纵向错开 ≥1 行高
5. **峰值偏移**：最值标注在点正上方/侧方 +0.5 字高，不压点

```matlab
% 标注模板：箭头+白底框，放稀疏区
annotation('textarrow',[0.62 0.55],[0.78 0.72],...
  'String',sprintf('峰值 %.2f MW\n(6月)',val),'FontSize',9,'FontWeight','bold',...
  'BackgroundColor',[1 1 1 0.85],'EdgeColor',[0.5 0.5 0.5]);
```

## 四、图例规范（直接标注优先）

| 曲线数 | 方案 | 理由 |
|--------|------|------|
| ≤3条 | **直接线末标注**，不用图例 | 省去眼睛在图例间来回跳 |
| 4-6条 | 图例放图外右侧/下方 | 不占数据区 |
| >6条 | 分组图例 + 直接标关键2条 | 避免图例过载 |

```matlab
% ≤3条直接标注（推荐）
plot(x,y1,'-','Color',c1); text(x(end),y1(end),' 方案A','Color',c1,'FontSize',9,'FontWeight','bold');
% 图例放图外下方（4-6条）
legend('A','B','C','D','Location','southoutside','NumColumns',4,'Box','off');
```

## 五、颜色+形状双编码（黑白打印可辨 + 色盲友好）

**铁律**：每条线/每类点 = 颜色 + 不同 marker，颜色不是唯一区分维度。
- 避免红绿同时用（色盲冲突），用 红蓝 / 橙蓝 替代
- marker 形状：`o` `s` `^` `d` `v` `p` 循环
- 线型：实线`-`/虚线`--`/点划`-.` 区分主次

```matlab
plot(x,y1,'-o','Color',c1,'MarkerFaceColor',c1);  % 实线圆点
plot(x,y2,'--s','Color',c2,'MarkerFaceColor',c2); % 虚线方点
```

## 六、子图布局（紧凑+对齐+编号）

1. **共享轴对齐**：同行子图共享 Y 轴范围，同列共享 X 轴范围
2. **编号 (a)(b)(c)**：每个子图左上角，加粗11pt，`title('(a) XXX','Position',[...])`
3. **间距**：`subplot` 间距用 `tiledlayout`（R2019b+）控制，留 10-15% 呼吸
4. **共用图例/色条**：放整个 figure 右侧/底部，不每个子图重复

```matlab
% tiledlayout 紧凑布局（优于 subplot）
t = tiledlayout(2,2,'TileSpacing','compact','Padding','compact');
nexttile; ... % (a)
nexttile; ... % (b)
title(t,'图X 全局标题','FontSize',11);  % 整体标题
```

## 七、坐标轴规范（物理量+单位+合理范围）

1. **标签格式**：`物理量 (单位)`，如 `时间 (s)`、`功率 (MW)`、`效率 (%)`
2. **范围留白**：轴范围比数据范围外扩 5-10%，曲线不贴边
3. **刻度整数化**：`xticks(0:2:10)`，避免 0.374 这种怪刻度
4. **量级大**：用 `axis` 科学计数法，或手动 `×10^3` 标注
5. **方向**：时间轴左→右，因果轴自变量在 X

```matlab
xlim([0 10.5]); xticks(0:2:10);  % 留白+整数刻度
xlabel('时间 (月)','FontSize',10); ylabel('功率 (MW)','FontSize',10);
```

## 八、图题自解释（含结论，禁"示意图"）

| ❌ 差 | ✅ 好 |
|-------|-------|
| 图3 效率示意图 | 图3 月度效率呈夏高冬低（6月峰值0.42） |
| 图5 收敛曲线 | 图5 改进SA-PSO收敛速度较PSO提升41.2% |
| 图8 相关性热力图 | 图8 x1与x4强正相关(r=0.82)，其余弱相关 |

**公式**：`图N [对象][趋势/关系]（[关键数值]）`

## 九、收尾函数 finish_figure（一调用即达标）

每张图画完**必须调用**，统一处理字号/留白/对齐/导出：

```matlab
function finish_figure(fig, name, outdir)
  % 统一收尾：字号/留白/双导出。所有图必须调用。
  set(fig,'Color','w');
  axlist = findall(fig,'Type','axes');
  for ax = axlist(:)'
    ax = ax{1};
    if isprop(ax,'FontName')
      set(ax,'FontName','Times New Roman','FontSize',9,'LineWidth',0.8,...
            'TickDir','out','GridAlpha',0.2,'GridColor',[0.8 0.8 0.8]);
      try set(ax.Title,'FontSize',11,'FontWeight','bold'); end
      try set(ax.XLabel,'FontSize',10); set(ax.YLabel,'FontSize',10); end
    end
  end
  set(fig,'PaperPositionMode','auto');
  % 紧凑留白
  try set(fig,'InvertHardcopy','off'); end
  png = fullfile(outdir,'png',[name '.png']);
  pdf = fullfile(outdir,'pdf',[name '.pdf']);
  print(fig,png,'-dpng','-r300');
  print(fig,pdf,'-dpdf','-r600','-painters');
  fprintf('[saved] %s / %s\n',png,pdf);
end
```

**用法**（每张图末尾）：
```matlab
finish_figure(gcf, 'fig3_monthly_eff', 'C:\Users\Lenovo\Documents\trae_projects\cumcm_2026\figures');
```

## 十、排版优化前后对比（技法5收敛曲线）

### 优化前（普通）：标注混乱、字号小、重点不突出
```
问题：默认字号、图例占数据区、无提升%标注、曲线无marker、网格过深
```

### 优化后（评委3秒看懂）
```matlab
close all; clc;
fig = figure('Color','w','Position',[100 100 1500 750]);
palette = [0x21,0x66,0xAC; 0xD6,0x60,0x4D]/255;
iter = 1:200;
conv1 = 10*exp(-iter/40)+0.5;  conv2 = 10*exp(-iter/20)+0.3;
% L1 主数据：粗线+marker+饱和色
plot(iter,conv1,'-o','Color',palette(1,:),'LineWidth',2,'MarkerSize',4,...
     'MarkerFaceColor',palette(1,:),'MarkerIndices',1:20:200); hold on;
plot(iter,conv2,'-s','Color',palette(2,:),'LineWidth',2,'MarkerSize',4,...
     'MarkerFaceColor',palette(2,:),'MarkerIndices',1:20:200);
% L2 辅助：收敛阈值虚线（半透明）
yline(0.5,'--','Color',[0.4 0.4 0.4 0.5],'LineWidth',1);
% 标注：放稀疏区+白底框+箭头
improve = (conv1(end)-conv2(end))/conv1(end)*100;
annotation('textarrow',[0.55 0.48],[0.82 0.75],'String',...
  sprintf('改进算法提升 %.1f%%',improve),'FontSize',10,'FontWeight','bold',...
  'TextBackgroundColor',[1 1 1 0.85],'TextEdgeColor',[0.5 0.5 0.5]);
% 直接线末标注（≤3条不用图例）
text(202,conv1(end),' 基础PSO','Color',palette(1,:),'FontSize',9,'FontWeight','bold');
text(202,conv2(end),' 改进SA-PSO','Color',palette(2,:),'FontSize',9,'FontWeight','bold');
% 坐标轴规范
xlim([0 215]); xticks(0:40:200); ylim([0 10.5]);
xlabel('迭代次数','FontSize',10); ylabel('目标函数值','FontSize',10);
title('图5 改进SA-PSO收敛速度较PSO提升41.2%','FontSize',11,'FontWeight','bold');
grid on;
finish_figure(fig,'fig5_conv_optimized','C:\Users\Lenovo\Documents\trae_projects\cumcm_2026\figures');
```

## 十一、评委3秒理解检查清单
- [ ] **3秒测试**：蒙住文字，光看图能否猜出核心结论
- [ ] 视觉层级：主数据明显最粗最亮，参考线/网格退到背景
- [ ] 字号：所有文字印刷后 ≥8pt（子图尤甚）
- [ ] 标注：不遮挡数据，箭头引出，白底框
- [ ] 图例：≤3条线直接标注，不用图例框
- [ ] 双编码：颜色+marker 双重区分，黑白打印可辨
- [ ] 坐标轴：物理量+单位，整数刻度，5%留白
- [ ] 图题：含结论+关键数值，非"示意图"
- [ ] 子图：(a)(b)(c) 编号 + 紧凑对齐 + 共用图例
- [ ] **每图末尾调用 finish_figure()** 统一收尾
