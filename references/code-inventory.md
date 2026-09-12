# v7 代码清单（自动生成）

> 由 `scripts/gen_code_manifest.py` 生成。**勿手改本文件**，改脚本后重跑刷新。

> 根目录：`D:\ClaudeCode\.claude\skills\cumcm-coach-skill-v7`

- 文件总数：87（其中 Python 75 个）


## scripts/（编排/检查/工具脚本）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `ablation.py` | 390 | ablation.py v2.0 — 多算法消融对比框架 | `_np`, `write_ablation`, `validate_ablation`, `run_ablation`, `statistical_test`, `generate_latex_table` …(+2) |
| `ablation_parallel.py` | 129 | ablation_parallel.py — 多算法消融的满核并行版(子进程隔离) | `run_ablation_parallel`, `main` |
| `ai_compliance.py` | 463 | ai_compliance.py — 2026 国赛 AI 工具使用合规模块 | `AILogger`, `main` |
| `auto_check.py` | 1196 | 自动化自检脚本 v7-pro — L1-L4 四级评审 + 5 项 PRO 冲刺检查 | `PaperChecker`, `main` |
| `baseline_compare.py` | 436 | 基线比较机制 v1.0 — 验证高级模型必须优于简单基线 | `BaselineModels`, `BaselineComparator`, `main` |
| `boundary_scan.py` | 314 | boundary_scan.py — 边界检验 + 鲁棒性分析 | `sensitivity_scan`, `_grade_elasticity`, `monte_carlo_boundary`, `find_failure_boundary`, `render_report`, `main` |
| `check_abstract.py` | 319 | 摘要质量自动评分 — 检查结构/数值密度/创新量化/关键词/AI味 | `extract_abstract_from_tex`, `check_abstract_structure`, `check_numerical_density`, `check_innovation_quantification`, `check_keywords`, `check_ai_flavor` …(+2) |
| `check_ethics.py` | 172 | check_ethics.py — 伦理维度检查（2025年新增） | `check_ethics_content`, `render_report`, `main` |
| `check_innovation.py` | 255 | check_innovation.py — 创新百分比强制检查 | `extract_innovations`, `check_ablation_coverage`, `generate_fix_suggestions`, `render_report`, `main` |
| `check_paper_quality.py` | 435 | 论文质量自检脚本 v1.0 | `PaperQualityChecker`, `main` |
| `check_references.py` | 249 | 参考文献自动审查 — 检查数量/年份/语言/格式/URL可访问性 | `extract_refs_from_bib`, `extract_refs_from_tex`, `check_references`, `generate_report` |
| `embed_figures.py` | 80 | 图表自动嵌入 — 读取 figure_manifest.json,在对应章节文件中插入图表引用 | `embed_figures` |
| `gen_code_manifest.py` | 318 | gen_code_manifest.py — v7 代码清单自动生成（增强版 v1.1） | `_first_line`, `extract_py`, `extract_text`, `_render_table`, `render_markdown`, `scan` …(+4) |
| `gen_figure_manifest.py` | 50 | 图表清单生成 — 扫描 figures 目录,生成 figure_manifest.json | `gen_manifest` |
| `gen_lit_review.py` | 192 | gen_lit_review.py — 文献综述模块 | `render_latex`, `render_markdown`, `try_openalex`, `main` |
| `gen_ppt_outline.py` | 279 | gen_ppt_outline.py — 国赛答辩PPT自动生成 | `extract_paper_info`, `extract_results`, `generate_markdown`, `generate_pptx`, `main` |
| `init_project.py` | 216 | init_project.py — 国赛项目初始化 | `init_project`, `main` |
| `isolated_solve.py` | 167 | isolated_solve.py — 子进程隔离求解执行器 (v1.1) | `_box_repair`, `_box_obj`, `_make_bench`, `_worker`, `run_isolated`, `_main` |
| `mc_multirun.py` | 102 | mc_multirun.py — 蒙特卡洛多轮满核并行评估(子进程隔离) | `run_mc_sim`, `main` |
| `mcp_router.py` | 286 | mcp_router.py — MCP 工具智能路由 | `check_mcp_status`, `_get_api_count`, `route_problem`, `print_route`, `main` |
| `polish_abstract.py` | 233 | polish_abstract.py — 摘要"5+3"结构检查 + 8稿迭代追踪 | `extract_abstract`, `check_5plus3`, `track_draft`, `render_report`, `main` |
| `reproducibility.py` | 208 | reproducibility.py — 一键复现 + 哈希绑定 | `file_hash`, `scan_project`, `generate_makefile`, `generate_requirements`, `verify_reproducibility`, `main` |
| `result_registry.py` | 322 | 数值结果溯源注册表 v1.0 — 确保每个写入论文的数值可溯源 | `init_registry`, `load_registry`, `save_registry`, `add_result`, `verify_registry`, `generate_report` …(+1) |
| `run_all.py` | 338 | run_all.py — 国赛全链流水线 | `run_step`, `run_pipeline`, `main` |
| `search_openalex.py` | 218 | search_openalex.py — OpenAlex 文献自动检索 | `search_openalex`, `format_bibtex_entry`, `format_table`, `save_bibtex`, `main` |
| `self_verify.py` | 180 | self_verify.py — 求解结果自证门禁（借鉴 AutoMCM-Pro 强制代码自证） | `_is_bad`, `SelfVerifier`, `verify_from_results`, `main` |
| `semantic_anchor.py` | 340 | 语义锚点验证 — 借鉴 SAC-Opt 思想 | `SemanticAnchor`, `VerificationResult`, `extract_anchors_from_problem`, `_extract_keywords`, `verify_anchors_against_paper`, `verify_against_decision_log` …(+2) |
| `solver_router.py` | 126 | HiGHS Enhanced Solver Router | `select_solver`, `solve_lp`, `solve_mip`, `_solve_highs`, `_solve_pulp`, `_solve_scipy` …(+1) |
| `test_ai_compliance.py` | 100 | test_ai_compliance.py — AI 合规模块单元测试 | `test_full_workflow` |
| `test_algorithms_smoke.py` | 131 | test_algorithms_smoke.py — 算法回归冒烟测试 | `check`, `test_optimizers_feasibility`, `main` |
| `writing_check.py` | 198 | writing_check.py — 论文写作质量检查（Windows兼容版） | `read`, `rel`, `check_paper`, `main` |

