"""
pytest 配置文件

提供共享的 fixtures 和配置。
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# scripts/ 目录下的自检工具（isolated_solve / ai_compliance 等）
# 供 test_algorithms_smoke / test_ai_compliance 导入
sys.path.insert(0, str(project_root / "scripts"))


@pytest.fixture
def sphere_function():
    """Sphere 测试函数: f(x) = sum(x_i^2)"""

    def sphere(x):
        return sum(xi**2 for xi in x)

    return sphere


@pytest.fixture
def rosenbrock_function():
    """Rosenbrock 测试函数"""

    def rosenbrock(x):
        return sum(100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2 for i in range(len(x) - 1))

    return rosenbrock


@pytest.fixture
def rastrigin_function():
    """Rastrigin 测试函数"""

    def rastrigin(x):
        n = len(x)
        return 10 * n + sum(xi**2 - 10 * np.cos(2 * np.pi * xi) for xi in x)

    return rastrigin


@pytest.fixture
def simple_bounds_2d():
    """简单 2D 边界"""
    return [(-5, 5), (-5, 5)]


@pytest.fixture
def simple_bounds_3d():
    """简单 3D 边界"""
    return [(-5, 5), (-5, 5), (-5, 5)]


@pytest.fixture
def sample_decision_matrix():
    """样本决策矩阵（用于评价算法）"""
    return [
        [7, 9, 9],
        [8, 6, 8],
        [9, 4, 7],
        [6, 8, 6],
    ]


@pytest.fixture
def sample_distance_matrix():
    """样本距离矩阵（用于 VRP）"""
    return [
        [0, 10, 15, 20, 25],
        [10, 0, 35, 25, 30],
        [15, 35, 0, 30, 20],
        [20, 25, 30, 0, 15],
        [25, 30, 20, 15, 0],
    ]


@pytest.fixture
def sample_time_series():
    """样本时间序列数据"""
    np.random.seed(42)
    t = np.arange(100)
    series = 50 + 0.5 * t + 10 * np.sin(2 * np.pi * t / 12) + np.random.randn(100) * 3
    return series.tolist()
