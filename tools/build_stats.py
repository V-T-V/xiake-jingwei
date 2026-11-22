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


def strip_notes_state_machine(t):
    """括号状态机去注（与 build_trip_data.clean_text 同口径）——kr 四库小注有
    跨行/未配对括号，文件级平衡正则会欠剔（漂移 0.39% 超阈），故统一用状态机"""
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


def plain_corpus():
    """原文语料（去编者括号注）——统计口径与锚点/字数管线一致（双底本：gx 22 + kr 21）"""
    from fetch_text import PIECES
    from parse_kr import PIECES_KR
    texts = {}
    for num, title in PIECES:
        t = open(os.path.join(ROOT, "data", "vol", f"{num}.txt"), encoding="utf-8").read()
        texts[num] = (title, strip_notes_state_machine(t))
    for _fid, _rx, num, title, _y in PIECES_KR:
        t = open(os.path.join(ROOT, "data", "vol", f"{num}.txt"), encoding="utf-8").read()
        texts[num] = (title, strip_notes_state_machine(t))
    return texts


def main():
    d = json.load(open(TRIPS, encoding="utf-8"))
    meta, trips = d["meta"], d["trips"]
    corpus = plain_corpus()

    # 语料字数自证：文件级（含日条头日期标签）对日条级（正文口径，日期头不入字数）
    # 的固有边差——gx 本日期头多带括号纪年注故差小，kr 四库本裸日期头（约 8 字/日）
    # 使差率升至 ~0.4%；容差 0.5% 为口径说明而非漂移
    chars_total = sum(len(t) for _, t in corpus.values())
    assert abs(chars_total - meta["charsOrig"]) < meta["charsOrig"] * 0.005, \
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
                   "source": t.get("source", "gx"),
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
    yb = dict(years_sorted)

    analysis = f"""# 霞客经纬 · 文本计量（ANALYSIS）

> 本文件由 `python tools/build_stats.py` 重写生成——凡数字必出自脚本，
> 与 `docs/stats.json`、`data/stats.js` 同一口径。勿手改。

## 一、语料（双底本）

- **底本一（gx）**：国学导航《徐霞客游记》（明）徐宏祖，通行「前半部」22 篇（000 游天台山日记 … 021 粤西游日记二）
- **底本二（kr）**：kanripo KR2k0135 文渊阁四库全书本·楊名時重编订十二卷，滇黔补编 21 篇
  （022 粤西游日记三 … 039 滇游日记十四 = 四库「西南游日记五至廿二」，另附记 3 篇 040-042）——
  粤三四（粤西游日记五六）· 黔游（七八）· 滇游十四篇（九至廿二）
- 原文 **{m['charsOrig']:,}** 字（gx {sum(t['stats']['chars'] for t in trips if t['source'] == 'gx'):,} +
  kr {sum(t['stats']['chars'] for t in trips if t['source'] == 'kr'):,}）+
  编者括号注 **{m['charsNote']:,}** 字（gx 题解音注 + kr 四库小注/阙文跋，已分离不入统计与检索）
- 编年跨度：万历四十一年（1613 癸丑·天台）— 崇祯十二年（1639 己卯·滇西）；起讫 27 年
- 版本边界（如实）：四库提要自言「所缺者一篇而已」，然卷内自注多处阙文（南宁段脱、武定后缺十九日、
  月终俱阙、永昌缺十日、卷十二下尾「以下阙」）；盘江考/溯江纪源两附编**不在两底本**；
  四库本有讳改删节风险（馆臣编辑），站内简体化呈现、罕字以 □ 存疑

## 二、游程结构（{m['pieces']} 程 · {m['days']} 日条）

| 篇 | 年 | 日条 | 锚定 | 折线km | 原文字 |
|---|---|---|---|---|---|
{trip_rows}

- 锚定日 {m['anchored']}（覆盖 **{m['coverage']}%**）：地名表 {m['gazetteer']} 条，
  置信 确 {m['confQu']} / 推 {m['confTui']}（全部 src=derived，今地常识定位）
- 可信里程合计 **{m['kmTotal']:,} km**（haversine 锚点折线，剔除 {m['jumps']} 处 >400km 跳段；
  含同地往返——霞客粤西期为静闻病情在柳州—浔州—郁林间数度折返，折线如实反映文本行踪，非人行实距）
- 滇黔补编贡献：{sum(t['stats']['km'] for t in trips if t['source'] == 'kr'):,} km ·
  {sum(t['stats']['days'] for t in trips if t['source'] == 'kr')} 日条 ·
  {sum(t['stats']['chars'] for t in trips if t['source'] == 'kr'):,} 字

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

1636–1637「万里遐征」前段（浙·江右·楚·粤西）日条 {yb[1636] + yb[1637]} 条，
1638–1639 滇黔段日条 {yb[1638] + yb[1639]} 条——晚年西行两段合计
占全书 {round((yb[1636] + yb[1637] + yb[1638] + yb[1639]) / m['days'] * 100)}%，仍是全书重心。

## 六、方法与边界

- 日条解析：行首日期标记（干支纪年/闰月/晦朔/廿X日）→ {m['days']} 日条；gx 本另以句末标点
  后日号分段（本版 HTML 常并数日于一段），kr 四库本每日自起一段（同行多日仅 0.2%，多为叙述性
  引日期，不切以免伪日条）
- 锚点：篇内 scope 消歧地名表逐日首现（避开前一锚同名），坐标今地近似（确 ±3km 级 / 推 ±10–25km 级）；
  kr 新篇地名以土州治所/名山今地常识定位，泛词（三里=里程/温泉/木公=人名）不收，
  同名异地（镇远·临安·太华山·石屏·独山·太平）以 scope 消歧
- 已知误锚风险：文本提及而未亲历之地（如楚游述及安福、滇一弥勒盘江叙事回指）会占锚——
  scope 表已消歧 {sum(1 for e in __import__('gazetteer').entries() if e['scope'])} 组，
  存疑处以 conf=推 与 ⚠跳段 双重标示
"""
    with open(os.path.join(ROOT, "docs", "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write(analysis)

    print(f"docs/stats.json · data/stats.js · docs/ANALYSIS.md 已生成")
    print(f"字种 {len(freq)} · 高频字 {top60[0][0]}={top60[0][1]:,} · "
          f"词类 {sum(v['total'] for v in wordstats.values()):,} 次 · 跳段 {jumps}")


if __name__ == "__main__":
    main()
