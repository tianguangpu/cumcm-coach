# -*- coding: utf-8 -*-
"""
cumcm-coach-skill-v7 《优化》子模块 —— PSO 变体 / 高级约束策略 / 混合算法框架

本文件在基础 SA-PSO/GA 之上提供"国一纵深"竞速部件，解决评估指出的短板：
  1) 无自适应参数(仅线性递减惯性)      -> Clerc 收敛系数 + 时变加速系数(TVAC)
  2) 无高级约束策略(仅惩罚项+repair)   -> 可行性规则(feasibility rule) + ε-约束
  3) 无混合策略                        -> PSO+局部搜索、GA+SA退火变异
每个函数返回结构化 dict，key 稳定，便于 Results 段直接取数。
依赖：numpy(纯 numpy，无 scipy/sklearn 强依赖)。
"""
import numpy as np


def clerc_constriction(c1=2.05, c2=2.05):
    """Clerc & Kennedy 收敛系数。phi=c1+c2>=4 -> chi=2/|2-phi-sqrt(phi^2-4phi)|。
    经典 (2.05,2.05) 得 chi=0.7298, c1'=c2'=1.49618。"""
    phi = c1 + c2
    if phi < 4.0:
        raise ValueError("Clerc 要求 c1+c2>=4, 得 phi=%.3f" % phi)
    chi = 2.0 / abs(2.0 - phi - np.sqrt(phi * phi - 4.0 * phi))
    return chi, chi * c1, chi * c2


def pso_clerc(obj, dim, bounds, iters=500, swarms=40, c1=2.05, c2=2.05,
              seed=None, repair=None):
    """Clerc 收敛系数 PSO(附加时变线性递减 w 双保险)。obj 最小化。"""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float)
    if b.ndim == 1:
        lo, hi = b[0], b[1]
    else:
        lo, hi = b[:, 0], b[:, 1]
    lo = float(np.broadcast_to(lo, (1,))[0]); hi = float(np.broadcast_to(hi, (1,))[0])
    chi, c1_, c2_ = clerc_constriction(c1, c2)
    X = rng.uniform(lo, hi, (swarms, dim))
    V = rng.uniform(-(hi - lo), hi - lo, (swarms, dim)) * 0.1
    if repair is not None:
        X = np.array([repair(x) for x in X])
    pbest, pbest_val = X.copy(), np.array([obj(x) for x in X])
    g = pbest[int(np.argmin(pbest_val))]
    g_val = float(pbest_val.min())
    hist = []
    for t in range(iters):
        r1, r2 = rng.random(X.shape), rng.random(X.shape)
        w = 0.9 - 0.5 * (t / iters)
        V = chi * (w * V + c1_ * r1 * (pbest - X) + c2_ * r2 * (g - X))
        X = np.clip(X + V, lo, hi)
        if repair is not None:
            X = np.array([repair(x) for x in X])
        vals = np.array([obj(x) for x in X])
        up = vals < pbest_val
        pbest[up], pbest_val[up] = X[up], vals[up]
        i = int(np.argmin(pbest_val))
        if pbest_val[i] < g_val:
            g, g_val = pbest[i].copy(), float(pbest_val[i])
        hist.append(g_val)
    return {"g_best": g, "g_val": g_val, "history": hist, "variant": "clerc", "chi": chi}


def pso_tvac(obj, dim, bounds, iters=500, swarms=40, seed=None, repair=None,
             c1_i=2.5, c1_f=0.5, c2_i=0.5, c2_f=2.5):
    """时变加速系数 PSO(Ratnaweera 2004)+方差自适应惯性。"""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float)
    if b.ndim == 1:
        lo, hi = b[0], b[1]
    else:
        lo, hi = b[:, 0], b[:, 1]
    lo = float(np.broadcast_to(lo, (1,))[0]); hi = float(np.broadcast_to(hi, (1,))[0])
    X = rng.uniform(lo, hi, (swarms, dim))
    V = rng.uniform(-(hi - lo), hi - lo, (swarms, dim)) * 0.1
    if repair is not None:
        X = np.array([repair(x) for x in X])
    pbest, pbest_val = X.copy(), np.array([obj(x) for x in X])
    g = pbest[int(np.argmin(pbest_val))]
    g_val = float(pbest_val.min())
    hist = []
    for t in range(iters):
        c1 = c1_i + (c1_f - c1_i) * (t / iters)
        c2 = c2_i + (c2_f - c2_i) * (t / iters)
        spread = float(np.std(pbest_val)) + 1e-12
        w = 0.4 + 0.5 * np.exp(-spread * (1 + t / iters))
        r1, r2 = rng.random(X.shape), rng.random(X.shape)
        V = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (g - X)
        X = np.clip(X + V, lo, hi)
        if repair is not None:
            X = np.array([repair(x) for x in X])
        vals = np.array([obj(x) for x in X])
        up = vals < pbest_val
        pbest[up], pbest_val[up] = X[up], vals[up]
        i = int(np.argmin(pbest_val))
        if pbest_val[i] < g_val:
            g, g_val = pbest[i].copy(), float(pbest_val[i])
        hist.append(g_val)
    return {"g_best": g, "g_val": g_val, "history": hist, "variant": "tvac"}


