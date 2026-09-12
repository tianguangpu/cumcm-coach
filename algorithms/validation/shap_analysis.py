"""
SHAP 可解释性分析 — 模型特征重要性解释
生成 summary/waterfall/dependence 三类图,论文 §6 可解释性章节必备。

用法:
    from shap_analysis import SHAPAnalyzer
    analyzer = SHAPAnalyzer(model, X_train, feature_names=cols)
    analyzer.fit()
    analyzer.plot_summary("figures/png/fig_shap_summary.png")
    analyzer.plot_waterfall(sample_idx=0, save_path="figures/png/fig_shap_waterfall.png")
    analyzer.plot_top_features("figures/png/fig_shap_top_features.png")
    report = analyzer.generate_report()
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    warnings.warn("shap 未安装。安装: pip install shap")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class SHAPAnalyzer:
    """
    SHAP 可解释性分析器。

    Parameters
    ----------
    model : object
        训练好的模型(支持 sklearn/xgboost/lightgbm/pytorch 等)
    X_train : array-like
        训练数据特征矩阵
    X_test : array-like, optional
        测试数据(用于计算 SHAP 值)
    feature_names : list, optional
        特征名称
    model_type : str
        "tree" (XGBoost/LightGBM/RandomForest) | "linear" | "deep" (神经网络) | "auto"
    """

    def __init__(self, model, X_train, X_test=None, feature_names=None, model_type="auto"):
        self.model = model
        self.X_train = np.array(X_train)
        self.X_test = np.array(X_test) if X_test is not None else self.X_train[:100]
        self.feature_names = feature_names or [f"X{i}" for i in range(self.X_train.shape[1])]
        self.model_type = model_type
        self.explainer = None
        self.shap_values = None
        self.fitted = False

    def fit(self):
        """计算 SHAP 值"""
        if not HAS_SHAP:
            raise RuntimeError("请安装 shap: pip install shap")

        if self.model_type == "auto":
            self.model_type = self._detect_model_type()

        if self.model_type == "tree":
            self.explainer = shap.TreeExplainer(self.model)
        elif self.model_type == "linear":
            self.explainer = shap.LinearExplainer(self.model, self.X_train)
        elif self.model_type == "deep":
            self.explainer = shap.DeepExplainer(self.model, self.X_train)
        else:
            # Model-agnostic: KernelExplainer (慢但通用)
            background = shap.kmeans(self.X_train, min(100, len(self.X_train)))
            self.explainer = shap.KernelExplainer(self.model.predict, background)

        self.shap_values = self.explainer.shap_values(self.X_test)

        # 处理多分类返回列表的情况
        if isinstance(self.shap_values, list):
            self.shap_values = self.shap_values[1]  # 取正类

        self.fitted = True
        return self

    def _detect_model_type(self):
        """自动检测模型类型"""
        model_class = type(self.model).__name__.lower()
        if any(x in model_class for x in ["xgb", "lgbm", "randomforest", "gradientboosting", "decisiontree"]):
            return "tree"
        elif any(x in model_class for x in ["linear", "ridge", "lasso", "elasticnet", "sgd"]):
            return "linear"
        elif any(x in model_class for x in ["sequential", "module", "net"]):
            return "deep"
        else:
            return "kernel"

    def get_feature_importance(self):
        """获取特征重要性排序"""
        if not self.fitted:
            raise RuntimeError("请先调用 fit()")

        importance = np.abs(self.shap_values).mean(axis=0)
        df = pd.DataFrame({
            "feature": self.feature_names,
            "importance": importance
        }).sort_values("importance", ascending=False)
        return df

    def plot_summary(self, save_path=None, max_display=20):
        """
        SHAP Summary Plot (蜂群图) — 全局特征重要性+方向
        论文中展示:哪些特征最重要?正向还是负向影响?
        """
        if not self.fitted or not HAS_MPL:
            return

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            self.shap_values,
            self.X_test,
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] SHAP Summary 图已保存: {save_path}")
        plt.close()

    def plot_waterfall(self, sample_idx=0, save_path=None, max_display=15):
        """
        SHAP Waterfall Plot — 单个样本的特征贡献分解
        论文中展示:这个预测为什么是这个值?每个特征贡献多少?
        """
        if not self.fitted or not HAS_MPL:
            return

        plt.figure(figsize=(10, 6))
        explanation = shap.Explanation(
            values=self.shap_values[sample_idx],
            base_values=self.explainer.expected_value,
            data=self.X_test[sample_idx],
            feature_names=self.feature_names
        )
        shap.plots.waterfall(explanation, max_display=max_display, show=False)
        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] SHAP Waterfall 图已保存: {save_path}")
        plt.close()

    def plot_bar(self, save_path=None, max_display=15):
        """
        SHAP Bar Plot — 全局特征重要性排名(简化版)
        论文中展示:特征重要性排序柱状图
        """
        if not self.fitted or not HAS_MPL:
            return

        plt.figure(figsize=(10, 6))
        explanation = shap.Explanation(
            values=self.shap_values,
            base_values=self.explainer.expected_value,
            data=self.X_test,
            feature_names=self.feature_names
        )
        shap.plots.bar(explanation, max_display=max_display, show=False)
        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] SHAP Bar 图已保存: {save_path}")
        plt.close()

    def plot_dependence(self, feature_name, interaction_feature="auto", save_path=None):
        """
        SHAP Dependence Plot — 特征与 SHAP 值的关系
        论文中展示:特征值变化如何影响预测?
        """
        if not self.fitted or not HAS_MPL:
            return

        plt.figure(figsize=(10, 6))
        feature_idx = self.feature_names.index(feature_name) if feature_name in self.feature_names else 0
        shap.dependence_plot(
            feature_idx,
            self.shap_values,
            self.X_test,
            feature_names=self.feature_names,
            interaction_index=interaction_feature,
            show=False
        )
        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] SHAP Dependence 图已保存: {save_path}")
        plt.close()

    def plot_top_features(self, save_path=None, top_n=10):
        """
        Top-N 特征重要性水平条形图(最常用的论文图)
        """
        if not self.fitted or not HAS_MPL:
            return

        importance_df = self.get_feature_importance().head(top_n)

        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.barh(
            range(len(importance_df)),
            importance_df["importance"].values,
            color="#2196F3",
            edgecolor="white",
            height=0.6
        )
        ax.set_yticks(range(len(importance_df)))
        ax.set_yticklabels(importance_df["feature"].values, fontsize=10)
        ax.set_xlabel("Mean |SHAP Value|", fontsize=11)
        ax.set_title(f"Top-{top_n} Feature Importance (SHAP)", fontsize=12, fontweight="bold")
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # 添加数值标签
        for bar, val in zip(bars, importance_df["importance"].values):
            ax.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height()/2,
                   f"{val:.4f}", va="center", fontsize=9)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] Top Features 图已保存: {save_path}")
        plt.close()

    def generate_report(self):
        """生成可解释性分析报告(Markdown)"""
        if not self.fitted:
            raise RuntimeError("请先调用 fit()")

        importance_df = self.get_feature_importance()
        top5 = importance_df.head(5)

        lines = [
            "# SHAP 可解释性分析报告",
            "",
            f"## 模型类型: {self.model_type}",
            f"## 样本数: {len(self.X_test)}",
            f"## 特征数: {len(self.feature_names)}",
            "",
            "## Top-5 特征重要性",
            "",
            "| 排名 | 特征 | 平均 |SHAP值| |",
            "|------|------|----------------|",
        ]

        for i, row in top5.iterrows():
            lines.append(f"| {len(lines)-6} | {row['feature']} | {row['importance']:.4f} |")

        lines.extend([
            "",
            "## SHAP 值统计",
            "",
            f"- 均值: {np.abs(self.shap_values).mean():.4f}",
            f"- 标准差: {np.abs(self.shap_values).std():.4f}",
            f"- 最大值: {np.abs(self.shap_values).max():.4f}",
            "",
            "## 图表清单",
            "",
            "- fig_shap_summary.png: 全局特征重要性蜂群图",
            "- fig_shap_waterfall.png: 单样本特征贡献瀑布图",
            "- fig_shap_top_features.png: Top-N 特征重要性条形图",
            "- fig_shap_dependence_*.png: 特征依赖图",
        ])

        return "\n".join(lines)


if __name__ == "__main__":
    # 示例
    from sklearn.ensemble import RandomForestRegressor
    np.random.seed(42)

    # 生成示例数据
    n, p = 200, 5
    X = np.random.randn(n, p)
    y = 3*X[:, 0] - 2*X[:, 1] + 0.5*X[:, 2] + np.random.randn(n) * 0.1

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X[:150], y[:150])

    analyzer = SHAPAnalyzer(
        model,
        X_train=X[:150],
        X_test=X[150:],
        feature_names=["温度", "压力", "流量", "浓度", "时间"]
    )
    analyzer.fit()

    # 生成图表
    analyzer.plot_summary("figures/png/fig_shap_summary.png")
    analyzer.plot_top_features("figures/png/fig_shap_top_features.png")
    analyzer.plot_waterfall(sample_idx=0, save_path="figures/png/fig_shap_waterfall.png")

    # 生成报告
    report = analyzer.generate_report()
    print(report)
