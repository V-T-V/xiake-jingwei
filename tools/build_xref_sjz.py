# -*- coding: utf-8 -*-
"""霞客经纬 × 水道经纬 · 互查桥构建（第六座桥；SDJW 只读，绝不写入）
霞客 52 篇语料（三源）× SDJW 水道谱（112 水道）：
  A 计入：霞客写法 → 水经水道（forms 支持篇域限定，如「大河」仅溯江纪源=黄河）
  B 消歧排除：单字泛称（江/河）· 泛指（江水/河水/涧水）· 普通词序（若水）
    · 人名假阳（沂水=黄沂水·滇中人；淮河=罗坡淮氏·江右所访）
    · 地名截搭（潜水=於潜县+水）
  C 水经谱无对应（如实）：盘江水系/澜沧江等明清水名——成书早千二百年，
    霞客《盘江考》《溯江纪源》正补其阙（学术叙事点，非缺陷）
  D 主题对读特辑：溯江纪源「岷山导江之辨」× 水经注·江水（卷33/34）——
    关键词岷山/禹贡/导江双侧脚本截句，人只选题
输出: data/xref_sjz.js —— window.XXK_SJZ（js/xrefsjz.js「水经」页签懒加载）
深链: ../SDJW/#r=<水道id>（相对兄弟路径——父目录同根服务约定）
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDJW = os.path.join(os.path.dirname(ROOT), "SDJW")   # 只读
SITE = "../SDJW/"

# ── A 计入表：(水经名, [form 或 (form, 限定篇num)], 注记) ──
WATERS = [
    ("河水", ["黄河", ("大河", ["044"])],
     "「大河」黔滇诸篇乃盘江水系俗称，仅溯江纪源之「大河即黄河」计入；河/河水泛称不计"),
    ("江水", ["大江", "长江", "金沙江"],
     "水经谱无「金沙江」之名——霞客《溯江纪源》考为江源正干，归江水系叙事计入"),
    ("湘水", ["湘江", "湘水"], None),
    ("漓水", ["漓江", "漓水"], None),
    ("赣水", ["赣江", "赣水"], None),
    ("渐江水", ["浙江"], "渐江水即钱塘江，霞客称浙江"),
    ("洛水", ["洛水"], "嵩山游记亲渡洛水"),
    ("伊水", ["伊水"], "嵩山游记伊阙所见"),
]

# ── B 消歧排除（如实注记，学伽蓝站「决水种麦」法） ──
EXCLUDED = [
    ("江", 0, "单字泛称（凡江皆称江），短语级不可消歧，不计"),
    ("河", 0, "单字泛称，同上"),
    ("江水", 15, "多泛指江中之水（「江水涨」类），保守不计"),
    ("河水", 5, "泛指河水，保守不计"),
    ("大河", 0, "黔滇诸篇（024/025/026）为盘江水系俗称——非黄河，不计（044 计入河水）"),
    ("涧水", 13, "山涧之水泛称，非水经卷十五涧水（新安）"),
    ("若水", 4, "普通词序（「若水」= 如水），非雅砻江古名（承伽蓝站同类排除）"),
    ("沂水", 5, "人名假阳：滇中黄沂水（唐大来之友），非山东沂水"),
    ("淮河", 2, "人名假阳：罗坡淮氏（江右游所访之友），非淮水"),
    ("潜水", 1, "地名截搭：於潜县+水（临安），非水经卷二十九潜水（四川）"),
    ("沅水", 0, "楚游未及（水经卷三十七之沅水，霞客语料零出现）"),
    ("澧水", 0, "同上，零出现"),
]

# ── C 水经谱无对应（明清水名·水经未及，如实计） ──
NO_CORR = [
    ("盘江水系", ["盘江", "南盘", "北盘", "南盘江", "北盘江"],
     "《盘江考》所考南北二盘源流——水经注未及西南盘江水系，霞客正补千二百年之阙"),
    ("都泥江", ["都泥江"], "北盘江下游古称"),
    ("郁江", ["郁江"], "粤西郁水（水经之郁水在今缅甸/滇西南，与此非一）"),
    ("右江", ["右江"], None),
    ("左江", ["左江"], None),
    ("柳江", ["柳江"], None),
    ("龙江", ["龙江"], "黔桂多条同名小水"),
    ("浔江", ["浔江"], None),
    ("榕江", ["榕江"], None),
    ("黔江", ["黔江"], None),
    ("澜沧江", ["澜沧江"], "《溯江纪源》并举之南江下流——水经注以澜沧为不出中国，未立水道"),
    ("灵渠", ["灵渠"], "秦凿渠，湘漓分背之枢纽——霞客亲历（水经湘漓二注间未立渠名）"),
]

# ── D 对读特辑关键词（人只选题，句皆脚本截） ──
PAIR_KEYS = ["岷山", "禹贡", "导江"]

PIECES = [(f"{i:03d}",) for i in range(52)]
TITLES = {}   # num → (title, source) 从 trips_raw.json


def load_const(path, const):
    t = io.open(path, encoding="utf-8").read()
    head = f"const {const} = "
    i = t.find(head)
    assert i >= 0, f"缺 const {const}"
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def strip_notes(t):
    out, depth = [], 0
    for ch in t.replace("\r", "").replace("\n", ""):
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            if depth > 0:
                depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def ctx_of(text, i, before=40, after=52):
    return text[max(0, i - before):i + after].replace("\n", "")


def main():
    if not os.path.isdir(SDJW):
        raise SystemExit("未找到姊妹站 D:/W_A_W/SDJW（互查桥需要其数据，只读）")
    sjz = load_const(os.path.join(SDJW, "data", "river_data.js"), "SJZ")
    secs = load_const(os.path.join(SDJW, "data", "sections.js"), "SJZ_SECTIONS")
    wid = {w["name"]: w for w in sjz["waterways"]}

    raw = json.load(io.open(os.path.join(ROOT, "data/intermediate/trips_raw.json"), encoding="utf-8"))
    for p in raw["pieces"]:
        TITLES[p["num"]] = (p["title"], p.get("source", "gx"))
    corpus = {}
    for num, in PIECES:
        t = io.open(os.path.join(ROOT, "data", "vol", f"{num}.txt"), encoding="utf-8").read()
        corpus[num] = strip_notes(t)

    # ── A：水道计数 + 样例 ──
    waters_out = []
    for name, forms, note in WATERS:
        w = wid.get(name)
        if not w:
            raise RuntimeError(f"SDJW 无水道 {name}")
        n = 0
        per_piece = {}
        samples = []
        for f in forms:
            if isinstance(f, tuple):
                f, only = f
                targets = only
            else:
                targets = list(corpus.keys())
            for num in targets:
                c = corpus[num].count(f)
                if c:
                    n += c
                    per_piece[num] = per_piece.get(num, 0) + c
                    for m in list(re.finditer(re.escape(f), corpus[num]))[:1]:
                        if len(samples) < 3:
                            samples.append({"form": f, "piece": TITLES[num][0],
                                            "ctx": ctx_of(corpus[num], m.start())})
        waters_out.append({
            "name": name, "sjzId": w["id"], "vols": w["vols"],
            "forms": [f if isinstance(f, str) else f[0] for f in forms],
            "n": n, "pieces": len(per_piece), "note": note or "",
            "href": f"{SITE}#r={w['id']}",
            "samples": samples,
        })

    # ── B：排除计数（EXCLUDED n=0 者实时计） ──
    allt = "".join(corpus.values())
    excluded_out = []
    for nm, n, why in EXCLUDED:
        if n == 0:
            n = allt.count(nm)
        excluded_out.append({"name": nm, "n": n, "why": why})

    # ── C：无对应计数 ──
    noco_out = []
    for nm, forms, why in NO_CORR:
        n = sum(allt.count(f) for f in forms)
        noco_out.append({"name": nm, "forms": forms, "n": n, "why": why or ""})

    # ── 按篇分组（A 侧命中） ──
    by_trip = []
    for num, in PIECES:
        title, src = TITLES[num]
        hits = []
        for wo in waters_out:
            for f in wo["forms"]:
                c = corpus[num].count(f)
                if c:
                    m = re.search(re.escape(f), corpus[num])
                    hits.append({"water": wo["name"], "form": f, "n": c,
                                 "ctx": ctx_of(corpus[num], m.start()) if m else "",
                                 "href": wo["href"]})
        hits.sort(key=lambda h: -h["n"])
        by_trip.append({"id": f"t{int(num) + 1:02d}", "num": num, "title": title,
                        "source": src, "n": sum(h["n"] for h in hits),
                        "hits": hits[:3]})

    # ── D：对读特辑（溯江纪源 × 江水注·经注全文） ──
    xk = corpus["044"]
    sjz_txt = "".join(b.get("j", "") + "".join(b.get("z", []))
                      for sec in w_vols_secs(wid["江水"], secs)
                      for b in sec.get("body", []))
    pairs = []
    for key in PAIR_KEYS:
        xk_sent = first_sentence_with(xk, key)
        sjz_sent = first_sentence_with(sjz_txt, key)
        if xk_sent and sjz_sent:
            pairs.append({"topic": key, "xk": xk_sent, "sjz": sjz_sent,
                          "xkHref": "#trip=t44&d=0",
                          "sjzHref": f"{SITE}#r={wid['江水']['id']}"})

    totals = {
        "watersMatched": len(waters_out),
        "waterMentions": sum(w["n"] for w in waters_out),
        "excluded": len(excluded_out),
        "noCorr": sum(w["n"] for w in noco_out),
        "pairs": len(pairs),
    }
    out = {
        "site": SITE,
        "generated": "tools/build_xref_sjz.py（SDJW 只读）",
        "note": "霞客（1587-1641）与郦道元（卒 527）隔千余年同问「水从何来」——"
                "溯江纪源驳「岷山导江」而推金沙，盘江考穷南北二盘之源，皆水经未详之地。"
                "深链为相对兄弟路径，须父目录同根服务（README 注明）。",
        "sdjw": {"waterways": sjz["meta"]["waterways"], "sections": sjz["meta"]["sections"],
                 "vols": sjz["meta"]["vols"]},
        "waters": waters_out,
        "excluded": excluded_out,
        "noCorrespondence": noco_out,
        "byTrip": by_trip,
        "feature": {"title": "溯江纪源 × 江水注 · 岷山导江之辨", "pairs": pairs},
        "totals": totals,
    }
    with io.open(os.path.join(ROOT, "data", "xref_sjz.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 霞客经纬 × 水道经纬 互查桥 · tools/build_xref_sjz.py 生成，勿手改（SDJW 只读） */\n")
        f.write("window.XXK_SJZ = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

    t = totals
    print(f"✓ data/xref_sjz.js")
    print(f"  匹配 {t['watersMatched']} 水道 · 提及 {t['waterMentions']} 次 · "
          f"排除 {t['excluded']} 名 · 无对应水名 {t['noCorr']} 次 · 对读 {t['pairs']} 对")
    for w in waters_out:
        print(f"    {w['name']:<4} {w['n']:>3} 次 {w['pieces']} 篇  {w['sjzId']}")


def w_vols_secs(w, secs):
    """水道 → 分节正文列表（sections.js 按 secIds）"""
    return [secs[sid] for sid in w.get("secIds", []) if sid in secs]


def first_sentence_with(text, key):
    """句读切句，取首个含 key 的句（扩窗 ±60 保语境）"""
    for m in re.finditer(re.escape(key), text):
        s = text[max(0, m.start() - 50):m.start() + 110]
        return s.replace("\n", "")
    return ""


if __name__ == "__main__":
    main()