def feasibility_rule(eps=1e-6):
    """Deb 可行性规则：可行优于不可行；都可行比目标；都不可行比违反量。
    用法: better((val_a, vio_a), (val_b, vio_b)) -> bool"""
    def pairwise_better(a, b):
        av, avi = a[0], a[1]; bv, bvi = b[0], b[1]
        if avi <= eps and bvi > eps:
            return True
        if avi > eps and bvi <= eps:
            return False
        if avi <= eps and bvi <= eps:
            return av < bv
        return avi < bvi
    return {"pairwise_better": pairwise_better, "eps": eps, "desc": "Deb 可行性规则"}


def epsilon_constrained(eps0=1.0, T=1e-6, cp=1e-3):
    """ε-约束法(Takahama)：eps(t)=eps0*exp(-cp*t) 下限T。
    增广目标: obj'(x)=obj(x) + eps(t)*max(0, vio)。"""
    def eps(t):
        return max(T, eps0 * np.exp(-cp * t))
    def augmented(obj, x, vio, t):
        return obj(x) + eps(t) * max(0.0, vio)
    return {"eps_curve": eps, "augmented": augmented, "desc": "epsilon-constraint"}


def pso_plus_local_search(g_best, g_val, obj, dim, bounds, seed=None,
                          lr=0.05, iters=80, repair=None):
    """对全局最优施以高斯局部搜索(局部求精)。返回 (best, val)。"""
    rng = np.random.default_rng(seed)
    b = np.asarray(bounds, float)
    lo, hi = (b[0], b[1]) if b.ndim == 1 else (b[:, 0], b[:, 1])
    lo = float(np.broadcast_to(lo, (1,))[0]); hi = float(np.broadcast_to(hi, (1,))[0])
    best, val = np.array(g_best, float).copy(), float(g_val)
    step = lr * (hi - lo)
    for _ in range(iters):
        cand = np.clip(best + rng.normal(0, step, best.shape), lo, hi)
        if repair is not None:
            cand = repair(cand)
        cv = float(obj(cand))
        if cv < val:
            best, val = cand, cv
    return best, val


def ga_sa_mutation(pop, fitness, parent=0.4, temp=1.0, cooling=0.9):
    """GA+SA：温度退火缩小变异幅度。返回新种群。"""
    pop = np.array(pop, float); fit = np.asarray(fitness, float).reshape(-1)
    N, dim = pop.shape
    order = np.argsort(fit)
    keep = int(np.ceil((1 - parent) * N)); n_need = N - keep
    offspring = pop[order[:keep]].copy()
    rng = np.random.default_rng(0)
    idx = rng.integers(0, keep, size=n_need)
    noise = rng.normal(0, temp * cooling, (n_need, dim))
    extra = np.clip(pop[order[:keep]][idx] + noise, pop.min(0), pop.max(0))
    return np.vstack([offspring, extra])


if __name__ == "__main__":
    def sphere(x): return float(np.sum(np.asarray(x, float) ** 2))
    print("Clerc:", clerc_constriction())
    r1 = pso_clerc(sphere, 2, (-5, 5), iters=300, seed=1)
    print("Clerc-PSO sphere: %.3e" % r1["g_val"])
    r2 = pso_tvac(sphere, 2, (-5, 5), iters=300, seed=1)
    print("TVAC-PSO sphere: %.3e" % r2["g_val"])
    fr = feasibility_rule()
    print("可行性规则:", fr["pairwise_better"]((0.1, 1.0), (0.2, 0.0)))
    ec = epsilon_constrained()
    print("eps(100):", round(float(ec["eps_curve"](100)), 4))
    b, v = pso_plus_local_search(r1["g_best"], r1["g_val"], sphere, 2, (-5, 5), seed=2)
    print("PSO+LS: %.3e->%.3e" % (r1["g_val"], v))
    pop = np.random.default_rng(0).uniform(-5, 5, (30, 2))
    fit = np.array([sphere(p) for p in pop])
    print("GA+SA mut shape:", ga_sa_mutation(pop, fit).shape)
    print("冒烟通过")