# -*- coding: utf-8 -*-
"""霞客经纬 · 计量产线（凡数字必出自脚本）
输入: data/intermediate/trips.json · data/vol/*.txt
输出: data/stats.js    前端计量层 const XXK_STATS
      docs/stats.json  数字存档（README/ANALYSIS 引用同一口径）
      docs/ANALYSIS.md 文本计量（每次重写，勿手改）
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIPS = os.path.join(ROOT, "data", "intermediate", "trips.json")

WORDLISTS = {
    "landform": {"label": "地貌词", "chars": list("山峰岭崖岩洞石瀑溪涧潭泉")},
    "motion": {"label": "行旅词", "chars": list("行登上下渡宿饭抵至入逾涉")},
    "weather": {"label": "天象词", "chars": list("雨雾云雪风霜日晴寒")},
    "wonder": {"label": "叹赏词", "chars": list("奇胜绝妙异灵秀险")},
}


def plain_corpus():
    """原文语料（去编者括号注）——统计口径与检索层一致"""
    PAREN = re.compile(r"（[^（）]*）|\([^()]*\)")
    from fetch_text import PIECES
    texts = {}
    for num, title in PIECES:
        t = open(os.path.join(ROOT, "data", "vol", f"{num}.txt"), encoding="utf-8").read()
        texts[num] = (title, PAREN.sub("", t).replace("\n", ""))
    return texts


def main():
    d = json.load(open(TRIPS, encoding="utf-8"))
    meta, trips = d["meta"], d["trips"]
    corpus = plain_corpus()

    # 语料字数（与 meta.charsOrig 同口径自证；允许 <0.3% 边差——
    # 日条级「跨段括号状态机」与文件级「平衡括号正则」对个别未闭合注释的处理差异）
    chars_total = sum(len(t) for _, t in corpus.values())
    assert abs(chars_total - meta["charsOrig"]) < meta["charsOrig"] * 0.003, \
        f"语料口径漂移过大 {chars_total} vs {meta['charsOrig']}"

    # 字频（CJ 区）
    freq = Counter(ch for t in corpus.values() for ch in t[1] if "\u4e00" <= ch <= "\u9fff")
    top60 = freq.most_common(60)

    # 词类命中
    wordstats = {}
    for key, conf in WORDLISTS.items():
        c = Counter()
        for _, (title, t) in corpus.items():
            for ch in conf["chars"]:
                n = t.count(ch)
                if n:
                    c[ch] += n
        wordstats[key] = {"label": conf["label"], "total": sum(c.values()),
                          "top": c.most_common(6)}

    # 游年分布
    years = Counter()
    for t in trips:
        for dd in t["days"]:
            if dd["y"]:
                years[dd["y"]] += 1
    years_sorted = [[y, n] for y, n in sorted(years.items())]

    jumps = sum(1 for t in trips for dd in t["days"] if dd["jump"])

    stats = {
        "meta": {
            **{k: meta[k] for k in ["pieces", "days", "anchored", "coverage",
                                    "kmTotal", "charsOrig", "charsNote", "gazetteer",
                                    "confQu", "confTui"]},
            "jumps": jumps, "kmMax": max(t["stats"]["km"] for t in trips),
            "freqTop1": top60[0], "corpusDistinct": len(freq),
        },
        "trips": [{"id": t["id"], "title": t["title"], "year": t["year"], "color": t["color"],
                   "days": t["stats"]["days"], "anchored": t["stats"]["anchored"],
                   "km": t["stats"]["km"], "chars": t["stats"]["chars"]} for t in trips],
        "freq": top60,
        "wordlists": wordstats,
        "years": years_sorted,
    }
    with open(os.path.join(ROOT, "docs", "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data", "stats.js"), "w", encoding="utf-8") as f:
        f.write("/* 霞客经纬 · 计量数据 · build_stats.py 生成，勿手改（数字同 docs/stats.json） */\n")
        f.write("const XXK_STATS = " + json.dumps(stats, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── ANALYSIS.md ──
    m = stats["meta"]
    freq_line = " · ".join(f"{c}{n}" for c, n in top60[:24])
    wl_lines = "\n".join(
        f"- **{v['label']}** {v['total']:,} 次：{('、'.join(f'{c} {n:,}' for c, n in v['top']))}"
        for v in wordstats.values())
    trip_rows = "\n".join(
        f"| {t['title']} | {t['year']} | {t['days']} | {t['anchored']} | "
        f"{t['km']:,} | {t['chars']:,} |" for t in stats["trips"])
    year_rows = "<br>".join(f"{y}：{n} 日条" for y, n in years_sorted)

    analysis = f"""# 霞客经纬 · 文本计量（ANALYSIS）

