# -*- coding: utf-8 -*-
"""霞客经纬 · 古今对照导出（P2 · 管线复算）
从 data/intermediate/trips.json 复算三格式导出 → docs/export/：
  霞客经纬-古今对照.csv  （UTF-8 带 BOM，Excel 直开）
  霞客经纬-古今对照.kml  （Google Earth 直开）
  霞客经纬-古今对照.geojson
口径与前端 js/stats.js 的 exportCSV/exportKML/exportGeoJSON 完全一致：
  t01→t22 · 逐日 · 锚点行；字段 地名/所属篇/日条/坐标/今名/依据/置信(确|推)/src
示意坐标（src=derived 今地常识定位）逐行注明。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "docs", "export")


def rows():
    """行构造——与前端 js/stats.js xrefRows() 同口径"""
    d = json.load(open(os.path.join(ROOT, "data/intermediate/trips.json"), encoding="utf-8"))
    out = []
    for t in d["trips"]:
        for i, dd in enumerate(t["days"]):
            if not dd["anchor"]:
                continue
            a = dd["anchor"]
            if dd.get("y") and dd.get("m"):
                ddv = "%02d" % dd["d"] if dd.get("d") else ""   # 与前端 String(d||"").padStart 同口径
                day = "%d.%02d.%s" % (dd["y"], dd["m"], ddv)
            else:
                day = "篇首"
            out.append({
                "name": a["name"], "piece": t["title"], "day": day,
                "lat": a["pos"][0], "lng": a["pos"][1],
                "today": a["today"], "basis": a["basis"],
                "conf": a["conf"], "src": a["src"],
            })
    return out, d["meta"]


def q(s):
    s = str(s)
    return '"%s"' % s.replace('"', '""') if any(c in s for c in ',"\n') else s


def main():
    rs, meta = rows()
    os.makedirs(OUT_DIR, exist_ok=True)

    # CSV（BOM）
    head = ["地名", "所属篇", "日条", "纬度", "经度", "今名", "依据", "置信", "src"]
    lines = [",".join(head)]
    for r in rs:
        lines.append(",".join(q(x) for x in
                        [r["name"], r["piece"], r["day"], r["lat"], r["lng"],
                         r["today"], r["basis"], r["conf"], r["src"]]))
    lines.append("注：坐标全部为今地常识定位示意坐标（src=derived，确±3km级/推±10-25km级），非实测")
    with open(os.path.join(OUT_DIR, "霞客经纬-古今对照.csv"), "w", encoding="utf-8-sig", newline="") as f:
        f.write("\n".join(lines) + "\n")

    # KML
    pins = []
    for r in rs:
        desc = "%s · %s · 今%s（%s）· 置信%s · 示意坐标(derived)" % (
            r["piece"], r["day"], r["today"], r["basis"], r["conf"])
        pins.append("<Placemark><name>%s</name><description>%s</description>"
                    "<Point><coordinates>%s,%s,0</coordinates></Point></Placemark>"
                    % (r["name"], desc, r["lng"], r["lat"]))
    kml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>霞客经纬·古今对照锚点（示意坐标）</name>'
           + "".join(pins) + "</Document></kml>")
    with open(os.path.join(OUT_DIR, "霞客经纬-古今对照.kml"), "w", encoding="utf-8") as f:
        f.write(kml)

    # GeoJSON
    feats = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
        "properties": {
            "地名": r["name"], "所属篇": r["piece"], "日条": r["day"], "今名": r["today"],
            "依据": r["basis"], "置信": r["conf"], "src": r["src"],
            "备注": "示意坐标（今地常识定位，非实测）",
        },
    } for r in rs]
    gj = {"type": "FeatureCollection",
          "note": "坐标全部为 src=derived 示意坐标（今地常识定位）",
          "features": feats}
    with open(os.path.join(OUT_DIR, "霞客经纬-古今对照.geojson"), "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    n_qu = sum(1 for r in rs if r["conf"] == "确")
    print("docs/export/ 三格式已生成：%d 行（确 %d / 推 %d）· 口径同 js/stats.js 导出"
          % (len(rs), n_qu, len(rs) - n_qu))
    assert len(rs) == meta["anchored"], "导出行数 %d ≠ 锚定 %d" % (len(rs), meta["anchored"])


if __name__ == "__main__":
    main()