## algorithms/ecology/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `ecology/__init__.py` | 1 |  |  |
| `ecology/population.py` | 150 | cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 种群动态 / 传染病模型 | `_as_time`, `lotka_volterra`, `SIR`, `SEIR` |

## algorithms/evaluation/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `evaluation/__init__.py` | 2 | cumcm-coach v7 — 评价类算法包(AHP/熵权/TOPSIS/VIKOR/GRA)。 |  |
| `evaluation/ahp_entropy_topsis.py` | 289 | AHP + 熵权 + TOPSIS 综合评价流程 | `ComprehensiveEvaluation`, `demo` |
| `evaluation/gra.py` | 45 | 灰色关联分析(GRA) — 评价题/相关性题常用,可与 VIKOR/TOPSIS 做消融对照 | `grey_relational` |
| `evaluation/vikor.py` | 54 | VIKOR 多准则折中排序 — 评价/决策题(国赛 C 题)常用,可与 TOPSIS 做消融对照 | `VIKOR` |

## algorithms/game/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `game/__init__.py` | 1 |  |  |
| `game/nash.py` | 140 | cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 纳什均衡 | `_profile_is_nash`, `pure_nash`, `mixed_nash_2x2` |

## algorithms/mechanistic/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `mechanistic/__init__.py` | 2 | cumcm-coach v7 — 机理类算法包(有限差分 FDM)。 |  |
| `mechanistic/de_quickref.py` | 90 | cumcm-coach 机理求解模块 — PDE 数值解法速查表 | `query` |
| `mechanistic/fdm_1d.py` | 58 | 一维有限差分法(FDM)求解扩散/热传导方程 — 机理题(国赛 A 题)数值求解模板 | `heat_1d_explicit` |
| `mechanistic/fdm_2d.py` | 105 | cumcm-coach 机理求解模块 — 二维有限差分法(FDM)求解扩散/热传导方程 | `fdm_2d_explicit` |
| `mechanistic/fem_poisson.py` | 136 | cumcm-coach 机理求解模块 — 三角网格有限元(FEM)解 Poisson 方程 | `rect_tri_mesh`, `_shape_data`, `_coerce_mesh`, `assemble_and_solve` |
| `mechanistic/ode_solver.py` | 87 | cumcm-coach 机理求解模块 — 常微分方程(ODE)直接数值求解器封装 | `_coerce`, `euler`, `rk4`, `solve_ivp_wrapper` |

## algorithms/misc/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `misc/innovation_guide.py` | 145 | innovation_guide.py — 创新点生成机制重构 (P0-2) | `suggest_innovations`, `eval_direction` |
| `misc/problem_analyzer.py` | 175 | problem_analyzer.py — 问题理解模块 (P0-4) | `_extract_sentences`, `_find_context_terms`, `_ambiguity_scan`, `_constraint_mining`, `_dependency_map`, `analyze_problem` …(+1) |

## algorithms/network/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `network/__init__.py` | 2 | cumcm-coach v7 — 图论/网络算法包(Dijkstra/Kruskal/最大流)。 |  |
| `network/graph_algo.py` | 121 | 图论算法 — Dijkstra 最短路 / Kruskal 最小生成树 / Edmonds-Karp 最大流 | `dijkstra`, `kruskal`, `max_flow` |

