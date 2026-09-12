"""扩展算法回归测试。

覆盖此前仅有"导入冒烟"级别保障的核心算法模块，并把已修复的缺陷
固化为回归测试。这些模块是国赛 B（优化）/ A（机理）/ D（数据）题的
主力工具，此前缺少行为级验证。

重点回归项：
- ``pso_clerc`` / ``pso_tvac`` 的逐维边界支持。这两个函数曾把
  ``lo`` / ``hi`` 强制转为标量，导致传入 ``bounds=[[lo1,hi1],[lo2,hi2]]``
  时直接抛 ``ValueError``，使"为不同量纲变量设置不同取值范围"这一
  常见需求无法实现。
"""

import numpy as np
import pandas as pd
import pytest

from algorithms.mechanistic.fdm_2d import fdm_2d_explicit
from algorithms.mechanistic.fem_poisson import assemble_and_solve, rect_tri_mesh
from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid
from algorithms.optimization.pso_variants import pso_clerc, pso_tvac
from algorithms.prediction.tam import TAM_Forecast
from algorithms.stats.hypothesis import (
    anova_oneway,
    chisq_test,
    ks_test,
    mann_whitney_u,
    paired_t,
)
from algorithms.validation.assumption_error import AssumptionChecker
from algorithms.validation.sensitivity import SensitivityAnalyzer


def _sphere(v):
    """球函数 f(x) = sum(x_i^2)，全局最优 0 位于原点。"""
    return float(sum(x * x for x in v))


# ---------------------------------------------------------------- PSO 变体


class TestPSOVariantBounds:
    """回归保护：逐维边界（per-dimension bounds）。"""

    @pytest.mark.parametrize("solver", [pso_clerc, pso_tvac])
    def test_per_dimension_bounds(self, solver):
        """两维取值范围不同：x∈[0,10] 期望 5，y∈[-1,1] 期望 0。"""
        obj = lambda v: float((v[0] - 5.0) ** 2 + v[1] ** 2)  # noqa: E731
        bounds = [[0.0, 10.0], [-1.0, 1.0]]

        r = solver(obj, dim=2, bounds=bounds, iters=120, swarms=40, seed=42)
        g = np.asarray(r["g_best"], dtype=float)

        assert g.shape == (2,), "最优解维度应为 2"
        assert 0.0 <= g[0] <= 10.0, f"x 越出下界/上界: {g[0]}"
        assert -1.0 <= g[1] <= 1.0, f"y 越出下界/上界: {g[1]}"
        assert r["g_val"] < 0.5, f"未收敛到最优: {r['g_val']}"

    @pytest.mark.parametrize("solver", [pso_clerc, pso_tvac])
    def test_uniform_bounds_still_work(self, solver):
        """回归：统一边界 [lo, hi] 的形式不能被改坏。"""
        r = solver(_sphere, dim=3, bounds=[(-5, 5)], iters=120, swarms=40, seed=1)
        assert r["g_val"] < 1e-2, f"球函数应接近 0，实际 {r['g_val']}"
        assert np.all(np.abs(np.asarray(r["g_best"])) <= 5.0)

    @pytest.mark.parametrize("solver", [pso_clerc, pso_tvac])
    def test_result_structure(self, solver):
        r = solver(_sphere, dim=2, bounds=[(-1, 1)], iters=20, swarms=10, seed=0)
        for key in ("g_best", "g_val", "history", "variant"):
            assert key in r, f"返回值缺少 {key}"
        assert len(r["history"]) == 20, "history 长度应等于迭代次数"

    def test_reproducible_with_seed(self):
        """固定种子应可复现（复现性是国赛评审关注点）。"""
        kw = dict(dim=2, bounds=[(-5, 5)], iters=40, swarms=20, seed=7)
        r1 = pso_clerc(_sphere, **kw)
        r2 = pso_clerc(_sphere, **kw)
        assert r1["g_val"] == pytest.approx(r2["g_val"])


# ---------------------------------------------------------------- 自适应混合优化


class TestAdaptiveHybrid:
    def test_solve_sphere(self):
        ah = AdaptiveHybrid(_sphere, [(-5, 5), (-5, 5)], pop_size=30, max_iter=60, seed=42)
        r = ah.solve()

        assert r["f_opt"] < 1e-2, f"球函数应收敛，实际 {r['f_opt']}"
        assert len(r["x_opt"]) == 2
        assert r["n_eval"] > 0

    def test_history_recorded(self):
        ah = AdaptiveHybrid(_sphere, [(-5, 5)], pop_size=20, max_iter=30, seed=1)
        ah.solve()
        assert len(ah.history) == 30
        assert {"iter", "best", "diversity", "strategy"} <= set(ah.history[0])


