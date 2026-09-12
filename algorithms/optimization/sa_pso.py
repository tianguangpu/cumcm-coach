"""
SA-PSO: 模拟退火粒子群优化算法
=======================================
用于连续优化问题，特别适合多峰、非线性目标函数。

特点：
- 结合 PSO 的全局搜索能力和 SA 的局部精细搜索
- 自适应温度退火策略，避免早熟收敛
- 支持多种约束处理方法

参数说明：
- N: 粒子数（推荐 30-100）
- T_max: 最大迭代次数（推荐 100-500）
- T_0: 初始温度（推荐 100-1000）
- alpha: 退火率（推荐 0.90-0.99）
- w: 惯性权重（推荐 0.4-0.9）
- c1, c2: 学习因子（推荐 1.5-2.5）

用法：
    from sa_pso import SA_PSO

    solver = SA_PSO(
        obj=my_objective,
        dim=10,
        bounds=[(0, 100)] * 10,
        constraints=my_constraints,
        N=50,
        T_max=200
    )
    result = solver.solve()
"""

import numpy as np
from typing import Callable, List, Tuple, Optional
import matplotlib.pyplot as plt


class SA_PSO:
    """模拟退火粒子群优化算法"""

    def __init__(
        self,
        obj: Callable[[np.ndarray], float],
        dim: int,
        bounds: List[Tuple[float, float]],
        constraints: Optional[Callable[[np.ndarray], bool]] = None,
        repair: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        N: int = 50,
        T_max: int = 200,
        T_0: float = 100.0,
        alpha: float = 0.95,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 2.0,
        seed: int = 42
    ):
        """
        初始化 SA-PSO 优化器

        Args:
            obj: 目标函数（返回值越小越好）
            dim: 决策变量维度
            bounds: 变量边界 [(min1, max1), (min2, max2), ...]
            constraints: 约束函数（返回 True 表示满足约束）
            N: 粒子数
            T_max: 最大迭代次数
            T_0: 初始温度
            alpha: 退火率
            w: 惯性权重
            c1: 认知学习因子
            c2: 社会学习因子
            seed: 随机种子
        """
        self.obj = obj
        self.dim = dim
        self.bounds = np.array(bounds)
        self.constraints = constraints
        self.repair = repair
        self.N = N
        self.T_max = T_max
        self.T_0 = T_0
        self.alpha = alpha
        self.w = w
        self.c1 = c1
        self.c2 = c2

        np.random.seed(seed)

        # 初始化粒子位置和速度
        self.X = np.random.uniform(
            self.bounds[:, 0],
            self.bounds[:, 1],
            (N, dim)
        )
        self.V = np.random.uniform(
            -0.1 * (self.bounds[:, 1] - self.bounds[:, 0]),
            0.1 * (self.bounds[:, 1] - self.bounds[:, 0]),
            (N, dim)
        )

        # 可行域投影修复: 把候选解投影回可行域, 作为约束主通道(惩罚项仅作安全网)
        if self.repair is not None:
            self.X = np.array([self.repair(self.X[i]) for i in range(N)])

        # 初始化个体最优和全局最优
        self.pbest = self.X.copy()
        self.pbest_val = np.array([self.fitness(x) for x in self.X])
        self.gbest = self.pbest[np.argmin(self.pbest_val)].copy()
        self.gbest_val = np.min(self.pbest_val)

        # 记录收敛历史
        self.history = []
        self.T_history = []

    def is_feasible(self, x: np.ndarray) -> bool:
        """检查解是否可行"""
        # 边界约束
        if np.any(x < self.bounds[:, 0]) or np.any(x > self.bounds[:, 1]):
            return False
        # 自定义约束
        if self.constraints is not None:
            return self.constraints(x)
        return True

    def penalty(self, x: np.ndarray) -> float:
        """约束违反惩罚项"""
        if self.is_feasible(x):
            return 0.0
        else:
            # 边界违反惩罚
            penalty = 1e6
            violation = np.maximum(0, self.bounds[:, 0] - x) + \
                        np.maximum(0, x - self.bounds[:, 1])
            penalty += 1e4 * np.sum(violation ** 2)
            return penalty

    def fitness(self, x: np.ndarray) -> float:
        """适应度函数。

        - 提供 ``repair`` 时, 调用方已保证 x 可行, 直接返回目标值(避免惩罚项在紧约束下
          把搜索推向不可行角落)。这是 skill 推荐的约束主通道。
        - 未提供 ``repair`` 时, 退回 目标值 + 惩罚项(兼容旧用法)。
        """
        if self.repair is not None:
            return self.obj(x)
        return self.obj(x) + self.penalty(x)

    def metropolis_accept(self, old_val: float, new_val: float, T: float) -> bool:
        """Metropolis 准则"""
        if new_val < old_val:
            return True
        else:
            prob = np.exp(-(new_val - old_val) / T)
            return np.random.rand() < prob

    def solve(self, verbose: bool = True) -> dict:
        """
        执行优化

        Returns:
            dict: 包含最优解、最优值、收敛历史等
        """
        T = self.T_0

        for t in range(self.T_max):
            # 更新速度和位置
            r1 = np.random.rand(self.N, self.dim)
            r2 = np.random.rand(self.N, self.dim)

            # 速度更新（带自适应惯性权重）
            w_adaptive = self.w * (1 - t / self.T_max) + 0.4 * (t / self.T_max)
            self.V = w_adaptive * self.V + \
                     self.c1 * r1 * (self.pbest - self.X) + \
                     self.c2 * r2 * (self.gbest - self.X)

            # 位置更新
            self.X = self.X + self.V

            # 边界处理（向量化反射）
            X_lower = self.bounds[:, 0][np.newaxis, :]  # (1, dim)
            X_upper = self.bounds[:, 1][np.newaxis, :]  # (1, dim)

            # 处理超出下界
            mask_lower = self.X < X_lower
            self.X = np.where(mask_lower, X_lower + np.abs(self.X - X_lower), self.X)
            # 处理超出上界
            mask_upper = self.X > X_upper
            self.X = np.where(mask_upper, X_upper - np.abs(self.X - X_upper), self.X)

            # 可行域投影修复(约束主通道)
            if self.repair is not None:
                fixed = np.empty_like(self.X)
                for i in range(self.N):
                    fixed[i] = self.repair(self.X[i])
                self.X = fixed

            # 批量评估适应度（向量化）
            fit_new = np.empty(self.N, dtype=float)
            for i in range(self.N):
                fit_new[i] = self.fitness(self.X[i])

            # SA 接受准则（向量化）
            accept_mask = np.zeros(self.N, dtype=bool)
            for i in range(self.N):
                if self.metropolis_accept(self.pbest_val[i], fit_new[i], T):
                    accept_mask[i] = True
                    self.pbest[i] = self.X[i].copy()
                    self.pbest_val[i] = fit_new[i]

                    # 更新全局最优
                    if fit_new[i] < self.gbest_val:
                        self.gbest = self.X[i].copy()
                        self.gbest_val = fit_new[i]

            # 降温
            T = T * self.alpha

            # 记录历史
            self.history.append(self.gbest_val)
            self.T_history.append(T)

            if verbose and (t + 1) % 20 == 0:
                print(f"Iter {t+1}/{self.T_max}: Best = {self.gbest_val:.6f}, T = {T:.2f}")

        # 求解后可行性断言: 若仍不可行, 显式报错(而非静默返回不可行解)
        x_opt = self.repair(self.gbest) if self.repair is not None else self.gbest
        feasible = self.is_feasible(x_opt)
        if self.constraints is not None and not feasible:
            import warnings
            warnings.warn(
                "SA-PSO 求解结果不满足 constraints, 请改用 repair 可行域投影修复。",
                stacklevel=2,
            )

        return {
            'x_opt': x_opt,
            'f_opt': self.fitness(x_opt),
            'history': self.history,
            'iterations': self.T_max,
            'feasible': feasible
        }

    def plot_convergence(self, save_path: str = None):
        """绘制收敛曲线"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # 收敛曲线
        ax1.plot(self.history, 'b-', linewidth=2, label='Best Value')
        ax1.set_xlabel('Iteration', fontsize=12)
        ax1.set_ylabel('Objective Value', fontsize=12)
        ax1.set_title('Convergence Curve', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 温度曲线
        ax2.plot(self.T_history, 'r-', linewidth=2, label='Temperature')
        ax2.set_xlabel('Iteration', fontsize=12)
        ax2.set_ylabel('Temperature', fontsize=12)
        ax2.set_title('Annealing Schedule', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()


def demo():
    """测试函数：Sphere 函数"""
    def sphere(x):
        return np.sum(x ** 2)

    solver = SA_PSO(
        obj=sphere,
        dim=10,
        bounds=[(-5, 5)] * 10,
        N=50,
        T_max=200,
        T_0=100,
        alpha=0.95,
        seed=42
    )

    result = solver.solve(verbose=True)
    print(f"\n最优解: {result['x_opt']}")
    print(f"最优值: {result['f_opt']:.6e}")

    solver.plot_convergence('sa_pso_convergence.png')


if __name__ == '__main__':
    demo()