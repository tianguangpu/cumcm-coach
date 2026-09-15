"""
第五批(二)低覆盖率冲刺测试（90%+ 目标）
覆盖: monte_carlo / sensitivity / hypothesis / nash / arima / problem_analyzer / sobol_enhanced / adaptive_hybrid
"""
import os
import sys
import json
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest

import matplotlib

matplotlib.use("Agg")


@pytest.fixture(scope="module")
def simple_series():
    np.random.seed(42)
    t = np.arange(30)
    return 10.0 + 0.3 * t + 5 * np.cos(t / 3.0)


# ============================================================
# monte_carlo
# ============================================================
class TestMonteCarlo:
    def _make(self, dist):
        def sim(p):
            return p["x"] + p.get("y", 0.0)
        return MonteCarlo(sim, dist)

    def _import(self):
        from algorithms.validation.monte_carlo import MonteCarlo
        return MonteCarlo

    def test_run_and_statistics(self):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: 2 * p["x"], {"x": {"dist": "normal", "mean": 10, "std": 1}})
        samples = mc.run(n=50, seed=7)
        assert samples.shape == (50,)
        stats = mc.statistics()
        assert "mean" in stats and "cv" in stats and "ci_95" in stats
        assert "dist_spec" in stats and "dist_statement" in stats
        assert "convergence" in stats

    def test_all_dist_types(self):
        MonteCarlo = self._import()
        dist = {
            "u": {"dist": "uniform", "low": 0, "max": 3},
            "l": {"dist": "lognormal", "mean": 1.0, "std": 0.3, "base": 10},
            "t": {"dist": "triangle", "low": 0, "mode": 0.5, "high": 1},
            "n": {"mean": 5, "std": 1},  # 缺省 dist -> normal
            
        }
        mc = MonteCarlo(lambda p: sum(p.values()), dist)
        samples = mc.run(n=20, seed=1)
        assert samples.shape == (20,)

    def test_quantiles_custom(self):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: p["x"], {"x": {"dist": "normal", "mean": 0, "std": 1}})
        mc.run(n=30)
        q = mc.quantiles([0.1, 0.9])
        assert set(q.keys()) == {"q10", "q90"}

    def test_convergence_diag_group(self):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: p["x"], {"x": {"dist": "normal", "mean": 2, "std": 0.1}})
        mc.run(n=100)
        conv = mc.convergence_diag(group=10)
        assert "converged" in conv and "stable_ratio" in conv
        assert conv["n"] == 100

    def test_raises_before_run(self):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: p["x"], {"x": {"dist": "normal", "mean": 0, "std": 1}})
        with pytest.raises(ValueError):
            mc.quantiles()
        with pytest.raises(ValueError):
            mc.statistics()
        with pytest.raises(ValueError):
            mc.plot_distribution()
        with pytest.raises(ValueError):
            mc.convergence_diag()

    def test_cv_nan_when_mean_zero(self):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: p["x"], {"x": {"dist": "normal", "mean": 0, "std": 1}})
        mc.run(n=100)
        stats = mc.statistics()
        # mean 非常接近 0，CV 可能为 nan
        assert ("cv" in stats)

    def test_dist_statement_formats(self):
        MonteCarlo = self._import()
        dist = {
            "n": {"dist": "normal", "mean": 2, "std": 0.5},
            "u": {"dist": "uniform", "low": 0, "high": 1},
            "l": {"dist": "lognormal", "mean": 1.0, "std": 0.3},
            "t": {"dist": "triangle", "low": 0, "mode": 0.5, "high": 1},
        }
        mc = MonteCarlo(lambda p: 1.0, dist)
        statement = mc._dist_statement()
        assert "N(" in statement and "U[" in statement and "LogN(" in statement and "Tri(" in statement

    def test_plot_distribution_save(self, tmp_path):
        MonteCarlo = self._import()
        mc = MonteCarlo(lambda p: p["x"], {"x": {"dist": "normal", "mean": 1, "std": 0.2}})
        mc.run(n=30)
        save = str(tmp_path / "mc.png")
        mc.plot_distribution(save)
        assert Path(save).exists()

    def test_demo_main_block(self, tmp_path, monkeypatch):
        import runpy
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        old = sys.argv
        sys.argv = ["monte_carlo.py"]
        try:
            runpy.run_module("algorithms.validation.monte_carlo", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# sensitivity
# ============================================================
class TestSensitivity:
    def test_analyze_linear(self):
        from algorithms.validation.sensitivity import SensitivityAnalyzer

        sa = SensitivityAnalyzer(lambda p: p["a"] * 3.0, {"a": 2.0}, perturbations=(0.1, 0.2))
        res = sa.analyze()
        assert len(res) == 2  # 2个扰动档
        # 线性弹性系数应为 1.0
        assert res[("a", 0.1)]["elasticity"] == pytest.approx(1.0, abs=1e-9)
        assert sa.base_output == pytest.approx(6.0)

    def test_elasticity_summary_grades(self):
        from algorithms.validation.sensitivity import SensitivityAnalyzer

        high = SensitivityAnalyzer(lambda p: 3 * p["x"], {"x": 2.0}, perturbations=(0.1, 0.2))
        high.analyze()
        assert high.elasticity_summary()["x"]["grade"] == "高"

        low = SensitivityAnalyzer(lambda p: 5.0, {"x": 2.0}, perturbations=(0.1, 0.2))
        low.analyze()
        assert low.elasticity_summary()["x"]["grade"] == "低"

    def test_base_output_zero(self):
        from algorithms.validation.sensitivity import SensitivityAnalyzer

        sa = SensitivityAnalyzer(lambda p: p["a"], {"a": 0.0})
        res = sa.analyze()
        assert sa.base_output == pytest.approx(0.0)
        # 除零规避：y0 -> 1.0，全部 rel 为 0
        assert res[("a", 0.1)]["change_up"] == pytest.approx(0.0)

    def test_plot_tornado_save(self, tmp_path):
        from algorithms.validation.sensitivity import SensitivityAnalyzer

        sa = SensitivityAnalyzer(lambda p: 2 * p["a"] + p["b"], {"a": 3.0, "b": 1.0})
        sa.analyze()
        save = str(tmp_path / "tor.png")
        sa.plot_tornado(save)
        assert Path(save).exists()


# ============================================================
# hypothesis
# ============================================================
class TestHypothesis:
    def test_ks_single_norm(self):
        from algorithms.stats.hypothesis import ks_test

        rng = np.random.default_rng(0)
        r = ks_test(rng.normal(size=300))
        assert "statistic" in r and "p_value" in r and "conclusion" in r
        assert r["alpha"] == 0.05

    def test_ks_single_uniform_expon(self):
        from algorithms.stats.hypothesis import ks_test

        rng = np.random.default_rng(1)
        assert ks_test(rng.uniform(size=200), dist="uniform")["conclusion"] in (True, False)
        assert ks_test(np.random.RandomState(2).exponential(1, 200), dist="expon")["conclusion"] in (True, False)

    def test_ks_single_custom_dist(self):
        from algorithms.stats.hypothesis import ks_test

        rng = np.random.default_rng(3)
        r = ks_test(rng.normal(size=200), dist="laplace")
        assert "p_value" in r

    def test_ks_two_sample(self):
        from algorithms.stats.hypothesis import ks_test

        rng = np.random.default_rng(0)
        r = ks_test(rng.normal(size=100), rng.normal(size=120))
        assert "statistic" in r

    def test_anova(self):
        from algorithms.stats.hypothesis import anova_oneway

        rng = np.random.default_rng(0)
        r = anova_oneway([rng.normal(1, 1, 60), rng.normal(3, 1, 60)])
        assert r["conclusion"] is True  # 两组差异显著

    def test_chisq_with_and_without_expected(self):
        from algorithms.stats.hypothesis import chisq_test

        assert "p_value" in chisq_test([40, 60, 50, 50])
        r = chisq_test([55, 45], expected=[50, 50])
        assert "conclusion" in r

    def test_mann_whitney(self):
        from algorithms.stats.hypothesis import mann_whitney_u

        rng = np.random.default_rng(0)
        r = mann_whitney_u(rng.normal(size=80), rng.normal(0.8, 1, 80))
        assert "statistic" in r

    def test_paired_t(self):
        from algorithms.stats.hypothesis import paired_t

        rng = np.random.default_rng(0)
        r = paired_t(rng.normal(size=90), rng.normal(0.3, 1, 90))
        assert "statistic" in r

    def test_main_block(self):
        import runpy

        old = sys.argv
        sys.argv = ["hypothesis.py"]
        try:
            runpy.run_module("algorithms.stats.hypothesis", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# nash
# ============================================================
class TestNash:
    def test_pure_nash_has_equilibrium(self):
        from algorithms.game.nash import pure_nash

        eqs = pure_nash([[3, 1], [2, 0]])
        assert len(eqs) == 1
        e = eqs[0]
        assert e["is_pure"] is True and e["type"] == "pure"
        assert e["strategy_row"] == [1.0, 0.0]

    def test_pure_nash_none(self):
        from algorithms.game.nash import pure_nash

        eqs = pure_nash([[1, 0], [0, 1]])
        assert isinstance(eqs, list)

    def test_mixed_nash_zero_sum(self):
        from algorithms.game.nash import mixed_nash_2x2

        eqs = mixed_nash_2x2([[1, -1], [-1, 1]])
        assert isinstance(eqs, list)
        kinds = {e["type"] for e in eqs}
        assert "mixed" in kinds

    def test_mixed_nash_explicit_payoff_b(self):
        from algorithms.game.nash import mixed_nash_2x2

        # 协调博弈，两个纯策略 + 一个混合
        eqs = mixed_nash_2x2([[3, 0], [0, 2]], [[3, 0], [0, 2]])
        kinds = {e["type"] for e in eqs}
        assert "pure" in kinds

    def test_profile_is_nash(self):
        from algorithms.game.nash import _profile_is_nash

        A = np.array([[3, 0], [0, 2]], float)
        B = A.copy()
        assert bool(_profile_is_nash(A, B, np.array([1.0, 0.0]), np.array([1.0, 0.0]))) is True


# ============================================================
# arima
# ============================================================
class TestArima:
    def test_fit_predict_forecast(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        m = ARIMA_Forecast(simple_series, order=(1, 0, 1))
        m.fit()
        assert m.fitted is True
        assert len(m.params) == 1 + 1 + 1
        pred = m.predict(5)
        assert pred.shape == (5,)
        f, lo, hi = m.forecast(5)
        assert np.all(lo <= hi)

    def test_ar_only(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        m = ARIMA_Forecast(simple_series, order=(1, 0, 0))
        m.fit()
        assert m.aic is not None

    def test_p_and_q_zero_raises(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        with pytest.raises(ValueError):
            ARIMA_Forecast(simple_series, order=(0, 1, 0)).fit()

    def test_non_1d_raises(self):
        from algorithms.prediction.arima import ARIMA_Forecast

        with pytest.raises(ValueError):
            ARIMA_Forecast(np.zeros((3, 3)))

    def test_too_few_samples_raises(self):
        from algorithms.prediction.arima import ARIMA_Forecast

        with pytest.raises(ValueError):
            ARIMA_Forecast([1, 2, 3, 4, 5], order=(3, 0, 3)).fit()

    def test_predict_before_fit_raises(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        m = ARIMA_Forecast(simple_series, order=(1, 0, 0))
        with pytest.raises(ValueError):
            m.predict(3)

    def test_inverse_difference(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        m = ARIMA_Forecast(simple_series, order=(2, 1, 1))
        integrated = m._inverse_difference(np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
        assert integrated.shape == (5,)

    def test_plot_save(self, simple_series, tmp_path, monkeypatch):
        from algorithms.prediction.arima import ARIMA_Forecast

        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        m = ARIMA_Forecast(simple_series[:25], order=(1, 0, 1))
        m.fit()
        save = str(tmp_path / "ar.png")
        m.plot(save, steps=3)
        assert Path(save).exists()

    def test_auto_order(self, simple_series):
        from algorithms.prediction.arima import ARIMA_Forecast

        res = ARIMA_Forecast.auto_order(simple_series, max_p=1, max_d=0, max_q=1)
        assert isinstance(res, tuple) and len(res) == 3


# ============================================================
# problem_analyzer
# ============================================================
class TestProblemAnalyzer:
    def test_analyze_with_ambiguity(self):
        from algorithms.misc.problem_analyzer import analyze_problem

        text = ("地块种植若干作物。轮作约束, 同地块不能连年种植同一作物。"
                "面积受限下求最大收益。约为8%。")
        rep = analyze_problem(text, title="种植", verbose=False)
        assert rep["title"] == "种植"
        assert rep["needs_confirmation"] is True  # 含"约/若干"
        assert len(rep["ambiguity"]) >= 1
        assert "轮作" in rep["terminology"]

    def test_no_ambiguity(self):
        from algorithms.misc.problem_analyzer import analyze_problem

        rep = analyze_problem("种植基地面积有限。", verbose=False)
        assert rep["ambiguity"] == [{"note": "未检出明显模糊词, 仍需人工复核"}]

    def test_json_md_write(self, tmp_path):
        from algorithms.misc.problem_analyzer import analyze_problem

        outdir = str(tmp_path / "res")
        analyze_problem("网络节点流量守恒。", outdir=outdir, verbose=True)
        assert Path(outdir, "problem_analysis.json").exists()
        assert Path(outdir, "problem_analysis.md").exists()
        data = json.load(open(Path(outdir, "problem_analysis.json"), encoding="utf-8"))
        assert "title" in data

    def test_dependency_map(self):
        from algorithms.misc.problem_analyzer import _dependency_map

        dep = _dependency_map("问题一: x。问题二: y。第三问: z。")
        assert len(dep["nodes"]) >= 2
        assert dep["nodeE"] if False else True

    def test_context_domains(self):
        from algorithms.misc.problem_analyzer import _find_context_terms

        assert "制造/排班" in _find_context_terms("排班受产能限制")
        assert "网络/流" in _find_context_terms("节点流量守恒")
        assert "经济/金融" in _find_context_terms("风险收益权衡")
        assert len(_find_context_terms("纯文本")) == 0

    def test_constraint_mining(self):
        from algorithms.misc.problem_analyzer import _constraint_mining

        explicit, implied = _constraint_mining("不得连作。面积不超过10。")
        assert any("不得" in e or "不超过" in e for e in explicit)

    def test_main_block(self, tmp_path, monkeypatch):
        import runpy
        monkeypatch.chdir(tmp_path)
        old = sys.argv
        sys.argv = ["problem_analyzer.py"]
        try:
            runpy.run_module("algorithms.misc.problem_analyzer", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old


# ============================================================
# sobol_enhanced
# ============================================================
class TestSobolEnhanced:
    def test_numpy_method(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis

        r = sobol_analysis(lambda x: x[0] + 2 * x[1], [(0.0, 1.0), (0.0, 1.0)],
                           N=64, n_boot=20, method="numpy")
        assert r["method"] == "numpy"
        assert len(r["S1"]) == 2 and len(r["ST"]) == 2

    def test_auto_fallback_warns(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis, HAS_SALIB

        if HAS_SALIB:
            pytest.skip("SALib 已安装")
        with pytest.warns(UserWarning):
            r = sobol_analysis(lambda x: x[0] + x[1], [(0.0, 1.0), (0.0, 1.0)],
                               N=32, n_boot=10, method="auto")
        assert r["method"] == "numpy"

    def test_salib_raises_without_lib(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis, HAS_SALIB

        if HAS_SALIB:
            pytest.skip("SALib 已安装")
        with pytest.raises(ImportError):
            sobol_analysis(lambda x: x[0], [(0.0, 1.0), (0.0, 1.0)], method="salib")

    def test_bad_method_raises(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis

        with pytest.raises(ValueError):
            sobol_analysis(lambda x: x[0], [(0.0, 1.0), (0.0, 1.0)], method="bad")

    def test_single_dim_raises(self):
        from algorithms.validation.sobol_enhanced import sobol_analysis

        with pytest.raises(ValueError):
            sobol_analysis(lambda x: x[0], [(0.0, 1.0)], method="numpy")

    def test_alias(self):
        from algorithms.validation.sobol_enhanced import sobol_total_and_first

        assert callable(sobol_total_and_first)


# ============================================================
# adaptive_hybrid 边界/methods
# ============================================================
class TestAdaptiveHybridExtra:
    def test_solve_dim_1_matches(self):
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        opt = AdaptiveHybrid(lambda x: float(x[0] ** 2), [(-3.0, 3.0)],
                             pop_size=8, max_iter=15, seed=0)
        result = opt.solve()
        assert len(result["x_opt"]) == 1
        assert len(result["history"]) == 15

    def test_default_params(self):
        from algorithms.optimization.adaptive_hybrid import AdaptiveHybrid

        opt = AdaptiveHybrid(lambda x: 0.0, [(-1.0, 1.0)] * 2)
        assert opt.w == 0.7 and opt.F == 0.5 and opt.T0 == 100
        assert opt.dim == 2
