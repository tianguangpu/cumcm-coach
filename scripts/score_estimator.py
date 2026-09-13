"""score_estimator.py — 国一分位锚定自评

**背景**

``references/gold-standard.md`` 定义了国赛档位的分位锚定规则::

    总分 = Σ(Qi得分 × Qi权重 × 题型权重) / Σ(Qi权重 × 题型权重)
    国一 ≥82 / 国二 ≥72 / 省一 ≥62

但原规则**未给出 Qi 权重与题型权重的具体取值**，因此「这篇论文能不能
冲国一」一直无法被实际计算 —— 使用者只能拿到 PASS/FAIL，不知道距离
国一还差多少、差在哪里。本脚本补上这个实现。

**评分维度**

从金标准内核 (a)~(j) 提炼为 6 个维度，每个维度 0-100 分：

============ ==========================================================
model        模型与推导：公式三段式（前置+本体+后置）、机理推导完整性
verify       四重检验：拟合精度 / Sobol 灵敏度 / 蒙特卡洛 / 假设误差量化
algo         算法与对比：算法对比表（≥3 算法）、基础 vs 创新消融对照
innovation   创新性：5 类创新框架（模型/算法/分解/约束/验证）+ 证据链
format       论文规范：摘要三段式、图题含结论、附录三模块、参考文献质量
compliance   合规：AI 工具使用声明、AIGC 检测风险
============ ==========================================================

**题型权重**

不同题型对各维度的侧重不同（A 题重机理推导，B 题重算法对比……），
由 ``TYPING_WEIGHTS`` 显式声明。**若你对该题型有更准确的经验，
直接改这张表即可**，无需改动计算逻辑。

**用法**::

    # 手动逐项自评（最常用）
    python scripts/score_estimator.py --type B \\
        --scores "model=85,verify=90,algo=70,innovation=75,format=88,compliance=95"

    # 只填部分维度，其余按 0 计（并在报告中提示）
    python scripts/score_estimator.py --type A --scores "model=90,verify=85"

    # 查看某题型的权重配置
    python scripts/score_estimator.py --type B --show-weights

退出码: 0 = 达到国一; 1 = 未达国一（可用于 CI 卡线）
"""

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 档位线（59 份公开样本的经验分位，非官方评分线）
TIERS: list[tuple[str, float]] = [("国一", 82.0), ("国二", 72.0), ("省一", 62.0)]

# 维度定义：key -> (中文名, 说明)
DIMENSIONS: dict[str, tuple[str, str]] = {
    "model": ("模型与推导", "公式三段式（前置+本体+后置）、机理推导完整性"),
    "verify": ("四重检验", "拟合精度 / Sobol 灵敏度 / 蒙特卡洛 / 假设误差量化"),
    "algo": ("算法与对比", "算法对比表（≥3 算法）、基础 vs 创新消融对照"),
    "innovation": ("创新性", "5 类创新框架（模型/算法/分解/约束/验证）+ 证据链"),
    "format": ("论文规范", "摘要三段式、图题含结论、附录三模块、参考文献质量"),
    "compliance": ("合规", "AI 工具使用声明、AIGC 检测风险"),
}

# 维度基础权重（题型权重在其上做侧重调制）
BASE_WEIGHTS: dict[str, float] = {
    "model": 0.20,
    "verify": 0.25,
    "algo": 0.20,
    "innovation": 0.15,
    "format": 0.10,
    "compliance": 0.10,
}

# 题型权重：不同题型对各维度的侧重。可按实际经验调整此表。
TYPING_WEIGHTS: dict[str, dict[str, float]] = {
    "A": {"model": 1.3, "verify": 1.2, "algo": 0.8, "innovation": 1.0, "format": 1.0, "compliance": 1.0},
    "B": {"model": 1.0, "verify": 1.2, "algo": 1.3, "innovation": 1.1, "format": 1.0, "compliance": 1.0},
    "C": {"model": 1.0, "verify": 1.1, "algo": 1.1, "innovation": 1.1, "format": 1.1, "compliance": 1.0},
    "D": {"model": 1.0, "verify": 1.3, "algo": 1.1, "innovation": 1.0, "format": 1.1, "compliance": 1.0},
}

# 低于此分视为「短板」，在报告中单列
WEAK_THRESHOLD = 80.0


def parse_scores(text: str) -> dict[str, float]:
    """解析 ``"model=85,verify=90"`` 形式的自评分数。"""
    scores: dict[str, float] = {}
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"格式应为 '维度=分数'，收到: {item!r}")
        key, _, val = item.partition("=")
        key = key.strip()
        if key not in DIMENSIONS:
            raise ValueError(
                f"未知维度 {key!r}；可用维度: {', '.join(DIMENSIONS)}"
            )
        try:
            score = float(val)
        except ValueError:
            raise ValueError(f"分数应为数字，{key} 收到 {val!r}") from None
        if not 0 <= score <= 100:
            raise ValueError(f"分数应在 0-100 之间，{key} 收到 {score}")
        scores[key] = score
    return scores


