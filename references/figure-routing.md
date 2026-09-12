# 图型路由表 v2.0 — v7 图表生成单一事实源

> **定位**：本文件是 v7 第 3 步「图表生成」的图型→工具路由总表。执行时按此分流，禁止凭直觉选工具。
> **原则**：常规数据图走 `figure-skill` / `figure-specs.md` 10 技法；**惊艳高级图 MATLAB 为主**（`nature-plot-repro`），Python 兜底（`mathmodel-figure-templates`）；流程图走 `diagram-design`；出版级配图走 `scipilot-figure-skill`。
> **与 figure-specs.md 关系**：`figure-specs.md` 的 10 技法（3D曲面/双编码散点/雷达/收敛渐变/inset 等）仍是**最基础的常规图强制要求**；本表的「惊艳高级图」是它的**补充升级**，用在「一张图顶三张」的关键结论处。
> **v2.0 更新**：完整集成 6 个绘图 skill + 2 个排版 skill，新增题型→图型→skill 三维映射表 + 选型层自动化 + scipilot 出版级配图集成。

---

## 一、三级路由总览

```
出图前选型 ── math-modeling-diagram-master（题型→40类图型清单，§0 选型层）
       │
       ├─ 概念图/流程图 ── 遵循 flowchart-specs.md（灰度无彩色国一标准）
       │                    diagram-design(HTML+SVG) / Mermaid(可复制进 Typora/Obsidian)
       │                    └─ mathmodel-flowchart（备选，LogicFlow 浏览器交互）
       │
       ├─ 常规数据图 ──── figure-skill（Python）/ figure-specs.md 10技法（MATLAB）
       │                    └─ scipilot-figure-skill（出版级配图，EDA→选型→视觉自检）
       │
       └─ 惊艳高级图 ──── nature-plot-repro（首选，MATLAB 26案例）
                            └─ mathmodel-figure-templates（兜底，Python 11模板）
```

### 绘图 Skill 完整集成矩阵（6 绘图 + 2 排版）

| Skill | 定位 | 触发词 | 核心能力 | 输出 |
|-------|------|--------|---------|------|
| **math-modeling-diagram-master** | §0 选型层 | "选图表"/"出图"/"流程图" | 题型→40类图型清单（fig_plan） | `fig_plan.md` 选型清单 |
| **figure-skill** | 常规数据图 | Python 出图/折线/柱状/散点/热图 | SimHei/双导出/5调色板/finish_figure | `figures/png/` + `figures/pdf/` |
| **nature-plot-repro** | 惊艳高级图 | "Nature同款"/弦图/桑基/雷达/泰勒/环形热图 | MATLAB 26案例复刻（只换数据不改配色） | 300dpi PNG + 矢量 PDF |
| **mathmodel-figure-templates** | Python兜底 | SHAP/山脊图/蜂群图/小提琴/UpSet | Python 11模板（替换数据出图） | `figures/png/` + `figures/pdf/` |
| **diagram-design** | 流程图唯一 | "技术路线"/"架构图"/"算法流程" | 编辑级 HTML+SVG，27图型，灰度无彩色 | SVG/PNG |
| **scipilot-figure-skill** | 出版级配图 | "期刊投稿级"/"EDA分析"/"配图审查" | EDA剖析→选图顾问→视觉自检闭环 | 质量报告 + 优化建议 |
| **math-modeling-paper-layouter** | 排版门禁 | "排版检查"/"重叠修复" | 5层门禁（重叠/编译/一致性/文献/编号） | 排版报告 |
| **math-modeling-abstract-polisher** | 摘要+文献 | "摘要审查"/"降AI味"/"参考文献" | 4维审查（摘要/文献/AI味/进度） | 审查报告 |

### Skill 调用时序（迭代式）

```
diagram-master 选型 ──→ figure-skill/nature-plot-repro 出图 ──→ scipilot 审查
                              │                                      │
                              ▼                                      ▼
                    paper-layouter 排版门禁 ◄──── abstract-polisher 内容审查
                              │
                              ▼
                    paper-layouter 终编译（总报告）
```

---

## 二、路由决策树

```
1. 这张图是不是"流程/结构/路线"性质？
   是 → 概念图 → 走 diagram-design/Mermaid，遵循 flowchart-specs.md 灰度规范（禁止彩色）
   否 ↓

2. 是不是常规统计图（折线/柱状/散点/普通热图/雷达/收敛曲线/3D曲面）？
   是 → 常规图 → Python 走 figure-skill，MATLAB 走 figure-specs 10技法
   否 ↓

3. 是不是"新颖高级图"（弦图/桑基/泰勒/环形热图/小提琴/UpSet/SHAP/山脊/冲积/哑铃）？
   是 → 惊艳图 → 首选 nature-plot-repro（MATLAB）；无 MATLAB 或纯 Python 项目 → mathmodel-figure-templates
   否 → 回到 2，重新审视是否该用常规图表达
```

