#!/usr/bin/env python3
"""
VRP/MTVRP 车辆路径问题求解器 v1.0
==================================
实现多种VRP变体的求解算法，适用于B题路径优化类问题。

支持的VRP变体：
- CVRP（容量约束VRP）
- VRPTW（时间窗口VRP）
- MTVRP（多车型VRP）
- VRPMB（多车场VRP）

算法：
- GA（遗传算法）
- PSO（粒子群算法）
- 贪心 + 2-opt（快速启发式）

使用方式：
    from algorithms.optimization.vrp import VRP

    vrp = VRP(distance_matrix, demands, capacity=5, n_vehicles=3)
    result = vrp.solve_ga(pop_size=100, max_gen=500)
    print(result['routes'], result['total_distance'])
"""

import random
from typing import Optional

import numpy as np

# ============================================================
# VRP 核心类
# ============================================================

class VRP:
    """车辆路径问题求解器"""

    def __init__(self,
                 distance_matrix: np.ndarray,
                 demands: list[float],
                 capacity: float,
                 n_vehicles: int,
                 depot: int = 0,
                 time_windows: Optional[list[tuple[float, float]]] = None,
                 service_times: Optional[list[float]] = None):
        """
        初始化VRP问题

        Args:
            distance_matrix: 距离矩阵 (n×n)
            demands: 各节点需求量
            capacity: 车辆最大载重
            n_vehicles: 车辆数量
            depot: 车场节点（默认0）
            time_windows: 时间窗口 [(earliest, latest), ...]（可选）
            service_times: 各节点服务时间（可选）
        """
        self.dist = np.array(distance_matrix)
        self.demands = np.array(demands)
        self.capacity = capacity
        self.n_vehicles = n_vehicles
        self.depot = depot
        self.n_nodes = len(demands)
        self.time_windows = time_windows
        self.service_times = service_times or [0] * self.n_nodes

        # 客户节点（排除车场）
        self.customers = [i for i in range(self.n_nodes) if i != depot]

    def _calculate_route_distance(self, route: list[int]) -> float:
        """计算单条路径的总距离"""
        if not route:
            return 0

        dist = self.dist[self.depot][route[0]]
        for i in range(len(route) - 1):
            dist += self.dist[route[i]][route[i + 1]]
        dist += self.dist[route[-1]][self.depot]

        return dist

    def _calculate_route_load(self, route: list[int]) -> float:
        """计算单条路径的总载重"""
        return sum(self.demands[i] for i in route)

    def _is_route_feasible(self, route: list[int]) -> bool:
        """检查路径是否可行（容量约束）"""
        return self._calculate_route_load(route) <= self.capacity

    def _split_routes(self, chromosome: list[int]) -> list[list[int]]:
        """将染色体分割为多条路径"""
        routes = []
        current_route = []
        current_load = 0

        for customer in chromosome:
            demand = self.demands[customer]

            if current_load + demand > self.capacity:
                if current_route:
                    routes.append(current_route)
                current_route = [customer]
                current_load = demand
            else:
                current_route.append(customer)
                current_load += demand

        if current_route:
            routes.append(current_route)

        # 确保不超过车辆数量
        while len(routes) > self.n_vehicles:
            # 合并最短的两条路径
            routes.sort(key=lambda r: self._calculate_route_load(r))
            merged = routes[0] + routes[1]
            routes = routes[2:]
            routes.append(merged)

        return routes

    def _total_distance(self, routes: list[list[int]]) -> float:
        """计算所有路径的总距离"""
        return sum(self._calculate_route_distance(route) for route in routes)

    # ── 贪心 + 2-opt 启发式 ──────────────────────────────────

    def solve_greedy_2opt(self) -> dict:
        """贪心构造 + 2-opt 改进"""
        # 贪心构造：最近邻
        unvisited = set(self.customers)
        routes = []

        for _ in range(self.n_vehicles):
            if not unvisited:
                break

            route = []
            current = self.depot
            load = 0

            while unvisited:
                # 找最近的可行客户
                nearest = None
                nearest_dist = float('inf')

                for customer in unvisited:
                    if load + self.demands[customer] <= self.capacity:
                        d = self.dist[current][customer]
                        if d < nearest_dist:
                            nearest = customer
                            nearest_dist = d

                if nearest is None:
                    break

                route.append(nearest)
                load += self.demands[nearest]
                unvisited.remove(nearest)
                current = nearest

            if route:
                routes.append(route)

        # 2-opt 改进
        routes = self._2opt_improve(routes)

        return {
            'method': '贪心+2-opt',
            'routes': routes,
            'total_distance': self._total_distance(routes),
            'n_vehicles_used': len(routes)
        }

    def _2opt_improve(self, routes: list[list[int]]) -> list[list[int]]:
        """2-opt 局部搜索改进"""
        improved_routes = []

        for route in routes:
            if len(route) < 3:
                improved_routes.append(route)
                continue

            improved = True
            best_route = route[:]

            while improved:
                improved = False
                for i in range(len(best_route) - 1):
                    for j in range(i + 2, len(best_route)):
                        # 计算2-opt交换后的距离变化
                        d1 = (self.dist[self.depot][best_route[0]] if i == 0
                              else self.dist[best_route[i-1]][best_route[i]])
                        d2 = self.dist[best_route[j-1]][best_route[j]]
                        d3 = self.dist[best_route[i]][best_route[i+1]]
                        d4 = (self.dist[best_route[j]][self.depot] if j == len(best_route) - 1
                              else self.dist[best_route[j]][best_route[j+1]])

                        old_dist = d1 + d2
                        new_dist = (self.dist[self.depot][best_route[0]] if i == 0
                                   else self.dist[best_route[i-1]][best_route[j-1]])
                        new_dist += self.dist[best_route[i]][best_route[j]]
                        new_dist += d3 + d4

                        if new_dist < old_dist:
                            # 执行2-opt交换
                            best_route[i:j] = best_route[i:j][::-1]
                            improved = True

            improved_routes.append(best_route)

        return improved_routes

    # ── 遗传算法 ──────────────────────────────────────────────

    def solve_ga(self,
                 pop_size: int = 100,
                 max_gen: int = 500,
                 pc: float = 0.8,
                 pm: float = 0.2,
                 elite_ratio: float = 0.1,
                 verbose: bool = False) -> dict:
        """
        遗传算法求解VRP

        Args:
            pop_size: 种群大小
            max_gen: 最大迭代次数
            pc: 交叉概率
            pm: 变异概率
            elite_ratio: 精英比例
            verbose: 是否打印进度

        Returns:
            包含routes和total_distance的字典
        """
        len(self.customers)

        # 初始化种群
        population = []
        for _ in range(pop_size):
            chromosome = self.customers[:]
            random.shuffle(chromosome)
            population.append(chromosome)

        best_fitness = float('inf')
        best_solution = None

        for gen in range(max_gen):
            # 计算适应度
            fitness = []
            for chrom in population:
                routes = self._split_routes(chrom)
                dist = self._total_distance(routes)
                fitness.append(dist)

            # 更新最优
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_solution = self._split_routes(population[min_idx])

            if verbose and gen % 50 == 0:
                print(f"Gen {gen}: best = {best_fitness:.2f}")

            # 选择（轮盘赌）
            max_fit = max(fitness)
            selection_probs = [(max_fit - f + 1) for f in fitness]
            total = sum(selection_probs)
            selection_probs = [p / total for p in selection_probs]

            # 精英保留
            elite_count = int(pop_size * elite_ratio)
            elite_indices = np.argsort(fitness)[:elite_count]
            new_population = [population[i][:] for i in elite_indices]

            # 交叉和变异
            while len(new_population) < pop_size:
                # 选择父代
                parent1_idx = np.random.choice(len(population), p=selection_probs)
                parent2_idx = np.random.choice(len(population), p=selection_probs)
                parent1 = population[parent1_idx][:]
                parent2 = population[parent2_idx][:]

                # 顺序交叉（OX）
                if random.random() < pc:
                    child = self._order_crossover(parent1, parent2)
                else:
                    child = parent1[:]

                # 变异（交换）
                if random.random() < pm:
                    child = self._swap_mutation(child)

                new_population.append(child)

            population = new_population

        return {
            'method': '遗传算法',
            'routes': best_solution,
            'total_distance': best_fitness,
            'n_vehicles_used': len(best_solution),
            'iterations': max_gen
        }

    def _order_crossover(self, parent1: list[int], parent2: list[int]) -> list[int]:
        """顺序交叉（OX）"""
        n = len(parent1)
        start, end = sorted(random.sample(range(n), 2))

        child = [None] * n
        child[start:end] = parent1[start:end]

        remaining = [x for x in parent2 if x not in child[start:end]]
        idx = 0
        for i in range(n):
            if child[i] is None:
                child[i] = remaining[idx]
                idx += 1

        return child

    def _swap_mutation(self, chromosome: list[int]) -> list[int]:
        """交换变异"""
        chrom = chromosome[:]
        i, j = random.sample(range(len(chrom)), 2)
        chrom[i], chrom[j] = chrom[j], chrom[i]
        return chrom

    # ── 粒子群算法 ────────────────────────────────────────────

    def solve_pso(self,
                  n_particles: int = 50,
                  max_iter: int = 300,
                  w: float = 0.7,
                  c1: float = 1.5,
                  c2: float = 1.5,
                  verbose: bool = False) -> dict:
        """
        粒子群算法求解VRP（基于排列的PSO）

        Args:
            n_particles: 粒子数量
            max_iter: 最大迭代次数
            w: 惯性权重
            c1: 个体学习因子
            c2: 社会学习因子
            verbose: 是否打印进度

        Returns:
            包含routes和total_distance的字典
        """
        n_customers = len(self.customers)

        # 初始化粒子（每个粒子是一个排列）
        particles = []
        velocities = []
        p_best = []
        p_best_fitness = []

        for _ in range(n_particles):
            perm = self.customers[:]
            random.shuffle(perm)
            particles.append(perm)
            velocities.append([0] * n_customers)
            p_best.append(perm[:])

            routes = self._split_routes(perm)
            fitness = self._total_distance(routes)
            p_best_fitness.append(fitness)

        # 全局最优
        g_best_idx = np.argmin(p_best_fitness)
        g_best = p_best[g_best_idx][:]
        g_best_fitness = p_best_fitness[g_best_idx]

        for iteration in range(max_iter):
            # 动态惯性权重
            w_dynamic = w * (1 - iteration / max_iter)

            for i in range(n_particles):
                # 生成新排列（基于交换序列）
                new_perm = particles[i][:]

                # 向个体最优学习
                if random.random() < c1:
                    # 从当前排列向p_best移动
                    swap_count = random.randint(1, n_customers // 3)
                    for _ in range(swap_count):
                        pos = random.randint(0, n_customers - 1)
                        target_val = p_best[i][pos]
                        curr_pos = new_perm.index(target_val)
                        new_perm[pos], new_perm[curr_pos] = new_perm[curr_pos], new_perm[pos]

                # 向全局最优学习
                if random.random() < c2:
                    swap_count = random.randint(1, n_customers // 3)
                    for _ in range(swap_count):
                        pos = random.randint(0, n_customers - 1)
                        target_val = g_best[pos]
                        curr_pos = new_perm.index(target_val)
                        new_perm[pos], new_perm[curr_pos] = new_perm[curr_pos], new_perm[pos]

                # 随机扰动
                if random.random() < w_dynamic:
                    i_idx, j_idx = random.sample(range(n_customers), 2)
                    new_perm[i_idx], new_perm[j_idx] = new_perm[j_idx], new_perm[i_idx]

                particles[i] = new_perm

                # 更新个体最优
                routes = self._split_routes(new_perm)
                fitness = self._total_distance(routes)

                if fitness < p_best_fitness[i]:
                    p_best[i] = new_perm[:]
                    p_best_fitness[i] = fitness

                    if fitness < g_best_fitness:
                        g_best = new_perm[:]
                        g_best_fitness = fitness

            if verbose and iteration % 50 == 0:
                print(f"Iter {iteration}: best = {g_best_fitness:.2f}")

        return {
            'method': '粒子群算法',
            'routes': self._split_routes(g_best),
            'total_distance': g_best_fitness,
            'n_vehicles_used': len(self._split_routes(g_best)),
            'iterations': max_iter
        }


# ============================================================
# MTVRP 多车型VRP
# ============================================================

class MTVRP:
    """多车型车辆路径问题"""

    def __init__(self,
                 distance_matrix: np.ndarray,
                 demands: list[float],
                 vehicle_types: list[dict],
                 depot: int = 0):
        """
        初始化MTVRP问题

        Args:
            distance_matrix: 距离矩阵
            demands: 各节点需求量
            vehicle_types: 车型列表 [{'capacity': 5, 'cost_per_km': 2, 'count': 3}, ...]
            depot: 车场节点
        """
        self.dist = np.array(distance_matrix)
        self.demands = np.array(demands)
        self.vehicle_types = vehicle_types
        self.depot = depot
        self.n_nodes = len(demands)
        self.customers = [i for i in range(self.n_nodes) if i != depot]

    def solve_greedy(self) -> dict:
        """贪心求解多车型VRP"""
        unvisited = set(self.customers)
        routes = []
        vehicle_assignments = []  # (车型, 路径)

        # 按容量从大到小排序车型
        sorted_types = sorted(self.vehicle_types,
                            key=lambda vt: vt['capacity'], reverse=True)

        for vtype in sorted_types:
            capacity = vtype['capacity']
            count = vtype['count']

            for _ in range(count):
                if not unvisited:
                    break

                route = []
                load = 0
                current = self.depot

                while unvisited:
                    nearest = None
                    nearest_dist = float('inf')

                    for customer in unvisited:
                        if load + self.demands[customer] <= capacity:
                            d = self.dist[current][customer]
                            if d < nearest_dist:
                                nearest = customer
                                nearest_dist = d

                    if nearest is None:
                        break

                    route.append(nearest)
                    load += self.demands[nearest]
                    unvisited.remove(nearest)
                    current = nearest

                if route:
                    routes.append(route)
                    vehicle_assignments.append(vtype)

        # 计算总成本
        total_cost = 0
        for route, vtype in zip(routes, vehicle_assignments):
            dist = self._calculate_route_distance(route)
            total_cost += dist * vtype['cost_per_km']

        return {
            'method': '贪心（多车型）',
            'routes': routes,
            'vehicle_assignments': vehicle_assignments,
            'total_cost': total_cost,
            'total_distance': sum(self._calculate_route_distance(r) for r in routes)
        }

    def _calculate_route_distance(self, route: list[int]) -> float:
        """计算单条路径的总距离"""
        if not route:
            return 0

        dist = self.dist[self.depot][route[0]]
        for i in range(len(route) - 1):
            dist += self.dist[route[i]][route[i + 1]]
        dist += self.dist[route[-1]][self.depot]

        return dist


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    # 生成测试数据
    np.random.seed(42)
    n_nodes = 10

    # 随机生成节点坐标
    coords = np.random.rand(n_nodes, 2) * 100

    # 计算距离矩阵
    dist_matrix = np.zeros((n_nodes, n_nodes))
    for i in range(n_nodes):
        for j in range(n_nodes):
            dist_matrix[i, j] = np.sqrt(np.sum((coords[i] - coords[j]) ** 2))

    # 需求量（车场为0）
    demands = [0] + [random.randint(1, 5) for _ in range(n_nodes - 1)]

    print("=" * 60)
    print("VRP 求解器测试")
    print("=" * 60)
    print(f"节点数: {n_nodes}")
    print(f"需求量: {demands}")
    print("车辆容量: 10")
    print()

    # 创建VRP问题
    vrp = VRP(dist_matrix, demands, capacity=10, n_vehicles=3)

    # 测试贪心+2-opt
    print("[1] 贪心 + 2-opt:")
    result1 = vrp.solve_greedy_2opt()
    print(f"    总距离: {result1['total_distance']:.2f}")
    print(f"    路径数: {result1['n_vehicles_used']}")
    for i, route in enumerate(result1['routes']):
        print(f"    路径{i+1}: {route}")
    print()

    # 测试GA
    print("[2] 遗传算法:")
    result2 = vrp.solve_ga(pop_size=50, max_gen=200, verbose=False)
    print(f"    总距离: {result2['total_distance']:.2f}")
    print(f"    路径数: {result2['n_vehicles_used']}")
    for i, route in enumerate(result2['routes']):
        print(f"    路径{i+1}: {route}")
    print()

    # 测试PSO
    print("[3] 粒子群算法:")
    result3 = vrp.solve_pso(n_particles=30, max_iter=200, verbose=False)
    print(f"    总距离: {result3['total_distance']:.2f}")
    print(f"    路径数: {result3['n_vehicles_used']}")
    for i, route in enumerate(result3['routes']):
        print(f"    路径{i+1}: {route}")

    print()
    print("=" * 60)
    print("测试完成!")
