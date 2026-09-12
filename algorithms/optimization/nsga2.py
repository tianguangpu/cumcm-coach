# -*- coding: utf-8 -*-
"""NSGA-II 多目标优化器 (实数编码)。

标准实现: 快速非支配排序 + 拥挤度 + 精英保留环境选择。
接口与 sa_pso.py / ga.py 对齐: 支持 repair 参数(可行域投影, 约束主通道),
返回 dict 含 feasible 标志、pareto_F / pareto_X (list) 与超体积/分布度等指标。

注意: 为避免 numpy 在 Python3.13 下 np.all/np.array 的偶发 C 层崩溃,
本模块内部的目标矩阵 F 一律使用 Python list of lists, 支配/排序/拥挤度/
超体积/分布度均用纯 Python 计算, 仅在决策向量(连续优化)处使用 numpy。
"""
import math
import random as _rng
from collections import defaultdict
from typing import Callable, List, Optional, Tuple

import numpy as np


def _dominates(a: List[float], b: List[float]) -> bool:
    """a 是否支配 b (均最小化)。纯 Python, 避免 np.all C 层崩溃。"""
    le = all(ai <= bi for ai, bi in zip(a, b))
    lt = any(ai < bi for ai, bi in zip(a, b))
    return le and lt


def _fast_non_dominated_sort(F: List[List[float]]):
    """F: List[List[float]] (pop, m) 目标矩阵(最小化)。返回 fronts: List[List[int]]"""
    pop = len(F)
    S = [[] for _ in range(pop)]      # 被 i 支配的解
    n = [0] * pop                     # i 被多少解支配
    fronts = [[]]
    for p in range(pop):
        for q in range(pop):
            if p == q:
                continue
            if _dominates(F[p], F[q]):
                S[p].append(q)
            elif _dominates(F[q], F[p]):
                n[p] += 1
        if n[p] == 0:
            fronts[0].append(p)
    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    nxt.append(q)
        i += 1
        fronts.append(nxt)
    if not fronts[-1]:
        fronts.pop()
    return fronts


def _crowding_distance(F: List[List[float]], front: List[int]) -> List[float]:
    """计算某 front 内每个解的拥挤度, 返回顺序与 front 一一对应。纯 Python。"""
    k = len(front)
    cd = [0.0] * k
    if k <= 2:
        return [math.inf] * k
    m = len(F[0])
    # 取该 front 的目标子矩阵 (按 front 内顺序)
    sub = [F[idx] for idx in front]
    for obj in range(m):
        order = sorted(range(k), key=lambda r: sub[r][obj])
        cd[order[0]] = math.inf
        cd[order[-1]] = math.inf
        fmax = sub[order[-1]][obj]
        fmin = sub[order[0]][obj]
        rng = (fmax - fmin) if fmax > fmin else 1.0
        for idx in range(1, k - 1):
            cd[order[idx]] += (sub[order[idx + 1]][obj] -
                               sub[order[idx - 1]][obj]) / rng
    return cd


def _hypervolume(F: List[List[float]], ref: List[float]) -> float:
    """2 维超体积 (目标最小化)。F: List[List[2]], ref: 参考点(最差角)。纯 Python。"""
    pts = sorted(F, key=lambda v: v[0])
    hv = 0.0
    f2_prev = ref[1]
    for i in range(len(pts)):
        if pts[i][1] < f2_prev:
            hv += (ref[0] - pts[i][0]) * (f2_prev - pts[i][1])
            f2_prev = pts[i][1]
    return float(hv)


def _spread(F: List[List[float]]) -> float:
    """Deb 分布度 Δ (2 维近似)。越接近 0 分布越均匀。纯 Python。"""
    pts = sorted(F, key=lambda v: v[0])
    k = len(pts)
    if k < 3:
        return 0.0
    d = [math.hypot(pts[i][0] - pts[i + 1][0], pts[i][1] - pts[i + 1][1])
         for i in range(k - 1)]
    dmean = sum(d) / len(d)
    df, dl = d[0], d[-1]
    num = df + dl + sum(abs(di - dmean) for di in d)
    den = df + dl + (k - 1) * dmean
    return num / den if den > 0 else 0.0