**触发词速查**：
- 「画流程图 / 技术路线 / 模型结构 / 算法流程」→ `diagram-design`
- 「弦图 / 桑基 / 泰勒 / 环形热图 / 小提琴 / 哑铃 / UpSet / 冲积」→ `nature-plot-repro`
- 「SHAP / 山脊图 / 蜂群图」→ `mathmodel-figure-templates`（Python 独有）
- 「Nature 同款 / 顶刊风格 / 期刊配图 / 复刻这张图」→ `nature-plot-repro`
- 「选图表 / 出图选型 / 图型清单」→ `math-modeling-diagram-master`
- 「期刊投稿级 / EDA分析 / 配图审查 / 出版级」→ `scipilot-figure-skill`
- 「排版检查 / 重叠修复 / 编译诊断」→ `math-modeling-paper-layouter`
- 「摘要审查 / 降AI味 / 参考文献」→ `math-modeling-abstract-polisher`

---

## 二b、题型→图型→Skill 三维映射表（v2.0 新增）

> 按题型列出推荐图型及对应 Skill，出图前先查此表。

### A 机理题（12-14 张图）

| 图型 | Skill | 优先级 | 说明 |
|------|-------|--------|------|
| 技术路线图 | diagram-design | ★★★ | 全局总图，灰度无彩色 |
| 3D 曲面图 | figure-skill | ★★★ | 物理场分布（温度/压力/浓度） |
| 等高线图 | figure-skill | ★★★ | 二维物理场截面 |
| 剖面图 | figure-skill | ★★☆ | 沿某方向的物理量变化 |
| 轨迹图 | figure-skill | ★★☆ | 运动轨迹/路径 |
| 收敛曲线 | figure-skill | ★★☆ | 数值方法收敛性 |
| 残差直方+Q-Q图 | figure-skill | ★★★ | 拟合精度检验（四重检验 6.1） |
| Sobol 柱状图 | figure-skill | ★★★ | 灵敏度分析（四重检验 6.2） |
| MC 直方图+CDF | figure-skill | ★★★ | 蒙特卡洛验证（四重检验 6.3） |
| 雷达图 | nature-plot-repro | ★★☆ | 多维对比（如需 Nature 风格） |
| 四重检验流程图 | diagram-design | ★★☆ | 检验体系总览 |

### B 优化题（14-16 张图）

| 图型 | Skill | 优先级 | 说明 |
|------|-------|--------|------|
| 技术路线图 | diagram-design | ★★★ | 全局总图 |
| 算法流程图 | diagram-design | ★★★ | SA-PSO/GA/DE 迭代流程 |
| 收敛曲线（多算法） | figure-skill | ★★★ | 3算法对比（SA-PSO/Clerc-PSO/GA） |
| 可行域图 | figure-skill | ★★☆ | 约束条件可视化 |
| 布局图/方案图 | figure-skill | ★★★ | 最优方案可视化 |
| 灵敏度龙卷风图 | figure-skill | ★★★ | 参数灵敏度（四重检验 6.2） |
| 泰勒图 | nature-plot-repro | ★★★ | 多算法精度对比（B/D 题消融） |
| Pareto 前沿图 | figure-skill | ★★☆ | 多目标优化 |
| 算法对比表 | — | ★★★ | 表格形式（非图） |
| 消融对比柱状图 | figure-skill | ★★☆ | 基础方案 vs 创新方案 |
| 四重检验流程图 | diagram-design | ★★☆ | 检验体系总览 |

### C 评价题（10-12 张图）

| 图型 | Skill | 优先级 | 说明 |
|------|-------|--------|------|
| 技术路线图 | diagram-design | ★★★ | 全局总图 |
| 雷达图（多方案） | figure-skill / nature-plot-repro | ★★★ | 多维评价对比 |
| 热力图（相关性） | figure-skill | ★★★ | 指标相关性矩阵 |
| 层次分析结构图 | diagram-design | ★★☆ | AHP 层次结构 |
| 灵敏度分析图 | figure-skill | ★★★ | 权重灵敏度（四重检验 6.2） |
| 聚类热图+树状图 | nature-plot-repro | ★★☆ | 方案聚类 |
| 评分排序图 | figure-skill | ★★☆ | TOPSIS 综合评分 |
| 四重检验流程图 | diagram-design | ★★☆ | 检验体系总览 |

### D 数据题（12-14 张图）

