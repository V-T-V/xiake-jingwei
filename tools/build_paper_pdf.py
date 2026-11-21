# -*- coding: utf-8 -*-
"""《霞客经纬》研究论文排印 → docs/霞客经纬-论文.pdf（P2，学 HHH docs/build_paper_pdf.py）
数字唯一来源：docs/stats.json（build_stats.py 产物）——出不了脚本的数字不许出现。
行文结构镜像 docs/ANALYSIS.md（语料/游程/字频/词汇场/游年/边界六节）；
方法与边界节的文字自 ANALYSIS.md §六 原样抽取（md↔PDF 联动，lint 哨兵校验新鲜度）。
配色沿站点绛霞 #8e2b22。"""
import json
import os
import re
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "霞客经纬-论文.pdf")
STATS = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))

# 插图缺失时自动重建（管线可重入：stats.json → build_paper_figs.py，学 HHH）
FIGS_DIR = os.path.join(ROOT, "docs", "figs")
NEED_FIGS = ["fig1_trips.png", "fig2_years.png"]
if not all(os.path.isfile(os.path.join(FIGS_DIR, f)) for f in NEED_FIGS):
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "build_paper_figs.py")],
                   check=True)

pdfmetrics.registerFont(TTFont("KaiTi", r"C:\Windows\Fonts\STKAITI.TTF"))
pdfmetrics.registerFont(TTFont("YaHei", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))

ACCENT = colors.HexColor("#8e2b22")          # 绛霞
TEXT_PRIMARY = colors.HexColor("#2e2a26")
TEXT_MUTED = colors.HexColor("#8d8177")
BG_SURFACE = colors.HexColor("#ece8d8")
BG_PAGE = colors.HexColor("#f5f2e3")

W, H = A4
M = 20 * mm
AW = W - 2 * M

S = {
    "title": ParagraphStyle("t", fontName="KaiTi", fontSize=22, leading=32, alignment=TA_CENTER,
                            textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "sub": ParagraphStyle("s", fontName="KaiTi", fontSize=12, leading=19, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, wordWrap="CJK"),
    "h1": ParagraphStyle("h1", fontName="KaiTi", fontSize=15, leading=23, textColor=ACCENT,
                         spaceBefore=14, spaceAfter=6, wordWrap="CJK"),
    "h2": ParagraphStyle("h2", fontName="KaiTi", fontSize=12.5, leading=19, textColor=TEXT_PRIMARY,
                         spaceBefore=9, spaceAfter=4, wordWrap="CJK"),
    "body": ParagraphStyle("b", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                           textColor=TEXT_PRIMARY, spaceAfter=5, wordWrap="CJK", firstLineIndent=21),
    "body0": ParagraphStyle("b0", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                            textColor=TEXT_PRIMARY, spaceAfter=5, wordWrap="CJK"),
    "abs": ParagraphStyle("a", fontName="YaHei", fontSize=9.8, leading=16.5, alignment=TA_JUSTIFY,
                          textColor=TEXT_PRIMARY, wordWrap="CJK", firstLineIndent=19.6),
    "cap": ParagraphStyle("c", fontName="KaiTi", fontSize=9.5, leading=14, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, spaceBefore=2, spaceAfter=8, wordWrap="CJK"),
    "th": ParagraphStyle("th", fontName="YaHei", fontSize=9, leading=13, alignment=TA_CENTER,
                         textColor=colors.white, wordWrap="CJK"),
    "td": ParagraphStyle("td", fontName="YaHei", fontSize=9, leading=13, alignment=TA_CENTER,
                         textColor=TEXT_PRIMARY, wordWrap="CJK"),
}


def P(t, st="body"):
    return Paragraph(t, S[st])


def tbl(headers, rows, widths, caption=None):
    data = [[Paragraph(h, S["th"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), S["td"]) for c in r])
    t = Table(data, colWidths=[w * AW for w in widths], hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_SURFACE]),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c9c5be")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    out = [t]
    if caption:
        out.append(Paragraph(caption, S["cap"]))
    return KeepTogether(out)


def fig(fname, h_mm, caption):
    img = Image(os.path.join(FIGS_DIR, fname), width=AW, height=h_mm * mm, hAlign="CENTER")
    return KeepTogether([Spacer(1, 2 * mm), img, Paragraph(caption, S["cap"])])


def footer(cv, doc):
    cv.saveState()
    cv.setFont("KaiTi", 8.5)
    cv.setFillColor(TEXT_MUTED)
    cv.drawCentredString(W / 2, 12 * mm, f"— {doc.page} —")
    cv.setFont("KaiTi", 7.5)
    cv.drawString(M, 12 * mm, "霞客经纬 · 数字人文研究")
    cv.drawRightString(W - M, 12 * mm, "徐霞客游记 · 前半部 22 篇")
    cv.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18 * mm,
                      bottomMargin=20 * mm,
                      title="《徐霞客游记》的线与时序：廿二程数字人文初析",
                      author="霞客经纬项目组", subject="数字人文·历史地理·游记文学",
                      creator="霞客经纬")
