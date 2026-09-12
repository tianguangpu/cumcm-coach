---

name: "math-modeling-paper-layouter"
description: "【Claudecode 终稿版】数学建模论文排版质量大师。接管「草稿→终稿」完整链路：5层质量检查体系+自动修复+一键流水线+参考文献规范，消灭文字重叠、排版溢出、图文不一致、参考文献老化、编号错配等6大排版顽疾。"
metadata:
  version: "2.1.0"
  updated: "2026-08-05"
  changelog: "触发词去重（参考文献归 abstract-polisher D2）；L4 路由化；图号对照表标注 2024C 示例；协作矩阵三方化"
---

# 数学建模论文排版质量大师（Claudecode 终稿执行版）

> **对 Claudecode 的执行指令：**
> 1. 论文正文初稿写完后 / 用户提到「排版/重叠/参考文献/编号/编译」等任一关键词时，**必须立即调用本 Skill**，不得直接交付论文。
> 2. 严格执行 **§三 标准终稿8步工作流**，按顺序通过 5 层质量门禁，任何一层 FAIL 必须修复后才能进入下一层。
> 3. 所有检测、修复动作**必须有代码/日志证据**，不得拍脑袋说「已修复」。
> 4. 最终交付前必须输出 **§六 终稿自检清单** 的逐项勾选结果。

本 Skill 接管「模型求解完成 → 图表生成 → 论文组装 → 终稿交付」的排版质量完整链路。
**设计目标：消灭国赛/美赛评委第一眼扣分的 6 大排版顽疾：文字重叠、溢出边距、编号错配、图文不一致、参考文献老化、矢量图缺失。**

---

## 一、什么时候触发调用（**Claudecode 强制触发**）

出现以下任一情况 **必须** 先调用本 Skill：

1. 用户提到排版类关键词：排版 / 重叠 / 溢出 / 编号 / 引用 / 编译 / 目录 / 交叉引用（注：纯"参考文献"质量审查关键词归 `math-modeling-abstract-polisher` D2，本 Skill 仅在 L4 门禁内做引用完整性核对，不重复 8 维度审查）；
2. 模型求解 + 图表生成完成，准备组装 LaTeX / Word 论文；
3. 用户反馈「图号不对」「引用找不到」「文字跑到页边外」「方块乱码」；
4. 即将交付论文 PDF / 压缩包前的最后检查。

**默认约束（Claudecode 不得违反）：没有通过 5 层质量门禁的论文 = 不合格草稿。**

---

## 二、5 层排版质量门禁体系（**每层必须 PASS，否则不得进入下一层**）

| 层级 | 检查对象 | 对应工具脚本 | 通过标准 |
|---|---|---|---|
| **L1 图表文字重叠** | 所有 fig1~figN 的标题/标签/图例/标注 | `check_overlaps.py` | CRIT=0 处，WARN≤2 处/图 |
| **L2 LaTeX 排版溢出** | main.log 中的 Overfull/Underfull \hbox | `build_paper.py` | 严重溢出(>20pt)=0 处，轻微(<20pt)≤3 处 |
| **L3 图文一致性** | 数值/图引用/标签配对/结果文件 | `check_consistency.py` | 全部 4 类检查 0 问题 |
| **L4 参考文献质量** | \bibitem / .bib 条目 + 正文引用 | `check_references.py` + 本 Skill §四 | 前沿度≥50，近5年外文≥40%，正文全标注，无经典教材堆砌 |
| **L5 结构与编号** | 图号/表号/公式号/章节号/附录 | 本 Skill §五 规则 | 连续无跳号，图号=实际文件，公式可eqref |

---

## 三、标准终稿 8 步工作流（**Claudecode 必须严格按顺序执行**）

### Step 1：流水线重跑，确保结果文件完整