## algorithms/optimization/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `optimization/__init__.py` | 2 | cumcm-coach v7 — 优化类算法包(SA-PSO/GA/DE)。 |  |
| `optimization/adaptive_hybrid.py` | 115 | 自适应混合优化器 (Adaptive Hybrid Optimizer, AHO) | `AdaptiveHybrid` |
| `optimization/de.py` | 202 | DE: 差分进化算法 | `DE`, `demo` |
| `optimization/ga.py` | 247 | GA: 遗传算法 | `GA`, `demo` |
| `optimization/job_shop.py` | 689 | 作业车间调度（JSSP）求解器 v1.0 | `JobShopScheduler`, `FlexibleJobShopScheduler` |
| `optimization/nsga2.py` | 309 | NSGA-II 多目标优化器 (实数编码)。 | `_dominates`, `_fast_non_dominated_sort`, `_crowding_distance`, `_hypervolume`, `_spread`, `NSGA2` |
| `optimization/pso_variants.py` | 173 | cumcm-coach-skill-v7 《优化》子模块 —— PSO 变体 / 高级约束策略 / 混合算法框架 | `clerc_constriction`, `pso_clerc`, `pso_tvac`, `feasibility_rule`, `epsilon_constrained`, `pso_plus_local_search` …(+1) |
| `optimization/sa_pso.py` | 296 | SA-PSO: 模拟退火粒子群优化算法 | `SA_PSO`, `demo` |
| `optimization/two_stage.py` | 544 | 两阶段求解框架 v1.0 | `TwoStageSolver`, `FacilityLocationSolver` |
| `optimization/vrp.py` | 595 | VRP/MTVRP 车辆路径问题求解器 v1.0 | `VRP`, `MTVRP` |

## algorithms/prediction/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `prediction/__init__.py` | 2 | cumcm-coach v7 — 预测类算法包(TAM/ARIMA/MLP/GM11)。 |  |
| `prediction/arima.py` | 251 | ARIMA: 差分整合移动平均自回归模型 | `ARIMA_Forecast`, `demo` |
| `prediction/gm11.py` | 66 | GM(1,1) 灰色预测模型 — 小样本时序预测(国赛 D 题/预测题高频) | `GM11` |
| `prediction/mlp.py` | 161 | MLP: 多层感知机序列预测 | `MLP_Forecast`, `demo` |
| `prediction/tam.py` | 252 | TAM (Time Series Additive Model) — D 数据型首选算法 | `TAM_Forecast` |

## algorithms/stats/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `stats/__init__.py` | 1 |  |  |
| `stats/hypothesis.py` | 118 | cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— 统计检验 | `_summary`, `_frozen_dist`, `ks_test`, `anova_oneway`, `chisq_test`, `mann_whitney_u` …(+1) |

## algorithms/validation/（算法库）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `validation/__init__.py` | 2 | cumcm-coach v7 — 检验类算法包(拟合精度/蒙特卡洛/灵敏度/SHAP/调参)。 |  |
| `validation/assumption_error.py` | 142 | AssumptionError: 假设误差量化 | `AssumptionChecker`, `_grade`, `_judge`, `_overall_judge`, `demo` |
| `validation/auto_tune.py` | 383 | 自动超参调优 + 交叉验证框架 | `AutoTuner`, `quick_cv` |
| `validation/metrics.py` | 155 | Metrics: 拟合精度指标 + 残差分析 | `FitMetrics`, `demo` |
| `validation/monte_carlo.py` | 222 | MonteCarlo: 蒙特卡洛模拟 | `MonteCarlo`, `demo` |
| `validation/sensitivity.py` | 146 | Sensitivity: 灵敏度分析 | `SensitivityAnalyzer`, `demo` |
| `validation/shap_analysis.py` | 324 | SHAP 可解释性分析 — 模型特征重要性解释 | `SHAPAnalyzer` |
| `validation/sobol.py` | 130 | cumcm-coach 博弈/生态/统计/全局灵敏度模块 —— Sobol 全局灵敏度分析 | `sobol_total_and_first` |
| `validation/sobol_enhanced.py` | 193 | Sobol 全局灵敏度分析 — 增强版（SALib 优先 + 纯 numpy 降级） | `_sobol_numpy`, `_sobol_salib`, `sobol_analysis` |

## algorithms/（索引文档）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `external_index.md` | 175 | 外部算法库索引（50+算法） |  |
| `hmml_index.md` | 172 | HMML 分层建模知识库 (Hierarchical Mathematical Modeling Library) |  |
| `innovative_index.md` | 250 | 创新算法库索引（2026电工杯助攻资料） |  |
| `quick_reference.md` | 121 | 算法速查卡（按题型） |  |

## templates/（题型模板 .tex/.md）

| 文件 | 行数 | 摘要 | 主要符号 |
|------|-----:|------|---------|
| `template-a.tex` | 349 | ============================================================ |  |
| `template-b.tex` | 355 | ============================================================ |  |
| `template-c.tex` | 324 | ============================================================ |  |
| `template-d.tex` | 333 | ============================================================ |  |
| `template-a.md` | 257 | A 题机理类模板 — 物理方程推导 + 数值求解 |  |
| `template-b.md` | 330 | B 题优化类模板 — 目标函数 + 约束 + 多算法对比 |  |
| `template-c.md` | 271 | C 题评价类模板 — 指标体系 + 权重计算 + 方案排序 |  |
| `template-d.md` | 302 | D 题数据类模板 — 统计分析 + 预测建模 |  |

---

> SKILL.md §六 引用本文件作为唯一文件结构源。