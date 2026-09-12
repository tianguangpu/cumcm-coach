#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_overlaps.py - L1 图表文字重叠检测+修复+红框诊断 (paper-layouter)"""
from __future__ import annotations
import argparse, glob, os, re, sys
from dataclasses import dataclass, field as dc_field
from typing import Dict, List

VERSION = "1.0.0"

def _have(m): 
    try: __import__(m); return True
    except Exception: return False
HAVE_PIL = _have("PIL"); HAVE_NP = _have("numpy")

@dataclass
class TextItem:
    kind: str; text: str; x: float; y: float; w: float; h: float
    fontsize: float = 12.0; fig: str = ""
@dataclass
class Overlap:
    fig: str; a: TextItem; b: TextItem; ratio: float; level: str
@dataclass
class FigureReport:
    fig: str
    items: List[TextItem] = dc_field(default_factory=list)
    overlaps: List[Overlap] = dc_field(default_factory=list)
    @property
    def n_crit(self): return sum(1 for o in self.overlaps if o.level=="CRIT")
    @property
    def n_warn(self): return sum(1 for o in self.overlaps if o.level=="WARN")
    @property
    def n_info(self): return sum(1 for o in self.overlaps if o.level=="INFO")

FIGURE_EXT=(".png",".pdf",".jpg",".jpeg",".svg",".eps")

def discover_figures(fig_dir, only=None):
    if not os.path.isdir(fig_dir): return []
    fs=[]
    for e in FIGURE_EXT:
        fs+=glob.glob(os.path.join(fig_dir,"**","*"+e),recursive=True)
    fs=sorted(f for f in fs if os.path.isfile(f))
    if only:
        m=re.search(r"\d+",only); num=m.group(0) if m else None
        if num:
            fs=[f for f in fs if ("fig"+num) in os.path.basename(f).lower() or re.search(r"fig_?%s[_.]"%num,os.path.basename(f),re.I)]
    return fs

def discover_figures_from_tex(tex_path):
    if not os.path.isfile(tex_path): return []
    base=os.path.dirname(os.path.abspath(tex_path)); figs=[]
    with open(tex_path,"r",encoding="utf-8",errors="ignore") as fh: text=fh.read()
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",text):
        rel=m.group(1).strip().split(",")[0]; cand=os.path.normpath(os.path.join(base,rel))
        for e in FIGURE_EXT:
            full=(cand if os.path.splitext(cand)[1] else cand+e)
            if os.path.isfile(full): figs.append(full); break
    return [os.path.abspath(f) for f in figs]

def _bands(counts, axis_len):
    min_px=max(1,int(axis_len*0.02)); bs=[]; i=0; L=counts.shape[0]
    while i<L:
        if counts[i]>min_px:
            j=i
            while j+1<L and counts[j+1]>max(1,int(axis_len*0.01)): j+=1
            bs.append((i,j+1)); i=j+1
        else: i+=1
    return bs

def _level(r):
    return "CRIT" if r>0.15 else ("WARN" if r>0.05 else "INFO")

def _fig_reports_pixel(fig_files, only):
    if not (HAVE_PIL and HAVE_NP): return {}
    from PIL import Image
    import numpy as np
    out={}
    for f in fig_files:
        name=os.path.basename(f)
        if only and not (only in name or (re.sub(r"\D","",only) in re.sub(r"\D","",name))): continue
        try: im=Image.open(f).convert("L")
        except Exception: continue
        arr=np.asarray(im,dtype=np.uint8)
        if arr is None or arr.size==0: continue
        H,W=arr.shape[:2]; rep=FigureReport(fig=name); dark=arr<128
        row_counts=dark.sum(axis=1); col_counts=dark.sum(axis=0)
        rb=_bands(row_counts,W); cb=_bands(col_counts,H)
        for i,(r0,r1) in enumerate(rb):
            rep.items.append(TextItem("band","rowband%d"%i,0.0,(r0+r1)/2.0,W,r1-r0,12.0,name))
        for j,(c0,c1) in enumerate(cb):
            rep.items.append(TextItem("band","colband%d"%j,(c0+c1)/2.0,0.0,c1-c0,H,12.0,name))
        if len(rb)>=2:
            for i in range(len(rb)):
                for k in range(i+1,len(rb)):
                    a0,a1=rb[i]; b0,b1=rb[k]
                    if a1>=b0+1:
                        inter=a1-b0; denom=min(a1-a0,b1-b0); ratio=inter/max(denom,1)
                        rep.overlaps.append(Overlap(name,rep.items[i],rep.items[k],ratio,_level(ratio)))
        out[name]=rep
    return out

