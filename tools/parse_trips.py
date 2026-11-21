"""霞客经纬 · Phase 1 篇章解析（游程 → 日记日条目）
输入: data/vol/NN.txt (22 篇)
输出: data/intermediate/trips_raw.json
      { pieces:[{num,title,year0,ganzhi,intro:[…],days:[{h,y,m,d,leap,paras:[…]}]}] }
规则:
  · 篇首连续「全括号行」= 编者题解（intro），不入日记正文
  · 行首日期标记开新日条目：〔干支（公元NNNN年）|干支（NNNN年）〕之？〔闰〕〔N月〕〔日号〕
    或裸日号「初二日／二十日」（继承当前月）；干支年给起始纪年
  · 无日期的篇首叙述行 → 「篇首」条目（首段原文，如「癸丑之三月晦自宁海出西门」外的长引子）
  · 月份回卷（十一→正 等，差≥9）→ 年+1（跨年西游日记 1636→1637）
  · 纪年兜底：篇目起始年表（通行编年，见 YEAR0 表）
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL = os.path.join(ROOT, "data", "vol")
OUT = os.path.join(ROOT, "data", "intermediate", "trips_raw.json")

# 通行编年（徐霞客游程年表，见 README「数据边界」）
YEAR0 = {"000": 1613, "001": 1613, "002": 1616, "003": 1616, "004": 1616,
         "005": 1618, "006": 1618, "007": 1620, "008": 1623, "009": 1623,
         "010": 1623, "011": 1630, "012": 1632, "013": 1632, "014": 1632,
         "015": 1633, "016": 1633, "017": 1636, "018": 1636, "019": 1637,
         "020": 1637, "021": 1637}

MONTHS = {"正": 1, "一": 1, "元": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
          "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "冬": 11, "十二": 12, "腊": 12}
CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

DAY_TOK = r"(?:元旦|晦|朔|初[一二三四五六七八九十]日|十[一二三四五六七八九]日|二十[一二三四五六七八九]?日|廿[一二三四五六七八九]?日|三十[一二]?日|卅[一二]?日)"
HEAD_RE = re.compile(
    r"^([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?"      # 干支
    r"(?:（(?:公元)?(\d{4})年）)?"                                  # 纪年（公元1613年 / 1618年）
    r"[，,]?"                                                       # 「戊午（1618年），余同兄」
    r"(?:之)?"                                                      # 「癸丑…之三月晦」
    r"(闰)?([正一二三四五六七八九十]{1,2})月"                       # 闰 / 月（须带「月」字）
    r"(" + DAY_TOK + r")?"                                          # 日号（可省：仅月）
)
DAY_RE = re.compile(r"^(" + DAY_TOK + r")")
INLINE_MD_RE = re.compile(r"([正一二三四五六七八九十]{1,2})月(" + DAY_TOK + r")")
# 句末标点后的日号 → 分段（本版 HTML 常把数日并入一段；「越N月N日」「以八月十八日」
# 等引述性日期因前置非句末标点而不切）
SPLIT_RE = re.compile(
    r"(?<=[。！？；」])((?:闰)?[正一二三四五六七八九十]{1,2}月)?(" + DAY_TOK + r")(?![年］」])")


def split_mid_days(lines):
    out = []
    for ln in lines:
        if ln.startswith("(") and ln.endswith(")"):   # 注释整行不切
            out.append(ln)
            continue
        parts = SPLIT_RE.split(ln)
        if len(parts) == 1:
            out.append(ln)
            continue
        # re.split 带捕获组：[前文, 月?, 日号, 中段, 月?, 日号, …] —— 重组为独立行
        buf = parts[0]
        for i in range(1, len(parts), 3):
            mo = parts[i] or ""
            dy = parts[i + 1] or ""
            out.append(buf)
            out.append(mo + dy + parts[i + 2])
            buf = ""
        # 尾段并入最后日条
        if buf:
            out[-1] += buf
    return [l for l in out if l]


def parse_month(tok):
    if tok in MONTHS:
        return MONTHS[tok]
    if len(tok) == 2 and tok[0] == "十":
        return 10 + CN.get(tok[1], 0)
    return None


def parse_day(tok):
    """日号 → 日数值；晦=30 近似（仅排序/标签用）"""
    if tok == "元旦" or tok == "朔":
        return 1
    if tok == "晦":
        return 30
    body = tok[:-1]
    if body.startswith("初"):
        return CN.get(body[1])
    if body.startswith("廿"):
        return 20 + (CN.get(body[1], 0) if len(body) > 1 else 0)
    if body.startswith("卅"):
        return 30 + (CN.get(body[1], 0) if len(body) > 1 else 0)
    if body == "二十":
        return 20
    if len(body) == 2 and body[0] == "十":
        return 10 + CN.get(body[1], 0)
    if body == "十":
        return 10
    return CN.get(body)


def is_full_paren(ln):
    return ln.startswith("(") and ln.endswith(")")


def ganzhi_year(gz, default):
    """干支 → 1604-1643 窗口内的公历年（本集编年域）"""
    if gz is None:
        return None
    for y in range(1604, 1644):
        stem = "甲乙丙丁戊己庚辛壬癸"[(y - 4) % 10]
        branch = "子丑寅卯辰巳午未申酉戌亥"[(y - 4) % 12]
        if stem + branch == gz:
            return y
    return default


NOISE_RE = re.compile(r"^(Powered by|www\.guoxue123\.com|© Copyright)")


def parse_piece(num, title, year0_default):
    lines = open(os.path.join(VOL, f"{num}.txt"), encoding="utf-8").read().split("\n")
    titles = {title, title[:-1] + "(后)"} if title.endswith("后") else {title}
    lines = [l.strip() for l in lines
             if l.strip() and l.strip() not in titles and not NOISE_RE.match(l.strip())]
    lines = split_mid_days(lines)

    intro, days, cur = [], [], None
    y, m, d = year0_default, None, None
    ganzhi, prev_m = None, None

    def flush():
        nonlocal cur
        if cur and (cur["paras"] or cur["d"] is not None):
            days.append(cur)
        cur = None

    seen_content = False
    for ln in lines:
        # 篇首题解：未见正文前的连续全括号行
        if not seen_content and is_full_paren(ln):
            intro.append(ln)
            continue

        h = HEAD_RE.match(ln)
        if h and (h.group(2) or h.group(4) or h.group(5)):
            flush()
            if h.group(1):
                ganzhi = h.group(1)
                # 干支优先于版内公元注（源注有误，如002「丙辰岁（1618年）」实为1616）
                y = ganzhi_year(ganzhi, year0_default) or int(h.group(2) or year0_default)
            elif h.group(2):
                y = int(h.group(2))
            else:
                y = y or year0_default
            leap = bool(h.group(3))
            if h.group(4):
                mo = parse_month(h.group(4))
                if mo:
                    # 月份回卷=跨年（仅当本行未自带纪年：干支/公元注优先）
                    if (prev_m and mo < prev_m and not leap and prev_m - mo >= 9
                            and not h.group(1) and not h.group(2)):
                        y += 1
                    prev_m = mo
                    m = mo
            if h.group(5):
                d = parse_day(h.group(5))
            body = ln[h.end():].strip()
            # 题解后的裸「N月」（如 004「二月…」）可能带日号在行内稍后——不管，标签即所捕获
            cur = {"h": ln[:h.end()].strip("之，, "), "y": y, "m": m, "d": d,
                   "leap": leap, "paras": ([body] if body else [])}
            seen_content = True
            continue

        d2 = DAY_RE.match(ln)
        if d2:
            flush()
            d = parse_day(d2.group(1))
            body = ln[d2.end():].strip()
            cur = {"h": d2.group(1), "y": y, "m": m, "d": d, "leap": False,
                   "paras": ([body] if body else [])}
            seen_content = True
            continue

        if cur is None:
            # 篇首叙述（无日期引导）：「篇首」条目；行内月日若有则初始化
            im = INLINE_MD_RE.search(ln[:40])
            if im:
                m = parse_month(im.group(1))
                prev_m = m
            cur = {"h": "篇首", "y": y, "m": m, "d": None, "leap": False, "paras": [ln]}
            seen_content = True
            continue
        cur["paras"].append(ln)
    flush()

    # 「篇首」空标签兜底
    return {"num": num, "title": title, "year0": year0_default, "ganzhi": ganzhi,
            "intro": intro, "days": days}


def main():
    from fetch_text import PIECES
    pieces = [parse_piece(num, title, YEAR0[num]) for num, title in PIECES]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"pieces": pieces}, f, ensure_ascii=False, indent=1)
    total = 0
    for p in pieces:
        total += len(p["days"])
        heads = " | ".join(dd["h"] for dd in p["days"][:3])
        print(f"{p['num']} {p['title']}  {len(p['days']):>3} 日条  首标 {heads[:40]}")
    print(f"\n合计 {len(pieces)} 篇 · {total} 日条目 → {OUT}")


if __name__ == "__main__":
    main()
