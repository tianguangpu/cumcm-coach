"""
算法基类定义

所有算法模块的抽象基类，提供统一的接口规范。

Usage:
    from algorithms.base import BaseSolver, SolverResult

    class MySolver(BaseSolver):
        def solve(self, objective, bounds):
            # 实现求解逻辑
            return SolverResult(x_opt=[1.0], f_opt=0.0)

        def validate_params(self):
            return True

    solver = MySolver()
    result = solver.solve(objective, bounds)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class SolverResult:
    """
    求解结果数据类。

    统一所有求解器的返回格式。

    Attributes:
        x_opt: 最优解（决策变量值）
        f_opt: 最优值（目标函数值）
        history: 收敛历史（可选）
        iterations: 迭代次数（可选）
        convergence: 是否收敛（可选）
        metadata: 额外元数据（可选）
        solver_name: 求解器名称（可选）
        solve_time: 求解耗时秒（可选）
    """

    x_opt: Any = None
    f_opt: float = float("inf")
    history: Optional[List[float]] = None
    iterations: Optional[int] = None
    convergence: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    solver_name: Optional[str] = None
    solve_time: Optional[float] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式。

        Returns:
            Dict: 包含所有字段的字典
        """
        return {
            "x_opt": self.x_opt.tolist() if isinstance(self.x_opt, np.ndarray) else self.x_opt,
            "f_opt": self.f_opt,
            "history": self.history,
            "iterations": self.iterations,
            "convergence": self.convergence,
            "metadata": self.metadata,
            "solver_name": self.solver_name,
            "solve_time": self.solve_time,
        }

    def summary(self) -> str:
        """
        生成结果摘要。

        Returns:
            str: 格式化的摘要字符串
        """
        lines = [
            f"Solver: {self.solver_name or 'Unknown'}",
            f"Optimal value: {self.f_opt:.6f}",
            f"Iterations: {self.iterations or 'N/A'}",
            f"Converged: {self.convergence or 'N/A'}",
            f"Solve time: {self.solve_time:.3f}s" if self.solve_time else "Solve time: N/A",
        ]
        if self.x_opt is not None:
            x_str = str(self.x_opt)[:50] + "..." if len(str(self.x_opt)) > 50 else str(self.x_opt)
            lines.append(f"Optimal solution: {x_str}")
        return "\n".join(lines)


class BaseSolver(ABC):
    """
    求解器抽象基类。

    所有算法模块必须继承此类并实现抽象方法。

    Attributes:
        name: 求解器名称
        version: 版本号
        description: 描述信息
    """

    name: str = "BaseSolver"
    version: str = "1.0.0"
    description: str = "Base solver class"

    def __init__(self, **kwargs):
        """
        初始化求解器。

        Args:
            **kwargs: 求解器参数
        """
        self.params = kwargs
        self._history: List[float] = []

    @abstractmethod
    def solve(self, objective: Callable, bounds: List[Tuple[float, float]], **kwargs) -> SolverResult:
        """
        求解优化问题。

        Args:
            objective: 目标函数，接受参数数组返回标量值
            bounds: 变量边界列表，每个元素为 (lower, upper) 元组
            **kwargs: 额外参数

        Returns:
            SolverResult: 求解结果

        Raises:
            ValueError: 参数无效时
            RuntimeError: 求解失败时
        """
        pass

    @abstractmethod
    def validate_params(self) -> bool:
        """
        验证参数有效性。

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 参数无效时
        """
        pass

    def get_history(self) -> List[float]:
        """
        获取收敛历史。

        Returns:
            List[float]: 目标函数值历史
        """
        return self._history.copy()

    def clear_history(self) -> None:
        """清空收敛历史"""
        self._history.clear()

    def _record(self, value: float) -> None:
        """
        记录一次迭代的值。

        Args:
            value: 目标函数值
        """
        self._history.append(value)

    def __repr__(self) -> str:
        return f"{self.name}(version={self.version})"


class PopulationBasedSolver(BaseSolver):
    """
    种群优化算法基类。

    继承自 BaseSolver，提供种群管理功能。

    Attributes:
        pop_size: 种群大小
        max_iter: 最大迭代次数
        dim: 问题维度
    """

    def __init__(self, pop_size: int = 50, max_iter: int = 200, **kwargs):
        """
        初始化种群算法。

        Args:
            pop_size: 种群大小
            max_iter: 最大迭代次数
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.dim: Optional[int] = None

    def validate_params(self) -> bool:
        """
        验证种群算法参数。

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 参数无效时
        """
        if self.pop_size <= 0:
            raise ValueError(f"pop_size must be positive, got {self.pop_size}")
        if self.max_iter <= 0:
            raise ValueError(f"max_iter must be positive, got {self.max_iter}")
        return True

    def _init_population(self, bounds: List[Tuple[float, float]]) -> np.ndarray:
        """
        初始化种群。

        Args:
            bounds: 变量边界

        Returns:
            np.ndarray: 种群矩阵 (pop_size, dim)
        """
        self.dim = len(bounds)
        lower = np.array([b[0] for b in bounds])
        upper = np.array([b[1] for b in bounds])
        return lower + np.random.rand(self.pop_size, self.dim) * (upper - lower)

    def _clip_bounds(self, x: np.ndarray, bounds: List[Tuple[float, float]]) -> np.ndarray:
        """
        将解裁剪到边界内。

        Args:
            x: 解向量
            bounds: 变量边界

        Returns:
            np.ndarray: 裁剪后的解
        """
        lower = np.array([b[0] for b in bounds])
        upper = np.array([b[1] for b in bounds])
        return np.clip(x, lower, upper)


class GradientBasedSolver(BaseSolver):
    """
    梯度优化算法基类。

    继承自 BaseSolver，提供梯度相关功能。

    Attributes:
        learning_rate: 学习率
        tolerance: 收敛容差
    """

    def __init__(self, learning_rate: float = 0.01, tolerance: float = 1e-6, **kwargs):
        """
        初始化梯度算法。

        Args:
            learning_rate: 学习率
            tolerance: 收敛容差
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.learning_rate = learning_rate
        self.tolerance = tolerance

    def validate_params(self) -> bool:
        """
        验证梯度算法参数。

        Returns:
            bool: 参数是否有效

        Raises:
            ValueError: 参数无效时
        """
        if self.learning_rate <= 0:
            raise ValueError(f"learning_rate must be positive, got {self.learning_rate}")
        if self.tolerance <= 0:
            raise ValueError(f"tolerance must be positive, got {self.tolerance}")
        return True

    def _numerical_gradient(self, func: Callable, x: np.ndarray, epsilon: float = 1e-8) -> np.ndarray:
        """
        数值梯度计算。

        Args:
            func: 目标函数
            x: 当前点
            epsilon: 差分步长

        Returns:
            np.ndarray: 梯度向量
        """
        grad = np.zeros_like(x)
        for i in range(len(x)):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += epsilon
            x_minus[i] -= epsilon
            grad[i] = (func(x_plus) - func(x_minus)) / (2 * epsilon)
        return grad