| 图型 | Skill | 优先级 | 说明 |
|------|-------|--------|------|
| 技术路线图 | diagram-design | ★★★ | 全局总图 |
| 时序图（原始+预测） | figure-skill | ★★★ | 时序数据+预测曲线 |
| 分布图（直方+核密度） | figure-skill | ★★☆ | 数据分布特征 |
| 相关性热力图 | figure-skill | ★★★ | 特征相关性矩阵 |
| 预测对比图 | figure-skill | ★★★ | 多算法预测对比 |
| 残差分析图 | figure-skill | ★★★ | 残差正态性（四重检验 6.1） |
| SHAP 特征重要性 | mathmodel-figure-templates | ★★☆ | 机器学习可解释性 |
| 泰勒图 | nature-plot-repro | ★★★ | 多模型精度对比 |
| 小提琴图 | nature-plot-repro | ★★☆ | 分布形态对比 |
| 四重检验流程图 | diagram-design | ★★☆ | 检验体系总览 |

---

## 三、惊艳高级图 → 图型映射表（核心，MATLAB 为主）

> 首选列 = `nature-plot-repro` 案例；兜底列 = `mathmodel-figure-templates` 模板。重叠图型（弦图/桑基/泰勒/UpSet/冲积/聚类热图）按「MATLAB 有案例 → 首选 MATLAB」。

| 图型 | 首选工具 + 案例/模板 | 兜底（Python） | 适用场景 |
|------|---------------------|----------------|---------|
| **弦图**（关系/流量） | nature-plot-repro 复刻四/十六/十九/二十六 | figure-templates 弦图 | 多对多关联、资源流转、生态网络 |
| **桑基图**（流向） | nature-plot-repro 复刻十二/十四/十九/二十四 | figure-templates 桑基图 | 能量流、资金流、层级分配 |
| **泰勒图**（多模型对比） | nature-plot-repro 复刻九 | figure-templates 泰勒图 | 预测模型精度对比（B/D 题消融） |
| **环形热图** | nature-plot-repro 复刻五/六 | figure-templates 聚类热图 | 带分组的时序/基因类热图 |
| **扇形热图** | nature-plot-repro 复刻二十一 | — | 圆形分区热图 |
| **小提琴图 / 半小提琴** | nature-plot-repro 复刻十七/二十一 | figure-templates 小提琴+蜂群 | 分布形态对比（替代裸箱线） |
| **山脊图** | —（MATLAB 无，Python 独有） | figure-templates 山脊图 | 多组分布重叠对比 |
| **SHAP 特征重要性** | —（Python 独有） | figure-templates SHAP | 机器学习可解释性（D 题） |
| **UpSet 图**（集合关系） | nature-plot-repro 复刻二十六 | figure-templates UpSet | 多集合交并关系 |
| **冲积图**（分类流转） | nature-plot-repro 复刻二十 | figure-templates 冲积 | 分类构成随时间/条件变化 |
| **聚类热图 + 树状图** | nature-plot-repro 复刻三/十八 | figure-templates 聚类热图 | 层次聚类 + 表达矩阵 |
| **三角热图 / 旋转热图** | nature-plot-repro 复刻二十二/十 | — | 相关性矩阵（三角布局） |
| **哑铃图** | nature-plot-repro 复刻八 | — | 前后对比 / 两时点变化 |
| **环形柱状图** | nature-plot-repro 复刻二十五 | — | 周期/环向数据（替代玫瑰图） |
| **雷达图（顶刊版）** | nature-plot-repro 复刻二十三 | figure-skill 常规雷达 | 多维评价（C 题） |

> 注：常规雷达图（C 题评价）也可直接用 `figure-specs.md` 技法7；需要 Nature 级视觉时升级到复刻二十三。

---

## 四、各工具调用链速查

### 4.1 diagram-design（流程图首选）
- 调用 `diagram-design` skill → 27 图型（流程图/架构图/泳道/时序/ER/树等）→ 自包含 HTML+SVG
- 中文内容字体栈加 `'Microsoft YaHei'` 回退（默认 Geist/Instrument Serif 不含中文）
- 导出 SVG/PNG → 插入 LaTeX（`\includegraphics` 或 `\includesvg`）

### 4.2 mathmodel-flowchart（流程图备选，需浏览器交互时）
- 触发「LogicFlow / 浏览器拖拽绘制」→ 启动本地 `pnpm dev` → 导出 PNG(300dpi)/SVG/JSON
- 仅当用户明确要在浏览器里手工微调节点时启用，否则默认 diagram-design

### 4.3 nature-plot-repro（惊艳高级图首选）
执行链路（**关键：类文件与 demo 必须同目录**）：
1. 图型识别 + 案例匹配（按上表；用户给期刊图 → `mcp__image-reader__read_image` 看图提取布局配色）
2. 复制案例到工作目录：`cp -r "~/.claude/skills/nature-plot-repro/assets/cases/<案例>" "<工作目录>/matlab/"`
3. 数据替换：注释掉 `rng(...)` 随机段 → 换成 `readtable`/`readcell` 读真实数据；**保留原脚本配色/布局/字体不动**（Nature 味来源）
4. 运行：`mcp__matlab__generate_matlab_script` → `mcp__matlab__execute_matlab_script`
5. 导出：300dpi PNG + 矢量 PDF → 视觉自检（`image-reader`）