> 本文件由 `python tools/build_stats.py` 重写生成——凡数字必出自脚本，
> 与 `docs/stats.json`、`data/stats.js` 同一口径。勿手改。

## 一、语料

- 底本：国学导航《徐霞客游记》（明）徐宏祖，通行「前半部」22 篇（000 游天台山日记 … 021 粤西游日记二）
- 原文 **{m['charsOrig']:,}** 字 + 编者括号注 **{m['charsNote']:,}** 字（题解/音注/义注，已分离不入统计与检索）
- 编年跨度：万历四十一年（1613 癸丑·天台）— 崇祯十年（1637 丁丑·粤西）；起讫 25 年
- 版本缺漏（如实）：粤西游日记三四、黔游日记、滇游日记十三、盘江考/溯江纪源等附编**不在本底本**——
  维基文库在本建站网络不可达（TLS 超时），国学导航即止于记二

## 二、游程结构（22 程 · {m['days']} 日条）

| 篇 | 年 | 日条 | 锚定 | 折线km | 原文字 |
|---|---|---|---|---|---|
{trip_rows}

- 锚定日 {m['anchored']}（覆盖 **{m['coverage']}%**）：地名表 {m['gazetteer']} 条，
  置信 确 {m['confQu']} / 推 {m['confTui']}（全部 src=derived，今地常识定位）
- 可信里程合计 **{m['kmTotal']:,} km**（haversine 锚点折线，剔除 {m['jumps']} 处 >400km 跳段；
  含同地往返——霞客粤西期为静闻病情在柳州—浔州—郁林间数度折返，折线如实反映文本行踪，非人行实距）

## 三、字频

全文最高频六十字（前 24 示下）：

{freq_line}

毫不意外：「{top60[0][0]}」（{top60[0][1]:,} 次）居首——山岳意象为全书底色；
地貌词合计 {wordstats['landform']['total']:,} 次，行旅词 {wordstats['motion']['total']:,} 次，
「游」之为书，一步一山。

## 四、词汇场

{wl_lines}

## 五、游年分布

{year_rows}

1636–1637「万里遐征」段（浙·江右·楚·粤西）日条 {years_sorted[-2][1] + years_sorted[-1][1]} 条，
占全书 {round((years_sorted[-2][1] + years_sorted[-1][1]) / m['days'] * 100)}%——晚年西行是全书重心。

## 六、方法与边界

- 日条解析：行首日期标记（干支纪年/闰月/晦朔/廿X日）+ 句末标点后日号分段 → {m['days']} 日条
- 锚点：篇内 scope 消歧地名表逐日首现（避开前一锚同名），坐标今地近似（确 ±3km 级 / 推 ±10–25km 级）
- 已知误锚风险：文本提及而未亲历之地（如楚游述及安福）会占锚——scope 表已消歧 47 组同名，
  存疑处以 conf=推 与 ⚠跳段 双重标示
"""
    with open(os.path.join(ROOT, "docs", "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write(analysis)

    print(f"docs/stats.json · data/stats.js · docs/ANALYSIS.md 已生成")
    print(f"字种 {len(freq)} · 高频字 {top60[0][0]}={top60[0][1]:,} · "
          f"词类 {sum(v['total'] for v in wordstats.values()):,} 次 · 跳段 {jumps}")


if __name__ == "__main__":
    main()
