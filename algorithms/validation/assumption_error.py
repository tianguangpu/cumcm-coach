"""
AssumptionError: 假设误差量化
=======================================
用于四重检验 §6.4 假设误差(2026 深化): 评估模型每条假设被放松后对
最终结果的影响，给出量化误差占总不确定性的占比，并据此给出"对结论
是否稳健"的判断 —— 是检验中最考验对模型不确定性来源理解的一环。

核心理念(对照评估指出的"只选2项、过于简略"):
  ▶ 每个假设必须覆盖: 假设内容 -> 放松后的模型变化 -> 结果变化量化 ->
    对结论的影响(方向/量级/是否致命)
  ▶ 不止选最"好算"的假设，而是全覆盖列出的关键假设
  ▶ 输出影响占比与风险等级: 致命 / 显著 / 轻微 / 可忽略

约定：
  an : assumptions = list of dict
       {"name": str, "relax_func": callable(orig_dict)->relaxed_dict,  # 放松假设后重估兜底也可用 delta 手工填
        "relaxed_name": str(可选, 放松后模型名)}
  每个假设可给出:
       - relax_func: 返回"放松后的模型/参数"并据此重算 f
       - OR 直接给 "delta": 经独立计算的相对变化(小数)
  base_output: 基准模型输出标量

用法：
    from assumption_error import AssumptionChecker
    checker = AssumptionChecker(base_output=..., assumptions=[...])
    report  = checker.analyze()
    # report['summary'] 排序后的影响; report['judgement'] 全文按假设判断
"""
from typing import Dict, List

import numpy as np


class AssumptionChecker:
    def __init__(self, base_output: float, assumptions: List[Dict]):
        """
        assumptions 每项:
          {"name": "轮作约束", "relax_func": lambda: <重算输出>,
           "relaxed_name": "允许连作"}
          或 {"name": "...", "delta": 0.023, "relaxed_name": "..."}
        """
        self.base = float(base_output)
        self.assumptions = assumptions
        self.results = []

    def _measure(self, a: Dict) -> Dict:
        """量化单条假设误差, 返回含 rel_change(相对变化率)。"""
        if "delta" in a:
            rel = float(a["delta"])
        elif "relax_func" in a:
            relaxed = a["relax_func"]()
            rel = (float(np.asarray(relaxed).ravel()[0]) - self.base) / self.base \
                if abs(self.base) > 1e-10 else float(np.asarray(relaxed).ravel()[0])
        else:
            raise ValueError("假设 %s 需提供 delta 或 relax_func" % a["name"])
        return {"name": a["name"],
                "relaxed_name": a.get("relaxed_name", "(放松后)"),
                "rel_change": float(rel),
                "impact_pct": abs(float(rel)) * 100.0,
                "grade": _grade(abs(float(rel)) * 100.0),
                "judgement": _judge(a.get("relaxed_name", ""), rel)}

    def analyze(self) -> Dict:
        """对每条假设量化, 并按影响从大到小排序, 给出总风险。"""
        self.results = [self._measure(a) for a in self.assumptions]
        self.results.sort(key=lambda r: -r["impact_pct"])
        n_fatal = sum(1 for r in self.results if r["grade"] == "致命")
        n_sig = sum(1 for r in self.results if r["grade"] == "显著")
        total = sum(r["impact_pct"] for r in self.results)
        return {
            "base_output": self.base,
            "n_assumptions": len(self.results),
            "details": self.results,
            "max_impact_pct": self.results[0]["impact_pct"] if self.results else 0.0,
            "n_fatal": n_fatal, "n_significant": n_sig,
            "total_impact_pct": round(float(total), 2),
            "summary": [
                {"name": r["name"], "impact_pct": round(r["impact_pct"], 2),
                 "grade": r["grade"]} for r in self.results
            ],
        }

    def paper_text(self) -> str:
        """生成可直接写进"假设误差分析"小节的段落。"""
        rep = self.analyze()
        if not rep["details"]:
            return "(无假设被检查)"
        lines = [f"共检查 {rep['n_assumptions']} 条关键假设："]
        for r in rep["details"]:
            lines.append(
                f"- 假设«{r['name']}»(放松为{r['relaxed_name']})："
                f"结果相对变化 {r['rel_change']*100:+.2f}%，影响占比 "
                f"{r['impact_pct']:.2f}%，等级:{r['grade']}——{r['judgement']}")
        lines.append(f"对结论的稳健性判断：{_overall_judge(rep)}")
        return "\n".join(lines)


def _grade(pct):
    if pct > 20:
        return "致命"      # >20% 严重影响结论
    if pct > 10:
        return "显著"      # 5..20% 需谨慎表述
    if pct > 5:
        return "轻微"      # 1..5%
    return "可忽略"         # <1%


def _judge(relaxed_name, rel):
    if abs(rel) > 0.20:
        return "该假设对结论有决定性影响，必须重点论证其成立或做稳健性对照"
    if abs(rel) > 0.10:
        return "影响显著，建议在正文明确限定范围并补充放松场景结果"
    return "结论对该假设的偏离不敏感，稳健可用"


def _overall_judge(rep):
    if rep["n_fatal"] > 0:
        return "存在致命假设，结论需对相应假设做专门敏感性分段，谨慎下强结论"
    if rep["n_significant"] > 0:
        return "存在显著敏感假设，建议对相应参数一并做全局灵敏度(Sobol)交叉验证"
    return "关键假设均稳健，评估在模型假设范围内的结论可信"


def demo():
    """示例：某产量模型 base=100，三条假设。"""
    base = 100.0
    assumptions = [
        {"name": "线性需求", "relaxed_name": "凹需求",
         "relax_func": lambda: 92.3},          # 放松后重算
        {"name": "轮作约束", "relaxed_name": "允许连作", "delta": 0.002},
        {"name": "价格恒定", "relaxed_name": "价格随机", "delta": 0.083},
    ]
    checker = AssumptionChecker(base, assumptions)
    rep = checker.analyze()
    print("排序后的假设误差:")
    for r in rep["details"]:
        print(f"  {r['name']}: {r['rel_change']*100:+.2f}% [{r['grade']}] {r['judgement']}")
    print("\n--- 可直接写入论文的段落 ---\n")
    print(checker.paper_text())


if __name__ == '__main__':
    demo()
