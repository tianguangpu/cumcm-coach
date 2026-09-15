"""第九批：shap_analysis fit + 全 plot 方法 + generate_report"""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest
import matplotlib
matplotlib.use("Agg")


@pytest.fixture(scope="module")
def shap_data():
    np.random.seed(42)
    X = np.random.randn(60, 4)
    y = 3 * X[:, 0] - 2 * X[:, 1] + 0.5 * X[:, 2] + np.random.randn(60) * 0.1
    return X, y


@pytest.fixture(scope="module")
def fitted_tree_analyzer(shap_data):
    from sklearn.ensemble import RandomForestRegressor
    from algorithms.validation.shap_analysis import SHAPAnalyzer

    X, y = shap_data
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X[:50], y[:50])
    a = SHAPAnalyzer(model, X_train=X[:50], X_test=X[50:],
                     feature_names=["温度", "压力", "流量", "浓度"])
    a.fit()
    return a


class TestShapFit:
    def test_fit_tree_model(self, shap_data):
        from sklearn.ensemble import RandomForestRegressor
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        X, y = shap_data
        model = RandomForestRegressor(n_estimators=30, random_state=42)
        model.fit(X[:50], y[:50])
        a = SHAPAnalyzer(model, X_train=X[:50], X_test=X[50:],
                         feature_names=["A", "B", "C", "D"],
                         model_type="tree")
        a.fit()
        assert a.fitted is True
        assert a.shap_values is not None
        assert a.shap_values.shape[0] == 10  # X_test 10 samples

    def test_fit_auto_detect_tree(self, shap_data):
        from sklearn.ensemble import GradientBoostingRegressor
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        X, y = shap_data
        model = GradientBoostingRegressor(n_estimators=20, random_state=42)
        model.fit(X[:50], y[:50])
        a = SHAPAnalyzer(model, X_train=X[:50], X_test=X[50:], model_type="auto")
        a.fit()
        assert a.model_type == "tree"

    def test_fit_linear_model(self, shap_data):
        from sklearn.linear_model import LinearRegression
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        X, y = shap_data
        model = LinearRegression()
        model.fit(X[:50], y[:50])
        a = SHAPAnalyzer(model, X_train=X[:50], X_test=X[50:], model_type="linear")
        a.fit()
        assert a.fitted is True

    def test_fit_kernel_model(self, shap_data):
        """KernelExplainer 路径（慢但通用）"""
        from sklearn.svm import SVR
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        X, y = shap_data
        model = SVR()
        model.fit(X[:50], y[:50])
        a = SHAPAnalyzer(model, X_train=X[:10], X_test=X[50:52],
                         model_type="kernel")
        a.fit()
        assert a.fitted is True

    def test_fit_multiclass_list_shap_values(self):
        """多分类 shap_values 返回 list 时取 [1]"""
        from sklearn.ensemble import RandomForestClassifier
        from algorithms.validation.shap_analysis import SHAPAnalyzer, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        np.random.seed(42)
        X = np.random.randn(60, 4)
        y = np.array([0] * 20 + [1] * 20 + [2] * 20)
        model = RandomForestClassifier(n_estimators=20, random_state=42)
        model.fit(X[:50], y[:50])
        a = SHAPAnalyzer(model, X_train=X[:50], X_test=X[50:55],
                         model_type="tree")
        a.fit()
        assert a.shap_values is not None
        # shap_values 可能是 list（多分类），应取 [1]
        assert not isinstance(a.shap_values, list) or len(a.shap_values) == 1


class TestShapPlots:
    def test_plot_summary_save(self, fitted_tree_analyzer, tmp_path):
        from algorithms.validation.shap_analysis import HAS_MPL
        if not HAS_MPL:
            pytest.skip("matplotlib 未安装")

        save = str(tmp_path / "shap_summary.png")
        fitted_tree_analyzer.plot_summary(save)
        assert Path(save).exists()
        assert Path(save.replace(".png", ".pdf")).exists()

    def test_plot_waterfall_save(self, fitted_tree_analyzer, tmp_path):
        save = str(tmp_path / "shap_waterfall.png")
        fitted_tree_analyzer.plot_waterfall(sample_idx=0, save_path=save)
        assert Path(save).exists()

    def test_plot_bar_save(self, fitted_tree_analyzer, tmp_path):
        save = str(tmp_path / "shap_bar.png")
        fitted_tree_analyzer.plot_bar(save)
        assert Path(save).exists()

    def test_plot_top_features_save(self, fitted_tree_analyzer, tmp_path):
        save = str(tmp_path / "shap_top.png")
        fitted_tree_analyzer.plot_top_features(save, top_n=4)
        assert Path(save).exists()

    def test_plot_dependence_save(self, fitted_tree_analyzer, tmp_path):
        save = str(tmp_path / "shap_dep.png")
        fitted_tree_analyzer.plot_dependence("温度", save_path=save)
        assert Path(save).exists()

    def test_plot_dependence_auto_interaction(self, fitted_tree_analyzer, tmp_path):
        save = str(tmp_path / "shap_dep_auto.png")
        fitted_tree_analyzer.plot_dependence("温度", interaction_feature="auto",
                                             save_path=save)
        assert Path(save).exists()

    def test_plot_summary_no_save(self, fitted_tree_analyzer):
        """无 save_path, 不崩"""
        fitted_tree_analyzer.plot_summary()

    def test_plot_top_features_no_save(self, fitted_tree_analyzer):
        fitted_tree_analyzer.plot_top_features()


class TestShapReport:
    def test_get_feature_importance(self, fitted_tree_analyzer):
        df = fitted_tree_analyzer.get_feature_importance()
        assert "feature" in df.columns and "importance" in df.columns
        assert len(df) == 4  # 4 features
        assert df["importance"].iloc[0] >= df["importance"].iloc[-1]

    def test_generate_report(self, fitted_tree_analyzer):
        report = fitted_tree_analyzer.generate_report()
        assert "SHAP 可解释性分析报告" in report
        assert "Top-5" in report
        assert "SHAP 值统计" in report
        assert "图表清单" in report


class TestShapMainBlock:
    def test_main_block(self, tmp_path, monkeypatch):
        from algorithms.validation.shap_analysis import HAS_SHAP
        if not HAS_SHAP:
            pytest.skip("shap 未安装")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr("matplotlib.pyplot.show", lambda: None)
        import runpy
        old = sys.argv
        sys.argv = ["shap_analysis.py"]
        try:
            runpy.run_module("algorithms.validation.shap_analysis", run_name="__main__")
        except SystemExit:
            pass
        finally:
            sys.argv = old