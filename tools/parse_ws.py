# -*- coding: utf-8 -*-
"""霞客经纬 · 附编收官 Phase 1（第三底本 ws：维基文库系通行本·季/李系）
输入: data_raw/ws/*.txt（fetch_ws.py 抓取）
输出: data/vol/043..051.txt   九篇纯净文本（简体化，一段一行）
      data/intermediate/ws_report.json  清点报告
口径:
  · 盤江考自 raylexlee 030.txt 切出（该文件 = ws 本「滇遊日記三」九月段 + 盤江考合体；
    验真标志：篇题「盤江考」行 + 「南北兩盤江，余於粵西已睹其下流」起 至 「類一丘之貉也夫」止）
  · 維基文庫腳注 [n] 剔除；△ 篇頭標記剔除；空行剔除
  · 繁→簡：opencc t2s + parse_kr 同款異體補表
  · 溯江紀源首行「(或作《江源考》)」為編者注 → 括號注化（intro，不入統計）；
    馄土仁敘為傳本付梓序，隨原文保留（如實聲明）
  · 系年從權：附編無確年，暫繫 1639（滇遊後）
"""
import json
import os
import re

import opencc

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_kr import VARIANTS  # 異體補表同源

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS_DIR = os.path.join(ROOT, "data_raw", "ws")
VOL_DIR = os.path.join(ROOT, "data", "vol")
OUT_REPORT = os.path.join(ROOT, "data", "intermediate", "ws_report.json")

CC = opencc.OpenCC("t2s")

# (slug, num, 站内题, year0, 起点, 终点)——盤江考用行标志切分，其余整文件
PIECES_WS = [
    ("panjiangkao", "043", "盘江考", 1639, "盤江考", None),
    ("sujiangjiyuan", "044", "溯江纪源", 1639, None, None),
    ("yongchangzhilue", "045", "永昌志略", 1639, None, None),
    ("fawangyuanqi", "046", "法王缘起", 1639, None, None),
    ("jintengzhuyi", "047", "近腾诸彝说略", 1639, None, None),
    ("jishanzhilue1", "048", "鸡山志略一", 1639, None, None),
    ("jishanzhilue2", "049", "鸡山志略二", 1639, None, None),
    ("jishanzhimu", "050", "鸡山志目", 1639, None, None),
    ("lijiangjilue", "051", "丽江纪略", 1639, None, None),
]

FOOTNOTE_RE = re.compile(r"\[\d+\]")


def to_simp(t: str) -> str:
    for k, v in VARIANTS.items():
        t = t.replace(k, v)
    return CC.convert(t)


def extract():
    report = {"pieces": []}
    for slug, num, title, year0, begin, end in PIECES_WS:
        raw = open(os.path.join(WS_DIR, f"{slug}.txt"), encoding="utf-8").read()
        lines = raw.split("\n")
        if begin:                       # 盤江考：自篇题行起切
            try:
                i = next(k for k, ln in enumerate(lines) if ln.strip().rstrip("△ ") == begin)
            except StopIteration:
                raise RuntimeError(f"{slug} 未见篇题「{begin}」——切分异常")
            lines = lines[i + 1:]
        if end:
            j = next((k for k, ln in enumerate(lines) if ln.strip().startswith(end)), None)
            if j is not None:
                lines = lines[:j]
        body = []
        for ln in lines:
            s = ln.strip().lstrip("△").strip()
            if not s:
                continue
            s = FOOTNOTE_RE.sub("", s)
            body.append(to_simp(s))
        if slug == "sujiangjiyuan" and body and body[0].startswith("(或作"):
            body[0] = "(" + body[0].strip("()") + ")"     # 规整为全括号注（intro）
        text = "\n".join(body)
        chars = len(text.replace("\n", ""))
        min_chars = 60 if slug != "panjiangkao" else 1500   # 盤江考全文约三千字
        if chars < min_chars:
            raise RuntimeError(f"{num} {title} 仅 {chars} 字（阈 {min_chars}）——验真/切分异常，请查 {slug}")
        with open(os.path.join(VOL_DIR, f"{num}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        report["pieces"].append({"num": num, "title": title, "slug": slug,
                                 "year0": year0, "source": "ws", "chars": chars,
                                 "head": text[:30]})
        print(f"[切] {num} {title}  {chars:>5} 字  首「{text[:22]}」")
    report["total_chars"] = sum(p["chars"] for p in report["pieces"])
    report["source"] = ("ws = 维基文库系通行本（季梦良/李介系）：michiboo/Classical_Chinese_Wikisource 镜像"
                        " + raylexlee TTS 语料（盤江考自 030.txt 切出验真）")
    report["caveat"] = ("ws 为通行本口径（非四库），与 kr 有版本源流之别；附编系年从权（暂系 1639）；"
                        "溯江纪源含馄土仁付梓叙（随原文保留）；考体文非日记，不设日条与锚点")
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"\n{len(report['pieces'])} 篇 · {report['total_chars']:,} 字 → data/vol/ · 报告 ws_report.json")


if __name__ == "__main__":
    extract()