# ---------------------------------------------------------------- 二维有限差分


class TestFDM2D:
    def test_shapes(self):
        U, x, y = fdm_2d_explicit(D=0.1, Lx=1.0, Ly=1.0, T=0.1, nx=10, ny=10, nt=100)
        assert U.shape == (11, 11), "nx=ny=10 应产生 11x11 网格"
        assert x.shape == (11,) and y.shape == (11,)

    def test_return_all(self):
        U_list, x, y, t = fdm_2d_explicit(
            D=0.1, Lx=1.0, Ly=1.0, T=0.1, nx=8, ny=8, nt=40, return_all=True
        )
        arr = np.asarray(U_list)
        assert arr.shape[1:] == (9, 9)
        assert arr.shape[0] == t.shape[0], "时间层数与时间轴长度应一致"

    def test_values_finite_and_non_negative(self):
        """显式格式在稳定条件下应保持数值有界（不振荡发散）。"""
        U, _, _ = fdm_2d_explicit(
            D=0.1, Lx=1.0, Ly=1.0, T=0.1, nx=10, ny=10, nt=100,
            u0=lambda x, y: 1.0, bc=0.0,
        )
        assert np.all(np.isfinite(U))
        assert np.all(U >= -1e-9), "扩散方程初值非负时解不应为负"

    def test_dirichlet_bc_applied(self):
        """边界值应被钉在给定常数上。"""
        U, _, _ = fdm_2d_explicit(
            D=0.1, Lx=1.0, Ly=1.0, T=0.05, nx=6, ny=6, nt=50, bc=2.0
        )
        assert np.allclose(U[0, :], 2.0), "下边界应等于 bc"
        assert np.allclose(U[-1, :], 2.0), "上边界应等于 bc"


# ---------------------------------------------------------------- 有限元


class TestFEMPoisson:
    def test_mesh_generation(self):
        nodes, elements = rect_tri_mesh(3, 3)
        assert nodes.ndim == 2 and nodes.shape[1] == 2, "节点应为 Nx2 坐标"
        assert len(elements) > 0, "应生成三角形单元"

    def test_solve_poisson_finite(self):
        mesh = rect_tri_mesh(4, 4)
        u, nodes, elements = assemble_and_solve(mesh, f_func=lambda x, y: 1.0)

        assert u.shape[0] == nodes.shape[0], "解向量长度应等于节点数"
        assert np.all(np.isfinite(u)), "解不应含 NaN/Inf"

    def test_dirichlet_pins_values(self):
        """指定 Dirichlet 边值应被精确满足。"""
        mesh = rect_tri_mesh(3, 3)
        u, nodes, _ = assemble_and_solve(
            mesh, f_func=lambda x, y: 0.0, dirichlet={0: 0.0, 1: 1.0}
        )
        assert u[0] == pytest.approx(0.0)
        assert u[1] == pytest.approx(1.0)


# ---------------------------------------------------------------- 统计检验