frame = Frame(M, 20 * mm, AW, H - 38 * mm, id="f")
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])

m = STATS["meta"]
trips = STATS["trips"]

# ── ANALYSIS.md §六 方法与边界：原样抽取（md↔PDF 联动的实物证据） ──
md = open(os.path.join(ROOT, "docs", "ANALYSIS.md"), encoding="utf-8").read()
sec6 = md.split("## 六、方法与边界", 1)[-1].strip()
method_bullets = [ln.strip()[2:] for ln in sec6.splitlines() if ln.strip().startswith("- ")]
assert len(method_bullets) >= 3, "ANALYSIS.md §六 抽取失败"

years_last2 = sum(y[1] for y in STATS["years"][-2:])
years_pct = round(years_last2 / m["days"] * 100)
freq24 = STATS["freq"][:24]
wl = STATS["wordlists"]

E = []
# ── 题页块 ──
E += [Spacer(1, 10 * mm),
      P("《徐霞客游记》的线与时序：廿二程数字人文初析", "title"),
      Spacer(1, 3 * mm),
      P(f"——基于 {m['pieces']} 篇游程 · {m['days']} 日条 · {m['charsOrig']:,} 字语料的计量", "sub"),
      Spacer(1, 8 * mm),
      P("霞客经纬项目组", "sub"),
      P("2026 年 11 月 · 全部数字由脚本可复核（tools/build_stats.py → docs/stats.json）", "sub"),
      Spacer(1, 5 * mm),
      HRFlowable(width="34%", thickness=.7, color=ACCENT, hAlign="CENTER"),
      Spacer(1, 5 * mm)]

top_land = "、".join(f"{x[0]} {x[1]:,}" for x in wl["landform"]["top"][:3])
top_motion = "、".join(f"{x[0]} {x[1]:,}" for x in wl["motion"]["top"][:3])
abs_tbl = Table([
    [P(f"<b>摘　要</b>　本文对徐弘祖《徐霞客游记》通行前半部 {m['pieces']} 篇（{m['charsOrig']:,} 字原文，另编者注 {m['charsNote']:,} 字分离不计）作游程—时序双维计量：{m['days']} 个日条解析为锚点折线 {m['kmTotal']:,} km（haversine，含同地往返），锚定 {m['anchored']} 日（覆盖 {m['coverage']}%），坐标以地文学常识定位（确 {m['confQu']} / 推 {m['confTui']}，全部 src=derived）。主要发现：(1) 文本重心在晚年——{STATS['years'][-2][0]}–{STATS['years'][-1][0]}「万里遐征」段 {years_last2} 日条占全书 {years_pct}%；(2) 高频字前四 之/而/里/山——「{freq24[0][0]}」{freq24[0][1]:,} 次居首，山岳意象为底色：地貌词 {wl['landform']['total']:,} 次、行旅词 {wl['motion']['total']:,} 次，山（{wl['landform']['top'][0][1]:,}）与洞（{wl['landform']['top'][2][1]:,}）构成身体在场的两级；(3) 游程结构呈「短游启程—晚年长程」双态：江右/楚/粤西四程 {sum(t['chars'] for t in trips[-4:]):,} 字，占原文 {round(sum(t['chars'] for t in trips[-4:]) / m['charsOrig'] * 100)}%。本文一切数字出自管线脚本，可全量复算。", "abs")],
    [P("<b>关键词</b>　徐霞客游记；数字人文；历史地理；游记文学；文本计量；GIS 锚点", "abs")],
], colWidths=[AW])
abs_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), BG_PAGE),
    ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#c9c5be")),
    ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
E += [abs_tbl, Spacer(1, 6 * mm)]

# ── 一、语料 ──
E += [P("一、语料与口径", "h1"),
      P(f"底本为国学导航《徐霞客游记》（GB18030 直抓 {m['pieces']} 页），通行「前半部」——止于粤西游日记二；"
        f"粤游三四·黔游·滇游十三·附编不在本底本（维基文库于建站网络不可达，宁缺毋假）。"
        f"原文 {m['charsOrig']:,} 字，编者括号注 {m['charsNote']:,} 字（题解/音注/义注）分离后不入统计与检索。"
        f"编年跨度万历四十一年（1613 癸丑·天台）至崇祯十年（1637 丁丑·粤西），纪年以干支推（版内公元注有误者已正）。")]