def estimate(scores: dict[str, float], ptype: str) -> dict:
    """按分位锚定规则估算总分。未提供的维度按 0 分计。"""
    tw = TYPING_WEIGHTS[ptype]
    full = dict.fromkeys(DIMENSIONS, 0.0)
    full.update(scores)

    numerator = sum(full[k] * BASE_WEIGHTS[k] * tw[k] for k in DIMENSIONS)
    denominator = sum(BASE_WEIGHTS[k] * tw[k] for k in DIMENSIONS)
    total = numerator / denominator if denominator else 0.0
    total = round(total, 6)  # 消除跨平台浮点误差（如 72.0 可能算成 71.9999...）

    tier = "未达省一"
    for name, line in TIERS:
        if total >= line:
            tier = name
            break

    gap_to_first = TIERS[0][1] - total

    # 短板：得分低于阈值，按「可提升空间 × 权重」排序（提升收益最大者在前）
    weak = []
    for k, sc in full.items():
        if sc < WEAK_THRESHOLD:
            room = (WEAK_THRESHOLD - sc) * BASE_WEIGHTS[k] * tw[k]
            weak.append({
                "key": k,
                "name": DIMENSIONS[k][0],
                "score": sc,
                "hint": DIMENSIONS[k][1],
                "contrib": room / denominator,
            })
    weak.sort(key=lambda w: -w["contrib"])

    return {
        "total": total,
        "tier": tier,
        "gap_to_first": gap_to_first,
        "scores": full,
        "weak": weak,
        "missing": [k for k in DIMENSIONS if k not in scores],
    }


def render(result: dict, ptype: str) -> str:
    L = []
    L.append("=" * 64)
    L.append("  国一分位锚定自评")
    L.append(f"  题型: {ptype}    规则: 国一≥82 / 国二≥72 / 省一≥62（经验分位，非官方线）")
    L.append("=" * 64)

    if result["missing"]:
        names = "、".join(DIMENSIONS[k][0] for k in result["missing"])
        L.append(f"\n  [注意] 以下维度未提供分数，已按 0 分计入: {names}")

    L.append("")
    L.append(f"  {'维度':<12}{'得分':>8}{'基础权重':>10}{'题型权重':>10}")
    L.append("  " + "-" * 42)
    for k, (cn, _) in DIMENSIONS.items():
        sc = result["scores"][k]
        L.append(f"  {cn:<12}{sc:>8.1f}{BASE_WEIGHTS[k]:>10.2f}{TYPING_WEIGHTS[ptype][k]:>10.2f}")

    L.append("")
    L.append(f"  ── 总分: {result['total']:.1f}  →  档位: {result['tier']}")

    if result["gap_to_first"] > 0:
        L.append(f"     距国一（82）还差 {result['gap_to_first']:.1f} 分")
    else:
        L.append(f"     已超过国一线 {-result['gap_to_first']:.1f} 分")

    if result["weak"]:
        L.append("")
        L.append("  【优先补强项】（按提升总分的效果排序）")
        for w in result["weak"]:
            L.append(f"    · {w['name']} {w['score']:.0f} 分"
                     f"（补至 {WEAK_THRESHOLD:.0f} 可提升总分约 {w['contrib']:.1f}）")
            L.append(f"      {w['hint']}")
    else:
        L.append("")
        L.append("  [OK] 各维度均无短板。")

    L.append("")
    L.append("  说明: 分档线为 59 份公开样本的经验分位，非官方评分标准；")
    L.append("        权重配置见 scripts/score_estimator.py 的 TYPING_WEIGHTS，可按经验调整。")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser(description="国一分位锚定自评")
    p.add_argument("--type", required=True, choices=["A", "B", "C", "D"],
                   help="题型（决定维度侧重）")
    p.add_argument("--scores",
                   help="各维度自评分数，如 \"model=85,verify=90,algo=70\"")
    p.add_argument("--show-weights", action="store_true",
                   help="只打印该题型的权重配置")
    a = p.parse_args()

    if a.show_weights:
        print(f"题型 {a.type} 的维度权重配置：")
        print(f"  {'维度':<12}{'基础权重':>10}{'题型权重':>10}{'实际占比':>10}")
        tw = TYPING_WEIGHTS[a.type]
        den = sum(BASE_WEIGHTS[k] * tw[k] for k in DIMENSIONS)
        for k, (cn, _) in DIMENSIONS.items():
            actual = BASE_WEIGHTS[k] * tw[k] / den
            print(f"  {cn:<12}{BASE_WEIGHTS[k]:>10.2f}{tw[k]:>10.2f}{actual:>10.1%}")
        return 0

    if not a.scores:
        print("[err] 请用 --scores 提供各维度分数，例如：")
        print('      --scores "model=85,verify=90,algo=70,innovation=75,format=88,compliance=95"')
        print("      可用维度：" + "、".join(f"{k}({v[0]})" for k, v in DIMENSIONS.items()))
        return 2

    try:
        scores = parse_scores(a.scores)
    except ValueError as e:
        print(f"[err] {e}")
        return 2

    result = estimate(scores, a.type)
    print(render(result, a.type))
    return 0 if result["tier"] == "国一" else 1


if __name__ == "__main__":
    sys.exit(main())
