#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
polish_text.py v2.0 — D3 语言润色/AI味检测 (2026对抗升级版)
============================================================
新增检测维度（对抗 Binoculars/CoCo/Burstiness 等 2026 AIGC 检测器）:
  - Burstiness（突发性）: 句长标准差，人类写作波动大，AI过于均匀
  - Entropy（信息熵）: 字符级/词级熵，AI文本熵值趋于一致
  - Paragraph Symmetry（段落对称性）: AI段落长度高度对称
  - Semantic Flow（语义流）: AI段落间逻辑过渡过于平滑
  - Sentence Starter Diversity（句首多样性）: AI句首模式重复

保留 v1.0 全部功能（AI用语词典/句长/被动/重复/创新语言）。
"""
from __future__ import annotations
import argparse, math, os, re, sys
from collections import Counter
from typing import List, Dict, Tuple, Any

VERSION = "2.0.0"

# ── v1.0 原有词典（保留兼容） ──────────────────────────────────────────
AI_TERMS = [
    "综上所述", "值得注意的是", "众所周知", "进行", "极大地", "显著地", "在当今",
    "首先，", "其次，", "最后，", "总而言之", "不难发现", "不仅同时", "有利于",
    "具有重要", "进一步", "综上所述，本文", "本文主要", "从...角度出发",
]
REWRITE = {
    "综上所述": "综上", "值得注意的是": "注意", "进行了": "做",
    "极大地提高了": "精度提高", "进行了聚类分析": "聚类分析",
    "从上述分析可以看出": "可见",
    "总而言之": "总之", "不难发现": "可见", "众所周知": "（删除）",
    "在当今社会": "（删除）", "具有重要意义": "有意义",
}
PASSIVE = ["被", "所", "使", "进行", "得到", "获得"]

# ── v2.0 新增：AI高频句首模式 ──────────────────────────────────────────
AI_SENTENCE_STARTERS = [
    "首先", "其次", "再次", "最后", "此外", "另外", "同时",
    "然而", "因此", "所以", "综上", "总之", "由此可见",
    "通过上述", "基于以上", "在此基础上", "为了进一步",
    "本文", "本研究", "本方法", "该方法", "该模型",
]

# ── v2.0 新增：AI高频连接词（机械连接） ────────────────────────────────
AI_CONNECTORS = [
    "与此同时", "在此基础上", "进一步而言", "具体而言",
    "换言之", "也就是说", "不难看出", "显而易见",
    "需要指出的是", "不容忽视", "至关重要",
]


# ══════════════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════════════

def split_sentences(t: str) -> List[str]:
    """按中英文句号/问号/叹号/分号/换行分句。"""
    return [s.strip() for s in re.split(r"[。！？；\n]", t) if s.strip()]


def split_paragraphs(t: str) -> List[str]:
    """按空行分段。"""
    paras = re.split(r"\n\s*\n", t)
    return [p.strip() for p in paras if p.strip()]


def char_entropy(text: str) -> float:
    """字符级信息熵（bits/char）。中文文本典型值 3.5~5.5。"""
    if not text:
        return 0.0
    freq = Counter(text)
    total = len(text)
    ent = -sum((c / total) * math.log2(c / total) for c in freq.values())
    return round(ent, 3)


def word_entropy(text: str) -> float:
    """词级信息熵（bits/word）。中文按2-gram切分。"""
    if len(text) < 2:
        return 0.0
    bigrams = [text[i:i+2] for i in range(len(text) - 1)]
    freq = Counter(bigrams)
    total = len(bigrams)
    ent = -sum((c / total) * math.log2(c / total) for c in freq.values())
    return round(ent, 3)


def burstiness(sent_lengths: List[int]) -> float:
    """
    Burstiness（突发性）= 句长标准差 / 句长均值。
    人类写作: 0.5~1.5（波动大）
    AI写作:   0.1~0.4（过于均匀）
    返回值越高越像人类。
    """
    if len(sent_lengths) < 3:
        return 0.0
    mean = sum(sent_lengths) / len(sent_lengths)
    if mean == 0:
        return 0.0
    std = (sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)) ** 0.5
    return round(std / mean, 3)


def paragraph_symmetry(paragraph_lengths: List[int]) -> float:
    """
    段落对称性得分: 0~1, 越高越对称（越像AI）。
    人类段落长短不一，AI段落长度趋于一致。
    """
    if len(paragraph_lengths) < 3:
        return 0.0
    mean = sum(paragraph_lengths) / len(paragraph_lengths)
    if mean == 0:
        return 0.0
    cv = (sum((x - mean) ** 2 for x in paragraph_lengths) / len(paragraph_lengths)) ** 0.5 / mean
    # cv 越小越对称，转换为 0~1 得分
    return round(max(0, 1 - cv), 3)


def sentence_starter_diversity(sentences: List[str]) -> Tuple[float, List[str]]:
    """
    句首多样性: 返回 (多样性比例, AI式句首列表)。
    多样性比例 = 不重复句首数 / 总句数。越高越像人类。
    """
    starters = []
    for s in sentences:
        s = s.strip()
        if len(s) >= 2:
            # 取前2~4个字作为句首
            starter = s[:min(4, len(s))]
            starters.append(starter)
    if not starters:
        return 1.0, []
    unique = len(set(starters)) / len(starters)
    # 检测AI式句首
    ai_starts = []
    for s in sentences:
        for pattern in AI_SENTENCE_STARTERS:
            if s.strip().startswith(pattern):
                ai_starts.append(f"{pattern}...({s[:20]})")
                break
    return round(unique, 3), ai_starts


def semantic_flow_uniformity(paragraphs: List[str]) -> float:
    """
    语义流均匀性: 检测段落间过渡是否过于平滑。
    返回 0~1, 越高越像AI（段落间信息密度变化小）。
    """
    if len(paragraphs) < 3:
        return 0.0
    # 计算每段的信息密度（独特词占比）
    densities = []
    for p in paragraphs:
        words = re.findall(r"[\u4e00-\u9fff]{2,}", p)
        if words:
            densities.append(len(set(words)) / len(words))
        else:
            densities.append(0)
    if not densities:
        return 0.0
    mean_d = sum(densities) / len(densities)
    if mean_d == 0:
        return 0.0
    cv = (sum((d - mean_d) ** 2 for d in densities) / len(densities)) ** 0.5 / mean_d
    # cv 越小越均匀，转换为 AI 味得分
    return round(max(0, 1 - cv * 3), 3)  # 乘3放大差异


def connector_density(text: str) -> Tuple[int, List[str]]:
    """检测AI机械连接词密度。"""
    hits = []
    for c in AI_CONNECTORS:
        if c in text:
            hits.append(c)
    return len(hits), hits


# ══════════════════════════════════════════════════════════════════════
# 核心检测（v1.0 + v2.0 合并）
# ══════════════════════════════════════════════════════════════════════

def detect(text: str) -> Dict[str, Any]:
    """全维度AI味检测，返回报告字典。"""
    rep: Dict[str, Any] = {}
    sents = split_sentences(text)
    paras = split_paragraphs(text)
    sent_lens = [len(s) for s in sents]
    para_lens = [len(p) for p in paras]

    # ── v1.0 原有维度 ──
    rep["句数"] = len(sents)
    rep["平均句长"] = round(sum(sent_lens) / len(sent_lens), 1) if sent_lens else 0
    rep["超长句"] = [(i + 1, len(sents[i]), sents[i][:30])
                     for i in range(len(sents)) if len(sents[i]) > 35]
    hits = {}
    for t in AI_TERMS:
        n = text.count(t)
        if n:
            hits[t] = n
    rep["AI用语"] = hits
    rep["被动"] = [w for w in PASSIVE if re.search(re.escape(w), text)]
    dup = []
    for i in range(len(sents) - 1):
        if len(sents[i]) < 2 or len(sents[i + 1]) < 2:
            continue
        a = set(re.findall(r"[\u4e00-\u9fff]{2,}", sents[i]))
        b = set(re.findall(r"[\u4e00-\u9fff]{2,}", sents[i + 1]))
        if len(a & b) >= 8:
            dup.append(i)
    rep["重复"] = dup[:5]

    # ── v2.0 新增维度 ──
    rep["段落数"] = len(paras)

    # Burstiness（突发性）
    rep["burstiness"] = burstiness(sent_lens)
    rep["burstiness评级"] = _rate_burstiness(rep["burstiness"])

    # Entropy（信息熵）
    rep["字符熵"] = char_entropy(text)
    rep["词熵"] = word_entropy(text)
    rep["熵评级"] = _rate_entropy(rep["字符熵"], rep["词熵"])

    # 段落对称性
    rep["段落对称性"] = paragraph_symmetry(para_lens)
    rep["对称性评级"] = _rate_symmetry(rep["段落对称性"])

    # 句首多样性
    rep["句首多样性"], rep["AI式句首"] = sentence_starter_diversity(sents)

    # 语义流均匀性
    rep["语义流均匀性"] = semantic_flow_uniformity(paras)

    # 机械连接词
    rep["连接词密度"], rep["AI连接词"] = connector_density(text)

    # ── 综合评分（v2.0 加权） ──
    rep["AI味综合分"] = _compute_score(rep)

    return rep


def _rate_burstiness(b: float) -> str:
    """Burstiness 评级。"""
    if b >= 0.6:
        return "优(人类特征明显)"
    elif b >= 0.4:
        return "良(偏人类)"
    elif b >= 0.25:
        return "中(偏AI)"
    else:
        return "差(AI特征明显)"


def _rate_entropy(char_e: float, word_e: float) -> str:
    """信息熵评级。中文字符熵典型 4.0~5.5。"""
    if char_e >= 4.5:
        return "优(高随机性)"
    elif char_e >= 3.8:
        return "良"
    elif char_e >= 3.0:
        return "中(偏低)"
    else:
        return "差(AI特征)"


def _rate_symmetry(s: float) -> str:
    """对称性评级（越低越像人类）。"""
    if s <= 0.3:
        return "优(段落长短不一)"
    elif s <= 0.5:
        return "良"
    elif s <= 0.7:
        return "中(偏对称)"
    else:
        return "差(高度对称=AI)"


def _compute_score(rep: Dict[str, Any]) -> float:
    """
    v2.0 综合评分: 0~100, 越高越像人类写作。
    权重分配:
      - AI用语词频:     20分
      - 超长句:         15分
      - 被动/机械词:    10分
      - 重复表述:       10分
      - Burstiness:     20分  ← 新增重点
      - 信息熵:         10分  ← 新增
      - 段落对称性:      5分  ← 新增
      - 连接词密度:     10分  ← 新增
    """
    sc = 100.0

    # 1. AI用语（20分）
    ai_count = sum(rep.get("AI用语", {}).values())
    sc -= min(20, ai_count * 2.5)

    # 2. 超长句（15分）
    sc -= min(15, len(rep.get("超长句", [])) * 2.5)

    # 3. 被动/机械词（10分）
    passive_ai = [w for w in rep.get("被动", []) if w in ("进行", "使", "被")]
    sc -= min(10, len(passive_ai) * 2)

    # 4. 重复表述（10分）
    sc -= min(10, len(rep.get("重复", [])) * 2)

    # 5. Burstiness（20分）— 越低越AI，扣分越多
    b = rep.get("burstiness", 0)
    if b < 0.2:
        sc -= 20  # 严重AI特征
    elif b < 0.3:
        sc -= 14
    elif b < 0.4:
        sc -= 8
    elif b < 0.5:
        sc -= 3
    # b >= 0.5 不扣分

    # 6. 信息熵（10分）
    char_e = rep.get("字符熵", 4.5)
    if char_e < 3.0:
        sc -= 10
    elif char_e < 3.5:
        sc -= 7
    elif char_e < 4.0:
        sc -= 3

    # 7. 段落对称性（5分）
    sym = rep.get("段落对称性", 0)
    if sym > 0.8:
        sc -= 5
    elif sym > 0.6:
        sc -= 3

    # 8. 连接词密度（10分）
    conn = rep.get("连接词密度", 0)
    sc -= min(10, conn * 2)

    return round(max(0, sc), 1)


# ══════════════════════════════════════════════════════════════════════
# 报告渲染
# ══════════════════════════════════════════════════════════════════════

def render(rep: Dict[str, Any]) -> str:
    """生成完整检测报告。"""
    L = []
    L.append("=" * 55)
    L.append("  D3 语言润色 / AI味检测报告 v2.0（2026对抗升级版）")
    L.append("=" * 55)

    # ── 基础统计 ──
    L.append("")
    L.append("【基础统计】")
    L.append(f"  段落数: {rep.get('段落数', '?')}")
    L.append(f"  句数: {rep['句数']}  平均句长: {rep['平均句长']}字")
    L.append(f"  超长句(>35字): {len(rep['超长句'])}句")
    for (i, l, snip) in rep["超长句"][:5]:
        L.append(f"    #{i}({l}字): {snip}...")

    # ── v1.0 原有维度 ──
    L.append("")
    L.append("【传统AI味维度】")
    ai_items = rep.get("AI用语", {})
    L.append(f"  AI用语: {', '.join(f'{k}x{v}' for k, v in ai_items.items()) or '无'}")
    L.append(f"  被动/机械词: {', '.join(rep.get('被动', [])) or '无'}")
    L.append(f"  重复表述: {len(rep.get('重复', []))}处")

    # ── v2.0 新增维度 ──
    L.append("")
    L.append("【2026对抗检测维度】")

    # Burstiness
    b = rep.get("burstiness", 0)
    L.append(f"  Burstiness(突发性): {b}  [{rep.get('burstiness评级', '?')}]")
    L.append(f"    → 人类典型: 0.5~1.5  AI典型: 0.1~0.4")

    # Entropy
    ce = rep.get("字符熵", 0)
    we = rep.get("词熵", 0)
    L.append(f"  信息熵: 字符={ce} bits/char, 词={we} bits/word  [{rep.get('熵评级', '?')}]")
    L.append(f"    → 中文典型: 4.0~5.5 bits/char")

    # 段落对称性
    sym = rep.get("段落对称性", 0)
    L.append(f"  段落对称性: {sym}  [{rep.get('对称性评级', '?')}]")
    L.append(f"    → 越低越像人类(段落长短不一)")

    # 句首多样性
    sd = rep.get("句首多样性", 0)
    L.append(f"  句首多样性: {sd} (不重复句首/总句数)")
    ai_starts = rep.get("AI式句首", [])
    if ai_starts:
        L.append(f"  AI式句首: {', '.join(ai_starts[:5])}")

    # 语义流
    sf = rep.get("语义流均匀性", 0)
    L.append(f"  语义流均匀性: {sf} (越低越好)")

    # 连接词
    cd = rep.get("连接词密度", 0)
    L.append(f"  机械连接词: {cd}个 → {', '.join(rep.get('AI连接词', [])) or '无'}")

    # ── 综合评分 ──
    L.append("")
    L.append("=" * 55)
    sc = float(rep["AI味综合分"])
    if sc >= 85:
        tag, emoji = "优秀", "★★★"
    elif sc >= 70:
        tag, emoji = "良好", "★★"
    elif sc >= 65:
        tag, emoji = "达标", "★"
    elif sc >= 50:
        tag, emoji = "偏AI", "△"
    else:
        tag, emoji = "严重AI味", "✗"
    L.append(f"  AI味综合分: {sc}  [{tag} {emoji}]")
    L.append(f"  达标线: ≥65 (国赛交付标准)")

    # ── 修复建议 ──
    L.append("")
    L.append("【修复建议(按优先级)】")
    suggestions = _generate_suggestions(rep)
    for i, s in enumerate(suggestions[:8], 1):
        L.append(f"  {i}. {s}")

    L.append("")
    if sc >= 65:
        L.append(f"[D3 末行] ✓ PASS AI味综合分>=65 ({sc})")
    else:
        L.append(f"[D3 末行] ✗ AI味重 ({sc}), 需改写")

    return "\n".join(L)


def _generate_suggestions(rep: Dict[str, Any]) -> List[str]:
    """根据检测结果生成优先级排序的修复建议。"""
    suggestions = []

    # Burstiness 低 → 最优先
    b = rep.get("burstiness", 0)
    if b < 0.3:
        suggestions.append("【紧急】句长过于均匀(Burstiness=%.2f)：插入2~3个超短句(5字以内)和1~2个长句，打破节奏" % b)
    elif b < 0.5:
        suggestions.append("句长波动偏小：适当混合长短句，增加口语化短句" )

    # AI用语
    ai_count = sum(rep.get("AI用语", {}).values())
    if ai_count > 5:
        suggestions.append("AI用语过多(%d个)：逐条替换，参考 REWRITE_MAP" % ai_count)
    elif ai_count > 2:
        suggestions.append("AI用语(%d个)：替换'综上所述→综上'、'值得注意的是→注意'" % ai_count)

    # 超长句
    long_count = len(rep.get("超长句", []))
    if long_count > 3:
        suggestions.append("超长句过多(%d句)：用句号断开，每句控制在25字以内" % long_count)

    # 信息熵低
    ce = rep.get("字符熵", 4.5)
    if ce < 3.5:
        suggestions.append("信息熵偏低(%.2f)：增加用词多样性，避免重复句式" % ce)

    # 段落对称
    sym = rep.get("段落对称性", 0)
    if sym > 0.7:
        suggestions.append("段落长度过于对称：让某些段落短一些(3~4句)，某些长一些(8~10句)")

    # 连接词
    cd = rep.get("连接词密度", 0)
    if cd > 3:
        suggestions.append("机械连接词过多(%d个)：删除'在此基础上'、'进一步而言'等，用自然过渡" % cd)

    # 句首重复
    ai_starts = rep.get("AI式句首", [])
    if len(ai_starts) > 3:
        suggestions.append("句首模式重复：避免连续用'首先/其次/最后'，改用变化开头")

    # 被动
    passive_ai = [w for w in rep.get("被动", []) if w in ("进行", "使", "被")]
    if passive_ai:
        suggestions.append("被动语态: '进行了X分析' → 'X分析...'，去掉'进行'")

    if not suggestions:
        suggestions.append("当前文本质量良好，无需大幅修改")

    return suggestions


# ══════════════════════════════════════════════════════════════════════
# CLI 入口（保持 v1.0 兼容）
# ══════════════════════════════════════════════════════════════════════

def main(argv=None):
    p = argparse.ArgumentParser(description="D3 语言润色/AI味检测 v2.0")
    p.add_argument("--tex", default="paper/main.tex", help="LaTeX源文件")
    p.add_argument("--section", default=None, help="仅检测某节")
    p.add_argument("--ai-score", action="store_true", help="仅输出AI味综合分")
    p.add_argument("--fix-suggest", action="store_true", help="输出修复建议")
    p.add_argument("--json", action="store_true", help="JSON格式输出")
    p.add_argument("--burstiness", action="store_true", help="仅输出Burstiness值")
    p.add_argument("--entropy", action="store_true", help="仅输出信息熵")
    a = p.parse_args(argv)

    if not os.path.isfile(a.tex):
        print(f"[err] 未找到 {a.tex}")
        return 1

    txt = open(a.tex, "r", encoding="utf-8", errors="ignore").read()
    txt = re.sub(r"(?m)^[ \t]*%.*$", "", txt)  # 去注释行
    txt = re.sub(r"(?m)%.*$", "", txt)  # 去行内注释
    m = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", txt, re.S)
    if m:
        txt = m.group(1)  # 仅分析正文
    plain = re.sub(r"\\[a-zA-Z]+", "", txt)

    # 如果指定了节，提取该节内容
    if a.section:
        sec_pat = re.compile(
            r"\\(?:sub)?section\{[^}]*" + re.escape(a.section) + r"[^}]*\}(.*?)(?=\\(?:sub)?section|\Z)",
            re.S
        )
        sec_m = sec_pat.search(txt)
        if sec_m:
            plain = re.sub(r"\\[a-zA-Z]+", "", sec_m.group(1))
        else:
            print(f"[warn] 未找到节: {a.section}")

    rep = detect(plain)

    # 快速输出模式
    if a.ai_score:
        print(f"AI味综合分={rep['AI味综合分']}")
        return 0
    if a.burstiness:
        print(f"Burstiness={rep['burstiness']}  [{rep['burstiness评级']}]")
        return 0
    if a.entropy:
        print(f"字符熵={rep['字符熵']} bits/char  [{rep['熵评级']}]")
        return 0
    if a.json:
        import json
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0

    # 完整报告
    if a.fix_suggest:
        for k, v in REWRITE.items():
            print(f"建议: '{k}' -> '{v}'")
    print(render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
