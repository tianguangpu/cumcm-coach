"""
AHP + 熵权 + TOPSIS 综合评价流程
=======================================
用于多指标综合评价、方案排序问题。

流程：
1. AHP 层次分析法确定主观权重
2. 熵权法确定客观权重
3. 组合赋权得到综合权重
4. TOPSIS 进行方案排序

用法：
    from ahp_entropy_topsis import ComprehensiveEvaluation

    ce = ComprehensiveEvaluation(data, benefit_cols, cost_cols)
    ce.run_ahp(pairwise_matrix)
    ce.run_entropy()
    ce.combine_weights(alpha=0.5)
    scores = ce.topsis()
"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np


class ComprehensiveEvaluation:
    """综合评价类"""

    def __init__(
        self,
        data: np.ndarray,
        benefit_cols: list[int],
        cost_cols: list[int],
        col_names: Optional[list[str]] = None
    ):
        """
        初始化

        Args:
            data: 数据矩阵 (n_samples, n_features)
            benefit_cols: 效益型指标索引列表（值越大越好）
            cost_cols: 成本型指标索引列表（值越小越好）
            col_names: 指标名称列表
        """
        self.data = np.array(data, dtype=float)
        self.n_samples, self.n_features = self.data.shape
        self.benefit_cols = benefit_cols
        self.cost_cols = cost_cols
        self.col_names = col_names or [f'指标{i+1}' for i in range(self.n_features)]

        self.weights_ahp = None
        self.weights_entropy = None
        self.weights_combined = None
        self.cr = None  # 一致性比率

    def normalize(self) -> np.ndarray:
        """标准化数据（极值标准化）"""
        normalized = np.zeros_like(self.data)

        for j in range(self.n_features):
            min_val = self.data[:, j].min()
            max_val = self.data[:, j].max()

            if j in self.benefit_cols:
                # 效益型：越大越好
                normalized[:, j] = (self.data[:, j] - min_val) / (max_val - min_val + 1e-10)
            else:
                # 成本型：越小越好
                normalized[:, j] = (max_val - self.data[:, j]) / (max_val - min_val + 1e-10)

        return normalized

    def run_ahp(self, pairwise_matrix: np.ndarray) -> np.ndarray:
        """
        AHP 层次分析法计算权重

        Args:
            pairwise_matrix: 判断矩阵 (n_features, n_features)

        Returns:
            权重向量
        """
        A = np.array(pairwise_matrix)
        n = A.shape[0]

        # 列归一化
        A_norm = A / A.sum(axis=0)

        # 权重（行平均）
        self.weights_ahp = A_norm.mean(axis=1)

        # 一致性检验
        # 最大特征值
        eigenvalues = np.linalg.eigvals(A)
        lambda_max = np.max(np.abs(eigenvalues))

        # 一致性指标
        CI = (lambda_max - n) / (n - 1)

        # 随机一致性指标（查表）
        RI_dict = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
                   6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
        RI = RI_dict.get(n, 1.5)

        # 一致性比率
        self.cr = CI / RI

        print(f"AHP 权重: {self.weights_ahp}")
        print(f"一致性比率 CR = {self.cr:.4f} {'< 0.1，通过检验' if self.cr < 0.1 else '>= 0.1，需调整判断矩阵'}")

        return self.weights_ahp

    def run_entropy(self) -> np.ndarray:
        """
        熵权法计算权重

        Returns:
            权重向量
        """
        # 标准化
        normalized = self.normalize()

        # 避免取对数时出现 0
        normalized = np.clip(normalized, 1e-10, 1 - 1e-10)

        # 计算 p_ij
        p = normalized / normalized.sum(axis=0)

        # 计算熵值
        E = -np.sum(p * np.log(p), axis=0) / np.log(self.n_samples)

        # 计算权重
        d = 1 - E
        self.weights_entropy = d / d.sum()

        print(f"熵权法权重: {self.weights_entropy}")

        return self.weights_entropy

    def combine_weights(self, alpha: float = 0.5) -> np.ndarray:
        """
        组合赋权

        Args:
            alpha: 主观权重偏好系数 (0-1)

        Returns:
            组合权重
        """
        if self.weights_ahp is None or self.weights_entropy is None:
            raise ValueError("请先运行 run_ahp() 和 run_entropy()")

        self.weights_combined = alpha * self.weights_ahp + (1 - alpha) * self.weights_entropy
        self.weights_combined /= self.weights_combined.sum()

        print(f"组合权重 (alpha={alpha}): {self.weights_combined}")

        return self.weights_combined

    def topsis(self) -> np.ndarray:
        """
        TOPSIS 方法排序

        Returns:
            综合得分向量
        """
        # 标准化
        normalized = self.normalize()

        # 加权规范化矩阵
        weighted = normalized * self.weights_combined

        # 正理想解和负理想解
        v_pos = weighted.max(axis=0)
        v_neg = weighted.min(axis=0)

        # 计算距离
        d_pos = np.sqrt(np.sum((weighted - v_pos) ** 2, axis=1))
        d_neg = np.sqrt(np.sum((weighted - v_neg) ** 2, axis=1))

        # 综合得分
        scores = d_neg / (d_pos + d_neg + 1e-10)

        print("\nTOPSIS 综合得分:")
        for i, score in enumerate(scores):
            print(f"  方案{i+1}: {score:.4f}")

        return scores

    def plot_weights(self, save_path: str = None):
        """绘制权重对比图"""
        fig, ax = plt.subplots(figsize=(10, 6))

        x = np.arange(self.n_features)
        width = 0.25

        ax.bar(x - width, self.weights_ahp, width, label='AHP权重', color='#2166AC')
        ax.bar(x, self.weights_entropy, width, label='熵权重', color='#D6604D')
        ax.bar(x + width, self.weights_combined, width, label='组合权重', color='#4DAF4A')

        ax.set_xlabel('指标', fontsize=12)
        ax.set_ylabel('权重', fontsize=12)
        ax.set_title('三种权重方法对比', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(self.col_names, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()

    def plot_radar(self, scores: np.ndarray, save_path: str = None):
        """绘制雷达图"""
        # 标准化原始数据用于雷达图
        normalized = self.normalize()

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})

        angles = np.linspace(0, 2 * np.pi, self.n_features, endpoint=False).tolist()
        angles += angles[:1]

        colors = plt.cm.Set2(np.linspace(0, 1, self.n_samples))

        for i in range(self.n_samples):
            values = normalized[i, :].tolist()
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=2, label=f'方案{i+1}', color=colors[i])
            ax.fill(angles, values, alpha=0.1, color=colors[i])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.col_names)
        ax.set_title('方案对比雷达图', fontsize=14, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"[Saved] {save_path}")

        plt.show()


def demo():
    """示例"""
    # 示例数据
    data = np.array([
        [85, 90, 78, 92, 88],  # 方案1
        [90, 85, 82, 88, 90],  # 方案2
        [78, 92, 85, 90, 85],  # 方案3
        [88, 88, 80, 85, 92],  # 方案4
    ])

    # 假设所有指标都是效益型
    benefit_cols = [0, 1, 2, 3, 4]
    cost_cols = []

    col_names = ['效率', '质量', '稳定性', '可维护性', '成本']

    ce = ComprehensiveEvaluation(data, benefit_cols, cost_cols, col_names)

    # AHP 判断矩阵（示例）
    pairwise = np.array([
        [1, 1, 3, 3, 5],
        [1, 1, 3, 3, 5],
        [1/3, 1/3, 1, 1, 3],
        [1/3, 1/3, 1, 1, 3],
        [1/5, 1/5, 1/3, 1/3, 1]
    ])

    ce.run_ahp(pairwise)
    ce.run_entropy()
    ce.combine_weights(alpha=0.5)
    scores = ce.topsis()

    ce.plot_weights('weights_comparison.png')
    ce.plot_radar(scores, 'radar_comparison.png')


if __name__ == '__main__':
    demo()
