# -*- coding: utf-8 -*-
"""霞客经纬 · Phase 2 游程构建（锚点匹配 + 游线 + 里程 + 前端产物）
输入: data/intermediate/trips_raw.json · tools/gazetteer.py
输出: data/intermediate/trips.json      全量结构化（stats/tests 用）
      data/trip_data.js                 前端轻量层 const XXK
      data/read/NN.js                   循程阅读层（22 篇懒加载，XXK_READ[num]）
      data/text/pNN.js                  全文检索层（22 片懒加载，XXKTEXT[n]）
匹配法: 逐日扫（scope 过滤后的）地名表，取首个「非前一锚点名」命中为当日锚；
        命中集合全部存入 day.places。坐标全标 src:"derived"（今地常识定位）。
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gazetteer import entries  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "intermediate", "trips_raw.json")

PAREN = re.compile(r"（[^（）]*）|\([^()]*\)")

# 游程配色（绢面低饱和系，青→绛轮转；43 篇两轮错相）
PALETTE = ["#7a3b2e", "#8a5a2b", "#6b6b2d", "#446b35", "#2f6b5e", "#2f5d70",
           "#3c4f7d", "#5d4a7d", "#7d4a6b", "#6e3b4b", "#24495a", "#2f6e63",
           "#57805f", "#5a8368", "#9a6b3f", "#b08d4f", "#8e2b22", "#3d6b7d",
           "#4a7a9b", "#4a6d8c", "#33658a", "#46664f",
           "#6e4a2e", "#75603a", "#5a6b3a", "#3d5b48", "#2b5a52", "#44586b",
           "#5b4a6b", "#6b4a58", "#58404a", "#3a4a52", "#4a6258", "#6b755f",
           "#7a6a52", "#8e7444", "#6e3230", "#35566b", "#52687b", "#5f6b52"]


def hav(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(h))


def clean_text(paras):
    """去括号注释的正文（匹配与统计用；跨段括号状态机——注释可断行）"""
    out = []
    depth = 0
    for ch in "".join(paras):
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            if depth > 0:
                depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def strip_for_search(text):
    return PAREN.sub("", text)


def build():
    gaz = entries()
    raw = json.load(open(RAW, encoding="utf-8"))
    trips, meta_days, anchored, total_km = [], 0, 0, 0.0
    chars_orig, chars_note = 0, 0

    for idx, p in enumerate(raw["pieces"]):
        num = p["num"]
        gz = [g for g in gaz if g["scope"] is None or num in g["scope"]]
        # 名+别名展开，长名优先（先长后短避免「天台山」被「天台」截走）
        toks = []
        for g in gz:
            for t in [g["name"]] + g["aliases"]:
                toks.append((t, g))
        toks.sort(key=lambda x: -len(x[0]))

        days_out, path, prev_name, prev_pos = [], [], None, None
        cum_km = 0.0
        for d in p["days"]:
            body = clean_text(d["paras"])
            full = "".join(d["paras"])
            chars_orig += len(body)
            chars_note += len(full) - len(body)
            hits = {}
            for tok, g in toks:
                pos = body.find(tok)
                if pos >= 0 and g["name"] not in hits:
                    hits[g["name"]] = (pos, tok, g)
            ordered = sorted(hits.values(), key=lambda x: x[0])
            places = [h[2]["name"] for h in ordered]
            anchor = None
            for pos, tok, g in ordered:
                if g["name"] != prev_name:
                    anchor = g
                    break
            day_km = None
            jump = False
            if anchor:
                prev_name = anchor["name"]
                pos_pt = [anchor["lat"], anchor["lon"]]
                if prev_pos is not None:
                    seg = hav(prev_pos, pos_pt)
                    jump = seg > 400
                    cum_km += seg
                    day_km = round(cum_km)
                else:
                    day_km = 0
                prev_pos = pos_pt
                path.append(pos_pt)
                anchored += 1
            days_out.append({
                "h": d["h"], "y": d["y"], "m": d["m"], "d": d["d"],
                "anchor": ({"name": anchor["name"], "pos": [anchor["lat"], anchor["lon"]],
                            "today": anchor["today"], "basis": anchor["basis"],
                            "conf": anchor["conf"], "src": anchor["src"]}
                           if anchor else None),
                "places": places, "km": day_km, "jump": jump,
                "chars": len(body),
            })
            meta_days += 1
        # 折线总长（含跳段剔除后的「可信里程」另算）
        km_all = sum(hav(path[i], path[i + 1]) for i in range(len(path) - 1)) if len(path) > 1 else 0
        # 可信里程：剔除 >400km 跳段
        km_ok = 0.0
        for i in range(len(path) - 1):
            seg = hav(path[i], path[i + 1])
            if seg <= 400:
                km_ok += seg
        total_km += km_ok
        y0 = p["year0"]
        ys = [d["y"] for d in days_out if d["y"]]
        ylabel = f"{min(ys)}" if ys and min(ys) == max(ys) else f"{min(ys)}–{max(ys)}" if ys else str(y0)
        trips.append({
            "id": f"t{idx + 1:02d}", "num": num, "title": p["title"],
            "source": p.get("source", "gx"),          # 双底本：gx=国学导航 / kr=四库楊名時
            "year": ylabel, "year0": min(ys) if ys else y0,
            "color": PALETTE[idx % len(PALETTE)],
            "days": days_out, "path": path,
            "stats": {"days": len(days_out),
                      "anchored": sum(1 for d in days_out if d["anchor"]),
                      "km": round(km_ok), "kmAll": round(km_all),
                      "chars": sum(d["chars"] for d in days_out),
                      "ganzhi": p.get("ganzhi")},
        })

    inter = {"meta": {
        "pieces": len(trips), "days": meta_days,
        "anchored": anchored, "coverage": round(anchored / meta_days * 100, 1),
        "kmTotal": round(total_km),
        "charsOrig": chars_orig, "charsNote": chars_note,
        "gazetteer": len(gaz),
        "confQu": sum(1 for d in [d for t in trips for d in t["days"]] if d["anchor"] and d["anchor"]["conf"] == "确"),
        "confTui": sum(1 for d in [d for t in trips for d in t["days"]] if d["anchor"] and d["anchor"]["conf"] == "推"),
    }, "trips": trips}
    with open(os.path.join(ROOT, "data", "intermediate", "trips.json"), "w", encoding="utf-8") as f:
        json.dump(inter, f, ensure_ascii=False, indent=1)

    # 前端轻量层（不含 paras）
    light = {k: v for k, v in inter.items()}
    with open(os.path.join(ROOT, "data", "trip_data.js"), "w", encoding="utf-8") as f:
        f.write("/* 霞客经纬 · 游程结构数据 · build_trip_data.py 生成，勿手改 */\n")
        f.write("const XXK = " + json.dumps(light, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # 阅读层 + 检索层（每篇一文件）
    read_dir = os.path.join(ROOT, "data", "read")
    text_dir = os.path.join(ROOT, "data", "text")
    os.makedirs(read_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)
    for idx, p in enumerate(raw["pieces"]):
        read = {"num": p["num"], "title": p["title"], "intro": p["intro"],
                "days": [{"h": d["h"], "paras": d["paras"]} for d in p["days"]]}
        with open(os.path.join(read_dir, f"{p['num']}.js"), "w", encoding="utf-8") as f:
            f.write(f"/* 霞客经纬 · {p['title']} · 循程阅读层 · 懒加载 */\n")
            f.write('(window.XXK_READ=window.XXK_READ||{})["' + p["num"] + '"]='
                    + json.dumps(read, ensure_ascii=False, separators=(",", ":")) + ";\n")
        plain = strip_for_search(open(os.path.join(ROOT, "data", "vol", f"{p['num']}.txt"),
                                      encoding="utf-8").read())
        with open(os.path.join(text_dir, f"p{idx + 1:02d}.js"), "w", encoding="utf-8") as f:
            f.write(f"/* 徐霞客游记 · 第{idx + 1}篇 {p['title']} · 懒加载（注释已剔） */\n")
            f.write('(window.XXKTEXT=window.XXKTEXT||{})[' + str(idx + 1) + ']='
                    + json.dumps(plain, ensure_ascii=False) + ";\n")

    m = inter["meta"]
    print(f"游程 {m['pieces']} · 日条 {m['days']} · 锚定 {m['anchored']}"
          f"（覆盖 {m['coverage']}% · 确 {m['confQu']} / 推 {m['confTui']}）")
    print(f"可信里程合计 {m['kmTotal']} km · 原文 {m['charsOrig']:,} 字 · 注释 {m['charsNote']:,} 字")
    for t in trips:
        print(f"  {t['id']} {t['title']:<10} {t['year']}  {t['stats']['days']:>3} 日"
              f"  锚 {t['stats']['anchored']:>3}  {t['stats']['km']:>5} km  {t['stats']['chars']:>6} 字")


if __name__ == "__main__":
    build()
