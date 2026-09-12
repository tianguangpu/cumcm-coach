# MCP 配置指南

> **先看这一句**：cumcm-coach 的 8 个 MCP **全部是可选增强**。一个都不配，
> 核心流程（题型识别 → 建模求解 → 图表 → 论文 → 四级评审）照样能跑通，
> 因为每个环节都有内置实现兜底。配了只是「更省事、更强」。
>
> [`mcp-integration.md`](mcp-integration.md) 讲的是**怎么调用**这些工具；
> 本文讲的是**怎么装**。

---

## 一、必需性分级

| MCP | 作用 | 不配的后果 |
|-----|------|-----------|
| **（无）** | 核心流程零 MCP 依赖 | — |
| `matlab` | MATLAB 绘图（惊艳图 26 案例） | 降级到 Python 绘图（`integrations/figure-skill`） |
| `gurddy-mcp` | 生产规划 / 图着色 / 博弈一键求解 | 降级到 `algorithms/` 内置实现 |
| `mcp-optimizer` | LP/MIP/VRP/调度/指派求解 | 降级到 `highspy` / `pulp` / `ortools`（需 pip 装） |
| `mcp-mathematics` | 公式推导 / 统计 / 矩阵 / 单位换算 | 降级到 `scipy` / `numpy` |
| `numpy-mcp` | 张量存储与矩阵运算 | 降级到直接 `import numpy` |
| `fetch` | 抓取网页/JSON/数据 | 无法抓线上数据（可手工下载） |
| `tavily` | 文献检索 / 行业背景 / 深度研究 | 无法自动检索（`search_openalex.py` 不依赖它） |
| `image-reader` | AI 读图复核图表质量 | 跳过 AI 读图环节（仍有程序自检） |

**结论**：只做国赛论文，**最小配置是零 MCP**；想要更好的图表与检索体验，
按需增配即可。

---

## 二、配置位置

Claude Code 的 MCP 配置写在 `~/.claude.json` 的 `mcpServers` 字段。

Windows 路径：`C:\Users\<你的用户名>\.claude.json`

也可用 CLI 添加：

```bash
claude mcp add <名称> -- <命令> <参数...>
```

---

## 三、逐个配置

### 3.1 本地 Python 包（4 个）

`numpy-mcp`、`mcp-optimizer`、`mcp-mathematics`、`gurddy-mcp` 都是
Python 模块，需要一个装了它们的 Python 环境。

**建议用独立虚拟环境**（避免污染系统 Python）：

```bash
# 建环境
python -m venv ~/mcp-venv

# 装包（Windows 用 mcp-venv\Scripts\python.exe，macOS/Linux 用 mcp-venv/bin/python）
~/mcp-venv/Scripts/python.exe -m pip install numpy mcp numpy-mcp mcp-optimizer mcp-mathematics
```

> `gurddy-mcp` 若不在 PyPI，需从其源码目录安装：
> `pip install -e /path/to/gurddy`（模块入口为 `mcp_server.mcp_stdio_server`）。

配置片段（把 `PYTHON` 换成你环境的 python 绝对路径）：

```json
{
  "mcpServers": {
    "numpy-mcp": {
      "command": "PYTHON",
      "args": ["-m", "numpy_mcp"]
    },
    "mcp-optimizer": {
      "command": "PYTHON",
      "args": ["-m", "mcp_optimizer"]
    },
    "mcp-mathematics": {
      "command": "PYTHON",
      "args": ["-m", "mcp_mathematics"]
    },
    "gurddy-mcp": {
      "command": "PYTHON",
      "args": ["-m", "mcp_server.mcp_stdio_server"]
    }
  }
}
```

### 3.2 走 npx 的（2 个）

`fetch` 与 `matlab` 通过 `npx` 启动，**需要先装 Node.js**（含 npx）。

```json
{
  "mcpServers": {
    "fetch": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@tokenizin/mcp-npx-fetch"]
    },
    "matlab": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "matlab-mcp"],
      "env": {
        "MATLAB_PATH": "D:\\MatLab\\bin\\matlab.exe"
      }
    }
  }
}
```

> - macOS / Linux 上把 `"command": "cmd"` 与 `"/c"` 去掉，直接用 `"npx"`。
> - `matlab` 的 `MATLAB_PATH` 改成你本机的 MATLAB 可执行文件绝对路径；
>   **没装 MATLAB 就不要配这个**，绘图会自动走 Python。

### 3.3 需要 API Key 的（`tavily`）

`tavily` 用于文献检索与深度研究，需要[Tavily](https://tavily.com/) 的 API Key。

```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "<你的 Key>"
      }
    }
  }
}
```

> ⚠️ **不要把真实 Key 提交到 Git**。本仓库的 `.gitignore` 已忽略
> `~/.claude.json` 类文件，但请在提交任何配置前自行确认。

### 3.4 `image-reader`

用于出图后做 AI 读图复核（检查文字遮蔽、子图对齐）。需要视觉模型的
API 凭据，配置方式取决于你选用的服务商（如 GLM-4V-Plus）。

**不配的影响**：仅跳过「AI 读图」这一道软性复核，
`scripts/check_figure_quality.py` 与 `check_overlaps.py` 仍会执行。

---

## 四、最小配置建议

按投入产出排序，推荐这样分三步走：

| 阶段 | 配什么 | 理由 |
|------|--------|------|
| **第一步（零成本）** | 什么都不配 | 核心流程已可跑通，先验证环境 |
| **第二步（推荐）** | `mcp-mathematics` + `numpy-mcp` | 纯本地包，无 API Key，覆盖公式推导与矩阵运算 |
| **第三步（按需）** | `fetch` + `tavily` | 需要文献综述、行业背景时再加 |

`matlab` 只在你要复刻顶刊级惊艳图、且本机已装 MATLAB 时才需要。

---

## 五、验证配置是否生效

```bash
# 列出已连接的 MCP
claude mcp list

# 在会话内查看
/mcp
```

若某个 MCP 未连接，流程不会中断——对应环节自动走内置实现，
并在日志中标注降级（例如 Sobol 分析会提示「SALib 未安装，降级到纯 numpy」）。

---

## 六、故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| MCP 显示为 failed | `command` 路径错误 | 用绝对路径，Windows 注意反斜杠转义 `\\` |
| `npx` 相关 MCP 启动失败 | 未装 Node.js | 安装 Node.js ≥ 18 |
| Python 包 MCP 启动失败 | 模块未装在该环境 | 用该环境的 python 执行 `-m pip install` |
| MATLAB MCP 报路径错误 | `MATLAB_PATH` 不对 | 指向 `matlab.exe` 而非安装目录 |
| 中文路径报错 | 编码问题 | 尽量把项目放在纯英文路径下 |

---

## 七、与论文合规的关系

国赛要求提交「AI 工具使用声明」。若你使用了任何 MCP 工具，
`scripts/ai_compliance.py` 会自动记录并生成声明材料：

```bash
python scripts/ai_compliance.py log      # 记录一次 AI 辅助
python scripts/ai_compliance.py all      # 生成声明 + 支撑材料
```

**声明必须如实填写实际使用的工具**，虚假声明会导致取消评奖资格。
