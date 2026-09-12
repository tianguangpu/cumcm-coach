#!/usr/bin/env python3
"""
两阶段求解框架 v1.0
===================
实现"聚类/选址→优化"的两阶段求解模式，适用于B题综合优化类问题。

典型应用场景：
- 中转站选址 + 路径优化（EECMCM.2025.B）
- 设施选址 + 资源分配
- 区域划分 + 调度优化

算法组合：
- 第一阶段：K-Means/层次聚类/贪心选址
- 第二阶段：VRP/JSSP/线性规划

使用方式：
    from algorithms.optimization.two_stage import TwoStageSolver

    solver = TwoStageSolver(problem_type='facility_routing')
    result = solver.solve(data, n_clusters=5, constraints={})
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import cdist
import random

# ============================================================
# 两阶段求解器
# ============================================================

class TwoStageSolver:
    """两阶段求解框架"""

    def __init__(self, problem_type: str = 'facility_routing'):
        """
        初始化两阶段求解器

        Args:
            problem_type: 问题类型
                - 'facility_routing': 设施选址 + 路径优化
                - 'clustering_scheduling': 聚类 + 调度
                - 'partition_assignment': 分区 + 分配
        """
        self.problem_type = problem_type
        self.stage1_result = None
        self.stage2_result = None

    def solve(self,
              customers: np.ndarray,
              demands: List[float],
              n_clusters: int,
              capacity: float = None,
              distance_matrix: np.ndarray = None,
              verbose: bool = False) -> Dict:
        """
        执行两阶段求解

        Args:
            customers: 客户坐标 (n×2) 或距离矩阵
            demands: 客户需求量
            n_clusters: 聚类/设施数量
            capacity: 设施/车辆容量限制
            distance_matrix: 距离矩阵（可选，不提供则自动计算）
            verbose: 是否打印进度

        Returns:
            包含两阶段结果的字典
        """
        # 计算距离矩阵
        if distance_matrix is None:
            distance_matrix = cdist(customers, customers, metric='euclidean')

        # 第一阶段：聚类/选址
        if verbose:
            print("=" * 50)
            print("第一阶段：聚类/选址")
            print("=" * 50)

        self.stage1_result = self._stage1_clustering(
            customers, demands, n_clusters, distance_matrix, verbose
        )

        # 第二阶段：路径/调度优化
        if verbose:
            print("\n" + "=" * 50)
            print("第二阶段：路径/调度优化")
            print("=" * 50)

        self.stage2_result = self._stage2_optimization(
            customers, demands, distance_matrix, capacity, verbose
        )

        # 合并结果
        return {
            'problem_type': self.problem_type,
            'stage1': self.stage1_result,
            'stage2': self.stage2_result,
            'total_cost': self.stage2_result.get('total_distance', 0),
            'n_facilities': n_clusters
        }

    def _stage1_clustering(self,
                          customers: np.ndarray,
                          demands: List[float],
                          n_clusters: int,
                          distance_matrix: np.ndarray,
                          verbose: bool) -> Dict:
        """第一阶段：聚类/选址"""
        n_customers = len(customers)

        if self.problem_type == 'facility_routing':
            # K-Means聚类
            return self._kmeans_clustering(customers, demands, n_clusters, verbose)

        elif self.problem_type == 'clustering_scheduling':
            # 层次聚类
            return self._hierarchical_clustering(customers, demands, n_clusters, verbose)

        else:
            # 贪心选址
            return self._greedy_facility_location(customers, demands, n_clusters,
                                                  distance_matrix, verbose)

    def _kmeans_clustering(self,
                          customers: np.ndarray,
                          demands: List[float],
                          n_clusters: int,
                          verbose: bool) -> Dict:
        """K-Means聚类"""
        from scipy.cluster.vq import kmeans2

        # 运行K-Means
        centroids, labels = kmeans2(customers, n_clusters, minit='points')

        # 整理聚类结果
        clusters = [[] for _ in range(n_clusters)]
        cluster_demands = [0] * n_clusters

        for i, label in enumerate(labels):
            clusters[label].append(i)
            cluster_demands[label] += demands[i]

        if verbose:
            for i in range(n_clusters):
                print(f"  聚类{i}: {len(clusters[i])}个客户, 需求={cluster_demands[i]:.1f}")

        return {
            'method': 'K-Means聚类',
            'centroids': centroids,
            'labels': labels,
            'clusters': clusters,
            'cluster_demands': cluster_demands
        }

    def _hierarchical_clustering(self,
                                customers: np.ndarray,
                                demands: List[float],
                                n_clusters: int,
                                verbose: bool) -> Dict:
        """层次聚类"""
        # 计算距离矩阵
        dist_matrix = cdist(customers, customers, metric='euclidean')

        # 层次聚类
        Z = linkage(dist_matrix, method='ward')
        labels = fcluster(Z, n_clusters, criterion='maxclust') - 1

        # 整理聚类结果
        clusters = [[] for _ in range(n_clusters)]
        cluster_demands = [0] * n_clusters

        for i, label in enumerate(labels):
            clusters[label].append(i)
            cluster_demands[label] += demands[i]

        if verbose:
            for i in range(n_clusters):
                print(f"  聚类{i}: {len(clusters[i])}个客户, 需求={cluster_demands[i]:.1f}")

        return {
            'method': '层次聚类',
            'labels': labels,
            'clusters': clusters,
            'cluster_demands': cluster_demands
        }

    def _greedy_facility_location(self,
                                  customers: np.ndarray,
                                  demands: List[float],
                                  n_facilities: int,
                                  distance_matrix: np.ndarray,
                                  verbose: bool) -> Dict:
        """贪心选址"""
        n_customers = len(customers)

        # 选择初始设施（需求最大的点）
        facility_indices = [np.argmax(demands)]

        for _ in range(n_facilities - 1):
            # 计算每个客户到最近设施的距离
            min_distances = np.full(n_customers, np.inf)

            for i in range(n_customers):
                for f in facility_indices:
                    d = distance_matrix[i][f]
                    if d < min_distances[i]:
                        min_distances[i] = d

            # 选择距离最远的点作为新设施
            new_facility = np.argmax(min_distances)
            facility_indices.append(new_facility)

        # 分配客户到最近设施
        clusters = [[] for _ in range(n_facilities)]
        cluster_demands = [0] * n_facilities
        labels = np.zeros(n_customers, dtype=int)

        for i in range(n_customers):
            nearest_facility = None
            nearest_dist = np.inf

            for f_idx, f in enumerate(facility_indices):
                d = distance_matrix[i][f]
                if d < nearest_dist:
                    nearest_facility = f_idx
                    nearest_dist = d

            clusters[nearest_facility].append(i)
            cluster_demands[nearest_facility] += demands[i]
            labels[i] = nearest_facility

        if verbose:
            print(f"  选址位置: {facility_indices}")
            for i in range(n_facilities):
                print(f"  设施{i}: {len(clusters[i])}个客户, 需求={cluster_demands[i]:.1f}")

        return {
            'method': '贪心选址',
            'facility_indices': facility_indices,
            'facility_locations': customers[facility_indices],
            'labels': labels,
            'clusters': clusters,
            'cluster_demands': cluster_demands
        }

    def _stage2_optimization(self,
                            customers: np.ndarray,
                            demands: List[float],
                            distance_matrix: np.ndarray,
                            capacity: float,
                            verbose: bool) -> Dict:
        """第二阶段：路径/调度优化"""
        clusters = self.stage1_result['clusters']
        n_clusters = len(clusters)

        total_distance = 0
        routes = []

        for cluster_idx in range(n_clusters):
            cluster = clusters[cluster_idx]

            if not cluster:
                continue

            # 为每个聚类求解VRP
            if verbose:
                print(f"  优化聚类{cluster_idx}: {len(cluster)}个客户")

            # 构建子问题距离矩阵
            # 节点0是虚拟车场，其他节点是客户
            cluster_nodes = list(cluster)  # 客户节点索引
            n_nodes = len(cluster_nodes) + 1  # +1 for depot

            # 创建子问题距离矩阵（加入车场到各客户的距离）
            sub_dist = np.zeros((n_nodes, n_nodes))

            # 车场到各客户的距离（用车辆质心作为车场）
            cluster_center = np.mean(customers[cluster], axis=0)

            for i in range(len(cluster_nodes)):
                # 车场到客户i的距离
                d_to_depot = np.sqrt(np.sum((customers[cluster_nodes[i]] - cluster_center) ** 2))
                sub_dist[0][i + 1] = d_to_depot
                sub_dist[i + 1][0] = d_to_depot

                # 客户之间的距离
                for j in range(len(cluster_nodes)):
                    sub_dist[i + 1][j + 1] = distance_matrix[cluster_nodes[i]][cluster_nodes[j]]

            # 子问题需求
            sub_demands = [0] + [demands[i] for i in cluster]

            # 求解子VRP（使用简化贪心算法）
            try:
                # 简化的贪心路径构造
                unvisited = list(range(1, n_nodes))  # 排除车场
                current = 0
                route = []
                load = 0

                while unvisited:
                    # 找最近的可行客户
                    nearest = None
                    nearest_dist = float('inf')

                    for node in unvisited:
                        if load + sub_demands[node] <= (capacity or 100):
                            d = sub_dist[current][node]
                            if d < nearest_dist:
                                nearest = node
                                nearest_dist = d

                    if nearest is None:
                        break

                    route.append(cluster_nodes[nearest - 1])  # 映射回原始编号
                    load += sub_demands[nearest]
                    unvisited.remove(nearest)
                    current = nearest

                routes.append(route)

                # 计算路径距离
                if route:
                    dist = sub_dist[0][1]  # 车场到第一个客户
                    for i in range(len(route) - 1):
                        orig_i = cluster_nodes.index(route[i])
                        orig_j = cluster_nodes.index(route[i + 1])
                        dist += distance_matrix[route[i]][route[i + 1]]
                    # 返回车场
                    last_node = cluster_nodes.index(route[-1])
                    dist += sub_dist[last_node + 1][0]
                    total_distance += dist

            except Exception as e:
                if verbose:
                    print(f"    警告: {e}")
                # 降级为简单路径
                route = cluster_nodes[:]
                routes.append(route)

                # 计算简单路径距离
                dist = 0
                for i in range(len(route) - 1):
                    dist += distance_matrix[route[i]][route[i + 1]]
                total_distance += dist

        return {
            'method': '两阶段优化',
            'routes': routes,
            'total_distance': total_distance,
            'n_routes': len(routes)
        }


# ============================================================
# 设施选址 + 分配 求解器
# ============================================================

class FacilityLocationSolver:
    """设施选址求解器"""

    def __init__(self,
                 customer_locations: np.ndarray,
                 customer_demands: List[float],
                 facility_candidates: np.ndarray,
                 fixed_costs: List[float],
                 transport_costs: np.ndarray = None):
        """
        初始化设施选址问题

        Args:
            customer_locations: 客户位置 (n×2)
            customer_demands: 客户需求量
            facility_candidates: 候选设施位置 (m×2)
            fixed_costs: 各候选设施的固定成本
            transport_costs: 运输成本矩阵 (n×m)，不提供则用欧氏距离
        """
        self.customers = customer_locations
        self.demands = np.array(customer_demands)
        self.facilities = facility_candidates
        self.fixed_costs = np.array(fixed_costs)
        self.n_customers = len(customer_locations)
        self.n_facilities = len(facility_candidates)

        # 计算运输成本
        if transport_costs is None:
            self.transport_costs = cdist(customer_locations, facility_candidates,
                                        metric='euclidean')
        else:
            self.transport_costs = transport_costs

    def solve_greedy(self, max_facilities: int = None) -> Dict:
        """贪心选址"""
        if max_facilities is None:
            max_facilities = self.n_facilities

        selected = []
        remaining = set(range(self.n_facilities))
        assignment = np.zeros(self.n_customers, dtype=int)

        for _ in range(max_facilities):
            if not remaining:
                break

            best_facility = None
            best_saving = -np.inf

            for f in remaining:
                # 计算选择该设施的总成本
                cost = self.fixed_costs[f]

                # 计算分配成本
                for c in range(self.n_customers):
                    if len(selected) == 0 or self.transport_costs[c][f] < self.transport_costs[c][assignment[c]]:
                        pass  # 会节省成本

                # 简化：选择能最大程度降低总成本的设施
                total_transport = 0
                for c in range(self.n_customers):
                    min_cost = self.transport_costs[c][f]
                    if len(selected) > 0:
                        current_cost = self.transport_costs[c][assignment[c]]
                        min_cost = min(min_cost, current_cost)
                    total_transport += min_cost * self.demands[c]

                saving = -self.fixed_costs[f] - total_transport

                if saving > best_saving:
                    best_saving = saving
                    best_facility = f

            if best_facility is not None:
                selected.append(best_facility)
                remaining.remove(best_facility)

                # 更新分配
                for c in range(self.n_customers):
                    best_f = None
                    best_cost = np.inf
                    for f in selected:
                        cost = self.transport_costs[c][f]
                        if cost < best_cost:
                            best_cost = cost
                            best_f = f
                    assignment[c] = best_f

        # 计算总成本
        total_cost = sum(self.fixed_costs[f] for f in selected)
        for c in range(self.n_customers):
            total_cost += self.transport_costs[c][assignment[c]] * self.demands[c]

        return {
            'method': '贪心选址',
            'selected_facilities': selected,
            'assignment': assignment,
            'total_cost': total_cost,
            'n_facilities': len(selected)
        }

    def solve_p_median(self, p: int = 3) -> Dict:
        """P-中位数问题求解"""
        # 简化：枚举所有p个设施的组合（适合小规模问题）
        if self.n_facilities > 15:
            # 大规模问题用贪心
            return self.solve_greedy(p)

        from itertools import combinations

        best_cost = np.inf
        best_selection = None
        best_assignment = None

        for selection in combinations(range(self.n_facilities), p):
            # 计算分配和成本
            assignment = np.zeros(self.n_customers, dtype=int)
            total_cost = sum(self.fixed_costs[f] for f in selection)

            for c in range(self.n_customers):
                best_f = None
                best_transport = np.inf
                for f in selection:
                    if self.transport_costs[c][f] < best_transport:
                        best_transport = self.transport_costs[c][f]
                        best_f = f
                assignment[c] = best_f
                total_cost += best_transport * self.demands[c]

            if total_cost < best_cost:
                best_cost = total_cost
                best_selection = list(selection)
                best_assignment = assignment

        return {
            'method': f'P-中位数 (p={p})',
            'selected_facilities': best_selection,
            'assignment': best_assignment,
            'total_cost': best_cost,
            'n_facilities': p
        }


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    np.random.seed(42)

    print("=" * 60)
    print("两阶段求解框架测试")
    print("=" * 60)

    # 生成测试数据
    n_customers = 30
    customers = np.random.rand(n_customers, 2) * 100
    demands = [random.randint(1, 5) for _ in range(n_customers)]

    # 测试设施选址+路径优化
    print("\n[1] 设施选址 + 路径优化:")
    solver = TwoStageSolver(problem_type='facility_routing')
    result = solver.solve(customers, demands, n_clusters=5, capacity=20, verbose=True)

    print(f"\n  总距离: {result['total_cost']:.2f}")
    print(f"  路径数: {result['stage2']['n_routes']}")

    # 测试设施选址求解器
    print("\n[2] 设施选址求解器:")
    n_candidates = 8
    facilities = np.random.rand(n_candidates, 2) * 100
    fixed_costs = [random.randint(50, 200) for _ in range(n_candidates)]

    fl_solver = FacilityLocationSolver(customers, demands, facilities, fixed_costs)
    fl_result = fl_solver.solve_greedy(max_facilities=4)

    print(f"  选中设施: {fl_result['selected_facilities']}")
    print(f"  总成本: {fl_result['total_cost']:.2f}")
    print(f"  设施数: {fl_result['n_facilities']}")

    print("\n" + "=" * 60)
    print("测试完成!")