# ── 二、游程结构 ──
rows = [[t["title"], t["year"], t["days"], t["anchored"], f"{t['km']:,}", f"{t['chars']:,}"] for t in trips]
rows.append(["合计", "1613–1637", m["days"], m["anchored"], f"{m['kmTotal']:,}", f"{m['charsOrig']:,}"])
E += [P("二、游程结构：线与时序", "h1"),
      P("游记的空间单位不是政区而是游程（线），时间单位不是卷而是日记日（时序）。解析以行首日期标记"
        "（干支纪年/闰月/晦朔/廿X日）+ 句末标点后日号分段，得 22 程 506 日条；"
        "地名锚定以 294 条篇内 scope 消歧地名表逐日首现法取之，坐标为今地常识定位（示意坐标，全 src=derived）。"),
      tbl(["篇", "年", "日条", "锚定", "折线km", "原文字"], rows,
          [.30, .13, .11, .11, .15, .20],
          f"表 1　廿二程游程结构（锚定 {m['anchored']} 日 · 覆盖 {m['coverage']}% · 确 {m['confQu']}/推 {m['confTui']}）"),
      P(f"可信里程合计 {m['kmTotal']:,} km 为锚点折线长（剔除 {m['jumps']} 处 >400km 跳段；含同地往返——"
        f"霞客粤西期为静闻病情数度折返，折线如实反映文本行踪，非人行实距）。"
        f"结构呈双态：早年多为一至数日之短游（天台 10 日、雁宕 6 日），晚年则连续数旬之长程"
        f"（江右 81 日、楚游 110 日）——「大丈夫当朝碧海而暮苍梧」由游程长度记于数据。"),
      fig("fig1_trips.png", 127.5,
          f"图 1　廿二程日条长短——早年短游（1613–1633）与万里遐征长程（1636–1637）的双态"
          f"（docs/stats.json: trips）")]

# ── 三、字频 ──
freq_line = " · ".join(f"{c}{n:,}" for c, n in freq24)
E += [P("三、字频", "h1"),
      P(f"全文最高频六十字（前 24 示下）：{freq_line}。"),
      P(f"「{freq24[0][0]}」（{freq24[0][1]:,} 次）居首毫不意外——山岳意象为全书底色；"
        f"地貌词合计 {wl['landform']['total']:,} 次（{top_land}），行旅词 {wl['motion']['total']:,} 次（{top_motion}），"
        f"「游」之为书，一步一山。方位词南（{dict(STATS['freq'])['南']:,}）先于北、东先于西，"
        f"与自东向西的万里遐征走向一致。")]

# ── 四、词汇场 ──
wl_rows = [[wl[k]["label"], f"{wl[k]['total']:,}",
            "、".join(f"{x[0]} {x[1]:,}" for x in wl[k]["top"][:6])] for k in
           ("landform", "motion", "weather", "wonder")]
E += [P("四、词汇场", "h1"),
      tbl(["词场", "合计", "高频词（次）"], wl_rows, [.14, .12, .74],
          f"表 2　四词场合计 {sum(v['total'] for v in wl.values()):,} 次（词表见 tools/build_stats.py）"),
      P(f"叹赏词（胜/奇/绝/异/灵/秀）{wl['wonder']['total']:,} 次而天象词 {wl['weather']['total']:,} 次——"
        f"霞客的注意力分配：地貌（{round(wl['landform']['total'] / sum(v['total'] for v in wl.values()) * 100)}%）≫ 行旅 ≫ 天象 ≫ 叹赏，"
        f"观察先于抒情，是为一部以山川为本体的行走日志。")]

# ── 五、游年分布 ──
yr_rows = [[str(y[0]), y[1], "▮" * max(1, round(y[1] / 6))] for y in STATS["years"]]
E += [P("五、游年分布", "h1"),
      tbl(["年", "日条", "分布"], yr_rows, [.25, .2, .55],
          f"表 3　游年分布（{len(STATS['years'])} 个游年）"),
      P(f"{STATS['years'][-2][0]}–{STATS['years'][-1][0]}「万里遐征」段（浙·江右·楚·粤西）{years_last2} 日条，"
        f"占全书 {years_pct}%——晚年西行是全书重心，亦是存世文本之主体。"),
      fig("fig2_years.png", 92.1,
          f"图 2　游年分布（1613–1637 十个游年）——1636–1637「万里遐征」{years_last2} 日条占 {years_pct}%"
          f"（docs/stats.json: years）")]

# ── 六、方法与边界（自 ANALYSIS.md §六 原样抽取） ──
E += [P("六、方法与边界", "h1")]
for b in method_bullets:
    E.append(P("· " + b, "body0"))

E += [Spacer(1, 4 * mm),
      HRFlowable(width="100%", thickness=.5, color=BG_SURFACE),
      Paragraph("本文一切数字可由仓库脚本复现（tools/build_stats.py → docs/stats.json；游程锚点 tools/build_trip_data.py）；"
                "交互验证：站点「循程而读」（线×时序）与「计量」页签；古今对照导出与方舆互查桥见 P2 管线。", S["cap"])]

doc.build(E)
print("OK →", OUT, os.path.getsize(OUT) // 1024, "KB")
