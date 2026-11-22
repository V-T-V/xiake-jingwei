# -*- coding: utf-8 -*-
"""霞客经纬 · 附编收官 Phase 0（第三底本 ws：维基文库系通行本）
源 1: michiboo/Classical_Chinese_Wikisource（维基文库镜像）「徐霞客遊記/」
      溯江紀源 + 杂著七件（永昌志略/法王緣起/近騰諸彜說略/雞山志略一二/雞山志目/麗江紀略）
源 2: raylexlee/raylexlee.github.io  zhtts/text/徐霞客遊記/030.txt —— 盤江考
      （维基文库系 TTS 语料；抓后由 parse_ws 验真：非盤江考正文即弃并如实报缺）
输出: data_raw/ws/<slug>.txt  原档 UTF-8 存档（gitignore 同 data_raw/）
用法: python tools/fetch_ws.py [--force]
"""
import os
import sys
import time
import urllib.parse

import requests

MICHIBOO = ("https://raw.githubusercontent.com/michiboo/Classical_Chinese_Wikisource/"
            "master/%E5%BE%90%E9%9C%9E%E5%AE%A2%E9%81%8A%E8%A8%98/")   # 徐霞客遊記/
RAYLEX = "https://raw.githubusercontent.com/raylexlee/raylexlee.github.io/master/zhtts/text/%E5%BE%90%E9%9C%9E%E5%AE%A2%E9%81%8A%E8%A8%98/"

# (slug, repo_base, 远端名)
FILES = [
    ("panjiangkao", RAYLEX, "030.txt"),
    ("sujiangjiyuan", MICHIBOO, "溯江紀源.txt"),
    ("yongchangzhilue", MICHIBOO, "永昌志略.txt"),
    ("fawangyuanqi", MICHIBOO, "法王緣起.txt"),
    ("jintengzhuyi", MICHIBOO, "近騰諸彜說略.txt"),
    ("jishanzhilue1", MICHIBOO, "雞山志略一.txt"),
    ("jishanzhilue2", MICHIBOO, "雞山志略二.txt"),
    ("jishanzhimu", MICHIBOO, "雞山志目.txt"),
    ("lijiangjilue", MICHIBOO, "麗江紀略.txt"),
]

SESSION = requests.Session()
SESSION.trust_env = False
HEADERS = {
    "User-Agent": "XXK-Jingwei/0.1 (xuxiake digital-humanities site build; "
                  "wikisource-mirror archival fetch; contact: local builder)",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data_raw", "ws")
os.makedirs(OUT_DIR, exist_ok=True)


def fetch(slug, base, name, force):
    path = os.path.join(OUT_DIR, f"{slug}.txt")
    if not force and os.path.exists(path) and os.path.getsize(path) > 100:
        return "缓存"
    url = base + urllib.parse.quote(name)
    last = None
    for attempt in range(5):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=40)
            r.raise_for_status()
            r.encoding = "utf-8"
            if len(r.text) < 80:
                raise RuntimeError(f"过短（{len(r.text)} 字）")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(r.text)
            return f"{len(r.text):,}B"
        except Exception as e:
            last = e
            if hasattr(e, "response") and e.response is not None and 400 <= e.response.status_code < 500:
                raise                     # 4xx 确定性失败——重试无益，直接红
            if attempt == 4:
                raise
            wait = 4 * (attempt + 1)
            print(f"  重试 {slug}（第{attempt + 1}次）: {e} —— {wait}s 后再试")
            time.sleep(wait)
    raise last


def main():
    force = "--force" in sys.argv
    for slug, base, name in FILES:
        tag = fetch(slug, base, name, force)
        print(f"[{'缓存' if tag == '缓存' else '抓取 ' + tag}] {slug} ← {name}")
        if tag != "缓存":
            time.sleep(1.0)
    print(f"\n{len(FILES)} 文件 → data_raw/ws/")


if __name__ == "__main__":
    main()
