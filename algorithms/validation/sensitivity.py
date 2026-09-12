"""
Sensitivity: 灵敏度分析
=======================================
用于四重检验 §6.2 灵敏度: 参数 ±10%/±20% + 弹性系数分级。

特点：
- 对每个参数做 ±10%/±20% 扰动，计算输出变化率
- 弹性系数 ε = (ΔY/Y) / (ΔX/X)，分级：高 |ε|>0.8 / 中 0.3<|ε|<0.8 / 低 |ε|<0.3
- 龙卷风图可视化

参数说明：
- model_func: 模型函数，接收 params dict，返回标量（数组取首元素）
- base_params: 基准参数 dict {name: value}
- perturbations: 扰动比例元组，默认 (0.1, 0.2)

用法：
    from sensitivity import SensitivityAnalyzer

    sa = SensitivityAnalyzer(model_func, base_params)
    sa.analyze()
    sa.plot_tornado('tornado.png')
"""

from typing import Callable

import matplotlib.pyplot as plt
import numpy as np


class SensitivityAnalyzer:
    """单因素灵敏度分析（局部扰动法）"""

    def __init__(
        self,
        model_func: Callable[[dict], float],
        base_params: dict,
        perturbations: tuple[float, ...] = (0.1, 0.2)
    ):
        self.model_func = model_func
        self.base_params = dict(base_params)
        self.perturbations = perturbations
        self.base_output = None
        self.results = {}

    def _eval(self, params: dict) -> float:
        out = self.model_func(dict(params))
        return float(np.asarray(out).ravel()[0])

    def analyze(self) -> dict:
        """执行灵敏度分析，返回 {参数名: {elasticity, grade, ...}}"""
        self.base_output = self._eval(self.base_params)
        self.results = {}

        for name, base_val in self.base_params.items():
            for pct in self.perturbations:
                delta = base_val * pct
                up = dict(self.base_params)
                up[name] = base_val + delta
                down = dict(self.base_params)
                down[name] = base_val - delta

                y_up = self._eval(up)
                y_down = self._eval(down)

                # 相对变化率（规避除零）
                y0 = self.base_output if abs(self.base_output) > 1e-10 else 1.0
                rel_y_up = (y_up - self.base_output) / y0
                rel_y_down = (y_down - self.base_output) / y0
                # 中心差分弹性系数
                elasticity = (rel_y_up - rel_y_down) / (2 * pct)

                self.results[(name, pct)] = {
                    'y_up': y_up, 'y_down': y_down,
                    'elasticity': elasticity,
                    'change_up': rel_y_up, 'change_down': rel_y_down,
                }
        return self.results

    def elasticity_summary(self) -> dict:
        """每个参数取最大扰动档的弹性系数并分级"""
        summary = {}
        for name in self.base_params:
            eps = max(
                (self.results[(name, p)]['elasticity'] for p in self.perturbations),
                key=abs
            )
            grade = '高' if abs(eps) > 0.8 else ('中' if abs(eps) > 0.3 else '低')
            summary[name] = {'elasticity': eps, 'grade': grade}
        return summary

    def plot_tornado(self, save_path: str = None):
        """龙卷风图（横向条形，按影响幅度排序）"""
        max_p = max(self.perturbations)
        rows = []
        for name in self.base_params:
            r = self.results[(name, max_p)]
            rows.append((name, r['change_down'] * 100, r['change_up'] * 100))

        rows.sort(key=lambda r: abs(r[2] - r[1]))
        names = [r[0] for r in rows]
        lows = [r[1] for r in rows]
        highs = [r[2] for r in rows]

        y = np.arange(len(names))
        left = [min(lo, hi) for lo, hi in zip(lows, highs)]
        width = [abs(hi - lo) for lo, hi in zip(lows, highs)]

        fig, ax = plt.subplots(figsize=(10, max(4, 0.6 * len(names))))
        ax.barh(y, width, left=left, color='#2166AC', edgecolor='k', alpha=0.8)

        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=12)
        ax.set_xlabel('输出变化率 (%)', fontsize=12)
        ax.set_title(f'灵敏度龙卷风图(±{int(max_p * 100)}%)', fontsize=14)
        ax.axvline(0, color='k', linewidth=1)
        ax.grid(True, alpha=0.3, axis='x')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()


def demo():
    """示例：线性模型 y = a*x1 + b*x2^2 + c"""
    def model(p):
        return p['a'] * 3.0 + p['b'] * 4.0 ** 2 + p['c']

    base = {'a': 2.0, 'b': 0.5, 'c': 1.0}

    sa = SensitivityAnalyzer(model, base)
    sa.analyze()
    summary = sa.elasticity_summary()

    print("弹性系数分级:")
    for name, info in summary.items():
        print(f"  {name}: ε={info['elasticity']:.3f} ({info['grade']})")

    sa.plot_tornado('tornado.png')


if __name__ == '__main__':
    demo()
