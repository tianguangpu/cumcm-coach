# -*- coding: utf-8 -*-
"""innovation_guide.py — 创新点生成机制重构 (P0-2)

废除旧的"强制创新点必须量化百分比"逻辑(易编造数字、抑制真创新)。
改为五类创新点, 每类带对应的证据要求与可验证方法:

  1. 模型结构创新  -> 须与经典模型理论对比 + 消融实验
  2. 算法改进创新  -> 须收敛速度/精度/稳定性量化对比 + 统计显著检验
  3. 问题分解创新  -> 须分解前后复杂度/精度对比
  4. 约束处理创新  -> 须约束满足率/可行性/计算代价对比
  5. 验证方法创新  -> 须说明对该题的独特价值(非堆指标)

并根据题型生成 3-5 条"具体的创新方向建议"(不是空泛的"改进模型"),
以及"强基线选择建议"(解决旧版贪心基线过弱的问题)。

用法:
    from algorithms.misc.innovation_guide import suggest_innovations, pick_strong_baseline
    plan = suggest_innovations(problem_type="B")   # A/B/C/D + 可传 problem_text
    base = pick_strong_baseline(problem_type="B")

输出 JSON: {
   categories: [...每类含 evidence_required / methods / rating],
   concrete_directions: [... 带预期收益的依据链],
   strong_baselines: [... 强基线候选: 用成熟求解器顶替弱贪心],
   anti_cheat_check: [... 防编造检查清单]
}
"""
import json
import os

# 每类创新点: 证据要求 + 建议验证方法
CATEGORIES = {
    "model_structure": {
        "label": "模型结构创新",
        "evidence": "与经典模型的理论对比(推导/极限情形) + 消融实验(去掉该结构后变差多少)",
        "methods": ["解析极限对比", "消融Ablation", "复杂度分析O(f(n))", "约束放松对偶分析"],
    },
    "algorithm": {
        "label": "算法改进创新",
        "evidence": "收敛速度/精度/稳定性(多次运行 std/CV)量化对比 + 统计显著检验(t检验/秩和)",
        "methods": ["收敛曲线", "多seed箱线图", "Mann-Whitney U", "收敛代数对比"],
    },
    "decomposition": {
        "label": "问题分解创新",
        "evidence": "分解前后的计算复杂度/求解精度对比(原整体 vs 分解子问题拼接)",
        "methods": ["复杂度对比", "拼接误差分析", "阶段间耦合性检验"],
    },
    "constraint": {
        "label": "约束处理创新",
        "evidence": "约束满足率/可行性/计算代价(与惩罚法/repair法对比)",
        "methods": ["可行解比例", "违反量分布", "时间对比", "ε约束法/可行性规则"],
    },
    "validation": {
        "label": "验证方法创新",
        "evidence": "说明对该题独特价值(如A题守恒验证、B题灵敏度→决策), 非堆指标",
        "methods": ["交叉验证", "Sobol全局灵敏度", "MC分布+收敛诊断", "Walk-forward"],
    },
}

