# -*- coding: utf-8 -*-
"""霞客经纬 · lint（确定性检查，失败即红）
用法: python tools/lint.py
类别（承方舆/水道经纬 lint 哲学——文字指令与 lint 冲突时 lint 是对的）：
  1  版本一致性   index/sw/js/3d 的 ?v= 全等于 sw.js VERSION
  2  资源存在性   index.html 引用的 script/css 存在；sw SHELL_FILES 全部存在
  3  数据哨兵     游程=22 · 日条≥480 · 锚定≥280 · 覆盖≥55% · 原文 20-26 万字
                 地名表≥250 · 可信里程≥10000km · stats.js 与 trips.json 同口径
  4  禁用模式     map.fire("click") / innerHTML.indexOf 验证 / window._ftw / git mv -q / || true
  5  Worker 纯净  ftworker.js 不引用 document/window
  6  深链一致     app.js 深链语法（#trip=/#t=/#m=）
  7  manifest     icons 存在
  8  游线连续性   跳段 ≤ 4（现基线 2：闽游后回杭州、粤西二真仙岩折返）
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def main():
    # ── 1 版本一致性 ──
    sw = read("sw.js")
    mver = re.search(r'VERSION = "v(\d+)"', sw)
    ok(mver, "sw.js 缺 VERSION 常量")
    ver = mver.group(1) if mver else ""
    files = ["index.html", "sw.js", "3d.html"] + \
            ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]
    for f in files:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        for bad in set(re.findall(r"\?v=(\d+)", t)):
            ok(bad == ver, f"{f} 含过期版本 ?v={bad}（当前 v{ver}）——版本 bump 用脚本全站替换")

    # ── 2 资源存在性 ──
    idx = read("index.html")
    for src in re.findall(r'(?:src|href)="([^"#?]+)(?:\?[^"]*)?"', idx):
        if src.startswith(("http", "data:")):
            continue
        ok(os.path.exists(os.path.join(ROOT, src)), f"index.html 引用缺失: {src}")
    for m2 in re.finditer(r'"(\./[^"]+?)(?:\?[^"]*)?"', sw):
        rel = m2.group(1)[2:]
        ok(os.path.exists(os.path.join(ROOT, rel)), f"sw SHELL_FILES 缺失: {rel}")

    # ── 3 数据哨兵 ──
    trips = json.load(open(os.path.join(ROOT, "data/intermediate/trips.json"), encoding="utf-8"))
    m = trips["meta"]
    ok(m["pieces"] == 22, f"游程 {m['pieces']} ≠ 22")
    ok(m["days"] >= 480, f"日条 {m['days']} < 480")
    ok(m["anchored"] >= 280, f"锚定 {m['anchored']} < 280")
    ok(m["coverage"] >= 55, f"锚覆盖率 {m['coverage']}% < 55%")
    ok(200000 <= m["charsOrig"] <= 260000, f"原文字数 {m['charsOrig']} 越界 20-26 万")
    ok(m["gazetteer"] >= 250, f"地名表 {m['gazetteer']} < 250")
    ok(m["kmTotal"] >= 10000, f"可信里程 {m['kmTotal']} < 10000 km")
    ok(m["confQu"] + m["confTui"] == m["anchored"], "置信计数与锚定数不一致")
    # stats.js 同口径
    sj = read("data/stats.js")
    mm = re.search(r'"charsOrig":(\d+)', sj)
    ok(mm and int(mm.group(1)) == m["charsOrig"], "stats.js 与 trips.json 字数口径不一致——重跑 build_stats.py")
    ok('"kmTotal":%d' % m["kmTotal"] in sj, "stats.js 里程口径不一致——重跑 build_stats.py")
    # 阅读层/检索层文件齐
    for i in range(22):
        ok(os.path.exists(os.path.join(ROOT, f"data/read/{i:03d}.js")), f"data/read/{i:03d}.js 缺失")
        ok(os.path.exists(os.path.join(ROOT, f"data/text/p{i + 1:02d}.js")), f"data/text/p{i + 1:02d}.js 缺失")

    # ── 4 折线连续性（跳段基线） ──
    jumps = sum(1 for t in trips["trips"] for dd in t["days"] if dd["jump"])
    ok(jumps <= 4, f"跳段 {jumps} > 基线 4")

    # ── 5 禁用模式 ──
    banned = [
        (r'map\.fire\(\s*["\']click', "map.fire(click) 委托分发不可靠——用 canvas.dispatchEvent"),
        (r'innerHTML\.indexOf\(', "innerHTML.indexOf 验证会因 & 序列化失效——用 textContent"),
        (r'window\._ft', "闭包 let 量不在 window 上——用存取函数"),
        (r'git mv -q', "git mv 无 -q flag"),
        (r'\|\|\s*true', "|| true 兜底吞错（教训 20）"),
    ]
    jss = ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]
    for f in jss:
        t = open(f if os.path.isabs(f) else os.path.join(ROOT, f), encoding="utf-8").read()
        for pat, why in banned:
            ok(not re.search(pat, t), f"{f} 触禁：{why}")

    # ── 6 Worker 纯净 ──
    w = read("js/ftworker.js")
    ok("document" not in w and "window" not in w, "ftworker.js 引用 DOM（Worker 无 DOM）")

    # ── 7 深链一致 ──
    app = read("js/app.js")
    for frag in ["#trip=", "#t=", "#m="]:
        ok(frag in app or frag.replace("#", "") in app, f"app.js 深链语法缺 {frag}")

    # ── 8 manifest ──
    mani = read("manifest.json")
    for icon in re.findall(r'"src":\s*"(icons/[^"]+)"', mani):
        ok(os.path.exists(os.path.join(ROOT, icon)), f"manifest 引用图标缺失: {icon}")

    # ── 9 3D 页存在与版本（index 底栏入口） ──
    ok(os.path.exists(os.path.join(ROOT, "3d.html")), "3d.html 缺失（index 底栏形胜入口指向它）")
    ok("tdlink" in idx, "index.html 缺 3D 入口（#tdlink）")

    # ── 报告 ──
    print(f"lint：{checks} 项检查")
    if fails:
        print(f"✗ {len(fails)} 项失败：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✓ 全绿")


if __name__ == "__main__":
    main()
