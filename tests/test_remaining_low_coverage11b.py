"""第十一批(补)：vrp 2-opt swap + break + MTVRP"""
import os
import sys
from pathlib import Path

os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import pytest
import random

SKILL_ROOT = r"C:\Users\Lenovo\.claude\skills\cumcm-coach-skill-v7"


class TestVrp2optSwap:
    def test_2opt_swap_executed(self):
        """覆盖 lines 206-207: 2-opt 实际执行交换

        构造坐标使贪心产生交叉路径，2-opt 能找到改进。
        4 个客户呈梯形排列，贪心按距离构造出交叉路径。
        """
        from algorithms.optimization.vrp import VRP
        # depot 在中心，客户分布在四周使贪心产生交叉
        coords = np.array([
            [50, 50],   # 0 depot
            [10, 60],   # 1 左上
            [90, 40],   # 2 右下
            [20, 30],   # 3 左下
            [80, 70],   # 4 右上
        ], float)
        n = 5
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 1, 1, 1, 1]
        # 单车辆，大容量 -> 所有客户在一条路径
        vrp = VRP(dist, demands, capacity=100, n_vehicles=1)
        r = vrp.solve_greedy_2opt()
        assert "routes" in r
        # 路径应至少有3个客户（触发2-opt）
        assert any(len(rt) >= 3 for rt in r["routes"])

    def test_2opt_directly(self):
        """直接调用 _2opt_improve 覆盖交换逻辑"""
        from algorithms.optimization.vrp import VRP
        n = 6
        coords = np.array([
            [0, 0], [10, 0], [9, 1], [11, 2], [8, 3], [12, 4]
        ], float)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 1, 1, 1, 1, 1]
        vrp = VRP(dist, demands, capacity=100, n_vehicles=1)
        # 手工传入一条可能有交叉的路径
        routes = [[1, 3, 2, 4, 5]]
        improved = vrp._2opt_improve(routes)
        assert len(improved) == 1

    def test_break_when_all_served(self):
        """覆盖 line 135: 车辆数多余时 break

        4 客户，1 车容量足够，3 辆车 -> 第2、3 轮 unvisited 为空
        """
        from algorithms.optimization.vrp import VRP
        n = 5
        coords = np.random.default_rng(0).uniform(0, 100, (n, 2))
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 1, 1, 1, 1]
        vrp = VRP(dist, demands, capacity=100, n_vehicles=3)
        r = vrp.solve_greedy_2opt()
        assert r["n_vehicles_used"] <= 3


class TestMTVRP:
    """覆盖 MTVRP 类的 break (line 497)"""

    def test_mtvrp_basic(self):
        from algorithms.optimization.vrp import MTVRP
        n = 6
        coords = np.random.default_rng(0).uniform(0, 100, (n, 2))
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 2, 3, 2, 3, 2]
        vehicle_types = [{"capacity": 5, "cost_per_km": 2, "count": 2}]
        m = MTVRP(dist, demands, vehicle_types)
        r = m.solve_greedy()
        assert "routes" in r
        assert "total_cost" in r

    def test_mtvrp_capacity_exceeded_break(self):
        """覆盖 line 497: nearest=None -> break (所有客户超容量)"""
        from algorithms.optimization.vrp import MTVRP
        n = 4
        coords = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], float)
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 5, 5, 5]
        vehicle_types = [{"capacity": 1, "cost_per_km": 1, "count": 2}]
        m = MTVRP(dist, demands, vehicle_types)
        r = m.solve_greedy()
        assert "routes" in r

    def test_mtvrp_multi_vehicle_type(self):
        from algorithms.optimization.vrp import MTVRP
        n = 8
        coords = np.random.default_rng(1).uniform(0, 100, (n, 2))
        dist = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                dist[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))
        demands = [0, 2, 3, 2, 3, 2, 1, 4]
        vehicle_types = [
            {"capacity": 5, "cost_per_km": 2, "count": 2},
            {"capacity": 10, "cost_per_km": 3, "count": 1},
        ]
        m = MTVRP(dist, demands, vehicle_types)
        r = m.solve_greedy()
        assert "total_cost" in r