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
    assert m["pieces"] == 22, f"游程 {m['pieces']} ≠ 22"
    assert m["days"] >= 480, f"日条 {m['days']} < 480"
    assert m["anchored"] >= 280, f"锚定 {m['anchored']} < 280"
    assert m["coverage"] >= 55, f"覆盖率 {m['coverage']}% < 55%"
    assert m["kmTotal"] >= 10000, f"可信里程 {m['kmTotal']} < 10000"
    assert 200000 <= m["charsOrig"] <= 260000, f"原文 {m['charsOrig']} 越界"
    assert m["gazetteer"] >= 250, f"地名表 {m['gazetteer']} < 250"
    jumps = sum(1 for t in d["trips"] for dd in t["days"] if dd["jump"])
    assert jumps <= 4, f"跳段 {jumps} > 4"
    t1, t22 = d["trips"][0], d["trips"][21]
    assert t1["title"] == "游天台山日记" and t1["year0"] == 1613, "首程应为天台 1613"
    assert t22["num"] == "021" and t22["stats"]["days"] > 50, "末程应为粤西游日记二"
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
    print(f"游程 {m['pieces']} · 日条 {m['days']} · 锚定 {m['anchored']}"
          f"（{m['coverage']}% · 确{m['confQu']}/推{m['confTui']}）"
          f" · 里程 {m['kmTotal']:,} km · 原文 {m['charsOrig']:,} 字 · 跳段 {jumps}")


def browser_pages():
    pages = [f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("assert_")]
    print(f"浏览器断言页 {len(pages)} 枚：{', '.join(pages)}")
    print("（serve 后逐页打开，title=PASS 即绿——http://127.0.0.1:9400/tests/assert_data.html）")


if __name__ == "__main__":
    step("lint", lint)
    step("数据断言", data_asserts)
    step("浏览器断言页", browser_pages)
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")
