#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dashboard.py - D4 进度看板/风险评估 (abstract-polisher)"""
from __future__ import annotations
import argparse, datetime, os, sys, glob

VERSION="1.0.0"

STAGES=[
  ("读题分析","题干分析.md","README.md",2),
  ("建模设计","code","data",6),
  ("求解编码","results","results",24),
  ("绘图生成","figures","png",12),
  ("论文写作","paper/main.tex","paper",20),
  ("终稿交付","paper/main.pdf","pdf",8),
]

def detect_stage(root):
    """根据存在文件推断当前阶段 index."""
    idx=0
    if os.path.isfile(os.path.join(root,"题干分析.md")) or os.path.isfile(os.path.join(root,"README.md")): idx=1
    if os.path.isdir(os.path.join(root,"code")) or first_script(root): idx=2
    if count_files(os.path.join(root,"results"),("json","xlsx","npy"))>=3: idx=3
    if count_files(os.path.join(root,"figures"),("png","pdf"))>=6: idx=4
    if os.path.isfile(os.path.join(root,"paper","main.tex")): idx=5
    if os.path.isfile(os.path.join(root,"paper","main.pdf")): idx=6
    return min(idx,6)

def first_script(root):
    return bool(glob.glob(os.path.join(root,"**","*.py"),recursive=True))

def count_files(d,exts):
    if not os.path.isdir(d): return 0
    n=0
    for e in exts:
        n+=len(glob.glob(os.path.join(d,"**","*."+e),recursive=True))
    return n

def budget_hours_deadline(deadline):
    now=datetime.datetime.now().astimezone()
    dl=deadline if deadline.tzinfo else deadline.replace(tzinfo=now.tzinfo)
    left=(dl-now).total_seconds()/3600.0
    return left

def main(argv=None):
    p=argparse.ArgumentParser(description="D4 progress dashboard (abstract-polisher)")
    p.add_argument("--root",default=".")
    p.add_argument("--start",default=None,help="开题时间 YYYY-MM-DD HH:MM")
    p.add_argument("--deadline",default=None,help="截止时间(否则用假设72h)")
    p.add_argument("--watch",action="store_true")
    a=p.parse_args(argv)
    st=detect_stage(a.root)
    # 剩余时间
    if a.deadline:
        dl=datetime.datetime.strptime(a.deadline,"%Y-%m-%d %H:%M"); left=budget_hours_deadline(dl)
    elif a.start:
        stt=datetime.datetime.strptime(a.start,"%Y-%m-%d %H:%M")
        el=(datetime.datetime.now()-stt).total_seconds()/3600.0
        left=max(0,72-el)
    else:
        left=sys.maxsize
    L=["===== D4 进度看板/风险评估 ====="]
    if st>=6: L.append("当前阶段: 终稿交付(完成)")
    else: L.append("当前阶段: %s (index %d/6)"%(STAGES[st][0],st))
    L.append("剩余时间: %s h"%(("%.1f"%left) if left!=sys.maxsize else "未设置"))
    # 风险
    if left!=sys.maxsize:
        total_left=sum(s[3] for s in STAGES[st:])
        need=total_left
        if need>left: risk="CRITICAL"
        elif need>left*0.6: risk="HIGH"
        elif need>left*0.35: risk="MEDIUM"
        else: risk="LOW"
    else: risk="UNKNOWN"
    L.append("风险评估: "+risk)
    if risk in ("HIGH","CRITICAL"):
        L.append("建议: 砍改进模型部分, 保摘要+问题1+图表")
    L.append("[D4 末行] " + ("✓ PASS 风险<=MEDIUM" if risk in ("LOW","MEDIUM") else "✗ 风险=%s 需砍范围"%risk))
    print("\n".join(L))
    return 0

if __name__=="__main__": sys.exit(main())
