# -*- coding: utf-8 -*-
"""霞客经纬 · 滇黔补编 Phase 1：mandoku 解析 → 篇目清点与切分（KR2k0135）
输入: data_raw/kr/KR2k0135_000..012.txt（文淵閣四庫全書·楊名時重編訂本）
输出: data/vol/022..042.txt   新篇纯净文本（简体化，一段一行，gx 同构）
      data/intermediate/kr_report.json  清点报告（字数/阙文注/日标样本）
口径:
  · org 头（# / +）与 <pb:…> 页标剔除；行尾 ¶ 剔除；全角空格缩进剔除
  · &KRdddd; 罕字实体 → □（存疑字，同 HHH「缺字以□存疑不删」纪律）
  · 繁→简：opencc t2s + 手工异体补表（逰→游 等 t2s 不覆盖者）
  · 编者阙文注（「以下…脱去」「…俱闕」「此後共缺…」「季夢良曰」跋）→ 括号注化
    （沿用 gx 管线的 原文/注 分离：不入统计与检索，阅读层淡显）
  · 篇题行（含四库属地小注）剔除；卷首尾「徐霞客遊記卷X」行剔除
双底本: 新篇 source=kr；gx 旧篇不动（同名篇异同抽样对比，报告在案）
"""
import json
import os
import re
import sys

import opencc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KR_DIR = os.path.join(ROOT, "data_raw", "kr")
VOL_DIR = os.path.join(ROOT, "data", "vol")
OUT_REPORT = os.path.join(ROOT, "data", "intermediate", "kr_report.json")
os.makedirs(VOL_DIR, exist_ok=True)

CC = opencc.OpenCC("t2s")
# t2s 不覆盖的异体/俗字补表（实测高频）
VARIANTS = {
    "逰": "游", "竒": "奇", "厯": "历", "徃": "往", "暁": "晓", "栁": "柳", "桞": "柳",
    "皷": "鼓", "菴": "庵", "峩": "峨", "旣": "既", "卽": "即", "劒": "剑", "灮": "光",
    "兎": "兔", "龎": "庞", "虵": "蛇", "跴": "踩", "咲": "笑", "啗": "啖", "壻": "婿",
    "屛": "屏", "歴": "历", "溝": "沟", "灘": "滩", "嵐": "岚", "嶂": "嶂",
    "㳺": "游", "㽜": "留", "㑹": "会", "㢘": "廉", "㕝": "事", "逺": "远",
}

# ── 篇目登记（四库卷帙 → 站内新篇号；旧 000..021 为 gx 本，不重产） ──
# (文件, 四库篇题正则(简体化后), 新num, 站内题, 通行编年 year0, source)
PIECES_KR = [
    ("KR2k0135_004", r"西南游日记五", "022", "粤西游日记三", 1637),
    ("KR2k0135_004", r"西南游日记六", "023", "粤西游日记四", 1637),
    ("KR2k0135_005", r"西南游日记七", "024", "黔游日记一", 1638),
    ("KR2k0135_005", r"西南游日记八", "025", "黔游日记二", 1638),
    ("KR2k0135_006", r"西南游日记九", "026", "滇游日记一", 1638),
    ("KR2k0135_006", r"西南游日记十", "027", "滇游日记二", 1638),
    ("KR2k0135_007", r"西南游日记十一", "028", "滇游日记三", 1638),
    ("KR2k0135_007", r"西南游日记十二", "029", "滇游日记四", 1638),
    ("KR2k0135_008", r"西南游日记十三", "030", "滇游日记五", 1638),
    ("KR2k0135_008", r"西南游日记十四", "031", "滇游日记六", 1638),
    ("KR2k0135_009", r"西南游日记十五", "032", "滇游日记七", 1639),
    ("KR2k0135_009", r"西南游日记十六", "033", "滇游日记八", 1639),
    ("KR2k0135_010", r"西南游日记十七", "034", "滇游日记九", 1639),
    ("KR2k0135_010", r"西南游日记十八", "035", "滇游日记十", 1639),
    ("KR2k0135_011", r"西南游日记十九", "036", "滇游日记十一", 1639),
    ("KR2k0135_011", r"西南游日记二十", "037", "滇游日记十二", 1639),
    ("KR2k0135_012", r"西南游日记二十一", "038", "滇游日记十三", 1639),
    ("KR2k0135_012", r"西南游日记二十二", "039", "滇游日记十四", 1639),
    ("KR2k0135_005", r"记游太华山", "040", "记游太华山", 1638),
    ("KR2k0135_005", r"记滇中花木", "041", "记滇中花木", 1638),
    ("KR2k0135_005", r"记游颜洞", "042", "记游颜洞", 1638),
]

