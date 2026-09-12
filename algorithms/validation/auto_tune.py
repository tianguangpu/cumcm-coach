"""
自动超参调优 + 交叉验证框架
替代手动设置参数,自动搜索最优超参并交叉验证。

用法:
    from auto_tune import AutoTuner
    tuner = AutoTuner(model_class=RandomForestRegressor, param_grid=PARAM_GRIDS["rf"])
    best_model, best_params, cv_results = tuner.fit(X, y, cv=5)
    tuner.plot_convergence("figures/png/fig_tuning_convergence.png")
    tuner.plot_cv_results("figures/png/fig_cv_results.png")
"""

import warnings
import time
import numpy as np
import pandas as pd
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from sklearn.model_selection import (
        GridSearchCV, RandomizedSearchCV, cross_val_score,
        KFold, TimeSeriesSplit, StratifiedKFold
    )
    from sklearn.metrics import make_scorer, mean_squared_error, r2_score, mean_absolute_error
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False


# ============================================================
# 内置参数网格(国赛常用算法)
# ============================================================

PARAM_GRIDS = {
    "rf": {
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [3, 5, 7, 10, None],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    },
    "xgb": {
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [3, 5, 7, 9],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "subsample": [0.7, 0.8, 0.9, 1.0],
        "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
    },
    "lgbm": {
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [3, 5, 7, -1],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "num_leaves": [15, 31, 63, 127],
        "subsample": [0.7, 0.8, 0.9, 1.0],
    },
    "svr": {
        "C": [0.1, 1, 10, 100],
        "epsilon": [0.01, 0.1, 0.2],
        "kernel": ["rbf", "linear", "poly"],
        "gamma": ["scale", "auto", 0.01, 0.1],
    },
    "ridge": {
        "alpha": [0.01, 0.1, 1, 10, 100],
    },
    "lasso": {
        "alpha": [0.001, 0.01, 0.1, 1, 10],
    },
    "knn": {
        "n_neighbors": [3, 5, 7, 9, 11],
        "weights": ["uniform", "distance"],
        "p": [1, 2],
    },
    "mlp": {
        "hidden_layer_sizes": [(64,), (128,), (64, 32), (128, 64), (128, 64, 32)],
        "activation": ["relu", "tanh"],
        "alpha": [0.0001, 0.001, 0.01],
        "learning_rate": ["constant", "adaptive"],
    },
}


