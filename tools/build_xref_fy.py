# -*- coding: utf-8 -*-
"""霞客经纬 × 方舆经纬 · 互查桥构建（P2 站际桥）
读 D:/W_A_W/HHH/data/site_data.js（**HHH 只读，绝不写入**），
把霞客锚点地名/今名与方舆（读史方舆纪要）明府县匹配：

  匹配法（同名异地 → 省域消歧）：
    1. 同名：霞客锚点名 == 方舆 府/属州/县 基名（剥 府|州|县|卫 尾）
    2. 同今名：锚点 today（剥 县城|府城|市区|城区 尾）与方舆府治今地（fu.now）前缀互含
    3. 多候选时：取距锚点最近的方舆府治所在省（haversine）——省域消歧；
       全省皆无而候选全省唯一者取之；否则取坐标最近者
    4. 匹配不上如实计「无对应」（霞客多山寺岩潭，本无府县对应）

输出 data/xref_fy.js：window.XXK_FYXREF —— 站内「方舆」页签渲染
（按篇分组计数 + 样例原文句 + ↗方舆深链 ../HHH/#mode=舆图&p=<省id>&fu=<府名>）。
凡计数出自本脚本。上下文句取 data/intermediate/trips_raw.json 当日正文（跳过编者括号注）。"""
import json
import math
import os
import re
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HHH_SITE_DATA = r"D:/W_A_W/HHH/data/site_data.js"   # 只读
SITE = "../HHH/"                                     # 相对兄弟路径（父目录同根服务约定）
MAXD = 250                                           # 同名异地防线（km）：候选距锚点上限

SUF = ("宣慰司", "军民", "府", "州", "县", "卫")


def base(n):
    n = str(n).strip()
    for s in SUF:
        if n.endswith(s) and len(n) > len(s):
            return n[:-len(s)]
    return n


