# 路线图

本文档记录项目方向与已知改进项。欢迎就其中任何一条提 Issue 或 PR，
参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 当前状态（v7.12.0）

| 指标 | 数值 |
|------|------|
| 算法模块 | 36 个（9 个方向） |
| 工具脚本 | 30 个 |
| 测试 | 119 passed / 0 skipped |
| 覆盖率 | 46.5% |
| ruff 检查 | 0 问题 |

---

## v8.0 规划方向

### 1. 测试覆盖率 → 80%

当前 46.5%，缺口集中在几个大模块：

| 模块 | 语句数 | 当前覆盖率 |
|------|--------|-----------|
| `optimization/job_shop.py` | 350 | 9.7% |
| `optimization/two_stage.py` | 250 | 8.0% |
| `optimization/nsga2.py` | 223 | 8.5% |
| `validation/auto_tune.py` | 163 | 17.8% |
| `validation/shap_analysis.py` | 158 | 15.2% |

**为什么值得做**：这几个模块是 B 题（优化调度类）的主力工具，也是
当前缺陷最可能潜伏的地方——它们只被"导入冒烟测试"覆盖过。

### 2. 解决 NSGA-II 段错误 ✅（已解决）

`optimization/nsga2.py` 在同进程内连续实例化多个求解器时会触发段错误。
已通过 `scripts/isolated_solve.py` 的子进程隔离解决，并新增真实 solve
回归测试（`test_solve_returns_pareto_front`）固化，防「段错误误判」回归。

### 3. 示例扩充

现有 4 个示例覆盖 B/C/D 题型与通用验证。可补充：

- A 题（机理建模）示例：FDM 求解 + 网格收敛性分析
- 完整的"赛题 → 论文"端到端示例（含 LaTeX 编译）
- 图表生成示例（300dpi PNG + 矢量 PDF 双导出）

### 4. 恢复 `ruff format`

`ruff 0.16.x` 对 `ecology` / `game` / `mechanistic` / `misc` / `stats`
等含多字节字符的文件会触发 Rust panic（上游 bug）。

**待办**：跟踪上游修复，恢复 `ruff format` 钩子并统一代码格式。
当前 `make format` 使用 black 替代。

### 5. 文档国际化

`README.en.md` 已覆盖安装与代码使用，但 `SKILL.md`、`references/`
与 `vault/` 仍为纯中文。

**权衡**：国赛论文本身是中文写作，模板与规范以中文为主是合理的；
但算法模块（`algorithms/`）的 docstring 可逐步补英文摘要，
便于国际用户复用其中的优化/预测/评价算法。

### 6. 算法库扩充

候选方向（按国赛出现频率）：

- 时间序列：Prophet 风格的变点检测、STL 分解
- 优化：NSGA-III（多目标 ≥4 目标）、约束处理的自适应惩罚
- 图论：最小费用最大流、二分图匹配
- 统计：贝叶斯参数估计、Bootstrap 置信区间（现已部分覆盖）

### 7. 补全 B/C 题端到端案例

当前只有 2026 E 题一个完整端到端案例。建议补：

- **B 题优化**：完整跑一个调度/分配类真题，验证 SA-PSO / GA / NSGA2 链路
- **C 题评价**：纯评价题（无求解难度，最看论证完整度），验证 AHP+熵权+TOPSIS

### 8. Docker 一键环境

新用户要装 Python + LaTeX + MATLAB + 8 个 MCP 才能完整体验，门槛高。
建议出 `docker-compose up` 一键起 Python + LaTeX 路径的环境，至少让
核心链路 5 分钟跑起来。

### 9. 「国一冲刺级」基准对照

强承诺缺乏公开对照数据。建议在 `docs/` 放一份「2023/2024 国一论文 vs
本工具产出」的对比报告，把这个承诺坐实。

---

## 已知限制（不计划修复）

以下为有意的设计选择，非缺陷：

- **MCP 工具均为可选**：`fetch` / `tavily` / `matlab` 等未连接时自动
  降级到内置实现，流程不中断。这是为了让项目在最小环境下也能跑通。
- **MATLAB 相关功能需本机安装**：未安装时降级到 Python 绘图。
- **`tam` 库需单独安装**：未安装时降级为简化加法分解，**此时论文中
  必须如实说明**，不得声称使用了 TAM 的物理约束或 PyTorch 后端。

---

## 贡献机会

适合首次贡献的任务：

- [ ] 为 `job_shop.py` / `two_stage.py` 补充单元测试（见方向 1）
- [ ] 补充 A 题（机理建模）示例（见方向 3）
- [ ] 为 `algorithms/` 下的模块 docstring 补英文摘要（见方向 5）
- [ ] 补 B/C 题端到端案例（见方向 7）
- [ ] 编写 Dockerfile + docker-compose 一键环境（见方向 8）

提 PR 前请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并确保
`make test` 与 `ruff check algorithms/ scripts/ utils/ tests/` 通过。
