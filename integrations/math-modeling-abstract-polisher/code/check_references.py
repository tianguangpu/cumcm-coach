#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_references.py - D2 参考文献8维审查 (abstract-polisher)"""
from __future__ import annotations
import argparse, os, re, sys
from collections import Counter

VERSION="1.0.0"

def is_ws(ch):
    return ch in " \t\r\n"

def load_bib(tex_path):
    entries=[]
    if os.path.isfile(tex_path):
        txt=open(tex_path,"r",encoding="utf-8",errors="ignore").read()
    else: txt=""
    bib=None
    for cand in ("paper/refs.bib","refs.bib"):
        if os.path.isfile(cand): bib=open(cand,"r",encoding="utf-8",errors="ignore").read(); break
    source=(bib or txt)

    def field(body,name):
        m=re.search(r"%s\s*=\s*\{" % re.escape(name) + "([^}]*)}", body, re.I)
        if m: return m.group(1).strip()
        m=re.search(r"%s\s*=\s*([0-9A-Za-z._/:,\-]+)" % re.escape(name), body, re.I)
        if m: return m.group(1).strip().rstrip(",")
        return ""

    i=0; n=len(source)
    while i<n:
        at=source.find("@",i)
        if at<0: break
        i=at+1
        while i<n and is_ws(source[i]): i+=1
        t0=i
        while i<n and source[i].isalnum(): i+=1
        typ=source[t0:i]
        while i<n and is_ws(source[i]): i+=1
        if i>=n or source[i]!="{": continue
        i+=1
        depth=0; k0=i
        while i<n:
            ch=source[i]
            if ch=="{": depth+=1
            elif ch=="}":
                if depth==0: break
                depth-=1
            i+=1
        body=source[k0:i]
        bm=re.search(r"([^,]+),(.*)",body,re.S)
        if not bm: continue
        b=bm.group(2)
        y=field(b,"year")
        entries.append({"type":typ,"author":field(b,"author"),"title":field(b,"title"),
                        "journal":field(b,"journal") or field(b,"booktitle"),
                        "year":int(y) if y.isdigit() else None,
                        "doi":field(b,"doi") or field(b,"url")})
        i+=1
    return entries

def weight_by_year(y, cur=2026):
    if not y: return 0.1
    age=cur-y
    if age<=1: return 1.0
    if age<=3: return 0.8
    if age<=5: return 0.6
    if age<=10: return 0.3
    return 0.05

def check(entries):
    n=len(entries); r={"总数":n}
    types=Counter(e["type"] for e in entries)
    r["期刊数"]=types.get("article",0); r["图书数"]=types.get("book",0)
    recent=[e for e in entries if e["year"] and e["year"]>=2021]
    r["近5年"]=len(recent); r["近5年占比"]=round(len(recent)/n*100) if n else 0
    def foreign(e): return bool(re.search(r"[a-zA-Z]{3,}",e["author"])) and not re.search(r"[\u4e00-\u9fff]",e["author"])
    fe=[e for e in entries if foreign(e)]
    r["外文"]=len(fe); r["外文占比"]=round(len(fe)/n*100) if n else 0
    r["前沿度"]=round(sum(weight_by_year(e["year"]) for e in entries)/max(1,n)*100)
    doi=[e for e in entries if e["doi"]]
    r["DOI"]=len(doi); r["DOI占比"]=round(len(doi)/n*100) if n else 0
    authc=Counter((e["author"].split(",")[0].strip()) for e in entries if e["author"])
    r["堆砌作者"]=[a for a,c in authc.items() if c>=3 and a]
    return r

def render(r):
    L=["===== D2 参考文献质量审查报告 ====="]
    L.append("总数=%d, 期刊=%d(%d%%), 图书=%d"%(r["总数"],r["期刊数"],round(r["期刊数"]/max(1,r["总数"])*100),r["图书数"]))
    L.append("近5年=%d(%d%%), 外文=%d(%d%%), DOI=%d(%d%%), 前沿度=%d"%(r["近5年"],r["近5年占比"],r["外文"],r["外文占比"],r["DOI"],r["DOI占比"],r["前沿度"]))
    if r["堆砌作者"]: L.append("教材堆砌嫌疑: "+",".join(r["堆砌作者"]))
    ok = r["总数"]>=15 and r["近5年占比"]>=40 and r["外文占比"]>=30 and r["前沿度"]>=50
    L.append("[D2 末行] " + ("✓ PASS 参考文献质量合格" if ok else "✗ 未达标(总数>=15, 近5年>=40%, 外文>=30%, 前沿度>=50)"))
    return "\n".join(L)

def hist(r):
    return "近5年=%d%%(>=40) 外文=%d%%(>=30) 期刊=%d%%(>=60) 前沿度=%d(>=50) DOI=%d%%"%(r["近5年占比"],r["外文占比"],round(r["期刊数"]/max(1,r["总数"])*100),r["前沿度"],r["DOI占比"])

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--tex",default="paper/main.tex")
    p.add_argument("--hist",action="store_true")
    p.add_argument("--suggest",action="store_true")
    a=p.parse_args(argv)
    entries=load_bib(a.tex)
    if not entries:
        print("[err] 未找到参考文献条目(缺 .bib 或 \\bibitem)"); return 1
    r=check(entries)
    print(hist(r) if a.hist else render(r))
    if a.suggest: print("-- 建议: 补近3年高被引期刊、补DOI、删未引用条目、增外文文献")
    return 0

if __name__=="__main__": sys.exit(main())
