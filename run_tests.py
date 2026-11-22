"""霞客经纬 · 回归入口
python run_tests.py
  1) tools/lint.py         确定性静态检查（60+ 项）
  2) 数据断言（同 tests/assert_data.html 的 python 版，≥10 项）
  3) 浏览器断言页提醒（tests/assert_*.html，需 http://127.0.0.1:9400/ 下验看，title=PASS 即绿）
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
fails = []


def step(name, fn):
    print(f"—— {name} ——")
    try:
        fn()
        print(f"✓ {name} 通过\n")
    except AssertionError as e:
        fails.append(name)
        print(f"✗ {name} 失败：{e}\n")


def lint():
    import os as _os
    env = dict(_os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(ROOT, "tools", "lint.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    print(r.stdout.strip())
    assert r.returncode == 0, f"lint 未全绿\n{r.stderr[-500:]}"


def data_asserts():
    d = json.load(open(os.path.join(ROOT, "data/intermediate/trips.json"), encoding="utf-8"))
    m = d["meta"]
    assert m["pieces"] == 52, f"游程 {m['pieces']} ≠ 52（三源 gx22+kr21+ws9）"
    assert m["days"] >= 900, f"日条 {m['days']} < 900"
    assert m["anchored"] >= 450, f"锚定 {m['anchored']} < 450"
    assert m["coverage"] >= 50, f"覆盖率 {m['coverage']}% < 50%"
    assert m["kmTotal"] >= 20000, f"可信里程 {m['kmTotal']} < 20000"
    assert 400000 <= m["charsOrig"] <= 500000, f"原文 {m['charsOrig']} 越界"
    assert m["gazetteer"] >= 350, f"地名表 {m['gazetteer']} < 350"
    n_gx = sum(1 for t in d["trips"] if t.get("source", "gx") == "gx")
    n_kr = sum(1 for t in d["trips"] if t.get("source") == "kr")
    n_ws = sum(1 for t in d["trips"] if t.get("source") == "ws")
    assert n_gx == 22 and n_kr == 21 and n_ws == 9,         f"三源构成 gx{n_gx}+kr{n_kr}+ws{n_ws} ≠ 22+21+9"
    ws_chars = sum(t["stats"]["chars"] for t in d["trips"] if t.get("source") == "ws")
    ws_anchors = sum(t["stats"]["anchored"] for t in d["trips"] if t.get("source") == "ws")
    assert ws_chars > 8000 and ws_anchors == 0,         f"ws 附编字数 {ws_chars}/锚 {ws_anchors} 异常（应 >8000 字 · 零锚）"
    kr_km = sum(t["stats"]["km"] for t in d["trips"] if t.get("source") == "kr")
    assert kr_km > 8000, f"滇黔补编里程贡献 {kr_km} km 异常"
    jumps = sum(1 for t in d["trips"] for dd in t["days"] if dd["jump"])
    assert jumps <= 4, f"跳段 {jumps} > 4"
    t1, t22, t43, t52 = d["trips"][0], d["trips"][21], d["trips"][42], d["trips"][51]
    assert t1["title"] == "游天台山日记" and t1["year0"] == 1613, "首程应为天台 1613"
    assert t22["num"] == "021" and t22["stats"]["days"] > 50, "t22 应为粤西游日记二（长程）"
    assert t43["num"] == "042" and t43["title"] == "记游颜洞" and t43.get("source") == "kr",         "t43 应为记游颜洞（kr 附记）"
    assert t52["num"] == "051" and t52["title"] == "丽江纪略" and t52.get("source") == "ws",         "末篇应为丽江纪略（ws 杂著）"
    # 每锚点字段完备
    n_anchor = 0
    for t in d["trips"]:
        for dd in t["days"]:
            if dd["anchor"]:
                n_anchor += 1
                a = dd["anchor"]
                assert a["src"] == "derived" and a["basis"] and a["conf"] in ("确", "推") and a["today"], \
                    f"{t['id']} 锚点字段不完备: {a.get('name')}"
    assert n_anchor == m["anchored"], f"锚点计数 {n_anchor} ≠ {m['anchored']}"
    # stats.json 同口径
    s = json.load(open(os.path.join(ROOT, "docs/stats.json"), encoding="utf-8"))
    assert s["meta"]["charsOrig"] == m["charsOrig"] and s["meta"]["kmTotal"] == m["kmTotal"], \
        "stats.json 与 trips.json 口径漂移——重跑 build_stats.py"
    # 阅读层文件与日条数一致
    rd = json.load(open(os.path.join(ROOT, "data/intermediate/trips_raw.json"), encoding="utf-8"))
    for p in rd["pieces"]:
        fp = os.path.join(ROOT, "data/read", f"{p['num']}.js")
        assert os.path.exists(fp), f"data/read/{p['num']}.js 缺失"
    # ── P2 · 方舆互查桥（HHH 只读，build_xref_fy.py 产物） ──
    import re as _re
    xraw = open(os.path.join(ROOT, "data/xref_fy.js"), encoding="utf-8").read()
    X = json.loads(_re.search(r"window\.XXK_FYXREF = (\{.*\});", xraw, _re.S).group(1))
    assert X["total"] == m["anchored"], f"互查桥锚数 {X['total']} ≠ 锚定 {m['anchored']}"
    assert X["matched"] + X["unmatched"] == X["total"], "互查桥 匹配+无对应 ≠ 总数"
    assert X["matched"] >= X["total"] * 0.4, "互查桥匹配率 < 40%"
    assert sum(t["matched"] + t["unmatched"] for t in X["byTrip"]) == X["total"], "分组计数和 ≠ 总数"
    hrefs = [e["href"] for t in X["byTrip"] for e in t["examples"]]
    assert hrefs and all(h.startswith("../HHH/#mode=") for h in hrefs), "深链须 ../HHH/#mode= 前缀"
    # ── P2 · 古今对照导出（export_data.py 产物，与前端同口径） ──
    exd = os.path.join(ROOT, "docs", "export")
    blob = open(os.path.join(exd, "霞客经纬-古今对照.csv"), "rb").read()
    assert blob[:3] == b"\xef\xbb\xbf", "CSV 缺 BOM"
    assert len(blob.decode("utf-8-sig").strip().splitlines()) == m["anchored"] + 2, "CSV 行数 ≠ 锚定+表头+注"
    gj = json.load(open(os.path.join(exd, "霞客经纬-古今对照.geojson"), encoding="utf-8"))
    assert len(gj["features"]) == m["anchored"], "GeoJSON features ≠ 锚定"
    # ── P2 · 论文 PDF 哨兵（ANALYSIS.md 改动必须重排） ──
    pdfp = os.path.join(ROOT, "docs", "霞客经纬-论文.pdf")
    assert os.path.exists(pdfp), "docs/霞客经纬-论文.pdf 缺失——重跑 tools/build_paper_pdf.py"
    assert os.path.getmtime(os.path.join(ROOT, "docs", "ANALYSIS.md")) <= os.path.getmtime(pdfp) + 60, \
        "ANALYSIS.md 新于 PDF——重跑 tools/build_paper_pdf.py"
    print(f"游程 {m['pieces']} · 日条 {m['days']} · 锚定 {m['anchored']}"
          f"（{m['coverage']}% · 确{m['confQu']}/推{m['confTui']}）"
          f" · 里程 {m['kmTotal']:,} km · 原文 {m['charsOrig']:,} 字 · 跳段 {jumps}")
    print(f"P2：互查桥 匹配 {X['matched']}/无对应 {X['unmatched']}（唯一名 {X['uniqMatched']}/{X['uniqNames']}）"
          f" · 导出 {len(gj['features'])} 行三格式 · 论文 PDF 就绪")


def account_sums():
    """账目对账（SHA256SUMS）：逐行指纹与磁盘实测（行尾无关）+ 行数与生成器一致，过期即红。"""
    import importlib.util
    import re as _re
    spec = importlib.util.spec_from_file_location(
        "build_sums", os.path.join(ROOT, "tools", "build_sums.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    want = bs.collect()
    path = os.path.join(ROOT, "SHA256SUMS")
    assert os.path.exists(path), "SHA256SUMS 缺失——先 python tools/build_sums.py"
    raw = open(path, "rb").read()
    assert b"\r" not in raw, "SHA256SUMS 行尾混入 CR——须纯 LF，重跑 tools/build_sums.py"
    lines = raw.decode("utf-8").splitlines()
    assert lines, "SHA256SUMS 为空"
    problems, seen = [], set()
    for i, line in enumerate(lines, 1):
        parts = line.split("  ", 1)
        rel = parts[1].strip().replace("\\", "/") if len(parts) == 2 else ""
        if len(parts) != 2 or not _re.fullmatch(r"[0-9a-f]{64}", parts[0]) or not rel:
            problems.append(f"第{i}行格式非法"); continue
        if rel in seen:
            problems.append(f"第{i}行重复 {rel}"); continue
        seen.add(rel)
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            problems.append(f"账上文件缺失 {rel}"); continue
        if bs.sha256(rel) != parts[0]:
            problems.append(f"指纹不符 {rel}")
    assert not problems, f"账目失真 {len(problems)} 处：{problems[:4]}——重跑 python tools/build_sums.py"
    assert len(lines) == len(want), \
        f"账目行数 {len(lines)} ≠ 生成器 {len(want)}（产物增删未记账）——重跑 python tools/build_sums.py"
    off = [r for r in want if r not in seen]
    assert not off, f"产物缺账 {off[:4]}——重跑 python tools/build_sums.py"
    print(f"SHA256SUMS 对账通过：{len(lines)} 行 · 指纹全符（纯 LF）")


def browser_pages():
    pages = [f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("assert_")]
    print(f"浏览器断言页 {len(pages)} 枚：{', '.join(pages)}")
    print("（serve 后逐页打开，title=PASS 即绿——http://127.0.0.1:9400/tests/assert_data.html）")


if __name__ == "__main__":
    step("lint", lint)
    step("数据断言", data_asserts)
    step("账目对账", account_sums)
    step("浏览器断言页", browser_pages)
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")