# 编者阙文/跋 注行（简体化后行首匹配）——括号注化（原文/注分离）
GAP_NOTE_RE = re.compile(
    r"^(以下.{0,40}(脱去|俱阙)|脱去$|.{0,24}俱阙$|此[后後]共缺.{0,10}|"
    r"自此至.{0,20}共缺.{0,12}|季梦良曰)")
JUAN_HDR_RE = re.compile(r"^徐霞客游记卷[一二三四五六七八九十上下]+$")
TITLE_LIKE_RE = re.compile(r"^(西南游日记[一二三四五六七八九十]+|记游太华山|记滇中花木|记游颜洞)")


def to_simp(t: str) -> str:
    for k, v in VARIANTS.items():
        t = t.replace(k, v)
    return CC.convert(t)


def clean_mandoku(raw: str):
    """→ [(line, kind)] kind: text/title/juan/note"""
    out = []
    n_ent = 0
    for ln in raw.split("\n"):
        s = ln.strip().rstrip("¶").strip()
        s = s.replace("\u3000", "").strip()
        if not s or s.startswith("#") or s.startswith("+"):
            continue
        if re.match(r"^<pb:[^>]+>$", s):
            continue
        n_ent += len(re.findall(r"&KR\d+;", s))
        s = re.sub(r"&KR\d+;", "□", s)
        out.append((s, "raw"))
    return out, n_ent


def extract():
    report = {"pieces": [], "gap_notes": []}
    files = {}
    for fid, _rx, _num, _title, _y in PIECES_KR:
        if fid not in files:
            raw = open(os.path.join(KR_DIR, fid + ".txt"), encoding="utf-8").read()
            files[fid] = clean_mandoku(raw)
    for fid, rx, num, title, year0 in PIECES_KR:
        lines, n_ent = files[fid]
        pat = re.compile(rx)
        body, capturing, sticky_note = [], False, False
        n_notes = 0
        for s, _ in lines:
            simp = to_simp(s)
            if JUAN_HDR_RE.match(simp):
                capturing, sticky_note = False, False   # 卷首尾题行：终止采集
                continue
            if TITLE_LIKE_RE.match(simp) or re.match(r"^记(游|滇)", simp):
                capturing, sticky_note = bool(pat.match(simp)), False
                continue
            if not capturing:
                continue
            if sticky_note or GAP_NOTE_RE.match(simp):
                # 「季梦良曰」跋起 sticky：整块到卷尾/下篇题皆注化（编者跋非霞客原文）
                sticky_note = simp.startswith("季梦良曰")
                body.append("(" + simp + ")")
                n_notes += 1
                report["gap_notes"].append(f"{num} {title}: {simp[:36]}")
                continue
            body.append(simp)
        text = "\n".join(body)
        chars = len(text.replace("\n", ""))
        min_chars = 80 if num >= "040" else 300    # 附记三篇本短（花木记 ~150 字）
        if chars < min_chars:
            raise RuntimeError(f"{num} {title} 仅 {chars} 字——切分异常，请查 {fid}")
        with open(os.path.join(VOL_DIR, f"{num}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        report["pieces"].append({"num": num, "title": title, "kr_file": fid,
                                 "kr_title_rx": rx, "year0": year0, "source": "kr",
                                 "chars": chars, "note_lines": n_notes,
                                 "rare_entity_to_box": n_ent})
        print(f"[切] {num} {title}  {chars:>6} 字  阙文注 {n_notes} 行  罕字□ {n_ent}")
    total = sum(p["chars"] for p in report["pieces"])
    report["total_chars"] = total
    report["source"] = "kanripo/KR2k0135 (文渊阁四库全书本·杨名时重编订)"
    report["caveat"] = ("四库本有讳改删节风险（馆臣编辑），且卷内自注多处阙文；"
                        "站内简体化呈现，罕字以□存疑")
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"\n{len(report['pieces'])} 新篇 · {total:,} 字 → data/vol/ · 报告 kr_report.json")
    print(f"阙文/跋注 {len(report['gap_notes'])} 处（括号注化，不入原文统计）")


if __name__ == "__main__":
    extract()
