#!/usr/bin/env python3
"""
作业车间调度（JSSP）求解器 v1.0
================================
实现作业车间调度问题的多种求解算法，适用于B题调度优化类问题。

支持的问题类型：
- JSSP（经典作业车间调度）
- FJSSP（柔性作业车间调度）
- 多目标调度（最小化makespan + 延期）

算法：
- GA（遗传算法，基于工序编码）
- NSGA-II（多目标优化）
- 启发式规则（SPT/LPT/EDD）

使用方式：
    from algorithms.optimization.job_shop import JobShopScheduler

    jobs = [
        [(0, 3), (1, 2), (2, 2)],  # Job 0: M0-3, M1-2, M2-2
        [(1, 2), (2, 1), (0, 4)],  # Job 1: M1-2, M2-1, M0-4
    ]
    scheduler = JobShopScheduler(jobs)
    result = scheduler.solve_ga(pop_size=100, max_gen=500)
    print(result['makespan'], result['schedule'])
"""

import random
from typing import Optional

import numpy as np

# ============================================================
# JSSP 核心类
# ============================================================

class JobShopScheduler:
    """作业车间调度求解器"""

    def __init__(self,
                 jobs: list[list[tuple[int, int]]],
                 n_machines: Optional[int] = None,
                 due_dates: Optional[list[int]] = None):
        """
        初始化JSSP问题

        Args:
            jobs: 作业列表，每个作业是工序列表 [(machine, processing_time), ...]
            n_machines: 机器数量（自动推断）
            due_dates: 各作业的交货期（可选，用于EDD规则）
        """
        self.jobs = jobs
        self.n_jobs = len(jobs)
        self.n_machines = n_machines or max(m for job in jobs for m, _ in job) + 1
        self.due_dates = due_dates

        # 计算总工序数
        self.n_operations = sum(len(job) for job in jobs)

        # 作业工序索引
        self.job_operation_idx = []
        idx = 0
        for job in jobs:
            self.job_operation_idx.append(list(range(idx, idx + len(job))))
            idx += len(job)

    def _decode_chromosome(self, chromosome: list[int]) -> dict:
        """
        解码染色体为调度方案

        Args:
            chromosome: 基于工序编码的染色体（作业编号序列）

        Returns:
            包含schedule和makespan的字典
        """
        # 初始化
        job_progress = [0] * self.n_jobs
        machine_available = [0] * self.n_machines
        job_available = [0] * self.n_jobs

        schedule = []  # [(job, operation, machine, start, end), ...]

        for gene in chromosome:
            job = gene
            op_idx = job_progress[job]

            if op_idx >= len(self.jobs[job]):
                continue

            machine, proc_time = self.jobs[job][op_idx]

            # 计算开始时间
            start = max(machine_available[machine], job_available[job])
            end = start + proc_time

            # 更新
            schedule.append((job, op_idx, machine, start, end))
            machine_available[machine] = end
            job_available[job] = end
            job_progress[job] += 1

        # 计算makespan
        makespan = max(end for _, _, _, _, end in schedule) if schedule else 0

        return {
            'schedule': schedule,
            'makespan': makespan,
            'machine_available': machine_available,
            'job_available': job_available
        }

    def _calculate_fitness(self, chromosome: list[int]) -> float:
        """计算适应度（makespan）"""
        result = self._decode_chromosome(chromosome)
        return result['makespan']

    def _generate_chromosome(self) -> list[int]:
        """生成随机染色体（基于工序编码）"""
        chromosome = []
        for job in range(self.n_jobs):
            chromosome.extend([job] * len(self.jobs[job]))
        random.shuffle(chromosome)
        return chromosome

    # ── 启发式规则 ────────────────────────────────────────────

    def solve_spt(self) -> dict:
        """最短加工时间优先（SPT）"""
        # 按加工时间排序工序
        operations = []
        for job_idx, job in enumerate(self.jobs):
            for op_idx, (machine, time) in enumerate(job):
                operations.append((time, job_idx, op_idx, machine))

        operations.sort(key=lambda x: x[0])

        # 构造染色体
        chromosome = []
        for _, job_idx, _, _ in operations:
            chromosome.append(job_idx)

        result = self._decode_chromosome(chromosome)
        result['method'] = 'SPT（最短加工时间）'
        return result

    def solve_edd(self) -> dict:
        """最早交货期优先（EDD）"""
        if not self.due_dates:
            # 如果没有交货期，使用SPT
            return self.solve_spt()

        # 按交货期排序作业
        job_order = sorted(range(self.n_jobs), key=lambda j: self.due_dates[j])

        # 构造染色体
        chromosome = []
        for job in job_order:
            chromosome.extend([job] * len(self.jobs[job]))

        result = self._decode_chromosome(chromosome)
        result['method'] = 'EDD（最早交货期）'
        return result

    # ── 遗传算法 ──────────────────────────────────────────────

    def solve_ga(self,
                 pop_size: int = 100,
                 max_gen: int = 500,
                 pc: float = 0.8,
                 pm: float = 0.2,
                 elite_ratio: float = 0.1,
                 verbose: bool = False) -> dict:
        """
        遗传算法求解JSSP

        Args:
            pop_size: 种群大小
            max_gen: 最大迭代次数
            pc: 交叉概率
            pm: 变异概率
            elite_ratio: 精英比例
            verbose: 是否打印进度

        Returns:
            包含schedule和makespan的字典
        """
        # 初始化种群
        population = [self._generate_chromosome() for _ in range(pop_size)]

        best_fitness = float('inf')
        best_chromosome = None

        for gen in range(max_gen):
            # 计算适应度
            fitness = [self._calculate_fitness(chrom) for chrom in population]

            # 更新最优
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_fitness:
                best_fitness = fitness[min_idx]
                best_chromosome = population[min_idx][:]

            if verbose and gen % 50 == 0:
                print(f"Gen {gen}: best makespan = {best_fitness}")

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

                # POX交叉（基于作业的顺序交叉）
                if random.random() < pc:
                    child = self._pox_crossover(parent1, parent2)
                else:
                    child = parent1[:]

                # 变异（交换变异）
                if random.random() < pm:
                    child = self._swap_mutation(child)

                new_population.append(child)

            population = new_population

        # 解码最优解
        result = self._decode_chromosome(best_chromosome)
        result['method'] = '遗传算法'
        result['iterations'] = max_gen
        return result

    def _pox_crossover(self, parent1: list[int], parent2: list[int]) -> list[int]:
        """POX交叉（Precedence Operation Crossover）"""
        n = len(parent1)

        # 随机选择一部分作业
        n_selected = random.randint(1, self.n_jobs - 1)
        selected_jobs = set(random.sample(range(self.n_jobs), n_selected))

        # 从parent1中提取选中作业的工序
        child = [None] * n
        p1_ops = []
        p2_ops = []

        for i in range(n):
            if parent1[i] in selected_jobs:
                p1_ops.append(parent1[i])
            if parent2[i] not in selected_jobs:
                p2_ops.append(parent2[i])

        # 填充child
        p1_idx = 0
        p2_idx = 0
        for i in range(n):
            if parent1[i] in selected_jobs:
                child[i] = p1_ops[p1_idx]
                p1_idx += 1

        for i in range(n):
            if child[i] is None:
                child[i] = p2_ops[p2_idx]
                p2_idx += 1

        return child

    def _swap_mutation(self, chromosome: list[int]) -> list[int]:
        """交换变异"""
        chrom = chromosome[:]
        i, j = random.sample(range(len(chrom)), 2)
        chrom[i], chrom[j] = chrom[j], chrom[i]
        return chrom

    # ── NSGA-II 多目标优化 ────────────────────────────────────

    def solve_nsga2(self,
                    pop_size: int = 100,
                    max_gen: int = 500,
                    verbose: bool = False) -> dict:
        """
        NSGA-II 多目标优化求解JSSP

        目标1：最小化 makespan
        目标2：最小化总延期（如果有交货期）

        Args:
            pop_size: 种群大小
            max_gen: 最大迭代次数
            verbose: 是否打印进度

        Returns:
            包含Pareto前沿的字典
        """
        # 初始化种群
        population = [self._generate_chromosome() for _ in range(pop_size)]

        # 计算目标值
        objectives = []
        for chrom in population:
            obj = self._calculate_objectives(chrom)
            objectives.append(obj)

        for gen in range(max_gen):
            # 非支配排序
            fronts = self._non_dominated_sort(objectives)

            # 计算拥挤度
            crowding = self._calculate_crowding(objectives, fronts)

            # 生成子代
            offspring = []
            while len(offspring) < pop_size:
                # 锦标赛选择
                parent1 = self._tournament_select(population, objectives, fronts, crowding)
                parent2 = self._tournament_select(population, objectives, fronts, crowding)

                # 交叉
                if random.random() < 0.8:
                    child = self._pox_crossover(parent1, parent2)
                else:
                    child = parent1[:]

                # 变异
                if random.random() < 0.2:
                    child = self._swap_mutation(child)

                offspring.append(child)

            # 计算子代目标值
            offspring_obj = [self._calculate_objectives(chrom) for chrom in offspring]

            # 合并父代和子代
            combined_pop = population + offspring
            combined_obj = objectives + offspring_obj

            # 非支配排序
            combined_fronts = self._non_dominated_sort(combined_obj)

            # 选择新一代
            new_pop = []
            new_obj = []
            front_idx = 0

            while len(new_pop) + len(combined_fronts[front_idx]) <= pop_size:
                for idx in combined_fronts[front_idx]:
                    new_pop.append(combined_pop[idx])
                    new_obj.append(combined_obj[idx])
                front_idx += 1
                if front_idx >= len(combined_fronts):
                    break

            # 用拥挤度选择剩余个体
            if len(new_pop) < pop_size and front_idx < len(combined_fronts):
                last_front = combined_fronts[front_idx]
                crowding_last = self._calculate_crowding_single(combined_obj, last_front)
                sorted_indices = sorted(last_front, key=lambda i: crowding_last[i], reverse=True)

                for idx in sorted_indices:
                    if len(new_pop) >= pop_size:
                        break
                    new_pop.append(combined_pop[idx])
                    new_obj.append(combined_obj[idx])

            population = new_pop
            objectives = new_obj

            if verbose and gen % 50 == 0:
                print(f"Gen {gen}: Pareto size = {len(combined_fronts[0])}")

        # 提取Pareto前沿
        final_fronts = self._non_dominated_sort(objectives)
        pareto_indices = final_fronts[0]

        pareto_solutions = []
        for idx in pareto_indices:
            result = self._decode_chromosome(population[idx])
            result['objectives'] = objectives[idx]
            pareto_solutions.append(result)

        return {
            'method': 'NSGA-II',
            'pareto_front': pareto_solutions,
            'n_solutions': len(pareto_solutions),
            'iterations': max_gen
        }

    def _calculate_objectives(self, chromosome: list[int]) -> list[float]:
        """计算多目标值"""
        result = self._decode_chromosome(chromosome)
        makespan = result['makespan']

        # 目标2：总延期
        total_tardiness = 0
        if self.due_dates:
            for job_idx in range(self.n_jobs):
                completion = result['job_available'][job_idx]
                tardiness = max(0, completion - self.due_dates[job_idx])
                total_tardiness += tardiness

        return [makespan, total_tardiness]

    def _non_dominated_sort(self, objectives: list[list[float]]) -> list[list[int]]:
        """非支配排序"""
        n = len(objectives)
        domination_count = [0] * n
        dominated_set = [[] for _ in range(n)]
        fronts = [[]]

        for i in range(n):
            for j in range(i + 1, n):
                if self._dominates(objectives[i], objectives[j]):
                    dominated_set[i].append(j)
                    domination_count[j] += 1
                elif self._dominates(objectives[j], objectives[i]):
                    dominated_set[j].append(i)
                    domination_count[i] += 1

            if domination_count[i] == 0:
                fronts[0].append(i)

        front_idx = 0
        while fronts[front_idx]:
            next_front = []
            for i in fronts[front_idx]:
                for j in dominated_set[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            front_idx += 1
            fronts.append(next_front)

        return [f for f in fronts if f]

    def _dominates(self, obj1: list[float], obj2: list[float]) -> bool:
        """判断obj1是否支配obj2"""
        better_in_any = False
        for a, b in zip(obj1, obj2):
            if a > b:
                return False
            if a < b:
                better_in_any = True
        return better_in_any

    def _calculate_crowding(self, objectives: list[list[float]],
                           fronts: list[list[int]]) -> dict[int, float]:
        """计算拥挤度"""
        crowding = dict.fromkeys(range(len(objectives)), 0.0)

        for front in fronts:
            if len(front) <= 2:
                for idx in front:
                    crowding[idx] = float('inf')
                continue

            # 对每个目标排序
            for obj_idx in range(len(objectives[0])):
                sorted_front = sorted(front, key=lambda i: objectives[i][obj_idx])

                crowding[sorted_front[0]] = float('inf')
                crowding[sorted_front[-1]] = float('inf')

                obj_range = (objectives[sorted_front[-1]][obj_idx] -
                           objectives[sorted_front[0]][obj_idx])

                if obj_range == 0:
                    continue

                for i in range(1, len(sorted_front) - 1):
                    crowding[sorted_front[i]] += (
                        (objectives[sorted_front[i+1]][obj_idx] -
                         objectives[sorted_front[i-1]][obj_idx]) / obj_range
                    )

        return crowding

    def _calculate_crowding_single(self, objectives: list[list[float]],
                                  indices: list[int]) -> dict[int, float]:
        """计算单个前沿的拥挤度"""
        crowding = dict.fromkeys(indices, 0.0)

        if len(indices) <= 2:
            for idx in indices:
                crowding[idx] = float('inf')
            return crowding

        for obj_idx in range(len(objectives[0])):
            sorted_indices = sorted(indices, key=lambda i: objectives[i][obj_idx])

            crowding[sorted_indices[0]] = float('inf')
            crowding[sorted_indices[-1]] = float('inf')

            obj_range = (objectives[sorted_indices[-1]][obj_idx] -
                        objectives[sorted_indices[0]][obj_idx])

            if obj_range == 0:
                continue

            for i in range(1, len(sorted_indices) - 1):
                crowding[sorted_indices[i]] += (
                    (objectives[sorted_indices[i+1]][obj_idx] -
                     objectives[sorted_indices[i-1]][obj_idx]) / obj_range
                )

        return crowding

    def _tournament_select(self, population, objectives, fronts, crowding,
                          tournament_size: int = 2) -> list[int]:
        """锦标赛选择"""
        candidates = random.sample(range(len(population)), tournament_size)

        # 按前沿排序
        front_rank = {}
        for rank, front in enumerate(fronts):
            for idx in front:
                front_rank[idx] = rank

        best = min(candidates, key=lambda i: (front_rank.get(i, 999), -crowding.get(i, 0)))
        return population[best][:]


# ============================================================
# FJSSP 柔性作业车间调度
# ============================================================

class FlexibleJobShopScheduler:
    """柔性作业车间调度求解器"""

    def __init__(self,
                 jobs: list[list[list[tuple[int, int]]]],
                 n_machines: Optional[int] = None):
        """
        初始化FJSSP问题

        Args:
            jobs: 作业列表，每个作业是工序列表，每个工序是可选机器列表
                  [  # Job 0
                    [(0, 3), (1, 4)],  # Op 0: M0-3 或 M1-4
                    [(1, 2), (2, 3)],  # Op 1: M1-2 或 M2-3
                  ]
            n_machines: 机器数量
        """
        self.jobs = jobs
        self.n_jobs = len(jobs)
        self.n_machines = n_machines or max(m for job in jobs for ops in job for m, _ in ops) + 1

    def solve_ga(self, pop_size: int = 100, max_gen: int = 500,
                 verbose: bool = False) -> dict:
        """遗传算法求解FJSSP（简化版）"""

        def decode(chromosome):
            """解码染色体：(工序序列, 机器选择序列)"""
            op_sequence, machine_selection = chromosome
            job_progress = [0] * self.n_jobs
            machine_available = [0] * self.n_machines
            job_available = [0] * self.n_jobs
            schedule = []

            for gene_idx in op_sequence:
                job = gene_idx
                op_idx = job_progress[job]

                if op_idx >= len(self.jobs[job]):
                    continue

                # 选择机器
                machine_options = self.jobs[job][op_idx]
                machine_idx = machine_selection[gene_idx] % len(machine_options)
                machine, proc_time = machine_options[machine_idx]

                start = max(machine_available[machine], job_available[job])
                end = start + proc_time

                schedule.append((job, op_idx, machine, start, end))
                machine_available[machine] = end
                job_available[job] = end
                job_progress[job] += 1

            makespan = max(end for _, _, _, _, end in schedule) if schedule else 0
            return schedule, makespan

        def generate():
            """生成随机染色体"""
            op_seq = []
            for job in range(self.n_jobs):
                op_seq.extend([job] * len(self.jobs[job]))
            random.shuffle(op_seq)

            machine_sel = []
            for job in range(self.n_jobs):
                for ops in self.jobs[job]:
                    machine_sel.append(random.randint(0, len(ops) - 1))

            return (op_seq, machine_sel)

        # 简化的GA
        population = [generate() for _ in range(pop_size)]
        best_makespan = float('inf')
        best_schedule = None

        for gen in range(max_gen):
            fitness = []
            for chrom in population:
                _, makespan = decode(chrom)
                fitness.append(makespan)

            min_idx = np.argmin(fitness)
            if fitness[min_idx] < best_makespan:
                best_makespan = fitness[min_idx]
                best_schedule, _ = decode(population[min_idx])

            if verbose and gen % 50 == 0:
                print(f"Gen {gen}: best makespan = {best_makespan}")

            # 简化的选择和交叉
            new_pop = [population[min_idx]]  # 精英保留
            while len(new_pop) < pop_size:
                p1 = population[random.randint(0, pop_size - 1)]
                p2 = population[random.randint(0, pop_size - 1)]
                # 简单交叉
                child = (p1[0][:], p1[1][:])
                new_pop.append(child)

            population = new_pop

        return {
            'method': 'GA（柔性车间调度）',
            'schedule': best_schedule,
            'makespan': best_makespan
        }


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("作业车间调度 (JSSP) 求解器测试")
    print("=" * 60)

    # 测试JSSP
    jobs = [
        [(0, 3), (1, 2), (2, 2)],  # Job 0: M0-3, M1-2, M2-2
        [(1, 2), (2, 1), (0, 4)],  # Job 1: M1-2, M2-1, M0-4
        [(2, 3), (0, 1), (1, 3)],  # Job 2: M2-3, M0-1, M1-3
    ]
    due_dates = [10, 12, 15]

    scheduler = JobShopScheduler(jobs, due_dates=due_dates)

    # SPT
    print("\n[1] SPT:")
    result1 = scheduler.solve_spt()
    print(f"    Makespan: {result1['makespan']}")

    # EDD
    print("\n[2] EDD:")
    result2 = scheduler.solve_edd()
    print(f"    Makespan: {result2['makespan']}")

    # GA
    print("\n[3] GA:")
    result3 = scheduler.solve_ga(pop_size=50, max_gen=100, verbose=False)
    print(f"    Makespan: {result3['makespan']}")

    # NSGA-II
    print("\n[4] NSGA-II (多目标):")
    result4 = scheduler.solve_nsga2(pop_size=50, max_gen=100, verbose=False)
    print(f"    Pareto解数量: {result4['n_solutions']}")
    for sol in result4['pareto_front'][:3]:
        print(f"    Makespan={sol['makespan']}, Tardiness={sol['objectives'][1]}")

    print("\n" + "=" * 60)
    print("测试完成!")