class AutoTuner:
    """
    自动超参调优器。

    Parameters
    ----------
    model_class : class
        模型类(如 RandomForestRegressor)
    param_grid : dict
        参数网格
    method : str
        "grid" (网格搜索) | "random" (随机搜索) | "optuna" (贝叶斯优化)
    n_iter : int
        随机搜索/贝叶斯优化的迭代次数
    scoring : str
        评分指标: "r2", "neg_mse", "neg_mae"
    """

    def __init__(self, model_class, param_grid=None, method="optuna", n_iter=50, scoring="r2"):
        self.model_class = model_class
        self.param_grid = param_grid or {}
        self.method = method
        self.n_iter = n_iter
        self.scoring = scoring
        self.best_model = None
        self.best_params = None
        self.cv_results = None
        self.search_time = 0

    def fit(self, X, y, cv=5, is_time_series=False):
        """
        执行超参搜索 + 交叉验证。

        Parameters
        ----------
        X : array-like
            特征矩阵
        y : array-like
            目标变量
        cv : int
            交叉验证折数
        is_time_series : bool
            是否为时序数据(使用 TimeSeriesSplit)

        Returns
        -------
        tuple: (best_model, best_params, cv_results_df)
        """
        if not HAS_SKLEARN:
            raise RuntimeError("请安装 scikit-learn")

        X, y = np.array(X), np.array(y)

        # 选择交叉验证策略
        if is_time_series:
            cv_strategy = TimeSeriesSplit(n_splits=cv)
        else:
            cv_strategy = KFold(n_splits=cv, shuffle=True, random_state=42)

        start_time = time.time()

        if self.method == "optuna" and HAS_OPTUNA:
            result = self._fit_optuna(X, y, cv_strategy)
        elif self.method == "random":
            result = self._fit_random(X, y, cv_strategy)
        else:
            result = self._fit_grid(X, y, cv_strategy)

        self.search_time = time.time() - start_time
        return result

    def _fit_grid(self, X, y, cv_strategy):
        """网格搜索"""
        search = GridSearchCV(
            self.model_class(),
            self.param_grid,
            cv=cv_strategy,
            scoring=self.scoring,
            n_jobs=-1,
            return_train_score=True,
        )
        search.fit(X, y)

        self.best_model = search.best_estimator_
        self.best_params = search.best_params_
        self.cv_results = pd.DataFrame(search.cv_results_)

        return self.best_model, self.best_params, self.cv_results

    def _fit_random(self, X, y, cv_strategy):
        """随机搜索"""
        search = RandomizedSearchCV(
            self.model_class(),
            self.param_grid,
            n_iter=self.n_iter,
            cv=cv_strategy,
            scoring=self.scoring,
            n_jobs=-1,
            random_state=42,
            return_train_score=True,
        )
        search.fit(X, y)

        self.best_model = search.best_estimator_
        self.best_params = search.best_params_
        self.cv_results = pd.DataFrame(search.cv_results_)

        return self.best_model, self.best_params, self.cv_results

    def _fit_optuna(self, X, y, cv_strategy):
        """贝叶斯优化(Optuna)"""
        def objective(trial):
            params = {}
            for name, values in self.param_grid.items():
                if isinstance(values[0], (int, np.integer)):
                    params[name] = trial.suggest_int(name, min(values), max(values))
                elif isinstance(values[0], (float, np.float64)):
                    params[name] = trial.suggest_float(name, min(values), max(values), log=True)
                elif isinstance(values[0], str):
                    params[name] = trial.suggest_categorical(name, values)
                else:
                    params[name] = trial.suggest_categorical(name, values)

            model = self.model_class(**params)
            scores = cross_val_score(model, X, y, cv=cv_strategy, scoring=self.scoring, n_jobs=-1)
            return scores.mean()

        study = optuna.create_study(direction="maximize" if self.scoring == "r2" else "minimize")
        study.optimize(objective, n_trials=self.n_iter, show_progress_bar=False)

        self.best_params = study.best_params
        self.best_model = self.model_class(**self.best_params)
        self.best_model.fit(X, y)

        # 构建 cv_results
        self.cv_results = pd.DataFrame([
            {"params": t.params, "mean_test_score": t.value, "trial": i}
            for i, t in enumerate(study.trials)
        ])

        return self.best_model, self.best_params, self.cv_results

    def cross_validate(self, X, y, cv=5, is_time_series=False):
        """
        对最优模型执行详细交叉验证。

        Returns
        -------
        dict: {"r2_mean", "r2_std", "mse_mean", "mse_std", "mae_mean", "mae_std", "scores"}
        """
        if self.best_model is None:
            raise RuntimeError("请先调用 fit()")

        X, y = np.array(X), np.array(y)

        if is_time_series:
            cv_strategy = TimeSeriesSplit(n_splits=cv)
        else:
            cv_strategy = KFold(n_splits=cv, shuffle=True, random_state=42)

        results = {}
        for metric_name, scorer in [("r2", "r2"), ("mse", "neg_mean_squared_error"), ("mae", "neg_mean_absolute_error")]:
            scores = cross_val_score(self.best_model, X, y, cv=cv_strategy, scoring=scorer)
            if metric_name in ("mse", "mae"):
                scores = -scores  # 转为正值
            results[f"{metric_name}_mean"] = scores.mean()
            results[f"{metric_name}_std"] = scores.std()
            results[f"{metric_name}_scores"] = scores.tolist()

        return results

    def plot_convergence(self, save_path=None):
        """绘制超参搜索收敛曲线"""
        if not HAS_MPL or self.cv_results is None:
            return

        fig, ax = plt.subplots(figsize=(8, 5))

        scores = self.cv_results["mean_test_score"].values
        best_so_far = np.maximum.accumulate(scores) if self.scoring == "r2" else np.minimum.accumulate(scores)

        ax.plot(range(1, len(scores)+1), scores, "o-", alpha=0.4, label="Trial Score", color="#90CAF9")
        ax.plot(range(1, len(best_so_far)+1), best_so_far, "s-", label="Best So Far", color="#1565C0", linewidth=2)

        ax.set_xlabel("Trial", fontsize=11)
        ax.set_ylabel("Score", fontsize=11)
        ax.set_title(f"Hyperparameter Search Convergence ({self.method})", fontsize=12, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] 收敛曲线已保存: {save_path}")
        plt.close()

    def plot_cv_results(self, save_path=None):
        """绘制交叉验证结果箱线图"""
        if not HAS_MPL or self.best_model is None:
            return

        fig, ax = plt.subplots(figsize=(8, 5))

        # 重新执行交叉验证获取各折分数
        from sklearn.model_selection import cross_val_score, KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=42)

        # 需要 X, y — 这里用 cv_results 的数据
        # 简化:用 train/test score 的分布
        if "mean_train_score" in self.cv_results.columns and "mean_test_score" in self.cv_results.columns:
            data = [self.cv_results["mean_test_score"].values]
            labels = ["Test Score"]
            ax.boxplot(data, labels=labels)
            ax.set_ylabel("Score", fontsize=11)
            ax.set_title("Cross-Validation Results", fontsize=12, fontweight="bold")
            ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.savefig(save_path.replace(".png", ".pdf"), dpi=600, bbox_inches="tight")
            print(f"[OK] CV 结果图已保存: {save_path}")
        plt.close()

    def summary(self):
        """输出调优摘要"""
        return {
            "method": self.method,
            "best_params": self.best_params,
            "best_score": self.cv_results["mean_test_score"].max() if self.cv_results is not None else None,
            "search_time": f"{self.search_time:.1f}s",
            "n_trials": len(self.cv_results) if self.cv_results is not None else 0,
        }


