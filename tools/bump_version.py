# -*- coding: utf-8 -*-
"""霞客经纬 · 全站版本号一步到位
用法: python tools/bump_version.py OLD NEW   （如 1 2）
范围: index.html sw.js 3d.html tests/*.html js/*.js（glob 全站 ?v=，勿手列清单——教训13）
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    old, new = sys.argv[1], sys.argv[2]
    targets = ["index.html", "sw.js", "3d.html"] + \
              sorted(glob.glob(os.path.join(ROOT, "tests", "*.html"))) + \
              sorted(glob.glob(os.path.join(ROOT, "js", "*.js")))
    n = 0
    for t in targets:
        p = t if os.path.isabs(t) else os.path.join(ROOT, t)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        s2 = s.replace(f"?v={old}", f"?v={new}")
        s2 = re.sub(r'VERSION = "v%s"' % re.escape(old), f'VERSION = "v{new}"', s2)
        if s2 != s:
            open(p, "w", encoding="utf-8", newline="").write(s2)
            n += 1
            print(f"bump {os.path.relpath(p, ROOT)}")
    print(f"共 {n} 文件 v{old} → v{new}")


if __name__ == "__main__":
    main()
