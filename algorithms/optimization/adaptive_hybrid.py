"""自适应混合优化器 (Adaptive Hybrid Optimizer, AHO)"""


import numpy as np


class AdaptiveHybrid:
    """v7 原创算法，融合 PSO/DE/SA 三大优势"""

    def __init__(self, objective, bounds, pop_size=50, max_iter=200, seed=42):
        self.objective = objective
        self.bounds = np.array(bounds)
        self.dim = len(bounds)
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.seed = seed
        self.w, self.c1, self.c2 = 0.7, 1.5, 1.5
        self.F, self.CR = 0.5, 0.9
        self.T0, self.T_min, self.alpha = 100, 0.01, 0.95
        self.best_solution = None
        self.best_fitness = float('inf')
        self.history = []

    def solve(self, verbose=False):
        rng = np.random.default_rng(self.seed)
        pop = rng.uniform(self.bounds[:,0], self.bounds[:,1], (self.pop_size, self.dim))
        fitness = np.array([self.objective(x) for x in pop])
        velocities = rng.uniform(-1, 1, (self.pop_size, self.dim))
        personal_best = pop.copy()
        personal_best_fitness = fitness.copy()
        best_idx = np.argmin(fitness)
        global_best = pop[best_idx].copy()
        global_best_fitness = fitness[best_idx]
        T = self.T0
        n_eval = self.pop_size
        stagnation = 0

        for it in range(self.max_iter):
            center = np.mean(pop, axis=0)
            diversity = np.mean(np.sqrt(np.sum((pop - center)**2, axis=1))) / np.sqrt(np.sum((self.bounds[:,1]-self.bounds[:,0])**2))

            if diversity < 0.1:
                for i in range(self.pop_size):
                    idxs = [j for j in range(self.pop_size) if j != i]
                    a, b, c = rng.choice(idxs, 3, replace=False)
                    mutant = pop[a] + self.F * (pop[b] - pop[c])
                    trial = pop[i].copy()
                    j_rand = rng.integers(0, self.dim)
                    for j in range(self.dim):
                        if rng.random() < self.CR or j == j_rand:
                            trial[j] = mutant[j]
                    trial = np.clip(trial, self.bounds[:,0], self.bounds[:,1])
                    tf = self.objective(trial)
                    n_eval += 1
                    if tf < fitness[i]:
                        pop[i] = trial
                        fitness[i] = tf
                strategy = 'DE'
            else:
                r1 = rng.random((self.pop_size, self.dim))
                r2 = rng.random((self.pop_size, self.dim))
                velocities = self.w*velocities + self.c1*r1*(personal_best-pop) + self.c2*r2*(global_best-pop)
                pop = np.clip(pop + velocities, self.bounds[:,0], self.bounds[:,1])
                fitness = np.array([self.objective(x) for x in pop])
                n_eval += self.pop_size
                strategy = 'PSO'

            improved = fitness < personal_best_fitness
            personal_best[improved] = pop[improved]
            personal_best_fitness[improved] = fitness[improved]
            min_idx = np.argmin(fitness)
            if fitness[min_idx] < global_best_fitness:
                global_best = pop[min_idx].copy()
                global_best_fitness = fitness[min_idx]
                stagnation = 0
            else:
                stagnation += 1

            if stagnation >= 5:
                perturbed = global_best + rng.normal(0, T/self.T0*0.1, self.dim) * (self.bounds[:,1]-self.bounds[:,0])
                perturbed = np.clip(perturbed, self.bounds[:,0], self.bounds[:,1])
                pf = self.objective(perturbed)
                n_eval += 1
                if pf < global_best_fitness:
                    global_best = perturbed
                    global_best_fitness = pf
                T = max(self.T_min, T * self.alpha)
                stagnation = 0
                strategy = 'SA'

            self.history.append({'iter': it, 'best': global_best_fitness, 'diversity': diversity, 'strategy': strategy})
            if verbose and it % 10 == 0:
                print(f'迭代 {it:4d}: 最优值={global_best_fitness:.6f}, 策略={strategy}')

        self.best_solution = global_best
        self.best_fitness = global_best_fitness
        return {'f_opt': global_best_fitness, 'x_opt': global_best.tolist(), 'n_eval': n_eval, 'history': self.history}


if __name__ == '__main__':
    def rastrigin(x):
        return 10*len(x) + sum(xi**2 - 10*np.cos(2*np.pi*xi) for xi in x)

    print('='*60)
    print('自适应混合优化器 (AHO) 演示')
    print('测试函数: Rastrigin (5维)')
    print('='*60)

    opt = AdaptiveHybrid(rastrigin, [(-5.12,5.12)]*5, pop_size=50, max_iter=100, seed=42)
    result = opt.solve(verbose=True)
    print(f'最优值: {result["f_opt"]:.6f}')
    print(f'最优解: {[round(x,4) for x in result["x_opt"]]}')
    print(f'评估次数: {result["n_eval"]}')
    print('理论最优: 0.0')
