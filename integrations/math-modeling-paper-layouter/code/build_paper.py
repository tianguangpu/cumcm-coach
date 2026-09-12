#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_paper.py - L2 LaTeX编译 + 排版溢出诊断 (paper-layouter)"""
from __future__ import annotations
import argparse, os, re, shutil, subprocess, sys

VERSION="1.0.0"

def find_tex(args_tex=None):
    if args_tex and os.path.isfile(args_tex): return args_tex
    for cand in ("paper/main.tex","main.tex","paper_v7pro/main.tex"):
        if os.path.isfile(cand): return cand
    return None

def run_latex(tex_path, passes):
    engine=shutil.which("xelatex") or shutil.which("pdflatex")
    if not engine:
        return None, "xelatex/pdflatex 不在 PATH，无法编译。请安装 TeXLive/MiKTeX。"
    d=os.path.dirname(os.path.abspath(tex_path)) or "."
    name=os.path.basename(tex_path)
    cmd=[engine,"-interaction=nonstopmode","-halt-on-error",name]
    for i in range(max(1,passes)):
        r=subprocess.run(cmd,cwd=d,capture_output=True,text=True)
        if i==0 and r.returncode!=0:
            return r.returncode, (r.stdout+r.stderr)
    return 0, "ok"

def parse_overfull(log_text):
    sev={"crit":0,"mild":0}; details=[]
    # 真实 TeX 日志: Overfull \hbox (X.Xpt too wide) in paragraph at lines 42--43
    pat=re.compile(r"Overfull[ \t]*\\hbox[ (]*([0-9.]+)pt\s+too wide")
    for m in pat.finditer(log_text):
        try: pt=float(m.group(1))
        except Exception: continue
        lvl="严重" if pt>20 else "轻微"
        sev["crit" if pt>20 else "mild"]+=1
        # line num from the same physical line
        line=m.group(0).split("\n")[-1].strip()
        details.append("  %s(%.1fpt) %s"%(lvl,pt,line[:70]))
    return sev, details

def render(sev,und,det,ok):
    L=["===== LaTeX 排版溢出诊断报告 (L2) ====="]
    for d in det: L.append(d)
    L.append("严重溢出(>20pt)=%d, 轻微溢出(<20pt)=%d, Underfull=%d"%(sev["crit"],sev["mild"],und))
    L.append("[L2 末行] " + ("✓ 无中/严重溢出, 排版可接受" if ok else "✗ 存在严重溢出需修复"))
    return "\n".join(L)

def main(argv=None):
    p=argparse.ArgumentParser(description="L2 build/overflow check (paper-layouter)")
    p.add_argument("--passes",default=3,type=int)
    p.add_argument("--check-only",action="store_true")
    p.add_argument("--view",action="store_true")
    p.add_argument("--tex",default=None)
    a=p.parse_args(argv)

    if a.check_only:
        # locate main.log
        log=None
        for cand in ("paper/main.log","main.log"):
            if os.path.isfile(cand): log=cand; break
        if not log: print("[warn] 未找到 main.log"); return 1
        txt=open(log,"r",encoding="utf-8",errors="ignore").read()
        sev,det=parse_overfull(txt)
        und=len(re.findall(r"Underfull\s+\\hbox",txt))
        ok=sev["crit"]==0 and sev["mild"]<=3
        print(render(sev,und,det,ok)); return 0

    tex=find_tex(a.tex)
    if not tex: print("[err] 未找到 main.tex"); return 1
    code,out=run_latex(tex,a.passes)
    if code==0:
        # re-check log
        log=tex.replace(".tex",".log")
        if os.path.isfile(log):
            txt=open(log,"r",encoding="utf-8",errors="ignore").read()
            sev,det=parse_overfull(txt)
            und=len(re.findall(r"Underfull\s+\\hbox",txt))
            ok=sev["crit"]==0 and sev["mild"]<=3
            print(render(sev,und,det,ok))
        else:
            print("✓ 编译通过 (无 log 或未检测到溢出)")
    else:
        print("[err] 编译失败(exit=%s). 请检查 main.log. 片段:"%code)
        print((out or "")[-1500:])
        return 1
    return 0

if __name__=="__main__": sys.exit(main())
