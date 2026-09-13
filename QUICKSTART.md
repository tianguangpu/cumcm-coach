# v7 快速启动指南

> 5 分钟上手，72 小时冲国一。

## 1. 环境准备（10 分钟）

```bash
# 安装核心依赖
pip install -r requirements.txt

# 验证安装
py -c "import numpy, scipy, pandas, matplotlib; print('核心依赖 OK')"
py -c "import highspy; print('HiGHS OK')" 2>/dev/null || echo "HiGHS 未安装（可选）"
```

## 2. 项目初始化（1 分钟）

```bash
# 创建项目目录
mkdir cumcm_2026C && cd cumcm_2026C

# 初始化项目结构
py ~/.claude/skills/cumcm-coach/scripts/init_project.py \
  --team "202600001" --members "张三,李四,王五" --type C
```

## 3. 快速试跑（30 分钟）

```bash
# 全链流水线（快速模式）
py ~/.claude/skills/cumcm-coach/scripts/run_all.py --fast

# 查看结果
ls results/
ls figures/png/
```

## 4. 正式比赛流程（72 小时）

### Day 1: 选题 + 建模（24h）
1. 比较 A/B/C 三题，选择最擅长的
2. 调用 `problem_analyzer.py` 分析题目
3. 调用 `innovation_guide.py` 确定创新方向
4. 建模求解，生成 `results/`

### Day 2: 图表 + 论文（24h）
5. 生成数据图（12-16张）
6. 生成流程图（1张）
7. 撰写论文（套用模板）
8. 去 AI 味自查

### Day 3: 评审 + 提交（24h）
9. L1-L4 四级评审
10. 修复所有 FAIL
11. 生成合规材料
12. 提交论文

## 5. 常用命令

```bash
# 检查可用求解器
py scripts/solver_router.py

# 运行 L1-L4 评审
py scripts/auto_check.py --paper paper/main.tex --level all

# 生成合规材料
py scripts/ai_compliance.py all

# 文献检索
py scripts/search_openalex.py --query "optimization" --limit 10

# 查看进度
py scripts/run_all.py --dry
```

## 6. 故障排除

| 问题 | 解决方案 |
|------|---------|
| 求解器不可用 | `pip install highspy pulp ortools` |
| LaTeX 编译失败 | 检查 MiKTeX/TeX Live 安装 |
| 中文乱码 | 安装 SimHei 字体 |
| 图表不显示 | 检查 matplotlib 后端设置 |

## 7. 参考文档

- `SKILL.md` - 主文档（921行）
- `references/gold-standard.md` - 金标准详细规范
- `references/typst-guide.md` - Typst 转译指南
- `references/de-ai-writing.md` - 去 AI 味指南
- `references/playbooks/` - 5 本解题手册