### 4.4 mathmodel-figure-templates（Python 兜底）
- 触发：无 MATLAB、纯 Python 项目、或 SHAP/山脊/蜂群等 Python 独有图型
- 每个模板含可运行代码骨架 + 合成数据示例 → 替换数据即可出图

### 4.5 figure-skill（Python 常规图）
- 初始化：SimHei 字体 + `axes.unicode_minus=False` + 600dpi 双导出 + 5 套调色板
- 覆盖：折线/柱/散点/热图/雷达/收敛/3D曲面

### 4.6 math-modeling-diagram-master（选型层，出图前第一步）
- 接到建模题、要出图时**先调本 skill** → 扫题干关键词 → 生成 fig_plan 选型清单 → 再按本路由表分发到各工具
- 40 类图型，强制流程图 + 验证图，消除 AI 假数据硬编码

### 4.7 scipilot-figure-skill（出版级配图，出图后审查）
- **触发时机**：关键图表出图后、论文提交前
- **核心能力**：
  1. **EDA 剖析**：数据特征分析，推荐最佳图型
  2. **选图顾问**：基于数据特征推荐图型+配色+布局
  3. **视觉自检**：缺字/裁切/刻度重叠/字号<8pt 检测
  4. **主动拦截**：禁止双Y轴、饼图、Y轴不当截断、小样本均值柱、rainbow/jet 色图
- **调用链**：`scipilot-figure-skill` → `check_figure.py --strict` → AI 读图复核
- **与 figure-skill 配合**：figure-skill 出图 → scipilot 审查 → 回改重渲

### 4.8 math-modeling-paper-layouter（排版门禁，论文级审查）
- **触发时机**：图表嵌入论文后、编译前
- **5 层门禁**：
  1. 重叠检测：`check_overlaps.py --fix --marked`（repel_text 仿 ggrepel 排斥）
  2. 编译诊断：`build_paper.py --check-only`
  3. 一致性：`check_consistency.py`（图文数值一致）
  4. 文献：`check_references.py`（近5年/外文比例）
  5. 编号：公式/图表/章节编号连续性
- **与 figure-routing 配合**：出图 → 嵌入论文 → paper-layouter 门禁 → 通过后编译

### 4.9 math-modeling-abstract-polisher（摘要+文献，内容级审查）
- **触发时机**：论文初稿完成后
- **4 维审查**：
  1. 摘要：5要素+量化值+关键词
  2. 文献：近5年比例+外文比例+DOI完整性
  3. AI味：对照 de-ai-writing.md 逐条检查
  4. 进度：72h 进度看板（dashboard.py）
- **与 figure-routing 配合**：图表审查通过后 → abstract-polisher 内容审查 → 最终编译

---

## 五、与 v7 其他环节的衔接

| 环节 | 衔接点 |
|------|--------|
| 阶段 2 图表生成 | 本表替代「数据图只走 10 技法」的单一规则，升级为三级路由 |
| §3.4 图表质量验证 | 所有图（含惊艳高级图）出图后仍调用 `image-reader` 做缺字/遮挡/裁切自检 |
| `figure_manifest.json` | 惊艳高级图与常规图一样，进入 `gen_figure_manifest.py` 扫描，统一 `figN_xxx` 命名 |
| L2 图表数量检查 | 惊艳高级图计入图表总数，不计入「创新技法 ≥1」的重复堆叠（一图选一套即可） |
| 国一排版规范 | 字号 ≥8pt、图题含结论、矢量 PDF 双导出——所有图型统一遵守 `figure-specs.md` §九 finish_figure 收尾 |

---

## 六、避坑清单

1. **不重复叠技法**：一张图要么走 10 技法常规图，要么走惊艳高级图，不要在图内又叠又改，避免视觉过载
2. **类文件同目录**：nature-plot-repro 的 `chordChart.m`/`SSankey.m` 等类文件必须与 demo 脚本放同一目录，否则运行报错
3. **保留原配色**：替换数据时只动数据段，不改配色/布局/字体，否则失去 Nature 味
4. **MATLAB 优先但别硬上**：数据是纯 Python 生态、或图型是 SHAP/山脊/蜂群时，直接走 figure-templates，不强行塞 MATLAB
5. **流程图别用数据图工具**：技术路线/模型结构/算法流程一律 diagram-design，禁止用 matplotlib 硬画框图（易成一坨）
6. **惊艳图别滥用**：弦图/桑基图等只在有真实关联/流转数据时用，无数据硬画 = 评委眼中的「凑图」，反而扣分
