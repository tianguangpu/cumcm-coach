# Changelog

本文件记录 CUMCM Coach Skill v7 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [7.11.0] - 2026-09-11

### Added
- **项目级文档**: README.md（徽章+功能概览+架构图+使用示例）
- **版本管理**: CHANGELOG.md + CONTRIBUTING.md
- **Git Hooks**: pre-commit 配置（black + flake8 + 烟雾测试）
- **正式单元测试**: pytest 测试套件，覆盖 34 个算法模块
- **Docker 容器化**: Dockerfile + docker-compose.yml
- **统一日志系统**: utils/logger.py，替代 print 输出
- **Makefile 自动化**: test/lint/build/benchmark/clean 等命令
- **基准测试可视化**: scripts/benchmark_viz.py，生成性能对比雷达图
- **算法接口标准化**: algorithms/base.py，BaseSolver 抽象基类 + SolverResult 数据类

### Changed
- 烟雾测试从独立脚本迁移至 pytest 框架
- 算法模块统一继承 BaseSolver 基类

---

## [7.10.0] - 2026-08-28

### Added
- **烟雾测试扩展**: 18→34 模块（+89%），新增 VRP/JobShop/TwoStage/AHO/PSO-Variants/Nash/Population/FDM2D/FEM/Sobol/AssumptionError/Hypothesis
- **Typst 支持**: check_paper_quality.py 自动检测 .typ 后缀，解析 Typst 摘要/公式/图表/参考文献
- **数据加载**: baseline_compare.py 新增 --data 参数支持 CSV/JSON/NPY
- **内置路由**: solver_router.py 新增 solve_vrp/solve_job_shop/solve_tsp_ga/select_solver_auto
- **依赖清单**: requirements.txt 标注必选/可选，补充 pyyaml/requests
- **流程集成**: run_all.py 步骤 10b 集成 check_references.py
- **SKILL.md 精简**: 923→785 行（-15%），详细示例移入 references/v7-features-guide.md

### Fixed
- solver_router VRP 路径 bug

---

## [7.9.0] - 2026-08-26

### Added
- **Typst 模板**: 7 套模板（国赛 A/B/C/D + 华数杯 + 华为杯 + MCM/ICM）
- **论文质量自检**: check_paper_quality.py，6 维度 100 分制检查
- **国一论文模板库**: references/excellent-papers/，收录历年国一论文特征
- **Obsidian 知识系统**: vault/ 目录，60 笔记 + 332 wikilinks

### Changed
- 模板目录结构调整：templates/ 下按赛事分类

---

## [7.8.0] - 2026-08-24

### Added
- **代码清单增强**: gen_code_manifest.py 新增 --check-deps / --check-syntax
- **参考文献审查**: check_references.py，检查近 5 年/外文比例

### Fixed
- 文献综述生成 bug

---

## [7.7.5] - 2026-08-22

### Added
- **四重检验自动化**: auto_check.py L1-L4 分级评审
- **基线比较机制**: baseline_compare.py，correctness beats sophistication
- **数值结果溯源**: result_registry.py，防止论文引用未验证数值

### Changed
- 验证流程从手动改为自动化

---

## [7.7.0] - 2026-08-20

### Added
- **精修闭环**: scipilot-figure-skill + check_figure.py --strict + AI 读图复核
- **文字重叠修复**: paper-layouter 的 check_overlaps.py --fix
- **72h 进度看板**: abstract-polisher 的 dashboard.py

### Fixed
- 图表文字重叠问题

---

## [7.6.0] - 2026-08-18

### Added
- **图型路由**: references/figure-routing.md 三级路由单一事实源
- **流程图约定**: diagram-design 唯一工具，黑白灰度无彩色

### Changed
- 流程图从多工具统一为 diagram-design

---

## [7.5.0] - 2026-08-15

### Added
- **创新算法库**: algorithms/innovative_index.md，30 种智能优化 + 21 改进组合
- **HMML 分层索引**: algorithms/hmml_index.md，三层检索（问题类型→建模方法→代码实现）

---

## [7.4.0] - 2026-08-12

### Added
- **消融对比**: ablation.py v2.0，统计检验 + LaTeX 表
- **并行消融**: ablation_parallel.py，多算法并行对比

---

## [7.3.0] - 2026-08-10

### Added
- **边界检验**: boundary_scan.py，灵敏度扫描 + 蒙特卡洛边界 + 失效边界
- **复现保障**: reproducibility.py，Makefile + requirements.txt + 哈希清单

---

## [7.2.0] - 2026-08-08

### Added
- **伦理维度**: check_ethics.py，公平性/可持续性/社会影响/风险伦理
- **创新百分比**: check_innovation.py，模糊表述检测 + 精确量化验证

---

## [7.1.0] - 2026-08-05

### Added
- **AI 合规**: ai_compliance.py，2026 新规 AI 工具使用声明
- **去 AI 味指南**: references/de-ai-writing.md

### Changed
- AI 味检测从脚本改为参考指南

---

## [7.0.0] - 2026-08-01

### Added
- **初版发布**: 28 个主脚本 + 34 个算法模块
- **全链流水线**: run_all.py，13 步断点续跑
- **项目初始化**: init_project.py
- **求解器路由**: solver_router.py
- **文献检索**: search_openalex.py

### Changed
- 从 v6 架构重构为 v7 模块化架构

---

## 版本命名规则

- **主版本号 (MAJOR)**: 架构重大变更
- **次版本号 (MINOR)**: 新功能/新算法
- **修订号 (PATCH)**: Bug 修复/文档更新

---

## 链接

- [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)
- [语义化版本](https://semver.org/lang/zh-CN/)