class TestHypothesis:
    def test_paired_t_detects_systematic_shift(self):
        rng = np.random.default_rng(0)
        x = rng.normal(1.0, 0.1, 50)
        y = x + 0.5  # 系统性偏移
        r = paired_t(x, y)

        assert r["p_value"] < 0.01, "明显偏移应被检出"
        assert r["conclusion"] is True
        assert 0.0 <= r["p_value"] <= 1.0

    def test_paired_t_result_keys(self):
        r = paired_t([1.0, 2.0, 3.0, 4.0], [1.1, 2.1, 3.1, 4.1])
        assert {"statistic", "p_value", "conclusion", "alpha"} <= set(r)

    def test_mann_whitney_separated_groups(self):
        r = mann_whitney_u([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
        assert r["p_value"] < 0.05, "完全分离的两组应有显著差异"

    def test_chisq_runs(self):
        r = chisq_test([25, 25, 25, 25])
        assert "p_value" in r
        assert 0.0 <= r["p_value"] <= 1.0

    def test_chisq_multiple_runs(self):
        """卡方检验应可重复调用（无残留状态）。"""
        r1 = chisq_test([10, 20, 30])
        r2 = chisq_test([10, 20, 30])
        assert r1["statistic"] == pytest.approx(r2["statistic"])

    def test_anova_oneway(self):
        r = anova_oneway([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert "p_value" in r
        assert 0.0 <= r["p_value"] <= 1.0

    def test_ks_test(self):
        rng = np.random.default_rng(3)
        r = ks_test(rng.normal(0, 1, 100))
        assert "p_value" in r


# ---------------------------------------------------------------- 灵敏度分析


class TestSensitivityAnalyzer:
    def test_single_param_elasticity_is_one(self):
        """单参数线性模型 y = 2a 的弹性系数应为 1
        （弹性系数 = 相对变化率之比，与系数 2 无关）。"""
        model = lambda p: p["a"] * 2.0  # noqa: E731
        sa = SensitivityAnalyzer(model, {"a": 10.0}, perturbations=(0.1,))
        res = sa.analyze()

        assert res[("a", 0.1)]["elasticity"] == pytest.approx(1.0, rel=1e-6)

    def test_multi_param_elasticity_is_share_weighted(self):
        """多参数模型 y = 2a + 3b：弹性系数为该参数对输出的贡献占比。
        y0 = 2*10 + 3*5 = 35，故 a 的弹性 = 20/35，b 的弹性 = 15/35。"""
        model = lambda p: p["a"] * 2.0 + p["b"] * 3.0  # noqa: E731
        sa = SensitivityAnalyzer(model, {"a": 10.0, "b": 5.0}, perturbations=(0.1,))
        res = sa.analyze()

        assert len(res) >= 2, "两个参数都应被分析"
        assert res[("a", 0.1)]["elasticity"] == pytest.approx(20.0 / 35.0, rel=1e-6)
        assert res[("b", 0.1)]["elasticity"] == pytest.approx(15.0 / 35.0, rel=1e-6)

    def test_elasticity_summary_covers_all_params(self):
        model = lambda p: p["a"] * 2.0  # noqa: E731
        sa = SensitivityAnalyzer(model, {"a": 10.0}, perturbations=(0.1, 0.2))
        sa.analyze()
        summary = sa.elasticity_summary()

        assert "a" in summary

    def test_results_are_finite(self):
        model = lambda p: p["x"] ** 2  # noqa: E731
        sa = SensitivityAnalyzer(model, {"x": 3.0}, perturbations=(0.1, 0.2))
        for val in sa.analyze().values():
            assert np.isfinite(val["elasticity"])


# ---------------------------------------------------------------- 假设误差量化


class TestAssumptionChecker:
    def test_analyze_with_delta(self):
        ac = AssumptionChecker(
            base_output=100.0,
            assumptions=[
                {"name": "忽略摩擦", "delta": 0.05, "relaxed_name": "计入摩擦"},
                {"name": "线性化近似", "delta": 0.01, "relaxed_name": "保留非线性"},
            ],
        )
        rep = ac.analyze()

        assert rep["n_assumptions"] == 2
        assert len(rep["details"]) == 2
        # 应按影响从大到小排序
        assert rep["details"][0]["impact_pct"] >= rep["details"][1]["impact_pct"]

    def test_analyze_with_relax_func(self):
        ac = AssumptionChecker(
            base_output=100.0,
            assumptions=[{
                "name": "固定需求",
                "relax_func": lambda: 120.0,
                "relaxed_name": "需求波动",
            }],
        )
        rep = ac.analyze()

        assert rep["details"][0]["impact_pct"] == pytest.approx(20.0, rel=1e-6)

    def test_paper_text_generated(self):
        ac = AssumptionChecker(
            base_output=100.0,
            assumptions=[{"name": "匀速", "delta": 0.03, "relaxed_name": "变速"}],
        )
        text = ac.paper_text()
        assert "匀速" in text
        assert len(text) > 0

    def test_empty_assumptions(self):
        ac = AssumptionChecker(base_output=1.0, assumptions=[])
        assert ac.paper_text() == "(无假设被检查)"


# ---------------------------------------------------------------- TAM 时序预测


class TestTAMForecast:
    @staticmethod
    def _make_series(n=60):
        t = np.arange(n)
        y = 10.0 + 0.5 * t + 3.0 * np.sin(2 * np.pi * t / 12)
        return pd.DataFrame({"t": t, "y": y})

    def test_fit_predict_pipeline(self):
        df = self._make_series()
        tam = TAM_Forecast()
        tam.fit(df, time_col="t", value_col="y")
        pred = tam.predict(steps=6)

        assert pred is not None, "预测结果不应为 None"

    def test_summary_after_fit(self):
        df = self._make_series()
        tam = TAM_Forecast()
        tam.fit(df, time_col="t", value_col="y")
        summary = tam.summary()

        assert summary is not None

    def test_summary_before_fit(self):
        """未拟合时应返回可读提示，而非抛异常。"""
        tam = TAM_Forecast()
        assert tam.summary() == "模型未拟合"
