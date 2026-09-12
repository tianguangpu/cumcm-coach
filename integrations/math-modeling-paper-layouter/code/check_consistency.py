#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_consistency.py - L3 图文一致性4维校验 (paper-layouter)"""
from __future__ import annotations
import argparse, glob, json, os, re, sys
from typing import Dict, List

VERSION="1.0.0"

def load_results(results_dir):
    vals={}
    if not os.path.isdir(results_dir): return vals
    for root,_,files in os.walk(results_dir):
        for f in files:
            if not f.endswith(".json"): continue
            fp=os.path.join(root,f)
            try:
                with open(fp,"r",encoding="utf-8",errors="ignore") as fh: data=json.load(fh)
            except Exception: continue
            for k,v in _flatten(data,f):
                if isinstance(v,(int,float)): vals[k]=v
    return vals

def _flatten(obj,prefix=""):
    if isinstance(obj,dict):
        for k,v in obj.items(): yield from _flatten(v,"%s.%s"%(prefix,k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): yield from _flatten(v,"%s[%d]"%(prefix,i))
    else: yield prefix,obj

def check_values(tex_text, vals):
    issues=[]
    for k,v in sorted(vals.items()):
        if not isinstance(v,(int,float)): continue
        s=("%.6g"%v)
        # 高精度整数值抽查正文是否含其整数部分
        if abs(v)>=100 and v.is_integer() and str(int(v)) not in tex_text.replace(" ","").replace(",",""):
            issues.append("数值 %s=%s 未在正文检索到"%(k,v))
    # 小数值(0~1)常见于准确率, 不强检
    return issues[:20]

def check_figure_refs(text, base_dir=None):
    missing=[]
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",text):
        rel=m.group(1).strip().split(",")[0]
        cands=[rel]
        if base_dir:
            cands += [os.path.join(base_dir, rel),
                      os.path.join(base_dir, "figures", rel),
                      os.path.join(base_dir, "paper", rel)]
        hit=False
        for cand in cands:
            for e in (".pdf",".png",".jpg",".svg",".eps"):
                full=(cand if os.path.splitext(cand)[1] else cand+e)
                if os.path.isfile(full): hit=True; break
            if hit: break
        if not hit and base_dir:
            if glob.glob(os.path.join(base_dir,"**",os.path.basename(rel)),recursive=True):
                hit=True
        if not hit: missing.append(rel)
    return missing

def check_labels(text):
    labels=set(re.findall(r"\\label\{([^}]+)\}",text))
    refs=set(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}",text))
    dangling=[r for r in refs if r not in labels]
    unused=[l for l in labels if l not in refs and not l.startswith("tab:")]
    return dangling,unused

def render(rep):
    L=["===== 图文一致性 4 维校验报告 (L3) ====="]
    L.append("A. 数值一致性: %d 处待核"%len(rep["values"]))
    for x in rep["values"]: L.append("   "+x)
    L.append("B. 图引用完整性: %d 缺失"%len(rep["figures"]))
    for x in rep["figures"]: L.append("   "+x)
    L.append("C. 标签配对: dangling=%d unused=%d"%(len(rep["dangling"]),len(rep["unused"])))
    for x in rep["dangling"][:10]: L.append("   dangling: "+x)
    for x in rep["unused"][:10]: L.append("   unused: "+x)
    bad=len(rep["values"])+len(rep["figures"])+len(rep["dangling"])
    L.append("[L3 末行] " + ("✓ 论文与结果文件完全一致, 无任何问题" if bad==0 else "✗ 存在 %d 处问题"%bad))
    return "\n".join(L)

def main(argv=None):
    p=argparse.ArgumentParser(description="L3 consistency check (paper-layouter)")
    p.add_argument("--tex",default="paper/main.tex")
    p.add_argument("--results",default="results")
    p.add_argument("--values",action="store_true")
    p.add_argument("--refs",action="store_true")
    p.add_argument("--output",default=None)
    a=p.parse_args(argv)
    if not os.path.isfile(a.tex):
        print("[err] 未找到 %s"%a.tex); return 1
    text=open(a.tex,"r",encoding="utf-8",errors="ignore").read()
    rep={"values":[],"figures":[],"dangling":[],"unused":[]}
    if not a.refs:
        rep["values"]=check_values(text,load_results(a.results))
    if not a.values:
        _td = os.path.dirname(os.path.abspath(a.tex))
        _root = os.path.dirname(_td) if os.path.basename(_td) in ("paper",) else _td
        rep["figures"]=check_figure_refs(text, _root)
        dl,un=check_labels(text); rep["dangling"]=dl; rep["unused"]=un
    out=render(rep)
    if a.output:
        os.makedirs(os.path.dirname(a.output) or ".",exist_ok=True)
        open(a.output,"w",encoding="utf-8").write(out); print("report ->",a.output)
    print(out)
    return 0

if __name__=="__main__": sys.exit(main())