# ============================================================
# 独立交叉验证函数(不依赖 AutoTuner)
# ============================================================

def quick_cv(model, X, y, cv=5, is_time_series=False, scoring="r2"):
    """
    快速交叉验证,返回均值±标准差。

    Returns
    -------
    dict: {"mean", "std", "scores", "report_str"}
    """
    from sklearn.model_selection import cross_val_score, KFold, TimeSeriesSplit

    cv_strategy = TimeSeriesSplit(n_splits=cv) if is_time_series else KFold(n_splits=cv, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv_strategy, scoring=scoring)

    result = {
        "mean": scores.mean(),
        "std": scores.std(),
        "scores": scores.tolist(),
        "report_str": f"{scores.mean():.4f} ± {scores.std():.4f}",
    }

    return result


if __name__ == "__main__":
    from sklearn.ensemble import RandomForestRegressor
    np.random.seed(42)

    X = np.random.randn(200, 5)
    y = 3*X[:, 0] - 2*X[:, 1] + np.random.randn(200) * 0.5

    # 快速交叉验证
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    cv_result = quick_cv(model, X, y, cv=5)
    print(f"快速 CV: R² = {cv_result['report_str']}")

    # 自动调优
    tuner = AutoTuner(RandomForestRegressor, PARAM_GRIDS["rf"], method="optuna", n_iter=30)
    best_model, best_params, _ = tuner.fit(X, y, cv=5)
    print(f"最优参数: {best_params}")
    print(f"调优摘要: {tuner.summary()}")

    # 详细交叉验证
    detailed = tuner.cross_validate(X, y, cv=5)
    print(f"详细 CV: R² = {detailed['r2_mean']:.4f} ± {detailed['r2_std']:.4f}")
    print(f"         MSE = {detailed['mse_mean']:.4f} ± {detailed['mse_std']:.4f}")
