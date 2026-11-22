# -*- coding: utf-8 -*-
"""霞客经纬 · 滇黔补编 Phase 0 抓取（kanripo KR2k0135）
数据源: https://github.com/kanripo/KR2k0135
  文淵閣四庫全書本《徐霞客遊記》——楊名時重編訂十二卷（每卷上下）。
  提要自载：卷一名山诸篇；卷二以下西南遊記二十五篇
  （浙江江西一 / 湖广一 / 廣西六 / 貴州一 / 雲南十六），「所缺者一篇而已」
  ——卷十二下尾「(以下闕)」实证。raw.githubusercontent 曾瞬断：重试 5 次
  指数退避（学 fetch_text.py 重试范式；TPHY 站 kanripo 抓取同款）。
输出: data_raw/kr/KR2k0135_NNN.txt   mandoku 原文（UTF-8 原样存档）
用法: python tools/fetch_kr.py            # 断点续抓（已存在且非空跳过）
      python tools/fetch_kr.py --force
"""
import os
import sys
import time

import requests

BASE = "https://raw.githubusercontent.com/kanripo/KR2k0135/master"
FILES = [f"KR2k0135_{i:03d}" for i in range(0, 13)]     # _000.._012

SESSION = requests.Session()
SESSION.trust_env = False        # 环境代理不可靠——直连（同 fetch_text）
HEADERS = {
    "User-Agent": "XXK-Jingwei/0.1 (xuxiake digital-humanities site build; "
                  "kanripo archival fetch; contact: local builder)",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data_raw", "kr")
os.makedirs(OUT_DIR, exist_ok=True)


def fetch_one(fid: str, force: bool) -> str:
    path = os.path.join(OUT_DIR, f"{fid}.txt")
    if not force and os.path.exists(path) and os.path.getsize(path) > 200:
        return "缓存"
    url = f"{BASE}/{fid}.txt"
    last = None
    for attempt in range(5):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=40)
            r.raise_for_status()
            r.encoding = "utf-8"
            if len(r.text) < 500:
                raise RuntimeError(f"过短（{len(r.text)} 字节），疑路径变动")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(r.text)
            return f"{len(r.text):,}B"
        except Exception as e:
            last = e
            if attempt == 4:
                raise
            wait = 4 * (attempt + 1)          # 4/8/12/16s 指数退避（源曾瞬断）
            print(f"  重试 {fid}（第{attempt + 1}次）: {e} —— {wait}s 后再试")
            time.sleep(wait)
    raise last


def main():
    force = "--force" in sys.argv
    for fid in FILES:
        tag = fetch_one(fid, force)
        print(f"[{tag if tag in ('缓存',) else '抓取 ' + tag}] {fid}")
        if tag not in ("缓存",):
            time.sleep(1.0)                    # 礼貌限速（≥0.5s）
    total = sum(os.path.getsize(os.path.join(OUT_DIR, f + ".txt")) for f in FILES)
    print(f"\n{len(FILES)} 文件 · 共 {total:,} 字节 → data_raw/kr/")


if __name__ == "__main__":
    main()
