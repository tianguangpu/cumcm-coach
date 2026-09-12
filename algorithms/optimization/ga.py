"""
GA: 遗传算法
=======================================
用于连续优化问题，作为 SA-PSO 的对照算法（金标准 §4.3d 三算法对比表）。

特点：
- 实数编码 + 锦标赛选择 + 算术交叉 + 高斯变异
- 精英保留，保证最优解不退化
- 接口与 sa_pso.py 对齐，可无缝进入同一算法对比表

参数说明：
- pop_size: 种群规模（推荐 30-100）
- max_gen: 最大进化代数（推荐 100-500）
- pc: 交叉概率（推荐 0.7-0.9）
- pm: 变异概率（推荐 0.05-0.2）
- elite_ratio: 精英保留比例（推荐 0.05-0.1）
- sigma: 高斯变异标准差（相对边界宽度，推荐 0.1）

用法：
    from ga import GA

    solver = GA(
        obj=my_objective,
        dim=10,
        bounds=[(0, 100)] * 10,
        constraints=my_constraints,
        pop_size=50,
        max_gen=200
    )
    result = solver.solve()
"""

import numpy as np
from typing import Callable, List, Tuple, Optional
import matplotlib.pyplot as plt


class GA:
    """遗传算法（实数编码，连续优化）"""

    def __init__(
        self,
        obj: Callable[[np.ndarray], float],
        dim: int,
        bounds: List[Tuple[float, float]],
        constraints: Optional[Callable[[np.ndarray], bool]] = None,
        repair: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        pop_size: int = 50,
        max_gen: int = 200,
        pc: float = 0.8,
        pm: float = 0.1,
        elite_ratio: float = 0.1,
        sigma: float = 0.1,
        seed: int = 42
    ):
        """
        初始化遗传算法优化器

        Args:
            obj: 目标函数（返回值越小越好）
            dim: 决策变量维度
            bounds: 变量边界 [(min1, max1), (min2, max2), ...]
            constraints: 约束函数（返回 True 表示满足约束）
            pop_size: 种群规模
            max_gen: 最大进化代数
            pc: 交叉概率
            pm: 变异概率
            elite_ratio: 精英保留比例
            sigma: 高斯变异标准差（相对边界宽度）
            seed: 随机种子
        """
        self.obj = obj
        self.dim = dim
        self.bounds = np.array(bounds)
        self.constraints = constraints
        self.repair = repair
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.pc = pc
        self.pm = pm
        self.elite_ratio = elite_ratio
        self.sigma = sigma

        np.random.seed(seed)

        # 初始化种群
        self.pop = np.random.uniform(
            self.bounds[:, 0], self.bounds[:, 1], (pop_size, dim)
        )
        self.fitness_val = np.array([self.fitness(x) for x in self.pop], dtype=float)

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
        """适应度函数。提供 ``repair`` 时直接返回目标值(修复即保证可行); 否则退回惩罚项。"""
        if self.repair is not None:
            return self.obj(x)
        return self.obj(x) + self.penalty(x)

    def _tournament_select(self) -> np.ndarray:
        """锦标赛选择（二元）"""
        idx = np.random.randint(0, self.pop_size, 2)
        return self.pop[idx[np.argmin(self.fitness_val[idx])]].copy()

    def _crossover(self, p1: np.ndarray, p2: np.ndarray):
        """算术交叉"""
        if np.random.rand() < self.pc:
            alpha = np.random.rand()
            return alpha * p1 + (1 - alpha) * p2, alpha * p2 + (1 - alpha) * p1
        return p1.copy(), p2.copy()

    def _mutate(self, x: np.ndarray) -> np.ndarray:
        """高斯变异"""
        for j in range(self.dim):
            if np.random.rand() < self.pm:
                width = self.bounds[j, 1] - self.bounds[j, 0]
                x[j] += np.random.normal(0, self.sigma * width)
        return x

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
        n_elite = max(1, int(self.pop_size * self.elite_ratio))

        for gen in range(self.max_gen):
            # 精英保留
            elite_idx = np.argsort(self.fitness_val)[:n_elite]
            elite = self.pop[elite_idx].copy()

            # 生成新一代
            new_pop = [ind.copy() for ind in elite]
            while len(new_pop) < self.pop_size:
                p1 = self._tournament_select()
                p2 = self._tournament_select()
                c1, c2 = self._crossover(p1, p2)
                c1 = self._bound(self._mutate(c1))
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    c2 = self._bound(self._mutate(c2))
                    new_pop.append(c2)

            self.pop = np.array(new_pop[:self.pop_size])
            if self.repair is not None:
                fixed = np.empty_like(self.pop)
                for i in range(self.pop_size):
                    fixed[i] = self.repair(self.pop[i])
                self.pop = fixed
            fv = np.empty(self.pop_size, dtype=float)
            for i in range(self.pop_size):
                fv[i] = self.fitness(self.pop[i])
            self.fitness_val = fv

            best_val = np.min(self.fitness_val)
            self.history.append(best_val)

            if verbose and (gen + 1) % 20 == 0:
                print(f"Gen {gen + 1}/{self.max_gen}: Best = {best_val:.6f}")

        best_idx = np.argmin(self.fitness_val)
        x_opt = self.repair(self.pop[best_idx]) if self.repair is not None else self.pop[best_idx]
        feasible = self.is_feasible(x_opt)
        if self.constraints is not None and not feasible:
            import warnings
            warnings.warn(
                "GA 求解结果不满足 constraints, 请改用 repair 可行域投影修复。",
                stacklevel=2,
            )
        return {
            'x_opt': x_opt,
            'f_opt': self.fitness(x_opt),
            'history': self.history,
            'iterations': self.max_gen,
            'feasible': feasible
        }

    def plot_convergence(self, save_path: str = None):
        """绘制收敛曲线"""
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(self.history, 'g-', linewidth=2, label='Best Fitness')
        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel('Fitness Value', fontsize=12)
        ax.set_title('GA Convergence Curve', fontsize=14)
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

    solver = GA(
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

    solver.plot_convergence('ga_convergence.png')


if __name__ == '__main__':
    demo()
