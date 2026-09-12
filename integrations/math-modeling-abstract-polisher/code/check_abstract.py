#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_abstract.py - D1 摘要质量8维审查 (abstract-polisher)"""
from __future__ import annotations
import argparse, os, re, sys

VERSION="1.0.0"

# 5要素模式词
FIVE = {
  "问题": ["针对","研究","本文","考虑","面向","围绕"],
  "模型方法": ["建立","采用","构建","提出","使用","利用","设计","基于"],
  "结果": ["结果","得到","表明","计算","求解","精度","误差","准确"],
  "创新": ["改进","优化","加权","融合","提升","对比","首次","创新","鲁棒","多目标"],
  "结论": ["综上","因此","可见","优于","适用","推广","验证"],
}
AI_PHRASES = ["综上所述","值得注意的是","首先","其次","最后","极大地","众所周知","在当今","综上所述，本文"]

def extract_abstract(tex_path):
    if not os.path.isfile(tex_path): return ""
    txt=open(tex_path,"r",encoding="utf-8",errors="ignore").read()
    # try \begin{abstract} ... \end{abstract}
    m=re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}",txt,re.S)
    if m: return m.group(1)
    m=re.search(r"\\section\*?\{摘要\}(.*?)(?:\\section|\\newpage|\\end\{document\})",txt,re.S)
    if m: return m.group(1)
    # CUMCM 中文模板: {\bfseries ... 摘\quad 要} ... 关键字
    m=re.search(r"\{\\bfseries.*?摘.*?要\}\s*(.*?)\s*\\noindent\\bfseries\s*关键字",txt,re.S)
    if m: return m.group(1)    # fallback: 去掉 latex 宏后截取前 1000 字
    return re.sub(r"\\(?:[a-zA-Z]+|\[[^\]]*\]|\{[^}]*\})","",txt)[:1000]

def clean(s):
    s=re.sub(r"\\[a-zA-Z]+","",s); s=re.sub(r"[{}]","",s)
    return s.strip()

def score(abst):
    t=clean(abst); detail={}
    # 5要素
    present={k:any(w in t for w in ws) for k,ws in FIVE.items()}
    detail["要素"]=", ".join("%s:%s"%(k,"有" if v else "缺") for k,v in present.items())
    # 字数
    n=len(re.sub(r"\s","",t)); detail["字数"]=n
    # 数值密度
    nums=re.findall(r"\d+\.?\d*",t); detail["数值数"]=len(nums)
    # 创新点
    innov=[w for w in FIVE["创新"] if w in t]; detail["创新词"]=",".join(innov) or "无"
    # AI味
    ai=[p for p in AI_PHRASES if p in t]; detail["AI套话"]=",".join(ai) or "无"
    # 打分(0~100)
    score_=0.0
    score_ += 15 if present["问题"] else 0
    score_ += 20 if present["模型方法"] else 0
    score_ += 25 if present["结果"] else 0
    score_ += 20 if present["创新"] else 0
    score_ += 10 if present["结论"] else 0
    normn=min(max((n-300)/400,0),1)*5  # 300~700字给5分
    score_ += normn
    score_ += min(5,len(nums)/3)
    score_ -= min(5,len(ai)*2)
    detail["综合分"]=round(max(0,score_),1)
    return detail

def render(t,detail):
    L=["===== D1 摘要质量审查报告 ====="]
    L.append("摘要(经清洗 %d 字): %s... "%(len(clean(t)),clean(t)[:80]))
    L.append("5要素: "+detail["要素"])
    L.append("字数=%d 数值数=%d 综合分=%s"%(detail["字数"],detail["数值数"],detail["综合分"]))
    L.append("创新词: "+detail["创新词"])
    L.append("AI套话: "+detail["AI套话"])
    sc=float(detail["综合分"])
    L.append("[D1 末行] " + ("✓ PASS 综合得分>=70 (%.1f)"%sc if sc>=70 else "✗ 综合得分<70 (%.1f), 需修复"%sc))
    return "\n".join(L)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--tex",default="paper/main.tex")
    p.add_argument("--score-only",action="store_true")
    p.add_argument("--fix-suggest",action="store_true")
    a=p.parse_args(argv)
    abst=extract_abstract(a.tex)
    if not abst.strip():
        print("[err] 未找到摘要: 缺 \\begin{abstract} 或 \\section*{摘要}"); return 1
    d=score(abst)
    if a.score_only:
        print("综合得分=%s"%d["综合分"]); return 0
    print(render(abst,d))
    if a.fix_suggest:
        print("-- 修复建议: 缺要素->补; 字数<300->扩; 字数>1000->缩; AI套话->换具体表述; 数值<4/千字->补关键指标")
    return 0

if __name__=="__main__": sys.exit(main())
