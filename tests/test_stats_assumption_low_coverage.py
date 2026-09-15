"""algorithms/stats + validation/assumption_error 补测。"""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("MPLBACKEND", "Agg")

from algorithms.stats.hypothesis import ks_test, anova_oneway, chisq_test, mann_whitney_u, paired_t, _frozen_dist
from algorithms.validation.assumption_error import AssumptionChecker, _grade, _judge, _overall_judge


# ============================================================
# hypothesis.py —— 覆盖 70% → 目标 95%+
# ============================================================

class TestHypothesis:
    @pytest.fixture
    def rng(self):
        return np.random.default_rng(42)

    def test_ks_one_sample_normal(self, rng):
        x = rng.normal(0, 1, 500)
        r = ks_test(x)
        assert {"statistic", "p_value", "conclusion", "alpha"} <= set(r.keys())
        assert r["alpha"] == 0.05

    def test_ks_two_sample(self, rng):
        x = rng.normal(0, 1, 100)
        y = rng.normal(0.5, 1, 100)
        r = ks_test(x, y)
        assert r["conclusion"] is True  # 均值不同应拒绝

    def test_ks_uniform(self, rng):
        x = rng.uniform(0, 1, 500)
        r = ks_test(x, dist="uniform")
        assert isinstance(r["p_value"], float)

    def test_ks_expon(self, rng):
        x = rng.exponential(1, 500)
        r = ks_test(x, dist="expon")
        assert isinstance(r["p_value"], float)

    def test_frozen_dist_norm(self, rng):
        x = rng.normal(5, 2, 100)
        d = _frozen_dist("norm", x)
        assert hasattr(d, "cdf")

    def test_frozen_dist_fallback(self):
        d = _frozen_dist("cauchy", np.array([1, 2, 3]))
        assert hasattr(d, "cdf")

    def test_anova_significant(self, rng):
        g1 = rng.normal(1, 1, 60)
        g2 = rng.normal(3, 1, 60)
        r = anova_oneway([g1, g2])
        assert r["conclusion"] is True

    def test_anova_not_significant(self, rng):
        g1 = rng.normal(5, 1, 60)
        g2 = rng.normal(5, 1, 60)
        r = anova_oneway([g1, g2])
        assert r["conclusion"] is False

    def test_chisq_default_expected(self):
        r = chisq_test([40, 60, 50, 50])
        assert "statistic" in r and "p_value" in r

    def test_chisq_custom_expected(self):
        r = chisq_test([40, 60], expected=[50, 50])
        assert isinstance(r["statistic"], float)

    def test_mann_whitney(self, rng):
        x = rng.normal(0, 1, 80)
        y = rng.normal(1, 1, 80)
        r = mann_whitney_u(x, y)
        assert r["conclusion"] is True

    def test_paired_t_significant(self, rng):
        x = rng.normal(0, 1, 90)
        y = x + 0.5 + rng.normal(0, 0.1, 90)
        r = paired_t(x, y)
        assert r["conclusion"] is True

    def test_paired_t_not_significant(self, rng):
        x = rng.normal(5, 1, 90)
        y = rng.normal(5, 1, 90)
        r = paired_t(x, y)
        assert r["conclusion"] is False

    def test_summary_alpha(self, rng):
        r = ks_test(rng.normal(0, 1, 100))
        assert r["alpha"] == 0.05


# ============================================================
# assumption_error.py —— 覆盖 0% → 目标 90%+
# ============================================================

class TestAssumptionChecker:
    def test_init(self):
        c = AssumptionChecker(100.0, [])
        assert c.base == 100.0
        assert c.results == []

    def test_measure_delta(self):
        c = AssumptionChecker(100.0, [{"name": "A", "delta": 0.06}])
        r = c._measure(c.assumptions[0])
        assert r["rel_change"] == 0.06
        assert r["impact_pct"] == 6.0
        assert r["grade"] == "轻微"

    def test_measure_delta_negligible(self):
        c = AssumptionChecker(100.0, [{"name": "A", "delta": 0.05}])
        r = c._measure(c.assumptions[0])
        assert r["grade"] == "可忽略"

    def test_measure_relax_func(self):
        c = AssumptionChecker(100.0, [{"name": "A", "relax_func": lambda: 90.0}])
        r = c._measure(c.assumptions[0])
        assert r["rel_change"] == pytest.approx(-0.10)
        assert r["impact_pct"] == 10.0

    def test_measure_relax_func_zero_base(self):
        c = AssumptionChecker(0.0, [{"name": "A", "relax_func": lambda: 5.0}])
        r = c._measure(c.assumptions[0])
        assert r["rel_change"] == 5.0  # base=0 时返回绝对值

    def test_measure_no_delta_no_func_raises(self):
        c = AssumptionChecker(100.0, [{"name": "A"}])
        with pytest.raises(ValueError, match="需提供 delta 或 relax_func"):
            c._measure(c.assumptions[0])

    def test_analyze_sorts_by_impact(self):
        c = AssumptionChecker(100.0, [
            {"name": "small", "delta": 0.01},
            {"name": "large", "delta": 0.20},
            {"name": "medium", "delta": 0.08},
        ])
        rep = c.analyze()
        assert rep["details"][0]["name"] == "large"
        assert rep["details"][1]["name"] == "medium"
        assert rep["n_assumptions"] == 3

    def test_analyze_fatal_count(self):
        c = AssumptionChecker(100.0, [{"name": "fatal", "delta": 0.25}])
        rep = c.analyze()
        assert rep["n_fatal"] == 1
        assert rep["details"][0]["grade"] == "致命"

    def test_analyze_significant_count(self):
        c = AssumptionChecker(100.0, [{"name": "sig", "delta": 0.15}])
        rep = c.analyze()
        assert rep["n_significant"] == 1
        assert rep["details"][0]["grade"] == "显著"

    def test_analyze_max_impact(self):
        c = AssumptionChecker(100.0, [{"name": "A", "delta": 0.10}])
        rep = c.analyze()
        assert rep["max_impact_pct"] == 10.0

    def test_analyze_total_impact(self):
        c = AssumptionChecker(100.0, [{"name": "A", "delta": 0.05}, {"name": "B", "delta": 0.03}])
        rep = c.analyze()
        assert rep["total_impact_pct"] == 8.0

    def test_paper_text(self):
        c = AssumptionChecker(100.0, [{"name": "A", "delta": 0.05, "relaxed_name": "B"}])
        text = c.paper_text()
        assert "假设" in text and "稳健" in text

    def test_paper_text_empty(self):
        c = AssumptionChecker(100.0, [])
        assert c.paper_text() == "(无假设被检查)"

    def test_grade_thresholds(self):
        assert _grade(25) == "致命"
        assert _grade(15) == "显著"
        assert _grade(7) == "轻微"
        assert _grade(2) == "可忽略"

    def test_judge_thresholds(self):
        assert "决定性影响" in _judge("x", 0.25)
        assert "影响显著" in _judge("x", 0.15)
        assert "不敏感" in _judge("x", 0.03)

    def test_overall_judge_fatal(self):
        rep = {"n_fatal": 1, "n_significant": 0}
        assert "致命" in _overall_judge(rep)

    def test_overall_judge_significant(self):
        rep = {"n_fatal": 0, "n_significant": 1}
        assert "显著" in _overall_judge(rep)

    def test_overall_judge_robust(self):
        rep = {"n_fatal": 0, "n_significant": 0}
        assert "可信" in _overall_judge(rep)