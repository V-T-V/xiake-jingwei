"""霞客经纬 · Phase 0 文本抓取
数据源: http://www.guoxue123.com/shibu/0301/00xxkyj/  (国学导航 · 徐霞客游记)
  —— 源探测记录(2026-11-21): zh.wikisource.org 本网络 TLS 握手超时(不可达);
     guwendao.net 需登录(302→DefaultGwd.aspx); guoxuedashi.net 域名已改投影视站;
     国学导航 HTTP 可达, 版本为通行「前半部」22 篇(000-021, 止于粤西游日记二)。
     缺后半(粤游三四·黔游·滇游·附编)在 README/站内「关于」如实标注。
输出:   data_raw/NNN.html          原始页面(GB18030→UTF-8 转存)
        data/vol/NNN.txt          每篇纯净 UTF-8 文本（段落以 \n 分隔）
        data/fetch_report.json    字数/段落盘点
用法:   python tools/fetch_text.py          # 断点续抓（已存在且非空则跳过）
        python tools/fetch_text.py --force # 全部重抓
"""
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "http://www.guoxue123.com/shibu/0301/00xxkyj"

# 本机环境代理(127.0.0.1:58319)已死而 curl 直连可达——会话禁用环境代理
SESSION = requests.Session()
SESSION.trust_env = False
# 自报家门（诚实 UA：本项目为数字人文建站，限速抓取）
HEADERS = {
    "User-Agent": "XXK-Jingwei/0.1 (xuxiake digital-humanities site build; "
                  "one-shot archival fetch; contact: local builder)",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data_raw")
VOL_DIR = os.path.join(ROOT, "data", "vol")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(VOL_DIR, exist_ok=True)

# 篇目（国学导航本顺序，即游记通行编次；解析自目录页 gx_xxkyj_idx.html）
PIECES = [
    ("000", "游天台山日记"), ("001", "游雁宕山日记"), ("002", "游白岳山日记"),
    ("003", "游黄山日记"), ("004", "游武彝山日记"), ("005", "游庐山日记"),
    ("006", "游黄山日记后"), ("007", "游九鲤湖日记"), ("008", "游嵩山日记"),
    ("009", "游太华山日记"), ("010", "游太和山日记"), ("011", "闽游日记前"),
    ("012", "闽游日记后"), ("013", "游天台山日记后"), ("014", "游雁宕山日记后"),
    ("015", "游五台山日记"), ("016", "游恒山日记"), ("017", "浙游日记"),
    ("018", "江右游日记"), ("019", "楚游日记"), ("020", "粤西游日记一"),
    ("021", "粤西游日记二"),
]

# 页面噪音行（导航/版权）——按精确匹配或前缀剔除
NOISE_EXACT = {
    "上一页", "目录页", "下一页", "首页", "国学导航", "经部", "史部", "子部", "集部",
    "专题", "今人新著", "",
    "Powered by www.guoxue123.com  © Copyright 2006. All rights reserved",
}
NOISE_RE = re.compile(r"^(徐霞客游记（明）徐宏祖|徐霞客游记|图文本导航)")
TITLE_RE = re.compile(r"^.{1,14}-徐霞客游记（明）徐宏祖_国学导航$")


def clean_html(html: str, num: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    titles = {t for _, t in PIECES} | {t[:-1] + "(后)" for _, t in PIECES if t.endswith("后")}
    lines = []
    for ln in text.split("\n"):
        ln = ln.replace("\u3000", "").replace("\xa0", "").strip()
        if ln in NOISE_EXACT or ln in titles or NOISE_RE.match(ln) or TITLE_RE.match(ln):
            continue
        if set(ln) <= {"－", "-", "—"}:
            continue
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def reclean(force_all: bool):
    """从 data_raw/*.html 重新清洗（不发网络请求）"""
    report = []
    for num, title in PIECES:
        raw_path = os.path.join(RAW_DIR, f"{num}.html")
        txt_path = os.path.join(VOL_DIR, f"{num}.txt")
        if not os.path.exists(raw_path):
            print(f"[缺] {num} 无原始页，跳过")
            continue
        body = clean_html(open(raw_path, encoding="utf-8").read(), num)
        if len(body) < 300:
            raise RuntimeError(f"{num} 清洗后仅 {len(body)} 字")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(body)
        report.append({"num": num, "title": title,
                       "chars": len(body.replace("\n", "")),
                       "paras": body.count("\n") + 1, "cached": True})
        print(f"[重洗] {num} {title}  {report[-1]['chars']:>6} 字")
    total = sum(r["chars"] for r in report)
    out = {"source": BASE, "source_note": "国学导航本为前半部22篇，止于粤西游日记二",
           "vols": report, "total_chars": total,
           "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n合计 {total} 字（{len(report)} 篇）→ data/fetch_report.json")


def fetch_one(num: str, title: str, force: bool) -> dict:
    txt_path = os.path.join(VOL_DIR, f"{num}.txt")
    raw_path = os.path.join(RAW_DIR, f"{num}.html")
    if not force and os.path.exists(txt_path) and os.path.getsize(txt_path) > 200:
        with open(txt_path, encoding="utf-8") as f:
            body = f.read()
        return {"num": num, "title": title, "chars": len(body.replace("\n", "")),
                "paras": body.count("\n") + 1, "cached": True}
    url = f"{BASE}/{num}.htm"
    for attempt in range(3):
        try:
            resp = SESSION.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  重试 {num}: {e}")
            time.sleep(3 * (attempt + 1))
    resp.encoding = "gb18030"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(resp.text)          # 保留原始页面（转码后）供复查
    body = clean_html(resp.text, num)
    if len(body) < 300:
        raise RuntimeError(f"{num}.htm 清洗后仅 {len(body)} 字，疑似版式变化，请人工检查 {raw_path}")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(body)
    return {"num": num, "title": title, "chars": len(body.replace("\n", "")),
            "paras": body.count("\n") + 1, "cached": False}


def main():
    if "--reclean" in sys.argv:
        reclean(True)
        return
    force = "--force" in sys.argv
    report = []
    for num, title in PIECES:
        info = fetch_one(num, title, force)
        tag = "缓存" if info["cached"] else "抓取"
        print(f"[{tag}] {num} {info['title']}  {info['chars']:>6} 字  {info['paras']:>3} 段")
        report.append(info)
        if not info["cached"]:
            time.sleep(0.8)   # 礼貌抓取（≥0.5s）
    total = sum(r["chars"] for r in report)
    out = {"source": BASE, "source_note": "国学导航本为前半部22篇，止于粤西游日记二",
           "vols": report, "total_chars": total,
           "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n合计 {total} 字（22 篇）→ data/fetch_report.json")


if __name__ == "__main__":
    main()
