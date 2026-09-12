"""cumcm-coach 算法库。

按建模任务分层组织,子包与题型细类的对应关系见 ``hmml_index.md``:

- :mod:`algorithms.optimization`  OPT 连续/组合优化(SA-PSO / GA / DE / AHO / PSO 变体)
- :mod:`algorithms.prediction`    PRE 时序与回归(TAM / ARIMA / MLP / GM(1,1))
- :mod:`algorithms.evaluation`    EVA 综合评价(AHP+熵权+TOPSIS / VIKOR / GRA)
- :mod:`algorithms.network`       GRA 图论与网络(Dijkstra / Kruskal / 最大流)
- :mod:`algorithms.mechanistic`   PDE/PHY 机理数值解(FDM 1D/2D / FEM / ODE)
- :mod:`algorithms.stats`         STA 统计检验(t / ANOVA / 卡方 / 非参数)
- :mod:`algorithms.game`          GAM 博弈(纯策略与混合策略纳什均衡)
- :mod:`algorithms.ecology`       ECO 生态与传染病(Lotka-Volterra / SIR / SEIR)
- :mod:`algorithms.validation`    VAL 验证(Sobol 灵敏度 / 假设误差量化 / 蒙特卡洛)
- :mod:`algorithms.misc`          MIS 元工具(问题分析 / 创新引导)

所有算法模块均可直接 ``import`` 使用,不依赖 MCP 服务;MCP 仅作为可选增强,
未连接时自动降级到内置实现。
"""

__version__ = "7.11.0"
