# -*- coding: utf-8 -*-
"""test_polish_v2.py — polish_text.py v2.0 单元测试"""
import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(__file__))
from polish_text import detect, burstiness, char_entropy, word_entropy, paragraph_symmetry

def test_human_like_text():
    """测试：人类风格文本应得分较高（低AI味）。"""
    text = """
    数据质量是建模的基础。我们先看原始数据。
    缺失值占比3.2%，不算高，但分布有偏——集中在周末。
    这很合理。工作日录入规范，周末值班人员少。
    异常值检测用箱线图法。Q1-1.5IQR到Q3+1.5IQR之外的都标记。
    共发现47个异常点。逐个核查后，28个是录入错误，19个是真实极端值。
    保留真实极端值，修正录入错误。数据清洗完成。
    """
    rep = detect(text)
    print("=== 人类风格文本 ===")
    print(f"  Burstiness: {rep['burstiness']}  [{rep['burstiness评级']}]")
    print(f"  字符熵: {rep['字符熵']}  [{rep['熵评级']}]")
    print(f"  段落对称性: {rep['段落对称性']}  [{rep['对称性评级']}]")
    print(f"  AI味综合分: {rep['AI味综合分']}")
    assert rep['burstiness'] > 0.3, f"Burstiness应>0.3, 实际={rep['burstiness']}"
    assert rep['AI味综合分'] >= 50, f"人类文本AI味应>=50, 实际={rep['AI味综合分']}"
    print("  ✓ 通过\n")

def test_ai_like_text():
    """测试：AI风格文本应得分较低（高AI味）。"""
    text = """
    综上所述，本文基于多层次分析框架，系统性地探讨了该问题。
    首先，进行了数据预处理，显著地提高了数据质量。
    其次，进行了特征工程，极大地提升了模型性能。
    最后，进行了模型优化，进一步提高了预测精度。
    值得注意的是，本方法具有重要的理论意义和实践价值。
    从上述分析可以看出，该方法在多个指标上均优于基线模型。
    与此同时，在此基础上，本文提出了改进方案。
    总而言之，本研究为该领域提供了新的思路和方法。
    """
    rep = detect(text)
    print("=== AI风格文本 ===")
    print(f"  Burstiness: {rep['burstiness']}  [{rep['burstiness评级']}]")
    print(f"  字符熵: {rep['字符熵']}  [{rep['熵评级']}]")
    print(f"  AI用语: {rep['AI用语']}")
    print(f"  连接词: {rep['AI连接词']}")
    print(f"  AI味综合分: {rep['AI味综合分']}")
    assert rep['AI味综合分'] < 65, f"AI文本AI味应<65(不达标), 实际={rep['AI味综合分']}"
    print("  ✓ 通过\n")

def test_burstiness_function():
    """测试 burstiness 函数。"""
    # 非常均匀的句长（AI特征）
    uniform = [20, 21, 20, 22, 20, 21]
    b1 = burstiness(uniform)
    assert b1 < 0.15, f"均匀句长burstiness应<0.15, 实际={b1}"

    # 波动大的句长（人类特征）
    varied = [5, 30, 12, 25, 8, 20, 35, 10]
    b2 = burstiness(varied)
    assert b2 > 0.4, f"波动句长burstiness应>0.4, 实际={b2}"
    print(f"✓ burstiness: 均匀={b1}, 波动={b2}")

def test_entropy_function():
    """测试信息熵函数。"""
    # 重复文本（低熵）
    low = "数据数据数据数据数据数据数据数据"
    e1 = char_entropy(low)
    assert e1 < 3.0, f"重复文本熵应<3.0, 实际={e1}"

    # 多样文本（高熵）
    high = "基于随机森林的特征选择方法，通过计算基尼不纯度下降量评估各变量重要性"
    e2 = char_entropy(high)
    assert e2 > 4.0, f"多样文本熵应>4.0, 实际={e2}"
    print(f"✓ 熵: 重复={e1}, 多样={e2}")

def test_symmetry_function():
    """测试段落对称性函数。"""
    # 对称段落（AI特征）
    sym = [100, 102, 98, 101, 99]
    s1 = paragraph_symmetry(sym)
    assert s1 > 0.8, f"对称段落应>0.8, 实际={s1}"

    # 不对称段落（人类特征）
    asym = [50, 200, 80, 150, 30]
    s2 = paragraph_symmetry(asym)
    assert s2 < 0.5, f"不对称段落应<0.5, 实际={s2}"
    print(f"✓ 对称性: 对称={s1}, 不对称={s2}")


if __name__ == "__main__":
    print("polish_text.py v2.0 测试\n")
    test_burstiness_function()
    test_entropy_function()
    test_symmetry_function()
    test_human_like_text()
    test_ai_like_text()
    print("=" * 40)
    print("全部测试通过！")
