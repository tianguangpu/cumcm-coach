# 外部依赖说明

cumcm-coach 的设计原则是**自包含**：核心流程（题型识别 → 建模求解 →
图表 → 论文 → 四级评审）不依赖任何本仓库之外的 Skill 或 MCP。

本文列出**可选**的外部组件 —— 装了能补强特定环节，不装也不影响流程跑通。

---

## 一、已随仓库分发（无需额外安装）

以下模块的副本已在 [`integrations/`](../integrations/) 内，
克隆本仓库即可使用：

**出图链路**：`math-modeling-diagram-master`（选型）、`figure-skill`（常规图）、
`mathmodel-figure-templates`（高级图）、`nature-plot-repro`（顶刊复刻）、
`scipilot-figure-skill`（出版级审查）、`diagram-design`（流程图）

**论文链路**：`math-modeling-abstract-polisher`（摘要/文献/AI 味）、
`math-modeling-paper-layouter`（排版门禁）

详见 [`integrations/README.md`](../integrations/README.md)。

---

## 二、可选协作 Skill（未分发）

以下 Skill **未随本仓库分发**，原因见各自说明。若你在本地已安装，
v7 的流程文档会引用到它们；未安装也不影响核心流程。

### 2.1 MathModelAgent 系列

| Skill | 作用 | 与 v7 的关系 |
|-------|------|-------------|
| `1start-mathmodel` | 启动建模（询问偏好 → 生成 plan/todo） | v7 的 §0–§1 已覆盖 |
| `2analysis-modeling` | 子问题拆解 → 建模报告 | v7 的 §2 已覆盖 |
| `3coding-visual` | 编码实现 + 数据图 | v7 的 §2–§3 已覆盖 |
| `4drawio` | draw.io 流程图 | v7 已统一到 `diagram-design` |
| `5writing` | 17 套赛事模板（Typst + LaTeX） | **仅非国赛赛事需要** |
| `6verity` | 9 步验收门禁 | v7 的 L1–L4 四级评审已覆盖 |
| `_references` | 共享规范知识库 | v7 的 `references/` 已覆盖 |
| `doctor` | 环境检查与安装向导 | 可选，v7 未含环境自检 |

**结论**：做国赛，这些都可以不装 —— v7 本身就是国赛主编 Skill，
功能上是它们的超集。

**何时才需要**：参加 MCM/ICM、华为杯、华中杯、APMCM 等**非国赛赛事**时，
`5writing` 的 17 套赛事模板有价值（v7 只提供国赛及少量赛事模板）。

### 2.2 其他

| Skill | 作用 | 何时需要 |
|-------|------|---------|
| `typst-author` | Typst 语法、编译与调试 | v7 支持 Typst 引擎；排版遇到语法问题时可装 |
| `mathmodel-flowchart` | LogicFlow 浏览器流程图工作室 | v7 已统一到 `diagram-design`；仅在需要浏览器手工微调时用 |

---

## 三、MCP 工具

8 个 MCP 全部为**可选增强**，配置方法见
[`mcp-setup.md`](mcp-setup.md)。一个都不配也能跑通全流程。

---

## 四、系统级依赖

| 依赖 | 用于 | 必需性 |
|------|------|--------|
| Python ≥ 3.9 | 全部脚本 | **必需** |
| LaTeX（XeLaTeX + biber） | 论文编译 | 二选一 |
| Typst ≥ 0.11 | 论文编译 | 二选一 |
| SimHei 字体 | 中文图表渲染 | 绘图时必需 |
| MATLAB R2024a+ | 惊艳图（26 案例复刻） | 可选，降级到 Python |
| Node.js ≥ 18 | npx 启动类 MCP | 可选 |

### 字体说明

中文字体缺失会导致图表出现方框（缺字）。安装 SimHei 或任一
CJK 字体即可；`integrations/figure-skill` 的字体栈已配置回退链：

```python
["SimHei", "Microsoft YaHei", "DejaVu Sans"]
```

Linux 上通常装 `fonts-noto-cjk` 或 `fonts-wqy-zenhei`。

---

## 五、降级行为一览

本项目的每个外部依赖都有明确的降级路径，**不会因缺失而中断**：

| 缺失项 | 降级行为 |
|--------|---------|
| 全部 MCP | 走 `algorithms/` 内置实现 |
| MATLAB | 走 Python 绘图（`integrations/figure-skill`） |
| SALib | Sobol 分析降级为纯 numpy 实现（**论文须说明**） |
| `tam` 库 | 降级为简化加法分解（**论文须说明**） |
| `shap` 库 | 跳过 SHAP 分析 |
| sklearn | 跳过 AutoTuner 相关功能 |
| LaTeX / Typst | 无法编译 PDF，但其余产物照常生成 |

> ⚠️ **重要**：凡是通过降级路径得到的结果，**论文中必须如实说明**
> 实际使用的实现，不得声称使用了未安装的工具。这是国赛 AI 合规
> 与学术诚信的基本要求。
