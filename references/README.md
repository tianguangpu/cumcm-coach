# 参考文档渐进式导航

> 别一次性读完 20 篇 references + 768 行 SKILL.md。**按你当前所处的阶段，只读对应的文档**，需要时再加载下一份。
> 借鉴 [XiaoMaColtAI/math-modeling-skill](https://github.com/XiaoMaColtAI/math-modeling-skill) 的渐进式加载：先读主入口，按「何时加载」表按需取用。

## 主入口（先读这个）

- [`../SKILL.md`](../SKILL.md) — 完整流程（题型识别、金标准内核、工具接线、四级评审）

## 何时加载哪个文档

| 你现在在做什么 | 读这些 |
|---------------|--------|
| 拿到赛题，不知道从哪下手 | `SKILL.md` §1.1 题型识别 + `algorithms/misc/problem_analyzer.py` |
| 想选算法 | [`algorithms/hmml_index.md`](../algorithms/hmml_index.md)（三层检索：题型→方法→代码）|
| 要写建模章节 | [`gold-standard.md`](gold-standard.md)（六段子结构 / 公式三段式 / 四重检验）|
| 要出图 | [`figure-routing.md`](figure-routing.md)（图型→工具路由）+ [`figure-specs.md`](figure-specs.md)（配色/技法）|
| 要排版/编译论文 | [`typst-guide.md`](typst-guide.md)（Typst）或 `templates/*.tex`（LaTeX）|
| 交卷前检查 | `SKILL.md` §5 四级评审 + `scripts/auto_check.py` |
| 降 AI 味 | [`de-ai-writing.md`](de-ai-writing.md) + [`aigc-awareness.md`](aigc-awareness.md) |
| 装不上依赖 | [`external-deps.md`](external-deps.md) |

## 其余文档（按需，不必先读）

| 文档 | 什么时候读 |
|------|-----------|
| [`playbooks/`](playbooks/) | 5 本解题手册，按你的题型取一本（物理ODE/路径规划/调度优化/评价决策/数据洞察）|
| [`mcp-integration.md`](mcp-integration.md) | 想接 MCP（tavily/matlab/mcp-optimizer 等）时 |
| [`self-review-framework.md`](self-review-framework.md) | 交卷前的五轮自审 |
| [`code-inventory.md`](code-inventory.md) | 想看全部脚本清单时 |

## 一句话

**72 小时里，你不需要读完所有文档**。主入口 SKILL.md 的 §1.1（题型识别）+ 对应题型的 playbook + 交卷前的 auto_check，这三样就够跑完一题。其余按需加载。