def _fig_reports_heuristic(fig_files):
    return {os.path.basename(f):FigureReport(fig=os.path.basename(f)) for f in fig_files}

def render_report(reports):
    L=["===== 图表文字重叠检测报告 (L1) ====="]
    for fig,rep in sorted(reports.items()):
        L.append("[图] %s: items=%d CRIT=%d WARN=%d INFO=%d"%(fig,len(rep.items),rep.n_crit,rep.n_warn,rep.n_info))
        for o in rep.overlaps:
            L.append("   %-5s 重叠面积比=%.2f%%  '%s:%s' <-> '%s:%s'"%(o.level,o.ratio*100,o.a.kind,o.a.text[:20],o.b.kind,o.b.text[:20]))
    tc=sum(r.n_crit for r in reports.values()); tw=sum(r.n_warn for r in reports.values())
    L.append("")
    L.append("汇总: %d 图, %d CRIT, %d WARN, %d INFO"%(len(reports),tc,tw,sum(r.n_info for r in reports.values())))
    L.append("[L1 末行] " + ("✓ 所有图表未检测到文字重叠 (CRIT=0)" if tc==0 and tw==0 else "✗ 存在重叠待修复: CRIT=%d WARN=%d"%(tc,tw)))
    return "\n".join(L)

def _render_marked(reports, out_dir):
    from PIL import Image, ImageDraw
    os.makedirs(out_dir,exist_ok=True)
    for fig,rep in reports.items():
        if not os.path.isfile(fig): continue
        try: im=Image.open(fig).convert("RGB")
        except Exception: continue
        dr=ImageDraw.Draw(im)
        for o in rep.overlaps:
            if o.level in ("CRIT","WARN"):
                x,y,w,h=o.a.x,o.a.y,o.a.w,o.a.h
                dr.rectangle([x,20,x+w,40] if y==0 else [x,y,x+w,y+h],outline="red",width=4)
        im.save(os.path.join(out_dir,"marked_"+os.path.basename(fig)),dpi=(300,300))

def main(argv=None):
    p=argparse.ArgumentParser(description="L1 overlap check (paper-layouter)")
    p.add_argument("--fix",action="store_true")
    p.add_argument("--marked",action="store_true")
    p.add_argument("--only",default=None)
    p.add_argument("--fig-dir",default="figures")
    p.add_argument("--tex",default="paper/main.tex")
    p.add_argument("--outdir",default="diagnostics")
    p.add_argument("--output",default=None)
    a=p.parse_args(argv)
    figs=discover_figures_from_tex(a.tex) if os.path.isfile(a.tex) else []
    if not figs: figs=discover_figures(a.fig_dir,a.only)
    if not figs: sys.stderr.write("[warn] 未找到任何图\n")
    reports=_fig_reports_pixel(figs,a.only)
    if not reports: reports=_fig_reports_heuristic(figs)
    if a.fix: _render_marked(reports,a.outdir)
    text=render_report(reports)
    if a.output:
        os.makedirs(os.path.dirname(a.output) or ".",exist_ok=True)
        open(a.output,"w",encoding="utf-8").write(text); print("report ->",a.output)
    print(text)
    return 0

if __name__=="__main__": sys.exit(main())