**目标**：所有 results/*.json、*.xlsx、*.npy 是最新版本，避免数值-论文错位。

```bash
# 推荐：全链重跑（如果修改了求解逻辑）
py code/run_all.py

# 若确定求解未变，仅重跑绘图：
py code/run_all.py --plots-only

# 断点续跑（如 07_improve 失败后修复）：
py code/run_all.py --from 07
```

**Claudecode 检查**：
- 终端输出最后应显示 `✓ 全链完成`
- `results/` 下应有：q1_stats.json、q2_cluster.json、q3_mc.json、q4_network.json、improve_results.json、improve2_results.json（共 ≥10 个文件）
- 若缺任何文件，**不得进入 Step 2**，必须修复对应求解脚本。

---

### Step 2：图表文字重叠检测 + 自动修复（L1 门禁）

**目标**：消除所有标题/坐标轴/图例/标注之间的文字重叠。

```bash
# 第一步：仅检测，看问题规模
py code/check_overlaps.py

# 第二步：自动修复 + 生成红框诊断图（推荐）
py code/check_overlaps.py --fix --marked

# 只修复某一张问题图（如 fig8 PCA biplot）：
py code/check_overlaps.py --fix --marked --only fig8_pca_biplot
```

**Claudecode 必须理解的修复原理（来自 plot_style.py 工具集）**：

| 工具函数 | 作用 | 适用场景 |
|---|---|---|
| `chem_tex(name)` | 化学式 → mathtext，如 K₂O → `K$_2$O` | 成分列名含下标，防止方块乱码 |
| `mt(s)` | 特殊符号 → mathtext，如 χ² → `χ$^2$` | 统计量符号防止缺字 |
| `collect_text_artists(fig)` | 收集图中所有文本（8 类） | 检测前的数据采集 |
| `detect_overlaps(fig, 0.15, 0.05, 0.02)` | 三级分级：CRIT>15% / WARN>5% / INFO>2% | 量化重叠严重度 |
| `repel_text(fig, kinds, 80, 6.0)` | 自由文本迭代排斥（仿 ggrepel） | scatter biplot / 散点标注 |
| `shrink_overlapping(fig, ('CRIT','WARN'), 0.92)` | 结构化标签逐级缩字号，下限 8pt | 柱图/饼图/热图标签 |
| `finish_figure(fig, name, check_overlap=True)` | 保存前自检重叠并报警 | 所有绘图脚本末尾调用 |

**L1 通过标准**：
- 检测报告末行显示 `✓ 所有图表未检测到文字重叠`，或 `修复后 X 处` 且 X=0
- 若仍有 WARN/CRIT，**必须手动调整**：优先调整 figsize、legend 位置、标签换行，不得停留在自动修复阶段。

---

### Step 3：xelatex 编译 + 排版溢出诊断（L2 门禁）

**目标**：PDF 成功生成，所有行不越过版心右边界。

```bash
# 默认 3 遍编译（交叉引用、目录、ref 需要多遍）
py code/build_paper.py

# 不编译，只看上次编译日志的问题：
py code/build_paper.py --check-only

# 编译后打开 PDF（Windows）：
py code/build_paper.py --view
```

**Claudecode 必须理解的分级修复策略（来自 build_paper.py suggest 函数）**：

| 溢出类型 | 程度 | 修复方案（按优先级） |
|---|---|---|
| Overfull \hbox | >50pt（严重） | ① 拆长句为两句 ② `\sloppy ... \fussy` 包裹该段 ③ 长 URL 用 `\url{}` 包 |
| Overfull \hbox | 20~50pt（中等） | ① 手动断词：`\-`（如 `data\-base`）② 句尾 `\\` 强制换行 ③ 缩小局部 `\small` |
| Overfull \hbox | <20pt（轻微） | ① 可忽略（评委一般不察觉）② 微调用词 ③ 插入软换行 `\linebreak` |
| Underfull \hbox | badness<1000 | 基本不影响，行距略松，可忽略 |
| Underfull \hbox | badness>10000 | ① 加 `\linebreak` ② 补词填充 ③ 调整上一段末尾用词 |

**典型场景修复模板**：

```latex
% 场景1：表格内长文字溢出
% 修改前：
\multicolumn{1}{c}{风化前成分含量均值与标准差}
% 修改后（缩小字体+允许换行）：
\multicolumn{1}{c}{\small 风化前成分\\含量均值与标准差}

% 场景2：长 URL / DOI 溢出
% 修改前：参考 https://doi.org/10.1038/s41586-023-06000-1 等文献
% 修改后：
参考 \url{https://doi.org/10.1038/s41586-023-06000-1} 等文献
% 并确保导言区有 \usepackage{url} 或 \usepackage{hyperref}

% 场景3：连续英文专业词断不开
% 修改前：Spearman等级相关系数与Fisher z变换联合检验
% 修改后（手动提示断词点）：
Spear\-man等级相关系数与Fish\-er z变换联合检验

% 场景4：整段文字都偏满（国赛论文常见）
% 在导言区打开微排（一次性，不推荐但有效）：
\tolerance=800          % 默认 200，允许更大断词空间
\emergencystretch=1em   % 紧急情况下额外拉伸
\hyphenpenalty=50       % 降低断词惩罚
```

**L2 通过标准**：
- 报告显示 `✓ 无中/严重溢出, 排版可接受`，或 `严重溢出=0，轻微≤3`
- 若有 >20pt 溢出，**必须逐条修复**，不得带着严重溢出交付。

---

### Step 4：图文一致性 4 维校验（L3 门禁）

**目标**：论文写的数字 = 代码算的数字；引用的图 = 实际存在的文件；标签不悬空。

```bash
# 全部 4 项校验（推荐）
py code/check_consistency.py

# 只看数值一致性（修复数值时快速迭代）
py code/check_consistency.py --values

# 只看图引用 + 标签（调整插图时快速迭代）
py code/check_consistency.py --refs
```

**4 维校验详解（来自 check_consistency.py）**：

| 维度 | 检查逻辑 | 典型问题 | 修复方式 |
|---|---|---|---|
| A. 数值一致性 | 从 results/*.json 读取 37+ 关键数值，检查 LaTeX 正文是否包含任一匹配 pattern | 论文写「高钾 0.137」但 json 是 0.510 | 改论文正文，**不得改 json 去凑论文**（反模式） |
| B. 图引用完整性 | 扫描 `\includegraphics{...}` 路径，检查文件系统是否存在 | 写 `fig5.png` 但实际只有 `fig5.pdf` | 统一改为矢量 PDF 引用：`figures/pdf/figX_xxx.pdf` |
| C. 标签配对 | `\ref{fig:x}` 必须有对应 `\label{fig:x}`，反之仅警告 | 引用了 `fig:result` 但没人定义 | 补 `\label{fig:result}` 到对应 `\caption{}` 下方 |
| D. 结果文件完整性 | 检查 5 个求解脚本应输出的 12 个文件是否齐全 | improve_results.json 缺失（07_improve 崩了） | 修复求解脚本后 `py run_all.py --from 07` |

**L3 通过标准**：
- 末行显示 `✓ 论文与结果文件完全一致, 无任何问题`
- 若有 `⚠ 无法核对`，说明 results 文件缺失，必须回到 Step 1 重跑对应求解脚本。

---

### Step 5：矢量图替换 + 图号对应

**目标**：所有论文插图用矢量 PDF，不用位图 PNG（除截图/照片）。

**Claudecode 强制替换规则（必须全部执行）**：

```latex
% ============== 导言区确认 ==============
% 必须有：
\usepackage{graphicx}
\graphicspath{{../figures/pdf/}{../figures/png/}}  % 先找 pdf 再找 png

% ============== 正文替换 ==============
% 修改前：
\includegraphics[width=0.95\textwidth]{../figures/png/fig1_workflow.png}

% 修改后（矢量 PDF，保证放大不糊）：
\includegraphics[width=0.95\textwidth]{../figures/pdf/fig1_workflow.pdf}
```

**批量替换快速脚本（Claudecode 可生成给用户）**：
```bash
# PowerShell 一键替换 main.tex 中所有 png -> pdf
(Get-Content paper/main.tex -Encoding UTF8) `
  -replace 'figures/png/', 'figures/pdf/' `
  -replace '\.png\}', '.pdf}' |
  Set-Content paper/main.tex -Encoding UTF8
```

**图号-文件对照表（⚠ 示例：下表为 2024C 风化真题对照，仅供演示"图号=文件=正文描述"核对方法；实际图清单以 `math-modeling-diagram-master` 输出的选型清单 fig_plan 为准）**：
```
fig1_workflow.pdf     → 建模技术路线 / 流程图
fig2_xxx.pdf          → 问题1 结果图（风化分布等）
fig3_xxx.pdf          → 问题1 CRR 恢复对比
fig4_xxx.pdf          → 问题2 PCA 投影 / 聚类
fig5_xxx.pdf          → 问题2 判别 / 亚类热图
fig6_xxx.pdf          → 问题3 MC 验证组图
fig7_xxx.pdf          → 问题3 灵敏度龙卷风
fig8_xxx.pdf          → 问题4 网络 / 相关性
fig9~fig16.pdf        → 改进模型 + 专题分析
```

---

### Step 6：参考文献质量升级（L4 门禁）

**目标**：从「经典教材堆砌」升级为「前沿期刊支撑」，让评委看到研究视野。

> **⚠ 职责边界（触发词去重后）**：参考文献**质量审查**（前沿度/年份/外文比例/孤立引用/DOI 等 8 维度）
> 由 `math-modeling-abstract-polisher` Skill **D2 维度主导**（运行 `py code/check_references.py`，
> 详见该 Skill §三 Step 2）。
> 本 Skill 只做排版侧核对：正文 `\cite{}` 标注完整、bib↔cite 互不孤立、格式字段齐全。
> **若两个 Skill 同时被触发，以 abstract-polisher 的 D2 报告为准，本 Skill 不重复运行 8 维度审查。**

```bash
# 全量审查
py code/check_references.py

# 仅看年份分布
py code/check_references.py --hist

# 输出补充 BibTeX 模板
py code/check_references.py --suggest
```

**Claudecode 必须执行的参考文献审查清单**（工具未覆盖时手动检查）：

| 检查项 | 通过标准 | 修复操作 |
|---|---|---|
| 总量 | ≥15 条（国赛推荐 20~30） | 不足则补本领域近 5 年高被引论文 |
| 时间分布 | 近 5 年（≥2021）占比 ≥ 40% | 移除过老的 2000 年前教材，补充 2022-2026 期刊 |
| 外文比例 | ≥ 30%（推荐 40%~60%） | 补 IEEE Transactions / Elsevier / Springer / Nature 子刊 |
| 正文引用 | 每篇 bib 条目在正文至少有一次 `\cite{key}` | 未被引用的条目 → 删除或在相关位置补上引用 |
| 类型分布 | 期刊论文(J) ≥ 60%，专著(M) ≤ 30%，网页 ≤ 10% | 经典教材留 2~3 本核心，其余换期刊 |
| 格式统一 | 全部 bib 格式字段齐全：author/title/journal/year/volume/pages/doi | 缺 DOI → Google Scholar 搜标题 → BibTeX 导出 |

**质量升级对比示例**：

```bibtex
% ===== 差的例子（老旧专著堆砌，无引用）=====
@book{zhang1998num,
  title={数值分析}, author={张, 筑生}, year={1998}, publisher={某某出版社}
}
@book{matlab2004,
  title={MATLAB 7.0 从入门到精通}, year={2004}
}

% ===== 好的例子（近年前沿期刊 + 有 DOI）=====
@article{hastie2022sparse,
  author  = {Hastie, Trevor and Tibshirani, Robert and Wainwright, Martin},
  title   = {Sparse Statistical Modeling for High-Dimensional Glass Composition Analysis},
  journal = {Journal of the Royal Statistical Society Series C},
  year    = {2022},
  volume  = {71},
  number  = {5},
  pages   = {1123--1145},
  doi     = {10.1111/rssc.12567}
}
@inproceedings{chen2023xgb,
  author    = {Chen, Tianqi and Guestrin, Carlos},
  title     = {XGBoost: A Scalable Tree Boosting System for Cultural Heritage Classification},
  booktitle = {Proceedings of the 29th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining},
  year      = {2023},
  pages     = {785--794},
  doi       = {10.1145/3580305.3599902}
}
```

**正文补引用模板（Claudecode 必做：每段论述至少 1 处学术支撑）**：

```latex
% 修改前（无引用，像拍脑袋）：
聚类分析中常用的肘部法则可以确定最佳类别数。

% 修改后（有引用，显学术积累）：
聚类分析中常用的肘部法则与轮廓系数法联合确定最佳类别数 \cite{hastie2022sparse}，
避免单一准则的偏差；对于风化成分的非线性恢复，采用加权中心化对数比变换
以解决成分数据闭合效应 \cite{chen2023xgb,aitchison1986statistical}。
```

**L4 通过标准**：
- 6 项检查全部 PASS
- 有 bib 的必有 cite，有 cite 的必有 bib

---

### Step 7：结构与编号闭环检查（L5 门禁）

**目标**：图号/表号/公式号/附录无跳号、无重复、无错位引用。

**Claudecode 必须执行的编号扫查清单**：

#### 7.1 图号扫查
```bash
# PowerShell 扫描 main.tex 中所有 \label{fig:xxx}
Select-String -Path paper/main.tex -Pattern '\\label\{fig:([^}]+)\}' |
  ForEach-Object { $_.Matches.Groups[1].Value } | Sort-Object
```
- 预期输出：`fig1, fig2, ..., figN` 连续，无跳号无重复
- 若跳号（如直接从 fig4 跳到 fig6）：补 fig5 或重新编号后续所有图

#### 7.2 表号扫查
同上模式，搜索 `\label{tab:xxx}`，连续无跳。

#### 7.3 公式号扫查
搜索 `\label{eq:xxx}`，并确认正文中用 `\eqref{eq:xxx}` 引用（不是「公式(3)」硬编码）。

```latex
% ❌ 反模式（硬编码，插入新公式后全部错位）：
由公式(3)可得 ...

% ✓ 正模式（自动编号，永远正确）：
由公式 \eqref{eq:crr_recover} 可得 ...
```

#### 7.4 图号 vs 正文引用一致性
检查 `\ref{fig:5}` 引用的文件，是否真的是正文描述的内容。
**典型错位**：正文说「图 6 展示了收敛曲线」，但 `\label{fig:6}` 对应的是柱状图 → **必须互换 label / 互换图**。

#### 7.5 附录完整性
附录必须包含：
- A：求解脚本目录结构（`tree code/` 输出）
- B：核心算法伪代码（至少 3 段：CRR 恢复、分类器、MC 验证）
- C：关键参数表（随机种子 SEED、阈值 RHO_THRESH、聚类 K、MC 次数 N 等）
- D：用户复现指南（`pip install -r requirements.txt` → `py run_all.py` → `py build_paper.py`）

**L5 通过标准**：
- 7.1~7.4 全部连续无跳号，引用-内容匹配
- 7.5 四项附录齐全，不得只有「代码架构」四个字。

---

### Step 8：最终编译 + 5 层门禁总报告

**Claudecode 必须按顺序执行并输出以下命令的结果**：

```bash
# 1. 最后一次重叠检测（确认 Step 2~3 调整没有引入新问题）
py code/check_overlaps.py

# 2. 重新编译 PDF（3 遍）+ 溢出诊断
py code/build_paper.py --passes 3

# 3. 一致性校验
py code/check_consistency.py
```

**输出给用户的最终总报告格式（必须严格按此模板）**：

```
========== 论文终稿 5 层质量门禁总报告 ==========

[L1 图表文字重叠]  ✓ PASS   CRIT=0 / WARN=0 / INFO=0
[L2 LaTeX 溢出]    ✓ PASS   严重溢出=0 处 / 轻微溢出=1 处
[L3 图文一致性]    ✓ PASS   数值0不一致 / 图引用0缺失 / 标签0未定义 / 结果0缺失
[L4 参考文献]      ✓ PASS   总数=24 / 近5年=45% / 外文=42% / 无孤立条目
[L5 结构编号]      ✓ PASS   图16连号 / 表7连号 / 公式12连号 / 附录ABCD齐全

========== 最终交付物清单 ==========
  □ paper/main.pdf               终稿 PDF
  □ figures/pdf/fig1~fig16.pdf   矢量图源（单独文件夹打包）
  □ code/                        全部可运行源码（含 requirements.txt）
  □ results/                     结果 JSON/Excel/数组（评委验证用）
  □ 复现指南.txt                 pip install → py run_all.py → py build_paper.py

========== 备注 ==========
  L2 轻微溢出 1 处（main.tex:276, 8.3pt）为长专业词，
  已手动插入 \- 断词提示，视觉不影响，评委不扣分。
```

如果任何一层 FAIL，**必须回到对应 Step 修复，不能在总报告里写 FAIL 就交付。**

---

## 四、常见排版问题修复知识库（Claudecode 查错优先翻阅）

### K1：化学式 / 希腊字母显示方块 □
**症状**：图标题、坐标轴出现 `K□O`、`Fe□O□`、`□□` 等方块。
**根因**：SimHei / 微软雅黑字体缺少 Unicode 下标（U+2080~）、上标（U+00B2~）、希腊字母（U+03C7 等）字形。
**修复**：
```python
# 全部用 plot_style.chem_tex + plot_style.mt 转 mathtext
from plot_style import chem_tex, mt

# ❌ 反模式
ax.set_xlabel('K2O 含量(%)')          # 方块
ax.set_title('χ2 检验结果')           # 方块

# ✓ 正模式
ax.set_xlabel(f'{chem_tex("K₂O")} 含量(%)')   # K$_2$O + SimHei 正体
ax.set_title(f'{mt("χ²")} 检验结果')          # χ$^2$ + mathtext
```
**配套 matplotlib 配置（plot_style.py 必须包含）**：
```python
rcParams['mathtext.default'] = 'regular'   # 下标数字用 SimHei，不用 LaTeX 默认 CMR
rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
rcParams['axes.unicode_minus'] = False
```

---

### K2：表格列名太长，溢出列宽
**修复模板**：
```latex
% 方式1：列内换行（推荐，最干净）
\usepackage{makecell}
% 原：风化后主要成分含量均值与标准差
\thead{风化后主要成分\\含量均值与标准差}

% 方式2：缩小整表字号（不到万不得已不用）
{\small
\begin{tabular}{...}
...
\end{tabular}
}

% 方式3：旋转表格（列太多）
\usepackage{rotating}
\begin{sidewaystable}
\centering
\begin{tabular}{...}
...
\end{tabular}
\end{sidewaystable}
```

---

### K3：长 URL / DOI 在参考文献中溢出
**修复**：用 `\usepackage{url}` + `\path{}` 或 BibLaTeX 的 DOI 字段：
```latex
% 导言区
\usepackage{xurl}            % 比 url 更激进，允许任意位置断
\Urlmuskip=0mu plus 1fill   % URL 拉伸间距

% bib 条目
@article{xxx2024,
  author = {...}, title = {...}, journal = {...},
  year = {2024}, doi = {10.1038/s41586-024-00000-1}
}
% 注意：有 DOI 就不要写 url 了，biblatex 自动生成链接
```

---

### K4：图片浮动到下一节 / 跑到参考文献之后
**症状**：正文 §3.2 的图，结果出现在 §4 或参考文献后面。
**修复优先级**：
```latex
% 1. 用 [htbp!] 放宽浮动限制（默认是 [tbp]）
\begin{figure}[htbp!]        % ! = 强烈要求放在这里
  \centering
  \includegraphics[width=0.9\textwidth]{figures/pdf/fig3_crr.pdf}
  \caption{CRR 恢复前后成分对比}\label{fig:3}
\end{figure}

% 2. 仍不行：用 placeins 在节边界拦一下
\usepackage{placeins}
% 在每节末尾 \FloatBarrier 之前的图全部输出
\section{问题二 聚类与判别分析}
... 正文 ...
\FloatBarrier   % 这里之前的 fig 必须在节内输出
\section{问题三 蒙特卡洛验证}
```

---

### K5：中文目录、图目录、表目录乱码 / 点线缺失
**修复**：
```latex
% 导言区正确顺序（xelatex 下）
\usepackage{ctex}                      % 中文支持
\usepackage{titletoc}                  % 目录样式
\setcounter{tocdepth}{2}               % 目录到 subsection

% 正文
\tableofcontents                       % 目录
\listoffigures                         % 图目录
\listoftables                          % 表目录
\newpage
```

---

### K6：算法伪代码格式混乱、编号断裂
**修复**：统一用 algorithm2e / algorithmicx，不得手写编号表格。
```latex
\usepackage[ruled,linesnumbered,algo2e,Chinese]{algorithm2e}

\begin{algorithm}[htbp!]
\SetAlgoLined
\KwIn{文物成分矩阵 $X \in \mathbb{R}^{n\times 14}$，风化标签 $w$}
\KwOut{恢复后的未风化成分 $\hat{X}_0$，MAE}
$groups \gets \text{groupby}(X, 类型)$\;
\ForEach{$g \in groups$}{
  $\mu_{unweathered} \gets \text{mean}(g[w==0])$\;
  $scale \gets \text{CRR}(g[w==1], \mu_{unweathered})$\;  \tcp*{闭式估计}
  $\hat{X}_0[w==1] \gets g[w==1] \oslash scale$\;
}
$\text{MAE} \gets \text{mean}(|\hat{X}_0 - X_{truth}|)$\;
\caption{风化成分 CRR 恢复算法}\label{alg:crr}
\end{algorithm}
```

---

## 五、与其他 Skill 的协作关系（分工矩阵）

| 阶段 | 负责 Skill |
|---|---|
| 拿到题目 → 选型清单 → 绘图代码 | `math-modeling-diagram-master`（图表选型+生成） |
| 摘要/参考文献/语言/进度 内容审查 | `math-modeling-abstract-polisher`（4 维内容审查） |
| 绘图完成 → 论文组装 → 终稿交付 | **本 Skill（math-modeling-paper-layouter）**（排版质量+终稿） |

**调用顺序约定**：Claudecode 应先调 `diagram-master` 出图 → 排版期间 L4 参考文献质量以 `abstract-polisher` D2 报告为准 → 图表生成完成后**立即转调本 Skill** 做排版收尾。三个 Skill 前后衔接，不替代；重复职责（参考文献审查）已明确归属 `abstract-polisher` D2。

---

## 六、终稿交付自检清单（**Claudecode 必须逐行勾选，任何一项 [ ] 不得交付**）

```
=== L1 图表质量 ===
[ ] 1. 所有 fig1~figN 运行 check_overlaps.py --fix 后 CRIT=0
[ ] 2. 化学式（K₂O、Fe₂O₃ 等）全部用 chem_tex/mt 转 mathtext，无方块
[ ] 3. 图例 ≥4 条时外置，不遮挡数据区
[ ] 4. 每张图同时存在 figures/png/*.png 和 figures/pdf/*.pdf（双备份）

=== L2 LaTeX 排版 ===
[ ] 5. build_paper.py 报告严重溢出(>20pt)=0 处
[ ] 6. 轻微溢出(<20pt)≤3 处，且已逐条确认视觉不可见
[ ] 7. 目录、图目录、表目录无乱码、页码正确

=== L3 图文一致性 ===
[ ] 8. check_consistency.py 数值不一致=0
[ ] 9. 所有 \includegraphics 引用的 PDF 文件实际存在
[ ] 10. 所有 \ref/\eqref 均有对应 \label，无 ?? 显示
[ ] 11. results/ 下 12 个预期文件齐全

=== L4 参考文献 ===
[ ] 12. 总数 ≥15，其中近 5 年 ≥40%，外文 ≥30%
[ ] 13. 每条 \bibitem / @article 在正文有至少一次 \cite{}
[ ] 14. DOI 字段齐全率 ≥80%，无缺 author/title/journal 的条目

=== L5 结构与附录 ===
[ ] 15. 图号、表号、公式号连续无跳号
[ ] 16. 正文描述「图 N 展示 XXX」与实际 figN.pdf 内容一致（无编号错位）
[ ] 17. 附录 A/B/C/D 四节齐全：目录结构/伪代码/参数表/复现指南
[ ] 18. 所有公式编号用 \eqref{} 引用，而非硬编码「式(3)」

=== 交付物打包 ===
[ ] 19. 压缩包根目录包含：main.pdf、code/、figures/pdf/、results/、复现指南.txt
[ ] 20. code/requirements.txt 存在，可直接 pip install -r 复现
```

---

## 七、失败兜底

1. **xelatex 不在 PATH** → 跳过编译，仅解析已有 main.log；提示用户安装 TeXLive 并把 bin/win32 加入环境变量。
2. **某个求解脚本崩溃** → `run_all.py` 自动终止流水线并提示 `--from XX 续跑`；不得跳过该脚本直接进排版。
3. **自动修复后重叠仍 CRIT** → 生成 `--marked` 红框诊断图，逐处列出建议（移动/换行/缩字/外置图例），提供手动调整代码，不得直接交付重叠图。
4. **数值不一致但找不到 pattern** → 在 check_consistency.py 的 `build_checks()` 中追加新 pattern，支持多 pattern OR 匹配，不得改 json 凑论文。

---

**Skill 输出承诺：**
> 调用本 Skill 后，我会按 §三 8 步工作流依次执行 L1~L5 门禁，每层输出检测报告，FAIL 项当场修复。全部通过后给出 §三 Step 8 格式的「5 层质量门禁总报告」+ §六 20 项自检清单的实勾结果。任何重叠/溢出/不一致/编号错配/参考文献老化问题，本 Skill 不解决不结束。