def hav(a, b):
    la1, lo1 = a
    la2, lo2 = b
    p1, p2 = math.radians(la1), math.radians(la2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def load_hhh():
    raw = open(HHH_SITE_DATA, encoding="utf-8").read()
    m = re.search(r"const FY = (\{.*\});", raw, re.S)
    fy = json.loads(m.group(1))
    idx, fus = {}, []
    n_county = 0
    for p in fy["provinces"]:
        for u in p["fu"]:
            if u.get("c"):
                fus.append((u["c"], p["id"], p["name"], u["n"]))
            e = {"pid": p["id"], "prov": p["name"], "fu": u["n"], "kind": "府", "c": u.get("c")}
            idx.setdefault(base(u["n"]), []).append(e)
            for z in (u.get("zx") or []):
                idx.setdefault(base(z["n"]), []).append(
                    {"pid": p["id"], "prov": p["name"], "fu": u["n"], "kind": "属州", "c": z.get("c")})
                for x in z.get("x", []):
                    idx.setdefault(base(x), []).append(
                        {"pid": p["id"], "prov": p["name"], "fu": u["n"], "kind": "县", "c": None})
                    n_county += 1
            for x in (u.get("xian") or []):
                idx.setdefault(base(x), []).append(
                    {"pid": p["id"], "prov": p["name"], "fu": u["n"], "kind": "县", "c": None})
                n_county += 1
            for x, dd in (u.get("xianc") or {}).items():
                c = dd if isinstance(dd, list) else dd.get("c")
                idx.setdefault(base(x), []).append(
                    {"pid": p["id"], "prov": p["name"], "fu": u["n"], "kind": "县", "c": c})
                n_county += 1
    return fy, idx, fus, n_county


def nearest_prov(pos, fus):
    best = min(fus, key=lambda f: hav(pos, f[0]))
    return best[1], best[2]


def match_anchor(a, idx, fus, fus_now):
    """→ (entry|None, how)
    同名异地防线：候选须距锚点 ≤ MAXD km（约明府域尺度）方可认对，
    否则视为同名异地而如实判无对应（例：浙江宁海 vs 山东登州府宁海州，HHH 台州府无宁海县）。"""
    nm = base(a["name"])
    cands = list(idx.get(nm, []))
    how = "同名"
    if not cands:
        tod = re.sub(r"(县城|府城|市区|城区)$", "", a["today"])
        if len(tod) >= 2:
            for e in fus_now:                      # fu.now 前缀互含（今名对照）
                if e["_now"] and (tod.startswith(e["_now"]) or e["_now"].startswith(tod)):
                    cands.append(e)
            how = "今名"
    if not cands:
        return None, ""
    npid, nprov = nearest_prov(a["pos"], fus)
    for c in cands:                                # 省域消歧：先取最近省内的候选
        if c["pid"] == npid:
            return c, how
    # 最近省无此名 → 候选取坐标最近者，且须在 MAXD 内（防同名异地误配）
    pick = min(cands, key=lambda c: hav(a["pos"], c["c"]) if c.get("c") else 1e9)
    if pick.get("c") and hav(a["pos"], pick["c"]) <= MAXD:
        return pick, how + "(邻省就近)"
    return None, ""


def context_sentence(raw_pieces, num, di, name):
    """当日正文找含锚名句（跳过编者注段）；取不到回退全篇搜索"""
    days = None
    for p in raw_pieces:
        if p["num"] == num:
            days = p["days"]
            break
    if not days:
        return ""
    order = [di] + [i for i in range(len(days)) if i != di]
    for i in order:
        if i >= len(days):
            continue
        for para in days[i]["paras"]:
            t = para.strip()
            if not t or t.startswith(("(", "（")):
                continue
            if name in t:
                frag = next((s for s in re.split(r"[。！？]", t) if name in s), "")
                frag = frag.strip()
                if not frag:
                    frag = t[:60]
                return ("…" if len(frag) > 64 else "") + frag[:64]
    return ""


def main():
    fy, idx, fus, n_county = load_hhh()
    fus_now = []
    for p in fy["provinces"]:
        for u in p["fu"]:
            if u.get("now"):
                fus_now.append({"pid": p["id"], "prov": p["name"], "fu": u["n"],
                                "kind": "府", "c": u.get("c"), "_now": u["now"]})

    trips = json.load(open(os.path.join(ROOT, "data/intermediate/trips.json"), encoding="utf-8"))
    raw = json.load(open(os.path.join(ROOT, "data/intermediate/trips_raw.json"), encoding="utf-8"))

    total = matched = unmatched = 0
    uniq, uniq_hit = set(), set()
    by_trip = []
    for t in trips["trips"]:
        rec = {"id": t["id"], "title": t["title"], "year": t["year"],
               "matched": 0, "unmatched": 0, "examples": [], "misses": []}
        for di, dd in enumerate(t["days"]):
            a = dd["anchor"]
            if not a:
                continue
            total += 1
            uniq.add(a["name"])
            hit, how = match_anchor(a, idx, fus, fus_now)
            if hit:
                matched += 1
                uniq_hit.add(a["name"])
                rec["matched"] += 1
                if len(rec["examples"]) < 3:
                    rec["examples"].append({
                        "name": a["name"],
                        "ctx": context_sentence(raw["pieces"], t["num"], di, a["name"]),
                        "fyProv": hit["prov"], "fyFu": hit["fu"], "kind": hit["kind"], "how": how,
                        "href": f'{SITE}#mode={quote("舆图")}&p={hit["pid"]}&fu={quote(hit["fu"])}',
                    })
            else:
                unmatched += 1
                rec["unmatched"] += 1
                if len(rec["misses"]) < 6 and a["name"] not in rec["misses"]:
                    rec["misses"].append(a["name"])
        by_trip.append(rec)

    out = {
        "site": SITE,
        "note": "深链为相对兄弟路径 ../HHH/ —— 需父目录同根服务（于 D:/W_A_W 起 python -m http.server 后 /XXK/ /HHH/ 同源可达）",
        "src": "HHH/data/site_data.js（只读）× XXK data/intermediate/trips.json",
        "hhh": {"provinces": len(fy["provinces"]), "fu": len(fus), "counties": n_county,
                "names": len(idx)},
        "total": total, "matched": matched, "unmatched": unmatched,
        "uniqNames": len(uniq), "uniqMatched": len(uniq_hit),
        "byTrip": by_trip,
    }
    with open(os.path.join(ROOT, "data/xref_fy.js"), "w", encoding="utf-8") as f:
        f.write("/* 霞客经纬 × 方舆经纬 互查桥 · tools/build_xref_fy.py 生成，勿手改（HHH 只读） */\n")
        f.write("window.XXK_FYXREF = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

    print("data/xref_fy.js：锚 %d（匹配 %d · 无对应 %d）· 唯一名 %d（中 %d）"
          % (total, matched, unmatched, len(uniq), len(uniq_hit)))
    print("方舆侧：%d 省 · %d 府治 · 县名 %d · 基名索引 %d" % (len(fy["provinces"]), len(fus), n_county, len(idx)))


if __name__ == "__main__":
    main()