class NSGA2:
    """非支配排序遗传算法 (多目标, 实数编码)"""

    def __init__(
        self,
        objs: List[Callable[[np.ndarray], float]],
        dim: int,
        bounds: List[Tuple[float, float]],
        constraints: Optional[Callable[[np.ndarray], bool]] = None,
        repair: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        pop_size: int = 60,
        max_gen: int = 200,
        pc: float = 0.9,
        pm: float = 0.1,
        sigma: float = 0.1,
        seed: int = 42,
    ):
        self.objs = objs
        self.m = len(objs)
        self.dim = dim
        self.bounds = np.array(bounds)
        self.constraints = constraints
        self.repair = repair
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.pc = pc
        self.pm = pm
        self.sigma = sigma
        _rng.seed(seed)

        lo = self.bounds[:, 0]
        hi = self.bounds[:, 1]
        self.pop = np.array([[_rng.uniform(lo[d], hi[d]) for d in range(dim)]
                              for _ in range(pop_size)])
        if self.repair is not None:
            fixed = np.empty_like(self.pop)
            for i in range(pop_size):
                fixed[i] = self.repair(self.pop[i])
            self.pop = fixed
        # F 用 Python list of lists, 避开 numpy 崩溃路径
        self.F = [self._eval(self.pop[i]) for i in range(pop_size)]
        # 初始 rank/cd 仅供首代锦标赛参考, solve 内会基于合并种群重建
        fronts = _fast_non_dominated_sort(self.F)
        self.rank = [0] * pop_size
        self.cd = [0.0] * pop_size
        for fi, front in enumerate(fronts):
            for idx in front:
                self.rank[idx] = fi
            cd_map = _crowding_distance(self.F, front)
            for pos, idx in enumerate(front):
                self.cd[idx] = cd_map[pos]
        self.history = []

    def _eval(self, x: np.ndarray) -> List[float]:
        return [float(f(x)) for f in self.objs]

    def _bound(self, x: np.ndarray) -> np.ndarray:
        return np.clip(x, self.bounds[:, 0], self.bounds[:, 1])

    def _mutate(self, x: np.ndarray) -> np.ndarray:
        if _rng.random() < self.pm:
            noise = np.array([_rng.gauss(0.0, 1.0) for _ in range(self.dim)])
            x = x + self.sigma * noise
        return self._bound(x)

    def _crossover(self, p1: np.ndarray, p2: np.ndarray):
        if _rng.random() < self.pc:
            alpha = _rng.random()
            c1 = alpha * p1 + (1 - alpha) * p2
            c2 = (1 - alpha) * p1 + alpha * p2
        else:
            c1, c2 = p1.copy(), p2.copy()
        return self._bound(c1), self._bound(c2)

    def _tournament(self) -> int:
        a, b = _rng.randrange(self.pop_size), _rng.randrange(self.pop_size)
        ra, rb = self.rank[a], self.rank[b]
        if ra != rb:
            return a if ra < rb else b
        ca, cb = self.cd[a], self.cd[b]
        return a if ca > cb else b   # 拥挤度大优先

    def solve(self, verbose: bool = False) -> dict:
        feasible_all = True
        for gen in range(self.max_gen):
            offspring = []
            while len(offspring) < self.pop_size:
                p1 = self.pop[self._tournament()]
                p2 = self.pop[self._tournament()]
                c1, c2 = self._crossover(p1, p2)
                c1 = self._mutate(c1)
                offspring.append(c1)
                if len(offspring) < self.pop_size:
                    c2 = self._mutate(c2)
                    offspring.append(c2)
            if self.repair is not None:
                offspring = [self.repair(o) for o in offspring]
            off_F = [self._eval(o) for o in offspring]

            # 合并父代 + 子代, 环境选择
            comb_X = list(self.pop) + list(offspring)
            comb_F = self.F + off_F
            fronts = _fast_non_dominated_sort(comb_F)

            new_idx, rank_arr = [], []
            for fi, front in enumerate(fronts):
                if len(new_idx) + len(front) > self.pop_size:
                    overflow_front = front
                    break
                new_idx.extend(front)
                rank_arr.extend([fi] * len(front))
            else:
                overflow_front = None
            if len(new_idx) < self.pop_size and overflow_front is not None:
                rem = self.pop_size - len(new_idx)
                included = set(new_idx)
                last = [idx for idx in overflow_front if idx not in included]
                cd_last = _crowding_distance(comb_F, last)
                order = sorted(range(len(last)), key=lambda o: -cd_last[o])
                need = [last[o] for o in order[:rem]]
                new_idx.extend(need)
                rank_arr.extend([len(fronts) - 1] * rem)

            # 可行性检查
            for idx in new_idx:
                if self.constraints is not None and not self.constraints(comb_X[idx]):
                    feasible_all = False

            new_pop = np.empty((len(new_idx), self.dim), dtype=float)
            for pos, i in enumerate(new_idx):
                new_pop[pos] = comb_X[i]
            self.pop = new_pop
            self.F = [comb_F[i] for i in new_idx]
            # rank_arr 已按 new_idx 顺序给出每个解的 front 编号
            self.rank = list(rank_arr)
            self.cd = [0.0] * self.pop_size
            # 按 front 分组计算拥挤度 (new_idx 内的局部索引)
            by_front = defaultdict(list)
            for pos, rk in enumerate(self.rank):
                by_front[rk].append(pos)
            for rk, members in by_front.items():
                cd_map = _crowding_distance(self.F, members)
                for pos, mbr in enumerate(members):
                    self.cd[mbr] = cd_map[pos]
            best = min(self.F[i][0] for i in range(self.pop_size))
            self.history.append(best)

            if verbose and (gen + 1) % 20 == 0:
                print(f"Gen {gen + 1}/{self.max_gen}: Best f1 = {best:.6f}")

        # 最终 Pareto 前沿 (rank 0)
        pf_idx = [i for i in range(self.pop_size) if self.rank[i] == 0]
        if not pf_idx:
            # 兜底: 直接对当前 F 重新排序取 front 0
            fr = _fast_non_dominated_sort(self.F)
            pf_idx = fr[0] if fr else list(range(self.pop_size))
            self.rank = [0] * self.pop_size
            if fr:
                for fi, front in enumerate(fr):
                    for i in front:
                        self.rank[i] = fi
        pareto_F = [self.F[i] for i in pf_idx]
        pareto_X = [self.pop[i].tolist() for i in pf_idx]
        # 参考点: 各目标最差角
        m = self.m
        ref = [max(pareto_F[i][k] for i in range(len(pareto_F))) for k in range(m)]
        hv = _hypervolume(pareto_F, ref) if m == 2 else 0.0
        spread = _spread(pareto_F) if m == 2 else 0.0

        if self.constraints is not None:
            for i in pf_idx:
                if not self.constraints(self.pop[i]):
                    feasible_all = False
        elif self.repair is not None:
            for i in pf_idx:
                if not self.repair(self.pop[i]).shape == self.pop[i].shape:
                    feasible_all = False

        return dict(
            x_opt=np.array(pareto_X[0]) if pareto_X else self.pop[0],
            f_opt=min(self.F[i][0] for i in range(self.pop_size)),
            pop=self.pop, F=self.F,
            pareto_F=np.array(pareto_F), pareto_X=np.array(pareto_X),
            n_pareto=len(pareto_F), hv=float(hv), spread=float(spread),
            feasible=bool(feasible_all), history=self.history,
        )


if __name__ == "__main__":
    # ZDT1 双目标 demo
    def zdt1(x):
        n = len(x)
        f1 = x[0]
        g = 1 + 9.0 / (n - 1) * sum(x[1:])
        h = 1 - (f1 / g) ** 0.5
        return [f1, g * h]
    dim = 30
    bnds = [(0.0, 1.0)] * dim
    ns = NSGA2([lambda x: zdt1(x)[0], lambda x: zdt1(x)[1]],
               dim, bnds, repair=None, pop_size=80, max_gen=200, seed=1)
    r = ns.solve(verbose=True)
    print(f"Pareto n={r['n_pareto']}, HV={r['hv']:.4f}, spread={r['spread']:.3f}, feasible={r['feasible']}")
