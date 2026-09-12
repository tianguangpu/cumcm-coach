"""
DE: 差分进化算法
=======================================
用于连续优化问题，作为 SA-PSO 的对照算法（金标准 §4.3d 三算法对比表）。

特点：
- DE/rand/1/bin 标准策略
- 逐个体贪婪选择，收敛稳定
- 接口与 sa_pso.py 对齐，可无缝进入同一算法对比表

参数说明：
- pop_size: 种群规模（推荐 30-100，通常取 dim 的 5-10 倍，至少 4）
- max_gen: 最大进化代数（推荐 100-500）
- F: 差分缩放因子（推荐 0.5-0.9）
- CR: 交叉概率（推荐 0.5-0.9）

用法：
    from de import DE

    solver = DE(
        obj=my_objective,
        dim=10,
        bounds=[(0, 100)] * 10,
        constraints=my_constraints,
        pop_size=50,
        max_gen=200
    )
    result = solver.solve()
"""

from typing import Callable, Optional

import matplotlib.pyplot as plt
import numpy as np

from .bounds import normalize_bounds


class DE:
    """差分进化算法（DE/rand/1/bin）"""

    def __init__(
        self,
        obj: Callable[[np.ndarray], float],
        dim: int,
        bounds: list[tuple[float, float]],
        constraints: Optional[Callable[[np.ndarray], bool]] = None,
        pop_size: int = 50,
        max_gen: int = 200,
        F: float = 0.7,
        CR: float = 0.8,
        seed: int = 42
    ):
        """
        初始化差分进化优化器

        Args:
            obj: 目标函数（返回值越小越好）
            dim: 决策变量维度
            bounds: 变量边界 [(min1, max1), (min2, max2), ...]
            constraints: 约束函数（返回 True 表示满足约束）
            pop_size: 种群规模（至少 4，需选 3 个互异个体）
            max_gen: 最大进化代数
            F: 差分缩放因子
            CR: 交叉概率
            seed: 随机种子
        """
        if pop_size < 4:
            raise ValueError("DE 种群规模至少为 4（需选 3 个互异个体）")

        self.obj = obj
        self.dim = dim
        self.bounds = normalize_bounds(bounds, dim)
        self.constraints = constraints
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.F = F
        self.CR = CR

        np.random.seed(seed)

        # 初始化种群
        self.pop = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], (pop_size, dim)
        )
        self.fitness_val = np.array([self.fitness(x) for x in self.pop])

        self.history = []

    def is_feasible(self, x: np.ndarray) -> bool:
        """检查解是否可行"""
        if np.any(x < self.bounds[:, 0]) or np.any(x > self.bounds[:, 1]):
            return False
        if self.constraints is not None:
            return self.constraints(x)
        return True

    def penalty(self, x: np.ndarray) -> float:
        """约束违反惩罚项"""
        if self.is_feasible(x):
            return 0.0
        violation = np.maximum(0, self.bounds[:, 0] - x) + \
                    np.maximum(0, x - self.bounds[:, 1])
        return 1e6 + 1e4 * np.sum(violation ** 2)

    def fitness(self, x: np.ndarray) -> float:
        """适应度函数（目标值 + 惩罚项）"""
        return self.obj(x) + self.penalty(x)

    def _mutate(self, idx: int) -> np.ndarray:
        """DE/rand/1 变异"""
        candidates = [i for i in range(self.pop_size) if i != idx]
        a, b, c = self.pop[np.random.choice(candidates, 3, replace=False)]
        return a + self.F * (b - c)

    def _crossover(self, target: np.ndarray, mutant: np.ndarray) -> np.ndarray:
        """二项式交叉"""
        mask = np.random.rand(self.dim) < self.CR
        if not np.any(mask):
            mask[np.random.randint(self.dim)] = True
        return np.where(mask, mutant, target)

    def _bound(self, x: np.ndarray) -> np.ndarray:
        """边界反射"""
        lower = self.bounds[:, 0]
        upper = self.bounds[:, 1]
        x = np.where(x < lower, lower + np.abs(x - lower), x)
        x = np.where(x > upper, upper - np.abs(x - upper), x)
        return x

    def solve(self, verbose: bool = True) -> dict:
        """
        执行优化

        Returns:
            dict: 包含最优解、最优值、收敛历史等
        """
        for gen in range(self.max_gen):
            for i in range(self.pop_size):
                mutant = self._mutate(i)
                trial = self._bound(self._crossover(self.pop[i], mutant))
                fit_trial = self.fitness(trial)

                if fit_trial < self.fitness_val[i]:
                    self.pop[i] = trial
                    self.fitness_val[i] = fit_trial

            best_val = np.min(self.fitness_val)
            self.history.append(best_val)

            if verbose and (gen + 1) % 20 == 0:
                print(f"Gen {gen + 1}/{self.max_gen}: Best = {best_val:.6f}")

        best_idx = np.argmin(self.fitness_val)
        return {
            'x_opt': self.pop[best_idx],
            'f_opt': self.fitness_val[best_idx],
            'history': self.history,
            'iterations': self.max_gen
        }

    def plot_convergence(self, save_path: str = None):
        """绘制收敛曲线"""
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(self.history, 'r-', linewidth=2, label='Best Fitness')
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Fitness Value', fontsize=12)
        ax.set_title('DE Convergence Curve', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()


def demo():
    """测试函数：Sphere 函数"""
    def sphere(x):
        return np.sum(x ** 2)

    solver = DE(
        obj=sphere,
        dim=10,
        bounds=[(-5, 5)] * 10,
        pop_size=50,
        max_gen=200,
        seed=42
    )

    result = solver.solve(verbose=True)
    print(f"\n最优解: {result['x_opt']}")
    print(f"最优值: {result['f_opt']:.6e}")

    solver.plot_convergence('de_convergence.png')


if __name__ == '__main__':
    demo()
