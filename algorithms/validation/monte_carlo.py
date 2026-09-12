"""
MonteCarlo: 蒙特卡洛模拟
=======================================
用于四重检验 §6.3 蒙特卡洛: ≥200次 + 均值/标准差/CV/95%CI。

增强(2026-08, 四重检验深化):
  1) 分位数分析: quantiles(5/50/95 及任意分位)
  2) 收敛性诊断: 标准误差随样本量演化 + 是否稳定
  3) 分布假设标注: dist_type 写入统计, 便于论文明示依据
  4) 明确 uniform/normal/log-normal/三角(triangle) 分布支持

参数说明：
- sim_func: 仿真函数，接收采样参数 dict，返回标量
- dist_params: 输入分布定义
    {'x': {'dist': 'normal',  'mean': 10, 'std': 1}}
    {'x': {'dist': 'uniform', 'low': 0, 'high': 1}}        (或 min/max)
    {'x': {'dist': 'lognormal','mean': 1.0,'std': 0.3,'base':10}}   (几何均值/几何标准差)
    {'x': {'dist': 'triangle','low': 0,'mode': 0.5,'high': 1}}
    （缺省 dist 视为 normal）

用法：
    from monte_carlo import MonteCarlo
    mc = MonteCarlo(sim_func, dist_params)
    mc.run(n=200, seed=42)
    stats = mc.statistics()          # 含 quantiles / convergence
    mc.plot_distribution('mc.png')
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Dict, Optional


class MonteCarlo:
    """蒙特卡洛模拟器"""

    def __init__(self, sim_func: Callable[[Dict], float], dist_params: Dict):
        self.sim_func = sim_func
        self.dist_params = dist_params
        self.samples = None
        self._dist_types = {name: spec.get('dist', 'normal')
                            for name, spec in dist_params.items()}

    def _sample_one(self) -> Dict:
        """按分布定义采样一组参数"""
        params = {}
        for name, spec in self.dist_params.items():
            kind = spec.get('dist', 'normal')
            if kind == 'uniform':
                lo, hi = spec['low'], spec.get('high', spec.get('max'))
                params[name] = np.random.uniform(lo, hi)
            elif kind == 'lognormal':
                gmu = spec.get('mean', 1.0)
                gsd = spec.get('std', 0.3)
                base = spec.get('base', 0.0)
                params[name] = base + np.random.lognormal(gmu, gsd)
            elif kind == 'triangle':
                lo = spec.get('low', 0.0)
                hi = spec.get('high', 1.0)
                mode = spec.get('mode', (lo + hi) / 2.0)
                params[name] = np.random.triangular(lo, mode, hi)
            else:  # normal 缺省
                params[name] = np.random.normal(spec['mean'], spec['std'])
        return params

    def run(self, n: int = 200, seed: int = 42) -> np.ndarray:
        """采样 n 次并仿真，返回输出样本数组"""
        np.random.seed(seed)
        out = []
        for _ in range(n):
            params = self._sample_one()
            val = self.sim_func(params)
            out.append(float(np.asarray(val).ravel()[0]))
        self.samples = np.array(out)
        return self.samples

    def quantiles(self, qs: Optional[list] = None) -> Dict:
        """分位数分析: 默认 5/50/95 分位，另含 min/max。"""
        if self.samples is None:
            raise ValueError("请先调用 run()")
        qs = qs if qs is not None else [0.05, 0.50, 0.95]
        return {('q%.0f' % (q * 100)): float(np.percentile(self.samples, q * 100))
                for q in qs}

    def convergence_diag(self, group=None) -> Dict:
        """收敛性诊断: 随样本量累积的均值与标准误(SE)是否趋于稳定。

        - 累积均值 mean_t 随 t 波动幅度越来越小 -> 收敛
        - SE = std/sqrt(t) 单调下降趋于 0
        返回 dict{ cum_mean_end, cum_se_end, final_se, stable_ratio, groups }。
        stable_ratio: 后 1/3 累计均值的极差 / 总均值，越小越收敛(经验阈值 <2%)。
        """
        if self.samples is None:
            raise ValueError("请先调用 run()")
        s = np.asarray(self.samples, float)
        n = len(s)
        g = group or max(int(n / 20), 5)
        cum_mean = np.convolve(s, np.ones(g) / g, mode='valid')
        se_t = lambda t: float(np.std(s[:t + 1], ddof=1) / np.sqrt(t + 1))
        final = np.arange(g, n, g)  # 抽样检查的累积长度
        tail = cum_mean[-max(int(len(cum_mean) / 3), 1):]
        span = float(tail.max() - tail.min())
        scale = float(abs(np.mean(s))) if abs(np.mean(s)) > 1e-10 else 1.0
        return {
            'cum_mean_end': float(cum_mean[-1]),
            'cum_se_end': se_t(n - 1),
            'final_se': se_t(n - 1),
            'stable_ratio': span / scale,
            'n': n,
            'tail_len': int(len(tail)),
            'converged': bool(span / scale < 0.02),
        }

    def statistics(self) -> Dict:
        """输出统计量: 均值/标准差/CV/95%CI/分位数/分布标注/收敛诊断。"""
        if self.samples is None:
            raise ValueError("请先调用 run()")
        s = self.samples
        mean = float(np.mean(s))
        std = float(np.std(s, ddof=1))
        cv = std / abs(mean) if abs(mean) > 1e-10 else float('nan')
        ci_lo = float(np.percentile(s, 2.5))
        ci_hi = float(np.percentile(s, 97.5))
        st = self.statistics  # placeholder (unused)
        return {
            'mean': mean, 'std': std, 'cv': cv,
            'ci_95': (ci_lo, ci_hi), 'n': len(s),
            'quantiles': self.quantiles(),
            'convergence': self.convergence_diag(),
            'dist_spec': self._dist_types,
            'dist_statement': self._dist_statement(),
        }

    def _dist_statement(self) -> str:
        """生成可直接写进论文的分布假设说明。"""
        parts = {}
        for name, kind in self._dist_types.items():
            spec = self.dist_params[name]
            if kind == 'normal':
                parts[name] = 'N(%.4g, %.4g^2)' % (spec.get('mean', 0), spec.get('std', 1))
            elif kind == 'uniform':
                parts[name] = 'U[%.4g, %.4g]' % (spec.get('low', 0),
                                                 spec.get('high', spec.get('max', 1)))
            elif kind == 'lognormal':
                parts[name] = 'LogN(mu=%.4g, sigma=%.4g)' % (
                    spec.get('mean', 1), spec.get('std', 0.3))
            elif kind == 'triangle':
                parts[name] = 'Tri(%.4g, %.4g, %.4g)' % (
                    spec.get('low', 0), spec.get('mode', 0.5),
                    spec.get('high', spec.get('max', 1)))
            else:
                parts[name] = kind
        return '、'.join('%s~%s' % (k, v) for k, v in parts.items())

    def plot_distribution(self, save_path: Optional[str] = None):
        """直方图 + CDF"""
        if self.samples is None:
            raise ValueError("请先调用 run()")
        s = self.samples

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.hist(s, bins=30, edgecolor='k', alpha=0.7, color='#2166AC')
        ax1.axvline(np.mean(s), color='r', linestyle='--', linewidth=1.5,
                    label=f'均值={np.mean(s):.3f}')
        ax1.axvline(np.percentile(s, 5), color='g', linestyle=':', linewidth=1.2,
                    label=f'q5={np.percentile(s, 5):.3f}')
        ax1.axvline(np.percentile(s, 95), color='g', linestyle=':', linewidth=1.2,
                    label=f'q95={np.percentile(s, 95):.3f}')
        ax1.set_xlabel('输出值', fontsize=12)
        ax1.set_ylabel('频数', fontsize=12)
        ax1.set_title('蒙特卡洛分布(含 5/95 分位)', fontsize=14)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        sorted_s = np.sort(s)
        cdf = np.arange(1, len(sorted_s) + 1) / len(sorted_s)
        ax2.plot(sorted_s, cdf, 'b-', linewidth=2)
        ax2.axvline(np.percentile(s, 2.5), color='r', linestyle='--', linewidth=1, label='2.5%')
        ax2.axvline(np.percentile(s, 97.5), color='r', linestyle='--', linewidth=1, label='97.5%')
        ax2.set_xlabel('输出值', fontsize=12)
        ax2.set_ylabel('累积概率', fontsize=12)
        ax2.set_title('累积分布函数(CDF)', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")
        else:
            plt.show()


def demo():
    """示例：仿真 y = 2*x1 + x2^2，x1~N(10,1)，x2~U(0,3)"""
    def sim(p):
        return 2.0 * p['x1'] + p['x2'] ** 2

    dist = {
        'x1': {'dist': 'normal', 'mean': 10, 'std': 1},
        'x2': {'dist': 'uniform', 'low': 0, 'high': 3},
    }

    mc = MonteCarlo(sim, dist)
    mc.run(n=200, seed=42)
    stats = mc.statistics()

    print("蒙特卡洛统计量:")
    print(f"  均值={stats['mean']:.4f}, 标准差={stats['std']:.4f}, CV={stats['cv']:.4f}")
    print(f"  95%CI = ({stats['ci_95'][0]:.4f}, {stats['ci_95'][1]:.4f})")
    print("  分位数:", {k: round(v, 4) for k, v in stats['quantiles'].items()})
    print("  收敛诊断:", stats['convergence']['converged'],
          "stable_ratio=%.4f" % stats['convergence']['stable_ratio'])
    print("  分布假设:", stats['dist_statement'])

    mc.plot_distribution('mc.png')


if __name__ == '__main__':
    demo()