# 题型 -> 具体可行创新方向 (带依据链)
DIRECTIONS = {
    "A": [
        {"dir": "PDE用2D坐标变换映射非规则几何", "why": "A题常含复杂形状; 映射避免全FDM", "evidence": "守恒误差+解析解对比"},
        {"dir": "物理量纲分析定位主导项, 再做渐近解析解", "why": "降低数值维度, 论文有理论深度", "evidence": "主导项残差最大项占比"},
        {"dir": "质量/能量守恒的全局守恒检查作为验证", "why": "A题珍视物理真实性", "evidence": "守恒残差<1e-6 曲线"},
        {"dir": "CFL稳定性自适应步长", "why": "兼顾精度与效率", "evidence": "时间开销+RMS误差权衡表"},
        {"dir": "隐式格式处理刚性项", "why": "避免显式步长过小", "evidence": "稳定域内允差增大"},
    ],
    "B": [
        {"dir": "用强基线(线性化/凸放松/专用求解器)做下限对照", "why": "弱贪心基线无说服力", "evidence": "gap vs 凸下界"},
        {"dir": "约束紧度分析找活跃约束, 定价/对偶解释", "why": "展示对问题本质理解", "evidence": "对偶乘子/影子价格表"},
        {"dir": "鲁棒/随机优化处理参数不确定", "why": "B题常涉价格产量扰动", "evidence": "决策对扰动的稳定性"},
        {"dir": "决策变量整数化处理不可分作物", "why": "贴近实际", "evidence": "整数解可行性与gap"},
        {"dir": "灵敏度→决策建议的因果链", "why": "让检验服务于决策", "evidence": "弹性系数结合资金分配"},
    ],
    "C": [
        {"dir": "指标体系构建逻辑(维度-准则-指标)可视化", "why": "C题核心是指标体系", "evidence": "指标相关性/区分度"},
        {"dir": "多方法权重(主观AHP+客观熵权)融合与稳定", "why": "避免单一赋权争议", "evidence": "权重排名Spearman相关"},
        {"dir": "与其他排序方法的排序一致性", "why": "稳健性证明", "evidence": "Kendall tau 矩阵"},
        {"dir": "敏感性: 权重扰动下排名是否翻转", "why": "评委关心鲁棒性", "evidence": "翻转阈值 + 扰动图"},
        {"dir": "去量纲/越权预处理及其影响", "why": "展示处理敏感度", "evidence": "标准化方式对比"},
    ],
    "D": [
        {"dir": "关键特征选择+与领域解释结合", "why": "数据题展示理解而非堆模型", "evidence": "特征重要性+业务映射"},
        {"dir": "时序Walk-forward验证而非单train/test", "why": "时序不可乱分", "evidence": "滚动窗口误差曲线"},
        {"dir": "外推(超样本范围)风险评估", "why": "数据题常考泛化", "evidence": "外推段指标+置信带"},
        {"dir": "缺失/异常处理策略的敏感性", "why": "展示数据工程严谨", "evidence": "不同策略结果对比"},
        {"dir": "多模型集成+轻微差异检查", "why": "提升稳健", "evidence": "集成vs单模型+std"},
    ],
}

# 题型 -> 强基线建议 (替代弱贪心)
STRONG_BASELINES = {
    "A": ["解析特解/稳态解", "FEM细网格参考解", "守恒解析积分"],
    "B": ["线性化凸松弛(用scipy.optimize.linprog)", "专一求解器(可调用mcpi/Gurobi若装)", "多起点局部搜"],
    "C": ["等权重算术平均", "单一AHP", "单一熵权TOPSIS"],
    "D": ["均值/最后观测外推", "简单线性回归", "单一GBDT(不经调参)"],
}


def suggest_innovations(problem_type="B", problem_text="", top=5):
    problem_type = problem_type.upper()
    dirs = DIRECTIONS.get(problem_type, DIRECTIONS["B"])
    return {
        "categories": [{"key": k, **v} for k, v in CATEGORIES.items()],
        "concrete_directions": dirs[:top][:5],
        "strong_baselines": STRONG_BASELINES.get(problem_type, STRONG_BASELINES["B"]),
        "anti_cheat_check": [
            "每个创新点的百分比必须有对应run的原始数据支撑(均值±std, 样本量)",
            "禁止只用1次运行的单一数字作创新证据",
            "创新对比至少一个强基线(否则标'相对弱基线, 存在乐观偏差')",
            "模型结构/约束处理/分解类创新不强制百分比, 改为理论+消融证据",
            "若最大提升来源于基线过弱, 必须补强基线后重算",
        ],
        "source": "problem_type={} matched={}".format(problem_type, bool(problem_text[:1])),
    }


def eval_direction(dirn, category="algorithm"):
    """评估一个创新方向是否足够'具体'(含依据链), 否则提示补充。"""
    need = CATEGORIES[category]["evidence"] if category in CATEGORIES else "证据链"
    ok = ("why" in dirn and "evidence" in dirn and "dir" in dirn)
    return {"valid": ok, "evidence_benchmark": need,
            "hint": None if ok else "创新方向需包含: dir(具体做法)/why(动机)/evidence(证据链)"}


if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "B"
    plan = suggest_innovations(problem_type=t)
    out = {
        "given_type": t,
        "directions": plan["concrete_directions"],
        "strong_baselines": plan["strong_baselines"],
        "anti_cheat": plan["anti_cheat_check"],
        "categories": [{"key": c["key"], "label": c["label"]} for c in plan["categories"]],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if len(sys.argv) > 2:  # argv[2] = 输出 json 路径(接入流水线用)
        outp = sys.argv[2]
        os.makedirs(os.path.dirname(outp) or ".", exist_ok=True)
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[innovation_guide] 已写入 {outp}")
