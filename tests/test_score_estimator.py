"""score_estimator.py 的单元测试。

覆盖分位锚定自评的计算正确性、边界与错误处理。
"""

import pytest

from scripts.score_estimator import (
    BASE_WEIGHTS,
    DIMENSIONS,
    TIERS,
    TYPING_WEIGHTS,
    estimate,
    parse_scores,
)


class TestParseScores:
    def test_parses_valid_input(self):
        s = parse_scores("model=85,verify=90")
        assert s == {"model": 85.0, "verify": 90.0}

    def test_tolerates_spaces(self):
        s = parse_scores(" model = 85 , verify = 90 ")
        assert s == {"model": 85.0, "verify": 90.0}

    def test_rejects_unknown_dimension(self):
        with pytest.raises(ValueError, match="未知维度"):
            parse_scores("nonexistent=80")

    def test_rejects_missing_equals(self):
        with pytest.raises(ValueError, match="格式应为"):
            parse_scores("model")

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="应为数字"):
            parse_scores("model=abc")

    @pytest.mark.parametrize("bad", ["model=-1", "model=101"])
    def test_rejects_out_of_range(self, bad):
        with pytest.raises(ValueError, match="0-100"):
            parse_scores(bad)


class TestEstimate:
    def _full(self, score):
        return dict.fromkeys(DIMENSIONS, float(score))

    def test_all_hundred_gives_hundred(self):
        r = estimate(self._full(100), "B")
        assert r["total"] == pytest.approx(100.0)
        assert r["tier"] == "国一"

    def test_all_zero_gives_zero(self):
        r = estimate(self._full(0), "B")
        assert r["total"] == pytest.approx(0.0)
        assert r["tier"] == "未达省一"

    def test_uniform_score_is_weight_invariant(self):
        """各维度同分时，无论权重如何，总分都应等于该分。"""
        for ptype in TYPING_WEIGHTS:
            r = estimate(self._full(80), ptype)
            assert r["total"] == pytest.approx(80.0), f"题型 {ptype} 不满足权重不变性"

    def test_missing_dimensions_count_as_zero(self):
        r = estimate({"model": 100}, "B")
        assert r["total"] < 100
        assert r["missing"], "应报告缺失维度"

    def test_tier_boundaries(self):
        """档位判定应与 TIERS 定义一致。"""
        for name, line in TIERS:
            r = estimate(self._full(line), "B")
            assert r["tier"] == name, f"{line} 分应判定为 {name}"

    def test_gap_to_first_positive_below_line(self):
        r = estimate(self._full(70), "B")
        assert r["gap_to_first"] > 0

    def test_typing_weights_change_result(self):
        """同一组分数在不同题型下应产生不同总分（权重确实生效）。"""
        scores = {"model": 100, "verify": 60, "algo": 60,
                  "innovation": 60, "format": 60, "compliance": 60}
        a_total = estimate(scores, "A")["total"]
        b_total = estimate(scores, "B")["total"]
        assert a_total != b_total, "A 题重模型、B 题重算法，总分不应相同"

    def test_weak_items_sorted_by_improvement(self):
        scores = {"model": 50, "verify": 50, "algo": 50,
                  "innovation": 90, "format": 90, "compliance": 90}
        r = estimate(scores, "B")
        contribs = [w["contrib"] for w in r["weak"]]
        assert contribs == sorted(contribs, reverse=True), "短板应按提升收益降序"
        assert all(w["score"] < 80 for w in r["weak"]), "短板应只含低于阈值项"


class TestWeightsConfig:
    def test_every_typing_covers_all_dimensions(self):
        for ptype, tw in TYPING_WEIGHTS.items():
            assert set(tw) == set(DIMENSIONS), f"题型 {ptype} 的权重键与维度不一致"

    def test_base_weights_sum_to_one(self):
        assert sum(BASE_WEIGHTS.values()) == pytest.approx(1.0)
